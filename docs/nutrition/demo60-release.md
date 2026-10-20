# Nutrition60 — bàn giao bản demo và đổi riêng từng món

Bản2026-10-20 theo quyết định chủ dự án: dữ liệu tham khảo có ước tính được chấp nhận, không phải phần mềm y tế. **Đã được chủ dự án phê duyệt đúng manifest và đã go-live Aiven thành công.** Xem [biên bản](demo60-go-live.json). Manifest cuối là `database/staging/food-quality-v1/release/final-manifest.json`; phê duyệt đúng SHA256 một lần đã được nhận và thực thi; giữ nguyên manifest bất biến.

## Dữ liệu và ảnh

-100Food/60Recipe/607Ingredient,20món mỗiBREAKFAST/LUNCH/DINNER. Mọi món mặc định1.00suất; không tự co giãn để khớp calories.
-500giá trị:236MATCHED/161CALCULATED/103ESTIMATED;35Food có ít nhất một giá trị ước tính.12Food dùng toàn bộ vector ước tính có mô tả công thức/trạng thái;25giá trị thuộc5proxy giống/quy trình/công thức khác được gắnESTIMATED thay vì coi khớp nguyên liệu;18giá trị khác là ước tính/assumedzero từ nguồn. Không có VERIFIED hay tuyên bố xét nghiệm.
-Ưu tiên dữ liệu USDA/MEXT/INMU đã thu thập; nguồn, trạng thái sống/chín,100g phần ăn được, cách tính availablecarbs và độ tin cậy được giữ trong demo-provenance.47MISSING trong audit nguồn nghiêm ngặt vẫn được giữ; chúng không được đổi thành dữ liệu phân tích đã biết. Release dùng phép ước tính riêng có giải thích, không biến null thành0.
-R044/R048/R050/R054/R057/R060 được rà soát từng thành phần là bữa đầy đủ cỡ lớn, có món kèm/rau nhiều nước. Không giảm gram để cải thiện benchmark; chưa cân đo thực bếp. Hướng dẫn giữ lại lượng nước/sốt/dầu đã kê, không nhân thêm hệ số sống/chín cho nguyên liệu đã chín.
-30WebP mới đã duyệt,800x450,2.124.668bytes, mapping theo từng món; giữ nguyên byte của30ảnh cũ. Ảnh AI minh họa, không phải bằng chứng suất đã cân. JSP dùng URL tương đối context và fallback an toàn.

## Đổi riêng từng món

POST `/nutrition/recommendations`,action=swap,mealType và token/CSRF. Server tự chọn recipe/nutrition/servings; không nhận nutrient/recipeId từ client. Chỉ cùng meal_type, active,1.00suất, không trùng món đang có. Free và Premium hết hạn không đọc sở thích; Premium loại DISLIKE, LIKE là ưu tiên mềm.

Ưu tiên calories trong15%, rồi25%, tối đa35%; tương đồng cả5giá trị có mẫu số sàn1kcal/10gprotein/15gcarbs/5gfat/3gfiber để tránh chia0. Không tăng fat quá max(10g,50%fat cũ). Xét tổng dự kiến thực tế gồm snapshot nhật ký: chênh năng lượng không xấu hơn max(chênh cũ,15%target)+3%target; điểm chất lượng toàn ngày không xấu hơn.06. Novelty chỉ trong cùng tầng năng lượng và biên điểm.08; hết lựa chọn thì giữ nguyên và báo rõ, không buộc món xấu để tránh lặp.

Swap chỉ sửa draft30phút trong session, không ghi mealentries. Session lock bao trùm swap/save; đổi draft thay nonce để tab cũ không lưu nhầm thực đơn. CSRF/owner/date/expiry/attempted/saved đều kiểm tra. Lưu sau swap vẫn tính lại bằng NutritionCalculator và giữ transaction/rollback/chống double-submit. Lỗi phản hồi chưa rõ thì UI yêu cầu tải lại, không tự retry.

AJAX cập nhật riêng một thẻ, ảnh/tên/5nutrient, tổng/menu-target/projectedday/warnings và token; hai thẻ khác và nhật ký giữ nguyên. BigDecimal gốc ở backend; HALF_UP số nguyên chỉ để hiển thị, không dùng số đã làm tròn tính tổng. Không có ô khẩu phần, không Gemini.

## Kết quả thực tế

