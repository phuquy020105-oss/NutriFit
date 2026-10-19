# Báo cáo Food Data Quality — PARTIAL

Mốc kiểm chứng: 2026-10-19, checkout `D:/Web/NutriFit-Integration`, nhánh `deploy/render-aiven-brevo`.

**Quyết định của chủ dự án: chưa có nhãn/công thức chuẩn cho các thành phẩm còn thiếu; giữ staging, không ghi Aiven.** Không biến kết quả benchmark tốt thành phê duyệt dữ liệu. Các giai đoạn dưới đây đều PARTIAL; kỹ thuật thử nghiệm local và các kiểm tra đã chạy PASS trong phạm vi nêu rõ.

## Giai đoạn 1 — PARTIAL: truy xuất nguồn, chưa xác minh toàn bộ

- Đã lập hồ sơ đủ82 Food và410 nutrient.59 Food có đủ năm giá trị nguồn/quy đổi;23 chưa đủ. Không có Food VERIFIED toàn bộ.
- Trạng thái410 nutrient: MATCHED175, CALCULATED120, ESTIMATED17, MISSING98, VERIFIED0.312 giá trị có dữ liệu nguồn/quy đổi, trong đó17 vẫn do nguồn ước tính; không gọi295 giá trị MATCHED/CALCULATED là đo kiểm trực tiếp.
- Nguồn chính: USDA SR Legacy04/2018 chính thức (7.793 Food/644.125 nutrient rows); MEXT English2015 cập nhật2017-12-27 (2.191 Food); tra cứu NIN công khai100g phần ăn được và38 truy vấn có checksum. FAO hỗ trợ phương pháp carbohydrate/yield/retention. Hai workbook SMILING trả403, không được coi là đã đọc.
- Giữ nguyên source row/cell IDs, raw text, đơn vị, nguyên liệu sống/chín, phần ăn được, ngày và SHA. Carbs khả dụng được tính rõ total carbohydrate trừ fiber cùng record, không ghép nguồn hoặc tự sửa calories bằng4/4/9. Null/Tr/estimated zero không bị biến thành số0 đã xác minh.
- Chả lụa, mắm ruốc/mắm tôm, hành phi, nước dùng và riêu cua còn cần nhãn/công thức định danh. Khác biệt cut/loài, nước, chất xơ và cooking vẫn được ghi; không âm thầm thay bằng thực phẩm khác.

Chi tiết đủ82 Food và từng nutrient: [food-data-verification.md](food-data-verification.md), [provenance](../../database/staging/food-quality-v1/food-provenance.json).

## Giai đoạn 2 — PARTIAL: audit30, chưa duyệt sửa công thức

- Đã kiểm tra30 recipes/383 liên kết và tính baseline bằng NutritionCalculator hiện hành, BigDecimal, đúng1.00 suất.9 công thức đủ nguồn để tính so sánh: R003/R012/R017/R018/R019/R024/R025/R027/R030;21 công thức còn thiếu được ghi null.
- Không sửa tên/loại bữa/base_servings/383 định lượng, canonical nutrient, seed SQL hoặc snapshot lịch sử. Không có công thức nào được chứng nhận toàn bộ yield/retention/dầu hấp thu bằng phép cân thực tế.
- Bảng trước/sau đủ năm chỉ số và delta của từng recipe có trong [recipe-quality-audit.md](recipe-quality-audit.md) và JSON audit. Không dùng số nguồn thiếu hoặc giá trị cũ để giả lập kết quả sau đã xác minh.
- B thăm dò thay59 Food đủ số nguồn;55 Food thực sự khác baseline,4 tương đương.23 Food chưa đủ vẫn là ước tính cũ, được đánh dấu rõ. B không phải catalog đã VERIFIED.

## Giai đoạn 3 — PARTIAL: đủ thiết kế staging, chưa đủ điều kiện production

- Đã có đúng30 thiết kế R031–R060 (10 sáng/10 trưa/10 tối), mỗi món1.00 suất,18 Food mới có nguồn và224 liên kết mới. Catalog C thăm dò có100 Food/60 recipes/607 liên kết,20 món mỗi bữa.
- Số món mới được duyệt production: **0**. Các món là thiết kế khẩu phần của NutriFit, chưa phải công thức được cân/kiểm nghiệm.8 món có khối lượng nguyên liệu kê trên800g cần review: R044/R047/R048/R050/R053/R054/R057/R060. Khối lượng kê khác khối lượng món sau nấu.
- Số ảnh mới đã hoàn thành: **0/30**. Có fallback trung thực; không dùng ảnh sai món. Giữ nguyên toàn bộ ảnh/mapping cũ30 món. Ảnh mới chờ công thức/khẩu phần ổn định và kiểm tra quyền sử dụng.
- C không được đưa vào seed chính hoặc WAR/Docker runtime. Không có60 recipes mới được ghi Aiven.

