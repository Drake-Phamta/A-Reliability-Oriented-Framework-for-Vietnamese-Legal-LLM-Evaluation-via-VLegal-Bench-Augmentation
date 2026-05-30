#!/usr/bin/env python3
"""
Comprehensive analysis of VLegal-Bench results.
Combines core metrics and reliability metrics into a unified view.
"""

import json
import os
import sys

VLEGAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODELS = ["gemma4_e4b-it-q8_0", "baseline_3", "proposed"]
MODEL_LABELS = {
    "gemma4_e4b-it-q8_0": "Gemma-4 (fewshot)",
    "baseline_3": "Baseline 3",
    "proposed": "Proposed"
}

TASK_CATEGORIES = {
    "Legal Knowledge": ["1.1", "1.2", "1.3", "1.4", "1.5"],
    "Legal Reasoning": ["2.1", "2.2", "2.3", "2.4", "2.5"],
    "Legal Text Gen": ["3.1", "3.2", "3.3", "3.4", "3.5"],
    "Judicial Analysis": ["4.1", "4.2", "4.3"],
    "Regulatory Compliance": ["5.1", "5.2", "5.4"]
}

MC_TASKS = ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2", "2.5", "3.1", "3.2", "3.3", "3.5", "5.1", "5.2", "5.4"]
GEN_TASKS = ["2.3", "4.1", "4.2", "4.3"]
TEXT_CLS_TASKS = ["2.4", "3.4"]


def load_core_metrics():
    path = os.path.join(VLEGAL_DIR, "core_metrics_results.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_reliability_results():
    path = os.path.join(VLEGAL_DIR, "reliability_results.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_core_metrics(core):
    """Analyze core metrics and generate summary."""
    print("=" * 80)
    print("CORE METRICS ANALYSIS")
    print("=" * 80)

    # MC Accuracy by category
    print("\n--- MC Accuracy by Category ---")
    for cat, tasks in TASK_CATEGORIES.items():
        mc_in_cat = [t for t in tasks if t in MC_TASKS]
        if not mc_in_cat:
            continue
        print(f"\n{cat}:")
        for model in MODELS:
            accs = []
            for t in mc_in_cat:
                if t in core.get(model, {}) and "accuracy" in core[model][t]:
                    accs.append(core[model][t]["accuracy"])
            if accs:
                avg = sum(accs) / len(accs)
                print(f"  {MODEL_LABELS[model]:20s}: {avg:.4f} (n={len(accs)})")

    # Overall MC average
    print("\n--- Overall MC Average ---")
    for model in MODELS:
        accs = []
        for t in MC_TASKS:
            if t in core.get(model, {}) and "accuracy" in core[model][t]:
                accs.append(core[model][t]["accuracy"])
        if accs:
            avg = sum(accs) / len(accs)
            print(f"  {MODEL_LABELS[model]:20s}: {avg:.4f} ({len(accs)} tasks)")

    # Generation tasks
    print("\n--- Generation Tasks (ROUGE-L) ---")
    for model in MODELS:
        print(f"\n  {MODEL_LABELS[model]}:")
        for t in GEN_TASKS:
            if t in core.get(model, {}) and "rouge_l" in core[model][t]:
                r = core[model][t]
                print(f"    Task {t}: BLEU={r.get('bleu', 0):.4f}, ROUGE-L={r['rouge_l']:.4f} (n={r.get('n', 0)})")

    # Text classification
    print("\n--- Text Classification ---")
    for model in MODELS:
        print(f"\n  {MODEL_LABELS[model]}:")
        for t in TEXT_CLS_TASKS:
            if t in core.get(model, {}) and "accuracy" in core[model][t]:
                r = core[model][t]
                print(f"    Task {t}: Acc={r['accuracy']:.4f} ({r['correct']}/{r['total']}), mismatch={r.get('format_mismatch', 0)}")

    # Best model per task
    print("\n--- Best Model per Task ---")
    for t in sorted(set(MC_TASKS + GEN_TASKS + TEXT_CLS_TASKS)):
        best_model = None
        best_val = -1
        for model in MODELS:
            if t not in core.get(model, {}):
                continue
            r = core[model][t]
            if "accuracy" in r:
                val = r["accuracy"]
            elif "rouge_l" in r:
                val = r["rouge_l"]
            else:
                continue
            if val > best_val:
                best_val = val
                best_model = model
        if best_model:
            print(f"  Task {t}: {MODEL_LABELS[best_model]} ({best_val:.4f})")


def analyze_reliability(rel):
    """Analyze reliability metrics."""
    print("\n" + "=" * 80)
    print("RELIABILITY METRICS ANALYSIS")
    print("=" * 80)

    if not rel:
        print("No reliability results found.")
        return

    for mode in ["baseline_3", "proposed"]:
        if mode not in rel:
            continue
        print(f"\n--- {MODEL_LABELS.get(mode, mode)} ---")
        mode_data = rel[mode]

        metrics_summary = {
            "CitAcc_doc": [], "CitAcc_art": [], "CitAcc_cls": [],
            "RAS": [], "RAR": [], "ESR": [], "UCR": [], "AbsAcc": []
        }

        for task, data in mode_data.items():
            if "error" in data:
                print(f"  Task {task}: ERROR - {data['error']}")
                continue

            print(f"  Task {task}:")
            print(f"    CitAcc (doc/art/cls): {data.get('CitAcc_document', 0):.4f} / {data.get('CitAcc_article', 0):.4f} / {data.get('CitAcc_clause', 0):.4f}")
            print(f"    RAS={data.get('RAS', 0):.4f}, RAR={data.get('RAR', 0):.4f}")
            print(f"    ESR={data.get('ESR', 0):.4f}, UCR={data.get('UCR', 0):.4f}")
            print(f"    AbsAcc={data.get('AbsAcc', 0):.4f}")

            for key in metrics_summary:
                val = data.get(key.replace("CitAcc_doc", "CitAcc_document").replace("CitAcc_art", "CitAcc_article").replace("CitAcc_cls", "CitAcc_clause"), 0)
                metrics_summary[key].append(val)

        # Averages
        print(f"\n  Averages:")
        for key, vals in metrics_summary.items():
            if vals:
                print(f"    {key}: {sum(vals)/len(vals):.4f}")


def main():
    core = load_core_metrics()
    rel = load_reliability_results()

    if core:
        analyze_core_metrics(core)
    else:
        print("No core metrics found. Run calculate_core_metrics_v2.py first.")

    if rel:
        analyze_reliability(rel)
    else:
        print("\nNo reliability results found. Run calculate_all_metrics.py after inference completes.")

    # Check for new reliability inference files
    print("\n" + "=" * 80)
    print("RELIABILITY INFERENCE STATUS")
    print("=" * 80)
    for task in ["1.4", "1.5", "3.1", "4.1", "4.2"]:
        task_name = task.replace(".", "_")
        for mode in ["baseline_3", "proposed"]:
            path = os.path.join(VLEGAL_DIR, task, f"{task_name}_llm_test_results_{mode}_reliability.json")
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  {task} ({mode}): {size:,} bytes - READY")
            else:
                print(f"  {task} ({mode}): NOT FOUND")


if __name__ == "__main__":
    main()
