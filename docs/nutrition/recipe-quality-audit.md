# Audit30 công thức — staging, đang thực hiện

Đã duyệt cấu trúc30 recipes/383 ingredient links và tính baseline bằng NutritionCalculator thật. 9/30 công thức có đủ năm giá trị nguồn cho tất cả nguyên liệu để tính so sánh; các dòng còn lại có source_comparison=null, không phải0. Không công thức nào được phê duyệt migration ở mốc này.

## Cách tính và chế biến

- Giữ ID, meal_type, base_servings, toàn bộ383 định lượng. Không sửa mealentries hoặc tính lại snapshot đã ghi.
- Số gram là khối lượng nguyên liệu đã kê, không tự nhận là khối lượng món hoàn thiện được cân. Gạo khô F007 khác cơm chín F001/F081; nấm khô cân trước ngâm, nước giữ lại kê riêng; thịt chín là thịt ăn được bỏ xương theo mô tả.
- [FAO recipe calculations](https://www.fao.org/4/y4705e/y4705e23.htm): hệ số phải phù hợp nguyên liệu và phương pháp nấu. Không áp thêm retention/yield cho thực phẩm đã dùng dữ liệu chín. Chưa có phép cân bếp thực tế nên không bịa hệ số, nước bay hơi hoặc phần dầu hấp thu.
- Dầu F061 là phần giả định giữ trong món; F077 dầu điều/F080 hành phi đã chứa dầu, không cộng dầu nền lần hai. Cần cân trước/sau hoặc công thức thành phẩm định danh để nâng confidence.
- Các món dùng nguyên liệu sống rồi rán/xào/kho chỉ là phép tính thành phần từ công thức; chưa xác minh hao hụt macro vào nước/mỡ bỏ đi. Với canh/sốt dùng hết vẫn cần xác định khối lượng cuối; không gọi đây là số đo phòng thí nghiệm.
- Tráng bánh/cuốn R007, xối mỡ R012, kho ba chỉ R013/R022, cá chiên R020 và nước dùng R001/R002/R004/R005/R008/R010 cần kiểm tra chế biến riêng; chưa đề xuất thay gram để đạt target.

## Kết quả từng recipe

K/P/C/F/Fiber lần lượt kcal/g/g/g/g cho1.00 suất, BigDecimal làm tròn cuối3 số HALF_UP. Cột sau là so sánh nguồn chưa phê duyệt, không phải catalog B đã xác minh.

| Recipe | Tên | Gram nguyên liệu | Trước K/P/C/F/Fiber | So sánh nguồn K/P/C/F/Fiber | Food còn thiếu |
|---|---|---:|---|---|---|
| R001 | Phở bò | 629.20 | 456.290/34.613/50.045/11.670/1.842 | CHƯA ĐỦ NGUỒN | F011 |
| R002 | Phở gà | 628.20 | 420.100/37.663/50.055/5.940/1.844 | CHƯA ĐỦ NGUỒN | F058 |
| R003 | Bánh mì trứng | 253.50 | 427.840/20.698/46.815/17.017/2.779 | 429.912/22.057/45.265/16.577/2.555 | — |
| R004 | Bún bò Huế | 648.00 | 509.330/38.853/50.748/14.674/2.068 | CHƯA ĐỦ NGUỒN | F044,F075,F077,F058 |
| R005 | Hủ tiếu Nam Vang | 638.20 | 465.950/38.235/45.835/12.977/2.007 | CHƯA ĐỦ NGUỒN | F025,F030,F074 |
| R006 | Cháo gà | 481.70 | 293.770/25.083/32.712/5.891/0.836 | CHƯA ĐỦ NGUỒN | F042 |
| R007 | Bánh cuốn | 351.00 | 424.420/21.700/55.643/11.943/1.577 | CHƯA ĐỦ NGUỒN | F016,F080,F032 |
| R008 | Bún riêu | 730.00 | 426.840/27.480/52.945/10.442/3.670 | CHƯA ĐỦ NGUỒN | F026,F074,F076,F077 |
| R009 | Xôi gà | 325.20 | 533.950/27.120/66.345/16.717/2.240 | CHƯA ĐỦ NGUỒN | F008,F080 |
| R010 | Bánh canh cua | 587.20 | 374.380/22.918/52.305/7.250/0.900 | CHƯA ĐỦ NGUỒN | F005,F074,F077 |
| R011 | Cơm tấm sườn | 481.30 | 645.275/31.712/66.585/26.805/2.554 | CHƯA ĐỦ NGUỒN | F051 |
| R012 | Cơm gà xối mỡ | 456.50 | 635.260/36.343/53.302/29.560/2.062 | 637.428/34.338/52.957/30.412/2.093 | — |
| R013 | Cơm thịt kho trứng | 413.30 | 666.855/18.912/51.588/41.627/1.270 | CHƯA ĐỦ NGUỒN | F018 |
| R014 | Cơm cá kho tộ | 369.50 | 372.345/26.377/50.778/6.555/1.352 | CHƯA ĐỦ NGUỒN | F023 |
| R015 | Bún chả Hà Nội | 474.30 | 539.965/33.559/55.585/18.881/2.951 | CHƯA ĐỦ NGUỒN | F082,F051 |
| R016 | Bún thịt nướng | 500.00 | 608.100/33.679/58.105/25.964/3.946 | CHƯA ĐỦ NGUỒN | F044 |
| R017 | Cơm bò lúc lắc | 441.30 | 554.375/36.030/53.820/19.875/3.524 | 528.633/37.563/53.027/17.156/3.549 | — |
| R018 | Cơm gà luộc | 400.30 | 439.880/36.946/52.606/7.276/1.698 | 427.846/34.864/53.191/6.664/1.645 | — |
| R019 | Cơm sườn ram | 414.30 | 568.365/31.092/51.668/25.672/1.811 | 684.743/35.200/51.209/35.953/1.836 | — |
| R020 | Cơm cá chiên | 439.20 | 466.290/34.430/50.120/13.427/1.898 | CHƯA ĐỦ NGUỒN | F024 |
| R021 | Cơm cá hấp | 392.20 | 368.220/28.974/48.871/5.840/1.755 | CHƯA ĐỦ NGUỒN | F023 |
| R022 | Cơm thịt rang | 339.30 | 633.975/13.427/49.978/41.358/1.352 | CHƯA ĐỦ NGUỒN | F018 |
| R023 | Cơm canh chua cá | 752.30 | 437.150/28.930/64.540/5.947/5.613 | CHƯA ĐỦ NGUỒN | F023,F055,F057,F058 |
| R024 | Cơm gà kho gừng | 396.20 | 467.900/33.979/50.066/13.409/1.557 | 488.392/32.885/50.961/15.350/1.438 | — |
| R025 | Cơm đậu hũ sốt cà | 587.70 | 489.560/22.960/57.195/17.882/4.393 | 462.042/21.489/54.595/17.436/3.878 | — |
| R026 | Cơm tôm rim | 415.20 | 398.910/32.022/52.568/5.959/1.746 | CHƯA ĐỦ NGUỒN | F025 |
| R027 | Cơm thịt luộc | 420.20 | 447.390/37.912/50.153/9.461/1.798 | 457.482/37.679/50.754/9.522/1.804 | — |
| R028 | Cơm canh bí đỏ | 628.70 | 395.710/23.220/52.115/9.051/1.808 | CHƯA ĐỦ NGUỒN | F016 |
| R029 | Cơm cá kho | 373.30 | 368.855/26.356/49.864/6.595/1.480 | CHƯA ĐỦ NGUỒN | F023 |
| R030 | Cơm trứng chiên | 394.50 | 428.830/17.994/47.996/17.157/2.006 | 427.372/18.033/47.050/17.142/2.007 | — |

## Sai khác cần review

- R019 Cơm sườn ram: kcal 568.365 → 684.743; nguồn/cut/cooking khác nhau phải được review trước khi dùng số mới. Không dùng sai khác này làm lý do tự sửa khẩu phần.
- R025 Cơm đậu hũ sốt cà: kcal 489.560 → 462.042; nguồn/cut/cooking khác nhau phải được review trước khi dùng số mới. Không dùng sai khác này làm lý do tự sửa khẩu phần.
- R017 Cơm bò lúc lắc: kcal 554.375 → 528.633; nguồn/cut/cooking khác nhau phải được review trước khi dùng số mới. Không dùng sai khác này làm lý do tự sửa khẩu phần.
- R024 Cơm gà kho gừng: kcal 467.900 → 488.392; nguồn/cut/cooking khác nhau phải được review trước khi dùng số mới. Không dùng sai khác này làm lý do tự sửa khẩu phần.

## Kiểm thử và bước còn lại

FoodDataQualityAuditTest gọi NutritionCalculator hiện hành cho baseline và chỉ tính kết quả nguồn khi đủ toàn bộ nutrient; có regression cơm chín+mộc nhĩ khô, từ chối snapshot nguồn thiếu và kiểm tra SHA catalog. Audit JSON chi tiết giữ recipe instructions, từng food/state/gram, nguồn, missing refs và absolute differences.
Local trial cơ chế đã PASS; bản SELECT-only khớp SHA catalog C hiện tại: rollback, idempotency, conflict và history invariants. Đây không phải dữ liệu B đã xác minh. B/C thăm dò được báo riêng trong data-quality-benchmark.md và catalog-expansion-staging.md; baseline ước tính còn lại được ghi rõ. Theo xác nhận của chủ dự án, giữ staging, không ghi Aiven. Chưa có manifest nutrient/gram được duyệt production.
