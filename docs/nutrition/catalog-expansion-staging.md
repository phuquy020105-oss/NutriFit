# Mở rộng catalog — continuation staging

Đã có30 thiết kế từ checkpoint; lần này bổ sung review đầy đủ trạng thái/khối lượng và30 ảnh minh họa AI riêng. Giữ nguyên100 Food/60 Recipe/607 links,20món/bữa; không đổi30 tên/meal_type/base_servings hoặc gram cũ.

24 thiết kế qua review phương pháp tính ở STAGING;6 suất đặc lớn còn cần review thực tế: R044/R048/R050/R054/R057/R060. Số món mới được duyệt ghi production vẫn0. Không bắt buộc mọi món phải được đo phòng thí nghiệm; các hạn chế quan trọng cần được giải quyết/ghi rõ và qua đầy đủ gates.

R047/R053 có200g nước kê riêng và cơm ăn kèm, nên không tự coi tổng>800g là sai. Khối lượng kê, khối lượng không gồm nước kê riêng và target khối lượng phục vụ được lưu riêng; measured final mass/evaporation vẫn null. Không bịa hệ số yield, không áp raw-to-cooked lần nữa cho thực phẩm đã chín. Dầu là lượng dự kiến ăn hết cùng sốt, không phải lượng đổ vào chảo chiên.

## Một suất chuẩn: số thực từ NutritionCalculator

