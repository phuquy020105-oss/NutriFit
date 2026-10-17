# Dữ liệu dinh dưỡng catalog món Việt — NutriFit

Ngày lập: 2026-10-17. Phạm vi: dữ liệu đồ án Meal Planner, không phải khẩu phần lâm sàng.

## Phê duyệt và nguồn dữ liệu

Chủ dự án đã duyệt giữ nguyên **30 Recipe, 82 Food, 383 liên kết**, 10 món mỗi bữa, base_servings **1.00**, gồm cả R014 và R029.
Tên, bữa và gram theo [bản thiết kế gốc](vietnamese-food-catalog-review.md) được giữ nguyên.
Các nhãn PROPOSED/MISSING_SOURCE trong bản thiết kế là lịch sử trước phê duyệt; tài liệu này bổ sung dinh dưỡng, không viết lại bản gốc.

**0 Food VERIFIED đủ năm chỉ số; 82 Food ESTIMATED.** Trong đó:
- **4 Food** F034, F038, F045, F046 sử dụng bốn chỉ số K/P/C/F đã tra từ Bảng thành phần thực phẩm Việt Nam 2007; fiber vẫn ước lượng.
- **78 Food** còn lại dùng kiến thức dinh dưỡng phổ thông, thực phẩm tương đương và giả định chế biến được ghi từng dòng.
- Không có giá trị nào được tuyên bố lấy trực tiếp từ USDA/nhãn sản phẩm khi chưa xác minh record/nhãn phù hợp.

