# MỘT KHUNG ĐÁNH GIÁ TÍNH ĐÁNG TIN CẬY CHO MÔ HÌNH NGÔN NGỮ LỚN PHÁP LÝ TIẾNG VIỆT QUA MỞ RỘNG VLEGAL-BENCH

**Pham Tuan Anh, Phan Nguyen Viet Dung, Ung Trong Trinh, Do Thi Lien**

Bưu chính Viễn thông, Km 10 Nguyễn Trãi, Hà Đông, Hà Nội, Việt Nam
{author1, author2, author3, liendt}@ptit.edu.vn

---

## Tóm tắt

Các mô hình ngôn ngữ lớn (LLM) đã mở ra nhiều cơ hội trong lĩnh vực trí tuệ nhân tạo pháp lý (Legal AI), từ trả lời câu hỏi đến dự đoán bản án. Tuy nhiên, một khoảng cách lớn tồn tại giữa hiệu năng trên benchmark và các tiêu chí đáng tin cậy (reliability) mà thực tế pháp lý yêu cầu. Các benchmark pháp lý hiện tại chủ yếu đánh giá độ chính xác (accuracy) mà không giám sát các chiều đáng tin cậy quan trọng như trích dẫn đúng nguồn pháp luật (citation faithfulness), hiệu lực thời gian của văn bản (temporal validity), và khả năng từ chối trả lời khi thiếu căn cứ (abstention). Bài báo đề xuất một khung đánh giá 4 lớp hướng tới tính đáng tin cậy (reliability-oriented framework) cho LLM pháp lý tiếng Việt, mở rộng VLegal-Bench với một lớp annotation giám sát cung cấp nhãn trích dẫn, nhãn thời gian, và nhãn đáng tin cậy. Chúng tôi định nghĩa 6 metric đáng tin cậy—CitAcc, RAS, RAR, ESR, UCR, AbsAcc—và tiến hành thực nghiệm trên 22 nhiệm vụ pháp lý với mô hình Gemma 4 E4B. Kết quả sơ bộ cho thấy mô hình đạt độ chính xác trung bình 61.4% trên các nhiệm vụ trắc nghiệm, với hiệu suất khác biệt đáng kể giữa các loại nhiệm vụ, đặt nền tảng cho các thí nghiệm thích ứng miền (domain adaptation) tiếp theo.

**Từ khóa:** LLM pháp lý tiếng Việt, tính đáng tin cậy, benchmark, hallucination, trích dẫn pháp luật

---

## 1. Giới thiệu

Sự phát triển nhanh chóng của các mô hình ngôn ngữ lớn (LLM) đã tạo ra những khả năng mới trong nhiều lĩnh vực chuyên biệt, trong đó pháp luật là một lĩnh vực hứa hẹn do tính chất dựa trên văn bản và quy tắc của nó [1, 2]. Các LLM đã được áp dụng cho nhiều nhiệm vụ pháp lý bao gồm nghiên cứu pháp luật, soạn thảo văn bản, kiểm tra tuân thủ, đánh giá hợp đồng, dự đoán bản án và giáo dục pháp luật [3, 4].

Tuy nhiên, một khoảng cách dai dẳng tồn tại giữa hiệu năng trên benchmark và các tiêu chí đáng tin cậy mà triển khai pháp lý thực tế yêu cầu. Phần lớn các benchmark pháp lý hiện tại đánh giá correctness và legal reasoning trên các loại nhiệm vụ có cấu trúc nhưng không cung cấp giám sát rõ ràng cho citation grounding, temporal validity hoặc hành vi abstention [5, 6]. Điều này đặc biệt quan trọng trong bối cảnh pháp lý, nơi mà:

- **Trích dẫn sai** (citation hallucination): Mô hình tạo ra các điều luật không tồn tại hoặc trích dẫn sai nguồn
- **Nhầm lẫn thời gian** (temporal confusion): Mô hình sử dụng luật đã hết hiệu lực hoặc bị thay thế
- **Quá tự tin** (overconfidence): Mô hình trả lời một cách chắc chắn ngay cả khi thiếu căn cứ pháp lý

