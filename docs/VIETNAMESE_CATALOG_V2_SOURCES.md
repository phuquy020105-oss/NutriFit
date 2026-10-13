# Nguồn và phép tính — công thức tham khảo cho đồ án (2026-10-12)

Phần mới này là tiêu chuẩn hiện hành; phần bên dưới lưu kết quả nghiên cứu cũ.
Cho phép giả định kỹ thuật minh bạch; không gán chúng thành số đo hoặc hệ số của
nguồn khoa học. Profile đầu vào đã đối chiếu mã/URL; nấu một biến thể tham khảo
không chứng minh dinh dưỡng của mọi món có cùng tên.

## Nguồn đầu vào

- SMILING Việt Nam 2013: https://www.fao.org/fileadmin/templates/food_composition/documents/FCT_SMILING_PROJECT_ASIA/D3_5a_SMILING_FCT_Vietnam_180713_protected.xlsx
  Đọc worksheet XML sheet4 và component descriptions trực tiếp; lưu mã/dòng/SHA256
  trong ingredient_sources.json. Không sửa 14 profile VNT2007; fat NULL không điền 0.
  Fat 0 trong SMILING là giá trị công bố của profile này, có thể imputed/calc,
  không tuyên bố là xét nghiệm mới. CHOCDF và FIBC ghi rõ định nghĩa.
- USDA SR Legacy archive: https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip
  Đã đọc food.csv / food_nutrient.csv trong bộ nhớ; FDC ID và nutrient IDs 1008/1003/1005/
  1004/1079. Public domain/CC0: https://fdc.nal.usda.gov/api-guide/.
- FSANZ AFCD Release 3: https://www.foodstandards.gov.au/science-data/food-nutrient-databases/afcd/data-files
  F001990 cải ngọt raw, F001988 boiled drained. Recipes.xlsx sheet2 row743 ghi -4%.
  500 g phần ăn được sống → 480 g modeled cooked; không cân thực tế. Dùng profile chín đã công bố,
  không áp yield/retention lần hai. 74 kJ/4.184=17.6864 kcal/100 g; P1.4/C0.9/F0.3/
  TDF2.9. Available carbs khác carbohydrate-by-difference; energy bao gồm fiber.
  Attribution/share-alike: https://www.foodstandards.gov.au/science-data/monitoringnutrients/afcd/datauserlicenceagreement
  Yield tham khảo, không bảo đảm mẻ Việt Nam: https://www.foodstandards.gov.au/sites/default/files/2025-12/About%20the%20Australian%20Food%20Composition%20Database%20-%20Release%203.pdf
- Cua đồng 8034: bảng Việt Nam 2007: trang PDF 422 / trang in 394, refuse 69%:
  https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf
  1000 g nguyên con*0.31=310 g phần ăn được là tham khảo. Recovery 80% nutrient vào riêu là GIẢ
  ĐỊNH của công thức, không hệ số nguồn, không dùng cua biển hay cả vỏ làm thịt ăn.

Cơ sở phương pháp: https://www.fao.org/4/y4705e/y4705e23.htm
Bản đồ án dùng cách tính nguyên liệu / cân bằng khối lượng tương tự, nhưng oil/yield/retention
không đo được đều ghi ENGINEERING_ASSUMPTION; không khẳng định thực hiện đầy đủ
quy trình cân của FAO.

## Công thức có thể chạy lại

P/C/F_batch = sum(g_edible*N_source_per100 g/100*declared_retention).
Energy_batch = sum(g_edible*source_energy_per100 g/100*r_energy).
Với thành phần bị mất macro: r_energy = (4P*rP+4C*rC+9F*rF)/(4P+4C+9F).
Nếu năng lượng nguồn và P/C/F đều 0 dùng r_energy=1; không suy NULL thành 0. Đây là
xấp xỉ kỹ thuật bảo toàn liên hệ kcal/macros, không phải hệ số retention công bố.
N_per100 g = N_batch*100/finished_edible_g.
Reference = finished_edible_g/servings; min/max là giới hạn planner đề xuất.
Massbalance = input_edible_g - discarded_g - evaporated_g = finished_edible_g.
Dầu bỏ tác động đồng thời massbalance và retention nutrient, không trừ fat hai lần.
Water/cookedstock/sợi chín được ghi đúng trạng thái; stock có nutrient, không phải nước 0 kcal.
Cellulose/crude-fiber chưa được cộng thành TDF; fiber NULL nếu có component thiếu.

Giả định khối lượng thành phẩm ±10% ở tổng nutrient cố định làm density thay đổi +11.11%/
-9.09%; đây là phân tích độ nhạy toán học, không phải sai số đo/CI. Mỗi 1 g dầu đậu nành giữ lại
thêm 8,84 kcal và 1 g fat theo USDA 171411; nếu trọng lượng cuối thay đổi cũng phải
cập nhật mẫu số. Mỡ thịt, lọc riêu, nước dùng và oil retention là nguồn sai số chính.

## 12 công thức, gram và giả định

### Phở bò — pho_beef

Khối lượng thành phẩm tham khảo  1200 g; 2 suất; reference 600 g. kcal/P/C/F trên 100 g:63.3/4.63/9.58/0.58.

