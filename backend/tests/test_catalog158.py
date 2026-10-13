"""Current 158-dish seed and Nutrition workflows; SQLite memory, mocked providers."""
import copy, sys, unittest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text
from app.config import Config
from app.extensions import db
from app.ai.gemini_client import AIUnavailable
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.services.food_catalog_service import catalog_by_id, catalog_dishes
from app.services.meal_preferences import validate_preferences, violates, ingredients
from app.services.quick_food_service import QuickFoodService
import test_meal_api as fixtures
import test_meal_v4 as v4fixtures
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"setup"))
from expand_demo_food_catalog import validate


class ExpandedCatalogTests(unittest.TestCase):
    tearDown=fixtures.ApiTests.tearDown
    login_headers=fixtures.ApiTests.login_headers
    generate=fixtures.ApiTests.generate
    choose=fixtures.ApiTests.choose
    v4=v4fixtures.V4Tests.v4
    intake=v4fixtures.V4Tests.intake
    daily=v4fixtures.V4Tests.daily
    swap=v4fixtures.V4Tests.swap

    def setUp(self):
        with patch.object(Config,"SQLALCHEMY_DATABASE_URI","sqlite:///:memory:"):
            fixtures.ApiTests.setUp(self)
        v4fixtures.migration_sqlite()
        assert db.engine.url.drivername=="sqlite" and db.engine.url.database==":memory:"
        db.session.execute(text("DELETE FROM NutritionFoodCatalog"))  # disposable memory only
        self.seed,self.manifest=validate()
        FoodCatalogRepository.insert_missing(self.seed["dishes"],[]);db.session.commit()
        for method in ("compose","rank","alternatives"):
            guard=patch.object(self.app.extensions["nutrifit_gemini"],method,side_effect=AIUnavailable("test_disabled"))
            guard.start();self.addCleanup(guard.stop)

    def test_complete_current_catalog_and_old77_profiles_preserved(self):
        response=self.client.get("/api/nutrition/catalog",headers=self.headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json["data"]),158)
        self.assertEqual(response.json["intake_gram_limits"],{"min":1,"max":2000})
        self.assertEqual(len(self.manifest["new_ids"]),81)
        self.assertFalse(any(d["dish_id"].startswith("usda_") for d in response.json["data"]))
        second=FoodCatalogRepository.insert_missing(self.seed["dishes"],[])
        self.assertEqual(second,{"dishes":0,"menus":0})
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM NutritionLegacyMenus")).scalar(),63)

    def test_search_accents_nonaccents_and_preview_does_not_write(self):
        for q in ("Sườn xào chua ngọt","  SUON  XAO CHUA NGOT "):
            self.assertEqual(QuickFoodService.search(q)["results"][0]["dish_id"],"vn_suon_xao_chua_ngot")
        for grams in (100,150):
            preview=QuickFoodService.preview({"dish_id":"vn_banh_flan","grams":grams})
            self.assertAlmostEqual(preview["totals"]["calories"],catalog_by_id()["vn_banh_flan"]["calories_per_100g"]*grams/100,delta=.1)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM NutritionFoodIntake")).scalar(),0)

    def test_new_ingredients_and_indirect_avoid_are_enforced(self):
        pref=validate_preferences({"avoid":["mực","mắm cá","đậu xanh","bò"]},"lunch")
        self.assertEqual(pref["avoid"],["squid","fermented_fish","mungbean","beef"])
        catalog=catalog_by_id()
        self.assertTrue(violates(catalog["vn_muc_xao_can_tay"],{"avoid":["seafood"]}))
        self.assertTrue(violates(catalog["vn_com_bo_luc_lac"],{"avoid":["beef"]}))
        self.assertTrue(violates(catalog["vn_com_gao_lut"],{"avoid":["rice"]}))
        self.assertFalse(violates(catalog["vn_com_bo_luc_lac"],{"dislikes":["beef"]}))

    def test_fallback_current_ids_cache_refresh_preferences_and_no_consumed(self):
        first=self.v4(preferences={"avoid":["cá","lạc"]})
        self.assertEqual(first.status_code,200,first.json)
        self.assertEqual(first.json["meta"]["source"],"fallback")
        meal=first.json["data"]
        for opt in meal["options"]:
            for part in opt["recipe"]["components"]:
                self.assertIn(part["dish_id"],catalog_by_id())
                self.assertFalse(violates(catalog_by_id()[part["dish_id"]],{"avoid":["fish","peanut"]}))
        self.assertTrue(self.v4(preferences={"avoid":["cá","lạc"]}).json["meta"]["cached"])
        changed=self.v4(forceRefresh=True,revision=meal["revision"],preferences={"avoid":["tỏi"]})
        self.assertEqual(changed.status_code,200,changed.json)
        self.assertEqual(self.v4(forceRefresh=True,revision=meal["revision"]).json["code"],"STALE_MEAL")
        self.assertEqual(self.daily()["consumed"]["calories"],0)

    def test_new_component_replacement_stale_revision_and_planned_only(self):
        meal=self.v4().json["data"];opt=meal["options"][0]
        protein=next(p for p in opt["recipe"]["components"] if p["type"]=="PROTEIN")
        new_id=next(d["dish_id"] for d in self.seed["dishes"] if d["dish_id"] in self.manifest["new_ids"] and d["type"]=="PROTEIN" and d["dish_id"]!=protein["dish_id"])
        dish=catalog_by_id()[new_id]
        response=self.swap(meal,opt,"PROTEIN",new_id,dish["reference_grams"])
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(self.swap(meal,opt,"PROTEIN",new_id,dish["reference_grams"]).json["code"],"STALE_MEAL")
        updated=response.json["data"];self.assertEqual(self.choose(updated,1).status_code,200)
        self.assertEqual(self.daily()["consumed"]["calories"],0)

    def test_new_intake_retry_snapshot_edit_delete_target_unchanged(self):
        target=self.daily()["targets"]["target_kcal"]
        payload={"requestId":"new158_recipe_idempotency","items":[{"dish_id":"vn_banh_flan","grams":100}]}
        first=self.intake(**payload);self.assertEqual(first.status_code,201,first.json)
        retry=self.intake(**payload);self.assertEqual(retry.status_code,200)
        self.assertEqual(first.json["data"]["id"],retry.json["data"]["id"])
        row=first.json["data"];frozen=copy.deepcopy(row["items"][0])
        self.assertEqual(frozen["portion_limits"],{"min":50,"max":180})
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999 WHERE DishId='vn_banh_flan'"));db.session.commit()
        body={"version":row["version"],"confirmed":True,"mealType":"snack","consumedAt":"2026-10-10T09:00:00+07:00","items":[{"dish_id":"vn_banh_flan","grams":50}]}
        changed=self.client.post(f"/api/nutrition/intake/{row['id']}/update",headers=self.headers,json=body)
        self.assertEqual(changed.status_code,200,changed.json)
        self.assertEqual(changed.json["data"]["items"][0]["nutrition_per_100g"],frozen["nutrition_per_100g"])
        self.assertAlmostEqual(changed.json["data"]["totals"]["calories"],row["totals"]["calories"]*.5,delta=.1)
        removed=self.client.post(f"/api/nutrition/intake/{row['id']}/delete",headers=self.headers,json={"version":changed.json["data"]["version"]})
        self.assertEqual(removed.status_code,200)
        self.assertEqual(self.daily()["consumed"]["calories"],0)
        self.assertEqual(self.daily()["targets"]["target_kcal"],target)

    def test_main_roles_remain_distinct_no_redundant_lunch_composition(self):
        from app.services.meal_planner_v4 import candidate_pool
        catalog=catalog_by_id();self.assertEqual(catalog["vn_com_tam_suon_bi_cha"]["type"],"MAIN")
        self.assertIn("vn_com_tam_suon_bi_cha",{d["dish_id"] for d in catalog_dishes("lunch")})
        pool=candidate_pool({},"lunch","maintain","new158",target=800,macro_targets={"protein":50,"carbs":90,"fat":27})
        self.assertTrue(pool);self.assertFalse(any(d["type"]=="MAIN" for d in pool))
