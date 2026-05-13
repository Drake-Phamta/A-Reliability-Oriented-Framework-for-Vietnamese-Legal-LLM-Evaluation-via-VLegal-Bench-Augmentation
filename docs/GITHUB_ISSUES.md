# GitHub Issues - Copy paste vào GitHub

---

## Issue 1: [Member A] Setup + Run 4 Baselines

**Labels:** `experiments`, `priority-high`

### Mô tả
Setup môi trường và chạy 4 baseline systems trên 22 tasks.

### Checklist

#### Setup (0.5 ngày)
- [ ] Clone repo: `git clone <url>`
- [ ] Chạy setup: `setup.bat` (Windows) hoặc `bash setup.sh`
- [ ] Edit `.env` với API key (Gemini/OpenAI/local vLLM)
- [ ] Test: `python tools/run_experiments.py --model <model> --task 3.4 --system baseline_1a --dry_run`

#### Chạy Baselines (2-4 ngày)
- [ ] Baseline 1a (zero-shot, 22 tasks)
- [ ] Baseline 1b (reasoning, 22 tasks)
- [ ] Baseline 2a (legal prompt, 22 tasks)
- [ ] Baseline 2b (legal+reasoning, 22 tasks)

#### Commands
```bash
# Chạy từng system
python tools/run_experiments.py --model <model> --system baseline_1a
python tools/run_experiments.py --model <model> --system baseline_1b
python tools/run_experiments.py --model <model> --system baseline_2a
python tools/run_experiments.py --model <model> --system baseline_2b

# Kiểm tra tiến độ
python tools/progress.py
python tools/verify_experiments.py --all
```

#### Evaluate (0.5 ngày)
- [ ] `python tools/evaluate_experiments.py --latex`
- [ ] `python tools/generate_tables.py --output experiments/latex/`
- [ ] Điền implementation details vào paper

### Output
- `experiments/results/{system}/{model}/*.jsonl` (22 files × 4 systems)
- `experiments/evaluation_results.json`
- `experiments/latex/table*.tex`

---

## Issue 2: [Member A] Fine-tune LoRA

**Labels:** `experiments`, `fine-tune`
**Depends on:** Issue 1

### Mô tả
Fine-tune model với LoRA cho Baseline 3 và Proposed.

### Checklist
- [ ] Baseline 3 (no reliability data): `python tools/finetune_lora.py --model <model> --mode baseline_3`
- [ ] Proposed (with reliability data): `python tools/finetune_lora.py --model <model> --mode proposed`
- [ ] Chạy inference cho cả 2: `python tools/run_experiments.py --model <model> --system baseline_3` và `proposed`
- [ ] Evaluate: `python tools/evaluate_experiments.py --latex`

### Output
- `experiments/models/baseline_3/final/`
- `experiments/models/proposed/final/`
- Updated `experiments/latex/table*.tex`

---

## Issue 3: [Member B] Annotation - Batch 1 (Tasks 1.4, 3.2, 4.1)

**Labels:** `annotation`, `priority-high`

### Mô tả
Annotate 750 samples (250 × 3 tasks) cho annotator 1.

### Checklist
- [ ] Đọc `docs/annotation_guideline.md`
- [ ] Task 1.4 (250 samples): `python tools/annotation_tool.py --input annotations/1_4_subset.jsonl --output annotations/1_4_annotated_B1.jsonl --task 1.4`
- [ ] Task 3.2 (250 samples): `python tools/annotation_tool.py --input annotations/3_2_subset.jsonl --output annotations/3_2_annotated_B1.jsonl --task 3.2`
- [ ] Task 4.1 (250 samples): `python tools/annotation_tool.py --input annotations/4_1_subset.jsonl --output annotations/4_1_annotated_B1.jsonl --task 4.1`

### Thời gian: 3-4 ngày (250 samples × 1-2 min/sample)

### Output
- `annotations/1_4_annotated_B1.jsonl`
- `annotations/3_2_annotated_B1.jsonl`
- `annotations/4_1_annotated_B1.jsonl`

---

## Issue 4: [Member B] Annotation - Batch 2 (Tasks 2.4, 3.3, 4.3)

**Labels:** `annotation`, `priority-high`

