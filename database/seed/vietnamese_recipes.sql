-- NutriFit Vietnamese catalog v1. Part 2/3; requires part 1 in SAME batch session.
INSERT INTO _nf_assert (check_name, ok)
SELECT 'part_1_food_mappings_required', IF(((SELECT COUNT(*) FROM _nf_food_map) = 82), 1, NULL);

CREATE TEMPORARY TABLE _nf_recipe_stage (
    ref CHAR(4) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    meal_type ENUM('BREAKFAST','LUNCH','DINNER') NOT NULL,
    base_servings DECIMAL(8,2) NOT NULL,
    instructions TEXT NOT NULL,
    prep_minutes INT UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO _nf_recipe_stage (ref, name, meal_type, base_servings, instructions, prep_minutes) VALUES
-- BEGIN RECIPE DATA
('R001', 'Phở bò', 'BREAKFAST', 1.00, 'Hâm nước dùng và nêm lượng nước mắm/đường đã kê; trụng bánh phở, xếp bò chín; thêm rau, nước dùng, chanh và tiêu.', 20),
('R002', 'Phở gà', 'BREAKFAST', 1.00, 'Hâm nước dùng gà và nêm; trụng phở, xé gà; thêm rau, nước dùng, chanh và tiêu.', 20),
('R003', 'Bánh mì trứng', 'BREAKFAST', 1.00, 'Pha cà rốt với giấm/đường và dùng hết phần pha; rán trứng với phần dầu giữ lại và muối; kẹp trứng, rau, nước tương, tiêu.', 15),
('R004', 'Bún bò Huế', 'BREAKFAST', 1.00, 'Hâm nước dùng; cho sả băm, mắm ruốc, dầu điều, nước mắm, đường và đun; xếp bún, bò, rau; chan nước và thêm chanh/ớt.', 25),
('R005', 'Hủ tiếu Nam Vang', 'BREAKFAST', 1.00, 'Nấu củ cải và tỏi với nước dùng, dùng hết nước; nêm; trụng hủ tiếu, xếp các phần thịt/gan/tôm/trứng; thêm giá, hẹ, hành.', 25),
('R006', 'Cháo gà', 'BREAKFAST', 1.00, 'Nấu gạo thành cháo; bù nước để đạt phần nước giữ trong suất; cho gà, gừng và gia vị; phi hành bằng dầu kê riêng và cho hết vào tô, thêm rau.', 45),
('R007', 'Bánh cuốn', 'BREAKFAST', 1.00, 'Ngâm nấm, phần nước ngấm giữ lại đề xuất 10 g; pha bột với 110 g nước để tráng; làm nhân heo/nấm và dùng 4 g dầu cho phần thực sự giữ; pha 30 g nước còn lại với mắm/đường/chanh/ớt; ăn kèm chả, dưa, hành phi.', 40),
('R008', 'Bún riêu', 'BREAKFAST', 1.00, 'Làm nóng nước dùng với riêu; xào cà chua/hành bằng dầu điều và đưa hết vào nồi; thêm đậu hũ, mắm; chan lên bún và rau.', 30),
('R009', 'Xôi gà', 'BREAKFAST', 1.00, 'Ngâm nấm với phần nước giữ lại; rim nấm/gà bằng nước tương/đường; làm mỡ hành bằng 3 g dầu; xếp trên xôi, thêm hành phi và dưa.', 25),
('R010', 'Bánh canh cua', 'BREAKFAST', 1.00, 'Hâm nước dùng; xào nhẹ hành bằng dầu điều; pha bột năng với 30 g nước, làm sánh; cho sợi/cua, nêm và thêm rau.', 30),
('R011', 'Cơm tấm sườn', 'LUNCH', 1.00, 'Hoàn thiện sườn chín với tỏi/nước tương/mật ong và một phần mắm/đường; dùng 3 g dầu làm mỡ hành, 3 g hoàn thiện sườn; pha đồ chua và nước chấm bằng phần còn lại; xếp suất.', 30),
('R012', 'Cơm gà xối mỡ', 'LUNCH', 1.00, 'Hoàn thiện gà đã hấp bằng xối dầu; cân phần dầu thực sự giữ; trộn nghệ vào cơm nóng; pha nước tương/đường/chanh/nước với tỏi; ăn cùng rau.', 30),
('R013', 'Cơm thịt kho trứng', 'LUNCH', 1.00, 'Đun thịt/trứng chín với nước dừa, nước, hành/tỏi, mắm/đường; giữ toàn bộ phần nước sốt phân cho suất; ăn cùng cơm và dưa.', 35),
('R014', 'Cơm cá kho tộ', 'LUNCH', 1.00, 'Pha sốt từ mắm/đường/hành/tỏi/nước/dầu; hoàn thiện cá chín trong tộ, chia toàn bộ sốt vào suất; thêm hành/tiêu, ăn với cơm và dưa.', 30),
('R015', 'Bún chả Hà Nội', 'LUNCH', 1.00, 'Dùng phần thịt/chả nướng chín đã cân; pha mắm/đường/giấm/chanh/nước với tỏi và đồ chua; ăn cùng bún và rau; hành/tiêu phân vào lớp gia vị giữ trên thịt.', 30),
('R016', 'Bún thịt nướng', 'LUNCH', 1.00, 'Hoàn thiện thịt nướng với sả/tỏi/nước tương/mật ong giữ lại; làm mỡ hành; pha nước chấm và cà rốt; xếp bún, rau, thịt, đậu phộng.', 30),
('R017', 'Cơm bò lúc lắc', 'LUNCH', 1.00, 'Xào rau và tỏi với dầu; cho bò đã chín cùng nước tương/mắm/đường, đảo nhanh, giữ nước thịt/sốt trong suất; ăn cùng cơm và rau.', 25),
('R018', 'Cơm gà luộc', 'LUNCH', 1.00, 'Trộn cơm nóng với nghệ/dầu đã kê; xé gà luộc; pha mắm gừng/tỏi/đường/chanh/nước; ăn cùng rau.', 25),
('R019', 'Cơm sườn ram', 'LUNCH', 1.00, 'Làm sốt hành/tỏi/mắm/nước tương/đường với nước; ram sườn chín bằng phần dầu giữ lại; ăn toàn bộ sốt phân cho suất cùng cơm/rau.', 30),
('R020', 'Cơm cá chiên', 'LUNCH', 1.00, 'Áp chảo cá nền đã chín với phần dầu giữ lại; pha nước mắm/tỏi/đường/chanh/nước; ăn cùng cơm và rau.', 25),
('R021', 'Cơm cá hấp', 'DINNER', 1.00, 'Hâm/hấp cá chín với gừng, hành và sốt đã kê; giữ nước cá trong suất; dùng dầu cho lớp hành; ăn cùng cơm/dưa.', 25),
('R022', 'Cơm thịt rang', 'DINNER', 1.00, 'Rang nhanh ba chỉ chín cùng hành/tỏi, mắm/đường/nước; chia toàn bộ phần mỡ/sốt giữ lại vào suất, thêm hành/tiêu.', 25),
('R023', 'Cơm canh chua cá', 'DINNER', 1.00, 'Nấu thơm/cà/đậu bắp/dọc mùng trong nước đã kê; cho me, cá chín và gia vị; thêm giá/rau thơm; phi tỏi bằng phần dầu riêng và dùng hết trong suất.', 30),
('R024', 'Cơm gà kho gừng', 'DINNER', 1.00, 'Phi hành/tỏi/gừng bằng dầu; kho nhanh gà chín với mắm/đường/nước; dùng sốt phân cho suất, ăn cùng cơm/dưa.', 30),
('R025', 'Cơm đậu hũ sốt cà', 'DINNER', 1.00, 'Xào cà/tỏi/hành với dầu, thêm nước/nước tương/đường/muối; cho đậu hũ trắng, đun nhẹ; ăn với cơm và xà lách.', 25),
('R026', 'Cơm tôm rim', 'DINNER', 1.00, 'Phi hành/tỏi, cho tôm chín với mắm/đường/nước, rim ngắn và dùng hết sốt phân cho suất; ăn cùng cơm/rau.', 25),
('R027', 'Cơm thịt luộc', 'DINNER', 1.00, 'Thái thịt luộc chín; pha nước chấm từ mắm/tỏi/ớt/đường/chanh/nước; ăn cùng cơm và rau.', 20),
('R028', 'Cơm canh bí đỏ', 'DINNER', 1.00, 'Phi hành bằng dầu kê riêng; nấu bí đỏ với nước, cho thịt băm chín và gia vị; thêm hành/tiêu; dùng toàn bộ canh với cơm.', 25),
('R029', 'Cơm cá kho', 'DINNER', 1.00, 'Làm sốt gừng/hành/tỏi/mắm/đường với dầu/nước; kho nhanh cá chín và chia sốt vào suất; ăn cùng cơm/dưa.', 30),
('R030', 'Cơm trứng chiên', 'DINNER', 1.00, 'Đánh trứng sống với hành và gia vị; chiên với phần dầu giữ lại; ăn cùng cơm/dưa/cà.', 20);
-- END RECIPE DATA

INSERT INTO _nf_assert (check_name, ok)
SELECT 'expected_30_staged_recipes', IF(((SELECT COUNT(*) FROM _nf_recipe_stage) = 30), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'ten_recipes_per_meal', IF((NOT EXISTS (
 SELECT meal_type FROM _nf_recipe_stage GROUP BY meal_type HAVING COUNT(*) <> 10)), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'base_servings_must_be_one', IF((NOT EXISTS (SELECT 1 FROM _nf_recipe_stage WHERE base_servings <> 1.00)), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'no_ambiguous_staged_recipe_names', IF((NOT EXISTS (SELECT name FROM _nf_recipe_stage GROUP BY name HAVING COUNT(*) <> 1)), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'no_ambiguous_existing_recipe_names', IF((NOT EXISTS (
 SELECT s.ref FROM _nf_recipe_stage s JOIN recipes r ON r.name = s.name
 GROUP BY s.ref HAVING COUNT(*) > 1)), 1, NULL);

INSERT INTO _nf_assert (check_name, ok)
SELECT 'existing_recipes_must_match_exactly', IF((NOT EXISTS (
 SELECT 1 FROM _nf_recipe_stage s JOIN recipes r ON r.name = s.name
 WHERE CAST(r.name AS BINARY) <> CAST(s.name AS BINARY)
 OR r.meal_type <> s.meal_type OR r.base_servings <> s.base_servings
 OR NOT (CAST(r.instructions AS BINARY) <=> CAST(s.instructions AS BINARY))
 OR NOT (r.prep_minutes <=> s.prep_minutes)
 OR r.image_url IS NOT NULL OR r.active <> 1)), 1, NULL);

CREATE TEMPORARY TABLE _nf_existing_recipe (
    ref CHAR(4) PRIMARY KEY,
    recipe_id BIGINT UNSIGNED NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
INSERT INTO _nf_existing_recipe (ref, recipe_id)
SELECT s.ref, r.recipe_id FROM _nf_recipe_stage s JOIN recipes r ON r.name = s.name;

INSERT INTO recipes (name, meal_type, base_servings, instructions, image_url, prep_minutes, active)
SELECT s.name, s.meal_type, s.base_servings, s.instructions, NULL, s.prep_minutes, TRUE
FROM _nf_recipe_stage s LEFT JOIN recipes r ON r.name = s.name WHERE r.recipe_id IS NULL;
SET @nf_new_recipes = ROW_COUNT();
INSERT INTO _nf_assert (check_name, ok)
SELECT 'recipe_names_still_unambiguous', IF((NOT EXISTS (
 SELECT s.ref FROM _nf_recipe_stage s JOIN recipes r ON r.name = s.name
 GROUP BY s.ref HAVING COUNT(*) <> 1)), 1, NULL);

CREATE TEMPORARY TABLE _nf_recipe_map (
    ref CHAR(4) PRIMARY KEY,
    recipe_id BIGINT UNSIGNED NOT NULL UNIQUE,
    was_existing BOOLEAN NOT NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
INSERT INTO _nf_recipe_map (ref, recipe_id, was_existing)
SELECT s.ref, r.recipe_id, e.ref IS NOT NULL FROM _nf_recipe_stage s
JOIN recipes r ON r.name = s.name LEFT JOIN _nf_existing_recipe e ON e.ref = s.ref;
INSERT INTO _nf_assert (check_name, ok)
SELECT 'expected_30_recipe_mappings', IF(((SELECT COUNT(*) FROM _nf_recipe_map) = 30), 1, NULL);

-- Do not COMMIT here. Continue part 3 in THIS connection.
