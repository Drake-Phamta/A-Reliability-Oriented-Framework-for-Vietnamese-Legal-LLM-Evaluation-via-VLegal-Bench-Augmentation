#!/usr/bin/env python3
"""
Progress Tracker for VLegal-Bench Paper

Shows overall progress across all workstreams:
- Experiments (6 systems × 22 tasks)
- Annotations (6 tasks × 2 annotators)
- Paper sections
- Tables & Figures

Usage:
    python tools/progress.py
    python tools/progress.py --json  # Machine-readable output
"""

import json
import os
import sys
import argparse
from datetime import datetime

# Fix UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


ALL_TASKS = [
    "1.1", "1.2", "1.3", "1.4", "1.5",
    "2.1", "2.2", "2.3", "2.4", "2.5",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.1", "4.2", "4.3",
    "5.1", "5.2", "5.3", "5.4",
]

SYSTEMS = ["baseline_1a", "baseline_1b", "baseline_2a", "baseline_2b", "baseline_3", "proposed"]
ANNOTATION_TASKS = ["1.4", "2.4", "3.2", "3.3", "4.1", "4.3"]

PAPER_SECTIONS = {
    "Section 1: Introduction": True,
    "Section 2: Related Work": False,
    "Section 3: Proposed Framework": True,
    "Section 4.1: Dataset & Annotation": False,
    "Section 4.2: Baselines & Implementation": False,
    "Section 4.3: Evaluation Metrics": True,
    "Section 5.1: Core Benchmark Results": False,
    "Section 5.2: Reliability Metrics Results": False,
    "Section 5.3: Ablation Study": False,
    "Section 5.4: Case Studies": False,
    "Section 6: Discussion": False,
    "Section 7: Conclusion": True,
    "References": True,
    "Figure 1: Framework Diagram": True,
    "Table 1: Dataset Statistics": False,
    "Table 2: Core Benchmark": False,
    "Table 3: Reliability Metrics": False,
    "Table 4: Ablation Study": False,
}


def check_experiments(results_dir: str) -> dict:
    """Check experiment completion status."""
    status = {}
    for system in SYSTEMS:
        system_status = {}
        system_dir = os.path.join(results_dir, system)
        if os.path.isdir(system_dir):
            for model in os.listdir(system_dir):
                model_dir = os.path.join(system_dir, model)
                if os.path.isdir(model_dir):
                    completed = []
                    for task in ALL_TASKS:
                        task_id = task.replace(".", "_")
                        result_file = os.path.join(model_dir, f"{task_id}_results.jsonl")
                        if os.path.exists(result_file) and os.path.getsize(result_file) > 0:
                            completed.append(task)
                    system_status[model] = {
                        "completed": len(completed),
                        "total": len(ALL_TASKS),
                        "tasks": completed,
                    }
        status[system] = system_status
    return status


def check_annotations(annotations_dir: str) -> dict:
    """Check annotation completion status."""
    status = {}
    for task in ANNOTATION_TASKS:
        task_id = task.replace(".", "_")

        # Check subset
        subset_file = os.path.join(annotations_dir, f"{task_id}_subset.jsonl")
        subset_size = 0
        if os.path.exists(subset_file):
            with open(subset_file, 'r', encoding='utf-8') as f:
                subset_size = sum(1 for line in f if line.strip())

        # Check annotated files
        annotators = {}
        for f in os.listdir(annotations_dir):
            if f.startswith(f"{task_id}_annotated") and f.endswith(".jsonl"):
                path = os.path.join(annotations_dir, f)
                with open(path, 'r', encoding='utf-8') as fh:
                    count = sum(1 for line in fh if line.strip())
                annotators[f] = count

        status[task] = {
            "subset_size": subset_size,
            "annotators": annotators,
            "total_annotated": sum(annotators.values()),
        }

    return status


def check_paper() -> dict:
    """Check paper section completion."""
    return PAPER_SECTIONS


