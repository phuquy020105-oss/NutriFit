# Gợi ý thực đơn và phân quyền Nutrition

## Quyền truy cập

- Mọi tài khoản đã đăng nhập được ghi nhật ký hôm nay, xem lịch sử, tạo bản xem trước ba bữa, chỉnh khẩu phần và lưu thực đơn.
- Chỉ Premium còn hạn được đọc/quản lý sở thích và áp dụng cá nhân hóa LIKE/DISLIKE.
- Điều kiện Premium của Nutrition khớp PremiumAccessService: subscription_status = PREMIUM và premium_expires_at khác NULL, lớn hơn thời điểm hiện tại.
- Premium hết hạn sử dụng đường gợi ý Free, không đọc sở thích cũ.
- FeatureCatalog.NUTRITION_PREFERENCE_RECOMMEND mô tả **cá nhân hóa**, không phải quyền dùng gợi ý cơ bản. Hai feature sở thích vẫn yêu cầu Premium; không thay đổi các feature Workout.

## Luồng dữ liệu

1. GET /nutrition/recommendations lấy target_kcal hiện có từ userprofiles và danh sách Recipe hợp lệ qua RecipeReadPort. Không tính lại BMR/TDEE và không gọi Gemini.
2. Mỗi bữa chọn một Recipe đúng meal_type. Premium loại Recipe chứa Food ID DISLIKE, ưu tiên số nguyên liệu LIKE; tiếp theo ưu tiên độ gần mục tiêu calories sau điều chỉnh khẩu phần. Khẩu phần ban đầu hướng tới 1/3 mục tiêu ngày, giới hạn 0.25–4.00 để tránh phóng đại lượng ăn. Giao diện hiển thị chênh lệch thực tế; không hứa đạt mục tiêu tuyệt đối.
3. NutritionCalculator tính tất cả năm chỉ số từ nguyên liệu/base_servings, không nhân lại các giá trị đã làm tròn mỗi khẩu phần. Preview chưa ghi mealplans/mealentries.
4. POST action=preview có CSRF tính lại qua cùng Calculator khi chỉnh khẩu phần. Giao diện không tự tính calories bằng số thực JavaScript.
5. Bản xem trước được giữ ở session, gắn userId, ngày, nonce và thời hạn 30 phút. Trình duyệt chỉ gửi nonce và ba khẩu phần; recipe ID, ngày, userId và calories gửi thêm không được dùng.
6. POST action=save kiểm tra lại tài khoản, ngày, recipe active/meal_type, Premium thực tế và DISLIKE hiện tại. Ba món ghi trong **một Connection/transaction**. Lỗi bất kỳ món nào thì rollback; không xóa hoặc thay thế các món thủ công.
7. Nếu trùng Recipe trong cùng bữa, cộng khẩu phần theo quy tắc addMeal hiện tại và rescale snapshot cũ. Preview mô tả ba phần ăn được đề xuất; mục trùng có thể giữ dinh dưỡng snapshot cũ nếu Recipe đã được sửa từ khi ghi nhận.
8. Ngày thay đổi trong lúc lưu thì rollback. CSRF vẫn bắt buộc, response Nutrition không được cache.
9. Nonce đã lưu được redirect lại mà không ghi thêm. Nếu lần lưu đã bắt đầu nhưng kết quả commit không chắc chắn, cùng nonce không được tự gửi lại; người dùng kiểm tra nhật ký trước khi tạo gợi ý mới. Cơ chế chống lặp này nằm trong session, không phải khóa idempotency bền vững trong database.

## Khi không có gợi ý

Thiếu target_kcal hoặc thiếu Recipe phù hợp cho một bữa trả thông báo an toàn. Không tự tạo Recipe, không bỏ DISLIKE để đủ ba món và không ghi nhật ký một phần. LIKE/DISLIKE đối chiếu Food ID hiện có; không suy luận thành phần ẩn hoặc bảo đảm tránh dị ứng.

## Mã liên quan

- MealRecommendationService: chọn món, khẩu phần, đọc trạng thái Premium và làm mới preview.
- MealPlannerService.saveSuggestion: transaction lưu ba bữa, giữ hành vi snapshot/gộp món đã có.
- FoodPreferenceService: kiểm tra Premium trước mọi thao tác sở thích, kể cả gọi trực tiếp.
- NutritionUserReadDAO: đọc Profile và trạng thái thuê bao; không sửa Payment.
- MealRecommendationsServlet: preview JSON, CSRF, session/nonce, chống lặp và redirect sau lưu.
- Các JSP Nutrition, nutrition.js và nutrition.css: nút gợi ý, ba món, khẩu phần, năm chỉ số, tổng ngày và chênh lệch mục tiêu.
- RecipeReadPort, DaySummary và NutritionFacts giữ nguyên hợp đồng tích hợp.