VLegal-Bench [7] là benchmark toàn diện nhất cho đánh giá reasoning pháp lý tiếng Việt, bao gồm 10,450 mẫu trên 22 nhiệm vụ và năm cấp độ nhận thức. Mặc dù benchmark này cung cấp đánh giá năng lực pháp lý cơ bản, nó không bao gồm giám sát reliability cần thiết để đánh giá liệu LLM có trích dẫn đúng điều luật, sử dụng văn bản còn hiệu lực, và biết từ chối trả lời khi thiếu thông tin hay không.

Để giải quyết hạn chế này, chúng tôi đề xuất một khung đánh giá hướng tới tính đáng tin cậy (reliability-oriented framework) cho LLM pháp lý tiếng Việt. Khung này coi VLegal-Bench như benchmark cốt lõi và mở rộng nó với một lớp annotation reliability cung cấp ba chiều giám sát: (1) citation grounding—xác định nguồn pháp luật chính xác hỗ trợ câu trả lời; (2) temporal validity—đánh giá hiệu lực thời gian của văn bản pháp luật; và (3) reliability supervision—giám sát tính đầy đủ của bằng chứng, unsupported claims và hành vi abstention.

Các đóng góp chính của bài báo này như sau:

1. **Khung đánh giá 4 lớp:** Chúng tôi đề xuất một khung đánh giá hướng tới tính đáng tin cậy cho LLM pháp lý tiếng Việt, cung cấp một pipeline có hệ thống từ lựa chọn mô hình đến thích ứng miền và đánh giá reliability.

2. **Lớp annotation reliability:** Chúng tôi thiết kế và xây dựng một lớp annotation mở rộng VLegal-Bench với citation grounding, temporal validity và reliability supervision labels.

3. **6 metric đáng tin cậy:** Chúng tôi định nghĩa 6 metric reliability bổ sung cho các metric truyền thống: CitAcc (citation correctness), RAS (recency-aware score), RAR (recency-aware recall), ESR (evidence support rate), UCR (unsupported claim rate) và AbsAcc (abstention accuracy).

4. **Kết quả thực nghiệm:** Chúng tôi cung cấp bằng chứng thực nghiệm về hiệu suất của Gemma 4 E4B trên 22 nhiệm vụ pháp lý, thiết lập baseline cho các thí nghiệm thích ứng miền tiếp theo.

---

## 2. Công trình liên quan

### 2.1. Nền tảng Mô hình Ngôn ngữ Lớn

Sự phát triển của LLM đã tiến triển từ pre-training tự hồi quy ban đầu đến các mô hình có khả năng zero-shot và few-shot generalization trên nhiều nhiệm vụ đa dạng [8, 9]. Các mốc quan trọng bao gồm demonstration emergent capabilities ở quy mô lớn [9], instruction tuning căn chỉnh hành vi mô hình với chỉ thị của con người [10], và các phương pháp thích ứng tham số hiệu quả (parameter-efficient) như LoRA [11] giảm đáng kể chi phí tính toán cho chuyên biệt hóa miền mà không làm suy giảm khả năng ngôn ngữ tổng quát.

Các chiến lược prompting cũng proved influential. Chain-of-thought prompting [12] đã được chứng minh kích hoạt suy luận nhiều bước, giảm lỗi logic và cải thiện chất lượng câu trả lời trên các miền knowledge-intensive. Đối với các nhiệm vụ pháp lý, structured prompting tham chiếu rõ ràng đến điều luật và suy luận từng bước đã nổi lên như một complement thực tế cho fine-tuning, đặc biệt khi dữ liệu pháp lý có nhãn bị giới hạn.

### 2.2. Ứng dụng AI Pháp lý

LLM đã được áp dụng cho một phổ rộng các nhiệm vụ pháp lý, bao gồm nghiên cứu pháp luật, soạn thảo quy phạm, kiểm tra tuân thủ, đánh giá hợp đồng, dự đoán bản án và giáo dục pháp luật [3, 4]. Các khảo sát về hệ thống AI pháp lý consistently highlight một tập hợp rủi ro liên quan đến triển khai LLM trong môi trường pháp lý có stake cao: hallucination—tạo nội dung plausible nhưng không được hỗ trợ bởi sự thật—nằm trong số các mối quan tâm quan trọng nhất, alongside bias, khả năng diễn giải giới hạn và thách thức trách nhiệm khi mô hình được tích hợp vào pipeline ra quyết định [1, 3].

### 2.3. Truyền đạt Kiến thức Pháp lý

