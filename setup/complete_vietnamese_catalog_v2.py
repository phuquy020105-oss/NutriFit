"""Offline, reproducible reference estimates; never connects to MySQL or HTTP.

Requires the official USDA SR Legacy 2018 CSV archive downloaded separately.
Existing READY records and runtime seed remain unchanged.
"""
import argparse
import copy
import csv
from datetime import date
import io
import json
from pathlib import Path
import zipfile

from seed_nutrition_catalog import seed_checksum
from validate_vietnamese_catalog_draft import calculate_recipe, validate

FOLDER = Path(__file__).resolve().parent / "drafts/vietnamese_catalog_v2"
USDA_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip"
# Alias, actual source ID, edible state and conservative ingredient tags.
INPUTS = {
    "egg": ("smiling2013_9001", "raw", "egg"),
    "oil": ("usda_171411", "ready", "oil soy"),
    "salt": ("usda_173468", "ready", "salt"),
    "water": ("usda_173647", "ready", "water"),
    "fishsauce": ("usda_174531", "ready", "fish seafood"),
    "soy": ("usda_174277", "ready", "soy wheat"),
    "sugar": ("usda_169655", "ready", "sugar"),
    "pepper": ("usda_170931", "ready", "seasoning"),
    "garlic": ("usda_169230", "raw", "vegetables"),
    "ginger": ("usda_169231", "raw", "vegetables"),
    "shallot": ("usda_170499", "raw", "vegetables"),
    "scallion": ("usda_170005", "raw", "vegetables"),
    "onion": ("usda_170000", "raw", "vegetables"),
    "coriander": ("usda_169997", "raw", "vegetables"),
    "tomato": ("smiling2013_4005", "raw", "vegetables"),
    "tofu": ("smiling2013_3025", "raw", "soy"),
    "pork": ("smiling2013_7017", "raw", "pork"),
    "porkfat": ("smiling2013_7018", "raw", "pork"),
    "chickenraw": ("usda_172385", "raw", "chicken"),
    "chickenstew": ("usda_173626", "cooked", "chicken"),
    "mackerel": ("usda_173672", "raw", "fish seafood"),
    "shrimp": ("usda_175179", "raw", "shrimp seafood"),
    "snakefish": ("smiling2013_8022", "raw", "fish seafood"),
    "crab": ("smiling2013_8034", "raw", "crab seafood"),
    "ngot": ("smiling2013_4086", "raw", "vegetables"),
    "muong": ("smiling2013_4083", "raw", "vegetables"),
    "shiitake": ("usda_169242", "raw", "vegetables mushroom"),
    "luffa": ("usda_168414", "raw", "vegetables"),
    "gourd": ("usda_169232", "raw", "vegetables"),
    "malabar": ("usda_169400", "cooked", "vegetables"),
    "bitter": ("usda_168393", "raw", "vegetables"),
    "eggplant": ("usda_169228", "raw", "vegetables"),
    "peanut": ("usda_173806", "ready", "peanut"),
    "papaya": ("usda_169926", "raw", "vegetables"),
    "carrot": ("usda_170393", "raw", "vegetables"),
    "lime": ("usda_168156", "raw", "fruit"),
    "corn": ("usda_168399", "cooked", "corn"),
    "pineapple": ("usda_169124", "raw", "fruit"),
    "okra": ("usda_169260", "raw", "vegetables"),
    "sprouts": ("usda_169136", "raw", "vegetables legumes"),
    "tamarind": ("usda_167763", "raw", "fruit"),
    "beef": ("usda_171804", "raw", "beef"),
    "beefstock": ("usda_172883", "ready", "beef"),
    "chickenstock": ("usda_172884", "ready", "chicken"),
    "lemongrass": ("usda_168573", "raw", "vegetables"),
    "ricenoodles": ("usda_168914", "cooked", "rice"),
    "rice": ("usda_169757", "cooked", "rice"),
    "lettuce": ("usda_169249", "raw", "vegetables"),
    "cucumber": ("usda_168409", "raw", "vegetables"),
    "turmeric": ("usda_172231", "ready", "seasoning"),
    "stickyrice": ("usda_169711", "cooked", "rice"),
    "phonoodles": ("usda_168914", "cooked", "rice"),
    "glassdry": ("usda_174258", "ready", "starch"),
    "ricedry": ("usda_169742", "ready", "rice"),
    "taro": ("usda_169308", "raw", "taro"),
    "soymilk": ("usda_175215", "ready", "soy"),
}
# ID suffix, assumed cooked batch g, servings, min/max g, quantities g,
# physical discard g, method/proxy disclosures. Finished grams are NOT raw totals.
RECIPES = [
    ("trung_chien_hanh", 210, 2, 60, 170, {"egg": 200, "scallion": 15, "oil": (10, .8), "salt": 2}, 2, "Trứng chiên hành; giữ8/10g dầu, bỏ2g dầu."),
    ("ga_luoc", 400, 3, 80, 220, {"chickenstew": 400, "ginger": 10, "salt": 2, "water": 30}, 0, "Gà luộc có da bỏ xương, dùng proxy đùi gà hầm USDA. Không áp dụng yield thịt sống lần hai; nước dùng riêng không tính vào thịt."),
    ("ga_kho_gung", 640, 4, 90, 230, {"chickenraw": 500, "ginger": 30, "shallot": 30, "fishsauce": 20, "sugar": 12, "oil": (10, .9), "water": 180, "salt": 2, "pepper": 1}, 1, "Đùi gà có da bỏ xương kho gừng, ăn cả sốt; giữ9/10g dầu."),
    ("ca_nuc_kho_ca_chua", 680, 4, 100, 240, {"mackerel": 400, "tomato": 200, "shallot": 20, "fishsauce": 15, "sugar": 8, "oil": 8, "water": 120}, 0, "Cá nục bỏ xương kho cà; proxy USDA mixed Pacific/jack mackerel, khác loài có thể thay fat đáng kể."),
    ("tom_rim_man_ngot", 470, 4, 65, 180, {"shrimp": 400, "fishsauce": 15, "sugar": 20, "oil": 12, "garlic": 10, "water": 100}, 0, "Tôm bỏ vỏ rim mặn ngọt, ăn dầu/sốt."),
    ("dau_phu_nhoi_thit", 920, 4, 130, 300, {"tofu": 400, "pork": 200, "tomato": 250, "garlic": 10, "fishsauce": 15, "oil": (20, .9), "water": 120}, 2, "Đậu tươi nhồi thịt sốt cà, giữ18/20g dầu; không cộng dầu hai lần bằng profile đậu chiên."),
    ("dau_phu_kho_nam", 680, 4, 100, 260, {"tofu": 400, "shiitake": 150, "soy": 15, "oil": 15, "ginger": 10, "water": 120, "sugar": 5}, 0, "Đậu tươi kho nấm hương và nước tương chứa soy/wheat."),
    ("rau_muong_luoc", 440, 3, 80, 240, {"muong": (500, {"protein": .95, "carbs": .9}), "water": 150, "salt": 3}, 180, "Rau luộc đã ráo:180g nước bỏ; hao P5%/C10% chỉ là giả định kỹ thuật."),
    ("muop_xao_dau_phong", 540, 3, 90, 260, {"luffa": 500, "peanut": 40, "oil": 12, "garlic": 12, "salt": 2, "water": 60}, 0, "Mướp xào đậu phộng rang, ăn toàn bộ dầu/sốt."),
    ("ca_tim_nuong_mo_hanh", 380, 3, 70, 220, {"eggplant": 400, "scallion": 30, "oil": 20, "fishsauce": 10, "sugar": 4, "water": 20}, 0, "Cà tím nướng, mỡ hành bằng dầu thực vật, có nước mắm."),
    ("kho_qua_xao_trung", 510, 3, 100, 270, {"bitter": 400, "egg": 150, "oil": 15, "garlic": 10, "salt": 2}, 0, "Khổ qua bỏ hạt xào trứng, giữ toàn bộ dầu."),
    ("nom_du_du_xanh", 420, 3, 90, 250, {"papaya": 250, "carrot": 100, "peanut": 30, "coriander": 10, "sugar": 15, "fishsauce": 15, "lime": 20}, 20, "Nộm đu đủ xanh: proxy USDA papaya không khớp độ chín, carbs bất định. Nước rau bỏ20g; giả định hao P/C2%."),
    ("canh_tom_rau_ngot_bap", 1150, 4, 180, 420, {"ngot": 100, "corn": 120, "shrimp": 100, "water": 900, "fishsauce": 10, "oil": 5, "salt": 2}, 0, "Rau ngót/tôm bóc vỏ/bắp đã luộc; ăn cả nước canh."),
    ("canh_mong_toi_cua", 1250, 4, 180, 450, {"malabar": 250, "crab": 150, "water": 900, "fishsauce": 10, "salt": 2}, 0, "Mồng tơi dùng profile đã nấu; cua150g là thịt ăn được, không gồm mai/vỏ."),
    ("canh_bau_nau_tom", 1320, 4, 180, 450, {"gourd": 350, "shrimp": 150, "water": 900, "fishsauce": 12, "salt": 2}, 0, "Bầu bỏ vỏ/hạt già, tôm bóc vỏ, tính cả nước canh."),
    ("canh_kho_qua_nhoi_thit_va_ca", 1800, 6, 180, 430, {"bitter": 400, "pork": 200, "snakefish": 100, "onion": 30, "shiitake": 30, "water": 1200, "fishsauce": 15, "salt": 3}, 0, "Khổ qua bỏ hạt nhồi heo nạc/cá lóc bỏ xương/nấm, ăn cả canh."),
    ("canh_chua_ca_loc", 1750, 5, 200, 480, {"snakefish": 300, "tomato": 150, "pineapple": 100, "okra": 100, "sprouts": 100, "tamarind": 20, "water": 1000, "fishsauce": 20, "sugar": 15, "oil": 5}, 0, "Canh chua cá bỏ xương với cà/dứa/đậu bắp/giá/thịt me bỏ hạt."),
    ("canh_muop_nam", 1400, 4, 180, 450, {"luffa": 350, "shiitake": 150, "water": 950, "oil": 5, "salt": 3}, 0, "Canh mướp nấm với nước, không có nước dùng thịt giấu trong recipe."),
    ("bun_bo_hue", 2100, 4, 350, 650, {"ricenoodles": 800, "beef": 250, "porkfat": 150, "beefstock": 1000, "lemongrass": 40, "fishsauce": 25, "oil": 20, "sugar": 8, "scallion": 20, "coriander": 20, "onion": 80}, 0, "Biến thể bún bò sả/bò/heo, không huyết/chả/mắm ruốc; broth USDA là proxy, sả băm ăn được."),
    ("bun_thit_nuong", 1380, 4, 240, 500, {"ricenoodles": 600, "porkfat": 400, "peanut": 40, "lettuce": 120, "cucumber": 150, "carrot": 80, "sugar": 30, "fishsauce": 30, "lime": 30, "oil": 15, "garlic": 15}, 15, "Bún heo nướng/rau/lạc/nước mắm; thịt hao P5%/fat10%, mỡ/cặn15g bỏ là giả định."),
    ("mi_quang_ga", 1650, 4, 280, 600, {"ricenoodles": 600, "chickenraw": 400, "chickenstock": 500, "peanut": 40, "lettuce": 150, "turmeric": 5, "fishsauce": 20, "oil": 20, "scallion": 20}, 0, "Mì Quảng gà dùng proxy sợi gạo chín, gà bỏ xương, ít nước dùng; không trứng/bánh đa trong biến thể này."),
    ("com_nep", 522, 3, 90, 280, {"stickyrice": 500, "salt": 2, "water": 20}, 0, "Cơm nếp nấu mềm, profile đã nấu thêm20g nước giữ; không dùng gram khô làm gram chín."),
    ("banh_pho_chin", 260, 2, 70, 220, {"phonoodles": 200, "water": 60}, 0, "Bánh phở trụng: proxy USDA rice noodles cooked giữ thêm60g nước; chỉ sợi, không cả tô phở."),
    ("mien_dong_chin", 320, 2, 80, 260, {"glassdry": 100, "water": 250}, 0, "Miến dong: proxy miến tinh bột đậu USDA cho phần khô, khác loại tinh bột. Giữ220g nước; không chứng nhận gluten/dị ứng."),
    ("hu_tieu_chin", 532, 4, 80, 240, {"ricenoodles": 500, "salt": 2, "water": 30}, 0, "Hủ tiếu chỉ sợi gạo, proxy rice noodles cooked; không tính nước dùng/thịt."),
    ("banh_canh_gao_chin", 500, 3, 90, 280, {"ricedry": 150, "water": 400, "salt": 2}, 0, "Bánh canh biến thể100% gạo: proxy sợi gạo khô và nước giữ348g, không gồm nước canh."),
    ("khoai_mon_hap", 560, 4, 80, 230, {"taro": 500, "water": 100, "salt": 2}, 0, "Khoai môn gọt vỏ hấp, giả định giữ58g nước và2g muối; output560g chưa đo."),
    ("sua_dau_nanh_khong_duong", 530, 2, 150, 400, {"soymilk": 500, "water": 30}, 0, "Sữa không đường proxy USDA unsweetened; khác nồng độ/brand, không suy vi chất USDA thành sữa nhà làm."),
]


