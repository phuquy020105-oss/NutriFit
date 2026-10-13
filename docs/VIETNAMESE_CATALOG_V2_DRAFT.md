# Vietnamese Food Catalog V2 — bản đồ án thực tế (2026-10-12)

**Phần này thay thế mục tiêu/tiêu chuẩn của các hồ sơ lịch sử bên dưới.**
Mục tiêu hiện tại: danh mục tuyển chọn khoảng 100 món; không tiếp tục 250 món.
READY_ESTIMATED là đủ đầu vào để review công thức ước tính cho đồ án; không phải
kiểm nghiệm dinh dưỡng, duyệt import hoặc phê duyệt ghi MySQL. PENDING là thiếu đầu vào
cơ bản/số liệu chưa hợp lý; REJECTED là trùng/không phù hợp. Giữ trạng thái READY cũ
cho hồ sơ lịch sử, nhưng batch thực tế dùng READY_ESTIMATED.

Input → gram nguyên liệu phần ăn được + profile nguồn + giả định dầu/nước/thất thoát
→ tính từng nutrient, kiểm tra số học/mass balance/portion/ID → số trên 100 g và
batch review JSON. Runtime vẫn đọc MySQL, không đọc DRAFT. Không đổi MealPlanner,
Gemini, QuickFood, Auth/Profile/Payment/Frontend hoặc công thức mục tiêu ngày.

## Cập nhật danh mục tuyển chọn

Batch tiếp nối: 28 món mới READY_ESTIMATED trong `completion_batch.json`.
Đủ dữ liệu cho 39/40 món đề xuất; cơm tấm sườn bì chả giữ PENDING vì thiếu
profile bì heo luộc phù hợp. Không cập nhật ID cũ hoặc `pho_beef`.
Sau import được duyệt, dự kiến 141 active với 99/100 ID tuyển chọn hiện diện.
DRAFT hiện có 49 hồ sơ: 40 READY_ESTIMATED (gồm đề xuất `pho_beef`), 9 PENDING
(8 hồ sơ nghiên cứu ID cũ và 1 món mới). Nguồn/giả định mới nằm trong
`ingredient_sources.json` và từng recipe; không phải số đo thành phẩm thực nghiệm.

## Batch 12 đã hoàn thiện (kết quả lịch sử)

12 READY_ESTIMATED, 0 PENDING trong batch; tại thời điểm batch đầu, 40 DRAFT: 12 READY_ESTIMATED,
28 PENDING. Giữ nguyên nghiên cứu cũ trong research_history. Món đang review ID cũ
pho_beef được tách khỏi 11 món mới; baseline_snapshot cũ không sửa.

| ID / món | Role | kcal/100g | P/C/F g/100g | Reference g | Min–max g | kcal/reference |
|---|---|---:|---|---:|---|---:|
| pho_beef — Phở bò | MAIN | 63.3 | 4.63/9.58/0.58 | 600 | 400–800 | 379.6 |
| vn_thit_kho_tieu — Thịt kho tiêu | PROTEIN | 262.4 | 15.64/3.75/20.72 | 130 | 80–180 | 341.2 |
| vn_thit_kho_trung — Thịt kho trứng | PROTEIN | 181.4 | 11.96/3.47/13.39 | 200 | 100–260 | 362.8 |
| vn_ca_loc_kho_to — Cá lóc kho tộ | PROTEIN | 118.7 | 15.45/5.53/4.05 | 150 | 90–210 | 178.0 |
| vn_dau_phu_sot_ca_chua — Đậu phụ sốt cà chua | PROTEIN | 95.9 | 6.35/3.99/6.18 | 187.5 | 100–260 | 179.8 |
| vn_rau_muong_xao_toi — Rau muống xào tỏi | VEGGIE | 48.3 | 3.29/4.22/2.15 | 170 | 80–240 | 82.1 |
| vn_cai_ngot_luoc — Cải ngọt luộc | VEGGIE | 17.7 | 1.40/0.90/0.30 | 120 | 60–240 | 21.2 |
| vn_cai_thia_xao_nam — Cải thìa xào nấm | VEGGIE | 52.2 | 1.69/4.87/3.41 | 143.33 | 70–210 | 74.8 |
| vn_canh_rau_ngot_thit_bam — Canh rau ngót thịt băm | SOUP | 25.8 | 2.79/0.98/1.21 | 275 | 150–380 | 70.9 |
| vn_canh_bi_dao_thit_bam — Canh bí đao thịt băm | SOUP | 30.5 | 2.92/1.12/1.63 | 290 | 150–400 | 88.6 |
| vn_canh_ca_chua_trung — Canh cà chua trứng | SOUP | 38.6 | 1.86/1.87/2.67 | 240 | 150–350 | 92.6 |
| vn_bun_rieu_cua — Bún riêu cua | MAIN | 64.5 | 3.10/8.52/2.04 | 700 | 450–850 | 451.6 |

Số trên 100 g là thành phẩm ăn được, gồm nước canh nếu có. Món nguyên liệu/component
không bị gắn nhầm MAIN; phở/bún riêu là món hoàn chỉnh, chỉ MAIN/breakfast theo
composition rules hiện hành; Quick Food có thể ghi món hoàn chỉnh với mealType khác.
Không cộng thành phần của một tô thêm lần nữa khi đã ghi cả tô.

Công thức/nguồn/định lượng chi tiết: [SOURCES](VIETNAMESE_CATALOG_V2_SOURCES.md).
Đậu phụ sốt có mắm/dầu hào; cải thìa xào nấm có dầu mè/dầu hào. Avoid tags vẫn gồm
fish/seafood/soy/egg/sesame phù hợp. Không cam kết an toàn dị ứng hoặc thấp natri.
Ba món canh không có fat nguồn2007 đầy đủ dùng NGUYÊN profile SMILING tương ứng,
không ghép fat0 vào record2007. Cellulose/crude fiber không chuyển thànhTDF;
fiber chưa đủ giữNULL và runtime báo fiber_complete=false.

## Danh sách 100 mục tiêu, chia nhóm

