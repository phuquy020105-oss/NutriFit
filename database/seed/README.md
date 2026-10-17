# Catalog món Việt — nhập bằng MySQL client

Giữ nguyên bộ dữ liệu được duyệt: **82 Food, 30 Recipe (10/10/10), 383 liên kết**, base_servings 1.00, gồm R014/R029.
Xem [dinh dưỡng và giả định](../../docs/nutrition/vietnamese-food-nutrition-data.md): cả 82 Food ESTIMATED; 4 có nguồn một phần, 78 dùng ước lượng.
JSON là bản dữ liệu đối chiếu; ba SQL là payload được MySQL thực thi. Không tự sửa gram/nutrients để xử lý xung đột.

## Các file cần giữ

| File | Vai trò |
|---|---|
| vietnamese_catalog.json | Tên, ref, dinh dưỡng và công thức được duyệt |
| vietnamese_foods.sql | Điều kiện an toàn, staging Food, START TRANSACTION, map generated Food ID |
| vietnamese_recipes.sql | Kiểm tra/chèn Recipe thiếu, map generated Recipe ID |
| vietnamese_recipe_ingredients.sql | Kiểm tra nguyên liệu, chèn cho Recipe mới, xác minh và COMMIT |

Các công cụ Python thiết lập ban đầu đã được bỏ theo quyết định bàn giao. Seed và test vẫn tái tạo được bằng quy trình dưới.
Lần dọn công cụ này không thực thi MySQL, không nhập lại hoặc tạo backup mới.

## Kết nối và cấu hình

MySQL client nhận host/port/user/database tường minh; dùng --password **không có giá trị** để client hỏi mật khẩu trực tiếp.
Không đặt mật khẩu vào command line hoặc README. Thay YOUR_MYSQL_USER trong ví dụ bằng account đã được cấp quyền.
Không thêm --force hoặc tùy chọn tự reconnect.

.env local được giữ nguyên và Git bỏ qua. Nếu thành viên cần file ghi cấu hình riêng, tự tạo bằng editor khi file chưa tồn tại, với các khóa DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD. Tự nhập credentials trên máy, không ghi đè cấu hình cũ.
MySQL client và Java **không tự đọc .env**. DatabaseConfig vẫn dùng NUTRIFIT_DB_USER/NUTRIFIT_DB_PASSWORD và URL 127.0.0.1:3306/nutrifitdb_java.
Xem [cấu hình test/Java](../../docs/nutrition/mysql-integration-setup.md).
.env, .env.*, .local-backups/ và target/ tiếp tục bị Git bỏ qua; không đưa credentials, dump hoặc log cá nhân lên Git.

## Điều kiện trước khi nhập lại

1. Chủ dự án cho phép đúng host/port/database và phạm vi chèn. Không cần nhập lại chỉ vì công cụ thiết lập đã bị xóa.
2. Xác minh database có sẵn, MySQL 8.0.16+, cấu trúc khớp schema.sql; ba bảng InnoDB, name utf8mb4_unicode_ci; FK và CHECK đúng. Không tạo lại/xóa database.
   schema.sql chứa CREATE DATABASE/USE NutriFitDB_Java: chỉ dùng để chuẩn bị môi trường mới trống được phê duyệt, hoặc bản DDL riêng được rà soát cho tên DB khác. Không chạy nguyên file trên database đang có dữ liệu.
3. Xác minh không có trigger trên ba bảng và account nhìn thấy đầy đủ metadata trigger (cần quyền TRIGGER tương ứng). Không suy ra không có trigger từ account thiếu quyền. Account seed cần SELECT, INSERT, CREATE TEMPORARY TABLES.
4. Dừng mọi writer/ứng dụng trong thời gian seed. Named lock chỉ phối hợp seed cùng khóa, không ngăn writer ngoài; schema không UNIQUE trên name/cặp Recipe–Food.
5. Kiểm tra số hàng/tên trùng/nội dung cũ. Tên mơ hồ hoặc dữ liệu khác catalog thì dừng; không xóa/sửa dữ liệu để ép nhập.
6. Trước nhập vào DB có dữ liệu cần giữ, phải có dump đã kiểm tra exit code, coverage DDL/data, kích thước/hash và footer hoàn tất; lưu ngoài Git. Không tạo/kiểm tra được backup thì dừng. Có dump không đồng nghĩa đã thử restore.
   Có thể dùng mysqldump --single-transaction --skip-lock-tables với --result-file trỏ nơi lưu riêng, credentials qua prompt. Không tạo backup mới trong đợt dọn này.

