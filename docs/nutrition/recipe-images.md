# Recipe illustrations and image-only migration

There are 30 distinct, original AI-generated food illustrations for the existing 30 recipes, plus one original SVG plate placeholder. No external restaurant/stock photographs, random Google Images, hotlinks or watermarks are used. They were generated specifically for NutriFit with `image_gen`, using each recipe's actual name, cooking instructions and ingredient list. They are illustrations, not proof of measured grams, nutrient content or an actual photographed serving. No third-party CC licence or exclusive copyright is claimed.

[recipe-image-sources.json](recipe-image-sources.json) records every name, meal type, generation brief/ID, local URL, SHA-256, dimensions and byte size. All WebP files are 800×450, 45,598–69,252 bytes, 1,675,848 bytes combined. The larger generated originals are retained outside Git. Only format conversion/resizing was used for web optimization; food content was not composited from unrelated dishes.

Every illustration was reviewed against its name and preparation: phở bò/gà use the correct protein, bún bò Huế follows this beef-only recipe, bánh mì trứng has egg/cucumber/carrot/cilantro, bún riêu includes white tofu, rice dishes include rice and their named main, canh bí đỏ includes pumpkin/minced pork, cơm trứng chiên is rice with omelette rather than fried rice. The JSON ingredient instructions remain authoritative; images do not imply exact visible portions.

## Runtime

The read-only JDBC recipe adapter carries the existing `recipes.image_url` through compatible DTO constructors into suggested meals. JSP accepts only packaged `/assets/images/recipes/<slug>.(webp|jpg|png|svg)` paths, prepends the servlet context, escapes attributes, supplies the dish as alt text and uses lazy 16:9 images. Empty/unsafe URLs use the SVG placeholder. JavaScript switches a failed image to the placeholder once, including failures before deferred script execution, and prevents error loops. No external image hosts or new dependencies are needed.

No portion control is introduced. NutritionCalculator, three-decimal storage, current journal snapshots, Premium gates, CSRF and the existing save transaction remain in place.

## Recreate image mappings on another machine

1. Deploy these assets with the WAR and verify the files/hashes in the manifest first.
2. Verify the intended MySQL target, schema and InnoDB, and take/verify a catalogue backup. Do not rerun the old food/recipe seeds on an existing database.
3. Review [20261019_recipe_images.sql](../../database/migrations/20261019_recipe_images.sql). It matches exact Unicode recipe name + meal type, never assumed IDs. All 30 must be present once, active, with base servings 1.00. A nonempty image URL different from the intended URL aborts; no existing image is overwritten blindly.
4. Connect with MySQL 8.4 client and a prompted password, not a password value on the command line. For Aiven, use `--ssl-mode=VERIFY_IDENTITY --ssl-ca="<private CA path>" --host=<AIVEN_HOST> --port=27047 --user=<AIVEN_USER> --database=nutrifitdb --default-character-set=utf8mb4 --abort-source-on-error --password`. Do not log credentials. The local target remains `nutrifitdb_java`.
5. In that one session, explicitly confirm and source the reviewed file:

```sql
SET @nutrifit_apply_recipe_images = 'YES';
SOURCE D:/Web/NutriFit-Integration/database/migrations/20261019_recipe_images.sql;
```

Do not use `--force`. On the first error, execute `ROLLBACK` and disconnect; do not continue past a failed guard or issue COMMIT manually. Batch clients must abort on SQL errors. The [MySQL CHECK constraint reference](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html) explains the guard mechanism. Temporary mapping/guard tables are session-only; persistent schema is untouched.

The script updates only missing/blank image_url values, inside one transaction, and verifies all 30 mappings before COMMIT. An already applied run returns zero changed URLs. The explicit confirmation variable and allowed database names are checked before the UPDATE. Successful runs remove their temporary tables. Disconnecting after an error removes temporary tables and rolls back uncommitted changes.

## Production execution evidence

See the execution record below for actual Aiven results; do not infer application from this SQL's presence in Git. The private backup includes full foods/recipes/recipeingredients rows and SHOW CREATE TABLE, JSON read-back checks and SHA-256 plus SQL data recovery material. Backup verification is not a restore rehearsal. Recovery, if needed, should restore only the image_url column from the reviewed backup using exact recipe IDs/current expected image guards in a transaction, not replay the full catalogue INSERT backup into a populated database.

No new foods/recipes are introduced here. Future recipes must get reviewed new assets and mappings; external URLs fall back until explicitly supported. Local database execution is optional and is not implied by Aiven verification.


### Verified Aiven result (2026-10-19)

- Target `nutrifitdb`, MySQL 8.4, 24 persistent tables, TLS VERIFY_IDENTITY / TLSv1.3, existing image_url VARCHAR(1000), all three catalog tables InnoDB; no recipe triggers.
- Before: 82 foods / 30 recipes / 383 ingredients; 0 nonempty image URLs. All food nutrients, recipe identities/base servings and ingredient grams matched the canonical JSON.
- Private backup: `D:/NutriFit-backups/nutrition-images-20261019/backup-before-images`, NTFS ACL restricted to the current Windows user and SYSTEM. Full rows and DDL read back; SHA-256 checked again before migration. Restore was not rehearsed.
- Initial pre-update JOIN failed with MySQL 1267 because meal_type collations differed between Aiven and the temporary map; the transaction was rolled back and SELECT confirmed 0 image URLs changed. Exact-byte comparison of both name and meal_type fixed this; a guard-only dry-run passed without executing the UPDATE.
- Final run: COMMIT, 30 image URLs changed and all 30 mappings verified. Second run: COMMIT, 0 URLs changed, all 30 still verified. 82/30/383 counts, persistent DDL, all IDs, nutrient values, instructions and ingredient grams remained unchanged. The SQL touches only recipes.image_url; no journal tables are written.
- MySQL local was not modified. No new 30 recipes or nutrient changes were imported.
- Before deployment: all 30 WebP URLs and SVG fallback returned HTTP 200 on isolated Tomcat 10.1, hashes matched the packaged source; six JSP fixture modes and a 390px mobile layout probe passed. Production HTTP verification is reported separately after deploy.