- JDK21.0.12/Maven3.9.16 `clean package`:127JUnit,0fail/error/skip,BUILD SUCCESS. Sau sửa blockJSP, đóng gói WAR lại và JspC0errors. JspC có thể exit0 khi lỗi nên runner kiểm tra cả nội dung errorcount.
- Python38PASS/0skip, nguồn cache USDA/MEXT/Thai thật. Chrome headless14legacy+23swap assertionsPASS. Đây là browserfixture/HTTPdouble, chưa phải đăng nhậpE2E production.
-432case/dataset: A30hiện tại meanabsKcalError598.575, B30nguồn/ước tính468.238, C60167.395; feasiblewithin10%target200/236/336.0case lệch>20% khi có tổ hợp trong10%. CmeanP125.190g/C248.803g/F52.887g/fiber35.753g; là thống kê cohort, không phải mục tiêu bắt buộc cho mọi người.
-18scenario swap mỗi catalog,6lần thử tối đa:30món95swap,max22.78%chênh;60món91swap,max14.90%; không scenario nào hoàn toàn thiếu món thay. Hết lựa chọn an toàn được trả unchanged. Không đảm bảo mọi món hay mọi mục tiêu đều có phương án tương đương.
-Local24bảng từ DDL backup Aiven, restore82/30/383 đúng từng giá trị/PK/Unicode. Migration thêm18/30/224 và cập nhật66Food;100/60/607,20/bữa,60ảnh/JDBCcalculator đúng. Injectlỗi sau99writes rollback toàn bộ; chạy lần hai0writes; conflict bị từ chối; mọi bảng ngoài catalog và recipeID/snapshot1.32suất cũ giữ nguyên.
-Backup riêng tại `D:/NutriFit-backups/food-quality-20261020/demo60-before`: catalogdataJSON+24DDL+SHA. Không có dữ liệu tài khoản/giao dịch và không phải full-data backup. Đã phục hồi thực tế vào `nutrifit_fq_demo60_20261020_v2_test`. Thử đầu phát hiện ANSI_QUOTES của SHOWCREATE, sau đó validator cột per_100g quá chặt; đã sửa và tiếp tục chỉ khi đủ24bảng đều trống. DB thử ban đầu `nutrifit_fq_demo60_20261020_test` còn trống, được giữ nguyên, khôngDROP.

## Tái tạo và triển khai

Trên Integration checkout, dùng JDK21/Maven3.9.16; `mvn clean package`. Python dependencies trong database/tools/food_quality/requirements.txt. Chạy unittest với USDA_SOURCE_ARCHIVE/MEXT_SOURCE_ARCHIVE/THAI_SOURCE_CACHE trỏ nguồn cache công khai; source thiếu thì test nguồn SKIP và không được báo đủPASS. Dùng verify_web.py với JDK/Tomcat/Chrome đã cài, sau đó finalize_demo_release.py.

PowerShell công cụ (không có password trong lệnh):

```powershell
# Chỉ đọc Aiven, tạo thư mục backup MỚI, không ghi dữ liệu production
./database/tools/food_quality/Invoke-DemoCatalogRelease.ps1 -Mode Backup -BackupDirectory 'D:\NutriFit-backups\food-quality-NEW\demo60-before'
# Restore vào database local MỚI có tên phù hợp, không tái tạo DB đang có
./database/tools/food_quality/Invoke-DemoCatalogRelease.ps1 -Mode LocalTrial -BackupDirectory 'D:\NutriFit-backups\food-quality-20261020\demo60-before' -LocalDatabase nutrifit_fq_demo60_NEW_test
# CHỈ SAU khi chủ dự án phê duyệt chính xác SHA256 trong final-manifest
./database/tools/food_quality/Invoke-DemoCatalogRelease.ps1 -Mode ApplyAiven -BackupDirectory 'D:\NutriFit-backups\food-quality-20261020\demo60-before' -GoLiveApprovedManifest '<APPROVED_SHA256>'
```

Mặc định tự nạp privateENV ngoài repository. Không đổi tên file, không hỏi/ghi password. Apply kiểm tra SHA manifest/tất cả file/backup đã restore, TLS/hostname/CA,24bảng/InnoDB/khôngtrigger, exactbefore hoặc alreadyafter, khóa và DML trong một transaction. Nếu có dữ liệu lạ, dừng/rollback; khôngDELETE/DROP/TRUNCATE/force hoặc tự retry. Rerun alreadyafter được verify và trả0writes. Không chạy migration từ Docker/Render startup.

Đã COMMIT và SELECT hậu kiểm100/60/607,20/bữa,60ảnh/calculator/FK hợp lệ; checksum21bảng ngoài catalog và schema không đổi. ID cũ,30recipe/383ingredient cũ và snapshot nhật ký giữ nguyên. Lần chạy thứ haiALREADY_APPLIED,0writes. Nếu kết quả commit không rõ, chỉ điều tra read-only. Backup restore wholesale chỉ dành local trống; không phủ lên users hoặc nhật ký mới trên production. Nếu phải hoàn nguyên sau có người dùng ghi mới, lập phương án catalog-only giữ mọi khóa ngoại/ID và xin phê duyệt riêng.

Code/assets có thể deploy trước dữ liệu: swap hoạt động ngay với30món Aiven hiện tại, tự dùng60món sau go-live. Health200 không đủ chứng minh revision; đối chiếu `/nutrifit/health` trườngrevision với commit đãpush. Không thay đổiAuth/Payment/Workout/Onboarding/schema/seed gốc hoặc lịch sử.
