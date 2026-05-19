# Hướng dẫn Annotation - VLegal-Bench Reliability Labels

## 1. Tổng quan

Mục tiêu: Gán nhãn (annotation) cho các mẫu trong VLegal-Bench để đánh giá độ tin cậy (reliability) của mô hình LLM pháp lý. Mỗi mẫu cần được annotate 3 nhóm thông tin:

1. **Citation Grounding** - Trích dẫn nguồn pháp luật
2. **Temporal Validity** - Hiệu lực thời gian của văn bản
3. **Reliability Supervision** - Giám sát độ tin cậy của câu trả lời

---

## 2. Schema Annotation

### 2.1 Citation Grounding

Ghi nhận nguồn pháp luật được sử dụng trong câu hỏi/đáp án.

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|-----------|-------|
| `document_name` | string | Có | Tên đầy đủ của văn bản pháp luật |
| `article` | string | Có | Số và tên điều (VD: "Điều 463") |
| `clause` | string | Không | Số khoản (VD: "Khoản 1") |
| `evidence_passage` | string | Không | Đoạn trích dẫn nguyên văn từ văn bản |

**Quy tắc:**
- `document_name`: Viết tên đầy đủ, không viết tắt. VD: "Bộ luật Dân sự 2015", không phải "BLDS 2015"
- `article`: Luôn bắt đầu bằng "Điều" + số. VD: "Điều 463"
- `clause`: Bắt đầu bằng "Khoản" + số. VD: "Khoản 1". Nếu điều không có khoản thì bỏ qua
- `evidence_passage`: Trích dẫn nguyên văn nếu có thể. Nếu câu hỏi đã tóm tắt thì ghi lại nội dung liên quan

**Ví dụ:**
```json
{
  "document_name": "Bộ luật Dân sự 2015",
  "article": "Điều 463",
  "clause": "Khoản 1",
  "evidence_passage": "Hợp đồng vay tài sản là sự thỏa thuận giữa các bên, theo đó bên cho vay giao tài sản cho bên vay; khi đến hạn trả, bên vay phải hoàn trả cho bên cho vay tài sản cùng loại theo đúng số lượng, chất lượng và chỉ phải trả lãi nếu có thỏa thuận hoặc pháp luật có quy định."
}
```

### 2.2 Temporal Validity

Ghi nhận thông tin thời gian và hiệu lực của văn bản pháp luật.

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|-----------|-------|
| `promulgation_date` | string | Không | Ngày ban hành (format: YYYY-MM-DD) |
| `effective_date` | string | Không | Ngày có hiệu lực |
| `expiration_date` | string | Không | Ngày hết hiệu lực (null nếu còn hiệu lực) |
| `superseded_by` | string | Không | Văn bản thay thế (null nếu không có) |
| `query_reference_date` | string | Không | Ngày tham chiếu truy vấn |
| `valid_at_query_date` | boolean | Có | Văn bản có hiệu lực tại ngày tham chiếu không |

**Quy tắc:**
- Format ngày: `YYYY-MM-DD` (VD: "2015-11-24")
- Nếu không biết chính xác ngày thì ghi `null`, không đoán
- `valid_at_query_date`: 
  - `true` nếu văn bản còn hiệu lực tại ngày tham chiếu
  - `false` nếu văn bản đã hết hiệu lực, bị thay thế, hoặc bị bãi bỏ
- Nếu câu hỏi không đề cập ngày cụ thể, `query_reference_date` = ngày hiện tại hoặc `null`

**Ví dụ văn bản còn hiệu lực:**
```json
{
  "promulgation_date": "2015-11-24",
  "effective_date": "2017-01-01",
  "expiration_date": null,
  "superseded_by": null,
  "query_reference_date": "2024-06-15",
  "valid_at_query_date": true
}
```

**Ví dụ văn bản đã hết hiệu lực:**
```json
{
  "promulgation_date": "2005-06-14",
  "effective_date": "2006-01-01",
  "expiration_date": "2017-01-01",
  "superseded_by": "Bộ luật Dân sự 2015",
  "query_reference_date": "2024-06-15",
  "valid_at_query_date": false
}
```

### 2.3 Reliability Supervision

