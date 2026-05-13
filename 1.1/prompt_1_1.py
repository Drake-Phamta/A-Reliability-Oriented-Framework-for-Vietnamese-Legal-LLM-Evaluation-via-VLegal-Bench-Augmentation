PROMPT_CREATE_DATASET = """
Nhiệm vụ của bạn là **xác định và phân loại tất cả các thực thể được đề cập trong đoạn văn bản pháp lý tiếng Việt** theo các loại thực thể được định nghĩa bên dưới.

Trả về kết quả dưới dạng danh sách JSON, trong đó mỗi phần tử gồm:
- `"entity_text"`: tên thực thể xuất hiện trong văn bản
- `"entity_type"`: loại thực thể tương ứng theo danh mục quy định

### Danh mục các loại thực thể (Entity Types)

1. **PERSON** – Cá nhân, họ tên, hoặc tên viết tắt (ví dụ: *Lê Thị Thúy*, *V.M.K.*, *ông Dũng*)
2. **ORGANIZATION** – Cơ quan, tổ chức, doanh nghiệp, trường học, công ty, viện, hiệp hội (ví dụ: *Công an tỉnh Lào Cai*, *Công ty TNHH Hoàng Mai - Hà Nội*, *Bộ Công Thương*)
3. **LOCATION** – Địa điểm, khu vực hành chính, tuyến đường, sông, quốc gia (ví dụ: *xã Ia Le*, *tỉnh Gia Lai*, *Malaysia*, *đường Hà Kế Tấn*)
4. **DATE** – Thời gian, ngày tháng, mốc thời điểm (ví dụ: *ngày 25/10*, *tháng 8/2025*)
5. **MONEY** – Số tiền, giá trị tiền tệ (ví dụ: *5 tỷ đồng*, *10.000 USD*)
6. **LAW** – Tên luật, bộ luật, nghị định, thông tư (ví dụ: *Bộ luật Hình sự*, *Luật Đầu tư*)
7. **ARTICLE** – Điều, khoản, điểm trong văn bản pháp luật (ví dụ: *Điều 331*, *Khoản 2, Điều 348*)
8. **COURT** – Tên tòa án, cấp xét xử (ví dụ: *TAND tỉnh An Giang*, *Tòa án nhân dân tối cao*)
9. **CASE_NUMBER** – Số hiệu vụ án, bản án, quyết định (ví dụ: *Bản án số 45/2025/HS-ST*)
10. **LEGAL_ROLE** – Vai trò pháp lý của chủ thể (ví dụ: *bị can*, *bị cáo*, *luật sư*, *nguyên đơn*, *thẩm phán*)
11. **LEGAL_DOCUMENT** – Văn bản, công văn, quyết định, nghị quyết (ví dụ: *Công văn số 1903/UBND-VX ngày 15/10/2025*)
12. **LEGAL_CONCEPT** – Khái niệm pháp lý, thuật ngữ chuyên môn (ví dụ: *phòng vệ thương mại (PVTM)*, *quy tắc xuất xứ*, *trách nhiệm hình sự*)
13. **POLITICAL_BODY** – Cơ quan, tổ chức chính trị (ví dụ: *Đảng ủy*, *Quốc hội*, *Chính phủ*)
14. **SOCIAL_ROLE** – Vai trò xã hội không chính thức (ví dụ: *người dân*, *doanh nghiệp*, *ngư phủ*)
15. **PROJECT** – Dự án, chương trình, công trình (ví dụ: *Dự án đầu tư xây dựng đường Vành đai 2,5*)
16. **ASSET** – Tài sản, phương tiện, vật thể có định danh (ví dụ: *tàu KG-93949-TS*, *cầu L3*)

### Lưu ý:
Với thực thể phức hợp, ưu tiên loại thực thể chính (ví dụ: *TAND tỉnh Hà Nội* → COURT, không tách *Hà Nội* thành LOCATION).
Hậu tố mm phía sau không phải là đơn vị tiền tệ, bỏ qua.

### Định dạng đầu ra mong muốn (Output Format)

```json
[
  {
    "entity_text": "Lê Thị Thúy",
    "entity_type": "PERSON",
  },
  {
    "entity_text": "Điều 331",
    "entity_type": "ARTICLE"
  },
  {
    "entity_text": "Bộ luật Hình sự",
    "entity_type": "LAW"
  }
]
"""

