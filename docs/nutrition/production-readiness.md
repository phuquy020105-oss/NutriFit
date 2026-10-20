# Go-live 60 món — hoàn tất 2026-10-20

Chủ dự án đã phê duyệt đúng manifest SHA256 `40c1ab4b874dc74089722f9b2952d2cfbd7ae8f4f120d4fb488c30da801c84cc`. Migration trên **Aiven nutrifitdb đã COMMIT thành công**: thêm 18 Food, 30 Recipe, 224 Ingredient và cập nhật 66 Food. Hậu kiểm bằng SELECT xác nhận **100 Food / 60 Recipe / 607 Ingredient, 20 món mỗi bữa**; cả 60 món khớp NutritionCalculator và ảnh, khóa ngoại hợp lệ. Schema và checksum của 21 bảng ngoài catalog giữ nguyên. ID cũ, 30 Recipe, 383 Ingredient cũ và nhật ký được bảo toàn. Lần chạy thứ hai trả `ALREADY_APPLIED`, **0 lần ghi**.

Biên bản máy đọc được: [demo60-go-live.json](demo60-go-live.json). Backup catalog và DDL của 24 bảng lưu ngoài Git đã được phục hồi thử thành công; backup này không chứa toàn bộ dữ liệu cá nhân. Manifest và 121 checksum của gói được giữ bất biến. Cờ chưa deploy trong manifest ghi trạng thái lúc đóng gói; biên bản go-live bổ sung trạng thái thực tế sau phê duyệt. Không chạy lại migration để cập nhật cờ trong manifest.

Code và ảnh đã được xác minh trên Render tại revision `b8a55682c96226959e57b14559a2797f20499e68`. Chưa kiểm thử trình duyệt production với tài khoản đăng nhập; dữ liệu đã được kiểm tra qua JDBC thật trên Aiven. Người dùng có thể nhấn **Gợi ý lại** để chọn từ 60 món. Các bản xem trước và nhật ký cũ không bị tự đổi.

Các checkpoint chuẩn bị bên dưới là lịch sử, không còn là yêu cầu chờ phê duyệt:

# Production readiness — educational60release2026-10-20

Tiêu chuẩn hiện hành do chủ dự án chấp nhận MATCHED/CALCULATED/ESTIMATED có căn cứ cho đồ án, không đòi VERIFIED hoặc kiểm nghiệm phòng thí nghiệm. Xem [bàn giao](demo60-release.md) và [manifest](../../database/staging/food-quality-v1/release/final-manifest.json).

Technicaldata/portions/assets/benchmark/tests/transaction/idempotency/restore gates đã có bằng chứng thực thi. Manifest đánh dấu PRODUCTION_READY chỉ sau finalize kiểm tra đủ bằng chứng. **Productionwrite vẫn CHƯA được phép** cho đến khi chủ dự án phê duyệt đúng SHA256 manifest một lần. Không chạy import chỉ vì code đãpush hoặc Renderhealthy.

47missing trong source-only audit không được tuyên bố đã đo/VERIFIED; release dùng ước tính riêng và giữ audit/provenance gốc. Bảng users/subscription/payment/mealentries không nằm trong DML migration. Catalogbackup+24DDL đãrestorelocal, không phảifulluserdata backup. Recovery sau có phát sinh nhật ký mới cần kế hoạch riêng, không restore chồngDBproduction.

Giới hạn: chưa chạy authenticatedE2E production, chưa go-live60data, một số mục tiêu cao chưa có tổ hợp gần năng lượng với3suấtchuẩn; hiển thị số thực và cảnh báo, không tự tăng/giảm suất.