E = đã có ID trong catalog102; N = cần bổ sung. R = đã READY_ESTIMATED ở batch này;
P = còn nghiên cứu/proposed, chưa import. Existing estimate chưa đồng nghĩa được
review lại hoàn toàn; xem phân loại từng 102 ID trong existing_catalog_audit.json.
100 là danh mục mục tiêu, không lệnh xóa/hủy kích hoạt42 ID không được tuyển chọn.

### CARB — 13 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Cơm trắng | rice | E | Existing estimate |
| Khoai lang hấp | sweet_potato | E | Existing estimate |
| Bún tươi | rice_noodles | E | Existing estimate |
| Cơm gạo lứt | usda_169704 | E | Existing estimate |
| Khoai tây luộc không muối, phần thịt | usda_170438 | E | Existing estimate |
| Hạt bắp vàng đông lạnh luộc không muối | usda_168399 | E | Existing estimate |
| Bánh mì trắng không muối | usda_172818 | E | Existing estimate |
| Cơm nếp | vn_com_nep | N | P |
| Bánh phở chín | vn_banh_pho_chin | N | P |
| Miến dong chín | vn_mien_dong_chin | N | P |
| Hủ tiếu chín | vn_hu_tieu_chin | N | P |
| Bánh canh gạo chín | vn_banh_canh_gao_chin | N | P |
| Khoai môn hấp | vn_khoai_mon_hap | N | P |

### PROTEIN — 26 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Ức gà hấp | chicken | E | Existing estimate |
| Gà áp chảo ít dầu | chicken_oil | E | Existing estimate |
| Bò áp chảo | beef | E | Existing estimate |
| Heo nạc hấp | pork | E | Existing estimate |
| Cá hấp | fish | E | Existing estimate |
| Tôm hấp | shrimp | E | Existing estimate |
| Đậu phụ hấp | tofu | E | Existing estimate |
| Trứng luộc | eggs | E | Existing estimate |
| Ức gà nướng bỏ da | usda_171477 | E | Existing estimate |
| Thịt đùi gà nướng bỏ da | usda_172388 | E | Existing estimate |
| Heo thăn nướng, gồm nạc và mỡ | usda_167904 | E | Existing estimate |
| Cá rô phi chín bằng nhiệt khô | usda_175177 | E | Existing estimate |
| Cá thu Thái Bình Dương, chín bằng nhiệt khô | usda_171994 | E | Existing estimate |
| Trứng omelet | usda_172185 | E | Existing estimate |
| Đậu phụ firm, dùng calcium sulfate và nigari | usda_172448 | E | Existing estimate |
| Thịt kho tiêu | vn_thit_kho_tieu | N | R |
| Thịt kho trứng | vn_thit_kho_trung | N | R |
| Trứng chiên hành | vn_trung_chien_hanh | N | P |
| Gà luộc | vn_ga_luoc | N | P |
| Gà kho gừng | vn_ga_kho_gung | N | P |
| Cá lóc kho tộ | vn_ca_loc_kho_to | N | R |
| Cá nục kho cà chua | vn_ca_nuc_kho_ca_chua | N | P |
| Tôm rim mặn ngọt | vn_tom_rim_man_ngot | N | P |
| Đậu phụ sốt cà chua | vn_dau_phu_sot_ca_chua | N | R |
| Đậu phụ nhồi thịt | vn_dau_phu_nhoi_thit | N | P |
| Đậu phụ kho nấm | vn_dau_phu_kho_nam | N | P |

### VEGGIE — 20 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Rau luộc | vegetables | E | Existing estimate |
| Rau xào ít dầu | vegetables_oil | E | Existing estimate |
| Bông cải xanh luộc | usda_169967 | E | Existing estimate |
| Cà rốt luộc không muối | usda_170394 | E | Existing estimate |
| Bắp cải luộc | usda_169976 | E | Existing estimate |
| Súp lơ luộc | usda_170397 | E | Existing estimate |
| Bí đỏ luộc không muối | usda_168449 | E | Existing estimate |
| Nấm trắng luộc không muối | usda_169252 | E | Existing estimate |
| Cà chua đỏ chín, nấu chín | usda_170050 | E | Existing estimate |
| Dưa leo còn vỏ, sống | usda_168409 | E | Existing estimate |
| Xà lách lá xanh, sống | usda_169249 | E | Existing estimate |
| Cà tím luộc không muối | usda_169229 | E | Existing estimate |
| Rau muống luộc | vn_rau_muong_luoc | N | P |
| Rau muống xào tỏi | vn_rau_muong_xao_toi | N | R |
| Cải ngọt luộc | vn_cai_ngot_luoc | N | R |
| Cải thìa xào nấm | vn_cai_thia_xao_nam | N | R |
| Mướp xào đậu phộng | vn_muop_xao_dau_phong | N | P |
| Cà tím nướng mỡ hành | vn_ca_tim_nuong_mo_hanh | N | P |
| Khổ qua xào trứng | vn_kho_qua_xao_trung | N | P |
| Nộm đu đủ xanh | vn_nom_du_du_xanh | N | P |

### SOUP — 11 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Canh rau | soup | E | Existing estimate |
| Canh rau thịt gà | chicken_soup | E | Existing estimate |
| Canh rau ngót thịt băm | vn_canh_rau_ngot_thit_bam | N | R |
| Canh tôm rau ngót bắp | vn_canh_tom_rau_ngot_bap | N | P |
| Canh mồng tơi cua | vn_canh_mong_toi_cua | N | P |
| Canh bầu nấu tôm | vn_canh_bau_nau_tom | N | P |
| Canh bí đao thịt băm | vn_canh_bi_dao_thit_bam | N | R |
| Canh cà chua trứng | vn_canh_ca_chua_trung | N | R |
| Canh khổ qua nhồi thịt và cá | vn_canh_kho_qua_nhoi_thit_va_ca | N | P |
| Canh chua cá lóc | vn_canh_chua_ca_loc | N | P |
| Canh mướp nấm | vn_canh_muop_nam | N | P |

