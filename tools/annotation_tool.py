#!/usr/bin/env python3
"""
Annotation Tool for VLegal-Bench Reliability Labels

CLI tool for annotators to label samples with:
- Citation grounding (document, article, clause, evidence passage)
- Temporal validity (dates, validity status)
- Reliability supervision (evidence sufficiency, unsupported claims, abstention)

Usage:
    python tools/annotation_tool.py --input 1.4/1_4.jsonl --output annotations/1_4_annotated.jsonl --task 1.4
"""

import json
import os
import argparse
import sys
from datetime import datetime

# Fix UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')


def load_jsonl(path: str) -> list:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def load_annotated_ids(path: str) -> set:
    """Load IDs of already-annotated samples to support resume."""
    ids = set()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    ann = json.loads(line)
                    ids.add(ann.get('sample_id', ''))
    return ids


def save_annotation(path: str, annotation: dict):
    """Append a single annotation to the output JSONL file."""
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(annotation, ensure_ascii=False) + '\n')


def get_sample_id(item: dict, idx: int, task: str) -> str:
    """Generate a unique sample ID."""
    if 'id' in item and item['id']:
        return f"{task}_{item['id']}"
    return f"{task}_{idx:04d}"


def display_sample(item: dict, idx: int, total: int):
    """Display a sample to the annotator."""
    print("\n" + "=" * 80)
    print(f"  SAMPLE {idx + 1} / {total}")
    print("=" * 80)

    # Show instruction
    instruction = item.get('instruction', '')
    if instruction:
        print(f"\n[Instruction]: {instruction[:300]}...")

    # Show question/context
    question = item.get('question', item.get('description', ''))
    if question:
        print(f"\n[Question]: {question[:500]}...")

    # Show context fields
    for field in ['content', 'document', 'article', 'court_judgement', 'description']:
        if field in item and item[field]:
            val = str(item[field])
            print(f"\n[{field}]: {val[:400]}...")

    # Show answers (for MC tasks)
    answers = item.get('answers', '')
    if answers:
        print(f"\n[Answers]: {str(answers)[:300]}...")

    # Show ground truth
    gt = item.get('ground_truth', item.get('answer', ''))
    if gt:
        print(f"\n[Ground Truth]: {gt}")

    print("-" * 80)


def prompt_input(prompt_text: str, default: str = "") -> str:
    """Prompt user for input with optional default."""
    if default:
        val = input(f"  {prompt_text} [{default}]: ").strip()
        return val if val else default
    else:
        val = input(f"  {prompt_text}: ").strip()
        return val


def prompt_bool(prompt_text: str, default: bool = False) -> bool:
    """Prompt user for boolean input."""
    default_str = "Y/n" if default else "y/N"
    val = input(f"  {prompt_text} [{default_str}]: ").strip().lower()
    if not val:
        return default
    return val in ('y', 'yes', 'true', '1')


def annotate_citation() -> dict:
    """Collect citation grounding annotation."""
    print("\n  --- Citation Grounding ---")
    doc_name = prompt_input("  Tên văn bản pháp luật (VD: Bộ luật Dân sự 2015)")
    article = prompt_input("  Điều (VD: Điều 463)")
    clause = prompt_input("  Khoản (VD: Khoản 1) [Enter để bỏ qua]")
    evidence = prompt_input("  Đoạn trích dẫn (evidence passage) [Enter để bỏ qua]")

    citation = {
        'document_name': doc_name,
        'article': article,
    }
    if clause:
        citation['clause'] = clause
    if evidence:
        citation['evidence_passage'] = evidence

    return citation


def annotate_temporal() -> dict:
    """Collect temporal validity annotation."""
    print("\n  --- Temporal Validity ---")
    promul = prompt_input("  Ngày ban hành (VD: 2015-11-24) [Enter nếu không rõ]")
    effective = prompt_input("  Ngày có hiệu lực (VD: 2017-01-01) [Enter nếu không rõ]")
    expiry = prompt_input("  Ngày hết hiệu lực [Enter nếu còn hiệu lực]")
    superseded = prompt_input("  Văn bản thay thế [Enter nếu không có]")
    query_date = prompt_input("  Ngày tham chiếu truy vấn (VD: 2024-06-15) [Enter nếu không có]")

    temporal = {}
    if promul:
        temporal['promulgation_date'] = promul
    if effective:
        temporal['effective_date'] = effective
    if expiry:
        temporal['expiration_date'] = expiry
    if superseded:
        temporal['superseded_by'] = superseded
    if query_date:
        temporal['query_reference_date'] = query_date

    # Ask validity status
    if query_date:
        valid = prompt_bool(f"  Văn bản có hiệu lực tại ngày {query_date}?", default=True)
        temporal['valid_at_query_date'] = valid
    else:
        temporal['valid_at_query_date'] = True

    return temporal


