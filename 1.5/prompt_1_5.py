PROMPT_CREATE_DATASET = """
Bạn là một chuyên gia xây dựng ngân hàng câu hỏi trắc nghiệm pháp luật Việt Nam.
Dưới đây là thông tin dạng lược đồ về một cặp văn bản pháp luật Việt Nam, 
bao gồm thông tin của văn bản ban hành trước, thông tin của văn bản ban hành sau và mối quan hệ của chúng.

Hãy tạo ra một câu hỏi trắc nghiệm duy nhất với 4 lựa chọn dựa trên thông tin này. 
**Yêu cầu**:
- Nội dung câu hỏi: liên quan đến mối quan hệ giữa văn bản trước và văn bản sau (ví dụ: văn bản sau sửa đổi, bổ sung văn bản trước; văn bản sau thay thế văn bản trước; văn bản sau được ban hành để thi hành văn bản trước; v.v.)
- Câu hỏi phải có:
  • Instruction: “Đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.”  
  • Question: [Một câu hỏi tự nhiên, rõ ràng về mối quan hệ giữa hai văn bản pháp luật. Văn bản được đề cập trong câu hỏi phải nêu rõ số liệu.]
  • Answers: [Đáp án là số hiệu của các văn bản quy phạm pháp luật khác nhau.Tạo 4 phương án A, B, C, D - gồm 1 đáp án đúng và 3 đáp án sai.]
  • Ground truth: chỉ ra đáp án đúng bằng chữ cái A, B, C hoặc D.
- Câu hỏi viết bằng tiếng Việt, rõ ràng, mang phong cách chính thống như trong các đề thi công chức.
- Tận dụng tối đa thông tin trong thông tin lược đồ được cung cấp:
• Thông tin văn bản ban hành trước: loai_van_ban, so_hieu, trich_yeu, ngay_ban_hanh, ngay_co_hieu_luc.
• Thông tin văn bản ban hành sau: so_hieu, loai_van_ban, ngay_ban_hanh, ngay_hieu_luc, tinh_trang.
- Đảm bảo rằng các lựa chọn đáp án là các văn bản pháp luật hợp lệ và khác nhau.
- Đa dạng mối quan hệ chủ động và bị động giữa hai văn bản trong câu hỏi.

Ví dụ đầu ra mong muốn: 
```json
{
  "Instruction": "Đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.",
  "Question": "Luật 90/2025/QH15 sửa đổi, bổ sung những văn bản quy phạm pháp luật nào?",
  "Answers": {
    "A": "Luật 48/2024/QH15",
    "B": "Luật 72/2025/QH15",
    "C": "Luật 56/2024/QH15",
    "D": "Luật 09/VBHN-VPQH"
    }
  },
  "Ground truth": "C"
}
```
"""
EXAMPLE = """
Nhiệm vụ của bạn là trả lời câu hỏi trắc nghiệm sau, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là trả lời câu hỏi trắc nghiệm sau, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.
**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Question: Thông tư 11/2025/TT-BTP có mối quan hệ như thế nào với Văn bản hợp nhất 5796/VBHN-BTP?
Answers: {"A": "Thông tư là cơ sở để ban hành Văn bản hợp nhất 5796/VBHN-BTP", "B": "Thông tư là văn bản hợp nhất từ Văn bản hợp nhất 5796/VBHN-BTP", "C": "Thông tư sửa đổi Văn bản hợp nhất 5796/VBHN-BTP", "D": "Thông tư hợp nhất các nội dung của Văn bản hợp nhất 5796/VBHN-BTP"}
Ground truth: C
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc câu hỏi trắc nghiệm pháp luật tiếng Việt về mối quan hệ giữa các văn bản pháp luật và chọn đáp án đúng (A, B, C hoặc D). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích câu hỏi và đưa ra suy luận cho câu trả lời.
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