### MAIN — 15 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Bánh mì trứng | bread_egg | E | Existing estimate |
| Bánh mì gà | bread_chicken | E | Existing estimate |
| Phở gà | pho_chicken | E | Existing estimate |
| Phở bò | pho_beef | E | R |
| Xôi gà | breakfast_main_d2_o1 | E | Existing estimate |
| Bánh cuốn thịt | breakfast_main_d3_o1 | E | Existing estimate |
| Miến gà | breakfast_main_d4_o2 | E | Existing estimate |
| Cháo gà | breakfast_main_d5_o2 | E | Existing estimate |
| Bún bò rau cải | breakfast_main_d6_o2 | E | Existing estimate |
| Xôi trứng | breakfast_main_d7_o1 | E | Existing estimate |
| Bún bò Huế | vn_bun_bo_hue | N | P |
| Bún riêu cua | vn_bun_rieu_cua | N | R |
| Bún thịt nướng | vn_bun_thit_nuong | N | P |
| Mì Quảng gà | vn_mi_quang_ga | N | P |
| Cơm tấm sườn bì chả | vn_com_tam_suon_bi_cha | N | P |

### DESSERT — 12 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Chuối | banana | E | Existing estimate |
| Sữa chua không đường | yogurt | E | Existing estimate |
| Cam | usda_169097 | E | Existing estimate |
| Đu đủ | usda_169926 | E | Existing estimate |
| Xoài | usda_169910 | E | Existing estimate |
| Ổi | usda_173044 | E | Existing estimate |
| Dứa | usda_169124 | E | Existing estimate |
| Dưa hấu | usda_167765 | E | Existing estimate |
| Quả bơ | usda_171705 | E | Existing estimate |
| Vải | usda_169086 | E | Existing estimate |
| Nhãn | usda_169089 | E | Existing estimate |
| Mít | usda_174687 | E | Existing estimate |

### DRINK — 3 món

| Món | Dish ID | Đã có/cần bổ sung | Trạng thái |
|---|---|---|---|
| Sữa bò nguyên kem 3,25%, bổ sung vitamin D | usda_171265 | E | Existing estimate |
| Sữa đậu nành original/vanilla, không tăng cường vi chất | usda_172446 | E | Existing estimate |
| Sữa đậu nành không đường | vn_sua_dau_nanh_khong_duong | N | P |

60 ID hiện có + 40 món mới đề xuất = 100. Chỉ 11 món mới đã đủ batch review;
29 món mới còn lại vẫn là đề xuất, chưa tạo bản ghi dinh dưỡng hoặc đưa vào seed.
102 ID cũ được giữ trong `preserved_runtime_ids`. Roadmap 250 được lưu trong
`research_archive` để bảo toàn nghiên cứu, nhưng đã ngừng dùng làm tiêu chí.

Phân loại 102 hiện có: 17 món Việt giữ estimate; 15 món Việt cần review tên,
công thức hoặc khẩu phần; 50 thành phần/trái cây/sữa phổ biến; 20 món quốc tế hoặc
trùng lặp cần cân nhắc. `practical_review` đánh giá từng ID. Nguồn USDA không tự
biến một nguyên liệu thành món Việt. Ví dụ cần review riêng: xôi dùng cơm thường;
bánh cuốn dùng bánh gạo tham khảo; miến dùng sợi chín chung; cá/rau/canh chưa rõ
loại; hai MAIN khoai lang trùng với CARB. Chưa thay đổi bất kỳ ID runtime nào.

## Batch review và cách import sau phê duyệt

[review_batch.json](../setup/drafts/vietnamese_catalog_v2/review_batch.json) chứa:

- `dishes`: 11 profile tương thích seed/runtime; `active=true` là giá trị đề xuất.
- `legacy_menus`: rỗng; không sửa 63 template.
- `review_existing`: phương án và before-image cho `pho_beef`, tách khỏi insert.
- `apply_authorized=false`; DRAFT gốc vẫn `active=false`, `import_ready=false`.

Các bước ngắn nhất:

1. Chốt 12 biến thể tham khảo và giả định. Review attribution các nguồn, giữ thông
   báo hạn chế dữ liệu; FSANZ có điều kiện attribution/share-alike riêng.
2. Xác nhận đúng NutriFitDB local; backup mới ngoài Git và kiểm tra khả năng phục
   hồi trên DB riêng nếu cần. Chụp counts, schema, before-images và fingerprint.
   Nhiệm vụ hiện tại chưa tạo backup hoặc thử restore vì chưa ghi dữ liệu.
3. Kiểm tra 11 ID/tên chưa tồn tại và validate batch. Sau phê duyệt, append đúng
   11 món qua CLI `--batch` đã chuẩn bị trong một transaction DML. CLI không tự
   đọc DRAFT khi không chỉ định batch; `--check-db` chỉ đọc, apply yêu cầu backup.
4. Insert-only: runtime 102 → 113 dòng; chạy lại phải thêm 0 dòng. Seed bỏ qua ID
   đã có, nên không tự cập nhật `pho_beef`. Hiệu chỉnh món này cần được duyệt riêng,
   giữ before-image và chính sách DataVersion; không backfill snapshot lịch sử.
5. Kiểm tra Search → Preview → Confirm → Daily/History với tài khoản demo trên
   MySQL sau khi được duyệt. Không coi SQLite mock là kết quả MySQL thật.

Thu gọn danh mục active về 100 là rollout riêng: hoàn thiện 29 món mới còn lại,
review 42 ID ngoài danh mục để cân nhắc deactivate. Mọi ID và lịch sử được giữ;
không tự deactivate hoặc xóa trong nhiệm vụ này.

Rollback: trước commit DML có thể rollback transaction. Sau commit, ưu tiên duyệt
ngừng gợi ý đúng ID mới đã thêm; không xóa món đã được tham chiếu. Nếu hiệu chỉnh
`pho_beef` được duyệt riêng, có thể khôi phục bản ghi catalog từ before-image;
không sửa snapshot hoặc nhật ký đã ăn. Không có DDL trong batch này.

## Kết quả kiểm tra

Quy trình/lệnh backup, dry-run, import, verify và rollback có kiểm tra tham chiếu:
[VIETNAMESE_CATALOG_V2_IMPORT.md](VIETNAMESE_CATALOG_V2_IMPORT.md).

- Validator offline và seed validate-only: PASS; `database_writes=0`.
- Batch 11 qua `load_seed(path)`: PASS cấu trúc; không gọi apply.
- Full regression: **310/310 PASS**, 139,55 giây. Bao gồm 36 tests dữ liệu DRAFT
  và 14 tests batch/import preparation; tests cache, revision, Replace, Quick Food, ownership,
  snapshot/history và Food Intake hiện có cũng PASS.
