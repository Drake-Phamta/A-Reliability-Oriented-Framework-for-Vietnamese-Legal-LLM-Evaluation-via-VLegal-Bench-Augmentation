#!/usr/bin/env python3
"""
Fine-tune Gemma 4 E4B for VLegal-Bench
Uses standard transformers + peft + trl (no unsloth)
Optimized for RTX 3090 Ti (24GB VRAM)

Usage:
    python train.py --mode baseline_3
    python train.py --mode proposed
    python train.py --mode both
"""

import json
import os
import sys
import argparse
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

DATA_DIR = "D:/Hunganh/vlegal-finetune/data"
OUTPUT_DIR = "D:/Hunganh/vlegal-finetune/output"
MODEL_NAME = "google/gemma-4-E4B-it"

ALL_TASKS = [
    "1.1","1.2","1.3","1.4","1.5",
    "2.1","2.2","2.3","2.4","2.5",
    "3.1","3.2","3.3","3.4","3.5",
    "4.1","4.2","4.3",
    "5.1","5.2","5.3","5.4",
]

ANNOTATED_TASKS = ["1.4", "1.5", "3.1", "3.3", "4.1", "4.2"]

TRAINING_CONFIG = {
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 4,
    "warmup_steps": 100,
    "num_train_epochs": 3,
    "learning_rate": 2e-4,
    "logging_steps": 10,
    "optim": "adamw_8bit",
    "weight_decay": 0.001,
    "lr_scheduler_type": "linear",
    "seed": 3407,
    "save_steps": 500,
    "save_total_limit": 2,
    "max_seq_length": 2048,
}

LORA_CONFIG = {
    "r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "bias": "none",
}


# ============================================================
# DATA LOADING
# ============================================================

def load_jsonl(path):
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def find_task_file(task):
    tid = task.replace(".", "_")
    patterns = [
        f"{DATA_DIR}/{task}/{tid}.jsonl",
        f"{DATA_DIR}/{tid}.jsonl",
    ]
    for p in patterns:
        if os.path.exists(p):
            return p
    task_dir = f"{DATA_DIR}/{task}"
    if os.path.exists(task_dir):
        for f in os.listdir(task_dir):
            if f.endswith(".jsonl") and "annotated" not in f and "result" not in f:
                return f"{task_dir}/{f}"
    return None


def find_annotated_file(task):
    tid = task.replace(".", "_")
    patterns = [
        f"{DATA_DIR}/annotated/{tid}_annotated.jsonl",
        f"{DATA_DIR}/{tid}_annotated.jsonl",
    ]
    for p in patterns:
        if os.path.exists(p):
            return p
    return None


def load_all_data():
    task_data = {}
    for task in ALL_TASKS:
        path = find_task_file(task)
        if path:
            task_data[task] = load_jsonl(path)
            logger.info(f"  Task {task}: {len(task_data[task])} samples")

    annotations = {}
    for task in ANNOTATED_TASKS:
        path = find_annotated_file(task)
        if path:
            raw = load_jsonl(path)
            for item in raw:
                sid = item.get("sample_id", "")
                if sid:
                    annotations[sid] = item
            logger.info(f"  Annotation {task}: {len(raw)} samples")

    total = sum(len(v) for v in task_data.values())
    logger.info(f"Total: {total} samples, {len(annotations)} annotated")
    return task_data, annotations


# ============================================================
# DATA FORMATTING
# ============================================================

def build_reasoning_response(ground_truth, annotation=None):
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
            parts.append(f"Căn cứ: {str(cit['evidence_passage'])[:200]}")
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


