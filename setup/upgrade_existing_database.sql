-- NutriFit incremental upgrade for an EXISTING NutriFitDB.
-- Back up the database in MySQL Workbench before running this file.
-- Safe to run repeatedly; it does not DROP, DELETE, TRUNCATE or reset existing rows.
USE NutriFitDB;

-- Add premium fields to older Users tables only when missing.
SET @ddl = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='Users' AND COLUMN_NAME='SubscriptionStatus')=0,
  'ALTER TABLE Users ADD COLUMN SubscriptionStatus VARCHAR(20) DEFAULT ''FREE''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SET @ddl = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='Users' AND COLUMN_NAME='PremiumExpiresAt')=0,
  'ALTER TABLE Users ADD COLUMN PremiumExpiresAt DATETIME NULL',
  'SELECT 1'
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS SubscriptionPlans (
  PlanId INT AUTO_INCREMENT PRIMARY KEY,
  PlanName VARCHAR(100) NOT NULL,
  PriceVnd INT NOT NULL,
  DurationDays INT NOT NULL,
  Description VARCHAR(255) NULL,
  IsActive BOOLEAN DEFAULT TRUE,
  CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS PaymentTransactions (
  TransactionId INT AUTO_INCREMENT PRIMARY KEY,
  UserId INT NOT NULL,
  PlanId INT NOT NULL,
  AmountVnd INT NOT NULL,
  PaymentMethod VARCHAR(50) NOT NULL,
  TransactionCode VARCHAR(100) UNIQUE NOT NULL,
  Status VARCHAR(20) DEFAULT 'SUCCESS',
  CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_Payments_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
  CONSTRAINT FK_Payments_Plans FOREIGN KEY (PlanId) REFERENCES SubscriptionPlans(PlanId) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed default plans only if their IDs do not already exist.
INSERT IGNORE INTO SubscriptionPlans (PlanId, PlanName, PriceVnd, DurationDays, Description, IsActive) VALUES
(1, 'Gói Premium 1 Tháng', 99000, 30, 'Mở khóa toàn bộ gợi ý mâm cơm & phân tích dinh dưỡng chuyên sâu', TRUE),
(2, 'Gói Premium 1 Năm', 990000, 365, 'Tiết kiệm 20% khi đăng ký trọn gói 1 năm', TRUE);

CREATE TABLE IF NOT EXISTS NutritionMealDetails (
  OptionId INT PRIMARY KEY,
  RecipeJson LONGTEXT NOT NULL,
  Version INT NOT NULL DEFAULT 1,
  CONSTRAINT fk_nutrition_option FOREIGN KEY (OptionId) REFERENCES MealOption(OptionId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS NutritionFoodIntake (
  IntakeId INT AUTO_INCREMENT PRIMARY KEY,
  UserId INT NOT NULL,
  RequestKey VARCHAR(64) NOT NULL,
  RequestHash CHAR(64) NOT NULL,
  IntakeDate DATE NOT NULL,
  OccurredAt DATETIME NOT NULL,
  MealType VARCHAR(20) NOT NULL,
  SnapshotJson LONGTEXT NOT NULL,
  Version INT NOT NULL DEFAULT 1,
  Deleted INT NOT NULL DEFAULT 0,
  CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_nutrition_request UNIQUE (UserId, RequestKey),
  CONSTRAINT fk_nutrition_intake_user FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS NutritionFoodCatalog (
  DishId VARCHAR(64) PRIMARY KEY,
  NameVi VARCHAR(200) NOT NULL,
  ComponentType VARCHAR(20) NOT NULL,
  PreparationState VARCHAR(20) NOT NULL,
  ReferenceGrams DECIMAL(9,2) NOT NULL,
  MinGrams DECIMAL(9,2) NOT NULL,
  MaxGrams DECIMAL(9,2) NOT NULL,
  KcalPer100G DECIMAL(10,4) NULL,
  ProteinPer100G DECIMAL(10,4) NULL,
  CarbsPer100G DECIMAL(10,4) NULL,
  FatPer100G DECIMAL(10,4) NULL,
  FiberPer100G DECIMAL(10,4) NULL,
  IngredientsJson LONGTEXT NOT NULL,
  MealTypesJson LONGTEXT NOT NULL,
  PrepMinutes INT NULL,
  ProvenanceJson LONGTEXT NOT NULL,
  Estimated INT NOT NULL DEFAULT 1,
  IsActive INT NOT NULL DEFAULT 1,
  DataVersion INT NOT NULL DEFAULT 1,
  UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS NutritionLegacyMenus (
  TemplateId VARCHAR(64) PRIMARY KEY,
  MealType VARCHAR(20) NOT NULL,
  DayIndex INT NOT NULL,
  TemplateJson LONGTEXT NOT NULL,
  IsActive INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create supporting indexes only when absent.
SET @ddl = IF((SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='NutritionFoodIntake' AND INDEX_NAME='ix_nutrition_intake_day')=0,
  'CREATE INDEX ix_nutrition_intake_day ON NutritionFoodIntake(UserId, IntakeDate, Deleted)', 'SELECT 1');
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SET @ddl = IF((SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='NutritionFoodCatalog' AND INDEX_NAME='ix_nutrition_catalog_active_type')=0,
  'CREATE INDEX ix_nutrition_catalog_active_type ON NutritionFoodCatalog(IsActive, ComponentType)', 'SELECT 1');
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SET @ddl = IF((SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='NutritionLegacyMenus' AND INDEX_NAME='ix_nutrition_legacy_meal_day')=0,
  'CREATE INDEX ix_nutrition_legacy_meal_day ON NutritionLegacyMenus(MealType, DayIndex, IsActive)', 'SELECT 1');
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;
