# Vietnamese Catalog V2 — review và import 11 món

## Batch tiếp nối danh mục tuyển chọn

`setup/drafts/vietnamese_catalog_v2/completion_batch.json` chỉ có 28 món mới
READY_ESTIMATED, không bao gồm 11 ID batch đầu hoặc cập nhật `pho_beef`.
Baseline kiểm tra: 113 active; sau insert đủ batch: 141 active, 99/100 ID tuyển chọn.
`vn_com_tam_suon_bi_cha` còn PENDING do thiếu profile phù hợp cho bì heo luộc;
không thay bằng bì chiên/gelatin. Các hồ sơ PENDING của ID cũ không làm vô hiệu
các bản ghi runtime hiện có và không được dùng để cập nhật chúng.

Công thức/giả định và nguồn nằm trong DRAFT; helper offline
`setup/complete_vietnamese_catalog_v2.py --usda-archive <official-SR-Legacy-2018-zip>`
tái lập số liệu bằng validator hiện có. Không truy cập HTTP/MySQL trong helper.
Nguyên liệu proxy được khai báo; calories/macros ước tính, không bảo đảm dị ứng.

Dùng quy trình backup A dưới đây, sau đó chạy một lần mỗi lệnh:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\completion_batch.json
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\completion_batch.json --check-db --database NutriFitDB
# Chỉ sau backup và dry-run đạt, đúng phê duyệt hiện tại:
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\completion_batch.json --apply --database NutriFitDB --backup $catalogBackupPath
```

Verify bằng SELECT: đủ 28 ID khớp manifest; 113 hàng cũ, `pho_beef`, 63 templates
và snapshot/intake/history có checksum trước/sau không đổi. Chỉ INSERT trong
transaction; không DDL/seed toàn catalog. Nếu lỗi trước commit, rollback transaction;
sau commit dừng, không tự xóa/restore dump. Quy trình E chỉ áp dụng các ID thực sự
đã insert và cần phê duyệt riêng sau kiểm tra tham chiếu JSON.

Các mục bên dưới lưu quy trình batch đầu 11 món, không phải lệnh seed lại 102 món.

Trạng thái: đã chuẩn bị, **chưa được duyệt ghi MySQL**. Các lệnh backup, apply
và rollback dưới đây chưa được chạy. Không chạy `setup/create_database.sql`.
Không đổi schema, `pho_beef`, 102 ID cũ hoặc 63 legacy templates.

## Batch và contract

Manifest: `setup/drafts/vietnamese_catalog_v2/review_batch.json`.
Chỉ `dishes` gồm 11 món mới READY_ESTIMATED được import. `review_existing` chỉ là
đề xuất, loader không đưa nó vào repository. Không import 28 PENDING.

| Dish ID | Nhóm | Bữa planner |
|---|---|---|
| vn_thit_kho_tieu | PROTEIN | lunch, dinner |
| vn_thit_kho_trung | PROTEIN | lunch, dinner |
| vn_ca_loc_kho_to | PROTEIN | lunch, dinner |
| vn_dau_phu_sot_ca_chua | PROTEIN | lunch, dinner |
| vn_rau_muong_xao_toi | VEGGIE | lunch, dinner |
| vn_cai_ngot_luoc | VEGGIE | lunch, dinner |
| vn_cai_thia_xao_nam | VEGGIE | lunch, dinner |
| vn_canh_rau_ngot_thit_bam | SOUP | lunch, dinner |
| vn_canh_bi_dao_thit_bam | SOUP | lunch, dinner |
| vn_canh_ca_chua_trung | SOUP | lunch, dinner |
| vn_bun_rieu_cua | MAIN | breakfast |

Bún riêu là món hoàn chỉnh; composition rules hiện tại chưa hỗ trợ MAIN cho
lunch/dinner. Quick Food vẫn có thể ghi món hoàn chỉnh vào nhật ký bữa khác.
Không tính thêm các thành phần của tô nếu đã ghi cả tô.

## Kiểm tra đã thực hiện

MySQL local `127.0.0.1:3306`, database trả tên `nutrifitdb` (Windows chuẩn hóa
tên của NutriFitDB). Catalog: 102 total/active; bảng dùng InnoDB. 11 ID chưa tồn
tại, không có tên xung đột theo normalization chữ hoa/thường, dấu và khoảng trắng.

Mapping thực tế: DishId VARCHAR(64), NameVi VARCHAR(200), gram DECIMAL(9,2),
kcal/P/C/F/fiber DECIMAL(10,4), JSON lưu LONGTEXT, Estimated/IsActive/DataVersion INT.
Các số batch khớp precision/scale; fiber NULL được giữ. Không có FK SQL trực tiếp
trỏ đến catalog; **snapshot JSON vẫn có tham chiếu cần kiểm tra khi rollback**.

Seed CLI mới chỉ mở database khi có `--check-db` hoặc `--apply`.
`--check-db` chạy transaction READ ONLY rồi rollback. `--apply --batch` yêu cầu
backup SQL không rỗng ngoài repository và dùng mapping của repository hiện tại.
Loader kiểm tra đủ 11 ID READY_ESTIMATED, checksum seed baseline và khớp DRAFT.
Checksum seed dùng JSON chuẩn hóa UTF-8/sorted keys, nên checkout LF/CRLF không
làm báo lỗi baseline giả. Byte checksum cũ được giữ trong manifest để truy nguyên.
ID đã tồn tại với dữ liệu giống batch được bỏ qua; khác dữ liệu hoặc trùng tên
thì dừng. Không ghi đè. Các insert và kiểm tra sau insert nằm cùng transaction.

`apply_authorized=false` trong manifest ghi trạng thái review; không phải hệ
thống phân quyền. Tham số `--apply` chỉ được dùng sau phê duyệt của người dùng.

## A. Backup — chỉ chạy sau phê duyệt

Chạy trong terminal của bạn để nhập password tại prompt `-p`; không đưa password
vào lệnh, chat, file hoặc Git. Dừng các thao tác ghi khác trong thời gian backup,
import và đối chiếu để baseline không thay đổi. Không tự dừng server ở nhiệm vụ này.

```powershell
Set-Location D:\Web\NutriFit
$catalogBackupDir = 'D:\NutriFitBackups'
New-Item -ItemType Directory -Path $catalogBackupDir -Force | Out-Null
$catalogBackupPath = Join-Path $catalogBackupDir ('NutriFitDB_before_v2_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.sql')
$catalogDumpExe = (Get-Command mysqldump.exe -ErrorAction Stop).Source
& $catalogDumpExe --host=127.0.0.1 --port=3306 --user=root -p --single-transaction --routines --triggers --events --no-tablespaces --databases NutriFitDB --result-file=$catalogBackupPath
if ($LASTEXITCODE -ne 0) { throw 'Backup failed; do not import' }
if (!(Test-Path -LiteralPath $catalogBackupPath) -or (Get-Item -LiteralPath $catalogBackupPath).Length -eq 0) { throw 'Empty/missing backup' }
Get-FileHash -LiteralPath $catalogBackupPath -Algorithm SHA256
```

Không dùng PowerShell `>` để chuyển dump, tránh vấn đề encoding. File dump chứa
dữ liệu riêng tư, phải ở ngoài repository. Helper chỉ kiểm tra cấu trúc tối thiểu
của backup, không chứng minh backup mới nhất hay restore thành công. Phải tạo
backup mới ngay trước import; nếu cần chứng minh khả năng phục hồi, thử trên
server/database riêng sau phê duyệt. Không restore toàn dump lên DB đang dùng.

## B. Validate-only và dry-run database

```powershell
.\.venv\Scripts\python.exe -X utf8 -B setup\validate_vietnamese_catalog_draft.py
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\review_batch.json
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\review_batch.json --check-db --database NutriFitDB
```

Hai lệnh đầu không kết nối SQL. Lệnh cuối chỉ đọc. Baseline đã kiểm tra: 102 active,
11 pending IDs, 0 already-matching, dự kiến 113 active. Lưu kết quả dry-run, checksum
manifest và đường dẫn/checksum backup vào nhật ký ngoài Git để biết chính xác ID
nào chưa tồn tại trước import. Nếu baseline hoặc nội dung thay đổi, review lại.

## C. Import thật — CHƯA CHẠY

Chỉ sau khi được duyệt ghi NutriFitDB và hoàn thành A/B:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\review_batch.json --apply --database NutriFitDB --backup $catalogBackupPath
if ($LASTEXITCODE -ne 0) { throw 'Import failed; stop and inspect before any retry' }
```

