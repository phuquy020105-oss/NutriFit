# Báo cáo rà soát source NutriFit

**Nguồn:** GitHub chính `feature/java-payment-chatbot` (ZIP 22 entries), Source local Auth/Chatbot/VNPay (ZIP 115 entries); đối chiếu tham khảo bản `feature/java-auth-profile` đã có trong cuộc trò chuyện.

**Đầu ra:** 85 file trong một dự án Maven Java 21, không có `.git`, `target`, backup `.bak` hoặc mã nguồn demo thanh toán trong WAR.

- Tệp giữ nguyên so với branch gốc: **6**.
- Tệp có thay đổi so với branch gốc: **4** (.gitignore, README-JAVA.md, README.md, pom.xml).
- Tệp được bổ sung: **75**.
- Trong số file trùng tên với nhánh Auth đã tải, **41/46** giữ nguyên byte-for-byte; phần còn khác là AuthFilter và Dashboard, cần review khi nhóm hợp nhất.

## Kiểm tra đã thực hiện trong môi trường tạo artifact

- Biên dịch **nhóm Java lõi** Payment/Chat/DAO/Model/Gemini bằng JDK 21: **PASS** (không cần servlet/mail/BCrypt).
- URL VNPay Sandbox, số tiền nhân 100, kiểm tra HMAC-SHA512 hợp lệ và từ chối số tiền bị sửa: **PASS**, chỉ dùng secret giả lập, không gọi VNPay.
- Cú pháp JavaScript `chat-modern.js` bằng `node --check`: **PASS**.
- Đếm thẻ `CREATE TABLE`: **23**; file schema gốc không bị sửa.
- Kiểm tra số dấu JSP `<%` và `%>`: **đều khớp**. Đây là kiểm tra cơ bản, không thay được Jasper/JSP compilation.
- **Chưa có Maven và thư viện Servlet/Jakarta Mail/MySQL đầy đủ trong môi trường tạo ZIP**: chưa chạy được `mvn clean verify`, không thể cam kết WAR build thành công trên máy khác.
- **Chưa kiểm thử thực tế** MySQL, OTP qua Gmail, Gemini API, VNPay merchant, Return và IPN trên Tomcat: người nhận phải kiểm thử E2E.

## Rủi ro khi merge

1. Auth/Admin đến từ bản local và phần lớn trùng `feature/java-auth-profile`, nhưng nhánh chính có thể đã cập nhật thêm. Hãy giữ code Auth nhóm làm nền khi tạo PR, không ghi đè tùy tiện.
2. `auth_version` dùng trong `UserDAO`, `AuthFilter`; database có sẵn phải áp dụng migration tương ứng; đối chiếu chữ hoa/thường tên DB khi chuyển từ Windows sang Linux.
3. Bảng `subscriptionplans` không tự có dữ liệu; seed gói 30/365 ngày nằm trong script optional và giá chỉ để kiểm thử.
4. VNPay sẽ không chuyển hướng nếu chưa có TMN Code, Hash Secret và Return URL; Return không cấp quyền Premium, cần IPN HTTPS đăng ký merchant.
5. README-JAVA gốc chỉ mô tả cấu trúc Java và nói Java tích hợp theo **`develop-java`**, không dùng `main` nếu nhóm chưa quyết định khác.
6. ZIP sạch được xuất không có `.git`: hãy gắn vào lịch sử nhánh GitHub chính trước khi commit, không push lịch sử Git tự tạo ở repo phụ.

## Đường dẫn trọng yếu

- Auth: `src/main/java/com/nutrifit/controller/{AuthServlet,RegisterServlet,VerifyOTPServlet}.java`
- Chat: `src/main/java/com/nutrifit/controller/ChatServlet.java`, `service/GeminiClient.java`, `service/ChatService.java`, hai DAO hội thoại và `WEB-INF/views/chatbot/chat.jsp`
- VNPay: `controller/{PaymentServlet,VnpayIpnServlet,VnpayReturnServlet}.java`, `service/{PaymentService,VnpayService,PremiumAccessService}.java`, DAO tương ứng, `WEB-INF/views/payment/{plans,result}.jsp`
- UI: `WEB-INF/views/dashboard/dashboard.jsp`, `assets/css/{chat-modern,payment-modern}.css`, `assets/js/chat-modern.js`
- DB: `database/schema.sql`, `database/migrations/...auth_version.sql`, `database/seeds/optional-premium-plans.sql`.

## File giữ nguyên từ nhánh nền
- `database/schema.sql`
- `src/main/java/com/nutrifit/config/DatabaseConfig.java`
- `src/main/java/com/nutrifit/controller/DatabaseHealthServlet.java`
- `src/main/java/com/nutrifit/controller/HealthServlet.java`
- `src/main/webapp/assets/css/style.css`
- `src/main/webapp/index.jsp`

## File có thay đổi từ nhánh nền
- `.gitignore`
- `README-JAVA.md`
- `README.md`
- `pom.xml`