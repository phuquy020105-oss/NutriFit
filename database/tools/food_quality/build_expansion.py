"""Build exploratory B/C catalogs only; no SQL or production approval is generated."""
import argparse
from collections import Counter
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from extract_usda import extract, RELEASE_SHA256
from build_provenance import normalized_usda, KEYS, ROOT, STAGING


def load(name):
    return json.loads((STAGING / name).read_text(encoding="utf-8"))


def write(name, content):
    (STAGING / name).write_text(json.dumps(content,ensure_ascii=False,indent=2) + "\n",encoding="utf-8",newline="\n")


def build(cache):
    original = json.loads((ROOT / "database/seed/vietnamese_catalog.json").read_text(encoding="utf-8"))
    provenance = load("food-provenance.json")
    if hashlib.sha256((ROOT / "database/seed/vietnamese_catalog.json").read_bytes()).hexdigest() != provenance["canonical_sha256"]:
        raise ValueError("Source evidence is stale")
    source = extract(Path(cache) / "usda-srlegacy-2018-official.zip")
    foods = []
    for decision in load("new-food-decisions.json")["foods"]:
        raw = source["foods"][decision["fdc_id"]]
        nutrients = {key:normalized_usda(key,raw["nutrients"]) for key in KEYS}
        if any(n["value"] is None for n in nutrients.values()):
            raise ValueError("A new design ingredient lacks a quantified source nutrient")
        foods.append(dict(ref=decision["food_ref"],name=decision["name_vi"],state=decision["state"],
            status="MATCHED_OR_CALCULATED_SOURCE_NOT_ANALYTICAL_VERIFICATION",
            aiven_food_id=None,basis="100g edible portion in stated state",nutrients={key:n["value"] for key,n in nutrients.items()},
            nutrient_provenance=nutrients,source_record=raw,source_archive_sha256=RELEASE_SHA256,
            source_release="USDA SR Legacy04/2018",retrieved_date="2026-10-19",matching_differences=decision["differences"],
            production_change_approved=False))
    b = copy.deepcopy(original)
    by_ref = {r["food_ref"]:r for r in provenance["foods"]}
    changed = []
    for food in b["foods"]:
        evidence = by_ref[food["ref"]]
        if evidence["source_complete"]:
            food["nutrients"] = {key:evidence["nutrients"][key]["value"] for key in KEYS}
            food["status"] = "SOURCE_COMPARISON_NOT_PRODUCTION_APPROVAL"
            food["provenance_file"] = "food-provenance.json"
            changed.append(food["ref"])
        else:
            food["status"] = "ESTIMATED_UNRESOLVED_BASELINE_RETAINED_FOR_EXPLORATORY_BENCHMARK_ONLY"
        food["production_change_approved"] = False
    images = json.loads((ROOT / "docs/nutrition/recipe-image-sources.json").read_text(encoding="utf-8"))
    images = {r["ref"]:r["image_url"] for r in images["images"]}
    for recipe in b["recipes"]:
        recipe["image_url"] = images[recipe["ref"]]
    b["quality_gate"] = dict(status="EXPLORATORY_PARTIAL_SOURCES_NOT_QUALIFIED_B",production_write_permitted=False,
        source_complete_foods=len(changed),unresolved_baseline_foods=82-len(changed),changed_food_refs=changed,
        baseline_sha256=provenance["canonical_sha256"],
        provenance_sha256=hashlib.sha256((STAGING / "food-provenance.json").read_bytes()).hexdigest(),
        cooking_portions_verified=False)
    c=copy.deepcopy(b)
    c["foods"].extend(foods)
    designs=load("new-recipe-designs.json")["recipes"]
    if Counter(r["meal_type"] for r in designs)!=dict(BREAKFAST=10,LUNCH=10,DINNER=10):
        raise ValueError("New designs must contain exactly10 recipes for each meal")
    names={r["name"].casefold() for r in b["recipes"]}
    refs={f["ref"] for f in c["foods"]}
    if len(refs)!=len(c["foods"]):
        raise ValueError("Food reference collision")
    signatures=set()
    for recipe in designs:
        if recipe["name"].casefold() in names or recipe["base_servings"]!="1.00":
            raise ValueError("Duplicate recipe or variable standard portion")
        names.add(recipe["name"].casefold())
        used=set()
        for ingredient in recipe["ingredients"]:
            ref=ingredient["food_ref"]
            grams=Decimal(ingredient["quantity_grams"])
            if ref not in refs or ref in used or not grams.is_finite() or grams<=0:
                raise ValueError("Invalid or duplicate ingredient reference/grams")
            used.add(ref)
            if ref.startswith("F") and not by_ref[ref]["source_complete"]:
                raise ValueError("A new recipe depends on an unresolved old food")
        signature=tuple(sorted((i["food_ref"],i["quantity_grams"]) for i in recipe["ingredients"]))
        if signature in signatures:
            raise ValueError("Duplicate ingredient/gram design")
        signatures.add(signature)
    c["recipes"].extend(copy.deepcopy(designs))
    c["quality_gate"] = dict(b["quality_gate"],status="EXPLORATORY60_NOT_PRODUCTION_APPROVAL",
        new_designs=30,new_source_foods=len(foods),new_ingredient_links=sum(len(r["ingredients"]) for r in designs),
        kitchen_validation="NOT_RUN",local_migration="NOT_RUN",new_images="HONEST_FALLBACK_FOR30_PENDING_IMAGES")
    if Counter(r["meal_type"] for r in c["recipes"])!=dict(BREAKFAST=20,LUNCH=20,DINNER=20):
        raise ValueError("Expanded meal counts mismatch")
    write("new-food-provenance.json",dict(status="STAGING_ONLY",foods=foods))
    write("catalog-B-exploratory.json",b)
    write("catalog-C-exploratory.json",c)
    print("STAGING only: B82foods/30recipes; C100foods/60recipes/607links; zero production approvals")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cache",type=Path,required=True)
    build(parser.parse_args().source_cache)
