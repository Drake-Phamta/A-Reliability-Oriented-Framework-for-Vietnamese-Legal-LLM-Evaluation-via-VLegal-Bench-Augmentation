# KẾ HOẠCH 2 TUẦN - Hoàn thiện Paper

## Timeline tổng thể

```
        Tuần 1                              Tuần 2
   T2  T3  T4  T5  T6              T2  T3  T4  T5  T6
A: Setup → Baselines 1a-2b → FT baseline3 → FT proposed → Evaluate → Tables
B: Calibration → Annotation batch1 → Annotation batch2 → IAA → Merge
C: Section 2 →------→ Done | Section 5 → Section 6 → Review → Submit
```

---

## NGÀY 1 (T2 Tuần 1)

### Member A: Setup + Test
```
09:00  Clone repo, chạy setup.bat
10:00  Edit .env với API key
10:30  Test pipeline: python tools/run_experiments.py --model X --task 3.4 --system baseline_1a
12:00  Verify output: python tools/verify_experiments.py --system baseline_1a
14:00  Nếu OK → start Baseline 1a full 22 tasks
```

### Member B: Setup + Calibration
```
09:00  Clone repo, đọc docs/annotation_guideline.md
10:00  Chạy annotation 10 mẫu đầu (calibration)
11:00  Review với nhau, thống nhất cách hiểu
14:00  Bắt đầu annotation Task 1.4 (250 mẫu)
```

### Member C: Section 2 Related Work
```
09:00  Đọc paper hiện tại (legal_llm_paper_ptit.docx)
10:00  Viết Section 2.1 LLM Foundations
14:00  Viết Section 2.2 Legal AI Applications
```

---

## NGÀY 2 (T3 Tuần 1)

### Member A
```
Cả ngày: Baseline 1a đang chạy → start Baseline 1b song song
Kiểm tra: python tools/progress.py
```

### Member B
```
Cả ngày: Tiếp tục Task 1.4 (target: 150-200 mẫu/ngày)
```

### Member C
```
09:00  Viết Section 2.3 Legal Knowledge Infusion
14:00  Viết Section 2.4 Evaluation Frameworks
```

---

## NGÀY 3 (T4 Tuần 1)

### Member A
```
Baseline 1a xong → start Baseline 2a
Baseline 1b đang chạy tiếp
```

### Member B
```
Hoàn thành Task 1.4 → chuyển Task 3.2
```

### Member C
```
Hoàn thành Section 2 → review + polish
Bắt đầu draft Section 5 outline (chưa có số liệu)
```

---

## NGÀY 4 (T5 Tuần 1)

### Member A
```
Baseline 2a xong → start Baseline 2b
Baseline 1b xong (hoặc gần xong)
```

### Member B
```
Tiếp tục Task 3.2 (target: 150 mẫu/ngày)
```

### Member C
```
Draft Section 5.4 Case Studies (3 cases) - dựa trên data samples
Draft Section 6 outline
```

---

## NGÀY 5 (T6 Tuần 1)

### Member A
```
Baseline 2b đang chạy
Start fine-tune Baseline 3 (không cần annotation data)
```

### Member B
```
Hoàn thành Task 3.2 → chuyển Task 4.1
Hoặc: overlap annotation cho IAA (25 samples × 6 tasks)
```

### Member C
```
Hoàn thành draft Section 5 + 6 outline
Review Section 2 lần cuối
```

---

## NGÀY 6 (T2 Tuần 2)

### Member A
```
Baseline 2b xong
Baseline 3 fine-tune xong → chạy inference
```

### Member B
```
Tiếp tục annotation Task 4.1
Start overlap annotation cho IAA
```

### Member C
```
ĐỢI: Baseline 1a/1b results → bắt đầu viết Section 5.1
```

---

## NGÀY 7 (T3 Tuần 2)

### Member A
```
Chạy evaluate: python tools/evaluate_experiments.py --latex
Xuất Table 2 (core benchmark)
```

### Member B
```
Hoàn thành annotation batch 1 (tasks 1.4, 3.2, 4.1)
Chuyển annotation batch 2 (tasks 2.4, 3.3, 4.3)
```

### Member C
```
Viết Section 5.1 (có Table 2 data)
Viết Section 5.3 Ablation (partial data)
```

---

## NGÀY 8 (T4 Tuần 2)

### Member A
```
Start fine-tune Proposed (cần annotation data từ Member B)
Chạy evaluate cho tất cả baselines
```

### Member B
```
Hoàn thành annotation batch 2
Tính IAA: python tools/calculate_iaa.py
```

### Member C
```
Viết Section 5.2 (có reliability metrics)
Viết Section 5.4 Case Studies (có raw responses)
```

---

## NGÀY 9 (T5 Tuần 2)

### Member A
```
Proposed fine-tune xong → chạy inference + evaluate
Xuất Table 3 (reliability), Table 4 (ablation)
Điền implementation details vào paper
```

### Member B
```
Merge annotation files → final
Generate Table 1 (dataset stats)
Điền IAA scores vào paper
```

### Member C
```
Viết Section 6 Discussion
Review toàn bộ paper
```

---

## NGÀY 10 (T6 Tuần 2) - DEADLINE

### All
```
09:00  Final review toàn bộ paper
11:00  Fix formatting, references
14:00  PDF render check
16:00  SUBMIT
```

---

## Critical Path

```
Member A: Setup → 4 Baselines → FT Baseline3 → FT Proposed → Evaluate → Tables
                      ↓                              ↑
Member B:    Calibration → Annotation Batch1 → Batch2 → IAA
                                                        ↓
Member C:           Section 2 → Section 5 (đợi results) → Section 6 → Review
```

## Rủi ro & Mitigation

| Rủi ro | Mitigation |
|--------|-----------|
| API rate limit | Chạy batch_size=1, tăng delay |
| Fine-tune quá lâu | Giảm epochs xuống 2, giảm samples |
| Annotation chậm | Giảm 250→150 samples/task |
| GPU không đủ | Dùng smaller model (1.5B thay vì 7B) |

## Giảm scope nếu cần

Nếu quá gấp:
- Giảm samples/task: 250 → 150 (tổng 900 thay vì 1500)
- Chỉ chạy 3 baselines: 1a, 1b, proposed (bỏ 2a, 2b)
- Fine-tune 1 epoch thay vì 3
- Bỏ 1-2 case studies
