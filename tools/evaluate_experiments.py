#!/usr/bin/env python3
"""
Evaluation Pipeline for VLegal-Bench Experiments

Computes core metrics and reliability metrics across all experimental systems.
Generates comparison tables for the paper.

Usage:
    # Evaluate all results
    python tools/evaluate_experiments.py --results_dir experiments/results --model Qwen2.5-7B

    # Evaluate specific system
    python tools/evaluate_experiments.py --results_dir experiments/results --system baseline_1b

    # Generate LaTeX tables
    python tools/evaluate_experiments.py --results_dir experiments/results --latex
"""

import json
import os
import sys
import argparse
import logging
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation import task_type_mapping, Metrics
from src.reliability_metrics import ReliabilityMetrics


# Task categories for grouping
TASK_CATEGORIES = {
    "1.x": ["1.1", "1.2", "1.3", "1.4", "1.5"],
    "2.x": ["2.1", "2.2", "2.3", "2.4", "2.5"],
    "3.x": ["3.1", "3.2", "3.3", "3.4", "3.5"],
    "4.x": ["4.1", "4.2", "4.3"],
    "5.x": ["5.1", "5.2", "5.3", "5.4"],
}

ALL_TASKS = [t for tasks in TASK_CATEGORIES.values() for t in tasks]


def load_jsonl(path: str) -> list:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def compute_core_metrics(result_path: str) -> dict:
    """Compute core metrics for a single result file."""
    try:
        metrics = Metrics(result_path)
        return metrics.eval()
    except Exception as e:
        logging.error(f"Error computing metrics for {result_path}: {e}")
        return {}


def compute_reliability_metrics(predictions: list, annotations: list) -> dict:
    """Compute reliability metrics on annotated subset."""
    try:
        rm = ReliabilityMetrics()
        return rm.eval_all(predictions, annotations)
    except Exception as e:
        logging.error(f"Error computing reliability metrics: {e}")
        return {}


def evaluate_system(results_dir: str, model: str, system: str) -> dict:
    """Evaluate all tasks for a single system."""
    model_safe = model.replace("/", "_")
    system_dir = os.path.join(results_dir, system, model_safe)

    if not os.path.exists(system_dir):
        logging.warning(f"System directory not found: {system_dir}")
        return {}

    results = {}
    for task in ALL_TASKS:
        task_id = task.replace(".", "_")
        result_file = os.path.join(system_dir, f"{task_id}_results.jsonl")

        if not os.path.exists(result_file):
            continue

        core = compute_core_metrics(result_file)
        results[task] = {"core": core, "file": result_file}

    return results


def load_annotations(annotations_dir: str) -> dict:
    """Load all annotation files."""
    annotations = {}
    if not os.path.exists(annotations_dir):
        return annotations

    for f in os.listdir(annotations_dir):
        if f.endswith("_annotated.jsonl"):
            task_id = f.replace("_annotated.jsonl", "").replace("_", ".")
            annotations[task_id] = load_jsonl(os.path.join(annotations_dir, f))

    return annotations


def compute_averages(results: dict) -> dict:
    """Compute average metrics across tasks."""
    task_metrics = defaultdict(list)

    for task, data in results.items():
        core = data.get("core", {})
        for metric, value in core.items():
            if isinstance(value, (int, float)):
                task_metrics[metric].append(value)

    averages = {}
    for metric, values in task_metrics.items():
        averages[metric] = sum(values) / len(values) if values else 0.0

    return averages


def compute_category_averages(results: dict) -> dict:
    """Compute averages per task category."""
    category_results = {}

    for category, tasks in TASK_CATEGORIES.items():
        cat_metrics = defaultdict(list)
        for task in tasks:
            if task in results:
                core = results[task].get("core", {})
                for metric, value in core.items():
                    if isinstance(value, (int, float)):
                        cat_metrics[metric].append(value)

        cat_avg = {}
        for metric, values in cat_metrics.items():
            cat_avg[metric] = sum(values) / len(values) if values else 0.0
        category_results[category] = cat_avg

    return category_results


def format_metric(value: float, metric_type: str = "accuracy") -> str:
    """Format a metric value for display."""
    if value is None:
        return "-"
    if metric_type in ["accuracy", "f1", "precision", "recall"]:
        return f"{value*100:.1f}"
    elif metric_type in ["bleu", "rouge"]:
        return f"{value*100:.2f}"
    else:
        return f"{value:.4f}"


