#!/usr/bin/env python3
"""
Colab Auto-Annotation Notebook Code

Chạy trên Google Colab với T4 GPU.
Model: Gemma 2 9B (4-bit quantization)

Usage: Copy cell-by-cell vào Colab notebook.
"""

# ============================================================
# CELL 1: Install & Setup
# ============================================================
"""
!pip install -q transformers accelerate bitsandbytes sentencepiece
!pip install -q huggingface_hub

import os
os.environ["HF_TOKEN"] = "YOUR_HF_TOKEN"  # Gemma cần accept license
"""

# ============================================================
# CELL 2: Load Model
# ============================================================
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "google/gemma-2-9b-it"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
)

tokenizer = AutoTokenizer.from_pretrained(model_id, token=os.environ["HF_TOKEN"])
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
    token=os.environ["HF_TOKEN"],
)
print(f"Model loaded: {model_id}")
print(f"VRAM: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")
"""

# ============================================================
# CELL 3: Upload Data
# ============================================================
"""
from google.colab import files
import json

# Upload the extracted JSONL files from local machine
print("Upload *_llm_input.jsonl files:")
uploaded = files.upload()

data = {}
for fname, content in uploaded.items():
    task = fname.replace('_llm_input.jsonl', '').replace('_', '.')
    lines = content.decode('utf-8').strip().split('\n')
    data[task] = [json.loads(l) for l in lines if l.strip()]
    print(f"Loaded {task}: {len(data[task])} samples")
"""

# ============================================================
# CELL 4: Annotation Prompt
# ============================================================

ANNOTATION_PROMPT_VI = """Bạn là chuyên gia pháp lý Việt Nam. Hãy annotate mẫu sau với 3 lớp: Citation Grounding, Temporal Validity, Reliability Supervision.

## Câu hỏi
{question}

## Đáp án đúng
{ground_truth}

## Citation đã trích xuất (từ regex)
- Văn bản: {document}
- Điều: {article}
- Khoản: {clause}

## Nhiệm vụ

1. **Citation Grounding**: Xác định văn bản pháp luật liên quan. Nếu regex đã đúng thì giữ nguyên. Nếu sai thì sửa lại.

2. **Temporal Validity**: Đánh giá hiệu lực thời gian:
   - Văn bản còn hiệu lực không?
   - Ngày ban hành (nếu biết)
   - Ngày hiệu lực (nếu biết)

3. **Reliability Supervision**:
   - evidence_sufficient: Thông tin trong câu hỏi có đủ để trả lời đúng không?
   - should_abstain: Model có nên từ chối trả lời không?
   - hallucination_type: Có nguy cơ hallucination không? (null/factual_fabrication/citation_hallucination/temporal_confusion)

## Output format (JSON):
```json
{{
  "citation": {{
    "document_name": "tên văn bản",
    "article": "Điều X",
    "clause": "Khoản Y hoặc null",
    "evidence_passage": "trích dẫn nguyên văn hoặc null"
  }},
  "temporal": {{
    "promulgation_date": "YYYY-MM-DD hoặc null",
    "effective_date": "YYYY-MM-DD hoặc null",
    "expiration_date": "YYYY-MM-DD hoặc null",
    "status": "còn hiệu lực / hết hiệu lực / không rõ",
    "valid_at_query_date": true/false
  }},
  "reliability": {{
    "evidence_sufficient": true/false,
    "unsupported_claims": [],
    "hallucination_type": null,
    "should_abstain": true/false,
    "abstain_reason": "lý do hoặc null"
  }}
}}
```

