"""Build auditable staging evidence. Offline only; does not create migration approval."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from extract_nin import extract as extract_nin
from extract_mext import extract as extract_mext
from extract_usda import extract as extract_usda, available_carbohydrate, FAO_CARBOHYDRATE_METHOD, RELEASE_SHA256

KEYS = ("calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g", "fiber_per_100g")
ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "database/staging/food-quality-v1"


def normalized_usda(key, nutrients, carbohydrate_columns="USDA1005 - USDA1079"):
    record = nutrients.get(key)
    if not record or record["value"] is None:
        return dict(value=None, status="MISSING", confidence="NONE", method="No source value")
    derivation = record.get("derivation") or {}
    description = derivation.get("description", "")
    if key == "carbs_per_100g":
        fiber = nutrients.get("fiber_per_100g", {}).get("value")
        value = available_carbohydrate(record["value"], fiber)
        return dict(value=value, status="CALCULATED" if value is not None else "MISSING",
            confidence=("LOW" if any(any(term in ((n.get("derivation") or {}).get("description", "").lower())
                for term in ("assum", "imput", "estimat")) for n in (record, nutrients.get("fiber_per_100g", {})))
                else "MODERATE") if value is not None else "NONE",
            method="Available carbohydrate by difference = " + carbohydrate_columns + ", same food record",
            method_url=FAO_CARBOHYDRATE_METHOD,
            inputs={"total_carbohydrate_g": record["value"], "dietary_fiber_g": fiber})
    if any(term in description.lower() for term in ("assum", "imput", "estimat")):
        status, confidence = "ESTIMATED", "LOW"
    elif "calculat" in description.lower():
        status, confidence = "CALCULATED", "MODERATE"
    else:
        status, confidence = "MATCHED", "MODERATE"
    return dict(value=record["value"], status=status, confidence=confidence,
        method="Published source value; " + (description or "no derivation stated; not claimed analytical"))


def normalize_nin(key, record, food_ref):
    nutrient = record["nutrients"].get(key)
    if (not nutrient or nutrient["value"] is None or not nutrient["definition_verified"]
            or food_ref in ("F044", "F058")):
        return dict(value=None, status="MISSING", confidence="NONE",
            method="NIN absent/ambiguous definition, implausible energy or conflicting species label; no substitution")
    return dict(value=nutrient["value"], status="MATCHED", confidence="MODERATE",
        method="NIN same stated edible state; analytical method/release not published by lookup")


def build(cache):
    inventory = json.loads((STAGING / "current-food-inventory.json").read_text(encoding="utf-8"))
    candidates = json.loads((STAGING / "source-candidates.json").read_text(encoding="utf-8"))
    decisions = json.loads((STAGING / "source-matching-decisions.json").read_text(encoding="utf-8"))
    raw_nin = extract_nin(Path(cache) / "nin-searches")
    raw_mext = extract_mext(Path(cache) / "mext2015-table.xlsx")
    raw_usda = extract_usda(Path(cache) / "usda-srlegacy-2018-official.zip")["foods"]
    by_ref = {r["food_ref"]: r for r in candidates["foods"]}
    for food in candidates["foods"]:
        for candidate in food["candidates"]:
            official = raw_usda[candidate["fdc_id"]]
            if candidate["evidence"] != official["nutrients"] or candidate["source_description"] != official["description"]:
                raise ValueError("Candidate evidence differs from official archive; review required")
    decision_map = {r["food_ref"]: r for r in decisions["decisions"]}
    if len(decision_map) != 82 or set(decision_map) != {r["food_ref"] for r in inventory["foods"]}:
        raise ValueError("Missing/duplicate food matching decisions")
    rows = []
    for old in inventory["foods"]:
        ref = old["food_ref"]
        decision = decision_map[ref]
        selected = next((r for r in by_ref[ref]["candidates"]
            if r.get("fdc_id") == decision["selected_usda_fdc_id"]), None)
        if selected and selected["matching_status"] != "MATCHED":
            raise ValueError("Rejected candidate cannot supply normalized values")
        alternative = raw_nin.get(decision["nin_alternative_code"])
        mext = raw_mext.get(decision.get("selected_mext_item_no"))
        nutrients = {}
        for key in KEYS:
            normalized = normalized_usda(key, mext["nutrients"], "MEXT Q - MEXT U") if mext else normalized_usda(key, selected["evidence"]) if selected else (
                normalize_nin(key, alternative, ref) if alternative else
                dict(value=None, status="MISSING", confidence="NONE", method="No compatible source selected"))
            source_value = mext["nutrients"].get(key) if mext else selected["evidence"].get(key) if selected else (
                alternative["nutrients"].get(key) if alternative else None)
            normalized.update(current_value=old["current_nutrients"][key], current_status="ESTIMATED",
                original_source_value=source_value,
                unit="KCAL" if key == "calories_per_100g" else "G", basis="100 g edible portion",
                delta_from_current=(format(Decimal(normalized["value"]) - Decimal(old["current_nutrients"][key]), "f")
                    if normalized["value"] is not None else None))
            nutrients[key] = normalized
        source = ({"publisher": selected["source"], "record_id": selected["fdc_id"],
            "url": selected["source_url"], "release": "SR Legacy04/2018", "food_publication_date": "2019-04-01",
            "archive_sha256": RELEASE_SHA256, "retrieved_date": "2026-10-19",
            "english_name": selected["source_description"], "match_differences": selected["differences"]}
            if selected else ({k: alternative[k] for k in ("source", "source_id", "source_url", "release", "retrieved_date", "name_en")}
                if alternative else None))
        if mext:
            source = {k: v for k, v in mext.items() if k != "nutrients"}
            source["match_differences"] = decision["notes"]
        rows.append(dict(food_ref=ref, aiven_food_id=old["aiven_food_id"], name_vi=old["name"],
            name_en=decision["catalog_name_en"], state=old["state"], edible_basis=old["basis"], category=decision["catalog_category"],
            recipe_count=old["recipe_count"], recipe_refs=old["recipe_refs"], source=source,
            nin_alternative=alternative, nutrients=nutrients,
            source_complete=all(n["value"] is not None for n in nutrients.values()),
            production_change_approved=False,
            issues=(["NIN carbohydrate/fiber labels lack assay/data dictionary confirmation; not used for normalization"] if alternative else [])
                + (["NIN Vietnamese/English species labels conflict"] if ref == "F058" else [])
                + (["NIN energy1kcal conflicts strongly with displayed macros; not auto-repaired to4/4/9"] if ref == "F044" else [])
                + (["Broth dilution, recipe and fat removal unknown; generic source is not recipe-specific verification"] if ref in ("F072", "F073", "F074") else [])))
    counts = Counter(n["status"] for row in rows for n in row["nutrients"].values())
    return dict(stage="STAGING_EVIDENCE_NOT_PRODUCTION_APPROVAL", retrieval_date="2026-10-19",
        canonical_sha256=hashlib.sha256((ROOT / "database/seed/vietnamese_catalog.json").read_bytes()).hexdigest(),
        carbohydrate_contract="AVAILABLE_BY_DIFFERENCE, not USDA total carbohydrate",
        source_evidence_does_not_mean_analytical_verification=True,
        summary=dict(food_count=len(rows), nutrient_count=sum(counts.values()), statuses=dict(sorted(counts.items())),
            complete_source_foods=sum(r["source_complete"] for r in rows),
            fully_verified_foods=sum(all(n["status"] == "VERIFIED" for n in r["nutrients"].values()) for r in rows)), foods=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=STAGING / "food-provenance.json")
    args = parser.parse_args()
    output = build(args.source_cache)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(output["summary"]))


if __name__ == "__main__":
    main()
