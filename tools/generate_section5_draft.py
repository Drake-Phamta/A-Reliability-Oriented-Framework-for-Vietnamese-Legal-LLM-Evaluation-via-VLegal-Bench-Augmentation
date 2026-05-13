#!/usr/bin/env python3
"""
Generate Section 5 draft with placeholder structure.

Creates a structured draft for Section 5 (Results) that Member C can fill in
with actual numbers after experiments complete.

Usage:
    python tools/generate_section5_draft.py --output paper/section5_draft.md
"""

import os
import argparse


def generate_section5_draft() -> str:
    return """## 5. Results

### 5.1 Performance on Core Benchmark

Table 2 presents the performance of six experimental systems across five task categories in VLegal-Bench.

| System | 1.x | 2.x | 3.x | 4.x | 5.x | Avg. |
|--------|-----|-----|-----|-----|-----|------|
| Baseline 1a (Zero-shot) | -- | -- | -- | -- | -- | -- |
| Baseline 1b (Reasoning) | -- | -- | -- | -- | -- | -- |
| Baseline 2a (Legal Prompt) | -- | -- | -- | -- | -- | -- |
| Baseline 2b (Legal+Reasoning) | -- | -- | -- | -- | -- | -- |
| Baseline 3 (LoRA, no rel.) | -- | -- | -- | -- | -- | -- |
| Proposed (LoRA + rel.) | -- | -- | -- | -- | -- | -- |

**Key findings:**

[TODO: Phân tích theo category]
- Category 1.x (Recognition & Recall): [TODO]
- Category 2.x (Understanding & Structuring): [TODO]
- Category 3.x (Reasoning & Inference): [TODO]
- Category 4.x (Interpretation & Generation): [TODO]
- Category 5.x (Ethics, Fairness & Bias): [TODO]

[TODO: So sánh giữa các hệ thống]
- Zero-shot vs Reasoning: [TODO]
- Without vs With legal prompt: [TODO]
- Without vs With LoRA: [TODO]

### 5.2 Performance on Reliability Metrics

Table 3 reports six reliability metrics on the annotated subset.

| System | CitAcc | RAS | RAR | ESR | UCR | AbsAcc |
|--------|--------|-----|-----|-----|-----|--------|
| Baseline 1a | -- | -- | -- | -- | -- | -- |
| Baseline 1b | -- | -- | -- | -- | -- | -- |
| Baseline 2a | -- | -- | -- | -- | -- | -- |
| Baseline 2b | -- | -- | -- | -- | -- | -- |
| Baseline 3 | -- | -- | -- | -- | -- | -- |
| Proposed | -- | -- | -- | -- | -- | -- |

**Key findings:**

[TODO: Phân tích từng metric]
- Citation Accuracy (CitAcc): [TODO]
- Recency-Aware Score (RAS): [TODO]
- Evidence Support Rate (ESR): [TODO]
- Abstention Accuracy (AbsAcc): [TODO]

[TODO: Correlation giữa core metrics và reliability metrics]

### 5.3 Ablation Study

Table 4 presents the ablation analysis showing the contribution of each component.

| Component | Acc. | F1 | CitAcc | RAS | ESR | AbsAcc |
|-----------|------|----|--------|-----|-----|--------|
| Base (Zero-shot) | -- | -- | -- | -- | -- | -- |
| + Reasoning | -- | -- | -- | -- | -- | -- |
| + Legal Prompt | -- | -- | -- | -- | -- | -- |
| + LoRA | -- | -- | -- | -- | -- | -- |
| + Reliability Training | -- | -- | -- | -- | -- | -- |

**Key findings:**

[TODO: Contribution của từng component]
- Reasoning prompt: [TODO]
- Legal system prompt: [TODO]
- LoRA fine-tuning: [TODO]
- Reliability annotation training: [TODO]

### 5.4 Case Study Analysis

We present three representative case studies illustrating key reliability challenges.

#### Case 1: Citation Hallucination

[TODO: Chọn 1 mẫu từ results mà model bịa đặt điều luật]
- Input: [TODO]
- Model output: [TODO]
- Ground truth: [TODO]
- Analysis: [TODO]

#### Case 2: Temporal Confusion

[TODO: Chọn 1 mẫu mà model dùng luật đã hết hiệu lực]
- Input: [TODO]
- Model output: [TODO]
- Ground truth: [TODO]
- Analysis: [TODO]

#### Case 3: Abstention Failure

[TODO: Chọn 1 mẫu mà model trả lời khi lẽ ra nên abstain]
- Input: [TODO]
- Model output: [TODO]
- Expected: [TODO]
- Analysis: [TODO]
"""


def main():
    parser = argparse.ArgumentParser(description="Generate Section 5 draft")
    parser.add_argument("--output", type=str, default="paper/section5_draft.md",
                        help="Output file path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    draft = generate_section5_draft()
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(draft)

    print(f"Section 5 draft saved to: {args.output}")
    print("Member C: Fill in [TODO] placeholders after experiments complete.")


if __name__ == "__main__":
    main()