- Regression chặn `pymysql.connect` và socket ngoài; fixture SQLite in-memory,
  SMTP mock và Gemini mock. Schema chỉ được dịch sang SQLite trong fixture;
  không chạy script schema trên MySQL.
- Không kiểm thử Chrome hoặc ghi MySQL bằng món mới, không gọi Gemini/payment
  thật. Metadata giả định chỉ trong DRAFT/provenance; không thêm trường schema.
- Đối chiếu MySQL bằng SELECT trong transaction READ ONLY: vẫn 18 bảng,
  102 món active và 63 template. Số dòng và fingerprint nội dung cả 18 bảng
  khớp đầu/cuối phiên. Seed và mọi file tracked giữ nguyên; 28 DRAFT ngoài batch
  cùng các source profile có sẵn được bảo toàn. Python AST/JSON/whitespace và
  quét secret trong nội dung DRAFT/tests/docs: PASS, không phát hiện secret mới.

---

## Hồ sơ lịch sử — mục tiêu250/tiêu chuẩnREADY nghiêm ngặt đã được thay thế

# Vietnamese Food Catalog V2 — DRAFT để review

Kiểm tra ngày 2026-10-11 trên feature/nutrition-mysql-food-catalog, HEAD 3aadc70.
Working tree sạch khi bắt đầu; năm file V4.1 đã được commit/push từ nhiệm vụ trước,
không còn modified để bảo toàn theo mô tả cũ. Nhiệm vụ này không sửa các file đó.

Mục tiêu: cải thiện lựa chọn cơm nhà/món hoàn chỉnh Việt Nam có dữ liệu minh bạch.
Không coi 250 slot nghiên cứu là 250 món Việt đã được kiểm định hoặc đã import.
Không thay runtime source, COMPOSITION_RULES, thuật toán, schema hoặc database.

## Kiểm kê từ MySQL read-only và source

SELECT DATABASE() trả nutrifitdb, driver mysql+pymysql, host 127.0.0.1:3306.
SELECT VERSION() trả 26.7.0; đây là giá trị server báo, chưa xác minh vendor/version
triển khai hoặc coi là MySQL 8.x. Không dùng thông tin này để chạy DDL.
Hai bảng catalog báo ENGINE=InnoDB. 18 bảng, 102 món active, 63 template legacy. Các field runtime của 102 món khớp
seed đã commit. Chỉ SELECT/SHOW; không chạy migration hoặc seed --apply.

Phân loại văn hóa/kiểu món là nhận định biên tập từ tên và provenance, không phải
xác nhận nguồn khoa học hay mức phổ biến toàn quốc. USDA là nguồn số liệu; USDA
không tự khiến một nguyên liệu không phù hợp với bữa cơm Việt.

| Nhóm | Số record | Cách hiểu |
|---|---:|---|
| A | 10 | Món Việt hoàn chỉnh theo tên; công thức/dinh dưỡng vẫn cần review |
| B | 41 | Thành phần có thể phối bữa cơm Việt; không đồng nhất proxy với món địa phương |
| C | 30 | Nguyên liệu/thực phẩm mua được hoặc phổ biến; không cam kết mức độ phổ biến từng vùng |
| D | 10 | Phong cách quốc tế, giữ làm lựa chọn tham khảo |
| E | 11 | Tên/công thức/role cần review trước khi ưu tiên gợi ý mới |

81 record được đề xuất giữ trong hướng Việt, 10 record quốc tế giữ tham khảo,
11 record cần review riêng. **Tất cả 102 record vẫn giữ nguyên và active trong MySQL**;
không áp dụng phân loại trên vào runtime. Nhóm A/B không đồng nghĩa đã đủ source/yield.

Dự kiến review: cân nhắc ngừng gợi ý mới hai MAIN khoai lang trùng
breakfast_main_d2_o3/breakfast_main_d6_o3, giữ CARB sweet_potato và tất cả snapshot.
Chín record E còn lại ưu tiên sửa định danh/công thức có nguồn sau phê duyệt,
không thay ID hoặc sửa dinh dưỡng lịch sử. Đây là đề xuất, không UPDATE/IsActive
thực tế; cần kiểm tra số MAIN/avoid và compatibility trước khi quyết định.

102/102 estimated=true. 63 USDA có source ID/URL; 39 nguồn nội bộ chưa có URL
tham chiếu ngoài. Chỉ 15 record có recipe_grams/ingredient profiles trong provenance;
24 record V4 không có công thức gram trong provenance đang lưu. Fiber/P/C/F/kcal
không null trong dữ liệu hiện tại, nhưng numeric khác với được xác minh. 63 record
không có prep_minutes. MealTypesJson ghi breakfast cho cả 102 và lunch/dinner cho
81; breakfast thực sự chỉ chọn MAIN/SIDE/DRINK/DESSERT, không chọn các CARB/PROTEIN/
VEGGIE/SOUP đơn lẻ chỉ vì chúng được gắn breakfast.

Ba record Khoai lang hấp dùng cùng profile nhưng khác ID/role/reference: sweet_potato,
breakfast_main_d2_o3, breakfast_main_d6_o3. Xôi gà/xôi trứng dùng profile cơm chín;
bánh cuốn dùng profile noodles; miến gà dùng noodles/rice. Đây là lý do review,
không phải lý do xóa ID. Canh rau/canh gà và cá/rau chung thiếu định danh công thức.
Kiểm kê từng record, issues và đối chiếu 4/4/9: [existing_catalog_audit.json](../setup/drafts/vietnamese_catalog_v2/existing_catalog_audit.json).

## Roadmap đúng 250 record

Cơ cấu tham khảo của yêu cầu cộng thành 265; điều chỉnh PROTEIN/VEGGIE/SOUP giảm
mỗi nhóm 5 để có đúng 250. Đây là 102 ID giữ lại + 148 ứng viên mới, không phải
thêm 250 vào 102 rồi tạo 352 record. Một số record cũ là duplicate/reference;
con số 250 vẫn chưa là số món Việt khác biệt đã được xác minh. Không đổi ID cũ.

