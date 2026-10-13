-- Additive migration; apply only after approval and verified backup.
-- No USE, DROP, ALTER, DELETE, TRUNCATE or seed statements.
CREATE TABLE NutritionFoodCatalog (
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

CREATE INDEX ix_nutrition_catalog_active_type ON NutritionFoodCatalog(IsActive, ComponentType);

CREATE TABLE NutritionLegacyMenus (
    TemplateId VARCHAR(64) PRIMARY KEY,
    MealType VARCHAR(20) NOT NULL,
    DayIndex INT NOT NULL,
    TemplateJson LONGTEXT NOT NULL,
    IsActive INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_nutrition_legacy_meal_day ON NutritionLegacyMenus(MealType, DayIndex, IsActive);
