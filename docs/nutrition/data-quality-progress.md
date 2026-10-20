# Go-live 60 món — hoàn tất 2026-10-20

Chủ dự án đã phê duyệt đúng manifest SHA256 `40c1ab4b874dc74089722f9b2952d2cfbd7ae8f4f120d4fb488c30da801c84cc`. Migration trên **Aiven nutrifitdb đã COMMIT thành công**: thêm 18 Food, 30 Recipe, 224 Ingredient và cập nhật 66 Food. Hậu kiểm bằng SELECT xác nhận **100 Food / 60 Recipe / 607 Ingredient, 20 món mỗi bữa**; cả 60 món khớp NutritionCalculator và ảnh, khóa ngoại hợp lệ. Schema và checksum của 21 bảng ngoài catalog giữ nguyên. ID cũ, 30 Recipe, 383 Ingredient cũ và nhật ký được bảo toàn. Lần chạy thứ hai trả `ALREADY_APPLIED`, **0 lần ghi**.

Biên bản máy đọc được: [demo60-go-live.json](demo60-go-live.json). Backup catalog và DDL của 24 bảng lưu ngoài Git đã được phục hồi thử thành công; backup này không chứa toàn bộ dữ liệu cá nhân. Manifest và 121 checksum của gói được giữ bất biến. Cờ chưa deploy trong manifest ghi trạng thái lúc đóng gói; biên bản go-live bổ sung trạng thái thực tế sau phê duyệt. Không chạy lại migration để cập nhật cờ trong manifest.

Code và ảnh đã được xác minh trên Render tại revision `b8a55682c96226959e57b14559a2797f20499e68`. Chưa kiểm thử trình duyệt production với tài khoản đăng nhập; dữ liệu đã được kiểm tra qua JDBC thật trên Aiven. Người dùng có thể nhấn **Đổi thực đơn** để chọn từ 60 món. Các bản xem trước và nhật ký cũ không bị tự đổi.

Các checkpoint chuẩn bị bên dưới là lịch sử, không còn là yêu cầu chờ phê duyệt:

# Checkpoint 2026-10-20 — release 60 món và đổi riêng từng món

Tiêu chuẩn hiện hành: ước tính có căn cứ được chấp nhận cho đồ án. **Không ghi Aiven trước khi chủ dự án phê duyệt SHA256 manifest cuối một lần.**

- Checkout: D:/Web/NutriFit-Integration; branch deploy/render-aiven-brevo. Bắt đầu từ0cfccdd đãpush và đã xác minh live revision qua health.
- Release mới: database/staging/food-quality-v1/release/final-manifest.json, build bởi finalize_demo_release.py;100Food/60Recipe/607Ingredient,20món/bữa.103/500factsESTIMATED trên35Food;236MATCHED/161CALCULATED.12whole-food legacy estimates và5whole-vector category/process analogs ghi rõ giả định/độ tin cậy. Không giả VERIFIED; strict47MISSING audit còn nguyên.
-30suất mới review; sáu suất lớn được chấp nhận là bữa đầy đủ có món kèm, không tự giảm gram.0suất được tuyên bố đã cân đo.30WebP đãduyệt copy byte-exact sang assets;30ảnh cũ/seed/schema/Onboarding/history không đổi.
- Swap service/servlet/UI hoàn thiện: cùngmeal_type,1.00suất,15/25/35%calorie tiers,five-nutrientfloors,fat/day-quality guards,actualprojectedjournal,Free/expired không đọc preferences,PremiumDISLIKE/softLIKE. Per-slot recentIDs; exhausted giữ nguyên. CSRF/owner/date/30minuteexpiry/attempted/saved/sessionlock/rotatingnonce chốngstale/double-submit. Không ghiDB khi swap; save vẫntransaction/rollback.
- Actual MavenJDK21.0.12.1/Maven3.9.16 cleanpackage và finalpackage PASS127JUnit0fail/error/skip. Python38PASS0skip với cache nguồn thật. JspC0errors;Chrome14legacy+23swap checksPASS. JspC từng bắt được block JSP thiếu đóng, đã sửa trước khi push. FixtureHTML từng chứa end-script trong string, đã sửa. Không authenticatedproductionE2E.
-432cases/dataset: A30meanabsKcalError598.575/B30qualified468.238/C60qualified167.395. Feasible10%target200/236/336;0avoidable>20%gap. Giá trịC giống exploratoryC trước đó; thay đổi là qualification cho demo, không phải có kết quả xét nghiệm mới.
- Swap trên30/60recipe:18scenario mỗi dataset,95/91swap thành công,0scenario không có lựa chọn đầu tiên,maxrelativekcal22.78%/14.90%. Chỉ đổi một thẻ, tổng/ảnh/warnings/nonce cập nhật bằng servervalues, integerHALF_UP chỉ cho display.
- AivenREADONLY backup mới: D:/NutriFit-backups/food-quality-20261020/demo60-before. Catalog82/30/383+24DDL+SHA,không exportuserrows. TLSVERIFY_IDENTITY/CApin/hostname. Không productionwrite.
- Restore thật vàoLOCAL nutrifit_fq_demo60_20261020_v2_test:24tables,baselineexactrows/PK/Unicode; migration+18Food/+30Recipe/+224links/update66Food;rollbackinjected99writes,idempotency0writes,conflictrejected,oldIDs/protectedtables/1.32snapshotpreserved,60JDBCcalculator/images/FKPASS. DDL ANSI_QUOTES và tên cột per_100g đã được xử lý đúng. DBthử đầunutrifit_fq_demo60_20261020_test còn trống,khôngDROP; DBstagingcũ/mainlocal không sửa.
- Bảncatalog-C-local-trial.json giữ SHA dữ liệu đã thửlocal trước khi relabel5proxyESTIMATED; finalize kiểm tra SQLcontract(nutrient/recipe/grams/images) bằng hệtcatalog-C-qualified. Không đổi số liệu sau thửlocal.
- Tools triển khai: Invoke-DemoCatalogRelease.ps1,FoodQualityReleaseSnapshot.java,CatalogReleaseMigration.java. Productionmode yêu cầu đúng --go-live-approved-manifest SHA,tất cả filehash/backuprestorechecked/exactbeforeorafter/TLS/InnoDB/khôngtrigger/transaction. KhôngDROP/DELETE/TRUNCATE/force/retry. SchemaDDL chỉ dùng tạoDBtestmới;AivenDML chỉ3catalogtables. Backup không phải fulluserdata; recoverylive cần giữ mọi ID/FK/history.
- README và docs/nutrition/demo60-release.md có lệnh tái tạo. STAGING/exploratory reports cũ là lịch sử, không phải gate hiện hành. Trạng thái kỹ thuật PRODUCTION_READY; go-live chưa được phép. Bước còn lại: finaldiff/secrets/checkoutfilter review,commit/pushnonforce,remoteSHA/Renderrevision/assets verification,rồi hỏi go-live một lần đúng manifest. Ghi SHA và kết quả thực tế vào handoff riêng sauGit để tránh vòng lặp tự tham chiếuSHA.

