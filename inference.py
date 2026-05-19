import asyncio
import json
import logging
import re
from openai import AsyncOpenAI
from tqdm import tqdm
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
load_dotenv()
from src.evaluation import Prediction, Metrics
from src.result_tracker import upsert_task_metrics
import tiktoken

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:e4b-it-q8_0"
DEFAULT_LLM_PROFILE = "balanced"


def parse_tasks_csv(tasks_csv: str) -> List[str]:
    seen = set()
    tasks: List[str] = []
    for raw in (tasks_csv or "").split(","):
        task = raw.strip()
        if not task:
            continue
        if task not in seen:
            seen.add(task)
            tasks.append(task)
    return tasks


def infer_task_name_from_dataset_path(dataset_path: str) -> str:
    path = Path(dataset_path)
    parent_name = path.parent.name
    if re.match(r"^\d+\.\d+$", parent_name):
        return parent_name

    stem = path.stem
    match = re.match(r"^(\d+)_(\d+)", stem)
    if match:
        return f"{match.group(1)}.{match.group(2)}"

    raise ValueError(f"Cannot infer task name from dataset path: {dataset_path}")


def resolve_dataset_path_for_task(task_name: str) -> str:
    task_name = task_name.strip()
    task_id = task_name.replace(".", "_")
    task_dir = Path(task_name)
    default_path = task_dir / f"{task_id}.jsonl"
    if default_path.exists():
        return str(default_path)

    if not task_dir.exists():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")

    candidates = []
    for item in sorted(task_dir.glob("*.jsonl")):
        low = item.name.lower()
        if "result" in low or "annotated" in low or "subset" in low:
            continue
        candidates.append(item)

    if task_name == "5.3":
        preferred = [p for p in candidates if "legal_ethics_cases" in p.name]
        if preferred:
            return str(preferred[0])

    if candidates:
        return str(candidates[0])

    raise FileNotFoundError(f"No dataset JSONL found for task {task_name}")

