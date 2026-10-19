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
- Gợi ý lại chủ động loại tổ hợp trước khi có phương án khác hợp lệ; nếu chỉ còn một tổ hợp, giữ nó và thông báo rõ.

## Preview và lưu

- GET giữ preview trong session; tải lại không tự đổi tổ hợp. Gợi ý lại là POST có CSRF và thay nonce.
- Giữ API POST preview để tích hợp, nhưng bỏ qua servings/recipeId/dinh dưỡng do client gửi. Các service cũ xử lý lượng trong lịch sử và POST nhật ký cũ được giữ.
- Lưu kiểm tra owner/ngày/nonce/thời hạn 30 phút và CSRF. Đọc lại mục tiêu, Premium, DISLIKE và Recipe active.
- Trong một transaction: khóa plan và các dòng nhật ký hiện tại, tính lại projection, so với preview, rồi ghi đủ ba món. Nếu nhật ký/mục tiêu/dinh dưỡng đã đổi, rollback và yêu cầu xem lại.
- Món trùng cùng bữa cộng lượng theo snapshot đang lưu. Món thủ công khác giữ nguyên; không sửa lịch sử. Projection đã bao gồm hành vi này.
- Sau lưu, redirect về cùng trang với thông báo và nonce đã lưu; reload hoặc gửi lại không lưu lần hai. Lỗi commit chưa rõ kết quả không tự retry. Người dùng có thể xem nhật ký và chủ động Gợi ý lại.
- Nếu thiếu mục tiêu hoặc thiếu món phù hợp, vẫn hiển thị nhật ký và thêm món thủ công, cùng thông báo an toàn.

## Kiểm thử

Chạy bằng JDK 21 / Maven 3.9.16:

```cmd
cd /d D:\Web\NutriFit-Integration
mvn -B clean package
git diff --check
```

JUnit dùng DAO/JDBC/HTTP doubles, không ghi database: Free/Premium, tổ hợp catalog 30 món, LIKE/DISLIKE, mặc định một suất, bỏ qua input giả, số liệu Calculator, dự báo nhật ký, gợi ý lại, nonce/CSRF/route cũ, rollback, đổi món giữ lượng cũ và kiểm tra owner/ngày.

JSP và JavaScript được kiểm tra thêm bằng Tomcat/Chrome fixture riêng. Transaction thực trên Aiven không được thực thi để kiểm thử. Menu Admin vẫn dùng quyền server hiện hành.
