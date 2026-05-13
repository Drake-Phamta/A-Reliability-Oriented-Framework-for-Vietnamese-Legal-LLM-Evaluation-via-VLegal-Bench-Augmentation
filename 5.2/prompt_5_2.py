
EXAMPLE = """
Nhiệm vụ của bạn là đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

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
Instruction: Đọc câu hỏi trắc nghiệm sau và chọn một hoặc nhiều đáp án đúng, chỉ cần chọn đáp án mà không cần giải thích gì thêm
Câu hỏi: "Trong tuần đầu tiên của năm học mới, T là lớp trưởng được cô chủ nhiệm giao nhiệm vụ thu thập thông tin cá nhân của các bạn trong lớp để lập sổ liên lạc điện tử. T lập một mẫu khảo sát online yêu cầu các thông tin cơ bản như Họ tên, Ngày sinh, Địa chỉ, Số điện thoại phụ huynh và Địa chỉ email cá nhân (cho việc nhận tài liệu học tập). T giải thích rõ ràng đây là yêu cầu của giáo viên chủ nhiệm và mục đích là để phục vụ công tác quản lý và liên lạc trong học tập. Tuy nhiên, khi gửi link khảo sát vào nhóm chat của lớp, một số bạn tỏ ra ngần ngại và băn khoăn về tính bảo mật của dữ liệu. Một thành viên trong lớp hỏi T: \"Lỡ thông tin cá nhân của tụi mình bị lộ ra ngoài thì sao?\". Hành vi nào là phản ánh đúng tình huống trên?"
Đáp án: "A: Lớp trưởng T được thu thập và sử dụng thông tin cá nhân của các bạn để phục vụ mục đích học tập nếu các bạn đồng ý cung cấp thông tin\nB: Nhà trường và giáo viên chủ nhiệm cần có trách nhiệm bảo vệ dữ liệu thông tin đã thu thập \nC: Người thu thập trực tiếp T mới là người chịu trách nhiệm chính và phải bồi thường nếu thông tin bị lộ\nD: Trách nhiệm bảo mật thuộc về các thành viên đã điền thông tin vì họ đã tự nguyện cung cấp, do đó họ phải chấp nhận rủi ro thông tin bị rò rỉ."
Đáp án đúng: A
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc câu hỏi trắc nghiệm về bảo vệ dữ liệu cá nhân và quyền riêng tư, rồi chọn đáp án đúng (A, B, C hoặc D). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và <think>. Đây là nơi bạn phân tích câu hỏi và đánh giá các phương án.
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
