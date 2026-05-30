# VLegal-Bench Reliability Framework - Team Guide

Paper: "A Reliability-Oriented Framework for Vietnamese Legal LLM Evaluation via VLegal-Bench Augmentation"

## Quick Start (2 phút)

```bash
# 1. Clone
git clone https://github.com/Drake-Phamta/A-Reliability-Oriented-Framework-for-Vietnamese-Legal-LLM-Evaluation-via-VLegal-Bench-Augmentation.git
cd A-Reliability-Oriented-Framework-for-Vietnamese-Legal-LLM-Evaluation-via-VLegal-Bench-Augmentation

# 2. Setup (Windows)
setup.bat

# 3. Edit .env với API key
# 4. Kiểm tra tiến độ
python tools/progress.py
```

## Dependency Graph

```
Member A                    Member B                 Member C
---------                   ---------                ---------
A1: Setup env               B1: Annotation           C1: Section 2 (ngay)
    |                           |                        |
A2: Baseline 1a ──┐        B2: IAA calc ──────┐    C2: Section 5 (đợi results)
A3: Baseline 1b   │        B3: Adjudication    │    C3: Section 6
A4: Baseline 2a   │            |                |
A5: Baseline 2b ──┤        B4: Table 1 ────────┤    C4: Case studies
    |             |                              |
A6: Fine-tune ────┤                              |
    |             |                              |
A7: Evaluate ─────┴──────────────────────────────┴──→ C5: Final review
```

## Phân công chi tiết

### THÀNH VIÊN A - Experiments & Infrastructure

#### Ngày 1: Setup
```bash
# Setup environment
setup.bat  # Windows
# hoặc: bash setup.sh  # Linux/Mac

# Edit .env
# OPENAI_API_KEY=sk-...  (hoặc GEMINI_API_KEY, hoặc local vLLM)

# Test pipeline (dry run)
python tools/run_experiments.py --model <model> --task 3.4 --system baseline_1a --dry_run

# Test thật (1 task nhỏ)
python tools/run_experiments.py --model <model> --task 3.4 --system baseline_1a
```

#### Ngày 2-4: Chạy 4 Baselines
```bash
# Chạy tuần tự hoặc song song (mỗi lệnh 1 terminal)
python tools/run_experiments.py --model <model> --system baseline_1a
python tools/run_experiments.py --model <model> --system baseline_1b
python tools/run_experiments.py --model <model> --system baseline_2a
python tools/run_experiments.py --model <model> --system baseline_2b

# Hoặc chạy tất cả cùng lúc
python tools/run_experiments.py --model <model> --all

# Kiểm tra tiến độ
python tools/progress.py
python tools/verify_experiments.py --all
```

#### Ngày 5-6: Fine-tune
```bash
# Baseline 3 (no reliability data)
python tools/finetune_lora.py --model <model> --mode baseline_3 --epochs 3

# Proposed (sau khi Member B có annotation)
python tools/finetune_lora.py --model <model> --mode proposed --epochs 3

# Chạy inference cho fine-tuned models
python tools/run_experiments.py --model <model> --system baseline_3
python tools/run_experiments.py --model <model> --system proposed
```

#### Ngày 7: Evaluate + Tables
```bash
# Tính metrics
python tools/evaluate_experiments.py --latex

# Generate tables
python tools/generate_tables.py --output experiments/latex/

# Verify
python tools/verify_experiments.py --all
```

---

### THÀNH VIÊN B - Annotation & Quality

#### Ngày 1: Đọc hướng dẫn + Calibration
```bash
# Đọc guideline
cat docs/annotation_guideline.md

# Annotate 10 mẫu đầu tiên (calibration)
python tools/annotation_tool.py --input annotations/1_4_subset.jsonl --output annotations/1_4_calib_B1.jsonl --task 1.4 --limit 10
```

