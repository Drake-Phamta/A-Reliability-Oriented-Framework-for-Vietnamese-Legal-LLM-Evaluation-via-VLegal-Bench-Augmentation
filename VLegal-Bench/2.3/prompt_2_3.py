PROMPT_CREATE_DATASET = """
Bạn là một chuyên gia pháp lý với kiến thức sâu rộng về luật pháp Việt Nam.
Nhiệm vụ của bạn là bóc tách – trích xuất – chuẩn hóa các điều khoản (Điều, Khoản, Mục, Chương) và mối quan hệ pháp lý giữa chúng từ dữ liệu đầu vào.
Hãy đảm bảo rằng bạn chỉ trích xuất **các điều khoản có liên quan** (bao gồm: Điều, Khoản, Mục, Chương) 
và **bỏ qua mọi thông tin không cần thiết**.

📌 1. CẤU TRÚC DỮ LIỆU ĐẦU VÀO
1.1. doc_info
Chứa thông tin về văn bản pháp luật:
- so_hieu
- trich_yeu
- ngay_ban_hanh
- ngay_co_hieu_luc
- tinh_trang_hieu_luc
- co_quan_ban_hanh
- loai_van_ban
1.2. context
Chứa thông tin về điều khoản
- com_path – đường dẫn điều khoản (VD: "Khoản 2 / Điều 6")
- com_type – loại điều khoản (khoản, điều, mục…)
- com_title – nội dung chính chứa từ khóa quan hệ
- com_titles_content – danh sách đoạn văn có chứa điều khoản & quan hệ
- com_titles_name – mapping các điều khoản liên quan
- com_titles_content_embedding – danh sách đoạn văn có chứa điều khoản & quan hệ, được xử lý trước khi đưa vào embedding
- com_content_embedding - nội dung chứa thông tin đầy đủ nhất về quan hệ và các điều khoản

2. HƯỚNG DẪN TRÍCH XUẤT TRIPLET

Bạn phải trích xuất danh sách các bộ ba (triplet) theo dạng:
👉 (thực thể 1, mối quan hệ, thực thể 2)
Trong đó:
2.1. THỰC THỂ 1 — Điều khoản đang được quy định trong văn bản đầu vào
Cách tạo tên thực thể 1:
- Dùng com_path để lấy tên điều khoản:
Ví dụ: "Khoản 2 / Điều 6"
- Ghép thêm tên văn bản pháp luật từ doc_info:
Ví dụ: "Luật 28/2018/QH14"
➡️ Kết quả thực thể 1:
"Khoản 2 / Điều 6 / Luật 28/2018/QH14"
2.2. MỐI QUAN HỆ — Từ khóa pháp lý trong nội dung
Tìm trong các trường sau: com_title, com_titles_content, com_content_embedding các từ khóa hợp lệ:
- sửa đổi bổ sung
- sửa đổi
- bổ sung
- bãi bỏ
- thay thế
- hướng dẫn thực hiện 
- quy định, quy định lại
- điều chỉnh
- thi hành
➡️ Lấy đúng từ khóa xuất hiện trong văn bản.

2.3. THỰC THỂ 2 — Điều khoản được đề cập hoặc bị tác động
Lấy từ các trường:
- com_titles_name (ví dụ "dieu": "Điều 9")
- com_content_embedding (thường đi sau các từ thuộc 2.2. MỐI QUAN HỆ như đã đề cập ở trên)
Sau đó chuẩn hóa tên đầy đủ của văn bản bị tác động bằng cách lấy từ: trich_yeu trong doc_info (nếu có đề cập)
➡️ Ví dụ:
"Điều 9" hoặc "Điều 9 / Luật Điện lực" nếu có nhắc đến văn bản .
Hãy format phản hồi của bạn dưới dạng **một câu hỏi tự luận** với cấu trúc JSON như sau:
  • **Instruction**: “Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet (thực thể 1, mối quan hệ, thực thể 2)”  
  • **Document**: Tên điều khoản + [Một DANH SÁCH đoạn văn bản có chứa các điều khoản và mối quan hệ giữa chúng.]  
  • **Answer**: [Danh sách các triplet dưới dạng (thực thể 1, mối quan hệ, thực thể 2).]

Ví dụ 1:
Input: 
    {
        "doc_info": {
            "so_hieu": "28/2018/QH14",
            "trich_yeu": "Sửa đổi bổ sung một số điều của 11 Luật có liên quan đến quy hoạch năm 2018",
            "ngay_ban_hanh": "2018-06-15T00:00:00Z",
            "ngay_co_hieu_luc": "2019-01-01T00:00:00Z",
            "co_quan_ban_hanh": "Quốc hội",
            "loai_van_ban": "Luật",
            "tinh_trang_hieu_luc": "Còn hiệu lực"
        },
        "context": {
            "com_key": "khoan_2_dieu_6",
            "com_path": "Khoản 2 / Điều 6",
            "com_type": "khoan",
            "com_title": "2. Sửa đổi, bổ sung Điều 9 như sau:\n“Điều 9. Lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực\n1. Bộ Công thương tổ chức lập quy hoạch phát triển điện lực trình Thủ tướng Chính phủ phê duyệt theo quy định của pháp luật về quy hoạch.\n2. Ủy ban nhân dân cấp tỉnh tổ chức lập nội dung phương án phát triển mạng lưới cấp điện trong quy hoạch tỉnh.\n3. Việc lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực theo quy định của pháp luật về quy hoạch.”.",
            "com_title_embedding": "Sửa đổi, bổ sung Điều 9 như sau: “Điều 9. Lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực Bộ Công thương tổ chức lập quy hoạch phát triển điện lực trình Thủ tướng Chính phủ phê duyệt theo quy định của pháp luật về quy hoạch. Ủy ban nhân dân cấp tỉnh tổ chức lập nội dung phương án phát triển mạng lưới cấp điện trong quy hoạch tỉnh. Việc lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực theo quy định của pháp luật về quy hoạch.”.",
            "com_name": "2.",
            "com_titles_content": [
                "2. Sửa đổi, bổ sung Điều 9 như sau:\n“Điều 9. Lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực\n1. Bộ Công thương tổ chức lập quy hoạch phát triển điện lực trình Thủ tướng Chính phủ phê duyệt theo quy định của pháp luật về quy hoạch.\n2. Ủy ban nhân dân cấp tỉnh tổ chức lập nội dung phương án phát triển mạng lưới cấp điện trong quy hoạch tỉnh.\n3. Việc lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực theo quy định của pháp luật về quy hoạch.”.",
                "Điều 6. Sửa đổi, bổ sung một số điều của Luật Điện lực"
            ],
            "com_titles_content_embedding": [
                "Sửa đổi, bổ sung Điều 9 như sau: “Điều 9. Lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực Bộ Công thương tổ chức lập quy hoạch phát triển điện lực trình Thủ tướng Chính phủ phê duyệt theo quy định của pháp luật về quy hoạch. Ủy ban nhân dân cấp tỉnh tổ chức lập nội dung phương án phát triển mạng lưới cấp điện trong quy hoạch tỉnh. Việc lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực theo quy định của pháp luật về quy hoạch.”.",
                "Sửa đổi, bổ sung một số điều của Luật Điện lực"
            ],
            "com_titles_name": {
                "khoan": "2.",
                "dieu": "Điều 6."
            },
            "com_content": "",
            "com_content_embedding": ""
        }
    }

Output:
```json
{
    "Instruction": "Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet (thực thể 1, mối quan hệ, thực thể 2).",
    "Document": Khoản 2 / Điều 6 / Luật 28/2018/QH14, trích yếu "Sửa đổi bổ sung một số điều của 11 Luật có liên quan đến quy hoạch năm 2018" có danh sách ngữ cảnh sau  [
                "2. Sửa đổi, bổ sung Điều 9 như sau:\n“Điều 9. Lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực\n1. Bộ Công thương tổ chức lập quy hoạch phát triển điện lực trình Thủ tướng Chính phủ phê duyệt theo quy định của pháp luật về quy hoạch.\n2. Ủy ban nhân dân cấp tỉnh tổ chức lập nội dung phương án phát triển mạng lưới cấp điện trong quy hoạch tỉnh.\n3. Việc lập, thẩm định, phê duyệt, công bố, tổ chức thực hiện và điều chỉnh quy hoạch phát triển điện lực theo quy định của pháp luật về quy hoạch.”.",
                "Điều 6. Sửa đổi, bổ sung một số điều của Luật Điện lực"
            ],
    "Answer": [
       ("Khoản 2 / Điều 6 / Luật 28/2018/QH14", "sửa đổi bổ sung", "Điều 9")
    ]
}

Ví dụ 2 (khi có com_content_embedding):
Input: 
    {
        "doc_info": {
            "so_hieu": "07/2019/TT-BTC",
            "trich_yeu": "SỬA ĐỔI, BỔ SUNG MỘT SỐ ĐIỀU CỦA THÔNG TƯ SỐ 72/2015/TT-BTC NGÀY 12 THÁNG 5 NĂM 2015 CỦA BỘ TRƯỞNG BỘ TÀI CHÍNH QUY ĐỊNH ÁP DỤNG CHẾ ĐỘ ƯU TIÊN TRONG VIỆC THỰC HIỆN THỦ TỤC HẢI QUAN, KIỂM TRA, GIÁM SÁT HẢI QUAN ĐỐI VỚI HÀNG HÓA XUẤT KHẨU, NHẬP KHẨU CỦA DOANH NGHIỆP",
            "ngay_ban_hanh": "2019-01-28T00:00:00Z",
            "ngay_co_hieu_luc": "2019-03-28T00:00:00Z",
            "co_quan_ban_hanh": "Bộ Tài chính",
            "loai_van_ban": "Thông tư",
            "tinh_trang_hieu_luc": "Còn hiệu lực"
        },
        "context": {
            "com_key": "dieu_1",
            "com_path": "Điều 1",
            "com_type": "dieu",
            "com_title": "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 72/2015/TT-BTC ngày 12 tháng 5 năm 2015 của Bộ trưởng Bộ Tài chính quy định áp dụng chế độ ưu tiên trong việc thực hiện thủ tục hải quan, kiểm tra, giám sát hải quan đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp:",
            "com_title_embedding": "Sửa đổi, bổ sung một số điều của Thông tư số 72/2015/TT-BTC ngày 12 tháng 5 năm 2015 của Bộ trưởng Bộ Tài chính quy định áp dụng chế độ ưu tiên trong việc thực hiện thủ tục hải quan, kiểm tra, giám sát hải quan đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp:",
            "com_name": "Điều 1.",
            "com_titles_content": [
                "Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 72/2015/TT-BTC ngày 12 tháng 5 năm 2015 của Bộ trưởng Bộ Tài chính quy định áp dụng chế độ ưu tiên trong việc thực hiện thủ tục hải quan, kiểm tra, giám sát hải quan đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp:"
            ],
            "com_titles_content_embedding": [
                "Sửa đổi, bổ sung một số điều của Thông tư số 72/2015/TT-BTC ngày 12 tháng 5 năm 2015 của Bộ trưởng Bộ Tài chính quy định áp dụng chế độ ưu tiên trong việc thực hiện thủ tục hải quan, kiểm tra, giám sát hải quan đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp:"
            ],
            "com_titles_name": {
                "dieu": "Điều 1."
            },
            "com_content": "1. Sửa đổi tiêu đề của Điều 6 như sau:\n“Điều 6. Thực hiện thủ tục hải quan bằng tờ khai chưa hoàn chỉnh”.\n2. Sửa đổi, bổ sung khoản 3 Điều 7 như sau:\n“3. Được cơ quan hải quan và các cơ quan kinh doanh cảng, kho bãi ưu tiên làm thủ tục giao nhận hàng hóa trước, ưu tiên kiểm tra giám sát trước”.\n3. Sửa đổi, bổ sung Điều 8 như sau:\n“Điều 8. Kiểm tra chuyên ngành\n1. Doanh nghiệp được đưa hàng hóa nhập khẩu về kho của doanh nghiệp để bảo quản trong khi chờ kết quả kiểm tra chuyên ngành, trừ trường hợp pháp luật kiểm tra chuyên ngành quy định hàng hóa phải kiểm tra tại cửa khẩu.\n2. Trường hợp cần lấy mẫu để kiểm tra chuyên ngành thì được ưu tiên lấy mẫu hàng hóa trước”.\n4. Sửa đổi, bổ sung Điều 9 như sau:\n“Điều 9. Thủ tục về thuế\n1. Được hoàn thuế trước, kiểm tra sau. Hồ sơ hoàn thuế thực hiện theo Nghị định số 134/2016/NĐ-CP ngày 01/9/2016 của Chính phủ; thủ tục nộp, tiếp nhận, xử lý hồ sơ hoàn thuế thực hiện theo quy định tại Nghị định số 134/2016/NĐ-CP ngày 01/9/2016 của Chính phủ, Thông tư số 38/2015/TT-BTC ngày 25/3/2015 và Thông tư số 39/2018/TT-BTC ngày 20/4/2018 của Bộ trưởng Bộ Tài chính. Căn cứ trên kết quả tự tính, tự khai của doanh nghiệp, cơ quan hải quan kiểm tra tính phù hợp về hồ sơ. Thời gian ra quyết định hoàn thuế không quá 01 (một) ngày làm việc kể từ ngày nhận được hồ sơ hợp lệ của doanh nghiệp.\n2. Thời hạn nộp thuế đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp ưu tiên thực hiện theo quy định tại khoản 2 Điều 9 Luật Thuế xuất khẩu, thuế nhập khẩu số 107/2016/QH13 ngày 06/4/2016.\n3. Được ưu tiên khi thực hiện các thủ tục về thuế đối với hàng hóa xuất khẩu, nhập khẩu theo quy định của pháp luật về thuế.”.\n5. Sửa đổi địa điểm nộp hồ sơ tại khoản 1 Điều 18 như sau:\n“1. Doanh nghiệp đáp ứng đủ các điều kiện quy định tại Thông tư này, có nhu cầu được áp dụng chế độ ưu tiên, gửi hồ sơ bản giấy đến Tổng cục Hải quan để được xem xét công nhận. Hồ sơ theo quy định tại các điểm a, b, c, d, đ, e khoản 1 Điều 18 Thông tư số 72/2015/TT-BTC của Bộ trưởng Bộ Tài chính”.\n6. Sửa đổi, bổ sung Điều 19 như sau:\n“Điều 19. Thẩm định điều kiện để áp dụng chế độ ưu tiên\n1. Trong thời hạn 30 ngày kể từ ngày nhận đủ hồ sơ theo quy định tại Điều 18 Thông tư này, Tổng cục Hải quan thẩm định, kết luận về việc công nhận doanh nghiệp ưu tiên.\nĐối với các trường hợp phức tạp, cần lấy ý kiến các Bộ, ngành liên quan thì thời gian thẩm định có thể được kéo dài nhưng không quá 30 ngày.\n2. Thẩm định hồ sơ.\na) Tổng cục Hải quan kiểm tra tính đầy đủ, hợp pháp, hợp lệ hồ sơ của doanh nghiệp và dự án đầu tư trọng điểm nộp theo quy định tại khoản 1, khoản 2 Điều 18 Thông tư này; đối chiếu thông tin doanh nghiệp cung cấp, thông tin thu thập về doanh nghiệp từ cơ quan thuế và cơ quan hải quan nơi doanh nghiệp có trụ sở chính và nơi doanh nghiệp có hoạt động xuất khẩu, nhập khẩu với điều kiện áp dụng chế độ ưu tiên quy định tại Chương III Thông tư này;\nb) Trường hợp hồ sơ chưa đầy đủ theo quy định, trong thời hạn 05 (năm) ngày làm việc kể từ ngày nhận được văn bản đề nghị áp dụng chế độ ưu tiên, Tổng cục Hải quan có văn bản thông báo để doanh nghiệp nộp bổ sung;\nc) Trường hợp hồ sơ doanh nghiệp không đáp ứng điều kiện áp dụng chế độ ưu tiên theo quy định, Tổng cục Hải quan có văn bản trả lời doanh nghiệp, nêu rõ lý do không đáp ứng;\nd) Trường hợp kết quả kiểm tra hồ sơ doanh nghiệp đáp ứng điều kiện áp dụng chế độ ưu tiên theo quy định, Tổng cục Hải quan thẩm định thực tế tại doanh nghiệp.\n3. Thẩm định thực tế tại doanh nghiệp.\na) Tổng cục Hải quan tổ chức thực hiện thẩm định thực tế tại doanh nghiệp. Nội dung thẩm định thực tế gồm:\na.1) Đối chiếu kết quả kiểm tra thực tế với thông tin khai báo của doanh nghiệp.\na.2) Kiểm tra sau thông quan tại trụ sở người khai hải quan để đánh giá việc tuân thủ pháp luật nếu trong thời gian 24 (hai mươi tư) tháng liên tục, gần nhất tính đến thời điểm doanh nghiệp có văn bản đề nghị công nhận doanh nghiệp ưu tiên, doanh nghiệp chưa được thanh tra hoặc kiểm tra sau thông quan để đánh giá việc tuân thủ pháp luật hải quan, pháp luật thuế;\nb) Thời gian thẩm định thực tế tại doanh nghiệp, dự án tối đa 05 (năm) ngày làm việc. Trường hợp phải kiểm tra sau thông quan tại trụ sở người khai hải quan thì thời gian thực hiện theo pháp luật về kiểm tra sau thông quan”.\n7. Bổ sung Điều 20a như sau:\n“Điều 20a. Gia hạn áp dụng chế độ ưu tiên\nTrong thời gian 03 (ba) tháng tính đến thời hạn gia hạn áp dụng chế độ ưu tiên, Tổng cục Hải quan căn cứ các thông tin thu thập từ các Cục Thuế, Cục Hải quan tỉnh, thành phố nơi doanh nghiệp có trụ sở chính và nơi doanh nghiệp có hoạt động xuất khẩu, nhập khẩu về kết quả quản lý, kết quả kiểm tra sau thông quan (nếu có) để quyết định gia hạn”.\n8. Sửa đổi bổ sung Điều 23 như sau:\n“Điều 23. Thẩm quyền công nhận, gia hạn, tạm đình chỉ, đình chỉ áp dụng chế độ ưu tiên\nTổng cục trưởng Tổng cục Hải quan quyết định việc công nhận, gia hạn, tạm đình chỉ, đình chỉ áp dụng chế độ ưu tiên.”.\n9. Sửa đổi bổ sung Điều 25 như sau:\n“Điều 25. Trách nhiệm quản lý của cơ quan hải quan\nTổng cục Hải quan có trách nhiệm tổ chức thực hiện:\n1. Quản lý, theo dõi, đánh giá việc chấp hành pháp luật hải quan, pháp luật thuế của doanh nghiệp ưu tiên. Tổng cục Hải quan hỗ trợ doanh nghiệp nâng cao năng lực tuân thủ khi doanh nghiệp có yêu cầu.\n2. Hàng năm thu thập thông tin về việc tuân thủ pháp luật thuế, pháp luật hải quan của doanh nghiệp từ Cục Thuế; Cục Hải quan tỉnh, thành phố nơi doanh nghiệp có trụ sở chính và nơi doanh nghiệp có hoạt động xuất khẩu, nhập khẩu.\n3. Kiểm tra việc duy trì các điều kiện áp dụng chế độ ưu tiên đối với các doanh nghiệp ưu tiên, các dự án đầu tư trọng điểm đã được công nhận và áp dụng chế độ ưu tiên khi dự án hoàn thành và đi vào hoạt động.\n4. Áp dụng các chế độ ưu tiên theo quy định tại Thông tư này cho các doanh nghiệp ưu tiên.\n5. Thông báo và cập nhật danh sách doanh nghiệp ưu tiên và phối hợp với các doanh nghiệp kinh doanh cảng, kho bãi để thực hiện chế độ ưu tiên cho doanh nghiệp.”.\n10. Sửa đổi khoản 3, bổ sung khoản 7 Điều 26 như sau:\n“3. Trong thời gian 90 (chín mươi) ngày kể từ ngày kết thúc năm tài chính, doanh nghiệp nộp cho Tổng cục Hải quan báo cáo tài chính, báo cáo kiểm toán của năm trước.”.\n“7. Thông báo bằng văn bản cho Tổng cục Hải quan quyết định xử lý vi phạm pháp luật về thuế, kế toán của cơ quan có thẩm quyền đối với doanh nghiệp trong thời gian 30 ngày kể từ ngày nhận được quyết định.”.\n11. Sửa đổi, bổ sung mẫu ban hành kèm theo Thông tư số 72/2015/TT-BTC ngày 12/5/2015 của Bộ trưởng Bộ Tài chính như sau:\na) Sửa đổi mẫu 02a/DNUT, mẫu 03/DNUT, mẫu 04/DNUT, mẫu 05/DNUT, mẫu 06/DNUT;\nb) Bổ sung mẫu 03a/DNUT.",
            "com_content_embedding": "Sửa đổi tiêu đề của Điều 6 như sau: “Điều 6. Thực hiện thủ tục hải quan bằng tờ khai chưa hoàn chỉnh”. Sửa đổi, bổ sung khoản 3 Điều 7 như sau: “3. Được cơ quan hải quan và các cơ quan kinh doanh cảng, kho bãi ưu tiên làm thủ tục giao nhận hàng hóa trước, ưu tiên kiểm tra giám sát trước”. Sửa đổi, bổ sung Điều 8 như sau: “Điều 8. Kiểm tra chuyên ngành Doanh nghiệp được đưa hàng hóa nhập khẩu về kho của doanh nghiệp để bảo quản trong khi chờ kết quả kiểm tra chuyên ngành, trừ trường hợp pháp luật kiểm tra chuyên ngành quy định hàng hóa phải kiểm tra tại cửa khẩu. Trường hợp cần lấy mẫu để kiểm tra chuyên ngành thì được ưu tiên lấy mẫu hàng hóa trước”. Sửa đổi, bổ sung Điều 9 như sau: “Điều 9. Thủ tục về thuế Được hoàn thuế trước, kiểm tra sau. Hồ sơ hoàn thuế thực hiện theo Nghị định số 134/2016/NĐ-CP ngày 01/9/2016 của Chính phủ; thủ tục nộp, tiếp nhận, xử lý hồ sơ hoàn thuế thực hiện theo quy định tại Nghị định số 134/2016/NĐ-CP ngày 01/9/2016 của Chính phủ, Thông tư số 38/2015/TT-BTC ngày 25/3/2015 và Thông tư số 39/2018/TT-BTC ngày 20/4/2018 của Bộ trưởng Bộ Tài chính. Căn cứ trên kết quả tự tính, tự khai của doanh nghiệp, cơ quan hải quan kiểm tra tính phù hợp về hồ sơ. Thời gian ra quyết định hoàn thuế không quá 01 (một) ngày làm việc kể từ ngày nhận được hồ sơ hợp lệ của doanh nghiệp. Thời hạn nộp thuế đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp ưu tiên thực hiện theo quy định tại khoản 2 Điều 9 Luật Thuế xuất khẩu, thuế nhập khẩu số 107/2016/QH13 ngày 06/4/2016. Được ưu tiên khi thực hiện các thủ tục về thuế đối với hàng hóa xuất khẩu, nhập khẩu theo quy định của pháp luật về thuế.”. Sửa đổi địa điểm nộp hồ sơ tại khoản 1 Điều 18 như sau: “1. Doanh nghiệp đáp ứng đủ các điều kiện quy định tại Thông tư này, có nhu cầu được áp dụng chế độ ưu tiên, gửi hồ sơ bản giấy đến Tổng cục Hải quan để được xem xét công nhận. Hồ sơ theo quy định tại các điểm a, b, c, d, đ, e khoản 1 Điều 18 Thông tư số 72/2015/TT-BTC của Bộ trưởng Bộ Tài chính”. Sửa đổi, bổ sung Điều 19 như sau: “Điều 19. Thẩm định điều kiện để áp dụng chế độ ưu tiên Trong thời hạn 30 ngày kể từ ngày nhận đủ hồ sơ theo quy định tại Điều 18 Thông tư này, Tổng cục Hải quan thẩm định, kết luận về việc công nhận doanh nghiệp ưu tiên. Đối với các trường hợp phức tạp, cần lấy ý kiến các Bộ, ngành liên quan thì thời gian thẩm định có thể được kéo dài nhưng không quá 30 ngày. Thẩm định hồ sơ. Tổng cục Hải quan kiểm tra tính đầy đủ, hợp pháp, hợp lệ hồ sơ của doanh nghiệp và dự án đầu tư trọng điểm nộp theo quy định tại khoản 1, khoản 2 Điều 18 Thông tư này; đối chiếu thông tin doanh nghiệp cung cấp, thông tin thu thập về doanh nghiệp từ cơ quan thuế và cơ quan hải quan nơi doanh nghiệp có trụ sở chính và nơi doanh nghiệp có hoạt động xuất khẩu, nhập khẩu với điều kiện áp dụng chế độ ưu tiên quy định tại Chương III Thông tư này; Trường hợp hồ sơ chưa đầy đủ theo quy định, trong thời hạn 05 (năm) ngày làm việc kể từ ngày nhận được văn bản đề nghị áp dụng chế độ ưu tiên, Tổng cục Hải quan có văn bản thông báo để doanh nghiệp nộp bổ sung; Trường hợp hồ sơ doanh nghiệp không đáp ứng điều kiện áp dụng chế độ ưu tiên theo quy định, Tổng cục Hải quan có văn bản trả lời doanh nghiệp, nêu rõ lý do không đáp ứng; Trường hợp kết quả kiểm tra hồ sơ doanh nghiệp đáp ứng điều kiện áp dụng chế độ ưu tiên theo quy định, Tổng cục Hải quan thẩm định thực tế tại doanh nghiệp. Thẩm định thực tế tại doanh nghiệp. Tổng cục Hải quan tổ chức thực hiện thẩm định thực tế tại doanh nghiệp. Nội dung thẩm định thực tế gồm: 1) Đối chiếu kết quả kiểm tra thực tế với thông tin khai báo của doanh nghiệp. 2) Kiểm tra sau thông quan tại trụ sở người khai hải quan để đánh giá việc tuân thủ pháp luật nếu trong thời gian 24 (hai mươi tư) tháng liên tục, gần nhất tính đến thời điểm doanh nghiệp có văn bản đề nghị công nhận doanh nghiệp ưu tiên, doanh nghiệp chưa được thanh tra hoặc kiểm tra sau thông quan để đánh giá việc tuân thủ pháp luật hải quan, pháp luật thuế; Thời gian thẩm định thực tế tại doanh nghiệp, dự án tối đa 05 (năm) ngày làm việc. Trường hợp phải kiểm tra sau thông quan tại trụ sở người khai hải quan thì thời gian thực hiện theo pháp luật về kiểm tra sau thông quan”. Bổ sung Điều 20a như sau: “Điều 20a. Gia hạn áp dụng chế độ ưu tiên Trong thời gian 03 (ba) tháng tính đến thời hạn gia hạn áp dụng chế độ ưu tiên, Tổng cục Hải quan căn cứ các thông tin thu thập từ các Cục Thuế, Cục Hải quan tỉnh, thành phố nơi doanh nghiệp có trụ sở chính và nơi doanh nghiệp có hoạt động xuất khẩu, nhập khẩu về kết quả quản lý, kết quả kiểm tra sau thông quan (nếu có) để quyết định gia hạn”. Sửa đổi bổ sung Điều 23 như sau: “Điều 23. Thẩm quyền công nhận, gia hạn, tạm đình chỉ, đình chỉ áp dụng chế độ ưu tiên Tổng cục trưởng Tổng cục Hải quan quyết định việc công nhận, gia hạn, tạm đình chỉ, đình chỉ áp dụng chế độ ưu tiên.”. Sửa đổi bổ sung Điều 25 như sau: “Điều 25. Trách nhiệm quản lý của cơ quan hải quan Tổng cục Hải quan có trách nhiệm tổ chức thực hiện: Quản lý, theo dõi, đánh giá việc chấp hành pháp luật hải quan, pháp luật thuế của doanh nghiệp ưu tiên. Tổng cục Hải quan hỗ trợ doanh nghiệp nâng cao năng lực tuân thủ khi doanh nghiệp có yêu cầu. Hàng năm thu thập thông tin về việc tuân thủ pháp luật thuế, pháp luật hải quan của doanh nghiệp từ Cục Thuế; Cục Hải quan tỉnh, thành phố nơi doanh nghiệp có trụ sở chính và nơi doanh nghiệp có hoạt động xuất khẩu, nhập khẩu. Kiểm tra việc duy trì các điều kiện áp dụng chế độ ưu tiên đối với các doanh nghiệp ưu tiên, các dự án đầu tư trọng điểm đã được công nhận và áp dụng chế độ ưu tiên khi dự án hoàn thành và đi vào hoạt động. Áp dụng các chế độ ưu tiên theo quy định tại Thông tư này cho các doanh nghiệp ưu tiên. Thông báo và cập nhật danh sách doanh nghiệp ưu tiên và phối hợp với các doanh nghiệp kinh doanh cảng, kho bãi để thực hiện chế độ ưu tiên cho doanh nghiệp.”. Sửa đổi khoản 3, bổ sung khoản 7 Điều 26 như sau: “3. Trong thời gian 90 (chín mươi) ngày kể từ ngày kết thúc năm tài chính, doanh nghiệp nộp cho Tổng cục Hải quan báo cáo tài chính, báo cáo kiểm toán của năm trước.”. “7. Thông báo bằng văn bản cho Tổng cục Hải quan quyết định xử lý vi phạm pháp luật về thuế, kế toán của cơ quan có thẩm quyền đối với doanh nghiệp trong thời gian 30 ngày kể từ ngày nhận được quyết định.”. Sửa đổi, bổ sung mẫu ban hành kèm theo Thông tư số 72/2015/TT-BTC ngày 12/5/2015 của Bộ trưởng Bộ Tài chính như sau: Sửa đổi mẫu 02a/DNUT, mẫu 03/DNUT, mẫu 04/DNUT, mẫu 05/DNUT, mẫu 06/DNUT; Bổ sung mẫu 03a/DNUT."
        }
    }

Output:
```json
{
  "Instruction": "Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet (thực thể 1, mối quan hệ, thực thể 2).",
  "Document": "Điều 1 / Thông tư 07/2019/TT-BTC, trích yếu 'SỬA ĐỔI, BỔ SUNG MỘT SỐ ĐIỀU CỦA THÔNG TƯ SỐ 72/2015/TT-BTC' có danh sách ngữ cảnh sau  [\n      'Điều 1. Sửa đổi, bổ sung một số điều của Thông tư số 72/2015/TT-BTC ngày 12 tháng 5 năm 2015 của Bộ trưởng Bộ Tài chính quy định áp dụng chế độ ưu tiên trong việc thực hiện thủ tục hải quan, kiểm tra, giám sát hải quan đối với hàng hóa xuất khẩu, nhập khẩu của doanh nghiệp:'\n    ]",
  "Answer": [
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi",
      "Điều 6 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi bổ sung",
      "Khoản 3 / Điều 7 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi bổ sung",
      "Điều 8 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi bổ sung",
      "Điều 9 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi",
      "Khoản 1 / Điều 18 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi bổ sung",
      "Điều 19 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "bổ sung",
      "Điều 20a / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi bổ sung",
      "Điều 23 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi bổ sung",
      "Điều 25 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "sửa đổi",
      "Khoản 3 / Điều 26 / Thông tư 72/2015/TT-BTC"
    ],
    [
      "Điều 1 / Thông tư 07/2019/TT-BTC",
      "bổ sung",
      "Khoản 7 / Điều 26 / Thông tư 72/2015/TT-BTC"
    ]
  ]
}

Yêu cầu:
- Dữ liệu đầu ra phải ở định dạng JSON hợp lệ.
- Chỉ trích xuất các điều khoản (Điều, Khoản, Mục) và mối quan hệ giữa chúng (sửa đổi bổ sung, sửa đổi, bổ sung, bãi bỏ, thay thế).
- Khi đề cập điều, khoản; phải đề cập tên đầy đủ, ví dụ Điểm a / Khoản 1 / Điều 1 / Luật Đầu tư, không chỉ đề cập Điểm a.
- Bỏ qua bất kỳ thông tin không cần thiết nào.
"""

