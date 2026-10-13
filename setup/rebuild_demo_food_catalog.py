"""Reviewed catalog-only data migration; validation is the default, no schema DDL."""
import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from seed_nutrition_catalog import load_seed, folded_name

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "setup/seeds/demo_catalog_rebuild_review.json"


def digest_rows(rows):
    values = [json.dumps(row, ensure_ascii=False, default=lambda v: v.hex() if isinstance(v, bytes) else str(v), separators=(",", ":")) for row in rows]
    return hashlib.sha256("\n".join(sorted(values)).encode()).hexdigest()


def qid(name):
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError("Invalid SQL identifier")
    return "`" + name + "`"


def fingerprints(connection):
    connection.rollback()
    result = {}
    with connection.cursor() as cur:
        cur.execute("START TRANSACTION READ ONLY")
        cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")
        tables = [row[0] for row in cur.fetchall()]
        for table in tables:
            cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION", (table,))
            columns = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT " + ",".join(qid(c) for c in columns) + " FROM " + qid(table))
            rows = cur.fetchall()
            result[table.lower()] = {"count": len(rows), "sha256": digest_rows(rows), "columns": columns}
    connection.rollback()
    return result


def reviewed_data(seed_path=None, review_path=REVIEW):
    # Freeze this historical 141-to-77 migration; later additive batches have their own manifest.
    frozen = ROOT / "setup/seeds/demo_catalog_rebuild_seed.json"
    data = load_seed(seed_path or (frozen if frozen.exists() else ROOT / "setup/seeds/nutrition_catalog.json"))
    review = json.loads(Path(review_path).read_text(encoding="utf-8"))
    rows = data["dishes"]
    if len(rows) != review["after_count"] or len(data["legacy_menus"]) != 63:
        raise ValueError("Reviewed count mismatch")
    if len({folded_name(d["name"]) for d in rows}) != len(rows):
        raise ValueError("Duplicate food name")
    for dish in rows:
        if dish["dish_id"].startswith("usda_") or "usda" in json.dumps(dish["provenance"]).lower():
            raise ValueError("Retired source in active seed")
        if dish["estimated"] is not True or dish.get("active") is not True:
            raise ValueError("Expected estimated active data")
        provenance = dish["provenance"]
        recipe = provenance.get("recipe", {})
        weight = recipe.get("finished_edible_grams", 0)
        if weight <= 0 or provenance.get("ingredients_complete") is not True:
            raise ValueError("Missing recipe mass/ingredients")
        raw = recipe["ingredients"]
        if any(i["edible_grams"] <= 0 or not 0 <= i["retained_grams"] <= i["edible_grams"] or i["state"] not in ("raw", "raw_edible", "cooked", "ready") for i in raw):
            raise ValueError("Invalid edible ingredient or retained mass")
        input_weight = sum(i["edible_grams"] for i in raw)
        if weight > input_weight + .01 or abs(recipe["input_edible_grams"] - input_weight) > .01:
            raise ValueError("Unexplained recipe mass gain")
        for macro in ("protein", "carbs", "fat"):
            value = sum(i["retained_grams"] * i["macro_per_100g"][macro] / 100 for i in raw) / weight * 100
            if not math.isfinite(value) or value < 0 or abs(value - dish["macros_per_100g"][macro]) > .001:
                raise ValueError("Nonreproducible nutrient calculation")
        m = dish["macros_per_100g"]
        if abs(dish["calories_per_100g"] - 4 * m["protein"] - 4 * m["carbs"] - 9 * m["fat"]) > .01 or sum(m[k] for k in ("protein", "carbs", "fat")) > 100.01:
            raise ValueError("Energy/macronutrient inconsistency")
    return data, review


