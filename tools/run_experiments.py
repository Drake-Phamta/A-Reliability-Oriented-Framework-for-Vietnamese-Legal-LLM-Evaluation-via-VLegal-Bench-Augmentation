#!/usr/bin/env python3
"""
Experiment Runner for VLegal-Bench Reliability Framework

Runs 6 experimental systems across 22 tasks:
  - Baseline 1a: zero-shot (standard prompt)
  - Baseline 1b: reasoning (<think>/<output> tags)
  - Baseline 2a: zero-shot + legal system prompt
  - Baseline 2b: reasoning + legal system prompt
  - Baseline 3:  LoRA fine-tuned (no reliability data)
  - Proposed:    LoRA fine-tuned (with reliability data)

Usage:
    # Run all systems
    python tools/run_experiments.py --model Qwen/Qwen2.5-7B-Instruct --all

    # Run specific system
    python tools/run_experiments.py --model Qwen/Qwen2.5-7B-Instruct --system baseline_1a

    # Run specific task
    python tools/run_experiments.py --model Qwen/Qwen2.5-7B-Instruct --system baseline_1b --task 1.4

    # Resume interrupted run
    python tools/run_experiments.py --model Qwen/Qwen2.5-7B-Instruct --system baseline_1b --resume
"""

import json
import os
import sys
import argparse
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference import VLLM
from src.evaluation import Metrics


# All 22 tasks
ALL_TASKS = [
    "1.1", "1.2", "1.3", "1.4", "1.5",
    "2.1", "2.2", "2.3", "2.4", "2.5",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.1", "4.2", "4.3",
    "5.1", "5.2", "5.3", "5.4",
]

# Experimental systems
SYSTEMS = {
    "baseline_1a": {
        "name": "Baseline 1a (Zero-shot)",
        "prompt_mode": "zero_shot",
        "legal_prompt": False,
        "finetuned": False,
        "checkpoint": None,
    },
    "baseline_1b": {
        "name": "Baseline 1b (Reasoning)",
        "prompt_mode": "reasoning",
        "legal_prompt": False,
        "finetuned": False,
        "checkpoint": None,
    },
    "baseline_2a": {
        "name": "Baseline 2a (Legal Zero-shot)",
        "prompt_mode": "zero_shot",
        "legal_prompt": True,
        "finetuned": False,
        "checkpoint": None,
    },
    "baseline_2b": {
        "name": "Baseline 2b (Legal Reasoning)",
        "prompt_mode": "reasoning",
        "legal_prompt": True,
        "finetuned": False,
        "checkpoint": None,
    },
    "baseline_3": {
        "name": "Baseline 3 (LoRA, no reliability)",
        "prompt_mode": "reasoning",
        "legal_prompt": True,
        "finetuned": True,
        "checkpoint": "experiments/models/baseline_3",
    },
    "proposed": {
        "name": "Proposed (LoRA + reliability)",
        "prompt_mode": "reliability",
        "legal_prompt": True,
        "finetuned": True,
        "checkpoint": "experiments/models/proposed",
    },
}

# Task dataset file mapping
TASK_FILES = {}
for task in ALL_TASKS:
    task_id = task.replace(".", "_")
    # Check for different file naming patterns
    TASK_FILES[task] = f"./{task}/{task_id}.jsonl"


def get_dataset_path(task: str) -> str:
    """Get the dataset path for a task, handling special cases."""
    task_id = task.replace(".", "_")
    base_path = f"./{task}"

    # Standard pattern
    standard = f"{base_path}/{task_id}.jsonl"
    if os.path.exists(standard):
        return standard

    # 5.3 special case
    if task == "5.3":
        path = f"{base_path}/{task_id}_legal_ethics_cases_reformatted.jsonl"
        if os.path.exists(path):
            return path

    # Look for any jsonl file
    if os.path.exists(base_path):
        for f in os.listdir(base_path):
            if f.endswith(".jsonl") and "result" not in f and "annotated" not in f and "subset" not in f:
                return f"{base_path}/{f}"

    return standard


def get_output_path(model: str, system: str, task: str) -> str:
    """Get the output path for experiment results."""
    model_safe = model.replace("/", "_")
    task_id = task.replace(".", "_")
    return f"experiments/results/{system}/{model_safe}/{task_id}_results.jsonl"


def is_completed(output_path: str) -> bool:
    """Check if a task has already been completed."""
    return os.path.exists(output_path) and os.path.getsize(output_path) > 0


def run_single_task(model: str, system: str, task: str, config: dict,
                    batch_size: int = 4, max_model_len: int = None,
                    delay: float = 0, base_url: str = None, api_key: str = None):
    """Run a single task with a single system."""
    dataset_path = get_dataset_path(task)
    if not os.path.exists(dataset_path):
        logging.warning(f"Dataset not found: {dataset_path}")
        return None

    output_path = get_output_path(model, system, task)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Determine model to use
    run_model = model
    if config["finetuned"] and config["checkpoint"]:
        checkpoint = config["checkpoint"]
        if os.path.exists(checkpoint):
            run_model = checkpoint
        else:
            logging.warning(f"Checkpoint not found: {checkpoint}, using base model")

    # Determine API config
    if base_url is None:
        base_url = os.getenv("HOST_NAME", "http://localhost:8000") + "/v1"
    if api_key is None:
        api_key = os.getenv("API_KEY", "not-needed")

    logging.info(f"[{system}] Task {task}: model={run_model}, mode={config['prompt_mode']}")

    vllm = VLLM(
        api_key=api_key,
        model=run_model,
        dataset_path=dataset_path,
        base_url=base_url,
        batch_size=batch_size,
        max_model_len=max_model_len or 4096,
        delay_between_requests=delay,
        prompt_mode=config["prompt_mode"],
    )

    asyncio.run(vllm.run())

    # Move output to experiment directory
    # The inference.py saves to task directory, we need to move it
    task_id = task.replace(".", "_")
    generated = f"./{task}/{task_id}_llm_test_results_{run_model.replace('/', '_')}.json"
    if os.path.exists(generated):
        import shutil
        shutil.move(generated, output_path)
        logging.info(f"[{system}] Task {task}: saved to {output_path}")
        return output_path
    else:
        logging.error(f"[{system}] Task {task}: output not found at {generated}")
        return None