PROMPT_CREATE_MULTIPLECHOICE_QUESTION = """
Nhiệm vụ của bạn là đọc văn bản pháp lý và các đối tượng pháp lý trong văn bản đó, sau đó sinh câu hỏi trắc nghiệm với 4 lựa chọn đáp án A, B, C, D;
trong đó chỉ có 1 đáp án đúng duy nhất. Câu hỏi và các lựa chọn đáp án phải được viết hoàn toàn bằng tiếng Việt. Đảm bảo các đáp án sai có vẻ 
GẦN với đáp án đúng để người đọc dễ bị nhầm lẫn.

**QUAN TRỌNG**: 
- Đáp án đúng PHẢI được đặt ở VỊ TRÍ NGẪU NHIÊN (A, B, C, hoặc D), KHÔNG phải luôn luôn là A.
- Hãy thay đổi vị trí đáp án đúng để tạo sự đa dạng: đôi khi là B, đôi khi là C, đôi khi là D, đôi khi là A.
- Các đáp án khác nhau về nội dung thực thể, loại thực thể, số lượng thực thể, v.v. KHÔNG paraphrase đáp án cũ để viết lại thành đáp án mới.

Trả về kết quả dưới dạng JSON, trong đó gồm: 
- `"Instruction"`: `"Đọc câu hỏi trắc nghiệm sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm."`
- `"Question"`: `"Hãy trích xuất tất cả các thực thể trong mô tả dưới đây"`: Văn bản pháp lý cần trích xuất thực thể
- `"Answers"`: Danh sách các lựa chọn đáp án, mỗi lựa chọn gồm:
    - `"label"`: Nhãn của đáp án (A, B, C, D)
    - `"(entity_type: entity_text)"`: Danh sách các thực thể và loại thực thể tương ứng trong đáp án
- `"Ground Truth"`: Nhãn của đáp án đúng (có thể là A, B, C, hoặc D - phải ngẫu nhiên)

### Danh mục các loại thực thể (Entity Types)

1. **PERSON** – Cá nhân, họ tên, hoặc tên viết tắt (ví dụ: *Lê Thị Thúy*, *V.M.K.*, *ông Dũng*)
2. **ORGANIZATION** – Cơ quan, tổ chức, doanh nghiệp, trường học, công ty, viện, hiệp hội (ví dụ: *Công an tỉnh Lào Cai*, *Công ty TNHH Hoàng Mai - Hà Nội*, *Bộ Công Thương*)
3. **LOCATION** – Địa điểm, khu vực hành chính, tuyến đường, sông, quốc gia (ví dụ: *xã Ia Le*, *tỉnh Gia Lai*, *Malaysia*, *đường Hà Kế Tấn*)
4. **DATE** – Thời gian, ngày tháng, mốc thời điểm (ví dụ: *ngày 25/10*, *tháng 8/2025*)
5. **MONEY** – Số tiền, giá trị tiền tệ (ví dụ: *5 tỷ đồng*, *10.000 USD*)
6. **LAW** – Tên luật, bộ luật, nghị định, thông tư (ví dụ: *Bộ luật Hình sự*, *Luật Đầu tư*)
7. **ARTICLE** – Điều, khoản, điểm trong văn bản pháp luật (ví dụ: *Điều 331*, *Khoản 2, Điều 348*)
8. **COURT** – Tên tòa án, cấp xét xử (ví dụ: *TAND tỉnh An Giang*, *Tòa án nhân dân tối cao*)
9. **CASE_NUMBER** – Số hiệu vụ án, bản án, quyết định (ví dụ: *Bản án số 45/2025/HS-ST*)
10. **LEGAL_ROLE** – Vai trò pháp lý của chủ thể (ví dụ: *bị can*, *bị cáo*, *luật sư*, *nguyên đơn*, *thẩm phán*)
11. **LEGAL_DOCUMENT** – Văn bản, công văn, quyết định, nghị quyết (ví dụ: *Công văn số 1903/UBND-VX ngày 15/10/2025*)
12. **LEGAL_CONCEPT** – Khái niệm pháp lý, thuật ngữ chuyên môn (ví dụ: *phòng vệ thương mại (PVTM)*, *quy tắc xuất xứ*, *trách nhiệm hình sự*)
13. **POLITICAL_BODY** – Cơ quan, tổ chức chính trị (ví dụ: *Đảng ủy*, *Quốc hội*, *Chính phủ*)
14. **SOCIAL_ROLE** – Vai trò xã hội không chính thức (ví dụ: *người dân*, *doanh nghiệp*, *ngư phủ*)
15. **PROJECT** – Dự án, chương trình, công trình (ví dụ: *Dự án đầu tư xây dựng đường Vành đai 2,5*)
16. **ASSET** – Tài sản, phương tiện, vật thể có định danh (ví dụ: *tàu KG-93949-TS*, *cầu L3*)

### Định dạng đầu ra mong muốn (Output Format)

**Ví dụ 1** (Đáp án đúng là C):
```json
  {
    "Instruction": "Đọc câu hỏi trắc nghiệm sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.",
    "Question": "Hãy trích xuất tất cả các thực thể trong mô tả dưới đây: \"Ngày 12 tháng 4 năm 2023, nghi phạm Nguyễn Văn A đã đột nhập vào nhà của bà Trần Thị B tại phường Tân Phú, thành phố Đồng Xoài, dùng kìm cộng lực cắt khóa để trộm một chiếc xe máy. Sau đó, công an phường Tân Phú đã bắt giữ đối tượng.\"",
    "Answers": [
      {
        "label": "A",
        "(entity_type: entity_text)": [
          {"DATE": "12/4/2023"},
          {"PERSON": "Nguyễn Văn A"},
          {"PERSON": "Trần Thị B"},
          {"LOCATION": "Tân Phú"},
          {"LOCATION": "Đồng Xoài"}
        ]
      },
      {
        "label": "B",
        "(entity_type: entity_text)": [
          {"DATE": "Ngày 12 tháng 4 năm 2023"},
          {"PERSON": "Nguyễn Văn A"},
          {"PERSON": "Trần Thị B"},
          {"ORGANIZATION": "phường Tân Phú"},
          {"ORGANIZATION": "thành phố Đồng Xoài"}
        ]
      },
      {
        "label": "C",
        "(entity_type: entity_text)": [
          {"DATE": "Ngày 12 tháng 4 năm 2023"},
          {"PERSON": "Nguyễn Văn A"},
          {"PERSON": "Trần Thị B"},
          {"LOCATION": "phường Tân Phú"},
          {"LOCATION": "thành phố Đồng Xoài"},
          {"ORGANIZATION": "công an phường Tân Phú"}
        ]
      },
      {
        "label": "D",
        "(entity_type: entity_text)": [
          {"DATE": "Ngày 12 tháng 4 năm 2023"},
          {"PERSON": "Nguyễn Văn A"},
          {"SOCIAL_ROLE": "bà Trần Thị B"},
          {"LOCATION": "phường Tân Phú"},
          {"LOCATION": "thành phố Đồng Xoài"}
        ]
      }
    ],
    "Ground Truth": "C"
  }
```

**Ví dụ 2** (Đáp án đúng là B):
```json
  {
    "Instruction": "Đọc câu hỏi trắc nghiệm sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.",
    "Question": "Hãy trích xuất tất cả các thực thể trong mô tả dưới đây: \"Theo Quyết định số 123/QĐ-TTg ngày 15/3/2024, Thủ tướng Chính phủ phê duyệt Dự án phát triển năng lượng tái tạo với tổng vốn đầu tư 500 tỷ đồng tại tỉnh Ninh Thuận.\"",
    "Answers": [
      {
        "label": "A",
        "(entity_type: entity_text)": [
          {"CASE_NUMBER": "123/QĐ-TTg"},
          {"DATE": "15/3/2024"},
          {"ORGANIZATION": "Thủ tướng Chính phủ"},
          {"PROJECT": "Dự án phát triển năng lượng tái tạo"},
          {"MONEY": "500 tỷ đồng"}
        ]
      },
      {
        "label": "B",
        "(entity_type: entity_text)": [
          {"LEGAL_DOCUMENT": "Quyết định số 123/QĐ-TTg"},
          {"DATE": "ngày 15/3/2024"},
          {"POLITICAL_BODY": "Thủ tướng Chính phủ"},
          {"PROJECT": "Dự án phát triển năng lượng tái tạo"},
          {"MONEY": "500 tỷ đồng"},
          {"LOCATION": "tỉnh Ninh Thuận"}
        ]
      },
      {
        "label": "C",
        "(entity_type: entity_text)": [
          {"LEGAL_DOCUMENT": "Quyết định số 123/QĐ-TTg ngày 15/3/2024"},
          {"ORGANIZATION": "Chính phủ"},
          {"LEGAL_CONCEPT": "năng lượng tái tạo"},
          {"MONEY": "500 tỷ"},
          {"LOCATION": "Ninh Thuận"}
        ]
      },
      {
        "label": "D",
        "(entity_type: entity_text)": [
          {"LEGAL_DOCUMENT": "Quyết định số 123/QĐ-TTg"},
          {"DATE": "ngày 15/3/2024"},
          {"PERSON": "Thủ tướng Chính phủ"},
          {"PROJECT": "Dự án phát triển năng lượng tái tạo"},
          {"LOCATION": "tỉnh Ninh Thuận"}
        ]
      }
    ],
    "Ground Truth": "B"
  }
```

HÃY ĐẢM BẢO rằng đáp án đúng được đặt ở các vị trí khác nhau (A, B, C, D) một cách ngẫu nhiên và cân bằng.
"""