def annotate_reliability() -> dict:
    """Collect reliability supervision annotation."""
    print("\n  --- Reliability Supervision ---")

    sufficient = prompt_bool("  Evidence có đủ để hỗ trợ kết luận không?", default=True)

    unsupported = []
    if not sufficient:
        claims_str = prompt_input("  Các claim không được hỗ trợ (phân tách bằng ';') [Enter nếu không có]")
        if claims_str:
            unsupported = [c.strip() for c in claims_str.split(';') if c.strip()]

    # Hallucination type
    print("  Loại hallucination:")
    print("    0. Không có")
    print("    1. Factual fabrication (bịa đặt sự thật)")
    print("    2. Citation hallucination (bịa đặt điều luật)")
    print("    3. Temporal confusion (nhầm lẫn thời gian)")
    hall_type_input = prompt_input("  Chọn (0/1/2/3)", default="0")
    hall_types = {'0': None, '1': 'factual_fabrication', '2': 'citation_hallucination', '3': 'temporal_confusion'}
    hall_type = hall_types.get(hall_type_input, None)

    # Should abstain
    should_abstain = prompt_bool("  Model nên từ chối trả lời (abstain)?", default=False)
    abstain_reason = ""
    if should_abstain:
        abstain_reason = prompt_input("  Lý do nên abstain")

    reliability = {
        'evidence_sufficient': sufficient,
        'unsupported_claims': unsupported,
        'hallucination_type': hall_type,
        'should_abstain': should_abstain,
    }
    if abstain_reason:
        reliability['abstain_reason'] = abstain_reason

    return reliability


def annotate_sample(item: dict, sample_id: str) -> dict:
    """Run full annotation workflow for one sample."""
    annotation = {
        'sample_id': sample_id,
        'timestamp': datetime.now().isoformat(),
    }

    # Citation grounding
    print("\n[Bước 1/3] Citation Grounding - Trích dẫn nguồn")
    skip_citation = prompt_bool("  Bỏ qua annotation citation?", default=False)
    if not skip_citation:
        annotation['citation'] = annotate_citation()
    else:
        annotation['citation'] = {}

    # Temporal validity
    print("\n[Bước 2/3] Temporal Validity - Hiệu lực thời gian")
    skip_temporal = prompt_bool("  Bỏ qua annotation temporal?", default=False)
    if not skip_temporal:
        annotation['temporal'] = annotate_temporal()
    else:
        annotation['temporal'] = {}

    # Reliability supervision
    print("\n[Bước 3/3] Reliability Supervision - Giám sát độ tin cậy")
    skip_reliability = prompt_bool("  Bỏ qua annotation reliability?", default=False)
    if not skip_reliability:
        annotation['reliability'] = annotate_reliability()
    else:
        annotation['reliability'] = {}

    return annotation


def main():
    parser = argparse.ArgumentParser(description="VLegal-Bench Annotation Tool")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to input JSONL dataset file")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to output annotated JSONL file")
    parser.add_argument("--task", type=str, required=True,
                        help="Task ID (e.g., 1.4, 2.4, 4.1)")
    parser.add_argument("--start", type=int, default=0,
                        help="Start index (for resuming)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of samples to annotate")
    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.input}...")
    data = load_jsonl(args.input)
    print(f"Loaded {len(data)} samples")

    # Load already-annotated IDs for resume support
    annotated_ids = load_annotated_ids(args.output)
    print(f"Already annotated: {len(annotated_ids)} samples")

    # Filter out already-annotated
    remaining = []
    for idx, item in enumerate(data):
        sample_id = get_sample_id(item, idx, args.task)
        if sample_id not in annotated_ids:
            remaining.append((idx, item, sample_id))

    if args.start > 0:
        remaining = remaining[args.start:]
    if args.limit:
        remaining = remaining[:args.limit]

    print(f"Remaining to annotate: {len(remaining)} samples")
    print("\nHướng dẫn:")
    print("  - Nhập thông tin theo prompt")
    print("  - Nhập Enter để bỏ qua field optional")
    print("  - Ctrl+C để thoát bất cứ lúc nào (progress đã lưu tự động)")

    try:
        for count, (idx, item, sample_id) in enumerate(remaining):
            display_sample(item, idx, len(data))
            print(f"\n  Sample ID: {sample_id}")

            # Ask if want to skip this sample
            skip = prompt_bool("  Bỏ qua sample này?", default=False)
            if skip:
                # Save empty annotation to mark as skipped
                annotation = {
                    'sample_id': sample_id,
                    'timestamp': datetime.now().isoformat(),
                    'skipped': True,
                    'citation': {},
                    'temporal': {},
                    'reliability': {}
                }
                save_annotation(args.output, annotation)
                print("  [Skipped]")
                continue

            # Run annotation
            annotation = annotate_sample(item, sample_id)

            # Confirm
            print("\n  [Annotation summary]")
            print(f"    Citation: {json.dumps(annotation.get('citation', {}), ensure_ascii=False)[:100]}")
            print(f"    Temporal: {json.dumps(annotation.get('temporal', {}), ensure_ascii=False)[:100]}")
            print(f"    Reliability: {json.dumps(annotation.get('reliability', {}), ensure_ascii=False)[:100]}")

            confirm = prompt_bool("  Lưu annotation này?", default=True)
            if confirm:
                save_annotation(args.output, annotation)
                print(f"  [Saved] ({count + 1}/{len(remaining)})")
            else:
                print("  [Discarded]")

    except KeyboardInterrupt:
        print("\n\n  Thoát. Progress đã được lưu.")
        sys.exit(0)

    print(f"\nHoàn thành! Đã annotate {len(remaining)} samples.")
    print(f"Kết quả lưu tại: {args.output}")


if __name__ == "__main__":
    main()
