# Nutrition, Meal và Gemini AI v3/v4 — NutriFit

V4 bổ sung catalog, recipe theo gram, thay một component và nhật ký đã ăn.
V3 vẫn là mặc định để chạy với 14 bảng hiện tại. V4 cần migration độc lập
[001_nutrition_v4.sql](../setup/migrations/001_nutrition_v4.sql), chỉ áp dụng sau
backup và phê duyệt theo [hướng dẫn migration](NUTRITION_V4_MIGRATION.md).
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
- breakfast_menus.py tách công thức sáng; vietnamese_menus.py giữ registry và 42 mẫu cũ để tránh refactor không cần thiết.
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

breakfast_menus.py có 7 ngày × quick/soup/balanced, 21 mẫu có khẩu phần gram.
Macro là tổng profile nguyên liệu trên 100 g; kcal = carbs × 4 + protein × 4 + fat × 9.
Component hiển thị gram sau scale. FOODS là ước tính làm tròn phục vụ đồ án,
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

GET /api/nutrition/catalog trả `success`, `data` (24 món), `estimated: true`.
Mỗi món có dish_id, name, type/group, reference_grams, min_grams/max_grams,
macros_per_100g (carbs/protein/fat/fiber), calories_per_100g, ingredients,
prep_minutes, provenance và estimated. Đây là số làm tròn phục vụ đồ án,
không phải bảng dinh dưỡng được kiểm định. Năng lượng = carbs×4 + protein×4 + fat×9.
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
meta.source là gemini/fallback khi tạo; cache có meta.cached=true.

V4 fallback là tổ hợp catalog có kiểm soát. Toàn bộ 63 mẫu V3 vẫn nguyên vẹn và
tiếp tục được dùng khi plannerVersion=v3. Giới hạn gram và scale có thể làm bộ
fallback khác mục tiêu kcal; không cam kết khớp kcal tuyệt đối.

Recipe V4 được lưu trong NutritionMealDetails và đọc lại sau F5.
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
