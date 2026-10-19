# Food Data Quality continuation — PARTIAL

Tiếp nối checkpoint `f04b2da`, ngày2026-10-19, checkout `D:/Web/NutriFit-Integration`, nhánh `deploy/render-aiven-brevo`. Các số111JUnit/59Food/9recipe/0ảnh mới của checkpoint là kết quả cũ; báo cáo này tách phần thực sự bổ sung. Chủ dự án vẫn giữ lệnh **không ghi production Aiven**.

## A. Nutrient evidence — PARTIAL

- Bổ sung thực sự **51/98 giá trị MISSING** trên12 Food so với checkpoint; còn **47 MISSING trong12 Food**. Food đủ năm giá trị nguồn/quy đổi tăng59→**70/82**.
- 410facts hiện gồm **MATCHED209 / CALCULATED135 / ESTIMATED19 / MISSING47 / VERIFIED0**. Không hạ tiêu chuẩn VERIFIED, không biến missing/Tr thành0. Số Food VERIFIED toàn bộ vẫn0.
- Tái sử dụng cache USDA/MEXT/NIN cũ đã kiểm SHA, không tải lại. Thêm19 trang INMU Thai FCD chính thức có URL/SHA/identity/scientific-name/100g edible và từng derivation/sample/update/footnote. Cache hiện59 file nguồn được pin; parser không chạy JavaScript của nguồn.
- INMU carbohydrate khả dụng được dùng trực tiếp, không trừ fiber lần nữa. Fiber0 do nguồn ghi assumed-zero giữ ESTIMATED. Proxy chả lụa/mắm có LOW confidence, không phải nhãn sản phẩm Việt đã duyệt.
- USDA168374 bổ sung F082 heo xay cooked pan-broiled84%lean/16%fat như proxy cùng loại/cùng trạng thái, ghi rõ khác tỷ lệ mỡ/cách nướng; không gọi là công thức bún chả đã xác minh.
- Không lấy giá trị nhãn từ trang tổng hợp. Trang VISSAN Giò Lụa chỉ cung cấp thành phần, chưa đủ năm nutrient để dùng làm nhãn. Tra cứu thêm vannamei trên INMU trả503, không bypass/lặp liên tục.

[Hồ sơ đủ82 Food](food-data-verification.md), [delta từng giá trị](../../database/staging/food-quality-v1/missing-resolution.json), [lý do cụ thể còn thiếu](remaining-food-evidence.md).

## B. Công thức/khẩu phần — PARTIAL

- 30 món cũ/383links đã được audit ở checkpoint. Lần này số công thức đủ nguồn để tính so sánh tăng **9→18/30**, bằng NutritionCalculator hiện hành;12 còn lại giữ kết quả nguồn null. Bảng trước/sau năm nutrient và delta có trong [recipe-quality-audit.md](recipe-quality-audit.md), không lấy số cũ để che missing.
- Không sửa recipe ID/tên/meal_type/base_servings,383 gram cũ, schema, canonical JSON/SQL, Onboarding/BMR/TDEE hoặc lịch sử mealentries. Source cut/moisture/broth/oil khác nhau chưa tự động được chấp thuận chỉ vì numeric đầy đủ.
- Đọc lại đủ30 thiết kế R031–R060; không tự giảm gram để làm benchmark đẹp. Mỗi món có bảng trạng thái nguyên liệu, khối lượng ăn được, nước kê riêng, target khối lượng phục vụ, cách giữ sốt/dầu, phương pháp dinh dưỡng và bất định. Target là giả định thiết kế, không phải cân thực tế; measured final mass/yield/evaporation vẫn null khi chưa đo.
- R047/R053 đều có200g nước canh kê riêng và cơm ăn kèm: không coi tổng>800g là sai. **24/30** qua review phương pháp ở STAGING với giả định minh bạch; sáu suất đặc lớn R044/R048/R050/R054/R057/R060 vẫn cần review đĩa ăn thực tế. Không bắt buộc mỗi món phải được đo trong phòng thí nghiệm; chưa được dùng review phương pháp thay thế qualification toàn món.
- **0 món mới được phê duyệt ghi production**; không import24 món riêng để đạt gần60. Xem [review khối lượng](../../database/staging/food-quality-v1/recipe-portion-review.json) và [catalog staging](catalog-expansion-staging.md).

## C. Ảnh mới — SUCCESS ở staging, chưa phát hành runtime

