"""Catalog migration/seed only inside disposable SQLite fixtures."""
import re
import sys
from pathlib import Path
from sqlalchemy import text
from app.extensions import db
from app.repositories.food_catalog_repository import FoodCatalogRepository

SETUP = Path(__file__).resolve().parents[2] / "setup"
sys.path.insert(0, str(SETUP))
from seed_nutrition_catalog import load_seed as load_runtime_seed


def load_seed():
    """Frozen pre-rebuild profiles for historical algorithm regression only."""
    data = load_runtime_seed(Path(__file__).parent / "fixtures/pre_rebuild_catalog.json")
    for dish in data["dishes"]:
        dish["provenance"]["ingredients_complete"] = True  # controlled fixture tags
    return data


def install_catalog(full=False):
    assert db.engine.url.drivername == "sqlite" and db.engine.url.database == ":memory:"
    source = (SETUP / "migrations/002_nutrition_food_catalog.sql").read_text(encoding="utf-8")
    assert not re.search(r"(?:^|;)\s*(DROP|TRUNCATE|DELETE|ALTER|USE|INSERT)\b", re.sub(r"--[^\n]*", "", source), re.I)
    for statement in re.findall(r"CREATE (?:TABLE|INDEX).*?;", source, re.S):
        db.session.execute(text(re.sub(r"\) ENGINE=.*?;", ");", statement)))
    data = load_seed()
    # Baseline contract cases retain exactly their original 24 food profiles.
    # New catalog cases import the complete sourced dataset separately.
    FoodCatalogRepository.insert_missing(data["dishes"] if full else data["dishes"][:24], data["legacy_menus"])
    db.session.commit()