PROMPT_CREATE_DATASET_REFORMATTED = """

Hãy trích xuất các thực thể pháp lý và quan hệ giữa chúng từ văn bản sau.

- Một THỰC THỂ PHÁP LÝ chỉ có 3 yếu tố cấu thành:
    + Điều
    + Khoản
    + Điểm
- Định dạng của THỰC THỂ PHÁP LÝ: "Điều X / Khoản Y / Điểm Z", với X, Y, Z là ký tự hoặc chữ số. Các Điều, Khoản, Điểm phải ngăn cách nhau bằng dấu "/".

***YÊU CẦU***:
- Trích xuất THỰC THỂ PHÁP LÝ:
    + Có đủ 3 yếu tố cấu thành.
    + THỰC THỂ PHÁP LÝ chỉ xác định khi có ít nhất 1 yếu tố cấu thành.
- Các Thực thể phải được trích xuất từ câu hỏi.
- Không chứa tên của văn bản quy phạm pháp luật như Nghị định, Hiến pháp, Sắc lệnh, Chương...
- 5 mối quan hệ chỉ được phép là: sửa đổi bổ sung, sửa đổi, bổ sung, bãi bỏ, thay thế.
- Chỉ trích xuất khi có ĐỦ 2 THỰC THỂ và QUAN HỆ giữa chúng.
- Không trích xuất thông tin ngoài phạm vi trên. Không suy diễn.
- Không sinh ra bất kỳ giải thích hoặc mô tả reasoning.
- Khi không có triplet hợp lệ, trả về [].
- Khi có triplet hợp lệ, định dạng kết quả: [<THỰC THỂ 1> + <QUAN HỆ> + <THỰC THỂ 2>, ...]
"""