Cân bằng khối lượng giả định: 1256-4-52=1200 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Rice noodles, cooked | 400 | cooked | usda_168914 | 1/1/1 |
| Beef, top sirloin, steak, separable lean only, trimmed to 1/8" fat, select, raw | 160 | raw | usda_171804 | 0.98/0.98/0.95 |
| Soup, stock, beef, home-prepared | 600 | ready | usda_172883 | 1/1/1 |
| Onions, raw | 40 | raw | usda_170000 | 1/1/1 |
| Onions, spring or scallions (includes tops and bulb), raw | 20 | raw | usda_170005 | 1/1/1 |
| Coriander (cilantro) leaves, raw | 10 | raw | usda_169997 | 1/1/1 |
| Ginger root, raw | 10 | raw | usda_169231 | 1/1/1 |
| Sauce, fish, ready-to-serve | 10 | ready | usda_174531 | 1/1/1 |
| Salt, table | 2 | ready | usda_173468 | 1/1/1 |
| Sugars, granulated | 4 | ready | usda_169655 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- 400 g sợi chín dùng profile Rice noodles cooked USDA làm tham khảo cho sợi gạo chín; hình dạng/công thức bánh phở có thể khác.
- 160 g bò sống dùng bò nạc top sirloin select USDA, không số liệu của mọi bắp/phi lê bò Việt.
- Nước dùng600 g lấy profile beef stock prepared USDA, không nước0 kcal; hớt mỡ và gia vị thay đổi giá trị thực tế.
- Thịt giữ 98% P/C,95% fat;1200 g thành phẩm ước tính; bỏ gia vị thơm nguyên đã lọc khỏi nước dùng.
- Đây là phương án hiệu chỉnh ID pho_beef hiện hữu, chỉ review; seed insert-only không tự cập nhật ID này.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://www.huongnghiepaau.com/pho-bo

### Thịt kho tiêu — vn_thit_kho_tieu

Khối lượng thành phẩm tham khảo 520 g; 4 suất; reference 130 g. kcal/P/C/F trên 100 g:262.4/15.64/3.75/20.72.

Cân bằng khối lượng giả định: 684-12-152=520 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Pork meat, medium fat, raw / Thịt lợn nửa nạc, nửa mỡ | 500 | raw | smiling2013_7018 | 0.95/0.95/0.9 |
| Shallots, raw | 15 | raw | usda_170499 | 1/1/1 |
| Garlic, raw | 10 | raw | usda_169230 | 1/1/1 |
| Spices, pepper, black | 4 | ready | usda_170931 | 1/1/1 |
| Oil, soybean, salad or cooking | 12 | ready | usda_171411 | 1/1/0.9 |
| Sauce, fish, ready-to-serve | 30 | ready | usda_174531 | 1/1/1 |
| Sugars, granulated | 10 | ready | usda_169655 | 1/1/1 |
| Salt, table | 3 | ready | usda_173468 | 1/1/1 |
| Beverages, water, tap, drinking | 100 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Chọn thịt nửa nạc nửa mỡ theo profile SMILING7018, không khẳng định là số đo của mọi loại nạc dăm.
- Giả định giữ 95% P/C và 90% fat trong thịt; dầu giữ 90%; phần mỡ/cặn bỏ12 g, nước bay hơi theo cân bằng khối lượng.
- Khối lượng mẻ 520 g là ước tính kỹ thuật, không số cân hay yield công bố.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/cong-thuc-nau-an/cach-lam-nac-dam-kho-tieu-thit-mem-sot-dam-da-thom-lung/

### Thịt kho trứng — vn_thit_kho_trung

Khối lượng thành phẩm tham khảo  1200 g; 6 suất; reference 200 g. kcal/P/C/F trên 100 g:181.4/11.96/3.47/13.39.

Cân bằng khối lượng giả định: 1395-20-175=1200 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Pork meat, medium fat, raw / Thịt lợn nửa nạc, nửa mỡ | 600 | raw | smiling2013_7018 | 0.95/0.95/0.9 |
| Chicken egg, whole, raw / Trứng gà | 300 | raw | smiling2013_9001 | 1/1/1 |
| Nuts, coconut water (liquid from coconuts) | 300 | ready | usda_170174 | 1/1/1 |
| Oil, soybean, salad or cooking | 10 | ready | usda_171411 | 1/1/0.9 |
| Sauce, fish, ready-to-serve | 30 | ready | usda_174531 | 1/1/1 |
| Sugars, granulated | 20 | ready | usda_169655 | 1/1/1 |
| Shallots, raw | 20 | raw | usda_170499 | 1/1/1 |
| Garlic, raw | 10 | raw | usda_169230 | 1/1/1 |
| Spices, pepper, black | 2 | ready | usda_170931 | 1/1/1 |
| Salt, table | 3 | ready | usda_173468 | 1/1/1 |
| Beverages, water, tap, drinking | 100 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Công thức tham khảo dùng600 g thịt nửa nạc nửa mỡ, không dùng dữ liệu này cho biến thể ba chỉ nhiều mỡ/trứng vịt.
- Trứng300 g phần không vỏ được định lượng theo gram, không tự quy đổi10 quả của recipe nguồn.
- Giữ95% P/C và 90% fat của thịt,90% dầu; bỏ20 g mỡ/cặn; mẻ 1200 g giả định gồm sốt còn lại.
- Nước dừa300 g là nước quả dừa theo USDA, không nước cốt dừa; không coi như nước0 kcal.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/cong-thuc-nau-an/thit-kho-trung-mon-an-truyen-thong-dam-vi-com-nha/

### Cá lóc kho tộ — vn_ca_loc_kho_to

Khối lượng thành phẩm tham khảo 600 g; 4 suất; reference 150 g. kcal/P/C/F trên 100 g:118.7/15.45/5.53/4.05.

Cân bằng khối lượng giả định: 769-5-164=600 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Fish, snake head, raw / Cá quả | 500 | raw | smiling2013_8022 | 0.98/0.98/0.98 |
| Garlic, raw | 15 | raw | usda_169230 | 1/1/1 |
| Shallots, raw | 20 | raw | usda_170499 | 1/1/1 |
| Ginger root, raw | 10 | raw | usda_169231 | 1/1/1 |
| Sauce, fish, ready-to-serve | 30 | ready | usda_174531 | 1/1/1 |
| Sugars, granulated | 20 | ready | usda_169655 | 1/1/1 |
| Spices, pepper, black | 2 | ready | usda_170931 | 1/1/1 |
| Oil, soybean, salad or cooking | 12 | ready | usda_171411 | 1/1/0.9 |
| Onions, spring or scallions (includes tops and bulb), raw | 10 | raw | usda_170005 | 1/1/1 |
| Beverages, water, tap, drinking | 150 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- 500 g là cá lóc phần ăn được, không500 g cá nguyên con; không dùng refuse nguyên con lần hai.
- Giữ98% P/C/F cá và 90% dầu; phần sốt được ăn; khối lượng mẻ 600 g giả định.
- Bản tham khảo bỏ tương ớt/bột ngọt không định lượng; gia vị chính đã ghi đủ, không giả là nguyên văn recipe.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/tin-tuc/huong-dan-cach-nau-ca-loc-kho-to-thom-ngon-dam-vi-cuc-de/

