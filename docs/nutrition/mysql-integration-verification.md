# Kiểm chứng Java Nutrition với MySQL thật

Ngày: **2026-10-17**, múi giờ Asia/Bangkok. Nhánh `feature/java-nutrition`, HEAD `018ccaf`.

Đây là bằng chứng lịch sử của lượt kiểm chứng đã chạy, không phải kết quả chạy lại sau khi dọn công cụ. Hướng dẫn hiện tại không cần Python nằm ở [thiết lập integration test](mysql-integration-setup.md) và [nhập SQL bằng MySQL client](../../database/seed/README.md).

**Đã chứng minh Java đọc và tính đúng catalog. Chưa chứng minh CRUD hoặc UI Nutrition sau đăng nhập.**
Chủ dự án xác nhận chưa có tài khoản thử nghiệm; database thực tế không có user/mealplan/mealentry. Không tạo user, session Auth, Premium, dữ liệu bữa ăn hoặc database thử nghiệm để vượt qua điều kiện này.

## Môi trường và cấu hình đã dùng

| Thành phần | Giá trị thực tế |
|---|---|
| JDK | Temurin 21.0.12.1+1-LTS |
| Maven | 3.9.16 |
| Tomcat | 10.1.61 |
| MySQL server | 26.7.0 local, cổng 3306 |
| Java JDBC database | nutrifitdb_java |
| Connector/J | 9.2.0, dependency đã có trong pom.xml và WAR |
| URL trong DatabaseConfig | `jdbc:mysql://127.0.0.1:3306/nutrifitdb_java?useUnicode=true&characterEncoding=UTF-8` |

DatabaseConfig **không tự đọc .env**; nó yêu cầu `NUTRIFIT_DB_USER` và `NUTRIFIT_DB_PASSWORD`.
Trong lượt kiểm chứng đã báo cáo, công cụ thiết lập đọc cấu hình local, đối chiếu host/port/database với URL cố định và truyền credentials bằng environment riêng của tiến trình Maven/JVM. Công cụ đó đã được bỏ khi bàn giao; hiện nhập credentials trực tiếp vào prompt theo tài liệu thiết lập. Không sửa DatabaseConfig hoặc đặt mật khẩu trong argv.
Tomcat kiểm thử cũng nhận hai environment variables này trong tiến trình con. Cách này không cấu hình vĩnh viễn cho Tomcat/IDE khác; tiến trình triển khai thật phải nhận đúng environment của nó.

Account hiện dùng có quyền SELECT/INSERT/UPDATE/DELETE. Đây là xác minh quyền qua metadata; không thực thi DML để thử quyền.

## Kết quả

| Thành phần | PASS / FAIL / BLOCKED | Bằng chứng thực thi và giới hạn |
|---|---|---|
| Java DatabaseConfig → MySQL | PASS | JDBC thật và `/health/db` trả connected/nutrifitdb_java; server 26.7.0, driver 9.2.0 |
| MySQL Food/Recipe Catalog | PASS | 82 Food, 30 Recipe, 383 liên kết; tên/nutrients/active/metadata/gram khớp JSON; validator đối chiếu tài liệu gốc và bảng tổng |
| JdbcRecipeReadAdapter | PASS | listCandidates 30, mỗi bữa 10; findNutritionInput đủ 383 dòng; generated IDs lấy từ DB bằng tên không mơ hồ; BigDecimal/base/type/Food active đúng; caller Connection vẫn mở |
| NutritionCalculator | PASS | 90 trường hợp = 30 món × 0.5/1/2 phần, mỗi trường hợp đối chiếu năm chất với Python Decimal độc lập; HALF_UP scale 3; chênh lệch tối đa 0.000 |
| MealPlannerService | BLOCKED một phần | listAvailableRecipes thực tế PASS với 30 món qua DAO/JDBC và connection read-only; CRUD/snapshot lưu trong DB/tổng ngày có dữ liệu thực BLOCKED vì chưa có tài khoản thử nghiệm |
| MealHistoryService | BLOCKED | Không có user hoặc nhật ký để kiểm tra luồng thực; không gán user ID giả. Unit của MealPlanner kiểm tra history/date/tổng snapshot bằng doubles đã PASS, không thay thế kiểm thử service MySQL |
| MealRecommendationService | BLOCKED | Catalog candidate đã PASS; chưa kiểm chứng ranking/LIKE/DISLIKE/Premium với user thật. Ba unit test của service PASS với JDBC doubles cho Premium/expiry/identity |
| Maven tests | PASS | 35 unit test PASS; 94 integration test MySQL PASS; failures=0, errors=0. Lần chạy unit không opt-in còn ghi 5 skipped cho lớp integration, không tính chúng là PASS |
| Maven build | PASS | WAR `target/nutrifit.war`, BUILD SUCCESS; package dùng skipTests sau khi hai lượt test đã PASS |
| Tomcat HTTP endpoints | PASS giới hạn | Health/DB health/static assets/index 200; bốn Nutrition GET và hai POST chưa login trả 401. HTTP sau login vẫn BLOCKED |
| JSP/JavaScript UI | BLOCKED | Index JSP chạy 200, file nutrition.js/CSS tải 200 và JS khớp source; chưa render/nhấn/submit các trang Nutrition trong phiên Auth hợp lệ; không tuyên bố UI PASS |