Kỳ vọng inserted.dishes=11, inserted.menus=0. Không append PENDING vào seed gốc.
Không cập nhật `pho_beef`. Lỗi trước commit rollback DML trong transaction; lỗi
kết nối trong/ sau commit có thể làm trạng thái commit chưa rõ, phải dry-run/verify
lại, không giả định mọi lỗi đều chắc chắn chưa ghi. Không chạy migration/DDL.

## D. Verify sau import

```powershell
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py --batch setup\drafts\vietnamese_catalog_v2\review_batch.json --check-db --database NutriFitDB
mysql --host=127.0.0.1 --port=3306 --user=root -p --database=NutriFitDB
```

Check-db phải trả 113 active, pending_ids rỗng, already_matching_ids đúng 11;
nó so sánh tên, role, meal eligibility, gram, toàn bộ nutrient và provenance.
Các truy vấn tại MySQL CLI chỉ đọc:

```sql
SELECT DATABASE();
SELECT COUNT(*) AS total, SUM(IsActive=1) AS active FROM NutritionFoodCatalog;
SELECT COUNT(*) AS legacy_total FROM NutritionLegacyMenus;
SELECT DishId, NameVi, ComponentType, PreparationState, ReferenceGrams,
       MinGrams, MaxGrams, KcalPer100G, ProteinPer100G, CarbsPer100G,
       FatPer100G, FiberPer100G, Estimated, IsActive, MealTypesJson
FROM NutritionFoodCatalog
WHERE DishId IN (
 'vn_thit_kho_tieu','vn_thit_kho_trung','vn_ca_loc_kho_to',
 'vn_dau_phu_sot_ca_chua','vn_rau_muong_xao_toi','vn_cai_ngot_luoc',
 'vn_cai_thia_xao_nam','vn_canh_rau_ngot_thit_bam','vn_canh_bi_dao_thit_bam',
 'vn_canh_ca_chua_trung','vn_bun_rieu_cua') ORDER BY DishId;
```

