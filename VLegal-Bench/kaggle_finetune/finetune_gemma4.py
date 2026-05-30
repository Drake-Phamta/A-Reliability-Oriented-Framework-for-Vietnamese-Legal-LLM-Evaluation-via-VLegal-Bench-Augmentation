# ============================================================
# CELL 1: Cài đặt Unsloth + dependencies
# ============================================================

%%capture
import torch
major_version, minor_version = torch.cuda.get_device_capability()
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
if major_version >= 8:
    !pip install --no-deps packaging ninja einops "flash-attn>=2.6.3"
!pip install datasets trl peft accelerate

# ============================================================
# CELL 2: Load Gemma 4 E4B với Unsloth (4-bit QLoRA)
# ============================================================

from unsloth import FastModel
import torch

model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-4-E4B-it",
    dtype=None,
    max_seq_length=2048,
    load_in_4bit=True,
    full_finetuning=False,
)

model = FastModel.get_peft_model(
    model,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    random_state=3407,
    target_modules="all-linear",
)

from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="gemma-4")

model.print_trainable_parameters()
print(f"VRAM: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")

# ============================================================
# CELL 3: Upload data
# ============================================================

"""
Upload lên Kaggle Dataset:
1. VLegal-Bench/{task}/{task_id}.jsonl  (22 tasks)
2. annotated/  (6 file *_annotated.jsonl từ Colab)

Hoặc upload trực tiếp vào /kaggle/input/
"""

import os
import json
import glob

DATA_DIR = "/kaggle/input/vlegal-bench"  # Thay đổi theo Kaggle dataset path

# Tìm tất cả task data
ALL_TASKS = ["1.1","1.2","1.3","1.4","1.5",
             "2.1","2.2","2.3","2.4","2.5",
             "3.1","3.2","3.3","3.4","3.5",
             "4.1","4.2","4.3",
             "5.1","5.2","5.3","5.4"]

ANNOTATED_TASKS = ["1.4", "1.5", "3.1", "3.3", "4.1", "4.2"]

def load_jsonl(path):
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def find_task_file(task):
    """Tìm file JSONL cho task."""
    task_id = task.replace(".", "_")
    patterns = [
        f"{DATA_DIR}/{task}/{task_id}.jsonl",
        f"{DATA_DIR}/{task_id}.jsonl",
        f"{DATA_DIR}/**/{task_id}.jsonl",
    ]
    for p in patterns:
        matches = glob.glob(p, recursive=True)
        if matches:
            return matches[0]
    # Tìm bất kỳ jsonl nào trong thư mục task
    task_dir = f"{DATA_DIR}/{task}"
    if os.path.exists(task_dir):
        for f in os.listdir(task_dir):
            if f.endswith(".jsonl") and "result" not in f and "annotated" not in f:
                return f"{task_dir}/{f}"
    return None

def find_annotated_file(task):
    """Tìm file annotated JSONL."""
    task_id = task.replace(".", "_")
    patterns = [
        f"{DATA_DIR}/annotated/{task_id}_annotated.jsonl",
        f"{DATA_DIR}/{task_id}_annotated.jsonl",
        f"{DATA_DIR}/**/{task_id}_annotated.jsonl",
    ]
    for p in patterns:
        matches = glob.glob(p, recursive=True)
        if matches:
            return matches[0]
    return None

# Load all task data
task_data = {}
for task in ALL_TASKS:
    path = find_task_file(task)
    if path:
        task_data[task] = load_jsonl(path)
        print(f"  Task {task}: {len(task_data[task])} samples")
    else:
        print(f"  Task {task}: NOT FOUND")

# Load annotations
annotations = {}
for task in ANNOTATED_TASKS:
    path = find_annotated_file(task)
    if path:
        raw = load_jsonl(path)
        # Index by sample_id
        for item in raw:
            sid = item.get("sample_id", "")
            if sid:
                annotations[sid] = item
        print(f"  Annotation {task}: {len(raw)} samples")
    else:
        print(f"  Annotation {task}: NOT FOUND")