Ví dụ xác minh local từ CMD, chỉ SELECT/metadata:

~~~cmd
mysql.exe --no-defaults --protocol=TCP --host=127.0.0.1 --port=3306 --user=YOUR_MYSQL_USER --password --database=nutrifitdb_java --batch --raw --skip-force --skip-reconnect --execute="SELECT DATABASE(), VERSION(); SHOW CREATE TABLE foods; SHOW CREATE TABLE recipes; SHOW CREATE TABLE recipeingredients; SELECT 'foods',COUNT(*) FROM foods UNION ALL SELECT 'recipes',COUNT(*) FROM recipes UNION ALL SELECT 'recipeingredients',COUNT(*) FROM recipeingredients; SHOW GRANTS FOR CURRENT_USER;"
~~~

## Ghép ba seed thành một input UTF-8

Một input, một lần gọi mysql, một connection. **Không dùng SOURCE**, không mở ba connection hoặc dùng GUI tiếp tục sau lỗi.
Chạy khối PowerShell dưới từ root. Mặc định tiền tố không cho nhập vào DB chính.
Chỉ sau khi xác minh tên thực chính xác **nutrifitdb_java** và hoàn tất điều kiện/backup, tự đổi $allowMainDb thành $true.
Tên phân biệt hoa/thường phải khớp chốt SQL; gặp tên khác thì dừng xem cấu hình, không bỏ chốt.

~~~powershell
Set-Location D:\Web\NutriFit
$ErrorActionPreference = 'Stop'
$allowMainDb = $false
$utf8 = New-Object System.Text.UTF8Encoding($false)
$root = (Get-Location).Path
$files = @(
    'database\seed\vietnamese_foods.sql',
    'database\seed\vietnamese_recipes.sql',
    'database\seed\vietnamese_recipe_ingredients.sql'
)
$nl = [Environment]::NewLine
$prefix = 'SET @nf_allow_main_db = 0;' + $nl + 'SET @nf_verified_main_database = NULL;' + $nl
if ($allowMainDb) {
    $prefix = 'SET @nf_allow_main_db = 1;' + $nl + "SET @nf_verified_main_database = 'nutrifitdb_java';" + $nl
}
$sessionSql = $prefix
foreach ($file in $files) {
    $sessionSql += [System.IO.File]::ReadAllText((Join-Path $root $file), $utf8) + $nl
}
New-Item -ItemType Directory -Path (Join-Path $root 'target') -Force | Out-Null
[System.IO.File]::WriteAllText((Join-Path $root 'target\import-vietnamese.sql'), $sessionSql, $utf8)
Write-Output 'Created target/import-vietnamese.sql; SQL has NOT been executed.'
~~~

Tiền tố mặc định chỉ dùng với DB tên kết thúc _test đã được chuẩn bị/xác nhận; đổi --database trong lệnh dưới tương ứng.
Với DB chính, thiếu xác nhận thì SQL cố ý báo lỗi trước khi chèn Food; không tự retry/tắt assertion.
Các SET xác nhận phải ở cùng input với seed, không chạy ở connection khác.

## Thực thi một lần bằng CMD sau khi được phép

Sau khi tạo input với lựa chọn đúng database, mở **CMD** ở root.
Dấu < là redirect CMD; không Get-Content pipe vào native client trong PowerShell vì có thể đổi encoding.

~~~cmd
cd /d D:\Web\NutriFit
mysql.exe --no-defaults --protocol=TCP --host=127.0.0.1 --port=3306 --user=YOUR_MYSQL_USER --password --database=nutrifitdb_java --batch --raw --default-character-set=utf8mb4 --skip-force --skip-reconnect --local-infile=0 --binary-mode < target\import-vietnamese.sql
echo %ERRORLEVEL%
~~~

