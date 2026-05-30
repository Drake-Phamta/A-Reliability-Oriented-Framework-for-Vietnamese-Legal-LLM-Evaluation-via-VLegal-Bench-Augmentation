# Colab Auto-Annotation - Bước 2

## Cấu trúc folder

```
colab_annotation/
├── colab_notebook.py          # Code cho Colab (copy từng cell)
├── README.md                  # File này
├── manual_annotations/        # 54 mẫu annotate thủ công (để validate)
│   ├── 1_4_annotated.jsonl
│   ├── 1_5_annotated.jsonl
│   ├── 3_1_annotated.jsonl
│   ├── 4_1_annotated.jsonl
│   └── 4_2_annotated.jsonl
├── 1_4_llm_input.jsonl        # Data cho LLM (968 mẫu)
├── 1_5_llm_input.jsonl        # Data cho LLM (821 mẫu)
├── 3_1_llm_input.jsonl        # Data cho LLM (600 mẫu)
├── 3_3_llm_input.jsonl        # Data cho LLM (292 mẫu)
├── 4_1_llm_input.jsonl        # Data cho LLM (396 mẫu)
├── 4_2_llm_input.jsonl        # Data cho LLM (300 mẫu)
└── *_stats.json               # Thống kê regex extraction
```

## Hướng dẫn chạy trên Colab

### Bước 1: Tạo notebook mới
- Vào https://colab.research.google.com
- Tạo notebook mới
- Chọn Runtime > Change runtime type > T4 GPU

### Bước 2: Copy code từ colab_notebook.py
- Copy từng CELL vào Colab
- Chạy theo thứ tự CELL 1 → CELL 9

### Bước 3: Upload data
- CELL 4 sẽ yêu cầu upload 6 file `*_llm_input.jsonl`
- Chọn tất cả 6 file trong folder này

### Bước 4: Chạy annotation
- CELL 8 chạy annotation trên tất cả 3,377 mẫu
- Ước tính: ~4-6 giờ trên T4 GPU

### Bước 5: Download kết quả
- CELL 9 download 6 file `*_annotated.jsonl`

### Bước 6: Copy về local
- Copy kết quả vào `annotations/auto_annotated/`
- Chạy validate với manual annotations

## Validate kết quả

```python
# So sánh với 54 mẫu annotate thủ công
result = validate(
    "annotated_output/1_4_annotated.jsonl",
    "manual_annotations/1_4_annotated.jsonl"
)
print(result)
# Expected: citation_agreement > 70%, temporal_agreement > 60%
```

## Yêu cầu

- Google Colab (free hoặc Pro)
- HuggingFace token (accept Gemma license)
- Thời gian: ~4-6 giờ
