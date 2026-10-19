# Production readiness — STAGING_READY, chưa PRODUCTION_READY

Mốc2026-10-19, continuation từf04b2da. Chủ dự án chưa cho phép ghi manifest mới lên Aiven. Không xin go-live cho dữ liệu chưa qualified; không có quyền UPDATE/INSERT/DELETE production hiện tại.

| Gate | Trạng thái | Bằng chứng / phần còn thiếu |
|---|---|---|
| Truy xuất nguồn/normalization | PARTIAL | 70/82 đủ số,51/98missing giải quyết;47missing/12foods còn lại; VERIFIED0 |
| Catalog A baseline | PASS snapshot | Aiven SELECT-only24tables/82/30/383,30images,VERIFY_IDENTITY TLSv1.3,khớp backup catalog |
| Qualified B30 | BLOCKED | Chỉ18source-complete recipe comparisons; source/cooking/proxy signoff chưa đủ |
| Qualified C60 | BLOCKED | 24method-reviewed staging designs,6large-solid portions pending; không phát hành partial30 mới |
| Hình ảnh mới | PASS STAGING | 30unique800x450WebP,2.125MB,AI rights/disclosure/prompt/hash,không nằm WAR hoặc activeDB URLs |
| Benchmark | PASS descriptive only | 432cases/dataset;A598.575/B468.238/C167.395mean absolute kcal error; không chứng minh source đúng |
| Existing MySQL local delta | PASS | SELECT before;10+1Foodupdates;noDDL/seed;rollback/conflict/idempotency0writes/history/JDBC/30imageURLrollback |
| Full tests | PASS | 114JUnit/32Python/14JS,JSP0errors,validator/cache/SQLbaseline |
| Backup catalog hiện có | PASS SHA/data read | NgoàiGit,JSON/SQLchecksum và đối chiếu catalog;không phải backupfullDB |
| Full backup + restore rehearsal | NOT RUN | Phải làm mới trước go-live và phục hồi thử vào database riêng |
| Release manifest/production SQL | BLOCKED | Có versioned candidate plan/diff,không sinh qualified B/C hoặc SQL thực thi khi gates thiếu |
| Quyền ghi production | NO | Hold của chủ dự án vẫn có hiệu lực |
| DEPLOYED dữ liệu mới | NO | Aiven giữ catalog30 cũ |

## Thành phẩm đã chuẩn bị

`database/staging/food-quality-v1/release/` có A-baseline,release-manifest và candidate-migration-plan. B/C thăm dò và SHA nằm trong manifest. Plan mô tả66Foodupdates,18newFood,30newRecipe,224newlinks; không có thay đổi user/role/subscription/payment/history. Existing IDs bảo toàn; new IDs phải lấy generated keys sau exact-name/meal-type mapping, không đoán AUTO_INCREMENT.

`FoodQualityReadOnly.java` chỉ SELECT/SHOW và kiểm backupSHA,target,TLS/CA/hostname; `LocalQualityDelta.java` chỉ ghi đúng database test đã chỉ định. Không có production writer được cấp quyền. Cờ --production của prepare_release.py phải FAIL trước khi sửa output ở trạng thái hiện tại; thay flag trongJSON không thay thế qualification/review/approval.

## Trước một lần go-live riêng trong tương lai

1. Giải quyết hoặc chuẩn hóa có căn cứ47giá trị thiếu; review proxy F024/F032/F075/F076/F082 và nước dùng/yield/oil. Giữ source-backed estimates minh bạch; không yêu cầu laboratory proof cho mọi món, nhưng không bỏ qua sai định danh/raw-cooked hoặc bất định quan trọng.
2. Hoàn thành6review suất đặc; cập nhật gram chỉ có lý do/phương pháp, không để tăng điểm; tái tính NutritionCalculator, same-cohort A/B/C và localdelta trên version cụ thể. Phải đủ toàn bộ30 món mới, không nhập một phần.
3. Tạo final qualified B/C, diff và production migration thực thi được sau khi gates dữ liệu đạt. Ràng buộc exact-before/equivalent-after, active/name/type/grams, stable IDs và hashes;unexpected state hoặc SQLerror phải dừng, khôngmysql--force/auto-retry/overwrite.
4. Fresh SELECT-only Aiven đúngnutrifitdb/hostname/27047,VERIFY_IDENTITY,CA đúng, schema/engine/InnoDB/FKs tương thích. So hàng và metadata với manifest; thay đổi ngoài dự kiến phải review, không tự sửa về snapshot.
5. Tạo backup đầy đủ mới vào thư mục riêng ngoàiGit, bằng công cụ nạp secret an toàn/option file ACL hoặc JDBC properties; không password argv/log. Kiểm checksum và phục hồi thực sự vào database local/test mới có target riêng được duyệt. Ghi version/tables/counts/FKs/collation/canonical row hashes và làm bằng chứng recovery. Backup cũ không thay thế bước này.
6. Xin một xác nhận rõ ràng cho manifest final(SHA) và target sau khi đạt PRODUCTION_READY. Hold hiện tại không tự hết hiệu lực vì có task tiếp tục hoặc codepush.
7. Đưa đủ assets đã duyệt vào src/main với manifestquyền/alt/AI disclosure;buildtest/push, xác minh Render chạy đúng SHA và30URLs trả200/hash đúng trước khi ghi image_url DB. Staging assets hiện không nằm runtime.
8. Một transaction DML:lock/catalog preconditions,parameterized updates/inserts,generated ID mapping,FK/nutrient/metadata verify trướcCOMMIT. KhôngDDL,DROP,DELETE,TRUNCATE hoặc sửa snapshot. Nếu lỗi trướcCOMMIT rollback; mất kết nối/commit không rõ phải read-only điều tra, khôngretry mù.
9. PostSELECT:100Food/60Recipe/607links đã mapped,20/meal,active/PK/FK/gram/image/nutrient/calc đúng; history/user/payment invariants không đổi; lần chạy thứhai0write đúng manifest. Không gọi stage/deploy PASS chỉ bằngCOUNT hoặchealth200.

## Recovery và dữ liệu sau go-live

TrướcCOMMIT: rollback toàn bộ DML, không cố hàn dữ liệu bằngDELETE. SauCOMMIT: dừng phát hành gợi ý mới, chụp thêm read-only trạng thái và kiểm xem recipe mới đã được tham chiếu chưa. Phục hồi nutrient catalog chỉ từ exact-after sang approved-before trong transaction được review; giữ nguyên snapshotmealentries. Không xóa recipe/food đang được tham chiếu, không restore đè fullDB làm mất giao dịch/người dùng mới. Nếu cần loại món mới, ưu tiên forward-recovery/deactivate theo kế hoạch riêng có xác nhận và kiểm FK/đọc lịch sử. Không tự chạy recovery production trong task này.

Khi backup restore rehearsal và manifest final chưa có, recovery chỉ là PLAN, chưa VERIFIED. STAGING_READY khácPRODUCTION_READY khácDEPLOYED. [Báo cáo](final-data-quality-report.md) và [điểm tiếp tục](data-quality-progress.md) chứa evidence và giới hạn hiện tại.
