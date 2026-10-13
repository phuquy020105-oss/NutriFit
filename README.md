> **CẬP NHẬT ĐĂNG KÝ OTP:** NutriFit Studio yêu cầu mã OTP gửi Gmail trước khi tạo tài khoản. Cần chạy migration tạo bảng OTP trên DB hiện có; xem **[Hướng dẫn Gmail OTP](docs/GMAIL_OTP_SETUP.md)**.

# NutriFit Studio — giao diện mới tích hợp 6 nhánh

**Ngôn ngữ:** Tiếng Việt · **Frontend:** HTML + CSS + JavaScript thuần (không cần npm) · **Backend:** Python Flask · **Dữ liệu:** MySQL · **AI:** Gemini (tùy chọn)

NutriFit Studio cung cấp một giao diện dashboard hiện đại, responsive và đồng nhất cho hệ sinh thái NutriFit: quản lý tài khoản, hồ sơ dinh dưỡng, tạo thực đơn V4, luyện tập và tiến độ, món ăn Việt, Quick Food Premium, chatbot Gemini, quản trị và gói dịch vụ. Project xây dựng trên bản `NutriFit-feature-nutrifit-demo-integration-release`, ghép các tính năng chat nâng cao, đồng thời lưu **toàn bộ frontend tích hợp cũ** tại `frontend/legacy/` để tránh mất chức năng chuyên sâu.

> **Quan trọng:** Mở giao diện mới **không cần MySQL** để xem trước. Dữ liệu sức khỏe trong chế độ xem trước **chỉ minh họa**; chỉ lưu thật sau khi chạy Backend + Database và đăng nhập. Chức năng Premium, AI và thanh toán cần cấu hình và quyền tương ứng. Không chạy schema/migration/seed lên database đang có dữ liệu nếu chưa sao lưu và kiểm tra.

## 1. Chạy nhanh giao diện (không cần Backend)

Yêu cầu Python 3.10+ (chỉ để phục vụ file qua HTTP).

Tại thư mục chứa file này, chạy:

```powershell
python -m http.server 5500
```

Mở trình duyệt: **http://127.0.0.1:5500/frontend/index.html**

Với chế độ xem trước, bạn có thể di chuyển giữa các trang, xem dashboard và chỉ số minh họa, dùng máy tính năng lượng tại trình duyệt, tra cứu/lọc bộ dữ liệu 36 món Việt, xem bài tập, gói Premium và giao diện AI. Các ghi nhận thực tế (lưu thực đơn, nhật ký, chat Gemini, Quick Food, thanh toán) không bị giả lập là đã thành công khi server chưa kết nối.

## 2. Chạy đầy đủ Backend + Frontend trên Windows

1. Cài Python 3.10+ và MySQL tương thích, có kết nối mạng nếu cần Gemini.
2. Chạy `setup/setup_local.bat` hoặc tự cài thư viện:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r backend\requirements.txt
   ```

3. Sao chép `.env.example` thành `.env` **ở thư mục gốc** và điền cấu hình MySQL (`DB_*`) cùng `SECRET_KEY` đủ mạnh. `GEMINI_API_KEY` là tùy chọn cho AI. Không đưa `.env` lên Git.
4. Chuẩn bị một **database mới** theo mục 3 bên dưới. Nếu đã có NutriFitDB với dữ liệu, hãy đọc kỹ file `docs/DEMO_RELEASE_VERIFICATION.md` và **không chạy lại** `setup/create_database.sql` bừa bãi.
5. Nhấp đúp `run/run_all.bat`, hoặc dùng hai terminal:

   ```powershell
   # Terminal 1
   .venv\Scripts\python.exe backend\wsgi.py
   # Terminal 2
   python -m http.server 5500
   ```

6. Mở `http://127.0.0.1:5500/frontend/index.html`. Kiểm tra API `http://127.0.0.1:5000/api/health` trả về `status: connected`.

Linux/macOS: `sh run/run_all.sh` (sau khi cài requirements, tạo `.env` và chuẩn bị database).

**Đăng ký:** chỉ tạo tài khoản sau khi nhập đúng OTP trong Gmail, cả ở chế độ local. Xem docs/GMAIL_OTP_SETUP.md. Không bỏ qua xác minh email hoặc công khai server debug trên mạng. Script Flask trong bản Studio mặc định bind `127.0.0.1` và không bật debug; chỉ bật debug khi chủ động thiết lập `NUTRIFIT_FLASK_DEBUG=true`.

## 3. Khởi tạo DB mới cho demo — lưu ý an toàn

Bộ integration có công cụ riêng để khởi tạo DB mới (không được ghi đè):

```powershell
.venv\Scripts\python.exe setup\init_demo_test_database.py --database nutrifit_demo_clean_studio
.venv\Scripts\python.exe setup\init_demo_test_database.py --database nutrifit_demo_clean_studio --apply
```

Lệnh đầu kiểm tra, lệnh sau tạo mới; **không được chạy lên DB tồn tại**. Sau đó trỏ `DB_NAME=nutrifit_demo_clean_studio` trong `.env`. Bộ setup sẽ chuẩn bị schema, catalog món ăn và dữ liệu tham chiếu theo cách đã được quy định ở nhánh tích hợp. Các migration độc lập liên quan MET được lưu tham khảo ở `docs/WORKOUT_MET_OPTIONAL.sql` — **không chạy mặc định** vì có thể không tương thích với schema đang dùng.

## 4. Các trang trong Studio