### Đậu phụ sốt cà chua — vn_dau_phu_sot_ca_chua

Khối lượng thành phẩm tham khảo 750 g; 4 suất; reference 187.5 g. kcal/P/C/F trên 100 g:95.9/6.35/3.99/6.18.

Cân bằng khối lượng giả định: 899.5-8-141.5=750 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Tofu, raw / Đậu phụ | 400 | raw | smiling2013_3025 | 1/1/1 |
| Tomato, raw / Cà chua | 300 | raw | smiling2013_4005 | 1/1/1 |
| Shallots, raw | 20 | raw | usda_170499 | 1/1/1 |
| Garlic, raw | 10 | raw | usda_169230 | 1/1/1 |
| Oil, soybean, salad or cooking | 28 | ready | usda_171411 | 1/1/0.857143 |
| Sauce, fish, ready-to-serve | 15 | ready | usda_174531 | 1/1/1 |
| Sauce, oyster, ready-to-serve | 8 | ready | usda_174529 | 1/1/1 |
| Sugars, granulated | 6 | ready | usda_169655 | 1/1/1 |
| Salt, table | 2 | ready | usda_173468 | 1/1/1 |
| Spices, pepper, black | 0.5 | ready | usda_170931 | 1/1/1 |
| Onions, spring or scallions (includes tops and bulb), raw | 10 | raw | usda_170005 | 1/1/1 |
| Beverages, water, tap, drinking | 100 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Đậu nguyên bản theoSMILING3025; không dùng profile đậu chiên cộng dầu lần hai.
- Dầu28 g cho vào, giả định 24 g giữ lại; không phải đo hấp thụ dầu. Mẻ750 g ước tính sau bay hơi và 8 g dầu/cặn bỏ.
- Mắm/dầu hào generic USDA để ước tính, nhãn từng hãng có thể khác; bỏ tương ớt trong biến thể định lượng này.
- Món này có mắm/dầu hào nên vẫn mang fish/seafood, không quảng cáo món chay.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/cong-thuc-nau-an/dau-hu-sot-ca-chua/

### Rau muống xào tỏi — vn_rau_muong_xao_toi

Khối lượng thành phẩm tham khảo 850 g; 5 suất; reference 170 g. kcal/P/C/F trên 100 g:48.3/3.29/4.22/2.15.

Cân bằng khối lượng giả định: 2922-2010-62=850 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Water spinach, raw / Rau muống | 800 | raw | smiling2013_4083 | 0.95/0.95/0.95 |
| Garlic, raw | 50 | raw | usda_169230 | 1/1/1 |
| Oil, soybean, salad or cooking | 20 | ready | usda_171411 | 1/1/0.9 |
| Sauce, fish, ready-to-serve | 10 | ready | usda_174531 | 1/1/1 |
| Salt, table | 2 | ready | usda_173468 | 1/1/1 |
| Beverages, water, tap, drinking | 2040 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- 800 g rau và 50 g tỏi theo công thức đã nghiên cứu; dầu20 g là lượng tham khảo tự chọn.
- Nước chần2000 g bỏ đi, nước40 g trong chảo; giữ 95% P/C/F rau sau chần+xào; dầu giữ 90%.
- Mẻ850 g là ước tính, không áp yield spinach cho rau muống. Bỏ hạt nêm/MSG, dùng muối/mắm định lượng.
- Fat 0 của rau muống lấy nguyên profile SMILING, không sửa NULL của bảng2007 thành0.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/tin-tuc/rau-muong-xao-toi/

### Cải ngọt luộc — vn_cai_ngot_luoc

Khối lượng thành phẩm tham khảo 480 g; 4 suất; reference 120 g. kcal/P/C/F trên 100 g:17.7/1.40/0.90/0.30.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Cải ngọt luộc ráo không gia vị | 480 | cooked | afcd3_F001988 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Plain unsalted reference variant uses published cooked F001988; -4% yield indicative, not measured locally.
- 500 g edible raw → 480 g modeled cooked; four servings120 g; min60/max240 are proposed planner bounds.
- Water for boiling discarded; no oil/seasoning/dipping sauce. Cooking loss already incorporated in cooked source, no repeated retention.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://www.foodstandards.gov.au/sites/default/files/2025-12/AFCD%20Release%203%20-%20Recipes.xlsx

### Cải thìa xào nấm — vn_cai_thia_xao_nam

Khối lượng thành phẩm tham khảo 430 g; 3 suất; reference 143.33 g. kcal/P/C/F trên 100 g:52.2/1.69/4.87/3.41.

Cân bằng khối lượng giả định: 485-5-50=430 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Cabbage, chinese (pak-choi), raw | 300 | raw | usda_170390 | 0.95/0.95/0.95 |
| Mushrooms, shiitake, raw | 100 | raw | usda_169242 | 0.95/0.95/0.95 |
| Garlic, raw | 10 | raw | usda_169230 | 1/1/1 |
| Ginger root, raw | 5 | raw | usda_169231 | 1/1/1 |
| Oil, soybean, salad or cooking | 12 | ready | usda_171411 | 1/1/0.9 |
| Oil, sesame, salad or cooking | 3 | ready | usda_171016 | 1/1/0.9 |
| Sauce, oyster, ready-to-serve | 10 | ready | usda_174529 | 1/1/1 |
| Sugars, granulated | 3 | ready | usda_169655 | 1/1/1 |
| Salt, table | 2 | ready | usda_173468 | 1/1/1 |
| Beverages, water, tap, drinking | 40 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Nấm100 g là nấm shiitake tươi theoUSDA, không100 g nấm khô hoặc sau ngâm không rõ.
- Giữ95% P/C/F rau/nấm,90% dầu,40 g nước cho sốt; mẻ 430 g ước tính.
- Dầu hào generic có seafood; dầu mè có sesame; không cam kết an toàn dị ứng.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://haithuycatering.com/menu/cai-thia-xao-nam-dong-co-chay-7.html

