# NutriFit — bàn giao backend Nutrition, Meal và Gemini (TV3)

Phụ trách: Bùi Hải Đăng. Nhánh triển khai: `feature/nutrition-ai`.

## Phạm vi

- Nutrition: BMI/BMR/TDEE, calorie mục tiêu, nước và macro.
- Meal: 3 mâm cơm Việt cho trưa/tối; tạo, cache, chọn/nghĩ sau, refresh, lịch sử.
- Gemini: chọn mẫu thực đơn qua REST API ở backend; output được kiểm tra.
- Fallback: chu kỳ 7 ngày, 3 lựa chọn/bữa, 2 bữa/ngày = 42 mẫu.
- Summary: dinh dưỡng **dự kiến** từ các thực đơn đã chọn.
- Không thay đổi schema, không tự seed/drop/create bảng khi khởi động.

Frontend là phạm vi Khoa. Workout và Street Food là phạm vi Phát. Auth/profile/database core của Quý được tái sử dụng và chỉ sửa tại các điểm tích hợp được liệt kê bên dưới.

## Chạy local

Ví dụ thiết lập môi trường mới từ thư mục gốc dự án trên PowerShell. Nếu đã có `.venv`, kiểm tra môi trường trước khi cài; không dùng các lệnh này để tự thay đổi bộ dependency đang được nhóm kiểm thử.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\wsgi.py
```

Trên macOS/Linux dùng `.venv/bin/python` thay cho `.venv\Scripts\python.exe`.
`backend/requirements.txt` là danh sách dependency chung được bàn giao. Đã đối chiếu imports của backend: Flask, Flask-Cors, Flask-Mail, Flask-SQLAlchemy, SQLAlchemy, Werkzeug, itsdangerous, python-dotenv và requests đều có trong file này; PyMySQL và cryptography phục vụ kết nối MySQL cũng đã được khai báo. Gemini mới dùng REST qua requests, không cần thêm SDK riêng.

Việc đối chiếu xác nhận các dependency cần thiết đã được khai báo, chưa xác nhận khả năng cài đặt và chạy suite trên đúng toàn bộ phiên bản pin của requirements gốc. Môi trường local đã kiểm thử khác pin gốc ở SQLAlchemy, PyMySQL, cryptography, python-dotenv và pycparser. Cần kiểm thử lại trong môi trường tách biệt theo requirements chung trước khi xác nhận tương thích phiên bản đầy đủ.

Cấu hình `.env` ở gốc dự án hoặc `backend/.env`. Nếu cả hai tồn tại, backend ưu tiên `backend/.env`; biến môi trường có sẵn không bị dotenv ghi đè. Tham khảo `backend/.env.nutrition.example` và giữ lại các biến mail trong `.env.example` của Quý. Không ghi giá trị thật vào tài liệu/Git.

| Biến | Ý nghĩa |
|---|---|
| `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME` | Kết nối MySQL đã được nhóm thiết lập |
| `DATABASE_URL` | Nếu có, thay thế cấu hình `DB_*` |
| `SECRET_KEY` | Chuỗi ngẫu nhiên riêng của môi trường; cần ổn định giữa các lần chạy/workers |
| `ACCESS_TOKEN_MAX_AGE` | Thời hạn token; mặc định 3600 giây |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Cả hai để trống: chạy fallback, không gọi mạng |
| `GEMINI_TIMEOUT_SECONDS` | Mặc định 10, giới hạn runtime 1–30 giây/lần gọi |
| `GEMINI_MAX_RETRIES` | Mặc định 1, giới hạn runtime 0–2 lần retry |
| `GEMINI_COOLDOWN_SECONDS` | Mặc định 30 giây/user trong mỗi process |
| `NUTRIFIT_TIMEZONE` | `Asia/Ho_Chi_Minh` hoặc `Asia/Bangkok` (UTC+7), hoặc `UTC` |
| `CORS_ORIGINS` | Danh sách origin frontend, ngăn cách bằng dấu phẩy |

Không có `SECRET_KEY`: ứng dụng tạo key tạm trong process. Token mất hiệu lực khi đổi key; cấu hình nhiều workers phải dùng cùng key.

Database phải có schema hiện có do Quý thiết lập. Không chạy `setup/create_database.sql` lên database đang sử dụng: script gốc có lệnh DROP TABLE. Module TV3 không chạy script này.
Việc đăng ký mới vẫn dùng quy trình gửi mail của Quý và cần cấu hình SMTP; không bổ sung hệ thống xác minh email trong module TV3.

## Xác thực và lỗi

`POST /api/auth/login` và `/api/auth/register` giữ các field `success`, `message`, `user`, bổ sung `access_token`, `token_type: "Bearer"`, `expires_in`.

Mọi API Meal, Nutrition cá nhân và profile yêu cầu:

```text
Authorization: Bearer <access_token>
```

`POST /api/nutrition/calculate` là calculator không ghi dữ liệu, không cần token.
Các field `userId`/`user_id` cũ được chấp nhận nếu đúng user trong token; ID khác trả 403. Header `X-User-Id` không xác thực được các API này.
Token có chữ ký và hạn dùng; không phải JWT. Chưa có refresh token, danh sách thu hồi token hoặc logout server. Không dùng ID/token giả từ demo offline để gọi API dữ liệu thật.

Lỗi JSON có dạng:

```json
{"success": false, "code": "INVALID_INPUT", "message": "Thông tin lỗi an toàn."}
```

| HTTP | Trường hợp |
|---|---|
| 400 | JSON/field/giới hạn không hợp lệ, thiếu revision, key được gửi từ client |
| 401 | Thiếu, giả mạo, hết hạn token hoặc tài khoản đã bị xóa |
| 403 | ID không thuộc người đăng nhập |
| 404 | Thiếu profile hoặc chưa có suggestion |
| 409 | Refresh thực đơn đã chốt hoặc revision đã cũ |
| 413 | Body vượt 64 KiB |
| 503 | Lỗi database hoặc dữ liệu/cấu hình module không hợp lệ |

## Nutrition API

### POST /api/nutrition/calculate

Request:

```json
{"gender":"male","age":22,"height":172,"weight":65,"activity_level":1.375,"goal":"maintain"}
```

Các field bắt buộc; `activity` là alias của `activity_level`. Các giới hạn phần mềm theo UI hiện có: tuổi nguyên 12–95, chiều cao 100–250 cm, cân nặng 30–250 kg; activity thuộc 1.2/1.375/1.55/1.725/1.9; gender male/female, goal lose/maintain/gain. Không nhận bool/NaN/infinity hay mục tiêu calorie không dương.

Kết quả nằm trong `data`: field hồ sơ chuẩn hóa, `bmi`, `bmr`, `tdee`, `target_kcal`, `target_water_ml`, `macros`, `target_carbs`, `target_protein`, `target_fat`, `target_fiber`, `meal_targets`, `calculation_version`, `estimated`.

Quy tắc phiên bản `nutrifit-v1`:

- BMI = kg / (cm/100)^2.
- BMR giữ Mifflin–St Jeor của Quý: 10w + 6.25h − 5a + 5 (male) / −161 (female).
- TDEE = BMR × activity; lose −500, gain +500, maintain giữ nguyên.
- BMR/TDEE/target làm tròn 1 số lẻ; nước giữ `int(weight × 35)`.
- Macro: carb 45%/4, protein 25%/4, fat 30%/9; làm tròn 1 số lẻ.
- Fiber dùng quy tắc sản phẩm hiện có của frontend: weight × 0.45.
- Phân bổ calorie dự kiến: sáng 25%, trưa 40%, tối 30%, phụ 5%.

Đây là quy tắc tính và ước tính của sản phẩm; chưa phải chính sách dinh dưỡng được chuyên gia phê duyệt. Khoảng tuổi là validation kế thừa UI, không chứng minh công thức phù hợp mọi lứa tuổi/tình trạng sức khỏe.

### GET /api/nutrition/me

Tính lại từ profile hiện tại, không tin các target cũ được seed hoặc gửi từ browser. Không ghi lại các target cũ vào DB chỉ vì GET.

### GET /api/nutrition/summary

`data` có `targets`, `planned: {calories,carbs,protein,fat,fiber}`, `selected_meals`, `remaining_planned_kcal`, `tracking_mode: "planned"`.
Chỉ cộng option đã chọn của trưa/tối hôm nay. Không tính options đang pending và không cộng lượng tập luyện vào calorie ăn. Số còn lại có thể âm nếu kế hoạch vượt mục tiêu.
Schema chưa lưu nhật ký thực sự ăn; không gắn nhãn `consumed` cho các số này. Chưa ghi nhật ký nước hoặc triển khai bữa sáng/bữa phụ.

## Profile integration

- Giữ `/save` và `/<user_id>`; bổ sung `/api/profile/save` và `/api/profile/<user_id>`.
- Các route yêu cầu Bearer token; ID được kiểm tra quyền sở hữu.
- POST nhận `user_id` hoặc `userId`, `activity_level` hoặc `activity`; ID có thể bỏ khi dùng token.
- Response giữ các field trước đây và bổ sung BMI/macro/activity.
- `ProfileService.calculate_metrics()` vẫn trả tuple 4 phần tử để code Quý tương thích.
- BMI/macro được tính lúc đọc; không thêm cột database.

## Meal API

### GET /api/meals/today

```json
{"success":true,"todayMeals":{"lunch":null,"dinner":null},"date":"YYYY-MM-DD"}
```

Nếu có thực đơn, `lunch`/`dinner` là Meal DTO được mô tả bên dưới.

### POST /api/meals/generate

```json
{"mealType":"lunch","forceRefresh":false}
```

Chấp nhận các alias `meal_type`, `force_refresh`. Bữa được hỗ trợ: lunch/dinner. Profile là điều kiện tạo mới. Nếu đã có thực đơn, generate thường trả lại nguyên options và selection mà không gọi Gemini.

Refresh pending cần `revision` từ DTO vừa tải:

```json
{"mealType":"lunch","forceRefresh":true,"revision":"<24-character-revision>"}
```

Response `{success,data,meta}`; meta có `cached`, `source`, và khi tạo mới có `target_kcal`; fallback có `fallback_reason` là mã an toàn. `source`: gemini/fallback/seed/mixed. Không trả body lỗi hoặc credential provider.

### Meal DTO

```text
suggestionId, date, mealType, selectedOption (1/2/3/null), status (pending/decided),
revision (24 ký tự), source, estimated, options[3]
```

Mỗi option có `id` (số thứ tự), `optionId` (PK), `title`, `calories`, `macros: {carbs,protein,fat,fiber}`, `carb`, `protein`, `soup`, `veggie`, `dessert`, `digestibility`, `nutritionNotes`, `estimated`.
Các field món giữ hình dạng Khoa đang render; mẫu mới ghi lượng gram ước tính trong tên món.

### POST /api/meals/select

```json
{"mealType":"lunch","selectedOption":2,"revision":"<24-character-revision>"}
```

Có thể bổ sung `suggestionId` và `optionId` để kiểm tra lựa chọn cụ thể. Alias snake_case được hỗ trợ. `selectedOption:null` là Nghĩ sau: đặt pending, giữ nguyên ba options.
Thiếu `selectedOption` là lỗi; không được ngầm chuyển thành Nghĩ sau.

Revision bắt buộc giúp ngăn tab cũ chọn nhầm options sau refresh. Khi 409, tải lại today. Backend khóa parent user, kiểm tra lại revision/trạng thái trong transaction và rollback khi có lỗi. Trước transaction ghi, bỏ snapshot đọc cũ để phù hợp MySQL REPEATABLE READ.
Refresh decided trả 409. Có thể chọn Nghĩ sau rồi refresh; đây là hành động bỏ lựa chọn trước đó trong cùng ngày. Schema chỉ lưu trạng thái mới nhất của mỗi ngày/bữa, chưa có lịch sử mọi lần click/refresh.

### GET /api/meals/history?page=1&limit=20

Response `{success,history,pagination:{page,limit,total}}`; limit 1–100. Sắp ngày và ID giảm dần, giới hạn đến ngày hiện tại. Mỗi bản ghi có `chosenMeal` hoặc null cùng options được lưu.

## Gemini và dữ liệu mẫu

Adapter dùng endpoint `models.generateContent` của Gemini REST API qua `requests`. Không import SDK `google-generativeai` cũ trong module mới.
Chọn model đang khả dụng cho tài khoản bằng `GEMINI_MODEL`; không hardcode vòng đời model.
Prompt chỉ chứa loại bữa, calorie mục tiêu và danh sách template; không gửi ID/email/mật khẩu/profile chi tiết.

AI trả JSON có 3 `template_id` khác nhau và lý do ngắn; mỗi lựa chọn thuộc một nhóm đạm khác nhau. Backend kiểm tra ID, số lượng, nhóm, độ dài, control characters và HTML. AI không cung cấp calorie/macro, không tự tạo món ngoài catalog.
HTTP timeout, output lỗi, thiếu key/model, quota, provider 4xx/5xx hoặc cooldown đều dùng fallback.
Provider requests gửi key qua header phía server, không qua URL hay browser; không log exception/body nhạy cảm.

Fallback có 7 ngày × 3 lựa chọn × 2 loại bữa. Mỗi mâm đủ CARB/PROTEIN/SOUP/VEGGIE/DESSERT. Ước tính macro từ template rồi scale khẩu phần trong khoảng 0.5–2 lần; calorie tính lại từ 4C+4P+9F. Vì giới hạn khẩu phần, calorie thực đơn có thể lệch mục tiêu cực thấp/cao. Không sửa giá trị dinh dưỡng thật của StreetFoodDish.
Số liệu mẫu chưa được kiểm chứng bằng cơ sở dữ liệu thực phẩm/chuyên gia. `DishCatalogId` để null cho component mẫu vì catalog hiện tại thiếu khẩu phần/macro và seed có tên chưa khớp; không tạo liên kết sai.
Nguồn gemini/fallback được giữ trong cột text `DigestibilityNote` bằng prefix; JSON bỏ prefix khi hiển thị. Không có cột metadata AI mới.
Cooldown là trong từng process, chưa phải rate limiter phân tán; multi-worker cần thống nhất hạ tầng nếu yêu cầu hạn mức toàn hệ thống.

## Bàn giao cho Khoa

1. Lưu `access_token` từ login/register; thêm Authorization ở API client trước khi gọi profile/meals.
2. Dùng BMI/target/macros/activity backend trả về; bỏ công thức tăng cân +350 và giá trị macro mặc định không tương ứng.
3. `normalizeProfile()` và session restore cần hỗ trợ các field mới thống nhất, tránh trộn PascalCase/camelCase/snake_case.
4. Khi select/Nghĩ sau/refresh, gửi revision của meal hiện tại; khi 409 tải lại today.
5. Bỏ prompt/localStorage Gemini key và field key thực từ request. Key cấu hình phía server.
6. Dùng summary để hiển thị kế hoạch ăn; escape/textContent cho nội dung dữ liệu/AI.
7. Frontend nhánh hiện tại còn rỗng; code Khoa ở origin/feature/frontend-ui chưa được checkout/cherry-pick trong phần việc TV3 này.

## Bàn giao cho Quý và Phát

Quý review 5 file có sửa: app factory, config, auth routes, profile routes và profile service. Auth service, user/profile models, schema, seed và setup/run được giữ nguyên. Config bỏ credential trong source, dùng Config/DB_* và SECRET_KEY. Profile tính qua Nutrition service; route canonical được đăng ký thêm.
Admin RBAC dựa trên X-User-Id của code cũ chưa được chuyển sang token trong phạm vi TV3; không coi đây là hoàn thiện bảo mật toàn hệ thống. `wsgi.py` vẫn chạy debug theo code Quý, chỉ dùng cách chạy trên cho local, cần cấu hình production riêng.
Phát giữ workout/progress/street-food. Đăng cung cấp meal_targets; không sửa file nhánh Phát hay cộng lặp calorie tiêu hao vào TDEE.

## Kiểm thử và bằng chứng

Chạy unittest trực tiếp từ thư mục `backend` trên PowerShell (nếu đang ở thư mục gốc, chạy `cd backend` trước):

```powershell
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

