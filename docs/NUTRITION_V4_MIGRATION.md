# Migration Nutrition V4 — cần phê duyệt trước khi áp dụng MySQL

Migration: [001_nutrition_v4.sql](../setup/migrations/001_nutrition_v4.sql).
Đã áp dụng MySQL local ngày 2026-10-10 sau phê duyệt: 14 → 16 bảng,
backup D:\NutriFitBackups\NutriFitDB_before_v4_20261010_230700.sql (52.201 byte).
Đối chiếu toàn bộ cấu trúc và dữ liệu 14 bảng trước/sau migration: không đổi.
Hướng dẫn dưới đây dùng cho máy/database chưa có V4; không chạy lại trên database
đã có hai bảng mới.
Không chạy lại setup/create_database.sql vì script đó có DROP TABLE.

## Phạm vi

- NutritionMealDetails: recipe JSON của mỗi MealOption; OptionId là PK/FK tới
  MealOption, cascade khi option được refresh theo nghiệp vụ Meal hiện có.
- NutritionFoodIntake: nhật ký ăn thực tế, FK UserId tới Users, snapshot JSON,
  ngày/giờ, version, deleted; unique (UserId, RequestKey) chống retry ghi trùng;
  index (UserId, IntakeDate, Deleted) cho truy vấn theo ngày.
- Chỉ thêm hai bảng và một index. Không ALTER bảng gốc, seed hoặc xóa dữ liệu.
  14 bảng hiện tại thành 16. V3 đọc và chạy khi chưa có migration; V4 trả 503
  V4_MIGRATION_REQUIRED thay vì tự tạo bảng.

## Kiểm tra trước

1. Dừng thao tác ghi từ frontend/backend để backup và so sánh được nhất quán.
2. Xác nhận cấu hình local mysql+pymysql, 127.0.0.1:3306, NutriFitDB.
3. Dùng MySQL CLI và nhập mật khẩu tại prompt, không truyền mật khẩu trong lệnh:

```powershell
mysql -h 127.0.0.1 -P 3306 -u root -p NutriFitDB
```

```sql
SELECT DATABASE(), @@hostname, @@port, @@lower_case_table_names;
SHOW TABLES;
SHOW TABLE STATUS WHERE Name IN ('Users','MealOption','users','mealoption');
SELECT COUNT(*) FROM Users;
SELECT COUNT(*) FROM UserProfiles;
SELECT COUNT(*) FROM MealSuggestions;
```

Windows local với lower_case_table_names=1 có thể trả `nutrifitdb` và tên bảng
viết thường; chỉ chấp nhận cùng tên database theo chế độ đó. Không tiếp tục
nếu trỏ server/database khác. Xác nhận đủ 14 bảng, Users/MealOption dùng InnoDB
và PK INT tương ứng. Kiểm tra cả hai bảng Nutrition* chưa tồn tại; nếu đã có,
dừng để review cấu trúc thay vì dùng IF NOT EXISTS hoặc reset.

## Backup bắt buộc

Tạo thư mục backup ngoài repository, ví dụ D:\NutriFitBackups, và dùng tên file mới
có thời điểm tạo. Không đưa backup chứa dữ liệu tài khoản vào Git hoặc chat.
Lệnh tham khảo (thay đường dẫn file và bảo đảm thư mục đã tồn tại):

```powershell
mysqldump -h 127.0.0.1 -P 3306 -u root -p --single-transaction --routines --triggers --no-tablespaces --result-file=D:\NutriFitBackups\NutriFitDB_before_v4_YYYYMMDD_HHMMSS.sql NutriFitDB
```

Xác nhận exit code 0, file tồn tại và không rỗng. Giữ backup cục bộ; không hiển thị
nội dung có dữ liệu riêng tư. Backup không được tự ghi đè bằng tên file cũ.
Nên kiểm chứng khả năng restore ở database khác nếu cần; tuyệt đối không restore
đè database đang dùng trong bước migration.

## Áp dụng — chỉ sau khi người dùng phê duyệt

Ở MySQL CLI đã kết nối đúng database, kiểm tra SELECT DATABASE() thêm lần nữa,
sau đó chạy file độc lập:

```sql
SELECT DATABASE();
SOURCE D:/Web/NutriFit/setup/migrations/001_nutrition_v4.sql;
```

File không có USE; database hiện hành phải đúng trước SOURCE.
MySQL DDL có thể commit từng câu; nếu một CREATE thất bại, dừng và báo phần đã
tạo. Không tự DROP bảng hoặc thay thiết kế để thử lại. Không coi transaction
bao quanh cả file là rollback chắc chắn cho MySQL DDL.

## Kiểm tra sau

```sql
SELECT DATABASE();
SHOW TABLES;
SHOW CREATE TABLE NutritionMealDetails;
SHOW CREATE TABLE NutritionFoodIntake;
SHOW INDEX FROM NutritionFoodIntake;
SELECT COUNT(*) FROM NutritionMealDetails;
SELECT COUNT(*) FROM NutritionFoodIntake;
SELECT COUNT(*) FROM Users;
SELECT COUNT(*) FROM UserProfiles;
SELECT COUNT(*) FROM MealSuggestions;
```

Mong đợi 16 bảng; hai bảng mới chưa có dòng; PK/FK/unique/index như migration;
số dòng và cấu trúc 14 bảng gốc không đổi. So sánh bản chụp trước/sau trong lúc
đã dừng mọi thao tác ghi, không chỉ dựa vào số lượng bảng.

Khởi động lại Flask để nạp code V4. Dùng tài khoản demo riêng để kiểm thử Generate,
đổi component, intake, edit/delete, F5 và persistence. Chặn Gemini thật/mock SMTP
trong đúng process kiểm thử; chỉ test Gemini thật riêng với quota tối thiểu.
Chưa phê duyệt migration thì chạy V3; V4/MySQL chưa thể tuyên bố hoạt động.
