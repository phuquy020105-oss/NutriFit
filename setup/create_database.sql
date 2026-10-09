-- ============================================================================
-- NUTRIFIT DATABASE SCHEMA - 3NF ENTERPRISE ARCHITECTURE
-- Dự án: Hệ thống quản lý dinh dưỡng và tập luyện NutriFit
-- ============================================================================

CREATE DATABASE IF NOT EXISTS NutriFitDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE NutriFitDB;

SET FOREIGN_KEY_CHECKS = 0;

-- Xóa bảng cũ nếu tồn tại để tái thiết lập schema sạch
DROP TABLE IF EXISTS WorkoutGoals;
DROP TABLE IF EXISTS WorkoutLogs;
DROP TABLE IF EXISTS Workouts;
DROP TABLE IF EXISTS WorkoutCategories;
DROP TABLE IF EXISTS StreetFoodDish;
DROP TABLE IF EXISTS MealComponentDish;
DROP TABLE IF EXISTS DishCatalog;
DROP TABLE IF EXISTS MealNutrition;
DROP TABLE IF EXISTS MealOption;
DROP TABLE IF EXISTS MealSuggestions;
DROP TABLE IF EXISTS BodyMetricLog;
DROP TABLE IF EXISTS WaterIntakeLog;
DROP TABLE IF EXISTS UserProfiles;
DROP TABLE IF EXISTS Users;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- MODULE 1: USERS, AUTHENTICATION & HEALTH METRICS (TV1 quản lý)
-- ============================================================================

