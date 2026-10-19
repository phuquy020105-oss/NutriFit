# Mở rộng catalog —30 thiết kế ở staging

Theo xác nhận mới nhất của chủ dự án: giữ staging, chưa ghi Aiven. Có30 thiết kế,10 mỗi bữa;18 Food mới có đủ năm số nguồn/quy đổi. Chưa món nào được duyệt production. Đây là công thức/định lượng gốc do NutriFit thiết kế, không phải số gram được NIN đo hoặc số liệu phòng thí nghiệm.

## Trạng thái dữ liệu

- C thăm dò:100 Food/60 Recipe/607 liên kết; thêm18/30/224 so với baseline82/30/383.
- Dùng lại Food cũ chỉ khi có đầy đủ năm giá trị nguồn trong hồ sơ; N001–N018 là mã ổn định staging, không phải food_id của MySQL. Tên, trạng thái và record USDA gốc được ghi trong new-food-provenance.json.
- Giữ nguyên30 ảnh cũ và image_url của chúng trong bản C.30 món mới chưa có ảnh riêng; image_url=null sử dụng fallback thật có sẵn. Chưa sinh ảnh cho thiết kế chưa duyệt để tránh đóng băng hình minh họa sai món/khẩu phần.
- Đã kiểm tra lookup món NIN qua5 truy vấn công khai: trả aggregates/nhóm/vùng, không có ingredient grams hoặc công thức nấu cần thiết trong response. Không sử dụng các aggregate đó làm số đo cho thiết kế này; không sao chép ảnh NIN khi chưa xác định quyền sử dụng.

## Mỗi suất chuẩn dự thảo

| Mã | Bữa | Món | Gram kê | Kcal | P | C khả dụng | Fat | Fiber | Cần review suất lớn |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| R031 | BREAKFAST | Cháo đậu xanh trứng gà | 523.50 | 449.250 | 24.359 | 51.083 | 11.395 | 9.895 | — |
| R032 | BREAKFAST | Cháo yến mạch gà bí đỏ | 646.00 | 412.070 | 37.571 | 35.432 | 10.424 | 6.600 | — |
| R033 | BREAKFAST | Khoai lang luộc trứng và muối mè | 495.50 | 479.750 | 19.754 | 51.045 | 18.318 | 10.000 | — |
| R034 | BREAKFAST | Bắp luộc đậu hũ mè rang | 578.00 | 594.640 | 31.460 | 61.374 | 27.587 | 11.084 | — |
| R035 | BREAKFAST | Bánh mì gà xé rau củ | 369.00 | 630.130 | 52.982 | 62.808 | 16.459 | 5.700 | — |
| R036 | BREAKFAST | Bánh mì đậu hũ sốt đậu phộng | 479.00 | 647.880 | 35.200 | 72.236 | 24.187 | 7.210 | — |
| R037 | BREAKFAST | Bún trộn trứng rau đậu phộng | 567.00 | 638.030 | 25.334 | 73.642 | 23.753 | 8.540 | — |
| R038 | BREAKFAST | Cơm nắm gạo lứt mè và trứng luộc | 475.50 | 596.150 | 23.316 | 72.529 | 20.614 | 6.980 | — |
| R039 | BREAKFAST | Cháo gạo lứt đậu đỏ | 615.50 | 631.750 | 23.205 | 86.860 | 14.727 | 17.450 | — |
| R040 | BREAKFAST | Khoai lang đậu xanh dừa nạo | 498.40 | 607.250 | 20.482 | 67.411 | 20.652 | 23.530 | — |
| R041 | LUNCH | Cơm gạo lứt cá hồi nướng bông cải | 678.00 | 811.240 | 48.519 | 82.006 | 27.108 | 12.904 | — |
| R042 | LUNCH | Cơm trộn gà bắp đậu Hà Lan | 678.00 | 848.240 | 59.227 | 114.613 | 11.901 | 10.394 | — |
| R043 | LUNCH | Cơm chay đậu đỏ nấm | 763.00 | 818.740 | 28.293 | 132.040 | 11.804 | 22.384 | — |
| R044 | LUNCH | Gỏi gà bắp cải kèm khoai lang | 854.00 | 792.170 | 62.147 | 75.967 | 20.615 | 18.290 | Có |
| R045 | LUNCH | Cơm đậu hũ mè đậu cô ve | 775.00 | 768.700 | 33.982 | 87.515 | 28.643 | 14.740 | — |
| R046 | LUNCH | Bún bò trộn rau đậu phộng | 723.00 | 900.250 | 64.429 | 87.686 | 29.106 | 10.520 | — |
| R047 | LUNCH | Cơm canh củ sen đậu xanh gà | 836.00 | 736.200 | 51.775 | 105.811 | 4.917 | 12.630 | Có |
| R048 | LUNCH | Cơm bò bắp cải đậu cô ve | 825.00 | 855.000 | 67.893 | 97.241 | 16.601 | 9.500 | Có |
| R049 | LUNCH | Cơm cá hồi đậu đỏ bí đỏ | 780.00 | 864.600 | 46.448 | 118.643 | 16.040 | 12.360 | — |
| R050 | LUNCH | Cơm bắp đậu hũ trứng luộc | 835.00 | 894.500 | 41.555 | 119.724 | 26.419 | 9.290 | Có |
| R051 | DINNER | Cơm gạo lứt đậu Hà Lan trứng luộc | 658.00 | 645.340 | 30.745 | 76.060 | 18.006 | 16.104 | — |
| R052 | DINNER | Cháo yến mạch đậu hũ nấm | 795.00 | 539.300 | 29.898 | 56.559 | 18.661 | 13.320 | — |
| R053 | DINNER | Cơm canh cải thảo đậu hũ trứng | 871.00 | 557.400 | 33.031 | 61.184 | 18.259 | 5.020 | Có |
| R054 | DINNER | Cơm gạo lứt gà đậu xanh củ sen | 808.00 | 822.240 | 60.761 | 96.638 | 12.365 | 23.254 | Có |
| R055 | DINNER | Bún nấm đậu hũ sốt mè | 798.00 | 747.160 | 32.328 | 88.854 | 27.587 | 13.550 | — |
| R056 | DINNER | Gỏi bắp cải trứng kèm khoai lang | 687.00 | 619.820 | 26.475 | 59.394 | 26.113 | 16.394 | — |
| R057 | DINNER | Cơm đậu hũ kho nấm | 823.00 | 668.380 | 30.323 | 96.450 | 17.053 | 10.610 | Có |
| R058 | DINNER | Cháo cá hồi bí đỏ | 642.00 | 442.450 | 29.672 | 44.912 | 14.076 | 3.215 | — |
| R059 | DINNER | Gỏi đậu đỏ bắp đậu hũ với cơm gạo lứt | 795.00 | 740.400 | 36.009 | 97.439 | 17.942 | 21.340 | — |
| R060 | DINNER | Cơm bò củ sen bông cải | 808.00 | 867.000 | 65.671 | 101.520 | 16.280 | 12.740 | Có |