Danh sách món, số liệu và hạn chế: [catalog-expansion-staging.md](catalog-expansion-staging.md).

## Giai đoạn 4 — PARTIAL: benchmark và thử cơ chế local PASS, production giữ nguyên

Mỗi dataset432 trường hợp:6 hồ sơ người lớn,3 mức hoạt động,3 mục tiêu,4 trạng thái gói/sở thích,2 trạng thái nhật ký. Target lấy từ OnboardingService nguyên bản qua capture DAO trong test, không sao chép BMR/TDEE. A/B/C dùng cùng thuật toán và cùng snapshot lịch sử. A trước guard lưu riêng.

| Chỉ số trung bình | A trước guard | A sau guard | B thăm dò | C thăm dò |
|---|---:|---:|---:|---:|
| Kcal | 1628.890 | 1636.264 | 1679.495 | 2077.562 |
| Sai lệch tuyệt đối kcal | 605.949 | 598.575 | 556.847 | 161.362 |
| Protein g | 94.260 | 93.714 | 94.895 | 125.508 |
| Carbs g | 190.347 | 190.578 | 191.701 | 247.144 |
| Fat g | 51.044 | 52.005 | 54.686 | 52.716 |
| Fiber g | 11.882 | 11.754 | 12.365 | 35.961 |
| Có tổ hợp trong10% target | 200/432 | 200/432 | 229/432 | 344/432 |
| Chọn lệch trên20% dù có tổ hợp trong10% | 5 | 0 | 0 | 0 |

Thay đổi runtime tối thiểu: nếu có tổ hợp đủ điều kiện trong10% mục tiêu, lựa chọn và gợi ý lại nằm trong15%, dùng nguyên trọng số/LIKE/DISLIKE. Nếu không có thì giữ fallback/cảnh báo. Không đổi servings, calories mục tiêu, Auth/Premium/CSRF hoặc lưu transaction. Fiber A giảm nhẹ sau guard; không tuyên bố mọi chỉ số đều cải thiện. C còn88/432 trường hợp không có tổ hợp trong10%; phần cải thiện chưa chứng minh được với khẩu phần thực tế.

[Benchmark đầy đủ](data-quality-benchmark.md) có median/P90, tỷ lệ macro, fiber gap, diversity, runtime và CSV từng trường hợp.

### MySQL local — PASS cơ chế, không phải phê duyệt dinh dưỡng

Đã tạo duy nhất database test riêng `nutrifit_fq_20261019_food_quality_test`, sáu bảng dẫn xuất từ schema, không phải clone24 bảng. Client báo phiên bản MySQL `26.7.0`; ghi đúng kết quả thực tế, không tự nhận8.4. Database local chính không bị sửa.

- C được áp dụng trong transaction: thêm18 Food/30 Recipe/224 liên kết, cập nhật55 Food ở database test.
- Cố ý lỗi sau99 lần ghi: rollback khôi phục hash toàn bộ catalog và lịch sử; AUTO_INCREMENT có thể có khoảng trống.
- Chạy thành công; lần hai0 insert/0 update, hash không đổi. Conflict bị từ chối và rollback; snapshot1.32 suất cũ giữ nguyên.
- Có100/60/607, khóa ngoại hợp lệ, active đúng, adapter đọc60 và tính bằng NutritionCalculator khớp JSON. Lần SELECT-only cuối khớp SHA hiện tại của C và metadata.
- Tool chỉ dùng LOCAL_DB_* và loopback3306, tên DB bắt buộc prefix/suffix test; từ chối ghi database có sẵn. Không DROP/cleanup. Schema DDL auto-commit được nêu rõ; rollback được kiểm tra cho migration DML.
- Database test được giữ để kiểm tra, có một fixture tài khoản vô hiệu hóa đăng nhập; không phải tài khoản hay session production.

Bằng chứng: [local-trial-result.json](../../database/staging/food-quality-v1/local-trial-result.json), [SELECT-only](../../database/staging/food-quality-v1/local-trial-readonly.json).

### Aiven và triển khai

Trong task chỉ đọc Aiven: lần audit xác nhận24 bảng,82 Food/30 Recipe/383 liên kết,30 image URLs, TLSv1.3 VERIFY_IDENTITY;410 giá trị và383 liên kết khớp canonical. Đây là snapshot tại thời điểm audit, không phải khẳng định database không thể thay đổi về sau. Không ghi Aiven hoặc sửa users/subscription/history. Backup catalog/DDL/SQL có SHA và roundtrip ở ngoài Git; chưa diễn tập restore và không gọi đây là backup đầy đủ database.

