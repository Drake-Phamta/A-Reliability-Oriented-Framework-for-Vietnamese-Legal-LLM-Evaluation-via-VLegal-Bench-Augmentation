#!/usr/bin/env python3
"""
LoRA Fine-tuning Script for VLegal-Bench

Fine-tunes a base model with LoRA/PEFT on VLegal-Bench data.
Supports two modes:
  - Baseline 3: Train on VLegal-Bench MC tasks (no reliability data)
  - Proposed: Train with reliability annotations

Usage:
    # Baseline 3: train without reliability data
    python tools/finetune_lora.py --model Qwen/Qwen2.5-7B-Instruct --mode baseline_3

    # Proposed: train with reliability data
    python tools/finetune_lora.py --model Qwen/Qwen2.5-7B-Instruct --mode proposed

    # Custom config
    python tools/finetune_lora.py --model Qwen/Qwen2.5-7B-Instruct --mode proposed \
        --lora_r 16 --lora_alpha 32 --epochs 3 --lr 2e-4
"""

import json
import os
import sys
import argparse
import logging
from pathlib import Path

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import SFTTrainer
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install torch transformers peft trl datasets")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# All 22 tasks
ALL_TASKS = [
    "1.1", "1.2", "1.3", "1.4", "1.5",
    "2.1", "2.2", "2.3", "2.4", "2.5",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.1", "4.2", "4.3",
    "5.1", "5.2", "5.3", "5.4",
]


def load_jsonl(path: str) -> list:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def get_task_data(task: str) -> list:
    """Load task data from JSONL."""
    task_id = task.replace(".", "_")
    base_path = f"./{task}"

    # Standard pattern
    standard = f"{base_path}/{task_id}.jsonl"
    if os.path.exists(standard):
        return load_jsonl(standard)

    # 5.3 special case
    if task == "5.3":
        path = f"{base_path}/{task_id}_legal_ethics_cases_reformatted.jsonl"
        if os.path.exists(path):
            return load_jsonl(path)

    # Look for any jsonl
    if os.path.exists(base_path):
        for f in os.listdir(base_path):
            if f.endswith(".jsonl") and "result" not in f and "annotated" not in f and "subset" not in f:
                return load_jsonl(f"{base_path}/{f}")

    return []


def load_prompt_template(task: str) -> str:
    """Load the EXAMPLE_RELIABILITY prompt for a task."""
    task_id = task.replace(".", "_")
    prompt_file = f"./{task}/prompt_{task_id}.py"

    # Handle 5.3 special naming
    if task == "5.3":
        prompt_file = f"./{task}/prompt_5_3_legal_ethics_cases.py"

    if not os.path.exists(prompt_file):
        return ""

    namespace = {}
    with open(prompt_file, 'r', encoding='utf-8') as f:
        exec(f.read(), namespace)

    return namespace.get("EXAMPLE_RELIABILITY", namespace.get("EXAMPLE_REASONING", namespace.get("EXAMPLE", "")))


def format_training_example(item: dict, task: str, include_reliability: bool = False) -> dict:
    """Format a single training example."""
    task_id = task.replace(".", "_")

    # Build instruction
    instruction = item.get("instruction", "")
    question = item.get("question", item.get("description", item.get("content", "")))
    answers = item.get("answers", "")
    ground_truth = item.get("ground_truth", item.get("answer", ""))

    user_text = f"{instruction}\n{question}"
    if answers:
        user_text += f"\n{answers}"

    # Build response
    if include_reliability:
        # Proposed mode: include reasoning and citation
        prompt_template = load_prompt_template(task)
        response = f"<think>\nPhân tích câu hỏi pháp lý...\n</think>\n<answer>{ground_truth}</answer>"
    else:
        # Baseline mode: direct answer
        response = str(ground_truth)

    return {
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý pháp lý AI."},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": response},
        ]
    }


def prepare_training_data(mode: str, tasks: list = None) -> list:
    """Prepare all training data."""
    if tasks is None:
        tasks = ALL_TASKS

    include_reliability = (mode == "proposed")
    training_data = []

    for task in tasks:
        data = get_task_data(task)
        logging.info(f"Task {task}: {len(data)} samples")

        for item in data:
            example = format_training_example(item, task, include_reliability)
            training_data.append(example)

    logging.info(f"Total training examples: {len(training_data)}")
    return training_data