Chỉ trả về JSON, không giải thích thêm."""


# ============================================================
# CELL 5: LLM Annotation Function
# ============================================================

def annotate_sample(sample: dict, model, tokenizer) -> dict:
    """Use LLM to annotate a single sample."""
    question = sample.get('question', sample.get('description', ''))
    ground_truth = sample.get('ground_truth', sample.get('answer', ''))
    citation = sample.get('extracted_citation', {})

    prompt = ANNOTATION_PROMPT_VI.format(
        question=question[:1500],  # Limit length
        ground_truth=str(ground_truth)[:500],
        document=citation.get('primary_document', 'Không xác định'),
        article=citation.get('primary_article', 'Không xác định'),
        clause=citation.get('primary_clause', 'Không xác định'),
    )

    # Format for Gemma chat template
    messages = [{"role": "user", "content": prompt}]
    input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    # Parse JSON from response
    annotation = parse_llm_response(response)
    annotation['sample_id'] = sample.get('sample_id', '')
    annotation['raw_response'] = response

    return annotation


def parse_llm_response(response: str) -> dict:
    """Extract JSON from LLM response."""
    import re

    # Try to find JSON block
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback
    return {
        'citation': {'document_name': None, 'article': None, 'clause': None, 'evidence_passage': None},
        'temporal': {'status': 'parse_error', 'valid_at_query_date': True},
        'reliability': {'evidence_sufficient': True, 'should_abstain': False, 'hallucination_type': None},
        'parse_error': True,
        'raw_response': response[:500],
    }


# ============================================================
# CELL 6: Run Annotation
# ============================================================

def run_annotation(data: dict, model, tokenizer, output_dir: str = "annotated_output"):
    """Run annotation on all tasks."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    all_results = {}

    for task, samples in data.items():
        print(f"\n{'='*50}")
        print(f"Processing task {task}: {len(samples)} samples")
        print(f"{'='*50}")

        results = []
        errors = 0

        for idx, sample in enumerate(samples):
            try:
                annotation = annotate_sample(sample, model, tokenizer)
                if annotation.get('parse_error'):
                    errors += 1
                results.append(annotation)
            except Exception as e:
                print(f"  Error at {idx}: {e}")
                errors += 1
                results.append({
                    'sample_id': sample.get('sample_id', f'{task}_{idx}'),
                    'error': str(e),
                })

            if (idx + 1) % 20 == 0:
                print(f"  [{idx+1}/{len(samples)}] errors: {errors}")

        # Save results
        output_path = os.path.join(output_dir, f'{task.replace(".", "_")}_annotated.jsonl')
        with open(output_path, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

        all_results[task] = {
            'total': len(samples),
            'errors': errors,
            'output': output_path,
        }
        print(f"  Saved: {output_path}")

    return all_results


# ============================================================
# CELL 7: Validate Against Manual Annotations
# ============================================================

def validate_against_manual(auto_results: list, manual_path: str) -> dict:
    """Compare auto annotations with manual annotations."""
    import json

    # Load manual annotations
    manual = {}
    with open(manual_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            if not item.get('skipped'):
                manual[item['sample_id']] = item

    # Compare
    agreements = {'citation': 0, 'temporal': 0, 'reliability': 0}
    total = 0

    for auto in auto_results:
        sid = auto.get('sample_id', '')
        if sid not in manual:
            continue

        m = manual[sid]
        total += 1

        # Citation agreement (document_name match)
        auto_doc = auto.get('citation', {}).get('document_name', '')
        man_doc = m.get('citation', {}).get('document_name', '')
        if auto_doc and man_doc and auto_doc.lower() in man_doc.lower() or man_doc.lower() in auto_doc.lower():
            agreements['citation'] += 1

        # Temporal agreement (valid_at_query_date match)
        auto_valid = auto.get('temporal', {}).get('valid_at_query_date')
        man_valid = m.get('temporal', {}).get('valid_at_query_date')
        if auto_valid == man_valid:
            agreements['temporal'] += 1

        # Reliability agreement (should_abstain match)
        auto_abstain = auto.get('reliability', {}).get('should_abstain')
        man_abstain = m.get('reliability', {}).get('should_abstain')
        if auto_abstain == man_abstain:
            agreements['reliability'] += 1

    if total == 0:
        return {'error': 'No matching samples found'}

    return {
        'total_compared': total,
        'citation_agreement': agreements['citation'] / total,
        'temporal_agreement': agreements['temporal'] / total,
        'reliability_agreement': agreements['reliability'] / total,
    }


# ============================================================
# CELL 8: Download Results
# ============================================================
"""
from google.colab import files
import os

for fname in os.listdir("annotated_output"):
    if fname.endswith('.jsonl'):
        files.download(f"annotated_output/{fname}")
"""