Historical checkpoint follows (outdated gates and push state are historical evidence, not current acceptance criteria):

# Food Data Quality — latest durable checkpoint

Continuation114a7953 fromf04b2da,2026-10-19 Bangkok. OverallPARTIAL; engineering and internal stagingPASS. **NO PRODUCTION AIVEN WRITE AUTHORIZED.** User must explicitly approve a final qualified manifest in a future step; current task does not lift hold.

## Resume first

- Actual checkout D:/Web/NutriFit-Integration, deploy/render-aiven-brevo. Default D:/Web/NutriFit is different.
- Read final-data-quality-report.md,production-readiness.md,remaining-food-evidence.md and this checkpoint; inspect currentGit/remote before work.
- StartingHEADf04b2da was clean and matchedremote. Prior quality code55fde65/data0dd67b9 remain history. Continuation commits/push/revision observation are recorded in the final handoff/private note after Git operations; do not assume an unpushed local commit is deployed.
- Sourcecache D:/NutriFit-data-sources/20261019 outsideGit/target.40oldcachefilesSHA verified withoutredownload;19newINMU detailpages undercontinuation,59total pinnedfiles. No secrets in reports. PrivateENV/backups outsideGit,neverdisplay values.

## Actual NEW data progress

-51of98MISSING resolved across12food references;47remain in12foods;70/82now have all5source/computedvalues (was59).
-410statuses209MATCHED/135CALCULATED/19ESTIMATED/47MISSING/0VERIFIED.0fullyVERIFIEDfoods. LowconfidenceMu-yo/Ka-pi/redtilapia/pan-broiledgroundpork remain disclosed comparisons, not approvedproductformulas.
-INMU19sourcepages preserve identity/scientificname/100gedible/derivation/n/update/footnote. Eleven selectedINMUrecords. Availablecarbs direct, nosecondfibersubtraction. USDA168374 explicit84%lean cookedpan-broiledproxy F082adds5facts; do notinferactualbuncha fatratio. Allsourceunit/missing/estimatedzeros retained. Extra vannameilookup503,no bypass/retry.
-Original30/383already audited incheckpoint; source-complete comparisons9->18now. No originalgram/name/mealtype/base/ID,canonicalseed/schema,Onboarding or historicalsnapshot changes.
-Cexploratory100Food/60Recipe/607links,20/meal unchangedcounts. 30newdesigns remainstaging;all30mass/state/water/oil/retentionnotes documented.24methodqualifiedforSTAGING;6largenon-soupservings pendingR044/R048/R050/R054/R057/R060. R047/R053include200gaddedwaterwithriceside;>800gnotautomaticfailure. No inventedmeasuredmass/yield/loss.0newrecipesproductionapproved.
-30distinctAIillustrations generated via built-inimage_gen,800x450WebP,30hashes,2,124,668bytes. AllvisuallyreviewedplusfullsizeR054recheck(broccolipresent). Prompt/source/rights/disclosure/alt/hash in image-generation-jobs.json;WebPs in staging/images.0runtimeURLsnew,old30imagesunchanged;WARdoesnotcontainnewassets. OriginalPNGsremain.codex/generated_images.

