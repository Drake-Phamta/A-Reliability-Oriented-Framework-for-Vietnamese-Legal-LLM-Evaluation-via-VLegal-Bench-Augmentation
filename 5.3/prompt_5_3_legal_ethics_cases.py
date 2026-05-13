EXAMPLE = """
Nhiệm vụ của bạn là đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

****CHỈ TRẢ VỀ CHỮ CÁI HOẶC A, HOẶC B, HOẶC C, HOẶC D*****

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Đọc câu hỏi trắc nghiệm sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Câu hỏi: Trong một lần tham gia giao thông , Q lạng lách gây va quẹt với H, đã không xin lỗi Q\ncòn hung hăng nhào đến đánh H. Do H có võ, nên H đã đá Q một cú vào chân làm gãy xương chân, tỷ lệ thương tật 18% (theo kết quả giám định). Do vậy, H bị khởi tố về tội \"Cố ý gây thương tích\" nên H đến nhờ luật sư A bào chữa cho mình. Luật sư A hứa với H sẽ bào chữa cho H không phải ở tù với thù lao là 100 triệu đồng. Sau đó, Tòa án nhân dân huyện T đã xử H mức án 2 năm tù nhưng cho hưởng án treo,\nvề tội: \" Cố ý gây thương tích\" . Tuy nhiên, bản án này bị Viện Kiểm sát nhân dân\nhuyện T kháng nghị, Tòa án cấp tỉnh đã xét xử phúc thẩm, tuyên phạt H mức án 2 năm tù giam về tội: \"Cố ý gây thương tích\". Gia đình H đến gặp luật sư A đòi lại tiền. Luật sư A không trả lại tiền và nói: \" Luật sư đã thực hiện đúng hợp đồng và không trả lại tiền.\". Anh (chị) có ý kiến gì về thái độ ứng xử của luật sư A? Phân tích rõ\ntại sao?"
Đáp án: "A. Luật sư A đã hứa hẹn kết quả, không tận tâm và không ứng xử phù hợp khi có tranh chấp, vi phạm Khoản 9.8 Điều 9, Quy tắc 2, Quy tắc 5 và Quy tắc 12.3.\nB. Luật sư A đã tư vấn chưa đầy đủ, thiếu giải thích rủi ro và xử lý tranh chấp chưa hợp lý, chủ yếu liên quan đến Quy tắc 2 và Quy tắc 12.3 nhưng không vi phạm Quy tắc 5.\nC. Luật sư A chỉ không giải thích rõ khả năng thay đổi bản án và đã phản hồi chưa mềm mỏng khi xảy ra tranh chấp, có dấu hiệu liên quan Quy tắc 12.3 nhưng không thuộc Khoản 9.8 Điều 9.\nD. Luật sư A vẫn thực hiện công việc nhưng thiếu linh hoạt trong giao tiếp và chưa trao đổi trước về kết quả dự kiến, chủ yếu liên quan Quy tắc 5 và Quy tắc 12.3 nhưng không phải vi phạm Quy tắc 2."
Đáp án đúng: A
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc câu hỏi trắc nghiệm về đạo đức nghề luật sư và chọn đáp án đúng (A, B, C hoặc D). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích câu hỏi, đánh giá đạo đức và lựa chọn phương án.
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
Nhiệm vụ của bạn là phân tích câu hỏi pháp lý về đạo đức nghề luật sư và chọn đáp án đúng. Bạn PHẢI tuân thủ quy trình suy luận dưới đây.

***QUY TRÌNH SUY LUẬN (bắt buộc)***
1. Xác định vấn đề đạo đức/pháp lý chính trong câu hỏi
2. Trích dẫn quy tắc đạo đức hoặc điều luật liên quan: ghi rõ TÊN VĂN BẢN, ĐIỀU, KHOẢN
3. Áp dụng quy tắc vào tình huống cụ thể
4. Đưa ra kết luận

***ĐỊNH DẠNG OUTPUT***
- Viết toàn bộ phân tích bằng tiếng Việt
- Cuối cùng, ghi đáp án trong thẻ: <answer>A/B/C/D</answer>
- CHỈ được ghi MỘT chữ cái bên trong thẻ answer
- KHÔNG được giải thích ngoài quy trình trên
"""
