"""Extract traceable SR Legacy nutrient records; offline, no MySQL, no zero filling.

Example: python database/tools/food_quality/extract_usda.py --archive <official.zip> --output <private-cache/index.json>
The official release checksum is pinned; source matching and production approval are separate steps.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import zipfile

RELEASE_SHA256 = "b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0"
SOURCE_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip"
NUTRIENTS = {"1008": ("calories_per_100g", "KCAL"), "1003": ("protein_per_100g", "G"),
             "1005": ("carbs_per_100g", "G"), "1004": ("fat_per_100g", "G"),
             "1079": ("fiber_per_100g", "G")}
FAO_CARBOHYDRATE_METHOD = "https://www.fao.org/4/Y5022E/y5022e03.htm"


def available_carbohydrate(total, fiber):
    """Explicit FAO by-difference conversion, not an analytical determination.

    Both must be supplied from compatible records/units. Missing remains missing;
    inconsistent inputs fail rather than being clamped or silently zero-filled.
    """
    if total is None or fiber is None:
        return None
    total_value, fiber_value = Decimal(total), Decimal(fiber)
    if any(not value.is_finite() or value < 0 for value in (total_value, fiber_value)):
        raise ValueError("Invalid carbohydrate/fiber source values")
    result = total_value - fiber_value
    if result < 0:
        raise ValueError("Source total carbohydrate is below fiber; review required")
    return format(result, "f")


def extract(archive):
    payload = Path(archive).read_bytes()
    if hashlib.sha256(payload).hexdigest() != RELEASE_SHA256:
        raise ValueError("Unreviewed dataset checksum; source review required")
    with zipfile.ZipFile(io.BytesIO(payload)) as zipped:
        if zipped.testzip() is not None:
            raise ValueError("Dataset CRC failure")
        prefix = "FoodData_Central_sr_legacy_food_csv_2018-04/"

        def read(name):
            return csv.DictReader(io.TextIOWrapper(zipped.open(prefix + name), encoding="utf-8-sig", newline=""))

        definitions = {row["id"]: row for row in read("nutrient.csv")}
        derivations = {row["id"]: row for row in read("food_nutrient_derivation.csv")}
        sources = {row["id"]: row for row in read("food_nutrient_source.csv")}
        foods = {}
        for row in read("food.csv"):
            if row["data_type"] != "sr_legacy_food":
                raise ValueError("Unexpected data type")
            foods[row["fdc_id"]] = dict(fdc_id=row["fdc_id"], description=row["description"],
                food_category_id=row["food_category_id"], publication_date=row["publication_date"],
                nutrients={})
        for row in read("sr_legacy_food.csv"):
            foods[row["fdc_id"]]["ndb_number"] = row["NDB_number"]
        row_count = 0
        for row in read("food_nutrient.csv"):
            row_count += 1
            if row["nutrient_id"] not in NUTRIENTS:
                continue
            key, expected_unit = NUTRIENTS[row["nutrient_id"]]
            definition = definitions[row["nutrient_id"]]
            if definition["unit_name"] != expected_unit:
                raise ValueError("Unexpected unit, especially kcal vs kJ")
            food = foods[row["fdc_id"]]
            if key in food["nutrients"]:
                raise ValueError("Duplicate nutrient record requires review")
            amount = row["amount"] or None
            if amount is not None:
                try:
                    number = Decimal(amount)
                except InvalidOperation as exc:
                    raise ValueError("Non-decimal source amount") from exc
                if not number.is_finite() or number < 0:
                    raise ValueError("Invalid source amount")
            derivation = derivations.get(row["derivation_id"])
            source = sources.get(derivation["source_id"]) if derivation else None
            food["nutrients"][key] = dict(value=amount, unit=expected_unit, basis="100 g edible portion",
                source_nutrient_row_id=row["id"], nutrient_id=row["nutrient_id"],
                source_nutrient_name=definition["name"], data_points=row["data_points"],
                derivation=derivation, source=source, footnote=row["footnote"] or None,
                min=row["min"] or None, max=row["max"] or None, median=row["median"] or None)
        # Values are source publications, not proof of matching a Vietnamese food or laboratory analysis.
        for food in foods.values():
            food["missing_nutrients"] = [key for key, _ in NUTRIENTS.values()
                if key not in food["nutrients"] or food["nutrients"][key]["value"] is None]
            food["source_url"] = "https://fdc.nal.usda.gov/food-details/" + food["fdc_id"] + "/nutrients"
        expected = {r["Table"]: int(r["Number of Records"]) for r in read("all_downloaded_table_record_counts.csv")}
        if len(foods) != expected["food"] or row_count != expected["food_nutrient"]:
            raise ValueError("Archive record-count verification failed")
    return dict(source="USDA FoodData Central SR Legacy", release="04/2018", archive_url=SOURCE_URL,
        archive_sha256=RELEASE_SHA256, source_food_count=len(foods), source_nutrient_row_count=row_count,
        carbohydrate_definition="USDA 1005 total carbohydrate by difference, includes fiber; not silently normalized",
        foods=foods)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = extract(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EXTRACTED: {data['source_food_count']} foods, {data['source_nutrient_row_count']} nutrient rows; source matching NOT approved")


if __name__ == "__main__":
    main()
