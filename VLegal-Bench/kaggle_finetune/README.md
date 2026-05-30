# Kaggle Fine-tune Gemma 4 E4B

## Cấu trúc folder

```
kaggle_finetune/
├── finetune_gemma4.py    # Code cho Kaggle notebook (copy từng cell)
└── README.md             # File này
```

## Chuẩn bị dữ liệu

### Bước 1: Tạo Kaggle Dataset

1. Vào kaggle.com > Create > New Dataset
2. Upload toàn bộ folder `VLegal-Bench/` với cấu trúc:
```
vlegal-bench/
├── 1.1/1_1.jsonl
├── 1.2/1_2.jsonl
├── ...
├── 5.4/5_4.jsonl
└── annotated/
    ├── 1_4_annotated.jsonl
    ├── 1_5_annotated.jsonl
    ├── 3_1_annotated.jsonl
    ├── 3_3_annotated.jsonl
    ├── 4_1_annotated.jsonl
    └── 4_2_annotated.jsonl
```

3. Đặt dataset name: `vlegal-bench`
4. Set visibility: Private

### Bước 2: Tạo Kaggle Notebook

1. Vào kaggle.com > Create > New Notebook
2. Chọn **Settings** > **Accelerator** > **GPU T4 x2**
3. Thêm dataset: **Add data** > tìm `vlegal-bench`

### Bước 3: Copy code

Copy lần lượt 10 cells từ `finetune_gemma4.py` vào Kaggle notebook.

**Lưu ý:** Thay đổi `DATA_DIR` trong CELL 3 thành đường dẫn thực tế:
```python
DATA_DIR = "/kaggle/input/vlegal-bench"  # Kaggle tự mount dataset vào đây
```

### Bước 4: Chạy

Chạy tuần tự từ CELL 1 → CELL 9.

- CELL 1-2: Cài đặt + load model (~5 phút)
- CELL 3-4: Load data (~2 phút)
- CELL 5: Train Baseline 3 (~1-2 giờ)
- CELL 6-7: Train Proposed (~2-3 giờ)
- CELL 8-9: Test + Export (~5 phút)

**Tổng thời gian: ~4-6 giờ**

## Cấu hình training

| Parameter | Giá trị | Lý do |
|-----------|---------|-------|
| Model | gemma-4-E4B-it | Backbone chính |
| Quantization | 4-bit QLoRA | Fit T4 15GB |
| LoRA r | 16 | Cân bằng quality/memory |
| LoRA alpha | 32 | 2x rank |
| Batch size | 2/GPU | T4 VRAM limit |
| Gradient accum | 8 | Effective batch = 32 |
| Epochs | 3 | Đủ cho convergence |
| LR | 2e-4 | Standard LoRA LR |
| Max seq len | 2048 | Đủ cho legal text |
| Precision | fp16 | T4 không hỗ trợ bf16 |

## Output

- `baseline_3_lora.zip` — LoRA adapter cho Baseline 3
- `proposed_lora.zip` — LoRA adapter cho Proposed

Download từ Kaggle Output panel (bên phải notebook).

## Merge LoRA vào base model (local)

```python
from unsloth import FastModel

model, tokenizer = FastModel.from_pretrained(
    "unsloth/gemma-4-E4B-it",
    load_in_4bit=True,
)
model.load_adapter("baseline_3_lora")
model.save_pretrained_merged("gemma4-baseline3-merged", tokenizer)
```