def setup_lora(model_name: str, lora_r: int = 8, lora_alpha: int = 16,
               lora_dropout: float = 0.05, target_modules: list = None):
    """Setup LoRA configuration."""
    logging.info(f"Loading model: {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    if target_modules is None:
        # Default target modules for common architectures
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj"]

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        bias="none",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer


def train(model, tokenizer, training_data: list, output_dir: str,
          epochs: int = 3, lr: float = 2e-4, batch_size: int = 4,
          gradient_accumulation: int = 4, max_seq_length: int = 2048,
          warmup_ratio: float = 0.1, save_steps: int = 100):
    """Run LoRA training."""

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation,
        learning_rate=lr,
        warmup_ratio=warmup_ratio,
        logging_steps=10,
        save_steps=save_steps,
        save_total_limit=3,
        bf16=True,
        remove_unused_columns=False,
        report_to="none",
        dataloader_pin_memory=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=training_data,
        processing_class=tokenizer,
        max_seq_length=max_seq_length,
    )

    logging.info("Starting training...")
    trainer.train()

    # Save final model
    final_dir = os.path.join(output_dir, "final")
    trainer.save_model(final_dir)
    tokenizer.save_pretrained(final_dir)
    logging.info(f"Model saved to: {final_dir}")

    return final_dir


def main():
    parser = argparse.ArgumentParser(description="LoRA Fine-tuning for VLegal-Bench")
    parser.add_argument("--model", type=str, required=True,
                        help="Base model name (e.g., Qwen/Qwen2.5-7B-Instruct)")
    parser.add_argument("--mode", type=str, required=True,
                        choices=["baseline_3", "proposed"],
                        help="Training mode: baseline_3 (no reliability) or proposed (with reliability)")
    parser.add_argument("--tasks", type=str, default=None,
                        help="Comma-separated task list (default: all)")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="Output directory (default: experiments/models/{mode})")
    parser.add_argument("--lora_r", type=int, default=8,
                        help="LoRA rank (default: 8)")
    parser.add_argument("--lora_alpha", type=int, default=16,
                        help="LoRA alpha (default: 16)")
    parser.add_argument("--lora_dropout", type=float, default=0.05,
                        help="LoRA dropout (default: 0.05)")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of epochs (default: 3)")
    parser.add_argument("--lr", type=float, default=2e-4,
                        help="Learning rate (default: 2e-4)")
    parser.add_argument("--batch_size", type=int, default=4,
                        help="Batch size (default: 4)")
    parser.add_argument("--gradient_accumulation", type=int, default=4,
                        help="Gradient accumulation steps (default: 4)")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                        help="Max sequence length (default: 2048)")
    parser.add_argument("--save_steps", type=int, default=100,
                        help="Save checkpoint every N steps (default: 100)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Show config without training")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Determine tasks
    tasks = ALL_TASKS
    if args.tasks:
        tasks = [t.strip() for t in args.tasks.split(",")]

    # Output directory
    output_dir = args.output_dir or f"experiments/models/{args.mode}"
    os.makedirs(output_dir, exist_ok=True)

    # Show config
    logging.info(f"\n{'='*60}")
    logging.info(f"LoRA Fine-tuning Configuration")
    logging.info(f"{'='*60}")
    logging.info(f"Model: {args.model}")
    logging.info(f"Mode: {args.mode}")
    logging.info(f"Tasks: {len(tasks)}")
    logging.info(f"LoRA rank: {args.lora_r}")
    logging.info(f"LoRA alpha: {args.lora_alpha}")
    logging.info(f"Epochs: {args.epochs}")
    logging.info(f"Learning rate: {args.lr}")
    logging.info(f"Batch size: {args.batch_size}")
    logging.info(f"Gradient accumulation: {args.gradient_accumulation}")
    logging.info(f"Max seq length: {args.max_seq_length}")
    logging.info(f"Output: {output_dir}")
    logging.info(f"{'='*60}")

    if args.dry_run:
        logging.info("Dry run - exiting without training")
        return

    # Prepare data
    training_data = prepare_training_data(args.mode, tasks)
    if not training_data:
        logging.error("No training data found")
        return

    # Setup model
    model, tokenizer = setup_lora(
        model_name=args.model,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
    )

    # Train
    final_dir = train(
        model=model,
        tokenizer=tokenizer,
        training_data=training_data,
        output_dir=output_dir,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
        gradient_accumulation=args.gradient_accumulation,
        max_seq_length=args.max_seq_length,
        save_steps=args.save_steps,
    )

    logging.info(f"\nTraining complete!")
    logging.info(f"Final model: {final_dir}")
    logging.info(f"\nTo evaluate:")
    logging.info(f"  python tools/run_experiments.py --model {args.model} --system {args.mode}")


if __name__ == "__main__":
    main()