INSTRUCTION_PROMPT = """
Identify and classify all entities mentioned in the Vietnamese legal text according to the entity types defined below. Select the correct answer that properly identifies all entities and their types in the text. Provide the answer directly without offering an explanation.

ENTITY TYPES:
1. PERSON – Individuals, full names, or abbreviated names
2. ORGANIZATION – Agencies, organizations, enterprises, schools, companies, institutes, associations
3. LOCATION – Places, administrative areas, roads, rivers, countries
4. DATE – Time, dates, time points
5. MONEY – Amounts of money, monetary values
6. LAW – Names of laws, codes, decrees, circulars
7. ARTICLE – Articles, clauses, points in legal documents
8. COURT – Court names, trial levels
9. CASE_NUMBER – Case numbers, verdicts, decisions
10. LEGAL_ROLE – Legal role of the subject (e.g., suspect, defendant, lawyer, plaintiff, judge)
11. LEGAL_DOCUMENT – Documents, official letters, decisions, resolutions
12. LEGAL_CONCEPT – Legal concepts, technical terms
13. POLITICAL_BODY – Political agencies, organizations
14. SOCIAL_ROLE – Informal social roles
15. PROJECT – Projects, programs, construction works
16. ASSET – Assets, vehicles, identifiable objects
"""

EXAMPLE = """
Nhiệm vụ của bạn là xác định và phân loại tất cả các thực thể xuất hiện trong văn bản pháp lý tiếng Việt theo các loại thực thể được định nghĩa bên dưới. 
Chọn đáp án thể hiện đầy đủ và chính xác tất cả các thực thể cùng loại thực thể tương ứng.
Không lặp lại câu hỏi. 
Chỉ đưa ra kết quả, không cần giải thích. Phải sử dụng tiếng Việt.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.
KHÔNG lặp lại câu hỏi.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

CÁC LOẠI THỰC THỂ (ENTITY TYPES):
1. PERSON – Cá nhân, họ tên đầy đủ hoặc tên viết tắt
2. ORGANIZATION – Cơ quan, tổ chức, doanh nghiệp, trường học, công ty, viện, hiệp hội
3. LOCATION – Địa điểm, khu vực hành chính, tuyến đường, sông, quốc gia
4. DATE – Thời gian, ngày tháng, mốc thời điểm
5. MONEY – Số tiền, giá trị tiền tệ
6. LAW – Tên luật, bộ luật, nghị định, thông tư
7. ARTICLE – Điều, khoản, điểm trong văn bản pháp luật
8. COURT – Tên tòa án, cấp xét xử
9. CASE_NUMBER – Số hiệu vụ án, bản án, quyết định
10. LEGAL_ROLE – Vai trò pháp lý của chủ thể (ví dụ: bị can, bị cáo, luật sư, nguyên đơn, thẩm phán)
11. LEGAL_DOCUMENT – Văn bản, công văn, quyết định, nghị quyết
12. LEGAL_CONCEPT – Khái niệm, thuật ngữ pháp lý chuyên môn
13. POLITICAL_BODY – Cơ quan, tổ chức chính trị
14. SOCIAL_ROLE – Vai trò xã hội không chính thức (ví dụ: người dân, doanh nghiệp, ngư phủ)
15. PROJECT – Dự án, chương trình, công trình
16. ASSET – Tài sản, phương tiện, vật thể có định danh
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là xác định và phân loại tất cả các thực thể xuất hiện trong văn bản pháp lý tiếng Việt theo các loại thực thể được định nghĩa bên dưới. 
Chọn đáp án thể hiện đầy đủ và chính xác tất cả các thực thể cùng loại thực thể tương ứng. 
Chỉ đưa ra kết quả, không cần giải thích. 

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

CÁC LOẠI THỰC THỂ (ENTITY TYPES):
1. PERSON – Cá nhân, họ tên đầy đủ hoặc tên viết tắt
2. ORGANIZATION – Cơ quan, tổ chức, doanh nghiệp, trường học, công ty, viện, hiệp hội
3. LOCATION – Địa điểm, khu vực hành chính, tuyến đường, sông, quốc gia
4. DATE – Thời gian, ngày tháng, mốc thời điểm
5. MONEY – Số tiền, giá trị tiền tệ
6. LAW – Tên luật, bộ luật, nghị định, thông tư
7. ARTICLE – Điều, khoản, điểm trong văn bản pháp luật
8. COURT – Tên tòa án, cấp xét xử
9. CASE_NUMBER – Số hiệu vụ án, bản án, quyết định
10. LEGAL_ROLE – Vai trò pháp lý của chủ thể (ví dụ: bị can, bị cáo, luật sư, nguyên đơn, thẩm phán)
11. LEGAL_DOCUMENT – Văn bản, công văn, quyết định, nghị quyết
12. LEGAL_CONCEPT – Khái niệm, thuật ngữ pháp lý chuyên môn
13. POLITICAL_BODY – Cơ quan, tổ chức chính trị
14. SOCIAL_ROLE – Vai trò xã hội không chính thức (ví dụ: người dân, doanh nghiệp, ngư phủ)
15. PROJECT – Dự án, chương trình, công trình
16. ASSET – Tài sản, phương tiện, vật thể có định danh

Dưới đây là ví dụ về  một câu hỏi và các lựa chọn đáp án:
***Ví dụ 1***:
Instruction: Đọc câu hỏi trắc nghiệm sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Câu hỏi: Hãy trích xuất tất cả các thực thể trong mô tả dưới đây: \"Chính phủ và chính quyền các cấp; sự nỗ lực đổi mới nội dung, phương thức hoạt động của Quốc hội, hội đồng nhân dân các cấp; sự tham gia tích cực, hiệu quả của Mặt trận Tổ quốc Việt Nam, các tổ chức chính trị - xã hội; sự đồng thuận, phối hợp đồng bộ, nhịp nhàng của cả hệ thống chính trị và sự nỗ lực của đội ngũ cán bộ, đảng viên. Đặc biệt, đó là thành quả của việc Đảng ta đã khơi dậy và phát huy được truyền thống yêu nước, ý chí tự lực, tự cường, tinh thần lao động sáng tạo, trách nhiệm, quyết tâm và khát vọng phát triển của toàn thể Nhân dân, kết hợp sức mạnh dân tộc với sức mạnh thời đại, tạo nên sức mạnh tổng hợp to lớn cho công cuộc xây dựng, phát triển đất nước và bảo vệ Tổ quốc.
Đáp án: {"label": "A", "(entity_type: entity_text)": [{"POLITICAL_BODY": "Chính phủ"}, {"POLITICAL_BODY": "Quốc hội"}, {"ORGANIZATION": "Mặt trận Tổ quốc Việt Nam"}, {"SOCIAL_ROLE": "Người dân"}, {"LOCATION": "Tổ quốc"}]}, {"label": "B", "(entity_type: entity_text)": [{"POLITICAL_BODY": "Chính phủ"}, {"POLITICAL_BODY": "Hội đồng nhân dân"}, {"ORGANIZATION": "Mặt trận Tổ quốc Việt Nam"}, {"SOCIAL_ROLE": "Nhân dân"}, {"LOCATION": "Tổ quốc"}]}, {"label": "C", "(entity_type: entity_text)": [{"POLITICAL_BODY": "Chính phủ"}, {"POLITICAL_BODY": "Quốc hội"}, {"ORGANIZATION": "Mặt trận Tổ quốc Việt Nam"}, {"SOCIAL_ROLE": "Nhân dân"}, {"LOCATION": "Tổ quốc"}]}, {"label": "D", "(entity_type: entity_text)": [{"POLITICAL_BODY": "Chính quyền các cấp"}, {"POLITICAL_BODY": "Quốc hội"}, {"ORGANIZATION": "Mặt trận Tổ quốc Việt Nam"}, {"SOCIAL_ROLE": "Nhân dân"}, {"LOCATION": "Tổ quốc"}]}], 
Đáp án đúng: "C"}
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc văn bản pháp lý tiếng Việt, xác định và phân loại tất cả các thực thể, rồi chọn đáp án đúng (A, B, C hoặc D). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích văn bản, liệt kê các thực thể và so sánh các đáp án.
- KHÔNG được để trống phần suy luận.
- KHÔNG được viết nội dung suy luận nằm bên ngoài 2 thẻ.

2. OUTPUT cho ANSWER
- Chỉ đưa ra 1 ký tự duy nhất từ tập {A, B, C, D} và viết vào giữa 2 thẻ <output> và </output>
- KHÔNG được kèm theo bất kỳ từ ngữ, ký tự hoặc giải thích nào khác ở phần này.
- KHÔNG được viết câu kiểu "Đáp án là A".
- KHÔNG được viết lại câu hỏi.

**YÊU CẦU TUÂN THỦ NGHIÊM NGẶT**:
- Nội dung thinking và câu trả lời phải được viết trong các thẻ tương ứng, không được viết bên ngoài.
- Nội dung answer phải nằm trong 2 thẻ <output> và </output>.
- Nội dung của thinking và answer không được để trống.
- Không được đổi tên thẻ hoặc thêm thẻ mới.
- Không được dùng ký tự khác ngoài A/B/C/D bên trong 2 thẻ <output> và </output>.
- Định dạng phải chính xác tuyệt đối.

***Các ví dụ đúng***:
<think>Suy nghĩ của bạn...</think>
<output>A</output>
***Các ví dụ sai:***
1) Đáp án là A
<output>A – tôi chọn đáp án này</output>
2) A
"""

