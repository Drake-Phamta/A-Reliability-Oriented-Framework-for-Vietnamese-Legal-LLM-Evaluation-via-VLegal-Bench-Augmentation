import argparse
import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import tiktoken
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm import tqdm

from src.evaluation import Metrics, Prediction, task_type_mapping

load_dotenv()

RAW_RESPONSE_LOG_PREVIEW_CHARS = 800


def truncate_text_to_tokens(
    text: str, max_tokens: Optional[int], encoding_name: str = "p50k_base"
) -> str:
    """Truncate text to fit within max_tokens using a specific tokenizer."""
    if max_tokens is None or max_tokens <= 0:
        return text
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)


class VLLM:
    def __init__(
        self,
        api_key: str,
        model: str,
        dataset_path: str,
        prompt_mode: str = "fewshot",
        base_url: Optional[str] = None,
        batch_size: int = 1,
        max_model_len: Optional[int] = 4096,
        reasoning_max_tokens: int = 2048,
        reasoning_fast_tokens: int = 256,
        reasoning_fallback_tokens: Optional[int] = None,
        max_concurrency: int = 4,
        max_empty_retries: int = 1,
        delay_between_requests: float = 1.0,
    ):
        resolved_base_url = base_url or f"{os.getenv('HOST_NAME', 'http://localhost:8000')}/v1"
        self.client = AsyncOpenAI(
            base_url=resolved_base_url,
            api_key=api_key,
        )
        self.base_url = resolved_base_url.rstrip("/")
        self.model = model
        self.dataset_path = Path(dataset_path)
        self.task_folder = self.dataset_path.parent.name
        self.prediction = Prediction(str(self.dataset_path))
        self.task_type = task_type_mapping.get(self.prediction.task, "generation")
        self.batch_size = batch_size
        self.max_model_len = max_model_len
        self.reasoning_max_tokens = max(1, reasoning_max_tokens)
        if reasoning_fallback_tokens is None:
            reasoning_fallback_tokens = self.reasoning_max_tokens
        self.reasoning_fast_tokens = max(1, reasoning_fast_tokens)
        self.reasoning_fallback_tokens = max(
            self.reasoning_fast_tokens, reasoning_fallback_tokens
        )
        self.max_concurrency = max(1, max_concurrency)
        self.max_empty_retries = max(0, max_empty_retries)
        self.delay = delay_between_requests
        self.is_ollama = self._is_ollama_endpoint(self.base_url)
        self.prompt_mode = prompt_mode
        self._system_prompt_cache: Optional[str] = None
        self._request_semaphore = asyncio.Semaphore(self.max_concurrency)

    @staticmethod
    def _is_ollama_endpoint(base_url: str) -> bool:
        parsed = urlparse(base_url)
        host = (parsed.hostname or "").lower()
        return host in {"localhost", "127.0.0.1"} and parsed.port == 11434

    @staticmethod
    def _safe_model_name(model_name: str) -> str:
        return model_name.replace("/", "_").replace(":", "_")

    def _is_multiple_choice_task(self) -> bool:
        return self.task_type in {"multiple_choices", "multiple_choices_imbalance"}

    def _reasoning_speedup_enabled(self) -> bool:
        return self.prompt_mode == "reasoning" and self._is_multiple_choice_task()

    def _max_completion_tokens(self, stage: str = "default") -> int:
        if self._reasoning_speedup_enabled():
            if stage == "fast":
                return self.reasoning_fast_tokens
            return self.reasoning_fallback_tokens
        if self.prompt_mode == "reasoning" and self._is_multiple_choice_task():
            return self.reasoning_max_tokens
        if self._is_multiple_choice_task():
            return 64
        return 500

    def get_system_prompt(self) -> str:
        if self._system_prompt_cache is not None:
            return self._system_prompt_cache

        task_name = self.task_folder.replace(".", "_")
        namespace: Dict[str, Any] = {}
        prompt_path = Path(f"./{self.task_folder}/prompt_{task_name}.py")
        with open(prompt_path, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            exec(code, namespace)
            mode_to_prompt_key = {
                "fewshot": "EXAMPLE_FEWSHOT",
                "zero_shot": "EXAMPLE",
                "reasoning": "EXAMPLE_REASONING",
                "reliability": "EXAMPLE_RELIABILITY",
            }
            prompt_key = mode_to_prompt_key.get(self.prompt_mode, "EXAMPLE")
            selected_prompt = namespace.get(prompt_key)
            if selected_prompt:
                self._system_prompt_cache = selected_prompt
                return selected_prompt
            fallback = namespace.get("EXAMPLE") or ""
            logging.warning(
                "Prompt key '%s' is missing in %s. Falling back to EXAMPLE.",
                prompt_key,
                prompt_path,
            )
            self._system_prompt_cache = fallback
            return fallback
        except SyntaxError as e:
            fallback = self._extract_example_from_raw(code)
            if fallback:
                logging.warning(
                    "Prompt exec SyntaxError for %s (%s). Fallback to raw EXAMPLE.",
                    prompt_path,
                    e,
                )
                self._system_prompt_cache = fallback
                return fallback
            raise

    @staticmethod
    def _extract_example_from_raw(code: str) -> str:
        patterns = [
            r'EXAMPLE\s*=\s*"""(.*?)"""',
            r"EXAMPLE\s*=\s*'''(.*?)'''",
            r'EXAMPLE\s*=\s*"((?:[^"\\]|\\.)*)"',
            r"EXAMPLE\s*=\s*'((?:[^'\\]|\\.)*)'",
        ]
        for pattern in patterns:
            match = re.search(pattern, code, flags=re.DOTALL)
            if match:
                return match.group(1)
        return ""

    def get_batch_questions(self, data, batch_size: int = 4):
        """Group raw dataset entries into batches of items."""
        batches = []
        current = []
        for item in tqdm(data, desc="Creating batches"):
            current.append(item)
            if len(current) >= batch_size:
                batches.append(current)
                current = []
        if current:
            batches.append(current)
        return batches

    async def ask(
        self,
        user_prompt: str,
        model: str,
        max_tokens_override: Optional[int] = None,
        system_prompt_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        system_prompt = system_prompt_override or self.get_system_prompt()
        user_prompt = truncate_text_to_tokens(user_prompt, self.max_model_len)
        max_tokens = max_tokens_override or self._max_completion_tokens()
        request_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0,
            "response_format": {"type": "text"},
        }
        if self.is_ollama:
            request_kwargs["extra_body"] = {
                "options": {
                    "num_ctx": 8192,  # Nới rộng ngữ cảnh lên 8k tokens để gánh prompt dài + 2k token output
                    "num_predict": max_tokens
                }
            }

        try:
            async with self._request_semaphore:
                response = await self.client.chat.completions.create(**request_kwargs)
        except Exception as first_err:
            logging.warning(f"Primary request failed, fallback to assistant-role prompt: {first_err}")
            fallback_kwargs = dict(request_kwargs)
            fallback_kwargs["messages"] = [
                {"role": "assistant", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            async with self._request_semaphore:
                response = await self.client.chat.completions.create(**fallback_kwargs)

        await asyncio.sleep(self.delay)

        status_code = None
        if hasattr(response, "status_code"):
            status_code = response.status_code
        elif getattr(response, "_transport_response", None) is not None:
            tr = response._transport_response
            status_code = getattr(tr, "status_code", None)
        status_code = status_code or 200
        if status_code != 200:
            raise Exception(f"Error from LLM API: {status_code}")

        content = ""
        reasoning = ""
        finish_reason = None
        if getattr(response, "choices", None):
            choice = response.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            message = getattr(choice, "message", None)
            if message is not None:
                content = (getattr(message, "content", None) or "").strip()
                reasoning = (getattr(message, "reasoning", None) or "").strip()

        usage = getattr(response, "usage", None)
        usage_payload = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        }

        return {
            "content": content,
            "reasoning": reasoning,
            "finish_reason": finish_reason,
            "usage": usage_payload,
        }

    def _format_rescue_system_prompt(self) -> str:
        return (
            f"{self.get_system_prompt()}\n\n"
            "BAT BUOC DINH DANG:\n"
            "- Tu duy ngan gon trong <think>...</think>.\n"
            "- Cau tra loi cuoi cung trong <output>...</output>.\n"
            "- CHI ghi dap an hop le cho bai trac nghiem trong output, khong viet them."
        )

    def _format_rescue_user_prompt(self, user_prompt: str) -> str:
        return (
            f"{user_prompt}\n\n"
            "Nhac lai: Chi tra loi theo dung 2 the <think>...</think> va <output>...</output>."
        )

    def _parse_payload(self, payload: Dict[str, Any]):
        raw_content = payload.get("content", "")
        if not raw_content:
            return None
        try:
            if self.prompt_mode == "reasoning" and self._is_multiple_choice_task():
                return self.prediction.parse_output_with_reasoning(raw_content)
            return self.prediction.parse_output(raw_content)
        except Exception as parse_err:
            logging.exception("Parsing failed in payload processing: %s", parse_err)
            return None

    @staticmethod
    def _is_prediction_empty(parsed_resp) -> bool:
        if parsed_resp is None:
            return True
        if isinstance(parsed_resp, str):
            return not parsed_resp.strip()
        if isinstance(parsed_resp, (list, tuple, dict, set)):
            return len(parsed_resp) == 0
        return False

    async def _ask_with_reasoning_fallback(self, user_prompt: str, model: str):
        """Reasoning-only speed path: fast -> fallback retries -> rescue format pass."""
        if not self._reasoning_speedup_enabled():
            payload = await self.ask(user_prompt, model)
            parsed_resp = self._parse_payload(payload)
            return payload, parsed_resp, "default"

        fast_payload = await self.ask(
            user_prompt,
            model,
            max_tokens_override=self._max_completion_tokens("fast"),
        )
        fast_parsed = self._parse_payload(fast_payload)
        if not self._is_prediction_empty(fast_parsed):
            return fast_payload, fast_parsed, "fast"

        for retry_idx in range(self.max_empty_retries):
            fallback_payload = await self.ask(
                user_prompt,
                model,
                max_tokens_override=self._max_completion_tokens("fallback"),
            )
            fallback_parsed = self._parse_payload(fallback_payload)
            if not self._is_prediction_empty(fallback_parsed):
                return fallback_payload, fallback_parsed, f"fallback_{retry_idx + 1}"

        rescue_payload = await self.ask(
            self._format_rescue_user_prompt(user_prompt),
            model,
            max_tokens_override=self._max_completion_tokens("fallback"),
            system_prompt_override=self._format_rescue_system_prompt(),
        )
        rescue_parsed = self._parse_payload(rescue_payload)
        if not self._is_prediction_empty(rescue_parsed):
            return rescue_payload, rescue_parsed, "rescue"
        return rescue_payload, rescue_parsed, "rescue_failed"

    async def run(self):
        task_name = self.task_folder
        add_content = "remove_content" not in str(self.dataset_path)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(f"./{task_name}/{task_name}_llm_test.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        data = self.prediction.data
        predictions = []
        batches = self.get_batch_questions(data, batch_size=self.batch_size)
        logging.info(
            "Run config | task=%s | task_type=%s | prompt_mode=%s | max_completion_tokens=%s | reasoning_max_tokens=%s | reasoning_fast_tokens=%s | reasoning_fallback_tokens=%s | max_concurrency=%s | max_empty_retries=%s | reasoning_speedup_enabled=%s",
            task_name,
            self.task_type,
            self.prompt_mode,
            self._max_completion_tokens(),
            self.reasoning_max_tokens,
            self.reasoning_fast_tokens,
            self.reasoning_fallback_tokens,
            self.max_concurrency,
            self.max_empty_retries,
            self._reasoning_speedup_enabled(),
        )

        for batch in tqdm(batches, desc="Processing batches"):
            valid_entries = []
            user_questions = []
            batch_ground_truths = []
            for item in batch:
                try:
                    input_str, ground_truth = self.prediction.preprocess_input(item)
                except Exception as e:
                    logging.warning(f"Preprocess failed: {e}")
                    continue
                valid_entries.append(item)
                user_questions.append(input_str)
                batch_ground_truths.append(ground_truth)

            if not user_questions:
                logging.warning("Skipping empty batch after preprocess.")
                continue

            try:
                response_tuples = list(
                    await asyncio.gather(
                        *(self._ask_with_reasoning_fallback(q, self.model) for q in user_questions)
                    )
                )
            except Exception as e:
                logging.exception(f"Error during gathering responses: {e}")
                continue

            parsed_responses = []
            for idx, response_tuple in enumerate(response_tuples):
                payload, parsed_resp, stage = response_tuple
                raw_content = payload.get("content", "")
                finish_reason = payload.get("finish_reason")
                usage = payload.get("usage", {})
                raw_reasoning = payload.get("reasoning", "")

                log_preview = raw_content
                if len(log_preview) > RAW_RESPONSE_LOG_PREVIEW_CHARS:
                    log_preview = (
                        f"{raw_content[:RAW_RESPONSE_LOG_PREVIEW_CHARS]}... [truncated "
                        f"{len(raw_content) - RAW_RESPONSE_LOG_PREVIEW_CHARS} chars]"
                    )
                logging.info("[Raw response %s | stage=%s]: %s", idx, stage, log_preview)
                logging.info(
                    "Response meta idx=%s | stage=%s | finish_reason=%s | usage=%s | reasoning_chars=%s",
                    idx,
                    stage,
                    finish_reason,
                    usage,
                    len(raw_reasoning),
                )
                if not raw_content:
                    logging.warning(
                        "Empty content at index %s | finish_reason=%s | usage=%s | reasoning_chars=%s",
                        idx,
                        finish_reason,
                        usage,
                        len(raw_reasoning),
                    )
                    parsed_responses.append([])
                    continue

                if self._is_prediction_empty(parsed_resp):
                    if self.prompt_mode == "reasoning" and self._is_multiple_choice_task():
                        logging.warning(
                            "Reasoning parse returned empty at index %s | stage=%s | finish_reason=%s | usage=%s | expected <output>...</output>",
                            idx,
                            stage,
                            finish_reason,
                            usage,
                        )
                    logging.warning(
                        "Parse returned empty at index %s | stage=%s | finish_reason=%s | usage=%s",
                        idx,
                        stage,
                        finish_reason,
                        usage,
                    )
                    parsed_responses.append([])
                else:
                    parsed_responses.append(parsed_resp)

            logging.info(f"Predicted Answer (batch): {parsed_responses}")
            for entry, pred, gt in zip(valid_entries, parsed_responses, batch_ground_truths):
                res_entry = entry.copy()
                res_entry["prediction"] = pred
                res_entry["ground_truth"] = gt
                predictions.append(res_entry)

        if task_name in ["3.3", "3.4"] and not add_content:
            output_path = (
                f"./{task_name}/{task_name.replace('.', '_')}_remove_content_llm_test_results_"
                f"{self._safe_model_name(self.model)}.json"
            )
        else:
            output_path = (
                f"./{task_name}/{task_name.replace('.', '_')}_llm_test_results_"
                f"{self._safe_model_name(self.model)}.json"
            )
        with open(output_path, "w", encoding="utf-8") as f:
            for pred in predictions:
                f.write(json.dumps(pred, ensure_ascii=False) + "\n")

        print("Evaluating predictions...")
        self.metrics = Metrics(output_path)
        metric_results = self.metrics.eval()
        print(metric_results)

        eval_md_path = "EVAL.md"
        columns = [
            "Task",
            "Model",
            "Accuracy",
            "Precision",
            "Recall",
            "F1-Score",
            "Macro-F1",
            "BLEU",
            "ROUGE",
        ]

        def format_val(val):
            if isinstance(val, dict):
                return ", ".join(
                    f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in val.items()
                )
            if isinstance(val, float):
                return f"{val:.4f}"
            return str(val) if val != "" else ""

        row_data = {
            "Task": task_name,
            "Model": self.model,
            "Accuracy": format_val(metric_results.get("accuracy", "")),
            "Precision": format_val(metric_results.get("precision", "")),
            "Recall": format_val(metric_results.get("recall", "")),
            "F1-Score": format_val(metric_results.get("f1-score", "")),
            "Macro-F1": format_val(metric_results.get("Macro-F1", "")),
            "BLEU": format_val(metric_results.get("BLEU", "")),
            "ROUGE": format_val(metric_results.get("ROUGE", "")),
        }

        lines = []
        if os.path.exists(eval_md_path):
            with open(eval_md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        header_idx = -1
        for i, line in enumerate(lines):
            if "| Task" in line and "| Model" in line:
                header_idx = i
                break

        if header_idx == -1:
            lines.append("| " + " | ".join(columns) + " |\n")
            lines.append("|" + "|".join(["---"] * len(columns)) + "|\n")
            header_idx = len(lines) - 2

        updated = False
        for i in range(header_idx + 2, len(lines)):
            parts = [p.strip() for p in lines[i].split("|")]
            if len(parts) >= 3 and parts[1] == task_name and parts[2] == self.model:
                lines[i] = "| " + " | ".join(row_data[col] for col in columns) + " |\n"
                updated = True
                break

        if not updated:
            lines.append("| " + " | ".join(row_data[col] for col in columns) + " |\n")

        data_rows = lines[header_idx + 2 :]

        def parse_task_name(line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                return parts[1]
            return ""

        data_rows.sort(key=parse_task_name)
        final_lines = lines[: header_idx + 2] + data_rows

        with open(eval_md_path, "w", encoding="utf-8") as f:
            f.writelines(final_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name",
        type=str,
        default="SeaLLMs/SeaLLMs-v3-1.5B-Chat",
        help="Model name for LLM inference",
    )
    parser.add_argument(
        "--max_model_len",
        type=int,
        default=None,
        help="Max token lens",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="./2.3/2_3_legal_graph_structuring_dataset_reformatted.jsonl",
        help="Path to the dataset file",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Batch size for processing",
    )
    parser.add_argument(
        "--prompt_mode",
        type=str,
        default="reasoning",
        choices=["fewshot", "zero_shot", "reasoning", "reliability"],
        help="Prompt mode for system prompt selection",
    )
    parser.add_argument(
        "--reasoning_max_tokens",
        type=int,
        default=2048,
        help="Max completion tokens used for multiple-choice tasks in reasoning mode",
    )
    parser.add_argument(
        "--reasoning_fast_tokens",
        type=int,
        default=256,
        help="Fast-pass max tokens for reasoning mode multiple-choice tasks",
    )
    parser.add_argument(
        "--reasoning_fallback_tokens",
        type=int,
        default=None,
        help="Fallback max tokens for reasoning mode multiple-choice tasks (default: reasoning_max_tokens)",
    )
    parser.add_argument(
        "--max_concurrency",
        type=int,
        default=4,
        help="Maximum concurrent requests per batch",
    )
    parser.add_argument(
        "--max_empty_retries",
        type=int,
        default=1,
        help="Number of fallback retries for empty/invalid reasoning parse",
    )
    args = parser.parse_args()

    model_name = args.model_name
    if "gpt" in model_name.lower() and "oss" not in model_name.lower():
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = "https://api.openai.com/v1"
        delay = 0.5
    elif "gemini" in model_name.lower():
        api_key = os.getenv("GEMINI_API_KEY")
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        delay = 5.0
    elif "claude" in model_name.lower():
        api_key = os.getenv("CLAUDE_API_KEY")
        base_url = "https://api.anthropic.com/v1/"
        delay = 7.0
    else:
        print("Using local host model or custom OpenAI-compatible endpoint")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or f"{os.getenv('HOST_NAME', 'http://localhost:8000')}/v1"
        delay = 0

    vllm = VLLM(
        api_key=api_key,
        model=model_name,
        base_url=base_url,
        dataset_path=args.dataset_path,
        prompt_mode=args.prompt_mode,
        batch_size=args.batch_size,
        max_model_len=args.max_model_len,
        reasoning_max_tokens=args.reasoning_max_tokens,
        reasoning_fast_tokens=args.reasoning_fast_tokens,
        reasoning_fallback_tokens=args.reasoning_fallback_tokens,
        max_concurrency=args.max_concurrency,
        max_empty_retries=args.max_empty_retries,
        delay_between_requests=delay,
    )
    asyncio.run(vllm.run())
