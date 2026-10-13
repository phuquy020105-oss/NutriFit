# Food catalog trong MySQL — migration và kiểm thử

Nhánh: `feature/nutrition-mysql-food-catalog`, nền V4 `77b04af`.
Migration 002 và seed **đã được phê duyệt và áp dụng trên MySQL local ngày 2026-10-11**.
Catalog có 102 món, 63 template; 18 bảng. Các tests tự động dùng SQLite/mock riêng.
Chrome/MySQL đã PASS; Gemini alternatives thật PASS. Compose bị từ chối ở phiên migration,
nhưng đã PASS trong phiên kiểm thử sửa compose bên dưới. Không suy đoán nguyên nhân
cụ thể của lần FAIL cũ khi không có raw output để tái hiện.

## Thay đổi additive: 16 → 18 bảng

| Bảng mới | Nội dung | Khóa/index |
|---|---|---|
| NutritionFoodCatalog | Tên tiếng Việt, nhóm món, trạng thái chế biến, khẩu phần/gram, kcal và macro/100 g, fiber nullable, nguyên liệu, bữa phù hợp, thời gian nullable, provenance, estimated, active, data version | PK DishId; index IsActive/ComponentType |
| NutritionLegacyMenus | 63 template legacy dưới dạng JSON, bữa và ngày | PK TemplateId; index MealType/DayIndex/IsActive |

Schema đầy đủ: [002_nutrition_food_catalog.sql](../setup/migrations/002_nutrition_food_catalog.sql).
Không ALTER bảng DishCatalog của Quý; không thay 16 bảng, models, foreign keys hoặc lịch sử.
Hai bảng mới không có khóa ngoại vào snapshot: deactivate món không phá nhật ký cũ.
Kcal/protein/carbs/fat thiếu được lưu null nhưng không dùng cho gợi ý hoặc nhật ký mới.
Fiber chưa biết giữ null; tổng fiber là phần đã biết, có cờ fiber_complete=false.

## Seed thực tế

[nutrition_catalog.json](../setup/seeds/nutrition_catalog.json) là artifact import duy nhất;
Flask runtime chỉ đọc database, không tự import/migrate khi khởi động.

- 24 profile V4 cũ: giữ nguyên Dish ID, tên và dinh dưỡng ước tính để tương thích.
- 63 thực phẩm thông dụng có mã USDA SR Legacy và trạng thái chế biến cụ thể.
- 15 món sáng lấy từ công thức nguyên liệu/gram cũ, ghi rõ ước tính và nguồn nội bộ.
- Tổng 102 món: 21 MAIN, 10 CARB, 21 PROTEIN, 25 VEGGIE, 2 SOUP, 2 SIDE, 4 DRINK, 17 DESSERT.
- 63 template legacy: 21 sáng + 21 trưa + 21 tối, giữ khẩu phần, macro và cách materialize cũ.

Không coi 102 record là 102 món Việt đã được kiểm định. Các recipe nội bộ còn là ước tính;
các thực phẩm USDA là tham khảo cho trạng thái được mô tả, không đại diện mọi cách nấu ở Việt Nam.
Tên raw_edible dùng cho trái cây/rau ăn sống; planner không chọn nguyên liệu ở trạng thái raw.
Thời gian của 63 record USDA chưa được xác minh: giữ null, không bịa số phút.
Ưu tiên dễ làm xếp món chưa rõ thời gian sau; giới hạn phút loại món chưa rõ thời gian.
Preferences hiện hỗ trợ các nhóm thực phẩm đã có trong API; thuật ngữ khác trả UNSUPPORTED_PREFERENCE.

