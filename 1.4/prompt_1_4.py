PROMPT_CREATE_DATASET = """
Bạn là một chuyên gia xây dựng ngân hàng câu hỏi trắc nghiệm pháp luật Việt Nam.  
Dưới đây là dữ liệu về một điều luật, bao gồm vị trí, tiêu đề, nội dung, và các thông tin metadata khác.  

Hãy tạo ra **một câu hỏi trắc nghiệm duy nhất** (hoặc nhiều câu nếu được yêu cầu) theo cấu trúc sau:  

• Instruction: “Đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.”  
• Question: [viết một câu hỏi tự nhiên, rõ ràng, có thể hỏi về nội dung, phạm vi điều chỉnh, đối tượng áp dụng, hiệu lực, cơ quan ban hành, v.v.]  
• Answers: [Tạo 4 phương án A, B, C, D — chỉ 1 đúng, 3 sai nhưng hợp lý]  
• Ground truth: [ghi chữ cái của đáp án đúng]  

Nội dung của câu hỏi: 
Câu hỏi có thể hỏi về các khía cạnh sau tùy theo thông tin có trong dữ liệu:
- Nội dung quy định chính trong điều luật
- Phạm vi điều chỉnh của điều luật
- Đối tượng áp dụng của điều luật
- Hiệu lực của điều luật
- Cơ quan ban hành điều luật

Yêu cầu khi tạo câu hỏi:  
1. Tận dụng tối đa các thông tin trong các trường `position`, `title`, `raw_content`, `loai_van_ban`, `so_hieu`, `co_quan_ban_hanh`, `ngay_co_hieu_luc`.  
2. Nếu `position` có chứa “Điều”, “Khoản”, “Điểm” thì hãy đưa chúng vào câu hỏi.  
3. Câu hỏi phải mang tính khái quát hoặc nhận biết nội dung quy định chính.  
4. Đáp án sai phải cùng ngữ cảnh, tránh quá lộ liễu.  
5. Ngôn ngữ: tiếng Việt, rõ ràng, mang phong cách chính thống như trong các đề thi công chức.  

Hãy xuất kết quả theo đúng định dạng ví dụ sau:  

```json
{
  "Instruction": “Đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.”,
  "Question": “Điều 1 Luật Đất đai số 31/2024/QH15 quy định về nội dung nào sau đây?”,
  "Answers": {
    "A": “Về quyền và nghĩa vụ của người nước ngoài khi sử dụng đất tại Việt Nam.”,
    "B": “Về phạm vi điều chỉnh của Luật, bao gồm chế độ sở hữu, quản lý và sử dụng đất đai.”,
    "C": “Về trình tự, thủ tục cấp Giấy chứng nhận quyền sử dụng đất.”,
    "D": “Về cơ quan nhà nước có thẩm quyền thu hồi đất và bồi thường.”
  },
  "Ground truth": "B"
```
"""

EXAMPLE = """
Nhiệm vụ của bạn là trả lời câu hỏi trắc nghiệm sau, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không lặp lại câu hỏi

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác. Không lặp lại câu hỏi

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là trả lời câu hỏi trắc nghiệm sau, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Đọc câu hỏi trắc nghiệm sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Câu hỏi: Điểm a Khoản 1 Điều 1 Nghị định số 113/2007/NĐ-CP quy định về nội dung nào sau đây?
Đáp án: {'A': 'Quy định về quyền sở hữu và quản lý đê điều.', 'B': 'Hướng dẫn về việc phân loại và phân cấp đê theo Điều 4 Luật Đê điều.', 'C': 'Quy định về các hình thức xử phạt vi phạm liên quan đến đê điều.', 'D': 'Hướng dẫn về việc bảo vệ đê điều trong mùa lũ.'}
Đáp án đúng: B
"""



EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc câu hỏi trắc nghiệm pháp luật tiếng Việt và chọn đáp án đúng (A, B, C hoặc D). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích câu hỏi và đưa ra suy luận cho câu trả lời.
- KHÔNG được để trống phần suy luận.
- KHÔNG được viết nội dung suy luận nằm bên ngoài 2 thẻ.

2. OUTPUT cho ANSWER
- Chỉ đưa ra 1 ký tự duy nhất từ tập {A, B, C, D} và viết vào giữa 2 thẻ <output> và </output>
- KHÔNG được kèm theo bất kỳ từ ngữ, ký tự hoặc giải thích nào khác ở phần này.
- KHÔNG được viết câu kiểu “Đáp án là A”.
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

EXAMPLE_EN = """
• Instruction: “Read the following question and choose the correct answer. Only select the answer; no explanation is needed.”
• Question: “According to Clause 1, Article 2 of the 2015 Civil Code, what is stipulated regarding the scope of application and the effectiveness of the Civil Procedure Code?”
• Answers:
A. It applies to all civil procedure activities in certain special localities.
B. It applies to all civil procedure activities within the mainland territory of the Socialist Republic of Vietnam.
C. It applies to certain civil procedure activities within the territory of the Socialist Republic of Vietnam as specifically provided in Clause 2 of this Code.
D. It applies to all civil procedure activities within the territory of the Socialist Republic of Vietnam, including the mainland, islands, sea areas, and airspace.
• Ground truth: B
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