PROMPT_CREATE_DATASET_NEW = """
Nhiệm vụ của bạn là trích xuất các thực thể pháp lý và quan hệ giữa chúng.

### NHIỆM VỤ
Từ văn bản đầu vào, hãy trích xuất tất cả các quan hệ pháp lý giữa các thực thể theo đúng schema sau:

Mỗi quan hệ là một đối tượng có dạng:
{
  "entity1": "<Thực thể pháp lý thứ nhất>",
  "relation": "<Quan hệ>",
  "entity2": "<Thực thể pháp lý thứ hai>"
}

Và danh sách tất cả các quan hệ phải được đặt trong:
{
  "triples": [ ... ]
}

### QUY TẮC TRÍCH XUẤT

#### 1. THỰC THỂ PHÁP LÝ
- Một thực thể pháp lý chỉ bao gồm ba thành phần:
  + Điểm
  + Khoản
  + Điều
- Định dạng chuẩn: "Điểm X / Khoản Y / Điều Z", ví dụ như:
  + "Điểm 5 / Khoản 2"
  + "Điểm a / Khoản 3 / Điều 7"
- Ít nhất phải có **một** trong ba thành phần (Điều hoặc Khoản hoặc Điểm).
- Không được trích xuất các tên văn bản quy phạm pháp luật như: Nghị định, Thông tư, Luật, Hiến pháp, Chương, Mục…

#### 2. QUAN HỆ PHÁP LÝ
Chỉ được phép dùng đúng 5 loại:
- "sửa đổi bổ sung"
- "sửa đổi"
- "bổ sung"
- "bãi bỏ"
- "thay thế"

#### 3. ĐIỀU KIỆN TRÍCH XUẤT
- Chỉ tạo triplet khi *có đủ 2 thực thể hợp lệ* và *một quan hệ hợp lệ* nằm trong 5 loại trên.
- Không được suy diễn thực thể hoặc suy diễn quan hệ không xuất hiện trong văn bản.
- Không sinh giải thích, không suy luận, không dùng token như </think>.
- Chú ý thứ tự của các thực thể pháp lý vì đây là quan hệ một chiều.

#### 4. ĐẦU RA
- Nếu không có quan hệ nào hợp lệ → trả về:
  {
    "triples": []
  }
- Nếu có quan hệ hợp lệ → trả về đúng JSON tương ứng với schema ExtractionResult.

### VĂN BẢN CẦN TRÍCH XUẤT:
{text}
"""

