#!/usr/bin/env python3
"""
LaTeX Table Generator for VLegal-Bench Paper

Generates 4 tables:
  Table 1: Dataset statistics
  Table 2: Core benchmark results
  Table 3: Reliability metrics
  Table 4: Ablation study

Usage:
    # Generate all tables
    python tools/generate_tables.py --results experiments/evaluation_results.json

    # Generate specific table
    python tools/generate_tables.py --results experiments/evaluation_results.json --table 1

    # Output to file
    python tools/generate_tables.py --results experiments/evaluation_results.json --output paper/tables/
"""

import json
import os
import sys
import argparse
from collections import defaultdict


# Task information
TASK_INFO = {
    "1.1": {"name": "Legal Entity Recognition", "type": "MC", "category": "1.x"},
    "1.2": {"name": "Legal Domain Classification", "type": "MC", "category": "1.x"},
    "1.3": {"name": "Legal Concept Understanding", "type": "MC", "category": "1.x"},
    "1.4": {"name": "Article Recall", "type": "MC", "category": "1.x"},
    "1.5": {"name": "Temporal Document Identification", "type": "MC", "category": "1.x"},
    "2.1": {"name": "Legal Relation Identification", "type": "MC", "category": "2.x"},
    "2.2": {"name": "Legal Norm Structure", "type": "MC", "category": "2.x"},
    "2.3": {"name": "Legal Graph Structuring", "type": "Gen", "category": "2.x"},
    "2.4": {"name": "Judgement Verification", "type": "MC", "category": "2.x"},
    "2.5": {"name": "Intent Classification", "type": "MC", "category": "2.x"},
    "3.1": {"name": "Legal Reasoning", "type": "MC", "category": "3.x"},
    "3.2": {"name": "Court Decision Analysis", "type": "MC", "category": "3.x"},
    "3.3": {"name": "Multi-hop Legal Reasoning", "type": "MC", "category": "3.x"},
    "3.4": {"name": "Legal QA", "type": "MC", "category": "3.x"},
    "3.5": {"name": "Legal Argument Analysis", "type": "MC", "category": "3.x"},
    "4.1": {"name": "Legal Summarization", "type": "Gen", "category": "4.x"},
    "4.2": {"name": "Legal Document Analysis", "type": "Gen", "category": "4.x"},
    "4.3": {"name": "Legal Opinion Generation", "type": "Gen", "category": "4.x"},
    "5.1": {"name": "Bias Detection", "type": "MC", "category": "5.x"},
    "5.2": {"name": "Privacy & Data Protection", "type": "MC", "category": "5.x"},
    "5.3": {"name": "Legal Ethics", "type": "MC", "category": "5.x"},
    "5.4": {"name": "Contract Fairness", "type": "MC", "category": "5.x"},
}

TASK_CATEGORIES = {
    "1.x": {"name": "Recognition \\& Recall", "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5"]},
    "2.x": {"name": "Understanding \\& Structuring", "tasks": ["2.1", "2.2", "2.3", "2.4", "2.5"]},
    "3.x": {"name": "Reasoning \\& Inference", "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5"]},
    "4.x": {"name": "Interpretation \\& Generation", "tasks": ["4.1", "4.2", "4.3"]},
    "5.x": {"name": "Ethics, Fairness \\& Bias", "tasks": ["5.1", "5.2", "5.3", "5.4"]},
}


def load_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def count_samples() -> dict:
    """Count samples per task from JSONL files."""
    counts = {}
    for task in TASK_INFO:
        task_id = task.replace(".", "_")
        base_path = f"./{task}"

        # Standard pattern
        standard = f"{base_path}/{task_id}.jsonl"
        if os.path.exists(standard):
            with open(standard, 'r', encoding='utf-8') as f:
                counts[task] = sum(1 for line in f if line.strip())
            continue

        # 5.3 special case
        if task == "5.3":
            path = f"{base_path}/{task_id}_legal_ethics_cases_reformatted.jsonl"
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    counts[task] = sum(1 for line in f if line.strip())

    return counts