def truncate_text_to_tokens(text: str, max_tokens: int, encoding_name: str = "p50k_base") -> str:
    """
    Truncate text to fit within max_tokens using a specific tokenizer.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)


def resolve_decode_config(
    prompt_mode: str,
    llm_profile: str,
    temperature: float = None,
    top_p: float = None,
    repeat_penalty: float = None,
    max_output_tokens: int = None,
) -> Dict:
    profile_key = (llm_profile or DEFAULT_LLM_PROFILE).strip().lower()
    profile_defaults = {
        "stable": {"temperature": 0.1, "top_p": 0.9, "repeat_penalty": 1.0},
        "balanced": {"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.05},
        "reasoning": {"temperature": 0.2, "top_p": 0.95, "repeat_penalty": 1.05},
    }
    if profile_key not in profile_defaults:
        profile_key = DEFAULT_LLM_PROFILE

    mode_key = (prompt_mode or "fewshot").strip().lower()
    mode_defaults = {
        "zero_shot": {"temperature": 0.1, "top_p": 0.9},
        "fewshot": {"temperature": 0.1, "top_p": 0.9},
        "reasoning": {"temperature": 0.2, "top_p": 0.95},
        "reliability": {"temperature": 0.15, "top_p": 0.9},
    }

    resolved = dict(profile_defaults[profile_key])
    resolved.update(mode_defaults.get(mode_key, {}))

    if temperature is not None:
        resolved["temperature"] = temperature
    if top_p is not None:
        resolved["top_p"] = top_p
    if repeat_penalty is not None:
        resolved["repeat_penalty"] = repeat_penalty

    if max_output_tokens is not None:
        resolved["max_output_tokens"] = max_output_tokens
    else:
        if mode_key in ("reasoning", "reliability") or profile_key == "reasoning":
            resolved["max_output_tokens"] = 256
        else:
            resolved["max_output_tokens"] = 128
    resolved["llm_profile"] = profile_key
    return resolved

class VLLM: 
    def __init__(self, 
                 api_key: str,
                 model: str,
                 dataset_path: str,
                 base_url: str = f"{DEFAULT_OLLAMA_BASE_URL}/v1",
                 batch_size: int = 4,
                 max_model_len: int = 4096,
                 max_output_tokens: int = 128,
                 max_retry: int = 1,
                 delay_between_requests: float = 0.0,
                 prompt_mode: str = "fewshot",
                 temperature: float = 0.2,
                 top_p: float = 0.9,
                 repeat_penalty: float = 1.05,
                 llm_profile: str = DEFAULT_LLM_PROFILE
    ):
        self.client = AsyncOpenAI(
            base_url=base_url, 
            api_key=api_key,                     
        )
        self.model = model
        self.dataset_path = dataset_path
        self.task_name = infer_task_name_from_dataset_path(dataset_path)
        self.prediction = Prediction(dataset_path)
        self.batch_size = batch_size
        self.max_model_len = max_model_len
        self.max_output_tokens = max_output_tokens
        self.max_retry = max_retry
        self.delay = delay_between_requests
        self.prompt_mode = prompt_mode
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.llm_profile = llm_profile

    def get_system_prompt(self, task_name_folder: str, prompt_mode: str = "fewshot"):
        task_name = task_name_folder.replace(".", "_")
        namespace = {}
        prompt_path = Path(f"./{task_name_folder}/prompt_{task_name}.py")
        if not prompt_path.exists():
            fallback_prompts = sorted(Path(task_name_folder).glob("prompt_*.py"))
            if not fallback_prompts:
                raise FileNotFoundError(
                    f"No prompt file found for task folder '{task_name_folder}'. "
                    f"Expected: {prompt_path}"
                )
            prompt_path = fallback_prompts[0]

        with open(prompt_path, 'r', encoding='utf-8') as f:
            code = f.read()
            exec(code, namespace)

        if prompt_mode == "fewshot":
            return namespace.get("EXAMPLE_FEWSHOT") or namespace.get("EXAMPLE") or ""
        elif prompt_mode == "reasoning":
            return namespace.get("EXAMPLE_REASONING") or namespace.get("EXAMPLE") or ""
        elif prompt_mode == "reliability":
            return namespace.get("EXAMPLE_RELIABILITY") or namespace.get("EXAMPLE_REASONING") or namespace.get("EXAMPLE") or ""
        else:  # zero_shot
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

    async def ask(self, user_prompt, model):
        system_prompt = self.get_system_prompt(self.task_name, self.prompt_mode)
        max_input_tokens = self.max_model_len
        user_prompt = truncate_text_to_tokens(user_prompt, max_input_tokens)
        request_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "response_format": {"type": "text"},
        }
        if self.repeat_penalty is not None:
            request_kwargs["repeat_penalty"] = self.repeat_penalty
        try:
            response = await self.client.chat.completions.create(**request_kwargs)
        except Exception:
            # Compatibility fallback for backends that do not accept repeat_penalty.
            request_kwargs.pop("repeat_penalty", None)
            response = await self.client.chat.completions.create(**request_kwargs)
        # Add delay after request
        await asyncio.sleep(self.delay)
        status_code = None
        if hasattr(response, "status_code"):
            status_code = response.status_code
        elif getattr(response, "_transport_response", None) is not None:
            tr = response._transport_response
            status_code = getattr(tr, "status_code", None)
        status_code = status_code or 200
        content = None
        if hasattr(response, "choices"):
            message = response.choices[0].message
            content = message.content
            if not content and hasattr(message, "reasoning"):
                content = message.reasoning
        elif hasattr(response, "choice"):
            content = response.choice[0].message.content
        if status_code != 200:
            raise Exception(f"Error from LLM API: {status_code}")
        return content

    async def run(self):

        task_name = self.task_name

        add_content = False if "remove_content" in self.dataset_path else True
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'./{task_name}/{task_name}_llm_test.log', encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True)
        data = self.prediction.data        
        results = []
        predictions = []
        batches = self.get_batch_questions(data, batch_size=self.batch_size)
        max_attempt = self.max_retry
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
                batch_raw_responses = list(responses)
                responses_new = []
                thinking = []
                for idx, resp in enumerate(responses):
                    logging.info(f"[Raw response {idx}]: {resp}")
                    parsed_resp = None
                    parsed_think = None
                    if resp:
                        try:
                            clean_resp = resp.replace("</think>", "")
                            if self.prompt_mode == "reasoning":
                                parsed_resp = self.prediction.parse_output_with_reasoning(clean_resp)
                            elif self.prompt_mode == "reliability":
                                parsed_resp = self.prediction.parse_answer_tag(clean_resp)
                            else:
                                parsed_resp = self.prediction.parse_output(clean_resp)
                        except Exception as e:
                            logging.exception(f"Parsing failed at index {idx}: {e}")

                    if parsed_resp is None:
                        for attempt in range(1, max_attempt + 1):
                            logging.info(
                                f"Retrying parsing for question {idx}, attempt {attempt}"
                            )

                            resp_retry = await self.ask(user_questions[idx], self.model)
                            if not resp_retry:
                                continue
                            try:
                                clean_retry = resp_retry.replace("</think>", "")
                                if self.prompt_mode == "reasoning":
                                    parsed_resp = self.prediction.parse_output_with_reasoning(clean_retry)
                                elif self.prompt_mode == "reliability":
                                    parsed_resp = self.prediction.parse_answer_tag(clean_retry)
                                else:
                                    parsed_resp = self.prediction.parse_output(clean_retry)
                            except Exception as e:
                                logging.exception(
                                    f"Retry parsing failed at index {idx}: {e}"
                                )
                            if parsed_resp is not None:
                                break
                    if parsed_resp is None:
                        responses_new.append([])
                    else:
                        responses_new.append(parsed_resp)
                responses = responses_new
                logging.info(f'Predicted Answer (batch): {responses}')
                results.extend(responses)
                for entry, pred, gt, raw_resp in zip(batch, responses, batch_ground_truths, batch_raw_responses):
                    res_entry = entry.copy()
                    res_entry['prediction'] = pred
                    res_entry['raw_response'] = raw_resp or ''
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
        upsert_task_metrics("./result.md", task_name, metric_results)
        print("Updated metrics table: ./result.md")
        return {
            "task": task_name,
            "dataset_path": self.dataset_path,
            "output_path": output_path,
            "metrics": metric_results,
            "num_predictions": len(predictions),
        }


def run_single_dataset(dataset_path: str, model_name: str, base_url: str, api_key: str, args) -> Dict:
    decode_config = resolve_decode_config(
        prompt_mode=args.prompt_mode,
        llm_profile=args.llm_profile,
        temperature=args.temperature,
        top_p=args.top_p,
        repeat_penalty=args.repeat_penalty,
        max_output_tokens=args.max_output_tokens,
    )
    vllm = VLLM(
        api_key=api_key,
        model=model_name,
        base_url=base_url,
        dataset_path=dataset_path,
        batch_size=args.batch_size,
        max_model_len=args.max_model_len,
        max_output_tokens=decode_config["max_output_tokens"],
        max_retry=args.max_retry,
        delay_between_requests=0.0,
        prompt_mode=args.prompt_mode,
        temperature=decode_config["temperature"],
        top_p=decode_config["top_p"],
        repeat_penalty=decode_config["repeat_penalty"],
        llm_profile=decode_config["llm_profile"],
    )
    return asyncio.run(vllm.run())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default=None,
                        help="Model name for LLM inference")
    parser.add_argument("--base_url", type=str, default=None,
                        help="Ollama base URL (without /v1)")
    parser.add_argument("--max_model_len", type=int, 
                        default=None,
                        help="Max token lens")   
    parser.add_argument("--max_output_tokens", type=int,
                        default=None,
                        help="Max output tokens for each response")
    parser.add_argument("--max_retry", type=int,
                        default=1,
                        help="Number of retry attempts when parsing fails")
    parser.add_argument("--dataset_path", type=str, 
                        default="./2.3/2_3_legal_graph_structuring_dataset_reformatted.jsonl",
                        help="Path to the dataset file")
    parser.add_argument("--tasks", type=str, default=None,
                        help="Comma-separated tasks to run (e.g., 1.1,1.2,1.3)")
    parser.add_argument("--batch_size", type=int,
                        default=4,
                        help="Batch size for processing")
    parser.add_argument("--prompt_mode", type=str,
                        default="fewshot",
                        choices=["zero_shot", "fewshot", "reasoning", "reliability"],
                        help="Prompt mode: zero_shot, fewshot, reasoning, or reliability")
    parser.add_argument("--temperature", type=float, default=None,
                        help="Decoding temperature (override profile/mode defaults)")
    parser.add_argument("--top_p", type=float, default=None,
                        help="Decoding top_p (override profile/mode defaults)")
    parser.add_argument("--repeat_penalty", type=float, default=None,
                        help="Decoding repeat penalty (override profile/mode defaults)")
    parser.add_argument("--llm_profile", type=str, default=DEFAULT_LLM_PROFILE,
                        choices=["stable", "balanced", "reasoning"],
                        help="Decode profile preset: stable, balanced, reasoning")
    args = parser.parse_args()
    dataset_path = args.dataset_path
    model_name = args.model_name or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    raw_base_url = args.base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    raw_base_url = raw_base_url.rstrip("/")
    base_url = f"{raw_base_url}/v1"
    api_key = os.getenv("OLLAMA_API_KEY", "ollama")

    if not model_name.strip():
        raise ValueError("OLLAMA model is empty. Set OLLAMA_MODEL or pass --model_name.")

    decode_config = resolve_decode_config(
        prompt_mode=args.prompt_mode,
        llm_profile=args.llm_profile,
        temperature=args.temperature,
        top_p=args.top_p,
        repeat_penalty=args.repeat_penalty,
        max_output_tokens=args.max_output_tokens,
    )
    args.temperature = decode_config["temperature"]
    args.top_p = decode_config["top_p"]
    args.repeat_penalty = decode_config["repeat_penalty"]
    args.max_output_tokens = decode_config["max_output_tokens"]
    args.llm_profile = decode_config["llm_profile"]
    print(
        "[INFO] Decode config: "
        f"profile={args.llm_profile}, prompt_mode={args.prompt_mode}, "
        f"temperature={args.temperature}, top_p={args.top_p}, "
        f"repeat_penalty={args.repeat_penalty}, max_output_tokens={args.max_output_tokens}"
    )

    if args.tasks:
        tasks = parse_tasks_csv(args.tasks)
        if not tasks:
            raise ValueError("No valid tasks parsed from --tasks.")

        success_runs = []
        failed_runs = []
        for task in tasks:
            try:
                resolved_dataset = resolve_dataset_path_for_task(task)
            except Exception as exc:
                failed_runs.append({
                    "task": task,
                    "dataset_path": None,
                    "error": f"Dataset resolve failed: {exc}",
                })
                print(f"[FAILED] {task} - Dataset resolve failed: {exc}")
                continue

            print(f"[RUNNING] task={task} dataset={resolved_dataset}")
            try:
                run_info = run_single_dataset(
                    dataset_path=resolved_dataset,
                    model_name=model_name,
                    base_url=base_url,
                    api_key=api_key,
                    args=args,
                )
                success_runs.append(run_info)
                print(f"[SUCCESS] {task}")
            except Exception as exc:
                failed_runs.append({
                    "task": task,
                    "dataset_path": resolved_dataset,
                    "error": str(exc),
                })
                print(f"[FAILED] {task} - {exc}")

        print("\n=== Multi-task Summary ===")
        print(f"Total tasks: {len(tasks)}")
        print(f"Success: {len(success_runs)}")
        print(f"Failed: {len(failed_runs)}")
        print("success_tasks:", [run["task"] for run in success_runs])
        print("failed_tasks:", [run["task"] for run in failed_runs])
        print("success_datasets:", {run["task"]: run["dataset_path"] for run in success_runs})
        if failed_runs:
            print("failed_details:", failed_runs)
    else:
        try:
            run_single_dataset(
                dataset_path=dataset_path,
                model_name=model_name,
                base_url=base_url,
                api_key=api_key,
                args=args,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to run inference with local Ollama. "
                f"Check endpoint '{base_url}' and ensure model '{model_name}' is available "
                "(for example: ollama list / ollama pull google/gemma-4-E4B-it)."
            ) from exc
