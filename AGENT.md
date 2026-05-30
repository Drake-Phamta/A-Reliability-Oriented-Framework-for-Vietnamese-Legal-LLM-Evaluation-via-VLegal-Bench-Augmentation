# AGENT.md — Hướng dẫn cho AI Agent

## 1. Tổng quan dự án

**Tên dự án:** VLegal-Bench — Reliability-Oriented Framework for Vietnamese Legal LLM Evaluation
**Paper:** ICIS 2026 submission
**Mục tiêu:** Đánh giá và cải thiện độ tin cậy của LLM trong lĩnh vực pháp luật Việt Nam

### Cấu trúc repository
```
D:\AI_LEGAL\
├── paper/                    # Paper LaTeX
│   ├── main.tex              # Paper chính (20 pages, compiles sạch)
│   ├── references.bib        # Bibliography
│   └── latex2md.py           # Convert LaTeX → markdown
├── VLegal-Bench/             # Benchmark code
│   ├── 1.1/ ... 5.4/         # 22 task folders (chỉ chứa .jsonl + prompt_*.py)
│   ├── src/                  # Core library (evaluation.py, reliability_metrics.py)
│   ├── tools/                # Training & utility scripts
│   ├── data/                 # Training data (raft_at_*.jsonl)
│   ├── annotations/          # Reliability annotations (6 tasks)
│   └── _corrupted/           # 101 file LLM test results bị hỏng (KHÔNG dùng)
├── AGENT.md                  # File này
├── PROJECT_STATUS.md         # Trạng thái dự án
└── ROADMAP.md                # Kế hoạch
```

---

## 2. Kết nối Workstation

- **Host:** `100.72.47.109`
- **User:** `ADMIN`
- **Password:** `11`
- **Root path:** `D:\Hunganh`
- **GPU:** NVIDIA GeForce RTX 3090 Ti (24GB VRAM)
- **Python:** 3.11.9
- **CUDA:** 13.1

### SSH via Paramiko (Python)
```python
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('100.72.47.109', username='ADMIN', password='11', timeout=10)

# Run command
stdin, stdout, stderr = client.exec_command('nvidia-smi', timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# File transfer via SFTP
sftp = client.open_sftp()
with sftp.open('D:/Hunganh/AI_LEGAL/script.py', 'w') as f:
    f.write(content)
sftp.close()
```

### Quy tắc an toàn (từ agent.md gốc)
- **KHÔNG reboot** workstation
- **KHÔNG xóa file** ngoài thư mục dự án
- **CHỈ làm việc** trong `D:\Hunganh\AI_LEGAL\`

---

## 3. Models & Checkpoints

### Base model
- **Tên:** `google/gemma-4-E4B-it` (Gemma 4, ~4B params, multimodal)
- **Checkpoint:** `D:/Hunganh/vlegal-finetune/merged/proposed`
- **Architecture:** `Gemma4ForConditionalGeneration` (multimodal: vision + audio + text)
- **Config:** `text_config.hidden_size=2560`, `num_hidden_layers=42`, `vocab_size=262144`

### Fine-tuned models
| Model | Path | Mô tả |
|-------|------|-------|
| Baseline 3 | `D:/Hunganh/vlegal-finetune/merged/baseline_3` | LoRA r=8, α=16, simple format |
| Proposed | `D:/Hunganh/vlegal-finetune/merged/proposed` | LoRA r=16, α=32, reasoning format |

### Checkpoint formats
- **Original:** Weights có prefix `model.language_model.*` (multimodal format)
- **Text-only:** Đã convert sang `model.*` prefix → `proposed_text/` (dùng cho Gemma4ForCausalLM)

---

## 4. Vấn đề đã biết & Fixes

### 4.1 Import crash (exit code 3221225477)
**Nguyên nhân:** `from transformers import Trainer` crash nếu import SAU `TrainingArguments` mà không có `import accelerate` trước.

**Fix:** Import theo thứ tự:
```python
import accelerate          # PHẢI có trước
import torch
from transformers import Trainer           # Trainer TRƯỚC
from transformers import TrainingArguments # TrainingArguments SAU
from transformers import AutoTokenizer
from transformers import Gemma4ForCausalLM  # Không dùng AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
```

### 4.2 Gemma4 checkpoint mismatch
**Nguyên nhân:** Checkpoint lưu từ `Gemma4ForConditionalGeneration` (prefix `model.language_model.*`), nhưng `Gemma4ForCausalLM` expects `model.*` prefix.

**Fix:** Load weights thủ công và remap:
```python
from safetensors.torch import load_file
state_dict = load_file("model.safetensors")
new_dict = {}
for k, v in state_dict.items():
    if k.startswith("model.language_model."):
        new_dict["model." + k[len("model.language_model."):]] = v