def generate_table1() -> str:
    """Generate Table 1: Dataset Statistics."""
    counts = count_samples()

    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\caption{VLegal-Bench dataset statistics.}")
    lines.append("\\label{tab:dataset_stats}")
    lines.append("\\small")
    lines.append("\\begin{tabular}{llccc}")
    lines.append("\\toprule")
    lines.append("\\textbf{Category} & \\textbf{Task} & \\textbf{Type} & \\textbf{Samples} & \\textbf{Total} \\\\")
    lines.append("\\midrule")

    for cat_id, cat_info in TASK_CATEGORIES.items():
        cat_tasks = cat_info["tasks"]
        cat_total = sum(counts.get(t, 0) for t in cat_tasks)

        for i, task in enumerate(cat_tasks):
            info = TASK_INFO[task]
            n = counts.get(task, 0)

            if i == 0:
                lines.append(f"\\multirow{{{len(cat_tasks)}}}{{*}}{{{cat_info['name']}}} & {info['name']} & {info['type']} & {n:,} & \\multirow{{{len(cat_tasks)}}}{{*}}{{{cat_total:,}}} \\\\")
            else:
                lines.append(f" & {info['name']} & {info['type']} & {n:,} & \\\\")

        if cat_id != "5.x":
            lines.append("\\midrule")

    # Total row
    total = sum(counts.values())
    lines.append("\\midrule")
    lines.append(f"\\multicolumn{{3}}{{l}}{{\\textbf{{Total}}}} & \\multicolumn{{1}}{{c}}{{}} & \\textbf{{{total:,}}} \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def generate_table2(results: dict) -> str:
    """Generate Table 2: Core Benchmark Results."""
    core_results = results.get("core_results", {})
    if not core_results:
        return "% No core results available"

    systems = list(core_results.keys())
    categories = list(TASK_CATEGORIES.keys())

    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Core benchmark results (\\%) across task categories.}")
    lines.append("\\label{tab:core_results}")
    lines.append("\\small")
    lines.append("\\resizebox{\\textwidth}{!}{%")
    lines.append("\\begin{tabular}{l" + "c" * (len(categories) + 1) + "}")
    lines.append("\\toprule")

    # Header
    header = "\\textbf{System}"
    for cat_id, cat_info in TASK_CATEGORIES.items():
        header += f" & {cat_info['name']}"
    header += " & \\textbf{Avg.} \\\\"
    lines.append(header)
    lines.append("\\midrule")

    # Data rows
    for system in systems:
        task_results = core_results[system]
        row = system.replace("_", "\\_")
        all_values = []

        for cat_id, cat_info in TASK_CATEGORIES.items():
            cat_values = []
            for task in cat_info["tasks"]:
                if task in task_results:
                    core = task_results[task]
                    # Use accuracy for MC, ROUGE for Gen
                    if TASK_INFO[task]["type"] == "MC":
                        val = core.get("accuracy", 0)
                    else:
                        val = core.get("ROUGE", 0)
                    cat_values.append(val)

            if cat_values:
                cat_avg = sum(cat_values) / len(cat_values) * 100
                row += f" & {cat_avg:.1f}"
                all_values.extend(cat_values)
            else:
                row += " & -"

        # Overall average
        if all_values:
            overall = sum(all_values) / len(all_values) * 100
            row += f" & \\textbf{{{overall:.1f}}}"
        else:
            row += " & -"

        row += " \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("}%")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def generate_table3(results: dict) -> str:
    """Generate Table 3: Reliability Metrics."""
    rel_results = results.get("reliability_results", {})
    if not rel_results:
        return "% No reliability results available"

    metrics = ["CitAcc", "RAS", "RAR", "ESR", "UCR", "AbsAcc"]
    metric_names = {
        "CitAcc": "Cit. Acc.",
        "RAS": "RAS",
        "RAR": "RAR",
        "ESR": "ESR",
        "UCR": "UCR",
        "AbsAcc": "Abs. Acc.",
    }
    systems = list(rel_results.keys())

    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Reliability metrics on annotated subset (\\%).}")
    lines.append("\\label{tab:reliability_metrics}")
    lines.append("\\small")
    lines.append("\\begin{tabular}{l" + "c" * len(metrics) + "}")
    lines.append("\\toprule")

    header = "\\textbf{System}"
    for m in metrics:
        header += f" & {metric_names[m]}"
    header += " \\\\"
    lines.append(header)
    lines.append("\\midrule")

    for system in systems:
        row = system.replace("_", "\\_")
        data = rel_results[system]
        for m in metrics:
            val = data.get(m, None)
            if val is not None:
                row += f" & {val*100:.1f}"
            else:
                row += " & -"
        row += " \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def generate_table4(results: dict) -> str:
    """Generate Table 4: Ablation Study."""
    core_results = results.get("core_results", {})
    rel_results = results.get("reliability_results", {})

    if not core_results:
        return "% No results available for ablation"

    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Ablation study: effect of each component.}")
    lines.append("\\label{tab:ablation}")
    lines.append("\\small")
    lines.append("\\begin{tabular}{lcccccc}")
    lines.append("\\toprule")
    lines.append("\\textbf{System} & \\textbf{Acc.} & \\textbf{F1} & \\textbf{CitAcc} & \\textbf{RAS} & \\textbf{ESR} & \\textbf{AbsAcc} \\\\")
    lines.append("\\midrule")

    # Ablation components
    ablation_systems = [
        ("baseline_1a", "Zero-shot"),
        ("baseline_1b", "+ Reasoning"),
        ("baseline_2a", "+ Legal prompt"),
        ("baseline_2b", "+ Legal + Reasoning"),
        ("baseline_3", "+ LoRA (no rel.)"),
        ("proposed", "+ LoRA (with rel.)"),
    ]

    for sys_id, sys_name in ablation_systems:
        if sys_id not in core_results:
            continue

        row = sys_name

        # Core metrics
        task_results = core_results[sys_id]
        accs, f1s = [], []
        for task, core in task_results.items():
            if "accuracy" in core:
                accs.append(core["accuracy"])
            if "f1-score" in core:
                f1s.append(core["f1-score"])

        avg_acc = sum(accs) / len(accs) * 100 if accs else 0
        avg_f1 = sum(f1s) / len(f1s) * 100 if f1s else 0
        row += f" & {avg_acc:.1f} & {avg_f1:.1f}"

        # Reliability metrics
        rel = rel_results.get(sys_id, {})
        for m in ["CitAcc", "RAS", "ESR", "AbsAcc"]:
            val = rel.get(m, None)
            if val is not None:
                row += f" & {val*100:.1f}"
            else:
                row += " & -"

        row += " \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX tables for paper")
    parser.add_argument("--results", type=str, default="experiments/evaluation_results.json",
                        help="Path to evaluation results JSON")
    parser.add_argument("--table", type=int, default=None,
                        help="Generate specific table (1-4)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory for LaTeX files")
    parser.add_argument("--stdout", action="store_true",
                        help="Print to stdout instead of files")
    args = parser.parse_args()

    # Load results if available
    results = {}
    if os.path.exists(args.results):
        results = load_json(args.results)
        print(f"Loaded results from: {args.results}")
    else:
        print(f"Results file not found: {args.results}")
        print("Generating Table 1 (dataset stats) only")

    # Generate tables
    tables = {}

    if args.table is None or args.table == 1:
        tables[1] = generate_table1()

    if args.table is None or args.table == 2:
        tables[2] = generate_table2(results)

    if args.table is None or args.table == 3:
        tables[3] = generate_table3(results)

    if args.table is None or args.table == 4:
        tables[4] = generate_table4(results)

    # Output
    if args.stdout:
        for table_num, content in tables.items():
            print(f"\n{'='*60}")
            print(f"TABLE {table_num}")
            print(f"{'='*60}")
            print(content)
    else:
        output_dir = args.output or "experiments/latex"
        os.makedirs(output_dir, exist_ok=True)

        for table_num, content in tables.items():
            filepath = os.path.join(output_dir, f"table{table_num}.tex")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Table {table_num} saved to: {filepath}")

    # Also print Table 1 since it doesn't need results
    if not results:
        print("\n" + "=" * 60)
        print("TABLE 1: Dataset Statistics")
        print("=" * 60)
        print(generate_table1())


if __name__ == "__main__":
    main()