def run_system(model: str, system: str, tasks: list, resume: bool = False,
               batch_size: int = 4, max_model_len: int = None,
               delay: float = 0, base_url: str = None, api_key: str = None):
    """Run all tasks for a single system."""
    config = SYSTEMS[system]
    logging.info(f"\n{'='*60}")
    logging.info(f"Running {config['name']}")
    logging.info(f"Model: {model}")
    logging.info(f"Tasks: {len(tasks)}")
    logging.info(f"{'='*60}")

    completed = 0
    skipped = 0
    failed = 0

    for task in tasks:
        output_path = get_output_path(model, system, task)

        if resume and is_completed(output_path):
            logging.info(f"[{system}] Task {task}: already completed, skipping")
            skipped += 1
            continue

        try:
            result = run_single_task(
                model=model, system=system, task=task, config=config,
                batch_size=batch_size, max_model_len=max_model_len,
                delay=delay, base_url=base_url, api_key=api_key
            )
            if result:
                completed += 1
            else:
                failed += 1
        except Exception as e:
            logging.error(f"[{system}] Task {task}: FAILED - {e}")
            failed += 1

    logging.info(f"[{system}] Done: {completed} completed, {skipped} skipped, {failed} failed")
    return completed, skipped, failed


def main():
    parser = argparse.ArgumentParser(description="VLegal-Bench Experiment Runner")
    parser.add_argument("--model", type=str, required=True,
                        help="Model name (e.g., Qwen/Qwen2.5-7B-Instruct)")
    parser.add_argument("--system", type=str, default=None,
                        choices=list(SYSTEMS.keys()),
                        help="Run specific system (default: all)")
    parser.add_argument("--all", action="store_true",
                        help="Run all systems")
    parser.add_argument("--task", type=str, default=None,
                        help="Run specific task (e.g., 1.4)")
    parser.add_argument("--tasks", type=str, default=None,
                        help="Comma-separated task list (e.g., 1.4,2.4,3.2)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already completed tasks")
    parser.add_argument("--batch_size", type=int, default=4,
                        help="Batch size for inference")
    parser.add_argument("--max_model_len", type=int, default=None,
                        help="Max model token length")
    parser.add_argument("--delay", type=float, default=0,
                        help="Delay between requests (seconds)")
    parser.add_argument("--base_url", type=str, default=None,
                        help="API base URL")
    parser.add_argument("--api_key", type=str, default=None,
                        help="API key")
    parser.add_argument("--dry_run", action="store_true",
                        help="Show what would be run without executing")
    args = parser.parse_args()

    # Setup logging
    log_dir = "experiments/logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe = args.model.replace("/", "_")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/{model_safe}_{timestamp}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Determine tasks
    if args.task:
        tasks = [args.task]
    elif args.tasks:
        tasks = [t.strip() for t in args.tasks.split(",")]
    else:
        tasks = ALL_TASKS

    # Determine systems
    if args.system:
        systems = [args.system]
    elif args.all:
        systems = list(SYSTEMS.keys())
    else:
        # Default: run baselines only (not fine-tuned)
        systems = ["baseline_1a", "baseline_1b", "baseline_2a", "baseline_2b"]

    # Dry run
    if args.dry_run:
        print("\nDRY RUN - Would execute:")
        for sys_name in systems:
            config = SYSTEMS[sys_name]
            print(f"\n  [{sys_name}] {config['name']}")
            print(f"    Prompt mode: {config['prompt_mode']}")
            print(f"    Legal prompt: {config['legal_prompt']}")
            print(f"    Fine-tuned: {config['finetuned']}")
            print(f"    Tasks: {len(tasks)}")
            for task in tasks:
                output = get_output_path(args.model, sys_name, task)
                status = "DONE" if is_completed(output) else "PENDING"
                print(f"      {task}: {status}")
        return

    # Run
    start_time = time.time()
    summary = {}

    for sys_name in systems:
        config = SYSTEMS[sys_name]
        completed, skipped, failed = run_system(
            model=args.model,
            system=sys_name,
            tasks=tasks,
            resume=args.resume,
            batch_size=args.batch_size,
            max_model_len=args.max_model_len,
            delay=args.delay,
            base_url=args.base_url,
            api_key=args.api_key,
        )
        summary[sys_name] = {"completed": completed, "skipped": skipped, "failed": failed}

    elapsed = time.time() - start_time

    # Print summary
    logging.info(f"\n{'='*60}")
    logging.info(f"EXPERIMENT SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"Model: {args.model}")
    logging.info(f"Tasks: {len(tasks)}")
    logging.info(f"Time: {elapsed/60:.1f} minutes")
    logging.info(f"")
    for sys_name, stats in summary.items():
        logging.info(f"  {sys_name}: {stats['completed']} ok, {stats['skipped']} skip, {stats['failed']} fail")

    # Save summary
    summary_path = f"experiments/results/{model_safe}_{timestamp}_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            "model": args.model,
            "systems": summary,
            "tasks": tasks,
            "elapsed_seconds": elapsed,
            "timestamp": timestamp,
        }, f, ensure_ascii=False, indent=2)
    logging.info(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
