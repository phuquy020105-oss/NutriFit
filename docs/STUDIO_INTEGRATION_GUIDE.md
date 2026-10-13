# NutriFit Studio: hướng dẫn phát triển tiếp

## Phạm vi

UI mới hoạt động tại `frontend/index.html`, bản gốc tại `frontend/legacy/index.html`. Khi cần cải tiến mô-đun có logic phức tạp, tham khảo mã tại `frontend/legacy/js/*.js` và giữ nguyên hợp đồng Backend trong `frontend/js/studio.js`.

## Những API đang dùng

- Sức khỏe Backend: `GET /api/health`
- Đăng ký, đăng nhập: `POST /api/auth/register`, `POST /api/auth/login`
- Hồ sơ: `GET /<user_id>`, `POST /save`
- Dinh dưỡng: `POST /api/nutrition/calculate`, `GET /api/nutrition/daily`, `GET /api/nutrition/summary`
- Thực đơn: `GET /api/meals/today`, `POST /api/meals/generate`, `POST /api/meals/select`, `GET /api/meals/history`
- Workout: `GET /api/workouts/catalog`, `POST /api/workouts/custom`, `POST /api/workouts/log`, `GET /api/workouts/logs`, `DELETE /api/workouts/log/<id>`
- Tiến độ: `GET /api/progress/weekly/<user_id>`
- Món Việt: `GET /api/street-food`, `POST /api/street-food/recommend`
- Quick Food: `GET /api/nutrition/quick-food/search`, `POST /api/nutrition/quick-food/preview`, `POST /api/nutrition/quick-food/confirm`
- AI: `POST /api/chatbot/chat`, optional `profile`
- Premium, admin: `/api/payment/*`, `/api/admin/*`

## Điểm cần chú ý

1. NutriFit dùng nhiều nguồn xác thực legacy. `/api/meals/*` và `/api/nutrition/*` dùng session cookie của Flask. `auth.login` thiết lập session ở `backend/app/nutrition_module.py`.
2. `premium` và `admin` đang dùng header `X-User-Id` theo backend tích hợp. Header client **không đủ là một cơ chế xác thực an toàn cho production**; trước khi triển khai internet, cần thay bằng authorization server-side dựa vào session và phân quyền.
3. Không tự động tạo/check-out thanh toán khi người dùng mới xem trang Premium; chỉ gọi endpoint sau khi nhấn nút, đăng nhập và xác nhận.
4. Quick Food yêu cầu `confirmed:true`, món hợp lệ và `requestId` ổn định qua retry để tránh ghi trùng. UI giữ `quickPending` nếu server chưa xác nhận. Trong trạng thái không chắc chắn, kiểm tra nhật ký trước khi gửi lại.
5. Không thể kiểm tra Gemini và MySQL thật nếu chưa có `.env`/DB phù hợp. Không đưa API key và thông tin ngân hàng vào JS hoặc ZIP.
6. Nếu thay đổi schema, đối chiếu migration sẵn có, chạy trên database sạch riêng trước, không chạy trực tiếp trên NutriFitDB của người dùng.

## Việc nên làm ở giai đoạn tiếp theo

- Chuyển màn hình chỉnh sửa từng thành phần V4 và báo cáo nhật ký chi tiết từ legacy sang thiết kế mới.
- Chuẩn hóa phân quyền Admin/Payment bằng Flask signed session thay cho header tự khai báo, bổ sung CSRF protection cho các thao tác thay đổi dữ liệu.
- Thêm browser E2E tests với database test mới, fixture tài khoản Premium và Gemini mock.
- Nếu triển khai public, dùng production WSGI server, HTTPS, cookie Secure, rate-limit chat và chính sách an toàn nội dung sức khỏe.