def dependency_check(connection, removed):
    """No live foreign keys or unfrozen/unknown ID references may be removed."""
    result = {}
    with connection.cursor() as cur:
        cur.execute("SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND LOWER(REFERENCED_TABLE_NAME)='nutritionfoodcatalog'")
        if cur.fetchall():
            raise ValueError("Catalog foreign key exists; review required")
        cur.execute("SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND DATA_TYPE IN ('json','text','mediumtext','longtext','varchar','char')")
        columns = cur.fetchall()
        pattern = re.compile(r'(?<![a-z0-9_])(' + '|'.join(re.escape(i) for i in sorted(removed)) + r')(?![a-z0-9_])')
        for table, column in columns:
            if table.lower() == "nutritionfoodcatalog":
                continue
            cur.execute("SELECT " + qid(column) + " FROM " + qid(table))
            found = [r[0] for r in cur.fetchall() if isinstance(r[0], str) and pattern.search(r[0])]
            if not found:
                continue
            expected = {("nutritionmealdetails", "RecipeJson"): "components", ("nutritionfoodintake", "SnapshotJson"): "items"}
            key = expected.get((table.lower(), column))
            if key is None:
                raise ValueError("Unreviewed reference outside frozen recipe/intake")
            for value in found:
                snapshot = json.loads(value)
                for part in snapshot.get(key, []):
                    if part.get("dish_id") in removed:
                        # Early snapshots froze portion totals only. Existing snapshot_component
                        # derives their per-100g values from those totals and original grams.
                        grams = part.get("grams")
                        macros = part.get("macros", {})
                        values = [part.get("calories"), *(macros.get(k) for k in ("protein", "carbs", "fat", "fiber"))]
                        if type(grams) not in (int, float) or not math.isfinite(grams) or grams <= 0 or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values):
                            raise ValueError("Missing frozen historical portion totals")
                        nutrients = part.get("nutrition_per_100g")
                        if nutrients and not all(k in nutrients for k in ("calories", "protein", "carbs", "fat", "fiber")):
                            raise ValueError("Incomplete frozen per100g snapshot")
            result[table.lower() + "." + column] = len(found)
    return result


