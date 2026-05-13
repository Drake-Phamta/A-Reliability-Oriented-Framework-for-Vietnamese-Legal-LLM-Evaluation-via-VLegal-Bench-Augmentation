EXAMPLE = """
Bạn sẽ được cung cấp một câu hỏi bao gồm 2 chủ thể pháp lý và một đoạn văn chứa điều/khoản trong một hợp đồng liên quan đến hai chủ thể đó.
Format của câu hỏi sẽ như sau:
BÊN A: <Tên bên A>
BÊN B: <Tên bên B>
ĐIỀU/KHOẢN: <Nội dung điều/khoản trong hợp đồng>
Dựa trên điều/khoản được cung cấp, bên nào có lợi hơn trong hợp đồng này?
A. Có lợi cho bên A B. Có lợi cho bên B C. Công bằng
Nhiệm vụ của bạn là đọc và xác định xem bên nào là bên có lợi hơn trong hợp đồng dựa trên điều/khoản được cung cấp.
Chỉ trả lời bằng một chữ cái duy nhất: A, B, hoặc C.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.
Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.
"""

EXAMPLE_FEWSHOT = """
Bạn sẽ được cung cấp một câu hỏi bao gồm 2 chủ thể pháp lý và một đoạn văn chứa điều/khoản trong một hợp đồng liên quan đến hai chủ thể đó.
Format của câu hỏi sẽ như sau:
BÊN A: <Tên bên A>
BÊN B: <Tên bên B>
ĐIỀU/KHOẢN: <Nội dung điều/khoản trong hợp đồng>
Dựa trên điều/khoản được cung cấp, bên nào có lợi hơn trong hợp đồng này?
A. Có lợi cho bên A B. Có lợi cho bên B C. Công bằng
Nhiệm vụ của bạn là đọc và xác định xem bên nào là bên có lợi hơn trong hợp đồng dựa trên điều/khoản được cung cấp.
Chỉ trả lời bằng một chữ cái duy nhất: A, B, hoặc C.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.
Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***.

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Đánh giá xem điều khoản hợp đồng này có công bằng cho hai bên không. Chọn đáp án đúng nhất trong các lựa chọn A, B, C, D được cung cấp, chỉ chọn đáp án và không giải thích gì thêm."
Câu hỏi: Trong hợp đồng giữa VĂN PHÒNG THỬA PHÁT LẠI và BÊN YÊU CẦU THỰC HIỆN TỐNG ĐẠT, điều khoản về thủ tục thực hiện việc tống đạt quy định như thế nào và nó có lợi cho bên nào hơn? Bên A phải thực hiện tống đạt các giấy tờ trong vòng 24 giờ đối với yêu cầu từ Cơ quan thi hành án dân sự và 48 giờ đối với yêu cầu từ Tòa án hoặc Viện Kiểm sát nhân dân. Trong trường hợp không thể tống đạt trực tiếp, Bên A phải niêm yết công khai giấy tờ tại các địa điểm liên quan và báo cáo kết quả định kỳ 1 tuần/lần cho Bên B, trong khi chi phí phát sinh sẽ do Bên B thanh toán.
Đáp án: 'A': 'Có lợi cho bên A vì điều khoản này cho phép Bên A lựa chọn các biện pháp tống đạt linh hoạt mà không bị ràng buộc bởi thời gian.', 'B': 'Công bằng vì điều khoản này yêu cầu cả hai bên hợp tác chặt chẽ và chia sẻ trách nhiệm trong quá trình thực hiện tống đạt.', 'C': 'Có lợi cho bên A vì điều khoản này cho phép bên A có quyền từ chối các trường hợp không thể tống đạt trực tiếp mà không chịu trách nhiệm.', 'D': 'Có lợi cho bên B vì điều khoản này quy định rõ thời hạn và thủ tục tống đạt, giúp bên B kiểm soát và đảm bảo quá trình tống đạt được thực hiện đúng theo thỏa thuận.'
Đáp án đúng: "D"
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc điều khoản hợp đồng và đánh giá tính công bằng, rồi chọn đáp án đúng (A, B hoặc C). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích điều khoản hợp đồng và đánh giá lợi ích giữa các bên.
- KHÔNG được để trống phần suy luận.
- KHÔNG được viết nội dung suy luận nằm bên ngoài 2 thẻ.

2. OUTPUT cho ANSWER
- Chỉ đưa ra 1 ký tự duy nhất từ tập {A, B, C} và viết vào giữa 2 thẻ <output> và </output>
- KHÔNG được kèm theo bất kỳ từ ngữ, ký tự hoặc giải thích nào khác ở phần này.
- KHÔNG được viết câu kiểu "Đáp án là A".
- KHÔNG được viết lại câu hỏi.

**YÊU CẦU TUÂN THỦ NGHIÊM NGẶT**:
- Nội dung thinking và câu trả lời phải được viết trong các thẻ tương ứng, không được viết bên ngoài.
- Nội dung answer phải nằm trong 2 thẻ <output> và </output>.
- Nội dung của thinking và answer không được để trống.
- Không được đổi tên thẻ hoặc thêm thẻ mới.
- Không được dùng ký tự khác ngoài A/B/C bên trong 2 thẻ <output> và </output>.
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
Nhiệm vụ của bạn là phân tích điều khoản hợp đồng và đánh giá tính công bằng. Bạn PHẢI tuân thủ quy trình suy luận dưới đây.

***QUY TRÌNH SUY LUẬN (bắt buộc)***
1. Xác định nội dung điều khoản hợp đồng được cung cấp
2. Phân tích quyền và nghĩa vụ của mỗi bên
3. Đánh giá tính cân bằng lợi ích giữa các bên
4. Đưa ra kết luận: Có lợi cho bên A, bên B, hay công bằng

***ĐỊNH DẠNG OUTPUT***
- Viết toàn bộ phân tích bằng tiếng Việt
- Cuối cùng, ghi đáp án trong thẻ: <answer>A</answer>, <answer>B</answer>, hoặc <answer>C</answer>
- CHỈ được ghi MỘT chữ cái bên trong thẻ answer
- KHÔNG được giải thích ngoài quy trình trên
"""
