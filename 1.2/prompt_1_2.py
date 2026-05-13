PROMPT_CREATE_DATASET = """
Bạn là một hệ thống tạo dữ liệu huấn luyện cho mô hình phân loại câu hỏi theo lĩnh vực.

Cho trước một dictionary JSON có dạng: 
- Key: Tên lĩnh vực
- Value: Nội dung một câu hỏi thuộc lĩnh vực đó

Yêu cầu:
Từ câu hỏi đã cho, bạn hãy tạo ra câu hỏi mới, có tình huống thực tế giả định liên quan mật thiết đến nội dung câu hỏi đã cho, sao cho câu hỏi mới vẫn thuộc cùng lĩnh vực với câu hỏi ban đầu.
Hãy đảm bảo rằng câu hỏi mới:
1. Vẫn giữ nguyên lĩnh vực của câu hỏi gốc.
2. Có tình huống thực tế giả định mang tính thực tiễn cao.
3. Độ dài câu hỏi mới ít nhất 50 từ.
4. Làm nhiễu câu hỏi bằng cách thay đổi cấu trúc câu, sử dụng từ đồng nghĩa, và thêm các chi tiết phụ trợ liên quan đến tình huống thực tế.
5. Hạn chế dùng các từ liên quan trực tiếp đến lĩnh vực trong câu hỏi mới để tránh lộ đáp án.
6: Đảm bảo văn phong chuyên nghiệp và phù hợp với ngữ cảnh pháp lý.

Đầu ra của bạn chỉ là câu hỏi mới, KHÔNG thêm bất kỳ chú thích hay giải thích nào khác.

*Ví dụ đầu ra*: 
Input: ```json
{
    "tien-te-ngan-hang": "Dịch vụ cho thuê két an toàn của tổ chức tín dụng là gì?"
}
```
Output: "Ông A muốn bảo vệ tài sản quý giá của mình tại nhà riêng. Ông ta đang cân nhắc việc sử dụng dịch vụ cho thuê két an toàn từ một tổ chức tín dụng uy tín. Vậy, ông A cần hiểu rõ những quy định và lợi ích liên quan đến dịch vụ cho thuê két an toàn này là gì?"
"""

EXAMPLE = """
Nhiệm vụ của bạn là đọc câu hỏi sau và cho biết nó thuộc lĩnh vực nào, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chọn đáp án chứa đúng lĩnh vực của câu hỏi. Phải sử dụng tiếng Việt.
Chỉ đưa ra kết quả, không cần giải thích. Không lặp lại câu hỏi.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.
KHÔNG lặp lại câu hỏi.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là đọc câu hỏi sau và cho biết nó thuộc lĩnh vực nào, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chọn đáp án chứa đúng lĩnh vực của câu hỏi. 
Chỉ đưa ra kết quả, không cần giải thích.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Đọc câu hỏi sau và cho biết nó thuộc lĩnh vực nào, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Câu hỏi: Anh B thường xuyên tổ chức hát karaoke di động và sử dụng loa kẹo kéo để phục vụ cho hoạt động giải trí cá nhân tại nhà. Gần đây, nhà anh nhận được phản ánh từ những người xung quanh vì âm lượng quá lớn gây ảnh hưởng đến sinh hoạt hàng ngày. Trong trường hợp này, nếu anh B tiếp tục duy trì hoạt động như vậy vào năm 2025, thì những quy định hiện hành có thể dẫn đến hình thức xử phạt nào không?
Đáp án: A. Dịch vụ pháp lý B. Bộ máy hành chính C. Chứng khoán D. Tiền tệ ngân hàng E. Vi phạm hành chính F. Lĩnh vực khác
Đáp án đúng: E
"""

EXAMPLE_EN = """
Instruction: “Read the following question and determine which field it belongs to. Only choose the answer, and do not provide any explanation.”
Question: “What are the guidelines in Official Dispatch No. 8935/BNV-CTTN&BĐG 2025 regarding the Action Month for Gender Equality and Prevention of Gender-Based Violence in 2025?”
Answer: A. Business B. Securities C. Civil Rights D. Legal Services
Ground truth: C
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là đọc câu hỏi và xác định lĩnh vực pháp lý mà câu hỏi thuộc về, rồi chọn đáp án đúng (A, B, C, D, E hoặc F). Để trả lời được câu hỏi, bạn phải suy nghĩ và đưa ra lập luận cho câu trả lời.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích câu hỏi và xác định lĩnh vực.
- KHÔNG được để trống phần suy luận.
- KHÔNG được viết nội dung suy luận nằm bên ngoài 2 thẻ.

2. OUTPUT cho ANSWER
- Chỉ đưa ra 1 ký tự duy nhất từ tập {A, B, C, D, E, F} và viết vào giữa 2 thẻ <output> và </output>
- KHÔNG được kèm theo bất kỳ từ ngữ, ký tự hoặc giải thích nào khác ở phần này.
- KHÔNG được viết câu kiểu "Đáp án là A".
- KHÔNG được viết lại câu hỏi.

**YÊU CẦU TUÂN THỦ NGHIÊM NGẶT**:
- Nội dung thinking và câu trả lời phải được viết trong các thẻ tương ứng, không được viết bên ngoài.
- Nội dung answer phải nằm trong 2 thẻ <output> và </output>.
- Nội dung của thinking và answer không được để trống.
- Không được đổi tên thẻ hoặc thêm thẻ mới.
- Không được dùng ký tự khác ngoài A/B/C/D/E/F bên trong 2 thẻ <output> và </output>.
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
