# VLegal-Bench Reliability Framework

Paper: "A Reliability-Oriented Framework for Vietnamese Legal LLM Evaluation via VLegal-Bench Augmentation"

## Cài đặt

```bash
# Clone repo
git clone <your-github-url>
cd VLegal-Bench

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# Cài dependencies
pip install openai tiktoken rouge-score nltk python-dotenv tqdm

# (Optional) Cho fine-tune
pip install torch transformers peft trl datasets

# Setup API key
cp .env.example .env
# Edit .env với API key của bạn
```

## Cấu trúc thư mục

```
VLegal-Bench/
├── 1.1/ ... 5.4/          # 22 tasks (data + prompts)
├── src/
│   ├── evaluation.py       # Core metrics
│   └── reliability_metrics.py  # 6 reliability metrics
├── tools/
│   ├── run_experiments.py  # ⭐ Chạy experiments
│   ├── evaluate_experiments.py  # Tính metrics
│   ├── generate_tables.py  # Tạo bảng LaTeX
│   ├── finetune_lora.py    # LoRA fine-tune
│   ├── annotation_tool.py  # Annotation CLI
│   ├── calculate_iaa.py    # Tính IAA
│   └── generate_figure1.py # Tạo Figure 1
├── annotations/            # Subset files cho annotation
├── docs/                   # Hướng dẫn annotation
└── experiments/            # Kết quả experiments
```

## Phân công & Workflow

### Thành viên A - Experiments

```bash
# 1. Test pipeline
PROMPT_MODE=zero_shot bash infer.sh

# 2. Chạy 4 baselines
python tools/run_experiments.py --model <model_name> --system baseline_1a
python tools/run_experiments.py --model <model_name> --system baseline_1b
python tools/run_experiments.py --model <model_name> --system baseline_2a
python tools/run_experiments.py --model <model_name> --system baseline_2b

# 3. Fine-tune
python tools/finetune_lora.py --model <model_name> --mode baseline_3
python tools/finetune_lora.py --model <model_name> --mode proposed

# 4. Evaluate
python tools/evaluate_experiments.py --latex
python tools/generate_tables.py --stdout
```

### Thành viên B - Annotation

```bash
# 1. Đọc hướng dẫn
cat docs/annotation_guideline.md

# 2. Chạy annotation (mỗi người 2 tasks)
# Person B1: tasks 1.4, 3.2, 4.1
python tools/annotation_tool.py --input annotations/1_4_subset.jsonl --output annotations/1_4_annotated_B1.jsonl --task 1.4
python tools/annotation_tool.py --input annotations/3_2_subset.jsonl --output annotations/3_2_annotated_B1.jsonl --task 3.2
python tools/annotation_tool.py --input annotations/4_1_subset.jsonl --output annotations/4_1_annotated_B1.jsonl --task 4.1

# Person B2: tasks 2.4, 3.3, 4.3
python tools/annotation_tool.py --input annotations/2_4_subset.jsonl --output annotations/2_4_annotated_B2.jsonl --task 2.4
python tools/annotation_tool.py --input annotations/3_3_subset.jsonl --output annotations/3_3_annotated_B2.jsonl --task 3.3
python tools/annotation_tool.py --input annotations/4_3_subset.jsonl --output annotations/4_3_annotated_B2.jsonl --task 4.3

# 3. Tính IAA (sau khi cả 2 annotator xong overlapping tasks)
# Cả 6 tasks đều cần 2 annotators → overlap 100%
python tools/calculate_iaa.py --dir annotations/ --pattern "*_annotated_*.jsonl" --output annotations/iaa_results.json
```

### Thành viên C - Paper Writing

- Viết Section 2 Related Work (ngay)
- Viết Section 5, 6 (sau khi có results)
- Review + polish paper

## Prompt Modes

| Mode | Mô tả | Dùng cho |
|------|-------|----------|
| `zero_shot` | Chỉ EXAMPLE | Baseline 1a, 2a |
| `fewshot` | EXAMPLE + ví dụ | (Optional) |
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

## Output Files

```
experiments/
├── results/{system}/{model}/{task}_results.jsonl  # Raw predictions
├── evaluation_results.json                         # Aggregated metrics
├── latex/
│   ├── table1.tex                                  # Dataset stats
│   ├── table2_core_results.tex                     # Core benchmark
│   ├── table3_reliability_metrics.tex              # Reliability
│   ├── table4_ablation.tex                         # Ablation
│   └── figure1_framework.png                       # Framework diagram
└── models/{mode}/final/                            # Fine-tuned checkpoints
```
