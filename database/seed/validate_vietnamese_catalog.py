"""Offline catalog checks only. Standard library; never connects to a database."""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
SEED = Path(__file__).resolve().parent
KEYS = ("calories_per_100g", "protein_per_100g", "carbs_per_100g",
        "fat_per_100g", "fiber_per_100g")
REVIEW_HASH = "727350446307d4f73739f9e5874e6dfbf93f9649a10e516df441cc0da7131028"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, precision, scale, positive=False):
    require(isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)?", value),
            f"Missing/invalid decimal: {value!r}")
    result = Decimal(value)
    maximum = Decimal(10) ** (precision - scale) - Decimal(10) ** (-scale)
    require(0 <= result <= maximum, f"DECIMAL({precision},{scale}) range: {value}")
    require(result == result.quantize(Decimal(10) ** (-scale)), f"Unexpected rounding: {value}")
    require(not positive or result > 0, f"Must be positive: {value}")
    return result


def quote(value):
    # SQL uses NO_BACKSLASH_ESCAPES, UTF-8 and standard doubled apostrophes.
    return "'" + value.replace("'", "''") + "'"


def marked(text, label, prefix="--"):
    return text.split(f"{prefix} BEGIN {label}\n", 1)[1].split(
        f"\n{prefix} END {label}", 1)[0]


def flags(values):
    result = []
    if values[0] < 400:
        result.append("Kcal <400")
    if values[0] > 800:
        result.append("Kcal >800")
    if values[3] > 30:
        result.append("Fat >30g")
    if values[4] < 3:
        result.append("Fiber <3g")
    return "; ".join(result) or "—"


