# NutriFit — Quản lý dinh dưỡng và luyện tập

Đồ án Lập trình Web dùng **Java 21, Maven WAR, Jakarta Servlet 6/JSP, Tomcat 10.1 và MySQL 8.4**. Ứng dụng triển khai tại context `/nutrifit`.

## Chức năng

- Đăng ký/khôi phục mật khẩu bằng OTP qua Brevo, đăng nhập và quản lý hồ sơ.
- Onboarding tính mục tiêu calories; Dashboard tổng hợp tiến trình.
- Nutrition: catalog **100 nguyên liệu, 60 món, 607 liên kết**, mỗi bữa 20 món và 60 ảnh. Gợi ý ba bữa, một suất chuẩn mỗi món; đổi thực đơn hoặc riêng từng món; lưu nhật ký và xem lịch sử.
- Free gợi ý theo mục tiêu calories; Premium thêm LIKE/DISLIKE nguyên liệu. Nhật ký cũ giữ snapshot dinh dưỡng; lịch sử chỉ liệt kê ngày có món.
- Bài tập, lộ trình và nhật ký luyện tập; Gemini Chatbot có lịch sử theo tài khoản.
- Gói Premium và thanh toán **VNPay Sandbox**; quyền Admin độc lập với gói thuê bao.

Số liệu dinh dưỡng là **ước tính tham khảo**, không phải dữ liệu y khoa. Nguồn, phương pháp và độ tin cậy nằm trong [provenance](database/seed/provenance.json); ảnh món ăn là minh họa AI.

## Chạy local trên Windows

Cần JDK21, Maven3.9, MySQL8.4 và Tomcat10.1. Các lệnh chạy từ thư mục clone; thay đường dẫn JDK/Tomcat bằng bản đã cài trên máy:

```powershell
git clone --branch deploy/render-aiven-brevo https://github.com/phuquy020105-oss/NutriFit.git
cd NutriFit
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot'
$env:PATH="$env:JAVA_HOME\bin;C:\tools\apache-maven-3.9.16\bin;$env:PATH"
$env:CATALINA_HOME='C:\tools\apache-tomcat-10.1.61'
$env:TOMCAT_HOME=$env:CATALINA_HOME
Copy-Item .env.example .env
```

Tự điền cấu hình vào `.env` bằng trình soạn thảo, không gửi mật khẩu qua chat/Git. Để `NUTRIFIT_DB_URL` và `NUTRIFIT_DB_CA_FILE` trống khi dùng MySQL local mặc định `nutrifitdb_java`. Điền `NUTRIFIT_DB_USER`, `NUTRIFIT_DB_PASSWORD`; cấu hình Brevo để gửi OTP, Gemini để chat và VNPay Sandbox để thanh toán. Không có tài khoản demo hoặc mật khẩu mặc định.

```powershell
mvn -DargLine=-Xmx768m clean package
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Init
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Run
```

`Init` chỉ dùng database local rỗng; không tạo lại database có bảng. Nó tạo 24 bảng và dữ liệu mẫu, không tạo người dùng. Schema chỉ định nghĩa bảng; công cụ tự nạp lần lượt Workout, gói Premium mẫu và catalog Nutrition từ `database/seed/`. Nếu database local đã được khởi tạo đúng phiên bản này, dùng `-Action Verify`, không chạy `Init` lại. Xem [database/README.md](database/README.md) trước khi nâng cấp một database đã có dữ liệu. `.env` chỉ được wrapper PowerShell nạp; Java/Tomcat tự chạy không tự đọc file đó.

Mở `http://localhost:8080/nutrifit/register`, đăng ký bằng email nhận OTP rồi hoàn tất onboarding. Không chạy hai Tomcat cùng cổng. Công cụ local chỉ copy WAR vào Tomcat được chỉ định; không sửa cấu hình Tomcat hoặc database cloud.

## Kiểm thử

```powershell
mvn -DargLine=-Xmx768m clean package
python scripts/verify_repository.py
python scripts/verify_web.py --jdk "$env:JAVA_HOME" --tomcat "$env:TOMCAT_HOME" --chrome 'C:\Program Files\Google\Chrome\Application\chrome.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Test -Database nutrifit_catalog_test
git diff --check
```

Test DB cần MySQL loopback và database test **chưa có bảng**; không dùng database chính/Aiven. `-Action Test` kiểm tra seed, rollback, conflict, idempotency và không tạo tài khoản. Database test được giữ lại để xem kết quả, không tự xóa. Test JSP thật cần `TOMCAT_HOME`, nếu thiếu sẽ báo SKIP. JavaScript fixtures chạy bằng Chrome headless. Verifier tự tải Ant qua Maven nếu thiếu lần đầu để biên dịch JSP; không thêm thư viện vào ứng dụng. Maven không gửi OTP, gọi Gemini hoặc thực hiện giao dịch thanh toán thật.

## Cấu trúc

```text
src/main/java/com/nutrifit/  controller, filter, service, dao, dto, model, util, config
src/main/webapp/            JSP, CSS, JavaScript và assets
src/test/                  unit/regression tests và browser fixtures
database/                  schema hoàn chỉnh 24 bảng và seed 60 món duy nhất
scripts/                   chạy local và kiểm tra repository/JSP/JS
docker/                    Tomcat, entrypoint và ROOT redirect
docs/                      kiến trúc và hướng dẫn triển khai
```

[Kiến trúc và quy tắc chức năng](docs/architecture.md) · [Database](database/README.md) · [Deploy Render/Aiven/Brevo](docs/deployment/render-aiven-brevo.md).

Không commit `.env`, certificate, backup hoặc `target/`. Docker không chứa secret, không seed khi khởi động. Khi chạy Docker, `/` trả HTTP302 đến `/nutrifit/register`; health tại `/nutrifit/health` báo revision đã deploy.
