# Deploy NutriFit: Render Docker + Aiven MySQL + Brevo HTTPS

Áp dụng cho `deploy/render-aiven-brevo`, nền `e0413d9`, Java 21 / Maven WAR / Tomcat 10.1. JSP và Servlet chạy chung tại `/nutrifit`. Đây là hướng dẫn thao tác sau khi chủ dự án review và cho phép push/deploy; nhiệm vụ chuẩn bị source **chưa chạy build, test hoặc deploy**.

## 1. Chuẩn bị và tạo Render Web Service

1. Review `git status`, `git diff`, `git diff --check`, xác nhận không có secret. Khi được phép, build/test riêng trước khi commit/push đúng nhánh `deploy/render-aiven-brevo`. Không đổi sang nhánh integration hoặc force-push.
2. Trên Render: **New → Web Service**, kết nối GitHub `phuquy020105-oss/NutriFit`, chọn branch trên, root repository và runtime **Docker**. Chọn **Free** nếu tài khoản/khu vực cho phép. Dockerfile path: `./Dockerfile`; giữ Docker command mặc định để dùng entrypoint.
3. Nhập environment variables ở bảng dưới, tạo Secret File CA trước lần deploy được duyệt. Chọn health check **`/nutrifit/health`** và `PORT=8080`. Không dùng `/` hoặc `/health`; WAR được triển khai tại `/nutrifit`.
4. Docker build dùng `maven:3.9.16-eclipse-temurin-21`, chạy `package` với `-Dmaven.test.skip=true` (không biên dịch/chạy tests), lấy đúng `target/nutrifit.war`. Runtime là `tomcat:10.1.61-jdk21-temurin-noble`, user không có quyền root.
5. Entrypoint kiểm tra PORT rồi truyền `-Dnutrifit.http.port=...`; `docker/server.xml` đọc system property đó, lắng nghe **0.0.0.0:PORT**. `EXPOSE 8080` là metadata, không thay thế PORT. Entrypoint `exec catalina.sh run`; Java chạy foreground và nhận SIGTERM để Tomcat dừng qua JVM shutdown hook.

Không có migration/seed lúc build hoặc khởi động. Image chỉ nhận `pom.xml`, `src/main`, cấu hình Docker; `.dockerignore` dùng allowlist để không mang `.git`, `.env`, CA/keystore, SQL/dump, backup, IDE, log hoặc `target` cũ vào build context. Không dùng `COPY . .` hoặc Docker build arguments chứa secret. Kiểm tra lại tag/digest base image khi cập nhật; các image này chưa được pull/build trong nhiệm vụ chuẩn bị.

