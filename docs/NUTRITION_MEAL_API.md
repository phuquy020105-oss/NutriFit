# Nutrition, Meal và Gemini AI v2 — NutriFit

Nhánh: feature/nutrition-ai-v2. Nền: origin/main tại f71c939.
Tái sử dụng chọn lọc Nutrition từ 257f938. Không thay schema/models hoặc nghiệp vụ Auth/Profile.

## Kiến trúc

- Quý sở hữu AuthService, ProfileService, BMR/TDEE/TargetKcal và dữ liệu profile.
- Nutrition thêm BMI, macro và phân bổ mục tiêu bữa ăn.
- Meal dùng các bảng MealSuggestions, MealOption, MealNutrition, MealComponentDish hiện có.
- Gemini chọn 3 template có sẵn; không tự tạo con số dinh dưỡng.
- Fallback có 42 mẫu Việt: 7 ngày × 3 lựa chọn × 2 bữa trưa/tối.
- app/__init__.py chỉ thêm import và lời gọi init_nutrition(app).
- nutrition_module.py đăng ký blueprint, cấu hình riêng module và kết nối session với login core.

## Chạy backend

Từ thư mục gốc, dùng môi trường đã cài dependencies chung:

```powershell
.\.venv\Scripts\python.exe backend\wsgi.py
```

Nếu chưa có môi trường, tạo/cài riêng theo backend/requirements.txt:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Các dependencies runtime đã khai báo trong requirements chung; module gọi Gemini bằng requests, không yêu cầu SDK mới.
Suite được kiểm thử trên .venv hiện có; chưa xác nhận tất cả phiên bản pin gốc trong môi trường mới.

Core ưu tiên backend/.env, sau đó .env ở gốc. Dùng DATABASE_URL của database đã thiết lập.
Không chạy setup/create_database.sql trên dữ liệu đang sử dụng: script có DROP TABLE.
Module không seed, migrate hoặc tạo bảng khi khởi động.

Tham khảo backend/.env.nutrition.example, giữ cấu hình DATABASE_URL và SMTP hiện có của Quý.
Đăng ký thật vẫn gửi mail theo AuthService; cần SMTP hợp lệ.
Không đưa .env hoặc giá trị secret vào Git/frontend.

## Đăng nhập và session demo

POST /api/auth/login và /api/auth/register giữ nguyên JSON của Quý:
success, message, user. Không thêm access_token, không dùng JWT hoặc Bearer riêng.

Sau response thành công từ core, backend đặt cookie session có chữ ký, HttpOnly.
API cá nhân dùng session này và kiểm tra tài khoản vẫn tồn tại.
userId/user_id trong payload/query chỉ dùng đối chiếu quyền, không chứng minh danh tính.
Header X-User-Id hoặc Bearer giả không đăng nhập được Nutrition/Meal.

Frontend cần credentials: "include" trên login và các request tiếp theo:

```javascript
await fetch(baseUrl + "/api/auth/login", {
  method: "POST",
  credentials: "include",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({email, password})
});
const response = await fetch(baseUrl + "/api/nutrition/me", {
  credentials: "include"
});
```

Dùng cùng hostname (localhost hoặc 127.0.0.1) cho frontend/backend.
Cookie SameSite=Lax phù hợp demo local cùng site, khác port.
NUTRITION_FRONTEND_ORIGINS khai báo chính xác origin được phép dùng cookie.
Các request ghi Nutrition/Meal có Origin ngoài danh sách trả 403.
CORS có credentials chỉ được thêm cho origin trong danh sách, trên Auth/Profile/Nutrition/Meal liên quan.
Không đổi cấu hình CORS toàn ứng dụng hoặc cơ chế Admin hiện có.

POST /api/nutrition/logout xóa cookie session trên browser.
SECRET_KEY ổn định giúp giữ session sau restart. Nếu bỏ trống, dùng khóa ngẫu nhiên trong process;
restart làm mất phiên, nhiều worker không chia sẻ khóa. Phù hợp chạy demo một process.
Logout không thu hồi bản sao cookie ở phía server; chưa có cơ chế production về thu hồi phiên/CSRF token.
Core Profile và Admin vẫn giữ giới hạn xác thực hiện có; module không tuyên bố đã bảo vệ toàn core.

## API Nutrition

| Method | URL | Session | Chức năng |
|---|---|---|---|
| POST | /api/nutrition/calculate | Không | Calculator không lưu dữ liệu |
| GET | /api/nutrition/me | Có | BMI/macro từ profile và chỉ số đã lưu |
| GET | /api/nutrition/summary | Có | Tổng dinh dưỡng kế hoạch từ các bữa đã chọn |
| POST | /api/nutrition/logout | Có | Xóa cookie session |

Calculator nhận JSON:

```json
{"gender":"male","age":22,"height":172,"weight":65,"activity_level":"LIGHT","goal":"giam_can"}
```

Các field bắt buộc như ví dụ. activity là alias của activity_level.
Activity tên mức dùng ProfileService.ACTIVITY_MULTIPLIERS, chuỗi số/số được hỗ trợ;
giá trị không đổi được sang số dùng fallback 1.375 theo core.
Calculator từ chối số không hữu hạn và dữ liệu ngoài giới hạn đầu vào của module.
Goal theo core: lose/weight_loss/giam_can giảm 500; gain/weight_gain/tang_can tăng 500;
goal khác giữ TDEE. Không đổi cách lưu/validation profile của core.

Kết quả trong data gồm dữ liệu đầu vào, bmi, bmr, tdee, target_kcal,
target_water_ml, macros, target_carbs, target_protein, target_fat, target_fiber,
meal_targets, calculation_version và estimated.