Không có lỗi ứng dụng Nutrition được tái hiện trong phạm vi đọc thực tế. Không sửa mã production để thay đổi kết quả.

## Những gì đã kiểm thử cụ thể

Integration test `NutritionMySqlIntegrationTest` được bật riêng bằng `NUTRIFIT_MYSQL_INTEGRATION=true`; mặc định không mở database.

- Mỗi connection kiểm thử đặt readOnly=true, autoCommit=false; truy vấn xác minh `@@session.transaction_read_only=1`. Không có INSERT/UPDATE/DELETE hoặc COMMIT trong suite; connection được rollback/close sau test.
- Đọc 82 Food bằng JDBC, so năm giá trị, active và tên với JSON. Các giá trị NULL/âm hoặc ID sai sẽ làm test thất bại.
- Đọc từng Recipe, so tên/meal/base=1.00/instructions/prep/image/active; đối chiếu toàn bộ tập Food IDs và gram. Không hardcode primary key.
- Đối chiếu candidates 30 món, 10/10/10, không món hợp lệ bị loại; mỗi món có nguyên liệu đúng, không FK thiếu. DAO FoodCatalog đọc đủ 82 tên.
- Giá trị kỳ vọng được sinh vào target từ JSON bằng Python Decimal; validator trước đó đã đối chiếu một phần với bảng 30 món đã công bố. Các phần 0.5/2 tính từ tổng chưa làm tròn, không nhân lại snapshot đã làm tròn.
- Kiểm tra servings null/0/âm/quá hai số thập phân/vượt DECIMAL(8,2) bị từ chối; 0.01 và 999999.99 hợp lệ trên Recipe đọc thật trong test. Giới hạn snapshot/overflow được kiểm tra thêm bởi unit NutritionFacts/Calculator/Service.
- 13 unit MealPlannerService dùng DAO/JDBC doubles: thêm món, cộng khẩu phần Recipe trùng, rescale snapshot, history/tổng, ownership, ngày quá khứ/tương lai, thay sang món trùng, overflow, rollback và commit failure. Đây là **unit**, không phải CRUD MySQL.
- CSRF có hai unit test PASS. HTTP POST chưa Auth dừng ở 401 trước CSRF; chưa thử CSRF trong phiên đăng nhập và không gọi đó là HTTP CSRF PASS.

Fixture TSV trong target được sinh lại từ JSON và kèm SHA256; test kiểm tra hash trước khi dùng. Không thêm dependency hoặc sửa pom.xml.

## HTTP đã chạy trên WAR vừa build

Tomcat chạy với CATALINA_BASE riêng tại `target/nutrition-integration/tomcat-20261017T130741Z`, chỉ bind 127.0.0.1:18080. Đã dừng tiến trình kiểm thử sau khi hoàn tất.

| Method | Đường dẫn dưới /nutrifit | HTTP thực tế |
|---|---|---:|
| GET | /health | 200 |
| GET | /health/db | 200, connected/nutrifitdb_java |
| GET | / | 200, index JSP |
| GET | /assets/js/nutrition.js | 200 |
| GET | /assets/css/meal-planner.css | 200 |
| GET | /nutrition/meal-planner | 401 |
| GET | /nutrition/history | 401 |
| GET | /nutrition/preferences | 401 |
| GET | /nutrition/recommendations | 401 |
| POST | /nutrition/meal-planner | 401 |
| POST | /nutrition/preferences | 401 |
| GET | /WEB-INF/views/nutrition/meal-planner.jsp | 404 |
| GET | /login | 404 |

401 là kết quả đúng cho request không có session đăng nhập. Branch/WAR hiện không có route Auth login; không thể dùng request params thay cho identity của session.
Các kiểm tra 400 validation trong unit không được mô tả thành HTTP 400 đã thử với Auth; request HTTP thực tế dừng ở authentication trước.

## Bảo toàn dữ liệu và mã nguồn

