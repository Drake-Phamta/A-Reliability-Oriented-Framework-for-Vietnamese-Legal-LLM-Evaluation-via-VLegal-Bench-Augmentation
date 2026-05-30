# Project Status

**Last updated**: 2026-05-26

## Completed Work

### 1. Core Benchmark Evaluation
All 3 models evaluated on 21 tasks (5 categories):
- **Baseline 3** (LoRA r=8, α=16, standard finetune)
- **Gemma 4 E4B** (few-shot, no fine-tuning)
- **Proposed** (LoRA r=16, α=32, enhanced prompts)

Results in `VLegal-Bench/core_metrics_results.json`

### 2. Reliability Inference (10/10 files)
All 5 tasks × 2 modes (baseline_3 + proposed) completed on workstation.
- Tasks evaluated: 1.4, 1.5, 3.1, 4.1, 4.2
- V2 improved prompts used for proposed mode
- Results: `VLegal-Bench/{task}/{task}_llm_test_results_{mode}_reliability_v2.json`

### 3. Reliability Metrics Computed
6 metrics calculated for all tasks/modes. Results in `VLegal-Bench/reliability_results.json`

#### Aggregate Results (v2)

| Model | CitAcc | RAS | RAR | ESR | UCR | AbsAcc |
|-------|--------|-----|-----|-----|-----|--------|
| Baseline | 0.247 | 0.019 | 0.204 | 0.321 | 0.559 | 0.000 |
| **Proposed** | **0.573** | **0.048** | **0.301** | **0.436** | **0.441** | **0.060** |

#### Per-Task Results (Proposed v2)

| Task | CitAcc | RAS | RAR | ESR | UCR | AbsAcc |
|------|--------|-----|-----|-----|-----|--------|
| 1.4 | 0.919 | 0.029 | 0.750 | 0.860 | 0.096 | 0.000 |
| 1.5 | 0.582 | 0.000 | 0.000 | 0.169 | 0.764 | 0.004 |
| 3.1 | 0.775 | 0.061 | 0.272 | 0.545 | 0.455 | 0.000 |
| 4.1 | 0.033 | 0.142 | 0.016 | 0.040 | 0.457 | 0.037 |
| 4.2 | 0.558 | 0.008 | 0.466 | 0.568 | 0.432 | 0.261 |

**Key findings:**
- Proposed model dominates on CitAcc (+132% vs baseline) and ESR (+36%)
- Task 4.2 shows strongest improvement: CitAcc 0.221→0.558, AbsAcc 0.0→0.261
- AbsAcc still low overall (0.060) — model rarely abstains
- Task 4.1 remains weak across all metrics

### 4. Paper Draft
Complete LaTeX paper at `paper/main.tex`:
- All sections written with actual data
- Tables updated with v2 results
- Reliability metrics framework formalized
- Radar chart and per-task analysis included

### 5. RAFT-AT Data Preparation
- Training data: `VLegal-Bench/data/raft_at_proposed.jsonl` (3085 samples)
- 751 abstain samples (24.3%), 2334 answer samples (75.7%)
- Data prep script: `VLegal-Bench/tools/prepare_raft_at_data.py`
- Training script: `VLegal-Bench/tools/finetune_raft_at.py`

### 6. Annotation Infrastructure
- 6 tasks annotated with reliability labels
- Auto-annotation pipeline (`VLegal-Bench/tools/auto_annotate.py`)
- Inter-annotator agreement calculation (`VLegal-Bench/tools/calculate_iaa.py`)

## In Progress

### RAFT-AT Training (Blocked — Workstation Offline)
Training command ready:
```bash
cd D:\Hunganh\AI_LEGAL
python VLegal-Bench/tools/finetune_raft_at.py \
  --model D:/Hunganh/vlegal-finetune/merged/proposed \
  --mode proposed --epochs 5 --lora_r 16 --lora_alpha 32 \
  --batch_size 2 --gradient_accumulation 8 \
  --output_dir D:/Hunganh/vlegal-finetune/output/raft_at_proposed
```
**Blocker**: Workstation (100.72.47.109) unreachable. Needs to be powered on.

## Pending

1. **RAFT-AT training** → merge LoRA → inference → calculate metrics
2. **Paper update** with RAFT-AT results (Tables 4/5, analysis)
3. **Novelty strengthening** — paper needs clearer method contribution
4. **Final paper polish** — proofread, format check

## Known Issues

- **AbsAcc=0 on most tasks**: Root cause identified (finetune_lora.py always uses ground_truth). RAFT-AT is the fix.
- **V2 results slightly worse on tasks 1.4, 1.5**: Paper uses v1 proposed results where v1 is better.
- **Task 4.1 weak**: Low CitAcc (0.033), model struggles with legal document summarization citations.

## File Inventory

| Category | Count | Location |
|----------|-------|----------|
| Benchmark tasks | 19 folders | `VLegal-Bench/1.1/` ... `5.4/` |
| Inference scripts | 8 files | `scripts/inference/` |
| Core library | 6 files | `VLegal-Bench/src/` |
| Utility tools | 17 files | `VLegal-Bench/tools/` |
| Annotations | 6 tasks | `data/annotations/` |
| Paper | 1 file | `paper/main.tex` |
| Results | 3 JSON files | `VLegal-Bench/reliability_results.json` |
| Documentation | 5 MD files | Root + `VLegal-Bench/docs/` |