def complete(archive):
    load = lambda name: json.loads((FOLDER / name).read_text(encoding="utf-8"))
    targets, drafts, registry = (load(n) for n in ("targets.json", "draft_dishes.json", "ingredient_sources.json"))
    seed = json.loads((FOLDER.parents[1] / "seeds/nutrition_catalog.json").read_text(encoding="utf-8"))
    prior = load("review_batch.json")
    sources = {s["source_id"]: s for s in registry["sources"]}
    missing = {sid.split("_", 1)[1] for sid, _, _ in INPUTS.values()
               if sid.startswith("usda_") and sid not in sources}
    with zipfile.ZipFile(archive) as z:
        prefix = "FoodData_Central_sr_legacy_food_csv_2018-04/"
        rows = lambda name: csv.DictReader(io.TextIOWrapper(z.open(prefix + name), encoding="utf-8"))
        names = {r["fdc_id"]: r["description"] for r in rows("food.csv")}
        values = {code: {} for code in missing}
        nutrients = {"1008": "calories", "1003": "protein", "1004": "fat", "1005": "carbs", "1079": "fiber"}
        for row in rows("food_nutrient.csv"):
            if row["fdc_id"] in missing and row["nutrient_id"] in nutrients:
                values[row["fdc_id"]][nutrients[row["nutrient_id"]]] = float(row["amount"])
    for sid, state, _ in INPUTS.values():
        if sid in sources:
            continue
        code = sid.split("_", 1)[1]
        n = values[code]
        if any(k not in n for k in ("calories", "protein", "carbs", "fat")):
            raise ValueError("Missing USDA macro, cannot substitute zero: " + code)
        source = {"source_id": sid, "name": names[code], "url": USDA_URL, "food_code": code,
                  "checked_on": date.today().isoformat(), "locator": {"fdc_id": code, "food_csv": "food.csv", "nutrient_csv": "food_nutrient.csv"},
                  "verified": True, "basis": "100g_edible_input", "state": state, "state_verified": True,
                  "nutrients_per_100g": {k: n.get(k) for k in ("calories", "protein", "carbs", "fat", "fiber")},
                  "carbohydrate_method": "USDA carbohydrate by difference", "fiber_method": "total_dietary_fiber",
                  "reuse_status": "VERIFIED_FOR_REUSE", "license": "CC0-1.0", "license_url": "https://fdc.nal.usda.gov/api-guide/",
                  "confidence": "VERIFIED_SOURCE_TRANSCRIPTION_NOT_AUTOMATIC_RECIPE_MATCH",
                  "limitations": ["Read from official CSV; recipe equivalence, quantities and yields remain estimates."]}
        sources[sid] = source
        registry["sources"].append(source)
    by_id = {d["dish_id"]: d for d in drafts["drafts"]}
    selected = {d["dish_id"]: d for d in targets["targets"]}
    records = []
    for suffix, finished, servings, minimum, maximum, amounts, discard, note in RECIPES:
        identifier = "vn_" + suffix
        target, old = selected[identifier], by_id.get(identifier)
        record = copy.deepcopy(old or {k: target[k] for k in ("dish_id", "name", "type", "existing_dish_id", "recipe_identity")})
        if old and old["review_status"] != "READY_ESTIMATED":
            record.setdefault("research_history", []).append({"phase": "before_catalog_completion", "review_status": old["review_status"], "provenance": copy.deepcopy(old["provenance"])})
        items = []
        for alias, amount in amounts.items():
            grams, loss = amount if isinstance(amount, tuple) else (amount, {})
            sid, state, tags = INPUTS[alias]
            source = sources[sid]
            if source["state"] != state:
                raise ValueError("Ingredient state mismatch")
            factors = {k: 1 for k in ("calories", "protein", "carbs", "fat", "fiber")}
            factors.update(loss if isinstance(loss, dict) else {"fat": loss})
            if suffix == "nom_du_du_xanh" and alias in ("papaya", "carrot"):
                factors.update(protein=.98, carbs=.98)
            if suffix == "bun_thit_nuong" and alias == "porkfat":
                factors.update(protein=.95, fat=.9)
            n = source["nutrients_per_100g"]
            energy = 4 * n["protein"] + 4 * n["carbs"] + 9 * n["fat"]
            retained_energy = sum(n[k] * factors[k] * w for k, w in (("protein", 4), ("carbs", 4), ("fat", 9)))
            factors["calories"] = min(1.0, round(retained_energy / energy, 12)) if energy else 1
            items.append({"name": source["name"], "recipe_input": alias, "tags": tags.split(), "state": state,
                          "nutrient_source": sid, "source_url": source["url"], "edible_grams": grams,
                          "edible_basis": "SPECIFIED_EDIBLE_WEIGHT", "basis_note": "Chosen edible grams, excludes bones/shells/peels; not measured household conversion.",
                          "state_or_edible_basis_verified": False, "nutrient_match_verified": False,
                          "match_kind": "REFERENCE_ESTIMATE", "match_note": note,
                          "retention_factors": factors, "retention_evidence": {"kind": "ENGINEERING_ASSUMPTION", "not_measured": True,
                          "rationale": "Declared estimated retention applied once;1 counts edible input, energy follows retained4P+4C+9F ratio."}})
        total = sum(i["edible_grams"] for i in items)
        if total - discard < finished:
            raise ValueError("Cooked mass exceeds declared inputs")
        recipe = {"estimated": True, "ingredient_list_complete": True, "allergen_review_complete": True, "method": note,
                  "assumptions": [note, "Quantities, oil/water retention, evaporation and discard are engineering assumptions, not measured yields.",
                                  "Allergen tags describe this recipe only; no allergy or contamination safety guarantee."],
                  "finished_edible_grams": finished, "finished_weight_basis": "ASSUMED_COOKED_WEIGHT",
                  "finished_weight_verified": False, "finished_weight_measured": False,
                  "finished_weight_evidence": {"kind": "ENGINEERING_ESTIMATE", "not_measured": True, "rationale": "Input minus discard/evaporation balances chosen edible output; not observed yield."},
                  "mass_balance": {"input_edible_grams": total, "discarded_grams": discard, "evaporated_grams": total - discard - finished},
                  "yield_factor": round(finished / total, 6), "servings": servings, "ingredients": items,
                  "cooking_variation_sensitivity": {"finished_weight_relative_change": [-.1, .1], "label": "Hypothetical sensitivity, not measured error bound."}}
        calculation = calculate_recipe(recipe, sources, estimated=True)
        if calculation["status"] != "CALCULATED":
            raise ValueError(identifier + ": " + str(calculation["blockers"]))
        n = calculation["per_100g"]
        references = [{"source_id": sid, "url": sources[sid]["url"], "food_code": sources[sid]["food_code"], "verified": True,
                       "scope": "Ingredient transcription only; recipe quantities/yield/equivalence estimated."}
                      for sid in dict.fromkeys(i["nutrient_source"] for i in items)]
        provenance = {"source": "NutriFit practical recipe estimate; saved Vietnamese references and directly checked USDA ingredient CSV",
                      "research_checked_on": date.today().isoformat(), "method": "sum(edible_g*source_per100g*retention)/assumed_finished_g*100",
                      "confidence": "REFERENCE_RECIPE_ESTIMATE_LOW" if any(a in amounts for a in ("papaya", "mackerel", "glassdry")) else "REFERENCE_RECIPE_ESTIMATE_MEDIUM",
                      "limitations": ["One reference variant, not lab-measured/clinical nutrition.", "Oil, water, yield and losses assumed; brand/recipe variation remains.",
                                      "Proxies disclosed; cooked profiles never presented as raw mass.", "Unknown fiber staysNULL; carbohydrate definitions may differ.",
                                      "No sodium, allergy or cross-contamination guarantee; retain attribution for reuse."],
                      "portion_evidence": f"{finished}g assumed batch/{servings} servings; min/max are planner proposal bounds.",
                      "license_status": "REVIEW_ATTRIBUTION_BEFORE_DISTRIBUTION", "nutrition_references": references,
                      "recipe": recipe, "missing_evidence": [], "name_aliases": copy.deepcopy((old or {}).get("provenance", {}).get("name_aliases", []))}
        meals = ["breakfast"] if target["type"] == "MAIN" else ["breakfast", "lunch", "dinner"] if target["type"] in ("CARB", "DRINK") else ["lunch", "dinner"]
        record.update(meal_types=meals, intended_meal_types=target["intended_meal_types"], preparation_state="ready" if target["type"] == "DRINK" else "cooked",
                      reference_grams=round(finished / servings, 2), min_grams=minimum, max_grams=maximum, calories_per_100g=n["calories"],
                      macros_per_100g={k: n[k] for k in ("protein", "carbs", "fat", "fiber")}, ingredients=sorted({t for i in items for t in i["tags"]}),
                      prep_minutes=15 if target["type"] == "DRINK" else 30 if target["type"] in ("CARB", "VEGGIE") else 45,
                      estimated=True, active=False, import_ready=False, review_status="READY_ESTIMATED", intent="RESEARCH_NEW", provenance=provenance)
        if old:
            drafts["drafts"][drafts["drafts"].index(old)] = record
        else:
            drafts["drafts"].append(record)
        target["research_status"] = "READY_ESTIMATED"
        records.append(record)
    # Do not silently invent a cooked pork-skin profile or replace it with gelatin.
    pending = by_id["vn_com_tam_suon_bi_cha"]
    pending["provenance"]["completion_blocker"] = "No matched nutrient reference for boiled pork skin in bi; keepPENDING rather than substitute fried rind/gelatin. Shortest fix: use a documented ready-made bi profile or supplied label."
    drafts["completion_batch_ids"] = [r["dish_id"] for r in records]
    drafts["draft_count"] = len(drafts["drafts"])
    result = validate(targets, drafts, seed, registry)
    if result["errors"]:
        raise ValueError(str(result["errors"]))
    keys = list(prior["dishes"][0])
    batch = {"format": "nutrifit-practical-vietnamese-completion-batch", "batch_ids": drafts["completion_batch_ids"],
             "seed_baseline_sha256": seed_checksum(), "seed_checksum_basis": "canonical_json_utf8_sorted_keys", "estimated": True,
             "dishes": [{k: True if k == "active" else copy.deepcopy(r[k]) for k in keys} for r in records], "legacy_menus": [], "review_existing": [],
             "rollback_plan": "Transaction rollback before commit; after commit stop on error, never auto-delete. Corrective removal requires separate approval and snapshot-reference checks."}
    for name, data in (("draft_dishes.json", drafts), ("targets.json", targets), ("ingredient_sources.json", registry), ("completion_batch.json", batch)):
        (FOLDER / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {"completed_new": len(records), "new_pending": [pending["dish_id"]], "validation": result["structural_validation"], "draft_statuses": result["statuses"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usda-archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(complete(args.usda_archive), ensure_ascii=False))
