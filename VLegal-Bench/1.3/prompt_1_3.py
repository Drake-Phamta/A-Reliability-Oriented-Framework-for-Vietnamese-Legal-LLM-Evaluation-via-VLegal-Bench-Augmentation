PROMPT_PARAPHRASE = """
Bạn là một chuyên gia tạo câu hỏi pháp lý.
Bạn sẽ được cung cấp dữ liệu gồm 1 câu hỏi, 4 câu trả lời trắc nghiệm (A, B, C, D), và đáp án đúng.
Nhiệm vụ của bạn là viết lại câu hỏi và các câu trả lời trắc nghiệm sao cho khác biệt về mặt ngôn ngữ so với dữ liệu gốc, nhưng vẫn giữ nguyên ý nghĩa và đảm bảo rằng đáp án đúng vẫn là đáp án đúng trong câu hỏi mới.
Hãy chắc chắn rằng câu hỏi và các câu trả lời trắc nghiệm mới không giống với câu hỏi và các câu trả lời trắc nghiệm gốc về mặt từ ngữ và cấu trúc câu.
Hãy đảm bảo câu trả lời đúng phải khó phân biệt với các câu trả lời sai để tăng tính thử thách.
Chỉ trả lời bằng định dạng JSON như sau, không thêm bất kỳ lời giải thích nào:
{
  "Paraphrased Question": "<Câu hỏi được viết lại>",
  "Paraphrased Answers": {
    "A": "<Câu trả lời A được viết lại>",
    "B": "<Câu trả lời B được viết lại>",
    "C": "<Câu trả lời C được viết lại>",
    "D": "<Câu trả lời D được viết lại>"
  },
  "Ground Truth": "<Đáp án đúng (A, B, C, hoặc D)>"
}
LƯU Ý QUAN TRỌNG: Phản hồi của bạn PHẢI LÀ MỘT ĐỐI TƯỢNG JSON HỢP LỆ THEO CẤU TRÚC Ở TRÊN. KHÔNG ĐƯỢC THÊM BẤT KỲ LỜI GIẢI THÍCH NÀO KHÁC. KHÔNG thay ĐỔI CẤU TRÚC JSON.
"""
EXAMPLE = """
Nhiệm vụ của bạn là đọc câu hỏi sau và xác định khái niệm được hỏi trong câu hỏi là gì, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token </think> hoặc ***Giải thích***. Không lặp lại câu hỏi

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác. Không lặp lại câu hỏi

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là đọc câu hỏi sau và xác định khái niệm được hỏi trong câu hỏi là gì, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Chỉ đưa ra kết quả, không cần giải thích. Không thêm các token </think> hoặc ***Giải thích***.

**QUAN TRỌNG**: Bạn CHỈ ĐƯỢC TRÀ LỜI bằng MỘT CHỮ CÁI duy nhất: A, B, C, hoặc D.
KHÔNG được giải thích, KHÔNG được thêm bất kỳ text nào khác.

Ví dụ đúng: A
Ví dụ sai: Đáp án là A
Ví dụ sai: A. Đây là đáp án đúng vì...

Chỉ trả lời: A hoặc B hoặc C hoặc D

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Đọc câu hỏi sau và chọn đáp án đúng, chỉ cần chọn đáp án và không cần giải thích gì thêm.
Câu hỏi: Theo quy định, Giao dịch dân sự được hiểu là gì?
Đáp án: {"A": "A. Giao dịch dân sự là giao dịch pháp lý đơn phương làm phát sinh, thay đổi hoặc chấm dứt quyền, nghĩa vụ dân sự.", "B": "B. Giao dịch dân sự là hợp đồng hoặc hành vi pháp lý đơn phương làm phát sinh, thay đổi hoặc chấm dứt quyền, nghĩa vụ dân sự.", "C": "C. Giao dịch dân sự là hợp đồng hoặc hành vi pháp lý đơn phương làm phát sinh, thay đổi quyền, nghĩa vụ dân sự.", "D": "D. Giao dịch dân sự là hợp đồng hoặc hành vi pháp lý làm phát sinh, thay đổi hoặc chấm dứt quyền, nghĩa vụ dân sự."}
Đáp án đúng: B
"""

EXAMPLE_REASONING = “””
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
“””

EXAMPLE_EN = “””
• Instruction: “Read the following question and choose the correct answer. Only select the answer; no explanation is needed.”
• Question: “According to regulations, what is the definition of a legal precedent (án lệ)?”
• Answers:
A. A legal precedent refers to the reasoning and judgments in a court’s legally effective judgments or decisions on a specific case, which are selected by the Council of Judges of the Supreme People’s Court and published by the Chief Justice of the Supreme People’s Court as precedents for other courts to study and apply in adjudication.
B. A legal precedent refers to the reasoning and judgments in a court’s legally effective judgments or decisions, which are selected by the Supreme People’s Procuracy and published by the Procurator General for judicial agencies to apply in adjudication.
C. A legal precedent refers to the reasoning and judgments in a court’s legally effective judgments or decisions on a specific case, which are selected by the National Assembly and published by the Chairperson of the National Assembly for courts to refer to during adjudication.
• Ground truth: A
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