| Trang | Chức năng | Chế độ dùng |
|---|---|---|
| Tổng quan | Cards chỉ số, biểu đồ hoạt động, bữa ăn, quick actions | Demo / dữ liệu thật khi đăng nhập |
| Dinh dưỡng | Calo, macro, BMI, BMR, TDEE, tính mục tiêu, nước uống, nhật ký | API `/api/nutrition/*`, máy tính offline có chú thích |
| Thực đơn AI | 3 gợi ý cho sáng/trưa/tối, chốt món, đổi món, lịch sử | Meal Planner V4 `/api/meals/*` |
| Luyện tập | Danh mục, lọc nhóm, tạo bài tập, nhật ký, xóa bản ghi, tiến độ tuần | `/api/workouts/*`, `/api/progress/*` |
| Món ăn Việt | 36 món mẫu, tìm kiếm, lọc ngân sách, phân tích, gợi ý | `frontend/data/street-food.json` / `/api/street-food/*` |
| Ghi nhanh Premium | Tìm món, chọn gram, preview, yêu cầu xác nhận đã ăn và ghi nhật ký | `/api/nutrition/quick-food/*`, Premium bắt buộc |
| Trợ lý AI | Chat nhiều lượt, câu hỏi gợi ý, prompt thông minh | `/api/chatbot/chat`, cấu hình Gemini |
| Hồ sơ | Đăng nhập/đăng ký, lưu chỉ số thể trạng, mục tiêu | `/api/auth/*`, `/save`, `/<user_id>` |
| Premium | Xem các gói và thanh toán thật khi đủ cấu hình | `/api/payment/*` |
| Quản trị | Tổng quan admin; giao diện gốc vẫn còn module quản trị đầy đủ | `/api/admin/*`, quyền ADMIN |

Các công cụ UI chuyên sâu hiện chưa chuyển hoàn toàn sang thiết kế mới như **chọn thay từng thành phần thực đơn**, **history/intake chỉnh sửa nâng cao**, **Workout MET estimator**, **quản trị danh sách/giao dịch chi tiết**... vẫn có thể truy cập ở `frontend/legacy/index.html`. Frontend gốc được lưu nguyên vẹn, không bị xóa.

## 5. Cấu trúc dự án

```text
NutriFit-NextUI/
├── frontend/
│   ├── index.html                 # NutriFit Studio (giao diện mới)
│   ├── assets/css/studio.css      # Design system responsive
│   ├── js/studio.js               # Client, state, SPA, API actions
│   ├── data/street-food.json      # Dữ liệu 36 món từ nhánh TV4
│   └── legacy/                   # Frontend tích hợp cũ (nguyên bản)
├── backend/
│   ├── app/                      # Flask + các blueprint/service/repository
│   ├── tests/                    # Bộ test tích hợp gốc
│   └── wsgi.py
├── setup/                        # Schema, migrations, seeds và test DB initializer
├── docs/                         # Tài liệu gốc + hướng dẫn Studio
├── run/                          # Scripts chạy Frontend/Backend
├── .env.example
└── README.md
```

## 6. Nguồn ghép sáu nhánh

- **backend-core-db**: hệ thống người dùng, đăng nhập, profile cơ bản, schema và admin.
- **frontend-ui**: bố cục cũ, hợp đồng API frontend ban đầu, dashboard/profile.
- **chatbox-ai**: service AI gồm prompt theo ý định, tính toán và hội thoại nhiều lượt.
- **chatbot-more-features**: nhánh bổ sung tính năng chatbot có nội dung khớp với chatbox-ai được cung cấp; sử dụng phiên bản service nâng cao.
- **workout-streetfood**: workout, progress, street food, nutrition, Food Catalog V4; giữ cả dữ liệu và tài liệu migration riêng.
- **nutrifit-demo-integration-release**: nền tích hợp nhiều API và tests; giữ nguyên tests, setup, docs và frontend legacy.

**Lưu ý về chatbot:** `backend/app/services/chatbot_service_original.py` giữ dịch vụ từ bản integration để đối chiếu. `chatbot_service.py` hiện là phiên bản nhiều tính năng hơn; route chat hỗ trợ truyền `profile` tùy chọn để AI tính toán theo dữ liệu cung cấp. Mọi truy cập Gemini thực tế do Backend thực hiện, không lưu khóa API tại Frontend.

## 7. Kiểm tra cơ bản

```powershell
node --check frontend\js\studio.js
python -m compileall -q backend
.venv\Scripts\python.exe -m pytest backend\tests -q
node frontend\legacy\tests\meal-integration.test.js
```

Việc pass unit test không chứng minh MySQL/Gemini/SMTP/bank thật sẵn sàng; cần test end-to-end trong môi trường đã cấu hình. UI cũng không tạo phiên thanh toán và không ghi nhật ký trong chế độ demo.

## 8. Lưu ý thiết kế

- Không cần bundler/npm, dễ học và sửa HTML/CSS/JS.
- CSS màu xanh trầm, kem, bạc hà; sidebar riêng, thẻ thống kê, biểu đồ, form, modal và layout responsive.
- Không dùng ảnh bên ngoài để giao diện chạy ổn định offline; icon SVG nội tuyến và emoji minh họa.
- Client fetch dùng cookie (`credentials: include`) với các route bảo vệ bởi session; admin/payment vẫn cần `X-User-Id` theo API backend gốc (cần củng cố kiểm soát quyền ở backend trước khi triển khai công khai).
- `frontend/data/street-food.json` là **bộ dữ liệu minh họa lấy từ dữ liệu nguồn trong ZIP**, không phải thông tin dinh dưỡng hay mức giá được kiểm chứng ngoài thực tế.
- Nút ghi nhận/checkout yêu cầu xác nhận và phản hồi thành công từ server trước khi thông báo thành công.

Đọc thêm `docs/STUDIO_INTEGRATION_GUIDE.md` để điều chỉnh các module và tiếp tục phát triển giao diện.