Client hỏi password qua console, không lấy password từ input SQL; file ghép không chứa credentials.
--no-defaults bỏ tùy chọn thông thường; dù login file được client đọc, đối số host/port/user và prompt password ở trên phải xác định đích. Kiểm tra server/đích trước khi cho phép ghi.

Phải kiểm tra exit=0 và COMMITTED. DB trống tương thích dự kiến chèn 82/30/383; dữ liệu cũ khớp có thể được tái dùng.
Đọc ref → generated ID in ra, không giả định ID bắt đầu 1/liên tục.
SELECT đối chiếu tên/bữa/active/base, năm chất, toàn bộ gram, không Recipe rỗng/FK sai với JSON/tài liệu.
Tổng catalog ánh xạ 82/30/383 không nhất thiết là tổng toàn DB nếu có dữ liệu khác.
Chạy lại có kiểm soát phải chèn 0/0/0 và giữ ID. Lỗi thì dừng/xác minh, không tự sửa dữ liệu.

## Những bảo vệ vẫn nằm trong SQL

- Chỉ DB _test hoặc DB chính chính xác nutrifitdb_java với @nf_allow_main_db=1 và @nf_verified_main_database khớp binary.
- Kiểm tra version, InnoDB, collation, trigger; STRICT_ALL_TABLES, FK/unique_checks bật; advisory lock.
- Tên duy nhất theo collation và nội dung khớp chính xác; sai tên byte/nutrients/active/Recipe metadata/nguyên liệu thì dừng. Không UPDATE/DELETE/REPLACE/INSERT IGNORE.
- Chèn Food/Recipe không truyền PK, map ID DB sinh; chỉ chèn liên kết cho Recipe mới. Recipe cũ phải đã có đúng bộ nguyên liệu, không thiếu/thừa/trùng/sai gram.
- Một START TRANSACTION trước ghi Food, một COMMIT sau kiểm tra. Chỉ DDL TEMPORARY, không DDL thường trực hoặc implicit commit xen giữa.
- Assertion lỗi NOT NULL ở strict mode. Không --force: client batch dừng/đóng connection khi lỗi trước COMMIT, rollback hàng InnoDB; AUTO_INCREMENT vẫn có thể khuyết.
- Mất kết nối sát COMMIT có thể đã ghi; SELECT xác minh trước thử lại. Không tuyên bố rollback mọi lỗi hoặc tự restore trên DB chính.

Cơ sở MySQL: [batch client](https://dev.mysql.com/doc/refman/8.0/en/mysql-command-options.html), [implicit commit](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html), [GET_LOCK](https://dev.mysql.com/doc/refman/8.0/en/locking-functions.html), [trigger metadata](https://dev.mysql.com/doc/refman/8.0/en/information-schema-triggers-table.html).

## Tự động hóa đã bỏ và phạm vi bàn giao

Không còn CLI Python tự đọc .env, đối chiếu đích trước kết nối, kiểm tra backup file/hash, ghép/gọi client, sinh fixture/chạy Maven một lệnh, hoặc validator offline toàn diện SQL/JSON/thiết kế.
Các bước xác minh/backup/ghép input/credentials/kiểm chứng kết quả nay làm thủ công theo hướng dẫn. Chỉ ghép file không đồng nghĩa đã kiểm tra schema/backup.
PowerShell tạo fixture còn kiểm tra số lượng, refs, dữ liệu cơ bản và bảng 30 tổng; Java integration test vẫn so DB với kỳ vọng JSON.
Khi sửa catalog tương lai phải review đồng bộ JSON/SQL/tài liệu và chạy test, không chỉ cập nhật một bản.

Kết quả lịch sử 2026-10-17: nutrifitdb_java, server 26.7.0; import đầu COMMITTED 82/30/383, lần hai COMMITTED 0/0/0; 20 bảng ngoài catalog không đổi.
Dump trước import và bằng chứng vẫn tại .local-backups/, không bị xóa/di chuyển; chưa thử restore.
Xem [báo cáo Java/MySQL](../../docs/nutrition/mysql-integration-verification.md) và [cách chạy test hiện tại](../../docs/nutrition/mysql-integration-setup.md).
Java production/Servlet/JSP/DAO/Service/schema/công thức giữ nguyên; Auth/Premium và hợp đồng tích hợp không đổi trong việc dọn công cụ.
