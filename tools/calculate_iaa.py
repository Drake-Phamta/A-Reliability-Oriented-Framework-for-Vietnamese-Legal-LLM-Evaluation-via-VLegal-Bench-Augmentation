#!/usr/bin/env python3
"""
Inter-Annotator Agreement (IAA) Calculator

Computes agreement metrics between annotators:
- Cohen's κ for categorical fields (evidence_sufficient, should_abstain, etc.)
- Span F1 for citation fields (document_name, article, clause)
- Percentage agreement for temporal fields

Usage:
    # Compare two annotators
    python tools/calculate_iaa.py --ann1 annotations/1_4_annotated_A.jsonl --ann2 annotations/1_4_annotated_B.jsonl

    # Compare all annotators in a directory
    python tools/calculate_iaa.py --dir annotations/ --pattern "*_annotated_*.jsonl"
"""

import json
import os
import sys
import argparse
from collections import Counter
from typing import List, Dict, Tuple

# Fix UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def load_jsonl(path: str) -> dict:
    """Load annotations indexed by sample_id."""
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                ann = json.loads(line)
                sid = ann.get('sample_id', '')
                if sid:
                    data[sid] = ann
    return data


def cohens_kappa(labels_a: list, labels_b: list) -> float:
    """Compute Cohen's κ for two lists of categorical labels."""
    assert len(labels_a) == len(labels_b), "Lists must have same length"
    n = len(labels_a)
    if n == 0:
        return 0.0

    # Count agreements
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    po = agree / n  # observed agreement

    # Count expected agreement
    all_labels = set(labels_a) | set(labels_b)
    counter_a = Counter(labels_a)
    counter_b = Counter(labels_b)

    pe = 0.0
    for label in all_labels:
        pe += (counter_a[label] / n) * (counter_b[label] / n)

    # Compute κ
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def span_f1(pred_spans: list, gold_spans: list) -> Tuple[float, float, float]:
    """Compute span-level Precision, Recall, F1 for citation fields."""
    pred_set = set(s.lower().strip() for s in pred_spans if s)
    gold_set = set(s.lower().strip() for s in gold_spans if s)

    if not pred_set and not gold_set:
        return 1.0, 1.0, 1.0
    if not pred_set:
        return 0.0, 0.0, 0.0
    if not gold_set:
        return 0.0, 0.0, 0.0

    tp = len(pred_set & gold_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(gold_set) if gold_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1


def compute_iaa(annotations_a: dict, annotations_b: dict) -> dict:
    """Compute all IAA metrics between two annotators."""
    # Find common samples
    common_ids = set(annotations_a.keys()) & set(annotations_b.keys())
    if not common_ids:
        return {"error": "No common samples found"}

    common_ids = sorted(common_ids)
    results = {
        "n_samples": len(common_ids),
        "metrics": {}
    }

    # === Categorical fields (Cohen's κ) ===
    categorical_fields = [
        ("reliability.evidence_sufficient", "Categorical"),
        ("reliability.should_abstain", "Categorical"),
        ("reliability.hallucination_type", "Categorical"),
        ("temporal.valid_at_query_date", "Categorical"),
    ]

    for field_path, field_type in categorical_fields:
        parts = field_path.split(".")
        labels_a, labels_b = [], []

        for sid in common_ids:
            val_a = annotations_a[sid]
            val_b = annotations_b[sid]
            for p in parts:
                val_a = val_a.get(p, None) if isinstance(val_a, dict) else None
                val_b = val_b.get(p, None) if isinstance(val_b, dict) else None

            # Convert to string for comparison
            label_a = str(val_a) if val_a is not None else "None"
            label_b = str(val_b) if val_b is not None else "None"
            labels_a.append(label_a)
            labels_b.append(label_b)

        kappa = cohens_kappa(labels_a, labels_b)
        agreement = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / len(labels_a)

        results["metrics"][field_path] = {
            "type": "Cohen's κ",
            "kappa": round(kappa, 4),
            "agreement": round(agreement, 4),
            "n": len(labels_a),
        }

    # === Citation fields (Span F1) ===
    citation_fields = [
        "citation.document_name",
        "citation.article",
        "citation.clause",
    ]

    for field_path in citation_fields:
        parts = field_path.split(".")
        spans_a, spans_b = [], []

        for sid in common_ids:
            val_a = annotations_a[sid]
            val_b = annotations_b[sid]
            for p in parts:
                val_a = val_a.get(p, "") if isinstance(val_a, dict) else ""
                val_b = val_b.get(p, "") if isinstance(val_b, dict) else ""

            spans_a.append(str(val_a) if val_a else "")
            spans_b.append(str(val_b) if val_b else "")

        precisions, recalls, f1s = [], [], []
        for a, b in zip(spans_a, spans_b):
            p, r, f = span_f1([a], [b])
            precisions.append(p)
            recalls.append(r)
            f1s.append(f)

        avg_p = sum(precisions) / len(precisions)
        avg_r = sum(recalls) / len(recalls)
        avg_f1 = sum(f1s) / len(f1s)

        results["metrics"][field_path] = {
            "type": "Span F1",
            "precision": round(avg_p, 4),
            "recall": round(avg_r, 4),
            "f1": round(avg_f1, 4),
            "n": len(spans_a),
        }

    # === Composite citation F1 ===
    all_citation_f1s = []
    for sid in common_ids:
        cit_a = annotations_a[sid].get("citation", {})
        cit_b = annotations_b[sid].get("citation", {})

        fields_match = []
        for f in ["document_name", "article", "clause"]:
            a_val = str(cit_a.get(f, "")).lower().strip()
            b_val = str(cit_b.get(f, "")).lower().strip()
            fields_match.append(a_val == b_val if a_val or b_val else True)

        all_citation_f1s.append(1.0 if all(fields_match) else 0.0)

    results["metrics"]["citation.composite"] = {
        "type": "Exact Match",
        "agreement": round(sum(all_citation_f1s) / len(all_citation_f1s), 4),
        "n": len(all_citation_f1s),
    }

    # === Summary ===
    kappas = [m["kappa"] for m in results["metrics"].values() if "kappa" in m]
    f1s = [m["f1"] for m in results["metrics"].values() if "f1" in m]

    results["summary"] = {
        "avg_kappa": round(sum(kappas) / len(kappas), 4) if kappas else 0.0,
        "avg_span_f1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0,
        "meets_target_kappa": all(k >= 0.75 for k in kappas),
        "meets_target_f1": all(f >= 0.80 for f in f1s) if f1s else True,
    }

    return results


def print_results(results: dict, label_a: str = "Annotator A", label_b: str = "Annotator B"):
    """Pretty print IAA results."""
    print(f"\n{'='*60}")
    print(f"INTER-ANNOTATOR AGREEMENT: {label_a} vs {label_b}")
    print(f"{'='*60}")
    print(f"Common samples: {results['n_samples']}")

    print(f"\n{'Field':<35} {'Type':<15} {'Score':<10} {'Target':<10}")
    print("-" * 70)

    for field, metric in results["metrics"].items():
        if metric["type"] == "Cohen's κ":
            score = f"κ={metric['kappa']:.3f}"
            target = "≥ 0.75"
            met = metric['kappa'] >= 0.75
        elif metric["type"] == "Span F1":
            score = f"F1={metric['f1']:.3f}"
            target = "≥ 0.80"
            met = metric['f1'] >= 0.80
        else:
            score = f"{metric['agreement']:.3f}"
            target = "≥ 0.80"
            met = metric['agreement'] >= 0.80

        status = "OK" if met else "LOW"
        print(f"  {field:<33} {metric['type']:<15} {score:<10} {target:<10} [{status}]")

    summary = results["summary"]
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Average κ:        {summary['avg_kappa']:.3f} {'PASS' if summary['meets_target_kappa'] else 'FAIL'}")
    print(f"  Average Span F1:  {summary['avg_span_f1']:.3f} {'PASS' if summary['meets_target_f1'] else 'FAIL'}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Calculate Inter-Annotator Agreement")
    parser.add_argument("--ann1", type=str, help="Path to annotator 1 JSONL")
    parser.add_argument("--ann2", type=str, help="Path to annotator 2 JSONL")
    parser.add_argument("--dir", type=str, help="Directory with annotation files")
    parser.add_argument("--pattern", type=str, default="*_annotated_*.jsonl",
                        help="File pattern for --dir mode")
    parser.add_argument("--output", type=str, default=None,
                        help="Save results to JSON file")
    args = parser.parse_args()

    if args.ann1 and args.ann2:
        # Compare two annotators
        ann1 = load_jsonl(args.ann1)
        ann2 = load_jsonl(args.ann2)
        results = compute_iaa(ann1, ann2)
        print_results(results, os.path.basename(args.ann1), os.path.basename(args.ann2))

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {args.output}")

    elif args.dir:
        # Compare all pairs in directory
        import glob
        files = glob.glob(os.path.join(args.dir, args.pattern))
        if len(files) < 2:
            print(f"Need at least 2 annotation files, found {len(files)}")
            return

        all_results = {}
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                ann1 = load_jsonl(files[i])
                ann2 = load_jsonl(files[j])
                key = f"{os.path.basename(files[i])}_vs_{os.path.basename(files[j])}"
                results = compute_iaa(ann1, ann2)
                all_results[key] = results
                print_results(results, os.path.basename(files[i]), os.path.basename(files[j]))

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {args.output}")
    else:
        print("Usage:")
        print("  --ann1 FILE --ann2 FILE    Compare two annotators")
        print("  --dir DIR                  Compare all pairs in directory")
        parser.print_help()


if __name__ == "__main__":
    main()
