# Catalog món Việt — seed dành cho database test

**Chưa thực thi SQL.** Bộ file này chỉ được tạo và kiểm tra tĩnh ngày 2026-10-17. Không có kết quả import, rollback hoặc chạy lại trên MySQL để báo PASS.

Phạm vi được duyệt: 82 Food, 30 Recipe (10 BREAKFAST / 10 LUNCH / 10 DINNER), 383 Recipe–Ingredient, base_servings 1.00. Giữ cả R014 và R029, giữ nguyên tên/bữa/gram trong [bản thiết kế](../../docs/nutrition/vietnamese-food-catalog-review.md).
Xem [nguồn, giả định và bảng dinh dưỡng](../../docs/nutrition/vietnamese-food-nutrition-data.md): 0 VERIFIED đủ năm chỉ số; 4 Food có bốn chỉ số nguồn Việt Nam + fiber ước lượng; 78 Food còn lại ước lượng. Cả 82 mang nhãn ESTIMATED.

## File và thứ tự

| File | Vai trò |
|---|---|
| `vietnamese_catalog.json` | Dữ liệu có ref cục bộ, dinh dưỡng dạng chuỗi decimal, nguồn/giả định, công thức được duyệt |
| `vietnamese_foods.sql` | 1: điều kiện thực thi, staging 82 Food, bắt đầu transaction, ánh xạ Food |
| `vietnamese_recipes.sql` | 2: staging 30 Recipe, kiểm tra Recipe cũ, ánh xạ Recipe |
| `vietnamese_recipe_ingredients.sql` | 3: staging 383 liên kết, kiểm tra bộ nguyên liệu, chèn cho Recipe mới, xác minh, COMMIT |
| `validate_vietnamese_catalog.py` | Kiểm tra offline bằng Python chuẩn, không kết nối DB, không chạy SQL |
| `run_vietnamese_catalog.py` | Công cụ import cho lần được phép sau: kiểm tra tĩnh trước, gửi ba SQL vào **một** mysql batch process |

SQL không tự đọc JSON. Validator đối chiếu từng tuple SQL với JSON và tài liệu gốc để tránh chúng lệch nhau. Nếu cập nhật dữ liệu trong tương lai, phải duyệt và cập nhật các bản tương ứng; không chỉ sửa JSON rồi nghĩ SQL tự thay đổi.
Không có thay đổi schema, Java/JSP, Maven hoặc các bảng ngoài `foods`, `recipes`, `recipeingredients`.

## Kiểm tra tĩnh hiện tại — CMD Windows

Python 3.10+; không cần cài package, Maven hoặc kết nối MySQL. Trong repository:

```cmd
cd /d D:\Web\NutriFit
py -3 database\seed\validate_vietnamese_catalog.py --show-totals
git diff --check
git status --short --untracked-files=all
```

Checker kiểm tra: hash nội dung bản thiết kế (chuẩn hóa xuống dòng CRLF/LF), đúng danh sách/tên/trạng thái/meal_type/base/gram/hướng dẫn/thời gian; 82/30/383; tham chiếu, số dương, độ dài/DECIMAL, không NULL, không Food lặp trong một Recipe, khai báo nguồn; sự hợp lý sơ bộ 4-4-9; từng tuple SQL; 30 tổng bằng Decimal HALF_UP 3 và khớp tài liệu. Số 0 được rà soát theo giả định từng Food, không phải xét nghiệm xác nhận.

Các kiểm tra SQL là kiểm tra tĩnh có giới hạn, **không phải parser hay MySQL execution**. Chúng không chứng minh engine/privilege/transaction/collation/ID mapping hoạt động thực tế. Tương thích adapter được đối chiếu theo mã nguồn hiện tại, chưa chạy tích hợp Java.

Kết quả đã chạy tại workspace ngày 2026-10-17 với Python 3.12: validator exit 0, 82/30/383 đúng, 30 tổng khớp; AST của hai script hợp lệ; tám file mới UTF-8, không BOM/trailing whitespace, có newline cuối. `git diff --check` exit 0; các file tracked không thay đổi. File thiết kế gốc đã untracked từ trước, giữ nguyên nội dung theo hash. Không có kết quả kiểm thử database hoặc Java trong đợt này.

## Điều kiện trước một lần import được chủ dự án cho phép