| Role | Hiện tại | Nghiên cứu bổ sung | Tổng slot |
|---|---:|---:|---:|
| CARB | 10 | 10 | 20 |
| PROTEIN | 21 | 44 | 65 |
| VEGGIE | 25 | 25 | 50 |
| SOUP | 2 | 28 | 30 |
| MAIN | 21 | 24 | 45 |
| SIDE | 2 | 8 | 10 |
| DESSERT | 17 | 3 | 20 |
| DRINK | 4 | 6 | 10 |

Tên/ID/role/meal intended/priority/region orientation cho từng slot:
[targets.json](../setup/drafts/vietnamese_catalog_v2/targets.json).
P1 ưu tiên batch 40 dưới đây; P2 nghiên cứu mở rộng bữa cơm và MAIN; P3 món phụ,
đồ uống/tráng miệng còn lại. Region orientation là định hướng công thức Bắc/Trung/Nam
để tìm nguồn, không gán xuất xứ lịch sử chưa chứng minh. Không tạo biến thể chỉ khác
liều dầu/gia vị để đủ slot; cần review identity/công thức thực chất trước READY.

## Batch ưu tiên 40 món

9 review-existing giữ ID để đối chiếu và 31 nghiên cứu mới. Có bốn trang công thức
được đọc và ghi một phần định lượng; chưa đủ finished_weight/nutrient matching/
portion/ingredient/allergen/licensing review. 36 món còn lại là outline nghiên cứu.
**READY 0 / PENDING 40 / REJECTED 0; số record được phép import bằng 0.**
Rejected không có nghĩa các record E cũ đã bị reject hoặc deactivate.

| Món | Role | Hành động | Trạng thái |
|---|---|---|---|
| Cơm trắng | CARB | Review ID cũ | PENDING |
| Khoai lang hấp | CARB | Review ID cũ | PENDING |
| Bún tươi | CARB | Review ID cũ | PENDING |
| Trứng luộc | PROTEIN | Review ID cũ | PENDING |
| Phở gà | MAIN | Review ID cũ | PENDING |
| Phở bò | MAIN | Review ID cũ | PENDING |
| Cơm gạo lứt | CARB | Review ID cũ | PENDING |
| Bánh cuốn thịt | MAIN | Review ID cũ | PENDING |
| Cháo gà | MAIN | Review ID cũ | PENDING |
| Thịt kho tiêu | PROTEIN | Nghiên cứu mới | PENDING |
| Thịt kho trứng | PROTEIN | Nghiên cứu mới | PENDING |
| Trứng chiên hành | PROTEIN | Nghiên cứu mới | PENDING |
| Gà luộc | PROTEIN | Nghiên cứu mới | PENDING |
| Gà kho gừng | PROTEIN | Nghiên cứu mới | PENDING |
| Cá lóc kho tộ | PROTEIN | Nghiên cứu mới | PENDING |
| Cá nục kho cà chua | PROTEIN | Nghiên cứu mới | PENDING |
| Tôm rim mặn ngọt | PROTEIN | Nghiên cứu mới | PENDING |
| Đậu phụ sốt cà chua | PROTEIN | Nghiên cứu mới | PENDING |
| Đậu phụ nhồi thịt | PROTEIN | Nghiên cứu mới | PENDING |
| Đậu phụ kho nấm | PROTEIN | Nghiên cứu mới | PENDING |
| Rau muống luộc | VEGGIE | Nghiên cứu mới | PENDING |
| Rau muống xào tỏi | VEGGIE | Nghiên cứu mới | PENDING |
| Cải ngọt luộc | VEGGIE | Nghiên cứu mới | PENDING |
| Cải thìa xào nấm | VEGGIE | Nghiên cứu mới | PENDING |
| Mướp xào đậu phộng | VEGGIE | Nghiên cứu mới | PENDING |
| Cà tím nướng mỡ hành | VEGGIE | Nghiên cứu mới | PENDING |
| Khổ qua xào trứng | VEGGIE | Nghiên cứu mới | PENDING |
| Nộm đu đủ xanh | VEGGIE | Nghiên cứu mới | PENDING |
| Canh rau ngót thịt băm | SOUP | Nghiên cứu mới | PENDING |
| Canh tôm rau ngót bắp | SOUP | Nghiên cứu mới | PENDING |
| Canh mồng tơi cua | SOUP | Nghiên cứu mới | PENDING |
| Canh bầu nấu tôm | SOUP | Nghiên cứu mới | PENDING |
| Canh bí đao thịt băm | SOUP | Nghiên cứu mới | PENDING |
| Canh cà chua trứng | SOUP | Nghiên cứu mới | PENDING |
| Canh khổ qua nhồi thịt và cá | SOUP | Nghiên cứu mới | PENDING |
| Bún bò Huế | MAIN | Nghiên cứu mới | PENDING |
| Bún riêu cua | MAIN | Nghiên cứu mới | PENDING |
| Bún thịt nướng | MAIN | Nghiên cứu mới | PENDING |
| Mì Quảng gà | MAIN | Nghiên cứu mới | PENDING |
| Cơm tấm sườn bì chả | MAIN | Nghiên cứu mới | PENDING |

Data: [draft_dishes.json](../setup/drafts/vietnamese_catalog_v2/draft_dishes.json).
Chưa biết giữ null ở gram/nutrient/yield; không dùng baseline_snapshot làm giá trị
mới. Ingredient quantities từ muỗng/lít/trái không tự đổi sang gram. Thịt kho nguồn
chưa xác nhận biến thể tiêu; món canh khổ qua nguồn có cá nên tên/tag ghi rõ cá.
Chi tiết nguồn và công thức tính: [VIETNAMESE_CATALOG_V2_SOURCES.md](VIETNAMESE_CATALOG_V2_SOURCES.md).

## Tương thích kiến trúc và giới hạn

- Breakfast: MAIN bắt buộc; SIDE/DRINK/DESSERT tùy chọn. Món hoàn chỉnh Việt có thể
  dùng ở breakfast sau review dữ liệu; khoai/ngô CARB đơn lẻ chưa được chọn làm MAIN.
