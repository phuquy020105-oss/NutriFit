-- 1. TẠO CƠ SỞ DỮ LIỆU
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'NutriFitDB')
BEGIN
    CREATE DATABASE NutriFitDB;
    PRINT N'Đã tạo cơ sở dữ liệu NutriFitDB thành công.';
END
GO

USE NutriFitDB;
GO

-- 2. BẢNG NGƯỜI DÙNG (Users)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' and xtype='U')
BEGIN
    CREATE TABLE Users (
        UserId INT IDENTITY(1,1) PRIMARY KEY,
        Email NVARCHAR(100) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        FullName NVARCHAR(100) NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT N'Đã tạo bảng Users.';
END
GO

-- 3. BẢNG HỒ SƠ THỂ TRẠNG CÁ NHÂN (UserProfiles)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserProfiles' and xtype='U')
BEGIN
    CREATE TABLE UserProfiles (
        ProfileId INT IDENTITY(1,1) PRIMARY KEY,
        UserId INT NOT NULL FOREIGN KEY REFERENCES Users(UserId) ON DELETE CASCADE,
        Gender NVARCHAR(10) NOT NULL,        -- 'male' hoặc 'female'
        Age INT NOT NULL,
        HeightCm FLOAT NOT NULL,
        WeightKg FLOAT NOT NULL,
        ActivityLevel FLOAT NOT NULL,        -- 1.2, 1.375, 1.55...
        Goal NVARCHAR(20) NOT NULL,          -- 'lose', 'maintain', 'gain'
        Bmr FLOAT,                           -- Năng lượng tiêu hao cơ bản (kcal)
        Tdee FLOAT,                          -- Tổng năng lượng tiêu hao mỗi ngày (kcal)
        TargetKcal FLOAT,                    -- Calo mục tiêu cần nạp (kcal)
        TargetCarbs FLOAT,                   -- Tinh bột mục tiêu (gram)
        TargetProtein FLOAT,                 -- Chất đạm mục tiêu (gram)
        TargetFat FLOAT,                     -- Chất béo mục tiêu (gram)
        TargetFiber FLOAT,                   -- Chất xơ mục tiêu (gram)
        TargetWaterMl INT,                   -- Nước uống khuyến nghị (ml)
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT N'Đã tạo bảng UserProfiles.';
END
GO

-- 4. BẢNG DANH MỤC BÀI TẬP (Workouts)
-- Chứa cả bài tập có sẵn của hệ thống và bài tập do người dùng tự nhập
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Workouts' and xtype='U')
BEGIN
    CREATE TABLE Workouts (
        WorkoutId INT IDENTITY(1,1) PRIMARY KEY,
        WorkoutName NVARCHAR(150) NOT NULL,
        DurationMinutes INT NOT NULL,        -- Thời gian tập chuẩn (phút)
        CaloriesBurned FLOAT NOT NULL,       -- Lượng calo đốt được (kcal)
        Category NVARCHAR(50) DEFAULT 'Cardio', -- 'Cardio', 'Gym', 'Yoga', v.v.
        IsCustom BIT DEFAULT 0,              -- 0: Bài có sẵn của hệ thống, 1: User tự nhập
        CreatedBy INT NULL FOREIGN KEY REFERENCES Users(UserId) -- NULL nếu là bài mặc định
    );
    PRINT N'Đã tạo bảng Workouts.';
END
GO

-- 5. BẢNG LỊCH SỬ TẬP LUYỆN (WorkoutLogs)
-- Phục vụ lưu lịch tập và truy vấn vẽ biểu đồ tần suất tập luyện
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='WorkoutLogs' and xtype='U')
BEGIN
    CREATE TABLE WorkoutLogs (
        LogId INT IDENTITY(1,1) PRIMARY KEY,
        UserId INT NOT NULL FOREIGN KEY REFERENCES Users(UserId) ON DELETE CASCADE,
        WorkoutId INT NOT NULL FOREIGN KEY REFERENCES Workouts(WorkoutId),
        LoggedDate DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        DurationMinutes INT NOT NULL,
        CaloriesBurned FLOAT NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT N'Đã tạo bảng WorkoutLogs.';
END
GO

-- 6. BẢNG GỢI Ý THỰC ĐƠN AI & LỊCH SỬ LỰA CHỌN (MealSuggestions)
-- Đáp ứng yêu cầu feature.txt:
-- + 3 options menu từ AI
-- + Nút thứ 4: để suy nghĩ (SelectedOption = NULL, Status = 'pending')
-- + 2 bữa: trưa (lunch) và tối (dinner)
-- + Cố định 3 options trong ngày, không sinh thêm ngoài 3 options ban đầu
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='MealSuggestions' and xtype='U')
BEGIN
    CREATE TABLE MealSuggestions (
        SuggestionId INT IDENTITY(1,1) PRIMARY KEY,
        UserId INT NOT NULL FOREIGN KEY REFERENCES Users(UserId) ON DELETE CASCADE,
        SuggestionDate DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        MealType NVARCHAR(20) NOT NULL,      -- 'lunch' hoặc 'dinner'
        OptionsJson NVARCHAR(MAX) NOT NULL,  -- Cấu trúc JSON chứa đúng 3 options từ AI
        SelectedOption INT NULL,             -- 1, 2, 3 (nếu chọn) hoặc NULL (nếu chọn nút thứ 4 để suy nghĩ)
        Status NVARCHAR(20) DEFAULT 'pending', -- 'pending' (đang suy nghĩ) hoặc 'decided' (đã chọn)
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        CONSTRAINT UQ_User_Meal_Date UNIQUE (UserId, SuggestionDate, MealType)
    );
    PRINT N'Đã tạo bảng MealSuggestions.';
END
-- NẠP DỮ LIỆU CÁC BÀI TẬP VẬN ĐỘNG CÓ SẴN (ĐÁP ỨNG FEATURE.TXT)
IF NOT EXISTS (SELECT 1 FROM Workouts WHERE IsCustom = 0)
BEGIN
    INSERT INTO Workouts (WorkoutName, DurationMinutes, CaloriesBurned, Category, IsCustom, CreatedBy) VALUES
    (N'Chạy bộ ngoài trời', 30, 280.0, N'Cardio', 0, NULL),
    (N'Đạp xe cardio đường bằng', 45, 320.0, N'Cardio', 0, NULL),
    (N'Nhảy dây cường độ vừa', 20, 200.0, N'Cardio', 0, NULL),
    (N'Tập tạ toàn thân (Full-body Gym)', 50, 350.0, N'Gym', 0, NULL),
    (N'HIIT đốt mỡ ngắt quãng', 25, 260.0, N'Cardio', 0, NULL),
    (N'Bơi lội tự do', 40, 310.0, N'Thể thao', 0, NULL),
    (N'Đi bộ nhanh dốc nhẹ', 40, 210.0, N'Cardio', 0, NULL),
    (N'Đạp xe leo dốc / Spinning', 35, 340.0, N'Cardio', 0, NULL),
    (N'Tập cơ bụng & Core (Abs Workout)', 20, 140.0, N'Gym', 0, NULL),
    (N'Tập ngực và tay sau (Chest & Triceps)', 45, 290.0, N'Gym', 0, NULL),
    (N'Tập lưng xô và tay trước (Back & Biceps)', 45, 285.0, N'Gym', 0, NULL),
    (N'Tập mông đùi (Leg Day / Squats)', 45, 320.0, N'Gym', 0, NULL),
    (N'Đánh cầu lông giao lưu', 45, 315.0, N'Thể thao', 0, NULL),
    (N'Chơi bóng đá mini', 60, 480.0, N'Thể thao', 0, NULL),
    (N'Bóng rổ nửa sân', 45, 360.0, N'Thể thao', 0, NULL),
    (N'Yoga vinyasa kéo giãn toàn thân', 40, 160.0, N'Yoga', 0, NULL),
    (N'Pilates siết eo & định hình vóc dáng', 35, 190.0, N'Yoga', 0, NULL),
    (N'Nhảy Zumba / Aerobic năng động', 40, 300.0, N'Cardio', 0, NULL);
    PRINT N'Đã nạp 18 bài tập mặc định vào bảng Workouts.';
END
GO


