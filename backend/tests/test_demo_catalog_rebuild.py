"""Current Vietnamese catalog, SQLite-memory workflows and frozen-history safety."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text
from app.extensions import db
from app.ai.gemini_client import AIUnavailable
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.services.food_catalog_service import catalog_by_id, catalog_dishes, component, snapshot_component
from app.services.meal_preferences import validate_preferences, violates, ingredients
from app.services.meal_planner_v4 import MealPlannerV4, eligible, score
from app.services.quick_food_service import QuickFoodService
from app.services.module_errors import ModuleError
import test_meal_api as fixtures
import test_meal_v4 as v4fixtures
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "setup"))
from rebuild_demo_food_catalog import reviewed_data


class RecipeDataTests(unittest.TestCase):
    def test_complete_reproducible_seed_has_no_retired_source(self):
        data, review = reviewed_data()
        self.assertEqual(len(data["dishes"]), 77)
        self.assertEqual(len(data["legacy_menus"]), 63)
        self.assertEqual(len(review["classifications"]), 147)  # all 141 + six new
        self.assertEqual(len(review["removed_ids"]), 70)
        self.assertNotIn("usda", json.dumps(data["dishes"]).lower())
        self.assertTrue(all(d["estimated"] for d in data["dishes"]))

    def test_three_sweet_potato_ids_become_one_active_representative(self):
        data, _ = reviewed_data()
        self.assertEqual([d["dish_id"] for d in data["dishes"] if d["name"] == "Khoai lang hấp"], ["sweet_potato"])

    def test_main_is_complete_meal_and_all_meal_eligibility_is_explicit(self):
        data, _ = reviewed_data()
        dishes = {d["dish_id"]: d for d in data["dishes"]}
        for identifier in ("pho_beef", "pho_chicken", "vn_bun_bo_hue", "vn_bun_rieu_cua"):
            self.assertEqual(dishes[identifier]["type"], "MAIN")
            self.assertEqual(set(dishes[identifier]["meal_types"]), {"breakfast", "lunch", "dinner"})
            self.assertGreater(dishes[identifier]["reference_grams"], 300)

    def test_early_portion_only_snapshot_can_scale_without_live_catalog(self):
        part = {"dish_id":"retired_fixture", "type":"MAIN", "name":"Bữa cũ", "grams":200,
            "calories":300, "macros":{"protein":10,"carbs":45,"fat":8,"fiber":2}}
        changed = snapshot_component(part, 100)
        self.assertEqual(changed["calories"], 150)
        self.assertEqual(changed["macros"], {"protein":5,"carbs":22.5,"fat":4,"fiber":1})
        self.assertEqual(part["grams"], 200)

    def test_known_fiber_is_not_fabricated_from_missing_sources(self):
        data, _ = reviewed_data()
        self.assertTrue(all(d["macros_per_100g"]["fiber"] is None for d in data["dishes"]))


class CatalogWorkflowTests(unittest.TestCase):
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    generate = fixtures.ApiTests.generate
    choose = fixtures.ApiTests.choose
    v4 = v4fixtures.V4Tests.v4
    intake = v4fixtures.V4Tests.intake
    daily = v4fixtures.V4Tests.daily
    swap = v4fixtures.V4Tests.swap

    def setUp(self):
        from app.config import Config
        with patch.object(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"):
            fixtures.ApiTests.setUp(self)
        v4fixtures.migration_sqlite()
        self.assertEqual(db.engine.url.database, ":memory:")
        db.session.execute(text("DELETE FROM NutritionFoodCatalog"))  # disposable fixture only
        self.seed, self.review = reviewed_data()
        FoodCatalogRepository.insert_missing(self.seed["dishes"], [])
        db.session.commit()
        for method in ("compose", "alternatives", "rank"):
            guard = patch.object(self.app.extensions["nutrifit_gemini"], method, side_effect=AIUnavailable("test_disabled"))
            guard.start()
            self.addCleanup(guard.stop)

    def test_catalog_full_free_session_and_cors(self):
        self.assertEqual(self.client.get("/api/nutrition/catalog", headers={"X-User-Id": "1"}).status_code, 401)
        r = self.client.get("/api/nutrition/catalog", headers={**self.headers, "Origin": "http://127.0.0.1:5500"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json["data"]), 77)
        self.assertEqual(r.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(len(catalog_dishes("lunch")), 77)

    def test_search_vietnamese_accents_case_spacing_and_preview(self):
        for name in ("Rau muống xào tỏi", "  RAU  MUONG XAO TOI "):
            data = QuickFoodService.search(name)
            self.assertIn("vn_rau_muong_xao_toi", [d["dish_id"] for d in data["results"]])
        result = QuickFoodService.preview({"dish_id": "vn_thit_kho_trung", "grams": 100})
        self.assertAlmostEqual(result["totals"]["calories"], catalog_by_id()["vn_thit_kho_trung"]["calories_per_100g"], places=1)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM NutritionFoodIntake")).scalar(), 0)

    def test_unknown_and_retired_ids_cannot_be_added(self):
        for identifier in ("usda_169704", "breakfast_main_d2_o3", "oats_yogurt"):
            r = self.intake(items=[{"dish_id": identifier, "grams": 100}])
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.json["code"], "UNKNOWN_DISH")
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_canonical_synonyms_multi_ingredient_and_unknown_are_explicit(self):
        for terms in (["thịt lợn", "lạc", "tỏi"], [" THIT HEO ", "dau phong", "TOI"]):
            p = validate_preferences({"avoid": terms}, "lunch")
            self.assertEqual(p["avoid"], ["pork", "peanut", "garlic"])
        with self.assertRaises(ModuleError) as caught:
            validate_preferences({"avoid": ["nguyên liệu không có", "tỏi"]}, "lunch")
        self.assertEqual(caught.exception.code, "UNSUPPORTED_PREFERENCE")
        self.assertEqual(validate_preferences({"avoid":["nghệ"]}, "lunch")["avoid"], ["turmeric"])
        self.assertEqual(validate_preferences({"avoid":["mè", "me chua"]}, "lunch")["avoid"], ["sesame", "tamarind"])
        with self.assertRaises(ModuleError):
            validate_preferences({"avoid":["me"]}, "lunch")

    def test_sauces_indirect_ingredients_are_not_allergy_safe(self):
        dishes = catalog_by_id()
        self.assertTrue(violates(dishes["vn_dau_phu_sot_ca_chua"], {"avoid": ["fish"]}))
        self.assertTrue(violates(dishes["vn_dau_phu_kho_nam"], {"avoid": ["wheat"]}))
        self.assertTrue(violates(dishes["vn_muop_xao_dau_phong"], {"avoid": ["peanut"]}))
        incomplete = copy.deepcopy(dishes["chicken"])
        incomplete["provenance"].pop("ingredients_complete")
        self.assertTrue(violates(incomplete, {"avoid": ["peanut"]}))
        self.assertFalse(violates(incomplete, {"dislikes": ["peanut"]}))

    def test_dislikes_and_preferences_stay_soft_but_avoid_is_hard(self):
        dish = catalog_by_id()["vn_muop_xao_dau_phong"]
        self.assertFalse(violates(dish, {"dislikes": ["peanut"], "prefer": ["garlic"]}))
        self.assertGreater(score(dish, "maintain", {"prefer": ["garlic"]}), score(dish, "maintain", {}))
        self.assertLess(score(dish, "maintain", {"dislikes": ["peanut"]}), score(dish, "maintain", {}))
        self.assertTrue(violates(dish, {"avoid": ["peanut"]}))
        self.assertTrue(all(not {"fish", "seafood", "peanut"} & ingredients(d) for d in eligible({"avoid": ["fish", "peanut"]}, "lunch")))

    def test_generate_refresh_and_avoid_use_current_catalog(self):
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=AIUnavailable("test_disabled")):
            r = self.v4(preferences={"avoid": ["cá", "lạc"]})
            self.assertEqual(r.status_code, 200, r.json)
            first = r.json["data"]
            self.assertEqual(r.json["meta"]["source"], "fallback")
            for o in first["options"]:
                for p in o["recipe"]["components"]:
                    d = catalog_by_id()[p["dish_id"]]
                    self.assertFalse(violates(d, {"avoid": ["fish", "peanut"]}))
                    self.assertLessEqual(p["grams"], d["max_grams"])
                    self.assertGreaterEqual(p["grams"], d["min_grams"])
            self.assertEqual(self.v4(preferences={"avoid":["cá","lạc"]}).json["meta"]["cached"], True)
            self.assertEqual(self.v4(preferences={"avoid":["tỏi"]}).status_code, 409)
            changed = self.v4(forceRefresh=True, revision=first["revision"], preferences={"avoid":["tỏi"]})
            self.assertEqual(changed.status_code, 200, changed.json)
            self.assertNotEqual(changed.json["data"]["revision"], first["revision"])
            self.assertEqual(self.v4(forceRefresh=True, revision=first["revision"]).json["code"], "STALE_MEAL")
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_replace_enforces_saved_avoid_role_revision_and_planned_only(self):
        r = self.v4(preferences={"avoid":["cá"]});self.assertEqual(r.status_code, 200, r.json)
        meal = r.json["data"];opt = meal["options"][0]
        bad = self.swap(meal,opt,"PROTEIN","vn_thit_kho_trung",200)
        self.assertEqual(bad.json["code"], "AVOID_CONFLICT")
        protein = next(p for p in opt["recipe"]["components"] if p["type"] == "PROTEIN")
        choices = [d for d in catalog_dishes("lunch") if d["type"] == "PROTEIN" and d["dish_id"] != protein["dish_id"] and not violates(d,{"avoid":["fish"]})]
        d = choices[0];result = self.swap(meal,opt,"PROTEIN",d["dish_id"],d["reference_grams"])
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(self.swap(meal,opt,"PROTEIN",d["dish_id"],d["reference_grams"]).json["code"], "STALE_MEAL")
        self.assertEqual(self.daily()["consumed"]["calories"], 0)
        self.assertEqual(result.json["data"]["options"][0]["recipe"]["change"], opt["recipe"]["change"] + 1)

    def test_revised_cached_plan_requires_refresh_no_silent_history_edit(self):
        meal = self.v4().json["data"]
        before = self.client.get("/api/meals/history",headers=self.headers).json["history"]
        identifier = meal["options"][0]["recipe"]["components"][0]["dish_id"]
        db.session.execute(text("UPDATE NutritionFoodCatalog SET DataVersion=DataVersion+1 WHERE DishId=:id"), {"id":identifier});db.session.commit()
        self.assertEqual(self.v4().json["code"], "CATALOG_REFRESH_REQUIRED")
        self.assertEqual(self.choose(meal,1).json["code"], "CATALOG_REFRESH_REQUIRED")
        self.assertTrue(self.client.get("/api/meals/today",headers=self.headers).json["todayMeals"]["lunch"]["catalog_refresh_required"])
        self.assertEqual(self.client.get("/api/meals/history",headers=self.headers).json["history"], before)
        self.assertEqual(self.choose(meal,None).status_code, 200)
        self.assertEqual(self.v4(forceRefresh=True,revision=meal["revision"]).status_code, 200)

    def test_catalog_change_during_generation_cannot_persist_retired_components(self):
        from app.repositories.meal_repository import MealRepository
        from app.services.meal_service import today
        from app.services.meal_planner_v4 import option_from_recipe
        meal = self.v4().json["data"]
        options = [option_from_recipe(copy.deepcopy(o["recipe"]), o["title"], "Fixture", "fallback") for o in meal["options"]]
        part = options[0]["recipe"]["components"][0]
        db.session.execute(text("DELETE FROM NutritionFoodCatalog WHERE DishId=:id"), {"id":part["dish_id"]});db.session.commit()
        with self.assertRaises(ModuleError) as caught:
            MealRepository.store(1,today(),"lunch",options,meal["revision"],True)
        self.assertEqual(caught.exception.code,"CATALOG_REFRESH_REQUIRED")
        db.session.rollback()
        self.assertEqual(MealRepository.load(1,today(),"lunch")["revision"],meal["revision"])

    def test_deleted_catalog_keeps_frozen_intake_edit_and_ownership(self):
        saved = self.intake(items=[{"dish_id":"vn_du_du_chin","grams":180}]).json["data"]
        frozen = copy.deepcopy(saved["items"][0])
        db.session.execute(text("DELETE FROM NutritionFoodCatalog WHERE DishId='vn_du_du_chin'"));db.session.commit()
        body={"version":saved["version"],"confirmed":True,"mealType":"snack","consumedAt":"2026-10-10T08:00:00+07:00","items":[{"dish_id":"vn_du_du_chin","grams":90}]}
        self.assertEqual(self.client.post(f"/api/nutrition/intake/{saved['id']}/update",headers=self.other_headers,json=body).status_code,404)
        r=self.client.post(f"/api/nutrition/intake/{saved['id']}/update",headers=self.headers,json=body)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(r.json["data"]["items"][0]["nutrition_per_100g"],frozen["nutrition_per_100g"])
        self.assertAlmostEqual(r.json["data"]["totals"]["calories"],saved["totals"]["calories"]*.5,delta=.1)
        self.assertEqual(self.intake(items=[{"dish_id":"vn_du_du_chin","grams":90}]).json["code"],"UNKNOWN_DISH")
        removed=self.client.post(f"/api/nutrition/intake/{saved['id']}/delete",headers=self.headers,json={"version":r.json["data"]["version"]})
        self.assertEqual(removed.status_code,200)
        self.assertEqual(self.daily()["consumed"]["calories"],0)

    def test_confirm_retry_counts_consumed_once_without_changing_target(self):
        target = self.daily()["targets"]["target_kcal"]
        first = self.intake(requestId="reference_recipe_retry",items=[{"dish_id":"vn_canh_ca_chua_trung","grams":240}])
        self.assertEqual(first.status_code,201,first.json)
        retry = self.intake(requestId="reference_recipe_retry",items=[{"dish_id":"vn_canh_ca_chua_trung","grams":240}])
        self.assertEqual(retry.status_code,200)
        self.assertEqual(first.json["data"]["id"],retry.json["data"]["id"])
        self.assertEqual(self.daily()["consumed"]["calories"],first.json["data"]["totals"]["calories"])
        self.assertEqual(self.daily()["targets"]["target_kcal"],target)
        self.assertEqual(self.client.get("/api/nutrition/summary",headers=self.headers).json["data"]["planned"]["calories"],0)
