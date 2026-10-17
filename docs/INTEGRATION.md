# Hướng dẫn tích hợp NutriFit — nhánh Java

## Nguồn và phạm vi

- Nền: `NutriFit-feature-java-payment-chatbot.zip` (GitHub chính; khung MVC và schema gốc).
- Source mở rộng: `NutriFit-Local-Full-Source.zip` (bản Preview có Auth, Chat, Premium, Dashboard).
- Đối chiếu thêm `feature/java-auth-profile` đã cung cấp trong cuộc trò chuyện: phần Auth gần như trùng bản local, khác chủ yếu ở `AuthFilter` và giao diện Dashboard. **Không được ghi đè tự động code Auth sau khi nhóm merge bản mới.**

## Các chỉnh sửa trong bản sạch

1. Chỉ còn các thư mục Maven MVC tiêu chuẩn, bỏ `target`, `.git`, backup, JSP `.bak`.
2. Thay adapter `PaymentChatDb` bằng `DatabaseConfig.getConnection()` dùng chung; không tạo MySQL connection thứ hai.
3. Bỏ JS/CSS checkout giả lập và chế độ `NUTRIFIT_PAYMENT_DEMO`: tính năng thanh toán chỉ chạy nếu có cấu hình VNPay Sandbox hợp lệ.
4. Giữ UI ba thẻ Premium, nút ở Dashboard, Gemini chat và bảo vệ lịch sử hội thoại theo tài khoản.
5. Giữ nguyên schema 23 bảng và migration `users.auth_version`; bổ sung seed Premium **tùy chọn**, không tự chạy.
6. Sửa chuỗi Unicode lỗi trong liên kết Premium của Chatbot và `.gitignore` cho backup.

## Triển khai Windows / Tomcat

1. **Sao lưu** thư mục source đang dùng và các thay đổi Git trước khi thay. Không đè `src` của nhánh nhóm trực tiếp nếu chưa xem diff.
2. Chọn nhánh `feature/java-payment-chatbot` từ **lịch sử GitHub chính**; không push commit từ lịch sử Git `baitap3` sang nhánh này. README nhóm xác nhận `develop-java` là nhánh Java tích hợp, không phải `main`.
3. Dùng nội dung ZIP này làm bản nguồn để so sánh, chọn file cần giữ; `git status`, `git diff` rồi mới commit. Nếu nhóm đã merge Auth/Admin mới, ưu tiên giữ Auth/Admin hiện hành và chỉ ghép Payment/Chatbot vào các file dùng chung.
4. Cần MySQL schema gốc; với DB đã tồn tại chỉ chạy `database/migrations/20261017_add_users_auth_version.sql` **nếu cột chưa có** (script idempotent). Script `database/seeds/optional-premium-plans.sql` chỉ khi muốn gói ví dụ và đã xác nhận giá.
5. Trong Terminal PowerShell chạy Tomcat, cấu hình `NUTRIFIT_DB_USER`, `NUTRIFIT_DB_PASSWORD`, `NUTRIFIT_SMTP_USER`, `NUTRIFIT_SMTP_PASSWORD`, `NUTRIFIT_IP_HASH_SECRET`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET`, `VNPAY_RETURN_URL` bằng biến môi trường (tham khảo `.env.example`, không commit giá trị thật).
6. Chạy `mvn clean verify`, dừng Tomcat cũ, triển khai `target/nutrifit.war`, chạy `catalina.bat run`. Kiểm tra `/nutrifit/health`, `/nutrifit/health/db`, `/nutrifit/login`, `/nutrifit/dashboard`, `/nutrifit/chatbot`, `/nutrifit/payment`.
7. Test chức năng đăng ký OTP, đăng nhập, nhiều người dùng và đổi tài khoản xem chat; test giao dịch VNPay 30/365 ngày, Return, IPN và các tình huống sai chữ ký/sai số tiền/trùng IPN. **Không kích hoạt Premium khi chỉ có Return URL**.

## Ràng buộc khi merge

- GitHub chính `phuquy020105-oss/NutriFit`, nhánh feature `feature/java-payment-chatbot`. Đẩy thay đổi lên nhánh feature cùng lịch sử, tạo PR vào `develop-java` sau khi nhóm xác nhận.
- Không dùng `git push --force`, `git reset --hard` hoặc `git merge --allow-unrelated-histories` để nối lịch sử repo phụ.
- Backend Tomcat không chạy nguyên file WAR trên Vercel; IPN của VNPay cần URL HTTPS công khai và đăng ký với merchant.
- Thành công của Maven không chứng minh SMTP, Gemini, MySQL hay VNPay đã được kiểm thử E2E.

## Đưa source sạch vào đúng lịch sử GitHub chính mà không clone thư mục mới

**Chỉ thực hiện khi bạn đã sao lưu source cũ bằng ZIP, làm sạch thay đổi chưa commit và có quyền push vào nhánh đích.** Không làm với project khác của nhóm đang mở.

```powershell
# Trong Terminal PowerShell đang ở thư mục source hiện tại
$project = (Get-Location).Path
$zip = "$HOME\Downloads\NutriFit-Integrated-Clean.zip"
git status --short
git remote -v
```

Nếu `git status --short` có thay đổi chưa lưu, dừng lại và commit hoặc sao lưu trước. Nếu Git repo local có lịch sử độc lập với GitHub nhóm, **không push trực tiếp HEAD cũ lên nhánh nhóm**.

```powershell
git remote add official https://github.com/phuquy020105-oss/NutriFit.git
# Nếu 'official' đã tồn tại, chỉ kiểm tra bằng git remote -v, không thêm lại
git fetch official feature/java-payment-chatbot
git switch -c feature/java-payment-chatbot --track official/feature/java-payment-chatbot
```

Nếu Git báo đã có nhánh, có file chưa commit hoặc xung đột khi switch, **dừng và đối chiếu** thay vì dùng `--force`. Sau khi chuyển nhánh thành công, vẫn ở **chính thư mục dự án này**, nạp nội dung ZIP sạch (ZIP không chứa thư mục `.git`):

```powershell
Expand-Archive -LiteralPath $zip -DestinationPath $project -Force
git status --short
git diff --check
mvn clean verify
```

Chỉ khi build thành công, diff đã được review, không có token/mật khẩu:

```powershell
git add src database pom.xml .gitignore README.md README-JAVA.md .env.example docs
git diff --cached --stat
git diff --cached --check
git commit -m "feat: integrate auth chatbot premium vnpay"
git push official HEAD:feature/java-payment-chatbot
```

**Phải xem lại các thay đổi Auth, Admin, Dashboard và `pom.xml` trước khi push** vì nhóm có nhánh riêng quản lý những phần này. Nếu nhánh feature ở xa đã có commit mới, cần fetch/review lại trước khi đẩy. Sau đó tạo PR vào `develop-java` (theo hướng dẫn nhóm).
