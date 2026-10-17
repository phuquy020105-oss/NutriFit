# Vietnamese Food & Recipe Catalog — bản trình duyệt v0.1

- Ngày thiết kế/tra cứu: **17/10/2026**, múi giờ Asia/Bangkok.
- Nhánh đối chiếu: `feature/java-nutrition`; source và schema được đọc tại thời điểm lập tài liệu.
- Trạng thái toàn bộ tên món, lựa chọn nguyên liệu, gram, phương pháp nấu: **PROPOSED — CHƯA PHÊ DUYỆT**.
- Phạm vi: 30 Recipe (10 mỗi bữa), 82 Food riêng biệt, 383 liên kết Recipe–Food. Không thêm món thứ 31.
- **Chưa đủ điều kiện tạo SQL/seed**: 0 Food có đủ năm trường dinh dưỡng được xác minh và chuẩn hóa cho ứng dụng; 4 Food có số liệu nguồn một phần, 78 Food chưa chốt bản ghi nguồn.
- Đây là công thức định lượng để xem xét, không phải khẩu phần chuẩn khoa học, không phải khuyến nghị điều trị. Chưa tính tổng calories/macro của bất kỳ món nào khi dữ liệu đầu vào chưa đủ.
- Chỉ tạo tài liệu này. Không sửa Java/JSP/CSS/schema, không tạo seed SQL, không kết nối MySQL, không chạy Maven/test/migration/deploy.

## A. Kết quả phân tích schema và code

### A1. Bảng foods