### Canh rau ngót thịt băm — vn_canh_rau_ngot_thit_bam

Khối lượng thành phẩm tham khảo 1100 g; 4 suất; reference 275 g. kcal/P/C/F trên 100 g:25.8/2.79/0.98/1.21.

Cân bằng khối lượng giả định: 1134.5-2-32.5=1100 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Sauropus, Leaves, raw / Rau ngót | 200 | raw | smiling2013_4086 | 1/1/1 |
| Pork meat, lean, raw / Thịt lợn nạc | 100 | raw | smiling2013_7017 | 1/1/1 |
| Oil, soybean, salad or cooking | 7 | ready | usda_171411 | 1/1/0.9 |
| Sauce, fish, ready-to-serve | 10 | ready | usda_174531 | 1/1/1 |
| Shallots, raw | 10 | raw | usda_170499 | 1/1/1 |
| Garlic, raw | 5 | raw | usda_169230 | 1/1/1 |
| Salt, table | 2 | ready | usda_173468 | 1/1/1 |
| Spices, pepper, black | 0.5 | ready | usda_170931 | 1/1/1 |
| Beverages, water, tap, drinking | 800 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Thịt heo nạc theoSMILING7017;800 g nước,7 g dầu tự chọn cho công thức tham khảo.
- Giữ toàn bộ nutrient trong nước canh và phần cái, không lọc/hớt mỡ; dầu90%;1100 g thành phẩm ước tính.
- Fat 0 của rau ngót là giá trị từ profile SMILING4086; source2007 fat NULL vẫn giữ nguyên.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/cong-thuc-nau-an/canh-rau-ngot-thit-bam-mon-canh-thanh-mat-de-nau-va-giau-dinh-duong/

### Canh bí đao thịt băm — vn_canh_bi_dao_thit_bam

Khối lượng thành phẩm tham khảo 1450 g; 5 suất; reference 290 g. kcal/P/C/F trên 100 g:30.5/2.92/1.12/1.63.

Cân bằng khối lượng giả định: 1553.5-3-100.5=1450 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Asgourd Waxgoured, Winter melon, raw / Bí đao (bí xanh) | 500 | raw | smiling2013_4002 | 1/1/1 |
| Pork meat, lean, raw / Thịt lợn nạc | 200 | raw | smiling2013_7017 | 1/1/1 |
| Oil, soybean, salad or cooking | 10 | ready | usda_171411 | 1/1/0.95 |
| Sauce, fish, ready-to-serve | 15 | ready | usda_174531 | 1/1/1 |
| Shallots, raw | 10 | raw | usda_170499 | 1/1/1 |
| Ginger root, raw | 5 | raw | usda_169231 | 1/1/1 |
| Onions, spring or scallions (includes tops and bulb), raw | 10 | raw | usda_170005 | 1/1/1 |
| Salt, table | 3 | ready | usda_173468 | 1/1/1 |
| Spices, pepper, black | 0.5 | ready | usda_170931 | 1/1/1 |
| Beverages, water, tap, drinking | 800 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Bí500 g phần ăn được, không gram mua cả vỏ; thịt200 g nạc.
- Nước800 g/dầu10 g là định lượng tham khảo; giữ 95% dầu, nutrient rau/thịt ở cả nước và cái;1450 g thành phẩm ước tính.
- Fat bí0 được công bố trong profileSMILING4002; không lấp NULL của profile2007.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://www.cet.edu.vn/cach-nau-canh-bi-dao-thit-bam

### Canh cà chua trứng — vn_canh_ca_chua_trung

Khối lượng thành phẩm tham khảo 960 g; 4 suất; reference 240 g. kcal/P/C/F trên 100 g:38.6/1.86/1.87/2.67.

Cân bằng khối lượng giả định: 1019.5-2-57.5=960 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Chicken egg, whole, raw / Trứng gà | 100 | raw | smiling2013_9001 | 1/1/1 |
| Tomato, raw / Cà chua | 360 | raw | smiling2013_4005 | 1/1/1 |
| Oil, soybean, salad or cooking | 14 | ready | usda_171411 | 1/1/0.95 |
| Sauce, fish, ready-to-serve | 8 | ready | usda_174531 | 1/1/1 |
| Shallots, raw | 10 | raw | usda_170499 | 1/1/1 |
| Onions, spring or scallions (includes tops and bulb), raw | 10 | raw | usda_170005 | 1/1/1 |
| Salt, table | 2 | ready | usda_173468 | 1/1/1 |
| Spices, pepper, black | 0.5 | ready | usda_170931 | 1/1/1 |
| Beverages, water, tap, drinking | 515 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Trứng100 g/cà chua360 g phần ăn được là công thức tự định lượng, không quy đổi giả2 trứng/3 quả thành gram.
- Nước500 g+15 g đánh trứng và dầu14 g định lượng theo cân dự kiến; giữ 95% dầu;960 g thành phẩm giả định.
- Dùng muối/mắm thay hạt nêm không rõ nhãn, không gán kcal theo suất trên trang recipe.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://cooponline.vn/cong-thuc-nau-an/canh-ca-chua-trung-mon-canh-thanh-mat-de-nau-va-day-dinh-duong/

### Bún riêu cua — vn_bun_rieu_cua

Khối lượng thành phẩm tham khảo 2800 g; 4 suất; reference 700 g. kcal/P/C/F trên 100 g:64.5/3.10/8.52/2.04.

