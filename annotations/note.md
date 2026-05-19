# Quá trình Annotation

Đã tạo các file `_subset.jsonl` làm dữ liệu đầu vào.
Đã chạy `annotation_tool.py` để gán nhãn, kết quả được lưu vào các file `_annotated.jsonl`.

**Thống kê:**

| Task | Tổng số câu | Đã gán nhãn | Skip |
|------|-------------|-------------|------|
| **1.4** | 16 | 10 | 6 |
| **1.5** | 19 | 11 | 8 |
| **3.1** | 16 | 12 | 4 |
| **4.1** | 15 | 10 | 5 |
| **4.2** | 47 | 11 | 36 |


**Task bị loại bỏ:**
| Task | Loại | Số mẫu gốc | Ghi chú |
|------|------|--------|-----------------|
| 2.4 | MC | 599 | Removed (Reliability focus) |
| 3.2 | MC | 600 | Removed (Temporal validity) |
| 3.3 | MC | 292 | Unsuitable (Multi-hop reasoning) |
| 4.3 | Generation | 498 | Removed (Abstention evaluation) |

**Vấn đề**
- Nhiều văn bản hết hiệu lực một phần --> không đánh giá
- Task 3.3 không phù hợp với mục tiêu --> loại bỏ
- Task 4.2 không thống nhất về cách viết trích dẫn (viết tắt / không viết tắt)