Đối chiếu 102 bản ghi cũ, `pho_beef`, 63 templates, meal/snapshot/intake/history
với trước import. Test lại APIs bằng tài khoản demo sau phê duyệt; không gọi Gemini
thật hoặc gửi email. Rerun cùng batch sau review không được tăng số dòng (inserted=0).

## E. Rollback — đề xuất, CHƯA CHẠY

Ưu tiên rollback transaction nếu chưa commit. Sau commit, dừng Backend và mọi
writer trước khi kiểm tra tham chiếu để tránh khoảng trống check-then-delete:
catalog không có FK bảo vệ các tham chiếu nằm trong JSON. Chỉ xóa sau phê duyệt
riêng và chứng minh 11 ID dưới đúng là ID đã thêm từ nhật ký dry-run/import.
Nếu đã có reference, dừng; đề xuất deactivate đúng ID mới hoặc giữ dữ liệu và
fix forward, không xóa history. Không deactivate món cũ.

Tại MySQL CLI, kiểm tra đúng database và nội dung khớp manifest trước. Sau đó:

```sql
START TRANSACTION;
SET @v2_ids = JSON_ARRAY(
 'vn_thit_kho_tieu','vn_thit_kho_trung','vn_ca_loc_kho_to',
 'vn_dau_phu_sot_ca_chua','vn_rau_muong_xao_toi','vn_cai_ngot_luoc',
 'vn_cai_thia_xao_nam','vn_canh_rau_ngot_thit_bam','vn_canh_bi_dao_thit_bam',
 'vn_canh_ca_chua_trung','vn_bun_rieu_cua');

SELECT COUNT(*) INTO @v2_referenced
FROM NutritionFoodCatalog c
WHERE JSON_CONTAINS(@v2_ids, JSON_QUOTE(c.DishId))
AND (
 EXISTS (SELECT 1 FROM NutritionMealDetails m WHERE
   JSON_SEARCH(m.RecipeJson, 'one', REPLACE(c.DishId, '_', '!_'), '!', '$**.dish_id') IS NOT NULL)
 OR EXISTS (SELECT 1 FROM NutritionFoodIntake i WHERE
   JSON_SEARCH(i.SnapshotJson, 'one', REPLACE(c.DishId, '_', '!_'), '!', '$**.dish_id') IS NOT NULL)
 OR EXISTS (SELECT 1 FROM NutritionLegacyMenus l WHERE
   JSON_SEARCH(l.TemplateJson, 'one', REPLACE(c.DishId, '_', '!_'), '!', '$**.dish_id') IS NOT NULL)
);
SELECT @v2_referenced AS referenced_batch_ids;
```

Nếu reference >0 hoặc query lỗi: `ROLLBACK;` và dừng. Chỉ khi bằng 0, mọi writer
đã dừng và danh sách ownership đã xác minh, câu xóa được giới hạn đúng 11 ID:

```sql
DELETE FROM NutritionFoodCatalog
WHERE @v2_referenced = 0 AND JSON_CONTAINS(@v2_ids, JSON_QUOTE(DishId));
SELECT ROW_COUNT() AS deleted_batch_rows;
-- Nếu deleted_batch_rows != 11: ROLLBACK; rồi điều tra.
-- Chỉ COMMIT sau khi xác minh đúng 11 dòng và tất cả điều kiện trên.
```

Không chạy rollback này trong nhiệm vụ chuẩn bị. SQL JSON_SEARCH đã escape `_`
vì underscore là wildcard; ID batch không có `%`/`!`. Cú pháp JSON reference được kiểm
chứng bằng SELECT với payload giả trên MySQL local; thao tác DELETE/COMMIT và
restore chưa được thử.

## Kết quả tests cho bản chuẩn bị

310/310 regression PASS trong 139,55 giây. Có 36 tests DRAFT và 14 tests batch/
import preparation; tất cả SQL ghi chỉ chạy trong SQLite in-memory, HTTP/SMTP
mock và kết nối mạng ngoài/MySQL bị chặn. Syntax/JSON/whitespace/secret được
kiểm tra trước staging. Không restore backup, apply batch hay rollback MySQL.

`baseline_replay.json` là replay lịch sử Phase 1 khi 40 DRAFT còn PENDING, được
giữ nguyên để bảo toàn nghiên cứu; nó không mô tả trạng thái READY_ESTIMATED mới.
