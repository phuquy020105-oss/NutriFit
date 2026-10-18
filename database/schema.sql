-- NutriFit Java / Design v1.0 - target schema
-- Run ONLY against the new empty NutriFitDB_Java database.
-- MySQL 8.0.16+ required for enforced CHECK constraints.
CREATE DATABASE IF NOT EXISTS NutriFitDB_Java CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE NutriFitDB_Java;

CREATE TABLE IF NOT EXISTS users (
 user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 email VARCHAR(255) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 full_name VARCHAR(150) NOT NULL,
 role ENUM('USER','ADMIN') NOT NULL DEFAULT 'USER',
 subscription_status ENUM('FREE','PREMIUM') NOT NULL DEFAULT 'FREE',
 premium_expires_at DATETIME NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS registrationotps (
 email VARCHAR(255) PRIMARY KEY,
 full_name VARCHAR(150) NOT NULL,
 password_hash VARCHAR(255) NOT NULL,
 otp_hash VARCHAR(255) NOT NULL,
 expires_at DATETIME NOT NULL,
 last_sent_at DATETIME NOT NULL,
 attempts INT UNSIGNED NOT NULL DEFAULT 0,
 window_start DATETIME NOT NULL,
 sent_in_window INT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS registrationotpipquota (
 ip_hash CHAR(64) PRIMARY KEY,
 window_start DATETIME NOT NULL,
 sent_in_window INT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS userprofiles (
 profile_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL UNIQUE,
 gender VARCHAR(30), age INT UNSIGNED, height_cm DECIMAL(6,2), weight_kg DECIMAL(6,2),
 activity_level VARCHAR(30), goal VARCHAR(40), bmr DECIMAL(9,2), tdee DECIMAL(9,2),
 target_kcal DECIMAL(9,2), target_water_ml INT UNSIGNED,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 CONSTRAINT ck_profile_height CHECK (height_cm IS NULL OR height_cm > 0),
 CONSTRAINT ck_profile_weight CHECK (weight_kg IS NULL OR weight_kg > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bodymetriclog (
 metric_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 recorded_date DATE NOT NULL,
 weight_kg DECIMAL(6,2) NOT NULL,
 bmi DECIMAL(6,2),
 CONSTRAINT fk_metric_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 CONSTRAINT ck_metric_weight CHECK (weight_kg > 0),
 INDEX idx_metric_user_date (user_id,recorded_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS waterintakelog (
 water_log_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 logged_date DATE NOT NULL,
 amount_ml INT UNSIGNED NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_water_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 CONSTRAINT ck_water_amount CHECK (amount_ml > 0),
 INDEX idx_water_user_date (user_id,logged_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS foods (
 food_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(200) NOT NULL,
 calories_per_100g DECIMAL(10,3) NOT NULL DEFAULT 0,
 protein_per_100g DECIMAL(10,3) NOT NULL DEFAULT 0,
 carbs_per_100g DECIMAL(10,3) NOT NULL DEFAULT 0,
 fat_per_100g DECIMAL(10,3) NOT NULL DEFAULT 0,
 fiber_per_100g DECIMAL(10,3) NOT NULL DEFAULT 0,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 CONSTRAINT ck_food_nutrients CHECK (calories_per_100g >= 0 AND protein_per_100g >= 0 AND carbs_per_100g >= 0 AND fat_per_100g >= 0 AND fiber_per_100g >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recipes (
 recipe_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(200) NOT NULL,
 meal_type ENUM('BREAKFAST','LUNCH','DINNER') NOT NULL,
 base_servings DECIMAL(8,2) NOT NULL DEFAULT 1,
 instructions TEXT,
 image_url VARCHAR(1000),
 prep_minutes INT UNSIGNED,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 CONSTRAINT ck_recipe_servings CHECK (base_servings > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recipeingredients (
 ingredient_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 recipe_id BIGINT UNSIGNED NOT NULL,
 food_id BIGINT UNSIGNED NOT NULL,
 quantity_grams DECIMAL(10,2) NOT NULL,
 CONSTRAINT fk_ingredient_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
 CONSTRAINT fk_ingredient_food FOREIGN KEY (food_id) REFERENCES foods(food_id) ON DELETE RESTRICT,
 CONSTRAINT ck_ingredient_quantity CHECK (quantity_grams > 0),
 INDEX idx_ingredient_recipe (recipe_id),
 INDEX idx_ingredient_food (food_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mealplans (
 plan_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 plan_date DATE NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_mealplan_user_date (user_id,plan_date),
 CONSTRAINT fk_mealplan_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS mealentries (
    entry_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    plan_id BIGINT UNSIGNED NOT NULL,
    recipe_id BIGINT UNSIGNED NOT NULL,

    recipe_name_snapshot VARCHAR(200) NOT NULL,

    meal_type ENUM('BREAKFAST','LUNCH','DINNER') NOT NULL,
    servings DECIMAL(8,2) NOT NULL,
    calories_kcal DECIMAL(12,3) NOT NULL,
    protein_g DECIMAL(12,3) NOT NULL,
    carbs_g DECIMAL(12,3) NOT NULL,
    fat_g DECIMAL(12,3) NOT NULL,
    fiber_g DECIMAL(12,3) NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mealentry_plan
        FOREIGN KEY (plan_id)
        REFERENCES mealplans(plan_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_mealentry_recipe
        FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_mealentry_values
        CHECK (
            servings > 0
            AND calories_kcal >= 0
            AND protein_g >= 0
            AND carbs_g >= 0
            AND fat_g >= 0
            AND fiber_g >= 0
        ),

    CONSTRAINT uq_mealentry_plan_meal_recipe
        UNIQUE (plan_id, meal_type, recipe_id),

    INDEX idx_mealentry_plan (plan_id)

) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS foodpreferences (
 preference_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 food_id BIGINT UNSIGNED NOT NULL,
 type ENUM('LIKE','DISLIKE') NOT NULL,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 UNIQUE KEY uq_foodpref_user_food (user_id,food_id),
 CONSTRAINT fk_foodpref_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 CONSTRAINT fk_foodpref_food FOREIGN KEY (food_id) REFERENCES foods(food_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workoutcategories (
 category_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 category_name VARCHAR(150) NOT NULL,
 icon_name VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workouts (
 workout_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 category_id BIGINT UNSIGNED NOT NULL,
 created_by BIGINT UNSIGNED NULL,
 workout_name VARCHAR(200) NOT NULL,
 is_custom BOOLEAN NOT NULL DEFAULT FALSE,
 access_level ENUM('FREE','PREMIUM') NOT NULL DEFAULT 'FREE',
 description TEXT, instructions TEXT, muscle_group VARCHAR(100),
 difficulty_level VARCHAR(50), equipment VARCHAR(200), target_goal VARCHAR(100),
 video_url VARCHAR(1000), met_value DECIMAL(6,2) NOT NULL,
 default_duration_minutes INT UNSIGNED NOT NULL,
 CONSTRAINT fk_workout_category FOREIGN KEY (category_id) REFERENCES workoutcategories(category_id) ON DELETE RESTRICT,
 CONSTRAINT fk_workout_creator FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL,
 CONSTRAINT ck_workout_met CHECK (met_value > 0),
 CONSTRAINT ck_workout_duration CHECK (default_duration_minutes > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workoutplans (
 plan_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 plan_name VARCHAR(200) NOT NULL,
 start_date DATE NOT NULL,
 end_date DATE NOT NULL,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 CONSTRAINT fk_workoutplan_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 CONSTRAINT ck_workoutplan_dates CHECK (end_date >= start_date),
 INDEX idx_workoutplan_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workoutplandays (
 plan_day_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 plan_id BIGINT UNSIGNED NOT NULL,
 day_index TINYINT UNSIGNED NOT NULL,
 day_name VARCHAR(30), focus_area VARCHAR(100), rest_day BOOLEAN NOT NULL DEFAULT FALSE,
 UNIQUE KEY uq_plan_day (plan_id,day_index),
 CONSTRAINT fk_planday_plan FOREIGN KEY (plan_id) REFERENCES workoutplans(plan_id) ON DELETE CASCADE,
 CONSTRAINT ck_plan_day_index CHECK (day_index BETWEEN 1 AND 7)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workoutplandetails (
 detail_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 plan_day_id BIGINT UNSIGNED NOT NULL,
 workout_id BIGINT UNSIGNED NOT NULL,
 duration_minutes INT UNSIGNED NOT NULL,
 order_index INT UNSIGNED NOT NULL,
 UNIQUE KEY uq_planday_order (plan_day_id,order_index),
 CONSTRAINT fk_plandetail_day FOREIGN KEY (plan_day_id) REFERENCES workoutplandays(plan_day_id) ON DELETE CASCADE,
 CONSTRAINT fk_plandetail_workout FOREIGN KEY (workout_id) REFERENCES workouts(workout_id) ON DELETE RESTRICT,
 CONSTRAINT ck_plandetail_duration CHECK (duration_minutes > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workoutlogs (
 log_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 workout_id BIGINT UNSIGNED NOT NULL,
 plan_detail_id BIGINT UNSIGNED NULL,
 logged_date DATE NOT NULL,
 duration_minutes INT UNSIGNED NOT NULL,
 met_value DECIMAL(6,2) NOT NULL,
 estimated_calories DECIMAL(12,3) NOT NULL,
 CONSTRAINT fk_workoutlog_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 CONSTRAINT fk_workoutlog_workout FOREIGN KEY (workout_id) REFERENCES workouts(workout_id) ON DELETE RESTRICT,
 CONSTRAINT fk_workoutlog_detail FOREIGN KEY (plan_detail_id) REFERENCES workoutplandetails(detail_id) ON DELETE SET NULL,
 CONSTRAINT ck_workoutlog_values CHECK (duration_minutes > 0 AND met_value > 0 AND estimated_calories >= 0),
 INDEX idx_workoutlog_user_date (user_id,logged_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workoutgoals (
 goal_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL UNIQUE,
 weekly_sessions_target INT UNSIGNED NOT NULL DEFAULT 0,
 weekly_duration_target INT UNSIGNED NOT NULL DEFAULT 0,
 CONSTRAINT fk_workoutgoal_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subscriptionplans (
 plan_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 plan_name VARCHAR(100) NOT NULL,
 price_vnd BIGINT UNSIGNED NOT NULL,
 duration_days INT UNSIGNED NOT NULL,
 description TEXT,
 is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT ck_subplan_duration CHECK (duration_days > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS paymenttransactions (
 transaction_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 plan_id BIGINT UNSIGNED NOT NULL,
 amount_vnd BIGINT UNSIGNED NOT NULL,
 method VARCHAR(30) NOT NULL DEFAULT 'VNPAY',
 transaction_code VARCHAR(100) NOT NULL UNIQUE,
 status ENUM('PENDING','SUCCESS','FAILED','CANCELLED') NOT NULL DEFAULT 'PENDING',
 paid_at DATETIME NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_payment_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
 CONSTRAINT fk_payment_plan FOREIGN KEY (plan_id) REFERENCES subscriptionplans(plan_id) ON DELETE RESTRICT,
 INDEX idx_payment_user_created (user_id,created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS chatconversations (
 conversation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 title VARCHAR(255),
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_chatconversation_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
 INDEX idx_chatconversation_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS chatmessages (
 message_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 conversation_id BIGINT UNSIGNED NOT NULL,
 sender_role ENUM('USER','ASSISTANT','SYSTEM') NOT NULL,
 content TEXT NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_chatmessage_conversation FOREIGN KEY (conversation_id) REFERENCES chatconversations(conversation_id) ON DELETE CASCADE,
 INDEX idx_chatmessage_conversation_date (conversation_id,created_at)
) ENGINE=InnoDB;

-- Verify: expected 23 tables.
SELECT COUNT(*) AS total_tables FROM information_schema.tables
WHERE table_schema = DATABASE() AND table_type='BASE TABLE';
SHOW TABLES;


-- =====================================================================
-- NutriFit - Dữ liệu mẫu cho chức năng WORKOUT
-- Cần chạy SAU database/schema.sql (đã tạo bảng). Có thể chạy lại nhiều lần:
-- danh mục và bài tập đã tồn tại (cùng tên) sẽ không bị chèn trùng.
--
-- Nội dung: 3 danh mục (Khởi động / Calisthenic / Giãn cơ) với
--   Khởi động  : 8 bài FREE   (mặc định 2 phút/bài)
--   Calisthenic: 24 bài FREE + 5 bài PREMIUM (mặc định 6 phút/bài)
--   Giãn cơ    : 10 bài FREE   (mặc định 3 phút/bài)
-- => một buổi tập mặc định (3 + 5 + 2 bài) dài 42 phút.
--
-- Nhóm cơ (cột muscle_group) dùng thống nhất các tên:
--   Ngực, Lưng, Vai, Tay, Bụng, Chân, Mông, Toàn thân (và Cổ cho bài giãn cơ).
-- Hệ thống sinh lộ trình dựa vào các tên này để phủ đủ nhóm cơ trong 7 ngày,
-- nên khi thêm bài mới hãy dùng đúng tên nhóm cơ ở trên.
-- Giá trị met_value là xấp xỉ theo Compendium of Physical Activities, có thể chỉnh lại.
-- =====================================================================
USE NutriFitDB_Java;
SET NAMES utf8mb4;

-- 1) Danh mục (tên phải khớp cách WorkoutPlanService nhận diện: "Khởi động", "Calisthenic", "Giãn cơ")
INSERT INTO workoutcategories (category_name, icon_name)
SELECT t.category_name, t.icon_name
FROM (
    SELECT 'Khởi động' AS category_name, 'warmup' AS icon_name
    UNION ALL SELECT 'Calisthenic', 'calisthenic'
    UNION ALL SELECT 'Giãn cơ', 'stretching'
) t
WHERE NOT EXISTS (SELECT 1 FROM workoutcategories c WHERE c.category_name = t.category_name);

-- 2) Bảng tạm chứa bài tập, rồi chèn vào workouts (bỏ qua bài đã có cùng tên)
DROP TEMPORARY TABLE IF EXISTS tmp_workout_seed;
CREATE TEMPORARY TABLE tmp_workout_seed (
    category_name VARCHAR(150) NOT NULL,
    workout_name VARCHAR(200) NOT NULL,
    access_level VARCHAR(10) NOT NULL,
    description TEXT,
    instructions TEXT,
    muscle_group VARCHAR(100),
    difficulty_level VARCHAR(50),
    equipment VARCHAR(200),
    met_value DECIMAL(6,2) NOT NULL,
    default_duration_minutes INT UNSIGNED NOT NULL
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

INSERT INTO tmp_workout_seed
(category_name, workout_name, access_level, description, instructions, muscle_group, difficulty_level, equipment, met_value, default_duration_minutes)
VALUES
-- ===== Khởi động =====
('Khởi động', 'Jumping jack', 'FREE', 'Nhảy dang tay chân nhịp nhàng, nâng nhịp tim và làm nóng toàn thân.', 'Đứng thẳng, nhảy dang chân rộng hơn vai đồng thời giơ hai tay lên cao rồi nhảy về tư thế đầu. Giữ nhịp đều, tiếp đất nhẹ nhàng.', 'Toàn thân', 'Dễ', 'Không cần dụng cụ', 4.0, 2),
('Khởi động', 'High knees tại chỗ', 'FREE', 'Chạy nâng cao gối tại chỗ để làm nóng chân và tim mạch.', 'Đứng thẳng, lần lượt nâng gối ngang hông với nhịp nhanh, đánh tay tự nhiên, tiếp đất bằng nửa bàn chân trước.', 'Chân', 'Dễ', 'Không cần dụng cụ', 4.5, 2),
('Khởi động', 'Xoay vai', 'FREE', 'Xoay khớp vai để chuẩn bị cho các bài đẩy và kéo.', 'Đứng thẳng, đặt đầu ngón tay lên vai, xoay khuỷu tay vẽ vòng tròn lớn về trước 10 lần rồi về sau 10 lần.', 'Vai', 'Dễ', 'Không cần dụng cụ', 2.5, 2),
('Khởi động', 'Mở rộng ngực', 'FREE', 'Đánh tay dang ngang giúp mở ngực và làm nóng cơ ngực.', 'Đứng thẳng, dang hai tay ngang vai rồi khép lại phía trước và mở rộng ra sau, lặp lại nhịp nhàng 15 lần.', 'Ngực', 'Dễ', 'Không cần dụng cụ', 2.5, 2),
('Khởi động', 'Cat-cow', 'FREE', 'Chuyển động võng và cong lưng giúp làm mềm cột sống.', 'Quỳ chống bốn điểm, hít vào võng lưng ngẩng đầu, thở ra cong lưng cúi đầu. Lặp lại chậm 10 lần.', 'Lưng', 'Dễ', 'Không cần dụng cụ', 2.3, 2),
('Khởi động', 'Xoay thân', 'FREE', 'Xoay thân trên để làm nóng cơ bụng và cột sống.', 'Đứng chân rộng bằng vai, hai tay co trước ngực, xoay thân sang hai bên luân phiên 20 lần, hông giữ cố định.', 'Bụng', 'Dễ', 'Không cần dụng cụ', 2.8, 2),
('Khởi động', 'Xoay cổ tay và khuỷu tay', 'FREE', 'Làm nóng khớp tay trước các bài chống đẩy.', 'Đan hai bàn tay xoay cổ tay mỗi chiều 10 lần, sau đó xoay khuỷu tay nhẹ nhàng 10 lần.', 'Tay', 'Dễ', 'Không cần dụng cụ', 2.0, 2),
('Khởi động', 'Xoay hông và squat nhẹ', 'FREE', 'Xoay hông kết hợp squat nhẹ làm nóng cơ mông và hông.', 'Đứng chân rộng bằng vai, xoay hông vẽ vòng tròn 10 lần mỗi chiều, sau đó squat nhẹ 10 lần với biên độ nhỏ.', 'Mông', 'Dễ', 'Không cần dụng cụ', 3.0, 2),
-- ===== Calisthenic =====
('Calisthenic', 'Push-up quỳ', 'FREE', 'Chống đẩy với đầu gối chạm sàn, phù hợp người mới bắt đầu.', 'Quỳ gối, hai tay chống rộng hơn vai, giữ thân thẳng từ đầu gối đến đầu, hạ ngực gần sàn rồi đẩy lên.', 'Ngực', 'Dễ', 'Không cần dụng cụ', 3.8, 6),
('Calisthenic', 'Push-up cơ bản', 'FREE', 'Bài chống đẩy tiêu chuẩn cho cơ ngực, vai và tay sau.', 'Chống hai tay rộng hơn vai, thân thẳng như tấm ván, hạ ngực gần sàn với khuỷu tay chếch khoảng 45 độ rồi đẩy lên.', 'Ngực', 'Trung bình', 'Không cần dụng cụ', 4.5, 6),
('Calisthenic', 'Push-up tay rộng', 'FREE', 'Chống đẩy tay rộng nhấn mạnh cơ ngực.', 'Đặt hai tay rộng gấp rưỡi vai, giữ thân thẳng, hạ ngực xuống sát sàn rồi đẩy lên.', 'Ngực', 'Trung bình', 'Không cần dụng cụ', 4.5, 6),
('Calisthenic', 'Superman', 'FREE', 'Nằm sấp nâng tay chân để tập cơ lưng dưới.', 'Nằm sấp, duỗi hai tay về trước, đồng thời nâng tay và chân lên khỏi sàn, giữ 2 giây rồi hạ xuống.', 'Lưng', 'Dễ', 'Không cần dụng cụ', 3.0, 6),
('Calisthenic', 'Bird-dog', 'FREE', 'Duỗi tay chân đối diện để tăng sức mạnh lưng và ổn định thân.', 'Quỳ chống bốn điểm, duỗi tay phải và chân trái thẳng ra, giữ 2 giây rồi đổi bên. Giữ lưng phẳng.', 'Lưng', 'Dễ', 'Không cần dụng cụ', 3.0, 6),
('Calisthenic', 'Inverted row dưới bàn', 'FREE', 'Kéo người lên dưới mặt bàn chắc chắn để tập cơ lưng xô.', 'Nằm dưới bàn chắc chắn, nắm mép bàn, giữ thân thẳng rồi kéo ngực lên sát bàn, hạ xuống có kiểm soát.', 'Lưng', 'Trung bình', 'Bàn chắc chắn', 4.5, 6),
('Calisthenic', 'Shoulder tap plank', 'FREE', 'Chống tay vỗ vai luân phiên để tập vai và ổn định thân.', 'Vào tư thế plank tay thẳng, lần lượt chạm tay vào vai đối diện mà hông không xoay.', 'Vai', 'Dễ', 'Không cần dụng cụ', 4.0, 6),
('Calisthenic', 'Pike push-up', 'FREE', 'Chống đẩy gập hông, nhấn mạnh cơ vai.', 'Vào tư thế chữ V ngược, gập khuỷu hạ đỉnh đầu về phía sàn rồi đẩy lên.', 'Vai', 'Trung bình', 'Không cần dụng cụ', 5.0, 6),
('Calisthenic', 'Bear crawl', 'FREE', 'Bò bằng bốn điểm với đầu gối nhấc khỏi sàn, tập vai và thân.', 'Từ tư thế bốn điểm nhấc đầu gối cách sàn một gang tay, bò tiến lùi bằng tay và chân đối diện.', 'Vai', 'Trung bình', 'Không cần dụng cụ', 5.5, 6),
('Calisthenic', 'Dips ghế', 'FREE', 'Hạ người trên ghế để tập cơ tay sau.', 'Ngồi mép ghế chắc, chống tay phía sau, trượt mông ra khỏi ghế, gập khuỷu hạ người rồi đẩy lên.', 'Tay', 'Trung bình', 'Ghế chắc chắn', 4.5, 6),
('Calisthenic', 'Diamond push-up', 'FREE', 'Chống đẩy tay hẹp tạo hình kim cương, tập mạnh tay sau.', 'Đặt hai tay sát nhau dưới ngực tạo hình kim cương, giữ khuỷu tay sát thân, hạ người rồi đẩy lên.', 'Tay', 'Khó', 'Không cần dụng cụ', 5.0, 6),
('Calisthenic', 'Plank to push-up', 'FREE', 'Chuyển từ plank khuỷu tay lên plank tay thẳng, tập tay và thân.', 'Từ plank khuỷu tay, lần lượt chống từng tay đẩy lên tư thế chống đẩy rồi hạ về, đổi tay dẫn đầu.', 'Tay', 'Trung bình', 'Không cần dụng cụ', 5.0, 6),
('Calisthenic', 'Plank', 'FREE', 'Giữ thân thẳng trên khuỷu tay, tập cơ bụng sâu.', 'Chống khuỷu tay dưới vai, thân thẳng từ đầu đến gót, siết bụng và mông, giữ 30 giây.', 'Bụng', 'Dễ', 'Không cần dụng cụ', 3.0, 6),
('Calisthenic', 'Crunch', 'FREE', 'Gập bụng ngắn để tập cơ bụng trên.', 'Nằm ngửa gập gối, hai tay sau đầu, nhấc vai khỏi sàn bằng lực bụng rồi hạ xuống, không kéo cổ.', 'Bụng', 'Dễ', 'Không cần dụng cụ', 3.8, 6),
('Calisthenic', 'Nâng chân nằm', 'FREE', 'Nâng hạ hai chân khi nằm để tập bụng dưới.', 'Nằm ngửa, tay dọc thân, nâng hai chân thẳng lên vuông góc rồi hạ chậm gần sàn mà không chạm.', 'Bụng', 'Trung bình', 'Không cần dụng cụ', 4.0, 6),
('Calisthenic', 'Mountain climber', 'FREE', 'Chạy leo núi tại chỗ ở tư thế plank, tập bụng và tim mạch.', 'Ở tư thế chống tay thẳng, lần lượt đưa gối về phía ngực với nhịp nhanh, hông thấp ổn định.', 'Bụng', 'Trung bình', 'Không cần dụng cụ', 8.0, 6),
('Calisthenic', 'Squat', 'FREE', 'Gập gối hạ người, bài cơ bản cho đùi và mông.', 'Đứng chân rộng bằng vai, đẩy hông ra sau và gập gối hạ người đến khi đùi song song sàn rồi đứng lên.', 'Chân', 'Dễ', 'Không cần dụng cụ', 5.0, 6),
('Calisthenic', 'Lunge', 'FREE', 'Bước chân chùng gối, tập đùi và mông từng bên.', 'Bước một chân ra trước, hạ thấp cho đến khi hai gối gập khoảng 90 độ rồi đẩy về, đổi chân.', 'Chân', 'Trung bình', 'Không cần dụng cụ', 5.0, 6),
('Calisthenic', 'Wall sit', 'FREE', 'Tựa lưng vào tường ở tư thế ngồi, tập sức bền đùi.', 'Tựa lưng vào tường, trượt xuống đến khi đùi song song sàn, giữ 30 giây.', 'Chân', 'Trung bình', 'Tường', 3.5, 6),
('Calisthenic', 'Jump squat', 'FREE', 'Squat bật nhảy để tăng sức mạnh bùng nổ của chân.', 'Squat xuống rồi bật mạnh lên khỏi sàn, tiếp đất nhẹ nhàng bằng nửa bàn chân và hạ thẳng vào squat tiếp theo.', 'Chân', 'Khó', 'Không cần dụng cụ', 8.0, 6),
('Calisthenic', 'Glute bridge', 'FREE', 'Nằm nâng hông để tập cơ mông.', 'Nằm ngửa gập gối, nâng hông lên cho thân thẳng từ vai đến gối, siết mông 2 giây rồi hạ xuống.', 'Mông', 'Dễ', 'Không cần dụng cụ', 3.5, 6),
('Calisthenic', 'Donkey kick', 'FREE', 'Đá chân ra sau ở tư thế bốn điểm để tập mông.', 'Quỳ chống bốn điểm, đá một chân gập gối lên trần, siết mông rồi hạ về, đổi chân.', 'Mông', 'Dễ', 'Không cần dụng cụ', 3.5, 6),
('Calisthenic', 'Fire hydrant', 'FREE', 'Nâng chân sang ngang như vòi cứu hỏa để tập mông ngoài.', 'Quỳ chống bốn điểm, nâng một gối sang ngang giữ gập 90 độ, hông không xoay, hạ xuống rồi đổi chân.', 'Mông', 'Dễ', 'Không cần dụng cụ', 3.5, 6),
('Calisthenic', 'Burpee', 'FREE', 'Bài tập toàn thân cường độ cao kết hợp squat, plank và nhảy.', 'Từ đứng hạ xuống chống tay, đưa chân ra sau thành plank, thu chân về rồi bật nhảy lên cao.', 'Toàn thân', 'Khó', 'Không cần dụng cụ', 8.0, 6),
('Calisthenic', 'Pull-up', 'PREMIUM', 'Kéo cằm qua xà đơn, bài tập lưng xô và tay trước nâng cao.', 'Treo người trên xà, kéo cơ thể lên đến khi cằm qua xà rồi hạ xuống có kiểm soát.', 'Lưng', 'Khó', 'Xà đơn', 8.0, 6),
('Calisthenic', 'Pistol squat', 'PREMIUM', 'Squat một chân, bài tập sức mạnh và thăng bằng nâng cao.', 'Đứng một chân, chân kia duỗi thẳng trước mặt, hạ người xuống sâu bằng chân trụ rồi đứng lên.', 'Chân', 'Khó', 'Không cần dụng cụ', 8.0, 6),
('Calisthenic', 'Archer push-up', 'PREMIUM', 'Chống đẩy lệch tải sang một tay, nâng cao.', 'Chống tay rộng, hạ người về một tay trong khi tay còn lại duỗi thẳng, đẩy lên rồi đổi bên.', 'Ngực', 'Khó', 'Không cần dụng cụ', 8.0, 6),
('Calisthenic', 'Handstand push-up', 'PREMIUM', 'Chống đẩy trồng cây chuối dựa tường, nâng cao cho vai.', 'Trồng cây chuối dựa tường, gập khuỷu hạ đầu xuống gần sàn rồi đẩy lên.', 'Vai', 'Khó', 'Tường', 8.0, 6),
('Calisthenic', 'L-sit', 'PREMIUM', 'Giữ thân chữ L trên hai tay, tập bụng và tay nâng cao.', 'Chống hai tay xuống sàn, nâng mông và hai chân thẳng song song sàn, giữ càng lâu càng tốt.', 'Bụng', 'Khó', 'Không cần dụng cụ', 5.0, 6),
-- ===== Giãn cơ =====
('Giãn cơ', 'Giãn cơ đùi trước', 'FREE', 'Kéo giãn cơ đùi trước sau các bài chân.', 'Đứng một chân, gập gối kéo gót về phía mông, giữ 20–30 giây mỗi bên.', 'Chân', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Giãn gân kheo', 'FREE', 'Kéo giãn cơ đùi sau.', 'Ngồi duỗi một chân, nghiêng thân về phía mũi chân giữ lưng thẳng, giữ 20–30 giây mỗi bên.', 'Chân', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Giãn cơ mông (figure-four)', 'FREE', 'Kéo giãn cơ mông và hông.', 'Nằm ngửa, gác mắt cá chân lên đùi đối diện, kéo đùi về phía ngực, giữ 20–30 giây mỗi bên.', 'Mông', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Tư thế em bé (Child pose)', 'FREE', 'Kéo giãn lưng và vai.', 'Quỳ ngồi lên gót, duỗi hai tay thẳng về trước, hạ ngực xuống sàn, hít thở sâu 30 giây.', 'Lưng', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Giãn ngực ở khung cửa', 'FREE', 'Kéo giãn cơ ngực.', 'Đặt cẳng tay lên khung cửa, bước một chân qua cửa để ngực mở ra, giữ 20–30 giây mỗi bên.', 'Ngực', 'Dễ', 'Khung cửa', 2.3, 3),
('Giãn cơ', 'Giãn vai chéo ngực', 'FREE', 'Kéo giãn cơ vai sau.', 'Kéo một tay ngang qua ngực, dùng tay kia ôm giữ, giữ 20–30 giây mỗi bên.', 'Vai', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Giãn cơ tay sau', 'FREE', 'Kéo giãn cơ tam đầu.', 'Đưa một tay ra sau đầu, tay kia kéo nhẹ khuỷu về phía sau, giữ 20–30 giây mỗi bên.', 'Tay', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Cobra', 'FREE', 'Kéo giãn cơ bụng.', 'Nằm sấp, đặt tay cạnh ngực, chống tay nâng ngực lên, mở bụng và giữ 20–30 giây.', 'Bụng', 'Dễ', 'Không cần dụng cụ', 2.3, 3),
('Giãn cơ', 'Giãn cơ cổ', 'FREE', 'Kéo giãn nhẹ cơ cổ và vai trên.', 'Nghiêng đầu sang một bên, dùng tay đặt nhẹ trên đầu, giữ 20 giây mỗi bên.', 'Cổ', 'Dễ', 'Không cần dụng cụ', 2.0, 3),
('Giãn cơ', 'Downward dog', 'FREE', 'Kéo giãn toàn thân từ vai đến gót chân.', 'Chống tay và chân tạo chữ V ngược, đẩy hông lên cao và ép gót về sàn, giữ 30 giây.', 'Toàn thân', 'Dễ', 'Không cần dụng cụ', 2.5, 3);

INSERT INTO workouts
(category_id, created_by, workout_name, is_custom, access_level, description, instructions,
 muscle_group, difficulty_level, equipment, target_goal, video_url, met_value, default_duration_minutes)
SELECT c.category_id, NULL, s.workout_name, FALSE, s.access_level, s.description, s.instructions,
       s.muscle_group, s.difficulty_level, s.equipment, NULL, NULL, s.met_value, s.default_duration_minutes
FROM tmp_workout_seed s
JOIN workoutcategories c ON c.category_name = s.category_name
WHERE NOT EXISTS (
    SELECT 1 FROM workouts w
    WHERE w.workout_name = s.workout_name AND w.created_by IS NULL
);

DROP TEMPORARY TABLE IF EXISTS tmp_workout_seed;

-- 3) Kiểm tra nhanh kết quả
SELECT c.category_name, w.access_level, COUNT(*) AS so_bai
FROM workouts w JOIN workoutcategories c ON c.category_id = w.category_id
WHERE w.created_by IS NULL
GROUP BY c.category_name, w.access_level
ORDER BY c.category_name, w.access_level;