print(f"\nTotal: {sum(len(v) for v in task_data.values())} samples, "
      f"{len(annotations)} annotated")

# ============================================================
# CELL 4: Chuẩn bị training data
# ============================================================

SYSTEM_PROMPT = "Bạn là trợ lý pháp lý AI chuyên về pháp luật Việt Nam."

def build_reasoning_response(ground_truth, annotation=None):
    """Tạo response có reasoning chain."""
    parts = ["Phân tích câu hỏi pháp lý:"]

    if annotation:
        cit = annotation.get("citation", {})
        if cit.get("document_name"):
            parts.append(f"Văn bản: {cit['document_name']}")
        if cit.get("article"):
            parts.append(f"Điều: {cit['article']}")
        if cit.get("clause"):
            parts.append(f"Khoản: {cit['clause']}")
        if cit.get("evidence_passage"):
            parts.append(f"Căn cứ: {cit['evidence_passage'][:200]}")

        temp = annotation.get("temporal", {})
        if temp.get("status"):
            parts.append(f"Hiệu lực: {temp['status']}")

        rel = annotation.get("reliability", {})
        if not rel.get("evidence_sufficient", True):
            parts.append("Lưu ý: Bằng chứng không đầy đủ")
        if rel.get("should_abstain", False):
            parts.append("Cần từ chối trả lời do thiếu thông tin")

    reasoning = "\n".join(parts)
    return f"<think>\n{reasoning}\n</think>\n<answer>{ground_truth}</answer>"


def format_baseline_example(item, task):
    """Format cho Baseline 3: direct answer."""
    instruction = item.get("instruction", "")
    question = item.get("question", item.get("description", item.get("content", "")))
    answers = item.get("answers", "")
    ground_truth = str(item.get("ground_truth", item.get("answer", "")))

    user_text = f"{instruction}\n{question}".strip()
    if answers:
        user_text += f"\n{answers}"

    return {
        "conversations": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": ground_truth},
        ]
    }


def format_proposed_example(item, task, annotation=None):
    """Format cho Proposed: reasoning + reliability."""
    instruction = item.get("instruction", "")
    question = item.get("question", item.get("description", item.get("content", "")))
    answers = item.get("answers", "")
    ground_truth = str(item.get("ground_truth", item.get("answer", "")))

    user_text = f"{instruction}\n{question}".strip()
    if answers:
        user_text += f"\n{answers}"

    response = build_reasoning_response(ground_truth, annotation)

    return {
        "conversations": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": response},
        ]
    }


def prepare_dataset(mode="baseline_3"):
    """Chuẩn bị dataset cho training."""
    from datasets import Dataset

    examples = []
    for task in ALL_TASKS:
        if task not in task_data:
            continue

        for item in task_data[task]:
            sid = item.get("sample_id", "")
            annotation = annotations.get(sid) if sid else None

            if mode == "baseline_3":
                ex = format_baseline_example(item, task)
            else:
                # Proposed: dùng annotation nếu có, không thì reasoning thường
                ex = format_proposed_example(item, task, annotation)

            examples.append(ex)

    dataset = Dataset.from_list(examples)

    # Apply chat template
    def apply_template(examples):
        texts = []
        for convo in examples["conversations"]:
            text = tokenizer.apply_chat_template(
                convo, tokenize=False, add_generation_prompt=False
            ).removeprefix("<bos>")
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(apply_template, batched=True, remove_columns=["conversations"])
    return dataset


# Chuẩn bị cả 2 dataset
print("Preparing Baseline 3 dataset...")
dataset_baseline = prepare_dataset("baseline_3")
print(f"  Baseline 3: {len(dataset_baseline)} samples")

print("Preparing Proposed dataset...")
dataset_proposed = prepare_dataset("proposed")
print(f"  Proposed: {len(dataset_proposed)} samples")

# ============================================================
# CELL 5: Train Baseline 3
# ============================================================

from trl import SFTTrainer, SFTConfig
from unsloth.chat_templates import train_on_responses_only

