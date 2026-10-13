"""Build a NEW isolated Demo database from reviewed CREATE TABLE definitions only.

Default is validate-only. --apply requires a new nutrifit_demo_clean_* database.
Never executes DROP, source USE/CREATE DATABASE, account seeds or old demo logs.
"""
import argparse
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def schema_statements():
    files = [ROOT/"setup/create_database.sql", ROOT/"setup/migrations/001_nutrition_v4.sql", ROOT/"setup/migrations/002_nutrition_food_catalog.sql"]
    statements = []
    for path in files:
        source = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
        statements.extend(re.findall(r"CREATE (?:TABLE|INDEX)\b.*?;", source, re.S | re.I))
    names = [re.search(r"CREATE TABLE(?: IF NOT EXISTS)? ([A-Za-z0-9_]+)", s, re.I).group(1) for s in statements if re.match("CREATE TABLE",s,re.I)]
    if len(names)!=20 or len(set(names))!=20:
        raise ValueError("Expected exactly twenty distinct tables")
    if any(re.search(r"(?:^|;)\s*(DROP|TRUNCATE|DELETE|ALTER|USE|INSERT|UPDATE)\b", s, re.I) for s in statements):
        raise ValueError("Unexpected statement in fresh schema")
    return statements


def reference_statements():
    """Only public lookup data; never seed accounts, plans, payments or logs."""
    source = re.sub(r"--[^\n]*", "", (ROOT/"setup/create_database.sql").read_text(encoding="utf-8"))
    result = re.findall(r"INSERT INTO (?:WorkoutCategories|Workouts|StreetFoodDish|DishCatalog)\b.*?;", source, re.S | re.I)
    if len(result) != 4 or any(re.search(r"\b(UserId|CreatedBy)\b", row) for row in result):
        raise ValueError("Unexpected public reference seed")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--apply", action="store_true")
    args=parser.parse_args()
    if not re.fullmatch(r"nutrifit_demo_clean_[a-z0-9_]+",args.database):
        parser.error("Only a new dedicated nutrifit_demo_clean_* database is allowed")
    from seed_nutrition_catalog import load_seed
    data=load_seed()
    if len(data["dishes"])!=158 or len(data["legacy_menus"])!=63 or any("usda" in json.dumps(d).lower() for d in data["dishes"]):
        raise ValueError("Expected reviewed158 Vietnamese dishes and63 legacy templates")
    statements=schema_statements()
    if not args.apply:
        print(json.dumps({"mode":"validate_only","database":args.database,"tables":20,"dishes":158,"legacy":63,"writes":0}));return
    from app.config import Config
    from sqlalchemy.engine import make_url
    import pymysql
    url=make_url(Config.SQLALCHEMY_DATABASE_URI)
    if url.drivername!="mysql+pymysql" or url.host not in ("localhost","127.0.0.1"):
        raise ValueError("Only local MySQL is allowed")
    connection=pymysql.connect(host=url.host,port=url.port or 3306,user=url.username,password=url.password or"",charset="utf8mb4",autocommit=True)
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s",(args.database,))
            if cur.fetchone()[0]:raise ValueError("Database already exists; refusing reset or overwrite")
            cur.execute("CREATE DATABASE `"+args.database+"` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            connection.select_db(args.database)
            for statement in statements:
                cur.execute("SELECT DATABASE()")
                if cur.fetchone()[0]!=args.database:raise ValueError("Wrong current database")
                cur.execute(statement)
            for statement in reference_statements():
                cur.execute("SELECT DATABASE()")
                if cur.fetchone()[0]!=args.database:raise ValueError("Wrong reference seed database")
                cur.execute(statement)
    finally:connection.close()
    # DDL auto-commits. On failure leave the isolated partial DB intact for review.
    Config.SQLALCHEMY_DATABASE_URI=url.set(database=args.database).render_as_string(hide_password=False)
    from app import create_app
    from app.extensions import db
    from app.repositories.food_catalog_repository import FoodCatalogRepository
    from sqlalchemy import text
    with create_app().app_context():
        if db.session.execute(text("SELECT DATABASE()")).scalar()!=args.database:raise ValueError("Wrong seed database")
        first=FoodCatalogRepository.insert_missing(data["dishes"],data["legacy_menus"]);db.session.commit()
        repeat=FoodCatalogRepository.insert_missing(data["dishes"],data["legacy_menus"]);db.session.commit()
        if first!={"dishes":158,"menus":63} or repeat!={"dishes":0,"menus":0}:raise ValueError("Seed mismatch")
        print(json.dumps({"database":args.database,"tables":20,"inserted":first,"repeat":repeat,"users_seeded":0}))


if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError) as error:
        print(json.dumps({"result":"FAIL","reason":str(error)}));raise SystemExit(1)