1. Xác nhận host, cổng, tài khoản và **database test tách biệt, dùng được để thử nghiệm**, ví dụ `nutrifit_catalog_test`. Hậu tố `_test` chỉ là chốt tránh chọn nhầm, không chứng minh database thực sự an toàn. Không dùng DB NutriFit đang chạy, kể cả chỉ đổi tên.
2. Chuẩn bị schema khớp `database/schema.sql`, MySQL **8.0.16+**, ba bảng InnoDB, cột name `utf8mb4_unicode_ci`. Không đổi cấu trúc trong repository. **Không chạy nguyên `schema.sql` với hy vọng `--database` đổi đích:** file gốc có `CREATE DATABASE` và `USE NutriFitDB_Java`. Quản trị viên cần chuẩn bị bản DDL riêng đã rà soát, trỏ rõ DB test, rồi xác minh đích trước khi nạp. Runner không tạo database/schema.
3. Dừng ứng dụng và mọi tiến trình ghi vào DB test suốt lần seed. Named lock chỉ ngăn các seed tuân theo cùng khóa, không ngăn writer khác. Schema không UNIQUE trên name hoặc cặp Recipe–Food, nên không bảo đảm chống trùng khi writer không hợp tác chạy đồng thời.
4. Xác minh không có trigger trên ba bảng đích hoặc cơ chế khác gây ghi sang module khác. Account phải nhìn thấy đầy đủ trigger của ba bảng ([MySQL yêu cầu quyền TRIGGER trên bảng để thấy thông tin trigger](https://dev.mysql.com/doc/refman/8.0/en/information-schema-triggers-table.html)). Không chỉ dựa vào kết quả rỗng từ account thiếu quyền. Seed cũng kiểm tra metadata nhưng không thể chứng minh quyền nhìn metadata thay cho quản trị viên.
5. Account import cần SELECT, INSERT trên ba bảng và CREATE TEMPORARY TABLES trong DB test; cần quyền nhìn metadata/trigger nêu trên. Seed không dùng UPDATE/DELETE hoặc DDL thường trực. Với DB test đã có dữ liệu cần giữ, xác nhận snapshot/backup và kế hoạch khôi phục trước khi import; lần này chưa tạo hay thử phục hồi backup.
6. Dùng mysql client chính thức, kết nối mới, batch, dừng khi lỗi, không reconnect; dùng login-path lưu ngoài Git. Không chạy từng file ở ba connection, không dùng GUI tiếp tục sau lỗi, không thêm `--force`.

## Các bước import sau khi được cho phép — ví dụ CMD

Các lệnh trong phần này **chưa được chạy**. Chỉ dùng sau khi hoàn tất điều kiện trên và xác nhận chính xác đích.

1. Cấu hình login-path cho account chỉ dùng DB test; mật khẩu nhập qua prompt của MySQL, không ghi vào file seed hoặc đối số dòng lệnh:

```cmd
mysql_config_editor.exe set --login-path=nutrifit-test --host=127.0.0.1 --port=3306 --user=nutrifit_seed --password
```

2. Kiểm tra tĩnh, rồi dùng runner (đổi đường dẫn mysql.exe nếu cài nơi khác):

```cmd
cd /d D:\Web\NutriFit
py -3 database\seed\validate_vietnamese_catalog.py --show-totals
py -3 database\seed\run_vietnamese_catalog.py --database nutrifit_catalog_test --login-path nutrifit-test --mysql "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
```

Runner dùng subprocess không qua shell; đọc UTF-8 và truyền cả ba file theo thứ tự trong một stdin. `--no-defaults` đứng đầu, đồng thời bật rõ `--skip-force`, `--skip-reconnect`, tắt local-infile. Login-path vẫn được MySQL đọc từ `.mylogin.cnf`; không truyền password. Không có bước retry/cleanup tự động.

3. Xác minh exit code bằng `echo %ERRORLEVEL%`, dòng COMMITTED, số insert và bảng ref → generated ID được in ra. DB trống tương thích phải chèn **82/30/383**; DB đã có các bản ghi **khớp hoàn toàn** có thể tái dùng ID, số insert thấp hơn. Các tổng catalog ánh xạ vẫn là 82/30/383, không phải tổng toàn database nếu có dữ liệu ngoài catalog.
4. Trên DB test, chạy lại đúng runner để xác minh **0/0/0 insert**, ID không đổi, không thêm bản ghi. Kiểm tra adapter đọc đủ 30 món và Calculator khớp bảng trong tài liệu. Đây là việc còn phải thử, chưa được xác nhận hiện tại.
5. Dùng các bản DB test tách biệt cho tình huống tên trùng, tên khác hoa/dấu/khoảng trắng nhưng cùng collation, dinh dưỡng cũ khác, Recipe cũ thiếu/thừa/trùng/sai gram nguyên liệu, active=false, lỗi FK và lỗi giữa chừng. Mỗi tình huống phải dừng; kiểm tra không có hàng catalog mới còn lại sau lỗi trước COMMIT, và không thay đổi các bảng người dùng. Không tạo các tình huống này trên DB đang dùng.

## Ánh xạ, trùng lặp, lỗi và giao dịch

- F001…F082 và R001…R030 là ref tài liệu, không phải ID SQL. Food/Recipe được INSERT không truyền PK. Map tạm lấy `food_id`/`recipe_id` thực từ đúng một bản ghi tên phù hợp, sau kiểm tra nội dung. Không dùng offset, thứ tự AUTO_INCREMENT, MAX(id), LAST_INSERT_ID()+n hoặc tự chọn bản ghi đầu tiên.
- Tên chưa có: chèn mới. Một tên khớp nhưng khác bất kỳ giá trị seed nào (kể cả active, instructions, image_url): dừng. Nhiều bản ghi tên bằng nhau theo collation: dừng. Tên bằng nhau theo collation nhưng khác byte: dừng; không tự hợp nhất tên.
- Recipe cũ chỉ được tái dùng khi đã có **đúng toàn bộ** bộ nguyên liệu: cùng generated Food ID và gram, mỗi cặp đúng một hàng, không hàng thừa. Recipe cũ thiếu nguyên liệu cũng dừng, không âm thầm hoàn thiện. Recipe mới mới được chèn liên kết. Không ghi đè hoặc sửa lịch sử, preference, user, mealplan/mealentry.
- Một START TRANSACTION trước khi chèn Food; một COMMIT sau tất cả kiểm tra liên kết. Assertion cố ý chèn NULL vào cột NOT NULL dưới STRICT_ALL_TABLES để gây lỗi có tên bước. Client phải dừng ngay, thoát và đóng kết nối. Khi lỗi trước COMMIT, các thay đổi hàng InnoDB được rollback lúc disconnect; AUTO_INCREMENT có thể vẫn để lại khoảng trống ID.
- Staging/map là TEMPORARY TABLE. Tạo chúng không implicit commit nhưng bản thân DDL tạm không rollback; chúng biến mất khi đóng connection. Không có ALTER, CREATE INDEX, LOCK TABLES hoặc DDL thường trực giữa transaction.
- Nếu mất kết nối/output sát hoặc sau COMMIT, kết quả có thể đã được ghi. Không tuyên bố rollback mọi lỗi; kiểm tra trạng thái trước khi chạy lại có kiểm soát. GET_LOCK được nhả cuối file hoặc khi disconnect.
- Không mở lại cùng temporary table nhiều lần trong một câu SELECT, cũng không INSERT…SELECT từ chính bảng tạm đích. Map Recipe hiện hữu và map cuối được tách để tránh giới hạn này.
- Kiểm soát chạy lại dựa trên dữ liệu khớp, không có bảng đánh dấu seed lâu dài. Thiếu UNIQUE trong schema, writer đồng thời, bản schema khác, trigger ẩn, thay đổi dữ liệu catalog sau seed hoặc gián đoạn COMMIT là các giới hạn phải xác minh thực tế.

Cơ sở kỹ thuật: tài liệu MySQL về [implicit commit của bảng tạm](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html), [tùy chọn mysql batch/login-path/force](https://dev.mysql.com/doc/refman/8.0/en/mysql-command-options.html), [GET_LOCK](https://dev.mysql.com/doc/refman/8.0/en/locking-functions.html), [giới hạn bảng tạm](https://dev.mysql.com/doc/refman/8.0/en/temporary-table-problems.html) và [INSERT…SELECT](https://dev.mysql.com/doc/refman/8.0/en/insert-select.html).

## Giới hạn tích hợp

Chưa thay CurrentUser/session Auth, RecipeReadPort, kiểm tra Premium/Payment, DaySummary/NutritionFacts cho Dashboard. Seed chỉ cung cấp catalog; không tạo user/login/session hoặc cấp Premium. Các Food hỗn hợp không tự khai triển thành thành phần ẩn cho LIKE/DISLIKE; không dùng catalog này như bộ kiểm soát dị ứng hoàn chỉnh.

Maven, unit/integration test, deploy, import MySQL và thử rollback/rerun **không chạy trong đợt bàn giao này theo yêu cầu**. Không commit/push/merge.
