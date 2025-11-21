L. Dự án: "Chuyến đi Chung" (TripSync) – Trợ lý Tổ chức Du lịch Nhóm
Bên liên quan: Nhóm bạn bè, gia đình, đồng nghiệp cùng đi du lịch (từ 3 người trở lên).

1. Tổng quan Dự án (Project Overview)
   "TripSync" là một ứng dụng di động/web "tất-cả-trong-một" được thiết kế để giải quyết sự hỗn
   loạn của việc lên kế hoạch du lịch nhóm. Hiện tại, mọi thông tin (ý tưởng, lịch trình, chi phí, file
   đặt vé) đều bị phân tán trên Zalo, Google Docs, Excel, Messenger, và Email, dẫn đến nhầm lẫn
   và xung đột.
   Ứng dụng này hoạt động như một "phòng tác chiến" trung tâm cho chuyến đi, nơi mọi thành
   viên có thể cùng nhau: Xây dựng Lịch trình, Theo dõi Chi tiêu & Chia tiền, Lưu trữ Giấy tờ, và
   Bình chọn Địa điểm.
2. Bối cảnh & Vấn đề (Business Problem & Context)
   Hiện trạng (Current State): Lên kế hoạch cho một chuyến đi 5 người là một bài kiểm tra về sự
   kiên nhẫn.

   1. Hỗn loạn Thông tin (Information Chaos):
      o Zalo/Messenger: Hàng trăm tin nhắn "Tối T7 ăn gì?", "Link khách sạn này OK
      không?". Các quyết định quan trọng bị trôi mất.
      o Excel: Dùng để tính toán chi phí, nhưng chỉ một người giữ file, cập nhật chậm, và
      rất khó xem trên di động.
      o Google Docs:Dùng để phác thảo lịch trình, nhưng mọi người lười mở và cập nhật.
   2. Ác mộng Tài chính (Financial Nightmare): Đây là vấn đề lớn nhất.
      o Bạn A trả tiền vé máy bay, bạn B trả tiền khách sạn, bạn C trả tiền ăn tối.
      o Cuối chuyến đi, không ai biết chính xác ai nợ ai bao nhiêu. Quá trình "chia bill"
      thủ công rất dễ sai sót và gây bất hòa.
   3. Thiếu Quyết định Chung: Khi có 5 ý tưởng về địa điểm ăn tối, việc thống nhất rất khó
      khăn. Cần một công cụ để "vote" (bình chọn) nhanh.

   4. Thất lạc Giấy tờ: Mã đặt vé máy bay, xác nhận khách sạn... bị gửi lung tung. Đến sân bay,
      cả nhóm mới cuống cuồng tìm lại email/tin nhắn cũ.
      Cơ hội (Opportunity): Xây dựng một không gian làm việc chung (collaborative workspace) duy
      nhất, được thiết kế chuyên biệt cho du lịch, giúp mọi thứ minh bạch, tự động và dễ dàng truy
      cập.

3. Đối tượng Người dùng (Target Audience)
   Chân dung người dùng (Persona): "Trưởng đoàn Bất đắc dĩ"
   • Mô tả: Là người "đứng ra" tổ chức chuyến đi cho nhóm bạn, gia đình.
   • Nhu "cầu": Cần một công cụ để hệ thống hóa các ý tưởng, minh bạch hóa tài chính, và
   giảm tải công việc tổ chức cho bản thân.
   • Tâm lý: Họ muốn chuyến đi vui vẻ, nhưng lại sợ hãi quá trình lên kế hoạch và "đòi tiền"
   bạn bè.