Mốc800g chỉ dùng triage thiết kế, không phải ngưỡng y khoa hoặc xác nhận những suất còn lại đã hợp lý. Đặc biệt cần cân phần ăn hoàn thiện, dầu giữ lại và lượng nước của các suất lớn/canh/cháo; không tự nhân/chia servings để tăng điểm.

## Trial MySQL local

Đã chạy trong database mới nutrifit_fq_20261019_food_quality_test trên127.0.0.1:3306, chỉ6 bảng schema-derived phục vụ trial; đây không phải bản sao24 bảng production. Không đụng nutrifitdb_java hoặc Aiven.

Công cụ LocalFoodQualityTrial: chỉ host loopback3306, tên mới có prefixnutrifit_fq_/suffix_test, từ chối database tồn tại; JDBCProperties giữ password trong memory, PreparedStatement, transaction và name/generated-ID mappings. Baseline dùng ID bắt đầu1001/2001 và rollback tạo gap, nhằm phát hiện giả định ID.

Kết quả: INSERT18 Food/30 Recipe/224 links, UPDATE55 Food có số khác thực tế;4 trong59 source-complete Food không cần đổi giá trị. Lỗi cưỡng bức sau99 writes rollback toàn bộ; conflict bị từ chối; chạy lại0/0/0 và0update; snapshot1.32suất fixture và users/mealplans thử nghiệm không đổi; JdbcRecipeReadAdapter/NutritionCalculator đọc hợp lệ60 món. Đây chỉ xác nhận cơ chế dữ liệu, không phải duyệt dinh dưỡng.

DDL tạo schema có auto-commit; công cụ không hứa rollback DDL và không tự DROP database. Database test được giữ để kiểm tra; chạy lại với cùng tên phải dừng trước CREATE. Không có công cụ ghi Aiven cho bộ dữ liệu chưa đạt gate.

Đã SELECT-only kiểm tra lại toàn bộ100 Food/60 Recipe/607 links cùng metadata/instructions và calculator theo hash C hiện tại. JDBC báo local MySQL26.7.0; không mặc định đây là cùng version8.4 của Aiven. Xem local-trial-readonly.json.