Trước và sau các kiểm thử, SELECT toàn bộ bảng để tính count/digest trên nội dung đã sắp thứ tự: **cả 23 bảng giữ nguyên số hàng và digest**.
Catalog vẫn 82/30/383; users, mealplans, mealentries vẫn bằng 0. Không chạy seed, không DDL thường trực, không dùng tài khoản thật để ghi dữ liệu, không tạo fixture lỗi trên DB chính.
Không tuyên bố đã kiểm chứng rollback của DML MySQL hoặc transaction độc lập qua Servlet; phần đó cần tài khoản/DB thử nghiệm được xác nhận.

Bằng chứng riêng trên máy:

- `target/surefire-reports/TEST-*.xml`, gồm suite MySQL 94/0/0/0 và sáu suite unit 35/0/0/0.
- `target/nutrition-integration/http-verification.json` và logs Tomcat.
- `.local-backups/nutrition-integration-20261017T130210Z/before.json`, `after.json`, `verification.json`: count/digest và kết quả bảo toàn DB, không chứa hàng dữ liệu người dùng.

.env, backup, Maven cache và artifact target tiếp tục bị Git bỏ qua. Không commit/push/merge.
Java integration test và bằng chứng lượt kiểm chứng được giữ lại. Những công cụ thiết lập ban đầu đã được loại bỏ theo quyết định bàn giao sau đó; chạy lại theo tài liệu thiết lập được liên kết ở đầu báo cáo, không dùng các lệnh thiết lập cũ.

Không thay đổi src/main, schema.sql, pom.xml hoặc JSON/công thức đã duyệt. `git diff --check` không có lỗi whitespace.

## Lệnh CMD để chạy lại an toàn

Chạy từ repository bằng JDK 21/Maven 3.9.16. Sinh fixture và đặt environment cho suite MySQL theo [hướng dẫn hiện tại](mysql-integration-setup.md).
Môi trường hiện trỏ cache mặc định tới C:\.m2\repository không ghi được; đã copy cache có sẵn vào target/maven-repository. Không cần đổi cấu hình hệ thống/pom.

```cmd
cd /d D:\Web\NutriFit
mvn.cmd -B -o -Dmaven.repo.local=D:\Web\NutriFit\target\maven-repository test
mvn.cmd -B -o -Dmaven.repo.local=D:\Web\NutriFit\target\maven-repository -DskipTests package
git diff --check
git status --short --untracked-files=all
```

Khối CMD trên chỉ chạy unit test/build; suite MySQL mặc định bị skip. Để chạy lại 94 trường hợp đọc thật, thực hiện các khối PowerShell trong tài liệu thiết lập.
Nếu target đã clean thì sinh lại fixture và chuẩn bị cache Maven ghi được. Không cần nhập lại seed khi catalog đã có. Không truyền giá trị mật khẩu bằng -D hoặc đối số dòng lệnh; cấu hình environment riêng cho Tomcat/IDE khi triển khai.

## Cảnh báo và phụ thuộc còn lại

- Lệnh Maven đầu tiên thất bại vì local repository không ghi được; chạy lại với cache workspace đã thành công. Đây là vấn đề môi trường, không sửa code Nutrition.
- Surefire 3.5.2 tạo `.dumpstream`: `Boot Manifest-JAR contains absolute paths ... 'other' has different root`. Có đường dẫn C:/D: trong quá trình dựng classpath Windows. Hai suite vẫn BUILD SUCCESS, không failures/errors; giữ lại file cảnh báo, không xóa lặp hoặc tắt kiểm tra JVM.
- Tomcat cảnh báo tạo SecureRandom mất khoảng 5 giây; startup và request thực tế vẫn thành công. Log TLD scan là INFO. Git có cảnh báo LF → CRLF theo cấu hình working copy.
- Auth cần route đăng nhập, tài khoản thử nghiệm riêng và session chính thức (`userId`/`authVersion` kiểu Long, role/fullName kiểu String); AuthFilter phải xác minh authVersion. Không tạo session giả.
- CRUD, thay món/khẩu phần, snapshot đã lưu, duplicate/ownership trên DB và history có dữ liệu phải thử tiếp trên tài khoản hoặc DB test được chuẩn bị/xác nhận. Không suy ra chúng PASS từ test đọc catalog.
- Payment cần xác nhận hợp đồng Premium/expiry và tài khoản thử Premium; LIKE/DISLIKE/ranking cần preference thực trên tài khoản test. Ba unit premium hiện dùng doubles.
- Food/Recipe vẫn dùng RecipeReadPort/JdbcRecipeReadAdapter; cần duy trì ID, trạng thái cân/gram và năm chất khi tích hợp owner. Dashboard/Profile cần user và dữ liệu nhật ký/target thật để kiểm tra luồng DaySummary đầy đủ.

Backend đọc catalog và Calculator đã có bằng chứng tích hợp MySQL. Toàn bộ luồng người dùng vẫn cần Auth và điều kiện CRUD an toàn trước khi xác nhận hoàn tất tích hợp nhóm.