## Actual NEW database side effects

- Existing LOCAL nutrifit_fq_20261019_food_quality_test verifiedSELECT-only beforewrites.6tables,MySQLreported26.7.0,not24tableclone. NoDDL/seed/recreation/drop.
-LocalQualityDelta firstupdated10foods(59->69complete),then1F082(69->70);0newfoods/recipes/links. Both injectedrollback,secondrun0writes,conflictrejection,historyhashpreservation,JDBCcalculator/FKs PASS.30imageURLmappings testedbygenerated/nameIDthenrolledback,activeURLsnew0.
-Hash-pinnedbeforeC59afdaad645524f15c334e7c0f6dfcb5dc4b1335b06dbdc2adc1b332e702f9ad20;intermediateC69 5523b9647bad68435b0f6ccbd07791d99915397ee108f71a962751e61ec7ad02;currentC70 a7ec81b5fbadce271f07bd3749cc7fcdcfcb57a0da2a90eb070dc555729c7d75. Versionedsnapshots+tworesultJSONs kept. Localmainnutrifitdb_java untouched.
-ActualfreshAivenSELECT-onlyviaFoodQualityReadOnly:24tables82/30/383,30imageURLs,TLSv1.3VERIFY_IDENTITY,CApin+hostnameverified;catalogrowsmatchprivatebackup.0persistentwrites. No user/paymentdataqueried.
-BackupcatalogJSON/DDL/SQLexists outsideGit at D:/NutriFit-backups/food-quality-20261019/backup-before-images;SHA/JSON/readcomparisonPASS. NotfullDBbackup,restoreNOTrehearsed. No currentproductionready claim.

## Actual NEW verification

-FinalJDK21.0.12/Maven3.9.16cleanpackagePASS114JUnit,0fail/error/skip,32.595s,end22:28:23+07. NutritionCalculator/RealCatalogBenchmark/cohort/CSRF/save/Premium/history/image tests retained. InitialobsoleteF018-missingassertionfailed thenupdatedtospecificINMU974boiledregression;coverageincreased.
-Python32PASS0skip withUSDA_SOURCE_ARCHIVE/MEXT_SOURCE_ARCHIVE/THAI_SOURCE_CACHE. Negativeunit/state/mapping/amount/source/production-holdchecksand30WebPdecode/hashPASS.59pinnedfilesandtechnicalvalidatorPASS;baselineSQL/JSONvalidator82/30/383PASS.
-JspC Tomcat10.1.61/JDK21compile0errors.14JSfixturePASSviaPythonChrome subprocesswait;firstPowerShellGUIlaunchreturnedearly/emptyDOM,notappfailure. NotauthenticatedproductionE2E,notDockerbuild.
-432cases/dataset;samealgorithm/targets/history/gatepolicies. Actualmeanabskcalerror Aguard598.575/B70sources468.238/C167.395. Ccheckpoint161.362wasbetterthannewC167.395;reportthishonestly. FeasibleA200/B236/C336of432;avoidable>20%gapwhenfeasible0allguarded. No scorer/runtime nutritionchange thiscontinuation.
-Only runtimeeditHealthServlet:validated40hexRENDER_GIT_COMMITorunknown,no-store;2regressiontests. RenderofficialdefaultenvdocsverifiedvariableavailableDocker runtime. No secrets/config/Auth/Payment/Workout/Chatbot change.

## Release and remaining work

- release/ containsA_baseline,version/checksum manifest and NONEXECUTABLEcandidateplan:66foodupdates+18newFood/30Recipe/224links. QualifiedB/C and productionSQL deliberately NOTemitted while gatesfail;--productionrefusaltestedwithoutoutputmutation.
- STAGING_READYtechnicalonly;PRODUCTION_READYfalse;DEPLOYEDnewdatafalse;writepermissionfalse. ImportantunapprovedproxiesF024/F032/F075/F076/F082,47missing12foods,sixlarge-solidportions,oldrecipecooking/sourcevariance,fullbackuprestoretest,qualifiedmanifest/assetsrelease andseparatego-liveapproval remain.
- Nextoperationsinthiscontinuation:finalstatic/secrets/scopereview,commitlogicalgroups,pushnonforce,verifyremoteandobserveRenderhealthrevision;storeactualSHAs/handoffoutsideGit. Ifalreadypushed,inspectcurrentGit/privatehandoffratherthanduplicatingwork.
- Subsequentdatatask:resolveconcreteinputslistedremaining-food-evidence.md,notgenericmissing-dataexcuse. Do notshrinkportionsjusttoboostbenchmark,fillmissingzero,pretendCqualifiedorimportpartial30new. Holdproductionuntilallgatesandexplicitapproval.

Reproduction/security/commands: ../../database/tools/food_quality/README.md. Fullartifacts andlimitations: final-data-quality-report.md andproduction-readiness.md.

Line-ending reproducibility: .gitattributes pins staging/tools LF and WebP binary, preserves the legacy canonical JSON CRLF checksum419fa5e4...; scorer source stays LF. Git checkout filters were verified to reproduce the exact current baseline/service bytes without modifying seed/schema.
