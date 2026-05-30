import asyncio
import json
import logging
from pyexpat import model
from openai import AsyncOpenAI
from tqdm import tqdm
import os
from dotenv import load_dotenv
load_dotenv()
from src.evaluation import Prediction, Metrics
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
                 base_url: str = f"{os.getenv("HOST_NAME")}/v1",
                 batch_size: int = 4,
                 max_model_len: int = 4096,
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
        self.delay = delay_between_requests
        self.prompt_mode = prompt_mode

    def get_system_prompt(self, task_name_folder: str, prompt_mode: str = "zero_shot"):
        task_name = task_name_folder.replace(".", "_")
        namespace = {}
        with open(f"./{task_name_folder}/prompt_{task_name}.py", 'r', encoding='utf-8') as f:
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
        system_prompt = self.get_system_prompt(self.dataset_path.split("/")[1], self.prompt_mode)
        max_input_tokens = self.max_model_len
        user_prompt = truncate_text_to_tokens(user_prompt, max_input_tokens)
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],  
                max_tokens=500,
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
                max_tokens=500,
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
        content = None
        if hasattr(response, "choices"):
            content = response.choices[0].message.content
        elif hasattr(response, "choice"):
            content = response.choice[0].message.content
        if status_code != 200:
            raise Exception(f"Error from LLM API: {status_code}")
        return content

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
        max_attempt = 3
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
        print("Using local host model")
        api_key = os.getenv("API_KEY")
        base_url = f"{os.getenv("HOST_NAME")}/v1"
        delay = 0
    vllm = VLLM(
        api_key=api_key,
        model=model_name,
        base_url=base_url,
        dataset_path=dataset_path,
        batch_size=args.batch_size,
        max_model_len=args.max_model_len,
        delay_between_requests=delay,
        prompt_mode=args.prompt_mode
    )
    asyncio.run(vllm.run())