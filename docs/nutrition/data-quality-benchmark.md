# Benchmark continuation — dữ liệu thăm dò, không phải qualification

432 tình huống/dataset; cùng6 hồ sơ giả lập,3 activity,3 goal,4 trạng thái gói/sở thích,2 nhật ký. Target từ OnboardingService không đổi. Cùng lịch sử A và cùng thuật toán cho guarded A/B/C. A_before lưu từ lần thực tế trước guard, không chạy lại bằng code mới. B hiện thay70 Food đủ số nguồn,12 Food còn thiếu giữ baseline ước tính có nhãn. C thêm18 Food/30 thiết kế.

| Chỉ số | A trước guard (cũ) | A guarded | B70 nguồn thăm dò | C60 thiết kế thăm dò |
|---|---:|---:|---:|---:|
| Đủ3 bữa | 432 | 432 | 432 | 432 |
| Có tổ hợp trong10%target | 200 | 200 | 236 | 336 |
| Lệch>20% dù có tổ hợp trong10% | 5 | 0 | 0 | 0 |
| projected_kcal mean | 1628.8898 | 1636.2640 | 1769.3046 | 2083.7773 |
| projected_kcal median | 1668.7850 | 1668.7850 | 1829.0080 | 2151.4050 |
| projected_kcal p90 | 1850.1850 | 1850.1850 | 2074.4920 | 2588.9450 |
| absolute_error_kcal mean | 605.9493 | 598.5750 | 468.2383 | 167.3951 |
| absolute_error_kcal median | 500.7950 | 485.1500 | 162.2470 | 3.8325 |
| absolute_error_kcal p90 | 1583.0400 | 1583.0400 | 1534.9900 | 686.3800 |
| relative_error mean | 0.2225 | 0.2190 | 0.1632 | 0.0576 |
| relative_error median | 0.2262 | 0.2130 | 0.0892 | 0.0021 |
| relative_error p90 | 0.5012 | 0.5012 | 0.4941 | 0.2247 |
| protein_g mean | 94.2599 | 93.7143 | 95.4866 | 125.1897 |
| protein_g median | 96.2570 | 96.2570 | 94.9270 | 120.0260 |
| protein_g p90 | 101.4620 | 100.2720 | 105.9760 | 167.0420 |
| available_carbs_g mean | 190.3470 | 190.5780 | 205.3510 | 248.8033 |
| available_carbs_g median | 190.1250 | 190.1250 | 208.2325 | 267.5620 |
| available_carbs_g p90 | 213.9150 | 213.9150 | 244.4690 | 308.3360 |
| fat_g mean | 51.0438 | 52.0045 | 58.5128 | 52.8874 |
| fat_g median | 52.7600 | 52.7600 | 63.9530 | 53.2190 |
| fat_g p90 | 63.5370 | 64.3780 | 74.3500 | 63.3510 |
| fiber_g mean | 11.8817 | 11.7537 | 11.4851 | 35.7531 |
| fiber_g median | 11.9940 | 11.9940 | 11.0580 | 36.5790 |
| fiber_g p90 | 13.8210 | 13.8210 | 14.8180 | 49.5970 |
| protein_energy_ratio mean | 0.2336 | 0.2315 | 0.2190 | 0.2404 |
| protein_energy_ratio median | 0.2351 | 0.2273 | 0.2140 | 0.2521 |
| protein_energy_ratio p90 | 0.2737 | 0.2737 | 0.2505 | 0.2627 |
| carb_energy_ratio mean | 0.4687 | 0.4673 | 0.4649 | 0.4770 |
| carb_energy_ratio median | 0.4713 | 0.4713 | 0.4639 | 0.4717 |
| carb_energy_ratio p90 | 0.4924 | 0.4924 | 0.4871 | 0.5049 |
| fat_energy_ratio mean | 0.2784 | 0.2821 | 0.2932 | 0.2298 |
| fat_energy_ratio median | 0.2771 | 0.2771 | 0.3096 | 0.2255 |
| fat_energy_ratio p90 | 0.3312 | 0.3312 | 0.3238 | 0.2589 |
| fiber_gap_g mean | 7.2850 | 7.4130 | 7.6859 | 0.0528 |
| fiber_gap_g median | 7.6140 | 7.7710 | 7.8310 | 0.0000 |
| fiber_gap_g p90 | 9.6530 | 9.9990 | 11.0060 | 0.0000 |
| unique_food_count mean | 29.0833 | 28.9028 | 28.8241 | 22.0741 |
| unique_food_count median | 29.0000 | 29.0000 | 30.0000 | 21.0000 |
| unique_food_count p90 | 35.0000 | 35.0000 | 35.0000 | 28.0000 |
| runtime_ms mean | 3.6292 | 5.7333 | 5.2837 | 40.3398 |
| runtime_ms median | 3.3106 | 5.9162 | 4.8810 | 41.3820 |
| runtime_ms p90 | 4.1903 | 6.6566 | 7.2438 | 46.7473 |
| Đa dạng món | 20 | 20 | 23 | 51 |
| Đa dạng Food | 73 | 73 | 72 | 96 |
| Fat>25%energy số case | 339 | 343 | 374 | 70 |
| Carbs ngoài50–65%energy số case | 416 | 416 | 420 | 370 |

P90 nearest-rank; runtime là service-call wall-time trên một máy, không phải load test. Macro tỷ lệ4/4/9 chia kcal nguồn, không ép tổng100%. NIN là tham chiếu mềm: fat20–25%,carbs50–65%,fiber nam trẻ21g/nữ18g,50+20g/17g; không phải khuyến nghị y khoa cá nhân. [Nguồn NIN](https://viendinhduong.vn/vi/proper-nutrition-and-health/nguoi-truong-thanh-19-59-tuoi/nhung-diem-cap-nhat-ve-nhu-cau-dinh-duong-khuyen-nghi-cho-nguoi-viet-nam-6a70094d06fb0c475f0ac123).

So với checkpoint: A guarded mean absolute error598.575kcal; C cũ161.362kcal. Những thay đổi trong B/C lần này là dữ liệu thăm dò, không sửa scorer. Không xem cải thiện benchmark là bằng chứng nguồn/khẩu phần đã đúng.24 thiết kế qua review phương pháp staging,6 suất đặc lớn còn pending; không phát hành partial30 mới để đủ60.

CSV/SHA, mean/median/P90 đủ năm nutrient, sai lệch, diversity và runtime ở cohort-comparison-summary.json. Dataset qualified B/C chưa được tạo vì còn47MISSING và gates khác.