BMR/TDEE/TargetKcal/nước của calculator gọi trực tiếp ProfileService.calculate_metrics().
GET /me đọc Bmr/Tdee/TargetKcal/TargetWaterMl đã lưu, không tính lại hoặc ghi đè.
Profile thiếu trả PROFILE_REQUIRED (404); chỉ số thiếu/không hợp lệ trả PROFILE_INCOMPLETE (400).
Ví dụ TargetKcal đã lưu = 2000 => carbs 225 g, protein 125 g, fat 66.7 g.
Macro: carbs/protein/fat = 45%/25%/30%, quy đổi 4/4/9 kcal mỗi gram.
Phân bổ breakfast/lunch/dinner/snack = 25%/40%/30%/5%.
Fiber mục tiêu ước tính = weight × 0.45. Không thêm cột BMI/macro vào database.

Profile vẫn dùng POST /save với user_id, activity_level; GET /<user_id>.
Không thêm alias /api/profile/* hoặc thay response profile để chứa BMI/macro.
Frontend lấy dữ liệu bổ sung qua Nutrition API sau khi lưu profile.

## API Meal

Tất cả yêu cầu session.

| Method | URL | Chức năng |
|---|---|---|
| GET | /api/meals/today | Hai bữa hôm nay; chưa có thì null |
| POST | /api/meals/generate | Tạo/cache/làm mới 3 lựa chọn |
| POST | /api/meals/select | Chọn hoặc Nghĩ sau |
| GET | /api/meals/history?page=1&limit=20 | Lịch sử có phân trang |

Generate:

```json
{"mealType":"lunch","forceRefresh":false}
```

Chỉ hỗ trợ lunch/dinner. forceRefresh mặc định false; alias meal_type/force_refresh được hỗ trợ.
Nếu đã có, generate thường trả nguyên options/selection từ DB, không gọi AI.
Refresh gửi forceRefresh=true và revision hiện tại. Bữa đã decided không được refresh;
chọn Nghĩ sau trước. Revision cũ trả STALE_MEAL (409).

Select:

```json
{"mealType":"lunch","selectedOption":1,"revision":"<revision nhận từ server>"}
```

selectedOption là 1..3, hoặc null để Nghĩ sau. Alias selected_option được hỗ trợ.
Có thể gửi suggestionId/optionId để đối chiếu; không dùng chúng làm danh tính.
Response generate/select: success, data; generate có meta.
data gồm suggestionId, date, mealType, selectedOption, status, options, revision, source, estimated.
Mỗi option gồm id, optionId, title, calories, macros và carb/protein/soup/veggie/dessert,
digestibility, nutritionNotes, estimated.
today trả success, todayMeals, date. history trả success, history, pagination.

Summary trả data với targets, planned, selected_meals, remaining_planned_kcal,
date, tracking_mode="planned", estimated=true.
Chỉ cộng các option đã chọn; không coi đây là lượng ăn thực tế.
Không cộng calorie Workout lần nữa vào TDEE.

Repository dùng parameterized SQL, unique key user/date/meal, khóa parent User và kiểm tra revision.
Mỗi request Meal sở hữu transaction của nó; không gộp ghi profile vào cùng transaction Meal.
Trước AI/khóa ghi, đóng transaction chỉ đọc; nếu có ORM edits chưa lưu thì báo TRANSACTION_CONFLICT.
Refresh lỗi rollback và giữ lựa chọn cũ.
Source được lưu bằng prefix [gemini]/[fallback] trong DigestibilityNote hiện có.

## Gemini và fallback

Chỉ backend đọc GEMINI_API_KEY. Model do GEMINI_MODEL cấu hình.
Prompt chỉ chứa mục tiêu bữa và template, không gửi user ID/email/profile chi tiết.
Thiếu key/model, HTTP lỗi, timeout hoặc output không hợp lệ đều dùng fallback.
Timeout/retry/cooldown được giới hạn; cooldown chỉ trong từng process.
Output phải có đúng 3 template hợp lệ thuộc 3 nhóm đạm; không lấy macro do AI sinh.
Số dinh dưỡng là ước tính từ template. Khẩu phần scale giới hạn 0.5..2,
nên calorie thực đơn có thể không khớp tuyệt đối mục tiêu cực thấp/cao.
GEMINI_API_KEY do client gửi bị từ chối; không cần đặt key trên frontend.

## Lỗi

JSON lỗi Nutrition/Meal: {"success":false,"code":"...","message":"..."}.
400: input/profile chưa hợp lệ; 401: thiếu/hỏng/hết hạn session; 403: sai user/origin;
404: thiếu profile/meal; 409: stale/decided/transaction; 413: JSON body trên 64 KiB;
503: database/menu/timezone không hợp lệ.
Giới hạn body chỉ ở endpoint module đọc JSON, không đổi MAX_CONTENT_LENGTH toàn core.
Auth/Profile giữ format lỗi và nghiệp vụ core; không áp dụng error wrapper của Nutrition lên core.

## Kiểm thử

Từ thư mục backend:

```powershell
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

Suite gọi app factory thật của Quý với DATABASE_URL=sqlite:///:memory:
được đặt trước db.init_app. Chỉ chạy CREATE TABLE đã dịch từ schema trong SQLite in-memory.
Không chạy DROP, seed/migration hoặc đụng MySQL thật.
HTTP Gemini mock; mail.send mock; không gửi SMTP thật. -B không tạo bytecode.
Bao phủ calculator/core aliases, stored targets, login session/ownership/logout,
core profile contract, registered routes, Meal transactions/cache/revision/history/summary,
fallback và provider failures.
SQLite không xác minh khóa/cạnh tranh MySQL. Chưa kiểm thử Gemini/SMTP/frontend thực tế.
Không dùng kết quả unit/integration này để tuyên bố toàn hệ thống production đã an toàn.
