# Nutrition: Thực đơn hằng ngày

## Giao diện và route

- Sidebar Dinh dưỡng mở `/nutrition/recommendations`. Navigation chỉ có Thực đơn, Lịch sử, Sở thích.
- Một trang hiển thị ba món, tổng năm chỉ số, mục tiêu/chênh lệch, cảnh báo tổng ngày, nhật ký đã ghi và phần Thêm món thủ công thu gọn.
- Không có ô nhập khẩu phần. Server quyết định `servings = 1.00` cho gợi ý và thêm món chuẩn.
- GET `/nutrition/meal-planner` và `/nutrition` redirect sang trang mới; giữ thông báo hợp lệ. Các POST add/update/delete cũ vẫn hoạt động.
- Đổi món trong nhật ký hôm nay giữ lượng đã lưu, kể cả số thập phân cũ; lịch sử ngày trước vẫn chỉ đọc.

## Chọn món và tính dinh dưỡng

- Đọc catalog hiện có qua RecipeReadPort; không tạo Recipe, không sửa seed hoặc BMR/TDEE.
- Xét các tổ hợp một BREAKFAST, một LUNCH, một DINNER ở đúng một suất. Với 10 món mỗi bữa là 1.000 tổ hợp.
- Tính độ lệch của tổng dự kiến sau khi lưu so với target_kcal; bao gồm nhật ký hôm nay và quy tắc cộng snapshot nếu trùng món/bữa.
- Xếp theo khoảng lệch 10% mục tiêu, ưu tiên LIKE trong cùng khoảng, rồi độ lệch thực tế và phân bố bữa. Đây là tiêu chí xếp hạng, không phải khuyến cáo dinh dưỡng hay cách sửa calories.
- Free không đọc sở thích. Premium còn hạn loại mọi Recipe chứa DISLIKE và ưu tiên nguyên liệu LIKE. Hết hạn dùng đường Free.
- Dùng NutritionCalculator để tính cả năm chỉ số từ nguyên liệu/base_servings. Chỉ làm tròn theo độ chính xác lưu trữ hiện có; không chỉnh số liệu để bằng mục tiêu.
- Đổi thực đơn chủ động loại tổ hợp trước khi có phương án khác hợp lệ; nếu chỉ còn một tổ hợp, giữ nó và thông báo rõ.

## Preview và lưu

- GET giữ preview trong session; tải lại không tự đổi tổ hợp. Đổi thực đơn là POST có CSRF và thay nonce.
- Giữ API POST preview để tích hợp, nhưng bỏ qua servings/recipeId/dinh dưỡng do client gửi. Các service cũ xử lý lượng trong lịch sử và POST nhật ký cũ được giữ.
- Lưu kiểm tra owner/ngày/nonce/thời hạn 30 phút và CSRF. Đọc lại mục tiêu, Premium, DISLIKE và Recipe active.
- Trong một transaction: khóa plan và các dòng nhật ký hiện tại, tính lại projection, so với preview, rồi ghi đủ ba món. Nếu nhật ký/mục tiêu/dinh dưỡng đã đổi, rollback và yêu cầu xem lại.
- Món trùng cùng bữa cộng lượng theo snapshot đang lưu. Món thủ công khác giữ nguyên; không sửa lịch sử. Projection đã bao gồm hành vi này.
- Sau lưu, redirect về cùng trang với thông báo và nonce đã lưu; reload hoặc gửi lại không lưu lần hai. Lỗi commit chưa rõ kết quả không tự retry. Người dùng có thể xem nhật ký và chủ động Đổi thực đơn.
- Nếu thiếu mục tiêu hoặc thiếu món phù hợp, vẫn hiển thị nhật ký và thêm món thủ công, cùng thông báo an toàn.

## Kiểm thử

Chạy bằng JDK 21 / Maven 3.9.16:

```cmd
cd /d D:\Web\NutriFit-Integration
mvn -B clean package
git diff --check
```

JUnit dùng DAO/JDBC/HTTP doubles, không ghi database: Free/Premium, tổ hợp catalog 30 món, LIKE/DISLIKE, mặc định một suất, bỏ qua input giả, số liệu Calculator, dự báo nhật ký, đổi thực đơn, nonce/CSRF/route cũ, rollback, đổi món giữ lượng cũ và kiểm tra owner/ngày.

JSP và JavaScript được kiểm tra thêm bằng Tomcat/Chrome fixture riêng. Transaction thực trên Aiven không được thực thi để kiểm thử. Menu Admin vẫn dùng quyền server hiện hành.


## Sửa nhãn thao tác và lịch sử rỗng (2026-10-20)

- **Đổi món** chỉ thay một bữa; **Đổi thực đơn** thay cả phương án ba bữa, vẫn dùng `action=regenerate`. Nhãn lưu không đổi; thuật toán recommendation/swap không đổi.
- `MealPlanDAO.findHistory` dùng `EXISTS` tương quan theo `plan_id`, lọc owner và ngày trước hôm nay rồi mới lấy 30 ngày gần nhất. Không join nhân bản ngày khi một plan có nhiều món. Index hiện có `uq_mealplan_user_date(user_id, plan_date)` và `idx_mealentry_plan(plan_id)` đã hỗ trợ truy vấn; không thay schema.
- Plan rỗng được giữ trong database nhưng không nằm trong danh sách ngày có nhật ký. Chọn ngày rỗng qua bộ chọn ngày vẫn được phép, chỉ hiện thông báo chưa có món; không dựng thẻ tổng bằng 0 hoặc bảng rỗng. Một entry thực sự có snapshot bằng 0 vẫn được hiển thị. Ngày có dữ liệu giữ nguyên snapshot và tổng năm chỉ số, số nguyên HALF_UP chỉ khi hiển thị.
- Không chạy migration, không xóa plan, không sửa Aiven/catalog/ảnh hoặc dữ liệu lịch sử. Manifest catalog60 là biên bản bất biến tại revision đã duyệt trước đây; không tái tạo manifest để phản ánh bản sửa UI sau này.

Kiểm thử JSP thật dùng Tomcat đã cài, trong context riêng chỉ bind loopback, không chạy Auth/filter/service hoặc database của ứng dụng:

```cmd
set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
set "PATH=%JAVA_HOME%\bin;C:\tools\apache-maven-3.9.16\bin;%PATH%"
set "TOMCAT_HOME=C:\tools\apache-tomcat-10.1.61"
mvn -DargLine=-Xmx768m clean package
python database/tools/food_quality/verify_web.py --jdk "%JAVA_HOME%" --tomcat "%TOMCAT_HOME%" --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
git diff --check
```

`NutritionViewsTest` render JSP thật cho ngày chưa chọn/rỗng/có dữ liệu/entry bằng 0 và nhãn thực đơn. Nếu thiếu `TOMCAT_HOME`, các test render được báo SKIP rõ ràng; không coi đó là đã kiểm chứng JSP. DAO/JDBC/HTTP/service unit tests không cần database.

`MealPlanHistoryReadOnlyCheck` là kiểm thử SQL tùy chọn: dùng helper kết nối TLS đã có, nhưng CTE `mealplans`/`mealentries` thay thế cả hai bảng thật trong mỗi SELECT. Nó chạy truy vấn DAO thật với dữ liệu tổng hợp trong câu SELECT, kiểm tra empty/populated/multiple/owner/date/latest30 và negative control tái hiện query cũ. Không tạo user/plan/entry, bảng tạm hoặc dữ liệu fixture trong database.
