# Nutrition, Meal và Gemini AI v3/v4 — NutriFit

Frontend chỉ hiển thị Meal Planner V4: recipe theo gram, thay một component và nhật ký đã ăn.
API legacy vẫn nhận plannerVersion=v3. V4 cần migration độc lập
[001_nutrition_v4.sql](../setup/migrations/001_nutrition_v4.sql), chỉ áp dụng sau
backup và phê duyệt theo [hướng dẫn migration](NUTRITION_V4_MIGRATION.md).
Phiên bản database-driven trên nhánh feature/nutrition-mysql-food-catalog cần thêm
[002_nutrition_food_catalog.sql](../setup/migrations/002_nutrition_food_catalog.sql)
và import seed theo [hướng dẫn catalog](NUTRITION_FOOD_CATALOG_MIGRATION.md).
Migration 002 đã được phê duyệt và áp dụng trên MySQL local ngày 2026-10-11:
18 bảng, 102 món và 63 template legacy. Database khác cần migration/seed trước khi chạy phiên bản này.
Chrome/MySQL đã PASS trước đợt tối ưu khẩu phần đa tiêu chí. Kết quả regression và
replay mới được ghi trong hướng dẫn catalog; không gọi lại Gemini thật khi replay.
Gemini alternatives thật PASS trong phiên migration.
Compose lần đầu HTTP 200 nhưng fallback vì invalid_output; không lưu raw output nên
chưa xác định được điều kiện cụ thể của lần đó. Sau đồng bộ prompt/schema với validator,
compose kiểm thử lại đúng một request: source=gemini, cached=false, ba lựa chọn lưu MySQL
và hiển thị sau F5. Xem phạm vi kiểm chứng trong hướng dẫn catalog.
Không chạy lại schema gốc và không tự tạo bảng khi Flask khởi động.

Nhánh v3: integration/frontend-nutrition, nền Nutrition v2 tại 6d21fe1.
Nhánh v2 được tạo từ origin/main tại f71c939; giữ nguyên nhánh tham chiếu.
Tái sử dụng chọn lọc Nutrition từ 257f938. Không thay schema/models hoặc nghiệp vụ Auth/Profile.

## Kiến trúc

- Quý sở hữu AuthService, ProfileService, BMR/TDEE/TargetKcal và dữ liệu profile.
- Nutrition thêm BMI, macro và phân bổ mục tiêu bữa ăn.
- Meal dùng các bảng MealSuggestions, MealOption, MealNutrition, MealComponentDish hiện có.
- V3: Gemini chọn 3 template có sẵn. V4: kết hợp ID món và gram trong catalog;
  backend kiểm tra rồi tính dinh dưỡng. Không dùng số kcal/macro do AI tự tạo.
- Có 63 mẫu Việt: 21 breakfast mới + 42 lunch/dinner cũ; một MealService dùng chung ba bữa.
- FoodCatalogRepository đọc NutritionFoodCatalog và NutritionLegacyMenus; food_catalog_service.py xử lý gram,
  tính dinh dưỡng và chuyển đổi template legacy. Runtime không đọc file seed hoặc danh sách Python hardcode.
- Ba module dữ liệu cũ được thay bằng seed riêng setup/seeds/nutrition_catalog.json:
  giữ 24 Dish ID/profile V4 và 63 template V3; bổ sung dữ liệu có nguồn, không ghi đè lịch sử.
- meal_preferences.py lọc trước cả Gemini/fallback và phân tích câu đổi món giới hạn.
- V3 không lưu preferences. V4 lưu preferences/focus cùng recipe trong bảng độc lập,
  không sửa UserProfiles, models hay công thức ProfileService.
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
| GET | /api/meals/today | breakfast/lunch/dinner hôm nay; chưa có thì null |
| POST | /api/meals/generate | Tạo/cache/làm mới 3 lựa chọn |
| POST | /api/meals/select | Chọn hoặc Nghĩ sau |
| POST | /api/meals/replace | Đổi bộ ba món theo yêu cầu giới hạn; bắt buộc revision |
| GET | /api/meals/history?page=1&limit=20 | Lịch sử có phân trang |

Generate:

```json
{"mealType":"lunch","forceRefresh":false}
```

Hỗ trợ breakfast/lunch/dinner; snack chưa có generate. forceRefresh mặc định false; alias meal_type/force_refresh được hỗ trợ.
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
Mỗi option gồm id, optionId, title, calories, macros, components (mảng {type,name}),
reason, digestibility, nutritionNotes, estimated.
Giữ carb/protein/soup/veggie/dessert cho các ComponentType cũ;
breakfast dùng MAIN/SIDE/DRINK và có thể DESSERT, không bị ép năm thành phần.
Repository giữ cả ComponentType chưa biết; không đổi cách tính revision.
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
Prompt chứa goal chuẩn hóa lose/gain/maintain, mục tiêu kcal/macro của bữa,
preferences đã kiểm tra và template hợp lệ (ID, tên, nhóm, nguyên liệu,
thời gian nếu có, kcal/macro ước tính sau scale khẩu phần).
Không gửi user ID/email/profile chi tiết hoặc câu đổi món thô lên Gemini.
User ID chỉ dùng nội bộ cho cooldown, không nằm trong payload HTTP.
Thiếu key/model, HTTP lỗi, timeout hoặc output không hợp lệ đều dùng fallback.
Timeout/retry/cooldown được giới hạn; cooldown chỉ trong từng process.
Output chỉ có choices gồm đúng 3 template_id khác nhau và reason tiếng Việt theo prompt;
không chấp nhận field dinh dưỡng do AI trả. Kiểm tra ở adapter và service.
Đủ ba nhóm: sáng quick/soup/balanced, trưa/tối ba nhóm đạm.
Nếu lọc còn ít nhóm hơn, chọn đủ các nhóm còn khả dụng và không lặp ID.
Món bị hard filter không được gửi Gemini hoặc dùng lại khi fallback.
Số dinh dưỡng là ước tính từ template. Khẩu phần scale giới hạn 0.5..2,
nên calorie thực đơn có thể không khớp tuyệt đối mục tiêu cực thấp/cao.
GEMINI_API_KEY do client gửi bị từ chối; không cần đặt key trên frontend.