Cân bằng khối lượng giả định: 3129-150-179=2800 g.

| Nguyên liệu / phần ăn được | Gram | Trạngthái | Source ID / code | Retention P/C/F |
|---|---:|---|---|---|
| Crab, fresh water, raw / Cua đồng | 310 | raw | smiling2013_8034 | 0.8/0.8/0.8 |
| Chicken egg, whole, raw / Trứng gà | 100 | raw | smiling2013_9001 | 1/1/1 |
| Rice noodles, cooked | 800 | cooked | usda_168914 | 1/1/1 |
| Tofu, fried | 120 | ready | usda_172451 | 1/1/1 |
| Tomato, raw / Cà chua | 300 | raw | smiling2013_4005 | 1/1/1 |
| Garlic, raw | 15 | raw | usda_169230 | 1/1/1 |
| Shallots, raw | 20 | raw | usda_170499 | 1/1/1 |
| Onions, spring or scallions (includes tops and bulb), raw | 20 | raw | usda_170005 | 1/1/1 |
| Sauce, fish, ready-to-serve | 20 | ready | usda_174531 | 1/1/1 |
| Sugars, granulated | 8 | ready | usda_169655 | 1/1/1 |
| Salt, table | 4 | ready | usda_173468 | 1/1/1 |
| Oil, soybean, salad or cooking | 12 | ready | usda_171411 | 1/1/0.9 |
| Beverages, water, tap, drinking | 1400 | ready | usda_173647 | 1/1/1 |

Giả định / biến thể, không phải số đo:

- Cua1000 g nguyên con: dùng31% phần ăn được tham khảo từ bảngVN2007 code8034 refuse 69%, không số đo lọc riêu. Phần input310 g edible, giữ 80% P/C/F khi lọc; uncertainty lớn.
- Bún800 g CHÍN dùng Rice noodles cooked USDA tham khảo, không sợi khô.
- Đậu chiên120 g dùng profile Tofu fried USDA; không cộng dầu chiên lần hai;12 g dầu riêng là dầu xào cà chua, giữ 90%.
- Mẻ2800 g gồm nước và topping ước tính; không gán dinh dưỡng thịt cua cho cả xác cua, không dùng cua biển thay cua đồng.
- Công thức đơn giản khác bản nguồn có huyết/trứng vịt/tôm khô; source profile/raw → riêu là ước lượng, confidence thấp hơn canh/rau.

Recipe đã nghiên cứu trước (không phải nguồnnutrient cả món): https://www.huongnghiepaau.com/bun-rieu-cua

## Trạng thái và review

12 READY_ESTIMATED đủ đề xuất review, chưa duyệt import. Phở/bún riêu có mức tin cậy thấp
hơn vìnguồn tham khảo sợi/nước dùng/cut bò và recovery cua. Các biến thể nhà hàng khác tỉ lệmỡ/dầu/
topping sẽkhác. Bún riêu ở đây không huyết/tôm khô; thịt kho trứng dùng thịt nửa nạc/mỡ,
trứng gà; cải ngọtplain không nêm. Nếu nhóm cần biến thể khác thì định lượng và tính lại,
không đổi Dish ID đã tham chiếu hoặc nhân kcal theo tên món.

Registry 56 profiles lưu cả nguồn cũ và mới; sourceverified chỉ xác nhận đã đọc/chép đúng,
không có nghĩa recipe ước tính được đo phòng lab. NguồnURL/code giả, fat NULL, trạngthái
raw/cooked sai, massbalance/macro sai hoặc giả định không ghi rõ vẫn bịvalidator chặn.

---


## Hồ sơ nguồn lịch sử — giữ để truy nguyên, không còn chặn estimate thiếu cân thực tế

# Vietnamese Food Catalog V2 — nguồn và phương pháp

Kiểm tra ngày 2026-10-11. Đây là nghiên cứu/DRAFT, không phải dataset được phép import.
Không sao chép toàn bộ sách, bảng hoặc hướng dẫn nấu ăn vào repository.

## Nguồn dinh dưỡng