model = Gemma4ForCausalLM(config)
model.load_state_dict(new_dict, strict=False)
```

### 4.3 Embedding index error (srcIndex < srcSelectDimSize)
**Nguyên nhân:** Thêm tokens mới (`<abstain>`, `</abstain>`) làm mismatch embedding size.

**Fix:** Không thêm tokens mới. Dùng vocabulary có sẵn (262144 tokens).

### 4.4 CUBLAS_STATUS_NOT_SUPPORTED
**Nguyên nhân:** `per_layer_model_projection` dtype mismatch giữa float32 và bfloat16.

**Fix:** Dùng `dtype=torch.float16` thay vì `torch.bfloat16` hoặc `torch.float32`.

### 4.5 OOM khi load model float32
**Nguyên nhân:** Model float32 chiếm 28GB > 24GB VRAM.

**Fix:** Dùng `dtype=torch.float16` (14GB VRAM).

### 4.6 Paging file too small
**Nguyên nhân:** Load multimodal checkpoint cần nhiều RAM.

**Fix:** Convert checkpoint sang text-only trước khi load (xem Section 4.2).

### 4.7 Vietnamese Unicode trong LaTeX
**Fix:** `\usepackage[T1,T5]{fontenc}` với T5 default, load TRƯỚC babel:
```latex
\usepackage[utf8]{inputenc}
\usepackage[T1,T5]{fontenc}
\usepackage[vietnamese,english]{babel}
```

### 4.8 pgf arrow tip error
**Fix:** `\usetikzlibrary{arrows.meta}`

---

## 5. Training Configurations

### 5.1 Paper ablation (4 configs)
| Config | Model | MC avg | Δ từ ZS |
|--------|-------|--------|---------|
| Zero-shot | Base model, direct prompt | 0.605 | — |
| Few-shot | Base + 1-3 examples | 0.618 | +1.4pp |
| Baseline 3 | LoRA r=8, α=16 | 0.659 | +5.4pp |
| Proposed | LoRA r=16, α=32, reasoning | 0.629 | +2.4pp |

### 5.2 RAFT-AT training (chưa chạy xong)
```bash
python VLegal-Bench/tools/finetune_raft_at.py \
  --model D:/Hunganh/vlegal-finetune/merged/proposed \
  --mode proposed \
  --epochs 5 \
  --lora_r 16 \
  --lora_alpha 32 \
  --batch_size 2 \
  --gradient_accumulation 8 \
  --output_dir D:/Hunganh/vlegal-finetune/output/raft_at_proposed
```

**Blocker:** Gemma4 weight format không tương thích với transformers 5.5.0. Cần fix weight mapping trước khi train.

### 5.3 Data
| File | Samples | Mô tả |
|------|---------|-------|
| `data/raft_at_proposed.jsonl` | 3085 | RAFT-AT training data (751 abstain, 2334 answer) |
| `data/raft_at_proposed_dpo.jsonl` | 3085 | DPO preference pairs |

---

## 6. Kết quả Reliability Metrics

| Metric | Baseline 3 | Proposed | Δ |
|--------|-----------|----------|---|
| CitAcc ↑ | 0.387 | 0.573 | +18.6pp |
| RAS ↑ | 0.019 | 0.048 | +2.9pp |
| RAR ↑ | 0.204 | 0.301 | +9.7pp |
| ESR ↑ | 0.321 | 0.436 | +11.5pp |
| UCR ↓ | 0.441 | 0.441 | 0 |
| AbsAcc ↑ | 0.000 | 0.060 | +6.0pp |

---

## 7. Checklist trước khi chạy

### Chạy inference
- [ ] Workstation online (`ping 100.72.47.109`)
- [ ] GPU free (`nvidia-smi`, memory < 5GB used)
- [ ] Model exists (`ls D:/Hunganh/vlegal-finetune/merged/proposed`)
- [ ] Data exists (`ls D:/Hunganh/AI_LEGAL/VLegal-Bench/data/`)

### Chạy training
- [ ] Tất cả trên +
- [ ] Python packages: `torch`, `transformers`, `peft`, `trl`, `accelerate`
- [ ] Import order đúng (accelerate TRƯỚC, Trainer TRƯỚC TrainingArguments)
- [ ] Checkpoint format đúng (text-only nếu dùng Gemma4ForCausalLM)

### Compile paper
- [ ] MiKTeX installed
- [ ] `pdflatex -interaction=nonstopmode main.tex` → 0 errors
- [ ] Chạy 2 lần để resolve cross-references

---

## 8. Files quan trọng

| File | Mô tả |
|------|-------|
| `paper/main.tex` | Paper LaTeX (20 pages, 4-config ablation) |
| `VLegal-Bench/src/evaluation.py` | Evaluation logic với `_extract_tag_content()` |
| `VLegal-Bench/src/reliability_metrics.py` | 6 reliability metrics |
| `VLegal-Bench/tools/finetune_raft_at.py` | RAFT-AT training script |
| `VLegal-Bench/tools/finetune_lora.py` | LoRA fine-tuning script |
| `VLegal-Bench/data/raft_at_proposed.jsonl` | RAFT-AT training data |
| `VLegal-Bench/_corrupted/` | 101 file results bị hỏng (KHÔNG dùng) |

---

## 9. Git workflow

```bash
# Check status
git status

# Stage & commit
git add -A
git commit -m "description"

# Push (nếu cần)
git push origin main
```

**Lưu ý:** `_corrupted/` và `_temp_scripts/` đã được .gitignore exclude.

---

## 10. Known issues còn lại

1. **RAFT-AT training chưa chạy xong** — Gemma4 weight format incompatible với transformers 5.5.0
2. **Format contamination** — Proposed model outputs MC format trên text_cls tasks (98.8% mismatch task 3.4)
3. **Generation tasks** — Fine-tuned models có 0.0 ROUGE-L trên tasks 2.3, 4.2, 4.3
4. **AbsAcc thấp** — Chỉ 0.060 aggregate, cần RAFT-AT để cải thiện