Đánh giá độ tin cậy của câu trả lời mô hình.

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|-----------|-------|
| `evidence_sufficient` | boolean | Có | Evidence có đủ để hỗ trợ kết luận không |
| `unsupported_claims` | list[string] | Không | Các claim không được hỗ trợ bởi evidence |
| `hallucination_type` | string | Không | Loại hallucination (xem bên dưới) |
| `should_abstain` | boolean | Có | Model nên từ chối trả lời không |
| `abstain_reason` | string | Không | Lý do nên abstain |

**Loại hallucination:**
- `null` - Không có hallucination
- `"factual_fabrication"` - Bịa đặt sự thật (sai thông tin pháp luật)
- `"citation_hallucination"` - Bịa đặt điều luật (trích dẫn điều không tồn tại)
- `"temporal_confusion"` - Nhầm lẫn thời gian (dùng luật cũ khi đã có luật mới)

**Quy tắc:**
- `evidence_sufficient`: 
  - `true` nếu thông tin trong câu hỏi đủ để trả lời chính xác
  - `false` nếu thiếu thông tin, hoặc câu hỏi quá mơ hồ
- `unsupported_claims`: Liệt kê các claim mà model có thể đưa ra nhưng không có cơ sở trong evidence
- `should_abstain`: 
  - `true` nếu câu hỏi không thể trả lời chính xác dựa trên thông tin có sẵn
  - VD: câu hỏi về luật đã hết hiệu lực, hoặc thông tin không đủ

**Ví dụ:**
```json
{
  "evidence_sufficient": true,
  "unsupported_claims": [],
  "hallucination_type": null,
  "should_abstain": false,
  "abstain_reason": null
}
```

**Ví dụ có vấn đề:**
```json
{
  "evidence_sufficient": false,
  "unsupported_claims": ["Điều 500 quy định về phạt vi phạm hợp đồng"],
  "hallucination_type": "citation_hallucination",
  "should_abstain": true,
  "abstain_reason": "Câu hỏi trích dẫn điều luật không tồn tại trong Bộ luật Dân sự 2015"
}
```

---

## 3. Quy trình Annotation

### 3.1 Các bước thực hiện

1. **Đọc câu hỏi và context**: Đọc kỹ instruction, question, và các trường liên quan (content, document, article, court_judgement, description)
2. **Xác định đáp án đúng**: Xem ground_truth/answer để hiểu câu trả lời kỳ vọng
3. **Annotate Citation**: Xác định văn bản pháp luật, điều, khoản liên quan
4. **Annotate Temporal**: Xác định thông tin thời gian của văn bản
5. **Annotate Reliability**: Đánh giá độ tin cậy dựa trên evidence có sẵn
6. **Xác nhận**: Kiểm tra lại annotation trước khi lưu

### 3.2 Sử dụng Annotation Tool

```bash
# Chạy annotation tool
python tools/annotation_tool.py \
    --input 1.4/1_4.jsonl \
    --output annotations/1_4_annotated.jsonl \
    --task 1.4

# Tiếp tục từ mẫu thứ 100
python tools/annotation_tool.py \
    --input 1.4/1_4.jsonl \
    --output annotations/1_4_annotated.jsonl \
    --task 1.4 \
    --start 100

# Chỉ annotate 50 mẫu
python tools/annotation_tool.py \
    --input 1.4/1_4.jsonl \
    --output annotations/1_4_annotated.jsonl \
    --task 1.4 \
    --limit 50
```

Tool tự động lưu progress, có thể Ctrl+C thoát bất cứ lúc nào.

### 3.3 Quy trình chất lượng

**Giai đoạn 1: Training (10% mẫu đầu)**
- Mỗi annotator annotate 10 mẫu đầu tiên
- Team review cùng nhau, thống nhất cách hiểu
- Hiệu chuẩn (calibration) giữa các annotator

**Giai đoạn 2: Independent Annotation**
- Mỗi mẫu được 2 annotator annotate độc lập
- Không trao đổi trong quá trình annotate

**Giai đoạn 3: Adjudication**
- So sánh annotation của 2 annotator
- Nếu khác biệt > 50% ở bất kỳ field nào → annotator thứ 3 review
- Thống nhất annotation cuối cùng

**Giai đoạn 4: Cross-validation**
- 10% mẫu được annotate bởi cả 3 annotator
- Tính Inter-Annotator Agreement (IAA)

---

## 4. Target Chất lượng