Trên macOS/Linux, từ thư mục `backend`, dùng `../.venv/bin/python -B -m unittest discover -s tests -p 'test_*.py' -v`.

`-B` ngăn ghi bytecode. Lệnh unittest hiển thị kết quả trong terminal, không xuất file kết quả hoặc báo cáo cá nhân. Suite dùng SQLite in-memory với DDL dịch từ 14 bảng gốc, bật foreign keys; không chạm MySQL thật. Gemini được mock HTTP. Fixtures mail suppress và sender thử nghiệm, không gửi mail thật.
Bao phủ công thức nam/nữ/mục tiêu, validation, auth/expired/ownership, tương thích profile, generate/cache, 42 mẫu/chu kỳ, select/pending, refresh/stale, history/summary, rollback khi insert lỗi, quota/timeout/output lỗi và CORS/body limit.

Suite hiện có 55 test methods: 10 unit tests Nutrition, 9 tests Gemini với HTTP mock và 36 integration tests Flask/SQLite có mock. Xem tổng số tests, failures, errors và skipped trong terminal của mỗi lần chạy; kết quả local không thay thế kiểm thử trên requirements chung hoặc các dịch vụ thật.

Chưa kiểm chứng MySQL thật (đặc biệt concurrent multi-process/locking), Gemini thật, SMTP thật hoặc frontend end-to-end. Những bước này cần cấu hình tài khoản/database và tích hợp các nhánh của nhóm; không có credential thật trong report.

Nguồn giao thức: https://ai.google.dev/api/generate-content và https://ai.google.dev/gemini-api/docs/structured-output.