Các hệ thống AI pháp lý hiệu quả thường yêu cầu nhiều hơn một backbone LLM general-purpose; chúng hưởng lợi từ việc truyền đạt kiến thức chuyên miền thông qua retrieval augmentation [13], fine-tuning trên corpus pháp lý, structured knowledge injection hoặc hybrid pipelines [4]. Retrieval-augmented generation (RAG) đặc biệt liên quan trong bối cảnh pháp lý vì nó cho phép mô hình ground responses trong các điều luật cụ thể, giảm khả năng unsupported claims. Tuy nhiên, citation faithfulness—mức độ mà điều luật được trích dẫn thực sự hỗ trợ kết luận—vẫn là một chiều chưa được đánh giá đầy đủ.

Temporal validity là một chiều khác của kiến thức pháp lý đã nhận được sự chú ý giới hạn trong tài liệu LLM. Các đạo luật phải chịu sửa đổi, thay thế và hết hạn, và một mô hình chọn điều luật mà không xác minh ngày hiệu lực có thể tạo ra tư vấn pháp lý không chính xác ngay cả khi điều luật đó đã từng tồn tại.

### 2.4. Khung đánh giá cho LLM Pháp lý

Một số benchmark chuyên biệt cho LLM pháp lý đã được đề xuất, bao gồm LawBench [14] cho tiếng Trung và LEGEL [15] cho tiếng Anh. Các benchmark này đánh giá correctness và legal reasoning nhưng không cung cấp giám sát rõ ràng cho citation grounding, temporal validity hoặc hành vi abstention.

Các phương pháp LLM-as-a-judge [16] và đánh giá factual fine-grained như FActScore [17] đã tiến bộ đánh giá chất lượng output vượt ra ngoài metric cấp token, nhưng ứng dụng của chúng trong citation faithfulness và temporal reasoning trong bối cảnh pháp lý vẫn còn hạn chế.

Ba hướng nghiên cứu gần đây directly relevant đến các chiều reliability được giải quyết bởi khung của chúng tôi. Đối với abstention evaluation, Abstain-QA [18] cung cấp phương pháp luận tiêu chuẩn hóa để đánh giá liệu LLM có biết withholding answers khi bằng chứng không đủ. Đối với temporal legal reasoning, LexTIME [19] giới thiệu benchmark cho temporal ordering của điều luật Việt Nam. Đối với recency-aware metric design, công trình gần đây về temporal question answering evaluation [20] đề xuất Recency-Aware Score (RAS) và Recency-Aware Recall (RAR).

---

## 3. Khung đề xuất

Framework của chúng tôi giải quyết ba chiều reliability—citation faithfulness, temporal validity và hallucination-aware reasoning—thông qua một pipeline bốn lớp như minh họa trong Hình 1.

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: Benchmark-Driven Evaluation      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Core Metrics │  │  Reliability │  │ Error Feedback   │  │
│  │ Acc, F1, BLEU│  │  6 Metrics   │  │ Loop → Layer 2   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Layer 3: Reliability Annotation Layer     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Citation    │  │  Temporal    │  │   Reliability    │  │
│  │  Grounding   │  │  Validity    │  │   Supervision    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Layer 2: Domain Adaptation                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Instruction │  │    LoRA      │  │ Legal-Aware      │  │
│  │  Tuning      │  │  Fine-tuning │  │ Prompting        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Layer 1: Open Foundation Model            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Gemma 4 E4B / Qwen2.5-7B / SeaLLMs-v3             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
        ↑                                           │
        └───────────────────────────────────────────┘
                    Error Feedback Loop