### Mô tả
Annotate 750 samples (250 × 3 tasks) cho annotator 2.

### Checklist
- [ ] Đọc `docs/annotation_guideline.md`
- [ ] Task 2.4 (250 samples): `python tools/annotation_tool.py --input annotations/2_4_subset.jsonl --output annotations/2_4_annotated_B2.jsonl --task 2.4`
- [ ] Task 3.3 (250 samples): `python tools/annotation_tool.py --input annotations/3_3_subset.jsonl --output annotations/3_3_annotated_B2.jsonl --task 3.3`
- [ ] Task 4.3 (250 samples): `python tools/annotation_tool.py --input annotations/4_3_subset.jsonl --output annotations/4_3_annotated_B2.jsonl --task 4.3`

### Output
- `annotations/2_4_annotated_B2.jsonl`
- `annotations/3_3_annotated_B2.jsonl`
- `annotations/4_3_annotated_B2.jsonl`

---

## Issue 5: [Member B] IAA + Adjudication

**Labels:** `annotation`, `quality`
**Depends on:** Issue 3, Issue 4

### Mô tả
Tính Inter-Annotator Agreement và xử lý disagreement.

### Checklist
- [ ] Cả 2 annotators annotate overlapping 10% samples (25 samples/task)
- [ ] Tính IAA: `python tools/calculate_iaa.py --dir annotations/ --pattern "*_annotated_*.jsonl" --output annotations/iaa_results.json`
- [ ] Kiểm tra target: Cohen's κ ≥ 0.75, Span F1 ≥ 0.80
- [ ] Adjudication: review samples có disagreement > 50%
- [ ] Tạo final annotation files: `*_final.jsonl`
- [ ] Generate Table 1: `python tools/generate_tables.py --stdout --table 1`

### Output
- `annotations/iaa_results.json`
- `annotations/*_final.jsonl`
- IAA scores cho paper

---

## Issue 6: [Member C] Viết Section 2 Related Work

**Labels:** `paper`, `priority-high`

### Mô tả
Viết Section 2 Related Work cho paper.

### Checklist
- [ ] 2.1 LLM Foundations (LLMs, instruction tuning, PEFT/LoRA)
- [ ] 2.2 Legal AI Applications (legal QA, document analysis, judicial reasoning)
- [ ] 2.3 Legal Knowledge Infusion (domain adaptation, legal corpora)
- [ ] 2.4 Evaluation Frameworks for Legal LLMs (benchmarks, metrics, reliability)
- [ ] Review 18 refs hiện có, bổ sung thêm nếu cần

### Tham khảo
- Paper hiện có: `legal_llm_paper_ptit.docx`
- 18 references đã có trong paper

### Output
- Section 2 text (copy vào paper)

---

## Issue 7: [Member C] Viết Section 5 + 6 (sau khi có results)

**Labels:** `paper`, `priority-medium`
**Depends on:** Issue 1, Issue 5

### Mô tả
Viết phân tích kết quả và discussion sau khi có experiment data.

### Checklist
- [ ] 5.1 Core Benchmark Analysis (so sánh 6 systems, phân tích theo category)
- [ ] 5.2 Reliability Metrics Analysis (6 metrics, so sánh systems)
- [ ] 5.3 Ablation Study (từng component: reasoning, legal prompt, LoRA, reliability)
- [ ] 5.4 Case Studies (3 cases: citation hallucination, temporal confusion, abstention)
- [ ] 6.1 Scholarly Implications
- [ ] 6.2 Practical Implications
- [ ] 6.3 Limitations
- [ ] Review + polish toàn bộ paper

### Tham khảo
- `experiments/evaluation_results.json` (sau khi Member A chạy xong)
- `experiments/latex/*.tex`
- `annotations/iaa_results.json` (sau khi Member B tính xong)

### Output
- Section 5, 6 text
- Final paper draft

---

## Issue 8: [All] Final Review

**Labels:** `paper`, `final`
**Depends on:** All previous issues

### Checklist
- [ ] Member A: Verify all tables match experiments
- [ ] Member B: Verify IAA scores in paper
- [ ] Member C: Proofread, format check
- [ ] All: Author info filled
- [ ] All: PDF render check
- [ ] All: Submit