## Kiểm chứng local

JDK 21 và Maven 3.9.16:

~~~cmd
cd /d D:\Web\NutriFit-Integration
mvn -B test
mvn -B package
git diff --check
~~~

Các test sử dụng DAO/JDBC/HTTP doubles, không mở DatabaseConfig và không dùng database chính:

- MealRecommendationServiceTest: Free, Premium, LIKE/DISLIKE, thiếu target, thiếu món, hết hạn, sai tài khoản/ngày, khẩu phần/overflow, tổng dinh dưỡng.
- FoodPreferenceServiceTest và NutritionUserReadDAOTest: chặn Free, LIKE/DISLIKE/xóa, Food inactive, điều kiện expiry và hợp đồng FeatureCatalog.
- MealSuggestionSaveTest: transaction ba món, lỗi món thứ hai/thứ ba rollback, giữ món thủ công, gộp snapshot và kiểm tra lại quyền/sở thích.
- NutritionRecommendationsHttpTest: preview không ghi, POST trực tiếp, CSRF, phân tách tài khoản, preview JSON, stale nonce và chống replay.
- Bộ test MealPlanner/NutritionCalculator/CSRF hiện có tiếp tục được giữ.

Đã kiểm tra thêm ba JSP bằng Jasper của Tomcat local và JavaScript bằng fixture Chrome headless (fetch giả lập, 14 kiểm tra). Đây không phải kiểm thử end-to-end với Auth và MySQL thật.

Cần kiểm thử bàn giao với tài khoản Free/Premium/hết hạn trên môi trường kiểm thử riêng: luồng đăng nhập thật, UI đầy đủ, SQL transaction/rollback thực, session sau restart. Không tự tạo tài khoản, sửa trạng thái thuê bao hoặc ghi dữ liệu vào MySQL/Aiven đang dùng chỉ để kiểm chứng.

## Kết quả xác minh của thay đổi này

- Maven package trên JDK 21.0.12.1 / Maven 3.9.16: BUILD SUCCESS; 66 test, 0 failure, 0 error, 0 skipped.
- Ba JSP thay đổi được Jasper/Tomcat local precompile với compiler mặc định: 0 lỗi.
- Fixture Chrome headless ngoại tuyến với fetch giả lập: 14 kiểm tra JavaScript PASS.
- git diff --check: PASS.
- Chưa kiểm thử đăng nhập thật hoặc transaction trên MySQL/Aiven; không mở kết nối database trong nhiệm vụ này.
- Không thay đổi schema, catalog 30 món, Auth, OnboardingService, Payment/VNPay, Workout, Chatbot, secrets hoặc cấu hình deploy. Chưa commit/push/deploy.

## Danh sách file thay đổi

Backend:

- src/main/java/com/nutrifit/controller/FoodPreferenceServlet.java
- src/main/java/com/nutrifit/controller/MealRecommendationsServlet.java
- src/main/java/com/nutrifit/controller/NutritionServletSupport.java
- src/main/java/com/nutrifit/dao/NutritionUserReadDAO.java
- src/main/java/com/nutrifit/dto/MealSuggestion.java (mới)
- src/main/java/com/nutrifit/dto/SuggestedMeal.java (mới)
- src/main/java/com/nutrifit/service/FoodPreferenceService.java
- src/main/java/com/nutrifit/service/MealPlannerService.java
- src/main/java/com/nutrifit/service/MealRecommendationService.java
- src/main/java/com/nutrifit/service/RecommendationUnavailableException.java (mới)

Giao diện:

- src/main/webapp/WEB-INF/views/nutrition/food-preferences.jsp
- src/main/webapp/WEB-INF/views/nutrition/meal-planner.jsp
- src/main/webapp/WEB-INF/views/nutrition/meal-recommendations.jsp
- src/main/webapp/assets/css/nutrition.css
- src/main/webapp/assets/js/nutrition.js

Kiểm thử:

- src/test/java/com/nutrifit/controller/NutritionRecommendationsHttpTest.java (mới)
- src/test/java/com/nutrifit/dao/NutritionUserReadDAOTest.java (mới)
- src/test/java/com/nutrifit/service/FoodPreferenceServiceTest.java (mới)
- src/test/java/com/nutrifit/service/MealRecommendationServiceTest.java
- src/test/java/com/nutrifit/service/MealSuggestionSaveTest.java (mới)

Tài liệu:

- docs/nutrition/meal-suggestions.md (mới)
- docs/nutrition/vietnamese-food-catalog-review.md (cập nhật quy tắc phân quyền cũ)
