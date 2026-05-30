# ============================================================
# CELL 1: Cài đặt thư viện
# ============================================================

!pip install -q transformers accelerate bitsandbytes sentencepiece

# ============================================================
# CELL 2: Load model Qwen2.5-3B (4-bit, chạy được trên T4 free)
# ============================================================

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "Qwen/Qwen2.5-3B-Instruct"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16,
)
print(f"Model loaded: {model_id}")
print(f"VRAM: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")

# ============================================================
# CELL 3: Upload 6 file *_llm_input.jsonl
# ============================================================

from google.colab import files
import json
import re

print("Upload 6 file: 1_4_llm_input.jsonl, 1_5_llm_input.jsonl, 3_1_llm_input.jsonl, 3_3_llm_input.jsonl, 4_1_llm_input.jsonl, 4_2_llm_input.jsonl")
uploaded = files.upload()

data = {}
for fname, content in uploaded.items():
    match = re.search(r'(\d+_\d+)_llm_input', fname)
    if match:
        task = match.group(1).replace('_', '.')
    else:
        print(f"  SKIP: {fname}")
        continue
    lines = content.decode('utf-8').strip().split('\n')
    data[task] = [json.loads(l) for l in lines if l.strip()]
    print(f"  {task}: {len(data[task])} samples")

print(f"\nLoaded {len(data)} tasks: {list(data.keys())}")

# ============================================================
# CELL 4: Định nghĩa prompt và hàm xử lý
# ============================================================

import os
import time

SHORT_PROMPT = """Bạn là chuyên gia pháp lý Việt Nam. Annotate mẫu sau.

Câu hỏi: {question}
Đáp án đúng: {ground_truth}
Citation: {document}, {article}, {clause}

Trả về JSON:
```json
{{
  "citation": {{"document_name": "...", "article": "Điều X", "clause": "Khoản Y hoặc null", "evidence_passage": "trích dẫn hoặc null"}},
  "temporal": {{"promulgation_date": "YYYY-MM-DD hoặc null", "effective_date": "YYYY-MM-DD hoặc null", "expiration_date": "YYYY-MM-DD hoặc null", "status": "còn/hết/không rõ", "valid_at_query_date": true}},
  "reliability": {{"evidence_sufficient": true, "unsupported_claims": [], "hallucination_type": null, "should_abstain": false, "abstain_reason": null}}
}}
```
Chỉ trả về JSON."""


def parse_llm_response(response):
    """Tách JSON từ output của LLM."""
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    return {
        'citation': {'document_name': None, 'article': None, 'clause': None, 'evidence_passage': None},
        'temporal': {'status': 'parse_error', 'valid_at_query_date': True},
        'reliability': {'evidence_sufficient': True, 'should_abstain': False, 'hallucination_type': None},
        'parse_error': True,
        'raw_response': response[:500],
    }


def build_prompt(sample):
    """Tạo prompt cho 1 mẫu."""
    question = sample.get('question', sample.get('description', ''))[:800]
    ground_truth = str(sample.get('ground_truth', sample.get('answer', '')))[:200]
    citation = sample.get('extracted_citation', {})
    return SHORT_PROMPT.format(
        question=question,
        ground_truth=ground_truth,
        document=citation.get('primary_document', 'Không rõ'),
        article=citation.get('primary_article', 'Không rõ'),
        clause=citation.get('primary_clause', 'Không rõ'),
    )


def annotate_batch(samples, model, tokenizer):
    """Annotate 1 batch mẫu (4 mẫu cùng lúc)."""
    prompts = [build_prompt(s) for s in samples]
    messages_list = [[{"role": "user", "content": p}] for p in prompts]
    texts = [tokenizer.apply_chat_template(m, tokenize=False, add_generation_prompt=True) for m in messages_list]
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=2048).to(model.device)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=512, do_sample=False, pad_token_id=tokenizer.eos_token_id)

    results = []
    for i, output in enumerate(outputs):
        response = tokenizer.decode(output[inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        annotation = parse_llm_response(response)
        annotation['sample_id'] = samples[i].get('sample_id', '')
        annotation['raw_response'] = response[:500]
        results.append(annotation)
    return results


def run_all(data, model, tokenizer, output_dir="annotated_output", batch_size=4):
    """Chạy annotation tất cả tasks."""
    os.makedirs(output_dir, exist_ok=True)
    summary = {}

    for task, samples in data.items():
        print(f"\n{'='*50}")
        print(f"Task {task}: {len(samples)} samples (batch_size={batch_size})")
        print(f"{'='*50}", flush=True)

        results = []
        errors = 0
        start_time = time.time()

        for i in range(0, len(samples), batch_size):
            batch = samples[i:i+batch_size]
            try:
                batch_results = annotate_batch(batch, model, tokenizer)
                for r in batch_results:
                    if r.get('parse_error'):
                        errors += 1
                    results.append(r)
            except Exception as e:
                errors += len(batch)
                for s in batch:
                    results.append({'sample_id': s.get('sample_id', ''), 'error': str(e)})

            processed = min(i + batch_size, len(samples))
            if processed % 20 == 0 or processed == len(samples):
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (len(samples) - processed) / rate if rate > 0 else 0
                print(f"  [{processed}/{len(samples)}] errors: {errors} | {rate:.1f} samples/s | ~{remaining/60:.0f} min left", flush=True)

        output_path = os.path.join(output_dir, f'{task.replace(".", "_")}_annotated.jsonl')
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

        elapsed = time.time() - start_time
        summary[task] = {'total': len(samples), 'errors': errors, 'time_min': elapsed / 60, 'output': output_path}
        print(f"  Saved: {output_path} ({elapsed/60:.1f} min)", flush=True)

    return summary

print("Functions ready. Chạy CELL 5 để bắt đầu annotation.")

# ============================================================
# CELL 5: Bắt đầu annotation
# ============================================================

summary = run_all(data, model, tokenizer)

print(f"\n{'='*50}")
print("SUMMARY")
print(f"{'='*50}")
for task, stats in summary.items():
    print(f"  {task}: {stats['total']} samples, {stats['errors']} errors, {stats['time_min']:.1f} min")

# ============================================================
# CELL 6: Download kết quả
# ============================================================

from google.colab import files as colab_files

for fname in sorted(os.listdir("annotated_output")):
    if fname.endswith('.jsonl'):
        colab_files.download(f"annotated_output/{fname}")
        print(f"Downloaded: {fname}")
