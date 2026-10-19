-- Nutrition recipe images v1. No schema, nutrients, recipe IDs or journal changes.
-- MySQL 8.0.16+; same session; stop on FIRST error, ROLLBACK and disconnect.
-- Never use mysql --force. Take/verify a catalog backup first.
-- Explicitly set @nutrifit_apply_recipe_images = 'YES' in this session before SOURCE.
SET NAMES utf8mb4;
START TRANSACTION;
CREATE TEMPORARY TABLE nf_recipe_image_guard_20261019 (
 stage VARCHAR(64) PRIMARY KEY, ok TINYINT NOT NULL, CONSTRAINT nf_image_guard CHECK (ok=1)
) ENGINE=InnoDB;
INSERT INTO nf_recipe_image_guard_20261019
SELECT 'confirmed target',IF(COALESCE(@nutrifit_apply_recipe_images,'')='YES' AND
 LOWER(DATABASE()) IN ('nutrifitdb','nutrifitdb_java'),1,0);
INSERT INTO nf_recipe_image_guard_20261019
SELECT 'InnoDB',IF(COUNT(*)=3,1,0) FROM information_schema.tables
 WHERE table_schema=DATABASE() AND table_name IN ('foods','recipes','recipeingredients') AND engine='InnoDB';
INSERT INTO nf_recipe_image_guard_20261019
SELECT 'image schema',IF(COUNT(*)=1,1,0) FROM information_schema.columns
 WHERE table_schema=DATABASE() AND table_name='recipes' AND column_name='image_url'
 AND data_type='varchar' AND character_maximum_length=1000;
CREATE TEMPORARY TABLE nf_recipe_image_mapping_20261019 (
 name VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
 meal_type VARCHAR(20) NOT NULL, image_url VARCHAR(1000) NOT NULL,
 PRIMARY KEY(name,meal_type)
) ENGINE=InnoDB;
INSERT INTO nf_recipe_image_mapping_20261019(name,meal_type,image_url) VALUES
('Phở bò','BREAKFAST','/assets/images/recipes/pho-bo.webp'),
('Phở gà','BREAKFAST','/assets/images/recipes/pho-ga.webp'),
('Bánh mì trứng','BREAKFAST','/assets/images/recipes/banh-mi-trung.webp'),
('Bún bò Huế','BREAKFAST','/assets/images/recipes/bun-bo-hue.webp'),
('Hủ tiếu Nam Vang','BREAKFAST','/assets/images/recipes/hu-tieu-nam-vang.webp'),
('Cháo gà','BREAKFAST','/assets/images/recipes/chao-ga.webp'),
('Bánh cuốn','BREAKFAST','/assets/images/recipes/banh-cuon.webp'),
('Bún riêu','BREAKFAST','/assets/images/recipes/bun-rieu.webp'),
('Xôi gà','BREAKFAST','/assets/images/recipes/xoi-ga.webp'),
('Bánh canh cua','BREAKFAST','/assets/images/recipes/banh-canh-cua.webp'),
('Cơm tấm sườn','LUNCH','/assets/images/recipes/com-tam-suon.webp'),
('Cơm gà xối mỡ','LUNCH','/assets/images/recipes/com-ga-xoi-mo.webp'),
('Cơm thịt kho trứng','LUNCH','/assets/images/recipes/com-thit-kho-trung.webp'),
('Cơm cá kho tộ','LUNCH','/assets/images/recipes/com-ca-kho-to.webp'),
('Bún chả Hà Nội','LUNCH','/assets/images/recipes/bun-cha-ha-noi.webp'),
('Bún thịt nướng','LUNCH','/assets/images/recipes/bun-thit-nuong.webp'),
('Cơm bò lúc lắc','LUNCH','/assets/images/recipes/com-bo-luc-lac.webp'),
('Cơm gà luộc','LUNCH','/assets/images/recipes/com-ga-luoc.webp'),
('Cơm sườn ram','LUNCH','/assets/images/recipes/com-suon-ram.webp'),
('Cơm cá chiên','LUNCH','/assets/images/recipes/com-ca-chien.webp'),
('Cơm cá hấp','DINNER','/assets/images/recipes/com-ca-hap.webp'),
('Cơm thịt rang','DINNER','/assets/images/recipes/com-thit-rang.webp'),
('Cơm canh chua cá','DINNER','/assets/images/recipes/com-canh-chua-ca.webp'),
('Cơm gà kho gừng','DINNER','/assets/images/recipes/com-ga-kho-gung.webp'),
('Cơm đậu hũ sốt cà','DINNER','/assets/images/recipes/com-dau-hu-sot-ca.webp'),
('Cơm tôm rim','DINNER','/assets/images/recipes/com-tom-rim.webp'),
('Cơm thịt luộc','DINNER','/assets/images/recipes/com-thit-luoc.webp'),
('Cơm canh bí đỏ','DINNER','/assets/images/recipes/com-canh-bi-do.webp'),
('Cơm cá kho','DINNER','/assets/images/recipes/com-ca-kho.webp'),
('Cơm trứng chiên','DINNER','/assets/images/recipes/com-trung-chien.webp');
-- Lock only the matched recipes. Exact Unicode name + meal type, never assumed numeric IDs.
SELECT r.recipe_id FROM recipes r JOIN nf_recipe_image_mapping_20261019 m
 ON CAST(r.name AS BINARY)=CAST(m.name AS BINARY) AND CAST(r.meal_type AS BINARY)=CAST(m.meal_type AS BINARY)
 ORDER BY r.recipe_id FOR UPDATE;