## Lỗi

JSON lỗi Nutrition/Meal: {"success":false,"code":"...","message":"..."}.
400: input/profile chưa hợp lệ; 401: thiếu/hỏng/hết hạn session; 403: sai user/origin;
404: thiếu profile/meal; 409: stale/decided/transaction/điều kiện mới cần refresh;
422: không đủ 3 món thỏa hard filter; 413: JSON body trên 64 KiB;
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
fallback, provider failures, breakfast, flexible components, preferences và smart replace.
SQLite không xác minh khóa/cạnh tranh MySQL. Gemini thật và SMTP thật chưa kiểm thử.
Không dùng kết quả unit/integration này để tuyên bố toàn hệ thống production đã an toàn.

## Preferences v3

Generate nhận thêm preferences tùy chọn, không làm thay đổi request cũ:

```json
{
  "mealType": "breakfast",
  "preferences": {
    "avoid": ["trứng", "sữa"],
    "dislikes": ["cá"],
    "prefer": ["gà"],
    "preferEasy": true,
    "maxPrepMinutes": 25
  }
}
```

- avoid là bắt buộc. maxPrepMinutes là giới hạn thời gian tham khảo, chỉ breakfast.
- dislikes/prefer là mềm: bỏ món không thích/ưu tiên nguyên liệu nếu vẫn còn ít nhất 3 món.
  Nếu không đủ, nới sở thích mềm; không nới avoid hoặc maxPrepMinutes.
- preferEasy chỉ breakfast; số phút là ước tính chuẩn bị với nguyên liệu có sẵn.
- Chưa có giá món nên không hỗ trợ ngân sách. Field/thực phẩm chưa hỗ trợ trả
  UNSUPPORTED_PREFERENCE (400), không âm thầm bỏ qua.
- Hỗ trợ Việt/English: cá/fish, hải sản/seafood, trứng/egg, sữa/milk,
  gà/chicken, bò/beef, heo/pork, đậu phụ/soy, bánh mì/wheat, yến mạch/oats,
  cơm/rice, bún-phở-miến/noodles, chuối/banana, khoai lang/sweet_potato.
- Cá/hải sản lọc bảo thủ; sợi tham khảo được xem là gạo khi tránh rice.
  Lunch/dinner gắn tag theo tên nguyên liệu có sẵn, không đổi dinh dưỡng cũ.
- Lọc theo công thức/tên món khai báo, không bảo đảm an toàn dị ứng:
  catalog chưa mô tả đầy đủ nước mắm, gia vị hoặc nhiễm chéo.
- Preferences không lưu DB. Frontend giữ theo từng bữa trong phiên trang;
  F5 mất điều kiện nhập, nhưng thực đơn/lựa chọn đã lưu vẫn đọc từ DB.
  Client phải gửi lại avoid khi refresh/replace.
- Generate thường vẫn là cache: sở thích mới không tự thay bộ đã lưu.
  Kiểm tra cả avoid, maxPrepMinutes và dislikes/prefer theo quy tắc nới mềm ở trên.
  preferEasy cần Đổi thực đơn vì DB không lưu điều kiện xếp hạng trước đó.
  Điều kiện mới không phù hợp cache (hoặc món cũ không xác minh được) trả
  PREFERENCES_REQUIRE_REFRESH (409). Chọn Nghĩ sau nếu đã chốt rồi gửi
  forceRefresh=true kèm revision; không tự thay thực đơn đã chốt.
- Ít hơn 3 ứng viên sau hard filter hoặc loại món cũ khi refresh:
  INSUFFICIENT_MENUS (422), giữ dữ liệu cũ. Có thể nới điều kiện hoặc giữ bộ đang dùng.

## Đổi món thông minh

```json
{
  "mealType": "lunch",
  "revision": "<revision hiện tại>",
  "request": "Tôi không thích cá, hãy đổi sang gà nhưng vẫn gần 700 kcal.",
  "preferences": {"avoid": ["trứng"]}
}
```

POST /api/meals/replace đổi bộ ba lựa chọn pending của hôm nay.
Dùng lại generate/refresh, khóa user, revision và transaction;
decided trả MEAL_DECIDED (409), revision cũ trả STALE_MEAL (409),
chưa có thực đơn trả MEAL_NOT_FOUND (404). Chọn Nghĩ sau trước khi đổi bộ đã chốt.

Parser hỗ trợ "không thích X", "tránh X", "không ăn X", "đổi sang X", "ưu tiên X",
mỗi cụm một thực phẩm hỗ trợ, và một số nguyên 100–3000 kcal.
Phần yêu cầu chưa hiểu trả UNSUPPORTED_REPLACEMENT (400); không phải chatbot.
Điều kiện được gộp với preferences, không xóa avoid đã gửi.
Kcal tùy chọn chỉ scale lần đổi này, không cập nhật TargetKcal Profile;
không có số kcal thì dùng mục tiêu bữa từ Profile.