EXAMPLE_OLD = """
Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet có dạng như sau: (thực thể 1, mối quan hệ, thực thể 2).
Không trích xuất thông tin không liên quan. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***. Không thêm bất kỳ giải thích nào ngoài yêu cầu.
Chỉ trích xuất ra các điều khoản (Điều, Khoản, Mục) và mối quan hệ giữa chúng (sửa đổi bổ sung, sửa đổi, bổ sung, bãi bỏ, thay thế), không trích xuất các thực thể khác.
"""

EXAMPLE = """
Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet có dạng như sau: ["<THỰC THỂ 1> + <MỐI QUAN HỆ> + <THỰC THỂ 2>"].
Không trích xuất thông tin không liên quan. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***. Không thêm bất kỳ giải thích nào ngoài yêu cầu.

Trong đó:
- THỰC THỂ là: Bạn hãy liệt kê các thực thể pháp lý theo thứ tự như sau: Chương / Mục / Tiểu mục / Điều / Khoản / Điểm.
Lưu ý: THỰC THỂ phải xuất hiện hoàn toàn trong văn bản gốc, không tự phát minh. Chỉ liệt kê các thực thể pháp lý 
- MỐI QUAN HỆ chỉ được phép nằm trong danh sách sau:
  + sửa đổi bổ sung
  + sửa đổi
  + bổ sung
  + bãi bỏ
  + thay thế

YÊU CẦU BẮT BUỘC:
- KHÔNG trích xuất bất kỳ thực thể nào ngoài Điều / Khoản / Mục / Điểm.
- KHÔNG suy diễn, KHÔNG tạo quan hệ nếu văn bản không nêu rõ.
- KHÔNG thêm bình luận, giải thích, mô tả, bước suy luận, hoặc token đặc biệt (ví dụ: </think>, <!-- -->).
- Output phải là một JSON list duy nhất gồm các string triplet.
- Mỗi triplet mô tả đúng mối quan hệ được nêu trực tiếp trong văn bản.

Nếu không có triplet hợp lệ, trả về: <unknown>.
"""