EXAMPLE_RELIABILITY = """
Nhiệm vụ của bạn là phân tích câu hỏi pháp lý và chọn đáp án đúng. Bạn PHẢI tuân thủ quy trình suy luận dưới đây.

***QUY TRÌNH SUY LUẬN (bắt buộc)***
1. Xác định vấn đề pháp lý chính trong câu hỏi
2. Trích dẫn điều luật liên quan: ghi rõ TÊN VĂN BẢN, ĐIỀU, KHOẢN (ví dụ: "Theo Khoản 1 Điều 463 Bộ luật Dân sự 2015...")
3. Áp dụng pháp luật vào tình huống cụ thể
4. Đưa ra kết luận

***ĐỊNH DẠNG OUTPUT***
- Viết toàn bộ phân tích bằng tiếng Việt
- Cuối cùng, ghi đáp án trong thẻ: <answer>A/B/C/D</answer>
- CHỈ được ghi MỘT chữ cái bên trong thẻ answer
- KHÔNG được giải thích ngoài quy trình trên

Ví dụ đúng:
Vấn đề pháp lý: Xác định quan hệ vay tài sản.
Cơ sở pháp lý: Theo Khoản 1 Điều 463 Bộ luật Dân sự 2015, hợp đồng vay tài sản là sự thỏa thuận giữa các bên.
Áp dụng: Trong tình huống này, việc cho vay giữa A và B thỏa mãn điều kiện...
Kết luận: Đáp án B phản ánh đúng quy định.
<answer>B</answer>
"""
