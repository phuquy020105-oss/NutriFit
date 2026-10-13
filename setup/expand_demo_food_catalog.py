"""Insert-only Vietnamese expansion; default validate-only, never alters existing records."""
import argparse, hashlib, json, re, sys
from pathlib import Path
from seed_nutrition_catalog import load_seed, folded_name
from rebuild_demo_food_catalog import fingerprints, digest_rows as legacy_digest_rows, qid, reviewed_data
from collections.abc import Mapping
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"setup/seeds/demo_catalog150_batch.json"
SEED=ROOT/"setup/seeds/nutrition_catalog.json"
BASE=ROOT/"setup/seeds/demo_catalog_rebuild_seed.json"


def digest_rows(rows, columns=None):
    """Unwrap driver containers before hashing; preserve the verified backup hash format.

    SELECTs use explicit schema column order. Record order is ignored by the shared
    digest; duplicate records remain significant. Decimal/date/time values retain
    their DB representation; NULL and Unicode remain native JSON values.
    """
    values = []
    for row in rows:
        if isinstance(row, Mapping):
            if columns is None:
                raise ValueError("Explicit column order required for mapping cursor")
            row = tuple(row[column] for column in columns)
        else:
            row = tuple(row)  # SQLAlchemy Row must not fall through json default=str.
        values.append(tuple(bytes(v) if isinstance(v, (bytearray, memoryview)) else v for v in row))
    return legacy_digest_rows(values)


def validate():
    data,manifest=reviewed_data(SEED,MANIFEST)
    base=load_seed(BASE)
    expected={d["dish_id"]:d for d in data["dishes"]}
    if data["legacy_menus"]!=base["legacy_menus"] or len(expected)<150:
        raise ValueError("Legacy changed or catalog below target")
    if set(manifest["baseline_ids"])!={d["dish_id"] for d in base["dishes"]} or set(manifest["new_ids"])!=set(expected)-set(manifest["baseline_ids"]):
        raise ValueError("Batch IDs differ from source")
    for d in base["dishes"]:
        if expected[d["dish_id"]]!=d:raise ValueError("Existing 77 dishes changed")
    signatures=set()
    for d in data["dishes"]:
        recipe=d["provenance"]["recipe"]
        signature=tuple(sorted((i["ingredient"],i["state"],round(i["retained_grams"]/recipe["finished_edible_grams"],5)) for i in recipe["ingredients"]))
        if signature in signatures:raise ValueError("Equivalent recipe duplicate")
        signatures.add(signature)
        if not d["ingredients"]:raise ValueError("Empty ingredient tags")
    return data,manifest


