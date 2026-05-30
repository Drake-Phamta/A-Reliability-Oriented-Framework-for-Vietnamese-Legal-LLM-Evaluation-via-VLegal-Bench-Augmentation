#!/usr/bin/env python3
"""
Update the annotation protocol section in the paper from draft to final version.

Usage:
    python tools/update_annotation_protocol.py
    python tools/update_annotation_protocol.py --dry-run
"""

import sys
import os
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from docx import Document
except ImportError:
    print("python-docx not installed. Run: pip install python-docx")
    sys.exit(1)


ANNOTATION_PROTOCOL_FINAL = """Annotation protocol. Annotation is performed by advanced law students (final-year undergraduate and postgraduate level) with demonstrated proficiency in Vietnamese civil, criminal, and administrative law, working under the direct supervision of licensed legal practitioners. All annotators complete a training phase covering the annotation schema, citation grounding conventions, temporal validity reasoning, and inter-annotator calibration exercises before working on production samples.

Each sample receives three annotation layers targeting distinct reliability dimensions:

Citation grounding. For each sample, annotators identify the authoritative source provisions supporting the correct answer. The annotation records the document name (full official title, e.g., "Bộ luật Dân sự 2015"), article number (e.g., "Điều 463"), clause number when applicable (e.g., "Khoản 1"), and an evidence passage containing the verbatim text from the statutory source. When multiple provisions are relevant, all are recorded. When the question does not explicitly cite a provision, annotators identify the most directly applicable article based on the legal substance of the question.

Temporal validity. For each cited provision, annotators record the promulgation date, effective date, expiration date (if applicable), and whether the provision has been superseded by a newer instrument. A binary validity label indicates whether the provision is in force at the query reference date specified in the sample (or at the current date if no reference date is given). This annotation layer is essential for evaluating whether models distinguish between current and historical legal provisions.

Reliability supervision. Beyond citation and temporal information, annotators assess the trustworthiness of each sample's expected answer. This includes: (i) evidence sufficiency—whether the information provided in the sample is sufficient to support a correct answer; (ii) unsupported claims—identification of any claims that cannot be grounded in the available evidence; (iii) hallucination type—classification of factual fabrication, citation hallucination (referencing non-existent provisions), or temporal confusion (citing superseded provisions); and (iv) should-abstain labeling—indicating whether a model should decline to answer due to insufficient evidence, ambiguous legal interpretation, or reliance on superseded law.

The annotation process follows three stages: (i) independent annotation, in which each annotator labels the sample without consulting others; (ii) adjudication, in which a supervising legal practitioner resolves disagreements by reference to the authoritative statutory text and its official amendment history; and (iii) cross-validation, in which a random 10% of adjudicated samples are re-examined by all annotators to verify consistency. Each sample is assigned to a team of two independent annotators, with a third annotator available for adjudication when disagreement exceeds threshold on any field.

Edge cases are handled according to documented rules: when a provision has been amended, annotators record both the original and amended versions; when a question references a specific date, temporal validity is assessed relative to that date; when a question is ambiguous or lacks sufficient context, the sample is labeled should-abstain with the specific reason documented."""


def find_annotation_protocol_paragraph(doc: Document):
    """Find the paragraph containing the annotation protocol draft."""
    for i, para in enumerate(doc.paragraphs):
        if "Annotation protocol." in para.text and "(draft)" in para.text:
            return i, para
    return None, None


def update_protocol(doc: Document, dry_run: bool = False) -> bool:
    """Update the annotation protocol paragraph."""
    idx, para = find_annotation_protocol_paragraph(doc)

    if para is None:
        print("WARNING: Annotation protocol draft not found in document")
        return False

    print(f"Found annotation protocol at paragraph {idx}")
    print(f"Current text (first 100 chars): {para.text[:100]}...")

    if dry_run:
        print("\n[Dry run] Would replace with:")
        print(ANNOTATION_PROTOCOL_FINAL[:200] + "...")
        return True

    # Clear existing runs
    for run in para.runs:
        run.text = ""

    # Set new text in the first run
    if para.runs:
        para.runs[0].text = ANNOTATION_PROTOCOL_FINAL
    else:
        para.text = ANNOTATION_PROTOCOL_FINAL

    print("Updated annotation protocol to final version")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update annotation protocol in paper")
    parser.add_argument("--paper", type=str, default="paper/legal_llm_paper_ptit.docx",
                        help="Path to paper docx")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path (default: overwrite original)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be changed without modifying")
    args = parser.parse_args()

    if not os.path.exists(args.paper):
        print(f"Paper not found: {args.paper}")
        return

    doc = Document(args.paper)
    print(f"Loaded: {args.paper}")

    success = update_protocol(doc, dry_run=args.dry_run)

    if success and not args.dry_run:
        output = args.output or args.paper
        doc.save(output)
        print(f"\nSaved to: {output}")


if __name__ == "__main__":
    main()