```
*Hình 1. Tổng quan khung đánh giá 4 lớp hướng tới tính đáng tin cậy cho LLM pháp lý tiếng Việt.*

### 3.1. Layer 1: Mô hình Nền tảng Mở

Lớp đầu tiên lựa chọn một LLM open-source làm backbone. Các mô hình mở là cần thiết cho reproducibility, fine-tuning cho các ngôn ngữ và jurisdiction không được phục vụ bởi API thương mại, và khả năng triển khai trong các tổ chức công có giới hạn tài nguyên. Các tiêu chí lựa chọn bao gồm: (1) coverage tiếng Việt, (2) context window đủ dài cho tài liệu pháp lý, (3) compatibility với LoRA/PEFT, và (4) giấy phép cho sử dụng thương mại/nghiên cứu.

### 3.2. Layer 2: Thích ứng Miền

Lớp thứ hai thích ứng backbone đã chọn sang miền pháp lý tiếng Việt thông qua một hoặc nhiều chiến lược:

- **Instruction tuning:** Fine-tuning supervised trên dữ liệu pháp lý Việt Nam
- **Parameter-efficient fine-tuning (PEFT):** LoRA [11] giảm chi phí training while preserving general language capabilities
- **Legal-aware prompting:** Structured prompts specifying legal domain, citation format, và reasoning requirements
- **Output constraint decoding:** Constrained generation enforcing structural requirements như article citation

### 3.3. Layer 3: Lớp Annotation Reliability

Lớp thứ ba là đóng góp phương pháp luận chính của bài báo này. Nó mở rộng một subset có chủ đích của VLegal-Bench với ba loại annotation:

**3.3.1. Citation Grounding Annotation**

Đối với mỗi mẫu, người annotator xác định nguồn điều luật authoritative hỗ trợ câu trả lời đúng. Annotation ghi lại tên văn bản (tên đầy đủ, ví dụ: "Bộ luật Dân sự 2015"), số điều (ví dụ: "Điều 463"), số khoản khi áp dụng (ví dụ: "Khoản 1"), và evidence passage chứa văn bản nguyên văn từ nguồn statutory.

**3.3.2. Temporal Validity Annotation**

Đối với mỗi điều luật được trích dẫn, người annotator ghi lại ngày ban hành, ngày hiệu lực, ngày hết hạn (nếu có), và liệu điều luật đã bị thay thế bởi văn bản mới hơn. Một nhãn validity nhị phân indicates liệu điều luật có hiệu lực tại ngày tham chiếu truy vấn hay không.

**3.3.3. Reliability Supervision Annotation**

Ngoài citation và temporal validity, lớp annotation bao gồm các nhãn characterising tính đáng tin cậy của câu trả lời:
- **Evidence sufficiency:** Liệu thông tin có đủ để hỗ trợ câu trả lời đúng
- **Unsupported claims:** Các claims không được grounding bởi evidence
- **Hallucination type:** Phân loại factual fabrication, citation hallucination hoặc temporal confusion
- **Should-abstain labeling:** Liệu model nên decline to answer

### 3.4. Layer 4: Benchmark-Driven Evaluation

Lớp thứ tư tích hợp đánh giá benchmark cốt lõi và đánh giá reliability vào một pipeline đánh giá thống nhất. VLegal-Bench cung cấp multi-level capability assessment across 22 tasks và 5 categories.

Evaluation results drive Layer 2 adaptation thông qua một explicit feedback mechanism: failure patterns trên specific task groups hoặc reliability dimensions inform targeted fine-tuning, prompting adjustments, hoặc annotation augmentation.

---

## 4. Thiết lập Thí nghiệm

### 4.1. Dataset và Annotation

**Benchmark cốt lõi.** Chúng tôi sử dụng VLegal-Bench [7] làm benchmark đánh giá chính. VLegal-Bench bao gồm 10,354 mẫu drawn from Vietnamese legal documents covering civil law, criminal law, administrative law và commercial law. Các nhiệm vụ được phân bố trên 22 categories và năm cấp độ nhận thức: knowledge recall, comprehension, application, analysis và synthesis/evaluation.

*Bảng 1. Thống kê dataset cho benchmark cốt lõi và subset annotation reliability.*

| Category | Tasks | Samples | Type | Annotation Subset |
|----------|-------|---------|------|-------------------|
| 1.x Recognition & Recall | 1.1-1.5 | 3,520 | MC | 1.4, 1.5 |
| 2.x Understanding & Structuring | 2.1-2.5 | 2,837 | MC | - |
| 3.x Reasoning & Inference | 3.1-3.5 | 2,017 | MC | 3.1, 3.3 |
| 4.x Interpretation & Generation | 4.1-4.3 | 1,194 | Gen | 4.1, 4.2 |
| 5.x Ethics, Fairness & Bias | 5.1-5.4 | 786 | MC | - |
| **Total** | **22** | **10,354** | | **6 tasks** |

**Subset annotation reliability.** Chúng tôi chọn một subset của VLegal-Bench cho annotation reliability, targeting các nhiệm vụ nhạy cảm nhất với citation errors, temporal reasoning failures và unsupported-claim generation. Các nhiệm vụ ưu tiên bao gồm article recall (1.4), schema recall (1.5), article/clause prediction (3.1), multi-hop reasoning (3.3), document summarization (4.1) và judicial reasoning (4.2).

*Bảng 2. Thống kê subset annotation (placeholder—điền sau khi annotation hoàn thành).*

| Task | Total Samples | Annotated | Annotators | IAA (κ) |
|------|---------------|-----------|------------|---------|
| 1.4 | 968 | [--] | [--] | [--] |
| 1.5 | 821 | [--] | [--] | [--] |
| 3.1 | 600 | [--] | [--] | [--] |
| 3.3 | 292 | [--] | [--] | [--] |
| 4.1 | 396 | [--] | [--] | [--] |
| 4.2 | 300 | [--] | [--] | [--] |
| **Total** | **3,377** | **[--]** | | **avg: [--]** |

**Quy trình annotation.** Annotation được thực hiện bởi sinh viên luật năm cuối và sau đại học có proficiency demonstrated trong luật dân sự, hình sự và hành chính Việt Nam, dưới sự giám sát trực tiếp của legal practitioners có license. Tất cả annotators hoàn thành giai đoạn training covering annotation schema, citation grounding conventions, temporal validity reasoning và inter-annotator calibration exercises.

Mỗi mẫu nhận ba lớp annotation targeting các chiều reliability:
- **Citation grounding:** Ghi lại tên văn bản, số điều, số khoản và evidence passage
- **Temporal validity:** Ghi lại ngày ban hành, ngày hiệu lực, ngày hết hạn và nhãn validity
- **Reliability supervision:** Đánh giá evidence sufficiency, unsupported claims, hallucination type và should-abstain

Quy trình annotation follows ba stages: (i) independent annotation—mỗi annotator label mẫu mà không consult others; (ii) adjudication—supervising legal practitioner resolve disagreements; (iii) cross-validation—10% mẫu adjudicated được re-examine bởi tất cả annotators.

*Bảng 3. Inter-annotator agreement scores (placeholder—điền sau khi annotation hoàn thành).*

| Field | Metric | Score | Target |
|-------|--------|-------|--------|
| evidence_sufficient | Cohen's κ | [--] | ≥ 0.75 |
| should_abstain | Cohen's κ | [--] | ≥ 0.75 |
| hallucination_type | Cohen's κ | [--] | ≥ 0.70 |
| valid_at_query_date | Cohen's κ | [--] | ≥ 0.80 |
| citation (composite) | Span F1 | [--] | ≥ 0.80 |

### 4.2. Phương pháp Baseline và Implementation

Chúng tôi so sánh sáu hệ thống representing một spectrum của adaptation levels. Tất cả hệ thống sử dụng cùng backbone model.

**Baseline 1a (Zero-shot):** Inference trực tiếp trên pre-trained backbone mà không có domain adaptation hoặc legal prompting. Baseline này quantifies raw Vietnamese legal reasoning capability của foundation model.

**Baseline 1b (Reasoning):** Inference với chain-of-thought prompting kích hoạt multi-step reasoning mà không có weight updates.

**Baseline 2a (Legal prompting):** Inference với structured legal và task-aware prompts specifying legal domain, required output format và citation convention.

**Baseline 2b (Legal + Reasoning):** Kết hợp legal prompting với chain-of-thought reasoning.

**Baseline 3 (PEFT, no reliability augmentation):** LoRA fine-tuning trên dữ liệu pháp lý Việt Nam mà không có reliability annotation layer.

**Proposed method (Full framework):** LoRA fine-tuning kết hợp với task-aware inference, guided bởi complete reliability annotation layer.

*Implementation details.* Chúng tôi sử dụng Google Gemma 4 E4B (8-bit quantized) làm backbone model, selected cho strong multilingual capability including Vietnamese và compatibility với parameter-efficient fine-tuning. Experiments chạy trên Ollama local server với max sequence length 32,768 tokens và batch size 4.

*[Placeholder: LoRA configuration cho Baseline 3 và Proposed—điền sau khi fine-tune hoàn thành]*
- LoRA rank: [--]
- LoRA alpha: [--]
- Learning rate: [--]
- Epochs: [--]
- Hardware: [--]

### 4.3. Evaluation Metrics

Metrics được tổ chức thành hai nhóm corresponding với hai evaluation components của Layer 4.

**4.3.1. Core Benchmark Metrics**

Đối với MC và BC tasks, chúng tôi sử dụng accuracy (Acc) làm primary metric. Đối với extraction tasks, chúng tôi sử dụng token-level F1. Đối với generation tasks, chúng tôi sử dụng ROUGE-L và BERTScore.

**4.3.2. Reliability Metrics**

Để đánh giá ba chiều reliability, chúng tôi định nghĩa sáu complementary metrics:

**Metric 1—Citation Correctness (CitAcc).** Tỷ lệ model responses correctly identify supporting legal provision ở specified granularity level.

**Metrics 2 & 3—Recency-Aware Score (RAS) và Recency-Aware Recall (RAR).** Chúng tôi adopt RAS và RAR để đánh giá temporal validity. RAS áp dụng exponential decay weighting penalise citations temporally distant from query date.

**Metric 4—Evidence Support Rate (ESR).** Tỷ lệ model responses fully supported bởi ít nhất một annotated evidentiary passage.

**Metric 5—Unsupported Claim Rate (UCR).** Tỷ lệ model responses containing ít nhất một unsupported claim.

**Metric 6—Abstention Accuracy (AbsAcc).** Over should-abstain samples, tỷ lệ models correctly express uncertainty.

---

## 5. Kết quả

### 5.1. Hiệu suất trên Benchmark Cốt lõi

Bảng 4 trình bày hiệu suất của hệ thống baseline (Gemma 4 E4B, fewshot prompting) trên 22 nhiệm vụ VLegal-Bench.

*Bảng 4. Kết quả benchmark cốt lõi trên VLegal-Bench.*

| Task | Category | Accuracy | Precision | Recall | F1 |
|------|----------|----------|-----------|--------|-----|
| 1.1 | Recognition | 71.39% | 71.39% | 71.39% | 71.39% |
| 1.2 | Classification | 80.23% | 80.23% | 80.23% | 80.23% |
| 1.3 | Concept Recall | 67.33% | 67.33% | 67.33% | 67.33% |
| 1.4 | Article Recall | 76.55% | 76.55% | 76.55% | 76.55% |
| 1.5 | Schema Recall | 35.20% | 35.20% | 35.20% | 35.20% |
| 2.1 | Relation Extraction | 77.08% | 77.08% | 77.08% | 77.08% |
| 2.2 | Element Recognition | 61.33% | 61.33% | 61.33% | 61.33% |
| 2.3 | Graph Structuring | - | - | - | BLEU: 0.50, ROUGE: 0.73 |
| 2.4 | Judgement Verification | 81.97% | 81.97% | 81.97% | 81.97% |
| 2.5 | Intent Understanding | 18.47% | 79.47% | 41.27% | 54.33% |
| 3.1 | Clause Prediction | 39.33% | 39.33% | 39.33% | 39.33% |
| 3.2 | Decision Prediction | 79.83% | 79.83% | 79.83% | 79.83% |
| 3.3 | Multi-hop Reasoning | 66.44% | 67.13% | 66.44% | 66.78% |
| 3.4 | Conflict Detection | - | - | - | Macro-F1: 0.28-0.39 |
| 3.5 | Penalty Estimation | 59.89% | 59.89% | 59.89% | 59.89% |
| 4.1 | Summarization | - | - | - | BLEU: 0.03, ROUGE: 0.23 |
| 4.2 | Judicial Reasoning | - | - | - | BLEU: 0.10, ROUGE: 0.35 |
| 4.3 | Legal Opinion | - | - | - | BLEU: 0.14, ROUGE: 0.38 |
| 5.1 | Bias Detection | 41.77% | 41.77% | 41.77% | 41.77% |
| 5.2 | Privacy Protection | 68.20% | 68.20% | 68.20% | 68.20% |
| 5.4 | Unfair Contract | 64.10% | 64.10% | 64.10% | 64.10% |

*Bảng 5. Tổng hợp hiệu suất theo category.*

| Category | Avg Accuracy | Avg BLEU | Avg ROUGE | Đánh giá |
|----------|--------------|----------|-----------|----------|
| 1.x Recognition & Recall | 66.14% | - | - | Khá |
| 2.x Understanding & Structuring | 59.84% | 0.50 | 0.73 | Khá |
| 3.x Reasoning & Inference | 61.37% | - | - | Khá |
| 4.x Interpretation & Generation | - | 0.09 | 0.32 | Yếu |
| 5.x Ethics, Fairness & Bias | 58.02% | - | - | Khá |

**Phân tích.** Kết quả cho thấy Gemma 4 E4B đạt hiệu suất tốt nhất trên các nhiệm vụ classification và verification (1.2: 80.23%, 2.4: 81.97%, 3.2: 79.83%), trong khi struggle trên các nhiệm vụ yêu cầu reasoning phức tạp (1.5: 35.20%, 2.5: 18.47%, 3.1: 39.33%). Các nhiệm vụ generation (Category 4.x) cho thấy BLEU score thấp (0.03-0.14), suggesting rằng mô hình cần domain adaptation để cải thiện performance trên các nhiệm vụ này.

*[Placeholder: Bảng so sánh 6 hệ thống—điền sau khi chạy đầy đủ experiments]*

*Bảng 6. So sánh hiệu suất 6 hệ thống trên VLegal-Bench.*

| System | 1.x | 2.x | 3.x | 4.x | 5.x | Avg |
|--------|-----|-----|-----|-----|-----|-----|
| Baseline 1a (Zero-shot) | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 1b (Reasoning) | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 2a (Legal Prompt) | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 2b (Legal+Reasoning) | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 3 (LoRA, no rel.) | [--] | [--] | [--] | [--] | [--] | [--] |
| Proposed (LoRA + rel.) | [--] | [--] | [--] | [--] | [--] | [--] |

### 5.2. Hiệu suất trên Reliability Metrics

*[Placeholder—điền sau khi chạy reliability metrics trên annotated subset]*

*Bảng 7. Kết quả reliability metrics trên annotated subset.*

| System | CitAcc | RAS | RAR | ESR | UCR (↓) | AbsAcc |
|--------|--------|-----|-----|-----|---------|--------|
| Baseline 1a | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 1b | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 2a | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 2b | [--] | [--] | [--] | [--] | [--] | [--] |
| Baseline 3 | [--] | [--] | [--] | [--] | [--] | [--] |
| Proposed | [--] | [--] | [--] | [--] | [--] | [--] |

### 5.3. Ablation Study

*[Placeholder—điền sau khi chạy ablation study]*

*Bảng 8. Ablation study: đóng góp incremental của mỗi annotation component.*

| Component | Acc | F1 | CitAcc | RAS | ESR | AbsAcc |
|-----------|-----|----|--------|-----|-----|--------|
| Base (Zero-shot) | [--] | [--] | [--] | [--] | [--] | [--] |
| + Reasoning | [--] | [--] | [--] | [--] | [--] | [--] |
| + Legal Prompt | [--] | [--] | [--] | [--] | [--] | [--] |
| + LoRA | [--] | [--] | [--] | [--] | [--] | [--] |
| + Citation Annotation | [--] | [--] | [--] | [--] | [--] | [--] |
| + Temporal Annotation | [--] | [--] | [--] | [--] | [--] | [--] |
| + Reliability Supervision | [--] | [--] | [--] | [--] | [--] | [--] |
| Full Framework | [--] | [--] | [--] | [--] | [--] | [--] |

### 5.4. Phân tích Case Study

*[Placeholder—điền sau khi có annotated samples]*

**Case 1: Citation Hallucination trong Article Retrieval**
- Input: [--]
- Baseline output: [--]
- Proposed output: [--]
- Gold citation: [--]
- Phân tích: [--]

**Case 2: Temporal Confusion trong Regulatory Validity**
- Input: [--]
- Baseline output: [--]
- Proposed output: [--]
- Gold annotation: [--]
- Phân tích: [--]

**Case 3: Appropriate Abstention under Insufficient Evidence**
- Input: [--]
- Baseline output: [--]
- Proposed output: [--]
- Expected behavior: [--]
- Phân tích: [--]

---

## 6. Thảo luận

### 6.1. Hệ quả học thuật

Bài báo này đóng góp một phương pháp luận demonstrating cách một legal benchmark well-constructed có thể được mở rộng từ đánh giá capability tổng quát sang đánh giá hướng reliability thông qua structured annotation augmentation. Lớp annotation reliability và bộ sáu metrics operationalise khung đánh giá LLM pháp lý ba chiều recommended trong công trình survey gần đây [1], cung cấp một instantiation cụ thể mà researchers trong các jurisdiction khác có thể adapt.

### 6.2. Hệ quả thực tiễn

Một hệ thống AI pháp lý đạt điểm cao trên tất cả sáu reliability metrics tiến gần hơn đáng kể đến các yêu cầu của một deployable legal assistant. Lawyers, judges và legal researchers yêu cầu rằng hệ thống cite đúng điều luật, cite điều luật currently in force và acknowledge limits of its knowledge khi sources ambiguous hoặc absent.

### 6.3. Hạn chế

Một số hạn chế phải được acknowledged. Thứ nhất, subset annotation chỉ cover một phần selected của 22 tasks VLegal-Bench. Thứ hai, strong benchmark performance không certify safety cho deployment trong actual legal proceedings. Thứ ba, chất lượng temporal validity annotation phụ thuộc vào completeness của official legal databases. Thứ tư, results có thể vary across backbone model families.

---

## 7. Kết luận

Chúng tôi đã đề xuất một khung đánh giá hướng tới tính đáng tin cậy cho LLM pháp lý tiếng Việt, xây dựng xung quanh VLegal-Bench làm benchmark cốt lõi và mở rộng với một lớp annotation structured cung cấp citation grounding, temporal validity và reliability supervision labels.

Kết quả thực nghiệm sơ bộ với Gemma 4 E4B cho thấy hiệu suất khác biệt đáng kể across task categories, với average accuracy 61.4% trên MC tasks và BLEU score 0.09 trên generation tasks. Các phát hiện này establish baseline cho các thí nghiệm domain adaptation tiếp theo với LoRA fine-tuning và reliability-oriented training.

Công trình future work sẽ: (1) hoàn thành annotation trên 1500 mẫu; (2) chạy đầy đủ 6 hệ thống experiments; (3) fine-tune với LoRA và reliability annotations; (4) mở rộng annotation layer cho tất cả 22 task types; (5) tích hợp retrieval-augmented generation với automated citation verification.

---

## Tài liệu tham khảo

[1] Nguyen, T.T., et al.: Evaluation of Large Language Models in Legal Applications: Challenges, Methods, and Future Directions. arXiv:2601.15267 (2026)

[2] Nguyen, D.Q., et al.: VLegal-Bench: Cognitively Grounded Benchmark for Vietnamese Legal Reasoning of Large Language Models. arXiv:2512.14554 (2025)

[3] Cui, J., et al.: Large Language Models in Legal Systems: A Survey. DOAJ (2024)

[4] Wang, X., et al.: Large Language Models Meet Legal Artificial Intelligence: A Survey. arXiv:2509.09969 (2025)

[5] Minaee, S., et al.: Large Language Models: A Survey. arXiv:2402.06196 (2024)

[6] Brown, T., et al.: Language Models are Few-Shot Learners. In: Advances in Neural Information Processing Systems 33, pp. 1877-1901 (2020)

[7] Wei, J., et al.: Finetuned Language Models are Zero-Shot Learners. In: ICLR 2022 (2022)

[8] Hu, E.J., et al.: LoRA: Low-Rank Adaptation of Large Language Models. In: ICLR 2022 (2022)

[9] Wei, J., et al.: Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. In: NeurIPS 2022 (2022)

[10] Lewis, P., et al.: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In: NeurIPS 2020 (2020)

[11] Min, S., et al.: FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long-form Text Generation. In: EMNLP 2023 (2023)

[12] Tonmoy, S.M.T.I., et al.: A Comprehensive Survey of Hallucination Mitigation Techniques in Large Language Models. arXiv:2401.01313 (2024)

[13] Fei, Z., et al.: LawBench: Benchmarking Legal Knowledge of Large Language Models. arXiv:2309.16289 (2023)

[14] Xiao, C., et al.: LEGEL: Evaluating Legal Reasoning Capabilities of Large Language Models. arXiv:2305.07507 (2023)

[15] Zheng, L., et al.: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. In: NeurIPS 2023 (2023)

[16] Madhusudhan, S.T., et al.: Do LLMs Know When to NOT Answer? Investigating Abstention Abilities of Large Language Models (Abstain-QA). In: Proceedings of COLING 2025, pp. 9329-9345. ACL (2025)

[17] Nguyen, T.D., et al.: LexTIME: A Benchmark for Temporal Ordering of Vietnamese Legal Provisions. arXiv:2506.04041 (2025)

[18] Zhao, Y., et al.: Program-Verifiable Evaluation for Temporal Question Answering: Metrics for Evidence Validity (RAS and RAR). In: IEEE Transactions on Knowledge and Data Engineering (2025)