Đối chiếu [schema.sql, dòng 70](../../database/schema.sql#L70):

| Cột | Kiểu / ràng buộc thực tế | Ý nghĩa với catalog |
|---|---|---|
| food_id | BIGINT UNSIGNED, AUTO_INCREMENT, PRIMARY KEY | DB sinh ID; Fxxx trong tài liệu không phải ID này |
| name | VARCHAR(200), NOT NULL | Không có UNIQUE; tên phải thể hiện trạng thái/cắt thịt/thực phẩm để tránh mơ hồ |
| calories_per_100g | DECIMAL(10,3), NOT NULL, DEFAULT 0 | kcal trên 100 g phần ăn được đúng trạng thái |
| protein_per_100g | DECIMAL(10,3), NOT NULL, DEFAULT 0 | g/100 g |
| carbs_per_100g | DECIMAL(10,3), NOT NULL, DEFAULT 0 | g/100 g; phải chốt định nghĩa carbohydrate |
| fat_per_100g | DECIMAL(10,3), NOT NULL, DEFAULT 0 | g/100 g |
| fiber_per_100g | DECIMAL(10,3), NOT NULL, DEFAULT 0 | g/100 g; schema không định nghĩa phương pháp chất xơ |
| active | BOOLEAN, NOT NULL, DEFAULT TRUE | Food inactive làm Recipe chứa nó không được chọn |

CHECK yêu cầu cả năm số không âm; giới hạn dương DECIMAL(10,3) là 9,999,999.999. **DEFAULT 0 không phải bằng chứng số liệu dinh dưỡng bằng 0**. Một bản ghi tạo thiếu cột có thể trông hợp lệ với code nhưng sai dữ liệu; công cụ seed sau này phải bắt buộc đủ năm giá trị có nguồn.

Không có cột: mã catalog, trạng thái sống/chín, loài/cắt thịt, edible fraction, nguồn, mã nguồn, ngày xác minh, phương pháp chất xơ, phiên bản hay đơn vị khối lượng. Không bổ sung cột trong nhiệm vụ này: tên chuẩn và tài liệu/manifest ngoài DB phải lưu những thông tin đó.

### A2. Bảng recipes

Đối chiếu [schema.sql, dòng 82](../../database/schema.sql#L82):

| Cột | Kiểu / ràng buộc thực tế | Quy ước đề xuất |
|---|---|---|
| recipe_id | BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY | Không cố định ID theo số thứ tự Rxxx |
| name | VARCHAR(200) NOT NULL | Giữ 30 tên đề xuất, bổ sung mô tả phiên bản trong instructions |
| meal_type | ENUM BREAKFAST/LUNCH/DINNER NOT NULL | Một Recipe đúng một loại bữa |
| base_servings | DECIMAL(8,2) NOT NULL DEFAULT 1, CHECK > 0 | Tất cả công thức dưới đây: 1.00 |
| instructions | TEXT, nullable | Chứa hướng dẫn, phần ăn, lưu ý chế biến được duyệt |
| image_url | VARCHAR(1000), nullable | Chưa đề xuất ảnh; để thiếu, không tạo URL giả |
| prep_minutes | INT UNSIGNED, nullable | Đề xuất số phút ở D; cần thống nhất tổng thời gian hay chỉ chuẩn bị |
| active | BOOLEAN NOT NULL DEFAULT TRUE | Chỉ bật sau khi thành phần và nguồn đạt yêu cầu |

Không có UNIQUE tên hoặc (name, meal_type); không có cột tổng dinh dưỡng. Không lưu cứng kcal/macro vào recipes. `prep_minutes` chưa có code tính lịch nấu; các phút dưới đây là ước tính xử lý một suất, có nguyên liệu nền chín, không tính ninh nước dùng theo mẻ. Nếu nhóm hiểu cột này chỉ là sơ chế, cần đổi quy ước trước khi seed.

### A3. Bảng recipeingredients và khóa ngoại

Đối chiếu [schema.sql, dòng 94](../../database/schema.sql#L94):

| Cột | Kiểu / ràng buộc |
|---|---|
| ingredient_id | BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY |
| recipe_id | BIGINT UNSIGNED NOT NULL; FK → recipes.recipe_id; ON DELETE CASCADE |
| food_id | BIGINT UNSIGNED NOT NULL; FK → foods.food_id; ON DELETE RESTRICT |
| quantity_grams | DECIMAL(10,2) NOT NULL; CHECK > 0; tối đa 99,999,999.99 |
| Index | idx_ingredient_recipe, idx_ingredient_food; không có UNIQUE (recipe_id, food_id) |

Một Recipe có nhiều dòng Ingredient; mỗi dòng trỏ đúng một Food. Food có thể được nhiều Recipe tham chiếu. Không có quan hệ Recipe lồng Recipe, không có cột nhóm thành phần/nước sốt, không có đơn vị ml/quả/thìa. Tài liệu gộp cùng Food vào **một dòng mỗi Recipe**, ghi phân bổ ở hướng dẫn khi dùng cho nhiều phần.

Recipe đã có MealEntry tham chiếu còn bị FK từ mealentries với ON DELETE RESTRICT. Không xóa/đánh số lại Food/Recipe hoặc sửa snapshot để seed.

### A4. Điều kiện Recipe hợp lệ trong ứng dụng

Đối chiếu [JdbcRecipeReadAdapter](../../src/main/java/com/nutrifit/dao/JdbcRecipeReadAdapter.java), [RecipeNutritionInput](../../src/main/java/com/nutrifit/dto/RecipeNutritionInput.java), [IngredientNutritionLine](../../src/main/java/com/nutrifit/dto/IngredientNutritionLine.java):

1. Recipe tồn tại, active, ID > 0, tên không trống; meal_type hợp lệ; base_servings > 0.
2. Có ít nhất một nguyên liệu; mọi Food tồn tại, active, ID > 0; gram > 0.
3. Cả năm số dinh dưỡng không null, không âm. Thiếu/sai thành phần làm loại **cả Recipe**, không bỏ riêng thành phần rồi tính thiếu.
4. Danh sách candidate đọc theo lô, không còn giới hạn 200 Recipe. Một khẩu phần không lưu được vì overflow bị loại khỏi danh sách; SQL lỗi vẫn được báo lỗi.
5. FoodCatalogDAO chỉ hiển thị Food active, sắp theo name/food_id; không xác minh nguồn, không phân biệt raw/cooked ngoài tên.
6. Code không phát hiện “0 giả”, nguồn sai, raw/cooked không khớp hoặc dòng Ingredient trùng. Đây là cổng duyệt dữ liệu bắt buộc bên ngoài code.

### A5. Công thức dinh dưỡng, Meal Planner và Recommendations

[NutritionCalculator](../../src/main/java/com/nutrifit/service/NutritionCalculator.java) áp dụng riêng từng chất:

```text
whole_recipe = Σ(quantity_grams_i / 100 × nutrient_per_100g_i)
entry_nutrient = whole_recipe × servings / base_servings
```

Tính bằng BigDecimal; chia cuối và làm tròn HALF_UP đến 3 số lẻ. [NutritionFacts.toMealEntry](../../src/main/java/com/nutrifit/dto/NutritionFacts.java#L45) chặn kết quả sau làm tròn > 999,999,999.999 của DECIMAL(12,3). Servings phải > 0, tối đa 999,999.99 và biểu diễn được bằng 2 số lẻ; không tự làm tròn khẩu phần.

[MealPlannerService](../../src/main/java/com/nutrifit/service/MealPlannerService.java) kiểm tra bữa của Recipe, lấy/tạo plan user/ngày, lưu tên và năm số snapshot. Chọn món là đã ăn; thêm cùng recipe/cùng bữa cộng khẩu phần và scale snapshot cũ. Sửa khẩu phần cùng món không đọc lại công thức mới. Đổi sang món khác lấy snapshot mới; đổi sang món đã có cùng bữa bị từ chối. Các ngày cũ chỉ đọc.

[MealRecommendationService](../../src/main/java/com/nutrifit/service/MealRecommendationService.java) yêu cầu Premium tại Service; lọc đúng meal_type, loại Recipe có Food ID DISLIKE, cộng 10 điểm cho mỗi Food ID LIKE khác nhau và tối đa 5 điểm theo độ gần 1/3 target_kcal mỗi khẩu phần. Thiếu target dương thì bỏ điểm mục tiêu; không tự tính mục tiêu. Đây không phải bộ tối ưu cân đối protein/carbs/fat/fiber. Không chấm điểm dinh dưỡng các món ở tài liệu khi số liệu còn thiếu.

**Giới hạn Preferences:** so khớp Food ID chính xác, không theo loài/nhóm. F012 ức gà và F013 đùi gà có da là hai Food; dislike một Food không tự lan sang Food kia. Nước dùng, chả, mắm, hành phi là Food hợp phần; nguyên liệu ẩn bên trong không được code duyệt đệ quy. Catalog này không bảo đảm tránh dị ứng hoặc tránh mọi dạng của một loài.

## B. Danh mục 30 món

Giữ nguyên tên và phân bữa từ đề xuất của người quản lý. Tên bữa là nhãn sử dụng của catalog, không khẳng định món chỉ phù hợp ăn ở bữa đó. Mỗi món có **base_servings = 1.00**, trạng thái PROPOSED. Nhóm “suất cơm” chỉ gồm đúng cơm, món chính và phần rau/canh kê ở D; không mặc định thêm canh, tráng miệng hoặc đồ uống.

| Mã | Tên món đề xuất | Meal type | Phạm vi một suất | Base servings | Trạng thái |
|---|---|---|---|---:|---|
| R001 | Phở bò | BREAKFAST | Một tô phở bò chín, không quẩy. | 1.00 | PROPOSED |
| R002 | Phở gà | BREAKFAST | Một tô phở ức gà bỏ da. | 1.00 | PROPOSED |
| R003 | Bánh mì trứng | BREAKFAST | Một ổ bánh mì với trứng rán và rau, không pate/bơ. | 1.00 | PROPOSED |
| R004 | Bún bò Huế | BREAKFAST | Một tô bún bò bắp; chưa gồm giò heo, huyết hoặc chả. | 1.00 | PROPOSED |
| R005 | Hủ tiếu Nam Vang | BREAKFAST | Một tô hủ tiếu nước với heo, gan, tôm và trứng cút. | 1.00 | PROPOSED |
| R006 | Cháo gà | BREAKFAST | Một tô cháo gạo với ức gà, rau răm. | 1.00 | PROPOSED |
| R007 | Bánh cuốn | BREAKFAST | Một suất bánh cuốn nhân heo/nấm kèm chả và nước chấm. | 1.00 | PROPOSED |
| R008 | Bún riêu | BREAKFAST | Một tô bún riêu cua đồng, đậu hũ trắng và cà chua. | 1.00 | PROPOSED |
| R009 | Xôi gà | BREAKFAST | Một suất xôi gà có da, nấm và hành phi. | 1.00 | PROPOSED |
| R010 | Bánh canh cua | BREAKFAST | Một tô bánh canh gạo với cua biển. | 1.00 | PROPOSED |
| R011 | Cơm tấm sườn | LUNCH | Suất cơm tấm, sườn, rau/đồ chua và nước chấm; không bì/chả. | 1.00 | PROPOSED |
| R012 | Cơm gà xối mỡ | LUNCH | Suất cơm trắng trộn nghệ với đùi gà có da, rau và nước chấm. | 1.00 | PROPOSED |
| R013 | Cơm thịt kho trứng | LUNCH | Suất cơm, ba chỉ kho trứng gà và dưa leo. | 1.00 | PROPOSED |
| R014 | Cơm cá kho tộ | LUNCH | Suất cơm, cá lóc kho tộ tiêu và dưa leo. | 1.00 | PROPOSED |
| R015 | Bún chả Hà Nội | LUNCH | Suất bún, chả miếng/chả viên, rau và nước chấm đồ chua. | 1.00 | PROPOSED |
| R016 | Bún thịt nướng | LUNCH | Suất bún thịt vai nướng với rau, đậu phộng, mỡ hành và nước chấm. | 1.00 | PROPOSED |
| R017 | Cơm bò lúc lắc | LUNCH | Suất cơm, bò xào ớt chuông/hành tây và rau. | 1.00 | PROPOSED |
| R018 | Cơm gà luộc | LUNCH | Suất cơm nghệ nhẹ, ức gà luộc bỏ da, rau và nước mắm gừng. | 1.00 | PROPOSED |
| R019 | Cơm sườn ram | LUNCH | Suất cơm, sườn ram nước tương và rau. | 1.00 | PROPOSED |
| R020 | Cơm cá chiên | LUNCH | Suất cơm, cá rô phi áp chảo và nước mắm chanh, rau. | 1.00 | PROPOSED |
| R021 | Cơm cá hấp | DINNER | Suất cơm, cá lóc hấp gừng và rau. | 1.00 | PROPOSED |
| R022 | Cơm thịt rang | DINNER | Suất cơm, ba chỉ rang cạnh và dưa leo. | 1.00 | PROPOSED |
| R023 | Cơm canh chua cá | DINNER | Suất cơm và canh chua cá lóc có rau; không thêm món mặn khác. | 1.00 | PROPOSED |
| R024 | Cơm gà kho gừng | DINNER | Suất cơm, đùi gà bỏ da kho gừng và dưa leo. | 1.00 | PROPOSED |
| R025 | Cơm đậu hũ sốt cà | DINNER | Suất cơm, đậu hũ trắng sốt cà và rau, không dùng nước mắm. | 1.00 | PROPOSED |
| R026 | Cơm tôm rim | DINNER | Suất cơm, tôm thẻ rim mặn ngọt và rau. | 1.00 | PROPOSED |
| R027 | Cơm thịt luộc | DINNER | Suất cơm, heo nạc luộc, rau và nước mắm tỏi chanh. | 1.00 | PROPOSED |
| R028 | Cơm canh bí đỏ | DINNER | Suất cơm và canh bí đỏ thịt nạc băm; không có món mặn riêng. | 1.00 | PROPOSED |
| R029 | Cơm cá kho | DINNER | Suất cơm, cá lóc kho gừng và dưa leo. | 1.00 | PROPOSED |
| R030 | Cơm trứng chiên | DINNER | Suất cơm, trứng chiên hành và rau. | 1.00 | PROPOSED |

## C. Danh mục Food dùng chung

82 mã nội bộ F001–F082, mỗi mã có đúng một đặc tả; tất cả được ít nhất một Recipe tham chiếu. “Nguồn dự kiến” là **đường hướng tra cứu**, không phải xác nhận đã tìm được bản ghi. Số liệu và tên thực phẩm thực sự đối chiếu nằm ở E. VN = bảng Việt Nam đúng ấn bản sẽ duyệt; USDA = phương án đối chiếu gần tương đương nếu cần. Không có dữ liệu dinh dưỡng nào được mặc định từ tên thực phẩm.

Trạng thái là tại **điểm cân/đưa vào công thức**, không phải yêu cầu ăn sống. Rau sống có thể được nấu sau khi cân; thịt nền đã chín có thể hoàn thiện với sốt. Không dùng số liệu trước nấu cho gram cân sau nấu. Các bước phát sinh phần bỏ đi cần cân yield/retention trước phê duyệt.

| Mã | Tên Food chuẩn đề xuất | Trạng thái tại điểm cân | Nguồn dự kiến / mục đã tra | Mức dữ liệu | Đặc tả và lưu ý cần xác nhận |
|---|---|---|---|---|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | CHÍN | VN/USDA | MISSING_SOURCE | Cân cơm đã nấu; không dùng số liệu gạo khô. Chốt giống gạo và độ ngậm nước. |
| F002 | Bánh phở tươi đã trụng, để ráo | CHÍN | VN/USDA | MISSING_SOURCE | Không dùng số liệu bánh phở khô; chốt lượng nước sau trụng. |
| F003 | Bún tươi đã trụng, để ráo | CHÍN | VN/USDA | MISSING_SOURCE | Bún gạo trắng; không thay bằng hủ tiếu. |
| F004 | Hủ tiếu gạo đã trụng, để ráo | CHÍN | VN/USDA | MISSING_SOURCE | Chốt loại sợi; không thay bằng miến hoặc mì trứng. |
| F005 | Bánh canh bột gạo đã luộc, để ráo | CHÍN | VN/nhãn | MISSING_SOURCE | Đề xuất loại gạo; nếu có bột năng phải đổi đặc tả và đối chiếu lại. |
| F006 | Bánh mì trắng ổ không nhân | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Chỉ phần bánh; không có bơ, pate hoặc sốt ngầm. |
| F007 | Gạo tẻ trắng khô | SỐNG | VN/USDA | MISSING_SOURCE | Chỉ dùng cho cháo, cân trước nấu. |
| F008 | Xôi nếp trắng đã hấp, không dầu | CHÍN | VN/USDA | MISSING_SOURCE | Không có nước cốt dừa hoặc mỡ ẩn. |
| F009 | Bột gạo tẻ khô | KHÔ | VN/USDA | MISSING_SOURCE | Dùng làm vỏ bánh cuốn; không đồng nhất với F007. |
| F010 | Bột năng khô | KHÔ | VN/nhãn | MISSING_SOURCE | Tinh bột sắn; cân khô trước pha. |
| F011 | Thịt bò thăn nạc luộc chín, không sốt | CHÍN | USDA/VN | MISSING_SOURCE | Phở bò phiên bản bò chín; bỏ gân/mỡ nhìn thấy trước cân. |
| F012 | Thịt ức gà luộc chín, bỏ da | CHÍN | USDA/VN | MISSING_SOURCE | Không cân xương, da hoặc nước luộc bỏ đi. |
| F013 | Thịt đùi gà hấp chín, có da, bỏ xương | CHÍN | USDA/VN | MISSING_SOURCE | Cân trước bước hoàn thiện; phần da được ăn. Khác F012/F022. |
| F014 | Thịt bắp bò luộc chín | CHÍN | USDA/VN | MISSING_SOURCE | Bắp bò cho bún bò; không gộp bò thăn. |
| F015 | Thịt heo nạc luộc chín | CHÍN | USDA/VN | MISSING_SOURCE | Chốt phần nạc thăn; không đại diện ba chỉ. |
| F016 | Thịt heo nạc băm hấp chín, không dầu | CHÍN | USDA/VN | MISSING_SOURCE | Dùng nhân/canh; không bao gồm dầu hoặc mộc nhĩ. |
| F017 | Gan heo luộc chín | CHÍN | USDA/VN | MISSING_SOURCE | Đã làm sạch; cần đối chiếu đúng nội tạng. |
| F018 | Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được | CHÍN | USDA/VN | MISSING_SOURCE | Cần chốt tỷ lệ nạc:mỡ; phần mỡ/nước thịt tiết ra khi hoàn thiện phải được dùng hết hoặc đo tổn thất. |
| F019 | Thịt nạc vai heo nướng chín, không sốt | CHÍN | USDA/VN | MISSING_SOURCE | Cân thịt chín để ráo; không cộng sốt ướp đã bỏ đi. |
| F020 | Thịt sườn heo hấp chín, bỏ xương, không sốt | CHÍN | USDA/VN | MISSING_SOURCE | Cân phần ăn được trước hoàn thiện nướng/ram; cần đo tổn thất nếu chảy bỏ mỡ. |
| F021 | Thịt bò thăn áp chảo chín, không dầu/sốt | CHÍN | USDA/VN | MISSING_SOURCE | Nước thịt giữ trong suất; dầu và sốt của bước hoàn thiện tính riêng. |
| F022 | Thịt đùi gà hấp chín, bỏ da và xương | CHÍN | USDA/VN | MISSING_SOURCE | Khác đùi có da F013 và ức F012. |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt | CHÍN | VN/USDA | MISSING_SOURCE | Chốt loài cá lóc; hoàn thiện hấp/kho nhanh, giữ nước thịt. |
| F024 | Thịt cá rô phi hấp chín, bỏ xương, không dầu/sốt | CHÍN | VN/USDA | MISSING_SOURCE | Làm nền phần cá chiên; cân trước áp chảo, dầu giữ lại tính riêng. |
| F025 | Tôm thẻ luộc chín, bóc vỏ | CHÍN | VN/USDA | MISSING_SOURCE | Bỏ đầu/vỏ/đuôi không ăn; phần nền chưa rim đường. |
| F026 | Thịt/riêu cua đồng nấu chín, lọc sạch vỏ | CHÍN | VN/nghiên cứu | MISSING_SOURCE | Cần đặc tả tỷ lệ phần thịt so với nước; không thay bằng cua biển. |
| F027 | Thịt cua biển hấp chín, gỡ vỏ | CHÍN | VN/USDA | MISSING_SOURCE | Chốt loài và tỷ lệ thịt trắng/nâu; không cân vỏ. |
| F028 | Trứng gà nguyên quả sống, bỏ vỏ | SỐNG | VN/USDA | MISSING_SOURCE | Cân phần trứng lỏng trước rán; giữ toàn bộ phần ăn được. |
| F029 | Trứng gà luộc chín, bỏ vỏ | CHÍN | VN/USDA | MISSING_SOURCE | Khác F028; cân cả lòng trắng và lòng đỏ. |
| F030 | Trứng cút luộc chín, bỏ vỏ | CHÍN | VN/USDA | MISSING_SOURCE | Không quy đổi số quả nếu chưa cân phần ăn được. |
| F031 | Đậu hũ trắng không chiên | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Chốt đậu hũ chắc, hàm lượng nước và chất kết tủa; không dùng số liệu đậu hũ chiên. |
| F032 | Chả lụa thành phẩm | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Cần công thức/nhãn đầy đủ; có thể chứa thịt heo, tinh bột và phụ gia. |
| F033 | Đậu phộng rang không muối, bỏ vỏ lụa | CHÍN | VN/USDA | MISSING_SOURCE | Không dùng số liệu hạt sống; không có dầu phủ. |
| F034 | Cà chua sống | SỐNG | VN2007-4005 | NEEDS_VERIFICATION (một phần) | Đã bỏ cuống; tra được bốn chỉ số, chưa chốt cách ánh xạ fiber. |
| F035 | Dưa leo sống, giữ vỏ ăn được | SỐNG | VN/USDA | MISSING_SOURCE | Chốt giữ vỏ; không dùng dữ liệu dưa đã gọt vỏ. |
| F036 | Xà lách sống | SỐNG | VN/USDA | MISSING_SOURCE | Chốt loại xà lách, rửa sạch, để ráo. |
| F037 | Giá đỗ đậu xanh sống | SỐNG | VN/USDA | MISSING_SOURCE | Cân sau rửa/để ráo, trước trụng nếu có. |
| F038 | Hành tây sống | SỐNG | VN2007-4039 | NEEDS_VERIFICATION (một phần) | Bỏ vỏ khô; không phải hành tím/hành lá. |
| F039 | Hành lá sống | SỐNG | VN/USDA | MISSING_SOURCE | Phần xanh và trắng ăn được; rửa để ráo. |
| F040 | Ngò rí sống | SỐNG | VN/USDA | MISSING_SOURCE | Còn gọi rau mùi; không tạo thêm Food đồng nghĩa. |
| F041 | Húng quế sống | SỐNG | VN/USDA | MISSING_SOURCE | Không dùng một Food chung tên rau thơm. |
| F042 | Rau răm sống | SỐNG | VN/nghiên cứu | MISSING_SOURCE | Không đối chiếu với húng hoặc ngò. |
| F043 | Hẹ lá sống | SỐNG | VN/USDA | MISSING_SOURCE | Phân biệt hành lá. |
| F044 | Sả tươi băm, phần lõi ăn được | SỐNG | VN/nghiên cứu | MISSING_SOURCE | Chỉ phần băm được ăn, không cân cây sả bỏ khỏi nồi. |
| F045 | Gừng tươi sống, gọt vỏ | SỐNG | VN2007-13003 | NEEDS_VERIFICATION (một phần) | Không dùng dữ liệu gừng bột; tra được bốn chỉ số. |
| F046 | Tỏi ta sống, bóc vỏ | SỐNG | VN2007-4103 | NEEDS_VERIFICATION (một phần) | Không gộp tỏi phi; tra được bốn chỉ số. |
| F047 | Hành tím sống, bóc vỏ | SỐNG | VN/USDA | MISSING_SOURCE | Không gộp hành tây hoặc hành phi. |
| F048 | Ớt tươi sống | SỐNG | VN/USDA | MISSING_SOURCE | Chốt loại ớt; cân phần ăn được, không tính cuống. |
| F049 | Cà rốt sống, sơ chế | SỐNG | VN/USDA | MISSING_SOURCE | Đồ chua tự pha; không dùng giá trị cà rốt ngâm sẵn. |
| F050 | Củ cải trắng sống, sơ chế | SỐNG | VN/USDA | MISSING_SOURCE | Cân phần sẽ được ăn, nước nấu giữ trong suất. |
| F051 | Đu đủ xanh sống, bỏ vỏ/hạt | SỐNG | VN/USDA | MISSING_SOURCE | Không phải đu đủ chín; dùng đồ chua tự pha. |
| F052 | Ớt chuông sống | SỐNG | VN/USDA | MISSING_SOURCE | Chốt màu đỏ; bỏ hạt/cuống. |
| F053 | Thơm chín tươi, bỏ vỏ/mắt/lõi cứng | SỐNG | VN/USDA | MISSING_SOURCE | Còn gọi dứa; một Food duy nhất. |
| F054 | Đậu bắp sống, bỏ cuống | SỐNG | VN/USDA | MISSING_SOURCE | Dùng canh chua, giữ cả phần ăn được. |
| F055 | Bạc hà/dọc mùng, phần thân đã tước vỏ | SỐNG | VN/nghiên cứu | MISSING_SOURCE | Không phải lá mint; cần đối chiếu đúng thực phẩm và phương pháp sơ chế. |
| F056 | Bí đỏ sống, bỏ vỏ/hạt | SỐNG | VN/USDA | MISSING_SOURCE | Chốt giống bí đỏ; phần nấu canh được ăn hết. |
| F057 | Rau ngổ sống | SỐNG | VN/nghiên cứu | MISSING_SOURCE | Tên khác ngò om; không gộp ngò rí. |
| F058 | Ngò gai sống | SỐNG | VN/nghiên cứu | MISSING_SOURCE | Tên khác mùi tàu; không gộp ngò rí. |
| F059 | Nấm mèo khô | KHÔ | VN/USDA | MISSING_SOURCE | Tên khác mộc nhĩ; cân khô trước ngâm, nước ngấm ghi trong F071. |
| F060 | Nấm hương khô | KHÔ | VN/USDA | MISSING_SOURCE | Cân khô trước ngâm; không dùng giá trị nấm tươi. |
| F061 | Dầu đậu nành tinh luyện | CHẾ_BIẾN | VN/nhãn/USDA | MISSING_SOURCE | Gram thực sự giữ trong suất; không phải lượng dầu đổ vào chảo. |
| F062 | Nước mắm nguyên chất | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Chốt nhãn và độ đạm; nước chấm pha phải tách đường/nước/chanh. |
| F063 | Nước tương lên men | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Chốt nhãn, nguyên liệu đậu nành/lúa mì và số liệu theo gram. |
| F064 | Đường trắng tinh luyện | CHẾ_BIẾN | VN/USDA | MISSING_SOURCE | Không tự điền số dinh dưỡng từ trí nhớ. |
| F065 | Muối ăn iod | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Chưa điền 0 mặc dù không kỳ vọng năng lượng; cần nguồn xác nhận. |
| F066 | Tiêu đen xay khô | KHÔ | VN/USDA | MISSING_SOURCE | Cân cả lượng nhỏ, không ghi vừa đủ. |
| F067 | Nước cốt chanh tươi, bỏ hạt | CHẾ_BIẾN | VN/USDA | MISSING_SOURCE | Khối lượng nước cốt; không cân cả quả hoặc quy đổi ml trực tiếp. |
| F068 | Giấm gạo | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Chốt nhãn và độ acid; gram, không mặc định ml=g. |
| F069 | Thịt me chín dạng nhuyễn, bỏ hạt | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Không tính vỏ/hạt; không thay bằng sốt me có đường. |
| F070 | Nước dừa tươi | SỐNG | VN/USDA | MISSING_SOURCE | Chỉ nước, không cơm dừa/nước cốt dừa. |
| F071 | Nước lọc dùng trong món | CHẾ_BIẾN | nguồn chuyên môn | MISSING_SOURCE | Chỉ phần giữ trong món; số 0 cũng cần được xác minh, không phải giá trị mặc định. |
| F072 | Nước dùng phở bò thành phẩm, không nêm | CHẾ_BIẾN | công thức thành phần/phân tích | MISSING_SOURCE | Cần định nghĩa nồng độ, lọc mỡ, thành phần hương liệu; Food hợp phần, chưa có số liệu. |
| F073 | Nước dùng gà thành phẩm, không nêm | CHẾ_BIẾN | công thức thành phần/phân tích | MISSING_SOURCE | Cần đặc tả chiết xuất và lớp mỡ; không coi là nước lọc. |
| F074 | Nước dùng heo thành phẩm, không nêm | CHẾ_BIẾN | công thức thành phần/phân tích | MISSING_SOURCE | Cần định nghĩa xương/thịt đã lọc bỏ, chất hòa tan và hàm lượng mỡ. |
| F075 | Mắm ruốc Huế thành phẩm | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Cần nhãn/công thức, có thành phần giáp xác; không dùng dữ liệu mắm tôm. |
| F076 | Mắm tôm thành phẩm | CHẾ_BIẾN | VN/nhãn | MISSING_SOURCE | Khác mắm ruốc; không suy diễn thành phần từ tên gọi. |
| F077 | Dầu điều màu thành phẩm | CHẾ_BIẾN | nhãn/công thức thành phần | MISSING_SOURCE | Toàn khối lượng đã bao gồm dầu nền; không cộng thêm dầu nền lần nữa. |
| F078 | Bột nghệ khô | KHÔ | VN/USDA | MISSING_SOURCE | Không dùng số liệu củ nghệ tươi. |
| F079 | Mật ong | CHẾ_BIẾN | VN/nhãn/USDA | MISSING_SOURCE | Chỉ lượng còn trên món, không toàn bộ phần sốt ướp đã bỏ. |
| F080 | Hành phi thành phẩm | CHẾ_BIẾN | VN/nhãn/công thức thành phần | MISSING_SOURCE | Đã chứa dầu; không cộng dầu chế biến hành phi lần nữa. |
| F081 | Cơm gạo tấm đã nấu, không dầu | CHÍN | VN/USDA | MISSING_SOURCE | Dành cơm tấm; nếu xác minh cùng loại/độ ẩm với F001 có thể gộp sau khi duyệt, chưa tự gộp. |
| F082 | Thịt heo băm viên nướng chín, không sốt | CHÍN | VN/công thức thành phần | MISSING_SOURCE | Dành bún chả; chỉ thịt đã chín, các gia vị/sốt giữ lại tính riêng, khác F016 hấp. |

## D. Công thức chi tiết — 1.00 khẩu phần mỗi món

**Mọi gram/phút/hướng dẫn dưới đây đều là đề xuất chưa xác nhận.** D dùng cùng danh mục C, không phát sinh Food ngoài C. Không có cụm “gia vị vừa đủ”: mọi thành phần đưa vào suất được kê gram.

Quy ước cân:
- Chỉ phần ăn được sau sơ chế; nguyên liệu chín cân ở trạng thái chín ghi tại C, nguyên liệu sống/khô cân trước nấu đúng trạng thái đó.
- F071 là lượng nước giữ lại mục tiêu; nước rửa, nước luộc/trụng bỏ đi và nước bay hơi không tính như phần ăn. Không cộng F071 lần nữa cho phần nước đã có trong cơm/sợi/nước dùng thành phẩm.
- F061 là dầu thực sự còn trong suất, không dầu còn lại ở chảo. Số lượng hiện chỉ là giả định cần đo.
- Gia vị, nước chấm, nước thịt và sốt dưới đây giả định được dùng hết trong một suất. Nếu để thừa phải cân lại lượng dùng; không coi lượng chế biến cả mẻ là lượng đã ăn.
- Nước dùng/nước chấm thành phẩm và thịt đã chín là các thành phần nền được chuẩn bị trước; thời gian nấu ở từng món không bao gồm toàn bộ thời gian chuẩn bị nền theo mẻ.
- Nguyên liệu sống/khô đổi khối lượng khi nấu do trao đổi nước: bộ tính hiện chỉ cộng chất từ lượng đầu vào, không có mô hình yield/retention. Tạm dùng giả định giữ toàn bộ chất trong phần được ăn để trình duyệt, **chưa coi giả định này được chứng minh**. Trường hợp bỏ nước/mỡ phải nghiên cứu lại, không âm thầm đổi gram.
- Không cộng thêm đồ uống, quẩy, bơ, sốt, rau hoặc món kèm ngoài từng bảng. Không lấy tổng gram các trạng thái trộn dưới đây làm cân nặng đĩa cuối.

### R001. Phở bò

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô phở bò chín, không quẩy.
- **Thời gian đề xuất:** 20 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F002 | Bánh phở tươi đã trụng, để ráo | 180.00 | CHÍN |
| F011 | Thịt bò thăn nạc luộc chín, không sốt | 80.00 | CHÍN |
| F072 | Nước dùng phở bò thành phẩm, không nêm | 300.00 | CHẾ_BIẾN |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F038 | Hành tây sống | 15.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F041 | Húng quế sống | 3.00 | SỐNG |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 6.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Hâm nước dùng và nêm lượng nước mắm/đường đã kê; trụng bánh phở, xếp bò chín; thêm rau, nước dùng, chanh và tiêu.

**Giả định/cần duyệt:** Phiên bản bò chín, không tái/nạm/gầu. Nước dùng cân thành phẩm, không cộng xương đã bỏ; chưa xác minh thành phần F072.

### R002. Phở gà

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô phở ức gà bỏ da.
- **Thời gian đề xuất:** 20 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F002 | Bánh phở tươi đã trụng, để ráo | 180.00 | CHÍN |
| F012 | Thịt ức gà luộc chín, bỏ da | 80.00 | CHÍN |
| F073 | Nước dùng gà thành phẩm, không nêm | 300.00 | CHẾ_BIẾN |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F038 | Hành tây sống | 15.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F058 | Ngò gai sống | 2.00 | SỐNG |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 6.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Hâm nước dùng gà và nêm; trụng phở, xé gà; thêm rau, nước dùng, chanh và tiêu.

**Giả định/cần duyệt:** Gà chỉ phần ức chín không da; không lấy dinh dưỡng đùi có da cho định lượng này.

### R003. Bánh mì trứng

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một ổ bánh mì với trứng rán và rau, không pate/bơ.
- **Thời gian đề xuất:** 15 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F006 | Bánh mì trắng ổ không nhân | 80.00 | CHẾ_BIẾN |
| F028 | Trứng gà nguyên quả sống, bỏ vỏ | 100.00 | SỐNG |
| F035 | Dưa leo sống, giữ vỏ ăn được | 40.00 | SỐNG |
| F049 | Cà rốt sống, sơ chế | 15.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 5.00 | CHẾ_BIẾN |
| F063 | Nước tương lên men | 5.00 | CHẾ_BIẾN |
| F068 | Giấm gạo | 3.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F065 | Muối ăn iod | 0.30 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Pha cà rốt với giấm/đường và dùng hết phần pha; rán trứng với phần dầu giữ lại và muối; kẹp trứng, rau, nước tương, tiêu.

**Giả định/cần duyệt:** 100 g trứng là phần lỏng đã bỏ vỏ trước rán, không phải 100 g trứng chín. Không có sốt mayonnaise/pate ẩn.

### R004. Bún bò Huế

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô bún bò bắp; chưa gồm giò heo, huyết hoặc chả.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F003 | Bún tươi đã trụng, để ráo | 180.00 | CHÍN |
| F014 | Thịt bắp bò luộc chín | 90.00 | CHÍN |
| F072 | Nước dùng phở bò thành phẩm, không nêm | 300.00 | CHẾ_BIẾN |
| F044 | Sả tươi băm, phần lõi ăn được | 3.00 | SỐNG |
| F075 | Mắm ruốc Huế thành phẩm | 3.00 | CHẾ_BIẾN |
| F077 | Dầu điều màu thành phẩm | 3.00 | CHẾ_BIẾN |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F038 | Hành tây sống | 15.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F041 | Húng quế sống | 3.00 | SỐNG |
| F058 | Ngò gai sống | 3.00 | SỐNG |
| F048 | Ớt tươi sống | 1.00 | SỐNG |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 5.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |

**Hướng dẫn ngắn:** Hâm nước dùng; cho sả băm, mắm ruốc, dầu điều, nước mắm, đường và đun; xếp bún, bò, rau; chan nước và thêm chanh/ớt.

**Giả định/cần duyệt:** Đây là phiên bản giản lược cần duyệt tên. Sả băm được ăn hết; không tính cây sả/xương loại khỏi nước dùng.

### R005. Hủ tiếu Nam Vang

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô hủ tiếu nước với heo, gan, tôm và trứng cút.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F004 | Hủ tiếu gạo đã trụng, để ráo | 160.00 | CHÍN |
| F015 | Thịt heo nạc luộc chín | 40.00 | CHÍN |
| F017 | Gan heo luộc chín | 20.00 | CHÍN |
| F025 | Tôm thẻ luộc chín, bóc vỏ | 35.00 | CHÍN |
| F030 | Trứng cút luộc chín, bỏ vỏ | 20.00 | CHÍN |
| F074 | Nước dùng heo thành phẩm, không nêm | 280.00 | CHẾ_BIẾN |
| F050 | Củ cải trắng sống, sơ chế | 30.00 | SỐNG |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F043 | Hẹ lá sống | 5.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 2.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 6.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Nấu củ cải và tỏi với nước dùng, dùng hết nước; nêm; trụng hủ tiếu, xếp các phần thịt/gan/tôm/trứng; thêm giá, hẹ, hành.

**Giả định/cần duyệt:** Trứng cút tính gram đã bỏ vỏ; không có xương, vỏ tôm hay hoành thánh. Dầu 3 g là phần tỏi phi giữ trong tô.

### R006. Cháo gà

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô cháo gạo với ức gà, rau răm.
- **Thời gian đề xuất:** 45 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F007 | Gạo tẻ trắng khô | 40.00 | SỐNG |
| F012 | Thịt ức gà luộc chín, bỏ da | 70.00 | CHÍN |
| F071 | Nước lọc dùng trong món | 350.00 | CHẾ_BIẾN |
| F045 | Gừng tươi sống, gọt vỏ | 2.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F042 | Rau răm sống | 3.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 3.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 5.00 | CHẾ_BIẾN |
| F065 | Muối ăn iod | 0.50 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Nấu gạo thành cháo; bù nước để đạt phần nước giữ trong suất; cho gà, gừng và gia vị; phi hành bằng dầu kê riêng và cho hết vào tô, thêm rau.

**Giả định/cần duyệt:** 40 g gạo khô, không dùng thêm cơm chín. 350 g nước là phần giữ lại mục tiêu, không phải tổng nước đổ nồi; cần cân suất thử.

### R007. Bánh cuốn

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một suất bánh cuốn nhân heo/nấm kèm chả và nước chấm.
- **Thời gian đề xuất:** 40 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F009 | Bột gạo tẻ khô | 45.00 | KHÔ |
| F010 | Bột năng khô | 10.00 | KHÔ |
| F071 | Nước lọc dùng trong món | 150.00 | CHẾ_BIẾN |
| F016 | Thịt heo nạc băm hấp chín, không dầu | 45.00 | CHÍN |
| F059 | Nấm mèo khô | 2.00 | KHÔ |
| F047 | Hành tím sống, bóc vỏ | 5.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 4.00 | CHẾ_BIẾN |
| F080 | Hành phi thành phẩm | 3.00 | CHẾ_BIẾN |
| F032 | Chả lụa thành phẩm | 30.00 | CHẾ_BIẾN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 40.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 4.00 | CHẾ_BIẾN |
| F048 | Ớt tươi sống | 1.00 | SỐNG |

**Hướng dẫn ngắn:** Ngâm nấm, phần nước ngấm giữ lại đề xuất 10 g; pha bột với 110 g nước để tráng; làm nhân heo/nấm và dùng 4 g dầu cho phần thực sự giữ; pha 30 g nước còn lại với mắm/đường/chanh/ớt; ăn kèm chả, dưa, hành phi.

**Giả định/cần duyệt:** Nấm cân khô; F071 gộp 110 g cho vỏ, 10 g nước ngấm nấm và 30 g nước chấm. Nước kỹ thuật ngâm bỏ đi không kê; cần cân lại tỷ lệ giữ nước. Hành phi đã chứa dầu riêng, không tính trùng F061.

### R008. Bún riêu

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô bún riêu cua đồng, đậu hũ trắng và cà chua.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F003 | Bún tươi đã trụng, để ráo | 170.00 | CHÍN |
| F026 | Thịt/riêu cua đồng nấu chín, lọc sạch vỏ | 60.00 | CHÍN |
| F031 | Đậu hũ trắng không chiên | 60.00 | CHẾ_BIẾN |
| F034 | Cà chua sống | 100.00 | SỐNG |
| F074 | Nước dùng heo thành phẩm, không nêm | 250.00 | CHẾ_BIẾN |
| F076 | Mắm tôm thành phẩm | 3.00 | CHẾ_BIẾN |
| F077 | Dầu điều màu thành phẩm | 3.00 | CHẾ_BIẾN |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F036 | Xà lách sống | 30.00 | SỐNG |
| F041 | Húng quế sống | 3.00 | SỐNG |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 5.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |

**Hướng dẫn ngắn:** Làm nóng nước dùng với riêu; xào cà chua/hành bằng dầu điều và đưa hết vào nồi; thêm đậu hũ, mắm; chan lên bún và rau.

**Giả định/cần duyệt:** Đậu hũ không chiên; không có huyết/chả ẩn. Riêu cua và nước dùng cần đặc tả riêng; có mắm tôm trong tổng gram.

### R009. Xôi gà

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một suất xôi gà có da, nấm và hành phi.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F008 | Xôi nếp trắng đã hấp, không dầu | 160.00 | CHÍN |
| F013 | Thịt đùi gà hấp chín, có da, bỏ xương | 80.00 | CHÍN |
| F060 | Nấm hương khô | 2.00 | KHÔ |
| F071 | Nước lọc dùng trong món | 20.00 | CHẾ_BIẾN |
| F080 | Hành phi thành phẩm | 5.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F063 | Nước tương lên men | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 40.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Ngâm nấm với phần nước giữ lại; rim nấm/gà bằng nước tương/đường; làm mỡ hành bằng 3 g dầu; xếp trên xôi, thêm hành phi và dưa.

**Giả định/cần duyệt:** Xôi là thành phẩm không dầu/cốt dừa; dầu, hành phi và nước sốt đã kê. Không thêm lạp xưởng/ruốc.

### R010. Bánh canh cua

- **Meal type:** BREAKFAST; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Một tô bánh canh gạo với cua biển.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F005 | Bánh canh bột gạo đã luộc, để ráo | 180.00 | CHÍN |
| F027 | Thịt cua biển hấp chín, gỡ vỏ | 70.00 | CHÍN |
| F074 | Nước dùng heo thành phẩm, không nêm | 280.00 | CHẾ_BIẾN |
| F010 | Bột năng khô | 5.00 | KHÔ |
| F071 | Nước lọc dùng trong món | 30.00 | CHẾ_BIẾN |
| F077 | Dầu điều màu thành phẩm | 3.00 | CHẾ_BIẾN |
| F047 | Hành tím sống, bóc vỏ | 3.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 6.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Hâm nước dùng; xào nhẹ hành bằng dầu điều; pha bột năng với 30 g nước, làm sánh; cho sợi/cua, nêm và thêm rau.

**Giả định/cần duyệt:** Bột năng 5 g là phần làm sánh thêm, không tính lại tinh bột có sẵn trong sợi bánh canh. Không có trứng cút/chả ngoài danh sách.

### R011. Cơm tấm sườn

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm tấm, sườn, rau/đồ chua và nước chấm; không bì/chả.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F081 | Cơm gạo tấm đã nấu, không dầu | 180.00 | CHÍN |
| F020 | Thịt sườn heo hấp chín, bỏ xương, không sốt | 100.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F034 | Cà chua sống | 40.00 | SỐNG |
| F049 | Cà rốt sống, sơ chế | 20.00 | SỐNG |
| F051 | Đu đủ xanh sống, bỏ vỏ/hạt | 20.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 6.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F063 | Nước tương lên men | 5.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 5.00 | CHẾ_BIẾN |
| F079 | Mật ong | 4.00 | CHẾ_BIẾN |
| F068 | Giấm gạo | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 20.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Hoàn thiện sườn chín với tỏi/nước tương/mật ong và một phần mắm/đường; dùng 3 g dầu làm mỡ hành, 3 g hoàn thiện sườn; pha đồ chua và nước chấm bằng phần còn lại; xếp suất.

**Giả định/cần duyệt:** Dùng cơm tấm F081, không thay số liệu gạo khô. Mắm/đường gộp cho sốt và nước chấm; sườn cân bỏ xương trước hoàn thiện, phải đo nếu mỡ chảy bỏ.

### R012. Cơm gà xối mỡ

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm trắng trộn nghệ với đùi gà có da, rau và nước chấm.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 160.00 | CHÍN |
| F013 | Thịt đùi gà hấp chín, có da, bỏ xương | 120.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F034 | Cà chua sống | 40.00 | SỐNG |
| F036 | Xà lách sống | 30.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 12.00 | CHẾ_BIẾN |
| F078 | Bột nghệ khô | 0.30 | KHÔ |
| F063 | Nước tương lên men | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 3.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 15.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Hoàn thiện gà đã hấp bằng xối dầu; cân phần dầu thực sự giữ; trộn nghệ vào cơm nóng; pha nước tương/đường/chanh/nước với tỏi; ăn cùng rau.

**Giả định/cần duyệt:** 12 g dầu giữ lại chỉ là giả định trình duyệt, không phải lượng dầu trong chảo. Phải đo hấp thu/mất nước; không dùng cả dữ liệu gà chiên đã có dầu và cộng thêm 12 g.

### R013. Cơm thịt kho trứng

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, ba chỉ kho trứng gà và dưa leo.
- **Thời gian đề xuất:** 35 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F018 | Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được | 70.00 | CHÍN |
| F029 | Trứng gà luộc chín, bỏ vỏ | 50.00 | CHÍN |
| F070 | Nước dừa tươi | 40.00 | SỐNG |
| F071 | Nước lọc dùng trong món | 20.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Đun thịt/trứng chín với nước dừa, nước, hành/tỏi, mắm/đường; giữ toàn bộ phần nước sốt phân cho suất; ăn cùng cơm và dưa.

**Giả định/cần duyệt:** Không thêm dầu; mỡ trong ba chỉ đã có trong F018. Cần duyệt tỷ lệ nạc:mỡ và lượng nước kho thực sự ăn.

### R014. Cơm cá kho tộ

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, cá lóc kho tộ tiêu và dưa leo.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt | 100.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 5.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 5.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 30.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.50 | KHÔ |

**Hướng dẫn ngắn:** Pha sốt từ mắm/đường/hành/tỏi/nước/dầu; hoàn thiện cá chín trong tộ, chia toàn bộ sốt vào suất; thêm hành/tiêu, ăn với cơm và dưa.

**Giả định/cần duyệt:** Chưa phân biệt đủ với R029; giữ nguyên đề xuất để người quản lý quyết định, không tự đổi tên hoặc loài cá.

### R015. Bún chả Hà Nội

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất bún, chả miếng/chả viên, rau và nước chấm đồ chua.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F003 | Bún tươi đã trụng, để ráo | 180.00 | CHÍN |
| F019 | Thịt nạc vai heo nướng chín, không sốt | 60.00 | CHÍN |
| F082 | Thịt heo băm viên nướng chín, không sốt | 45.00 | CHÍN |
| F036 | Xà lách sống | 40.00 | SỐNG |
| F041 | Húng quế sống | 3.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F051 | Đu đủ xanh sống, bỏ vỏ/hạt | 30.00 | SỐNG |
| F049 | Cà rốt sống, sơ chế | 20.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 10.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 6.00 | CHẾ_BIẾN |
| F068 | Giấm gạo | 5.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 60.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Dùng phần thịt/chả nướng chín đã cân; pha mắm/đường/giấm/chanh/nước với tỏi và đồ chua; ăn cùng bún và rau; hành/tiêu phân vào lớp gia vị giữ trên thịt.

**Giả định/cần duyệt:** F019/F082 là thịt chín không sốt; không cộng nước ướp đã bỏ. Nước chấm 60 g nước phải được tính theo phần thực sự dùng, không cả bát nếu để thừa.

### R016. Bún thịt nướng

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất bún thịt vai nướng với rau, đậu phộng, mỡ hành và nước chấm.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F003 | Bún tươi đã trụng, để ráo | 180.00 | CHÍN |
| F019 | Thịt nạc vai heo nướng chín, không sốt | 90.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 50.00 | SỐNG |
| F036 | Xà lách sống | 40.00 | SỐNG |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F049 | Cà rốt sống, sơ chế | 20.00 | SỐNG |
| F033 | Đậu phộng rang không muối, bỏ vỏ lụa | 10.00 | CHÍN |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F044 | Sả tươi băm, phần lõi ăn được | 3.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 5.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F063 | Nước tương lên men | 5.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F079 | Mật ong | 3.00 | CHẾ_BIẾN |
| F068 | Giấm gạo | 4.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 35.00 | CHẾ_BIẾN |

**Hướng dẫn ngắn:** Hoàn thiện thịt nướng với sả/tỏi/nước tương/mật ong giữ lại; làm mỡ hành; pha nước chấm và cà rốt; xếp bún, rau, thịt, đậu phộng.

**Giả định/cần duyệt:** Đậu phộng rang và dầu mỡ hành đều có gram; không thêm chả giò. Phần thịt F019 đã loại nước ướp, lớp sốt còn ăn tính riêng.

### R017. Cơm bò lúc lắc

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, bò xào ớt chuông/hành tây và rau.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F021 | Thịt bò thăn áp chảo chín, không dầu/sốt | 100.00 | CHÍN |
| F052 | Ớt chuông sống | 60.00 | SỐNG |
| F038 | Hành tây sống | 35.00 | SỐNG |
| F034 | Cà chua sống | 40.00 | SỐNG |
| F036 | Xà lách sống | 30.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 8.00 | CHẾ_BIẾN |
| F063 | Nước tương lên men | 8.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 3.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 3.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Xào rau và tỏi với dầu; cho bò đã chín cùng nước tương/mắm/đường, đảo nhanh, giữ nước thịt/sốt trong suất; ăn cùng cơm và rau.

**Giả định/cần duyệt:** Bò cân ở trạng thái áp chảo chín không dầu/sốt. Nếu cân bò sống phải dùng Food sống khác và duyệt lại, không đổi gram ngầm.

### R018. Cơm gà luộc

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm nghệ nhẹ, ức gà luộc bỏ da, rau và nước mắm gừng.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 160.00 | CHÍN |
| F012 | Thịt ức gà luộc chín, bỏ da | 100.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F036 | Xà lách sống | 30.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F045 | Gừng tươi sống, gọt vỏ | 4.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 20.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F078 | Bột nghệ khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Trộn cơm nóng với nghệ/dầu đã kê; xé gà luộc; pha mắm gừng/tỏi/đường/chanh/nước; ăn cùng rau.

**Giả định/cần duyệt:** Không phải cơm nấu nước luộc gà chưa định lượng. Đề xuất phiên bản ức bỏ da cần duyệt, không suy ra giá trị cho gà nguyên con có da.

### R019. Cơm sườn ram

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, sườn ram nước tương và rau.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F020 | Thịt sườn heo hấp chín, bỏ xương, không sốt | 100.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F034 | Cà chua sống | 40.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F063 | Nước tương lên men | 8.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 5.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 5.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 30.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Làm sốt hành/tỏi/mắm/nước tương/đường với nước; ram sườn chín bằng phần dầu giữ lại; ăn toàn bộ sốt phân cho suất cùng cơm/rau.

**Giả định/cần duyệt:** F020 là nền hấp chín, không sốt. Nếu công thức thực tế ram từ sườn sống hoặc loại mỡ đi, phải lập lại yield và nguồn tương ứng.

### R020. Cơm cá chiên

- **Meal type:** LUNCH; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, cá rô phi áp chảo và nước mắm chanh, rau.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F024 | Thịt cá rô phi hấp chín, bỏ xương, không dầu/sốt | 110.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F034 | Cà chua sống | 40.00 | SỐNG |
| F036 | Xà lách sống | 30.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 10.00 | CHẾ_BIẾN |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 3.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 20.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Áp chảo cá nền đã chín với phần dầu giữ lại; pha nước mắm/tỏi/đường/chanh/nước; ăn cùng cơm và rau.

**Giả định/cần duyệt:** Chọn cá rô phi bỏ xương; 10 g dầu là lượng giữ lại đề xuất. Không tính dầu bỏ chảo, không dùng dữ liệu cá chiên đã chứa dầu rồi cộng dầu lần nữa.

### R021. Cơm cá hấp

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, cá lóc hấp gừng và rau.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt | 110.00 | CHÍN |
| F045 | Gừng tươi sống, gọt vỏ | 6.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F038 | Hành tây sống | 25.00 | SỐNG |
| F063 | Nước tương lên men | 8.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 3.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 2.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 20.00 | CHẾ_BIẾN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Hâm/hấp cá chín với gừng, hành và sốt đã kê; giữ nước cá trong suất; dùng dầu cho lớp hành; ăn cùng cơm/dưa.

**Giả định/cần duyệt:** Cá lóc chín bỏ xương trước hoàn thiện; không có nấm hoặc miến ngoài danh sách.

### R022. Cơm thịt rang

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, ba chỉ rang cạnh và dưa leo.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F018 | Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được | 80.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 70.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 5.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F071 | Nước lọc dùng trong món | 15.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Rang nhanh ba chỉ chín cùng hành/tỏi, mắm/đường/nước; chia toàn bộ phần mỡ/sốt giữ lại vào suất, thêm hành/tiêu.

**Giả định/cần duyệt:** Không thêm dầu. Đây là giả định giữ phần mỡ tiết ra; nếu thực tế chắt bỏ phải cân phần loại bỏ và duyệt lại, không giữ nguyên số liệu.

### R023. Cơm canh chua cá

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm và canh chua cá lóc có rau; không thêm món mặn khác.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt | 100.00 | CHÍN |
| F034 | Cà chua sống | 80.00 | SỐNG |
| F053 | Thơm chín tươi, bỏ vỏ/mắt/lõi cứng | 50.00 | SỐNG |
| F054 | Đậu bắp sống, bỏ cuống | 50.00 | SỐNG |
| F055 | Bạc hà/dọc mùng, phần thân đã tước vỏ | 40.00 | SỐNG |
| F069 | Thịt me chín dạng nhuyễn, bỏ hạt | 8.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 220.00 | CHẾ_BIẾN |
| F037 | Giá đỗ đậu xanh sống | 30.00 | SỐNG |
| F057 | Rau ngổ sống | 3.00 | SỐNG |
| F058 | Ngò gai sống | 3.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F065 | Muối ăn iod | 0.30 | CHẾ_BIẾN |

**Hướng dẫn ngắn:** Nấu thơm/cà/đậu bắp/dọc mùng trong nước đã kê; cho me, cá chín và gia vị; thêm giá/rau thơm; phi tỏi bằng phần dầu riêng và dùng hết trong suất.

**Giả định/cần duyệt:** Me là thịt nhuyễn bỏ hạt, không tính hạt; canh/nước cá được ăn hết. Sơ chế dọc mùng theo quy trình phù hợp và chốt phần giữ lại.

### R024. Cơm gà kho gừng

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, đùi gà bỏ da kho gừng và dưa leo.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F022 | Thịt đùi gà hấp chín, bỏ da và xương | 110.00 | CHÍN |
| F045 | Gừng tươi sống, gọt vỏ | 8.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 5.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 40.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Phi hành/tỏi/gừng bằng dầu; kho nhanh gà chín với mắm/đường/nước; dùng sốt phân cho suất, ăn cùng cơm/dưa.

**Giả định/cần duyệt:** Đùi bỏ da, không dùng số liệu ức hoặc đùi có da; không có nước dừa trừ khi đổi công thức được duyệt.

### R025. Cơm đậu hũ sốt cà

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, đậu hũ trắng sốt cà và rau, không dùng nước mắm.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F031 | Đậu hũ trắng không chiên | 180.00 | CHẾ_BIẾN |
| F034 | Cà chua sống | 120.00 | SỐNG |
| F038 | Hành tây sống | 20.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 8.00 | CHẾ_BIẾN |
| F063 | Nước tương lên men | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 3.00 | CHẾ_BIẾN |
| F065 | Muối ăn iod | 0.50 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 40.00 | CHẾ_BIẾN |
| F036 | Xà lách sống | 50.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Xào cà/tỏi/hành với dầu, thêm nước/nước tương/đường/muối; cho đậu hũ trắng, đun nhẹ; ăn với cơm và xà lách.

**Giả định/cần duyệt:** Không chiên sẵn đậu; dầu đã kê cho sốt. Phiên bản không nguyên liệu động vật trực tiếp, chưa cam kết chay/dị ứng vì phụ thuộc nhãn nước tương.

### R026. Cơm tôm rim

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, tôm thẻ rim mặn ngọt và rau.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F025 | Tôm thẻ luộc chín, bóc vỏ | 110.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F034 | Cà chua sống | 40.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 5.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 5.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 25.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Phi hành/tỏi, cho tôm chín với mắm/đường/nước, rim ngắn và dùng hết sốt phân cho suất; ăn cùng cơm/rau.

**Giả định/cần duyệt:** Tôm cân phần chín đã bóc vỏ; không dùng trọng lượng tôm nguyên đầu/vỏ.

### R027. Cơm thịt luộc

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, heo nạc luộc, rau và nước mắm tỏi chanh.
- **Thời gian đề xuất:** 20 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F015 | Thịt heo nạc luộc chín | 110.00 | CHÍN |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F036 | Xà lách sống | 50.00 | SỐNG |
| F040 | Ngò rí sống | 3.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 4.00 | SỐNG |
| F048 | Ớt tươi sống | 1.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F067 | Nước cốt chanh tươi, bỏ hạt | 5.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 25.00 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Thái thịt luộc chín; pha nước chấm từ mắm/tỏi/ớt/đường/chanh/nước; ăn cùng cơm và rau.

**Giả định/cần duyệt:** Phiên bản thịt nạc thăn, không ba chỉ. Không tính nước luộc bỏ đi; nước chấm là lượng dùng hết.

### R028. Cơm canh bí đỏ

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm và canh bí đỏ thịt nạc băm; không có món mặn riêng.
- **Thời gian đề xuất:** 25 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F056 | Bí đỏ sống, bỏ vỏ/hạt | 180.00 | SỐNG |
| F016 | Thịt heo nạc băm hấp chín, không dầu | 60.00 | CHÍN |
| F071 | Nước lọc dùng trong món | 220.00 | CHẾ_BIẾN |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F039 | Hành lá sống | 5.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 3.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 6.00 | CHẾ_BIẾN |
| F065 | Muối ăn iod | 0.50 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |

**Hướng dẫn ngắn:** Phi hành bằng dầu kê riêng; nấu bí đỏ với nước, cho thịt băm chín và gia vị; thêm hành/tiêu; dùng toàn bộ canh với cơm.

**Giả định/cần duyệt:** Đã chọn phiên bản có heo băm để tránh món mơ hồ; cần người quản lý duyệt, không tự coi là món chay hoặc suất cân đối.

### R029. Cơm cá kho

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, cá lóc kho gừng và dưa leo.
- **Thời gian đề xuất:** 30 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt | 100.00 | CHÍN |
| F045 | Gừng tươi sống, gọt vỏ | 6.00 | SỐNG |
| F046 | Tỏi ta sống, bóc vỏ | 3.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F062 | Nước mắm nguyên chất | 8.00 | CHẾ_BIẾN |
| F064 | Đường trắng tinh luyện | 4.00 | CHẾ_BIẾN |
| F061 | Dầu đậu nành tinh luyện | 4.00 | CHẾ_BIẾN |
| F071 | Nước lọc dùng trong món | 30.00 | CHẾ_BIẾN |
| F039 | Hành lá sống | 4.00 | SỐNG |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F066 | Tiêu đen xay khô | 0.30 | KHÔ |

**Hướng dẫn ngắn:** Làm sốt gừng/hành/tỏi/mắm/đường với dầu/nước; kho nhanh cá chín và chia sốt vào suất; ăn cùng cơm/dưa.

**Giả định/cần duyệt:** Giữ nguyên mục số 29. Cùng cá lóc và cách kho gần R014, chưa chấp thuận giữ cả hai; không thêm món thay thế vào bộ 30.

### R030. Cơm trứng chiên

- **Meal type:** DINNER; **base_servings:** 1.00; **trạng thái:** PROPOSED.
- **Mô tả:** Suất cơm, trứng chiên hành và rau.
- **Thời gian đề xuất:** 20 phút làm một suất, có nguyên liệu nền; cần duyệt quy ước prep_minutes.

| Food ref | Nguyên liệu (cùng tên ở C) | Gram cho 1 khẩu phần | Trạng thái tại điểm cân |
|---|---|---:|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 150.00 | CHÍN |
| F028 | Trứng gà nguyên quả sống, bỏ vỏ | 100.00 | SỐNG |
| F039 | Hành lá sống | 8.00 | SỐNG |
| F047 | Hành tím sống, bóc vỏ | 4.00 | SỐNG |
| F061 | Dầu đậu nành tinh luyện | 7.00 | CHẾ_BIẾN |
| F062 | Nước mắm nguyên chất | 5.00 | CHẾ_BIẾN |
| F065 | Muối ăn iod | 0.30 | CHẾ_BIẾN |
| F066 | Tiêu đen xay khô | 0.20 | KHÔ |
| F035 | Dưa leo sống, giữ vỏ ăn được | 60.00 | SỐNG |
| F034 | Cà chua sống | 60.00 | SỐNG |

**Hướng dẫn ngắn:** Đánh trứng sống với hành và gia vị; chiên với phần dầu giữ lại; ăn cùng cơm/dưa/cà.

**Giả định/cần duyệt:** 100 g trứng sống đã bỏ vỏ, không 100 g trứng chín. Không thêm thịt băm hoặc bơ chưa kê.

## E. Dữ liệu dinh dưỡng và quy trình xác minh

### E1. Nguồn đã truy cập và phạm vi bằng chứng

- **S-VN2007:** [Bảng thành phần thực phẩm Việt Nam 2007 — Viện Dinh dưỡng/Bộ Y tế, bản lưu FAO](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf). Đã đối chiếu nguyên tắc và bốn mục; chưa dùng ấn bản 2017.
- **S-USDA:** [USDA FoodData Central — Data Documentation](https://fdc.nal.usda.gov/data-documentation/) và [API Guide](https://fdc.nal.usda.gov/api-guide/). Hướng tra cứu dự phòng; lần này chưa trích xuất/xác minh được bản ghi đủ năm số, nên **không đưa số USDA vào bảng** và không khẳng định tên/mã record nước ngoài nào là tương đương.
- Bản 2017: cần người quản lý cung cấp/chốt quyền truy cập đúng ấn bản; chưa dùng số liệu của ấn bản này.
- Với nhãn nhà sản xuất: phải lưu ảnh/tài liệu gốc, tên nhãn, quy cách, ngày truy cập, đơn vị và thành phần. Nhãn không nêu fiber thì fiber còn thiếu, không tự gán 0.
- Với Food hợp phần F032/F072–F077/F080: cần công thức thành phần hoặc phân tích đủ năm số. Nguồn cho món có tên gần giống không tự trở thành nguồn cho thành phẩm này.

S-VN2007 phân biệt “—” (thiếu) với 0; Glucid trừ xơ, Celluloza dùng phương pháp khối lượng. Hai trường cần duyệt ánh xạ, không tự đồng nhất định nghĩa với nguồn khác. [Nguyên tắc của bảng gốc](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=8).

### E2. Bảng năm trường cho từng Food

Tất cả giá trị dưới đây trên **100 g phần ăn được**: energy kcal; protein/carbs/fat/fiber g. “—” là chưa có giá trị đã xác minh/chuẩn hóa, **không phải 0**. Dấu † tại carbs là Glucid đã đọc từ nguồn, còn chờ phê duyệt ánh xạ. Những dòng NEEDS_VERIFICATION có bốn số đọc được, nhưng chưa đủ năm trường cho NutriFit; không coi là seed-ready.

| Food | Trạng thái | Kcal | Protein g | Carbs g | Fat g | Fiber g | Nguồn / tên thực phẩm thực sự đối chiếu | Trạng thái xác minh |
|---|---|---:|---:|---:|---:|---:|---|---|
| F001 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F002 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F003 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F004 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F005 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F006 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F007 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F008 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F009 | KHÔ | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F010 | KHÔ | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F011 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F012 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F013 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F014 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F015 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F016 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F017 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F018 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F019 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F020 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F021 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F022 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F023 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F024 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F025 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F026 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F027 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F028 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F029 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F030 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F031 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F032 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F033 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F034 | SỐNG | 20 | 0.6 | 4† | 0.2 | — | [S-VN2007, mã 4005, PDF trang 107](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=107): Cà chua / Tomato | NEEDS_VERIFICATION |
| F035 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F036 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F037 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F038 | SỐNG | 41 | 1.8 | 8.2† | 0.1 | — | [S-VN2007, mã 4039, PDF trang 141](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=141): Hành tây / Onion, common, garden | NEEDS_VERIFICATION |
| F039 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F040 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F041 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F042 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F043 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F044 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F045 | SỐNG | 29 | 0.4 | 5.1† | 0.8 | — | [S-VN2007, mã 13003, PDF trang 528](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=528): Gừng tươi / Ginger root, fresh | NEEDS_VERIFICATION |
| F046 | SỐNG | 121 | 6 | 23† | 0.5 | — | [S-VN2007, mã 4103, PDF trang 205](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=205): Tỏi ta / Garlic bulbs | NEEDS_VERIFICATION |
| F047 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F048 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F049 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F050 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F051 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F052 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F053 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F054 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F055 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F056 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F057 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F058 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F059 | KHÔ | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F060 | KHÔ | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F061 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F062 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F063 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F064 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F065 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F066 | KHÔ | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F067 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F068 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F069 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F070 | SỐNG | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F071 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F072 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F073 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F074 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F075 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F076 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F077 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F078 | KHÔ | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F079 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F080 | CHẾ_BIẾN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F081 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |
| F082 | CHÍN | — | — | — | — | — | —; chưa xác nhận tên/mã record, hướng tra cứu xem C | MISSING_SOURCE |

### E3. Cách hiểu số liệu một phần

Celluloza nguồn (g/100 g): F034 = 0.8; F038 = 1.1; F045 = 3.3; F046 = 1.5. **Chưa điền vào fiber_per_100g.** Bốn mục nguồn là thực phẩm tươi; cần duyệt ánh xạ sang Food sống.

Phân loại dữ liệu hiện tại:
- 0 Food: VERIFIED_5_OF_5 (đủ năm số và định nghĩa phù hợp).
- 4 Food: NEEDS_VERIFICATION, đã đối chiếu một phần với S-VN2007.
- 78 Food: MISSING_SOURCE, chưa chốt record và chưa điền bất kỳ số dinh dưỡng.
- Cả 82 Food chưa đủ điều kiện seed; cả 30 Recipe chưa được phê duyệt hoặc tính dinh dưỡng đáng tin cậy.

Các số nguồn giữ nguyên độ chính xác công bố; không thêm các chữ số để ngụ ý độ chính xác cao hơn. Khi chuyển DECIMAL(10,3), chỉ định dạng/round có kiểm soát và lưu giá trị nguồn bên ngoài DB.

### E4. Quy trình xác minh đề xuất

1. Chốt định nghĩa **total carbohydrate hay available carbohydrate**, **total dietary fiber hay chỉ tiêu khác**. Không cộng/trừ xơ tùy ý để ép hai nguồn khớp nhau; phép chuyển đổi phải có phương pháp và được duyệt.
2. Chốt tên Food, loài/cắt thịt, da/mỡ, sống/chín, nước, phần ăn được, sản phẩm/nhãn và phương pháp nấu. Không đổi các đặc tả này khi chỉ thay nguồn.
3. Tra bảng Việt Nam đúng ấn bản trước. Chỉ sử dụng record nước ngoài khi thiếu record Việt Nam phù hợp; ghi rõ “đối chiếu gần tương đương”, khác giống/cắt thịt/độ ẩm/chiên/nêm và trạng thái NEEDS_VERIFICATION.
4. Với từng giá trị lưu nguồn, tác giả/cơ quan, phiên bản, URL/trang hoặc mã record, tên trong nguồn, đơn vị, phương pháp/định nghĩa, ngày tra cứu. Thiếu một trong năm trường thì giữ “—”; số 0 chỉ được ghi khi nguồn nêu rõ 0.
5. Dữ liệu trên 100 ml chỉ đổi sang 100 g khi có khối lượng riêng được xác minh cho đúng sản phẩm. Nhãn theo một khẩu phần phải có gram khẩu phần. Không dùng quy tắc 1 ml = 1 g cho dầu, mắm, giấm hoặc nước dùng.
6. Nấu thử theo công thức đã duyệt, cân nguyên liệu ăn được, phần loại bỏ, dầu giữ lại, nước sốt thực dùng và suất sau nấu. Lập cân bằng khối lượng/yield; không chỉ chọn số kcal để món trông “cân đối”.
7. Với thịt nền chín trước bước hoàn thiện: gram ở D và dữ liệu phải cùng trạng thái tại điểm cân. Cân riêng phần mỡ/nước thịt bị bỏ khi nướng/rang/chiên. Nếu có thất thoát đáng kể không thể hạch toán theo mô hình cộng hiện tại, sửa đặc tả Food thành phẩm được duyệt hoặc xác lập bảng chuyển đổi bên ngoài; không dùng hệ số bảo toàn mặc định như một kết quả nghiên cứu.
8. Food hợp phần phải có nguồn số liệu thành phẩm và danh sách thành phần để duyệt, dù app hiện không thể phân giải Food ID con. Không tự phân bổ dinh dưỡng từ nước/xương ban đầu cho nước dùng thành phẩm.
9. Người quản lý ký duyệt record và năm giá trị; chỉ sau đó mới tính tổng Recipe bằng đúng công thức A5, kiểm tra phạm vi DB và kiểm lại khẩu phần. Bản tài liệu này chưa thực hiện bước nấu thử/phân tích hoặc tính tổng dinh dưỡng.

## F. Kiểm tra tính nhất quán của bản thiết kế

Các kiểm đếm dưới đây được tính từ các bảng thiết kế, không phải test Maven hay kết quả truy vấn MySQL.

| Hạng mục | Kết quả thiết kế |
|---|---:|
| Recipe | 30 |
| BREAKFAST / LUNCH / DINNER | 10 / 10 / 10 |
| Food được định nghĩa | 82 |
| Food được ít nhất một công thức dùng | 82 |
| Food được định nghĩa nhưng không dùng | 0 |
| Liên kết Recipe–Food (dòng Ingredient) | 383 |
| Recipe rỗng | 0 |
| Mã Food bị tham chiếu nhưng chưa định nghĩa | 0 |
| Cặp (recipe_ref, food_ref) trùng | 0 |
| Gram không dương | 0 |
| Recipe có base_servings khác 1.00 | 0 |
| Food đầy đủ năm số xác minh/chuẩn hóa | 0 |
| Food thiếu ít nhất một trường/định nghĩa cần thiết | 82 |

### F1. Các tình huống lỗi và cách tránh

| Tình huống | Điều kiện trong thiết kế / cổng duyệt |
|---|---|
| Recipe không nguyên liệu | Mỗi Rxxx có bảng gram riêng; chưa tạo active Recipe trống trong một giao dịch seed dở dang |
| Recipe/Food inactive | Chỉ bật sau duyệt và đối chiếu toàn bộ dependency active; không tự bật lại Food cũ |
| Gram = 0 hoặc âm | Mọi dòng đề xuất > 0 và có hai số lẻ; thành phần bỏ khỏi phiên bản thì bỏ dòng, không ghi 0 |
| Dữ liệu dinh dưỡng thiếu | Giữ trong tài liệu, không seed. NOT NULL/DEFAULT 0 không thay được xác minh |
| Overflow | Gram dưới giới hạn DECIMAL(10,2); năm số Food phải trong DECIMAL(10,3). Chưa đủ đầu vào để xác nhận tổng; sau duyệt kiểm cả một khẩu phần và giới hạn servings trước lưu DECIMAL(12,3) |
| Raw/cooked sai | Cột trạng thái trong C/D, cùng một điểm cân với nguồn; cơm và sợi đã chín không lấy số gạo/sợi khô; trứng sống khác trứng luộc |
| Nhân đôi Ingredient | Không lặp Fxxx trong Rxxx; đường/mắm/dầu dùng nhiều chỗ đã gộp gram và phân bổ trong hướng dẫn |
| Tính trùng dầu | F077/F080 đã chứa dầu; F061 chỉ lượng khác được thêm và giữ lại. Không đồng thời dùng dữ liệu món chiên đã có dầu và toàn bộ dầu chiên lần nữa |
| Phần không ăn được | Không đưa xương, vỏ trứng, vỏ tôm/cua, hạt me, nước luộc bỏ hoặc dầu chảo bỏ vào gram |
| Sai tổng khối lượng sau nấu | Tổng gram tham chiếu không được gắn nhãn trọng lượng cuối của đĩa; phải cân yield thực tế vì có bay hơi/trao đổi nước |
| Sai DISLIKE/LIKE | Dùng lại cùng Fxxx khi cùng thực phẩm/trạng thái; không giả định các Food khác cùng loài tự chia sẻ preference |
| Nguồn mắm/nước dùng sai | Hợp phần cần nguồn riêng và danh sách thành phần; chưa chấp nhận giả định 0 kcal hoặc bỏ qua chất hòa tan |

Tên phân biệt cố ý: F001/F081 (cơm tẻ/tấm), F007/F009 (gạo/bột gạo), F012/F013/F022 (ức/đùi có da/đùi bỏ da), F016/F082 (băm hấp/băm viên nướng), F023/F024 (loài cá), F026/F027 (cua đồng/cua biển), F028/F029/F030 (trứng gà sống/gà luộc/cút luộc), F039/F043 (hành lá/hẹ). Không gộp chỉ vì tên gần nhau; nếu chứng minh F001/F081 thực sự cùng đặc tả và nguồn, việc gộp phải do người quản lý duyệt, giữ bảng ánh xạ mã cũ.

### F2. Nhận xét về mức đa dạng và “cân đối”

Danh sách thiên về món tinh bột trắng, nhiều món nước buổi sáng, nhiều món heo/cá với cơm ở trưa/tối; chỉ R025 không dùng trực tiếp thịt/cá/trứng. R028 được đề xuất là canh có heo băm. Không có cơ sở kết luận cân đối năng lượng/macro hoặc đủ rau khi chưa xác minh số liệu và khẩu phần. Không tự thêm món mới để bù.

R014 và R029 cùng cá lóc, cơm và cách kho, khác gia vị nhẹ; phân bữa khác nhau không đủ tạo sự khác biệt về công thức. R011/R019 cùng nền sườn nhưng khác cơm/nước chấm/cách hoàn thiện; R012/R018/R024 khác da/cắt thịt và dầu; R021/R023 có cùng cá nhưng một suất cá hấp, một suất canh chua. Những phân biệt này là đề xuất, không phải kết quả phân tích dinh dưỡng.

## G. Các quyết định cần người quản lý phê duyệt

| Mã quyết định | Nội dung cần quyết định | Đề xuất trình duyệt, chưa áp dụng thay thế |
|---|---|---|
| G01 | Có giữ nguyên 30 tên và phân bữa không? | Giữ như B; tất cả đang PROPOSED |
| G02 | Trùng R014/R029 | Ưu tiên thay R029 bằng “Cơm cá thu sốt cà” hoặc một món khác do người quản lý chọn. Chưa thêm cá thu/Food/Recipe thay thế vào bảng; nếu duyệt phải cập nhật đồng bộ B–F và kiểm đếm lại |
| G03 | Bản chất một Recipe | Các món cơm là suất đúng thành phần D; R023/R028 là cơm + canh có đạm, không tự cộng món mặn. Có chấp nhận phạm vi này không? |
| G04 | Phiên bản món đặc trưng | Duyệt R001 bò chín; R004 bún bò không giò/huyết/chả; R007 bánh cuốn có chả; R008 đậu trắng không chiên; R010 sợi gạo; R011 không bì/chả; R018 ức gà bỏ da; R028 canh có heo băm |
| G05 | Khẩu phần tinh bột/đạm/rau | Duyệt gram từng dòng D. Các số không phải chuẩn lâm sàng; chưa có mục tiêu kcal chứng minh cho 30 suất |
| G06 | Nguyên liệu nền chín trước hoàn thiện | Có chấp nhận cách định lượng thành phần này hay muốn công thức từ nguyên liệu sống? Nếu chọn sống cần Food sống, gram/yield/retention mới; không đổi số cục bộ |
| G07 | Dầu và chất béo | Đặc biệt R012 12 g, R020 10 g, R030 7 g dầu giữ lại; R013/R022 tỷ lệ ba chỉ và phần mỡ ăn. Cần cân thực tế trước chốt |
| G08 | Nguồn và tên chuẩn Food | Ưu tiên bản Việt Nam nào? Duyệt record/nhãn, loài/cắt thịt, raw/cooked. Không có quyền tự xác nhận nhãn/loài từ tên phổ thông |
| G09 | Định nghĩa carbs/fiber | Chốt có dùng Glucid/Celluloza Việt Nam 2007 hay bộ total carbohydrate/total dietary fiber khác; 4 dòng một phần chưa là dữ liệu ứng dụng được duyệt |
| G10 | Food hợp phần | Chốt công thức/nhãn nước dùng, mắm, chả, hành phi, dầu điều; phê duyệt giới hạn theo dõi Food ID con |
| G11 | Preferences theo Food ID | Có chấp nhận người dùng phải LIKE/DISLIKE riêng từng dạng/cắt thịt? Nếu cần tránh toàn bộ một loài phải phối hợp thiết kế riêng sau này; không sửa app trong nhiệm vụ này |
| G12 | Mức đa dạng | Có muốn thay một món kho/chiên bằng món khác để tăng đa dạng? Chỉ thay sau duyệt; không gọi danh sách hiện tại là bộ ăn cân đối |
| G13 | prep_minutes | Phút tại D là thời gian làm một suất với nền chín, không gồm ninh nước dùng. Chốt cách lưu cột prep_minutes |
| G14 | Chống seed trùng | Duyệt manifest ánh xạ và cơ chế một tiến trình seed; schema hiện không có khóa catalog duy nhất |
| G15 | Ngưỡng phát hành | Chỉ tạo SQL khi người quản lý duyệt món/gram và từng Food có đủ năm số phù hợp; không seed trước những phần “tạm 0” |

Phiếu duyệt: người duyệt ___; ngày ___; phiên bản ___; món giữ/thay ___; gram thay đổi ___; nguồn/định nghĩa ___; quyết định seed ___.
Mặc định mọi ô còn trống; không có phê duyệt ngầm.

## H. Kế hoạch tạo SQL sau khi duyệt

### H1. File dự kiến và thứ tự khóa ngoại

Chưa tạo các file sau:

1. `database/seed/vietnamese_foods.sql`: chỉ Food đã duyệt đủ số liệu, tên/trạng thái rõ ràng.
2. `database/seed/vietnamese_recipes.sql`: đúng danh sách Recipe đã duyệt và meal_type/base_servings.
3. `database/seed/vietnamese_recipe_ingredients.sql`: liên kết đã resolve đúng Fxxx/Rxxx sang ID thực.

Không tạo seed cho users, profile, subscription, preferences, mealplans hoặc mealentries. Không tạo table/cột mới, không chạy lại schema.sql để làm sạch database.

### H2. Không suy đoán ID hoặc dựa vào tên để ghi đè

- Fxxx/Rxxx là mã thiết kế ổn định, không phải PRIMARY KEY; tuyệt đối không coi R001 là recipe_id=1 hoặc dựa vào thứ tự auto-increment.
- Cần manifest phiên bản bên ngoài DB: catalog_ref, loại bản ghi, tên chuẩn, trạng thái/method, checksum dữ liệu duyệt, ID thực và định danh môi trường đích. Manifest là đề xuất bổ sung ở giai đoạn seed, chưa tạo trong lần này.
- Trước seed, đọc inventory hiện có. Nếu có tên trùng: đối chiếu cả trạng thái ở tên, năm số Food hoặc meal_type/base_servings/thành phần Recipe. Có nhiều ứng viên hoặc không chứng minh tương đương thì dừng để người quản lý chọn; không lấy bản ghi đầu tiên.
- Bản ghi mới: lấy generated key từ lần insert của chính connection đó rồi cập nhật ánh xạ trong bộ nhớ; bản ghi tái sử dụng: chỉ nhận ID đã được kiểm chứng. Không dùng MAX(id), khoảng ID liên tục, LAST_INSERT_ID()+offset hoặc ID từ database khác.
- Các file SQL không được giả định tự chạy độc lập: bước seed phải có công cụ điều phối/ánh xạ cùng phiên DB được duyệt. Chưa quyết định cú pháp hoặc viết SQL thực tế ở đây.

### H3. Tính lặp lại và giới hạn của schema hiện tại

**Không thể bảo đảm idempotency/concurrency chỉ bằng ba file insert thông thường:** foods.name và recipes.name không unique; Ingredient cũng không unique theo cặp. Tên không phải khóa tự nhiên đủ mạnh.

Chiến lược không sửa schema được đề xuất:
1. Một tiến trình seed được kiểm soát; khóa giữa các lần seed và ngăn writer khác sửa catalog trong cửa sổ đó. Khóa do công cụ seed dùng không thể ngăn writer không tuân thủ; phải có phối hợp vận hành.
2. Manifest bền vững, gắn đúng môi trường và phiên bản dữ liệu. Đọc lại DB theo ID/checksum khi chạy lại; giống dữ liệu được duyệt thì bỏ qua có ghi nhận, khác thì dừng, không ghi đè.
3. Nếu DB commit nhưng manifest chưa ghi thành công, không seed lại mù: đối soát nội dung và khôi phục mapping trước. Nhiều ứng viên trùng thì yêu cầu người quản lý xử lý.
4. Với Ingredient, dùng cặp ID đã resolve, đối chiếu đúng gram và tổng số dòng dự kiến; dòng khác gram hoặc nhiều dòng trùng là xung đột, không tự xóa/cộng/sửa.
5. Không dùng thao tác replace/upsert theo name như một bảo đảm chống trùng khi thiếu khóa duy nhất. Không chuyển active của dữ liệu cũ một cách tự động.

### H4. Giao dịch, bảo toàn dữ liệu và xác nhận

- Trước mọi thực thi sau này: xác nhận database đích, quyền phê duyệt cụ thể, inventory, backup và khả năng phục hồi. Chưa có backup/restore nào được tạo hoặc kiểm chứng trong nhiệm vụ thiết kế này.
- Thử trước trên database test riêng. Trong một connection/giao dịch InnoDB, thực hiện theo thứ tự Food → Recipe → Ingredient; kiểm tra trước commit. Các file seed chỉ chứa DML được duyệt, không trộn DDL auto-commit.
- Lỗi giữa chừng phải rollback toàn bộ phần DML mới trong transaction; auto-increment có thể có khoảng trống và điều đó không làm sai mapping.
- Sau seed đối chiếu mapping, tập ID mới/tái dùng và checksum; số tăng thực tế có thể nhỏ hơn 82/30/383 nếu tái dùng bản ghi đã được xác minh. Không lấy chênh lệch count đơn thuần làm bằng chứng đúng.
- Kiểm tra đúng 10 candidate mỗi bữa thuộc bộ đã duyệt (không phải toàn DB chỉ được có 30 món), đúng gram, Food active, không rỗng, không trùng liên kết, cả năm số, đơn vị và trạng thái.
- Tính một và nhiều khẩu phần theo NutritionCalculator sau khi được cho phép kiểm thử; kiểm tra giới hạn, chế độ thiếu target, LIKE/DISLIKE và snapshot cũ không đổi. Đây chỉ là kế hoạch, chưa chạy.
- Không xóa hoặc sửa Food/Recipe đang dùng để “cài lại seed”; không đụng nhật ký, sở thích hoặc snapshot hiện có. Thay công thức về sau phải có phiên bản/đánh giá ảnh hưởng; không tự inactive Food làm vô hiệu tất cả Recipe liên quan.
- Sau xác nhận mới cho phép đưa catalog đã duyệt vào sử dụng. Việc duyệt bản thiết kế không tự động là quyền thực thi SQL.

**Điểm dừng:** chờ người quản lý duyệt mục B–E và các quyết định G. Không tạo SQL, không nhập MySQL trong lần này.

