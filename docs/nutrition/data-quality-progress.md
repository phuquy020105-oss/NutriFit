# Food Data Quality — durable checkpoint

Updated2026-10-19 Bangkok. Status PARTIAL; engineering checks PASS; production nutrient/catalog gates remain CLOSED.

## Resume first

- Actual repository: D:/Web/NutriFit-Integration, branch deploy/render-aiven-brevo. D:/Web/NutriFit is a DIFFERENT checkout.
- User explicitly confirmed: no product/formula evidence yet; keep staging and DO NOT write Aiven. This overrides any earlier conditional production migration plan.
- Authoritative four-stage task: attachment021d3a6f-4faa-4c64-bfde-498751544728/Pasted text.txt. Read final-data-quality-report.md plus current Git state before resuming; do not repeat imports.
- Baseline98c0204fc43a132ae323b3117f5de5153ceddca9. Data-only commit0dd67b937b8c652cd3cfe292ee2b54ed151dbb0c. Code/docs commit follows separately. Final push/Render evidence lives in the handoff and private progress note; verify current remote rather than assuming.
- No secret values in checkpoints. Source cache D:/NutriFit-data-sources/20261019 survives Maven clean. Private env/backup outside Git; never display them.

## Completed evidence

- USDA official SR Legacy04/2018 ZIP: HTTP200, verified TLS/ZIP CRC;7793foods/644125nutrient rows; SHA b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0. DNS resolved via DoH/curl --resolve retaining original HTTPS hostname, not disabling TLS.
- MEXT English2015 updated2017-12-27:2191foods, SHA5c968f1801f706b2970d51599ab2dce6f9e09ff3901fcf1990922960761885fb. Four selected matches; raw Excel values/estimated/trace/missing qualifiers preserved. Two SMILING Vietnam URLs returned403, not read.
- NIN38 public food queries,30 selected alternatives; public dish lookup also inspected but no recipe gram/yield basis. FAO methods retained.57USDA selections,4MEXT,59originalfoods with five source/computed values;23incomplete.410facts:175MATCHED/120CALCULATED/17ESTIMATED/98MISSING/0VERIFIED.0fullyVERIFIED foods. Null/Tr not zero; available carbs explicitly total minus fiber same-record.
- Full30recipe/383link audit via real unchanged NutritionCalculator.9source-complete comparisons: R003/R012/R017/R018/R019/R024/R025/R027/R030. No original gram/ID/type/base/history changes; cooking/yield/oil not fully verified.
- New18source-matched foods,30draft recipes R031–R060,10/meal,224links. C exploratory100foods/60recipes/607links,20/meal.0approved new productionrecipes,0new images; fallback honest, old30images unchanged.8designs>800glistedmass require review: R044/R047/R048/R050/R053/R054/R057/R060.
- Minimal runtime guard: when an eligible projected menu within10%target exists, select/regenerate within15%, same weights/preferences/one serving/history. BigDecimal distance; no source/target/BMR change. A baseline avoidable>20%error cases5→0.
- Benchmark432cases/dataset, real original OnboardingService via captureDAO;6adults/3activities/3goals/4subscription-preference states/2journalstates. Same algorithm and A historical snapshot for guardedA/B/C. Originalpre-guardA separately preserved. Mean absolute kcalerror A_before605.949/A_guard598.575/B556.847/C161.362. C exploratory remains88/432notfeasiblewithin10%; unweighed portions mean no clinical/production approval.

## Actual database side effects

- Aiven THIS task SELECT-only:24tables/82foods/30recipes/383links/30imageURLs;TLSv1.3 VERIFY_IDENTITY. All410facts/383links matched baseline. No Aiven write. Snapshot is time-specific, not perpetual state.
- Catalog backup/DDL/SQL with SHA/roundtrip outside Git: D:/NutriFit-backups/food-quality-20261019/backup-before-images. Legacy folder name; not full DB backup, no restore rehearsal.
- ONLY local write: new isolated database nutrifit_fq_20261019_food_quality_test, six schema-derived tables, NOT24table production clone. Reported MySQL version26.7.0. Main local DB untouched. Left staging DB intact for inspection; never DROP/overwrite existing.
- Baseline fixtures with deliberately shifted IDs and synthetic disabled-login account/history. C inserted18foods/30recipes/224links,updated55foods. Failureafter99writes rolled back full catalog/history; valid run succeeded; secondrun0insert/0update; conflict rejected/rolledback; old1.32snapshot intact. JDBC adapter/calculator matches60recipes. Final SELECT-only matches C SHA afdaad645524f15c334e7c0f6dfcb5dc4b1335b06dbdc2adc1b332e702f9ad20.
- Local tool only LOCAL_DB_* memory properties, loopback3306/test-only name, refuses existing DB in write mode. Separate --verify-existing read-only. DDLauto-commit explicitly acknowledged; transaction rollback covers DML. No production migrator or approved nutrient/gram manifest exists.

## Actual checks, do not relabel as E2E

- JDK21.0.12/Maven3.9.16 clean package PASS111JUnit,0fail/error/skip,36.322s,2026-10-19T21:07:25+07. Includes5newaudit/4newcohort plus existing102.
- Python20PASS, six realarchive tests configured,0skip. Without env archive tests explicitlySKIP.
- Publicsourcecache40files SHA PASS offline; baselinevalidatorPASS82/30/383.
- JSP Tomcat10.1.61/JDK21 compile0errors (tomcat-juli/Ant classpath required).
- Chrome headless fixture14JavaScriptchecksPASS; imageassetJUnitPASS. No authenticated E2E/loadtest/Dockerbuild claimed.
- Standalone javac LocalFoodQualityTrial PASS, actual local trial and SELECT-only PASS. NegativewrongDB/nonloopback/existingDB checksPASS before writes.
- Secret/scope/JSON/PythonAST/whitespace checksPASS; .env/backup/target ignored. Docker copies only pom/src/main; staging/tools/docs not deployed. Runtime change only recommendationservice. Seedvalidator checksum fixed for document-only prose drift501e0fa; independentdataSQLguards unchanged.

## Pending after this checkpoint

1. Commit code/docs/tests/tools separately, push origin/deploy/render-aiven-brevo safely and verify exact remote SHA. If already done, inspect Git/private handoff instead of duplicating commit.
2. Render check public health/Nutrition/assets and commit status where accessible. Health200 alone does NOT prove deployed SHA. No dashboard/APIaccess established; do not change cloud configuration or database.
3. Keep data staging. Obtain actual labels/formulas for chả lụa/mắm ruốc/mắm tôm/hành phi/nước dùng/riêu cua, resolve98missing facts/state/assay questions; no guessed matches/zeros.
4. Kitchen review originalrecipes/oil/yield,8large new portions, all30new designs; acquire30correct licensed/generated images after portions stabilize. PreserveoldIDs/grams/history/images until separately approved.
5. Only then rebuild qualifiedB/C, benchmarksamecohort, migrationmanifest/localtrial/fullbackup/restore rehearsal/freshread-onlyTLS/conflictgates. User must lift current no-Aiven-write hold before production data mutation.

Detailed results and reproducible commands: final-data-quality-report.md and ../../database/tools/food_quality/README.md.