def generate_latex_table2(all_results: dict) -> str:
    """Generate LaTeX table for core benchmark results."""
    systems = list(all_results.keys())
    categories = list(TASK_CATEGORIES.keys())

    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Core benchmark results across task categories.}")
    lines.append("\\label{tab:core_results}")
    lines.append("\\small")

    # Header
    header = "\\textbf{System}"
    for cat in categories:
        header += f" & {cat}"
    header += " & \\\\"
    lines.append("\\begin{tabular}{l" + "c" * (len(categories) + 1) + "}")
    lines.append("\\toprule")
    lines.append(header)
    lines.append("\\midrule")

    # Data rows
    for system in systems:
        results = all_results[system]
        cat_avgs = compute_category_averages(results)
        overall = compute_averages(results)

        row = system.replace("_", "\\_")
        for cat in categories:
            avg = cat_avgs.get(cat, {})
            # Use accuracy for MC tasks, ROUGE-L for gen tasks
            acc = avg.get("accuracy", avg.get("ROUGE", 0))
            row += f" & {format_metric(acc)}"
        row += f" & {format_metric(overall.get('accuracy', overall.get('ROUGE', 0)))} \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def generate_latex_table3(reliability_results: dict) -> str:
    """Generate LaTeX table for reliability metrics."""
    metrics = ["CitAcc", "RAS", "RAR", "ESR", "UCR", "AbsAcc"]
    systems = list(reliability_results.keys())

    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Reliability metrics on annotated subset.}")
    lines.append("\\label{tab:reliability_metrics}")
    lines.append("\\small")

    header = "\\textbf{System}"
    for m in metrics:
        header += f" & {m}"
    header += " \\\\"
    lines.append("\\begin{tabular}{l" + "c" * len(metrics) + "}")
    lines.append("\\toprule")
    lines.append(header)
    lines.append("\\midrule")

    for system in systems:
        row = system.replace("_", "\\_")
        data = reliability_results[system]
        for m in metrics:
            val = data.get(m, None)
            row += f" & {format_metric(val, 'f1') if val else '-'}"
        row += " \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate VLegal-Bench experiments")
    parser.add_argument("--results_dir", type=str, default="experiments/results",
                        help="Directory containing experiment results")
    parser.add_argument("--model", type=str, default=None,
                        help="Model name filter")
    parser.add_argument("--system", type=str, default=None,
                        help="Evaluate specific system only")
    parser.add_argument("--annotations_dir", type=str, default="annotations",
                        help="Directory containing annotated data")
    parser.add_argument("--latex", action="store_true",
                        help="Generate LaTeX tables")
    parser.add_argument("--output", type=str, default="experiments/evaluation_results.json",
                        help="Output file for evaluation results")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Discover systems
    if args.system:
        systems = [args.system]
    else:
        systems = [d for d in os.listdir(args.results_dir)
                   if os.path.isdir(os.path.join(args.results_dir, d))]

    if not systems:
        logging.error(f"No systems found in {args.results_dir}")
        return

    # Discover models
    models = set()
    for system in systems:
        system_dir = os.path.join(args.results_dir, system)
        if os.path.isdir(system_dir):
            for d in os.listdir(system_dir):
                if os.path.isdir(os.path.join(system_dir, d)):
                    models.add(d)

    if args.model:
        models = {m for m in models if args.model in m}

    if not models:
        logging.error("No models found")
        return

    # Evaluate each system
    all_results = {}
    for system in systems:
        for model in models:
            key = f"{system}"
            logging.info(f"Evaluating {system}/{model}...")
            results = evaluate_system(args.results_dir, model, system)
            if results:
                all_results[key] = results
                avg = compute_averages(results)
                logging.info(f"  Overall: {avg}")

    # Load annotations for reliability metrics
    annotations = load_annotations(args.annotations_dir)

    # Compute reliability metrics if annotations exist
    reliability_results = {}
    if annotations:
        logging.info("\nComputing reliability metrics...")
        for system in systems:
            for model in models:
                rel_metrics = {}
                for task, ann_list in annotations.items():
                    result_file = os.path.join(args.results_dir, system, model,
                                               f"{task.replace('.', '_')}_results.jsonl")
                    if os.path.exists(result_file):
                        predictions = load_jsonl(result_file)
                        task_rel = compute_reliability_metrics(predictions, ann_list)
                        for k, v in task_rel.items():
                            if k not in rel_metrics:
                                rel_metrics[k] = []
                            rel_metrics[k].append(v)

                # Average across tasks
                avg_rel = {}
                for k, values in rel_metrics.items():
                    if values:
                        avg_rel[k] = sum(values) / len(values)
                reliability_results[system] = avg_rel
                logging.info(f"  {system}: {avg_rel}")

    # Save results
    output_data = {
        "core_results": {k: {t: d.get("core", {}) for t, d in v.items()} for k, v in all_results.items()},
        "reliability_results": reliability_results,
        "task_categories": TASK_CATEGORIES,
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    logging.info(f"\nResults saved to: {args.output}")

    # Print summary table
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    for system, results in all_results.items():
        avg = compute_averages(results)
        print(f"\n{system}:")
        for metric, value in sorted(avg.items()):
            print(f"  {metric}: {format_metric(value, metric)}")

    # Generate LaTeX
    if args.latex:
        print("\n" + "=" * 80)
        print("LATEX: Table 2 (Core Results)")
        print("=" * 80)
        print(generate_latex_table2(all_results))

        if reliability_results:
            print("\n" + "=" * 80)
            print("LATEX: Table 3 (Reliability Metrics)")
            print("=" * 80)
            print(generate_latex_table3(reliability_results))

        # Save LaTeX to files
        latex_dir = "experiments/latex"
        os.makedirs(latex_dir, exist_ok=True)
        with open(f"{latex_dir}/table2_core_results.tex", 'w') as f:
            f.write(generate_latex_table2(all_results))
        if reliability_results:
            with open(f"{latex_dir}/table3_reliability_metrics.tex", 'w') as f:
                f.write(generate_latex_table3(reliability_results))
        logging.info(f"LaTeX tables saved to {latex_dir}/")


if __name__ == "__main__":
    main()
