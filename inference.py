import asyncio
import json
import logging
import re
from openai import AsyncOpenAI
from tqdm import tqdm
import os
from dotenv import load_dotenv
load_dotenv()
from src.evaluation import Prediction, Metrics
from src.reliability_metrics import parse_answer_tag
import tiktoken

def truncate_text_to_tokens(text: str, max_tokens: int, encoding_name: str = "p50k_base") -> str:
    """
    Truncate text to fit within max_tokens using a specific tokenizer.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)

class VLLM: 
    def __init__(self, 
                 api_key: str,
                 model: str,
                 dataset_path: str,
                 base_url: str = f"{os.getenv('HOST_NAME')}/v1",
                 batch_size: int = 4,
                 max_model_len: int = 4096,
                 max_output_tokens: int = 500,
                 delay_between_requests: float = 1.0,
                 prompt_mode: str = "zero_shot"
    ):
        self.client = AsyncOpenAI(
            base_url=base_url, 
            api_key=api_key,                     
        )
        self.model = model
        self.dataset_path = dataset_path
        self.prediction = Prediction(dataset_path)
        self.batch_size = batch_size
        self.max_model_len = max_model_len
        self.max_output_tokens = max_output_tokens
        self.ollama_fallback_max_output_tokens = int(
            os.getenv("OLLAMA_FALLBACK_MAX_OUTPUT_TOKENS", "2048")
        )
        self.delay = delay_between_requests
        self.prompt_mode = prompt_mode
        self.generation_tasks = {"2_3", "4_1", "4_2", "4_3"}

    def get_system_prompt(self, task_name_folder: str):
        task_name = task_name_folder.replace(".", "_")
        namespace = {}
        with open(f"./{task_name_folder}/prompt_{task_name}.py", 'r', encoding='utf-8') as f:
            code = f.read()
            exec(code, namespace)

        if self.prompt_mode == "fewshot":
            return namespace.get("EXAMPLE_FEWSHOT") or namespace.get("EXAMPLE") or ""
        if self.prompt_mode == "reasoning":
            return namespace.get("EXAMPLE_REASONING") or namespace.get("EXAMPLE") or ""
        if self.prompt_mode == "reliability":
            return (
                namespace.get("EXAMPLE_RELIABILITY")
                or namespace.get("EXAMPLE_REASONING")
                or namespace.get("EXAMPLE")
                or ""
            )
        return namespace.get("EXAMPLE") or ""

    def get_batch_questions(self, data, batch_size: int = 4):
        """Group raw dataset entries into batches of items.

        Returns a list of batches where each batch is a list of original data entries.
        This keeps full entry metadata so we can merge predictions back with ground-truths.
        """
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

    async def ask(self, user_prompt, model, max_tokens=None):
        system_prompt = self.get_system_prompt(self.dataset_path.split("/")[1])
        if self.max_model_len is not None:
            user_prompt = truncate_text_to_tokens(user_prompt, self.max_model_len)
        request_max_tokens = max_tokens if max_tokens is not None else self.max_output_tokens
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],  
                max_tokens=request_max_tokens,
                # temperature=1 if is_retry else 0,
                temperature=0,
                response_format={"type": "text"}
            )
        except Exception as e:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "assistant", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],  
                max_tokens=request_max_tokens,
                # temperature=1 if is_retry else 0,
                temperature=0,
                response_format={"type": "text"}
            )
        # Add delay after request
        await asyncio.sleep(self.delay)
        status_code = None
        if hasattr(response, "status_code"):
            status_code = response.status_code
        elif getattr(response, "_transport_response", None) is not None:
            tr = response._transport_response
            status_code = getattr(tr, "status_code", None)
        status_code = status_code or 200
        content = ""
        reasoning = ""
        finish_reason = None
        completion_tokens = None
        if hasattr(response, "choices"):
            choice = response.choices[0]
            message = choice.message
            content = message.content or ""
            finish_reason = choice.finish_reason
            reasoning_attr = getattr(message, "reasoning", None)
            if reasoning_attr:
                reasoning = str(reasoning_attr)
            elif getattr(message, "model_extra", None):
                reasoning = str(message.model_extra.get("reasoning", "") or "")
        elif hasattr(response, "choice"):
            content = response.choice[0].message.content or ""

        if getattr(response, "usage", None) is not None:
            completion_tokens = getattr(response.usage, "completion_tokens", None)
        if status_code != 200:
            raise Exception(f"Error from LLM API: {status_code}")
        return {
            "content": content,
            "reasoning": reasoning,
            "finish_reason": finish_reason,
            "completion_tokens": completion_tokens,
            "max_tokens": request_max_tokens,
        }

    def _is_multiple_choice_task(self) -> bool:
        return self.prediction.task not in self.generation_tasks

    def _extract_mc_answer_from_reasoning(self, reasoning_text: str):
        if not reasoning_text:
            return None
        tail = reasoning_text[-1000:]
        preferred_patterns = [
            r"(?:đáp án|dap an|chọn|chon|final answer|final|answer)\s*(?:là|la|:)?\s*\**\s*([ABCD])\b",
            r"<output>\s*([ABCD])\s*</output>",
            r"<answer>\s*([ABCD])\s*</answer>",
        ]
        for pattern in preferred_patterns:
            matches = re.findall(pattern, tail, flags=re.IGNORECASE)
            if matches:
                return matches[-1].upper()

        fallback = re.findall(r"\b([ABCD])\b", tail, flags=re.IGNORECASE)
        if fallback:
            return fallback[-1].upper()
        return None

    def _parse_model_output(self, raw_text: str):
        clean_text = raw_text.replace("</think>", "")
        if self.prompt_mode == "reasoning":
            return self.prediction.parse_output_with_reasoning(clean_text)
        if self.prompt_mode == "reliability":
            answer_tag = parse_answer_tag(clean_text)
            if answer_tag is not None:
                return self.prediction.parse_output(answer_tag)
            return None
        return self.prediction.parse_output(clean_text)

    async def run(self):

        task_name = self.dataset_path.split("/")[1]

        add_content = False if "remove_content" in self.dataset_path else True
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'./{task_name}/{task_name}_llm_test.log', encoding='utf-8'),
                logging.StreamHandler()
            ])
        data = self.prediction.data        
        results = []
        predictions = []
        batches = self.get_batch_questions(data, batch_size=self.batch_size)
        reasoning_fallback_count = 0
        conditional_retry_count = 0
        for batch in tqdm(batches, desc="Processing batches"):
            user_questions = []
            batch_ground_truths = []
            for item in batch:
                try:
                    input_str, ground_truth = self.prediction.preprocess_input(item)
                    user_questions.append(input_str)
                    batch_ground_truths.append(ground_truth)
                except Exception as e:
                    logging.warning(f"Unknown task: {str(e)}")
            try:
                responses = list(await asyncio.gather(*(self.ask(q, self.model) for q in user_questions)))
                responses_new = []
                for idx, resp_meta in enumerate(responses):
                    content = resp_meta.get("content", "") or ""
                    reasoning = resp_meta.get("reasoning", "") or ""
                    finish_reason = resp_meta.get("finish_reason")
                    completion_tokens = resp_meta.get("completion_tokens")
                    retry_reasoning = ""
                    logging.info(
                        f"[Response meta {idx}] content_len={len(content)} "
                        f"reasoning_len={len(reasoning)} finish_reason={finish_reason} "
                        f"completion_tokens={completion_tokens} max_tokens={resp_meta.get('max_tokens')}"
                    )
                    logging.info(f"[Raw response {idx}]: {content}")
                    parsed_resp = None
                    if content:
                        try:
                            parsed_resp = self._parse_model_output(content)
                        except Exception as e:
                            logging.exception(f"Parsing failed at index {idx}: {e}")

                    if parsed_resp is None:
                        should_retry = (
                            not content.strip()
                            and finish_reason == "length"
                            and bool(reasoning.strip())
                            and self.ollama_fallback_max_output_tokens > (resp_meta.get("max_tokens") or 0)
                        )
                        if should_retry:
                            conditional_retry_count += 1
                            logging.warning(
                                f"Empty content do reasoning token budget exhausted at question {idx}; "
                                f"retrying once with max_tokens={self.ollama_fallback_max_output_tokens}"
                            )
                            resp_retry_meta = await self.ask(
                                user_questions[idx],
                                self.model,
                                max_tokens=self.ollama_fallback_max_output_tokens,
                            )
                            retry_content = resp_retry_meta.get("content", "") or ""
                            retry_reasoning = resp_retry_meta.get("reasoning", "") or ""
                            logging.info(
                                f"[Retry meta {idx}] content_len={len(retry_content)} "
                                f"reasoning_len={len(retry_reasoning)} "
                                f"finish_reason={resp_retry_meta.get('finish_reason')} "
                                f"completion_tokens={resp_retry_meta.get('completion_tokens')} "
                                f"max_tokens={resp_retry_meta.get('max_tokens')}"
                            )

                            if retry_content:
                                try:
                                    parsed_resp = self._parse_model_output(retry_content)
                                except Exception as e:
                                    logging.exception(
                                        f"Retry parsing failed at index {idx}: {e}"
                                    )

                    if parsed_resp is None and self._is_multiple_choice_task():
                        reasoning_source = retry_reasoning if retry_reasoning else reasoning
                        parsed_from_reasoning = self._extract_mc_answer_from_reasoning(reasoning_source)
                        if parsed_from_reasoning is not None:
                            parsed_resp = parsed_from_reasoning
                            reasoning_fallback_count += 1
                            logging.warning(
                                f"Used reasoning fallback for question {idx}: {parsed_resp}"
                            )

                    if parsed_resp is None:
                        logging.warning(f"Failed to parse output for question {idx}; storing empty prediction.")
                        responses_new.append([])
                    else:
                        responses_new.append(parsed_resp)
                responses = responses_new
                logging.info(
                    f"Fallback summary: reasoning_fallback_count={reasoning_fallback_count}, "
                    f"conditional_retry_count={conditional_retry_count}"
                )
                logging.info(f'Predicted Answer (batch): {responses}')
                results.extend(responses)
                for entry, pred, gt in zip(batch, responses, batch_ground_truths):
                    res_entry = entry.copy()
                    res_entry['prediction'] = pred
                    res_entry['ground_truth'] = gt
                    predictions.append(res_entry)
            except Exception as e:
                import traceback
                logging.info(traceback.print_exc())
                logging.error(f"Error during gathering responses: {str(e)}")

        if task_name in ["3.3", "3.4"] and add_content == False:
            output_path = f'./{task_name}/{task_name.replace(".", "_")}_remove_content_llm_test_results_{self.model.replace("/", "_")}.json'
        else: 
            output_path = f'./{task_name}/{task_name.replace(".", "_")}_llm_test_results_{self.model.replace("/", "_")}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            for pred in predictions:
                f.write(json.dumps(pred, ensure_ascii=False) + "\n")

        print("Evaluating predictions...")
        self.metrics = Metrics(output_path)
        metric_results = self.metrics.eval()
        print(metric_results)

        # Update EVAL.md file
        eval_md_path = "EVAL.md"
        columns = ["Task", "Model", "Accuracy", "Precision", "Recall", "F1-Score", "Macro-F1", "BLEU", "ROUGE"]
        
        def format_val(val):
            if isinstance(val, dict):
                return ", ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in val.items())
            elif isinstance(val, float):
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
            "ROUGE": format_val(metric_results.get("ROUGE", ""))
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

        # Sort the rows by Task name (and then Model)
        data_rows = lines[header_idx + 2:]
        
        def parse_task_name(line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                return parts[1]
            return ""
            
        data_rows.sort(key=lambda x: parse_task_name(x))
        
        final_lines = lines[:header_idx + 2] + data_rows
            
        with open(eval_md_path, "w", encoding="utf-8") as f:
            f.writelines(final_lines)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="SeaLLMs/SeaLLMs-v3-1.5B-Chat",
                        help="Model name for LLM inference")
    parser.add_argument("--max_model_len", type=int, 
                        default=None,
                        help="Max token lens")   
    parser.add_argument("--dataset_path", type=str, 
                        default="./2.3/2_3_legal_graph_structuring_dataset_reformatted.jsonl",
                        help="Path to the dataset file")
    parser.add_argument("--batch_size", type=int, 
                        default=4,
                        help="Batch size for processing")
    parser.add_argument("--max_output_tokens", type=int,
                        default=500,
                        help="Max output tokens for each completion")
    parser.add_argument("--prompt_mode", type=str,
                        default="zero_shot",
                        choices=["zero_shot", "fewshot", "reasoning", "reliability"],
                        help="Prompt mode: zero_shot, fewshot, reasoning, or reliability")
    args = parser.parse_args()
    dataset_path = args.dataset_path
    model_name = args.model_name
    
    # Configure rate limits based on provider
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
        dataset_path=dataset_path, 
        batch_size=args.batch_size,
        max_model_len=args.max_model_len,
        max_output_tokens=args.max_output_tokens,
        delay_between_requests=delay,
        prompt_mode=args.prompt_mode
    )
    asyncio.run(vllm.run())
