# Gmail OTP registration — NutriFit Studio

## Bảo mật và hành vi

- `POST /api/auth/register` gửi 6 chữ số qua Gmail, **chưa tạo Users**, trả HTTP `202` và `requires_otp: true`.
- `POST /api/auth/verify-otp` nhận `{ "email":"...@gmail.com", "otp":"123456" }`. Chỉ đúng mã mới tạo `Users` (role MEMBER) và phiên đăng nhập; trả HTTP `201`, `user`.
- `POST /api/auth/resend-otp` nhận `{ "email":"...@gmail.com" }`. Chỉ gửi lại khi có đăng ký chờ, sau tối thiểu 60 giây; mã cũ hết hiệu lực.
- OTP hết hạn sau 10 phút; tối đa 5 lần nhập sai/mã; tối đa 5 lần gửi/Gmail/giờ và 15 lần gửi/IP/giờ. Giới hạn lưu trong MySQL, không bị reset khi khởi động Flask.
- Mã OTP **không lưu dạng rõ**; dùng HMAC-SHA256 với `SECRET_KEY`. Mật khẩu người dùng được băm trước khi lưu trong bảng chờ. Email chỉ hỗ trợ `@gmail.com`.
- Trong môi trường development, không có nút tắt OTP hoặc mã thử nghiệm công khai. Cần cấu hình SMTP Gmail thực và Internet, không dùng `MAIL_SUPPRESS_SEND=true`.

## 1. Sao lưu database

Nếu `NutriFitDB` đã có dữ liệu, sao lưu trước bằng MySQL Workbench (Data Export). **KHÔNG** chạy lại `setup/create_database.sql`, vì script đó có DROP TABLE.

## 2. Đặt file .env tại NutriFit-NextUI/.env

```ini
NUTRIFIT_ENV=production
NUTRIFIT_DEMO_REGISTRATION=false
MAIL_SUPPRESS_SEND=false
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=NutriFitDB
DB_USER=root
DB_PASS=your_new_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_TIMEOUT=20
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_sender@gmail.com
MAIL_PASSWORD=your_new_app_password
MAIL_DEFAULT_SENDER=your_sender@gmail.com
SESSION_COOKIE_SECURE=false
NUTRITION_FRONTEND_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
```

Tạo `SECRET_KEY` mới đủ mạnh. Thay mật khẩu ứng dụng Gmail, khóa API và MySQL đã xuất hiện trong ảnh chụp hoặc tin nhắn trước đó. **Không chia sẻ file .env**.

## 3. Cài hai bảng OTP một lần, không xóa dữ liệu

Terminal CMD, nếu `.venv` nằm ở thư mục **cha** `NutriFit-Studio-Full-Project/.venv`:

```bat
cd NutriFit-NextUI
..\.venv\Scripts\python.exe setup\install_registration_otp.py
```

Nếu bạn đã mở Terminal ở thư mục `NutriFit-NextUI`, chỉ chạy dòng Python. Kết quả mong đợi:

```text
OK: RegistrationOTPs
OK: RegistrationOTPIPQuota
OTP migration complete. Existing accounts and health records untouched.
```

Cũng có thể dùng Workbench để chạy `setup/add_registration_otp.sql`, sau khi chọn schema `NutriFitDB`.

## 4. Chạy Backend & Frontend

Dừng tiến trình Flask cũ ở cổng 5000 rồi chạy:

```bat
..\.venv\Scripts\python.exe backend\wsgi.py
```

Trong Terminal mới (ở cùng thư mục project):

```bat
python -m http.server 5500
```

Mở `http://127.0.0.1:5500/frontend/index.html` và nhấn `Ctrl+Shift+R` để xóa cache JavaScript. Chọn Đăng ký -> nhập Gmail -> nhận OTP -> xác minh -> đăng nhập tự động.

## 5. Các lưu ý

- Gmail không tồn tại hoặc không thuộc quyền sở hữu người đăng ký sẽ **không kích hoạt được** tài khoản vì không nhận được OTP. SMTP báo gửi thành công **không** chứng tỏ Gmail tồn tại.
- Các tài khoản đã tạo trước khi nâng cấp **không tự động được xác minh**. Để buộc xác minh tài khoản cũ, cần quy trình chuyển đổi riêng.
- `frontend/legacy` giữ giao diện cũ để tham khảo, nhưng **form đăng ký cũ không có bước OTP**. Hãy dùng `frontend/index.html` để đăng ký mới. Đăng nhập bằng tài khoản đã xác minh vẫn dùng được.
- Không đặt `SECRET_KEY` mới sau khi đã gửi OTP, vì các mã chưa xác minh sẽ mất hiệu lực.
- Giới hạn IP dựa vào `request.remote_addr`. Khi triển khai sau reverse proxy cần cấu hình trusted proxies và bảo vệ rate-limit ở proxy; không tin header `X-Forwarded-For` trực tiếp.
