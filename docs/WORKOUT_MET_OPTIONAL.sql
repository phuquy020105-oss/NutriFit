-- NutriFit: chuyển Workouts từ "calo cố định" sang "MET".
-- Calo mỗi buổi tập = MET x cân nặng (kg) x giờ, tính lúc ghi nhận.
-- BACKUP NutriFitDB trước khi chạy. Chạy lặp lại an toàn (bỏ qua nếu đã chuyển xong).
-- WorkoutLogs.CaloriesBurned được giữ nguyên: đó là calo thực tế đã tính ở thời điểm tập (lịch sử).
USE NutriFitDB;

-- 1) Thêm cột Met (cho phép NULL tạm thời)
SET @ddl = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='Workouts' AND COLUMN_NAME='Met')=0,
  'ALTER TABLE Workouts ADD COLUMN Met DOUBLE NULL AFTER DurationMinutes',
  'SELECT 1'
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) MET cho 18 bài hệ thống (theo tên bài)
UPDATE Workouts SET Met = 9.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Chạy bộ ngoài trời';
UPDATE Workouts SET Met = 11.0 WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Nhảy dây tốc độ';
UPDATE Workouts SET Met = 5.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Tập ngực & tay sau (Gym)';
UPDATE Workouts SET Met = 6.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Tập chân & mông (Squats)';
UPDATE Workouts SET Met = 7.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Đá bóng phong trào';
UPDATE Workouts SET Met = 8.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Bơi lội tự do';
UPDATE Workouts SET Met = 2.5  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Yoga giãn cơ buổi sáng';
UPDATE Workouts SET Met = 8.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Đạp xe đường dài';
UPDATE Workouts SET Met = 3.8  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Đi bộ nhanh';
UPDATE Workouts SET Met = 8.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'HIIT tại nhà';
UPDATE Workouts SET Met = 8.8  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Leo cầu thang';
UPDATE Workouts SET Met = 5.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Tập lưng & tay trước (Gym)';
UPDATE Workouts SET Met = 4.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Tập vai & bụng (Core)';
UPDATE Workouts SET Met = 3.8  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Hít đất & plank tại nhà';
UPDATE Workouts SET Met = 5.5  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Cầu lông';
UPDATE Workouts SET Met = 4.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Bóng chuyền';
UPDATE Workouts SET Met = 4.0  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Yoga Vinyasa năng động';
UPDATE Workouts SET Met = 2.3  WHERE IsCustom = 0 AND Met IS NULL AND WorkoutName = 'Giãn cơ trước khi ngủ';

-- 3) Bài tự tạo: suy ngược MET từ calo đã lưu và cân nặng của người tạo (mặc định 60 kg)
SET @ddl = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='Workouts' AND COLUMN_NAME='CaloriesBurned')=1,
  'UPDATE Workouts w LEFT JOIN UserProfiles p ON p.UserId = w.CreatedBy
      SET w.Met = LEAST(25, GREATEST(1, ROUND(w.CaloriesBurned * 60 / (w.DurationMinutes * COALESCE(NULLIF(p.WeightKg, 0), 60)), 1)))
    WHERE w.Met IS NULL AND w.IsCustom = 1 AND w.DurationMinutes > 0',
  'SELECT 1'
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4) Còn bài nào chưa có MET (tên bài hệ thống đã bị đổi...) thì gán MET trung bình 5.0
UPDATE Workouts SET Met = 5.0 WHERE Met IS NULL;
ALTER TABLE Workouts MODIFY COLUMN Met DOUBLE NOT NULL;

-- 5) Bỏ calo cố định
SET @ddl = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='Workouts' AND COLUMN_NAME='CaloriesBurned')=1,
  'ALTER TABLE Workouts DROP COLUMN CaloriesBurned',
  'SELECT 1'
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT WorkoutId, WorkoutName, DurationMinutes, Met, IsCustom FROM Workouts ORDER BY CategoryId, WorkoutId;