Nguồn một phần: [Bảng thành phần thực phẩm Việt Nam 2007, bản FAO lưu trữ](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf).
Trang PDF tính từ 1: [F034 mã 4005 tr.107](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=107),
[F038 mã 4039 tr.141](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=141),
[F045 mã 13003 tr.528](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=528),
[F046 mã 4103 tr.205](https://www.fao.org/fileadmin/templates/food_composition/documents/pdf/VTN_FCT_2007.pdf#page=205).
Celluloza của bảng cũ không được mặc định là tổng dietary fiber. Fiber trong bốn dòng trên là giả định riêng.

## Quy ước và độ chính xác

- Mỗi dòng tính trên **100g phần ăn được tại đúng trạng thái cân**. Gạo/bột/nấm khô khác cơm/bún/phở/nấm đã ngậm nước.
- Carbs là carbohydrate khả dụng ước lượng, tách fiber; bốn dòng nguồn giữ trường glucid của bảng Việt Nam, chưa chuẩn hóa bằng phép phân tích mới.
- Số đầu vào thường nguyên hoặc một chữ số thập phân, phản ánh ước lượng. DECIMAL lưu được ba chữ số không làm số liệu chính xác hơn.
- 0 là giả định thành phần không có hoặc vết không đáng kể theo mô tả từng Food, không phải dữ liệu thiếu. Chỉ muối F065 và nước F071 có cả năm bằng 0. Protein/carb/fiber của dầu, protein/fat/fiber của đường, fiber của mô động vật/lỏng đã lọc được giải thích ở bảng.
- Đối chiếu sơ bộ kcal với 4P + 4C + 9F; cho phép năng lượng fiber khoảng 2 kcal/g để rà soát. Không ép bằng nhau: acid hữu cơ (giấm/chanh), hệ số riêng dầu/đường tự nhiên, nước và làm tròn tạo sai khác. Đây là kiểm tra hợp lý, không phải xác minh thành phần bằng nguồn.
- Dầu F061/F077 là **lượng giữ lại và ăn**, không phải toàn bộ dầu đổ chảo. F077 đã có dầu nền; F080 đã có dầu hút trong hành phi; không cộng lại dầu nội tại.
- Nước dùng F072–F074 là chất lỏng thành phẩm chưa nêm, đã lọc, gồm mỡ/đạm còn lại. Xương/phần bỏ không tính; thịt ăn kèm cân riêng. Gia vị nêm kê riêng.
- Sai khác nhãn hàng, giống, mỡ thịt, lượng nước và hao hụt khi nấu chưa được hiệu chỉnh. Giá trị không áp dụng cho mọi phiên bản món ăn.

## 82 Food

| Ref | Food và trạng thái cân | kcal | Protein g | Carbs g | Fat g | Fiber g | Trạng thái | Nguồn/cơ sở ước lượng |
|---|---|---:|---:|---:|---:|---:|---|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu (CHÍN) | 130 | 2.7 | 28 | 0.3 | 0.4 | ESTIMATED | Cơm gạo tẻ chín ngậm nước khoảng 65–70%; ước lượng cơm trắng thường. |
| F002 | Bánh phở tươi đã trụng, để ráo (CHÍN) | 110 | 2 | 24 | 0.3 | 0.4 | ESTIMATED | Sợi phở chín để ráo; nước chiếm phần lớn, không dùng số gạo khô. |
| F003 | Bún tươi đã trụng, để ráo (CHÍN) | 110 | 2 | 24 | 0.2 | 0.5 | ESTIMATED | Bún chín để ráo, sợi gạo thông thường; khác nhau theo độ ráo. |
| F004 | Hủ tiếu gạo đã trụng, để ráo (CHÍN) | 110 | 2 | 24 | 0.2 | 0.4 | ESTIMATED | Hủ tiếu gạo chín để ráo, ước lượng gần bún/phở, không phải sợi khô. |
| F005 | Bánh canh bột gạo đã luộc, để ráo (CHÍN) | 105 | 1.5 | 24 | 0.2 | 0.3 | ESTIMATED | Bánh canh gạo chín mềm nhiều nước; không dùng loại pha nhiều bột năng khác. |
| F006 | Bánh mì trắng ổ không nhân (CHẾ_BIẾN) | 270 | 9 | 52 | 3 | 2.5 | ESTIMATED | Bánh mì trắng ruột thường, không bơ/sữa/nhân; độ khô và công thức thay đổi. |
| F007 | Gạo tẻ trắng khô (SỐNG) | 360 | 7 | 79 | 0.8 | 1 | ESTIMATED | Gạo tẻ khô trước nấu; nước cháo kê riêng F071, không dùng hệ số cơm chín. |
| F008 | Xôi nếp trắng đã hấp, không dầu (CHÍN) | 170 | 3.5 | 37 | 0.5 | 0.8 | ESTIMATED | Xôi nếp chín không dầu/đường; ngậm nước ít hơn cơm tẻ. |
| F009 | Bột gạo tẻ khô (KHÔ) | 360 | 6 | 80 | 1 | 1 | ESTIMATED | Bột gạo khô chưa pha, không phải bánh thành phẩm. |
| F010 | Bột năng khô (KHÔ) | 350 | 0.2 | 87 | 0.1 | 0 | ESTIMATED | Tinh bột năng tinh lọc; fiber coi không đáng kể bằng 0, không phải củ sắn. |
| F011 | Thịt bò thăn nạc luộc chín, không sốt (CHÍN) | 210 | 29 | 0 | 10 | 0 | ESTIMATED | Bò thăn nạc luộc; ước lượng thịt chín, carb và fiber xấp xỉ 0 của thịt không tẩm. |
| F012 | Thịt ức gà luộc chín, bỏ da (CHÍN) | 165 | 31 | 0 | 3.6 | 0 | ESTIMATED | Ức gà luộc bỏ da; đạm cô đặc sau nấu; carb/fiber coi 0 với thịt không tẩm. |
| F013 | Thịt đùi gà hấp chín, có da, bỏ xương (CHÍN) | 230 | 25 | 0 | 14 | 0 | ESTIMATED | Đùi gà hấp còn da bỏ xương; mỡ da được tính; carb/fiber coi 0 với thịt không tẩm. |
| F014 | Thịt bắp bò luộc chín (CHÍN) | 210 | 30 | 0 | 9 | 0 | ESTIMATED | Bắp bò luộc, bỏ phần không ăn; carb/fiber coi 0 với thịt không tẩm. |
| F015 | Thịt heo nạc luộc chín (CHÍN) | 190 | 29 | 0 | 8 | 0 | ESTIMATED | Heo nạc luộc, không nước sốt; carb/fiber coi 0 với thịt không tẩm. |
| F016 | Thịt heo nạc băm hấp chín, không dầu (CHÍN) | 200 | 28 | 0 | 9 | 0 | ESTIMATED | Heo xay nạc hấp không dầu; tỷ lệ mỡ khoảng 9%; carb/fiber coi 0 với thịt không tẩm. |
| F017 | Gan heo luộc chín (CHÍN) | 170 | 25 | 4 | 6 | 0 | ESTIMATED | Gan heo luộc, có carbohydrate dự trữ; fiber 0 vì không có mô thực vật. |
| F018 | Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được (CHÍN) | 500 | 10 | 0 | 51 | 0 | ESTIMATED | Ba chỉ luộc còn mỡ; khoảng 51% fat, dao động lớn theo miếng; carb/fiber coi 0. |
| F019 | Thịt nạc vai heo nướng chín, không sốt (CHÍN) | 260 | 27 | 0 | 17 | 0 | ESTIMATED | Vai heo nướng không sốt; khoảng 17% fat; sốt/dầu kê riêng, carb/fiber coi 0. |
| F020 | Thịt sườn heo hấp chín, bỏ xương, không sốt (CHÍN) | 280 | 25 | 0 | 20 | 0 | ESTIMATED | Sườn hấp bỏ xương chưa sốt; khoảng 20% fat, phụ thuộc phần nạc; carb/fiber coi 0. |
| F021 | Thịt bò thăn áp chảo chín, không dầu/sốt (CHÍN) | 220 | 29 | 0 | 11 | 0 | ESTIMATED | Bò thăn áp chảo khô; dầu ăn kê riêng; carb/fiber coi 0 với thịt không tẩm. |
| F022 | Thịt đùi gà hấp chín, bỏ da và xương (CHÍN) | 180 | 26 | 0 | 8 | 0 | ESTIMATED | Đùi gà hấp bỏ da/xương; không dùng số liệu đùi còn da; carb/fiber coi 0. |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt (CHÍN) | 100 | 21 | 0 | 2 | 0 | ESTIMATED | Cá lóc hấp chỉ thịt không xương; thịt cá nạc không tẩm nên carb/fiber coi 0. |
| F024 | Thịt cá rô phi hấp chín, bỏ xương, không dầu/sốt (CHÍN) | 128 | 26 | 0 | 2.5 | 0 | ESTIMATED | Cá rô phi hấp không xương; chiên hoàn thiện cộng dầu giữ lại riêng, carb/fiber coi 0. |
| F025 | Tôm thẻ luộc chín, bóc vỏ (CHÍN) | 100 | 24 | 0.2 | 0.3 | 0 | ESTIMATED | Tôm thẻ luộc bóc vỏ, protein cao; carb vết 0.2, fiber 0 không tính vỏ chitin. |
| F026 | Thịt/riêu cua đồng nấu chín, lọc sạch vỏ (CHÍN) | 95 | 18 | 1 | 2 | 0 | ESTIMATED | Riêu/thịt cua đồng chín đã lọc vỏ; ước lượng mô thịt/cặn đông, còn ít carb; fiber 0 vì loại vỏ. |
| F027 | Thịt cua biển hấp chín, gỡ vỏ (CHÍN) | 100 | 20 | 0.5 | 1.5 | 0 | ESTIMATED | Thịt cua biển chín gỡ vỏ; còn ít carb; fiber 0 vì loại vỏ. |
| F028 | Trứng gà nguyên quả sống, bỏ vỏ (SỐNG) | 143 | 12.6 | 0.7 | 9.5 | 0 | ESTIMATED | Trứng gà nguyên quả sống bỏ vỏ; tỷ lệ lòng đỏ/trắng trung bình, fiber 0. |
| F029 | Trứng gà luộc chín, bỏ vỏ (CHÍN) | 155 | 12.6 | 1.1 | 10.6 | 0 | ESTIMATED | Trứng gà luộc bỏ vỏ; cô đặc nhẹ do nước, không thêm dầu; fiber 0. |
| F030 | Trứng cút luộc chín, bỏ vỏ (CHÍN) | 158 | 13 | 0.5 | 11 | 0 | ESTIMATED | Trứng cút luộc bỏ vỏ; có lipid lòng đỏ, fiber 0. |
| F031 | Đậu hũ trắng không chiên (CHẾ_BIẾN) | 90 | 9 | 2 | 5 | 0.6 | ESTIMATED | Đậu hũ trắng chắc vừa chưa chiên; khoảng 9% protein, không dùng loại ép khô rất đặc. |
| F032 | Chả lụa thành phẩm (CHẾ_BIẾN) | 170 | 17 | 7 | 8 | 0.2 | ESTIMATED | Chả lụa hỗn hợp heo nạc/mỡ/tinh bột; giả định 17% protein, 8% fat, 7% carb; không phải nhãn sản phẩm cụ thể. |
| F033 | Đậu phộng rang không muối, bỏ vỏ lụa (CHÍN) | 590 | 25 | 13 | 50 | 8.5 | ESTIMATED | Đậu phộng rang khô, không dầu thêm; carb khả dụng khoảng 13%, fiber 8.5%. |
| F034 | Cà chua sống (SỐNG) | 20 | 0.6 | 4 | 0.2 | 1.2 | ESTIMATED | VN2007 mã 4005 tr.107: K/P/C/F = 20/0.6/4/0.2. Fiber 1.2 ước lượng cà chua sống; không đổi Celluloza 0.8 thành tổng fiber. |
| F035 | Dưa leo sống, giữ vỏ ăn được (SỐNG) | 15 | 0.7 | 2.8 | 0.1 | 0.5 | ESTIMATED | Dưa leo tươi giữ vỏ; nhiều nước, fiber thấp, không phải dưa bỏ vỏ. |
| F036 | Xà lách sống (SỐNG) | 15 | 1.4 | 1.5 | 0.2 | 1.3 | ESTIMATED | Xà lách lá sống phổ thông; không cố định giống, chưa trộn sốt. |
| F037 | Giá đỗ đậu xanh sống (SỐNG) | 30 | 3 | 4 | 0.2 | 1.8 | ESTIMATED | Giá đỗ đậu xanh sống để ráo, không phải hạt đậu khô. |
| F038 | Hành tây sống (SỐNG) | 41 | 1.8 | 8.2 | 0.1 | 1.7 | ESTIMATED | VN2007 mã 4039 tr.141: K/P/C/F = 41/1.8/8.2/0.1. Fiber 1.7 ước lượng hành tây; Celluloza 1.1 là chỉ số khác. |
| F039 | Hành lá sống (SỐNG) | 32 | 1.8 | 4.7 | 0.2 | 2.6 | ESTIMATED | Hành lá cả phần xanh/trắng ăn được, ước lượng rau họ hành sống. |
| F040 | Ngò rí sống (SỐNG) | 23 | 2.1 | 1 | 0.5 | 2.8 | ESTIMATED | Ngò rí tươi; ước lượng rau gia vị lá nhiều nước, không phải hạt ngò. |
| F041 | Húng quế sống (SỐNG) | 23 | 3 | 1 | 0.6 | 1.6 | ESTIMATED | Húng quế tươi; ước lượng rau lá gia vị, không phải húng khô. |
| F042 | Rau răm sống (SỐNG) | 30 | 3 | 2.5 | 0.5 | 3 | ESTIMATED | Rau răm tươi; ước lượng rau gia vị lá tương tự, chưa có record khớp loài. |
| F043 | Hẹ lá sống (SỐNG) | 30 | 3.3 | 2 | 0.7 | 2.5 | ESTIMATED | Hẹ lá tươi; ước lượng rau họ hành lá, không phải củ hành. |
| F044 | Sả tươi băm, phần lõi ăn được (SỐNG) | 99 | 1.8 | 20 | 0.5 | 2.5 | ESTIMATED | Lõi sả tươi ăn được, băm mịn; nhiều chất khô hơn rau lá, không tính thân bị vớt bỏ. |
| F045 | Gừng tươi sống, gọt vỏ (SỐNG) | 29 | 0.4 | 5.1 | 0.8 | 3.5 | ESTIMATED | VN2007 mã 13003 tr.528: K/P/C/F = 29/0.4/5.1/0.8. Fiber 3.5 là ước lượng riêng, không đồng nhất với Celluloza 3.3. |
| F046 | Tỏi ta sống, bóc vỏ (SỐNG) | 121 | 6 | 23 | 0.5 | 2.1 | ESTIMATED | VN2007 mã 4103 tr.205: K/P/C/F = 121/6/23/0.5. Fiber 2.1 ước lượng tỏi bóc vỏ; Celluloza 1.5 không phải tổng fiber. |
| F047 | Hành tím sống, bóc vỏ (SỐNG) | 72 | 2.5 | 14 | 0.1 | 3.2 | ESTIMATED | Hành tím củ sống bỏ vỏ; ước lượng củ hành khô chất nhiều hơn hành tây. |
| F048 | Ớt tươi sống (SỐNG) | 40 | 1.9 | 7.3 | 0.4 | 1.5 | ESTIMATED | Ớt cay tươi bỏ cuống; giả định loại đỏ thông thường, không phải ớt khô. |
| F049 | Cà rốt sống, sơ chế (SỐNG) | 41 | 0.9 | 6.8 | 0.2 | 2.8 | ESTIMATED | Cà rốt sống sơ chế; dùng carb khả dụng và fiber riêng; gia vị đồ chua kê riêng. |
| F050 | Củ cải trắng sống, sơ chế (SỐNG) | 18 | 0.6 | 2.5 | 0.1 | 1.6 | ESTIMATED | Củ cải trắng sống sơ chế, nhiều nước; không dùng củ cải muối. |
| F051 | Đu đủ xanh sống, bỏ vỏ/hạt (SỐNG) | 35 | 0.6 | 7 | 0.1 | 1.8 | ESTIMATED | Đu đủ xanh bỏ vỏ/hạt, ít đường hơn quả chín; ước lượng, chưa ngâm đường. |
| F052 | Ớt chuông sống (SỐNG) | 31 | 1 | 3.9 | 0.3 | 2.1 | ESTIMATED | Ớt chuông đỏ sống bỏ hạt/cuống, không phải loại xanh. |
| F053 | Thơm chín tươi, bỏ vỏ/mắt/lõi cứng (SỐNG) | 50 | 0.5 | 11.8 | 0.1 | 1.4 | ESTIMATED | Dứa/thơm chín phần thịt, không siro; đường tự nhiên đã nằm trong carb. |
| F054 | Đậu bắp sống, bỏ cuống (SỐNG) | 33 | 1.9 | 4.3 | 0.2 | 3.2 | ESTIMATED | Đậu bắp sống bỏ cuống; rau có chất nhầy và fiber, không phải đậu hạt. |
| F055 | Bạc hà/dọc mùng, phần thân đã tước vỏ (SỐNG) | 14 | 0.7 | 1.8 | 0.1 | 1.5 | ESTIMATED | Thân bạc hà/dọc mùng tước vỏ; ước lượng thân rau nhiều nước, KHÔNG phải lá mint. |
| F056 | Bí đỏ sống, bỏ vỏ/hạt (SỐNG) | 26 | 1 | 5 | 0.1 | 0.5 | ESTIMATED | Bí đỏ tươi phần thịt, không hạt/vỏ; giống nhiều nước, không phải bí rất bột. |
| F057 | Rau ngổ sống (SỐNG) | 25 | 2 | 2 | 0.4 | 2.5 | ESTIMATED | Rau ngổ/ngò om sống; ước lượng rau gia vị lá tương tự, chưa có record khớp loài. |
| F058 | Ngò gai sống (SỐNG) | 25 | 2 | 2 | 0.4 | 2.5 | ESTIMATED | Ngò gai/mùi tàu sống; ước lượng rau gia vị lá tương tự, chưa có record khớp loài. |
| F059 | Nấm mèo khô (KHÔ) | 293 | 9 | 52 | 1 | 25 | ESTIMATED | Mộc nhĩ khô trước ngâm; fiber cao, nước ngâm giữ lại kê riêng, không dùng số nấm ngậm nước. |
| F060 | Nấm hương khô (KHÔ) | 296 | 9.5 | 53 | 1 | 12 | ESTIMATED | Nấm hương khô trước ngâm; nhiều chất khô, không áp số nấm tươi. |
| F061 | Dầu đậu nành tinh luyện (CHẾ_BIẾN) | 884 | 0 | 0 | 100 | 0 | ESTIMATED | Dầu đậu nành tinh luyện: gần 100% fat, P/C/fiber coi 0; 884 kcal theo hệ số dầu xấp xỉ 8.84, không buộc 900. |
| F062 | Nước mắm nguyên chất (CHẾ_BIẾN) | 40 | 6 | 4 | 0 | 0 | ESTIMATED | Nước mắm nguyên chất lọc, không pha đường; ước lượng acid amin/protein 6%, carb 4%; fat/fiber không đáng kể coi 0. |
| F063 | Nước tương lên men (CHẾ_BIẾN) | 55 | 8 | 5 | 0.5 | 0.5 | ESTIMATED | Nước tương lên men thông thường, chưa pha đường thêm; còn chất hòa tan/cặn vết, không giả định bằng nước. |
| F064 | Đường trắng tinh luyện (CHẾ_BIẾN) | 400 | 0 | 100 | 0 | 0 | ESTIMATED | Đường trắng tinh luyện: carb 100%, 400 kcal; protein/fat/fiber coi 0. |
| F065 | Muối ăn iod (CHẾ_BIẾN) | 0 | 0 | 0 | 0 | 0 | ESTIMATED | Muối iod vô cơ: không cung cấp năng lượng hay năm chất này, cả năm bằng 0 có chủ ý. |
| F066 | Tiêu đen xay khô (KHÔ) | 255 | 10 | 40 | 3.3 | 25 | ESTIMATED | Tiêu đen khô xay; carb khả dụng khoảng 40%, fiber cao, không dùng tiêu tươi. |
| F067 | Nước cốt chanh tươi, bỏ hạt (CHẾ_BIẾN) | 25 | 0.4 | 6 | 0.1 | 0.3 | ESTIMATED | Nước cốt chanh không hạt, còn ít tép mịn; acid hữu cơ làm khác hệ số năng lượng. |
| F068 | Giấm gạo (CHẾ_BIẾN) | 18 | 0 | 0.5 | 0 | 0 | ESTIMATED | Giấm gạo lọc khoảng 4–5% acid acetic: năng lượng chủ yếu từ acid, không nằm trong P/C/F; P/fat/fiber coi 0. |
| F069 | Thịt me chín dạng nhuyễn, bỏ hạt (CHẾ_BIẾN) | 240 | 3 | 53 | 0.6 | 5 | ESTIMATED | Thịt me chua bỏ hạt chưa pha đường, đặc; không phải nước me loãng hay sốt me ngọt. |
| F070 | Nước dừa tươi (SỐNG) | 19 | 0.7 | 3.7 | 0.2 | 0 | ESTIMATED | Nước dừa tươi lọc không thịt dừa; fiber coi 0 vì loại mô rắn, còn vết đạm/mỡ. |
| F071 | Nước lọc dùng trong món (CHẾ_BIẾN) | 0 | 0 | 0 | 0 | 0 | ESTIMATED | Nước sạch giữ lại trong món: không cung cấp năng lượng hay năm chất này, cả năm bằng 0 có chủ ý. |
| F072 | Nước dùng phở bò thành phẩm, không nêm (CHẾ_BIẾN) | 20 | 2 | 0.5 | 1 | 0 | ESTIMATED | Nước dùng bò thành phẩm lọc, chưa nêm, còn khoảng 1% fat; không cộng xương/thịt bỏ đi; fiber 0 vì lọc cặn. |
| F073 | Nước dùng gà thành phẩm, không nêm (CHẾ_BIẾN) | 20 | 2.5 | 0.5 | 0.8 | 0 | ESTIMATED | Nước dùng gà thành phẩm lọc, chưa nêm, khoảng 0.8% fat; không cộng lại thịt gà; fiber 0 vì lọc cặn. |
| F074 | Nước dùng heo thành phẩm, không nêm (CHẾ_BIẾN) | 20 | 2 | 0.5 | 1 | 0 | ESTIMATED | Nước dùng heo thành phẩm lọc, chưa nêm, khoảng 1% fat; không cộng lại xương; fiber 0 vì lọc cặn. |
| F075 | Mắm ruốc Huế thành phẩm (CHẾ_BIẾN) | 100 | 15 | 4 | 2.5 | 0.5 | ESTIMATED | Mắm ruốc Huế dạng đặc lên men chưa pha, có cặn; ước lượng đạm/mỡ/carb và fiber vết, biến thiên lớn theo hãng. |
| F076 | Mắm tôm thành phẩm (CHẾ_BIẾN) | 80 | 12 | 4 | 1.5 | 0.3 | ESTIMATED | Mắm tôm đặc lên men chưa pha; giả định 12% protein, có cặn; fiber vết là ước lượng, không phải xét nghiệm. |
| F077 | Dầu điều màu thành phẩm (CHẾ_BIẾN) | 884 | 0 | 0 | 100 | 0 | ESTIMATED | Dầu điều đã lọc hạt, nền dầu tinh luyện: 100% fat, P/C/fiber coi 0; không cộng dầu nền lần nữa. |
| F078 | Bột nghệ khô (KHÔ) | 310 | 9 | 44 | 3 | 22 | ESTIMATED | Bột nghệ khô nguyên chất; nhiều fiber, không dùng số liệu củ nghệ tươi. |
| F079 | Mật ong (CHẾ_BIẾN) | 304 | 0.3 | 82 | 0 | 0 | ESTIMATED | Mật ong thông thường khoảng 82% carb; fat/fiber không đáng kể coi 0, năng lượng theo hệ số đường tự nhiên gần 3.7. |
| F080 | Hành phi thành phẩm (CHẾ_BIẾN) | 500 | 6 | 45 | 32 | 6 | ESTIMATED | Hành phi thành phẩm gồm cả dầu hút vào: giả định 32% fat, 45% carb, 6% fiber; không cộng lại dầu chiên bên trong. |
| F081 | Cơm gạo tấm đã nấu, không dầu (CHÍN) | 130 | 2.5 | 28 | 0.3 | 0.3 | ESTIMATED | Cơm gạo tấm chín không dầu; độ ngậm nước tương tự cơm tẻ, không phải gạo tấm khô. |
| F082 | Thịt heo băm viên nướng chín, không sốt (CHÍN) | 270 | 26 | 0 | 18 | 0 | ESTIMATED | Chả thịt heo băm nướng không sốt: thịt có khoảng 18% fat; sốt/đường kê riêng, carb/fiber coi 0 theo công thức chỉ thịt. |

## Dinh dưỡng 30 Recipe

Công thức hiện tại của NutritionCalculator: **SUM(quantity_grams / 100 × nutrient_per_100g) / base_servings**, cho 1.00 khẩu phần.
Tính Decimal chính xác, không làm tròn mỗi nguyên liệu; làm tròn kết quả cuối **HALF_UP, 3 chữ số**, giống NutritionFacts.toMealEntry.
Các số ba chữ số dưới đây là kết quả toán học từ dữ liệu ước lượng, không phải mức chính xác đo lường.

<!-- BEGIN RECIPE TOTALS -->
| Ref | Món | Bữa | kcal | Protein g | Carbs g | Fat g | Fiber g | Cờ rà soát |
|---|---|---|---:|---:|---:|---:|---:|---|
| R001 | Phở bò | BREAKFAST | 456.290 | 34.613 | 50.045 | 11.670 | 1.842 | Fiber <3g |
| R002 | Phở gà | BREAKFAST | 420.100 | 37.663 | 50.055 | 5.940 | 1.844 | Fiber <3g |
| R003 | Bánh mì trứng | BREAKFAST | 427.840 | 20.698 | 46.815 | 17.017 | 2.779 | Fiber <3g |
| R004 | Bún bò Huế | BREAKFAST | 509.330 | 38.853 | 50.748 | 14.674 | 2.068 | Fiber <3g |
| R005 | Hủ tiếu Nam Vang | BREAKFAST | 465.950 | 38.235 | 45.835 | 12.977 | 2.007 | Fiber <3g |
| R006 | Cháo gà | BREAKFAST | 293.770 | 25.083 | 32.712 | 5.891 | 0.836 | Kcal <400; Fiber <3g |
| R007 | Bánh cuốn | BREAKFAST | 424.420 | 21.700 | 55.643 | 11.943 | 1.577 | Fiber <3g |
| R008 | Bún riêu | BREAKFAST | 426.840 | 27.480 | 52.945 | 10.442 | 3.670 | — |
| R009 | Xôi gà | BREAKFAST | 533.950 | 27.120 | 66.345 | 16.717 | 2.240 | Fiber <3g |
| R010 | Bánh canh cua | BREAKFAST | 374.380 | 22.918 | 52.305 | 7.250 | 0.900 | Kcal <400; Fiber <3g |
| R011 | Cơm tấm sườn | LUNCH | 645.275 | 31.712 | 66.585 | 26.805 | 2.554 | Fiber <3g |
| R012 | Cơm gà xối mỡ | LUNCH | 635.260 | 36.343 | 53.302 | 29.560 | 2.062 | Fiber <3g |
| R013 | Cơm thịt kho trứng | LUNCH | 666.855 | 18.912 | 51.588 | 41.627 | 1.270 | Fat >30g; Fiber <3g |
| R014 | Cơm cá kho tộ | LUNCH | 372.345 | 26.377 | 50.778 | 6.555 | 1.352 | Kcal <400; Fiber <3g |
| R015 | Bún chả Hà Nội | LUNCH | 539.965 | 33.559 | 55.585 | 18.881 | 2.951 | Fiber <3g |
| R016 | Bún thịt nướng | LUNCH | 608.100 | 33.679 | 58.105 | 25.964 | 3.946 | — |
| R017 | Cơm bò lúc lắc | LUNCH | 554.375 | 36.030 | 53.820 | 19.875 | 3.524 | — |
| R018 | Cơm gà luộc | LUNCH | 439.880 | 36.946 | 52.606 | 7.276 | 1.698 | Fiber <3g |
| R019 | Cơm sườn ram | LUNCH | 568.365 | 31.092 | 51.668 | 25.672 | 1.811 | Fiber <3g |
| R020 | Cơm cá chiên | LUNCH | 466.290 | 34.430 | 50.120 | 13.427 | 1.898 | Fiber <3g |
| R021 | Cơm cá hấp | DINNER | 368.220 | 28.974 | 48.871 | 5.840 | 1.755 | Kcal <400; Fiber <3g |
| R022 | Cơm thịt rang | DINNER | 633.975 | 13.427 | 49.978 | 41.358 | 1.352 | Fat >30g; Fiber <3g |
| R023 | Cơm canh chua cá | DINNER | 437.150 | 28.930 | 64.540 | 5.947 | 5.613 | — |
| R024 | Cơm gà kho gừng | DINNER | 467.900 | 33.979 | 50.066 | 13.409 | 1.557 | Fiber <3g |
| R025 | Cơm đậu hũ sốt cà | DINNER | 489.560 | 22.960 | 57.195 | 17.882 | 4.393 | — |
| R026 | Cơm tôm rim | DINNER | 398.910 | 32.022 | 52.568 | 5.959 | 1.746 | Kcal <400; Fiber <3g |
| R027 | Cơm thịt luộc | DINNER | 447.390 | 37.912 | 50.153 | 9.461 | 1.798 | Fiber <3g |
| R028 | Cơm canh bí đỏ | DINNER | 395.710 | 23.220 | 52.115 | 9.051 | 1.808 | Kcal <400; Fiber <3g |
| R029 | Cơm cá kho | DINNER | 368.855 | 26.356 | 49.864 | 6.595 | 1.480 | Kcal <400; Fiber <3g |
| R030 | Cơm trứng chiên | DINNER | 428.830 | 17.994 | 47.996 | 17.157 | 2.006 | Fiber <3g |
<!-- END RECIPE TOTALS -->

Cờ rà soát là ngưỡng nội bộ để đọc catalog: kcal <400 hoặc >800, fat >30g, fiber <3g. Không phải chuẩn dinh dưỡng cho mọi người/bữa.
Không tự sửa gram đã duyệt. Món được gắn cờ vẫn giữ nguyên công thức; nếu cần cải thiện cân đối, đề xuất chủ dự án duyệt thêm rau/tăng phần đạm hoặc điều chỉnh phần dầu/mỡ trong một phiên bản sau.
Không phát hiện Food lặp trong cùng công thức, nguyên liệu tham chiếu thiếu hoặc cộng lại dầu nền của F077/F080.
Phần thịt/cá đã chín làm nền rồi hoàn thiện với dầu/sốt kê riêng; biến đổi độ ẩm khi chiên/kho lần cuối chưa được mô hình hóa.

## Mức bất định và giới hạn tích hợp

Cần ưu tiên kiểm chứng F018 (mỡ ba chỉ), F020 (sườn bỏ xương), F026 (riêu cua lọc), F031 (độ ép đậu hũ), F032 (chả lụa),
F055 (đúng loài thân dọc mùng), F072–F076 (nước dùng/mắm), F080 (dầu hút trong hành phi). F042/F057/F058 là ước lượng rau gia vị tương đương.
Dầu F061/F077 có thành phần khá ổn định nhưng **khối lượng dầu thực ăn** nhạy cảm nhất trong công thức.

JdbcRecipeReadAdapter có thể đọc các Food/Recipe active và nguyên liệu dương, đầy đủ, không NULL.
Tất cả tổng cho một phần nằm trong DECIMAL(12,3); không có cam kết mọi số phần đến trần DECIMAL(8,2) đều nhân được — Service/Calculator vẫn phải chặn overflow khi người dùng tăng khẩu phần.
Giữ nguyên NutritionCalculator, NutritionFacts, DaySummary, CurrentUser, RecipeReadPort và kiểm tra Premium.
Auth/Payment/Dashboard không được triển khai thêm. Hợp đồng Food/Recipe về sau phải giữ ID ổn định và thống nhất ý nghĩa gram/trạng thái cân.
LIKE/DISLIKE hiện đối chiếu Food ID trực tiếp; Food hỗn hợp không mở rộng thành phần ẩn nên **không đủ để bảo đảm tránh dị ứng**.

Dữ liệu máy: [vietnamese_catalog.json](../../database/seed/vietnamese_catalog.json).
SQL và hướng dẫn: [database/seed/README.md](../../database/seed/README.md).
Lần này chỉ kiểm tra tĩnh; chưa chạy SQL, chưa chứng minh hành vi MySQL thực tế hay giao diện Meal Planner.