| Nguồn | Đã xác minh | Phạm vi sử dụng và giới hạn |
|---|---|---|
| [Viện Dinh dưỡng, Bảng thành phần thực phẩm Việt Nam 2007, bản tại FAO](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf) | Đọc được PDF 567 trang; đúng tác giả/ấn bản, phần giới thiệu và danh mục thực phẩm | Ưu tiên đối chiếu nguyên liệu Việt. Chưa trích số dinh dưỡng cho 40 DRAFT, chưa xác minh quyền tái phân phối hàng loạt. Không coi tên món tương tự là đúng trạng thái nguyên liệu |
| [FAO/INFOODS, danh mục châu Á](https://www.fao.org/infoods/infoods/tables-and-databases/asia/en/) | Trang có nguồn Vietnam/SMILING 2013 và bảng reference/quality | Link tương đối bị 404; URL tuyệt đối trả XLSX nhưng công cụ web không đọc nội dung. Chưa dùng giá trị dinh dưỡng trong workbook |
| [USDA FoodData Central, API Guide — Licensing](https://fdc.nal.usda.gov/api-guide/) | Tài liệu xác nhận dữ liệu FDC thuộc public domain/CC0 | Dùng bổ trợ cho nguyên liệu và đúng trạng thái chế biến. Không dùng công thức USDA để tự gọi là món Việt. URL food-details thử ở mã 171705 trả 404, không kết luận source ID sai chỉ vì trang UI không đọc được |
| [USDA SR Legacy 2018-04 CSV](https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip) | Source/release đã ghi trong provenance hiện có; lần này không tải lại archive hoặc tái xác minh từng giá trị nguồn | 63 record đang dùng dữ liệu tham khảo từ release này. Snapshot MySQL khớp seed trên các field runtime được so sánh; điều đó không chứng nhận công thức Việt hoặc khẩu phần |

Bản 2017 chưa được xác minh trong phiên này; không gán nhãn 2017 cho số liệu 2007.
Khả năng đọc PDF công khai không chứng minh quyền sao chép hàng loạt. Cần kiểm tra
điều kiện của chủ sở hữu trước khi phát hành lại một dataset dựa trên bảng đó.

Carbs và fiber cần giữ phương pháp nguồn: glucid/celluloza trong bảng Việt không
tự động đồng nhất carbohydrate-by-difference/total dietary fiber của nguồn khác.
Missing là null, không tự biến thành 0. 4/4/9 chỉ dùng kiểm tra plausibility;
năng lượng công bố có thể dùng hệ số khác. Không ghi đè kcal nguồn bằng phép kiểm này.

## Nguồn công thức — không phải nguồn dinh dưỡng

| Món nghiên cứu | Công thức được đọc | Dữ kiện có thể ghi nhận | Vì sao vẫn PENDING |
|---|---|---|---|
| Thịt kho tiêu | [Món Ngon Mỗi Ngày: Thịt kho](https://monngonmoingay.com/thit-kho/) | Thịt ba chỉ 300 g, dầu 7 g; các gia vị có đơn vị gia dụng | Tên nguồn là Thịt kho; cần xác nhận biến thể tiêu. Chưa đủ gram gia vị/nhãn gói nêm/yield/nguồn từng nguyên liệu |
| Rau muống xào tỏi | [Co.op Online](https://cooponline.vn/tin-tuc/rau-muong-xao-toi/) | Rau 800 g, tỏi 50 g; dầu được dùng nhưng không định lượng | Chưa biết dầu giữ lại, gram gia vị và khối lượng sau nấu |
| Canh tôm rau ngót bắp | [Món Ngon Mỗi Ngày: Canh tôm bồ ngót](https://monngonmoingay.com/canh-tom-bo-ngot-2/) | Tôm 100 g, rau 100 g, bắp 120 g; dầu 12 g; nước dùng 1 lít | Chưa rõ edible basis của tôm/bắp, thành phần nước dùng, gram hành/gia vị đầy đủ và yield |
| Canh khổ qua nhồi thịt và cá | [Món Ngon Mỗi Ngày](https://monngonmoingay.com/canh-kho-qua-ham-thit/) | Thịt heo 100 g, cá thác lác 50 g; khổ qua/miến/nấm dùng đơn vị gia dụng | Không bỏ cá khỏi recipe/tags. Chưa có gram đủ, lượng nước, edible basis, yield và nutrient matching |

Chỉ ghi dữ kiện cần thiết và URL, không sao chép lời hướng dẫn/ảnh hoặc tuyên bố
điều trị trên website. Kcal theo suất do website công thức công bố không được tự
quy về kcal/100 g khi chưa có mẫu số khối lượng. Thời gian "thực hiện" có thể không
gồm chuẩn bị/ngâm/ướp; prep_minutes vẫn null trong DRAFT này.
36 DRAFT khác mới có danh sách nguyên liệu cần nghiên cứu, chưa có công thức đã
được xác minh. Ingredient lists là outline, ingredient_list_complete=false.

## Cách tính sau khi đã có đủ bằng chứng

Tham khảo [FAO, tính dinh dưỡng từ recipe](https://www.fao.org/4/y4705e/y4705e23.htm)
và [FAO/INFOODS Recipes](https://www.fao.org/infoods/infoods/recipes/en/).

1. Chốt một công thức đại diện. Ghi nguyên liệu, gram phần ăn được, trạng thái
   sống/chín và mã thực phẩm nguồn của từng nguyên liệu. Không dùng gram sống với
   profile chín; không tự xem nước dùng là nước có zero nutrient.
2. Ghi dầu, đường, nước mắm/nước tương, nước cốt dừa, lạc/mè và các gia vị có năng
   lượng. Đơn vị muỗng/chén/trái cần gram đo được hoặc nguồn conversion phù hợp.
3. Nếu dùng nguyên liệu sống để tính món nấu, ghi yield/retention phù hợp và bằng
   chứng; tính phần bỏ đi, nước/dầu bị mất hoặc giữ lại. Không tự đặt hệ số bằng 1.
4. Cân thành phẩm ăn được sau nấu, gồm phần nước canh thực sự sử dụng. Không suy
   finished_weight từ tổng gram sống hoặc từ số suất.
5. Với nutrient n: tổng n = tổng(m_i × n_i/100 × retention_i), sau khi hiệu chỉnh
   phần ăn được và các dòng thất thoát/thu thêm. n/100 g thành phẩm = tổng n ×
   100/finished_edible_grams. Dữ liệu chín trực tiếp chỉ dùng với khối lượng chín
   tương ứng; tránh hiệu chỉnh yield/retention hai lần.
6. Đối chiếu kcal/P/C/F, nguồn/cách xác định carbs/fiber và sai khác với 4/4/9.
   Sai khác cần lời giải thích; không coi sai khác nào cũng là lỗi và không bỏ
   kiểm tra. Validator offline dùng mức 20% chỉ để yêu cầu explanation, không là
   tiêu chuẩn kiểm định dinh dưỡng.
7. Review reference/min/max theo món và phần ăn được. Không mặc định mọi món
   gấp đôi reference đều hợp lý; không lấy min/max kỹ thuật làm khẩu phần được
   chuyên gia chứng nhận. Ghi provenance, estimated=true cho số tính từ recipe.

## Điều kiện READY và ánh xạ sau này

READY nghĩa là đủ bằng chứng để review, vẫn không đồng nghĩa được phép import.
Giữ JSON DRAFT riêng; tất cả active=false/import_ready=false/not_importable=true.
Chưa có exporter hoặc chế độ --apply cho dữ liệu này.

Các field cơ bản khớp shape runtime: dish_id, name, type, preparation_state,
reference_grams/min_grams/max_grams, calories_per_100g, macros_per_100g,
ingredients (tags), meal_types, prep_minutes, provenance, estimated.
Recipe ingredient amounts/source/state/yield và tài liệu nằm trong provenance.recipe
và nutrition_references; tương lai có thể lưu trong ProvenanceJson, không cần
thay bảng core. baseline_snapshot là evidence đối chiếu, không phải dữ liệu mới
và không được export vào một lần import mới.

Seed hiện tại chỉ INSERT ID chưa có và bỏ qua ID cũ; không thể dùng nó để âm thầm
sửa dinh dưỡng/tags của 9 DRAFT review-existing. Nếu cần hiệu chỉnh catalog đang
active, phải có kế hoạch version/update được duyệt riêng; snapshot cũ giữ nguyên.

Tags phải phản ánh nước mắm (fish/seafood), mắm tôm (seafood), trứng, đậu phụ,
sữa, lạc, mè, nước dùng và phụ gia có thành phần cần tránh. DRAFT có tag peanut
nhưng API hiện chưa cho người dùng nhập avoid peanut/sesame; không tuyên bố đã
hỗ trợ tránh dị ứng. Gói nêm, dầu pha và nước dùng chưa rõ nguyên liệu thì record
vẫn PENDING. Không có bảo đảm an toàn dị ứng hoặc lây nhiễm chéo.

## Phase 2 — kiểm tra ngày 2026-10-12

Giữ nghiên cứu Phase 1 ở trên và trong `research_history` của 12 record được
review. Không coi kết quả đọc web là cân thực nghiệm hoặc phân tích phòng lab.
Các con số dưới là dữ kiện nguyên liệu/định lượng, không phải dinh dưỡng món chín.

### Bảng nguyên liệu có mã truy xuất

Đối chiếu trực tiếp [Bảng Việt Nam 2007 tại FAO](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf).
Registry: [ingredient_sources.json](../setup/drafts/vietnamese_catalog_v2/ingredient_sources.json).
Locator lưu trang PDF **1-based** và trang in, không dùng số dòng của công cụ web.
Các chỉ tiêu dưới tính trên 100 g **phần ăn được của nguyên liệu nguồn**.

| Code | Nguyên liệu nguồn | Trang PDF / trang in | kcal | P / glucid / fat (g) |
|---|---|---|---:|---|
| 3025 | Đậu phụ | 91 / 74 | 95 | 10,9 / 0,7 / 5,4 |
| 7016 | Thịt lợn mỡ | 320 / 294 | 394 | 14,5 / 0 / 37,3 |
| 7017 | Thịt lợn nạc | 321 / 295 | 139 | 19 / 0 / 7 |
| 7018 | Thịt lợn nửa nạc, nửa mỡ | 322 / 296 | 260 | 16,5 / 0 / 21,5 |
| 8022 | Cá quả | 410 / 382 | 97 | 18,2 / 0 / 2,7 |
| 4083 | Rau muống | 185 / 165 | 25 | 3,2 / 2,1 / 0,4 |
| 4086 | Rau ngót | 188 / 168 | 35 | 5,3 / 3,4 / chưa có |
| 4002 | Bí đao | 104 / 84 | 12 | 0,6 / 2,4 / chưa có |
| 4015 | Cải thìa | 117 / 97 | 17 | 1,4 / 2,4 / 0,2 |
| 4005 | Cà chua | 107 / 87 | 20 | 0,6 / 4 / 0,2 |
| 4103 | Tỏi ta | 205 / 185 | 121 | 6 / 23 / 0,5 |
| 9001 | Trứng gà nguyên quả | 450 / 420 | 166 | 14,8 / 0,5 / 11,6 |
| 1013 | Bánh phở | 26 / 13 | 143 | 3,2 / 31,7 / 0,4 |
| 1020 | Bún | 33 / 20 | 110 | 1,7 / 25,7 / chưa có |

Code 7016/7018 không tự chứng minh match ba chỉ/nạc dăm/thịt băm thực tế. Bảng
8022 tính phần ăn được, không phải 500 g cá mua hoặc cả xương; refuse tham khảo
không được tự áp dụng cho cá đã sơ chế. Code 3025 và 9001 ghi raw trong tên
tiếng Anh. Các trạng thái chưa rõ được đánh dấu `state_verified=false` để chặn
tính recipe. **Không dùng 4014 cải soong thay cải ngọt.**

Dấu gạch ở fat được giữ NULL. Chỉ tiêu celluloza được lưu riêng;
`nutrients_per_100g.fiber=null` vì chưa chứng minh đây là total dietary fiber.
Không ghép cột fat/fiber từ USDA vào cùng record Việt để lấp chỗ trống.
Quyền tái phân phối bảng Việt vẫn PENDING; không import hoặc xuất bản dataset
runtime dựa vào các record này trước review quyền dùng.

[USDA API Guide](https://fdc.nal.usda.gov/api-guide/) xác nhận dữ liệu FDC public
domain/CC0. Phase 2 chưa trích profile USDA mới; không gán mã FDC hoặc giá trị
chưa đọc. Dầu đúng loại, nước dừa, nấm đúng dạng, cut thịt và nước chấm là các
ứng viên đối chiếu USDA/Vietnam tiếp theo, không dùng proxy tự động.

### Nguồn recipe của 12 món

| ID | Nguồn trực tiếp đã đọc | Dữ kiện / thiếu hụt quyết định |
|---|---|---|
| vn_thit_kho_tieu | [Co.op: nạc dăm kho tiêu](https://cooponline.vn/cong-thuc-nau-an/cach-lam-nac-dam-kho-tieu-thit-mem-sot-dam-da-thom-lung/) | Thịt 500 g; hành 15 g, tỏi 10 g, tiêu 4 g, đường 10 g, muối 3 g; dầu 15 ml, mắm 30 ml, nước 50 ml. Biến thể nạc dăm, chưa match cut/yield/density |
| vn_thit_kho_trung | [Co.op: thịt kho trứng](https://cooponline.vn/cong-thuc-nau-an/thit-kho-trung-mon-an-truyen-thong-dam-vi-com-nha/) | Ba chỉ 1 kg, 10 trứng gà, nước dừa 400 ml. Trứng/củ/tép/muỗng chưa có gram phần ăn được; không gán hột vịt/trứng cút cùng profile |
| vn_ca_loc_kho_to | [Co.op: cá lóc kho tộ](https://cooponline.vn/tin-tuc/huong-dan-cach-nau-ca-loc-kho-to-thom-ngon-dam-vi-cuc-de/) | Cá 500 g; lượng mắm/đường/dầu theo muỗng, gồm cả bước ướp và nước màu. Chưa rõ gross/net, phần xương bỏ, dầu/sốt còn lại |
| vn_dau_phu_sot_ca_chua | [Co.op: đậu hũ sốt cà chua](https://cooponline.vn/cong-thuc-nau-an/dau-hu-sot-ca-chua/) | Đậu 400 g, cà chua 300 g, dầu 2 muỗng canh; có nước mắm và dầu hào. Thiếu gram gia vị/dầu giữ lại; không đánh dấu chay |
| vn_rau_muong_xao_toi | [Co.op: rau muống xào tỏi](https://cooponline.vn/tin-tuc/rau-muong-xao-toi/) | Giữ 800 g rau làm sạch, 50 g tỏi của Phase 1. Không có lượng dầu; thiếu nhãn nêm và khối lượng sau xào |
| vn_cai_ngot_luoc | [Kingfoodmart: cải ngọt luộc](https://kingfoodmart.com/bai-viet/cach-luoc-rau-cai-ngot-xanh-muot) | 500 g rau cho 5 người; bột ngọt có mâu thuẫn canh/cà phê giữa danh sách và bước nấu. Không suy 100 g thành phẩm/người |
| vn_cai_thia_xao_nam | [Hai Thụy: cải thìa xào nấm đông cô](https://haithuycatering.com/menu/cai-thia-xao-nam-dong-co-chay-7.html) | Rau khoảng 300 g, nấm 100 g nhưng có bước ngâm; chưa biết khô/hydrated. Thiếu dầu; có dầu mè/dầu hào, cần nhãn |
| vn_canh_rau_ngot_thit_bam | [Co.op: canh rau ngót thịt băm](https://cooponline.vn/cong-thuc-nau-an/canh-rau-ngot-thit-bam-mon-canh-thanh-mat-de-nau-va-giau-dinh-duong/) | Rau 200 g, thịt 100 g; lượng nước không có, mắm/hành xuất hiện ở bước nấu. Không dùng kcal theo suất thay tính recipe |
| vn_canh_bi_dao_thit_bam | [CET: canh bí đao thịt bằm](https://www.cet.edu.vn/cach-nau-canh-bi-dao-thit-bam) | Bí 500 g, thịt 200 g, nước 500 ml; chưa rõ gram sau gọt, cỡ thìa dầu, nhãn nêm và yield |
| vn_canh_ca_chua_trung | [Co.op: canh cà chua trứng](https://cooponline.vn/cong-thuc-nau-an/canh-ca-chua-trung-mon-canh-thanh-mat-de-nau-va-day-dinh-duong/) | 2 trứng, 3 cà chua, 500 ml nước và nước thêm vào trứng; thiếu gram món/giá vị và cân thành phẩm |
| pho_beef | [Hướng Nghiệp Á Âu: phở bò](https://www.huongnghiepaau.com/pho-bo) | Xương 2 kg, phi lê 1,2 kg, bắp 0,7 kg, bánh phở 1 kg. Thiếu lượng nước sau lọc/hớt mỡ và cấu trúc mỗi tô; không tính xương là thịt ăn |
| vn_bun_rieu_cua | [Hướng Nghiệp Á Âu: bún riêu cua](https://www.huongnghiepaau.com/bun-rieu-cua) | Cua gross 1 kg, tôm khô 50 g, huyết hấp 500 g, đậu chiên 300 g; nước lọc cua 3 lít. Thiếu yield lọc cua, gram bún/topping theo tô và dầu thực giữ lại |

Một số trang không đọc được bằng web tool; đã đọc đúng phần nguyên liệu qua HTTP
200 trong bộ nhớ cho thịt kho trứng, cải thìa xào nấm và phở bò. Không lưu HTML,
hình ảnh hoặc hướng dẫn nấu nguyên văn. Kcal theo suất do trang recipe công bố
chỉ là thông tin chưa được kiểm chứng, không dùng làm dinh dưỡng runtime.

Nguồn [CJ Thịt kho tiêu](https://cjfoods.com.vn/recipes/thit-kho-tieu/) có mô tả
kimchi không khớp tiêu đề và dùng xốt premix chưa đủ thành phần; giữ như nguồn
đã loại khỏi phép tính, không REJECTED món thịt kho tiêu. Công thức Phase 1
Món Ngon Mỗi Ngày vẫn được bảo toàn trong research_history.

### Phương pháp và bước còn thiếu

Theo [FAO recipe calculation](https://www.fao.org/4/y4705e/y4705e23.htm) và
[FAO/INFOODS Recipes](https://www.fao.org/infoods/infoods/recipes/en/): tính tổng
từng nutrient từ đúng gram phần ăn được, đúng trạng thái và retention phù hợp;
chia cho gram thành phẩm được ăn sau hiệu chỉnh nước/mỡ/phần bỏ. Không áp dụng
yield/retention hai lần cho profile đã chín. Không dùng nước hầm/xốt như nước
zero nutrient hoặc cân bằng gram sống = gram món chín.

Validator offline mới yêu cầu nguồn được liên kết, state và edible basis đã
review, retention có evidence và finished weight được xác minh. Nếu thiếu bất
kỳ nguyên liệu/gram/PCF/mẫu số nào, phép tính trả `BLOCKED`, `per_100g=null`,
không tính phần thiếu như 0. Các fixture số học trong tests là dữ liệu nhân tạo
để kiểm tra công thức, không phải số dinh dưỡng của 12 món này.
