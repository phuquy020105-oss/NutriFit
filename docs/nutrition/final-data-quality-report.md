# Food Data Quality — educational60release

Tiếp tục từ0cfccdd theo quyết định mới2026-10-20. Đã hoàn thiện bộ100Food/60Recipe/607Ingredient và swap một món. Tóm tắt chi tiết, nguồn, phương pháp ước tính, benchmark, localrestore/migration, test và lệnh tái tạo ở [demo60-release.md](demo60-release.md).

-500facts:236MATCHED/161CALCULATED/103ESTIMATED,35foods có estimate;12wholefood vectors được mô tả giả định, không giả là xét nghiệm. Giữ strictsource47MISSING audit.
-30món mới10/bữa cùng30ảnhWebP đãduyệt, giữ nguyên30món/ảnh cũ, không giảmgram làm đẹpbenchmark.
-127JUnit/38Python/37JavaScriptchecks/JSP0errors/MavenBUILD SUCCESS; local24tablesbackuprestore exact,rollback/idempotency0writes/conflict/FK/stableIDs/60JDBCcalculator/snapshotPASS.
-432cohort: meanabsKcalError598.575→167.395; feasible10%200→336;0avoidable>20%gap. Swap thực tế30/60mónPASS,5nutrient và projectedjournal guards.
-PRODUCTION_READY được đóng dấu trong final-manifest sau các bước kiểm tra. Code/assets được commit/push và revision Render được báo ở handoff cuối. **Dữ liệu Aiven vẫn82/30/383; chưa productionwrite.** Chỉ go-live sau phê duyệt một lần đúng SHA256 manifest cuối.

Các báo cáo thăm dò/candidateplan cũ được giữ để truy vết, không thay thế finalmanifest hiện hành. Không thay đổiAuth/Payment/Workout/Onboarding/schema.sql/seed gốc hoặc lịch sử. Chưa authenticatedE2E production; healthrevision và asset checks không thay cho xác minh tài khoản đăng nhập.
