#!/usr/bin/env python3
"""
Calculate core metrics for all models with proper task-specific parsing.
Handles: MC (letter), text classification (Đúng/Sai, Có/Không), multi-label, generation.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

VLEGAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODELS = ["gemma4_e4b-it-q8_0", "baseline_3", "proposed"]
MODEL_LABELS = {
    "gemma4_e4b-it-q8_0": "Gemma-4 (fewshot)",
    "baseline_3": "Baseline 3",
    "proposed": "Proposed"
}

# Task type definitions with evaluation method
TASK_CONFIG = {
    "1.1": {"type": "mc"},
    "1.2": {"type": "mc"},
    "1.3": {"type": "mc"},
    "1.4": {"type": "mc"},
    "1.5": {"type": "mc"},
    "2.1": {"type": "mc"},
    "2.2": {"type": "mc"},
    "2.3": {"type": "generation"},
    "2.4": {"type": "text_cls", "labels": ["Đúng", "Sai"]},
    "2.5": {"type": "mc_multi"},
    "3.1": {"type": "mc"},
    "3.2": {"type": "mc"},
    "3.3": {"type": "mc"},
    "3.4": {"type": "text_cls", "labels": ["Có", "Không"]},
    "3.5": {"type": "mc"},
    "4.1": {"type": "generation"},
    "4.2": {"type": "generation"},
    "4.3": {"type": "generation"},
    "5.1": {"type": "mc"},
    "5.2": {"type": "mc"},
    "5.4": {"type": "mc"},
}


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
    """Extract MC answer letter(s) from text."""
    if not text:
        return ""
    text = str(text).strip()
    if len(text) == 1 and text in "ABCD":
        return text
    if len(text) == 2 and text[0] in "ABCD" and text[1] == '.':
        return text[0]
    lines = text.strip().split('\n')
    answers = []
    for line in lines:
        line = line.strip()
        if line and line[0] in "ABCD":
            answers.append(line[0])
    return ''.join(sorted(set(answers))) if answers else ""


def normalize_text(text):
    """Normalize text for comparison."""
    if isinstance(text, list):
        return [str(x).strip() for x in text]
    return str(text).strip()


def eval_mc(predictions):
    """Evaluate MC tasks (single or multi-answer letters)."""
    correct = 0
    total = 0
    for pred in predictions:
        gt_raw = pred.get("ground_truth", "")
        if isinstance(gt_raw, list):
            gt = ''.join(str(x).strip() for x in gt_raw)
        else:
            gt = str(gt_raw).strip()
        raw = pred.get("raw_response", pred.get("prediction", ""))
        predicted = parse_mc_answer(raw)
        if not gt:
            continue
        total += 1
        if set(gt) == set(predicted):
            correct += 1
    return correct / total if total > 0 else 0.0, correct, total


def eval_text_cls(predictions, labels):
    """Evaluate text classification tasks (Đúng/Sai, Có/Không)."""
    correct = 0
    total = 0
    format_mismatch = 0
    for pred in predictions:
        gt = str(pred.get("ground_truth", "")).strip()
        raw = str(pred.get("raw_response", pred.get("prediction", ""))).strip()
        if not gt:
            continue
        total += 1
        # Direct text match
        if raw in labels and gt in labels:
            if raw == gt:
                correct += 1
        else:
            format_mismatch += 1
    return correct / total if total > 0 else 0.0, correct, total, format_mismatch


def eval_generation(predictions):
    """Evaluate generation tasks (BLEU, ROUGE-L)."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    smooth = SmoothingFunction().method1
    bleu_scores = []
    rouge_scores = []

    for pred in predictions:
        gt_raw = pred.get("ground_truth", "")
        gt = str(gt_raw).strip() if not isinstance(gt_raw, list) else str(gt_raw)
        raw = pred.get("raw_response", pred.get("prediction", ""))
        predicted = str(raw).strip() if not isinstance(raw, list) else str(raw)
        if not gt or not predicted:
            continue
        try:
            bleu = sentence_bleu([gt.split()], predicted.split(), smoothing_function=smooth)
            bleu_scores.append(bleu)
        except:
            pass
        try:
            scores = scorer.score(gt, predicted)
            rouge_scores.append(scores['rougeL'].fmeasure)
        except:
            pass

    avg_bleu = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0
    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0
    return avg_bleu, avg_rouge, len(bleu_scores)


