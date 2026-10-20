# Database NutriFit

## Bộ khởi tạo hiện hành

- `schema.sql`: schema gốc 23 bảng và 3 danh mục/47 bài tập mẫu, được giữ để tương thích.
- `migrations/20261017_add_users_auth_version.sql`: bổ sung version phiên đăng nhập cho database cũ; script này chọn database local.
- `migrations/20261020_password_reset_otps.sql`: bảng OTP khôi phục mật khẩu. Cùng `auth_version`, đây là cấu trúc ứng dụng hiện hành **24 bảng**.
- `seed/catalog.json`: **nguồn catalog duy nhất** — 100 Food, 60 Recipe, 607 Ingredient, 20 món mỗi bữa. Giá trị trên 100g phần ăn được, gram theo trạng thái sống/chín ghi trong mỗi Food; `base_servings=1.00`.
- `seed/provenance.json`: nguồn/phương pháp/độ tin cậy 500 giá trị dinh dưỡng và checksum 60 ảnh. Có 103 giá trị ESTIMATED ở 35 Food; không đồng nhất chúng với kết quả kiểm nghiệm.
- `seed/premium-plans.sql`: 2 gói mẫu phục vụ VNPay Sandbox, không phải bảng giá bắt buộc cho production.
- `seed/CatalogSeed.java`: công cụ JDBC local, dùng PreparedStatement và generated IDs; không giả định số ID giống máy khác.

Không có dump dữ liệu người dùng. Dữ liệu nghiên cứu và công cụ go-live một lần không cần cho khởi tạo; phiên bản cũ có thể tra trong Git history.

## Khởi tạo trên MySQL local sạch

Làm theo phần cấu hình/build trong [README](../README.md), sau đó:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Init
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Verify
```

Tool chỉ cho host `127.0.0.1`/`localhost`, đích `nutrifitdb_java` hoặc tên dạng `nutrifit_*_test`. Không hỗ trợ Aiven. `Init` từ chối database đã có bảng, tạo schema và dữ liệu mẫu. DDL MySQL auto-commit: nếu khởi tạo DDL bị lỗi, dừng và kiểm tra các bảng đã tạo, không tự retry hoặc tự xóa. Không chạy tool này trên database đang sử dụng để nâng cấp schema.

Sau bước DDL, cả catalog được ghi trong **một transaction**. Food/Recipe có cùng tên phải tương đương từng giá trị; gram và tập nguyên liệu phải khớp. Nếu khác thì rollback, không ghi đè, không xóa. Chạy `Seed` lại trên đúng bộ dữ liệu sẽ chèn 0 bản ghi; `Verify` chỉ đọc. Công cụ giữ named lock theo database để từ chối hai lần setup chạy đồng thời.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Seed
```

Kết quả mong đợi: 100/60/607, 20 món mỗi bữa, đủ ảnh, không orphan. ID có thể có khoảng trống do rollback/auto-increment, đó không phải duplicate. Tất cả users, nhật ký, hội thoại và giao dịch vẫn rỗng khi khởi tạo mới; người dùng tự đăng ký qua website.

## Kiểm thử database riêng

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Test -Database nutrifit_catalog_test
```

Cần database test chưa có bảng. Test gây lỗi sau20 lần ghi để chứng minh rollback, nhập lại đủ catalog, chạy lần hai0writes và thử conflict trong transaction rồi rollback. Kiểm tra24bảng, foreign keys, NutritionCalculator, ảnh, dữ liệu riêng tư trống và dữ liệu Workout/gói mẫu. Không tự DROP database test. Mật khẩu được nạp từ `.env` hoặc `-EnvFile` private, không truyền trên command line.

## Database đã có dữ liệu

Dừng trước khi chạy khởi tạo. Backup và thử phục hồi trên database riêng, đối chiếu schema rồi lập migration cụ thể theo phiên bản nguồn. Không áp dụng lại seed để ghi đè Food/nội dung Recipe đã sửa. Công cụ khởi tạo không cập nhật Aiven và không chạm snapshot `mealentries` đã lưu. Không cần migration production cho đợt cleanup source này.

Sau khi database test đã tồn tại, có thể kiểm tra lại mà không khởi tạo/xóa dữ liệu:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-local.ps1 -Action Check -Database nutrifit_catalog_test
```

`Check` chỉ cho database test không có users/mealentries. Các Food fixture thử nghiệm có tên riêng được rollback sau20lần ghi, trước bước Recipe; conflict cũng rollback. Sau đó đối chiếu lại toàn bộ500giá trị dinh dưỡng/60Recipe/607gram, chạy SQL history bằng CTE chỉ đọc. Không tự xóa/recreate database test.