Nguồn: [USDA FoodData Central downloads](https://fdc.nal.usda.gov/download-datasets/),
[SR Legacy 2018-04 CSV](https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip).
Archive tham khảo: 6,074,592 bytes; SHA256
`b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0`.
Các record giữ source_id, description, source_url và basis per 100 g.
Kcal USDA dùng nutrient 1008; protein 1003, fat 1004, carbs 1005, fiber 1079.
Không thay công thức BMR/TDEE/TargetKcal của Quý.

## Chuẩn bị trước khi được phê duyệt

Lệnh sau chỉ kiểm tra JSON, không khởi tạo Flask và không kết nối database:

```powershell
.\.venv\Scripts\python.exe -B setup\seed_nutrition_catalog.py
```

Mong đợi: mode validate_only, dishes 102, legacy_menus 63, database_writes 0.
Không chạy các lệnh bên dưới trước khi người dùng phê duyệt migration/seed.

## Quy trình sau khi được phê duyệt

1. Tạm dừng các thao tác ghi từ UI/backend. Kiểm tra DATABASE_URL local qua engine;
   không in URL/password. Xác nhận mysql+pymysql, 127.0.0.1:3306, SELECT DATABASE() = NutriFitDB.
2. Tạo **backup mới** ngoài Git, ví dụ D:\NutriFitBackups. Backup cũ trước V4 không bao gồm
   mọi dữ liệu demo mới. Dùng mysqldump --single-transaction --routines --triggers
   --host=127.0.0.1 --port=3306 --user=root --password --result-file=<đường dẫn ngoài repo> NutriFitDB.
   Nhập password tại terminal; không đưa password vào command, file source hoặc chat.
   Kiểm tra exit code, file tồn tại/kích thước khác 0 và checksum; không in dump chứa dữ liệu cá nhân.
3. Dùng MySQL CLI --host=127.0.0.1 --port=3306 --user=root --password NutriFitDB.
   Chạy SELECT DATABASE(), SHOW TABLES và kiểm tra hai bảng mới chưa tồn tại.
   Nếu bảng đã có hoặc trạng thái không đúng, dừng để review; không tự DROP hoặc chạy lại.
4. Chỉ trên NutriFitDB đã xác minh, SOURCE D:/Web/NutriFit/setup/migrations/002_nutrition_food_catalog.sql.
   Migration có đúng hai CREATE TABLE và hai CREATE INDEX. Không chạy create_database.sql hoặc migration 001 lại.
5. Kiểm tra đủ 18 bảng, SHOW CREATE TABLE/SHOW INDEX của hai bảng mới.
6. Chỉ khi schema đúng, chạy import sau từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -B setup\seed_nutrition_catalog.py --apply --database NutriFitDB
```

7. Script kiểm tra host/driver/database, dùng INSERT-only và commit một transaction.
   ID đã có được bỏ qua, không UPDATE, không nhân bản, không ghi đè chỉnh sửa thủ công.
   Lần đầu mong đợi 102 dishes/63 menus; lần hai 0/0. Lỗi import rollback dữ liệu ghi trong transaction.
8. SELECT đếm record; so sánh checksum/schema/count của các bảng cũ với trước migration.
   Restart Flask để nạp code; kiểm thử demo Chrome 5500/Flask 5000 với SMTP suppress.
   Mock Gemini cho regression; sau đó kiểm tra một compose và một alternatives thật khi key/quota cho phép.
   Báo riêng source gemini/fallback/cached, không suy thành công AI từ fallback.

## Tương thích và rollback

- Runtime gồm FoodCatalogRepository + food_catalog_service; ba module Python dữ liệu cũ được loại bỏ
  sau khi dependency đã chuyển và tests đạt. Dữ liệu cũ nằm trong seed, sau import nằm trong MySQL.
- V3 Generate dùng NutritionLegacyMenus. V4 Generate/đổi món/catalog/intake/fallback cùng đọc NutritionFoodCatalog.
- Các thực đơn/intake đã lưu đọc snapshot; sửa gram của món cũ dùng snapshot cũ, thêm món mới dùng catalog active.
- Khi thiếu bảng, request cần catalog trả 503 FOOD_CATALOG_MIGRATION_REQUIRED, không tự tạo bảng.
  Endpoint đọc lịch sử/today/daily vẫn đọc dữ liệu snapshot; không bắt buộc nạp catalog.
- MySQL DDL có implicit commit: migration không được xem là một transaction có thể rollback toàn bộ.
  Nếu CREATE lỗi giữa chừng, dừng và review trạng thái thật; không tự sửa schema hoặc DROP bảng.
- Có thể quay lại chạy code V4 ổn định tại 77b04af để phục vụ giao diện cũ; code cũ bỏ qua hai bảng mới.
  Không xóa các bảng mới hoặc reset user data để rollback code. Không tự thực hiện thao tác Git rollback.
  Phục hồi dump chỉ sau phê duyệt riêng, ưu tiên database phục hồi tách biệt để tránh mất dữ liệu phát sinh.
- Không deploy code mới trước khi migration/seed hoàn tất. Chưa commit, stage hoặc push các thay đổi này.

## Kiểm thử an toàn

Từ backend, dùng môi trường hiện có (không cài/nâng dependencies):

```powershell
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

Fixtures khẳng định SQLite :memory:, dịch DDL gốc/migration chỉ trong database disposable,
mock SMTP và bỏ API key Gemini trong bộ nhớ. Phiên kiểm thử của Codex còn chặn socket bên ngoài.
Không chạy run_checks.py hoặc script reset MySQL. Các tests catalog bổ sung full seed 102 món;
119 tests baseline giữ 24 profile gốc trong fixture để so sánh hành vi cũ.

## Kết quả trước migration — 2026-10-11

- Baseline 119/119 PASS trước refactor; sau cleanup 148/148 PASS (119 cũ + 29 mới),
  54.380 giây, SQLite in-memory, HTTP mock và socket ngoài bị chặn.
- So sánh dữ liệu seed với commit 77b04af: giữ 24 ID/profile dinh dưỡng gốc;
  provenance chuyển thành metadata có cấu trúc. Giữ cả 63 template, chỉ chuyển tuple thành JSON array
  và bổ sung ingredient_labels để materialize legacy không cần module Python cũ.
- Python AST: 40 file; Chrome compileScript: 8 file JavaScript + 1 script inline PASS.
  HTML không trùng ID, các script local đều tồn tại.
- Chrome headless 5500/Flask HTTP 5000 với **SQLite disposable**, full seed: login/session,
  generate ba bữa, refresh, đổi component, history, select không cộng intake, tìm món mới,
  kcal nguồn, double-submit, sửa gram theo snapshot sau khi món inactive, F5 và logout PASS.
  CDN được stub cho kiểm thử chức năng; đây không phải xác nhận giao diện/CDN/MySQL production.
  Không gửi SMTP hoặc gọi Gemini thật. Các process kiểm thử đã dừng.
- MySQL local chỉ đọc trong transaction READ ONLY: database trả tên nutrifitdb,
  còn 16 bảng; chưa có hai bảng catalog. DishCatalog 11, MealSuggestions 27,
  MealOption 81, NutritionMealDetails 33, NutritionFoodIntake 6 record, khớp kiểm tra trước refactor.
- git diff --check PASS; file mới/sửa không phát hiện secret; backend/.env vẫn được ignore.
- Phát hiện riêng ở Backend Core đã có từ trước: backend/app/__init__.py:24 có literal
  connection URL chứa credential. Không in giá trị, không sửa Core; cần Quý review/xử lý riêng
  trước phát hành. Không quy kết fixture/seed mới đã tạo credential này.
- Chưa kiểm chứng migration MySQL, import thực tế, compose/alternatives Gemini thật hoặc Chrome dùng MySQL
  cho catalog mới. Chờ phê duyệt schema/seed/backup trước bước đó; không stage/commit/push.

## Sau phê duyệt — 2026-10-11

- SQL 002 có đúng 2 CREATE TABLE và 2 CREATE INDEX, chỉ nhắm hai bảng Nutrition mới;
  không DROP/TRUNCATE/DELETE/ALTER/USE hoặc chạy lại schema gốc. Cả hai bảng chưa tồn tại trước khi chạy.
- Backup mới ngoài Git: D:\NutriFitBackups\NutriFitDB_before_catalog_002_20261011_173931.sql,
  182,730 bytes; SHA256 `00e8d2b06938e7d12bcadaca81a817833e4b992777207e705410e5b7911427f7`.
  mysqldump exit 0, đủ 16 CREATE TABLE, số INSERT của từng bảng khớp snapshot và có footer hoàn tất.
  Dump không chứa DROP/DELETE/TRUNCATE/USE. Chưa thực hiện diễn tập restore vào database khác.
  Snapshot checksum/primary key phục vụ đối chiếu nằm trong file .verification.json cạnh backup,
  không chứa email, password, cookie hoặc URL kết nối.
- Migration chạy 4 statements thành công, 16 → 18 bảng; cả hai primary key/index kiểm tra đạt.
- Import đầu: 102 món và 63 template; chạy lại: 0 món/0 template thêm mới. Record và nguồn seed khớp dữ liệu đọc từ MySQL.
- Sau migration/seed: checksum dữ liệu và thiết kế của cả 16 bảng cũ khớp nguyên trạng.
- Demo mới UserId=14: register/login qua browser, Profile lưu qua /save, cookie, Nutrition,
  ba bữa, refresh, đổi component, history, intake, double-submit, sửa gram, xóa nhật ký demo,
  F5/logout và persistence qua app factory mới PASS. Không ghi calories khi chỉ chọn thực đơn.
- API bổ sung qua Flask test client, chỉ UserId=14: đổi món bằng câu yêu cầu, Nghĩ sau,
  revision cũ, preferences mới, V3 Generate từ template MySQL rồi refresh về V4, summary,
  gram sai và ownership PASS. Thay số đo demo 65 → 66 kg dùng activity alias LIGHT:
  BMR 1630, TDEE/TargetKcal 2241.2, nước 2310 ml, đúng round() của ProfileService Quý.
- Trong đúng app kiểm thử: đặt MAIL_SUPPRESS_SEND=True, sender example.invalid và init lại Flask-Mail
  trong bộ nhớ; SMTP/SMTP_SSL bị chặn. Probe được ghi nhận nhưng có 0 transport SMTP,
  đăng ký demo không gửi email thật. Không sửa AuthService hoặc config source.
- Chrome headless frontend 5500/backend Flask HTTP 5000 đọc MySQL thật; CDN được stub cho kiểm thử chức năng.
  Các process kiểm thử được dừng sau khi hoàn tất; suppression/cấu hình test không được lưu vào source/.env.
- Gemini thật: giới hạn một compose + một alternatives, retries=0 trong bộ nhớ; đúng 2 HTTP requests,
  cả hai HTTP 200. Compose lunch nhận 34 ứng viên MySQL đã lọc tránh cá; ID trả về thuộc tập ứng viên,
  nhưng validate_composition từ chối output: source=fallback, fallback_reason=invalid_output, **FAIL**.
  Không lưu raw output hoặc nới validation; chưa xác định chi tiết điều kiện nào trong validator bị vi phạm.
  Alternatives nhận 8 ứng viên PROTEIN MySQL, trả 3 ID hợp lệ khác nhau:
  usda_171477, usda_167904, usda_172448; source=gemini, **PASS**.
  Các lần generate còn lại dùng fallback chủ động để tránh thêm request/quota; không phải kết quả AI thật.
- Sau kiểm thử: Users 13 → 14; UserProfiles 12 → 13; MealSuggestions 27 → 30;
  MealOption/MealNutrition 81 → 90; MealComponentDish 281 → 305; NutritionMealDetails 33 → 42;
  NutritionFoodIntake 6 → 8 (demo thêm 2 record, một record soft-delete). Catalog giữ 102/63.
  Mọi record tồn tại trước backup đều còn đủ và khớp checksum; schema/FK cũ không đổi.
- Regression chạy sau migration: **148/148 PASS**, 53.981 giây, SQLite in-memory/HTTP mock,
  chặn mạng ngoài; không dùng regression suite để ghi lên MySQL thật.
- Không stage, commit, push, merge hoặc rollback phá hủy bảng. Vấn đề credential literal trong Core
  vẫn cần Quý xử lý riêng; không sửa trong migration này.

## Kiểm thử sửa compose — 2026-10-11

- Điểm lệch được xác minh: responseSchema cũ không giới hạn số choices/type/Dish ID;
  prompt chỉ yêu cầu kcal gần mục tiêu, không nêu 65–135%, giới hạn title/reason hoặc
  định nghĩa ba thực đơn khác nhau theo tập ID. Schema hợp lệ không đảm bảo qua validator.
  Raw output của lần FAIL cũ không được lưu, nên chưa thể quy lỗi đó cho một điều kiện cụ thể.
- Đồng bộ prompt/schema với validator; giữ nguyên ngưỡng kcal, giới hạn gram từng món,
  nhóm bắt buộc, kiểm tra tránh món và cách Backend tính kcal/macro. Chẩn đoán chỉ trả mã
  an toàn qua meta.fallback_diagnostic, không log raw output/text hay thông tin đăng nhập.
- 170 regression tests PASS: 148 tests cũ + 22 mới. Suite dùng SQLite in-memory/mock,
  socket bị chặn. Có test replay ID/gram đã lược bỏ văn bản AI và test tổ hợp khả thi
  cho ba bữa × bốn focus trên catalog 102 món. Không cam kết mọi mục tiêu/tùy chọn đều khả thi.
- Sau mock PASS, gọi compose thật đúng một request, retries=0: HTTP 200,
  source=gemini, cached=false, ba lựa chọn lunch cho demo UserId=15, tránh cá.
  34 ứng viên lấy từ MySQL; tất cả ID trả về thuộc tập ứng viên; không gọi alternatives lại.
- Mục tiêu 891 kcal; Backend tính ba tổng 589.1 / 591.5 / 646.5 kcal trong khoảng
  579.15–1202.85, không tuyên bố khớp mục tiêu tuyệt đối. Kcal/macro tính theo per-100g
  và gram trong MySQL; không nhận tổng dinh dưỡng từ Gemini.
- Chrome 5500/Flask 5000 hiển thị ba lựa chọn, F5 đọc lại source=gemini.
  Factory mới đọc được ba recipe/giá trị dinh dưỡng đúng từ MySQL. Không tự ghi nhật ký ăn.
  CDN được stub khi test chức năng; không kiểm chứng giao diện qua CDN thật.
- Lấy checksum toàn bộ dữ liệu có sẵn của 18 bảng ngay trước phiên test và đối chiếu sau:
  mọi dòng cũ, bao gồm lịch sử/nhật ký demo cũ, còn nguyên. Chỉ thêm tài khoản/profile demo mới,
  một MealSuggestions, ba options/nutrition/details và các thành phần tương ứng.
- SMTP suppress được kiểm tra trước đăng ký, SMTP/SMTP_SSL bị chặn, 0 transport.
  Cấu hình test chỉ trong bộ nhớ; dừng các process Chrome/Flask/frontend sau test.
- Không chạy migration/seed, không sửa Core/schema/frontend, không stage/commit/push/merge.

## Tinh chỉnh chất lượng kcal — 2026-10-11

- Đọc MySQL cho ba tổ hợp compose trước: mức kcal tối đa lần lượt 966.32, 803.08,
  1085.201. Target 891 khả thi với hai tổ hợp; tổ hợp bún/đậu phụ đạt khoảng -9.9%
  ở gram tối đa. Replay có điều chỉnh đạt 891.0 / 803.1 / 891.0, không tạo thêm kcal.
- Prompt ưu tiên ±15%, cho phép ±20% khi giới hạn tổ hợp; biên an toàn cuối vẫn 65–135%.
  Target đã theo Goal của Core. Candidate pool giữ ranking theo focus/preferences/lịch sử,
  đồng thời giữ ứng viên đủ khả năng đáp ứng năng lượng trong giới hạn tối đa 8 món/nhóm.
- Bộ mới tạo được kiểm tra schema/ID/role/gram/avoid, scale gram cùng nhau có clip min/max
  MySQL, tính lại kcal/macro rồi kiểm tra kcal cuối. Giữ nguyên món AI chọn và tính đa dạng.
  Fallback thử các nhóm bắt buộc với ba món chính/nguồn đạm khác nhau; thêm nhóm tùy chọn
  khi tổ hợp chưa đáp ứng. Không điều chỉnh cache/bộ đã chốt/lịch sử.
- Lưu recipe.calorie_adjustment và trả meta.calorie_quality. Bộ AI không đủ ba lựa chọn
  trong ±20% chuyển fallback với SELECTED_COMBINATION_ENERGY_LIMIT; nếu bộ fallback vẫn
  không đạt, trả limited=true và COMBINATION_PORTION_LIMIT, không ép gram vượt giới hạn.
- 182/182 regression tests PASS, 74.263 giây, SQLite/mock/chặn socket. Thêm 12 tests so với
  mốc 170: độ lệch, tính lại macro, phần ăn hợp lệ, ba tổ hợp khác nhau, các focus/bữa,
  target không thể đạt, cache bất biến và replay của output thật bị thiếu kcal.
- Dùng đúng hai requests compose thật, retries=0. Lần đầu HTTP 200 có ba tổng
  582.0 / 479.3 / 595.0; lựa chọn 479.3 thấp hơn 579.15 nên bị validator cũ từ chối
  trước khi fitting chạy. Fallback an toàn đạt 891 cho cả ba. Đây là bằng chứng cụ thể
  để chuyển kiểm tra kcal cuối xuống sau fitting; không bỏ kiểm tra ID/gram/avoid hoặc biên cuối.
- Sau sửa và regression PASS, lần cuối HTTP 200, source=gemini, cached=false, UserId=17:
  gà/cơm trắng/rau xào 728.5 → 891.0; heo thăn/khoai lang/collard 605.9 → 891.0;
  bò/cơm gạo lứt/rau đậu phụ 656.9 → 891.0. Độ lệch hiển thị 0.0% cả ba.
  Macro Backend tính tương ứng (carbs/protein/fat): 98.1/81.3/17.1,
  90.2/84.1/21.6, 86.2/65.3/31.4 gram. Gemini không tự trả dinh dưỡng để lưu.
- Tất cả ID thuộc 34 ứng viên MySQL đã lọc tránh cá; gram trong min/max. Chrome 5500,
  Flask 5000 hiển thị đủ ba options; F5/factory mới đọc đúng dữ liệu MySQL sau điều chỉnh.
  Checksum toàn bộ 18 bảng trước/sau phiên cuối: mọi dòng có sẵn, kể cả demo/historical intake,
  giữ nguyên. Chỉ thêm demo mới và thực đơn, không tạo nhật ký ăn, không SMTP, không migration/seed.
- Python/JavaScript syntax, HTML/script paths, diff whitespace và secret scan phần thay đổi PASS.
  Không commit/push/merge; các process kiểm thử đã dừng. Kết quả này không bảo đảm mọi tổ hợp
  catalog/mục tiêu/sở thích đều khả thi hoặc mọi lần Gemini đều tự tính kcal chính xác.

## Tối ưu khẩu phần đa tiêu chí — 2026-10-11

Đợt này thay tối ưu kcal đơn lẻ bằng điểm E + M + 0.25 × R, được mô tả trong
[tài liệu API](NUTRITION_MEAL_API.md). E ưu tiên khoảng mềm ±15%, M chuẩn hóa riêng
protein/carbs/fat theo mục tiêu bữa ăn, R phạt độ lệch gram/reference của từng món.
Tìm kiếm hữu hạn thay gram từng thành phần trong min/max MySQL, giữ nguyên ID/nhóm
Gemini chọn, avoid, nguồn provider và ba tổ hợp khác nhau. Không đổi target của Core.
Không áp dụng một giới hạn gram chung hay điều chỉnh dữ liệu catalog.

Replay chỉ đọc ba recipe đã lưu trước đó và catalog MySQL; kết quả mới ở trong bộ nhớ,
không cập nhật recipe, snapshot hoặc lịch sử. Target 891 kcal, macro mục tiêu
protein/carbs/fat 55.7/100.2/29.7 g:

| Tổ hợp | Kcal trước → sau | Độ lệch kcal sau | Protein/carbs/fat trước → sau (g) | Khối lượng trước → sau (g) |
| --- | --- | --- | --- | --- |
| Cơm trắng, gà nướng, rau xào | 891 → 764.3 | −14.22% | 81.3/98.1/17.1 → 63.4/90.6/14.9 | 770.55 → 683.11 |
| Khoai lang, heo thăn, collard | 891 → 767.1 | −13.91% | 84.1/90.2/21.6 → 67.9/83.9/17.2 | 897.13 → 729.78 |
| Cơm gạo lứt, bò, rau đậu phụ | 891 → 821.3 | −7.82% | 65.3/86.2/31.4 → 59.7/80.4/28.7 | 745.99 → 655.38 |

- Sai lệch macro chuẩn hóa tổng hợp và độ lệch khẩu phần tham khảo giảm ở cả ba.
  Điều này không có nghĩa mọi macro đều cải thiện: fat hai bộ đầu còn thiếu lần lượt
  49.83% và 42.09%, lớn hơn mức thiếu trước đó; giảm lượng thịt giúp giảm protein dư.
- Với chính ID các món đó, fat tối đa theo min/max là 21.0 và 23.7 g, không thể đạt
  29.7 g bằng điều chỉnh gram. Metadata ghi macro_feasible_ranges và độ lệch để chỉ rõ
  giới hạn tổ hợp, không tuyên bố các bộ này cân bằng macro. Các khoảng khả thi riêng
  không bảo đảm cả ba macro đồng thời đạt mục tiêu.
- Mốc phát triển này dùng tiêu chí mềm, chưa bảo đảm mọi macro đạt target. Hướng
  cải thiện tiếp theo là nâng chất lượng chọn tổ hợp món ở bước Gemini compose,
  thay vì ép gram. Dữ liệu dinh dưỡng vẫn là ước tính; thực đơn chưa được kiểm định
  dinh dưỡng và không có cam kết luôn cân bằng hoàn toàn.
- Ba nguồn đạm gà/heo/bò và các món đi kèm giữ nguyên. Các khẩu phần sau:
  rice 280.44, usda_171477 165.32, vegetables_oil 237.35;
  sweet_potato 373.07, usda_167904 192.65, usda_170407 164.06;
  usda_169704 285.73, beef 168.55, tofu_vegetables 201.10 g.
- Checksum nội dung toàn bộ 18 bảng trước/sau replay không đổi. Không chạy migration,
  seed, SQL ghi hoặc Gemini thật; 102 món và 63 template vẫn giữ nguyên.
- Chrome frontend 5500/Flask 5000 được kiểm tra với SQLite in-memory độc lập và mock:
  đăng nhập, ba bữa, refresh, đổi món, history, chọn option không cộng calories đã ăn,
  tìm món, nguồn kcal, double-submit, sửa theo snapshot cũ, F5 và logout PASS.
  Python AST 41 file, JavaScript 8 file + 1 inline, HTML/script paths PASS.
- Thêm 10 regression tests: trade-off kcal/macro/reference, phạt tăng đồng loạt,
  riêng min/max từng món, bảo toàn ID/avoid/đa dạng/snapshot, ngân sách macro còn lại
  cho cả fallback/Gemini, giới hạn fat không thể đạt, goal bằng 0 và khoảng mềm
  không tự loại bộ AI khi fallback có chất lượng thấp hơn.
- 192/192 regression tests PASS, 84.717 giây, SQLite in-memory/mock và chặn toàn bộ
  socket ngoài. Một test mới ban đầu thiếu mock compose nên đi vào fallback mặc định;
  đã sửa fixture và chạy lại toàn bộ suite, không sửa source để làm test đó PASS.
- Không sửa GeminiClient, Core/Auth/Profile, frontend, schema hoặc seed trong đợt này.
  Không stage, commit, push hoặc merge.
