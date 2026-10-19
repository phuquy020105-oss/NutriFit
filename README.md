# NutriFit Java Web — Auth, Gemini Chatbot, Premium/VNPay

Dự án Java 21 / Maven WAR / Jakarta Servlet 6 / Tomcat 10.1 / MySQL 8.

- Auth: đăng ký OTP, đăng nhập, hồ sơ, Dashboard, admin.
- Chatbot: Gemini API, lịch sử hội thoại theo từng tài khoản, JSP trong `WEB-INF/views/chatbot`.
- Premium: ba thẻ Khám phá, 30 ngày, 365 ngày. Giá hai gói trả phí lấy từ MySQL.
- VNPay Sandbox: tạo giao dịch `PENDING`, chuyển hướng thanh toán, Return hiển thị, IPN xác minh chữ ký và cập nhật Premium có khóa giao dịch.

**Lưu ý:** Bản này hợp nhất mã từ bản Preview chạy local và snapshot nhánh `feature/java-payment-chatbot`. Chưa được kiểm thử E2E trên máy chủ, MySQL và merchant VNPay thực tế. Không đưa API key, mật khẩu vào repository.

**Hướng dẫn tích hợp**: xem [`docs/INTEGRATION.md`](docs/INTEGRATION.md). Xem thêm [`README-JAVA.md`](README-JAVA.md) về workflow nhánh `develop-java` của nhóm.

**Chuẩn bị triển khai cloud:** [Render Docker + Aiven MySQL TLS + Brevo HTTPS](docs/deployment/render-aiven-brevo.md). Nhánh `deploy/render-aiven-brevo` dùng Brevo cho OTP; giữ nguyên ứng dụng WAR tại `/nutrifit`.
