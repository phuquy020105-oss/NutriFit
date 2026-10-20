# Kiến trúc và quy tắc NutriFit

Luồng xử lý: HTTP → Filter → Servlet → Service → DAO/JDBC → MySQL; Servlet đưa DTO sang JSP. JSP nằm trong `WEB-INF/views`, không được gọi trực tiếp. Assets nằm trong `src/main/webapp/assets`.

## Phân chia trách nhiệm

- `controller`: nhận input, phân biệt400/401/403/lỗi database và redirect/forward; không tính dinh dưỡng trong JSP.
- `filter`: xác thực session/version, kiểm tra Admin, CSRF, onboarding và quyền điều hướng hiện hành.
- `service`: quy tắc nghiệp vụ và transaction. `ConnectionProvider` là điểm ghép kiểm thử, không phải code chết.
- `dao`: SQL PreparedStatement, owner isolation và ánh xạ dữ liệu; `RecipeReadPort` tách thuật toán khỏi nguồn Recipe.
- `dto/model`: dữ liệu hiển thị, snapshot và model database; `util/config`: escaping, CSRF, định dạng, kết nối và truststore TLS.

Servlet/Filter được Tomcat tìm bằng annotation; không có Java caller không đồng nghĩa không dùng. Các POST/route Nutrition cũ được giữ để tương thích. Health DB là chẩn đoán vận hành, khác health không truy cập DB.

## Nutrition

Mỗi preview có một món sáng/trưa/tối và `servings=1.00`. `MealRecommendationService` xét tổ hợp; `MealPlanScorer` cân bằng độ lệch calories, protein/carbs/fat/fiber và đa dạng. Không ép mục tiêu bằng khẩu phần lẻ. Calories thực tế/chênh lệch được giữ nguyên; số nguyên HALF_UP chỉ áp dụng khi hiển thị.

Free dùng mục tiêu hồ sơ; Premium còn hạn loại DISLIKE và ưu tiên LIKE. Đổi món chỉ thay bữa được chọn, giữ hai bữa còn lại; Đổi thực đơn đổi phương án ba bữa. Preview trong session không ghi database. Save kiểm tra owner/ngày/nonce/CSRF/thời hạn, đọc lại dữ liệu và lưu ba món trong một transaction; lỗi rollback, không tự retry khi COMMIT chưa rõ kết quả. Snapshot cũ, kể cả khẩu phần thập phân, không bị thay bằng giá trị catalog mới.

Lịch sử là read-only: query dùng EXISTS để chỉ lấy30ngày trước hôm nay có món, owner-bound và không nhân bản ngày. Chọn ngày rỗng chỉ hiện thông báo; entry thật có số liệu bằng0 vẫn hiển thị. Sở thích lưu ở endpoint riêng và Premium được kiểm tra trong Service.

## Bảo mật và tích hợp

Mật khẩu dùng BCrypt; session bị vô hiệu khi auth_version thay đổi. Admin được kiểm tra bằng tài khoản hiện hành từ backend, độc lập FREE/PREMIUM; menu không thay thế AdminFilter. Không tạo fake session để kiểm thử production.

Brevo gửi OTP qua HTTPS; Gemini chỉ gọi khi có cấu hình. VNPay dùng Sandbox: Return hiển thị kết quả, IPN xác minh chữ ký/số tiền/giao dịch và cập nhật Premium có transaction/idempotency. Không dùng thanh toán thật hay gửi email hàng loạt để smoke test.

Aiven dùng TLS VERIFY_IDENTITY với CA đọc từ Secret File; truststore tạm được tạo khi chạy, không chứa trong image. Docker giữ UID10001 và supplementaryGID1000, context `/nutrifit`, ROOT302 sang register và health báo revision. Không seed/migrate trong startup.

## Kiểm thử và giới hạn

JUnit kiểm tra calculator/giới hạn số học, menu/swap/save, Free/Premium, CSRF/owner/nonce/rollback, history, role navigation, BCrypt, VNPay canonical và health. Fixture HTTP/JDBC không chứng minh email, merchant, Gemini hay browser đăng nhập production đã hoạt động.

`NutritionViewsTest` render JSP thật trong Tomcat loopback tách biệt, cần TOMCAT_HOME. `scripts/verify_web.py` biên dịch toàn bộ JSP và chạy37assertions JavaScript trong Chrome. `scripts/verify_repository.py` kiểm tra catalog/provenance/ảnh, includes và đường dẫn assets/tài liệu. Database test riêng kiểm tra seed/transaction/idempotency và dữ liệu JDBC thực, không dùng dữ liệu người thật.

Trước bàn giao, vẫn cần tự kiểm tra UI đăng nhập/OTP, Dashboard/Admin đúng quyền, Workout, Gemini và VNPay Sandbox bằng tài khoản được phép trên môi trường đích; không coi mock tests là authenticated E2E.
