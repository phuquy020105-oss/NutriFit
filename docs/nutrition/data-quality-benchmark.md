# Benchmark chất lượng dữ liệu — kết quả thăm dò

Không phải kết quả của catalog B/C đã xác minh hoàn chỉnh. Các nutrient/khẩu phần còn thiếu bằng chứng không được chuyển thành PASS nhờ benchmark.

## Thiết kế cố định

- Sáu hồ sơ giả lập: nữ22/45/68 và nam20/42/70 tuổi, nhiều chiều cao/cân nặng; sedentary/moderate/very_high; lose/maintain/gain; Free, Premium LIKE, Premium DISLIKE, expired với DISLIKE cũ; nhật ký rỗng hoặc snapshot1/2 suất R023. Mỗi dataset432 trường hợp.
- Target lấy bằng cách gọi OnboardingService.save nguyên bản, chỉ thay DAO trong test bằng capture-only DAO. Không kết nối JDBC, không chép công thức BMR/TDEE. Cùng snapshot lịch sử từ A cho cả A/B/C; service vẫn dùng logic merge snapshot hiện hành.
- A_before đo thuật toán trước sửa trên chính A. A_guarded/B/C chạy cùng thuật toán sau sửa và cùng trọng số. B thay59 Food đủ số nguồn, giữ23 Food cũ chưa đủ; C thêm30 thiết kế/18 Food mới. Không gọi B là dữ liệu đã VERIFIED.
- NIN2026 là tham chiếu mềm cho báo cáo: fat20–25% năng lượng; carbs50–65%; ngưỡng fiber nam trẻ21g/nữ18g, nhóm50+20g/17g. Gap là khoảng cách đến mốc tối thiểu, không phải đánh giá y khoa. [Nguồn NIN chính thức](https://viendinhduong.vn/vi/proper-nutrition-and-health/nguoi-truong-thanh-19-59-tuoi/nhung-diem-cap-nhat-ve-nhu-cau-dinh-duong-khuyen-nghi-cho-nguoi-viet-nam-6a70094d06fb0c475f0ac123).
- Tỷ lệ macro dùng4/4/9 chia kcal nguồn, không ép tổng tỷ lệ thành100%. Calories vẫn giữ NutritionCalculator. Thời gian là service-call wall time trên một máy, không phải thử tải production. P90 dùng nearest rank.

## Kết quả

| Chỉ số | A trước guard | A sau guard | B thăm dò | C60 thiết kế thăm dò |
|---|---:|---:|---:|---:|
| Đủ3 bữa | 432 | 432 | 432 | 432 |
| Có tổ hợp trong10% target | 200 | 200 | 229 | 344 |
| Chọn lệch>20% dù có tổ hợp trong10% | 5 | 0 | 0 | 0 |
| Kcal trung bình | 1628.8898 | 1636.2640 | 1679.4948 | 2077.5618 |
| Sai lệch tuyệt đối kcal trung bình | 605.9493 | 598.5750 | 556.8466 | 161.3620 |
| Sai lệch tuyệt đối kcal median | 500.7950 | 485.1500 | 283.6845 | 3.2400 |
| Sai lệch tuyệt đối kcal P90 | 1583.0400 | 1583.0400 | 1587.1900 | 686.3800 |
| Sai lệch tương đối trung bình | 0.2225 | 0.2190 | 0.1998 | 0.0529 |
| Protein g trung bình | 94.2599 | 93.7143 | 94.8947 | 125.5082 |
| Carbs khả dụng g trung bình | 190.3470 | 190.5780 | 191.7006 | 247.1438 |
| Fat g trung bình | 51.0438 | 52.0045 | 54.6855 | 52.7163 |
| Fiber g trung bình | 11.8817 | 11.7537 | 12.3645 | 35.9610 |
| Protein energy ratio trung bình | 0.2336 | 0.2315 | 0.2288 | 0.2421 |
| Carb energy ratio trung bình | 0.4687 | 0.4673 | 0.4587 | 0.4761 |
| Fat energy ratio trung bình | 0.2784 | 0.2821 | 0.2878 | 0.2286 |
| Fiber gap g trung bình | 7.2850 | 7.4130 | 6.8022 | 0.2233 |
| Số món được chọn toàn cohort | 20 | 20 | 22 | 54 |
| Số nguyên liệu được chọn toàn cohort | 73 | 73 | 72 | 98 |
| Số nguyên liệu trung bình/menu | 29.0833 | 28.9028 | 29.5949 | 21.7593 |
| Fat>25% energy: số case | 339 | 343 | 350 | 49 |
| Carbs ngoài50–65% energy: số case | 416 | 416 | 421 | 377 |
| Runtime service ms median | 3.3106 | 6.7297 | 5.4153 | 46.9438 |
| Runtime service ms P90 | 4.1903 | 7.5918 | 7.2817 | 51.0860 |

## Diễn giải và giới hạn

Guard xử lý đúng lỗi quan sát được: khi tồn tại lựa chọn trong10%, chỉ xếp hạng/gợi ý lại trong15%. Nếu không có tổ hợp khả thi, giữ fallback và cảnh báo; không đổi servings, target, LIKE/DISLIKE hay trọng số. Fiber của A giảm nhẹ sau guard: đây là đánh đổi được ghi nhận, không giấu để tuyên bố mọi chỉ số cải thiện.

C giảm sai lệch năng lượng và tăng xơ trong dữ liệu thăm dò, nhưng không chứng minh lợi ích ngoài thực tế. Có8 thiết kế trên800g nguyên liệu được kê, cần kiểm tra suất thực tế; khối lượng kê không phải khối lượng sau nấu. Không dùng cải thiện benchmark để bỏ qua source/portion gates. C vẫn có88/432 trường hợp không có tổ hợp trong10% target.

CSV từng case, source/dataset SHA và thống kê mean/median/P90 nằm tại database/staging/food-quality-v1/. Dữ liệu thăm dò không được import production. Cùng thuật toán chỉ cô lập phần source/catalog trong thử nghiệm này, không loại trừ sai lệch do23 Food cũ còn ước tính.