- Lunch/dinner: CARB + PROTEIN + VEGGIE bắt buộc; SOUP/DESSERT tùy chọn. Chỉ hai SOUP
  hiện có, thiếu nhiều canh cơm nhà; cần bổ sung riêng công thức nước/dầu/thịt.
- Phở/bún bò/cơm tấm/Mì Quảng MAIN không thể chỉ đổi MealTypesJson để dùng trưa/tối.
  Nếu cần, thiết kế riêng hai dạng bữa: món hoàn chỉnh MAIN hoặc mâm cơm component;
  xem xét validator, candidate pool, fallback, Replace và UI. Chưa sửa hoặc phê duyệt.
- SIDE lạc/mè/hạt điều không được dùng trưa/tối theo rule hiện tại. Không gắn sai
  DESSERT/VEGGIE chỉ để lách role. Fat phù hợp cơm Việt có thể đến từ trứng/đậu phụ,
  cá/thịt phù hợp, dầu thực tế trong rau xào, mè/lạc trong recipe rau; cần định lượng.
- Avoid fish phải tính cả nước mắm; seafood phải tính mắm tôm/tép/cua. Gói nêm/dầu/
  nước dùng cần truy nguyên. API chưa hỗ trợ avoid peanut/sesame; thêm tag vào data
  không tự tạo hỗ trợ request. Không tuyên bố tránh dị ứng đầy đủ hoặc đảm bảo y khoa.
- Pool tối đa 8/role, giữ slot ranking/energy/complement và beam role limit 24.
  250 record không tự nghĩa 250 ứng viên được Gemini nhìn thấy. Lịch sử/focus/
  preferences và crop có thể bỏ món Việt hoặc món bổ trợ tốt. Hiện chưa có cuisine/
  meal-pattern scoring; score/diversity ưu tiên nutrient/ID không đánh giá món hợp nhau.
- Schema hỗ trợ stable ID/nutrient/portion/tags và ProvenanceJson đủ chỗ cho recipe.
  Chưa có state nghiên cứu READY/PENDING/REJECTED trong bảng, chỉ IsActive; vì vậy
  giữ DRAFT ngoài seed. usable() loại thiếu kcal/P/C/F/portion nhưng không chứng minh
  provenance/recipe đúng. Runtime không tự import DRAFT.
- Insert-only seed bỏ qua ID đã có. Sửa dữ liệu/tags 9 record cũ cần quy trình update
  được duyệt riêng, không lén thay bằng ID mới hoặc dùng lại INSERT để tưởng đã cập nhật.
- Snapshot/history/intake đọc dữ liệu đã lưu; nếu catalog được hiệu chỉnh sau này,
  không backfill calories/macro cũ hoặc đổi reference cũ của người dùng.

## Validation và replay trong bộ nhớ