def progress_bar(current: int, total: int, width: int = 20) -> str:
    """Create a text progress bar."""
    if total == 0:
        return "[" + "?" * width + "]"
    filled = int(width * current / total)
    bar = "#" * filled + "-" * (width - filled)
    pct = current / total * 100
    return f"[{bar}] {current}/{total} ({pct:.0f}%)"


def print_report(experiments: dict, annotations: dict, paper: dict):
    """Print full progress report."""
    print()
    print("=" * 60)
    print("  VLegal-Bench Paper Progress Report")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Experiments
    print("\n  EXPERIMENTS")
    print("  " + "-" * 50)
    total_done = 0
    total_expected = 0
    for system in SYSTEMS:
        sys_data = experiments.get(system, {})
        if not sys_data:
            print(f"  {system:<20} not started")
            total_expected += len(ALL_TASKS)
            continue
        for model, info in sys_data.items():
            done = info["completed"]
            total = info["total"]
            total_done += done
            total_expected += total
            model_short = model.split("/")[-1][:20]
            print(f"  {system:<20} {model_short:<20} {progress_bar(done, total)}")

    if total_expected > 0:
        print(f"\n  Overall: {progress_bar(total_done, total_expected)}")

    # Annotations
    print("\n  ANNOTATIONS")
    print("  " + "-" * 50)
    ann_total = 0
    ann_done = 0
    for task, info in annotations.items():
        subset = info["subset_size"]
        ann_total += subset * 2  # 2 annotators per sample
        for ann_file, count in info["annotators"].items():
            ann_done += count
        n_ann = len(info["annotators"])
        print(f"  Task {task}: {subset} samples, {n_ann} annotator(s) [{info['total_annotated']} annotations]")

    if ann_total > 0:
        print(f"\n  Overall: {progress_bar(ann_done, ann_total)}")

    # IAA
    iaa_file = "annotations/iaa_results.json"
    if os.path.exists(iaa_file):
        with open(iaa_file, 'r') as f:
            iaa = json.load(f)
        print(f"\n  IAA: computed ({len(iaa)} comparisons)")
    else:
        print(f"\n  IAA: not computed yet")

    # Paper
    print("\n  PAPER SECTIONS")
    print("  " + "-" * 50)
    done_count = 0
    total_count = len(paper)
    for section, done in paper.items():
        status = "DONE" if done else "TODO"
        print(f"  [{status}] {section}")
        if done:
            done_count += 1

    print(f"\n  Overall: {progress_bar(done_count, total_count)}")

    # Summary
    print("\n" + "=" * 60)
    exp_pct = total_done / total_expected * 100 if total_expected else 0
    ann_pct = ann_done / ann_total * 100 if ann_total else 0
    pap_pct = done_count / total_count * 100

    print(f"  SUMMARY")
    print(f"    Experiments:  {exp_pct:.0f}%")
    print(f"    Annotations:  {ann_pct:.0f}%")
    print(f"    Paper:        {pap_pct:.0f}%")

    # Blockers
    print(f"\n  BLOCKERS:")
    if exp_pct < 100:
        print(f"    - Experiments incomplete (need GPU + API key)")
    if ann_pct < 100:
        print(f"    - Annotations incomplete (need annotators)")
    if not paper.get("Section 2: Related Work", True):
        print(f"    - Section 2 (Related Work) not written")
    if not paper.get("Section 5.1: Core Benchmark Results", True):
        print(f"    - Section 5 (Results) needs experiment data")
    if exp_pct >= 50 and ann_pct >= 50:
        print(f"    - None! Ready to write results sections")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Track paper progress")
    parser.add_argument("--results_dir", type=str, default="experiments/results")
    parser.add_argument("--annotations_dir", type=str, default="annotations")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    experiments = check_experiments(args.results_dir)
    annotations = check_annotations(args.annotations_dir)
    paper = check_paper()

    if args.json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "experiments": experiments,
            "annotations": annotations,
            "paper": paper,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_report(experiments, annotations, paper)


if __name__ == "__main__":
    main()