#### Ngày 2-5: Annotation (mỗi người 3 tasks)
```bash
# ANNOTATOR 1 (tasks 1.4, 3.2, 4.1)
python tools/annotation_tool.py --input annotations/1_4_subset.jsonl --output annotations/1_4_annotated_B1.jsonl --task 1.4
python tools/annotation_tool.py --input annotations/3_2_subset.jsonl --output annotations/3_2_annotated_B1.jsonl --task 3.2
python tools/annotation_tool.py --input annotations/4_1_subset.jsonl --output annotations/4_1_annotated_B1.jsonl --task 4.1

# ANNOTATOR 2 (tasks 2.4, 3.3, 4.3)
python tools/annotation_tool.py --input annotations/2_4_subset.jsonl --output annotations/2_4_annotated_B2.jsonl --task 2.4
python tools/annotation_tool.py --input annotations/3_3_subset.jsonl --output annotations/3_3_annotated_B2.jsonl --task 3.3
python tools/annotation_tool.py --input annotations/4_3_subset.jsonl --output annotations/4_3_annotated_B2.jsonl --task 4.3

# Kiểm tra tiến độ
python tools/progress.py
```

#### Ngày 6: IAA + Adjudication
```bash
# Tính IAA
python tools/calculate_iaa.py --dir annotations/ --pattern "*_annotated_*.jsonl" --output annotations/iaa_results.json

# Review disagreements và adjudicate
# Tạo final annotation files
```

---

### THÀNH VIÊN C - Paper Writing

#### Ngày 1-3: Section 2 Related Work
- 2.1 LLM Foundations
- 2.2 Legal AI Applications
- 2.3 Legal Knowledge Infusion
- 2.4 Evaluation Frameworks for Legal LLMs

#### Ngày 4-5: Section 5 Results (sau khi Member A có results)
- 5.1 Core Benchmark Analysis
- 5.2 Reliability Metrics Analysis
- 5.3 Ablation Study
- 5.4 Case Studies (3 cases)

#### Ngày 6: Section 6 Discussion
- 6.1 Scholarly Implications
- 6.2 Practical Implications
- 6.3 Limitations

#### Ngày 7: Final Review
- Proofread
- Format check
- PDF render

---

## Tools Reference

| Tool | Command | Mô tả |
|------|---------|-------|
| `run_experiments.py` | `--model X --system Y` | Chạy experiments |
| `finetune_lora.py` | `--model X --mode Y` | Fine-tune LoRA |
| `evaluate_experiments.py` | `--latex` | Tính metrics |
| `generate_tables.py` | `--output dir/` | Tạo bảng LaTeX |
| `annotation_tool.py` | `--input X --output Y` | Annotation CLI |
| `calculate_iaa.py` | `--dir X --pattern Y` | Tính IAA |
| `verify_experiments.py` | `--all` | Verify outputs |
| `progress.py` | | Xem tiến độ |
| `generate_figure1.py` | `--output X` | Tạo Figure 1 |

## Prompt Modes

| Mode | Mô tả | Dùng cho |
|------|-------|----------|
| `zero_shot` | Chỉ EXAMPLE | Baseline 1a, 2a |
| `reasoning` | `<think>` + `<output>` | Baseline 1b, 2b, 3 |
| `reliability` | `<answer>` tag + citation | Proposed |

## 6 Reliability Metrics

| Metric | Tên | Mô tả |
|--------|-----|-------|
| CitAcc | Citation Accuracy | Trích dẫn đúng điều luật |
| RAS | Recency-Aware Score | Trọng số theo thời gian hiệu lực |
| RAR | Recency-Aware Recall | Recall có trọng số thời gian |
| ESR | Evidence Support Rate | Tỷ lệ được evidence hỗ trợ |
| UCR | Unsupported Claim Rate | Tỷ lệ claim không có cơ sở |
| AbsAcc | Abstention Accuracy | Từ chối trả lời đúng lúc |

## Troubleshooting

**Lỗi encoding Windows:**
```bash
python -X utf8 tools/progress.py
```

**Lỗi API key:**
```bash
# Kiểm tra .env
cat .env
# Đảm bảo có OPENAI_API_KEY hoặc GEMINI_API_KEY
```

**Lỗi import:**
```bash
# Đảm bảo đang trong venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**Kiểm tra kết quả:**
```bash
python tools/verify_experiments.py --all
python tools/progress.py
```
