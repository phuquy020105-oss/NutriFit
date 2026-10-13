-- Forward-only additive migration. No USE, DROP, DELETE, seed or core ALTER.
-- Apply manually only after backup and explicit approval on NutriFitDB.
CREATE TABLE NutritionMealDetails (
    OptionId INT PRIMARY KEY,
    RecipeJson LONGTEXT NOT NULL,
    Version INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_nutrition_option FOREIGN KEY (OptionId) REFERENCES MealOption(OptionId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE NutritionFoodIntake (
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

CREATE INDEX ix_nutrition_intake_day ON NutritionFoodIntake(UserId, IntakeDate, Deleted);
