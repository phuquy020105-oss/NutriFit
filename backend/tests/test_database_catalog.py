"""Database-driven catalog contracts in SQLite memory; MySQL/live AI require approval."""
import copy
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text
from app.extensions import db
from app.ai.gemini_client import AIUnavailable
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.services.food_catalog_service import catalog_dishes, catalog_by_id, component, totals, templates
from app.services.meal_planner_v4 import MealPlannerV4, candidate_pool
from app.services.module_errors import ModuleError
from catalog_fixture import load_seed
import test_meal_api as fixtures
import test_meal_v4 as v4fixtures


class DatabaseCatalogTests(unittest.TestCase):
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    generate = fixtures.ApiTests.generate
    choose = fixtures.ApiTests.choose
    v4 = v4fixtures.V4Tests.v4
    intake = v4fixtures.V4Tests.intake
    daily = v4fixtures.V4Tests.daily
    swap = v4fixtures.V4Tests.swap

    def setUp(self):
        fixtures.ApiTests.setUp(self)
        v4fixtures.migration_sqlite()
        self.seed = load_seed()
        FoodCatalogRepository.insert_missing(self.seed["dishes"], self.seed["legacy_menus"])
        db.session.commit()

    @staticmethod
    def raw(candidates, meal_type, target, focus, preferences=None, macro_targets=None):
        options = MealPlannerV4.fallback(candidates, meal_type, target, focus, preferences or {}, macro_targets=macro_targets)
        return {"choices": [{"title": "Thực đơn Việt " + str(i), "reason": "Theo mục tiêu và nhóm thực phẩm.",
            "components": [{key: p[key] for key in ("type", "dish_id", "grams")} for p in option["recipe"]["components"]]}
            for i, option in enumerate(options)]}

    def test_full_catalog_is_read_from_database(self):
        response = self.client.get("/api/nutrition/catalog", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["catalog_source"], "database")
        self.assertEqual(len(body["data"]), 102)
        db.session.execute(text("UPDATE NutritionFoodCatalog SET NameVi='Tên cập nhật từ DB' WHERE DishId='rice'"))
        db.session.commit()
        self.assertEqual(catalog_by_id()["rice"]["name"], "Tên cập nhật từ DB")

    def macro_pool_fixture(self):
        prototype = catalog_by_id()["rice"]
        def dish(identifier, role, kcal, carbs, protein, fat):
            d = copy.deepcopy(prototype)
            d.update(dish_id=identifier, type=role, ingredients=[], reference_grams=100,
                min_grams=50, max_grams=200, calories_per_100g=kcal,
                macros_per_100g={"carbs": carbs, "protein": protein, "fat": fat, "fiber": 0})
            return d
        rows = [dish("starch", "CARB", 350, 85, 0, 0), dish("greens", "VEGGIE", 50, 10, 3, 0)]
        rows += [dish("lean" + str(i), "PROTEIN", 200, 0, 40, 4) for i in range(3)]
        rows += [dish("fruit" + str(i), "DESSERT", 100, 25, 0, 0) for i in range(9)]
        rows += [dish("complement", "DESSERT", 135, 0, 0, 15), dish("too_rich", "DESSERT", 450, 0, 0, 50)]
        return rows

    def test_v41_pool_preserves_macro_complement_not_just_highest_fat(self):
        rows = self.macro_pool_fixture()
        with patch("app.services.meal_planner_v4.eligible", return_value=rows):
            pool = candidate_pool({}, "lunch", "lose", "macro-pool", target=891,
                                  macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 30})
        self.assertIn("complement", [d["dish_id"] for d in pool])
        ids = [d["dish_id"] for d in pool]
        self.assertLess(ids.index("complement"), ids.index("too_rich"))

    def test_v41_pool_changes_with_macro_budget_deterministically(self):
        rows = self.macro_pool_fixture()
        with patch("app.services.meal_planner_v4.eligible", return_value=rows):
            high = candidate_pool({}, "lunch", "lose", "macro-pool", target=891, macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 30})
            low = candidate_pool({}, "lunch", "lose", "macro-pool", target=891, macro_targets={"protein": 55.7, "carbs": 160, "fat": 0})
            again = candidate_pool({}, "lunch", "lose", "macro-pool", target=891, macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 30})
        self.assertNotEqual([d["dish_id"] for d in high], [d["dish_id"] for d in low])
        self.assertEqual(high, again)

    def test_v41_pool_keeps_eight_role_limit_avoid_meal_and_focus(self):
        from collections import Counter
        rankings = []
        for meal in ("breakfast", "lunch", "dinner"):
            for focus in ("lose", "maintain", "gain", "muscle_gain"):
                pool = candidate_pool({"avoid": ["fish"]}, meal, focus, "macro-contract", target=891,
                    macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 29.7})
                self.assertTrue(all(n <= 8 for n in Counter(d["type"] for d in pool).values()))
                self.assertTrue(all(meal in d["meal_types"] and not {"fish", "seafood"} & set(d["ingredients"]) for d in pool))
                primary = "MAIN" if meal == "breakfast" else "PROTEIN"
                self.assertGreaterEqual(sum(d["type"] == primary for d in pool), 3)
                rankings.append(tuple(d["dish_id"] for d in pool))
        self.assertGreater(len(set(rankings)), 3)

    def test_v41_macro_reservations_respect_prefer_and_dislikes(self):
        pool = candidate_pool({"avoid": ["fish"], "prefer": ["chicken"], "dislikes": ["beef"]},
            "lunch", "maintain", "preferences", target=891, macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 29.7})
        proteins = [d for d in pool if d["type"] == "PROTEIN"]
        self.assertGreaterEqual(len(proteins), 3)
        self.assertTrue(any("chicken" in d["ingredients"] for d in proteins))
        self.assertTrue(any("chicken" not in d["ingredients"] for d in proteins), "Soft preference must not exclude every alternative")

    def test_v41_macro_search_never_reintroduces_avoided_helper(self):
        pool = candidate_pool({"avoid": ["fish", "egg", "milk", "soy", "beef"]}, "lunch", "gain", "hard-avoid",
            target=891, macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 60})
        self.assertTrue(pool)
        self.assertTrue(all(not {"fish", "seafood", "egg", "milk", "soy", "beef"} & set(d["ingredients"]) for d in pool))

    def test_seed_idempotent_and_does_not_overwrite_manual_edits(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET IsActive=0,NameVi='Giữ chỉnh sửa' WHERE DishId='rice'"))
        db.session.commit()
        result = FoodCatalogRepository.insert_missing(self.seed["dishes"], self.seed["legacy_menus"])
        db.session.commit()
        self.assertEqual(result, {"dishes": 0, "menus": 0})
        row = db.session.execute(text("SELECT NameVi,IsActive FROM NutritionFoodCatalog WHERE DishId='rice'")).one()
        self.assertEqual(tuple(row), ("Giữ chỉnh sửa", 0))
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM NutritionFoodCatalog")).scalar(), 102)

    def test_seed_has_stable_ids_sources_and_explicit_preparation_states(self):
        records = self.seed["dishes"]
        self.assertEqual(len({d["dish_id"] for d in records}), len(records))
        self.assertEqual(len([d for d in records if d["dish_id"].startswith("usda_")]), 63)
        self.assertTrue(all(d["provenance"].get("source") for d in records))
        self.assertTrue(all(d["preparation_state"] != "raw" for d in records))
        self.assertEqual({m: len(templates(m)) for m in ("breakfast", "lunch", "dinner")},
                         {"breakfast": 21, "lunch": 21, "dinner": 21})

    def test_missing_catalog_returns_safe_error_without_creating_tables(self):
        db.session.execute(text("DROP TABLE NutritionFoodCatalog"))  # disposable SQLite only
        db.session.commit()
        response = self.client.get("/api/nutrition/catalog", headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "FOOD_CATALOG_MIGRATION_REQUIRED")
        self.assertEqual(self.client.get("/api/meals/today", headers=self.headers).status_code, 200)
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_inactive_missing_macros_and_raw_meat_are_not_recommended(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET IsActive=0 WHERE DishId='chicken'"))
        db.session.execute(text("UPDATE NutritionFoodCatalog SET ProteinPer100G=NULL WHERE DishId='beef'"))
        db.session.execute(text("UPDATE NutritionFoodCatalog SET PreparationState='raw' WHERE DishId='pork'"))
        db.session.commit()
        ids = {d["dish_id"] for d in catalog_dishes("lunch")}
        self.assertTrue({"chicken", "beef", "pork"}.isdisjoint(ids))

    def test_unknown_fiber_is_exposed_in_snapshots_as_incomplete(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET FiberPer100G=NULL WHERE DishId='rice'"))
        db.session.commit()
        self.assertIsNone(catalog_by_id()["rice"]["macros_per_100g"]["fiber"])
        row = self.intake().get_json()["data"]
        self.assertFalse(row["fiber_complete"])
        self.assertIsNone(row["items"][0]["nutrition_per_100g"]["fiber"])
        self.assertFalse(self.daily()["fiber_complete"])

    def test_unknown_preparation_time_does_not_break_easy_breakfast(self):
        body = self.v4("breakfast", preferences={"preferEasy": True}).get_json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["data"]["options"]), 3)
        limited = candidate_pool({"maxPrepMinutes": 20}, "breakfast", "maintain", "demo")
        self.assertTrue(limited)
        self.assertEqual([d["dish_id"] for d in limited], [d["dish_id"] for d in candidate_pool({}, "breakfast", "maintain", "demo")])

    def test_malformed_catalog_tags_fail_safely(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET IngredientsJson='[{}]' WHERE DishId='rice'"))
        db.session.commit()
        response = self.client.get("/api/nutrition/catalog", headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "INVALID_CATALOG")

    def test_invalid_catalog_portions_and_fiber_are_excluded(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET MinGrams=400,MaxGrams=100 WHERE DishId='rice'"))
        db.session.execute(text("UPDATE NutritionFoodCatalog SET FiberPer100G=-1 WHERE DishId='beef'"))
        db.session.commit()
        self.assertTrue({"rice", "beef"}.isdisjoint(catalog_by_id()))

    def test_component_energy_uses_the_stored_rounded_portion(self):
        dish = catalog_by_id()["usda_169704"]
        part = component(dish["dish_id"], 123.45678, actual=True)
        self.assertEqual(part["grams"], 123.46)
        self.assertEqual(part["calories"], round(dish["calories_per_100g"] * part["grams"] / 100, 4))

    def test_meal_type_filter_and_prompt_size_preserve_required_groups(self):
        for meal in ("breakfast", "lunch", "dinner"):
            candidates = candidate_pool({}, meal, "maintain", "demo")
            self.assertLessEqual(len(candidates), 40)
            self.assertTrue(all(meal in d["meal_types"] for d in candidates))
            groups = {d["type"] for d in candidates}
            self.assertTrue(({"MAIN"} if meal == "breakfast" else {"CARB", "PROTEIN", "VEGGIE"}) <= groups)

    def test_seafood_avoidance_also_excludes_usda_fish(self):
        candidates = candidate_pool({"avoid": ["seafood"]}, "lunch", "maintain", "demo")
        self.assertTrue(candidates)
        self.assertTrue(all(not {"fish", "seafood"} & set(d["ingredients"]) for d in candidates))
        body = self.v4(preferences={"avoid": ["hải sản"]}).get_json()
        self.assertTrue(body["success"])
        by_id = catalog_by_id()
        self.assertTrue(all(not {"fish", "seafood"} & set(by_id[part["dish_id"]]["ingredients"])
            for option in body["data"]["options"] for part in option["components"]))

    def test_gemini_receives_only_active_eligible_database_candidates(self):
        def compose(candidates, meal, target, uid, focus, macros, context):
            self.assertLessEqual(len(candidates), 40)
            self.assertTrue(all(not {"fish", "seafood"} & set(d["ingredients"]) for d in candidates))
            self.assertEqual(context["preferences"]["avoid"], ["fish"])
            self.assertIn("protein", context["remaining"])
            return self.raw(candidates, meal, target, focus, context["preferences"])
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=compose):
            body = self.v4(preferences={"avoid": ["cá"]}).get_json()
        self.assertEqual(body["meta"]["source"], "gemini")

    def test_unknown_ai_id_falls_back_without_invented_food(self):
        def compose(candidates, meal, target, uid, focus, *args):
            raw = self.raw(candidates, meal, target, focus)
            raw["choices"][0]["components"][0]["dish_id"] = "not_in_database"
            return raw
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=compose):
            body = self.v4().get_json()
        self.assertEqual(body["meta"]["source"], "fallback")
        self.assertEqual(body["meta"]["fallback_reason"], "invalid_output")

    def test_invalid_ai_grams_and_extra_nutrition_are_rejected(self):
        candidates = candidate_pool({}, "lunch", "maintain", "demo")
        valid = self.raw(candidates, "lunch", 800, "maintain")
        for grams in (0, -1, 100000, True, float("nan")):
            invalid = copy.deepcopy(valid)
            invalid["choices"][0]["components"][0]["grams"] = grams
            with self.assertRaises(AIUnavailable):
                MealPlannerV4.validate_composition(invalid, candidates, "lunch", 800, "maintain", {})
        valid["choices"][0]["calories"] = 99999
        with self.assertRaises(AIUnavailable):
            MealPlannerV4.validate_composition(valid, candidates, "lunch", 800, "maintain", {})

    def test_duplicate_ai_combinations_are_rejected(self):
        candidates = candidate_pool({}, "lunch", "maintain", "demo")
        raw = self.raw(candidates, "lunch", 800, "maintain")
        raw["choices"][1] = copy.deepcopy(raw["choices"][0])
        with self.assertRaises(AIUnavailable):
            MealPlannerV4.validate_composition(raw, candidates, "lunch", 800, "maintain", {})

    def test_provider_failure_uses_database_fallback_for_three_meals(self):
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=AIUnavailable("provider_busy", 429)):
            for meal in ("breakfast", "lunch", "dinner"):
                body = self.v4(meal).get_json()
                self.assertEqual(body["meta"]["source"], "fallback")
                options = body["data"]["options"]
                self.assertEqual(len(options), 3)
                self.assertEqual(len({tuple(sorted(p["dish_id"] for p in o["components"])) for o in options}), 3)
                for option in options:
                    self.assertEqual(totals(option["components"])["calories"], option["calories"])

    def test_goals_change_ranking_and_never_write_core_profile(self):
        rankings = []
        for focus in ("lose", "maintain", "gain", "muscle_gain"):
            rankings.append([d["dish_id"] for d in candidate_pool({}, "lunch", focus, "same")])
            body = self.v4(planningFocus=focus).get_json()
            if body.get("code") == "PREFERENCES_REQUIRE_REFRESH":
                meal = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"]
                body = self.v4(forceRefresh=True, revision=meal["revision"], planningFocus=focus).get_json()
            self.assertEqual(body["data"]["options"][0]["recipe"]["focus"], focus)
        self.assertGreater(len({tuple(r) for r in rankings}), 1)
        self.assertEqual(db.session.execute(text("SELECT TargetKcal FROM UserProfiles WHERE UserId=1")).scalar(), 2000)

    def test_refresh_varies_combinations_and_select_does_not_record_intake(self):
        first = self.v4().get_json()["data"]
        refreshed = self.v4(forceRefresh=True, revision=first["revision"]).get_json()["data"]
        signature = lambda meal: [tuple(p["dish_id"] for p in o["components"]) for o in meal["options"]]
        self.assertNotEqual(signature(first), signature(refreshed))
        self.choose(refreshed, 1)
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_cached_metadata_is_distinct_and_does_not_call_gemini(self):
        first = self.v4().get_json()
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=AssertionError("Cache must not call provider")):
            cached = self.v4().get_json()
        self.assertEqual(cached["data"], first["data"])
        self.assertEqual(cached["meta"]["source"], "cached")
        self.assertEqual(cached["meta"]["provider_source"], first["meta"]["source"])
        self.assertTrue(cached["meta"]["cached"])

    def test_component_swap_reads_database_and_preserves_unrelated_components(self):
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        old = next(p for p in option["components"] if p["type"] == "PROTEIN")
        replacement = next(d for d in catalog_dishes("lunch") if d["type"] == "PROTEIN" and d["dish_id"] != old["dish_id"])
        response = self.swap(meal, option, "PROTEIN", replacement["dish_id"], replacement["reference_grams"])
        updated = response.get_json()["data"]
        self.assertNotEqual(updated["revision"], meal["revision"])
        self.assertEqual(updated["options"][1:], meal["options"][1:])
        self.assertEqual([p for p in updated["options"][0]["components"] if p["type"] != "PROTEIN"],
                         [p for p in option["components"] if p["type"] != "PROTEIN"])
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_component_alternatives_use_database_and_validate_ai_ids(self):
        meal = self.v4().get_json()["data"]
        payload = {"mealType": "lunch", "optionId": meal["options"][0]["optionId"], "componentType": "PROTEIN", "revision": meal["revision"]}
        response = self.client.post("/api/meals/component-suggestions", headers=self.headers, json=payload).get_json()
        ids = {d["dish_id"] for d in catalog_dishes("lunch")}
        self.assertEqual(response["data"]["source"], "catalog")
        self.assertTrue(all(d["dish_id"] in ids for d in response["data"]["choices"]))
        with patch.object(self.app.extensions["nutrifit_gemini"], "alternatives", return_value={"choices": [{"dish_id": "invented", "reason": "Sai"}] * 3}):
            self.assertEqual(self.client.post("/api/meals/component-suggestions", headers=self.headers, json=payload).get_json()["data"]["source"], "catalog")

    def test_new_database_food_can_be_recorded_and_has_source_energy(self):
        dish = catalog_by_id()["usda_169704"]
        row = self.intake(items=[{"dish_id": dish["dish_id"], "grams": 100}]).get_json()["data"]
        self.assertEqual(row["totals"]["calories"], dish["calories_per_100g"])
        self.assertEqual(row["items"][0]["provenance"]["source_id"], "169704")

    def test_edit_scales_frozen_nutrition_after_catalog_changes_or_deactivation(self):
        row = self.intake().get_json()["data"]
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999,CarbsPer100G=999,IsActive=0 WHERE DishId='rice'"))
        db.session.commit()
        response = self.client.post(f'/api/nutrition/intake/{row["id"]}/update', headers=self.headers,
            json={"version": row["version"], "confirmed": True, "mealType": "breakfast", "consumedAt": "2026-10-10T08:00:00+07:00",
                  "items": [{"dish_id": "rice", "grams": 400}]})
        self.assertEqual(response.status_code, 200)
        changed = response.get_json()["data"]
        self.assertEqual(changed["totals"]["calories"], round(row["totals"]["calories"] * 2, 1))
        self.assertEqual(changed["items"][0]["nutrition_per_100g"], row["items"][0]["nutrition_per_100g"])

    def test_history_snapshot_is_unchanged_when_catalog_changes(self):
        meal = self.v4().get_json()["data"]
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999"))
        db.session.commit()
        loaded = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"]
        self.assertEqual(loaded, meal)

    def test_catalog_and_intake_require_session_and_ownership(self):
        self.assertEqual(self.client.get("/api/nutrition/catalog").status_code, 401)
        row = self.intake().get_json()["data"]
        self.assertEqual(self.client.post(f'/api/nutrition/intake/{row["id"]}/delete', headers=self.other_headers,
                                         json={"version": row["version"]}).status_code, 404)

    def test_inactive_food_cannot_be_added_as_new_intake(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET IsActive=0 WHERE DishId='rice'"))
        db.session.commit()
        response = self.intake()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "UNKNOWN_DISH")
        self.assertEqual(self.daily()["logs"], [])

    def test_no_runtime_imports_reference_old_python_data_modules(self):
        root = Path(__file__).resolve().parents[1] / "app"
        old = {"food_catalog.py", "breakfast_menus.py", "vietnamese_menus.py"}
        for name in old:
            self.assertFalse((root / "data" / name).exists())
        for source in root.rglob("*.py"):
            self.assertNotRegex(source.read_text(encoding="utf-8"), r"app\.data\.(food_catalog|breakfast_menus|vietnamese_menus)")

    def test_seed_validation_does_not_connect_to_database(self):
        with patch.object(db.session, "execute", side_effect=AssertionError("No DB expected")):
            self.assertEqual(len(load_seed()["dishes"]), 102)


if __name__ == "__main__":
    unittest.main()
