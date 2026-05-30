#!/usr/bin/env python3
"""
Calculate core metrics (accuracy, BLEU, ROUGE-L) for all models and tasks.
Generates summary table and LaTeX for paper.
"""

import json
import os
import sys
import glob
import re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import task_type_mapping, parse_triplets
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

VLEGAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODELS = [
    "gemma4_e4b-it-q8_0",
    "baseline_3",
    "proposed"
]

MODEL_LABELS = {
    "gemma4_e4b-it-q8_0": "Gemma-4 (fewshot)",
    "baseline_3": "Baseline 3 (fine-tuned)",
    "proposed": "Proposed (fine-tuned)"
}

ALL_TASKS = [
    "1.1","1.2","1.3","1.4","1.5",
    "2.1","2.2","2.3","2.4","2.5",
    "3.1","3.2","3.3","3.4","3.5",
    "4.1","4.2","4.3",
    "5.1","5.2","5.3","5.4"
]


def load_predictions(task, model):
    task_name = task.replace(".", "_")
    path = os.path.join(VLEGAL_DIR, task, f"{task_name}_llm_test_results_{model}.json")
    if not os.path.exists(path):
        return None
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def parse_mc_answer(text):
    """Extract MC answer letter from text."""
    if not text:
        return ""
    text = text.strip()
    # Direct single letter
    if len(text) == 1 and text in "ABCD":
        return text
    # Letter with period
    if len(text) == 2 and text[0] in "ABCD" and text[1] == '.':
        return text[0]
    # Multiple lines - take first letter of each line
    lines = text.strip().split('\n')
    answers = []
    for line in lines:
        line = line.strip()
        if line and line[0] in "ABCD":
            answers.append(line[0])
    return ''.join(sorted(set(answers))) if answers else ""


def calculate_accuracy(predictions):
    """Calculate accuracy for MC tasks."""
    correct = 0
    total = 0
    for pred in predictions:
        gt = str(pred.get("ground_truth", "")).strip()
        raw = pred.get("raw_response", pred.get("prediction", ""))
        predicted = parse_mc_answer(raw)
        if not gt:
            continue
        total += 1
        # Compare as sets (handles multi-answer)
        gt_set = set(gt)
        pred_set = set(predicted)
        if gt_set == pred_set:
            correct += 1
    return correct / total if total > 0 else 0.0, correct, total