def validate(show_totals=False):
    data = json.loads((SEED / "vietnamese_catalog.json").read_text(encoding="utf-8"))
    foods, recipes = data["foods"], data["recipes"]
    review = (ROOT / "docs/nutrition/vietnamese-food-catalog-review.md").read_text(encoding="utf-8")
    require(hashlib.sha256(review.encode("utf-8")).hexdigest() == REVIEW_HASH,
            "Approved design changed: review before updating the frozen hash")
    require([f["ref"] for f in foods] == [f"F{i:03}" for i in range(1, 83)], "82 canonical Food refs")
    require([r["ref"] for r in recipes] == [f"R{i:03}" for i in range(1, 31)], "30 canonical Recipe refs")
    require(Counter(r["meal_type"] for r in recipes) == {"BREAKFAST": 10, "LUNCH": 10, "DINNER": 10},
            "Expected 10 recipes per meal")
    require(len({f["name"] for f in foods}) == 82, "Duplicate Food names")
    require(len({r["name"] for r in recipes}) == 30, "Duplicate Recipe names")
    by_food = {f["ref"]: f for f in foods}
    food_section = review.split("## C.", 1)[1].split("## D.", 1)[0]
    original_foods = {}
    for line in food_section.splitlines():
        if re.match(r"\| F\d{3} \|", line):
            cells = [part.strip() for part in line.split("|")[1:-1]]
            original_foods[cells[0]] = (cells[1], cells[2])
    summary_section = review.split("## B.", 1)[1].split("## C.", 1)[0]
    original_recipes = {}
    for line in summary_section.splitlines():
        if re.match(r"\| R\d{3} \|", line):
            cells = [part.strip() for part in line.split("|")[1:-1]]
            original_recipes[cells[0]] = (cells[1], cells[2], cells[4])
    require(len(original_foods) == 82 and len(original_recipes) == 30, "Original design parse failed")

    plausibility_warnings = []
    for f in foods:
        ref = f["ref"]
        require((f["name"], f["state"]) == original_foods[ref], f"Food changed: {ref}")
        require(0 < len(f["name"]) <= 200 and f["basis"].strip(), f"Missing Food metadata: {ref}")
        require(f["status"] == "ESTIMATED", f"Unsupported VERIFIED claim: {ref}")
        require(set(f["nutrients"]) == set(KEYS), f"Missing/extra nutrient fields: {ref}")
        values = [number(f["nutrients"][k], 10, 3) for k in KEYS]
        kcal, protein, carbs, fat, fiber = values
        require(kcal <= 1000 and all(v <= 100 for v in values[1:]), f"Implausible per-100g values: {ref}")
        require(protein + carbs + fat + fiber <= 100, f"Mass >100g: {ref}")
        require((kcal == 0) == (ref in {"F065", "F071"}), f"Unexplained zero kcal: {ref}")
        require(any(values) or ref in {"F065", "F071"}, f"Missing data masked by zeros: {ref}")
        energy = 4 * protein + 4 * carbs + 9 * fat
        # A screening tolerance, not a claim of scientific verification.
        deviation = min(abs(kcal - energy), abs(kcal - energy - 2 * fiber))
        if deviation > max(Decimal("25"), kcal * Decimal("0.20")):
            plausibility_warnings.append(ref)
    require(not plausibility_warnings, f"Review energy plausibility: {plausibility_warnings}")
    require([f["ref"] for f in foods if f["partial_source"] == "VN2007"] ==
            ["F034", "F038", "F045", "F046"], "Partial source attribution changed")
    # Four partial-source values transcribed in the reviewed design; fiber remains estimated.
    for ref, expected in {"F034": ("20", "0.6", "4", "0.2"),
                          "F038": ("41", "1.8", "8.2", "0.1"),
                          "F045": ("29", "0.4", "5.1", "0.8"),
                          "F046": ("121", "6", "23", "0.5")}.items():
        require(tuple(by_food[ref]["nutrients"][k] for k in KEYS[:4]) == expected,
                f"Partial source numbers changed: {ref}")

    details = dict((m.group(1), m.group(2)) for m in re.finditer(
        r"^### (R\d{3})\. [^\n]+\n(.*?)(?=^### R\d{3}\.|^## E\.)", review, re.M | re.S))
    require(len(details) == 30, "Expected 30 original recipe details")
    totals = []
    for r in recipes:
        ref = r["ref"]
        require((r["name"], r["meal_type"], r["base_servings"]) == original_recipes[ref],
                f"Recipe name/meal/base changed: {ref}")
        require(r["base_servings"] == "1.00", f"Unexpected base servings: {ref}")
        base = number(r["base_servings"], 8, 2, positive=True)
        require(0 < len(r["name"]) <= 200 and r["image_url"] is None, f"Recipe metadata: {ref}")
        require(isinstance(r["prep_minutes"], int) and 0 <= r["prep_minutes"] <= 4294967295,
                f"prep_minutes range: {ref}")
        require(0 < len(r["instructions"].encode("utf-8")) <= 65535, f"TEXT size: {ref}")
        original_steps = re.search(r"\*\*Hướng dẫn ngắn:\*\* (.+)", details[ref]).group(1)
        original_minutes = int(re.search(r"\*\*Thời gian đề xuất:\*\* (\d+) phút", details[ref]).group(1))
        require(r["instructions"] == original_steps and r["prep_minutes"] == original_minutes,
                f"Instructions/prep changed: {ref}")
        original_ingredients = []
        for line in details[ref].splitlines():
            if re.match(r"\| F\d{3} \|", line):
                cells = [part.strip() for part in line.split("|")[1:-1]]
                original_ingredients.append({"food_ref": cells[0], "quantity_grams": cells[2]})
        require(r["ingredients"] == original_ingredients, f"Approved grams/order changed: {ref}")
        require(r["ingredients"] and len({i["food_ref"] for i in r["ingredients"]}) == len(r["ingredients"]),
                f"Empty or duplicate ingredients: {ref}")
        sums = [Decimal(0)] * 5
        for i in r["ingredients"]:
            require(i["food_ref"] in by_food, f"Missing Food reference: {ref}/{i['food_ref']}")
            grams = number(i["quantity_grams"], 10, 2, positive=True)
            for index, key in enumerate(KEYS):
                sums[index] += grams / 100 * Decimal(by_food[i["food_ref"]]["nutrients"][key])
        values = [(v / base).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP) for v in sums]
        require(all(0 <= v <= Decimal("999999999.999") for v in values), f"Snapshot overflow: {ref}")
        totals.append((r, values))
    require(sum(len(r["ingredients"]) for r in recipes) == 383, "Expected 383 links")

    # Compare every SQL data tuple, including names, instructions and approved grams.
    food_rows = ",\n".join("(" + ", ".join([quote(f["ref"]), quote(f["name"])] +
                           [f["nutrients"][k] for k in KEYS]) + ")" for f in foods) + ";"
    recipe_rows = ",\n".join("(" + ", ".join([quote(r["ref"]), quote(r["name"]),
                             quote(r["meal_type"]), r["base_servings"], quote(r["instructions"]),
                             str(r["prep_minutes"])]) + ")" for r in recipes) + ";"
    ingredient_rows = ",\n".join("(" + ", ".join([quote(r["ref"]), quote(i["food_ref"]),
                                  i["quantity_grams"]]) + ")"
                                  for r in recipes for i in r["ingredients"]) + ";"
    sqls = []
    for filename, label, expected in (
            ("vietnamese_foods.sql", "FOOD DATA", food_rows),
            ("vietnamese_recipes.sql", "RECIPE DATA", recipe_rows),
            ("vietnamese_recipe_ingredients.sql", "INGREDIENT DATA", ingredient_rows)):
        sql = (SEED / filename).read_text(encoding="utf-8")
        require(marked(sql, label) == expected, f"SQL payload drift: {filename}")
        # Only additive inserts plus session/temporary state; no persistent DDL or broad mutations.
        executable = re.sub(r"--[^\n]*", "", sql)
        require(not re.search(r"\b(?:UPDATE|DELETE|REPLACE|DROP|TRUNCATE|ALTER|USE)\b", executable, re.I),
                f"Disallowed SQL statement: {filename}")
        require(not re.search(r"CREATE\s+(?!TEMPORARY\b)", executable, re.I), f"Permanent DDL: {filename}")
        targets = re.findall(r"INSERT INTO\s+(\w+)", executable, re.I)
        require(all(t.startswith("_nf_") or t in {"foods", "recipes", "recipeingredients"} for t in targets),
                f"Out-of-scope INSERT: {filename}")
        # MySQL cannot reopen a temporary table, even under a second alias.
        without_literals = re.sub(r"'(?:''|[^'])*'", "''", executable)
        for statement in without_literals.split(";"):
            reads = re.findall(r"\b(?:FROM|JOIN)\s+(_nf_\w+)", statement, re.I)
            require(len(reads) == len(set(reads)), f"Temporary table reopened: {filename}")
            target = re.search(r"\bINSERT INTO\s+(_nf_\w+)", statement, re.I)
            require(not target or target.group(1) not in reads,
                    f"INSERT SELECT reads its own temporary target: {filename}")
        sqls.append(executable)
    combined = "\n".join(sqls)
    require(len(re.findall(r"\bSTART TRANSACTION\s*;", combined)) == 1 and
            len(re.findall(r"\bCOMMIT\s*;", combined)) == 1, "Single transaction expected")
    require(combined.index("START TRANSACTION;") < combined.index("INSERT INTO foods") and
            combined.index("COMMIT;") > combined.index("INSERT INTO recipeingredients"), "Transaction scope")
    require("STRICT_ALL_TABLES" in combined and "GET_LOCK(" in combined and
            "existing_recipe_ingredients_exact" in combined and
            "existing_foods_must_match_exactly" in combined and
            "existing_recipes_must_match_exactly" in combined, "Missing SQL safety guards")

    document = (ROOT / "docs/nutrition/vietnamese-food-nutrition-data.md").read_text(encoding="utf-8")
    for f in foods:
        expected = "| " + " | ".join([f["ref"], f["name"] + " (" + f["state"] + ")"] +
                                     [f["nutrients"][k] for k in KEYS] +
                                     [f["status"], f["basis"]]) + " |"
        require(expected in document, f"Nutrition document drift: {f['ref']}")
    rows = ["| " + " | ".join([r["ref"], r["name"], r["meal_type"]] +
                              [f"{v:.3f}" for v in values] + [flags(values)]) + " |"
            for r, values in totals]
    printed = document.split("<!-- BEGIN RECIPE TOTALS -->", 1)[1].split("<!-- END RECIPE TOTALS -->", 1)[0]
    require([line for line in printed.splitlines() if re.match(r"\| R\d{3} \|", line)] == rows,
            "Published recipe totals differ from Decimal calculation")
    print("PASS (STATIC ONLY): 82 Foods; 30 Recipes (10/10/10); 383 ingredients.")
    print("PASS: approved design unchanged; references, decimals, source flags, SQL payloads and document totals match.")
    print("Sources: 0 fully VERIFIED; 4 partially sourced + 78 analog/general estimates; all 82 ESTIMATED.")
    print("Energy plausibility: 82/82 within screening tolerance; zeros reviewed by documented assumptions.")
    print("Review flags:", ", ".join(f"{r['ref']} ({flags(v)})" for r, v in totals if flags(v) != "—"))
    print("No MySQL connection, SQL execution, Maven or Java tests performed.")
    if show_totals:
        print("| Ref | Recipe | Meal | kcal | Protein | Carbs | Fat | Fiber | Review |")
        print("|---|---|---|---:|---:|---:|---:|---:|---|")
        print("\n".join(rows))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-totals", action="store_true", help="Print the 30 calculated recipe rows")
    args = parser.parse_args()
    try:
        validate(args.show_totals)
    except (ValueError, KeyError, IndexError, AttributeError) as error:
        parser.exit(1, f"STATIC CHECK FAILED: {error}\n")