4. Yêu cầu Chức năng (Functional Requirements - FRs)
   Mỗi "Chuyến đi" là một dự án riêng trong app.
   FR1: Module "Lịch trình Cộng tác" (Collaborative Itinerary)
   • FR1.1: Trục Thời gian Trực quan: Hiển thị lịch trình theo trục thời gian (Ngày 1, Ngày
   2...).
   • FR1.2: Thêm Hoạt động: Bất kỳ thành viên nào cũng có thể "đề xuất" (suggest) một hoạt
   động (ví dụ: "Ăn trưa ở quán X", "Thăm bảo tàng Y").
   • FR1.3: Bình chọn (Voting): Tính năng cốt lõi. Các thành viên khác có thể "Vote"
   ( / ) cho đề xuất đó. Đề xuất nào được nhiều vote nhất sẽ được "chốt" và thêm vào
   lịch trình chính thức.
   • FR1.4: Tích hợp Bản đồ: Tự động hiển thị các địa điểm đã chốt (khách sạn, quán ăn...)
   trên một bản đồ chung (Google Maps) để mọi người hình dung được lộ trình.
   FR2: Module "Chia tiền Thông minh" (Smart Bill Splitter)
   • FR2.1: Thêm Chi tiêu: Bất kỳ thành viên nào cũng có thể thêm một khoản chi (ví dụ: "Bạn
   A đã trả 5.000.000đ tiền khách sạn").
   • FR2.2: Phân chia Linh hoạt (Tương tự HousePal): Chọn cách chia (chia đều, chia cho
   3/5 người, chia theo tỷ lệ...).
   • FR2.3: Bảng Cân đối Tự động: Tính năng "ăn tiền". Ứng dụng tự động tính toán và tối
   giản hóa các khoản nợ:
   o Trạng thái: "Bạn đang nợ Nhóm: 200.000đ" hoặc "Nhóm đang nợ bạn: 500.000đ".
   • FR2.4: Chốt/Thanh toán Nợ: Hiển thị rõ: "Để huề, B chỉ cần trả A 300k, C trả A 200k".
   FR3: Module "Kho Tài liệu Chung" (Document Vault)
   • FR3.1: Tải lên Tập trung: Một nơi duy nhất để tải lên tất cả các giấy tờ quan trọng.
   • FR3.2: Phân loại: Tự động (hoặc thủ công) phân loại: "Vé máy bay", "Khách sạn", "Vé tàu",
   "Giấy tờ tùy thân".
   • FR3.3: Truy cập Offline: (Nâng cao) Cho phép xem các tài liệu này ngay cả khi không có
   mạng (rất quan trọng khi ở sân bay hoặc ra nước ngoài).
   FR4: Module "Checklist Nhóm" (Shared Checklist)
   • FR4.1: Danh sách Đóng gói: Một danh sách các món đồ cần mang (ví dụ: "Kem chống
   nắng", "Sạc dự phòng", "Thuốc say xe").
   • FR4.2: Phân công: Các món đồ chung có thể được phân công (ví dụ: "[Bạn A] mang loa
   kéo", "[Bạn B] mang kem đánh răng").
5. Yêu cầu Phi chức năng (Non-Functional Requirements - NFRs)
   • NFR1: Đồng bộ Thời gian thực (Real-time Sync): Cực kỳ quan trọng. Khi A thêm một
   khoản chi, B và C phải thấy ngay lập tức.
   • NFR2: Trải nghiệm Người dùng (UX): Giao diện phải trực quan. Thao tác "Thêm chi tiêu"
   và "Vote" phải cực kỳ nhanh.
   • NFR3: Đa tiền tệ (Multi-currency): (Nâng cao) Nếu đi nước ngoài, cho phép nhập chi
   tiêu bằng ngoại tệ (USD, JPY...) và tự động quy đổi về VND theo tỷ giá do người dùng nhập.
   • NFR4: Hoạt động Offline: (Nâng cao) Cho phép nhập chi tiêu khi không có mạng, và tự
   động đồng bộ khi có mạng trở lại.
6. Ràng buộc & Giả định (Constraints & Assumptions)
   • Ràng buộc 1: Ứng dụng không xử lý thanh toán thật (không liên kết ngân hàng). Nó là
   một "sổ kế toán" và "công cụ lập kế hoạch" chung.
   • Giả định 1 (Lớn nhất): Cần có sự đồng thuận của cả nhóm để cài đặt và sử dụng ứng
   dụng này làm "kênh chính thức" cho chuyến đi, thay vì Zalo.
   • Giả định 2: Các thành viên trung thực và chủ động trong việc nhập các khoản chi tiêu
   của mìn