def main():
    all_results = {}

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {MODEL_LABELS.get(model, model)}")
        print(f"{'='*60}")

        model_results = {}
        for task, config in TASK_CONFIG.items():
            predictions = load_predictions(task, model)
            if not predictions:
                print(f"  Task {task}: NO PREDICTIONS")
                continue

            task_type = config["type"]

            if task_type == "mc":
                acc, correct, total = eval_mc(predictions)
                model_results[task] = {"type": task_type, "accuracy": acc, "correct": correct, "total": total}
                print(f"  Task {task}: Acc={acc:.4f} ({correct}/{total})")

            elif task_type == "mc_multi":
                acc, correct, total = eval_mc(predictions)
                model_results[task] = {"type": task_type, "accuracy": acc, "correct": correct, "total": total}
                print(f"  Task {task}: Acc={acc:.4f} ({correct}/{total})")

            elif task_type == "text_cls":
                labels = config["labels"]
                acc, correct, total, mismatch = eval_text_cls(predictions, labels)
                model_results[task] = {
                    "type": task_type, "accuracy": acc,
                    "correct": correct, "total": total, "format_mismatch": mismatch
                }
                if mismatch > 0:
                    print(f"  Task {task}: Acc={acc:.4f} ({correct}/{total}), FORMAT MISMATCH={mismatch}")
                else:
                    print(f"  Task {task}: Acc={acc:.4f} ({correct}/{total})")

            elif task_type == "generation":
                bleu, rouge, n = eval_generation(predictions)
                model_results[task] = {"type": task_type, "bleu": bleu, "rouge_l": rouge, "n": n}
                print(f"  Task {task}: BLEU={bleu:.4f}, ROUGE-L={rouge:.4f} (n={n})")

        all_results[model] = model_results

    # Save results
    output_path = os.path.join(VLEGAL_DIR, "core_metrics_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

    # Generate summary
    generate_summary(all_results)
    generate_latex(all_results)


def generate_summary(all_results):
    print(f"\n{'='*80}")
    print("SUMMARY TABLE")
    print(f"{'='*80}")
    print(f"{'Task':<6} {'Type':<12} {'Gemma-4':>10} {'Baseline3':>10} {'Proposed':>10} {'Best':>10}")
    print("-" * 60)

    for task, config in TASK_CONFIG.items():
        row = f"{task:<6} {config['type']:<12}"
        vals = {}
        for model in MODELS:
            if task in all_results.get(model, {}):
                r = all_results[model][task]
                if config["type"] in ("mc", "mc_multi", "text_cls"):
                    v = r["accuracy"]
                    vals[model] = v
                    row += f" {v:>10.4f}"
                elif config["type"] == "generation":
                    v = r["rouge_l"]
                    vals[model] = v
                    row += f" {v:>10.4f}"
            else:
                row += f" {'---':>10}"

        # Best model
        if vals:
            best_model = max(vals, key=vals.get)
            best_label = {"gemma4_e4b-it-q8_0": "G4", "baseline_3": "B3", "proposed": "Pr"}
            row += f" {best_label.get(best_model, '?'):>10}"
        print(row)

    # Averages
    print("-" * 60)
    for model in MODELS:
        mc_vals = [all_results[model][t]["accuracy"] for t in TASK_CONFIG
                   if TASK_CONFIG[t]["type"] in ("mc", "mc_multi")
                   and t in all_results.get(model, {})]
        gen_vals = [all_results[model][t]["rouge_l"] for t in TASK_CONFIG
                    if TASK_CONFIG[t]["type"] == "generation"
                    and t in all_results.get(model, {})]
        avg_mc = sum(mc_vals) / len(mc_vals) if mc_vals else 0
        avg_gen = sum(gen_vals) / len(gen_vals) if gen_vals else 0
        print(f"  {MODEL_LABELS.get(model, model)}: Avg MC Acc={avg_mc:.4f}, Avg Gen ROUGE-L={avg_gen:.4f}")


def generate_latex(all_results):
    print(f"\n{'='*80}")
    print("LATEX TABLE")
    print(f"{'='*80}")

    mc_tasks = [t for t, c in TASK_CONFIG.items() if c["type"] in ("mc", "mc_multi")]
    gen_tasks = [t for t, c in TASK_CONFIG.items() if c["type"] == "generation"]
    text_tasks = [t for t, c in TASK_CONFIG.items() if c["type"] == "text_cls"]

    # Table 1: MC Accuracy
    print("\n% Table 1: MC Accuracy")
    print("\\begin{table}[htbp]")
    print("\\centering")
    print("\\small")
    print("\\caption{Accuracy on Multiple-Choice Tasks}")
    print("\\label{tab:mc_accuracy}")
    cols = "l" + "c" * len(mc_tasks) + "c"
    print(f"\\begin{{tabular}}{{{cols}}}")
    print("\\toprule")
    print("Model & " + " & ".join(mc_tasks) + " & Avg \\\\")
    print("\\midrule")

    for model in MODELS:
        label = MODEL_LABELS.get(model, model)
        vals = []
        for task in mc_tasks:
            if task in all_results.get(model, {}):
                vals.append(f"{all_results[model][task]['accuracy']:.3f}")
            else:
                vals.append("-")
        # Average
        mc_accs = [all_results[model][t]["accuracy"] for t in mc_tasks if t in all_results.get(model, {})]
        avg = sum(mc_accs) / len(mc_accs) if mc_accs else 0
        print(f"{label} & " + " & ".join(vals) + f" & \\textbf{{{avg:.3f}}} \\\\")

    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")

    # Table 2: Generation
    print("\n% Table 2: Generation Metrics")
    print("\\begin{table}[htbp]")
    print("\\centering")
    print("\\caption{BLEU and ROUGE-L on Generation Tasks}")
    print("\\label{tab:gen_metrics}")
    print("\\begin{tabular}{lcccccc}")
    print("\\toprule")
    print("Model & \\multicolumn{2}{c}{2.3} & \\multicolumn{2}{c}{4.1} & \\multicolumn{2}{c}{4.2} \\\\")
    print(" & BLEU & ROUGE-L & BLEU & ROUGE-L & BLEU & ROUGE-L \\\\")
    print("\\midrule")

    for model in MODELS:
        label = MODEL_LABELS.get(model, model)
        vals = []
        for task in gen_tasks:
            if task in all_results.get(model, {}):
                r = all_results[model][task]
                vals.append(f"{r['bleu']:.3f} & {r['rouge_l']:.3f}")
            else:
                vals.append("- & -")
        print(f"{label} & " + " & ".join(vals) + " \\\\")

    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


if __name__ == "__main__":
    main()
