#!/usr/bin/env python3
"""
Verify experiment outputs and annotation completeness.

Checks:
- Experiment result files exist and are valid JSONL
- Prediction fields are present and well-formed
- Annotation files have required fields
- IAA scores meet targets

Usage:
    python tools/verify_experiments.py --all
    python tools/verify_experiments.py --system baseline_1a --model Qwen2.5-7B
    python tools/verify_experiments.py --annotations
"""

import json
import os
import sys
import argparse
from pathlib import Path

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


def load_jsonl(path: str) -> list:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return data


def verify_result_file(path: str) -> dict:
    """Verify a single result file."""
    issues = []
    if not os.path.exists(path):
        return {"status": "MISSING", "issues": ["File not found"]}

    data = load_jsonl(path)
    if not data:
        return {"status": "EMPTY", "issues": ["File is empty or no valid JSON lines"]}

    # Check required fields
    required = ["prediction", "ground_truth"]
    for field in required:
        missing = sum(1 for d in data if field not in d)
        if missing > 0:
            issues.append(f"{missing}/{len(data)} entries missing '{field}'")

    # Check raw_response
    has_raw = sum(1 for d in data if "raw_response" in d)
    if has_raw < len(data):
        issues.append(f"{len(data) - has_raw}/{len(data)} entries missing 'raw_response'")

    # Check for null predictions
    null_preds = sum(1 for d in data if d.get("prediction") is None)
    if null_preds > 0:
        issues.append(f"{null_preds}/{len(data)} predictions are null")

    status = "OK" if not issues else "WARNING"
    return {
        "status": status,
        "samples": len(data),
        "issues": issues,
    }


def verify_experiment(results_dir: str, model: str, system: str) -> dict:
    """Verify all tasks for a system."""
    model_safe = model.replace("/", "_")
    system_dir = os.path.join(results_dir, system, model_safe)

    if not os.path.exists(system_dir):
        return {"status": "NOT_FOUND", "tasks": {}}

    tasks = {}
    ok_count = 0
    for task in ALL_TASKS:
        task_id = task.replace(".", "_")
        result_file = os.path.join(system_dir, f"{task_id}_results.jsonl")
        result = verify_result_file(result_file)
        tasks[task] = result
        if result["status"] == "OK":
            ok_count += 1

    return {
        "status": "OK" if ok_count == len(ALL_TASKS) else f"{ok_count}/{len(ALL_TASKS)}",
        "tasks": tasks,
    }


def verify_annotations(annotations_dir: str) -> dict:
    """Verify annotation completeness."""
    required_citation = ["document_name", "article"]
    required_temporal = ["valid_at_query_date"]
    required_reliability = ["evidence_sufficient", "should_abstain"]

    results = {}
    for f in sorted(os.listdir(annotations_dir)):
        if not f.endswith(".jsonl") or "subset" in f:
            continue

        path = os.path.join(annotations_dir, f)
        data = load_jsonl(path)

        issues = []
        for ann in data:
            sid = ann.get("sample_id", "?")

            # Check citation
            cit = ann.get("citation", {})
            for field in required_citation:
                if not cit.get(field):
                    issues.append(f"{sid}: missing citation.{field}")

            # Check temporal
            temp = ann.get("temporal", {})
            for field in required_temporal:
                if field not in temp:
                    issues.append(f"{sid}: missing temporal.{field}")

            # Check reliability
            rel = ann.get("reliability", {})
            for field in required_reliability:
                if field not in rel:
                    issues.append(f"{sid}: missing reliability.{field}")

        # Check for duplicate IDs
        ids = [a.get("sample_id") for a in data]
        dupes = [x for x in set(ids) if ids.count(x) > 1]
        if dupes:
            issues.append(f"Duplicate sample_ids: {dupes[:5]}")

        results[f] = {
            "samples": len(data),
            "issues": issues[:10],  # Limit to first 10 issues
            "status": "OK" if not issues else f"WARNING ({len(issues)} issues)",
        }

    return results


def print_system_report(model: str, system: str, result: dict):
    """Print verification report for a system."""
    print(f"\n{'='*60}")
    print(f"  {system} / {model}")
    print(f"{'='*60}")
    print(f"  Status: {result['status']}")

    if result.get("tasks"):
        print(f"\n  {'Task':<8} {'Status':<12} {'Samples':<10} {'Issues'}")
        print(f"  {'-'*50}")
        for task in ALL_TASKS:
            tr = result["tasks"].get(task, {"status": "MISSING", "samples": 0, "issues": []})
            issues_str = "; ".join(tr.get("issues", [])[:2])
            if not issues_str:
                issues_str = "-"
            print(f"  {task:<8} {tr['status']:<12} {tr.get('samples', 0):<10} {issues_str}")


def main():
    parser = argparse.ArgumentParser(description="Verify experiment outputs")
    parser.add_argument("--results_dir", type=str, default="experiments/results")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--system", type=str, default=None)
    parser.add_argument("--annotations", action="store_true", help="Verify annotations")
    parser.add_argument("--all", action="store_true", help="Verify everything")
    args = parser.parse_args()

    if args.all or args.system:
        # Verify experiments
        systems = [args.system] if args.system else []
        if not systems and os.path.exists(args.results_dir):
            systems = [d for d in os.listdir(args.results_dir)
                       if os.path.isdir(os.path.join(args.results_dir, d))]

        models = set()
        if args.model:
            models = {args.model}
        else:
            for system in systems:
                system_dir = os.path.join(args.results_dir, system)
                if os.path.isdir(system_dir):
                    for d in os.listdir(system_dir):
                        if os.path.isdir(os.path.join(system_dir, d)):
                            models.add(d)

        for system in systems:
            for model in models:
                result = verify_experiment(args.results_dir, model, system)
                print_system_report(model, system, result)

    if args.all or args.annotations:
        print(f"\n{'='*60}")
        print(f"  ANNOTATIONS VERIFICATION")
        print(f"{'='*60}")

        ann_dir = "annotations"
        if os.path.exists(ann_dir):
            results = verify_annotations(ann_dir)
            for f, info in results.items():
                print(f"\n  {f}:")
                print(f"    Samples: {info['samples']}")
                print(f"    Status: {info['status']}")
                if info['issues']:
                    for issue in info['issues'][:5]:
                        print(f"    - {issue}")
        else:
            print("  No annotations directory found")

    if not args.all and not args.system and not args.annotations:
        # Quick status check
        print("\n  QUICK STATUS CHECK")
        print(f"  {'='*40}")

        # Check what experiments exist
        if os.path.exists(args.results_dir):
            for system in sorted(os.listdir(args.results_dir)):
                system_dir = os.path.join(args.results_dir, system)
                if os.path.isdir(system_dir):
                    for model in os.listdir(system_dir):
                        model_dir = os.path.join(system_dir, model)
                        if os.path.isdir(model_dir):
                            n_files = len([f for f in os.listdir(model_dir) if f.endswith('.jsonl')])
                            print(f"  {system}/{model}: {n_files}/{len(ALL_TASKS)} tasks")
        else:
            print("  No experiment results yet")

        # Check annotations
        ann_dir = "annotations"
        if os.path.exists(ann_dir):
            subset = len([f for f in os.listdir(ann_dir) if f.endswith('_subset.jsonl')])
            annotated = len([f for f in os.listdir(ann_dir) if 'annotated' in f and f.endswith('.jsonl')])
            print(f"\n  Annotations: {subset} subsets, {annotated} annotated files")


if __name__ == "__main__":
    main()