| Metric | Target | Cách tính |
|--------|--------|-----------|
| Cohen's κ (reliability) | ≥ 0.75 | So sánh `evidence_sufficient`, `should_abstain` |
| Cohen's κ (temporal) | ≥ 0.80 | So sánh `valid_at_query_date` |
| Span F1 (citation) | ≥ 0.80 | So sánh `document_name`, `article`, `clause` |
| Agreement (hallucination) | ≥ 0.70 | So sánh `hallucination_type` |

---

## 5. Edge Cases

### 5.1 Citation Edge Cases

| Trường hợp | Xử lý |
|------------|-------|
| Câu hỏi không trích dẫn điều luật cụ thể | Ghi `document_name` và `article` dựa trên nội dung liên quan, `evidence_passage` = null |
| Nhiều văn bản liên quan | Liệt kê tất cả trong annotation (dùng annotation tool nhiều lần) |
| Văn bản địa phương | Ghi đầy tên: "Nghị định số .../NĐ-CP ngày .../.../..." |
| Luật chung → luật chuyên ngành | Ghi cả hai nếu câu hỏi liên quan |

### 5.2 Temporal Edge Cases

| Trường hợp | Xử lý |
|------------|-------|
| Không rõ ngày ban hành | Ghi `null`, không đoán |
| Văn bản bị sửa đổi bổ sung | Ghi `superseded_by` = "Luật sửa đổi, bổ sung một số điều của ..." |
| Câu hỏi không đề cập thời gian | `query_reference_date` = null, `valid_at_query_date` = true (giả định hiện tại) |
| Văn bản dự thảo | `valid_at_query_date` = false |

### 5.3 Reliability Edge Cases

| Trường hợp | Xử lý |
|------------|-------|
| Câu hỏi đúng nhưng lý do sai | `evidence_sufficient` = true, `unsupported_claims` chứa lý do sai |
| Model trả lời "Tôi không biết" | `should_abstain` = true nếu câu hỏi có thể trả lời được |
| Câu hỏi không có đáp án đúng | `should_abstain` = true, `abstain_reason` = "Câu hỏi không có đáp án đúng" |
| Câu hỏi dựa trên luật đã hết hiệu lực | `valid_at_query_date` = false, `should_abstain` = true (nếu yêu cầu luật hiện hành) |

---

## 6. Tasks được chọn cho Annotation

| Task | Loại | Số mẫu | Annotation Focus |
|------|------|--------|-----------------|
| 1.4 | MC | 968 | Citation grounding (article recall) |
| 2.4 | MC | 599 | Reliability (judgement verification) |
| 3.2 | MC | 600 | Temporal validity (court decision) |
| 3.3 | MC | 292 | Citation + evidence (multi-hop) |
| 4.1 | Generation | 396 | Citation + temporal (summarization) |
| 4.3 | Generation | 498 | Citation + abstention (legal opinion) |

# task bị loại bỏ:
| Task | Loại | Số mẫu gốc | Ghi chú |
|------|------|--------|-----------------|
| 2.4 | MC | 599 | Removed (Reliability focus) |
| 3.2 | MC | 600 | Removed (Temporal validity) |
| 3.3 | MC | 292 | Unsuitable (Multi-hop reasoning) |
| 4.3 | Generation | 498 | Removed (Abstention evaluation) |

# Lựa chọn hiện tại
| Task | Loại | Số mẫu gốc | Annotation Focus |
|------|------|--------|-----------------|
| 1.4 | MC | 968 | Citation grounding (Article recall) |
| 1.5 | MC | 821 | Citation grounding (Document-level basis) |
| 3.1 | MC | 600 | Citation grounding (Article-level basis) |
| 4.1 | Generation | 396 | Citation + Temporal (Summarization) |
| 4.2 | Generation | 300 | Generation (IRAC structured analysis) |



**Subset annotation**: 200-300 mẫu/task → tổng ~1,200-1,500 mẫu

---

## 7. Checklist cho mỗi mẫu

- [ ] Đọc kỹ instruction và question
- [ ] Xác định ground_truth/answer
- [ ] Annotate citation (document_name, article bắt buộc)
- [ ] Annotate temporal (valid_at_query_date bắt buộc)
- [ ] Annotate reliability (evidence_sufficient, should_abstain bắt buộc)
- [ ] Kiểm tra lại annotation
- [ ] Lưu annotation

---

## 8. Liên hệ

Nếu có thắc mắc về annotation, liên hệ team lead để được giải quyết.
