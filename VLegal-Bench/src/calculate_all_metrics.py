#!/usr/bin/env python3
"""
Calculate reliability metrics for all annotated tasks.
Handles both baseline_3 and proposed modes.

Usage:
    python calculate_all_metrics.py
    python calculate_all_metrics.py --mode baseline_3
    python calculate_all_metrics.py --mode proposed
"""

import json
import os
import sys
import glob
import re
from collections import defaultdict

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reliability_metrics import (
    ReliabilityMetrics,
    parse_citation_from_response,
    detect_abstention,
    extract_atomic_claims,
    CitationAnnotation,
    TemporalAnnotation
)

VLEGAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANNOTATIONS_DIR = os.path.join(VLEGAL_DIR, "annotations")

ANNOTATED_TASKS = ["1.4", "1.5", "3.1", "4.1", "4.2"]


def load_predictions_with_index(predictions_path: str) -> list:
    """Load predictions and add index-based sample_id if missing."""
    predictions = []
    with open(predictions_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                pred = json.loads(line)
                # Add sample_id based on index if not present
                if 'sample_id' not in pred and 'id' not in pred:
                    pred['_index'] = i
                predictions.append(pred)
    return predictions


def load_annotations_with_index(annotations_path: str) -> dict:
    """Load annotations and create index-based mapping."""
    annotations = {}
    with open(annotations_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                ann = json.loads(line)
                # Map by sample_id if available, otherwise by index
                sid = ann.get('sample_id', '')
                if sid:
                    annotations[sid] = ann
                annotations[f'_idx_{i}'] = ann
    return annotations


def match_predictions_to_annotations(predictions: list, annotations: dict) -> list:
    """Match predictions to annotations using sample_id or index."""
    matched = []
    for i, pred in enumerate(predictions):
        # Try sample_id first
        sid = pred.get('sample_id', pred.get('id', ''))
        ann = annotations.get(sid)

        # Fallback to index
        if not ann:
            ann = annotations.get(f'_idx_{i}')

        if ann:
            matched.append((pred, ann))
    return matched


def calculate_metrics_for_task(task: str, mode: str) -> dict:
    """Calculate all reliability metrics for a single task."""
    task_name = task.replace(".", "_")

    # Find prediction file (reliability mode)
    pred_patterns = [
        os.path.join(VLEGAL_DIR, task, f"{task_name}_llm_test_results_{mode}_reliability.json"),
        os.path.join(VLEGAL_DIR, task, f"{task_name}_llm_test_results_{mode}.json"),
    ]

    pred_path = None
    for p in pred_patterns:
        if os.path.exists(p):
            pred_path = p
            break

    if not pred_path:
        return {"error": f"No predictions found for {task} ({mode})"}

    # Find annotation file
    ann_path = os.path.join(ANNOTATIONS_DIR, f"{task_name}_annotated.jsonl")
    if not os.path.exists(ann_path):
        return {"error": f"No annotations found for {task}"}

    # Load data
    predictions = load_predictions_with_index(pred_path)
    annotations = load_annotations_with_index(ann_path)

    # Filter to only non-skipped annotations
    valid_ann_indices = set()
    for key, ann in annotations.items():
        if key.startswith('_idx_') and not ann.get('skipped', False):
            valid_ann_indices.add(key)

    # Match predictions to valid annotations
    matched = []
    for i, pred in enumerate(predictions):
        idx_key = f'_idx_{i}'
        ann = annotations.get(idx_key)
        if ann and not ann.get('skipped', False):
            matched.append((pred, ann))

    if not matched:
        return {"error": f"No matched samples for {task} ({mode})"}

    # Calculate metrics
    results = {
        "task": task,
        "mode": mode,
        "total_predictions": len(predictions),
        "total_annotations": len([a for a in annotations.values() if not a.get('skipped', False)]),
        "matched_samples": len(matched),
    }

    # CitAcc
    for granularity in ['document', 'article', 'clause']:
        correct = 0
        total = 0
        for pred, ann in matched:
            if 'citation' not in ann:
                continue
            total += 1
            raw_response = pred.get('raw_response', pred.get('prediction', ''))
            predicted_citations = parse_citation_from_response(raw_response)

            gold = CitationAnnotation(
                document=ann['citation'].get('document_name', ''),
                article=ann['citation'].get('article', ''),
                clause=ann['citation'].get('clause', None)
            )

            for pc in predicted_citations:
                if gold.match(pc, granularity):
                    correct += 1
                    break

        results[f'CitAcc_{granularity}'] = correct / total if total > 0 else 0.0
        results[f'CitAcc_{granularity}_count'] = f"{correct}/{total}"

    # RAS (Recency-Aware Score)
    import math
    total_ras = 0.0
    ras_count = 0
    for pred, ann in matched:
        if 'temporal' not in ann:
            continue
        temporal = ann['temporal']
        query_date = temporal.get('query_reference_date', '')
        if not query_date:
            continue

        ras_count += 1
        temporal_ann = TemporalAnnotation(
            effective_date=temporal.get('effective_date'),
            expiration_date=temporal.get('expiration_date'),
            valid_at_query_date=temporal.get('valid_at_query_date', True)
        )

        if temporal_ann.is_valid_at(query_date):
            distance = temporal_ann.temporal_distance(query_date)
            total_ras += math.exp(-0.01 * distance)

    results['RAS'] = total_ras / ras_count if ras_count > 0 else 0.0
    results['RAS_count'] = ras_count

    # RAR (Recency-Aware Recall)
    valid_count = 0
    rar_count = 0
    for pred, ann in matched:
        if 'temporal' not in ann:
            continue
        temporal = ann['temporal']
        query_date = temporal.get('query_reference_date', '')
        if not query_date:
            continue

        rar_count += 1
        temporal_ann = TemporalAnnotation(
            effective_date=temporal.get('effective_date'),
            expiration_date=temporal.get('expiration_date'),
            valid_at_query_date=temporal.get('valid_at_query_date', True)
        )
        if temporal_ann.is_valid_at(query_date):
            valid_count += 1

    results['RAR'] = valid_count / rar_count if rar_count > 0 else 0.0
    results['RAR_count'] = f"{valid_count}/{rar_count}"

    # ESR (Evidence Support Rate)
    supported = 0
    esr_count = 0
    for pred, ann in matched:
        if 'reliability' not in ann:
            continue
        esr_count += 1
        reliability = ann['reliability']
        if reliability.get('evidence_sufficient', False):
            supported += 1

    results['ESR'] = supported / esr_count if esr_count > 0 else 0.0
    results['ESR_count'] = f"{supported}/{esr_count}"

    # UCR (Unsupported Claim Rate)
    unsupported = 0
    ucr_count = 0
    for pred, ann in matched:
        if 'reliability' not in ann:
            continue
        ucr_count += 1
        reliability = ann['reliability']
        unsup = reliability.get('unsupported_claims', [])
        if unsup and len(unsup) > 0:
            unsupported += 1

    results['UCR'] = unsupported / ucr_count if ucr_count > 0 else 0.0
    results['UCR_count'] = f"{unsupported}/{ucr_count}"

    # AbsAcc (Abstention Accuracy)
    correct_abstain = 0
    should_abstain = 0
    for pred, ann in matched:
        if 'reliability' not in ann:
            continue
        reliability = ann['reliability']
        if not reliability.get('should_abstain', False):
            continue

        should_abstain += 1
        raw_response = pred.get('raw_response', pred.get('prediction', ''))
        if detect_abstention(raw_response):
            correct_abstain += 1

    results['AbsAcc'] = correct_abstain / should_abstain if should_abstain > 0 else 0.0
    results['AbsAcc_count'] = f"{correct_abstain}/{should_abstain}"

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="both", choices=["baseline_3", "proposed", "both"])
    parser.add_argument("--tasks", type=str, nargs="+", default=ANNOTATED_TASKS)
    args = parser.parse_args()

    modes = ["baseline_3", "proposed"] if args.mode == "both" else [args.mode]

    all_results = {}
    summary_table = []

    for mode in modes:
        print(f"\n{'='*70}")
        print(f"MODE: {mode}")
        print(f"{'='*70}")

        mode_results = {}
        for task in args.tasks:
            print(f"\n--- Task {task} ---")
            result = calculate_metrics_for_task(task, mode)
            mode_results[task] = result

            if "error" in result:
                print(f"  ERROR: {result['error']}")
            else:
                print(f"  Matched: {result['matched_samples']}/{result['total_annotations']}")
                print(f"  CitAcc (doc):  {result['CitAcc_document']:.4f}  ({result['CitAcc_document_count']})")
                print(f"  CitAcc (art):  {result['CitAcc_article']:.4f}  ({result['CitAcc_article_count']})")
                print(f"  CitAcc (cls):  {result['CitAcc_clause']:.4f}  ({result['CitAcc_clause_count']})")
                print(f"  RAS:           {result['RAS']:.4f}  (n={result['RAS_count']})")
                print(f"  RAR:           {result['RAR']:.4f}  ({result['RAR_count']})")
                print(f"  ESR:           {result['ESR']:.4f}  ({result['ESR_count']})")
                print(f"  UCR:           {result['UCR']:.4f}  ({result['UCR_count']})")
                print(f"  AbsAcc:        {result['AbsAcc']:.4f}  ({result['AbsAcc_count']})")

                summary_table.append({
                    "mode": mode,
                    "task": task,
                    "n": result['matched_samples'],
                    "CitAcc_doc": result['CitAcc_document'],
                    "CitAcc_art": result['CitAcc_article'],
                    "CitAcc_cls": result['CitAcc_clause'],
                    "RAS": result['RAS'],
                    "RAR": result['RAR'],
                    "ESR": result['ESR'],
                    "UCR": result['UCR'],
                    "AbsAcc": result['AbsAcc'],
                })

        all_results[mode] = mode_results

    # Print summary table
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"{'Mode':<12} {'Task':<6} {'n':>4} {'CitAcc_d':>8} {'CitAcc_a':>8} {'CitAcc_c':>8} {'RAS':>6} {'RAR':>6} {'ESR':>6} {'UCR':>6} {'AbsAcc':>7}")
    print("-" * 90)
    for row in summary_table:
        print(f"{row['mode']:<12} {row['task']:<6} {row['n']:>4} {row['CitAcc_doc']:>8.4f} {row['CitAcc_art']:>8.4f} {row['CitAcc_cls']:>8.4f} {row['RAS']:>6.4f} {row['RAR']:>6.4f} {row['ESR']:>6.4f} {row['UCR']:>6.4f} {row['AbsAcc']:>7.4f}")

    # Save results
    output_path = os.path.join(VLEGAL_DIR, "reliability_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

    # Generate LaTeX table
    generate_latex_table(summary_table)


def generate_latex_table(summary_table: list):
    """Generate LaTeX table for paper."""
    print(f"\n{'='*70}")
    print("LATEX TABLE")
    print(f"{'='*70}")

    # Group by mode
    by_mode = defaultdict(list)
    for row in summary_table:
        by_mode[row['mode']].append(row)

    print("\\begin{table}[h]")
    print("\\centering")
    print("\\caption{Reliability Metrics Results}")
    print("\\label{tab:reliability}")
    print("\\begin{tabular}{llccccccc}")
    print("\\toprule")
    print("Mode & Task & $n$ & CitAcc & RAS & RAR & ESR & UCR & AbsAcc \\\\")
    print("\\midrule")

    for mode in ["baseline_3", "proposed"]:
        rows = by_mode.get(mode, [])
        for i, row in enumerate(rows):
            mode_label = "Baseline" if mode == "baseline_3" else "Proposed"
            if i == 0:
                print(f"\\multirow{{{len(rows)}}}{{*}}{{{mode_label}}} & {row['task']} & {row['n']} & {row['CitAcc_doc']:.3f} & {row['RAS']:.3f} & {row['RAR']:.3f} & {row['ESR']:.3f} & {row['UCR']:.3f} & {row['AbsAcc']:.3f} \\\\")
            else:
                print(f" & {row['task']} & {row['n']} & {row['CitAcc_doc']:.3f} & {row['RAS']:.3f} & {row['RAR']:.3f} & {row['ESR']:.3f} & {row['UCR']:.3f} & {row['AbsAcc']:.3f} \\\\")

        # Average
        if rows:
            avg_cit = sum(r['CitAcc_doc'] for r in rows) / len(rows)
            avg_ras = sum(r['RAS'] for r in rows) / len(rows)
            avg_rar = sum(r['RAR'] for r in rows) / len(rows)
            avg_esr = sum(r['ESR'] for r in rows) / len(rows)
            avg_ucr = sum(r['UCR'] for r in rows) / len(rows)
            avg_abs = sum(r['AbsAcc'] for r in rows) / len(rows)
            total_n = sum(r['n'] for r in rows)
            print(f" & \\textbf{{Avg}} & {total_n} & \\textbf{{{avg_cit:.3f}}} & \\textbf{{{avg_ras:.3f}}} & \\textbf{{{avg_rar:.3f}}} & \\textbf{{{avg_esr:.3f}}} & \\textbf{{{avg_ucr:.3f}}} & \\textbf{{{avg_abs:.3f}}} \\\\")

        if mode == "baseline_3":
            print("\\midrule")

    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


if __name__ == "__main__":
    main()