Runtime dùng `USER nutrifit` (UID 10001, primary GID 10001), thêm supplementary GID 1000 để đọc Render Secret Files như `/etc/secrets/ca.pem`. Dockerfile kiểm tra GID 1000 đã tồn tại trước khi tạo group, rồi thêm user vào group đó; không chỉ định `USER user:group` vì Docker sẽ bỏ qua supplementary groups. Giữ ownership thư mục Tomcat và cơ chế truststore tạm; không chmod Secret File, không copy CA vào image hoặc chạy runtime bằng root. Tham khảo [Render runtime Secret Files](https://render.com/docs/docker-secrets#accessing-secret-files-at-runtime) và [Docker USER](https://docs.docker.com/reference/dockerfile/#user). Quyền đọc thực tế trên Render chưa được kiểm chứng vì chưa build/run/deploy.

## 2. Environment variables

Đặt **giá trị thật chỉ trên Render Dashboard**. `.env.example` là mẫu; Java/Tomcat không tự đọc `.env`. Khi chạy Windows, đặt biến trong đúng process IDE/Tomcat. `.env`, CA, keystore và backup phải tiếp tục nằm ngoài Git.

| Biến | Giá trị hoặc vai trò |
|---|---|
| `PORT` | `8080`; bắt buộc đúng cổng Render chuyển tiếp, mặc định image cũng là 8080. |
| `NUTRIFIT_DB_URL` | Trên Render bắt buộc: `jdbc:mysql://<AIVEN_HOST>:27047/nutrifitdb?sslMode=VERIFY_IDENTITY&useUnicode=true&characterEncoding=UTF-8`. Dùng hostname DNS đúng certificate; không nhúng user/password trong URL. |
| `NUTRIFIT_DB_USER` | `avnadmin` cho service hiện tại hoặc DB user được cấp phù hợp. |
| `NUTRIFIT_DB_PASSWORD` | Password tương ứng, không đặt giá trị trong source/README. |
| `NUTRIFIT_DB_CA_FILE` | Trên Aiven đặt `/etc/secrets/ca.pem`; yêu cầu file CA hợp lệ, đọc được. |
| `BREVO_API_KEY` | Transactional Email API key; không dùng SMTP key. |
| `BREVO_SENDER_EMAIL` | Địa chỉ sender đã xác minh trong Brevo. |
| `BREVO_SENDER_NAME` | Tùy chọn, mặc định `NutriFit`. |
| `NUTRIFIT_IP_HASH_SECRET` | Secret riêng, đủ ngẫu nhiên và ổn định để HMAC quota IP của Auth. Không dùng chung API key hoặc VNPay secret. |
| `GEMINI_API_KEY` | Bắt buộc khi dùng Chatbot. |
| `GEMINI_MODEL` | Tùy chọn, mặc định hiện tại `gemini-3.8-flash`. Không đặt rỗng. |
| `VNPAY_TMN_CODE` | Merchant Sandbox hiện có, cần khi thanh toán. |
| `VNPAY_HASH_SECRET` | Hash secret Sandbox tương ứng. |
| `VNPAY_RETURN_URL` | Sau khi Render cấp domain: `https://<RENDER_DOMAIN>/nutrifit/payment/return`. |

`CATALINA_OPTS` là tùy chọn quản trị JVM, không phải secret ứng dụng. Image đặt heap theo giới hạn container và timezone `Asia/Ho_Chi_Minh`; nếu ghi đè biến này phải chủ động giữ cấu hình phù hợp bộ nhớ/timezone. Entrypoint luôn bổ sung property PORT cuối cùng. `CATALINA_HOME` do base image cung cấp; không cần đặt lại. Không đặt `javax.net.ssl.trustStore*` toàn JVM cho riêng Aiven.

## 3. Aiven và CA certificate

- Bật service nếu **Powered off**, xác nhận MySQL 8.4.x, hostname, port 27047 và database `nutrifitdb` thực tế trong Aiven Console. Không dùng credential local `root` trên cloud.
- Đã xác nhận tên file local là `D:\Web\ca.pem` bằng danh sách file, chưa đọc/kiểm tra nội dung certificate. Lấy project CA đúng service từ Aiven Console. Trong Render → Environment → **Secret Files**, tên file **`ca.pem`**, dán nội dung PEM lấy từ file CA đúng. Runtime mount là `/etc/secrets/ca.pem`. Không copy chứng chỉ từ Windows vào repo/image và không tải certificate khi khởi động.
- `DatabaseConfig` giữ nguyên JDBC URL local nếu `NUTRIFIT_DB_URL` thiếu/rỗng. Với URL được cấu hình, code yêu cầu MySQL single-host URL và `sslMode=VERIFY_IDENTITY`; nếu chưa ghi mode thì áp dụng qua Connector/J Properties. Cấu hình hạ TLS, embedded credentials hoặc ghi đè truststore trong URL bị từ chối. Lỗi TLS không chuyển về plaintext hay URL local.
- `DatabaseTrustStore` đọc PEM CA ở lần JDBC đầu tiên, kiểm tra X.509/CA/thời hạn, tạo PKCS12 tạm với password ngẫu nhiên trong bộ nhớ. File Linux có quyền owner read/write; Connector/J nhận URL/type/password truststore riêng và `fallbackToSystemTrustStore=false`. Cache trong process, đổi CA cần restart/redeploy. Không thay đổi truststore HTTPS mặc định: Brevo/Gemini vẫn dùng CA công cộng của JDK.
- Thiếu/sai CA khi đã cấu hình phải sửa file/mount; không dùng `trustAll`, `allowPublicKeyRetrieval=true`, `sslMode=PREFERRED`, `REQUIRED` hoặc tắt hostname verification để chữa lỗi.

**Schema Aiven chưa được xác nhận.** Database local có 24 bảng không có nghĩa `nutrifitdb` đã có dữ liệu. Cần một nhiệm vụ DBA riêng được cho phép để đối chiếu và nhập schema/seed sạch: 24 bảng, `users.auth_version`, `password_reset_otps`, catalog 82/30/383, Workout 3/47 và các gói đã duyệt. `schema.sql`/migration có `CREATE DATABASE`/`USE NutriFitDB_Java`; seed chính thức có guard `_test`. Không chạy nguyên các file đó hoặc `nutrifit_full.sql` lên `nutrifitdb`, không bỏ guard, không nhập dữ liệu cá nhân từ dump. Container không tự chuẩn bị database.

Sau deploy, `/nutrifit/health/db` phải trả `connected`, database `nutrifitdb`. Endpoint chỉ chứng minh kết nối và `SELECT DATABASE()`, **không** chứng minh đủ schema/dữ liệu/TLS bằng kiểm thử E2E; TLS policy nằm trong cấu hình JDBC. `/nutrifit/health` không phụ thuộc database.

## 4. Brevo và contract Auth

Xác minh sender trong Brevo và cấu hình API key + sender variables trên Render. EmailService dùng Java HttpClient gửi JSON UTF-8 tới `POST https://api.brevo.com/v3/smtp/email`, header `api-key`, connect timeout 10 giây, request timeout 20 giây, không theo redirects. Chấp nhận **HTTP 201**; các status khác thành `MessagingException` có mã HTTP, không giữ response body. IOException được chuyển thành thông báo chung; InterruptedException khôi phục interrupt flag. Không retry tự động, không SMTP fallback, không gửi email khi startup.

Giữ nguyên `sendRegistrationOtp(String,String)` và `sendPasswordResetOtp(String,String)` với `throws MessagingException`. Jakarta Mail dependency hiện có vẫn dùng cho exception/address validation, không còn dùng để gửi SMTP. Không sửa RegistrationService/PasswordResetService: tạo/hash OTP, hạn 5 phút, quota, attempts, verify, transaction và rollback giữ nguyên. Auth owner cần review transport mới và thử E2E; email 201 là provider nhận yêu cầu, không đảm bảo inbox đã nhận, và email bên ngoài không thể rollback cùng MySQL.

## 5. HTTPS, session, Gemini và VNPay

Render kết thúc HTTPS ở edge rồi chuyển HTTP nội bộ đến Tomcat. Chỉ dùng Docker config này sau edge HTTPS: connector đặt cố định `scheme=https`, `secure=true`, `proxyPort=443`, không hardcode domain. Redirect theo context path có metadata HTTPS; session cookie được Tomcat xử lý theo secure request. Không thêm RemoteIpValve hoặc tin tùy ý `X-Forwarded-*`. Local Tomcat ngoài Docker giữ nguyên cấu hình cũ; chạy image trực tiếp bằng HTTP không phù hợp login/cookie Secure.

Địa chỉ `request.getRemoteAddr()` vẫn có thể là proxy Render. Quota IP của Auth vì thế có thể gộp nhiều người dùng vào cùng một IP; chưa sửa Auth hoặc giả định dải proxy. Trước production cần xác minh chuỗi ingress và cấu hình proxy tin cậy chính xác nếu cần, không dùng regex chấp nhận mọi client. Nguồn không có upload/file bắt buộc lưu lâu dài; chưa cần persistent disk. Session và filesystem container có thể mất khi restart/cold start, người dùng cần đăng nhập lại. Kiểm tra timezone DB/session và JVM trong E2E để tránh lệch các mốc OTP/thanh toán.

Giữ nguyên GeminiClient, model mặc định `gemini-3.8-flash` và endpoint `v1beta/models/{model}:generateContent`. Model này có trong tài liệu chính thức tại thời điểm rà soát; quyền truy cập/quota của API key phải kiểm tra sau deploy. Không tự đổi model hoặc thuật toán VNPay.

- **Return URL:** `https://<RENDER_DOMAIN>/nutrifit/payment/return` là browser trở về để hiển thị kết quả, yêu cầu session; không cấp Premium.
- **IPN URL:** `https://<RENDER_DOMAIN>/nutrifit/payment/ipn` là callback server-to-server, xác minh chữ ký và giao dịch trước khi cập nhật Premium. Không tạo biến `VNPAY_IPN_URL` vì source không đọc biến đó.
- Sau khi có domain, cập nhật `VNPAY_RETURN_URL` trên Render **và** đăng ký callback Return/IPN đúng môi trường với VNPay. Chỉ đổi biến môi trường không đủ. Source hiện dùng VNPay **Sandbox**, không phải cấu hình payment production. Giữ nguyên HMAC, kiểm tra số tiền, locking, idempotency và authorization hiện có.

## 6. Kiểm tra sau deploy được phép

Mở lần lượt health, database health, login; tự tạo tài khoản hợp lệ qua Register OTP và thử resend/OTP sai/hết hạn; thử Forgot Password OTP. Sau đó kiểm tra Dashboard, Profile/Onboarding, Nutrition/catalog/preferences/history/recommendations, Workout, Gemini, Admin đúng quyền và VNPay Sandbox Return/IPN (bao gồm chữ ký/số tiền sai và IPN trùng). Xác nhận HTTPS redirect, cookie Secure/HttpOnly, session và logout. Không tạo fake login/session hoặc cấp Premium thủ công để né kiểm tra.

Các thao tác này **chưa thực hiện** trong giai đoạn chỉ sửa code. Không tuyên bố BUILD SUCCESS, gửi OTP thành công hay kết nối Aiven thành công trước khi có kết quả thực tế.

## 7. Troubleshooting

| Hiện tượng | Kiểm tra |
|---|---|
| Docker build failed | Đúng root/Dockerfile, base image/tag truy cập được, Maven repository/network, lỗi compile trong logs. Không thêm secret build arguments. |
| Render không thấy cổng | `PORT=8080` hoặc cổng hợp lệ, entrypoint không bị thay bởi Docker command; property trong server.xml, LF của script và runtime user. |
| HTTP 404 | Dùng `/nutrifit/...`, xác nhận WAR tên `nutrifit.war`; `/` không phải trang ứng dụng. |
| MySQL timeout | URL/host/port/nutrifitdb, Aiven Powered on, allowlist/network đúng; không fallback local. |
| TLS verification error | Secret File/read permission, PEM CA còn hạn, hostname khớp certificate; restart sau đổi CA. Không hạ TLS. |
| DB connected nhưng chức năng lỗi | Health không kiểm tra schema; đối chiếu đủ 24 bảng/column/catalog trong nhiệm vụ DBA riêng. |
| Brevo 401 | API key đúng loại/quyền, chưa bị thu hồi; không in key vào logs. |
| Brevo 403 | Quyền tài khoản, sender/domain và chính sách IP/security của Brevo. |
| Brevo 400 | Sender đã verify, địa chỉ nhận hợp lệ, cấu hình email/payload; xem chẩn đoán trong Brevo dashboard, không log OTP hoặc raw response. |
| Thiếu biến | Xem tên biến trong exception an toàn, đặt vào Render runtime environment và redeploy. `.env` local không tự được đọc. |
| Cold start / session mất | Render Free có thể sleep sau thời gian idle, request đầu chậm; đợi khởi động và đăng nhập lại. Xem giới hạn Free hiện hành. |
| Quota IP bị chia sẻ / sai thời hạn | Kiểm tra proxy ingress và timezone; không tự tin header client hay sửa Auth để né quota. |

## Tài liệu chính thức đã đối chiếu

- [Render Docker](https://render.com/docs/docker), [Web Service và PORT](https://render.com/docs/web-services), [Secret Files](https://render.com/docs/configure-environment-variables), [giới hạn Free/SMTP](https://render.com/docs/free).
- [Tomcat HTTP connector](https://tomcat.apache.org/tomcat-10.1-doc/config/http.html), [proxy support](https://tomcat.apache.org/tomcat-10.1-doc/proxy-howto.html), [Tomcat image](https://hub.docker.com/_/tomcat), [Maven image](https://hub.docker.com/_/maven).
- [Connector/J TLS/truststore properties](https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-security.html), [server authentication](https://dev.mysql.com/doc/connector-j/en/connector-j-server-authentication.html), [Aiven CA](https://aiven.io/docs/platform/concepts/tls-ssl-certificates).
- [Brevo send transactional email](https://developers.brevo.com/reference/send-transac-email), [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).