def calculate_bleu_rouge(predictions):
    """Calculate BLEU and ROUGE-L for generation tasks."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    smooth = SmoothingFunction().method1

    bleu_scores = []
    rouge_scores = []

    for pred in predictions:
        gt = str(pred.get("ground_truth", "")).strip()
        raw = pred.get("raw_response", pred.get("prediction", ""))
        predicted = raw.strip()

        if not gt or not predicted:
            continue

        # BLEU
        ref_tokens = gt.split()
        pred_tokens = predicted.split()
        try:
            bleu = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smooth)
            bleu_scores.append(bleu)
        except:
            pass

        # ROUGE-L
        try:
            scores = scorer.score(gt, predicted)
            rouge_scores.append(scores['rougeL'].fmeasure)
        except:
            pass

    avg_bleu = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0
    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0
    return avg_bleu, avg_rouge, len(bleu_scores)


def calculate_f1(predictions):
    """Calculate macro F1 for imbalanced MC (task 3.4)."""
    from collections import Counter
    labels = set()
    y_true = []
    y_pred = []

    for pred in predictions:
        gt = str(pred.get("ground_truth", "")).strip()
        raw = pred.get("raw_response", pred.get("prediction", ""))
        predicted = parse_mc_answer(raw)
        if not gt:
            continue
        y_true.append(gt)
        y_pred.append(predicted)
        labels.add(gt)
        labels.add(predicted)

    # Per-class F1
    f1_scores = []
    weights = {"khong": 3}  # Weight for minority class
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        weight = weights.get(label, 1)
        f1_scores.append((f1, weight))

    if not f1_scores:
        return 0.0
    total_weight = sum(w for _, w in f1_scores)
    weighted_f1 = sum(f * w for f, w in f1_scores) / total_weight
    return weighted_f1


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=MODELS)
    parser.add_argument("--tasks", nargs="+", default=ALL_TASKS)
    parser.add_argument("--output", default=os.path.join(VLEGAL_DIR, "core_metrics_results.json"))
    args = parser.parse_args()

    all_results = {}

    for model in args.models:
        print(f"\n{'='*60}")
        print(f"Model: {MODEL_LABELS.get(model, model)}")
        print(f"{'='*60}")

        model_results = {}
        for task in args.tasks:
            task_name = task.replace(".", "_")
            task_type = task_type_mapping.get(task_name, "unknown")

            predictions = load_predictions(task, model)
            if not predictions:
                print(f"  Task {task}: NO PREDICTIONS")
                continue

            if task_type == "multiple_choices" or task_type == "multiple_choices_imbalance":
                if task_type == "multiple_choices_imbalance":
                    f1 = calculate_f1(predictions)
                    acc, correct, total = calculate_accuracy(predictions)
                    model_results[task] = {
                        "type": task_type, "accuracy": acc, "f1": f1,
                        "correct": correct, "total": total
                    }
                    print(f"  Task {task}: Acc={acc:.4f} ({correct}/{total}), F1={f1:.4f}")
                else:
                    acc, correct, total = calculate_accuracy(predictions)
                    model_results[task] = {
                        "type": task_type, "accuracy": acc,
                        "correct": correct, "total": total
                    }
                    print(f"  Task {task}: Acc={acc:.4f} ({correct}/{total})")
            elif task_type == "generation":
                bleu, rouge, n = calculate_bleu_rouge(predictions)
                model_results[task] = {
                    "type": task_type, "bleu": bleu, "rouge_l": rouge, "n": n
                }
                print(f"  Task {task}: BLEU={bleu:.4f}, ROUGE-L={rouge:.4f} (n={n})")
            else:
                print(f"  Task {task}: Unknown type")

        all_results[model] = model_results

    # Save results
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {args.output}")

    # Generate LaTeX table
    generate_latex(all_results, args.tasks)


def generate_latex(all_results, tasks):
    print(f"\n{'='*60}")
    print("LATEX TABLE - Core Metrics")
    print(f"{'='*60}")

    # MC tasks table
    mc_tasks = [t for t in tasks if task_type_mapping.get(t.replace(".", "_")) in
                ("multiple_choices", "multiple_choices_imbalance")]
    gen_tasks = [t for t in tasks if task_type_mapping.get(t.replace(".", "_")) == "generation"]

    # MC Accuracy table
    print("\n% Table 1: MC Task Accuracy")
    print("\\begin{table}[h]")
    print("\\centering")
    print("\\caption{Accuracy on Multiple-Choice Tasks}")
    print("\\label{tab:mc_accuracy}")
    print("\\begin{tabular}{l" + "c" * len(mc_tasks) + "}")
    print("\\toprule")
    header = "Model & " + " & ".join(mc_tasks) + " \\\\"
    print(header)
    print("\\midrule")

    for model in MODELS:
        if model not in all_results:
            continue
        label = MODEL_LABELS.get(model, model)
        vals = []
        for task in mc_tasks:
            if task in all_results[model]:
                acc = all_results[model][task]["accuracy"]
                vals.append(f"{acc:.3f}")
            else:
                vals.append("-")
        print(f"{label} & " + " & ".join(vals) + " \\\\")

    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")

    # Generation tasks table
    print("\n% Table 2: Generation Task Metrics")
    print("\\begin{table}[h]")
    print("\\centering")
    print("\\caption{BLEU and ROUGE-L on Generation Tasks}")
    print("\\label{tab:gen_metrics}")
    print("\\begin{tabular}{l" + "cc" * len(gen_tasks) + "}")
    print("\\toprule")
    header = "Model & " + " & ".join(f"BLEU & ROUGE-L" for _ in gen_tasks) + " \\\\"
    print(header)
    print("\\midrule")

    for model in MODELS:
        if model not in all_results:
            continue
        label = MODEL_LABELS.get(model, model)
        vals = []
        for task in gen_tasks:
            if task in all_results[model]:
                bleu = all_results[model][task]["bleu"]
                rouge = all_results[model][task]["rouge_l"]
                vals.append(f"{bleu:.3f} & {rouge:.3f}")
            else:
                vals.append("- & -")
        print(f"{label} & " + " & ".join(vals) + " \\\\")

    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


if __name__ == "__main__":
    main()
