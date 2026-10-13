# NutriFit Studio — Build report

- Tạo dự án từ `NutriFit-feature-nutrifit-demo-integration-release` làm nền backend/test/setup; bảo toàn frontend cũ dưới `frontend/legacy/`.
- Đưa AI service nâng cao từ `NutriFit-feature-chatbox-ai` và `NutriFit-feature-chatbot-more-features` vào service chính (service integration cũ được lưu riêng).
- Xuất dữ liệu 36 món đường phố từ danh sách Python của TV4 sang JSON cho xem trước offline.
- Kiểm tra syntax JS bằng Node 22 (`node --check`): **đạt**.
- Kiểm tra syntax Python (`python -m compileall`): **đạt**.
- Thực thi lại bộ unit test UI cũ `node frontend/legacy/tests/meal-integration.test.js`: **55/55 đạt**.
- Smoke test 9 trang Studio bằng Chromium + script mô phỏng API không kết nối thật: **9/9 mở được, không có pageerror**; tìm thấy **36** food cards trong bộ lọc mặc định.
- Kiểm tra giao diện desktop và mobile qua ảnh preview.

**Chưa kiểm thử trong môi trường này:** luồng chạy Flask thật, đăng nhập có MySQL thật, kho món trong MySQL và quyền Premium, đầu ra từ Gemini API, SMTP và checkout/VietQR. Các kiểm thử này cần cấu hình `.env` riêng, database kiểm thử và dịch vụ tương ứng. Việc giao diện hiển thị dữ liệu demo không phải bằng chứng các dịch vụ đang kết nối.
