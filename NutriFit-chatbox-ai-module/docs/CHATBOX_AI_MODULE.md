# NutriFit AI Chatbox — Module riêng

Gói này chỉ chứa Chatbox AI và các phụ thuộc trực tiếp. Không chứa toàn bộ dự án, database schema, `.env` thật, `.venv`, `.git` hay API key.

## File trong module

- `frontend/assets/css/chatbox.css`: kiểu dáng widget chat nổi.
- `frontend/js/chatbox.js`: mở/đóng khung chat, lịch sử phiên, gợi ý câu hỏi, gửi request dạng streaming và hiển thị lỗi.
- `backend/app/routes/chatbot.py`: endpoint `POST /api/chatbot/chat`, hỗ trợ JSON thường và Server-Sent Events.
- `backend/app/services/chatbot_service.py`: system prompt, gọi Gemini, streaming và ánh xạ lỗi thành thông báo an toàn.
- `backend/app/ai/api_key_pool.py`: đọc tối đa 10 key duy nhất từ biến môi trường, phân loại lỗi key không hợp lệ.
- `backend/tests/test_api_key_pool.py`: test cho bộ đọc key và phân loại lỗi.
- `integration-snippets/`: các đoạn cần thêm vào `frontend/index.html` và `backend/app/__init__.py`, tránh phải ghi đè các file chung.

## Cách tích hợp vào project NutriFit đang có

1. Sao lưu dự án trước khi sửa.
2. Sao chép các file trong `frontend/` và `backend/app/` của gói vào các đường dẫn tương ứng trong dự án đang dùng. Chỉ chép các file đã liệt kê; không thay `frontend/index.html`, `backend/app/__init__.py`, `backend/app/config.py` hay toàn bộ `requirements.txt` bằng file khác.
3. Mở `frontend/index.html`: thêm `frontend-head.html` vào trong `<head>` và thêm `frontend-before-body-end.html` một lần ngay trước `</body>`. Kiểm tra trước nếu các dòng đó đã có.
4. Mở `backend/app/__init__.py`: đăng ký `chatbot_bp` trong `create_app()` như `backend-blueprint-registration.py`. Kiểm tra trước để tránh đăng ký blueprint hai lần.
5. Giữ cơ chế cấu hình hiện tại của ứng dụng. `backend/app/config.py` cần nạp file `.env` từ thư mục gốc (như bản NutriFit tích hợp hiện tại).
6. Mở file `.env` thật trên máy rồi thêm/chỉnh các biến trong `.env.ai.example`; không ghi đè toàn bộ `.env`, không điền key trong JavaScript hay commit lên GitHub.
7. Nếu thiếu thư viện, cài các dòng cần thiết trong `backend/requirements-chatbox-additions.txt` vào `.venv` hiện tại. Không cài một môi trường mới trừ khi cần thiết.
8. Khởi động lại Backend và tải lại Frontend bằng Ctrl+Shift+R.

## API contract

- URL mặc định của Frontend: `http://127.0.0.1:5000/api/chatbot/chat`.
- Request JSON: `{"message":"...", "history":[], "stream":true}`.
- `stream: true`: trả `text/event-stream` gồm các event `chunk`, `done` hoặc `error`.
- `stream: false` hoặc bỏ trường `stream`: trả JSON `{ "success": true, "reply": "..." }`.

`chatbox.js` cho phép đặt `window.NUTRIFIT_API_BASE_URL` trước khi script nạp; nếu không đặt thì dùng `http://127.0.0.1:5000`.

## Gemini keys và hạn mức

- `GEMINI_API_KEY` là key chính; `GEMINI_API_KEYS` là danh sách phụ, phân tách bằng dấu phẩy, chấm phẩy hoặc newline. Tổng cộng tối đa 10 key duy nhất.
- Tự chuyển key chỉ khi lỗi xác thực cho thấy key bị từ chối rõ ràng và chưa có nội dung stream nào được gửi.
- `429 RESOURCE_EXHAUSTED`/quota không làm xoay key. Nhiều key trong cùng project không làm tăng quota project.
- Lỗi UI có thể tổng quát; đọc log Backend để phân biệt quota, key bị chặn và lỗi kết nối. Không ghi log API key.

## Kiểm tra cơ bản

Từ thư mục `backend`, chạy test helper:

```bat
..\.venv\Scripts\python.exe -m unittest discover -s tests -p test_api_key_pool.py
```

Kiểm tra cú pháp frontend:

```bat
node --check frontend\js\chatbox.js
```

Lệnh Node phải chạy từ thư mục gốc project. Test live cần Gemini key hợp lệ và không được coi là đã chạy nếu chưa tự thực hiện.

## Bảo mật

Không chia sẻ hoặc commit `.env`. Nếu key đã lộ, thu hồi key đó và tạo key mới. Đây là chatbox tư vấn tổng quát; không dùng thay thế chuyên gia y tế.
