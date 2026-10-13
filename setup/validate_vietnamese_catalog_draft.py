"""Offline review of Vietnamese catalog drafts; no Flask, SQL, HTTP or import mode."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import unicodedata

DEFAULT_PATH = Path(__file__).resolve().parent / "drafts/vietnamese_catalog_v2"
ROLES = {"CARB", "PROTEIN", "VEGGIE", "SOUP", "MAIN", "SIDE", "DESSERT", "DRINK"}
MEALS = {"breakfast", "lunch", "dinner"}
STATES = {"raw", "raw_edible", "cooked", "ready"}
STATUSES = {"READY", "READY_ESTIMATED", "PENDING", "REJECTED"}
NUTRIENTS = ("calories", "protein", "carbs", "fat")


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def identity(value):
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def published_yield_blockers(recipe, sources):
    """Verify a cited recipe yield, never pass a proposed kitchen weight as measured."""
    if recipe.get("finished_weight_basis") != "PUBLISHED_RECIPE_YIELD":
        return []
    model = recipe.get("published_yield") or {}
    cooked = sources.get(model.get("source_id"), {})
    raw = sources.get(model.get("input_source_id"), {})
    reference = cooked.get("recipe_yield") or {}
    evidence = recipe.get("finished_weight_evidence")
    inputs, items = recipe.get("preparation_inputs", []), recipe.get("ingredients", [])
    if (not isinstance(evidence, dict) or evidence.get("verified") is not True
            or evidence.get("url") != reference.get("url") or not evidence.get("locator")
            or not reference.get("url") or not reference.get("locator")
            or cooked.get("verified") is not True or cooked.get("state") != "cooked"
            or raw.get("verified") is not True or raw.get("state") != "raw"
            or cooked.get("state_verified") is not True or raw.get("state_verified") is not True
            or reference.get("input_source_id") != model.get("input_source_id")
            or model.get("method") != reference.get("method")
            or recipe.get("nutrition_basis") != "PUBLISHED_COOKED_PROFILE"
            or recipe.get("additional_nutrient_ingredients") != []):
        return ["PUBLISHED_YIELD_SOURCE_MISMATCH"]
    change, factor, grams = reference.get("weight_change_percent"), model.get("factor"), model.get("input_edible_grams")
    if (type(change) not in (int, float) or not math.isfinite(change) or change <= -100
            or not number(factor) or factor <= 0 or not number(grams) or grams <= 0
            or not math.isclose(factor, 1 + change / 100, abs_tol=1e-9)
            or not number(recipe.get("finished_edible_grams"))
            or not math.isclose(recipe["finished_edible_grams"], grams * factor, abs_tol=.001)
            or len(inputs) != 1 or inputs[0].get("nutrient_source") != model.get("input_source_id")
            or inputs[0].get("edible_grams") != grams or inputs[0].get("state") != "raw"):
        return ["PUBLISHED_YIELD_MASS_MISMATCH"]
    # The source already models cooking losses. Applying them again is a double correction.
    if (len(items) != 1 or items[0].get("nutrient_source") != model.get("source_id")
            or items[0].get("edible_grams") != recipe["finished_edible_grams"]
            or any((items[0].get("retention_factors") or {}).get(k) != 1 for k in NUTRIENTS)):
        return ["COOKED_PROFILE_DOUBLE_CORRECTION"]
    return []


def calculate_recipe(recipe, sources, estimated=False):
    """Offline arithmetic only when every edible input and cooked denominator is evidenced."""
    blockers = published_yield_blockers(recipe, sources)
    weight = recipe.get("finished_edible_grams")
    assumed = estimated and recipe.get("finished_weight_basis") == "ASSUMED_COOKED_WEIGHT"
    if not number(weight) or weight <= 0 or (not assumed and recipe.get("finished_weight_verified") is not True):
        blockers.append("FINISHED_WEIGHT_NOT_VERIFIED")
    if not recipe.get("finished_weight_evidence"):
        blockers.append("FINISHED_WEIGHT_EVIDENCE_REQUIRED")
    if recipe.get("ingredient_list_complete") is not True:
        blockers.append("COMPLETE_RECIPE_REQUIRED")
    if estimated:
        if not recipe.get("assumptions") or recipe.get("estimated") is not True:
            blockers.append("ESTIMATE_ASSUMPTIONS_REQUIRED")
        if assumed:
            evidence = recipe.get("finished_weight_evidence")
            if (not isinstance(evidence, dict) or evidence.get("kind") != "ENGINEERING_ESTIMATE"
                    or evidence.get("not_measured") is not True or not evidence.get("rationale")):
                blockers.append("ESTIMATED_WEIGHT_DISCLOSURE_REQUIRED")
            balance = recipe.get("mass_balance", {})
            parts = [balance.get(k) for k in ("input_edible_grams", "discarded_grams", "evaporated_grams")]
            inputs = [i.get("edible_grams") for i in recipe.get("ingredients", [])]
            if (not all(number(v) for v in parts + inputs) or not number(weight)
                    or not math.isclose(parts[0], sum(inputs), abs_tol=.001)
                    or not math.isclose(parts[0] - parts[1] - parts[2], weight, abs_tol=.001)):
                blockers.append("ESTIMATED_MASS_BALANCE_MISMATCH")
    amounts = {k: 0.0 for k in NUTRIENTS}
    fiber_total, fiber_complete = 0.0, True
    items = recipe.get("ingredients", [])
    if not items:
        blockers.append("COMPLETE_RECIPE_REQUIRED")
    for item in items:
        source = sources.get(item.get("nutrient_source"))
        if source is None or source.get("verified") is not True:
            blockers.append("INGREDIENT_SOURCE_NOT_VERIFIED")
            continue
        if source.get("state_verified") is not True or source.get("state") != item.get("state"):
            blockers.append("INGREDIENT_SOURCE_STATE_MISMATCH")
        disclosed_match = (estimated and item.get("match_kind") == "REFERENCE_ESTIMATE" and item.get("match_note"))
        if item.get("nutrient_match_verified") is not True and not disclosed_match:
            blockers.append("INGREDIENT_NUTRIENT_MATCH_REQUIRED")
        designed_input = (estimated and item.get("edible_basis") == "SPECIFIED_EDIBLE_WEIGHT" and item.get("basis_note"))
        if item.get("state_or_edible_basis_verified") is not True and not designed_input:
            blockers.append("INGREDIENT_STATE_BASIS_REQUIRED")
        grams = item.get("edible_grams")
        if not number(grams) or grams <= 0:
            blockers.append("INGREDIENT_GRAMS_REQUIRED")
            continue
        factors = item.get("retention_factors", {})
        if (not isinstance(factors, dict) or any(not number(factors.get(k)) or factors[k] > 1 for k in NUTRIENTS)
                or not item.get("retention_evidence")):
            blockers.append("RETENTION_EVIDENCE_REQUIRED")
            continue
        if estimated and assumed:
            evidence = item.get("retention_evidence")
            if (not isinstance(evidence, dict) or evidence.get("kind") != "ENGINEERING_ASSUMPTION"
                    or evidence.get("not_measured") is not True or not evidence.get("rationale")):
                blockers.append("ESTIMATED_RETENTION_DISCLOSURE_REQUIRED")
        nutrients = source.get("nutrients_per_100g", {})
        if any(not number(nutrients.get(k)) for k in NUTRIENTS):
            blockers.append("INGREDIENT_NUTRIENTS_INCOMPLETE")
            continue
        for key in NUTRIENTS:
            amounts[key] += grams * nutrients[key] / 100 * factors[key]
        if number(nutrients.get("fiber")) and number(factors.get("fiber")) and factors["fiber"] <= 1:
            fiber_total += grams * nutrients["fiber"] / 100 * factors["fiber"]
        else:
            fiber_complete = False
    if blockers:
        return {"status": "BLOCKED", "blockers": sorted(set(blockers)), "per_100g": None}
    values = {k: round(v * 100 / weight, 4) for k, v in amounts.items()}
    values["fiber"] = round(fiber_total * 100 / weight, 4) if fiber_complete else None
    return {"status": "CALCULATED", "blockers": [], "per_100g": values,
            "fiber_complete": fiber_complete, "finished_edible_grams": weight,
            "batch_totals": {**amounts, "fiber": fiber_total if fiber_complete else None}}


def source_registry_errors(source_data):
    errors = []
    if source_data.get("not_importable") is not True:
        errors.append("SOURCE_REGISTRY_MUST_NOT_BE_IMPORTABLE")
    ids = [s.get("source_id") for s in source_data.get("sources", [])]
    if len(ids) != len(set(ids)):
        errors.append("DUPLICATE_SOURCE_ID")
    for source in source_data.get("sources", []):
        if (not source.get("food_code") or not source.get("checked_on") or not source.get("locator")
                or not re.match(r"https?://", source.get("url", "")) or source.get("basis") != "100g_edible_input"):
            errors.append("SOURCE_METADATA_REQUIRED")
        values = source.get("nutrients_per_100g", {})
        if set(values) != set(NUTRIENTS) | {"fiber"} or any(v is not None and not number(v) for v in values.values()):
            errors.append("SOURCE_NUTRIENT_VALUE")
        # Cellulose is retained separately, never silently called total dietary fiber.
        if source.get("fiber_method") in ("cellulose", "crude_fiber") and values.get("fiber") is not None:
            errors.append("CELLULOSE_IS_NOT_TOTAL_DIETARY_FIBER")
        code = str(source.get("food_code", ""))
        if "fdc_id" in source.get("locator", {}) and str(source["locator"]["fdc_id"]) != code:
            errors.append("SOURCE_FOOD_CODE_MISMATCH")
        if ".invalid" in source.get("url", ""):
            errors.append("SOURCE_URL_NOT_REAL")
    return sorted(set(errors))


def readiness_blockers(dish, sources=None):
    """Data sufficiency for review, never authorization to import persistent data."""
    if dish.get("review_status") == "READY_ESTIMATED":
        return estimated_readiness_blockers(dish, sources or {})
    blockers = []
    portions = [dish.get(k) for k in ("min_grams", "reference_grams", "max_grams")]
    if not all(number(v) for v in portions) or not 1 <= portions[0] <= portions[1] <= portions[2] <= 2000:
        blockers.append("PORTION_EVIDENCE_REQUIRED")
    macros = dish.get("macros_per_100g", {})
    if not all(number(v) for v in [dish.get("calories_per_100g"), *(macros.get(k) for k in ("protein", "carbs", "fat"))]):
        blockers.append("NUTRIENTS_REQUIRED")
    provenance = dish.get("provenance", {})
    recipe = provenance.get("recipe", {})
    if provenance.get("license_status") != "VERIFIED_FOR_REUSE":
        blockers.append("REUSE_TERMS_REQUIRED")
    references = provenance.get("nutrition_references", [])
    if not references or not all(r.get("verified") is True and r.get("url") and r.get("food_code") for r in references):
        blockers.append("MATCHED_NUTRIENT_SOURCES_REQUIRED")
    if not number(recipe.get("finished_edible_grams")) or recipe.get("finished_edible_grams", 0) <= 0 or not recipe.get("finished_weight_evidence"):
        blockers.append("FINISHED_WEIGHT_EVIDENCE_REQUIRED")
    ingredients = recipe.get("ingredients", [])
    if not ingredients or not recipe.get("ingredient_list_complete"):
        blockers.append("COMPLETE_RECIPE_REQUIRED")
    for item in ingredients:
        if not number(item.get("edible_grams")) or item.get("edible_grams", 0) <= 0:
            blockers.append("INGREDIENT_GRAMS_REQUIRED")
        if item.get("state") not in STATES or item.get("state_or_edible_basis_verified") is not True:
            blockers.append("INGREDIENT_STATE_BASIS_REQUIRED")
        if not item.get("nutrient_source"):
            blockers.append("INGREDIENT_NUTRIENT_MATCH_REQUIRED")
        if not set(item.get("tags", [])) <= set(dish.get("ingredients", [])):
            blockers.append("INGREDIENT_TAG_MISSING")
    if recipe.get("allergen_review_complete") is not True:
        blockers.append("ALLERGEN_REVIEW_REQUIRED")
    if not provenance.get("method") or provenance.get("method", "").startswith("pending"):
        blockers.append("CALCULATION_METHOD_REQUIRED")
    if not provenance.get("portion_evidence"):
        blockers.append("PORTION_REVIEW_REQUIRED")
    if provenance.get("phase2_review") or dish.get("review_status") == "READY":
        calculated = calculate_recipe(recipe, sources or {})
        blockers.extend(calculated["blockers"])
        if provenance.get("portion_verified") is not True:
            blockers.append("PORTION_NOT_VERIFIED")
        for item in ingredients:
            source = (sources or {}).get(item.get("nutrient_source"))
            if source and source.get("reuse_status") != "VERIFIED_FOR_REUSE":
                blockers.append("INGREDIENT_REUSE_TERMS_REQUIRED")
        if calculated["per_100g"] is not None:
            for key in NUTRIENTS:
                actual = dish.get("calories_per_100g") if key == "calories" else macros.get(key)
                if not number(actual) or not math.isclose(actual, calculated["per_100g"][key], rel_tol=.001, abs_tol=.05):
                    blockers.append("RECIPE_NUTRIENT_MISMATCH")
    # 4/4/9 is a plausibility check, not a replacement for published energy.
    if "NUTRIENTS_REQUIRED" not in blockers:
        calculated = 4 * (macros["protein"] + macros["carbs"]) + 9 * macros["fat"]
        delta = abs(calculated - dish["calories_per_100g"]) / max(dish["calories_per_100g"], 1)
        if delta > .20 and not provenance.get("energy_consistency_explanation"):
            blockers.append("ENERGY_DIFFERENCE_NEEDS_EXPLANATION")
    blockers.extend(provenance.get("missing_evidence", []))
    return sorted(set(blockers))


def estimated_readiness_blockers(dish, sources):
    """Student-project estimates may disclose assumptions, but must reproduce arithmetic."""
    p = dish.get("provenance", {})
    recipe = p.get("recipe", {})
    result = calculate_recipe(recipe, sources, estimated=True)
    blockers = list(result["blockers"])
    servings = recipe.get("servings")
    # A chosen serving is reproducible, without pretending it was weighed after cooking.
    if (not number(servings) or servings < 1 or int(servings) != servings
            or not number(recipe.get("finished_edible_grams")) or not number(dish.get("reference_grams"))
            or not math.isclose(dish["reference_grams"], recipe["finished_edible_grams"] / servings, abs_tol=.01)):
        blockers.append("ESTIMATED_SERVING_MISMATCH")
    portions = [dish.get(k) for k in ("min_grams", "reference_grams", "max_grams")]
    if not all(number(v) for v in portions) or not 1 <= portions[0] <= portions[1] <= portions[2] <= 2000:
        blockers.append("PORTION_EVIDENCE_REQUIRED")
    if (dish.get("estimated") is not True or not p.get("method") or not p.get("confidence")
            or not p.get("limitations") or not p.get("portion_evidence")):
        blockers.append("ESTIMATE_PROVENANCE_REQUIRED")
    references = p.get("nutrition_references", [])
    if not references:
        blockers.append("MATCHED_NUTRIENT_SOURCES_REQUIRED")
    linked = {}
    for reference in references:
        source = sources.get(reference.get("source_id"))
        if (not source or source.get("verified") is not True or reference.get("verified") is not True
                or reference.get("food_code") != source.get("food_code") or reference.get("url") != source.get("url")):
            blockers.append("SOURCE_REFERENCE_MISMATCH")
        linked[reference.get("source_id")] = reference
    for item in recipe.get("ingredients", []):
        if item.get("nutrient_source") not in linked:
            blockers.append("INGREDIENT_REFERENCE_REQUIRED")
        if not set(item.get("tags", [])) <= set(dish.get("ingredients", [])):
            blockers.append("INGREDIENT_TAG_MISSING")
    if recipe.get("allergen_review_complete") is not True:
        blockers.append("ALLERGEN_REVIEW_REQUIRED")
    if result["per_100g"] is not None:
        values = {"calories": dish.get("calories_per_100g"), **dish.get("macros_per_100g", {})}
        for key in NUTRIENTS + ("fiber",):
            computed, actual = result["per_100g"].get(key), values.get(key)
            if computed is None:
                if actual is not None:
                    blockers.append("RECIPE_NUTRIENT_MISMATCH")
            elif not number(actual) or not math.isclose(actual, computed, rel_tol=.001, abs_tol=.005):
                blockers.append("RECIPE_NUTRIENT_MISMATCH")
        if all(number(values.get(k)) for k in NUTRIENTS):
            if values["calories"] > 900 or sum(values[k] for k in ("protein", "carbs", "fat")) > 100:
                blockers.append("IMPLAUSIBLE_NUTRIENT_DENSITY")
            energy = 4 * (values["protein"] + values["carbs"]) + 9 * values["fat"]
            if abs(energy - values["calories"]) / max(values["calories"], 1) > .20 and not p.get("energy_consistency_explanation"):
                blockers.append("ENERGY_DIFFERENCE_NEEDS_EXPLANATION")
    blockers.extend(p.get("missing_evidence", []))
    return sorted(set(blockers))


def validate(target_data, draft_data, seed, source_data=None):
    errors = []
    sources = {s["source_id"]: s for s in (source_data or {}).get("sources", [])}
    if source_data is not None:
        errors.extend(source_registry_errors(source_data))
    targets, drafts = target_data["targets"], draft_data["drafts"]
    if target_data.get("not_importable") is not True or draft_data.get("not_importable") is not True:
        errors.append("DRAFT_MUST_NOT_BE_IMPORTABLE")
    if len(targets) != target_data["target_count"] or target_data.get("goal") != "PRACTICAL_100_FOODS":
        errors.append("TARGET_COUNT")
    if len(drafts) != draft_data["draft_count"]:
        errors.append("DRAFT_COUNT")
    for label, records in (("TARGET", targets), ("DRAFT", drafts)):
        ids = [d["dish_id"] for d in records]
        if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[a-z0-9_-]{1,64}", i) for i in ids):
            errors.append(label + "_DUPLICATE_OR_INVALID_ID")
        if any(d["type"] not in ROLES or not 1 <= len(d["name"]) <= 200 for d in records):
            errors.append(label + "_ROLE_OR_NAME")
    if dict(Counter(d["type"] for d in targets)) != target_data["role_targets"]:
        errors.append("ROLE_TOTALS")
    existing = {d["dish_id"] for d in seed["dishes"]}
    retained = {d["existing_dish_id"] for d in targets if d["existing_dish_id"]}
    if (set(target_data.get("preserved_runtime_ids", [])) != existing
            or not retained <= existing
            or any(d["dish_id"] != d["existing_dish_id"] for d in targets if d["existing_dish_id"])):
        errors.append("EXISTING_IDS_MUST_BE_PRESERVED")
    new = [d for d in targets if not d["existing_dish_id"]]
    names = [identity(d["name"]) for d in new]
    families = [d["recipe_identity"] for d in new]
    if len(names) != len(set(names)) or len(families) != len(set(families)):
        errors.append("DUPLICATE_NEW_RECIPE")
    if {d["dish_id"] for d in new} & existing:
        errors.append("NEW_ID_COLLIDES_WITH_EXISTING")
    by_id = {d["dish_id"]: d for d in targets}
    seed_by_id = {d["dish_id"]: d for d in seed["dishes"]}
    report = []
    for dish in drafts:
        identifier = dish["dish_id"]
        if identifier not in by_id or dish["type"] != by_id[identifier]["type"]:
            errors.append(identifier + ":TARGET_MISMATCH")
        if (not dish.get("existing_dish_id") and any(identity(dish["name"]) == identity(old["name"]) for old in seed["dishes"])):
            errors.append(identifier + ":NEW_NAME_COLLIDES_WITH_EXISTING")
        if dish.get("existing_dish_id") and dish.get("baseline_snapshot") != seed_by_id.get(identifier):
            errors.append(identifier + ":BASELINE_SNAPSHOT_CHANGED")
        if dish.get("review_status") not in STATUSES:
            errors.append(identifier + ":INVALID_STATUS")
        if dish.get("active") is not False or dish.get("import_ready") is not False:
            errors.append(identifier + ":DRAFT_CANNOT_BE_ACTIVE_OR_IMPORT_READY")
        if dish.get("preparation_state") not in STATES or not dish["meal_types"] or not set(dish["meal_types"]) <= MEALS:
            errors.append(identifier + ":STATE_OR_MEAL")
        if dish["type"] == "MAIN" and set(dish["meal_types"]) != {"breakfast"}:
            errors.append(identifier + ":CURRENT_MAIN_RULES")
        if not isinstance(dish.get("ingredients"), list) or any(not isinstance(tag, str) for tag in dish["ingredients"]):
            errors.append(identifier + ":TAGS")
        if type(dish.get("estimated")) is not bool:
            errors.append(identifier + ":ESTIMATED_FLAG")
        values = [dish.get("calories_per_100g"), *dish.get("macros_per_100g", {}).values()]
        if set(dish.get("macros_per_100g", {})) != {"protein", "carbs", "fat", "fiber"} or any(v is not None and not number(v) for v in values):
            errors.append(identifier + ":NUTRIENT_UNIT_OR_VALUE")
        portions = [dish.get(k) for k in ("min_grams", "reference_grams", "max_grams")]
        if any(v is not None and (not number(v) or v < 1 or v > 2000) for v in portions):
            errors.append(identifier + ":PORTION_VALUE")
        if all(number(v) for v in portions) and not portions[0] <= portions[1] <= portions[2]:
            errors.append(identifier + ":PORTION_ORDER")
        for item in dish.get("provenance", {}).get("recipe", {}).get("ingredients", []):
            if item.get("edible_grams") is not None and not number(item["edible_grams"]):
                errors.append(identifier + ":INGREDIENT_GRAMS")
            if not set(item.get("tags", [])) <= set(dish["ingredients"]):
                errors.append(identifier + ":INGREDIENT_TAG_MISSING")
            if source_data is not None and item.get("nutrient_source") and item["nutrient_source"] not in sources:
                errors.append(identifier + ":UNKNOWN_INGREDIENT_SOURCE")
        aliases = dish.get("provenance", {}).get("name_aliases", [])
        if any(a.get("approved_for_runtime") is not False or a.get("equivalence") not in ("equivalent", "broader", "variant") for a in aliases):
            errors.append(identifier + ":DRAFT_ALIAS_NOT_RUNTIME_APPROVED")
        blockers = readiness_blockers(dish, sources)
        if dish["review_status"] in ("READY", "READY_ESTIMATED") and blockers:
            errors.append(identifier + ":READY_WITH_MISSING_EVIDENCE")
        report.append({"dish_id": identifier, "status": dish["review_status"], "readiness_blockers": blockers})
    return {"structural_validation": "PASS" if not errors else "FAIL", "errors": errors,
            "targets": len(targets), "new_targets": len(new), "retained_ids": len(retained),
            "drafts": len(drafts), "statuses": dict(Counter(d["review_status"] for d in drafts)),
            "ready_for_review": sum(d["review_status"] in ("READY", "READY_ESTIMATED") for d in drafts),
            "preserved_runtime_ids": len(existing),
            "authorized_for_import": False, "database_writes": 0, "records": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--details", action="store_true")
    parser.add_argument("--baseline-seed", type=Path, help="Historical study baseline; no database writes")
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    result = validate(load(args.path / "targets.json"), load(args.path / "draft_dishes.json"),
                      load(args.baseline_seed or Path(__file__).resolve().parent / "seeds/nutrition_catalog.json"),
                      load(args.path / "ingredient_sources.json") if (args.path / "ingredient_sources.json").exists() else None)
    if not args.details:
        result.pop("records")
    print(json.dumps(result, ensure_ascii=False))
    return bool(result["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
