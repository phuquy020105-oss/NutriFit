# Go-live 60 món — hoàn tất 2026-10-20

Chủ dự án đã phê duyệt đúng manifest SHA256 `40c1ab4b874dc74089722f9b2952d2cfbd7ae8f4f120d4fb488c30da801c84cc`. Migration trên **Aiven nutrifitdb đã COMMIT thành công**: thêm 18 Food, 30 Recipe, 224 Ingredient và cập nhật 66 Food. Hậu kiểm bằng SELECT xác nhận **100 Food / 60 Recipe / 607 Ingredient, 20 món mỗi bữa**; cả 60 món khớp NutritionCalculator và ảnh, khóa ngoại hợp lệ. Schema và checksum của 21 bảng ngoài catalog giữ nguyên. ID cũ, 30 Recipe, 383 Ingredient cũ và nhật ký được bảo toàn. Lần chạy thứ hai trả `ALREADY_APPLIED`, **0 lần ghi**.

Biên bản máy đọc được: [demo60-go-live.json](demo60-go-live.json). Backup catalog và DDL của 24 bảng lưu ngoài Git đã được phục hồi thử thành công; backup này không chứa toàn bộ dữ liệu cá nhân. Manifest và 121 checksum của gói được giữ bất biến. Cờ chưa deploy trong manifest ghi trạng thái lúc đóng gói; biên bản go-live bổ sung trạng thái thực tế sau phê duyệt. Không chạy lại migration để cập nhật cờ trong manifest.

Code và ảnh đã được xác minh trên Render tại revision `b8a55682c96226959e57b14559a2797f20499e68`. Chưa kiểm thử trình duyệt production với tài khoản đăng nhập; dữ liệu đã được kiểm tra qua JDBC thật trên Aiven. Người dùng có thể nhấn **Gợi ý lại** để chọn từ 60 món. Các bản xem trước và nhật ký cũ không bị tự đổi.

Các checkpoint chuẩn bị bên dưới là lịch sử, không còn là yêu cầu chờ phê duyệt:

# Food Data Quality — educational60release

Tiếp tục từ0cfccdd theo quyết định mới2026-10-20. Đã hoàn thiện bộ100Food/60Recipe/607Ingredient và swap một món. Tóm tắt chi tiết, nguồn, phương pháp ước tính, benchmark, localrestore/migration, test và lệnh tái tạo ở [demo60-release.md](demo60-release.md).

-500facts:236MATCHED/161CALCULATED/103ESTIMATED,35foods có estimate;12wholefood vectors được mô tả giả định, không giả là xét nghiệm. Giữ strictsource47MISSING audit.
-30món mới10/bữa cùng30ảnhWebP đãduyệt, giữ nguyên30món/ảnh cũ, không giảmgram làm đẹpbenchmark.
-127JUnit/38Python/37JavaScriptchecks/JSP0errors/MavenBUILD SUCCESS; local24tablesbackuprestore exact,rollback/idempotency0writes/conflict/FK/stableIDs/60JDBCcalculator/snapshotPASS.
-432cohort: meanabsKcalError598.575→167.395; feasible10%200→336;0avoidable>20%gap. Swap thực tế30/60mónPASS,5nutrient và projectedjournal guards.
-PRODUCTION_READY được đóng dấu trong final-manifest sau các bước kiểm tra. Code/assets được commit/push và revision Render được báo ở handoff cuối. **Aiven đã go-live100/60/607 sau xác nhận một lần đúng manifest.** COMMIT và hậu kiểm21bảng bảo vệ/schema/60calculator/FK/ID cũPASS; chạy lần hai0writes. Xem [biên bản](demo60-go-live.json).

Các báo cáo thăm dò/candidateplan cũ được giữ để truy vết, không thay thế finalmanifest hiện hành. Không thay đổiAuth/Payment/Workout/Onboarding/schema.sql/seed gốc hoặc lịch sử. Chưa authenticatedE2E production; healthrevision và asset checks không thay cho xác minh tài khoản đăng nhập.