Response giữ success/data/meta; meta thêm target_kcal, profile_target_kcal,
macro_targets, applied_preferences. Dinh dưỡng luôn từ catalog,
Gemini chỉ chọn ID và giải thích. Scale 0.5..2 và làm tròn không bảo đảm khớp kcal tuyệt đối.
Không giữ phiên hội thoại/preferences trên server.

## Dữ liệu breakfast và mức độ ước tính

NutritionLegacyMenus giữ 7 ngày × quick/soup/balanced, 21 mẫu sáng có khẩu phần gram.
Macro là tổng profile nguyên liệu trên 100 g; kcal = carbs × 4 + protein × 4 + fat × 9.
Component hiển thị gram sau scale. Dữ liệu legacy là ước tính làm tròn phục vụ đồ án,
chưa đối chiếu từng recipe với mã thực phẩm được chứng nhận.
Xôi/bánh cuốn/miến dùng profile cơm/sợi chín thay thế ghi rõ trong tên,
không coi là số liệu phòng thí nghiệm. Giữ nguyên 42 mẫu lunch/dinner và materialization mặc định.

Có thể cải thiện bảng nguyên liệu bằng dữ liệu có nguồn và khẩu phần đo được;
tham khảo [USDA FoodData Central documentation](https://fdc.nal.usda.gov/data-documentation/).
REST structured output tham khảo [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output);
khả năng gọi model thật phải kiểm tra riêng, không suy ra từ mock.

## Frontend v3

Frontend ở 127.0.0.1:5500, backend ở 127.0.0.1:5000.
Ba tab dùng chung generate/select/refresh/history; renderer đọc components
và fallback về alias năm thành phần để xem dữ liệu cũ.
Dashboard lấy meal_targets/Summary từ backend, cộng ba bữa đã chọn,
không gọi kế hoạch là lượng đã ăn. Giữ toast thành công hiện có;
lỗi Meal dùng toast error, không alert chặn trang.
Avoid/dislikes/prefer và thời gian sáng gửi cùng generate/replace.
Không có Gemini key frontend; không thay Workout/Street Food.

Nếu backend đang chạy process v2 cũ, restart để nạp v3.
Không đăng ký qua server bình thường nếu SMTP chưa cấu hình/suppress:
kiểm thử local chỉ suppress trong app kiểm thử, không sửa AuthService.
Gemini key chỉ ở backend/.env đã ignore; không gửi từ trình duyệt.

## V4: catalog và gợi ý theo mục tiêu

GET /api/nutrition/catalog trả `success`, `data`, `estimated: true`, `catalog_source: "database"`.
Seed hiện có 102 món; response chỉ chứa món active có kcal/protein/carbs/fat và khẩu phần hợp lệ.
Mỗi món có dish_id, name, type/group, reference_grams, min_grams/max_grams,
macros_per_100g (carbs/protein/fat/fiber), calories_per_100g, ingredients,
prep_minutes, provenance, estimated, preparation_state, meal_types và data_version.
Backend tính kcal = calories_per_100g × gram / 100, macro tương tự. Dữ liệu USDA dùng
năng lượng được nguồn công bố; 24 profile cũ vẫn giữ số ước tính theo 4/4/9.
Đây là giá trị tham khảo; chuẩn bị sống/chín/ăn ngay được ghi riêng, không hoán đổi tùy tiện.
Fiber hoặc prep_minutes chưa biết là null. fiber_complete=false trong recipe/intake/daily
báo tổng chất xơ chỉ là phần đã biết, không khẳng định chất xơ chưa biết bằng 0.
Món thiếu kcal/protein/carbs/fat không được đưa vào gợi ý hoặc nhật ký mới.
Catalog chưa bảo đảm an toàn dị ứng/nhiễm chéo.

POST /api/meals/generate giữ contract V3, bổ sung opt-in:

```json
{
  "mealType": "lunch",
  "plannerVersion": "v4",
  "planningFocus": "muscle_gain",
  "preferences": {"avoid": ["cá"], "prefer": ["gà"]}
}
```

planningFocus có lose/maintain/gain/muscle_gain; null dùng Goal đã lưu.
Lose ưu tiên mật độ đạm, chất xơ và ít dầu; maintain cân bằng;
gain ưu tiên mật độ năng lượng; muscle_gain ưu tiên mật độ và lượng đạm.
Focus tác động xếp hạng món/prompt; không đổi Goal, BMR/TDEE, TargetKcal hoặc macro
ngày của Profile. Avoid và thời gian chuẩn bị là điều kiện cứng; dislikes/prefer
là điểm xếp hạng mềm. Không phải gợi ý điều trị.

V4 trả ba options có recipe (version=4, focus, preferences, components, provider_source,
change) và components có type/dish_id/name/grams/calories/macros. Backend từ chối
ID lạ, nhóm sai, gram ngoài giới hạn, thiếu nhóm, ba bộ trùng hoặc số AI tự tạo.
Output AI không hợp lệ chuyển fallback; reason trong digestibility chỉ là giải thích.
meta.source là gemini/fallback khi tạo; V4 cache có meta.source=cached và meta.cached=true.
meta.provider_source giữ nguồn tạo bộ đã lưu, tách biệt với việc đọc cache.

V4 fallback là tổ hợp món từ cùng database, không có danh sách Python dự phòng riêng.
Gemini compose nhận tối đa 8 ứng viên mỗi nhóm (tối đa 40), ngân sách còn lại và preferences;
alternatives nhận tối đa 8 món cùng nhóm. Không gửi toàn bộ catalog hoặc thông tin đăng nhập.
Compose schema ràng buộc đúng ba choices, enum loại thành phần và Dish ID ứng viên;
prompt nêu nhóm bắt buộc, giới hạn gram của từng món, tập ID khác nhau, title tối đa 140
và reason tối đa 220 ký tự một dòng. Backend vẫn tính dinh dưỡng từ catalog và giữ
khoảng kcal hợp lệ 65–135% mục tiêu; đạt khoảng này không có nghĩa khớp mục tiêu tuyệt đối.
Khi compose không hợp lệ, meta.fallback_reason vẫn là invalid_output để tương thích;
meta.fallback_diagnostic chỉ chứa mã an toàn: INVALID_RESPONSE_SCHEMA, INVALID_CHOICE_COUNT,
INVALID_COMPONENT_COUNT, INVALID_COMPONENT_ROLE, DUPLICATE_COMPONENT_ROLE, INVALID_DISH_ID,
INVALID_PORTION, MISSING_REQUIRED_GROUP, INVALID_DISH_ELIGIBILITY, AVOID_CONFLICT,
DUPLICATE_COMPOSITION, CALORIE_TARGET_MISMATCH, INVALID_TITLE hoặc INVALID_REASON.
Response bị cắt/quá lớn có INCOMPLETE_RESPONSE/RESPONSE_TOO_LARGE. Không ghi raw output vào log.
Mục tiêu chất lượng mới: ưu tiên ±15%, cho phép ±20% khi bị giới hạn tổ hợp món;
đây không phải biên an toàn mới. Candidate pool giữ tối đa 8 món/nhóm, dành một phần
cho món có khả năng đáp ứng kcal bên cạnh ranking theo focus/preferences/lịch sử.
Target đã phản ánh Goal từ Profile; AI không tự giảm hoặc tăng target lần nữa.
Luồng tạo mới kiểm tra schema/ID/nhóm/gram/avoid trước, sau đó tối ưu gram từng món
trong min/max riêng của món đó ở MySQL, rồi kiểm tra kcal cuối bằng biên 65–135%.
Không ép tổng về đúng target. Backend tính lại toàn bộ kcal/macro; không thêm hoặc đổi
Dish ID trong bộ AI ở bước điều chỉnh. Macro target lấy từ ngân sách bữa ăn hiện có.

Hàm điểm dùng các sai lệch không đơn vị:
- E = bình phương sai lệch kcal tương đối + 4 × bình phương phần vượt khoảng mềm
  ±15%, chuẩn hóa phần vượt theo 15%.
- M = trung bình bình phương sai lệch protein/carbs/fat, mỗi chỉ số chia cho mục tiêu
  riêng (mẫu số tối thiểu 1 g để tránh chia cho 0).
- R = trung bình bình phương (gram/reference_grams − 1).
- H = 0.02 × max(0, tổng gram / tổng reference gram của các vai trò bắt buộc − 1)²
  + 0.01 × max(0, số component tùy chọn − 1).
- Điểm tổng = E + M + 0.25 × R + H. Điểm thấp hơn được ưu tiên, sau kiểm tra an toàn kcal.

Trọng số là lựa chọn kỹ thuật: tăng gấp đôi mọi khẩu phần bị phạt 0.25, tương đương
sai lệch 50% của cả ba macro; phần vượt thêm 15% ngoài khoảng mềm bị phạt 4 để vẫn
ưu tiên năng lượng. Đây không phải giới hạn điều trị. Tìm kiếm tọa độ hữu hạn dùng
ba điểm khởi đầu (đề xuất, reference và điểm đủ năng lượng), giảm bước theo khoảng
min/max từng món; không cần thư viện mới và không bảo đảm nghiệm tối ưu toàn cục.

H là điểm mềm để món phụ/canh ở reference không trở thành miễn phí khi thêm vào
bữa. Khối lượng gấp đôi reference của vai trò bắt buộc bị phạt 0.02, bằng độ nhạy
chuyển nguồn; component tùy chọn thứ hai trở đi bị phạt 0.01 mỗi món. Không áp một
trần gram chung, không loại bỏ canh hay nhóm món nào, và không thay min/max MySQL.

V4.1 so sánh AI/fallback cả khi AI đã đạt khoảng kcal. Điểm lựa chọn S = E + M +
0.25 × R + H + W²/3, với W là sai lệch macro chuẩn hóa lớn nhất. Thành phần cuối tính
macro lệch nhất thêm một lần bằng trọng số của một macro trong M; không thay đổi
objective dùng để fit gram. Chỉ chuyển sang fallback khi cả ba bộ fallback nằm trong
biên an toàn, điểm cả danh sách giảm ít nhất max(0.02, 15% điểm danh sách AI), và S của bộ kém nhất
không tăng. 0.02 và 15% là độ nhạy kỹ thuật để tránh chuyển nguồn vì sai số nhỏ,
không phải ngưỡng dinh dưỡng. Nếu AI vượt khoảng kcal ±20%, giữ reason/diagnostic cũ:
calorie_quality / SELECTED_COMBINATION_ENERGY_LIMIT. Nếu cải thiện tổ hợp khi kcal
đã trong khoảng, dùng composition_quality / BETTER_MACRO_PORTION_COMBINATION.
Không gọi lại Gemini và không đổi ID món trong bộ AI để giả nhận source=gemini.
Nếu fallback vẫn bị giới hạn,
meta.calorie_quality.limited=true, reason=COMBINATION_PORTION_LIMIT, không giả tạo kcal.
Mỗi recipe mới lưu calorie_adjustment gồm target/before/after/deviation_percent, trạng thái
đạt khoảng mềm, macro_targets, macro_deviation_percent, macro_feasible_ranges,
reference_ratios, portion_quality và objective. Macro goal bằng 0 có deviation_percent=null.
V4.1 bổ sung selection_score, worst_macro_error, macro_diagnostics (actual, target,
difference_grams, normalized_error, target_within_individual_bounds), unmet_macros,
macro_limited, joint_feasibility=not_proven và reference_data_complete. macro_limited
chỉ phản ánh target nằm ngoài min/max riêng của ít nhất một macro; unmet_macros
liệt kê phần còn thiếu dù target vẫn có thể nằm trong khoảng. Đây là diagnostics
mềm, không thêm điều kiện từ chối output. meta.composition_quality bổ sung danh sách
quality; meta.calorie_quality và các field cũ được giữ. Snapshot cũ thiếu field mới
vẫn đọc được, cache không chạy fitting hoặc ghi lại snapshot.
macro_feasible_ranges là min/max riêng của từng macro trong tổ hợp, không bảo đảm ba
macro đồng thời đạt được. Các độ lệch phản ánh giới hạn tổ hợp; không tuyên bố đạt kcal
là cân bằng macro. Không điều chỉnh bộ cache, bộ đã chốt hoặc lịch sử sau F5.

V4.1 tính macro target từ ngân sách bữa trước candidate_pool, không thay TargetKcal.
Pool giữ tối đa 8 món/role: 4 slot focus/preferences/lịch sử, 2 slot năng lượng,
2 slot bổ trợ từ tổ hợp được chấm điểm; slot trùng được bù theo ranking. Lọc avoid,
meal type và prefer/dislikes hiện có áp dụng trước các slot bổ trợ. Beam search
giữ 12 tổ hợp trung gian, tối đa 24 món/role khi phân tích pool và 8 khi fallback.
Partial beam dùng tối đa 3 tổ hợp reference đối tác để đánh giá; so sánh khẩu phần
theo 5 scale (.75, 1, 1.25, 1.5, 2), luôn clamp theo min/max từng món. Đây chỉ là
shortlist; gram cuối vẫn dùng fit_portions. Lunch/dinner tối đa 1,200 beam expansions
cho pool, 416 cho fallback; tối đa 6 tổ hợp được fitting ở fallback.
Không duyệt Cartesian product toàn catalog. Beam giữ tối đa 6 primary tốt trước,
rồi giữ các đối tác CARB khác nhau khi điểm gần nhau. Fallback dành 3 slot fitting
cho primary khác nhau, 3 slot còn lại cho đối tác CARB; chọn cả bộ ba từ tối đa
20 danh sách có primary khác nhau, thay vì greedy từng option.
Điểm danh sách B = trung bình S + D, với D = 0.03 × tỷ lệ cặp lặp CARB +
0.03 × tỷ lệ cặp lặp PROTEIN/MAIN + 0.01 × trung bình Jaccard của ID component.
D tối đa 0.07, là chi phí tie mềm: không bắt buộc ba CARB khác nhau, không đánh đổi
macro sai lệch lớn chỉ để lấy diversity. Trước khi so D, chỉ giữ bộ có cùng mức
an toàn kcal và trung bình S/S kém nhất không cao hơn bộ chất lượng tốt nhất quá
0.02 điểm (ngân sách tie kỹ thuật, không phải ngưỡng macro). meta.composition_quality.diversity gồm
score=1−D/0.07 (cao hơn là đa dạng hơn), penalty và số món chung của từng cặp.
Score này đánh giá ID/role, không chứng nhận đa dạng sinh học hay cân bằng dinh dưỡng.
Không hardcode ID hoặc bắt buộc dùng một nguồn fat cụ thể.

Compose prompt yêu cầu xét đồng thời kcal/P/C/F và reference grams, đổi món hoặc
thêm allowed role để bổ trợ thay vì tăng cực nhiều gram. JSON schema/request count
không thay đổi. Backend luôn tự tính từ MySQL; macro chỉ là mục tiêu tham khảo mềm.

Compose bổ sung optional_roles và optional_macro_support vào prompt nội bộ.
Support là lookup tối đa một Dish ID/role/macro (lunch/dinner tối đa 6 mục), chọn
theo lượng macro ở reference_grams từ chính pool hợp lệ đã lọc meal type/avoid.
Không gửi recipe Backend dựng sẵn, không hardcode món và không thêm request.
Lookup chỉ chỉ dẫn ứng viên bổ trợ, không chứng minh khả thi đồng thời và không
yêu cầu luôn chọn món nhiều fat nhất. Model phải kiểm tra trần từng macro theo
max_grams trước khi tăng gram; đổi món/thêm role còn trống nếu tổ hợp thiếu, rồi
kiểm tra lại kcal, macro và khẩu phần. Không thêm món nếu các vai trò bắt buộc đã
đủ cân đối. Validator, fitting, quality gate và API response schema giữ nguyên.

Replace một component tính lại quality từ recipe mới, giữ target/macro_targets của
snapshot và mọi component khác. Không fitting lại hoặc gọi generate. Recipe cũ
thiếu quality dùng mục tiêu bữa từ Profile. Dinh dưỡng của component không thay giữ
snapshot; reference/bounds lấy từ catalog hiện có. Nếu một món cũ không còn active,
reference_data_complete=false, objective/selection_score=null và khoảng khả thi
không được suy đoán. Revision, ownership, planned/consumed và persistence giữ nguyên.

Giới hạn hiện tại: tối ưu kcal, macro và khẩu phần dùng tiêu chí mềm, không bảo đảm
mọi macro đạt target khi tổ hợp món không đáp ứng. Replay baseline 891 kcal giữ
nguyên ID từng bộ vẫn thiếu fat 49.83% và 42.09% ở hai bộ đầu. V4.1 cải thiện chọn
tổ hợp từ catalog nhưng không sửa dữ liệu lịch sử. Beam hữu hạn không bảo đảm nghiệm
tối ưu toàn cục; vài bộ có thể còn lặp tinh bột hoặc có tổng khối lượng lớn do món canh.
Phase 3 tăng đa dạng và giảm khối lượng bằng tiêu chí mềm; có thể đổi lấy độ lệch
macro cao hơn. Replay 891 kcal/avoid fish cho ba bộ mới có fat lệch −12.79%,
−20.54% và −5.05%; chưa cải thiện đồng thời mọi tiêu chí so với Phase 2.
Không cam kết vừa đa dạng tối đa vừa đạt mọi macro hay mọi
khẩu phần đều tối ưu. Không ghi lại các bộ Phase 2 đã lưu khi thay thuật toán.
Dữ liệu dinh dưỡng vẫn là ước tính; thực đơn chưa được kiểm định dinh dưỡng và không
có cam kết luôn cân bằng hoàn toàn.

Kiểm chứng Gemini thật gần nhất của V4.1 dùng hai request trong bộ nhớ, retry=0,
không ghi MySQL. Cả 2/2 response HTTP 200 có đúng ba choices và qua validator,
nhưng quality gate chọn source=fallback ở cả hai vì điểm tổ hợp tốt hơn rõ rệt.
Tình huống lunch: 891 kcal, P/C/F=55.7/100.2/29.7 g, avoid fish; dinner:
600 kcal, P/C/F=37.5/67.5/20 g, avoid fish/milk. Cả sáu lựa chọn Gemini chỉ dùng
nhóm bắt buộc; 4/6 tổ hợp có trần fat riêng thấp hơn target. Điểm S trung bình
lunch thay đổi 0.2330 → 0.2495, dinner 0.1664 → 0.1338 (thấp hơn tốt hơn).
Đây là mốc kỹ thuật, chưa chứng minh chất lượng Gemini Compose cải thiện ổn định.
Replay mock bổ sung món hỗ trợ chỉ chứng minh khả năng của catalog, không chứng
minh Gemini thật tuân thủ prompt. Không coi response hợp lệ là source=gemini
khi thực tế Backend đã chọn fallback.

Toàn bộ 63 mẫu V3 được giữ trong NutritionLegacyMenus và
tiếp tục được dùng khi plannerVersion=v3. Giới hạn gram và scale có thể làm bộ
fallback khác mục tiêu kcal; không cam kết khớp kcal tuyệt đối.

Recipe V4 được lưu trong NutritionMealDetails và đọc lại sau F5.
Component lưu nutrition_per_100g, nguồn dữ liệu, data version và fiber_complete làm snapshot.
Đọc lịch sử không tính lại theo catalog mới. Sửa gram của món đã ghi nhận dùng snapshot cũ,
kể cả món đã inactive; món được thêm mới vào nhật ký lấy dữ liệu active hiện tại.
Frontend preview dùng kcal nguồn và snapshot khi sửa, không tự suy kcal từ macro 4/4/9.
Cache kiểm tra preferences/focus đã lưu: khác trả PREFERENCES_REQUIRE_REFRESH (409),
không âm thầm bỏ điều kiện. Đổi V3 đang cache sang V4 trả V4_REFRESH_REQUIRED (409):
giữ bộ cũ, chọn Nghĩ sau nếu đã chốt rồi refresh với revision hiện hành.
POST /api/meals/replace nhận plannerVersion/planningFocus tương tự, giữ parser V3;
kcal trong câu đổi món chỉ áp dụng lần đổi đó, không thay mục tiêu Profile.

## V4: đổi một component

POST /api/meals/component-suggestions:

```json
{"mealType":"lunch","optionId":123,"componentType":"PROTEIN","revision":"<24 ký tự hiện hành>"}
```

Response data có choices (món cùng nhóm + reason), revision, source, fallback_reason.
Gemini chỉ đề xuất ID hợp lệ; catalog hạn chế hoặc lỗi provider dùng fallback.
POST /api/meals/replace-component gửi cùng field và thêm dishId/grams:

```json
{"mealType":"lunch","optionId":123,"componentType":"PROTEIN","revision":"<hiện hành>","dishId":"chicken","grams":130}
```

Response data là thực đơn được cập nhật: chỉ component được chỉ định trong đúng
option thay đổi; tổng macro/kcal tính lại; recipe.change và revision thay đổi kể cả
kcal bằng nhau. Không thêm nhật ký đã ăn. Các option khác giữ nguyên.
MEAL_DECIDED/STALE_MEAL trả 409; món vi phạm avoid trả AVOID_CONFLICT (422).
V3 không có gram/macro từng món: LEGACY_COMPONENT_NUTRITION_REQUIRED (409),
không chia tổng kcal cũ để giả lập số dinh dưỡng từng component.

## V4: nhật ký thực sự đã ăn

Các endpoint dùng cùng session và kiểm tra quyền user; không tin userId client:

| Method | URL | Chức năng |
|---|---|---|
| GET | /api/nutrition/daily?date=2026-10-10 | Nhật ký và ngân sách đúng user/ngày |
| POST | /api/nutrition/intake | Xác nhận một lần ăn |
| POST | /api/nutrition/intake/{id}/update | Sửa món/gram/thời gian với version |
| POST | /api/nutrition/intake/{id}/delete | Xóa khỏi tổng với version |

```json
{
  "requestId": "<UUID tạo một lần cho thao tác xác nhận>",
  "confirmed": true,
  "mealType": "breakfast",
  "consumedAt": "2026-10-10T08:00:00+07:00",
  "items": [{"dish_id":"bread_egg","grams":180}]
}
```

mealType breakfast/lunch/dinner/snack. items gồm 1–20 món catalog, gram 1–2000/món;
cho phép món ngoài thực đơn AI nhưng chưa cho phép món ngoài catalog không có dữ liệu.
consumedAt cần ISO có timezone; bỏ trống dùng giờ UTC hiện tại. Ngày nhật ký tính
UTC+7, OccurredAt lưu UTC. Không cộng calories Workout vào phần đã nạp.
confirmed=true bắt buộc; Select/Generate/Replace không đồng nghĩa đã ăn.

Có thể gửi thêm meal={optionId,revision} để xác minh bộ hôm nay của chính user.
V4 vẫn yêu cầu items/gram thực tế. V3 có thể gửi servings 0.1–4 thay items để ghi
tổng dinh dưỡng nguyên bộ ước tính; không suy diễn khẩu phần từng món.
Snapshot được lưu tại thời điểm ghi, vẫn đọc/sửa tổng V3 được sau khi bộ gốc đổi.

Tạo mới trả 201, retry cùng requestId và cùng payload trả 200/created=false.
requestId có 16–64 ký tự, duy nhất trong từng user. Cùng key khác payload trả
IDEMPOTENCY_CONFLICT (409). Client giữ UUID và payload khi retry sau lỗi mạng.
Update nhận confirmed, mealType, consumedAt, items (hoặc servings V3), version.
Delete nhận {"version":1}; xóa mềm để retry cũ không tái tạo nhật ký đã xóa.
STALE_INTAKE/INTAKE_DELETED trả 409; nhật ký user khác trả 404.

GET daily trả data: date, targets (Nutrition từ Profile), consumed, remaining,
over_target, logs, consumed_meals, suggested_meal_targets, snack_reserve_kcal,
requires_confirmation=true, tracking_mode=consumed, estimated=true.
remaining[k] = mục tiêu[k] − tổng snapshot[k]; có thể âm, phần vượt hiển thị riêng.
Phân bổ phần còn lại theo tỷ lệ các bữa chưa ghi nhận, dành phần snack nếu chưa ăn.
Khi phần còn lại quá thấp/vượt mục tiêu, giữ mục tiêu bữa tham khảo thay vì 0 kcal
hoặc khuyên bỏ bữa. Đây là đề xuất, không tự thay bộ chốt hay ghi bữa chưa ăn.
Generate V4 dùng ngân sách hiện tại; người dùng xác nhận refresh với revision nếu
muốn cập nhật bộ đã cache. Summary cũ vẫn chỉ là Planned; daily là Consumed.

## V4: Gemini thật và kiểm thử

Gemini REST dùng key trong header server, không trong URL; structured JSON,
timeout/retry/cooldown giới hạn. Không ghi provider body hay secret vào log.
400/403/404 => provider_error, 429/5xx => provider_busy; meta có status an toàn
khi generate fallback. Thiếu key/model hoặc cooldown vẫn dùng fallback.

Kiểm chứng riêng ngày 2026-10-10: models.get HTTP 200 cho gemini-3.5-flash-lite,
hỗ trợ generateContent; đúng một lần generateContent qua GeminiClient.rank thành
công với ba lựa chọn JSON hợp lệ. Compose/alternatives V4 được kiểm thử mock,
chưa gọi thật riêng. Không suy ra V4 trên MySQL đã PASS từ test này.
Không gửi temperature/topP/topK vì các tham số sampling đã bị model 3.5 bỏ hỗ trợ:
[tài liệu model chính thức](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).

Chạy regression từ backend, không chạy helper ghi kết quả hay reset DB:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

Fixtures tạo app factory gốc với SQLite in-memory, key/model rỗng, mock mail/HTTP;
không dùng MySQL thật. Migration chỉ được dịch và chạy trong SQLite disposable.
Chrome E2E kiểm tra giao diện thật + HTTP Flask trên SQLite, chuyển API sang server
cô lập trong browser kiểm thử, mock CDN/SMTP và chặn Gemini thật.
V4 MySQL local đã được phê duyệt migration và kiểm thử ngày 2026-10-10:
16 bảng, backup ngoài Git; 14 bảng gốc không đổi cấu trúc/dữ liệu khi migration.
Chrome + Flask HTTP tại đúng 5500/5000 PASS luồng V4, dữ liệu demo UserId=11;
MySQL lưu 9 recipe và 2 dòng nhật ký (1 xóa mềm). App factory khởi tạo lại đọc
được session/recipe/nhật ký. So sánh SHA của từng hàng có sẵn trước/sau lượt test
trên 16 bảng: không đổi. Gemini bị chặn, SMTP suppress và chặn kết nối trong server test.
Hai lượt đầu gặp server V3 cũ còn ở cổng 5000, đã để lại demo 9/10 với profile
và thực đơn sáng V3; giữ nguyên, không tự xóa hoặc reset để che kết quả.

Regression: 119/119 PASS (93 baseline + 26 mới), network socket bị chặn;
Chrome SQLite 10 checkpoint PASS, Chrome MySQL 12 checkpoint PASS,
8 kiểm tra UI V3/syntax PASS. Kiểm tra Python AST, ID HTML, script path,
git diff --check và scan mẫu secret: PASS. Scan không bảo đảm phát hiện mọi secret.
Backend kiểm thử 5000 đang dùng fallback và suppress mail trong bộ nhớ, không
thay .env/AuthService; khởi động bình thường sẽ dùng Gemini key/model local và
cấu hình mail của core. Không đăng ký email thật khi chưa thống nhất SMTP.

Frontend chỉ hiển thị Meal Planner V4, kể cả sau F5 hoặc đăng nhập lại;
backend vẫn giữ 63 mẫu V3, endpoint cũ và fallback. Giao diện giữ ưu tiên Nutrition
và Đổi món từng component. Theo dõi dinh dưỡng hiển thị Mục tiêu/Đã nạp/Còn lại,
thanh tiến độ và macro thu gọn; khi vượt mục tiêu, Còn lại hiển thị 0 và phần vượt
hiển thị riêng, không thay giá trị remaining có thể âm trong API.
Modal Ghi nhận bữa ăn cho phép tìm món, thêm/bỏ món khỏi bản nháp, chỉnh gram
và xem tổng ước tính. Nút lưu gửi confirmed=true; chặn bữa rỗng, khẩu phần sai
và double-submit, giữ UUID/payload khi retry. Giữ nhật ký sửa/xóa và lựa chọn ngày.
Bỏ món khỏi bản nháp nhật ký không sửa thực đơn đã chốt; chọn thực đơn không
ghi calories đã ăn.
Gợi ý bữa còn lại chỉ điều hướng; phải nhấn Gợi ý/Đổi và xử lý bộ chốt như trước.
Session/cookie/toast hiện có giữ nguyên. Chưa mở rộng Workout/Street Food.


## Demo: khẩu vị và đổi bộ gợi ý

Luồng V4 chỉ dùng ba danh sách `avoid`, `dislikes`, `prefer`. Frontend tách
nguyên liệu bằng dấu phẩy; Backend chuẩn hóa dấu/chữ hoa/tên đồng nghĩa và loại
trùng. Tên không nhận diện trả `400 UNSUPPORTED_PREFERENCE`, nêu rõ tên bị lỗi;
không ghi thực đơn. `avoid` lọc theo nguyên liệu khai báo, không phải chứng nhận
an toàn dị ứng. `dislikes` và `prefer` là ưu tiên mềm: dinh dưỡng, cấu trúc và
avoid vẫn được giữ. Khi mâu thuẫn, avoid thắng; dislikes ưu tiên hơn prefer.
`meta.preference_notices` chứa các mã nguyên liệu có ưu tiên mâu thuẫn.

V4 bỏ qua `preferEasy`/`maxPrepMinutes` từ client hoặc snapshot cũ. Không xóa
snapshot lịch sử, metadata thời gian hay contract V3. Frontend bỏ hai điều khiển
thời gian và không gửi/phục hồi chúng vào trạng thái khẩu vị hiện hành.

`POST /api/meals/generate` giữ request hiện có: `mealType`, `plannerVersion:"v4"`,
`preferences`, `planningFocus`; khi đổi bộ thêm `forceRefresh:true` và `revision`.
Bộ khác được so bằng role + Dish ID, bỏ qua thứ tự lựa chọn/gram/ID response.
Fallback tìm một bộ khác trong shortlist giới hạn; không tăng số request Gemini.
Pool giữ tối đa tám món/role, có chỗ cho nguồn món khác khi ưu tiên mềm.

Response bổ sung vào `meta`:
- `changed:true`, `refresh_status:"updated"`: danh sách món thay đổi.
- `changed:false`, `refresh_status:"no_alternative"`, `cached:true`,
  `source:"cached"`, `reason:"BOUNDED_SEARCH_EXHAUSTED"`: giữ nguyên bộ và revision,
  không ghi DB. Đây là kết quả tìm kiếm giới hạn, không khẳng định toàn catalog
  không còn tổ hợp khả thi. Frontend báo thông tin, không báo đổi thành công.
- `changed:false`, `refresh_status:"preferences_applied"`: khẩu vị/focus mới đã
  được lưu và kiểm tra nhưng bộ món vẫn giống; frontend nêu rõ điều này.

`STALE_MEAL`/`MEAL_DECIDED` vẫn trả 409; `INSUFFICIENT_MENUS` trả 422, không
bỏ qua avoid hoặc ghi đè kế hoạch cũ. Gemini lặp lại bộ cũ có thể bị thay bằng
fallback mới, với `source:"fallback"`, `fallback_reason:"repeated_composition"`.
Chọn/đổi thực đơn không cộng consumed; Food Intake xác nhận vẫn là luồng riêng.