-- 1. Bảng Tài khoản người dùng
CREATE TABLE Users (
    UserId INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName VARCHAR(100) NOT NULL,
    Role VARCHAR(20) DEFAULT 'MEMBER',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Bảng Hồ sơ thể trạng và mục tiêu calo
CREATE TABLE UserProfiles (
    ProfileId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Gender VARCHAR(10) NOT NULL,
    Age INT NOT NULL,
    HeightCm DOUBLE NOT NULL,
    WeightKg DOUBLE NOT NULL,
    ActivityLevel DOUBLE NOT NULL,
    Goal VARCHAR(20) NOT NULL,
    Bmr DOUBLE,
    Tdee DOUBLE,
    TargetKcal DOUBLE,
    TargetWaterMl INT,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT FK_Profiles_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Bảng Lịch sử uống nước
CREATE TABLE WaterIntakeLog (
    WaterLogId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    LoggedDate DATE NOT NULL,
    AmountMl INT NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_WaterLog_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bảng Lịch sử biến động cân nặng & BMI
CREATE TABLE BodyMetricLog (
    MetricId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    RecordedDate DATE NOT NULL,
    WeightKg DOUBLE NOT NULL,
    Bmi DOUBLE NOT NULL,
    CONSTRAINT FK_BodyMetric_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MODULE 2: NUTRITION & VIETNAMESE MEALS (TV3 quản lý nghiệp vụ, TV1 quản lý schema)
-- ============================================================================

-- 5. Bảng Phiên gợi ý mâm cơm
CREATE TABLE MealSuggestions (
    SuggestionId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    SuggestionDate DATE NOT NULL,
    MealType VARCHAR(20) NOT NULL,
    SelectedOption INT NULL,
    Status VARCHAR(20) DEFAULT 'pending',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT UQ_Meal_User_Date UNIQUE (UserId, SuggestionDate, MealType),
    CONSTRAINT FK_MealSuggestions_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Bảng Lựa chọn mâm cơm (Mâm 1, 2, 3)
CREATE TABLE MealOption (
    OptionId INT AUTO_INCREMENT PRIMARY KEY,
    SuggestionId INT NOT NULL,
    OptionNumber INT NOT NULL,
    Title VARCHAR(255) NOT NULL,
    DigestibilityNote VARCHAR(255),
    CONSTRAINT FK_MealOption_Suggestion FOREIGN KEY (SuggestionId) REFERENCES MealSuggestions(SuggestionId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Bảng Thành phần Calo & Macro dinh dưỡng riêng biệt (1-1 với MealOption)
CREATE TABLE MealNutrition (
    NutritionId INT AUTO_INCREMENT PRIMARY KEY,
    OptionId INT NOT NULL UNIQUE,
    TotalCalories DOUBLE NOT NULL,
    CarbsGrams DOUBLE NOT NULL,
    ProteinGrams DOUBLE NOT NULL,
    FatGrams DOUBLE NOT NULL,
    FiberGrams DOUBLE DEFAULT 0,
    CONSTRAINT FK_MealNutrition_Option FOREIGN KEY (OptionId) REFERENCES MealOption(OptionId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Bảng Kho món Việt tham chiếu
CREATE TABLE DishCatalog (
    DishCatalogId INT AUTO_INCREMENT PRIMARY KEY,
    Category VARCHAR(20) NOT NULL,
    StandardName VARCHAR(200) NOT NULL,
    BaseCalories DOUBLE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Bảng Chi tiết 5 món của từng mâm cơm
CREATE TABLE MealComponentDish (
    ComponentId INT AUTO_INCREMENT PRIMARY KEY,
    OptionId INT NOT NULL,
    DishCatalogId INT NULL,
    ComponentType VARCHAR(20) NOT NULL,
    DishName VARCHAR(255) NOT NULL,
    CONSTRAINT FK_MealComponent_Option FOREIGN KEY (OptionId) REFERENCES MealOption(OptionId) ON DELETE CASCADE,
    CONSTRAINT FK_MealComponent_Catalog FOREIGN KEY (DishCatalogId) REFERENCES DishCatalog(DishCatalogId) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Bảng Món lẻ mua ngoài đường phố (Module Street Food do TV4 phụ trách)
CREATE TABLE StreetFoodDish (
    DishId INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(200) NOT NULL,
    PriceVnd INT NOT NULL DEFAULT 0,
    Calories DOUBLE NOT NULL,
    CarbsGrams DOUBLE NOT NULL,
    ProteinGrams DOUBLE NOT NULL,
    FatGrams DOUBLE NOT NULL,
    MealType VARCHAR(20) NOT NULL DEFAULT 'all',
    ProteinDesc VARCHAR(255),
    CarbDesc VARCHAR(255),
    SoupDesc VARCHAR(255),
    VeggieDesc VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MODULE 3: WORKOUT TRACKING & ANALYTICS (TV4 quản lý nghiệp vụ, TV1 quản lý schema)
-- ============================================================================

-- 11. Bảng Nhóm bài tập
CREATE TABLE WorkoutCategories (
    CategoryId INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL,
    IconName VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Bảng Danh mục bài tập
CREATE TABLE Workouts (
    WorkoutId INT AUTO_INCREMENT PRIMARY KEY,
    CategoryId INT NULL,
    WorkoutName VARCHAR(150) NOT NULL,
    DurationMinutes INT NOT NULL,
    CaloriesBurned DOUBLE NOT NULL,
    IsCustom BOOLEAN DEFAULT FALSE,
    CreatedBy INT NULL,
    CONSTRAINT FK_Workouts_Category FOREIGN KEY (CategoryId) REFERENCES WorkoutCategories(CategoryId) ON DELETE SET NULL,
    CONSTRAINT FK_Workouts_User FOREIGN KEY (CreatedBy) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Bảng Nhật ký luyện tập
CREATE TABLE WorkoutLogs (
    LogId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    WorkoutId INT NOT NULL,
    LoggedDate DATE NOT NULL,
    DurationMinutes INT NOT NULL,
    CaloriesBurned DOUBLE NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_WorkoutLogs_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    CONSTRAINT FK_WorkoutLogs_Workouts FOREIGN KEY (WorkoutId) REFERENCES Workouts(WorkoutId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. Bảng Mục tiêu luyện tập tuần
CREATE TABLE WorkoutGoals (
    GoalId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL UNIQUE,
    WeeklySessionsTarget INT DEFAULT 4,
    WeeklyCaloriesTarget DOUBLE DEFAULT 1200,
    CONSTRAINT FK_WorkoutGoals_Users FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- NẠP DỮ LIỆU BAN ĐẦU (SEED DATA TOÀN DIỆN CHO KIỂM THỬ)
-- ============================================================================

-- 1. Tài khoản kiểm thử (Mật khẩu mặc định: 123456 - scrypt băm an toàn)
INSERT INTO Users (UserId, Email, PasswordHash, FullName, Role) VALUES
(1, 'admin@nutrifit.vn', 'scrypt:32768:8:1$kYgqXv4e7Hj$2c354e605d5e5e6a0d4c18f773418d18471bbadca161a0b36873bc0ee04344bebfcf23d5bf9273c683b584d4715fbc706adab5416cb482ce3bb0535bc20c57ff', 'Quản Trị Viên', 'ADMIN'),
(2, 'user@nutrifit.vn', 'scrypt:32768:8:1$kYgqXv4e7Hj$2c354e605d5e5e6a0d4c18f773418d18471bbadca161a0b36873bc0ee04344bebfcf23d5bf9273c683b584d4715fbc706adab5416cb482ce3bb0535bc20c57ff', 'Lê Phú Quý', 'MEMBER');

-- 2. Hồ sơ thể trạng mẫu cho User 2 (Mục tiêu duy trì cân nặng: 2000 kcal, nước 2275ml)
INSERT INTO UserProfiles (ProfileId, UserId, Gender, Age, HeightCm, WeightKg, ActivityLevel, Goal, Bmr, Tdee, TargetKcal, TargetWaterMl) VALUES
(1, 2, 'male', 22, 172, 65, 1.375, 'maintain', 1610.0, 2213.8, 2000.0, 2275);

-- 3. Nhật ký uống nước mẫu
INSERT INTO WaterIntakeLog (UserId, LoggedDate, AmountMl) VALUES
(2, CURRENT_DATE, 500),
(2, CURRENT_DATE, 350),
(2, CURRENT_DATE, 600);

-- 4. Nhật ký chỉ số cơ thể mẫu
INSERT INTO BodyMetricLog (UserId, RecordedDate, WeightKg, Bmi) VALUES
(2, CURRENT_DATE, 65.0, 21.97);

-- 5. Nhóm bài tập
INSERT INTO WorkoutCategories (CategoryId, CategoryName, IconName) VALUES
(1, 'Cardio (Tim mạch)', 'flame'),
(2, 'Gym (Kháng lực)', 'dumbbell'),
(3, 'Thể thao (Bóng đá, bơi...)','trophy'),
(4, 'Yoga & Giãn cơ', 'activity'),
(5, 'Tự chọn', 'plus-circle');

-- 6. Danh mục bài tập chuẩn
INSERT INTO Workouts (CategoryId, WorkoutName, DurationMinutes, CaloriesBurned, IsCustom) VALUES
(1, 'Chạy bộ ngoài trời', 30, 280, 0),
(1, 'Nhảy dây tốc độ', 20, 220, 0),
(2, 'Tập ngực & tay sau (Gym)', 45, 260, 0),
(2, 'Tập chân & mông (Squats)', 40, 290, 0),
(3, 'Đá bóng phong trào', 60, 450, 0),
(3, 'Bơi lội tự do', 45, 360, 0),
(4, 'Yoga giãn cơ buổi sáng', 30, 120, 0);

-- 7. Mục tiêu tập luyện tuần mẫu
INSERT INTO WorkoutGoals (UserId, WeeklySessionsTarget, WeeklyCaloriesTarget) VALUES
(2, 4, 1200);

-- 8. Nhật ký tập luyện mẫu
INSERT INTO WorkoutLogs (UserId, WorkoutId, LoggedDate, DurationMinutes, CaloriesBurned) VALUES
(2, 1, CURRENT_DATE, 30, 280),
(2, 3, CURRENT_DATE, 45, 260);

-- 9. Danh mục món Việt chuẩn tham chiếu
INSERT INTO DishCatalog (DishCatalogId, Category, StandardName, BaseCalories) VALUES
(1, 'CARB', 'Cơm gạo trắng', 200),
(2, 'CARB', 'Cơm gạo lứt huyết rồng', 180),
(3, 'PROTEIN', 'Thịt kho tàu nước dừa', 260),
(4, 'PROTEIN', 'Cá hồi áp chảo sốt bơ tỏi', 240),
(5, 'PROTEIN', 'Gà kho sả ớt', 220),
(6, 'SOUP', 'Canh chua cá lóc', 90),
(7, 'SOUP', 'Canh rau ngót thịt bằm', 75),
(8, 'VEGGIE', 'Rau muống xào tỏi', 80),
(9, 'VEGGIE', 'Bông cải xanh hấp', 45),
(10, 'DESSERT', 'Chuối tiêu chín', 90),
(11, 'DESSERT', 'Thanh long ruột trắng', 60);

-- 10. Phiên gợi ý mâm cơm mẫu (Bữa trưa hôm nay)
INSERT INTO MealSuggestions (SuggestionId, UserId, SuggestionDate, MealType, SelectedOption, Status) VALUES
(1, 2, CURRENT_DATE, 'lunch', 1, 'decided');

-- 11. Ba mâm cơm gợi ý cho phiên trên
INSERT INTO MealOption (OptionId, SuggestionId, OptionNumber, Title, DigestibilityNote) VALUES
(1, 1, 1, 'Mâm cơm Truyền Thống: Thịt kho & Canh chua', 'Cân đối dinh dưỡng, giàu đạm và vitamin C'),
(2, 1, 2, 'Mâm cơm Tinh Gọn: Cá hồi áp chảo bơ tỏi', 'Giàu Omega-3, tốt cho tim mạch và phục hồi cơ'),
(3, 1, 3, 'Mâm cơm Dân Dã: Gà kho sả ớt & Rau muống', 'Đậm đà hương vị quê hương, ấm bụng');

-- 12. Bảng phân tích dinh dưỡng chi tiết từng mâm cơm
INSERT INTO MealNutrition (NutritionId, OptionId, TotalCalories, CarbsGrams, ProteinGrams, FatGrams, FiberGrams) VALUES
(1, 1, 680, 85, 38, 22, 6.5),
(2, 2, 650, 75, 42, 20, 5.0),
(3, 3, 620, 80, 36, 18, 5.5);

-- 13. Chi tiết đủ 5 món cấu thành Mâm cơm 1
INSERT INTO MealComponentDish (OptionId, DishCatalogId, ComponentType, DishName) VALUES
(1, 1, 'CARB', 'Cơm gạo trắng (1 chén rưỡi)'),
(1, 3, 'PROTEIN', 'Thịt kho tàu nước dừa ít mỡ'),
(1, 6, 'SOUP', 'Canh chua cá lóc dọc mùng'),
(1, 8, 'VEGGIE', 'Rau muống xào tỏi non'),
(1, 10, 'DESSERT', '1 quả chuối tiêu chín');

-- Chi tiết Mâm cơm 2
INSERT INTO MealComponentDish (OptionId, DishCatalogId, ComponentType, DishName) VALUES
(2, 2, 'CARB', 'Cơm gạo lứt huyết rồng'),
(2, 4, 'PROTEIN', 'Cá hồi áp chảo sốt bơ tỏi'),
(2, 7, 'SOUP', 'Canh rau ngót thịt bằm'),
(2, 9, 'VEGGIE', 'Bông cải xanh luộc chấm kho quẹt'),
(2, 11, 'DESSERT', 'Nửa quả thanh long ruột trắng');

-- Chi tiết Mâm cơm 3
INSERT INTO MealComponentDish (OptionId, DishCatalogId, ComponentType, DishName) VALUES
(3, 1, 'CARB', 'Cơm trắng dẻo thơm'),
(3, 5, 'PROTEIN', 'Gà kho sả ớt cay nồng'),
(3, 7, 'SOUP', 'Canh bí đao nấu tôm khô'),
(3, 8, 'VEGGIE', 'Đậu que xào nấm rơm'),
(3, 10, 'DESSERT', 'Dưa hấu ướp lạnh thái lát');

-- 14. Kho 36 món ăn đường phố mua ngoài (Street Food)
INSERT INTO StreetFoodDish (Title, PriceVnd, Calories, CarbsGrams, ProteinGrams, FatGrams, MealType, ProteinDesc, CarbDesc, SoupDesc, VeggieDesc) VALUES
('Cơm tấm sườn bì chả', 45000, 620, 75, 32, 21, 'lunch', 'Sườn cốt lết nướng, bì heo, chả trứng hấp', 'Cơm tấm trắng thơm', 'Nước mắm chua ngọt, chén canh súp nóng', 'Đồ chua củ cải cà rốt, dưa leo'),
('Cơm gà xối mỡ đùi góc tư', 50000, 680, 82, 36, 24, 'lunch', 'Đùi gà chiên da giòn rụm', 'Cơm chiên cà chua hạt tơi', 'Chén nước súp thanh', 'Xà lách, cà chua, dưa leo'),
('Cơm sườn non ram mặn', 40000, 580, 72, 28, 20, 'lunch', 'Sườn non heo kho ram đậm đà', 'Cơm trắng dẻo', 'Canh rau ngót thịt bằm', 'Dưa leo, rau sống'),
('Cơm cá lóc kho tộ', 42000, 530, 70, 30, 14, 'lunch', 'Cá lóc đồng kho tiêu thơm nức', 'Cơm trắng', 'Canh chua cá bông điên điển', 'Rau muống luộc chấm nước cá'),
('Cơm thịt kho tàu trứng cút', 40000, 610, 70, 26, 25, 'lunch', 'Thịt ba rọi kho mềm rục, trứng cút', 'Cơm trắng nóng hổi', 'Canh bí đao tôm khô', 'Dưa giá, cải chua bóp xổi'),
('Cơm gà luộc xé phay Hội An', 45000, 510, 68, 33, 12, 'lunch', 'Thịt gà ta thả vườn luộc xé sợi', 'Cơm nấu nước luộc gà vàng ươm', 'Nước súp lòng gà', 'Hành tây ngâm chua, rau răm, gỏi bắp cải'),
('Cơm bò lúc lắc khoai tây', 55000, 640, 65, 34, 28, 'lunch', 'Thịt thăn bò áp chảo bơ tỏi mềm ngọt', 'Cơm chiên tỏi hoặc cơm trắng', 'Chén nước tương ớt cắt lát', 'Xà lách xoong, cà chua, khoai tây chiên'),
('Phở bò tái nạm truyền thống', 50000, 520, 65, 30, 15, 'all', 'Thịt bò tái mềm, nạm gầu giòn béo', 'Bánh phở mềm dai', 'Nước dùng hầm xương bò thanh trong thơm quế hồi', 'Rau quế, ngò gai, chanh ớt, giá trụng'),
('Phở gà ta lá chanh', 45000, 480, 64, 29, 12, 'all', 'Thịt gà ta da giòn thái miếng rắc lá chanh', 'Bánh phở mềm', 'Nước dùng gà hầm thanh ngọt', 'Hành hoa, rau mùi, quẩy giòn'),
('Bún bò Huế thập cẩm', 50000, 580, 66, 32, 20, 'all', 'Bắp bò hoa, giò heo, chả cua, huyết', 'Bún sợi to dai giòn', 'Nước dùng sả ớt mắm ruốc dậy mùi', 'Bắp chuối bào, giá đỗ, rau muống chẻ, chanh tươi'),
('Bún chả Hà Nội nướng than', 45000, 560, 68, 28, 19, 'lunch', 'Chả viên nướng xém cạnh, chả miếng ba chỉ', 'Bún lá tươi', 'Nước mắm chấm dấm tỏi ớt ấm nóng kèm đu đủ giòn', 'Xà lách, tía tô, kinh giới tươi ngon'),
('Hủ tiếu Nam Vang sườn tôm', 45000, 490, 62, 26, 15, 'all', 'Tôm thẻ tươi, thịt bằm, sườn non, tim cật, trứng cút', 'Hủ tiếu dai Nam Vang', 'Nước lèo xương ống hầm củ cải ngọt thanh', 'Cần tàu, hẹ lá, giá đỗ sống'),
('Bún riêu cua đồng bắp bò', 40000, 480, 60, 26, 16, 'all', 'Riêu cua đồng béo ngậy, bắp bò tái, đậu hũ chiên', 'Bún tươi', 'Nước dùng cà chua thanh mát vị dấm bỗng', 'Rau muống chẻ, hoa chuối, kinh giới'),
('Bún ốc chuối đậu Hà Nội', 45000, 470, 62, 24, 15, 'all', 'Ốc nhồi giòn sần sật, thịt ba chỉ, đậu hũ rán', 'Bún tươi sợi nhỏ', 'Nước ốc nấu chua cay nghệ vàng thơm lừng', 'Tía tô thái chỉ, rau thơm các loại'),
('Bánh canh ghẹ miền Tây', 55000, 510, 60, 28, 17, 'all', 'Thịt ghẹ xé tươi ngọt, chả cá thu', 'Sợi bánh canh bột lọc dai dẻo', 'Nước dùng sền sệt nấu gạch ghẹ đỏ au', 'Hành ngò, chanh ớt tiêu xay'),
('Mì Quảng tôm thịt trứng', 40000, 530, 65, 27, 18, 'lunch', 'Tôm rim đậm đà, thịt ba chỉ kho nghệ, trứng cút', 'Sợi mì Quảng vàng dẻo', 'Nước nhưỡng xăm xắp béo ngậy', 'Bánh tráng mè nướng giòn, bắp chuối, đậu phộng rang'),
('Bún cá rô đồng rau cải', 40000, 440, 58, 26, 11, 'dinner', 'Cá rô đồng chiên giòn rụm và thịt cá rim', 'Bún sợi nhỏ', 'Nước dùng xương cá hầm thanh ngọt', 'Rau cải xanh cay nồng, thì là'),
('Bún mắm miền Tây sặc sỡ', 55000, 610, 68, 34, 21, 'lunch', 'Tôm sú, mực tươi, heo quay giòn da, cá lóc phi lê', 'Bún tươi', 'Nước lèo nấu mắm cá linh cá sặc thơm nồng', 'Cà tím, bông súng, rau đắng, kèo nèo, bắp chuối'),
('Bánh canh cua chả cá', 45000, 490, 59, 27, 16, 'all', 'Thịt cua xé, chả cá chiên, giò heo', 'Bánh canh bột gạo mềm', 'Nước súp sền sệt nóng hổi', 'Ngò rí, tiêu sọ, quẩy'),
('Bún thịt nướng chả giò Sài Gòn', 40000, 530, 70, 25, 17, 'lunch', 'Thịt nạc dăm ướp sả nướng mè, chả giò chiên giòn', 'Bún tươi', 'Nước mắm chua ngọt tỏi ớt', 'Rau sống, xà lách, dưa leo, mỡ hành, đậu phộng'),
('Bánh mì chảo ốp la xíu mại pate', 35000, 490, 55, 22, 20, 'lunch', '2 trứng gà ốp la lòng đào, xíu mại sốt cà, pate béo', '1 ổ bánh mì đặc ruột giòn rụm', 'Nước sốt cà chua tiêu đen chấm bánh mì', 'Dưa leo, ngò gai'),
('Bánh mì kẹp thịt nguội pate', 25000, 420, 52, 18, 16, 'lunch', 'Chả lụa, giò thủ, thịt xá xíu, pate gan', 'Ổ bánh mì giòn tan', 'Nước sốt tương ớt đậm đà', 'Đồ chua, dưa leo, ớt sừng cay'),
('Bánh mì bò kho thơm lừng', 45000, 560, 63, 28, 21, 'all', 'Nạm bò hầm mềm gân, cà rốt ngọt', 'Ổ bánh mì nóng giòn', 'Nước sốt bò kho cay nồng hoa hồi quế chi', 'Rau quế, ngò gai, muối tiêu chanh'),
('Hủ tiếu khô xá xíu sườn non', 45000, 510, 68, 27, 14, 'all', 'Thịt xá xíu xắt lát mỏng, sườn non mềm ngọt', 'Sợi hủ tiếu dai trộn sốt hắc xì dầu', 'Chén canh súp tôm thịt hầm thanh', 'Hẹ lá, cần tây, giá đỗ'),
('Bún đậu mắm tôm thập cẩm', 50000, 590, 66, 31, 23, 'lunch', 'Đậu hũ rán vàng giòn, chả cốm chiên, thịt chân giò luộc', 'Bún lá ép miếng', 'Mắm tôm Thanh Hóa đánh sủi bọt tắc ớt', 'Dưa leo, kinh giới, tía tô tươi'),
('Mì trộn xá xíu lòng đào', 40000, 540, 72, 26, 17, 'lunch', 'Thịt xá xíu rim óng ánh, trứng lòng đào dẻo', 'Mì gói trụng trộn sốt chua ngọt đặc biệt', 'Chén nước súp hành lá', 'Cải thìa luộc, tóp mỡ giòn rụm'),
('Miến xào cua bể tay cầm', 60000, 510, 64, 28, 15, 'lunch', 'Thịt cua bể tươi bóc sẵn ngọt lịm', 'Sợi miến dong xào tơi mềm không dính', 'Nước tương tỏi ớt chấm kèm', 'Cà rốt, nấm mèo, cần tây, giá đỗ'),
('Bánh hỏi heo quay giòn bì', 45000, 550, 67, 24, 22, 'lunch', 'Thịt ba chỉ quay lớp da nổ giòn tan', 'Bánh hỏi thoa mỡ hành lá thơm phức', 'Nước mắm tỏi ớt chua ngọt', 'Rau thơm, xà lách, dưa leo cuốn bánh tráng'),
('Bánh xèo miền Tây giòn rụm', 40000, 520, 58, 22, 23, 'lunch', 'Tôm nõn, thịt ba rọi, giá đỗ, đậu xanh', 'Vỏ bánh xèo bột nghệ mỏng giòn rụm', 'Nước mắm chấm tỏi ớt cà rốt', 'Rau cải xanh, xà lách, lá lốt, đọt xoài non'),
('Cháo sườn sụn hạt sen', 35000, 390, 52, 22, 10, 'dinner', 'Sườn sụn giòn sần sật ninh nhừ, hạt sen bùi béo', 'Cháo gạo tẻ nấu sánh mịn nhuyễn', 'Tiêu bắc, hành hoa, quẩy nóng giòn', 'Gừng tươi thái chỉ giữ ấm bụng'),
('Cháo gà ta đậu xanh', 35000, 420, 54, 25, 11, 'dinner', 'Thịt gà xé sợi trộn tiêu muối ớt', 'Cháo đậu xanh nở búp ngọt bùi', 'Hành lá, tía tô, tiêu đen xay nhuyễn', 'Rau răm tươi cắt nhỏ'),
('Miến gà đồi nấu nấm hương', 45000, 430, 56, 27, 10, 'dinner', 'Thịt gà đồi luộc da giòn thịt săn chắc', 'Sợi miến dong trong suốt dai mềm', 'Nước dùng gà hầm nấm hương ngọt ngào', 'Hành lá, ngò gai, lá chanh non'),
('Bánh cuốn nóng thịt bằm mộc nhĩ', 35000, 410, 58, 18, 12, 'dinner', 'Thịt heo nạc bằm xào nấm mèo hành tây, chả lụa', 'Bánh tráng tay mỏng mướt tráng nóng', 'Nước mắm dấm ớt tỏi ấm nhẹ', 'Rau giá trụng, rau thơm, dưa leo xắt mỏng'),
('Cháo cá lóc rau đắng miền Tây', 40000, 380, 50, 24, 9, 'dinner', 'Phi lê cá lóc đồng hấp chín tới ngọt thịt', 'Cháo hoa nấu nở bung hạt', 'Nước mắm mặn ớt hiểm chấm cá', 'Đĩa rau đắng tươi mát, giá sống'),
('Cháo hàu sữa hạt sen', 45000, 410, 53, 23, 11, 'dinner', 'Hàu sữa tươi béo ngậy xào hành phi thơm phức', 'Cháo gạo sánh thơm hạt sen', 'Hành lá, ngò rí, tiêu xay mịn', 'Gừng sợi ấm bụng dễ tiêu'),
('Súp cua gà xé nấm tuyết', 35000, 320, 38, 22, 9, 'dinner', 'Thịt cua tươi, ức gà xé nhuyễn, nấm tuyết, trứng cút', 'Súp sánh mịn nấu từ nước dùng gà', 'Dầu mè, tiêu sọ, giấm tiều thơm lừng', 'Ngò rí tươi thái nhỏ');