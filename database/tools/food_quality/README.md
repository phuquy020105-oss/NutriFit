# Offline food quality evidence tools

The Python tools are offline and do not connect to MySQL. The optional Java LOCAL trial below is explicitly database-backed. Neither creates migration approval. Source cache stays outside Git and target, for example D:/NutriFit-data-sources/20261019. Never put .env or database backups in this cache.

The reviewed59-file retrieval manifest is committed at database/staging/food-quality-v1/source-retrieval-manifest.json. Verify an existing cache without network, or explicitly fetch missing files (HTTPS/SHA checked; changed responses and403 stop):

```powershell
python -X utf8 database/tools/food_quality/fetch_sources.py --cache D:/NutriFit-data-sources/20261019
# Only on a workstation missing the public inputs:
python -X utf8 database/tools/food_quality/fetch_sources.py --cache D:/NutriFit-data-sources/20261019 --download-missing
```

Official inputs:

- [USDA SR Legacy April2018 CSV ZIP](https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip), SHA256 b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0. Download using HTTPS certificate/hostname verification. The public DNS issue on this workstation was resolved using a validated DNS-over-HTTPS A record with curl --resolve retaining the official hostname and TLS verification; do not disable TLS or permanently assume the IP remains valid.
- [MEXT English2015 workbook](https://www.mext.go.jp/component/english/__icsFiles/afieldfile/2017/12/25/1374049_1r12_1.xlsx), SHA256 5c968f1801f706b2970d51599ab2dce6f9e09ff3901fcf1990922960761885fb. Older controlled edition, not the2023 edition. Symbols/presentation follow the official introduction linked from each source record.
- NIN snapshots: nin-searches/retrieval-index.json lists the38 public query URLs, date, response file and SHA256. The selected nutrient excerpts and response hashes are retained in committed provenance; a teammate can inspect these without downloading the entire website. A refresh must be reviewed, not silently substituted under the old hash.

Run from the repository root in PowerShell (JDK21/Maven installed):

```powershell
$sourceCache='D:/NutriFit-data-sources/20261019'
python -X utf8 database/tools/food_quality/extract_usda.py --archive "$sourceCache/usda-srlegacy-2018-official.zip" --output "$sourceCache/usda-traceable-index.json"
python -X utf8 database/tools/food_quality/build_provenance.py --source-cache $sourceCache
python -X utf8 database/tools/food_quality/build_expansion.py --source-cache $sourceCache
$env:USDA_SOURCE_ARCHIVE="$sourceCache/usda-srlegacy-2018-official.zip"
$env:MEXT_SOURCE_ARCHIVE="$sourceCache/mext2015-table.xlsx"
python -X utf8 -m unittest discover -s database/tools/food_quality -p 'test_*.py' -v
mvn '-Dtest=FoodDataQualityAuditTest,FoodQualityCohortBenchmarkTest' test
if ($LASTEXITCODE -ne 0) { throw 'Java audit failed; do not publish an old report' }
Copy-Item target/food-quality/recipe-audit.json database/staging/food-quality-v1/recipe-audit.json
python -X utf8 database/tools/food_quality/write_reports.py
```

Source-archive integration tests SKIP explicitly if their environment variables are not configured. A skipped test is NOT evidence of archive validation. The committed source matching decisions and provenance support code review without a local cache; source extraction/refresh needs the hash-pinned inputs. Do not normalize absent nutrients to zero, use a raw food for a cooked one, or mark every source value analytical/VERIFIED. Estimated zero from a publication is preserved with its estimated qualifier.

Data gates remain closed for Aiven. B/C are expressly exploratory: B now uses70 source-complete food comparisons and12 unresolved baseline estimates; C adds30 original portion designs and18 source-matched foods. They are not a qualified/fully verified B/C comparison. All changes remain staging, as the owner confirmed.30 distinct AI illustrations are now decoded/reviewed under staging/images with full prompts/rights/disclosure and null runtime URLs; fallback remains explicit until qualification/asset release. The Docker allowlist copies only src/main, not these datasets or tools.

## Optional isolated LOCAL MySQL trial

This is deliberately NOT a production migration tool. It reads only LOCAL_DB_HOST/PORT/USER/PASSWORD from a private env file; no option file, password arguments or logs. Host must be loopback3306; name must start nutrifit_fq_ and end _test; a write run refuses an existing database. It creates six schema-derived tables plus disposable fixtures, not a full24-table production clone. DDL auto-commits; no automatic DROP or DDL rollback is promised.

After Maven package, compile and run with JDK21. Choose an unused test database name. Do not replace the target with your main database.

```powershell
javac -encoding UTF-8 -cp 'target/classes;target/nutrifit/WEB-INF/lib/*' -d target/food-quality-tools database/tools/food_quality/LocalFoodQualityTrial.java
java -cp 'target/food-quality-tools;target/classes;target/nutrifit/WEB-INF/lib/*' com.nutrifit.service.LocalFoodQualityTrial 'D:/NutriFit-backups/aiven-migration/.env' nutrifit_fq_YYYYMMDD_unique_test
# A later read-only verification of that exact test database:
java -cp 'target/food-quality-tools;target/classes;target/nutrifit/WEB-INF/lib/*' com.nutrifit.service.LocalFoodQualityTrial 'D:/NutriFit-backups/aiven-migration/.env' nutrifit_fq_YYYYMMDD_unique_test --verify-existing
```

The trial maps checked names/generated IDs, deliberately shifts ID sequences, applies transactional food corrections/new foods/new recipes/links, injects an expected mid-transaction failure and verifies full rollback, re-runs for idempotency, rejects a conflicting value, and compares historical snapshots and JDBC calculator output. A genuine SQL error stops; no automatic production retry or permission bypass exists. Local TLS is REQUIRED; this tool never reads or weakens Aiven VERIFY_IDENTITY configuration. Keep private configuration/backup outside Git.

Latest actual evidence is in local-trial-result.json and local-trial-readonly.json. It proves local mechanics, not nutritional validity, compatibility with every production contract or a successful Aiven import. Continuation final Maven114 tests, Python32 tests and14 JS fixture checks passed; archive tests still explicitly skip when no source inputs are supplied.

## Continuation: current source and release gates

INMU Thai FCD adds19 hash-pinned public detail pages, with food/scientific identity and per100g edible basis. Available carbohydrate is used directly (never subtract fiber twice); derivation, sample counts and original missing/assumed-zero remain explicit. USDA168374 ground-pork pan-broiled is a disclosed LOW-confidence proxy for F082; no brand/fat formulation is invented. See remaining-food-evidence.md for47 unresolved facts in12foods. New fullyVERIFIED foods remain0.

```powershell
$env:THAI_SOURCE_CACHE="$sourceCache/continuation"
python -X utf8 database/tools/food_quality/validate_quality.py --source-cache $sourceCache
python -X utf8 database/tools/food_quality/review_recipes.py
python -X utf8 database/tools/food_quality/summarize_benchmarks.py
python -X utf8 database/tools/food_quality/prepare_release.py
# Expected REFUSAL while source/portion/backup/owner gates are unresolved; emits no production SQL:
python -X utf8 database/tools/food_quality/prepare_release.py --production
```

After every fresh Maven audit, copy target/food-quality/recipe-audit.json and new-recipe-nutrition.json to staging. Copy cohort-A/B/C.csv and their summaries to cohort-A/B/C-guarded.csv and -guarded-summary.txt before summarizing. A-before is the preserved actual old-algorithm run, never regenerated with new code. New image decoding requires Pillow from requirements.txt (tool-only, not Maven/runtime); `python -m pip install -r database/tools/food_quality/requirements.txt` on a fresh workstation. Source tests without archive/cache envs explicitly SKIP.

### Existing staging: verify first, never recreate or rerun the old seed

```powershell
javac -encoding UTF-8 -cp 'target/classes;target/nutrifit/WEB-INF/lib/*' -d target/food-quality-tools database/tools/food_quality/LocalFoodQualityTrial.java database/tools/food_quality/LocalQualityDelta.java
java -cp 'target/food-quality-tools;target/classes;target/nutrifit/WEB-INF/lib/*' com.nutrifit.service.LocalQualityDelta 'D:/NutriFit-backups/aiven-migration/.env' nutrifit_fq_20261019_food_quality_test
# Only for this explicitly named disposable staging DB after successful SELECT-only validation:
java -cp 'target/food-quality-tools;target/classes;target/nutrifit/WEB-INF/lib/*' com.nutrifit.service.LocalQualityDelta 'D:/NutriFit-backups/aiven-migration/.env' nutrifit_fq_20261019_food_quality_test --apply-local-delta
```

The delta accepts only hash-pinned known checkpoint states or the exact current C; any unexpected state stops. It never creates schema, runs a seed or contacts Aiven. Two actual continuation deltas updated10 then1 foods;0 new foods/recipes/links, injected rollback and second-run0writes, conflict rejection, snapshot invariants,30 temporary image mappings all PASS. Image trial URLs are rolled back, not activated. Keep local-delta-69-source-result.json as earlier evidence and local-delta-result.json as current proof. The old fresh-database trial remains available for a separately named disposable test only; its old report is not evidence for a changed C.

### Optional Aiven SELECT-only verification

```powershell
javac -encoding UTF-8 -cp 'target/classes;target/nutrifit/WEB-INF/lib/*' -d target/food-quality-tools database/tools/food_quality/FoodQualityReadOnly.java
java -cp 'target/food-quality-tools;target/classes;target/nutrifit/WEB-INF/lib/*' com.nutrifit.config.FoodQualityReadOnly 'D:/NutriFit-backups/aiven-migration/.env' 'D:/NutriFit-backups/food-quality-20261019/backup-before-images' target/food-quality/aiven-readonly-current.json
```

Uses only SELECT/SHOW on allowlisted catalog tables; target/database/version/CA pin/TLS VERIFY_IDENTITY are checked. Passwords loaded privately into JDBC properties, never arguments or logs. Baseline catalog snapshots/SQL remain private outside Git; a different operator must obtain an approved baseline privately rather than copying user backups into the repository. SHA/JSON comparison is not a restore rehearsal or full-database backup. No production writer is supplied: release/candidate-migration-plan.json is a reviewable non-executable plan, not permission to import.

Image generation used30 separate built-in image_gen calls; all prompts/outputs/checksums/rights/disclosure are in image-generation-jobs.json and images/. These are conceptual illustrations, not photographed/weighed servings. Nothing copies them into the WAR automatically. Keep the existing30 runtime assets and image URLs unchanged.

Health exposes only a validated40hex RENDER_GIT_COMMIT or unknown, with no-store. This is a public deployment marker, not a secret dump. [Render documented default environment variables](https://render.com/docs/environment-variables). Deployment still requires observing the expected SHA on the live endpoint; HTTP200 alone is insufficient.

Line-ending reproducibility: .gitattributes pins staging/tools LF and WebP binary, preserves the legacy canonical JSON CRLF checksum419fa5e4...; scorer source stays LF. Git checkout filters were verified to reproduce the exact current baseline/service bytes without modifying seed/schema.
