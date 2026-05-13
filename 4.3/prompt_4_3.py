PROMPT_CREATE_DATASET = """
Nhiệm vụ:
Dựa trên một bài báo do tôi cung cấp, hãy thực hiện các yêu cầu sau:

1. Tạo một câu hỏi mở liên quan trực tiếp đến nội dung bài báo và phản ánh một vấn đề pháp lý, xã hội hoặc chính sách được đề cập trong bài.
2. Soạn một phần Mô tả tình huống (Description) tóm lược bối cảnh vụ việc, sự kiện hoặc vấn đề trong bài, với văn phong khách quan, súc tích và chính xác.
3. Viết một câu trả lời mẫu (Answer) cho câu hỏi đã tạo, bảo đảm:
   - Văn phong trang trọng, khách quan, rành mạch và có tính chuyên môn cao.
   - Sử dụng ngôn ngữ pháp lý chuẩn hóa.
   - Trình bày trong một đoạn văn duy nhất, không xuống dòng, dài không quá 400 từ.
   - Nội dung nhất quán với lập luận và tinh thần của bài báo.
   - Dựa hoàn toàn trên tri thức trong bài báo, không suy diễn ngoài văn bản.

4. Tách riêng tất cả các trích dẫn từ bài báo (grounding knowledge) vào trường "Grounding", trình bày dưới dạng một danh sách các đoạn trích nguyên văn từ bài báo mà bạn đã sử dụng để lập luận trong phần Answer.

Yêu cầu bổ sung:
- Mọi trích dẫn trong "Grounding" phải khớp hoàn toàn với bài báo.
- Trong phần Answer không được trích dẫn nguyên văn; chỉ được diễn giải dựa trên các trích dẫn nằm trong trường "Grounding".

Đầu ra cần trả về theo cấu trúc JSON sau:
```json 
{
  "Question": "...",
  "Description": "...",
  "Answer": "...",
  "Grounding": [
    "...",
    "..."
  ]
}
```
"""

EXAMPLE = """
Nhiệm vụ của bạn là trả lời câu hỏi pháp luật sau. Phải sử dụng tiếng Việt, không sử dụng ngôn ngữ nào khác. Câu trả lời của bạn không được dài quá 400 từ, trình bày trong một đoạn văn duy nhất,
không xuống dòng. Văn phong trang trọng, khách quan, rành mạch và có tính chuyên môn cao. Sử dụng ngôn ngữ pháp lý chuẩn hóa.
"""

EXAMPLE_FEWSHOT = """
Nhiệm vụ của bạn là trả lời câu hỏi pháp luật sau. Câu trả lời của bạn không được dài quá 400 từ, trình bày trong một đoạn văn duy nhất,
không xuống dòng. Văn phong trang trọng, khách quan, rành mạch và có tính chuyên môn cao. Sử dụng ngôn ngữ pháp lý chuẩn hóa.

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: Nhiệm vụ của bạn là trả lời câu hỏi pháp luật sau. Câu trả lời của bạn không được dài quá 400 từ, trình bày trong một đoạn văn duy nhất,không xuống dòng. Văn phong trang trọng, khách quan, rành mạch và có tính chuyên môn cao. Sử dụng ngôn ngữ pháp lý chuẩn hóa.
Câu hỏi: Những thách thức mà chính phủ Việt Nam đang đối mặt trong công tác phòng, chống tội phạm trên không gian mạng là gì và các biện pháp nào đã được thực hiện để giải quyết vấn đề này?
Đáp án đúng: Chính phủ Việt Nam đang đối mặt với nhiều thách thức trong công tác phòng, chống tội phạm trên không gian mạng, bao gồm sự gia tăng liên tục của các hành vi vi phạm như lừa đảo qua mạng, tội phạm tài chính trực tuyến, và hoạt động đánh bạc qua mạng. Đặc biệt, các phương thức và thủ đoạn phạm tội thường xuyên thay đổi và ngày càng tinh vi, gây khó khăn trong việc phát hiện và đấu tranh hiệu quả. Để đối phó, Chính phủ đã chỉ đạo Bộ Công an và các cơ quan liên quan tăng cường quản lý nhà nước trong các lĩnh vực viễn thông, công nghệ thông tin và thương mại điện tử. Đồng thời, việc ban hành các nghị định và chính sách mới nhằm bảo vệ dữ liệu cá nhân và tăng cường an ninh mạng cũng đóng vai trò quan trọng. Bên cạnh đó, công tác rà soát, khắc phục các lỗ hổng bảo mật được thực hiện định kỳ để giảm thiểu nguy cơ mất an ninh, an toàn thông tin. Chính phủ cũng chú trọng đến việc đẩy mạnh công tác tuyên truyền và nâng cao ý thức bảo vệ an ninh mạng trong cộng đồng, nhằm giảm thiểu sự phát sinh của các loại tội phạm này.
"""

EXAMPLE_REASONING = """
Nhiệm vụ của bạn là trả lời câu hỏi pháp luật bằng cách đưa ra ý kiến pháp lý khách quan. Bạn phải suy nghĩ và phân tích trước khi viết.

***ĐỊNH DẠNG CỦA OUTPUT***
1. OUTPUT cho THINKING
- Hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích câu hỏi, xác định cơ sở pháp lý và lập luận.
- KHÔNG được để trống phần suy luận.
- KHÔNG được viết nội dung suy luận nằm bên ngoài 2 thẻ.

2. OUTPUT cho ANSWER
- Viết câu trả lời bằng tiếng Việt, tối đa 400 từ, trong một đoạn văn duy nhất không xuống dòng.
- Văn phong trang trọng, khách quan, rành mạch và có tính chuyên môn cao.
- Sử dụng ngôn ngữ pháp lý chuẩn hóa.
- Viết vào giữa 2 thẻ <output> và </output>.

**YÊU CẦU TUÂN THỦ NGHIÊM NGẶT**:
- Nội dung thinking và answer phải được viết trong các thẻ tương ứng.
- Không được đổi tên thẻ hoặc thêm thẻ mới.
- Định dạng phải chính xác tuyệt đối.

***Ví dụ đúng***:
<think>Phân tích câu hỏi: ... Cơ sở pháp lý: ... Lập luận: ... Kết luận: ...</think>
<output>Ý kiến pháp lý khách quan...</output>
"""

EXAMPLE_RELIABILITY = """
Nhiệm vụ của bạn là trả lời câu hỏi pháp lý. Bạn PHẢI tuân thủ quy trình suy luận dưới đây.

***QUY TRÌNH SUY LUẬN (bắt buộc)***
1. Xác định vấn đề pháp lý chính
2. Trích dẫn điều luật liên quan: ghi rõ TÊN VĂN BẢN, ĐIỀU, KHOẢN
3. Áp dụng pháp luật vào tình huống
4. Đưa ra câu trả lời hoàn chỉnh

***ĐỊNH DẠNG OUTPUT***
- Viết toàn bộ phân tích bằng tiếng Việt
- Ghi câu trả lời cuối cùng trong thẻ: <answer>nội dung trả lời</answer>
- Câu trả lời phải đầy đủ, chuyên nghiệp, tối đa 400 từ
- KHÔNG được thêm text ngoài quy trình trên

Ví dụ:
Vấn đề pháp lý: ...
Cơ sở pháp lý: Theo Điều X Luật Y...
Áp dụng: ...
<answer>Câu trả lời pháp lý chi tiết...</answer>
"""