Lệnh chỉ đọc JSON, không import Flask hoặc kết nối SQL/HTTP:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B setup\validate_vietnamese_catalog_draft.py
.\.venv\Scripts\python.exe -X utf8 -B setup\seed_nutrition_catalog.py
```

Validation PASS nghĩa là cấu trúc/status/blocker nhất quán, **không** là đủ nutrient
để import. Kiểm tra ID/identity, bảo toàn 102 ID, role, MAIN/meal, nutrient đơn vị,
gram, ingredient tags, estimated và READY không thiếu evidence. Tất cả DRAFT vẫn
inactive/not_importable. Source URLs/recipe identity/giả định còn cần human review.

10 tests offline mới và 34 tests catalog/SQLite/mock hiện có: 44/44 PASS.
Socket ngoài bị chặn; fixture xác nhận SQLite in-memory, SMTP mock, Gemini mock.
Không chạy full regression vì không đổi runtime source.

Replay patch repository trong bộ nhớ bằng snapshot 81 record KEEP_VIETNAM_FOCUS
đọc từ MySQL. Không ghi database, không gọi Gemini. Các Dish ID/gram/nutrient đều
lấy từ dữ liệu cũ thực tế, không từ 40 món PENDING. Chi tiết recipe/quality/timing:
[baseline_replay.json](../setup/drafts/vietnamese_catalog_v2/baseline_replay.json).

| Bữa | Target | Kcal ba lựa chọn | P/C/F ba lựa chọn (g) | Pool | Diversity | Pool/fallback ms |
|---|---:|---|---|---:|---:|---|
| lunch | 891 | 845.2 / 832.9 / 831.6 | 58.0/91.9/28.1; 42.7/108.3/28.1; 57.3/87.3/30.9 | 32 | 0.993 | 86.86/196.16 |
| dinner | 600 | 594.4 / 577.2 / 596.7 | 40.6/68.1/18.7; 36.1/64.4/19.1; 31.4/76.1/20.4 | 32 | 0.992 | 81.59/186.8 |
| breakfast | 600 | 599.2 / 577.4 / 593.5 | 37.0/68.4/21.1; 39.1/61.2/20.9; 40.2/64.8/20.7 | 17 | 0.963 | 32.65/153.85 |

Ba lựa chọn mỗi bữa khác Dish IDs, đúng role/avoid/min-max và biên an toàn kcal.
Nhưng lunch vẫn có bánh mì + đậu đen + bơ; breakfast ba bộ đều có bơ, hai bộ còn
sữa đậu nành/sữa chua. Một số breakfast >800 g vì phở/cháo có nước. Diversity cao
không chứng minh bữa cơm Việt tự nhiên. Bộ lunch đậu đen có protein 42.7 g so target
55.7 g, vẫn thiếu dù kcal/fat gần. Đây là hạn chế được quan sát, không sửa thuật toán.
**Nutritional replay cho 31 món mới: NOT RUN**, vì không có nutrient/yield đã xác minh.
Không dựng fixture có dinh dưỡng tưởng tượng để báo món mới chạy được.

## Lộ trình an toàn 102 → 150 → 250

1. Review DRAFT 40: chốt recipe đại diện, tìm nutrient source đúng trạng thái, đo
   gram nguyên liệu/dầu/gia vị/thành phẩm, thống nhất portions, tags và quyền dùng.
   Dùng ưu tiên canh, rau Việt và nguồn fat phù hợp; không đặt READY theo quota.
2. Mốc 150 tổng record cần 48 ID mới đủ evidence, không phải 40 DRAFT này đã đủ
   (batch có 9 review-existing +31 new). Nghiên cứu tiếp tối thiểu 17 new sau batch
   đầu nếu cả 31 đều được review chấp thuận. Giữ data cũ; sửa catalog cũ là bước riêng.
3. Replay READY-only trong bộ nhớ, xét dinh dưỡng và tính hợp món; thử avoid/focus,
   nguồn fat, ba primaries/carb khác nhau và giới hạn pool. Không dùng PENDING.
4. Nếu cần MAIN trưa/tối/cuisine/peanut/sesame preferences, trình đề xuất riêng với
   impacts/test cases trước khi đổi rule hoặc frontend; không xem seed là sửa được kiến trúc.
5. Trước import: exact DB, backup mới ngoài Git, checksum/restore rehearsal riêng,
   inventory/counts/hash/FK/schema, ID/collision checks, insert-only dry-run và kế
   hoạch partial/error recovery. Trình review và chờ phê duyệt persistent operation.
6. Khi được duyệt: import batch nhỏ có transaction dữ liệu; không chạy DDL nếu không
   cần. Chạy lại import để verify idempotency; không ghi đè manual edits; so invariant
   snapshots/history/intake, restart/backend/browser và source semantics.
7. Mốc 250: thêm tổng 148 new đã review theo role roadmap, đánh giá phần review/
   reference/duplicate cũ. 250 database rows không là 250 distinct verified Vietnamese
   dishes nếu chưa xử lý identity. Không tự deactivate/delete bất kỳ ID cũ nào.

Backup, restore rehearsal, seed apply, migration, Gemini thật, Chrome với món mới:
**NOT RUN**, không thuộc giai đoạn DRAFT. Không tạo backup mới khi chỉ đọc dữ liệu.
Đối chiếu cuối phiên: số dòng của cả 18 bảng không đổi; nội dung tám bảng
catalog/legacy/meal/snapshot/intake khớp fingerprint đầu phiên. Không lưu nội dung
riêng tư của người dùng vào artifact; audit chỉ có số dòng và dữ liệu catalog công khai.
Credential core hardcode từ trước vẫn cần Quý xử lý/rotation riêng; không in giá trị
hoặc sửa Core ở nhiệm vụ này.

## Phase 2 — batch 12, ngày 2026-10-12

Baseline `721bc2c` (Premium Quick Food), nhánh `feature/nutrition-mysql-food-catalog`.
Tiếp tục đúng 40 DRAFT; không tạo 12 ID mới thay thế. Giữ research_history Phase 1
cho từng record được cập nhật, baseline_snapshot Phở bò và 28 record ngoài batch.

**Kết quả dữ liệu món hoàn chỉnh: 0 READY / 12 PENDING / 0 REJECTED.**
Toàn bộ 40 DRAFT vẫn PENDING. Đã đọc recipe của cả 12 và thêm registry 14 bản ghi
nguyên liệu từ nguồn Việt Nam có food code/trang truy xuất. Không coi source
nguyên liệu là source của cả món hoặc lấy số theo suất chia cho gram tự đặt.
Không có nguồn trong batch xác minh đủ gram thành phẩm, toàn bộ gia vị và yield.

`—` dưới đây là NULL chưa biết, không phải 0. Khẩu phần thành phẩm cũng giữ NULL;
số người/mẻ hoặc gram sống công bố không phải reference_grams.

| Món / ID | Role | kcal/100g | P/C/F g/100g | Reference thành phẩm | Status | Thiếu hụt cần xử lý |
|---|---|---|---|---|---|---|
| Thịt kho tiêu — vn_thit_kho_tieu | PROTEIN | — | —/—/— | — | PENDING | Nạc dăm không khớp profile thịt generic; dầu/ml, nước mắm, retention và cân sốt/thành phẩm |
| Thịt kho trứng — vn_thit_kho_trung | PROTEIN | — | —/—/— | — | PENDING | Cut ba chỉ, trứng bóc vỏ, density nước dừa/gia vị, mỡ tiết ra và yield |
| Cá lóc kho tộ — vn_ca_loc_kho_to | PROTEIN | — | —/—/— | — | PENDING | Gross/net cá 500g, xương bỏ và lượng sốt/dầu ăn thực tế |
| Đậu phụ sốt cà chua — vn_dau_phu_sot_ca_chua | PROTEIN | — | —/—/— | — | PENDING | Dạng đậu, dầu chiên giữ lại, gia vị và yield; nguồn có mắm/dầu hào |
| Rau muống xào tỏi — vn_rau_muong_xao_toi | VEGGIE | — | —/—/— | — | PENDING | Dầu không định lượng, nhãn gia vị, retention và gram rau sau xào |
| Cải ngọt luộc — vn_cai_ngot_luoc | VEGGIE | — | —/—/— | — | PENDING | Đúng loài/raw-cooked source; mâu thuẫn đơn vị nêm, trọng lượng ráo nước |
| Cải thìa xào nấm — vn_cai_thia_xao_nam | VEGGIE | — | —/—/— | — | PENDING | Nấm khô/hydrated, dầu ăn/dầu mè, nhãn dầu hào và yield sau chần/xào |
| Canh rau ngót thịt băm — vn_canh_rau_ngot_thit_bam | SOUP | — | —/—/— | — | PENDING | Nước chưa định lượng, fat nguồn rau thiếu, tỷ lệ mỡ thịt và cân canh |
| Canh bí đao thịt băm — vn_canh_bi_dao_thit_bam | SOUP | — | —/—/— | — | PENDING | Bí gọt vỏ, thịt/nêm/dầu, fat bí thiếu; 500ml không phải yield |
| Canh cà chua trứng — vn_canh_ca_chua_trung | SOUP | — | —/—/— | — | PENDING | Cân trứng/cà chua, gia vị, nước thêm và thành phẩm |
| Phở bò — pho_beef | MAIN | — | —/—/— | — | PENDING | Nước dùng lọc/hớt mỡ, gram mỗi tô; giữ ID/baseline, không đổi MAIN lunch/dinner |
| Bún riêu cua — vn_bun_rieu_cua | MAIN | — | —/—/— | — | PENDING | Yield lọc cua, bún/topping mỗi tô, dầu điều và nước dùng cuối |

Nguồn chính, định lượng quan sát và mã nguyên liệu xem bảng Phase 2 trong
[VIETNAMESE_CATALOG_V2_SOURCES.md](VIETNAMESE_CATALOG_V2_SOURCES.md).

### Công thức và điều kiện tính

Với nutrient `n`: `N_batch = Σ(edible_input_g × N_source/100 × retention_n)`;
`N_finished_per_100g = N_batch × 100 / finished_edible_g`.
Finished weight phải có bằng chứng, giữ/bỏ nước/mỡ/xương/bã phải được phản ánh
trong inputs/retention. Cooked-profile chỉ dùng với gram cùng trạng thái và
không áp yield lần hai. Gram raw không tự bằng gram cooked; muỗng/quả/ml không
tự thành gram. Không đặt hệ số retention mặc định bằng 1 cho món nấu.

Validator trả BLOCKED/NULL nếu thiếu dữ liệu; chỉ đối chiếu 4/4/9 khi có toàn bộ
P/C/F và kcal. Fat NULL ở bảng nguồn không điền 0; celluloza giữ riêng, không đổi
tên thành total dietary fiber. Các số nguyên liệu trong registry dùng để matching,
không tự gán vào `macros_per_100g` của dish.

### Tương thích Meal Planner / Quick Food

- PROTEIN/VEGGIE/SOUP phù hợp role cho lunch/dinner về cấu trúc; cần READY và
  replay thật về nguồn fat/khẩu phần trước khi đưa vào candidate_pool.
- Phở bò/Bún riêu cua là món hoàn chỉnh, không đổi thành CARB hoặc PROTEIN để
  ép qua validator. Giữ MAIN/breakfast; intended lunch/dinner là đề xuất tương lai.
- Quick Food có thể tính món hoàn chỉnh theo gram sau khi profile có bằng chứng;
  hiện không thấy các DRAFT active=false và không đọc file DRAFT/seed ở runtime.
- Aliases chỉ trong provenance DRAFT. Đậu hũ/đậu phụ và băm/bằm là tên tương đương;
  Bún riêu là tên rộng có nhiều biến thể, không tự match về Bún riêu cua. Bộ search
  hiện chỉ tìm `name`, chưa đọc aliases. Đề xuất sau review: lưu alias đã duyệt trong
  ProvenanceJson và sửa matching có tests; không cần tự migration bảng ở Phase 2.
- Tags bổ sung theo nước mắm/dầu hào/huyết/mè; không tuyên bố hỗ trợ tránh mè ở API
  preferences hiện tại. Chưa có bảo đảm an toàn dị ứng.

### Kiểm chứng và import đề xuất

Chạy validator offline, tests DRAFT + catalog/Quick Food trong SQLite/mock.
Không gọi Gemini; chưa có READY để replay nutritional-quality của món mới.
Các phép tính fixture nhân tạo chỉ kiểm tra số học, không chứng minh 12 món đạt target.
Không có batch import được đề xuất lúc này; không sửa seed hoặc gọi --apply.

Khi đủ bằng chứng: kiểm tra trùng tên/ID/cut/alias, export READY-only sau review,
chạy dry-run và replay trong bộ nhớ; đề xuất insert-only cho 11 new của batch.
`pho_beef` là review-existing: seed hiện có sẽ bỏ qua ID, cần kế hoạch hiệu chỉnh
được duyệt riêng, giữ snapshot lịch sử. Không tự ghi đè bằng seed.

Đợt tiếp: ưu tiên hoàn tất cân mẻ đậu phụ sốt, rau muống xào, cải ngọt luộc và
canh cà chua trứng (ít nguyên liệu hơn); rồi nhóm thịt/cá/nước dùng nhiều biến số.
Sau đó tiếp tục các DRAFT sẵn có: trứng chiên hành, gà luộc, gà kho gừng, cá nục
kho cà chua, tôm rim, đậu phụ kho nấm, canh bầu tôm và canh mồng tơi cua.
Mốc 150 vẫn cần 48 ID mới đạt chất lượng từ 102; toàn bộ 31 new trong 40 DRAFT
nếu được chấp thuận mới đóng góp 31, cần ít nhất 17 new thêm. Không đếm PENDING
hoặc alias như món đã import để đạt mốc 250.

### Kết quả kiểm tra Phase 2

- Validator offline: PASS, 250 targets / 102 retained / 148 new, 40 PENDING,
  0 READY, authorized_for_import=false.
- Unittest liên quan: **84/84 PASS** = 24 DRAFT (14 tests mới) + 34 Catalog +
  26 Quick Food. SQLite in-memory; pymysql.connect và socket ra ngoài bị chặn
  trong bộ nhớ. Không chạy lại full regression 270 trong nhiệm vụ này.
- Seed CLI không có --apply: validate-only PASS, 102 dishes / 63 legacy menus,
  database_writes=0. Seed/runtime code và nội dung file seed không thay đổi.
- Python AST / JSON / whitespace: PASS. Không tạo pycache hoặc output báo cáo tạm.
- MySQL read-only: 18 bảng, NutritionFoodCatalog 102 active, NutritionLegacyMenus
  63; catalog ENGINE=InnoDB. SELECT VERSION() trả 26.7.0, không suy vendor là MySQL 8.
  Hash nội dung và số dòng cả 18 bảng, cùng metadata cột, khớp trước/sau.
- Hash source backend/seed, targets.json, existing_catalog_audit.json và
  baseline_replay.json không đổi. 28 DRAFT ngoài batch giữ nguyên; có thể tái dựng
  đúng dữ liệu trước Phase 2 của 12 món từ research_history, không mất nghiên cứu.
- Git giữ HEAD 721bc2c; 9 file untracked (8 DRAFT trước + ingredient_sources.json).
  Không staged/commit/push/merge. Không sửa schema hoặc import món mới.

File cập nhật: draft_dishes.json, hai tài liệu DRAFT/SOURCES, validator và tests
DRAFT. File mới duy nhất: ingredient_sources.json. Không có READY nên chưa có
đề xuất import thực thi; cần review số liệu và đo/chốt recipe trước Phase tiếp.
