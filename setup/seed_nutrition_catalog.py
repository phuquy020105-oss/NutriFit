"""Explicit, insert-only catalog import. Default mode validates without database I/O."""
import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parent / "seeds/nutrition_catalog.json"
REVIEW_PATH = SEED_PATH.parent.parent / "drafts/vietnamese_catalog_v2"
ROLES = {"MAIN", "CARB", "PROTEIN", "VEGGIE", "SOUP", "SIDE", "DRINK", "DESSERT"}
MEALS = {"breakfast", "lunch", "dinner"}


def load_seed(path=SEED_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    seen = set()
    for dish in data["dishes"]:
        identifier = dish["dish_id"]
        if not re.fullmatch(r"[a-z0-9_-]{1,64}", identifier) or identifier in seen:
            raise ValueError("Duplicate or invalid dish ID")
        seen.add(identifier)
        if not isinstance(dish["name"], str) or not 1 <= len(dish["name"]) <= 200:
            raise ValueError("Invalid dish name")
        if dish["type"] not in ROLES or dish["preparation_state"] not in ("raw", "cooked", "ready", "raw_edible"):
            raise ValueError("Invalid dish role or preparation state")
        if not dish["meal_types"] or not set(dish["meal_types"]) <= MEALS:
            raise ValueError("Invalid meal types")
        if not 1 <= dish["min_grams"] <= dish["reference_grams"] <= dish["max_grams"] <= 2000:
            raise ValueError("Invalid reference portion")
        if set(dish["macros_per_100g"]) != {"carbs", "protein", "fat", "fiber"}:
            raise ValueError("Invalid nutrient fields")
        for value in (dish["calories_per_100g"], *dish["macros_per_100g"].values()):
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError("Invalid nutrient")
        if not isinstance(dish["ingredients"], list) or any(not isinstance(t, str) for t in dish["ingredients"]):
            raise ValueError("Invalid ingredients")
        if not isinstance(dish["provenance"], dict) or not dish["provenance"].get("source"):
            raise ValueError("Missing provenance")
        if type(dish["estimated"]) is not bool or type(dish.get("active", True)) is not bool:
            raise ValueError("Invalid status")
        if dish.get("prep_minutes") is not None and (type(dish["prep_minutes"]) is not int or not 1 <= dish["prep_minutes"] <= 120):
            raise ValueError("Invalid preparation time")
    seen = set()
    for menu in data["legacy_menus"]:
        if menu["template_id"] in seen or menu["meal_type"] not in MEALS or not 0 <= menu["day"] <= 6:
            raise ValueError("Invalid legacy menu")
        seen.add(menu["template_id"])
    return data


def seed_checksum(path=SEED_PATH):
    """Compare data, not checkout-specific LF/CRLF bytes."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_review_batch(path, baseline_seed_path=None):
    """Validate reviewed new dishes; never import proposed updates to existing IDs."""
    from validate_vietnamese_catalog_draft import validate
    load = lambda name: json.loads((REVIEW_PATH / name).read_text(encoding="utf-8"))
    drafts = load("draft_dishes.json")
    baseline_path = Path(baseline_seed_path) if baseline_seed_path else SEED_PATH
    result = validate(load("targets.json"), drafts, load_seed(baseline_path), load("ingredient_sources.json"))
    if result["errors"]:
        raise ValueError("Draft validation failed")
    batch = load_seed(path)
    formats = {"nutrifit-practical-vietnamese-review-batch", "nutrifit-practical-vietnamese-completion-batch"}
    if batch.get("format") not in formats or batch["legacy_menus"]:
        raise ValueError("Expected review batch without legacy writes")
    if (batch.get("seed_checksum_basis") != "canonical_json_utf8_sorted_keys"
            or batch.get("seed_baseline_sha256") != seed_checksum(baseline_path)):
        raise ValueError("Seed baseline changed; review again")
    if batch["format"] == "nutrifit-practical-vietnamese-review-batch":
        expected = {d["dish_id"]: d for d in drafts["drafts"] if d["dish_id"] in drafts["phase2_batch_ids"]
                    and not d.get("existing_dish_id") and d["review_status"] == "READY_ESTIMATED"}
        if len(expected) != 11:
            raise ValueError("Expected exactly eleven initial estimated dishes")
    else:
        targets = load("targets.json")["targets"]
        eligible = {d["dish_id"] for d in targets if not d["existing_dish_id"]} - set(drafts["phase2_batch_ids"])
        expected = {d["dish_id"]: d for d in drafts["drafts"] if d["dish_id"] in eligible
                    and d["review_status"] == "READY_ESTIMATED"}
        declared = batch.get("batch_ids", [])
        if (not expected or set(declared) != set(expected) or len(declared) != len(expected)
                or set(drafts.get("completion_batch_ids", [])) != set(expected) or batch.get("review_existing")):
            raise ValueError("Completion batch must match all reviewed new target IDs, excluding initial batch")
    if {d["dish_id"] for d in batch["dishes"]} != set(expected):
        raise ValueError("Batch IDs differ from reviewed estimated dishes")
    names = [folded_name(d["name"]) for d in batch["dishes"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate reviewed food names")
    for row in batch["dishes"]:
        original = expected[row["dish_id"]]
        if row.get("active") is not True or row.get("estimated") is not True:
            raise ValueError("Estimated active batch expected")
        if any(original.get(k) != value for k, value in row.items() if k != "active"):
            raise ValueError("Batch differs from reviewed draft")
        if any(row.get(k) is None for k in ("calories_per_100g",)) or any(
                row["macros_per_100g"].get(k) is None for k in ("protein", "carbs", "fat")):
            raise ValueError("Required nutrients missing")
    return batch


def folded_name(name):
    value = " ".join(name.casefold().split()).replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c))


def inspect_review_batch(batch, repository):
    """Read-only collision/value review; return only counts and public food IDs."""
    existing = repository.dishes(active=False)
    by_id = {d["dish_id"]: d for d in existing}
    names = {folded_name(d["name"]): d["dish_id"] for d in existing}
    pending, matched = [], []
    for dish in batch["dishes"]:
        old = by_id.get(dish["dish_id"])
        if old is not None:
            if any(old.get(k) != value for k, value in dish.items()):
                raise ValueError("Existing batch ID has different data; will not overwrite")
            matched.append(dish["dish_id"])
        else:
            if folded_name(dish["name"]) in names:
                raise ValueError("Existing food name collision; review before insert")
            pending.append(dish["dish_id"])
    return {"total_before": len(existing), "active_before": sum(d["active"] for d in existing),
            "pending_ids": pending, "already_matching_ids": matched,
            "expected_total_after": len(existing) + len(pending),
            "expected_active_after": sum(d["active"] for d in existing) + len(pending)}


def require_external_backup(path):
    backup = Path(path).resolve()
    repo = Path(__file__).resolve().parents[1]
    if backup.is_relative_to(repo) or not backup.is_file() or backup.stat().st_size == 0:
        raise ValueError("Nonempty backup outside repository required")
    # Structural sanity only; an actual restore rehearsal is a separate operation.
    with backup.open("rb") as stream:
        if not any(b"create table `nutritionfoodcatalog`" in line.lower() for line in stream):
            raise ValueError("Expected catalog table in SQL backup")
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="Write only after explicit approval and backup")
    action.add_argument("--check-db", action="store_true", help="Read-only review of local database; requires --batch")
    parser.add_argument("--batch", type=Path, help="Review manifest; imports new dishes only, ignores review_existing")
    parser.add_argument("--baseline-seed", type=Path, help="Explicit historical baseline; validate-only, never apply/check-db")
    parser.add_argument("--backup", type=Path, help="Existing SQL backup outside Git, required for --batch --apply")
    parser.add_argument("--database", help="Exact local database name required with --apply")
    args = parser.parse_args()
    if args.baseline_seed and (not args.batch or args.apply or args.check_db):
        parser.error("Historical baseline override is allowed only with --batch validate-only")
    try:
        data = load_review_batch(args.batch, args.baseline_seed) if args.batch else load_seed()
    except (ValueError, KeyError, TypeError):
        parser.error("Invalid seed/review batch; validate drafts and manifest")
    if not args.baseline_seed and any(d["dish_id"].startswith("usda_") or "usda" in json.dumps(d["provenance"]).lower() for d in data["dishes"]):
        parser.error("Archived external-source batch retired; use the reviewed Vietnamese runtime seed")
    if args.check_db and not args.batch:
        parser.error("--check-db requires --batch")
    if not args.apply and not args.check_db:
        print(json.dumps({"mode": "validate_only", "dishes": len(data["dishes"]),
                          "legacy_menus": len(data["legacy_menus"]), "database_writes": 0}))
        return
    if args.database != "NutriFitDB":
        parser.error("Database mode requires --database NutriFitDB")
    if args.batch and args.apply:
        if not args.backup:
            parser.error("Batch apply requires --backup outside repository")
        try:
            require_external_backup(args.backup)
        except ValueError:
            parser.error("Nonempty catalog SQL backup outside repository required; restore not verified by this check")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from app import create_app
    from app.extensions import db
    from app.repositories.food_catalog_repository import FoodCatalogRepository
    from sqlalchemy import text
    try:
        app = create_app()
        with app.app_context():
            if db.engine.url.drivername != "mysql+pymysql" or db.engine.url.host != "127.0.0.1" or (db.engine.url.port or 3306) != 3306:
                raise ValueError("Expected local MySQL 127.0.0.1:3306")
            if args.check_db:
                db.session.execute(text("START TRANSACTION READ ONLY"))
            actual = db.session.execute(text("SELECT DATABASE()")).scalar()
            if str(actual).casefold() != args.database.casefold():
                raise ValueError("Unexpected current database")
            if args.batch:
                from sqlalchemy import inspect
                columns = {c["name"] for c in inspect(db.session.connection()).get_columns("NutritionFoodCatalog")}
                required = {"DishId", "NameVi", "ComponentType", "PreparationState", "ReferenceGrams",
                    "MinGrams", "MaxGrams", "KcalPer100G", "ProteinPer100G", "CarbsPer100G",
                    "FatPer100G", "FiberPer100G", "IngredientsJson", "MealTypesJson", "PrepMinutes",
                    "ProvenanceJson", "Estimated", "IsActive", "DataVersion"}
                if not required <= columns:
                    raise ValueError("Catalog mapping incompatible with schema")
                engine = db.session.execute(text("SELECT ENGINE FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA=DATABASE() AND LOWER(TABLE_NAME)='nutritionfoodcatalog'")).scalar()
                if str(engine).casefold() != "innodb":
                    raise ValueError("Transactional InnoDB required")
                review = inspect_review_batch(data, FoodCatalogRepository)
                if args.check_db:
                    db.session.rollback()
                    print(json.dumps({"mode": "read_only_review", "database_writes": 0, **review}))
                    return
            try:
                inserted = FoodCatalogRepository.insert_missing(data["dishes"], data["legacy_menus"])
                if args.batch:
                    after = inspect_review_batch(data, FoodCatalogRepository)
                    if (after["pending_ids"] or inserted["dishes"] != len(review["pending_ids"])
                            or after["total_before"] != review["expected_total_after"]):
                        raise ValueError("Post-insert verification failed")
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
            print(json.dumps({"mode": "insert_only", "inserted": inserted}))
    except Exception as error:
        # Never print SQL parameters, connection URLs or provider credentials.
        print("Seed failed; rolled back data writes. Error type: " + type(error).__name__)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