def review_database(repository,data,manifest):
    rows=repository.dishes(active=False)
    expected={d["dish_id"]:d for d in data["dishes"]};existing={d["dish_id"]:d for d in rows}
    if not set(manifest["baseline_ids"])<=set(existing) or set(existing)-set(expected):raise ValueError("Unexpected catalog IDs")
    for ident,dish in existing.items():
        if any(dish.get(k)!=v for k,v in expected[ident].items()):raise ValueError("Existing ID differs from reviewed data")
    names={folded_name(d["name"]) for d in rows}
    pending=[d for d in data["dishes"] if d["dish_id"] not in existing]
    if any(folded_name(d["name"]) in names for d in pending):raise ValueError("Existing name collision")
    return pending


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group();action.add_argument("--check-db",action="store_true");action.add_argument("--apply",action="store_true")
    parser.add_argument("--database");parser.add_argument("--backup",type=Path);parser.add_argument("--attestation",type=Path)
    args=parser.parse_args();data,manifest=validate()
    if not args.check_db and not args.apply:
        print(json.dumps({"validate":"PASS","baseline":77,"new":len(manifest["new_ids"]),"total":len(data["dishes"]),"writes":0}));return
    if args.database!="NutriFitDB" and not re.fullmatch(r"nutrifit_catalog150_[a-z0-9_]+",args.database or ""):
        raise ValueError("Approved explicit database required")
    sys.path.insert(0,str(ROOT/"backend"))
    from app.config import Config
    from app import create_app
    from app.extensions import db
    from app.repositories.food_catalog_repository import FoodCatalogRepository
    from sqlalchemy.engine import make_url
    from sqlalchemy import text
    import pymysql
    url=make_url(Config.SQLALCHEMY_DATABASE_URI)
    if url.drivername!="mysql+pymysql" or url.host not in ("127.0.0.1","localhost") or (url.port or 3306)!=3306 or url.database.lower()!="nutrifitdb":raise ValueError("Local MySQL required")
    c=pymysql.connect(host=url.host,port=url.port or 3306,user=url.username,password=url.password or "",database=args.database,charset="utf8mb4",autocommit=False)
    try:before=fingerprints(c)
    finally:c.close()
    if len(before)!=20 or before["nutritionlegacymenus"]["count"]!=63:raise ValueError("Unexpected table/template count")
    Config.SQLALCHEMY_DATABASE_URI=url.set(database=args.database).render_as_string(hide_password=False)
    app=create_app()
    with app.app_context():
        db.session.execute(text("START TRANSACTION READ ONLY"))
        if str(db.session.execute(text("SELECT DATABASE()")).scalar()).casefold()!=args.database.casefold():raise ValueError("Wrong current database")
        pending=review_database(FoodCatalogRepository,data,manifest)
        db.session.rollback()
        if args.check_db:
            print(json.dumps({"preflight":"PASS","database":args.database,"active_before":before["nutritionfoodcatalog"]["count"],"insert_pending":len(pending),"writes":0}));return
        if not args.backup or args.backup.resolve().is_relative_to(ROOT) or not args.backup.is_file():raise ValueError("External SQL backup required")
        raw=args.backup.read_bytes()
        if len(raw)<10000 or b"-- Dump completed on " not in raw[-8192:]:raise ValueError("Invalid backup")
        if args.database=="NutriFitDB":
            if not args.attestation or args.attestation.resolve().is_relative_to(ROOT):raise ValueError("External restore/test proof required")
            proof=json.loads(args.attestation.read_text())
            if not proof.get("restore_pass") or not proof.get("test_pass") or proof["backup_sha"]!=hashlib.sha256(raw).hexdigest() or proof["seed_sha"]!=hashlib.sha256(SEED.read_bytes()).hexdigest():raise ValueError("Rehearsal not verified")
            if pending and before!=proof["before"]:raise ValueError("Local data changed since backup")
        if not pending:
            print(json.dumps({"migration":"PASS","database":args.database,"inserted":0,"idempotent":True,"active":len(data["dishes"])}));return
        try:
            # Lock catalog rows before rechecking pending IDs; no existing row is updated.
            db.session.execute(text("SELECT DishId FROM NutritionFoodCatalog FOR UPDATE")).all()
            pending=review_database(FoodCatalogRepository,data,manifest)
            engine=db.session.execute(text("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND LOWER(TABLE_NAME)='nutritionfoodcatalog'")).scalar()
            if engine!="InnoDB":raise ValueError("Transactional catalog required")
            inserted=FoodCatalogRepository.insert_missing(pending,[])
            if inserted["dishes"]!=len(pending) or review_database(FoodCatalogRepository,data,manifest):raise ValueError("Inserted data mismatch")
            for table,old in before.items():
                if table=="nutritionfoodcatalog":
                    placeholders=",".join(":id"+str(i) for i in range(len(manifest["baseline_ids"])))
                    params={"id"+str(i):v for i,v in enumerate(manifest["baseline_ids"])}
                    rows=db.session.execute(text("SELECT "+",".join(qid(c) for c in old["columns"])+" FROM NutritionFoodCatalog WHERE DishId IN ("+placeholders+")"),params).all()
                    # Original full rows, including timestamps/DataVersion, must stay byte-equivalent.
                    if old["count"]==77 and (len(rows)!=77 or digest_rows(rows)!=old["sha256"]):raise ValueError("Existing catalog rows changed")
                else:
                    rows=db.session.execute(text("SELECT "+",".join(qid(c) for c in old["columns"])+" FROM "+qid(table))).all()
                    if len(rows)!=old["count"] or digest_rows(rows)!=old["sha256"]:raise ValueError("Protected table changed")
            db.session.commit()
            print(json.dumps({"migration":"PASS","database":args.database,"inserted":inserted["dishes"],"active":len(data["dishes"]),"old_77_and_other_19_tables_unchanged":True}))
        except Exception:
            db.session.rollback();raise
        finally:db.session.remove();db.engine.dispose()

if __name__=="__main__":
    try:main()
    except Exception as e:
        print(json.dumps({"result":"FAIL","type":type(e).__name__,"reason":str(e) if type(e)is ValueError else "Details suppressed; transaction rolled back"}));raise SystemExit(1) from None
