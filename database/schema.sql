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