- **30/30** ảnh minh họa riêng tạo bằng built-in image_gen, một call/prompt mỗi món. WebP800×450,30hash khác nhau, tổng **2.124.668bytes**, giải mã và kiểm trực quan toàn bộ. Giữ nguyên30 ảnh cũ.
- Có mã R031–R060 ổn định, tên file/alt, prompt đầy đủ, source artifact hash, hồ sơ quyền tạo, ngày và disclosure **ảnh minh họa AI, không phải ảnh chụp suất đã cân đo**. Ảnh không chứng minh định lượng/clinical quality.
- Đã xem năm contact sheets; R054 được xem đầy đủ lại để xác nhận bông cải ở phía phải, không cần thay ảnh. Không có ảnh Google/watermark/ảnh món khác dùng cho đủ số lượng.
- Lưu tại `database/staging/food-quality-v1/images/`, tách khỏi Docker/WAR khi món chưa qualification. Catalog image_url mới vẫn null, fallback giữ nguyên; không tự kích hoạt ảnh mới trên Aiven. Đây là lựa chọn staging có chủ đích thay vì cho asset chưa phát hành vào src/main.

[Toàn bộ prompts/quyền/hash/mapping](../../database/staging/food-quality-v1/image-generation-jobs.json).

## D. Qualification/benchmark/migration — PARTIAL

Catalog A production baseline vẫn82Food/30recipes/383links. B thăm dò70Food đủ số nguồn +12 Food baseline ước tính còn thiếu; C thăm dò có **100Food/60recipes/607links,20món mỗi bữa**. **Qualified B/C chưa được tạo** vì gates chưa đạt. Không đổi nhãn thăm dò thành qualified.

Cùng432 tình huống, cùng target từ OnboardingService nguyên bản, cùng chính sách gói/sở thích, lịch sử A và thuật toán cho A_guarded/B/C. Không đổi scorer lần này. A_before là kết quả thực tế cũ, không giả lập lại bằng code mới.

| Dataset | Mean kcal error | Feasible trong10% | Lệch>20% dù feasible |
|---|---:|---:|---:|
| A trước guard, checkpoint cũ | 605.949 | 200/432 | 5 |
| A guarded, chạy lại | 598.575 | 200/432 | 0 |
| B70 nguồn thăm dò | 468.238 | 236/432 | 0 |
| C60 thiết kế thăm dò | 167.395 | 336/432 | 0 |

C cũ ở checkpoint khoảng161.362kcal error, lần này167.395: **không cải thiện so với C cũ**, dù vẫn thấp hơn A/B. Còn96/432 trường hợp không có tổ hợp trong10% target. Không ép servings hay target để tạo thành tích. [Bảng đầy đủ](data-quality-benchmark.md) có mean/median/P90 calorie/relative error, năm nutrient, tỷ lệ macro, fiber gap, số thiếu món, diversity và runtime; CSV/summary có checksum, tổng hợp lại được bằng summarize_benchmarks.py. Benchmark không chứng minh đúng nutrient/khẩu phần thực tế.

### Local — SUCCESS cho cơ chế test

- SELECT-only xác minh database staging hiện có trước ghi. Không tạo/xóa/rebuild/seed lại database; giữ sáu bảng test, không giả định nó là clone24 bảng. Driver báo version26.7.0, không tự nhận8.4.
- Hai delta có version/hash đã cập nhật **10 rồi1 Food**, **0 Food/Recipe/Ingredient mới**. Các report và snapshot từng bước được giữ riêng để tái lập. Không ghi local nutrifitdb_java.
- Injected failure trước COMMIT chứng minh rollback; re-run mỗi delta0writes; conflict bị từ chối/rollback; users/mealplans/mealentries fixture hash không đổi, snapshot1.32 suất cũ giữ nguyên.
- 30 image URLs thử theo checked generated-ID/name mapping, đọc bằng JdbcRecipeReadAdapter rồi rollback toàn bộ. URL mới active cuối cùng0; không biến staging asset thành production URL.
- NutritionCalculator/JDBC/FK/metadata/counts đều khớp C cuối. Đây là integration với MySQL local thật, không phải production E2E. LocalQualityDelta chỉ cho đúng target test, LOCAL config trong JDBC memory, từ chối trạng thái lạ và không có CREATE/DROP/seed.

### Aiven — SELECT-only, chưa triển khai dữ liệu

Lần kiểm tra mới trong continuation: **24tables /82Food /30Recipe /383links /30imageURLs**, TLSv1.3 với **VERIFY_IDENTITY**, CA pin và hostname verification. Tất cả hàng catalog khớp snapshot riêng đã sao lưu;0persistent writes. Không đọc/ghi tài khoản hoặc giao dịch để test.

