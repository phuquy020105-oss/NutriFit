-- MySQL dump 10.13  Distrib 8.4.11, for Win64 (x86_64)
--
-- Host: localhost    Database: NutriFitDB
-- ------------------------------------------------------
-- Server version	8.4.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bodymetriclog`
--

DROP TABLE IF EXISTS `bodymetriclog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bodymetriclog` (
  `MetricId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `RecordedDate` date NOT NULL,
  `WeightKg` double NOT NULL,
  `Bmi` double NOT NULL,
  PRIMARY KEY (`MetricId`),
  KEY `FK_BodyMetric_Users` (`UserId`),
  CONSTRAINT `FK_BodyMetric_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dishcatalog`
--

DROP TABLE IF EXISTS `dishcatalog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dishcatalog` (
  `DishCatalogId` int NOT NULL AUTO_INCREMENT,
  `Category` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `StandardName` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `BaseCalories` double NOT NULL,
  PRIMARY KEY (`DishCatalogId`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mealcomponentdish`
--

DROP TABLE IF EXISTS `mealcomponentdish`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mealcomponentdish` (
  `ComponentId` int NOT NULL AUTO_INCREMENT,
  `OptionId` int NOT NULL,
  `DishCatalogId` int DEFAULT NULL,
  `ComponentType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DishName` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ComponentId`),
  KEY `FK_MealComponent_Option` (`OptionId`),
  KEY `FK_MealComponent_Catalog` (`DishCatalogId`),
  CONSTRAINT `FK_MealComponent_Catalog` FOREIGN KEY (`DishCatalogId`) REFERENCES `dishcatalog` (`DishCatalogId`) ON DELETE SET NULL,
  CONSTRAINT `FK_MealComponent_Option` FOREIGN KEY (`OptionId`) REFERENCES `mealoption` (`OptionId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=266 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mealnutrition`
--

DROP TABLE IF EXISTS `mealnutrition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mealnutrition` (
  `NutritionId` int NOT NULL AUTO_INCREMENT,
  `OptionId` int NOT NULL,
  `TotalCalories` double NOT NULL,
  `CarbsGrams` double NOT NULL,
  `ProteinGrams` double NOT NULL,
  `FatGrams` double NOT NULL,
  `FiberGrams` double DEFAULT '0',
  PRIMARY KEY (`NutritionId`),
  UNIQUE KEY `OptionId` (`OptionId`),
  CONSTRAINT `FK_MealNutrition_Option` FOREIGN KEY (`OptionId`) REFERENCES `mealoption` (`OptionId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mealoption`
--

DROP TABLE IF EXISTS `mealoption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mealoption` (
  `OptionId` int NOT NULL AUTO_INCREMENT,
  `SuggestionId` int NOT NULL,
  `OptionNumber` int NOT NULL,
  `Title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DigestibilityNote` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`OptionId`),
  KEY `FK_MealOption_Suggestion` (`SuggestionId`),
  CONSTRAINT `FK_MealOption_Suggestion` FOREIGN KEY (`SuggestionId`) REFERENCES `mealsuggestions` (`SuggestionId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mealsuggestions`
--

DROP TABLE IF EXISTS `mealsuggestions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mealsuggestions` (
  `SuggestionId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `SuggestionDate` date NOT NULL,
  `MealType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `SelectedOption` int DEFAULT NULL,
  `Status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`SuggestionId`),
  UNIQUE KEY `UQ_Meal_User_Date` (`UserId`,`SuggestionDate`,`MealType`),
  CONSTRAINT `FK_MealSuggestions_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nutritionfoodcatalog`
--

DROP TABLE IF EXISTS `nutritionfoodcatalog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nutritionfoodcatalog` (
  `DishId` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `NameVi` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ComponentType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PreparationState` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ReferenceGrams` decimal(9,2) NOT NULL,
  `MinGrams` decimal(9,2) NOT NULL,
  `MaxGrams` decimal(9,2) NOT NULL,
  `KcalPer100G` decimal(10,4) DEFAULT NULL,
  `ProteinPer100G` decimal(10,4) DEFAULT NULL,
  `CarbsPer100G` decimal(10,4) DEFAULT NULL,
  `FatPer100G` decimal(10,4) DEFAULT NULL,
  `FiberPer100G` decimal(10,4) DEFAULT NULL,
  `IngredientsJson` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `MealTypesJson` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `PrepMinutes` int DEFAULT NULL,
  `ProvenanceJson` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `Estimated` int NOT NULL DEFAULT '1',
  `IsActive` int NOT NULL DEFAULT '1',
  `DataVersion` int NOT NULL DEFAULT '1',
  `UpdatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`DishId`),
  KEY `ix_nutrition_catalog_active_type` (`IsActive`,`ComponentType`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nutritionfoodintake`
--

DROP TABLE IF EXISTS `nutritionfoodintake`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nutritionfoodintake` (
  `IntakeId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `RequestKey` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `RequestHash` char(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `IntakeDate` date NOT NULL,
  `OccurredAt` datetime NOT NULL,
  `MealType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `SnapshotJson` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `Version` int NOT NULL DEFAULT '1',
  `Deleted` int NOT NULL DEFAULT '0',
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`IntakeId`),
  UNIQUE KEY `uq_nutrition_request` (`UserId`,`RequestKey`),
  KEY `ix_nutrition_intake_day` (`UserId`,`IntakeDate`,`Deleted`),
  CONSTRAINT `fk_nutrition_intake_user` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nutritionlegacymenus`
--

DROP TABLE IF EXISTS `nutritionlegacymenus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nutritionlegacymenus` (
  `TemplateId` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `MealType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DayIndex` int NOT NULL,
  `TemplateJson` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `IsActive` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`TemplateId`),
  KEY `ix_nutrition_legacy_meal_day` (`MealType`,`DayIndex`,`IsActive`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nutritionmealdetails`
--

DROP TABLE IF EXISTS `nutritionmealdetails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nutritionmealdetails` (
  `OptionId` int NOT NULL,
  `RecipeJson` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `Version` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`OptionId`),
  CONSTRAINT `fk_nutrition_option` FOREIGN KEY (`OptionId`) REFERENCES `mealoption` (`OptionId`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `paymenttransactions`
--

DROP TABLE IF EXISTS `paymenttransactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paymenttransactions` (
  `TransactionId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `PlanId` int NOT NULL,
  `AmountVnd` int NOT NULL,
  `PaymentMethod` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `TransactionCode` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'SUCCESS',
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`TransactionId`),
  UNIQUE KEY `TransactionCode` (`TransactionCode`),
  KEY `FK_Payments_Users` (`UserId`),
  KEY `FK_Payments_Plans` (`PlanId`),
  CONSTRAINT `FK_Payments_Plans` FOREIGN KEY (`PlanId`) REFERENCES `subscriptionplans` (`PlanId`) ON DELETE RESTRICT,
  CONSTRAINT `FK_Payments_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registrationotpipquota`
--

DROP TABLE IF EXISTS `registrationotpipquota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registrationotpipquota` (
  `IPHash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `WindowStart` datetime NOT NULL,
  `SentInWindow` int NOT NULL,
  PRIMARY KEY (`IPHash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registrationotps`
--

DROP TABLE IF EXISTS `registrationotps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registrationotps` (
  `Email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `FullName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PasswordHash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `OTPHash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ExpiresAt` datetime NOT NULL,
  `LastSentAt` datetime NOT NULL,
  `Attempts` int NOT NULL,
  `WindowStart` datetime NOT NULL,
  `SentInWindow` int NOT NULL,
  PRIMARY KEY (`Email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `streetfooddish`
--

DROP TABLE IF EXISTS `streetfooddish`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `streetfooddish` (
  `DishId` int NOT NULL AUTO_INCREMENT,
  `Title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PriceVnd` int NOT NULL DEFAULT '0',
  `Calories` double NOT NULL,
  `CarbsGrams` double NOT NULL,
  `ProteinGrams` double NOT NULL,
  `FatGrams` double NOT NULL,
  `MealType` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'all',
  `ProteinDesc` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `CarbDesc` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `SoupDesc` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `VeggieDesc` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`DishId`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `subscriptionplans`
--

DROP TABLE IF EXISTS `subscriptionplans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subscriptionplans` (
  `PlanId` int NOT NULL AUTO_INCREMENT,
  `PlanName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PriceVnd` int NOT NULL,
  `DurationDays` int NOT NULL,
  `Description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `IsActive` tinyint(1) DEFAULT '1',
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`PlanId`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `userprofiles`
--

DROP TABLE IF EXISTS `userprofiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userprofiles` (
  `ProfileId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `Gender` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Age` int NOT NULL,
  `HeightCm` double NOT NULL,
  `WeightKg` double NOT NULL,
  `ActivityLevel` double NOT NULL,
  `Goal` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Bmr` double DEFAULT NULL,
  `Tdee` double DEFAULT NULL,
  `TargetKcal` double DEFAULT NULL,
  `TargetWaterMl` int DEFAULT NULL,
  `UpdatedAt` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ProfileId`),
  KEY `FK_Profiles_Users` (`UserId`),
  CONSTRAINT `FK_Profiles_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `UserId` int NOT NULL AUTO_INCREMENT,
  `Email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PasswordHash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `FullName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Role` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'MEMBER',
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  `SubscriptionStatus` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'FREE',
  `PremiumExpiresAt` datetime DEFAULT NULL,
  PRIMARY KEY (`UserId`),
  UNIQUE KEY `Email` (`Email`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `waterintakelog`
--

DROP TABLE IF EXISTS `waterintakelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `waterintakelog` (
  `WaterLogId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `LoggedDate` date NOT NULL,
  `AmountMl` int NOT NULL,
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`WaterLogId`),
  KEY `FK_WaterLog_Users` (`UserId`),
  CONSTRAINT `FK_WaterLog_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workoutcategories`
--

DROP TABLE IF EXISTS `workoutcategories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutcategories` (
  `CategoryId` int NOT NULL AUTO_INCREMENT,
  `CategoryName` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `IconName` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`CategoryId`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workoutgoals`
--

DROP TABLE IF EXISTS `workoutgoals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutgoals` (
  `GoalId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `WeeklySessionsTarget` int DEFAULT '4',
  `WeeklyCaloriesTarget` double DEFAULT '1200',
  PRIMARY KEY (`GoalId`),
  UNIQUE KEY `UserId` (`UserId`),
  CONSTRAINT `FK_WorkoutGoals_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workoutlogs`
--

DROP TABLE IF EXISTS `workoutlogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutlogs` (
  `LogId` int NOT NULL AUTO_INCREMENT,
  `UserId` int NOT NULL,
  `WorkoutId` int NOT NULL,
  `LoggedDate` date NOT NULL,
  `DurationMinutes` int NOT NULL,
  `CaloriesBurned` double NOT NULL,
  `CreatedAt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`LogId`),
  KEY `FK_WorkoutLogs_Users` (`UserId`),
  KEY `FK_WorkoutLogs_Workouts` (`WorkoutId`),
  CONSTRAINT `FK_WorkoutLogs_Users` FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`) ON DELETE CASCADE,
  CONSTRAINT `FK_WorkoutLogs_Workouts` FOREIGN KEY (`WorkoutId`) REFERENCES `workouts` (`WorkoutId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workouts`
--

DROP TABLE IF EXISTS `workouts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workouts` (
  `WorkoutId` int NOT NULL AUTO_INCREMENT,
  `CategoryId` int DEFAULT NULL,
  `WorkoutName` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DurationMinutes` int NOT NULL,
  `CaloriesBurned` double NOT NULL,
  `IsCustom` tinyint(1) DEFAULT '0',
  `CreatedBy` int DEFAULT NULL,
  PRIMARY KEY (`WorkoutId`),
  KEY `FK_Workouts_Category` (`CategoryId`),
  KEY `FK_Workouts_User` (`CreatedBy`),
  CONSTRAINT `FK_Workouts_Category` FOREIGN KEY (`CategoryId`) REFERENCES `workoutcategories` (`CategoryId`) ON DELETE SET NULL,
  CONSTRAINT `FK_Workouts_User` FOREIGN KEY (`CreatedBy`) REFERENCES `users` (`UserId`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'NutriFitDB'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-15  0:17:01