| Mã | Món | Bữa | Gram kê | Nước kê riêng g | Kcal | Protein | Carbs | Fat | Fiber | Review phương pháp staging |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| R031 | Cháo đậu xanh trứng gà | BREAKFAST | 523.50 | 250.00 | 449.250 | 24.359 | 51.083 | 11.395 | 9.895 | Đã review, có giả định |
| R032 | Cháo yến mạch gà bí đỏ | BREAKFAST | 646.00 | 100.00 | 412.070 | 37.571 | 35.432 | 10.424 | 6.600 | Đã review, có giả định |
| R033 | Khoai lang luộc trứng và muối mè | BREAKFAST | 495.50 | 0.00 | 479.750 | 19.754 | 51.045 | 18.318 | 10.000 | Đã review, có giả định |
| R034 | Bắp luộc đậu hũ mè rang | BREAKFAST | 578.00 | 0.00 | 594.640 | 31.460 | 61.374 | 27.587 | 11.084 | Đã review, có giả định |
| R035 | Bánh mì gà xé rau củ | BREAKFAST | 369.00 | 0.00 | 630.130 | 52.982 | 62.808 | 16.459 | 5.700 | Đã review, có giả định |
| R036 | Bánh mì đậu hũ sốt đậu phộng | BREAKFAST | 479.00 | 15.00 | 647.880 | 35.200 | 72.236 | 24.187 | 7.210 | Đã review, có giả định |
| R037 | Bún trộn trứng rau đậu phộng | BREAKFAST | 567.00 | 20.00 | 638.030 | 25.334 | 73.642 | 23.753 | 8.540 | Đã review, có giả định |
| R038 | Cơm nắm gạo lứt mè và trứng luộc | BREAKFAST | 475.50 | 0.00 | 596.150 | 23.316 | 72.529 | 20.614 | 6.980 | Đã review, có giả định |
| R039 | Cháo gạo lứt đậu đỏ | BREAKFAST | 615.50 | 200.00 | 631.750 | 23.205 | 86.860 | 14.727 | 17.450 | Đã review, có giả định |
| R040 | Khoai lang đậu xanh dừa nạo | BREAKFAST | 498.40 | 0.00 | 607.250 | 20.482 | 67.411 | 20.652 | 23.530 | Đã review, có giả định |
| R041 | Cơm gạo lứt cá hồi nướng bông cải | LUNCH | 678.00 | 0.00 | 811.240 | 48.519 | 82.006 | 27.108 | 12.904 | Đã review, có giả định |
| R042 | Cơm trộn gà bắp đậu Hà Lan | LUNCH | 678.00 | 0.00 | 848.240 | 59.227 | 114.613 | 11.901 | 10.394 | Đã review, có giả định |
| R043 | Cơm chay đậu đỏ nấm | LUNCH | 763.00 | 0.00 | 818.740 | 28.293 | 132.040 | 11.804 | 22.384 | Đã review, có giả định |
| R044 | Gỏi gà bắp cải kèm khoai lang | LUNCH | 854.00 | 15.00 | 792.170 | 62.147 | 75.967 | 20.615 | 18.290 | Pending suất đặc lớn |
| R045 | Cơm đậu hũ mè đậu cô ve | LUNCH | 775.00 | 20.00 | 768.700 | 33.982 | 87.515 | 28.643 | 14.740 | Đã review, có giả định |
| R046 | Bún bò trộn rau đậu phộng | LUNCH | 723.00 | 20.00 | 900.250 | 64.429 | 87.686 | 29.106 | 10.520 | Đã review, có giả định |
| R047 | Cơm canh củ sen đậu xanh gà | LUNCH | 836.00 | 200.00 | 736.200 | 51.775 | 105.811 | 4.917 | 12.630 | Đã review, có giả định |
| R048 | Cơm bò bắp cải đậu cô ve | LUNCH | 825.00 | 20.00 | 855.000 | 67.893 | 97.241 | 16.601 | 9.500 | Pending suất đặc lớn |
| R049 | Cơm cá hồi đậu đỏ bí đỏ | LUNCH | 780.00 | 0.00 | 864.600 | 46.448 | 118.643 | 16.040 | 12.360 | Đã review, có giả định |
| R050 | Cơm bắp đậu hũ trứng luộc | LUNCH | 835.00 | 0.00 | 894.500 | 41.555 | 119.724 | 26.419 | 9.290 | Pending suất đặc lớn |
| R051 | Cơm gạo lứt đậu Hà Lan trứng luộc | DINNER | 658.00 | 0.00 | 645.340 | 30.745 | 76.060 | 18.006 | 16.104 | Đã review, có giả định |
| R052 | Cháo yến mạch đậu hũ nấm | DINNER | 795.00 | 100.00 | 539.300 | 29.898 | 56.559 | 18.661 | 13.320 | Đã review, có giả định |
| R053 | Cơm canh cải thảo đậu hũ trứng | DINNER | 871.00 | 200.00 | 557.400 | 33.031 | 61.184 | 18.259 | 5.020 | Đã review, có giả định |
| R054 | Cơm gạo lứt gà đậu xanh củ sen | DINNER | 808.00 | 20.00 | 822.240 | 60.761 | 96.638 | 12.365 | 23.254 | Pending suất đặc lớn |
| R055 | Bún nấm đậu hũ sốt mè | DINNER | 798.00 | 20.00 | 747.160 | 32.328 | 88.854 | 27.587 | 13.550 | Đã review, có giả định |
| R056 | Gỏi bắp cải trứng kèm khoai lang | DINNER | 687.00 | 15.00 | 619.820 | 26.475 | 59.394 | 26.113 | 16.394 | Đã review, có giả định |
| R057 | Cơm đậu hũ kho nấm | DINNER | 823.00 | 30.00 | 668.380 | 30.323 | 96.450 | 17.053 | 10.610 | Pending suất đặc lớn |
| R058 | Cháo cá hồi bí đỏ | DINNER | 642.00 | 250.00 | 442.450 | 29.672 | 44.912 | 14.076 | 3.215 | Đã review, có giả định |
| R059 | Gỏi đậu đỏ bắp đậu hũ với cơm gạo lứt | DINNER | 795.00 | 15.00 | 740.400 | 36.009 | 97.439 | 17.942 | 21.340 | Đã review, có giả định |
| R060 | Cơm bò củ sen bông cải | DINNER | 808.00 | 20.00 | 867.000 | 65.671 | 101.520 | 16.280 | 12.740 | Pending suất đặc lớn |

## Ảnh mới

30/30 WebP800×450,30hash khác nhau,2.124.668bytes tổng. Có alt text, prompt riêng, quyền tạo bằng built-in image_gen và disclosure ảnh AI, đã xem contact sheets và kiểm tra giải mã/hash. Lưu database/staging/food-quality-v1/images; không tự copy vào src/main hoặc WAR khi chưa qualification. image_url trong catalog vẫn null và fallback hiện hành vẫn hoạt động. Không sửa30 ảnh/mapping cũ.

## MySQL local / production

Tiếp tục dùng nutrifit_fq_20261019_food_quality_test hiện có, không xóa/tạo lại: SELECT trước ghi, hai delta10+1 Food updates,0 new rows. Injected rollback/idempotency0writes/conflict/history/JDBC và30 image mappings thử rồi rollback đều PASS. Sáu bảng schema-derived, không phải24-table production clone; version thực tế26.7.0. Snapshot1.32 suất cũ giữ nguyên. Aiven chỉ SELECT, vẫn82/30/383; không import.

Xem recipe-portion-review.json, image-generation-jobs.json, local-delta-result.json và production-readiness.md. C là catalog thăm dò:70 Food cũ có đủ số nguồn,12 chưa đủ vẫn giữ ước tính baseline có nhãn. Không gọi đây là qualified C.
