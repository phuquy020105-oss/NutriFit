"""Render staging reports from source evidence and the real Java calculator audit, offline."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "database/staging/food-quality-v1"
DOCS = ROOT / "docs/nutrition"
KEYS = ("calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g", "fiber_per_100g")


def main():
    data = json.loads((STAGING / "food-provenance.json").read_text(encoding="utf-8"))
    audit = json.loads((STAGING / "recipe-audit.json").read_text(encoding="utf-8"))
    if audit["canonical_sha256"] != data["canonical_sha256"] or audit.get("provenance_sha256") != hashlib.sha256((STAGING / "food-provenance.json").read_bytes()).hexdigest():
        raise ValueError("Recipe audit and provenance use different catalogs")
    trial_path = STAGING / "local-trial-result.json"
    verified_path = STAGING / "local-trial-readonly.json"
    catalog_path = STAGING / "catalog-C-exploratory.json"
    trial_matches = False
    if trial_path.is_file() and verified_path.is_file() and catalog_path.is_file():
        trial = json.loads(trial_path.read_text(encoding="utf-8"))
        verified = json.loads(verified_path.read_text(encoding="utf-8"))
        trial_matches = (
            trial.get("status") == "PASS_LOCAL_MECHANICS_ONLY_NOT_DATA_APPROVAL"
            and verified.get("status") == "PASS_READ_ONLY_LOCAL_CATALOG_VERIFICATION"
            and trial.get("database") == verified.get("database")
            and verified.get("catalog_sha256") == hashlib.sha256(catalog_path.read_bytes()).hexdigest()
        )
    delta_path = STAGING / "local-delta-result.json"
    if delta_path.is_file() and catalog_path.is_file():
        delta = json.loads(delta_path.read_text(encoding="utf-8"))
        trial_matches = trial_matches or (delta.get("status") == "PASS_EXISTING_LOCAL_STAGING_DELTA"
            and delta.get("after_sha256") == hashlib.sha256(catalog_path.read_bytes()).hexdigest()
            and delta.get("history_unchanged") is True and delta.get("conflict_rejected") is True
            and delta.get("second_run_writes") == 0)
    trial_note = (
        "Local trial/delta cơ chế đã PASS và khớp SHA catalog C hiện tại: rollback, idempotency, conflict và history invariants. "
        if trial_matches else
        "Chưa có bằng chứng local trial và SELECT-only khớp SHA catalog C hiện tại; phải chạy lại trên database test riêng trước khi kết luận. "
    )
    s = data["summary"]
    lines = ["# Kiểm chứng dữ liệu Food — staging, đang thực hiện", "",
        "Báo cáo được tái tạo bằng `database/tools/food_quality/write_reports.py`. Không phải phê duyệt migration.", "",
        f"Đã đối chiếu {s['food_count']} Food, {s['nutrient_count']} nutrient. {s['complete_source_foods']} Food có đủ năm giá trị nguồn/quy đổi để so sánh; không đồng nghĩa đã đo/VERIFIED trong món Việt. {s['fully_verified_foods']} Food VERIFIED toàn bộ.", "",
        "| Trạng thái nutrient | Số lượng |", "|---|---:|"]
    for status in ("VERIFIED", "MATCHED", "CALCULATED", "ESTIMATED", "MISSING"):
        lines.append(f"| {status} | {s['statuses'].get(status,0)} |")
    lines += ["", "## Nguồn và chuẩn hóa", "",
        "- USDA SR Legacy04/2018: ZIP chính thức, SHA256 `b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0`; 7.793 Food, 644.125 nutrient rows. Ngày publication2019-04-01 khác ngày release. Có row ID, derivation và source gốc cho từng chỉ số; không gọi tất cả là kết quả phòng thí nghiệm.",
        "- [INMU Thai FCD](https://inmu.mahidol.ac.th/thaifcd/foodsearch/food_name):19 bản ghi được pin URL/SHA;11 mapping INMU được chọn, cùng record100g ăn được. Carbohydrate available dùng trực tiếp, không trừ fiber lần nữa. Giữ derivation/update/n/footnote; assumed zero vẫn ESTIMATED. Proxy Mu-yo/Ka-pi/giống rô phi khác ghi LOW confidence, không phải công thức Việt đã duyệt. USDA168374 bổ sung proxy F082 heo xay pan-broiled84%lean; chưa duyệt công thức nướng cụ thể.",
        "- [NIN tra cứu công khai](https://viendinhduong.vn/vi/cong-cu-va-tien-ich/gia-tri-dinh-duong-thuc-pham): 100g phần ăn được; 38 truy vấn snapshot2026-10-19 có checksum. Release và phương pháp chất xơ/carbohydrate của live lookup chưa công bố rõ. Null/absent giữ thiếu; không biến cellulose thành tổng dietary fiber. Các bản ghi thay thế giữ trong JSON, không trộn macro của một record với fiber record khác.",
        "- [MEXT English2015](https://www.mext.go.jp/en/policy/science_technology/policy/title01/detail01/sdetail01/sdetail01/1385122.htm): 2.191 Food; workbook cập nhật2017-12-27, không phải edition2023. SHA256 `5c968f1801f706b2970d51599ab2dce6f9e09ff3901fcf1990922960761885fb`. Bốn matching:02028 bột năng;06207 hẹ lá;11133 heo luộc bỏ mỡ ngoài;17016 giấm gạo. Khác biệt giống/cut/nồng độ vẫn được ghi.",
        "- [MEXT phương pháp, tr.24–25](https://www.mext.go.jp/component/english/__icsFiles/afieldfile/2017/10/02/1385123_Standard-Table_Chap.1_Prov_1.pdf): giữ `(0)` là nguồn ước tính; `Tr` không phải0, dấu gạch là chưa có số đo. Loại bỏ đuôi nhị phân Excel theo độ chính xác công bố (macro/fiber1 chữ số, kcal số nguyên), đồng thời lưu nguyên văn ô nguồn.",
        "- [FAO carbohydrate](https://www.fao.org/4/Y5022E/y5022e03.htm): giữ hợp đồng carbs khả dụng hiện có; dùng total carbohydrate trừ dietary fiber cùng record, ghi CALCULATED và giữ hai đầu vào. Kcal giữ số nguồn, không ép4/4/9. Đây là phép tính by-difference, có giới hạn phân tích và không phải đo trực tiếp.",
        "- SMILING Việt Nam2013 theo liên kết FAO: hai workbook trả HTTP403; không được dùng làm bằng chứng đã đọc.", "",
        "## Phạm vi và hạn chế", "",
        "Nguồn có giá trị không tự chứng minh đúng loài, độ ngậm nước, phần mỡ hoặc công thức thành phẩm. Mọi production_change_approved hiện là false. Baseline JSON/SQL và dữ liệu Aiven chưa bị thay đổi. MATCHED là đối chiếu thực phẩm tương đương có sai khác, CALCULATED là phương pháp công bố hoặc quy đổi rõ ràng, ESTIMATED có thể là ước tính do chính nguồn ghi; MISSING không được điền từ baseline.", "",
        "Các candidate bị loại vẫn được giữ trong source-candidates.json: tapioca pearl không phải bột năng; common chive không phải hẹ lá; cua biển không phải riêu cua đồng; ba chỉ sống không thay ba chỉ luộc; raw quail không thay trứng cút luộc. MEXT bổ sung được bột năng/hẹ nhưng không hợp thức hóa các candidate sai trước đó.", "",
        "## Những sai khác đáng chú ý", "",
        "- NIN sả có energy1kcal/100g nhưng macro không tương xứng: giữ nguyên bằng chứng và đánh dấu cần review, không tự sửa energy bằng4/4/9.",
        "- NIN ngò gai có English parsley không được dùng. INMU499 xác nhận Eryngium foetidum nhưng vẫn thiếu carbs/fiber; không thay bằng parsley.",
        "- Mộc nhĩ khô USDA có fiber70.1g/100g, baseline25g; khác lớn và phương pháp/định nghĩa cần review trước migration. Không lấy fiber7g của NIN ghép macro USDA để tạo số mong muốn.",
        "- Nước dùng bò/gà nguồn generic không xác minh được nồng độ, lượng mỡ và cách lọc của nước dùng Việt. Kết quả so sánh không phải chứng nhận công thức.", "",
        "## Nguyên liệu ảnh hưởng nhiều nhất", "", "| Food | Tên | Số recipe |", "|---|---|---:|"]
    for r in sorted(data["foods"], key=lambda r:(-r["recipe_count"],r["food_ref"]))[:12]:
        lines.append(f"| {r['food_ref']} | {r['name_vi']} | {r['recipe_count']} |")
    lines += ["", "## Đối chiếu đủ82 Food", "",
        "Đơn vị thứ tự K/P/C/F/Fiber: kcal/g/g/g/g trên100g ăn được; dấu — là thiếu. Giá trị cũ, delta, raw values, ô/row ID và nguồn đầy đủ nằm trong [food-provenance.json](../../database/staging/food-quality-v1/food-provenance.json).", "",
        "| Mã | Tên / trạng thái | K/P/C/F/Fiber nguồn đã chuẩn hóa | Trạng thái nutrient |", "|---|---|---|---|"]
    for r in data["foods"]:
        values='/'.join(r['nutrients'][k]['value'] or '—' for k in KEYS)
        counts=Counter(n['status'] for n in r['nutrients'].values())
        lines.append(f"| {r['food_ref']} | {r['name_vi']} ({r['state']}) | {values} | " + ', '.join(f"{k}:{v}" for k,v in sorted(counts.items())) + " |")
    lines += ["", "## Tái lập", "", "Xem [công cụ offline](../../database/tools/food_quality/README.md). Mỗi lần thay catalog phải làm mới provenance và audit cùng SHA; không dùng dữ liệu này trực tiếp làm seed.", ""]
    (DOCS / "food-data-verification.md").write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    lines=["# Audit30 công thức — staging, đang thực hiện", "",
        f"Đã duyệt cấu trúc30 recipes/383 ingredient links và tính baseline bằng NutritionCalculator thật. {audit['source_complete_recipe_count']}/30 công thức có đủ năm giá trị nguồn cho tất cả nguyên liệu để tính so sánh; các dòng còn lại có source_comparison=null, không phải0. Không công thức nào được phê duyệt migration ở mốc này.", "",
        "## Cách tính và chế biến", "",
        "- Giữ ID, meal_type, base_servings, toàn bộ383 định lượng. Không sửa mealentries hoặc tính lại snapshot đã ghi.",
        "- Số gram là khối lượng nguyên liệu đã kê, không tự nhận là khối lượng món hoàn thiện được cân. Gạo khô F007 khác cơm chín F001/F081; nấm khô cân trước ngâm, nước giữ lại kê riêng; thịt chín là thịt ăn được bỏ xương theo mô tả.",
        "- [FAO recipe calculations](https://www.fao.org/4/y4705e/y4705e23.htm): hệ số phải phù hợp nguyên liệu và phương pháp nấu. Không áp thêm retention/yield cho thực phẩm đã dùng dữ liệu chín. Chưa có phép cân bếp thực tế nên không bịa hệ số, nước bay hơi hoặc phần dầu hấp thu.",
        "- Dầu F061 là phần giả định giữ trong món; F077 dầu điều/F080 hành phi đã chứa dầu, không cộng dầu nền lần hai. Cần cân trước/sau hoặc công thức thành phẩm định danh để nâng confidence.",
        "- Các món dùng nguyên liệu sống rồi rán/xào/kho chỉ là phép tính thành phần từ công thức; chưa xác minh hao hụt macro vào nước/mỡ bỏ đi. Với canh/sốt dùng hết vẫn cần xác định khối lượng cuối; không gọi đây là số đo phòng thí nghiệm.",
        "- Tráng bánh/cuốn R007, xối mỡ R012, kho ba chỉ R013/R022, cá chiên R020 và nước dùng R001/R002/R004/R005/R008/R010 cần kiểm tra chế biến riêng; chưa đề xuất thay gram để đạt target.", "",
        "## Kết quả từng recipe", "",
        "K/P/C/F/Fiber lần lượt kcal/g/g/g/g cho1.00 suất, BigDecimal làm tròn cuối3 số HALF_UP. Cột sau là so sánh nguồn chưa phê duyệt, không phải catalog B đã xác minh.", "",
        "| Recipe | Tên | Gram nguyên liệu | Trước K/P/C/F/Fiber | So sánh nguồn K/P/C/F/Fiber | Food còn thiếu |", "|---|---|---:|---|---|---|"]
    def vector(n):
        return '/'.join(n[k] for k in ('calories','protein','carbs','fat','fiber')) if n else 'CHƯA ĐỦ NGUỒN'
    for r in audit['recipes']:
        lines.append(f"| {r['recipe_ref']} | {r['name']} | {r['listed_ingredient_grams']} | {vector(r['before'])} | {vector(r['source_comparison'])} | {','.join(r['missing_food_refs']) or '—'} |")
    lines += ["", "## Sai khác cần review", ""]
    complete=[r for r in audit['recipes'] if r['source_complete']]
    for r in sorted(complete,key=lambda r:Decimal(r['absolute_difference']['calories']),reverse=True)[:4]:
        lines.append(f"- {r['recipe_ref']} {r['name']}: kcal {r['before']['calories']} → {r['source_comparison']['calories']}; nguồn/cut/cooking khác nhau phải được review trước khi dùng số mới. Không dùng sai khác này làm lý do tự sửa khẩu phần.")
    lines += ["", "## Kiểm thử và bước còn lại", "",
        "FoodDataQualityAuditTest gọi NutritionCalculator hiện hành cho baseline và chỉ tính kết quả nguồn khi đủ toàn bộ nutrient; có regression cơm chín+mộc nhĩ khô, từ chối snapshot nguồn thiếu và kiểm tra SHA catalog. Audit JSON chi tiết giữ recipe instructions, từng food/state/gram, nguồn, missing refs và absolute differences.",
        trial_note + "Đây không phải dữ liệu B đã xác minh. B/C thăm dò được báo riêng trong data-quality-benchmark.md và catalog-expansion-staging.md; baseline ước tính còn lại được ghi rõ. Theo xác nhận của chủ dự án, giữ staging, không ghi Aiven. Chưa có manifest nutrient/gram được duyệt production.", ""]
    (DOCS / "recipe-quality-audit.md").write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    print(f"Reports generated:82 foods/410 nutrients;30 recipes/383 links;{audit['source_complete_recipe_count']} source-complete comparisons (not approval)")


if __name__ == '__main__':
    main()
