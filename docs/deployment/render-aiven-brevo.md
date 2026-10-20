# Triển khai Render + Aiven + Brevo

Ứng dụng hiện dùng Docker, Java21, Maven3.9.16 và Tomcat10.1.61. WAR là `nutrifit.war`, context `/nutrifit`. Repository: `phuquy020105-oss/NutriFit`, nhánh deploy: `deploy/render-aiven-brevo`.

## Cấu hình dịch vụ

Render Web Service dùng Dockerfile ở root repository, giữ entrypoint mặc định. Đặt health check `/nutrifit/health`, `PORT=8080` hoặc cổng do Render cấp. Docker build chỉ nhận source/config cần thiết qua `.dockerignore`, không nhận `.env`, certificate, backup hay database seed. Không có seed/migration trong build/startup.

Runtime chạy `USER nutrifit`, UID10001, primaryGID10001 và supplementaryGID1000 để đọc Secret File. Giữ ownership Tomcat; không chmod `/etc/secrets/ca.pem`, không copy CA vào image và không chuyển runtime sang root. Entrypoint chuyển PORT thành system property, Java chạy foreground để nhận SIGTERM.

## Environment variables

Đặt giá trị thật trong Render Dashboard, không ghi vào Git hoặc Docker build arguments. `.env.example` chỉ là mẫu tên biến.

| Biến | Vai trò |
|---|---|
| `PORT` | Cổng HTTP runtime, mặc định8080 |
| `NUTRIFIT_DB_URL` | `jdbc:mysql://<AIVEN_HOST>:27047/nutrifitdb?sslMode=VERIFY_IDENTITY&useUnicode=true&characterEncoding=UTF-8` |
| `NUTRIFIT_DB_USER`, `NUTRIFIT_DB_PASSWORD` | Tài khoản Aiven, không nhúng vào URL |
| `NUTRIFIT_DB_CA_FILE` | `/etc/secrets/ca.pem`; tạo Render Secret File từ CA của service Aiven |
| `BREVO_API_KEY` | API key transactional email |
| `BREVO_SENDER_EMAIL`, `BREVO_SENDER_NAME` | Sender đã xác minh trong Brevo; tên mặc địnhNutriFit |
| `NUTRIFIT_IP_HASH_SECRET` | Secret băm IP cho quota OTP |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Key và model Gemini được tài khoản hỗ trợ; mặc định model xem `.env.example` |
| `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET` | Merchant Sandbox và secret ký |
| `VNPAY_RETURN_URL` | `https://<RENDER_DOMAIN>/nutrifit/payment/return` |

Database cloud là `nutrifitdb`; local mặc định `nutrifitdb_java`. URL custom phải xác minh TLS/hostname, không được hạ xuống DISABLED/PREFERRED hoặc bật fallback local. CA hợp lệ được chuyển thành truststore tạm bởi DatabaseTrustStore.

Đăng ký callback VNPay Sandbox đúng domain: Return `/nutrifit/payment/return`, IPN `/nutrifit/payment/ipn`. Return không cấp Premium; IPN có kiểm tra chữ ký/idempotency. Không đổi biến môi trường để né kiểm tra.

## Kiểm tra deployment

Chạy Maven/JSP/JS/DB test trước push. Nếu Auto Deploy bật, đợi rollout rồi đọc `/nutrifit/health`: phải HTTP200 và `revision` khớp commit remote, không coi push là deploy thành công.

- `/` phải HTTP302 Location `/nutrifit/register` khi dùng ROOT webapp Docker.
- `/nutrifit/register`, `/nutrifit/login` trả trang công khai.
- Nutrition, History, Dashboard/Admin yêu cầu xác thực; anonymous redirect login không chứng minh authenticated E2E.
- Kiểm tra60ảnh trong catalog trả HTTP200, không thay bằng fallback sai món.
- `/nutrifit/health/db` là chẩn đoán kết nối, không chứng minh schema/nội dung đúng.

Sau deploy, kiểm tra OTP/login/logout, onboarding, Admin/USER, Nutrition, Workout, Gemini và VNPay Sandbox bằng tài khoản hợp lệ khi có quyền. Không tạo session giả, gửi hàng loạt OTP hoặc giao dịch thật.

## Xử lý lỗi

- 404: kiểm tra context `/nutrifit`, tên WAR và đường dẫn callback.
- Timeout DB: kiểm tra hostname/port/database/network Aiven; không tự fallback database khác.
- TLS: CA, quyền đọcSecret File và hostname phải khớp; không tắt xác minh.
- OTP: kiểm tra Brevo sender/key/quota; không log OTP, key hoặc raw response chứa dữ liệu riêng.
- Session mất sau deploy: đăng nhập lại; không thay Auth để bỏ kiểm tra.

Khởi tạo local xem [database](../../database/README.md); nâng cấp production là thao tác DBA riêng cần backup và phê duyệt, không thuộc cleanup source.