EXAMPLE_REASONING = """
Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet có dạng như sau: ["<THỰC THỂ 1> + <MỐI QUAN HỆ> + <THỰC THỂ 2>"].

Bạn phải thực hiện ĐÚNG HAI bước sau:

ĐỊNH DẠNG CỦA OUTPUT
1. OUTPUT cho THINKING
Bạn phải thực hiện ĐÚNG các bước sau:
hãy viết toàn bộ phần suy luận chi tiết nằm giữa 2 thẻ <think> và </think>. Đây là nơi bạn phân tích câu hỏi và đưa ra suy luận cho câu trả lời.
Không được để trống. Không được viết nội dung suy luận nằm bên ngoài 2 thẻ.

2. OUTPUT cho ANSWER
Trong thẻ <output> ... </output>, chỉ đưa ra danh sách các bộ ba quan hệ có dạng ["<THỰC THỂ 1> + <MỐI QUAN HỆ> + <THỰC THỂ 2>"].
KHÔNG được kèm theo bất kỳ từ ngữ, ký tự hoặc giải thích nào khác ở phần này.
KHÔNG được viết câu kiểu “Có các quan hệ sau:<THỰC THỂ 1> + <MỐI QUAN HỆ> + <THỰC THỂ 2>"]. ”.
KHÔNG được viết lại câu hỏi.


YÊU CẦU TUÂN THỦ NGHIÊM NGẶT:
Nội dung thinking và câu trả lời phải được viết trong các thẻ tương ứng, không được viết bên ngoài.
Không được thêm văn bản ngoài hai thẻ <think> và <output>.
Không được đổi tên thẻ hoặc thêm thẻ mới.
Không được viết nội dung khác ngoài các triplet bên trong thẻ <output>.
Định dạng phải chính xác tuyệt đối.

Ví dụ đúng:
<think>Phân tích nội bộ...</think>
<output>["Điểm b / Khoản 35 / Điều 1 + bổ sung + Phụ lục II"]</output>

Ví dụ sai:
Đáp án là A
<output>Văn bản có quan hệ ["Điểm b / Khoản 35 / Điều 1 + bổ sung + Phụ lục II"] vì</output>
A. Đây là đáp án đúng vì...
"""