Theo quyết định chủ dự án, chưa áp dụng dữ liệu mới production. Còn thiếu phê duyệt nguồn/thành phẩm, cân khẩu phần, ảnh mới, production manifest/migrator được duyệt, backup/recovery rehearsal và kiểm tra lại trạng thái ngay trước mọi thao tác. Không chạy cloud migration để đạt số lượng60.

Đã push code guard lên đúng nhánh; staging/tools/docs bị loại khỏi Docker theo allowlist hiện hành. Sau push: health HTTP200/status ok; Nutrition không đăng nhập HTTP302 tới /nutrifit/login; ảnh banh-mi-trung.webp HTTP200 và SHA khớp local. Các kết nối HTTPS xác minh chứng chỉ thành công. Đây không phải authenticated E2E và không chứng minh commit mới đã chạy. Không có quyền dashboard/API Render được xác minh. GitHub commit status chỉ có Vercel failure, không có Render status; không sửa Vercel ngoài phạm vi. **Render deployment commit mới: UNVERIFIED.**

## Engineering — các kiểm tra đã PASS

- JDK21.0.12 + Maven3.9.16: `mvn -DargLine=-Xmx768m clean package`, **111 JUnit,0 failure/error/skipped, BUILD SUCCESS**,36.322s, kết thúc2026-10-19T21:07:25+07. Bao gồm RealCatalogBenchmarkTest, recommendation/save/CSRF/history và asset tests hiện có,5 audit tests và4 cohort tests mới. Test trong Maven không ghi MySQL production.
- Python: **20 PASS**, gồm6 test dùng archive chính thức khi USDA_SOURCE_ARCHIVE/MEXT_SOURCE_ARCHIVE được cấu hình;0 skipped trong lần thực tế. Nếu thiếu archive, test ghi SKIP, không được tính là đã kiểm archive.
- Cache nguồn:40 file khớp manifest/SHA, kiểm offline.
- Validator baseline: PASS82/30/383. Chỉ sửa checksum review-document đã đổi prose Free/Premium trong commit501e0fa; các guard dữ liệu/SQL/grams vẫn giữ.
- Tomcat10.1.61/JDK21 JspC: compile0 lỗi sau khi cung cấp đủ tomcat-juli/Ant classpath.
- Chrome headless UI fixture: **14 JavaScript checks PASS**. Đây không phải authenticated E2E hoặc load test.
- Local trial và ba kiểm tra từ chối target/host/database có sẵn PASS; javac tool standalone PASS. Không chạy Docker build trong task này.
- git diff --check và kiểm phạm vi/secrets/artifact PASS trước commit; LF/CRLF chỉ là cảnh báo Git.

### Phạm vi file và khả năng tái lập

Runtime chỉ sửa `MealRecommendationService.java`. Test sửa RealCatalog loader và thêm FoodDataQualityAuditTest/FoodQualityCohortBenchmarkTest. Thêm các extractor/provenance/reports/local-trial tools trong `database/tools/food_quality`, staging JSON/CSV/evidence và các báo cáo `docs/nutrition`. Validator chỉ đổi checksum tài liệu; .gitignore thêm Python bytecode.

Không sửa schema/pom/canonical catalog/ba seed SQL, NutritionCalculator/OnboardingService, Auth/Payment/Workout/Chatbot, historical snapshots, secrets hoặc30 ảnh cũ.

Cách chạy lại nguồn/audit/test/local trial: [README công cụ](../../database/tools/food_quality/README.md). Cache công khai có hash tại `D:/NutriFit-data-sources/20261019`; không phụ thuộc target tồn tại. Cấu hình và backup riêng tư không được commit.

Commit dữ liệu staging riêng: `0dd67b937b8c652cd3cfe292ee2b54ed151dbb0c`. Commit code/docs/tests: `55fde6519e00e29d2a4cbeeed5a30cc1099cf48b`. Cả hai đã push thành công lên origin/deploy/render-aiven-brevo; git ls-remote xác nhận đúng SHA55fde65, working tree sạch tại mốc đó. Bản cập nhật bàn giao tài liệu này được commit sau các kiểm tra remote/HTTP; SHA cuối cùng của nó được ghi trong phản hồi bàn giao và checkpoint riêng ngoài Git. Không force push.

## Kết luận và bước tiếp theo

**Toàn nhiệm vụ PARTIAL.** Engineering kiểm thử và local trial cơ chế PASS; bốn giai đoạn dữ liệu chưa đủ điều kiện SUCCESS. Không cần chạy lại import Aiven trong trạng thái hiện tại. Tiếp tục từ [checkpoint](data-quality-progress.md): thu thập nhãn/công thức thành phẩm, giải quyết98 nutrient thiếu, review8 khẩu phần lớn, cân/yield/retention và30 ảnh hợp lệ; sau đó mới benchmark qualified B/C và xem xét phê duyệt production riêng.
