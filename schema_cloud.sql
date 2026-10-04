-- NutriFit - MySQL cloud schema
-- Chọn database do nhà cung cấp MySQL cấp trước khi chạy file này.
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS Users (
    UserId INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName VARCHAR(100) NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS UserProfiles (
    ProfileId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Gender VARCHAR(10) NOT NULL,
    Age INT NOT NULL,
    HeightCm DOUBLE NOT NULL,
    WeightKg DOUBLE NOT NULL,
    ActivityLevel DOUBLE NOT NULL,
    Goal VARCHAR(20) NOT NULL,
    Bmr DOUBLE, Tdee DOUBLE, TargetKcal DOUBLE, TargetCarbs DOUBLE,
    TargetProtein DOUBLE, TargetFat DOUBLE, TargetFiber DOUBLE,
    TargetWaterMl INT,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_UserProfiles_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Workouts (
    WorkoutId INT AUTO_INCREMENT PRIMARY KEY,
    WorkoutName VARCHAR(150) NOT NULL,
    DurationMinutes INT NOT NULL,
    CaloriesBurned DOUBLE NOT NULL,
    Category VARCHAR(50) DEFAULT 'Cardio',
    IsCustom BOOLEAN DEFAULT FALSE,
    CreatedBy INT NULL,
    CONSTRAINT FK_Workouts_Users FOREIGN KEY (CreatedBy) REFERENCES Users(UserId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS WorkoutLogs (
    LogId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    WorkoutId INT NOT NULL,
    LoggedDate DATE NOT NULL DEFAULT (CURRENT_DATE),
    DurationMinutes INT NOT NULL,
    CaloriesBurned DOUBLE NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_WorkoutLogs_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    CONSTRAINT FK_WorkoutLogs_Workouts FOREIGN KEY (WorkoutId) REFERENCES Workouts(WorkoutId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS MealSuggestions (
    SuggestionId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    SuggestionDate DATE NOT NULL DEFAULT (CURRENT_DATE),
    MealType VARCHAR(20) NOT NULL,
    OptionsJson JSON NOT NULL,
    SelectedOption INT NULL,
    Status VARCHAR(20) DEFAULT 'pending',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT UQ_User_Meal_Date UNIQUE (UserId, SuggestionDate, MealType),
    CONSTRAINT FK_MealSuggestions_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chỉ seed khi chưa có workout mặc định.
INSERT INTO Workouts (WorkoutName, DurationMinutes, CaloriesBurned, Category, IsCustom, CreatedBy)
SELECT * FROM (
    SELECT 'Chạy bộ ngoài trời', 30, 280.0, 'Cardio', 0, NULL UNION ALL
    SELECT 'Đạp xe cardio đường bằng', 45, 320.0, 'Cardio', 0, NULL UNION ALL
    SELECT 'Nhảy dây cường độ vừa', 20, 200.0, 'Cardio', 0, NULL UNION ALL
    SELECT 'Tập tạ toàn thân (Full-body Gym)', 50, 350.0, 'Gym', 0, NULL UNION ALL
    SELECT 'HIIT đốt mỡ ngắt quãng', 25, 260.0, 'Cardio', 0, NULL UNION ALL
    SELECT 'Bơi lội tự do', 40, 310.0, 'Thể thao', 0, NULL UNION ALL
    SELECT 'Đi bộ nhanh dốc nhẹ', 40, 210.0, 'Cardio', 0, NULL UNION ALL
    SELECT 'Đạp xe leo dốc / Spinning', 35, 340.0, 'Cardio', 0, NULL UNION ALL
    SELECT 'Tập cơ bụng & Core (Abs Workout)', 20, 140.0, 'Gym', 0, NULL UNION ALL
    SELECT 'Tập ngực và tay sau (Chest & Triceps)', 45, 290.0, 'Gym', 0, NULL UNION ALL
    SELECT 'Tập lưng xô và tay trước (Back & Biceps)', 45, 285.0, 'Gym', 0, NULL UNION ALL
    SELECT 'Tập mông đùi (Leg Day / Squats)', 45, 320.0, 'Gym', 0, NULL UNION ALL
    SELECT 'Đánh cầu lông giao lưu', 45, 315.0, 'Thể thao', 0, NULL UNION ALL
    SELECT 'Chơi bóng đá mini', 60, 480.0, 'Thể thao', 0, NULL UNION ALL
    SELECT 'Bóng rổ nửa sân', 45, 360.0, 'Thể thao', 0, NULL UNION ALL
    SELECT 'Yoga vinyasa kéo giãn toàn thân', 40, 160.0, 'Yoga', 0, NULL UNION ALL
    SELECT 'Pilates siết eo & định hình vóc dáng', 35, 190.0, 'Yoga', 0, NULL UNION ALL
    SELECT 'Nhảy Zumba / Aerobic năng động', 40, 300.0, 'Cardio', 0, NULL
) AS seed(WorkoutName, DurationMinutes, CaloriesBurned, Category, IsCustom, CreatedBy)
WHERE NOT EXISTS (SELECT 1 FROM Workouts WHERE IsCustom = 0);