print("="*60)
print("TRAINING: Baseline 3 (LoRA, no reliability data)")
print("="*60)

trainer_baseline = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset_baseline,
    args=SFTConfig(
        dataset_text_field="text",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        warmup_steps=50,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.001,
        lr_scheduler_type="linear",
        seed=3407,
        report_to="none",
        output_dir="outputs_baseline_3",
        save_steps=500,
        save_total_limit=2,
        fp16=True,
        remove_unused_columns=False,
        max_seq_length=2048,
    ),
)

trainer_baseline = train_on_responses_only(
    trainer_baseline,
    instruction_part="<|turn|>user\n",
    response_part="<|turn|>model\n",
)

trainer_stats = trainer_baseline.train()

# Save
model.save_pretrained("baseline_3_lora")
tokenizer.save_pretrained("baseline_3_lora")
print(f"Baseline 3 saved. Stats: {trainer_stats}")

# ============================================================
# CELL 6: Reload model cho Proposed (reset LoRA weights)
# ============================================================

# Reload base model để train Proposed từ đầu
model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-4-E4B-it",
    dtype=None,
    max_seq_length=2048,
    load_in_4bit=True,
    full_finetuning=False,
)

model = FastModel.get_peft_model(
    model,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    random_state=3407,
    target_modules="all-linear",
)

tokenizer = get_chat_template(tokenizer, chat_template="gemma-4")
print("Model reloaded for Proposed training")

# ============================================================
# CELL 7: Train Proposed
# ============================================================

print("="*60)
print("TRAINING: Proposed (LoRA + reliability annotations)")
print("="*60)

trainer_proposed = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset_proposed,
    args=SFTConfig(
        dataset_text_field="text",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        warmup_steps=50,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.001,
        lr_scheduler_type="linear",
        seed=3407,
        report_to="none",
        output_dir="outputs_proposed",
        save_steps=500,
        save_total_limit=2,
        fp16=True,
        remove_unused_columns=False,
        max_seq_length=2048,
    ),
)

trainer_proposed = train_on_responses_only(
    trainer_proposed,
    instruction_part="<|turn|>user\n",
    response_part="<|turn|>model\n",
)

trainer_stats = trainer_proposed.train()

# Save
model.save_pretrained("proposed_lora")
tokenizer.save_pretrained("proposed_lora")
print(f"Proposed saved. Stats: {trainer_stats}")

# ============================================================
# CELL 8: Test inference
# ============================================================

from transformers import TextStreamer

def test_inference(model, tokenizer, question, max_tokens=256):
    """Test inference với 1 câu hỏi."""
    messages = [
        {"role": "user", "content": question},
    ]
    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_tensors="pt"
    ).to("cuda")

    streamer = TextStreamer(tokenizer, skip_prompt=True)
    _ = model.generate(
        input_ids=inputs,
        max_new_tokens=max_tokens,
        streamer=streamer,
        use_cache=True,
    )

# Test câu hỏi mẫu
test_q = "Hợp đồng vay tài sản theo Bộ luật Dân sự 2015 cần có những yếu tố gì?"

print("=== Baseline 3 ===")
# Load baseline model nếu cần
test_inference(model, tokenizer, test_q)

print("\n=== Proposed ===")
test_inference(model, tokenizer, test_q)

# ============================================================
# CELL 9: Export models
# ============================================================

import shutil

# Zip LoRA adapters
shutil.make_archive("baseline_3_lora", 'zip', "baseline_3_lora")
shutil.make_archive("proposed_lora", 'zip', "proposed_lora")

print("Exported:")
print("  - baseline_3_lora.zip")
print("  - proposed_lora.zip")
print("\nDownload từ Kaggle Output panel bên phải")

# ============================================================
# CELL 10: (Optional) Push to HuggingFace
# ============================================================

# Uncomment nếu muốn push lên HF
# model.push_to_hub_merged("your-username/vlegal-gemma4-proposed", tokenizer, save_method="merged_16bit")
# model.push_to_hub("your-username/vlegal-gemma4-proposed-lora", tokenizer)
