-- NutriFit Vietnamese catalog v1. Part 1/3. NEVER execute against a live DB.
-- One fresh mysql batch session, without --force; see README.md / run_vietnamese_catalog.py.
-- Fxxx/Rxxx are local references only, never database IDs. No permanent DDL.
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET SESSION sql_mode = 'STRICT_ALL_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,NO_BACKSLASH_ESCAPES';
SET SESSION foreign_key_checks = 1;
SET SESSION unique_checks = 1;

CREATE TEMPORARY TABLE _nf_assert (
    check_name VARCHAR(100) PRIMARY KEY,
    ok TINYINT NOT NULL
) ENGINE=InnoDB;
-- Failed assertions insert NULL into NOT NULL under strict mode: batch must STOP.
INSERT INTO _nf_assert (check_name, ok)
SELECT 'database_name_must_end_in_test', IF((DATABASE() IS NOT NULL AND RIGHT(LOWER(DATABASE()), 5) = '_test'), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'mysql_8_0_16_or_newer_required', IF((
    VERSION() NOT LIKE '%MariaDB%' AND (
      CAST(SUBSTRING_INDEX(VERSION(), '.', 1) AS UNSIGNED) > 8
      OR (CAST(SUBSTRING_INDEX(VERSION(), '.', 1) AS UNSIGNED) = 8 AND (
        CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(VERSION(), '.', 2), '.', -1) AS UNSIGNED) > 0
        OR CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(VERSION(), '.', 3), '.', -1) AS UNSIGNED) >= 16
      ))
    )), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'three_target_tables_must_be_innodb', IF(((SELECT COUNT(*) FROM information_schema.tables
 WHERE table_schema = DATABASE() AND table_name IN ('foods','recipes','recipeingredients')
 AND engine = 'InnoDB') = 3), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'name_collations_must_match_schema', IF(((SELECT COUNT(*) FROM information_schema.columns
 WHERE table_schema = DATABASE() AND table_name IN ('foods','recipes')
 AND column_name = 'name' AND collation_name = 'utf8mb4_unicode_ci') = 2), 1, NULL);

-- Account must be able to see ALL triggers on the three tables; see README.
INSERT INTO _nf_assert (check_name, ok)
SELECT 'target_tables_must_have_no_triggers', IF(((SELECT COUNT(*) FROM information_schema.triggers
 WHERE trigger_schema = DATABASE() AND event_object_table IN ('foods','recipes','recipeingredients')) = 0), 1, NULL);

SET @nf_lock_name = CONCAT('seed:vn1:', LEFT(SHA2(DATABASE(), 256), 40));
SET @nf_lock_ok = GET_LOCK(@nf_lock_name, 10);
INSERT INTO _nf_assert (check_name, ok)
SELECT 'catalog_lock_required', IF((@nf_lock_ok = 1), 1, NULL);

CREATE TEMPORARY TABLE _nf_food_stage (
    ref CHAR(4) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    calories_per_100g DECIMAL(10,3) NOT NULL,
    protein_per_100g DECIMAL(10,3) NOT NULL,
    carbs_per_100g DECIMAL(10,3) NOT NULL,
    fat_per_100g DECIMAL(10,3) NOT NULL,
    fiber_per_100g DECIMAL(10,3) NOT NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO _nf_food_stage (ref, name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g) VALUES
-- BEGIN FOOD DATA
('F001', 'Cơm trắng gạo tẻ đã nấu, không dầu', 130, 2.7, 28, 0.3, 0.4),
('F002', 'Bánh phở tươi đã trụng, để ráo', 110, 2, 24, 0.3, 0.4),
('F003', 'Bún tươi đã trụng, để ráo', 110, 2, 24, 0.2, 0.5),
('F004', 'Hủ tiếu gạo đã trụng, để ráo', 110, 2, 24, 0.2, 0.4),
('F005', 'Bánh canh bột gạo đã luộc, để ráo', 105, 1.5, 24, 0.2, 0.3),
('F006', 'Bánh mì trắng ổ không nhân', 270, 9, 52, 3, 2.5),
('F007', 'Gạo tẻ trắng khô', 360, 7, 79, 0.8, 1),
('F008', 'Xôi nếp trắng đã hấp, không dầu', 170, 3.5, 37, 0.5, 0.8),
('F009', 'Bột gạo tẻ khô', 360, 6, 80, 1, 1),
('F010', 'Bột năng khô', 350, 0.2, 87, 0.1, 0),
('F011', 'Thịt bò thăn nạc luộc chín, không sốt', 210, 29, 0, 10, 0),
('F012', 'Thịt ức gà luộc chín, bỏ da', 165, 31, 0, 3.6, 0),
('F013', 'Thịt đùi gà hấp chín, có da, bỏ xương', 230, 25, 0, 14, 0),
('F014', 'Thịt bắp bò luộc chín', 210, 30, 0, 9, 0),
('F015', 'Thịt heo nạc luộc chín', 190, 29, 0, 8, 0),
('F016', 'Thịt heo nạc băm hấp chín, không dầu', 200, 28, 0, 9, 0),
('F017', 'Gan heo luộc chín', 170, 25, 4, 6, 0),
('F018', 'Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được', 500, 10, 0, 51, 0),
('F019', 'Thịt nạc vai heo nướng chín, không sốt', 260, 27, 0, 17, 0),
('F020', 'Thịt sườn heo hấp chín, bỏ xương, không sốt', 280, 25, 0, 20, 0),
('F021', 'Thịt bò thăn áp chảo chín, không dầu/sốt', 220, 29, 0, 11, 0),
('F022', 'Thịt đùi gà hấp chín, bỏ da và xương', 180, 26, 0, 8, 0),
('F023', 'Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt', 100, 21, 0, 2, 0),
('F024', 'Thịt cá rô phi hấp chín, bỏ xương, không dầu/sốt', 128, 26, 0, 2.5, 0),
('F025', 'Tôm thẻ luộc chín, bóc vỏ', 100, 24, 0.2, 0.3, 0),
('F026', 'Thịt/riêu cua đồng nấu chín, lọc sạch vỏ', 95, 18, 1, 2, 0),
('F027', 'Thịt cua biển hấp chín, gỡ vỏ', 100, 20, 0.5, 1.5, 0),
('F028', 'Trứng gà nguyên quả sống, bỏ vỏ', 143, 12.6, 0.7, 9.5, 0),
('F029', 'Trứng gà luộc chín, bỏ vỏ', 155, 12.6, 1.1, 10.6, 0),
('F030', 'Trứng cút luộc chín, bỏ vỏ', 158, 13, 0.5, 11, 0),
('F031', 'Đậu hũ trắng không chiên', 90, 9, 2, 5, 0.6),
('F032', 'Chả lụa thành phẩm', 170, 17, 7, 8, 0.2),
('F033', 'Đậu phộng rang không muối, bỏ vỏ lụa', 590, 25, 13, 50, 8.5),
('F034', 'Cà chua sống', 20, 0.6, 4, 0.2, 1.2),
('F035', 'Dưa leo sống, giữ vỏ ăn được', 15, 0.7, 2.8, 0.1, 0.5),
('F036', 'Xà lách sống', 15, 1.4, 1.5, 0.2, 1.3),
('F037', 'Giá đỗ đậu xanh sống', 30, 3, 4, 0.2, 1.8),
('F038', 'Hành tây sống', 41, 1.8, 8.2, 0.1, 1.7),
('F039', 'Hành lá sống', 32, 1.8, 4.7, 0.2, 2.6),
('F040', 'Ngò rí sống', 23, 2.1, 1, 0.5, 2.8),
('F041', 'Húng quế sống', 23, 3, 1, 0.6, 1.6),
('F042', 'Rau răm sống', 30, 3, 2.5, 0.5, 3),
('F043', 'Hẹ lá sống', 30, 3.3, 2, 0.7, 2.5),
('F044', 'Sả tươi băm, phần lõi ăn được', 99, 1.8, 20, 0.5, 2.5),
('F045', 'Gừng tươi sống, gọt vỏ', 29, 0.4, 5.1, 0.8, 3.5),
('F046', 'Tỏi ta sống, bóc vỏ', 121, 6, 23, 0.5, 2.1),
('F047', 'Hành tím sống, bóc vỏ', 72, 2.5, 14, 0.1, 3.2),
('F048', 'Ớt tươi sống', 40, 1.9, 7.3, 0.4, 1.5),
('F049', 'Cà rốt sống, sơ chế', 41, 0.9, 6.8, 0.2, 2.8),
('F050', 'Củ cải trắng sống, sơ chế', 18, 0.6, 2.5, 0.1, 1.6),
('F051', 'Đu đủ xanh sống, bỏ vỏ/hạt', 35, 0.6, 7, 0.1, 1.8),
('F052', 'Ớt chuông sống', 31, 1, 3.9, 0.3, 2.1),
('F053', 'Thơm chín tươi, bỏ vỏ/mắt/lõi cứng', 50, 0.5, 11.8, 0.1, 1.4),
('F054', 'Đậu bắp sống, bỏ cuống', 33, 1.9, 4.3, 0.2, 3.2),
('F055', 'Bạc hà/dọc mùng, phần thân đã tước vỏ', 14, 0.7, 1.8, 0.1, 1.5),
('F056', 'Bí đỏ sống, bỏ vỏ/hạt', 26, 1, 5, 0.1, 0.5),
('F057', 'Rau ngổ sống', 25, 2, 2, 0.4, 2.5),
('F058', 'Ngò gai sống', 25, 2, 2, 0.4, 2.5),
('F059', 'Nấm mèo khô', 293, 9, 52, 1, 25),
('F060', 'Nấm hương khô', 296, 9.5, 53, 1, 12),
('F061', 'Dầu đậu nành tinh luyện', 884, 0, 0, 100, 0),
('F062', 'Nước mắm nguyên chất', 40, 6, 4, 0, 0),
('F063', 'Nước tương lên men', 55, 8, 5, 0.5, 0.5),
('F064', 'Đường trắng tinh luyện', 400, 0, 100, 0, 0),
('F065', 'Muối ăn iod', 0, 0, 0, 0, 0),
('F066', 'Tiêu đen xay khô', 255, 10, 40, 3.3, 25),
('F067', 'Nước cốt chanh tươi, bỏ hạt', 25, 0.4, 6, 0.1, 0.3),
('F068', 'Giấm gạo', 18, 0, 0.5, 0, 0),
('F069', 'Thịt me chín dạng nhuyễn, bỏ hạt', 240, 3, 53, 0.6, 5),
('F070', 'Nước dừa tươi', 19, 0.7, 3.7, 0.2, 0),
('F071', 'Nước lọc dùng trong món', 0, 0, 0, 0, 0),
('F072', 'Nước dùng phở bò thành phẩm, không nêm', 20, 2, 0.5, 1, 0),
('F073', 'Nước dùng gà thành phẩm, không nêm', 20, 2.5, 0.5, 0.8, 0),
('F074', 'Nước dùng heo thành phẩm, không nêm', 20, 2, 0.5, 1, 0),
('F075', 'Mắm ruốc Huế thành phẩm', 100, 15, 4, 2.5, 0.5),
('F076', 'Mắm tôm thành phẩm', 80, 12, 4, 1.5, 0.3),
('F077', 'Dầu điều màu thành phẩm', 884, 0, 0, 100, 0),
('F078', 'Bột nghệ khô', 310, 9, 44, 3, 22),
('F079', 'Mật ong', 304, 0.3, 82, 0, 0),
('F080', 'Hành phi thành phẩm', 500, 6, 45, 32, 6),
('F081', 'Cơm gạo tấm đã nấu, không dầu', 130, 2.5, 28, 0.3, 0.3),
('F082', 'Thịt heo băm viên nướng chín, không sốt', 270, 26, 0, 18, 0);
-- END FOOD DATA

INSERT INTO _nf_assert (check_name, ok)
SELECT 'expected_82_staged_foods', IF(((SELECT COUNT(*) FROM _nf_food_stage) = 82), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'no_ambiguous_staged_food_names', IF((NOT EXISTS (SELECT name FROM _nf_food_stage GROUP BY name HAVING COUNT(*) <> 1)), 1, NULL);

CREATE TEMPORARY TABLE _nf_food_map (
    ref CHAR(4) PRIMARY KEY,
    food_id BIGINT UNSIGNED NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

START TRANSACTION;
INSERT INTO _nf_assert (check_name, ok)
SELECT 'no_ambiguous_existing_food_names', IF((NOT EXISTS (
 SELECT s.ref FROM _nf_food_stage s JOIN foods f ON f.name = s.name
 GROUP BY s.ref HAVING COUNT(*) > 1)), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'existing_foods_must_match_exactly', IF((NOT EXISTS (
 SELECT 1 FROM _nf_food_stage s JOIN foods f ON f.name = s.name
 WHERE CAST(f.name AS BINARY) <> CAST(s.name AS BINARY)
 OR f.calories_per_100g <> s.calories_per_100g
 OR f.protein_per_100g <> s.protein_per_100g
 OR f.carbs_per_100g <> s.carbs_per_100g
 OR f.fat_per_100g <> s.fat_per_100g
 OR f.fiber_per_100g <> s.fiber_per_100g
 OR f.active <> 1)), 1, NULL);

INSERT INTO foods (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g, active)
SELECT s.name, s.calories_per_100g, s.protein_per_100g, s.carbs_per_100g, s.fat_per_100g, s.fiber_per_100g, TRUE
FROM _nf_food_stage s LEFT JOIN foods f ON f.name = s.name
WHERE f.food_id IS NULL;
SET @nf_new_foods = ROW_COUNT();
INSERT INTO _nf_assert (check_name, ok)
SELECT 'food_names_still_unambiguous', IF((NOT EXISTS (
 SELECT s.ref FROM _nf_food_stage s JOIN foods f ON f.name = s.name
 GROUP BY s.ref HAVING COUNT(*) <> 1)), 1, NULL);

INSERT INTO _nf_food_map (ref, food_id)
SELECT s.ref, f.food_id FROM _nf_food_stage s JOIN foods f ON f.name = s.name;
INSERT INTO _nf_assert (check_name, ok)
SELECT 'expected_82_food_mappings', IF(((SELECT COUNT(*) FROM _nf_food_map) = 82), 1, NULL);

-- Do not COMMIT here. Continue parts 2 and 3 in THIS connection.