INSERT INTO nf_recipe_image_guard_20261019
SELECT 'all 30 unique active recipes',IF(COUNT(*)=30 AND COUNT(DISTINCT r.recipe_id)=30 AND COUNT(DISTINCT m.name,m.meal_type)=30
 AND SUM(r.active=1 AND r.base_servings=1.00)=30,1,0)
 FROM recipes r JOIN nf_recipe_image_mapping_20261019 m
 ON CAST(r.name AS BINARY)=CAST(m.name AS BINARY) AND CAST(r.meal_type AS BINARY)=CAST(m.meal_type AS BINARY);
INSERT INTO nf_recipe_image_guard_20261019
SELECT 'no unexpected existing image',IF(COUNT(*)=0,1,0)
 FROM recipes r JOIN nf_recipe_image_mapping_20261019 m
 ON CAST(r.name AS BINARY)=CAST(m.name AS BINARY) AND CAST(r.meal_type AS BINARY)=CAST(m.meal_type AS BINARY)
 WHERE r.image_url IS NOT NULL AND TRIM(r.image_url)<>'' AND CAST(r.image_url AS BINARY)<>CAST(m.image_url AS BINARY);
UPDATE recipes r JOIN nf_recipe_image_mapping_20261019 m
 ON CAST(r.name AS BINARY)=CAST(m.name AS BINARY) AND CAST(r.meal_type AS BINARY)=CAST(m.meal_type AS BINARY)
 SET r.image_url=m.image_url WHERE r.image_url IS NULL OR TRIM(r.image_url)='';
SET @nutrifit_recipe_images_changed=ROW_COUNT();
INSERT INTO nf_recipe_image_guard_20261019
SELECT 'all 30 image mappings verified',IF(COUNT(*)=30,1,0)
 FROM recipes r JOIN nf_recipe_image_mapping_20261019 m
 ON CAST(r.name AS BINARY)=CAST(m.name AS BINARY) AND CAST(r.meal_type AS BINARY)=CAST(m.meal_type AS BINARY)
 WHERE CAST(r.image_url AS BINARY)=CAST(m.image_url AS BINARY);
SELECT @nutrifit_recipe_images_changed AS image_urls_changed,30 AS mappings_verified;
COMMIT;
-- Session-only objects; these never refer to persistent tables.
DROP TEMPORARY TABLE nf_recipe_image_mapping_20261019;
DROP TEMPORARY TABLE nf_recipe_image_guard_20261019;
