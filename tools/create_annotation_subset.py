#!/usr/bin/env python3
"""
Create annotation subset from VLegal-Bench tasks.

Samples 200-300 entries per task from 6 selected tasks for reliability annotation.
Supports stratified sampling for MC tasks to maintain answer distribution.

Usage:
    python tools/create_annotation_subset.py --output_dir annotations --samples_per_task 250
"""

import json
import os
import argparse
import random
from collections import Counter


# Selected tasks for annotation
ANNOTATION_TASKS = {
    "1.4": {"type": "mc", "focus": "citation_grounding", "file": "1.4/1_4.jsonl"},
    "2.4": {"type": "mc", "focus": "reliability", "file": "2.4/2_4.jsonl"},
    "3.2": {"type": "mc", "focus": "temporal_validity", "file": "3.2/3_2.jsonl"},
    "3.3": {"type": "mc", "focus": "citation_evidence", "file": "3.3/3_3.jsonl"},
    "4.1": {"type": "gen", "focus": "citation_temporal", "file": "4.1/4_1.jsonl"},
    "4.3": {"type": "gen", "focus": "citation_abstention", "file": "4.3/4_3.jsonl"},
}


def load_jsonl(path: str) -> list:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def stratified_sample_mc(data: list, n: int, seed: int = 42) -> list:
    """Stratified sampling for MC tasks - maintain answer distribution."""
    random.seed(seed)

    # Group by ground_truth
    groups = {}
    for item in data:
        gt = item.get('ground_truth', item.get('answer', 'unknown'))
        gt_str = str(gt).strip()
        if gt_str not in groups:
            groups[gt_str] = []
        groups[gt_str].append(item)

    # Calculate proportional allocation
    total = len(data)
    sampled = []
    remaining = n

    for gt_str, items in sorted(groups.items()):
        proportion = len(items) / total
        alloc = max(1, round(proportion * n))
        alloc = min(alloc, len(items), remaining)
        sampled.extend(random.sample(items, alloc))
        remaining -= alloc

    # If we still need more, sample from remaining
    if remaining > 0:
        already_ids = {id(s) for s in sampled}
        pool = [item for item in data if id(item) not in already_ids]
        if pool:
            extra = random.sample(pool, min(remaining, len(pool)))
            sampled.extend(extra)

    # Shuffle to avoid grouped ordering
    random.shuffle(sampled)
    return sampled[:n]


def sample_gen(data: list, n: int, seed: int = 42) -> list:
    """Simple random sampling for generation tasks."""
    random.seed(seed)
    if n >= len(data):
        return data
    return random.sample(data, n)


def create_subset(data: list, task_id: str, task_info: dict, n: int, seed: int = 42) -> list:
    """Create annotated subset for a task."""
    if task_info["type"] == "mc":
        sampled = stratified_sample_mc(data, n, seed)
    else:
        sampled = sample_gen(data, n, seed)

    # Add sample IDs
    for i, item in enumerate(sampled):
        item['sample_id'] = f"{task_id}_{i:04d}"
        item['task'] = task_id
        item['annotation_focus'] = task_info["focus"]

    return sampled


def save_jsonl(data: list, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description="Create annotation subset")
    parser.add_argument("--output_dir", type=str, default="annotations",
                        help="Output directory for annotation files")
    parser.add_argument("--samples_per_task", type=int, default=250,
                        help="Number of samples per task")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    summary = {}

    for task_id, task_info in ANNOTATION_TASKS.items():
        file_path = task_info["file"]
        print(f"\n--- Task {task_id} ({task_info['focus']}) ---")

        if not os.path.exists(file_path):
            print(f"  [SKIP] File not found: {file_path}")
            continue

        data = load_jsonl(file_path)
        print(f"  Total samples: {len(data)}")

        n = min(args.samples_per_task, len(data))
        subset = create_subset(data, task_id, task_info, n, args.seed)

        # Show distribution for MC tasks
        if task_info["type"] == "mc":
            gt_counter = Counter(str(s.get('ground_truth', '')) for s in subset)
            print(f"  Sampled: {len(subset)} (distribution: {dict(gt_counter)})")
        else:
            print(f"  Sampled: {len(subset)}")

        # Save
        output_file = os.path.join(args.output_dir, f"{task_id.replace('.', '_')}_subset.jsonl")
        save_jsonl(subset, output_file)
        print(f"  Saved to: {output_file}")

        summary[task_id] = {
            "total": len(data),
            "sampled": len(subset),
            "focus": task_info["focus"],
            "output": output_file
        }

    # Print summary
    print("\n" + "=" * 60)
    print("ANNOTATION SUBSET SUMMARY")
    print("=" * 60)
    total_sampled = 0
    for task_id, info in summary.items():
        print(f"  Task {task_id}: {info['sampled']}/{info['total']} samples ({info['focus']})")
        total_sampled += info['sampled']
    print(f"\n  Total: {total_sampled} samples for annotation")
    print(f"  Output directory: {args.output_dir}")
    print("\nNext steps:")
    print("  1. Review annotation guideline: docs/annotation_guideline.md")
    print("  2. Run annotation tool per task:")
    for task_id in summary:
        tid = task_id.replace('.', '_')
        print(f"     python tools/annotation_tool.py --input {args.output_dir}/{tid}_subset.jsonl --output {args.output_dir}/{tid}_annotated.jsonl --task {task_id}")


if __name__ == "__main__":
    main()