def same_catalog(connection, dishes):
    from app.repositories.food_catalog_repository import FoodCatalogRepository
    with connection.cursor(__import__("pymysql").cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM NutritionFoodCatalog ORDER BY DishId")
        actual = {r["DishId"]: FoodCatalogRepository.serialize(r) for r in cur.fetchall()}
    expected = {d["dish_id"]: d for d in dishes}
    return set(actual) == set(expected) and all(all(actual[i].get(k) == v for k, v in dish.items()) for i, dish in expected.items())


def apply_catalog(connection, data, review):
    """Single InnoDB transaction; only reviewed catalog IDs may change."""
    before = fingerprints(connection)
    if same_catalog(connection, data["dishes"]):
        connection.rollback()
        return {"idempotent": True, "writes": 0, "active": len(data["dishes"])}
    connection.rollback()
    if before["nutritionfoodcatalog"]["sha256"] != review["baseline_catalog_sha256"]:
        raise ValueError("Catalog changed since review")
    references = dependency_check(connection, set(review["removed_ids"]))
    connection.rollback()
    try:
        connection.begin()
        with connection.cursor() as cur:
            cur.execute("SELECT DishId FROM NutritionFoodCatalog FOR UPDATE")
            cur.fetchall()
            if digest_catalog_locked(connection) != review["baseline_catalog_sha256"]:
                raise ValueError("Catalog changed before lock")
            existing = {r["dish_id"] for r in review["classifications"] if r["class"] != "E"}
            columns = ["NameVi","ComponentType","PreparationState","ReferenceGrams","MinGrams","MaxGrams","KcalPer100G","ProteinPer100G","CarbsPer100G","FatPer100G","FiberPer100G","IngredientsJson","MealTypesJson","PrepMinutes","ProvenanceJson","Estimated","IsActive","DataVersion"]
            for dish in data["dishes"]:
                m = dish["macros_per_100g"]
                values = [dish["name"],dish["type"],dish["preparation_state"],dish["reference_grams"],dish["min_grams"],dish["max_grams"],dish["calories_per_100g"],m["protein"],m["carbs"],m["fat"],m["fiber"],json.dumps(dish["ingredients"],ensure_ascii=False),json.dumps(dish["meal_types"]),dish.get("prep_minutes"),json.dumps(dish["provenance"],ensure_ascii=False),1,1,dish["data_version"]]
                if dish["dish_id"] in existing:
                    cur.execute("UPDATE NutritionFoodCatalog SET " + ",".join(qid(k)+"=%s" for k in columns) + " WHERE DishId=%s", values + [dish["dish_id"]])
                else:
                    cur.execute("INSERT INTO NutritionFoodCatalog (DishId," + ",".join(qid(k) for k in columns) + ") VALUES (" + ",".join(["%s"]*(len(columns)+1)) + ")", [dish["dish_id"]]+values)
            for identifier in review["removed_ids"]:
                cur.execute("DELETE FROM NutritionFoodCatalog WHERE DishId=%s", (identifier,))
        if not same_catalog(connection, data["dishes"]):
            raise ValueError("Post-migration catalog differs from reviewed seed")
        # Hash other tables in this same transaction; never commit an unexpected write.
        with connection.cursor() as cur:
            for table, old in before.items():
                if table == "nutritionfoodcatalog":
                    continue
                cur.execute("SELECT " + ",".join(qid(c) for c in old["columns"]) + " FROM " + qid(table))
                rows = cur.fetchall()
                if len(rows) != old["count"] or digest_rows(rows) != old["sha256"]:
                    raise ValueError("Protected table changed during migration")
        connection.commit()
        return {"idempotent": False, "updated": 71, "inserted": 6, "deleted": len(review["removed_ids"]), "active": len(data["dishes"]), "frozen_references": references, "other_19_tables_unchanged": True}
    except Exception:
        connection.rollback()
        raise


def digest_catalog_locked(connection):
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM NutritionFoodCatalog")
        return digest_rows(cur.fetchall())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check-db", action="store_true")
    action.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--attestation", type=Path, help="Verified restore/test metadata outside Git; required for main DB")
    args = parser.parse_args()
    data, review = reviewed_data()
    if not args.apply and not args.check_db:
        print(json.dumps({"validate": "PASS", "dishes": len(data["dishes"]), "retired_ids": len(review["removed_ids"]), "database_writes": 0}))
        return
    if args.database != "NutriFitDB" and not re.fullmatch(r"nutrifit_catalog_rebuild_[a-z0-9_]+", args.database or ""):
        raise ValueError("Explicit approved local database required")
    sys.path.insert(0, str(ROOT / "backend"))
    from app.config import Config
    from sqlalchemy.engine import make_url
    import pymysql
    url = make_url(Config.SQLALCHEMY_DATABASE_URI)
    if url.drivername != "mysql+pymysql" or url.host not in ("127.0.0.1", "localhost") or (url.port or 3306) != 3306 or url.database.lower() != "nutrifitdb":
        raise ValueError("Expected configured local MySQL NutriFitDB")
    c = pymysql.connect(host=url.host,port=url.port or 3306,user=url.username,password=url.password or "",database=args.database,charset="utf8mb4",autocommit=False)
    try:
        before = fingerprints(c)
        if len(before) != 20:
            raise ValueError("Expected 20 tables")
        references = dependency_check(c, set(review["removed_ids"]))
        with c.cursor() as cur:
            cur.execute("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND LOWER(TABLE_NAME)='nutritionfoodcatalog'")
            if cur.fetchone()[0] != "InnoDB":
                raise ValueError("Transactional catalog required")
        c.rollback()
        if args.check_db:
            if before["nutritionfoodcatalog"]["sha256"] != review["baseline_catalog_sha256"] and not same_catalog(c, data["dishes"]):
                raise ValueError("Unreviewed catalog state")
            print(json.dumps({"preflight":"PASS","database":args.database,"tables":len(before),"catalog":before["nutritionfoodcatalog"]["count"],"references":references,"writes":0}))
            return
        if not args.backup or args.backup.resolve().is_relative_to(ROOT) or not args.backup.is_file():
            raise ValueError("SQL backup outside repository required")
        raw = args.backup.read_bytes()
        if len(raw) < 10000 or b"CREATE TABLE `nutritionfoodcatalog`" not in raw or b"-- Dump completed on " not in raw[-8192:]:
            raise ValueError("Invalid SQL backup")
        if args.database == "NutriFitDB":
            if not args.attestation or args.attestation.resolve().is_relative_to(ROOT):
                raise ValueError("External verified restore/test attestation required")
            proof = json.loads(args.attestation.read_text())
            if not proof.get("test_pass") or not proof.get("restore_pass") or proof["backup_sha"] != hashlib.sha256(raw).hexdigest() or proof.get("seed_sha") != hashlib.sha256((ROOT/"setup/seeds/nutrition_catalog.json").read_bytes()).hexdigest():
                raise ValueError("Backup, seed or rehearsal not verified")
            if before != proof["baseline"]["data"] and not same_catalog(c, data["dishes"]):
                raise ValueError("Local data changed since verified backup")
        result = apply_catalog(c, data, review)
        print(json.dumps({"database":args.database,"migration":"PASS",**result}))
    finally:
        c.rollback()
        c.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # SQL parameters, private user rows and URLs are never logged.
        print(json.dumps({"result":"FAIL","type":type(error).__name__,"reason":str(error) if type(error) is ValueError else "Database details suppressed; transaction rolled back"}))
        raise SystemExit(1) from None