def format_example(item, task, annotation=None, include_reasoning=False):
    instruction = item.get("instruction", "")
    question = item.get("question", item.get("description", item.get("content", "")))
    answers = item.get("answers", "")
    ground_truth = str(item.get("ground_truth", item.get("answer", "")))

    user_text = f"{instruction}\n{question}".strip()
    if answers:
        user_text += f"\n{answers}"

    if include_reasoning:
        response = build_reasoning_response(ground_truth, annotation)
    else:
        response = ground_truth

    return {"text": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{response}<|eot_id|>"}


def prepare_dataset(task_data, annotations, mode="baseline_3"):
    from datasets import Dataset
    include_reasoning = (mode == "proposed")
    examples = []
    for task in ALL_TASKS:
        if task not in task_data:
            continue
        for item in task_data[task]:
            sid = item.get("sample_id", "")
            annotation = annotations.get(sid) if sid else None
            ex = format_example(item, task, annotation, include_reasoning)
            examples.append(ex)
    dataset = Dataset.from_list(examples)
    logger.info(f"Dataset ({mode}): {len(dataset)} examples")
    return dataset


# ============================================================
# MODEL SETUP
# ============================================================

def setup_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, TaskType

    logger.info(f"Loading model: {MODEL_NAME}")
    start = time.time()

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )

    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"]

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules,
        **LORA_CONFIG,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    elapsed = time.time() - start
    logger.info(f"Model loaded in {elapsed:.0f}s")
    logger.info(f"VRAM: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")

    return model, tokenizer


# ============================================================
# TRAINING
# ============================================================

def train_model(model, tokenizer, dataset, mode):
    import torch
    from transformers import TrainingArguments
    from trl import SFTTrainer, SFTConfig

    output_dir = f"{OUTPUT_DIR}/{mode}"
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Starting training: {mode}")
    logger.info(f"  Samples: {len(dataset)}")
    logger.info(f"  Output: {output_dir}")

    training_args = SFTConfig(
        dataset_text_field="text",
        output_dir=output_dir,
        per_device_train_batch_size=TRAINING_CONFIG["per_device_train_batch_size"],
        gradient_accumulation_steps=TRAINING_CONFIG["gradient_accumulation_steps"],
        warmup_steps=TRAINING_CONFIG["warmup_steps"],
        num_train_epochs=TRAINING_CONFIG["num_train_epochs"],
        learning_rate=TRAINING_CONFIG["learning_rate"],
        logging_steps=TRAINING_CONFIG["logging_steps"],
        optim=TRAINING_CONFIG["optim"],
        weight_decay=TRAINING_CONFIG["weight_decay"],
        lr_scheduler_type=TRAINING_CONFIG["lr_scheduler_type"],
        seed=TRAINING_CONFIG["seed"],
        save_steps=TRAINING_CONFIG["save_steps"],
        save_total_limit=TRAINING_CONFIG["save_total_limit"],
        max_seq_length=TRAINING_CONFIG["max_seq_length"],
        fp16=True,
        report_to="none",
        remove_unused_columns=False,
        gradient_checkpointing=True,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )

    start = time.time()
    trainer_stats = trainer.train()
    elapsed = time.time() - start

    save_dir = f"{output_dir}/final"
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)

    logger.info(f"Training complete: {mode}")
    logger.info(f"  Time: {elapsed/60:.1f} min")
    logger.info(f"  Saved to: {save_dir}")

    return trainer_stats, save_dir


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True,
                        choices=["baseline_3", "proposed", "both"])
    args = parser.parse_args()

    logger.info("="*60)
    logger.info(f"VLegal Fine-tune: {args.mode}")
    logger.info("="*60)

    logger.info("Loading data...")
    task_data, annotations = load_all_data()

    if args.mode in ["baseline_3", "both"]:
        logger.info("\n" + "="*60)
        logger.info("BASELINE 3: LoRA without reliability data")
        logger.info("="*60)
        model, tokenizer = setup_model()
        dataset = prepare_dataset(task_data, annotations, "baseline_3")
        train_model(model, tokenizer, dataset, "baseline_3")
        del model, tokenizer
        import torch
        torch.cuda.empty_cache()

    if args.mode in ["proposed", "both"]:
        logger.info("\n" + "="*60)
        logger.info("PROPOSED: LoRA with reliability annotations")
        logger.info("="*60)
        model, tokenizer = setup_model()
        dataset = prepare_dataset(task_data, annotations, "proposed")
        train_model(model, tokenizer, dataset, "proposed")

    logger.info("\n" + "="*60)
    logger.info("ALL TRAINING COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()