EXAMPLE_FEWSHOT = """
Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet có dạng như sau: ["<THỰC THỂ 1> + <MỐI QUAN HỆ> + <THỰC THỂ 2>"].
Không trích xuất thông tin không liên quan. Không thêm các token thuộc về giải thích, suy luận như </think> hoặc ***Giải thích***. Không thêm bất kỳ giải thích nào ngoài yêu cầu.

Trong đó:
- THỰC THỂ là: Bạn hãy liệt kê các thực thể pháp lý theo thứ tự như sau: Chương / Mục / Tiểu mục / Điều / Khoản / Điểm.
Lưu ý: THỰC THỂ phải xuất hiện hoàn toàn trong văn bản gốc, không tự phát minh. Chỉ liệt kê các thực thể pháp lý 
- MỐI QUAN HỆ chỉ được phép nằm trong danh sách sau:
  + sửa đổi bổ sung
  + sửa đổi
  + bổ sung
  + bãi bỏ
  + thay thế

YÊU CẦU BẮT BUỘC:
- KHÔNG trích xuất bất kỳ thực thể nào ngoài Điều / Khoản / Mục / Điểm.
- KHÔNG suy diễn, KHÔNG tạo quan hệ nếu văn bản không nêu rõ.
- KHÔNG thêm bình luận, giải thích, mô tả, bước suy luận, hoặc token đặc biệt (ví dụ: </think>, <!-- -->).
- Output phải là một JSON list duy nhất gồm các string triplet.
- Mỗi triplet mô tả đúng mối quan hệ được nêu trực tiếp trong văn bản.
- Không sử dụng ngôn ngữ khác ngoài tiếng Việt.

Nếu không có triplet hợp lệ, trả về: <unknown>.

Dưới đây là một ví dụ để bạn tham khảo:
Instruction: "Hãy trích xuất các điều khoản và mối quan hệ giữa chúng từ dữ liệu đầu vào dưới dạng danh sách các triplet (thực thể 1, mối quan hệ, thực thể 2).", 
Document: "Điểm b / Khoản 35 / Điều 1 có danh sách ngữ cảnh sau [\"b) Bổ sung các cửa khẩu cho phép người nước ngoài nhập cảnh, xuất cảnh bằng thị thực điện tử (Phụ lục II) như sau:\\n- Danh sách cửa khẩu đường bộ:\\n+ Cửa khẩu quốc tế Tây Trang/tỉnh Điện Biên;\\n+ Cửa khẩu quốc tế Na Mèo/tỉnh Thanh Hóa;\\n+ Cửa khẩu quốc tế La Lay/tỉnh Quảng Trị;\\n- Danh sách cửa khẩu đường biển:\\n+ Cửa khẩu cảng Dương Đông/tỉnh Kiên Giang;\\n+ Cửa khẩu cảng Chân Mây/tỉnh Thừa Thiên - Huế.\", \"Điều 1. Sửa đổi, bổ sung một số điều của Nghị định số 07/2017/NĐ-CP ngày 25 tháng 01 năm 2017 của Chính phủ quy định trình tự, thủ tục thực hiện thí điểm cấp thị thực điện tử cho người nước ngoài nhập cảnh Việt Nam]"
Answer: ["Điểm b / Khoản 35 / Điều 1 + bổ sung + Phụ lục II"]
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
