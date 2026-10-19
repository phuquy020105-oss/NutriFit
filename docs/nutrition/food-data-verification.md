# Kiểm chứng dữ liệu Food — staging, đang thực hiện

Báo cáo được tái tạo bằng `database/tools/food_quality/write_reports.py`. Không phải phê duyệt migration.

Đã đối chiếu 82 Food, 410 nutrient. 59 Food có đủ năm giá trị nguồn/quy đổi để so sánh; không đồng nghĩa đã đo/VERIFIED trong món Việt. 0 Food VERIFIED toàn bộ.

| Trạng thái nutrient | Số lượng |
|---|---:|
| VERIFIED | 0 |
| MATCHED | 175 |
| CALCULATED | 120 |
| ESTIMATED | 17 |
| MISSING | 98 |

## Nguồn và chuẩn hóa

- USDA SR Legacy04/2018: ZIP chính thức, SHA256 `b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0`; 7.793 Food, 644.125 nutrient rows. Ngày publication2019-04-01 khác ngày release. Có row ID, derivation và source gốc cho từng chỉ số; không gọi tất cả là kết quả phòng thí nghiệm.
- [NIN tra cứu công khai](https://viendinhduong.vn/vi/cong-cu-va-tien-ich/gia-tri-dinh-duong-thuc-pham): 100g phần ăn được; 38 truy vấn snapshot2026-10-19 có checksum. Release và phương pháp chất xơ/carbohydrate của live lookup chưa công bố rõ. Null/absent giữ thiếu; không biến cellulose thành tổng dietary fiber. Các bản ghi thay thế giữ trong JSON, không trộn macro của một record với fiber record khác.
- [MEXT English2015](https://www.mext.go.jp/en/policy/science_technology/policy/title01/detail01/sdetail01/sdetail01/1385122.htm): 2.191 Food; workbook cập nhật2017-12-27, không phải edition2023. SHA256 `5c968f1801f706b2970d51599ab2dce6f9e09ff3901fcf1990922960761885fb`. Bốn matching:02028 bột năng;06207 hẹ lá;11133 heo luộc bỏ mỡ ngoài;17016 giấm gạo. Khác biệt giống/cut/nồng độ vẫn được ghi.
- [MEXT phương pháp, tr.24–25](https://www.mext.go.jp/component/english/__icsFiles/afieldfile/2017/10/02/1385123_Standard-Table_Chap.1_Prov_1.pdf): giữ `(0)` là nguồn ước tính; `Tr` không phải0, dấu gạch là chưa có số đo. Loại bỏ đuôi nhị phân Excel theo độ chính xác công bố (macro/fiber1 chữ số, kcal số nguyên), đồng thời lưu nguyên văn ô nguồn.
- [FAO carbohydrate](https://www.fao.org/4/Y5022E/y5022e03.htm): giữ hợp đồng carbs khả dụng hiện có; dùng total carbohydrate trừ dietary fiber cùng record, ghi CALCULATED và giữ hai đầu vào. Kcal giữ số nguồn, không ép4/4/9. Đây là phép tính by-difference, có giới hạn phân tích và không phải đo trực tiếp.
- SMILING Việt Nam2013 theo liên kết FAO: hai workbook trả HTTP403; không được dùng làm bằng chứng đã đọc.

## Phạm vi và hạn chế

Nguồn có giá trị không tự chứng minh đúng loài, độ ngậm nước, phần mỡ hoặc công thức thành phẩm. Mọi production_change_approved hiện là false. Baseline JSON/SQL và dữ liệu Aiven chưa bị thay đổi. MATCHED là đối chiếu thực phẩm tương đương có sai khác, CALCULATED là phương pháp công bố hoặc quy đổi rõ ràng, ESTIMATED có thể là ước tính do chính nguồn ghi; MISSING không được điền từ baseline.

Các candidate bị loại vẫn được giữ trong source-candidates.json: tapioca pearl không phải bột năng; common chive không phải hẹ lá; cua biển không phải riêu cua đồng; ba chỉ sống không thay ba chỉ luộc; raw quail không thay trứng cút luộc. MEXT bổ sung được bột năng/hẹ nhưng không hợp thức hóa các candidate sai trước đó.

## Những sai khác đáng chú ý

- NIN sả có energy1kcal/100g nhưng macro không tương xứng: giữ nguyên bằng chứng và đánh dấu cần review, không tự sửa energy bằng4/4/9.
- NIN ngò gai có English parsley: chưa giải quyết được định danh, không thay ngò gai bằng parsley.
- Mộc nhĩ khô USDA có fiber70.1g/100g, baseline25g; khác lớn và phương pháp/định nghĩa cần review trước migration. Không lấy fiber7g của NIN ghép macro USDA để tạo số mong muốn.
- Nước dùng bò/gà nguồn generic không xác minh được nồng độ, lượng mỡ và cách lọc của nước dùng Việt. Kết quả so sánh không phải chứng nhận công thức.

## Nguyên liệu ảnh hưởng nhiều nhất

| Food | Tên | Số recipe |
|---|---|---:|
| F064 | Đường trắng tinh luyện | 27 |
| F062 | Nước mắm nguyên chất | 26 |
| F066 | Tiêu đen xay khô | 24 |
| F071 | Nước lọc dùng trong món | 22 |
| F039 | Hành lá sống | 21 |
| F061 | Dầu đậu nành tinh luyện | 21 |
| F035 | Dưa leo sống, giữ vỏ ăn được | 18 |
| F046 | Tỏi ta sống, bóc vỏ | 18 |
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu | 17 |
| F047 | Hành tím sống, bóc vỏ | 14 |
| F067 | Nước cốt chanh tươi, bỏ hạt | 11 |
| F034 | Cà chua sống | 10 |

## Đối chiếu đủ82 Food

Đơn vị thứ tự K/P/C/F/Fiber: kcal/g/g/g/g trên100g ăn được; dấu — là thiếu. Giá trị cũ, delta, raw values, ô/row ID và nguồn đầy đủ nằm trong [food-provenance.json](../../database/staging/food-quality-v1/food-provenance.json).

| Mã | Tên / trạng thái | K/P/C/F/Fiber nguồn đã chuẩn hóa | Trạng thái nutrient |
|---|---|---|---|
| F001 | Cơm trắng gạo tẻ đã nấu, không dầu (CHÍN) | 130/2.69/27.77/0.28/0.4 | CALCULATED:2, MATCHED:3 |
| F002 | Bánh phở tươi đã trụng, để ráo (CHÍN) | 108/1.79/23.01/0.2/1 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F003 | Bún tươi đã trụng, để ráo (CHÍN) | 108/1.79/23.01/0.2/1 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F004 | Hủ tiếu gạo đã trụng, để ráo (CHÍN) | 108/1.79/23.01/0.2/1 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F005 | Bánh canh bột gạo đã luộc, để ráo (CHÍN) | —/—/—/—/— | MISSING:5 |
| F006 | Bánh mì trắng ổ không nhân (CHẾ_BIẾN) | 272/10.75/49.68/2.42/2.2 | CALCULATED:2, MATCHED:3 |
| F007 | Gạo tẻ trắng khô (SỐNG) | 365/7.13/78.65/0.66/1.3 | CALCULATED:2, MATCHED:3 |
| F008 | Xôi nếp trắng đã hấp, không dầu (CHÍN) | —/—/—/—/— | MISSING:5 |
| F009 | Bột gạo tẻ khô (KHÔ) | 366/5.95/77.73/1.42/2.4 | CALCULATED:2, MATCHED:3 |
| F010 | Bột năng khô (KHÔ) | 346/0.1/85.3/0.2/0.0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F011 | Thịt bò thăn nạc luộc chín, không sốt (CHÍN) | —/—/—/—/— | MISSING:5 |
| F012 | Thịt ức gà luộc chín, bỏ da (CHÍN) | 151/28.98/0/3.03/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F013 | Thịt đùi gà hấp chín, có da, bỏ xương (CHÍN) | 232/23.26/0/14.74/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F014 | Thịt bắp bò luộc chín (CHÍN) | 201/33.68/0/6.36/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F015 | Thịt heo nạc luộc chín (CHÍN) | 199/28.9/0.3/8.1/0.0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F016 | Thịt heo nạc băm hấp chín, không dầu (CHÍN) | —/—/—/—/— | MISSING:5 |
| F017 | Gan heo luộc chín (CHÍN) | 165/26.02/3.76/4.4/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F018 | Thịt ba chỉ heo luộc chín, giữ lớp mỡ ăn được (CHÍN) | —/—/—/—/— | MISSING:5 |
| F019 | Thịt nạc vai heo nướng chín, không sốt (CHÍN) | 259/25.58/0/16.61/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F020 | Thịt sườn heo hấp chín, bỏ xương, không sốt (CHÍN) | 397/29.06/0/30.3/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F021 | Thịt bò thăn áp chảo chín, không dầu/sốt (CHÍN) | 198/30.7/0/8.32/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F022 | Thịt đùi gà hấp chín, bỏ da và xương (CHÍN) | 195/25/0/9.79/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F023 | Thịt cá lóc hấp chín, bỏ xương, không dầu/sốt (CHÍN) | —/—/—/—/— | MISSING:5 |
| F024 | Thịt cá rô phi hấp chín, bỏ xương, không dầu/sốt (CHÍN) | —/—/—/—/— | MISSING:5 |
| F025 | Tôm thẻ luộc chín, bóc vỏ (CHÍN) | 99/23.98/—/0.28/— | CALCULATED:1, MATCHED:2, MISSING:2 |
| F026 | Thịt/riêu cua đồng nấu chín, lọc sạch vỏ (CHÍN) | —/—/—/—/— | MISSING:5 |
| F027 | Thịt cua biển hấp chín, gỡ vỏ (CHÍN) | 83/17.88/0/0.74/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F028 | Trứng gà nguyên quả sống, bỏ vỏ (SỐNG) | 143/12.56/0.72/9.51/0 | CALCULATED:2, MATCHED:3 |
| F029 | Trứng gà luộc chín, bỏ vỏ (CHÍN) | 155/12.58/1.12/10.61/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F030 | Trứng cút luộc chín, bỏ vỏ (CHÍN) | —/—/—/—/— | MISSING:5 |
| F031 | Đậu hũ trắng không chiên (CHẾ_BIẾN) | 76/8.08/1.57/4.78/0.3 | CALCULATED:2, MATCHED:3 |
| F032 | Chả lụa thành phẩm (CHẾ_BIẾN) | —/—/—/—/— | MISSING:5 |
| F033 | Đậu phộng rang không muối, bỏ vỏ lụa (CHÍN) | 587/24.35/12.86/49.66/8.4 | CALCULATED:2, MATCHED:3 |
| F034 | Cà chua sống (SỐNG) | 18/0.88/2.69/0.2/1.2 | CALCULATED:2, MATCHED:3 |
| F035 | Dưa leo sống, giữ vỏ ăn được (SỐNG) | 15/0.65/3.13/0.11/0.5 | CALCULATED:2, MATCHED:3 |
| F036 | Xà lách sống (SỐNG) | 15/1.36/1.57/0.15/1.3 | CALCULATED:2, MATCHED:3 |
| F037 | Giá đỗ đậu xanh sống (SỐNG) | 30/3.04/4.14/0.18/1.8 | CALCULATED:2, MATCHED:3 |
| F038 | Hành tây sống (SỐNG) | 40/1.1/7.64/0.1/1.7 | CALCULATED:2, MATCHED:3 |
| F039 | Hành lá sống (SỐNG) | 32/1.83/4.74/0.19/2.6 | CALCULATED:2, MATCHED:3 |
| F040 | Ngò rí sống (SỐNG) | 23/2.13/0.87/0.52/2.8 | CALCULATED:2, MATCHED:3 |
| F041 | Húng quế sống (SỐNG) | 23/3.15/1.05/0.64/1.6 | CALCULATED:2, MATCHED:3 |
| F042 | Rau răm sống (SỐNG) | 45/4.7/—/—/— | MATCHED:2, MISSING:3 |
| F043 | Hẹ lá sống (SỐNG) | 21/1.7/1.3/0.3/2.7 | CALCULATED:2, MATCHED:3 |
| F044 | Sả tươi băm, phần lõi ăn được (SỐNG) | 99/1.82/—/0.49/— | CALCULATED:1, MATCHED:2, MISSING:2 |
| F045 | Gừng tươi sống, gọt vỏ (SỐNG) | 80/1.82/15.77/0.75/2 | CALCULATED:2, MATCHED:3 |
| F046 | Tỏi ta sống, bóc vỏ (SỐNG) | 149/6.36/30.96/0.5/2.1 | CALCULATED:2, MATCHED:3 |
| F047 | Hành tím sống, bóc vỏ (SỐNG) | 72/2.5/13.6/0.1/3.2 | CALCULATED:2, MATCHED:3 |
| F048 | Ớt tươi sống (SỐNG) | 40/1.87/7.31/0.44/1.5 | CALCULATED:2, MATCHED:3 |
| F049 | Cà rốt sống, sơ chế (SỐNG) | 41/0.93/6.78/0.24/2.8 | CALCULATED:2, MATCHED:3 |
| F050 | Củ cải trắng sống, sơ chế (SỐNG) | 18/0.6/2.5/0.1/1.6 | CALCULATED:2, MATCHED:3 |
| F051 | Đu đủ xanh sống, bỏ vỏ/hạt (SỐNG) | 30/0.8/—/—/— | MATCHED:2, MISSING:3 |
| F052 | Ớt chuông sống (SỐNG) | 26/0.99/3.93/0.3/2.1 | CALCULATED:2, MATCHED:3 |
| F053 | Thơm chín tươi, bỏ vỏ/mắt/lõi cứng (SỐNG) | 50/0.54/11.72/0.12/1.4 | CALCULATED:2, MATCHED:3 |
| F054 | Đậu bắp sống, bỏ cuống (SỐNG) | 33/1.93/4.25/0.19/3.2 | CALCULATED:2, MATCHED:3 |
| F055 | Bạc hà/dọc mùng, phần thân đã tước vỏ (SỐNG) | 13/0.4/—/—/— | MATCHED:2, MISSING:3 |
| F056 | Bí đỏ sống, bỏ vỏ/hạt (SỐNG) | 26/1/6.0/0.1/0.5 | CALCULATED:2, MATCHED:3 |
| F057 | Rau ngổ sống (SỐNG) | 24/1.5/—/—/— | MATCHED:2, MISSING:3 |
| F058 | Ngò gai sống (SỐNG) | —/—/—/—/— | MISSING:5 |
| F059 | Nấm mèo khô (KHÔ) | 284/9.25/2.91/0.73/70.1 | CALCULATED:2, MATCHED:3 |
| F060 | Nấm hương khô (KHÔ) | 296/9.58/63.87/0.99/11.5 | CALCULATED:2, MATCHED:3 |
| F061 | Dầu đậu nành tinh luyện (CHẾ_BIẾN) | 884/0/0/100/0 | CALCULATED:2, MATCHED:3 |
| F062 | Nước mắm nguyên chất (CHẾ_BIẾN) | 35/5.06/3.64/0.01/0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F063 | Nước tương lên men (CHẾ_BIẾN) | 53/8.14/4.13/0.57/0.8 | CALCULATED:2, MATCHED:3 |
| F064 | Đường trắng tinh luyện (CHẾ_BIẾN) | 387/0/99.98/0/0 | CALCULATED:2, MATCHED:3 |
| F065 | Muối ăn iod (CHẾ_BIẾN) | 0/0/0/0/0 | CALCULATED:2, MATCHED:3 |
| F066 | Tiêu đen xay khô (KHÔ) | 251/10.39/38.65/3.26/25.3 | CALCULATED:2, MATCHED:3 |
| F067 | Nước cốt chanh tươi, bỏ hạt (CHẾ_BIẾN) | 25/0.42/8.02/0.07/0.4 | CALCULATED:2, MATCHED:3 |
| F068 | Giấm gạo (CHẾ_BIẾN) | 46/0.2/7.4/0.0/0.0 | CALCULATED:2, ESTIMATED:1, MATCHED:2 |
| F069 | Thịt me chín dạng nhuyễn, bỏ hạt (CHẾ_BIẾN) | 239/2.8/57.4/0.6/5.1 | CALCULATED:2, MATCHED:3 |
| F070 | Nước dừa tươi (SỐNG) | 19/0.72/2.61/0.2/1.1 | CALCULATED:2, MATCHED:3 |
| F071 | Nước lọc dùng trong món (CHẾ_BIẾN) | 0/0/0/0/0 | CALCULATED:2, MATCHED:3 |
| F072 | Nước dùng phở bò thành phẩm, không nêm (CHẾ_BIẾN) | 13/1.97/1.2/0.09/0 | CALCULATED:2, MATCHED:3 |
| F073 | Nước dùng gà thành phẩm, không nêm (CHẾ_BIẾN) | 36/2.52/3.53/1.2/0 | CALCULATED:2, MATCHED:3 |
| F074 | Nước dùng heo thành phẩm, không nêm (CHẾ_BIẾN) | —/—/—/—/— | MISSING:5 |
| F075 | Mắm ruốc Huế thành phẩm (CHẾ_BIẾN) | —/—/—/—/— | MISSING:5 |
| F076 | Mắm tôm thành phẩm (CHẾ_BIẾN) | 73/14.8/—/1.5/— | MATCHED:3, MISSING:2 |
| F077 | Dầu điều màu thành phẩm (CHẾ_BIẾN) | —/—/—/—/— | MISSING:5 |
| F078 | Bột nghệ khô (KHÔ) | 312/9.68/44.44/3.25/22.7 | CALCULATED:2, MATCHED:3 |
| F079 | Mật ong (CHẾ_BIẾN) | 304/0.3/82.2/0/0.2 | CALCULATED:2, MATCHED:3 |
| F080 | Hành phi thành phẩm (CHẾ_BIẾN) | —/—/—/—/— | MISSING:5 |
| F081 | Cơm gạo tấm đã nấu, không dầu (CHÍN) | 130/2.69/27.77/0.28/0.4 | CALCULATED:2, MATCHED:3 |
| F082 | Thịt heo băm viên nướng chín, không sốt (CHÍN) | —/—/—/—/— | MISSING:5 |

## Tái lập

Xem [công cụ offline](../../database/tools/food_quality/README.md). Mỗi lần thay catalog phải làm mới provenance và audit cùng SHA; không dùng dữ liệu này trực tiếp làm seed.