Backup catalog JSON/DDL/SQL ngoài Git vẫn tồn tại, hash và JSON đối chiếu lại PASS. **Không có full-database backup mới hoặc restore rehearsal**; không gọi SHA hợp lệ là đã phục hồi thử. [Read-only evidence](../../database/staging/food-quality-v1/aiven-readonly-current.json).

### Bộ bàn giao và trạng thái

[production-readiness.md](production-readiness.md) mô tả gates, backup/recovery, thứ tự assets→data, pre/post/conflict checks. `release/` có version/source checksum, A baseline, diff/plan dự kiến **UPDATE66Food + INSERT18Food/30Recipe/224links** khi đủ điều kiện; đây là plan chưa được phép thực thi, không phải import đã chạy. Không phát hành SQL production cho bộ dữ liệu chưa qualified. `prepare_release.py --production` bị từ chối trước khi sửa output khi còn gate thiếu; có regression test cho điều này.

**STAGING_READY:** cơ chế nội bộ PASS. **PRODUCTION_READY:** FALSE. **DEPLOYED dữ liệu mới:** FALSE. Quyền ghi Aiven hiện **chưa có**; lệnh giữ staging vẫn còn hiệu lực. Chưa xin go-live vì dữ liệu chưa đủ điều kiện.

## Engineering và triển khai

- Final JDK21.0.12/Maven3.9.16 `clean package`: **114 JUnit PASS,0failure/error/skipped,32.595s**, kết thúc2026-10-19T22:28:23+07. Bao gồm NutritionCalculator/RealCatalogBenchmark/cohort/Free-Premium-expired/preferences/save transaction/CSRF/Auth boundary/history/image tests hiện có và nguồn/revision tests mới.
- **32 Python PASS,0skip** với USDA/MEXT/THAI_SOURCE_CACHE cấu hình thật; test âm nguồn/đơn vị/negative/raw-cooked/duplicate/grams/missing và production-hold, giải mã30 ảnh. Validator70nguồn/100-60-607 và59cachefile PASS; canonical seed validator82/30/383 PASS.
- Tomcat10.1.61/JDK21 JspC **0errors**,14JavaScriptfixturechecks PASS bằng Chrome headless. PowerShell gọi GUI Chrome trả sớm trong lần đầu; chạy subprocess chờ kết thúc mới kiểm DOM và PASS, không coi file trống là app regression.
- Một focused run ban đầu FAIL assertion cũ F018-phải-missing. Đã cập nhật đúng bằng chứng INMU974 boiled-belly, thêm regression cụ thể; không xóa coverage. Guard SHA của local tool cũ cũng đã dừng trước kết nối khi provenance đổi; dùng delta snapshot/version rõ ràng, không bypass guard.
- Runtime chỉ thêm revision đã kiểm40hex từ RENDER_GIT_COMMIT vào HealthServlet và no-store; giá trị sai/missing trả unknown, không dump env. [Render documented variable](https://render.com/docs/environment-variables). Không đổi thuật toán, Auth/Payment/Workout/Chatbot hay database schema. Hai regression tests revision PASS.
- Code/staging sẽ commit theo nhóm logic và push đúng origin/deploy/render-aiven-brevo sau static/secrets review; SHA, remote và deployment sau push được ghi ở checkpoint/bàn giao cuối. Báo cáo tại mốc lập này không tự nhận Render đã chạy revision mới. Health200 đơn thuần không đủ; cần quan sát SHA mới, không thay secrets/config cloud.
- Không chạy Docker build hay authenticated production E2E trong continuation. Ảnh mới không nằm trong WAR, không sửa Dockerfile/pom/schema/seed. git diff --check/secrets/scope được kiểm trước commit.

## Kết luận

**A PARTIAL; B PARTIAL; C SUCCESS ở staging; D PARTIAL; toàn nhiệm vụ PARTIAL.** Đã bổ sung có nguồn, có review và kiểm thử đáng kể, không chỉ đếm đủ60. Phần còn thiếu cụ thể:47 nutrient/12Food theo remaining-food-evidence.md; proxy sản phẩm/nồng độ/giống/tỷ lệ mỡ; sáu suất đặc lớn; signoff cooking của món cũ; final qualified B/C/production SQL; full backup/restore rehearsal và xác nhận manifest go-live. Giữ production nguyên trạng cho tới khi các điều kiện này được đáp ứng.

Line-ending reproducibility: .gitattributes pins staging/tools LF and WebP binary, preserves the legacy canonical JSON CRLF checksum419fa5e4...; scorer source stays LF. Git checkout filters were verified to reproduce the exact current baseline/service bytes without modifying seed/schema.
