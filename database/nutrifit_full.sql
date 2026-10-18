-- MySQL dump 10.13  Distrib 9.7.1, for macos15 (arm64)
--
-- Host: localhost    Database: NutriFitDB_Java
-- ------------------------------------------------------
-- Server version	9.7.1

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
  `metric_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `recorded_date` date NOT NULL,
  `weight_kg` decimal(6,2) NOT NULL,
  `bmi` decimal(6,2) DEFAULT NULL,
  PRIMARY KEY (`metric_id`),
  KEY `idx_metric_user_date` (`user_id`,`recorded_date`),
  CONSTRAINT `fk_metric_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_metric_weight` CHECK ((`weight_kg` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bodymetriclog`
--

LOCK TABLES `bodymetriclog` WRITE;
/*!40000 ALTER TABLE `bodymetriclog` DISABLE KEYS */;
/*!40000 ALTER TABLE `bodymetriclog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chatconversations`
--

DROP TABLE IF EXISTS `chatconversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chatconversations` (
  `conversation_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`conversation_id`),
  KEY `idx_chatconversation_user` (`user_id`),
  CONSTRAINT `fk_chatconversation_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chatconversations`
--

LOCK TABLES `chatconversations` WRITE;
/*!40000 ALTER TABLE `chatconversations` DISABLE KEYS */;
INSERT INTO `chatconversations` VALUES (1,3,'hello','2026-10-17 20:58:07','2026-10-17 20:58:07'),(2,3,'hello','2026-10-17 21:31:50','2026-10-17 21:31:56'),(3,3,'fuck you','2026-10-18 21:53:50','2026-10-18 21:53:50');
/*!40000 ALTER TABLE `chatconversations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chatmessages`
--

DROP TABLE IF EXISTS `chatmessages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chatmessages` (
  `message_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `conversation_id` bigint unsigned NOT NULL,
  `sender_role` enum('USER','ASSISTANT','SYSTEM') COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `idx_chatmessage_conversation_date` (`conversation_id`,`created_at`),
  CONSTRAINT `fk_chatmessage_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `chatconversations` (`conversation_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chatmessages`
--

LOCK TABLES `chatmessages` WRITE;
/*!40000 ALTER TABLE `chatmessages` DISABLE KEYS */;
INSERT INTO `chatmessages` VALUES (1,1,'USER','hello','2026-10-17 20:58:07'),(2,1,'SYSTEM','Chưa thiết lập Gemini API Key trên Tomcat. Hãy cấu hình GEMINI_API_KEY rồi khởi động lại.','2026-10-17 20:58:07'),(3,2,'USER','hello','2026-10-17 21:31:50'),(4,2,'ASSISTANT','Chào bạn! Mình là **NutriFit AI**, trợ lý đồng hành cùng bạn về dinh dưỡng, tập luyện và chăm sóc sức khỏe tổng quát.\n\nHôm nay mình có thể hỗ trợ gì cho bạn? Bạn đang muốn:\n- Lên thực đơn ăn uống lành mạnh (tăng cơ, giảm mỡ, ăn chay...)?\n- Thiết kế lịch tập luyện phù hợp với thể trạng?\n- Hay cần lời khuyên về phục hồi và cải thiện sức khỏe nói chung? \n\nHãy chia sẻ thêm về mục tiêu của bạn nhé!','2026-10-17 21:31:56'),(5,3,'USER','fuck you','2026-10-18 21:53:50'),(6,3,'SYSTEM','Chưa thiết lập Gemini API Key trên Tomcat. Hãy cấu hình GEMINI_API_KEY rồi khởi động lại.','2026-10-18 21:53:50');
/*!40000 ALTER TABLE `chatmessages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `foodpreferences`
--

DROP TABLE IF EXISTS `foodpreferences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `foodpreferences` (
  `preference_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `food_id` bigint unsigned NOT NULL,
  `type` enum('LIKE','DISLIKE') COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`preference_id`),
  UNIQUE KEY `uq_foodpref_user_food` (`user_id`,`food_id`),
  KEY `fk_foodpref_food` (`food_id`),
  CONSTRAINT `fk_foodpref_food` FOREIGN KEY (`food_id`) REFERENCES `foods` (`food_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_foodpref_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `foodpreferences`
--

LOCK TABLES `foodpreferences` WRITE;
/*!40000 ALTER TABLE `foodpreferences` DISABLE KEYS */;
/*!40000 ALTER TABLE `foodpreferences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `foods`
--

DROP TABLE IF EXISTS `foods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `foods` (
  `food_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `calories_per_100g` decimal(10,3) NOT NULL DEFAULT '0.000',
  `protein_per_100g` decimal(10,3) NOT NULL DEFAULT '0.000',
  `carbs_per_100g` decimal(10,3) NOT NULL DEFAULT '0.000',
  `fat_per_100g` decimal(10,3) NOT NULL DEFAULT '0.000',
  `fiber_per_100g` decimal(10,3) NOT NULL DEFAULT '0.000',
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`food_id`),
  CONSTRAINT `ck_food_nutrients` CHECK (((`calories_per_100g` >= 0) and (`protein_per_100g` >= 0) and (`carbs_per_100g` >= 0) and (`fat_per_100g` >= 0) and (`fiber_per_100g` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=128 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `foods`
--

LOCK TABLES `foods` WRITE;
/*!40000 ALTER TABLE `foods` DISABLE KEYS */;
INSERT INTO `foods` VALUES (1,'Cơm trắng gạo tẻ đã nấu, không dầu',130.000,2.700,28.000,0.300,0.400,1),(2,'Bánh phở tươi đã trụng, để ráo',110.000,2.000,24.000,0.300,0.400,1),(3,'Bún tươi đã trụng, để ráo',110.000,2.000,24.000,0.200,0.500,1),(4,'Hủ tiếu gạo đã trụng, để ráo',110.000,2.000,24.000,0.200,0.400,1),(5,'Bánh canh bột gạo đã luộc, để ráo',105.000,1.500,24.000,0.200,0.300,1),(6,'Bánh mì trắng ổ không nhân',270.000,9.000,52.000,3.000,2.500,1),(7,'Gạo tẻ trắng khô',360.000,7.000,79.000,0.800,1.000,1),(8,'Xôi nếp trắng đã hấp, không dầu',170.000,3.500,37.000,0.500,0.800,1),(9,'Bột gạo tẻ khô',360.000,6.000,80.000,1.000,1.000,1),(10,'Bột năng khô',350.000,0.200,87.000,0.100,0.000,1),(11,'Thịt bò thăn nạc luộc chín, không sốt',210.000,29.000,0.000,10.000,0.000,1),(12,'Thịt ức gà luộc chín, bỏ da',165.000,31.000,0.000,3.600,0.000,1),(13,'Thịt đùi gà hấp chín, có da, bỏ xương',230.000,25.000,0.000,14.000,0.000,1),(14,'Thịt bắp bò luộc chín',210.000,30.000,0.000,9.000,0.000,1),(15,'Thịt heo nạc luộc chín',190.000,29.000,0.000,8.000,0.000,1),(16,'Thịt heo nạc băm hấp chín, không dầu',200.000,28.000,0.000,9.000,0.000,1),(17,'Gan heo luộc chín',170.000,25.000,4.000,6.000,0.000,1),(18,'Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được',500.000,10.000,0.000,51.000,0.000,1),(19,'Thịt nạc vai heo nướng chín, không sốt',260.000,27.000,0.000,17.000,0.000,1),(20,'Thịt sườn heo hấp chín, bỏ xương, không sốt',280.000,25.000,0.000,20.000,0.000,1),(21,'Thịt bò thăn áp chảo chín, không dầu/sốt',220.000,29.000,0.000,11.000,0.000,1),(22,'Thịt đùi gà hấp chín, bỏ da và xương',180.000,26.000,0.000,8.000,0.000,1),(23,'Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt',100.000,21.000,0.000,2.000,0.000,1),(24,'Thịt cá rô phi hấp chín, bỏ xương, không dầu/sốt',128.000,26.000,0.000,2.500,0.000,1),(25,'Tôm thẻ luộc chín, bóc vỏ',100.000,24.000,0.200,0.300,0.000,1),(26,'Thịt/riêu cua đồng nấu chín, lọc sạch vỏ',95.000,18.000,1.000,2.000,0.000,1),(27,'Thịt cua biển hấp chín, gỡ vỏ',100.000,20.000,0.500,1.500,0.000,1),(28,'Trứng gà nguyên quả sống, bỏ vỏ',143.000,12.600,0.700,9.500,0.000,1),(29,'Trứng gà luộc chín, bỏ vỏ',155.000,12.600,1.100,10.600,0.000,1),(30,'Trứng cút luộc chín, bỏ vỏ',158.000,13.000,0.500,11.000,0.000,1),(31,'Đậu hũ trắng không chiên',90.000,9.000,2.000,5.000,0.600,1),(32,'Chả lụa thành phẩm',170.000,17.000,7.000,8.000,0.200,1),(33,'Đậu phộng rang không muối, bỏ vỏ lụa',590.000,25.000,13.000,50.000,8.500,1),(34,'Cà chua sống',20.000,0.600,4.000,0.200,1.200,1),(35,'Dưa leo sống, giữ vỏ ăn được',15.000,0.700,2.800,0.100,0.500,1),(36,'Xà lách sống',15.000,1.400,1.500,0.200,1.300,1),(37,'Giá đỗ đậu xanh sống',30.000,3.000,4.000,0.200,1.800,1),(38,'Hành tây sống',41.000,1.800,8.200,0.100,1.700,1),(39,'Hành lá sống',32.000,1.800,4.700,0.200,2.600,1),(40,'Ngò rí sống',23.000,2.100,1.000,0.500,2.800,1),(41,'Húng quế sống',23.000,3.000,1.000,0.600,1.600,1),(42,'Rau răm sống',30.000,3.000,2.500,0.500,3.000,1),(43,'Hẹ lá sống',30.000,3.300,2.000,0.700,2.500,1),(44,'Sả tươi băm, phần lõi ăn được',99.000,1.800,20.000,0.500,2.500,1),(45,'Gừng tươi sống, gọt vỏ',29.000,0.400,5.100,0.800,3.500,1),(46,'Tỏi ta sống, bóc vỏ',121.000,6.000,23.000,0.500,2.100,1),(47,'Hành tím sống, bóc vỏ',72.000,2.500,14.000,0.100,3.200,1),(48,'Ớt tươi sống',40.000,1.900,7.300,0.400,1.500,1),(49,'Cà rốt sống, sơ chế',41.000,0.900,6.800,0.200,2.800,1),(50,'Củ cải trắng sống, sơ chế',18.000,0.600,2.500,0.100,1.600,1),(51,'Đu đủ xanh sống, bỏ vỏ/hạt',35.000,0.600,7.000,0.100,1.800,1),(52,'Ớt chuông sống',31.000,1.000,3.900,0.300,2.100,1),(53,'Thơm chín tươi, bỏ vỏ/mắt/lõi cứng',50.000,0.500,11.800,0.100,1.400,1),(54,'Đậu bắp sống, bỏ cuống',33.000,1.900,4.300,0.200,3.200,1),(55,'Bạc hà/dọc mùng, phần thân đã tước vỏ',14.000,0.700,1.800,0.100,1.500,1),(56,'Bí đỏ sống, bỏ vỏ/hạt',26.000,1.000,5.000,0.100,0.500,1),(57,'Rau ngổ sống',25.000,2.000,2.000,0.400,2.500,1),(58,'Ngò gai sống',25.000,2.000,2.000,0.400,2.500,1),(59,'Nấm mèo khô',293.000,9.000,52.000,1.000,25.000,1),(60,'Nấm hương khô',296.000,9.500,53.000,1.000,12.000,1),(61,'Dầu đậu nành tinh luyện',884.000,0.000,0.000,100.000,0.000,1),(62,'Nước mắm nguyên chất',40.000,6.000,4.000,0.000,0.000,1),(63,'Nước tương lên men',55.000,8.000,5.000,0.500,0.500,1),(64,'Đường trắng tinh luyện',400.000,0.000,100.000,0.000,0.000,1),(65,'Muối ăn iod',0.000,0.000,0.000,0.000,0.000,1),(66,'Tiêu đen xay khô',255.000,10.000,40.000,3.300,25.000,1),(67,'Nước cốt chanh tươi, bỏ hạt',25.000,0.400,6.000,0.100,0.300,1),(68,'Giấm gạo',18.000,0.000,0.500,0.000,0.000,1),(69,'Thịt me chín dạng nhuyễn, bỏ hạt',240.000,3.000,53.000,0.600,5.000,1),(70,'Nước dừa tươi',19.000,0.700,3.700,0.200,0.000,1),(71,'Nước lọc dùng trong món',0.000,0.000,0.000,0.000,0.000,1),(72,'Nước dùng phở bò thành phẩm, không nêm',20.000,2.000,0.500,1.000,0.000,1),(73,'Nước dùng gà thành phẩm, không nêm',20.000,2.500,0.500,0.800,0.000,1),(74,'Nước dùng heo thành phẩm, không nêm',20.000,2.000,0.500,1.000,0.000,1),(75,'Mắm ruốc Huế thành phẩm',100.000,15.000,4.000,2.500,0.500,1),(76,'Mắm tôm thành phẩm',80.000,12.000,4.000,1.500,0.300,1),(77,'Dầu điều màu thành phẩm',884.000,0.000,0.000,100.000,0.000,1),(78,'Bột nghệ khô',310.000,9.000,44.000,3.000,22.000,1),(79,'Mật ong',304.000,0.300,82.000,0.000,0.000,1),(80,'Hành phi thành phẩm',500.000,6.000,45.000,32.000,6.000,1),(81,'Cơm gạo tấm đã nấu, không dầu',130.000,2.500,28.000,0.300,0.300,1),(82,'Thịt heo băm viên nướng chín, không sốt',270.000,26.000,0.000,18.000,0.000,1);
/*!40000 ALTER TABLE `foods` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mealentries`
--

DROP TABLE IF EXISTS `mealentries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mealentries` (
  `entry_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `plan_id` bigint unsigned NOT NULL,
  `recipe_id` bigint unsigned NOT NULL,
  `recipe_name_snapshot` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `meal_type` enum('BREAKFAST','LUNCH','DINNER') COLLATE utf8mb4_unicode_ci NOT NULL,
  `servings` decimal(8,2) NOT NULL,
  `calories_kcal` decimal(12,3) NOT NULL,
  `protein_g` decimal(12,3) NOT NULL,
  `carbs_g` decimal(12,3) NOT NULL,
  `fat_g` decimal(12,3) NOT NULL,
  `fiber_g` decimal(12,3) NOT NULL,
  `recorded_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`entry_id`),
  UNIQUE KEY `uq_mealentry_plan_meal_recipe` (`plan_id`,`meal_type`,`recipe_id`),
  KEY `fk_mealentry_recipe` (`recipe_id`),
  KEY `idx_mealentry_plan` (`plan_id`),
  CONSTRAINT `fk_mealentry_plan` FOREIGN KEY (`plan_id`) REFERENCES `mealplans` (`plan_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_mealentry_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`recipe_id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_mealentry_values` CHECK (((`servings` > 0) and (`calories_kcal` >= 0) and (`protein_g` >= 0) and (`carbs_g` >= 0) and (`fat_g` >= 0) and (`fiber_g` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mealentries`
--

LOCK TABLES `mealentries` WRITE;
/*!40000 ALTER TABLE `mealentries` DISABLE KEYS */;
INSERT INTO `mealentries` VALUES (2,2,1,'Phở bò','BREAKFAST',3.00,1368.870,103.839,150.135,35.010,5.526,'2026-10-18 23:06:13'),(3,2,11,'Cơm tấm sườn','LUNCH',1.00,645.275,31.712,66.585,26.805,2.554,'2026-10-18 23:09:55'),(4,2,21,'Cơm cá hấp','DINNER',1.00,368.220,28.974,48.871,5.840,1.755,'2026-10-18 23:10:05');
/*!40000 ALTER TABLE `mealentries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mealplans`
--

DROP TABLE IF EXISTS `mealplans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mealplans` (
  `plan_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `plan_date` date NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`plan_id`),
  UNIQUE KEY `uq_mealplan_user_date` (`user_id`,`plan_date`),
  CONSTRAINT `fk_mealplan_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mealplans`
--

LOCK TABLES `mealplans` WRITE;
/*!40000 ALTER TABLE `mealplans` DISABLE KEYS */;
INSERT INTO `mealplans` VALUES (1,3,'2026-10-17','2026-10-17 22:53:19'),(2,3,'2026-10-18','2026-10-18 23:06:13');
/*!40000 ALTER TABLE `mealplans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `password_reset_otps`
--

DROP TABLE IF EXISTS `password_reset_otps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `password_reset_otps` (
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `otp_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expires_at` datetime NOT NULL,
  `attempts` int unsigned NOT NULL DEFAULT '0',
  `last_sent_at` datetime NOT NULL,
  `window_start` datetime NOT NULL,
  `sent_in_window` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`email`),
  CONSTRAINT `fk_password_reset_email` FOREIGN KEY (`email`) REFERENCES `users` (`email`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `password_reset_otps`
--

LOCK TABLES `password_reset_otps` WRITE;
/*!40000 ALTER TABLE `password_reset_otps` DISABLE KEYS */;
/*!40000 ALTER TABLE `password_reset_otps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paymenttransactions`
--

DROP TABLE IF EXISTS `paymenttransactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paymenttransactions` (
  `transaction_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `plan_id` bigint unsigned NOT NULL,
  `amount_vnd` bigint unsigned NOT NULL,
  `method` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'VNPAY',
  `transaction_code` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('PENDING','SUCCESS','FAILED','CANCELLED') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING',
  `paid_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`transaction_id`),
  UNIQUE KEY `transaction_code` (`transaction_code`),
  KEY `fk_payment_plan` (`plan_id`),
  KEY `idx_payment_user_created` (`user_id`,`created_at`),
  CONSTRAINT `fk_payment_plan` FOREIGN KEY (`plan_id`) REFERENCES `subscriptionplans` (`plan_id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_payment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paymenttransactions`
--

LOCK TABLES `paymenttransactions` WRITE;
/*!40000 ALTER TABLE `paymenttransactions` DISABLE KEYS */;
INSERT INTO `paymenttransactions` VALUES (1,3,1,49000,'VNPAY','1N08CMIDSK5GEUIJDOFSR6OLTC','PENDING',NULL,'2026-10-17 21:30:20','2026-10-17 21:30:20');
/*!40000 ALTER TABLE `paymenttransactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipeingredients`
--

DROP TABLE IF EXISTS `recipeingredients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipeingredients` (
  `ingredient_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `recipe_id` bigint unsigned NOT NULL,
  `food_id` bigint unsigned NOT NULL,
  `quantity_grams` decimal(10,2) NOT NULL,
  PRIMARY KEY (`ingredient_id`),
  KEY `idx_ingredient_recipe` (`recipe_id`),
  KEY `idx_ingredient_food` (`food_id`),
  CONSTRAINT `fk_ingredient_food` FOREIGN KEY (`food_id`) REFERENCES `foods` (`food_id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ingredient_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`recipe_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_ingredient_quantity` CHECK ((`quantity_grams` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=512 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipeingredients`
--

LOCK TABLES `recipeingredients` WRITE;
/*!40000 ALTER TABLE `recipeingredients` DISABLE KEYS */;
INSERT INTO `recipeingredients` VALUES (1,1,2,180.00),(2,1,11,80.00),(3,1,37,30.00),(4,1,38,15.00),(5,1,39,5.00),(6,1,40,3.00),(7,1,41,3.00),(8,1,62,6.00),(9,1,64,2.00),(10,1,66,0.20),(11,1,67,5.00),(12,1,72,300.00),(13,2,2,180.00),(14,2,12,80.00),(15,2,37,30.00),(16,2,38,15.00),(17,2,39,5.00),(18,2,40,3.00),(19,2,58,2.00),(20,2,62,6.00),(21,2,64,2.00),(22,2,66,0.20),(23,2,67,5.00),(24,2,73,300.00),(25,3,6,80.00),(26,3,28,100.00),(27,3,35,40.00),(28,3,40,3.00),(29,3,49,15.00),(30,3,61,5.00),(31,3,63,5.00),(32,3,64,2.00),(33,3,65,0.30),(34,3,66,0.20),(35,3,68,3.00),(36,4,3,180.00),(37,4,14,90.00),(38,4,37,30.00),(39,4,38,15.00),(40,4,39,5.00),(41,4,41,3.00),(42,4,44,3.00),(43,4,48,1.00),(44,4,58,3.00),(45,4,62,5.00),(46,4,64,2.00),(47,4,67,5.00),(48,4,72,300.00),(49,4,75,3.00),(50,4,77,3.00),(51,5,4,160.00),(52,5,15,40.00),(53,5,17,20.00),(54,5,25,35.00),(55,5,30,20.00),(56,5,37,30.00),(57,5,39,5.00),(58,5,43,5.00),(59,5,46,2.00),(60,5,50,30.00),(61,5,61,3.00),(62,5,62,6.00),(63,5,64,2.00),(64,5,66,0.20),(65,5,74,280.00),(66,6,7,40.00),(67,6,12,70.00),(68,6,39,5.00),(69,6,42,3.00),(70,6,45,2.00),(71,6,47,3.00),(72,6,61,3.00),(73,6,62,5.00),(74,6,65,0.50),(75,6,66,0.20),(76,6,71,350.00),(77,7,9,45.00),(78,7,10,10.00),(79,7,16,45.00),(80,7,32,30.00),(81,7,35,40.00),(82,7,47,5.00),(83,7,48,1.00),(84,7,59,2.00),(85,7,61,4.00),(86,7,62,8.00),(87,7,64,4.00),(88,7,67,4.00),(89,7,71,150.00),(90,7,80,3.00),(91,8,3,170.00),(92,8,26,60.00),(93,8,31,60.00),(94,8,34,100.00),(95,8,36,30.00),(96,8,37,30.00),(97,8,39,5.00),(98,8,41,3.00),(99,8,47,4.00),(100,8,62,5.00),(101,8,64,2.00),(102,8,67,5.00),(103,8,74,250.00),(104,8,76,3.00),(105,8,77,3.00),(106,9,8,160.00),(107,9,13,80.00),(108,9,35,40.00),(109,9,39,5.00),(110,9,60,2.00),(111,9,61,3.00),(112,9,63,8.00),(113,9,64,2.00),(114,9,66,0.20),(115,9,71,20.00),(116,9,80,5.00),(117,10,5,180.00),(118,10,10,5.00),(119,10,27,70.00),(120,10,39,5.00),(121,10,40,3.00),(122,10,47,3.00),(123,10,62,6.00),(124,10,64,2.00),(125,10,66,0.20),(126,10,71,30.00),(127,10,74,280.00),(128,10,77,3.00),(129,11,20,100.00),(130,11,34,40.00),(131,11,35,60.00),(132,11,39,5.00),(133,11,46,4.00),(134,11,49,20.00),(135,11,51,20.00),(136,11,61,6.00),(137,11,62,8.00),(138,11,63,5.00),(139,11,64,5.00),(140,11,66,0.30),(141,11,68,4.00),(142,11,71,20.00),(143,11,79,4.00),(144,11,81,180.00),(145,12,1,160.00),(146,12,13,120.00),(147,12,34,40.00),(148,12,35,60.00),(149,12,36,30.00),(150,12,46,4.00),(151,12,61,12.00),(152,12,63,8.00),(153,12,64,3.00),(154,12,66,0.20),(155,12,67,4.00),(156,12,71,15.00),(157,12,78,0.30),(158,13,1,150.00),(159,13,18,70.00),(160,13,29,50.00),(161,13,35,60.00),(162,13,39,4.00),(163,13,46,3.00),(164,13,47,4.00),(165,13,62,8.00),(166,13,64,4.00),(167,13,66,0.30),(168,13,70,40.00),(169,13,71,20.00),(170,14,1,150.00),(171,14,23,100.00),(172,14,35,60.00),(173,14,39,4.00),(174,14,46,3.00),(175,14,47,5.00),(176,14,61,4.00),(177,14,62,8.00),(178,14,64,5.00),(179,14,66,0.50),(180,14,71,30.00),(181,15,3,180.00),(182,15,19,60.00),(183,15,36,40.00),(184,15,40,3.00),(185,15,41,3.00),(186,15,46,4.00),(187,15,47,4.00),(188,15,49,20.00),(189,15,51,30.00),(190,15,62,10.00),(191,15,64,6.00),(192,15,66,0.30),(193,15,67,4.00),(194,15,68,5.00),(195,15,71,60.00),(196,15,82,45.00),(197,16,3,180.00),(198,16,19,90.00),(199,16,33,10.00),(200,16,35,50.00),(201,16,36,40.00),(202,16,37,30.00),(203,16,39,5.00),(204,16,44,3.00),(205,16,46,4.00),(206,16,49,20.00),(207,16,61,5.00),(208,16,62,8.00),(209,16,63,5.00),(210,16,64,4.00),(211,16,67,4.00),(212,16,68,4.00),(213,16,71,35.00),(214,16,79,3.00),(215,17,1,150.00),(216,17,21,100.00),(217,17,34,40.00),(218,17,36,30.00),(219,17,38,35.00),(220,17,46,4.00),(221,17,52,60.00),(222,17,61,8.00),(223,17,62,3.00),(224,17,63,8.00),(225,17,64,3.00),(226,17,66,0.30),(227,18,1,160.00),(228,18,12,100.00),(229,18,35,60.00),(230,18,36,30.00),(231,18,40,3.00),(232,18,45,4.00),(233,18,46,3.00),(234,18,61,3.00),(235,18,62,8.00),(236,18,64,4.00),(237,18,67,5.00),(238,18,71,20.00),(239,18,78,0.30),(240,19,1,150.00),(241,19,20,100.00),(242,19,34,40.00),(243,19,35,60.00),(244,19,39,4.00),(245,19,46,4.00),(246,19,47,4.00),(247,19,61,5.00),(248,19,62,5.00),(249,19,63,8.00),(250,19,64,4.00),(251,19,66,0.30),(252,19,71,30.00),(253,20,1,150.00),(254,20,24,110.00),(255,20,34,40.00),(256,20,35,60.00),(257,20,36,30.00),(258,20,46,3.00),(259,20,61,10.00),(260,20,62,8.00),(261,20,64,3.00),(262,20,66,0.20),(263,20,67,5.00),(264,20,71,20.00),(265,21,1,150.00),(266,21,23,110.00),(267,21,35,60.00),(268,21,38,25.00),(269,21,39,5.00),(270,21,45,6.00),(271,21,61,3.00),(272,21,62,3.00),(273,21,63,8.00),(274,21,64,2.00),(275,21,66,0.20),(276,21,71,20.00),(277,22,1,150.00),(278,22,18,80.00),(279,22,35,70.00),(280,22,39,4.00),(281,22,46,3.00),(282,22,47,5.00),(283,22,62,8.00),(284,22,64,4.00),(285,22,66,0.30),(286,22,71,15.00),(287,23,1,150.00),(288,23,23,100.00),(289,23,34,80.00),(290,23,37,30.00),(291,23,46,3.00),(292,23,53,50.00),(293,23,54,50.00),(294,23,55,40.00),(295,23,57,3.00),(296,23,58,3.00),(297,23,61,3.00),(298,23,62,8.00),(299,23,64,4.00),(300,23,65,0.30),(301,23,69,8.00),(302,23,71,220.00),(303,24,1,150.00),(304,24,22,110.00),(305,24,35,60.00),(306,24,39,4.00),(307,24,45,8.00),(308,24,46,3.00),(309,24,47,5.00),(310,24,61,4.00),(311,24,62,8.00),(312,24,64,4.00),(313,24,66,0.20),(314,24,71,40.00),(315,25,1,150.00),(316,25,31,180.00),(317,25,34,120.00),(318,25,36,50.00),(319,25,38,20.00),(320,25,39,5.00),(321,25,46,3.00),(322,25,61,8.00),(323,25,63,8.00),(324,25,64,3.00),(325,25,65,0.50),(326,25,66,0.20),(327,25,71,40.00),(328,26,1,150.00),(329,26,25,110.00),(330,26,34,40.00),(331,26,35,60.00),(332,26,39,4.00),(333,26,46,4.00),(334,26,47,4.00),(335,26,61,5.00),(336,26,62,8.00),(337,26,64,5.00),(338,26,66,0.20),(339,26,71,25.00),(340,27,1,150.00),(341,27,15,110.00),(342,27,35,60.00),(343,27,36,50.00),(344,27,40,3.00),(345,27,46,4.00),(346,27,48,1.00),(347,27,62,8.00),(348,27,64,4.00),(349,27,66,0.20),(350,27,67,5.00),(351,27,71,25.00),(352,28,1,150.00),(353,28,16,60.00),(354,28,39,5.00),(355,28,47,4.00),(356,28,56,180.00),(357,28,61,3.00),(358,28,62,6.00),(359,28,65,0.50),(360,28,66,0.20),(361,28,71,220.00),(362,29,1,150.00),(363,29,23,100.00),(364,29,35,60.00),(365,29,39,4.00),(366,29,45,6.00),(367,29,46,3.00),(368,29,47,4.00),(369,29,61,4.00),(370,29,62,8.00),(371,29,64,4.00),(372,29,66,0.30),(373,29,71,30.00),(374,30,1,150.00),(375,30,28,100.00),(376,30,34,60.00),(377,30,35,60.00),(378,30,39,8.00),(379,30,47,4.00),(380,30,61,7.00),(381,30,62,5.00),(382,30,65,0.30),(383,30,66,0.20);
/*!40000 ALTER TABLE `recipeingredients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipes`
--

DROP TABLE IF EXISTS `recipes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipes` (
  `recipe_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `meal_type` enum('BREAKFAST','LUNCH','DINNER') COLLATE utf8mb4_unicode_ci NOT NULL,
  `base_servings` decimal(8,2) NOT NULL DEFAULT '1.00',
  `instructions` text COLLATE utf8mb4_unicode_ci,
  `image_url` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `prep_minutes` int unsigned DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`recipe_id`),
  CONSTRAINT `ck_recipe_servings` CHECK ((`base_servings` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipes`
--

LOCK TABLES `recipes` WRITE;
/*!40000 ALTER TABLE `recipes` DISABLE KEYS */;
INSERT INTO `recipes` VALUES (1,'Phở bò','BREAKFAST',1.00,'Hâm nước dùng và nêm lượng nước mắm/đường đã kê; trụng bánh phở, xếp bò chín; thêm rau, nước dùng, chanh và tiêu.',NULL,20,1),(2,'Phở gà','BREAKFAST',1.00,'Hâm nước dùng gà và nêm; trụng phở, xé gà; thêm rau, nước dùng, chanh và tiêu.',NULL,20,1),(3,'Bánh mì trứng','BREAKFAST',1.00,'Pha cà rốt với giấm/đường và dùng hết phần pha; rán trứng với phần dầu giữ lại và muối; kẹp trứng, rau, nước tương, tiêu.',NULL,15,1),(4,'Bún bò Huế','BREAKFAST',1.00,'Hâm nước dùng; cho sả băm, mắm ruốc, dầu điều, nước mắm, đường và đun; xếp bún, bò, rau; chan nước và thêm chanh/ớt.',NULL,25,1),(5,'Hủ tiếu Nam Vang','BREAKFAST',1.00,'Nấu củ cải và tỏi với nước dùng, dùng hết nước; nêm; trụng hủ tiếu, xếp các phần thịt/gan/tôm/trứng; thêm giá, hẹ, hành.',NULL,25,1),(6,'Cháo gà','BREAKFAST',1.00,'Nấu gạo thành cháo; bù nước để đạt phần nước giữ trong suất; cho gà, gừng và gia vị; phi hành bằng dầu kê riêng và cho hết vào tô, thêm rau.',NULL,45,1),(7,'Bánh cuốn','BREAKFAST',1.00,'Ngâm nấm, phần nước ngấm giữ lại đề xuất 10 g; pha bột với 110 g nước để tráng; làm nhân heo/nấm và dùng 4 g dầu cho phần thực sự giữ; pha 30 g nước còn lại với mắm/đường/chanh/ớt; ăn kèm chả, dưa, hành phi.',NULL,40,1),(8,'Bún riêu','BREAKFAST',1.00,'Làm nóng nước dùng với riêu; xào cà chua/hành bằng dầu điều và đưa hết vào nồi; thêm đậu hũ, mắm; chan lên bún và rau.',NULL,30,1),(9,'Xôi gà','BREAKFAST',1.00,'Ngâm nấm với phần nước giữ lại; rim nấm/gà bằng nước tương/đường; làm mỡ hành bằng 3 g dầu; xếp trên xôi, thêm hành phi và dưa.',NULL,25,1),(10,'Bánh canh cua','BREAKFAST',1.00,'Hâm nước dùng; xào nhẹ hành bằng dầu điều; pha bột năng với 30 g nước, làm sánh; cho sợi/cua, nêm và thêm rau.',NULL,30,1),(11,'Cơm tấm sườn','LUNCH',1.00,'Hoàn thiện sườn chín với tỏi/nước tương/mật ong và một phần mắm/đường; dùng 3 g dầu làm mỡ hành, 3 g hoàn thiện sườn; pha đồ chua và nước chấm bằng phần còn lại; xếp suất.',NULL,30,1),(12,'Cơm gà xối mỡ','LUNCH',1.00,'Hoàn thiện gà đã hấp bằng xối dầu; cân phần dầu thực sự giữ; trộn nghệ vào cơm nóng; pha nước tương/đường/chanh/nước với tỏi; ăn cùng rau.',NULL,30,1),(13,'Cơm thịt kho trứng','LUNCH',1.00,'Đun thịt/trứng chín với nước dừa, nước, hành/tỏi, mắm/đường; giữ toàn bộ phần nước sốt phân cho suất; ăn cùng cơm và dưa.',NULL,35,1),(14,'Cơm cá kho tộ','LUNCH',1.00,'Pha sốt từ mắm/đường/hành/tỏi/nước/dầu; hoàn thiện cá chín trong tộ, chia toàn bộ sốt vào suất; thêm hành/tiêu, ăn với cơm và dưa.',NULL,30,1),(15,'Bún chả Hà Nội','LUNCH',1.00,'Dùng phần thịt/chả nướng chín đã cân; pha mắm/đường/giấm/chanh/nước với tỏi và đồ chua; ăn cùng bún và rau; hành/tiêu phân vào lớp gia vị giữ trên thịt.',NULL,30,1),(16,'Bún thịt nướng','LUNCH',1.00,'Hoàn thiện thịt nướng với sả/tỏi/nước tương/mật ong giữ lại; làm mỡ hành; pha nước chấm và cà rốt; xếp bún, rau, thịt, đậu phộng.',NULL,30,1),(17,'Cơm bò lúc lắc','LUNCH',1.00,'Xào rau và tỏi với dầu; cho bò đã chín cùng nước tương/mắm/đường, đảo nhanh, giữ nước thịt/sốt trong suất; ăn cùng cơm và rau.',NULL,25,1),(18,'Cơm gà luộc','LUNCH',1.00,'Trộn cơm nóng với nghệ/dầu đã kê; xé gà luộc; pha mắm gừng/tỏi/đường/chanh/nước; ăn cùng rau.',NULL,25,1),(19,'Cơm sườn ram','LUNCH',1.00,'Làm sốt hành/tỏi/mắm/nước tương/đường với nước; ram sườn chín bằng phần dầu giữ lại; ăn toàn bộ sốt phân cho suất cùng cơm/rau.',NULL,30,1),(20,'Cơm cá chiên','LUNCH',1.00,'Áp chảo cá nền đã chín với phần dầu giữ lại; pha nước mắm/tỏi/đường/chanh/nước; ăn cùng cơm và rau.',NULL,25,1),(21,'Cơm cá hấp','DINNER',1.00,'Hâm/hấp cá chín với gừng, hành và sốt đã kê; giữ nước cá trong suất; dùng dầu cho lớp hành; ăn cùng cơm/dưa.',NULL,25,1),(22,'Cơm thịt rang','DINNER',1.00,'Rang nhanh ba chỉ chín cùng hành/tỏi, mắm/đường/nước; chia toàn bộ phần mỡ/sốt giữ lại vào suất, thêm hành/tiêu.',NULL,25,1),(23,'Cơm canh chua cá','DINNER',1.00,'Nấu thơm/cà/đậu bắp/dọc mùng trong nước đã kê; cho me, cá chín và gia vị; thêm giá/rau thơm; phi tỏi bằng phần dầu riêng và dùng hết trong suất.',NULL,30,1),(24,'Cơm gà kho gừng','DINNER',1.00,'Phi hành/tỏi/gừng bằng dầu; kho nhanh gà chín với mắm/đường/nước; dùng sốt phân cho suất, ăn cùng cơm/dưa.',NULL,30,1),(25,'Cơm đậu hũ sốt cà','DINNER',1.00,'Xào cà/tỏi/hành với dầu, thêm nước/nước tương/đường/muối; cho đậu hũ trắng, đun nhẹ; ăn với cơm và xà lách.',NULL,25,1),(26,'Cơm tôm rim','DINNER',1.00,'Phi hành/tỏi, cho tôm chín với mắm/đường/nước, rim ngắn và dùng hết sốt phân cho suất; ăn cùng cơm/rau.',NULL,25,1),(27,'Cơm thịt luộc','DINNER',1.00,'Thái thịt luộc chín; pha nước chấm từ mắm/tỏi/ớt/đường/chanh/nước; ăn cùng cơm và rau.',NULL,20,1),(28,'Cơm canh bí đỏ','DINNER',1.00,'Phi hành bằng dầu kê riêng; nấu bí đỏ với nước, cho thịt băm chín và gia vị; thêm hành/tiêu; dùng toàn bộ canh với cơm.',NULL,25,1),(29,'Cơm cá kho','DINNER',1.00,'Làm sốt gừng/hành/tỏi/mắm/đường với dầu/nước; kho nhanh cá chín và chia sốt vào suất; ăn cùng cơm/dưa.',NULL,30,1),(30,'Cơm trứng chiên','DINNER',1.00,'Đánh trứng sống với hành và gia vị; chiên với phần dầu giữ lại; ăn cùng cơm/dưa/cà.',NULL,20,1);
/*!40000 ALTER TABLE `recipes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `registrationotpipquota`
--

DROP TABLE IF EXISTS `registrationotpipquota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registrationotpipquota` (
  `ip_hash` char(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `window_start` datetime NOT NULL,
  `sent_in_window` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`ip_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `registrationotpipquota`
--

LOCK TABLES `registrationotpipquota` WRITE;
/*!40000 ALTER TABLE `registrationotpipquota` DISABLE KEYS */;
INSERT INTO `registrationotpipquota` VALUES ('4c9a1d04b3a8c6acfa519da6552efe6e5f85da95a79fd6e84692612d042583f0','2026-10-16 23:25:44',2),('8cc217a763c61eba7df62a81b76a02ed14aba83df790d3909e9c276adb8684b2','2026-10-16 21:25:32',1);
/*!40000 ALTER TABLE `registrationotpipquota` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `registrationotps`
--

DROP TABLE IF EXISTS `registrationotps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registrationotps` (
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `otp_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expires_at` datetime NOT NULL,
  `last_sent_at` datetime NOT NULL,
  `attempts` int unsigned NOT NULL DEFAULT '0',
  `window_start` datetime NOT NULL,
  `sent_in_window` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `registrationotps`
--

LOCK TABLES `registrationotps` WRITE;
/*!40000 ALTER TABLE `registrationotps` DISABLE KEYS */;
INSERT INTO `registrationotps` VALUES ('test@example.com','Test','$2a$12$7HLvIsHVLPT7whQctF87/eKQAAiTZn9tv8YnrY6a3Uxsqh5OPkZm.','$2a$12$.9Vl2Eqw3V/FGUftvD.PveTxHC1doAVaemA2VcAlwT6OCP1QO0n.2','2026-10-16 21:30:32','2026-10-16 21:25:32',0,'2026-10-16 21:25:32',1);
/*!40000 ALTER TABLE `registrationotps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subscriptionplans`
--

DROP TABLE IF EXISTS `subscriptionplans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subscriptionplans` (
  `plan_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `plan_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price_vnd` bigint unsigned NOT NULL,
  `duration_days` int unsigned NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`plan_id`),
  CONSTRAINT `ck_subplan_duration` CHECK ((`duration_days` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subscriptionplans`
--

LOCK TABLES `subscriptionplans` WRITE;
/*!40000 ALTER TABLE `subscriptionplans` DISABLE KEYS */;
INSERT INTO `subscriptionplans` VALUES (1,'Premium 30 ngày',49000,30,'Truy cập quyền lợi Premium trong 30 ngày',1,'2026-10-17 21:07:38'),(2,'Premium dài hạn',399000,365,'Truy cập quyền lợi Premium trong 365 ngày',1,'2026-10-17 21:07:39');
/*!40000 ALTER TABLE `subscriptionplans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userprofiles`
--

DROP TABLE IF EXISTS `userprofiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userprofiles` (
  `profile_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `gender` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `age` int unsigned DEFAULT NULL,
  `height_cm` decimal(6,2) DEFAULT NULL,
  `weight_kg` decimal(6,2) DEFAULT NULL,
  `activity_level` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `goal` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bmr` decimal(9,2) DEFAULT NULL,
  `tdee` decimal(9,2) DEFAULT NULL,
  `target_kcal` decimal(9,2) DEFAULT NULL,
  `target_water_ml` int unsigned DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`profile_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_profile_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_profile_height` CHECK (((`height_cm` is null) or (`height_cm` > 0))),
  CONSTRAINT `ck_profile_weight` CHECK (((`weight_kg` is null) or (`weight_kg` > 0)))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userprofiles`
--

LOCK TABLES `userprofiles` WRITE;
/*!40000 ALTER TABLE `userprofiles` DISABLE KEYS */;
INSERT INTO `userprofiles` VALUES (1,3,'male',21,175.00,68.00,'very_high','gain',1673.75,3180.13,3480.13,2400,'2026-10-18 21:53:10');
/*!40000 ALTER TABLE `userprofiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('USER','ADMIN') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'USER',
  `subscription_status` enum('FREE','PREMIUM') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'FREE',
  `premium_expires_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `auth_version` bigint NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'test@nutrifit.local','$2a$12$9ggX1R4lQ7nKuVeNL092z.5BdTL3EN8F2NDRvEWomzaBlj.FlwZ1q','NutriFit Test User','USER','FREE',NULL,'2026-10-16 14:53:58',0),(2,'vungocanhkhoa11a7@gmail.com','$2a$12$RQbA7fA6oeQG1.2gVrgcsuNNYnYom1n9EjkEQBruQ2xJBC8LiKyVq','Khoa Cu','USER','FREE',NULL,'2026-10-16 16:00:36',2),(3,'phuquy020105@gmail.com','$2a$12$5OhrPDrpGojB1vM/3lxgueYht8hJadc7HYWNidej.CBfCIxzP0.e.','Phú Quý','ADMIN','FREE',NULL,'2026-10-16 23:28:52',1);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waterintakelog`
--

DROP TABLE IF EXISTS `waterintakelog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `waterintakelog` (
  `water_log_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `logged_date` date NOT NULL,
  `amount_ml` int unsigned NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`water_log_id`),
  KEY `idx_water_user_date` (`user_id`,`logged_date`),
  CONSTRAINT `fk_water_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_water_amount` CHECK ((`amount_ml` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waterintakelog`
--

LOCK TABLES `waterintakelog` WRITE;
/*!40000 ALTER TABLE `waterintakelog` DISABLE KEYS */;
/*!40000 ALTER TABLE `waterintakelog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workoutcategories`
--

DROP TABLE IF EXISTS `workoutcategories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutcategories` (
  `category_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `category_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `icon_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workoutcategories`
--

LOCK TABLES `workoutcategories` WRITE;
/*!40000 ALTER TABLE `workoutcategories` DISABLE KEYS */;
INSERT INTO `workoutcategories` VALUES (1,'Khởi động','warmup'),(2,'Calisthenic','calisthenic'),(3,'Giãn cơ','stretching');
/*!40000 ALTER TABLE `workoutcategories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workoutgoals`
--

DROP TABLE IF EXISTS `workoutgoals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutgoals` (
  `goal_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `weekly_sessions_target` int unsigned NOT NULL DEFAULT '0',
  `weekly_duration_target` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`goal_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_workoutgoal_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workoutgoals`
--

LOCK TABLES `workoutgoals` WRITE;
/*!40000 ALTER TABLE `workoutgoals` DISABLE KEYS */;
/*!40000 ALTER TABLE `workoutgoals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workoutlogs`
--

DROP TABLE IF EXISTS `workoutlogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutlogs` (
  `log_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `workout_id` bigint unsigned NOT NULL,
  `plan_detail_id` bigint unsigned DEFAULT NULL,
  `logged_date` date NOT NULL,
  `duration_minutes` int unsigned NOT NULL,
  `met_value` decimal(6,2) NOT NULL,
  `estimated_calories` decimal(12,3) NOT NULL,
  PRIMARY KEY (`log_id`),
  KEY `fk_workoutlog_workout` (`workout_id`),
  KEY `fk_workoutlog_detail` (`plan_detail_id`),
  KEY `idx_workoutlog_user_date` (`user_id`,`logged_date`),
  CONSTRAINT `fk_workoutlog_detail` FOREIGN KEY (`plan_detail_id`) REFERENCES `workoutplandetails` (`detail_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_workoutlog_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_workoutlog_workout` FOREIGN KEY (`workout_id`) REFERENCES `workouts` (`workout_id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_workoutlog_values` CHECK (((`duration_minutes` > 0) and (`met_value` > 0) and (`estimated_calories` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workoutlogs`
--

LOCK TABLES `workoutlogs` WRITE;
/*!40000 ALTER TABLE `workoutlogs` DISABLE KEYS */;
/*!40000 ALTER TABLE `workoutlogs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workoutplandays`
--

DROP TABLE IF EXISTS `workoutplandays`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutplandays` (
  `plan_day_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `plan_id` bigint unsigned NOT NULL,
  `day_index` tinyint unsigned NOT NULL,
  `day_name` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `focus_area` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rest_day` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`plan_day_id`),
  UNIQUE KEY `uq_plan_day` (`plan_id`,`day_index`),
  CONSTRAINT `fk_planday_plan` FOREIGN KEY (`plan_id`) REFERENCES `workoutplans` (`plan_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_plan_day_index` CHECK ((`day_index` between 1 and 7))
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workoutplandays`
--

LOCK TABLES `workoutplandays` WRITE;
/*!40000 ALTER TABLE `workoutplandays` DISABLE KEYS */;
INSERT INTO `workoutplandays` VALUES (1,1,1,'Ngày 1','Vai, Mông',0),(2,1,2,'Ngày 2','Lưng, Chân',0),(3,1,3,'Ngày 3','Nghỉ ngơi',1),(4,1,4,'Ngày 4','Bụng, Ngực',0),(5,1,5,'Ngày 5','Nghỉ ngơi',1),(6,1,6,'Ngày 6','Tay',0),(7,1,7,'Ngày 7','Nghỉ ngơi',1),(8,2,1,'Ngày 1','Vai, Mông',0),(9,2,2,'Ngày 2','Lưng, Chân',0),(10,2,3,'Ngày 3','Nghỉ ngơi',1),(11,2,4,'Ngày 4','Bụng, Ngực',0),(12,2,5,'Ngày 5','Nghỉ ngơi',1),(13,2,6,'Ngày 6','Tay',0),(14,2,7,'Ngày 7','Nghỉ ngơi',1),(15,3,1,'Ngày 1','Vai, Mông',0),(16,3,2,'Ngày 2','Lưng, Chân',0),(17,3,3,'Ngày 3','Nghỉ ngơi',1),(18,3,4,'Ngày 4','Bụng, Ngực',0),(19,3,5,'Ngày 5','Nghỉ ngơi',1),(20,3,6,'Ngày 6','Tay',0),(21,3,7,'Ngày 7','Nghỉ ngơi',1),(22,4,1,'Ngày 1','Vai, Mông',0),(23,4,2,'Ngày 2','Lưng, Chân',0),(24,4,3,'Ngày 3','Nghỉ ngơi',1),(25,4,4,'Ngày 4','Bụng, Ngực',0),(26,4,5,'Ngày 5','Nghỉ ngơi',1),(27,4,6,'Ngày 6','Tay',0),(28,4,7,'Ngày 7','Nghỉ ngơi',1),(29,5,1,'Ngày 1','Vai, Mông',0),(30,5,2,'Ngày 2','Lưng, Chân',0),(31,5,3,'Ngày 3','Nghỉ ngơi',1),(32,5,4,'Ngày 4','Bụng, Ngực',0),(33,5,5,'Ngày 5','Nghỉ ngơi',1),(34,5,6,'Ngày 6','Tay',0),(35,5,7,'Ngày 7','Nghỉ ngơi',1),(36,6,1,'Ngày 1','Vai, Mông',0),(37,6,2,'Ngày 2','Lưng, Chân',0),(38,6,3,'Ngày 3','Nghỉ ngơi',1),(39,6,4,'Ngày 4','Bụng, Ngực',0),(40,6,5,'Ngày 5','Nghỉ ngơi',1),(41,6,6,'Ngày 6','Tay',0),(42,6,7,'Ngày 7','Nghỉ ngơi',1),(43,7,1,'Ngày 1','Vai, Mông',0),(44,7,2,'Ngày 2','Lưng, Chân',0),(45,7,3,'Ngày 3','Nghỉ ngơi',1),(46,7,4,'Ngày 4','Bụng, Ngực',0),(47,7,5,'Ngày 5','Nghỉ ngơi',1),(48,7,6,'Ngày 6','Tay',0),(49,7,7,'Ngày 7','Nghỉ ngơi',1),(50,8,1,'Ngày 1','Vai, Mông',0),(51,8,2,'Ngày 2','Lưng, Chân',0),(52,8,3,'Ngày 3','Nghỉ ngơi',1),(53,8,4,'Ngày 4','Bụng, Ngực',0),(54,8,5,'Ngày 5','Nghỉ ngơi',1),(55,8,6,'Ngày 6','Tay',0),(56,8,7,'Ngày 7','Nghỉ ngơi',1),(57,9,1,'Ngày 1','Vai, Mông',0),(58,9,2,'Ngày 2','Lưng, Chân',0),(59,9,3,'Ngày 3','Nghỉ ngơi',1),(60,9,4,'Ngày 4','Bụng, Ngực',0),(61,9,5,'Ngày 5','Nghỉ ngơi',1),(62,9,6,'Ngày 6','Tay',0),(63,9,7,'Ngày 7','Nghỉ ngơi',1),(64,10,1,'Ngày 1','Vai, Mông',0),(65,10,2,'Ngày 2','Lưng, Chân',0),(66,10,3,'Ngày 3','Nghỉ ngơi',1),(67,10,4,'Ngày 4','Bụng, Ngực',0),(68,10,5,'Ngày 5','Nghỉ ngơi',1),(69,10,6,'Ngày 6','Tay',0),(70,10,7,'Ngày 7','Nghỉ ngơi',1),(71,11,1,'Ngày 1','Vai, Mông',0),(72,11,2,'Ngày 2','Lưng, Chân',0),(73,11,3,'Ngày 3','Nghỉ ngơi',1),(74,11,4,'Ngày 4','Bụng, Ngực',0),(75,11,5,'Ngày 5','Nghỉ ngơi',1),(76,11,6,'Ngày 6','Tay',0),(77,11,7,'Ngày 7','Nghỉ ngơi',1),(78,12,1,'Ngày 1','Vai, Mông',0),(79,12,2,'Ngày 2','Lưng, Chân',0),(80,12,3,'Ngày 3','Nghỉ ngơi',1),(81,12,4,'Ngày 4','Bụng, Ngực',0),(82,12,5,'Ngày 5','Nghỉ ngơi',1),(83,12,6,'Ngày 6','Tay',0),(84,12,7,'Ngày 7','Nghỉ ngơi',1);
/*!40000 ALTER TABLE `workoutplandays` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workoutplandetails`
--

DROP TABLE IF EXISTS `workoutplandetails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutplandetails` (
  `detail_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `plan_day_id` bigint unsigned NOT NULL,
  `workout_id` bigint unsigned NOT NULL,
  `duration_minutes` int unsigned NOT NULL,
  `order_index` int unsigned NOT NULL,
  PRIMARY KEY (`detail_id`),
  UNIQUE KEY `uq_planday_order` (`plan_day_id`,`order_index`),
  KEY `fk_plandetail_workout` (`workout_id`),
  CONSTRAINT `fk_plandetail_day` FOREIGN KEY (`plan_day_id`) REFERENCES `workoutplandays` (`plan_day_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_plandetail_workout` FOREIGN KEY (`workout_id`) REFERENCES `workouts` (`workout_id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_plandetail_duration` CHECK ((`duration_minutes` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=482 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workoutplandetails`
--

LOCK TABLES `workoutplandetails` WRITE;
/*!40000 ALTER TABLE `workoutplandetails` DISABLE KEYS */;
INSERT INTO `workoutplandetails` VALUES (1,1,3,2,1),(2,1,8,2,2),(3,1,1,2,3),(4,1,17,6,4),(5,1,30,6,5),(6,1,16,6,6),(7,1,31,6,7),(8,1,15,6,8),(9,1,43,3,9),(10,1,40,3,10),(11,2,5,2,1),(12,2,2,2,2),(13,2,1,2,3),(14,2,13,6,4),(15,2,28,6,5),(16,2,14,6,6),(17,2,26,6,7),(18,2,12,6,8),(19,2,41,3,9),(20,2,38,3,10),(21,4,6,2,1),(22,4,4,2,2),(23,4,1,2,3),(24,4,22,6,4),(25,4,10,6,5),(26,4,24,6,6),(27,4,9,6,7),(28,4,23,6,8),(29,4,45,3,9),(30,4,42,3,10),(31,6,7,2,1),(32,6,1,2,2),(33,6,5,2,3),(34,6,19,6,4),(35,6,18,6,5),(36,6,20,6,6),(37,6,32,6,7),(38,6,17,6,8),(39,6,44,3,9),(40,6,47,3,10),(41,8,3,2,1),(42,8,8,2,2),(43,8,1,2,3),(44,8,17,6,4),(45,8,30,6,5),(46,8,16,6,6),(47,8,31,6,7),(48,8,15,6,8),(49,8,43,3,9),(50,8,40,3,10),(51,9,5,2,1),(52,9,2,2,2),(53,9,1,2,3),(54,9,13,6,4),(55,9,28,6,5),(56,9,14,6,6),(57,9,26,6,7),(58,9,12,6,8),(59,9,41,3,9),(60,9,38,3,10),(61,11,6,2,1),(62,11,4,2,2),(63,11,1,2,3),(64,11,22,6,4),(65,11,10,6,5),(66,11,24,6,6),(67,11,9,6,7),(68,11,23,6,8),(69,11,45,3,9),(70,11,42,3,10),(71,13,7,2,1),(72,13,1,2,2),(73,13,5,2,3),(74,13,19,6,4),(75,13,18,6,5),(76,13,20,6,6),(77,13,32,6,7),(78,13,17,6,8),(79,13,44,3,9),(80,13,47,3,10),(81,15,3,2,1),(82,15,8,2,2),(83,15,1,2,3),(84,15,17,6,4),(85,15,30,6,5),(86,15,16,6,6),(87,15,31,6,7),(88,15,15,6,8),(89,15,43,3,9),(90,15,40,3,10),(91,16,5,2,1),(92,16,2,2,2),(93,16,1,2,3),(94,16,13,6,4),(95,16,28,6,5),(96,16,14,6,6),(97,16,26,6,7),(98,16,12,6,8),(99,16,41,3,9),(100,16,38,3,10),(101,18,6,2,1),(102,18,4,2,2),(103,18,1,2,3),(104,18,22,6,4),(105,18,10,6,5),(106,18,24,6,6),(107,18,9,6,7),(108,18,23,6,8),(109,18,45,3,9),(110,18,42,3,10),(111,20,7,2,1),(112,20,1,2,2),(113,20,5,2,3),(114,20,19,6,4),(115,20,18,6,5),(116,20,20,6,6),(117,20,32,6,7),(118,20,17,6,8),(119,20,44,3,9),(120,20,47,3,10),(121,22,3,2,1),(122,22,8,2,2),(123,22,1,2,3),(124,22,17,6,4),(125,22,30,6,5),(126,22,16,6,6),(127,22,31,6,7),(128,22,15,6,8),(129,22,43,3,9),(130,22,40,3,10),(131,23,5,2,1),(132,23,2,2,2),(133,23,1,2,3),(134,23,13,6,4),(135,23,28,6,5),(136,23,14,6,6),(137,23,26,6,7),(138,23,12,6,8),(139,23,41,3,9),(140,23,38,3,10),(141,25,6,2,1),(142,25,4,2,2),(143,25,1,2,3),(144,25,22,6,4),(145,25,10,6,5),(146,25,24,6,6),(147,25,9,6,7),(148,25,23,6,8),(149,25,45,3,9),(150,25,42,3,10),(151,27,7,2,1),(152,27,1,2,2),(153,27,5,2,3),(154,27,19,6,4),(155,27,18,6,5),(156,27,20,6,6),(157,27,32,6,7),(158,27,17,6,8),(159,27,44,3,9),(160,27,47,3,10),(161,29,3,2,1),(162,29,8,2,2),(163,29,1,2,3),(164,29,17,6,4),(165,29,30,6,5),(166,29,16,6,6),(167,29,31,6,7),(168,29,15,6,8),(169,29,43,3,9),(170,29,40,3,10),(171,30,5,2,1),(172,30,2,2,2),(173,30,1,2,3),(174,30,13,6,4),(175,30,28,6,5),(176,30,14,6,6),(177,30,26,6,7),(178,30,12,6,8),(179,30,41,3,9),(180,30,38,3,10),(181,32,6,2,1),(182,32,4,2,2),(183,32,1,2,3),(184,32,22,6,4),(185,32,10,6,5),(186,32,24,6,6),(187,32,9,6,7),(188,32,23,6,8),(189,32,45,3,9),(190,32,42,3,10),(191,34,7,2,1),(192,34,1,2,2),(193,34,5,2,3),(194,34,19,6,4),(195,34,18,6,5),(196,34,20,6,6),(197,34,32,6,7),(198,34,17,6,8),(199,34,44,3,9),(200,34,47,3,10),(201,36,3,2,1),(202,36,8,2,2),(203,36,1,2,3),(204,36,17,6,4),(205,36,30,6,5),(206,36,16,6,6),(207,36,31,6,7),(208,36,15,6,8),(209,36,43,3,9),(210,36,40,3,10),(211,37,5,2,1),(212,37,2,2,2),(213,37,1,2,3),(214,37,13,6,4),(215,37,28,6,5),(216,37,14,6,6),(217,37,26,6,7),(218,37,12,6,8),(219,37,41,3,9),(220,37,38,3,10),(221,39,6,2,1),(222,39,4,2,2),(223,39,1,2,3),(224,39,22,6,4),(225,39,10,6,5),(226,39,24,6,6),(227,39,9,6,7),(228,39,23,6,8),(229,39,45,3,9),(230,39,42,3,10),(231,41,7,2,1),(232,41,1,2,2),(233,41,5,2,3),(234,41,19,6,4),(235,41,18,6,5),(236,41,20,6,6),(237,41,32,6,7),(238,41,17,6,8),(239,41,44,3,9),(240,41,47,3,10),(241,43,3,2,1),(242,43,8,2,2),(243,43,1,2,3),(244,43,17,6,4),(245,43,30,6,5),(246,43,16,6,6),(247,43,31,6,7),(248,43,15,6,8),(249,43,43,3,9),(250,43,40,3,10),(251,44,5,2,1),(252,44,2,2,2),(253,44,1,2,3),(254,44,13,6,4),(255,44,28,6,5),(256,44,14,6,6),(257,44,26,6,7),(258,44,12,6,8),(259,44,41,3,9),(260,44,38,3,10),(261,46,6,2,1),(262,46,4,2,2),(263,46,1,2,3),(264,46,22,6,4),(265,46,10,6,5),(266,46,24,6,6),(267,46,9,6,7),(268,46,23,6,8),(269,46,45,3,9),(270,46,42,3,10),(271,48,7,2,1),(272,48,1,2,2),(273,48,5,2,3),(274,48,19,6,4),(275,48,18,6,5),(276,48,20,6,6),(277,48,32,6,7),(278,48,17,6,8),(279,48,44,3,9),(280,48,47,3,10),(281,50,3,2,1),(282,50,8,2,2),(283,50,1,2,3),(284,50,17,6,4),(285,50,30,6,5),(286,50,16,6,6),(287,50,31,6,7),(288,50,15,6,8),(289,50,43,3,9),(290,50,40,3,10),(291,51,5,2,1),(292,51,2,2,2),(293,51,1,2,3),(294,51,13,6,4),(295,51,28,6,5),(296,51,14,6,6),(297,51,26,6,7),(298,51,12,6,8),(299,51,41,3,9),(300,51,38,3,10),(301,53,6,2,1),(302,53,4,2,2),(303,53,1,2,3),(304,53,22,6,4),(305,53,10,6,5),(306,53,24,6,6),(307,53,9,6,7),(308,53,23,6,8),(309,53,45,3,9),(310,53,42,3,10),(311,55,7,2,1),(312,55,1,2,2),(313,55,5,2,3),(314,55,19,6,4),(315,55,18,6,5),(316,55,20,6,6),(317,55,32,6,7),(318,55,17,6,8),(319,55,44,3,9),(320,55,47,3,10),(321,57,3,2,1),(322,57,8,2,2),(323,57,1,2,3),(324,57,17,6,4),(325,57,30,6,5),(326,57,16,6,6),(327,57,31,6,7),(328,57,15,6,8),(329,57,43,3,9),(330,57,40,3,10),(331,58,5,2,1),(332,58,2,2,2),(333,58,1,2,3),(334,58,13,6,4),(335,58,28,6,5),(336,58,14,6,6),(337,58,26,6,7),(338,58,12,6,8),(339,58,41,3,9),(340,58,38,3,10),(341,60,6,2,1),(342,60,4,2,2),(343,60,1,2,3),(344,60,22,6,4),(345,60,10,6,5),(346,60,24,6,6),(347,60,9,6,7),(348,60,23,6,8),(349,60,45,3,9),(350,60,42,3,10),(351,62,7,2,1),(352,62,1,2,2),(353,62,5,2,3),(354,62,19,6,4),(355,62,18,6,5),(356,62,20,6,6),(357,62,32,6,7),(358,62,17,6,8),(359,62,44,3,9),(360,62,47,3,10),(361,64,3,2,1),(362,64,8,2,2),(363,64,1,2,3),(364,64,17,6,4),(365,64,30,6,5),(366,64,16,6,6),(367,64,31,6,7),(368,64,15,6,8),(369,64,43,3,9),(370,64,40,3,10),(371,65,5,2,1),(372,65,2,2,2),(373,65,1,2,3),(374,65,13,6,4),(375,65,28,6,5),(376,65,14,6,6),(377,65,26,6,7),(378,65,12,6,8),(379,65,41,3,9),(380,65,38,3,10),(381,67,6,2,1),(382,67,4,2,2),(383,67,1,2,3),(384,67,22,6,4),(385,67,10,6,5),(386,67,24,6,6),(387,67,9,6,7),(388,67,23,6,8),(389,67,45,3,9),(390,67,42,3,10),(391,69,7,2,1),(392,69,1,2,2),(393,69,5,2,3),(394,69,19,6,4),(395,69,18,6,5),(396,69,20,6,6),(397,69,32,6,7),(398,69,17,6,8),(399,69,44,3,9),(400,69,47,3,10),(401,65,17,30,11),(402,71,3,2,1),(403,71,8,2,2),(404,71,1,2,3),(405,71,17,6,4),(406,71,30,6,5),(407,71,16,6,6),(408,71,31,6,7),(409,71,15,6,8),(410,71,43,3,9),(411,71,40,3,10),(412,72,5,2,1),(413,72,2,2,2),(414,72,1,2,3),(415,72,13,6,4),(416,72,28,6,5),(417,72,14,6,6),(418,72,26,6,7),(419,72,12,6,8),(420,72,41,3,9),(421,72,38,3,10),(422,74,6,2,1),(423,74,4,2,2),(424,74,1,2,3),(425,74,22,6,4),(426,74,10,6,5),(427,74,24,6,6),(428,74,9,6,7),(429,74,23,6,8),(430,74,45,3,9),(431,74,42,3,10),(432,76,7,2,1),(433,76,1,2,2),(434,76,5,2,3),(435,76,19,6,4),(436,76,18,6,5),(437,76,20,6,6),(438,76,32,6,7),(439,76,17,6,8),(440,76,44,3,9),(441,76,47,3,10),(442,78,3,2,1),(443,78,8,2,2),(444,78,1,2,3),(445,78,17,6,4),(446,78,30,6,5),(447,78,16,6,6),(448,78,31,6,7),(449,78,15,6,8),(450,78,43,3,9),(451,78,40,3,10),(452,79,5,2,1),(453,79,2,2,2),(454,79,1,2,3),(455,79,13,6,4),(456,79,28,6,5),(457,79,14,6,6),(458,79,26,6,7),(459,79,12,6,8),(460,79,41,3,9),(461,79,38,3,10),(462,81,6,2,1),(463,81,4,2,2),(464,81,1,2,3),(465,81,22,6,4),(466,81,10,6,5),(467,81,24,6,6),(468,81,9,6,7),(469,81,23,6,8),(470,81,45,3,9),(471,81,42,3,10),(472,83,7,2,1),(473,83,1,2,2),(474,83,5,2,3),(475,83,19,6,4),(476,83,18,6,5),(477,83,20,6,6),(478,83,32,6,7),(479,83,17,6,8),(480,83,44,3,9),(481,83,47,3,10);
/*!40000 ALTER TABLE `workoutplandetails` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workoutplans`
--

DROP TABLE IF EXISTS `workoutplans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workoutplans` (
  `plan_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `plan_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`plan_id`),
  KEY `idx_workoutplan_user` (`user_id`),
  CONSTRAINT `fk_workoutplan_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_workoutplan_dates` CHECK ((`end_date` >= `start_date`))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workoutplans`
--

LOCK TABLES `workoutplans` WRITE;
/*!40000 ALTER TABLE `workoutplans` DISABLE KEYS */;
INSERT INTO `workoutplans` VALUES (1,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(2,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(3,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(4,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(5,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(6,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(7,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(8,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(9,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(10,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(11,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',0),(12,3,'Lộ trình 7 ngày từ 2026-10-18','2026-10-18','2026-10-24',1);
/*!40000 ALTER TABLE `workoutplans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workouts`
--

DROP TABLE IF EXISTS `workouts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workouts` (
  `workout_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `category_id` bigint unsigned NOT NULL,
  `created_by` bigint unsigned DEFAULT NULL,
  `workout_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_custom` tinyint(1) NOT NULL DEFAULT '0',
  `access_level` enum('FREE','PREMIUM') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'FREE',
  `description` text COLLATE utf8mb4_unicode_ci,
  `instructions` text COLLATE utf8mb4_unicode_ci,
  `muscle_group` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `difficulty_level` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `equipment` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `target_goal` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `video_url` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `met_value` decimal(6,2) NOT NULL,
  `default_duration_minutes` int unsigned NOT NULL,
  PRIMARY KEY (`workout_id`),
  KEY `fk_workout_category` (`category_id`),
  KEY `fk_workout_creator` (`created_by`),
  CONSTRAINT `fk_workout_category` FOREIGN KEY (`category_id`) REFERENCES `workoutcategories` (`category_id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_workout_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_workout_duration` CHECK ((`default_duration_minutes` > 0)),
  CONSTRAINT `ck_workout_met` CHECK ((`met_value` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workouts`
--

LOCK TABLES `workouts` WRITE;
/*!40000 ALTER TABLE `workouts` DISABLE KEYS */;
INSERT INTO `workouts` VALUES (1,1,NULL,'Jumping jack',0,'FREE','Nhảy dang tay chân nhịp nhàng, nâng nhịp tim và làm nóng toàn thân.','Đứng thẳng, nhảy dang chân rộng hơn vai đồng thời giơ hai tay lên cao rồi nhảy về tư thế đầu. Giữ nhịp đều, tiếp đất nhẹ nhàng.','Toàn thân','Dễ','Không cần dụng cụ',NULL,NULL,4.00,2),(2,1,NULL,'High knees tại chỗ',0,'FREE','Chạy nâng cao gối tại chỗ để làm nóng chân và tim mạch.','Đứng thẳng, lần lượt nâng gối ngang hông với nhịp nhanh, đánh tay tự nhiên, tiếp đất bằng nửa bàn chân trước.','Chân','Dễ','Không cần dụng cụ',NULL,NULL,4.50,2),(3,1,NULL,'Xoay vai',0,'FREE','Xoay khớp vai để chuẩn bị cho các bài đẩy và kéo.','Đứng thẳng, đặt đầu ngón tay lên vai, xoay khuỷu tay vẽ vòng tròn lớn về trước 10 lần rồi về sau 10 lần.','Vai','Dễ','Không cần dụng cụ',NULL,NULL,2.50,2),(4,1,NULL,'Mở rộng ngực',0,'FREE','Đánh tay dang ngang giúp mở ngực và làm nóng cơ ngực.','Đứng thẳng, dang hai tay ngang vai rồi khép lại phía trước và mở rộng ra sau, lặp lại nhịp nhàng 15 lần.','Ngực','Dễ','Không cần dụng cụ',NULL,NULL,2.50,2),(5,1,NULL,'Cat-cow',0,'FREE','Chuyển động võng và cong lưng giúp làm mềm cột sống.','Quỳ chống bốn điểm, hít vào võng lưng ngẩng đầu, thở ra cong lưng cúi đầu. Lặp lại chậm 10 lần.','Lưng','Dễ','Không cần dụng cụ',NULL,NULL,2.30,2),(6,1,NULL,'Xoay thân',0,'FREE','Xoay thân trên để làm nóng cơ bụng và cột sống.','Đứng chân rộng bằng vai, hai tay co trước ngực, xoay thân sang hai bên luân phiên 20 lần, hông giữ cố định.','Bụng','Dễ','Không cần dụng cụ',NULL,NULL,2.80,2),(7,1,NULL,'Xoay cổ tay và khuỷu tay',0,'FREE','Làm nóng khớp tay trước các bài chống đẩy.','Đan hai bàn tay xoay cổ tay mỗi chiều 10 lần, sau đó xoay khuỷu tay nhẹ nhàng 10 lần.','Tay','Dễ','Không cần dụng cụ',NULL,NULL,2.00,2),(8,1,NULL,'Xoay hông và squat nhẹ',0,'FREE','Xoay hông kết hợp squat nhẹ làm nóng cơ mông và hông.','Đứng chân rộng bằng vai, xoay hông vẽ vòng tròn 10 lần mỗi chiều, sau đó squat nhẹ 10 lần với biên độ nhỏ.','Mông','Dễ','Không cần dụng cụ',NULL,NULL,3.00,2),(9,2,NULL,'Push-up quỳ',0,'FREE','Chống đẩy với đầu gối chạm sàn, phù hợp người mới bắt đầu.','Quỳ gối, hai tay chống rộng hơn vai, giữ thân thẳng từ đầu gối đến đầu, hạ ngực gần sàn rồi đẩy lên.','Ngực','Dễ','Không cần dụng cụ',NULL,NULL,3.80,6),(10,2,NULL,'Push-up cơ bản',0,'FREE','Bài chống đẩy tiêu chuẩn cho cơ ngực, vai và tay sau.','Chống hai tay rộng hơn vai, thân thẳng như tấm ván, hạ ngực gần sàn với khuỷu tay chếch khoảng 45 độ rồi đẩy lên.','Ngực','Trung bình','Không cần dụng cụ',NULL,NULL,4.50,6),(11,2,NULL,'Push-up tay rộng',0,'FREE','Chống đẩy tay rộng nhấn mạnh cơ ngực.','Đặt hai tay rộng gấp rưỡi vai, giữ thân thẳng, hạ ngực xuống sát sàn rồi đẩy lên.','Ngực','Trung bình','Không cần dụng cụ',NULL,NULL,4.50,6),(12,2,NULL,'Superman',0,'FREE','Nằm sấp nâng tay chân để tập cơ lưng dưới.','Nằm sấp, duỗi hai tay về trước, đồng thời nâng tay và chân lên khỏi sàn, giữ 2 giây rồi hạ xuống.','Lưng','Dễ','Không cần dụng cụ',NULL,NULL,3.00,6),(13,2,NULL,'Bird-dog',0,'FREE','Duỗi tay chân đối diện để tăng sức mạnh lưng và ổn định thân.','Quỳ chống bốn điểm, duỗi tay phải và chân trái thẳng ra, giữ 2 giây rồi đổi bên. Giữ lưng phẳng.','Lưng','Dễ','Không cần dụng cụ',NULL,NULL,3.00,6),(14,2,NULL,'Inverted row dưới bàn',0,'FREE','Kéo người lên dưới mặt bàn chắc chắn để tập cơ lưng xô.','Nằm dưới bàn chắc chắn, nắm mép bàn, giữ thân thẳng rồi kéo ngực lên sát bàn, hạ xuống có kiểm soát.','Lưng','Trung bình','Bàn chắc chắn',NULL,NULL,4.50,6),(15,2,NULL,'Shoulder tap plank',0,'FREE','Chống tay vỗ vai luân phiên để tập vai và ổn định thân.','Vào tư thế plank tay thẳng, lần lượt chạm tay vào vai đối diện mà hông không xoay.','Vai','Dễ','Không cần dụng cụ',NULL,NULL,4.00,6),(16,2,NULL,'Pike push-up',0,'FREE','Chống đẩy gập hông, nhấn mạnh cơ vai.','Vào tư thế chữ V ngược, gập khuỷu hạ đỉnh đầu về phía sàn rồi đẩy lên.','Vai','Trung bình','Không cần dụng cụ',NULL,NULL,5.00,6),(17,2,NULL,'Bear crawl',0,'FREE','Bò bằng bốn điểm với đầu gối nhấc khỏi sàn, tập vai và thân.','Từ tư thế bốn điểm nhấc đầu gối cách sàn một gang tay, bò tiến lùi bằng tay và chân đối diện.','Vai','Trung bình','Không cần dụng cụ',NULL,NULL,5.50,6),(18,2,NULL,'Dips ghế',0,'FREE','Hạ người trên ghế để tập cơ tay sau.','Ngồi mép ghế chắc, chống tay phía sau, trượt mông ra khỏi ghế, gập khuỷu hạ người rồi đẩy lên.','Tay','Trung bình','Ghế chắc chắn',NULL,NULL,4.50,6),(19,2,NULL,'Diamond push-up',0,'FREE','Chống đẩy tay hẹp tạo hình kim cương, tập mạnh tay sau.','Đặt hai tay sát nhau dưới ngực tạo hình kim cương, giữ khuỷu tay sát thân, hạ người rồi đẩy lên.','Tay','Khó','Không cần dụng cụ',NULL,NULL,5.00,6),(20,2,NULL,'Plank to push-up',0,'FREE','Chuyển từ plank khuỷu tay lên plank tay thẳng, tập tay và thân.','Từ plank khuỷu tay, lần lượt chống từng tay đẩy lên tư thế chống đẩy rồi hạ về, đổi tay dẫn đầu.','Tay','Trung bình','Không cần dụng cụ',NULL,NULL,5.00,6),(21,2,NULL,'Plank',0,'FREE','Giữ thân thẳng trên khuỷu tay, tập cơ bụng sâu.','Chống khuỷu tay dưới vai, thân thẳng từ đầu đến gót, siết bụng và mông, giữ 30 giây.','Bụng','Dễ','Không cần dụng cụ',NULL,NULL,3.00,6),(22,2,NULL,'Crunch',0,'FREE','Gập bụng ngắn để tập cơ bụng trên.','Nằm ngửa gập gối, hai tay sau đầu, nhấc vai khỏi sàn bằng lực bụng rồi hạ xuống, không kéo cổ.','Bụng','Dễ','Không cần dụng cụ',NULL,NULL,3.80,6),(23,2,NULL,'Nâng chân nằm',0,'FREE','Nâng hạ hai chân khi nằm để tập bụng dưới.','Nằm ngửa, tay dọc thân, nâng hai chân thẳng lên vuông góc rồi hạ chậm gần sàn mà không chạm.','Bụng','Trung bình','Không cần dụng cụ',NULL,NULL,4.00,6),(24,2,NULL,'Mountain climber',0,'FREE','Chạy leo núi tại chỗ ở tư thế plank, tập bụng và tim mạch.','Ở tư thế chống tay thẳng, lần lượt đưa gối về phía ngực với nhịp nhanh, hông thấp ổn định.','Bụng','Trung bình','Không cần dụng cụ',NULL,NULL,8.00,6),(25,2,NULL,'Squat',0,'FREE','Gập gối hạ người, bài cơ bản cho đùi và mông.','Đứng chân rộng bằng vai, đẩy hông ra sau và gập gối hạ người đến khi đùi song song sàn rồi đứng lên.','Chân','Dễ','Không cần dụng cụ',NULL,NULL,5.00,6),(26,2,NULL,'Lunge',0,'FREE','Bước chân chùng gối, tập đùi và mông từng bên.','Bước một chân ra trước, hạ thấp cho đến khi hai gối gập khoảng 90 độ rồi đẩy về, đổi chân.','Chân','Trung bình','Không cần dụng cụ',NULL,NULL,5.00,6),(27,2,NULL,'Wall sit',0,'FREE','Tựa lưng vào tường ở tư thế ngồi, tập sức bền đùi.','Tựa lưng vào tường, trượt xuống đến khi đùi song song sàn, giữ 30 giây.','Chân','Trung bình','Tường',NULL,NULL,3.50,6),(28,2,NULL,'Jump squat',0,'FREE','Squat bật nhảy để tăng sức mạnh bùng nổ của chân.','Squat xuống rồi bật mạnh lên khỏi sàn, tiếp đất nhẹ nhàng bằng nửa bàn chân và hạ thẳng vào squat tiếp theo.','Chân','Khó','Không cần dụng cụ',NULL,NULL,8.00,6),(29,2,NULL,'Glute bridge',0,'FREE','Nằm nâng hông để tập cơ mông.','Nằm ngửa gập gối, nâng hông lên cho thân thẳng từ vai đến gối, siết mông 2 giây rồi hạ xuống.','Mông','Dễ','Không cần dụng cụ',NULL,NULL,3.50,6),(30,2,NULL,'Donkey kick',0,'FREE','Đá chân ra sau ở tư thế bốn điểm để tập mông.','Quỳ chống bốn điểm, đá một chân gập gối lên trần, siết mông rồi hạ về, đổi chân.','Mông','Dễ','Không cần dụng cụ',NULL,NULL,3.50,6),(31,2,NULL,'Fire hydrant',0,'FREE','Nâng chân sang ngang như vòi cứu hỏa để tập mông ngoài.','Quỳ chống bốn điểm, nâng một gối sang ngang giữ gập 90 độ, hông không xoay, hạ xuống rồi đổi chân.','Mông','Dễ','Không cần dụng cụ',NULL,NULL,3.50,6),(32,2,NULL,'Burpee',0,'FREE','Bài tập toàn thân cường độ cao kết hợp squat, plank và nhảy.','Từ đứng hạ xuống chống tay, đưa chân ra sau thành plank, thu chân về rồi bật nhảy lên cao.','Toàn thân','Khó','Không cần dụng cụ',NULL,NULL,8.00,6),(33,2,NULL,'Pull-up',0,'PREMIUM','Kéo cằm qua xà đơn, bài tập lưng xô và tay trước nâng cao.','Treo người trên xà, kéo cơ thể lên đến khi cằm qua xà rồi hạ xuống có kiểm soát.','Lưng','Khó','Xà đơn',NULL,NULL,8.00,6),(34,2,NULL,'Pistol squat',0,'PREMIUM','Squat một chân, bài tập sức mạnh và thăng bằng nâng cao.','Đứng một chân, chân kia duỗi thẳng trước mặt, hạ người xuống sâu bằng chân trụ rồi đứng lên.','Chân','Khó','Không cần dụng cụ',NULL,NULL,8.00,6),(35,2,NULL,'Archer push-up',0,'PREMIUM','Chống đẩy lệch tải sang một tay, nâng cao.','Chống tay rộng, hạ người về một tay trong khi tay còn lại duỗi thẳng, đẩy lên rồi đổi bên.','Ngực','Khó','Không cần dụng cụ',NULL,NULL,8.00,6),(36,2,NULL,'Handstand push-up',0,'PREMIUM','Chống đẩy trồng cây chuối dựa tường, nâng cao cho vai.','Trồng cây chuối dựa tường, gập khuỷu hạ đầu xuống gần sàn rồi đẩy lên.','Vai','Khó','Tường',NULL,NULL,8.00,6),(37,2,NULL,'L-sit',0,'PREMIUM','Giữ thân chữ L trên hai tay, tập bụng và tay nâng cao.','Chống hai tay xuống sàn, nâng mông và hai chân thẳng song song sàn, giữ càng lâu càng tốt.','Bụng','Khó','Không cần dụng cụ',NULL,NULL,5.00,6),(38,3,NULL,'Giãn cơ đùi trước',0,'FREE','Kéo giãn cơ đùi trước sau các bài chân.','Đứng một chân, gập gối kéo gót về phía mông, giữ 20–30 giây mỗi bên.','Chân','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(39,3,NULL,'Giãn gân kheo',0,'FREE','Kéo giãn cơ đùi sau.','Ngồi duỗi một chân, nghiêng thân về phía mũi chân giữ lưng thẳng, giữ 20–30 giây mỗi bên.','Chân','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(40,3,NULL,'Giãn cơ mông (figure-four)',0,'FREE','Kéo giãn cơ mông và hông.','Nằm ngửa, gác mắt cá chân lên đùi đối diện, kéo đùi về phía ngực, giữ 20–30 giây mỗi bên.','Mông','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(41,3,NULL,'Tư thế em bé (Child pose)',0,'FREE','Kéo giãn lưng và vai.','Quỳ ngồi lên gót, duỗi hai tay thẳng về trước, hạ ngực xuống sàn, hít thở sâu 30 giây.','Lưng','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(42,3,NULL,'Giãn ngực ở khung cửa',0,'FREE','Kéo giãn cơ ngực.','Đặt cẳng tay lên khung cửa, bước một chân qua cửa để ngực mở ra, giữ 20–30 giây mỗi bên.','Ngực','Dễ','Khung cửa',NULL,NULL,2.30,3),(43,3,NULL,'Giãn vai chéo ngực',0,'FREE','Kéo giãn cơ vai sau.','Kéo một tay ngang qua ngực, dùng tay kia ôm giữ, giữ 20–30 giây mỗi bên.','Vai','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(44,3,NULL,'Giãn cơ tay sau',0,'FREE','Kéo giãn cơ tam đầu.','Đưa một tay ra sau đầu, tay kia kéo nhẹ khuỷu về phía sau, giữ 20–30 giây mỗi bên.','Tay','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(45,3,NULL,'Cobra',0,'FREE','Kéo giãn cơ bụng.','Nằm sấp, đặt tay cạnh ngực, chống tay nâng ngực lên, mở bụng và giữ 20–30 giây.','Bụng','Dễ','Không cần dụng cụ',NULL,NULL,2.30,3),(46,3,NULL,'Giãn cơ cổ',0,'FREE','Kéo giãn nhẹ cơ cổ và vai trên.','Nghiêng đầu sang một bên, dùng tay đặt nhẹ trên đầu, giữ 20 giây mỗi bên.','Cổ','Dễ','Không cần dụng cụ',NULL,NULL,2.00,3),(47,3,NULL,'Downward dog',0,'FREE','Kéo giãn toàn thân từ vai đến gót chân.','Chống tay và chân tạo chữ V ngược, đẩy hông lên cao và ép gót về sàn, giữ 30 giây.','Toàn thân','Dễ','Không cần dụng cụ',NULL,NULL,2.50,3);
/*!40000 ALTER TABLE `workouts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'NutriFitDB_Java'
--

--
-- Dumping routines for database 'NutriFitDB_Java'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-18 23:26:47
