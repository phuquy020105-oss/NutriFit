"""V4 integration: original core factory, additive DDL in SQLite, mocked AI/mail."""
import copy
import json
import re
import secrets
import unittest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text
from app.extensions import db
from app.data.food_catalog import CATALOG, DISHES, component, totals
from app.services.meal_planner_v4 import MealPlannerV4, eligible, score
from app.ai.gemini_client import AIUnavailable
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.nutrition_v4_repository import NutritionV4Repository
import test_meal_api as fixtures


def migration_sqlite():
    source = (Path(__file__).resolve().parents[2] / "setup/migrations/001_nutrition_v4.sql").read_text(encoding="utf-8")
    assert not re.search(r"(?:^|;)\s*(DROP|TRUNCATE|DELETE|ALTER|USE)\b", re.sub(r"--[^\n]*", "", source), re.I)
    for statement in re.findall(r"CREATE (?:TABLE|INDEX).*?;", source, re.S):
        statement = statement.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        statement = re.sub(r"\) ENGINE=.*?;", ");", statement)
        db.session.execute(text(statement))
    db.session.commit()


class V4Tests(unittest.TestCase):
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    generate = fixtures.ApiTests.generate
    choose = fixtures.ApiTests.choose

    def setUp(self):
        fixtures.ApiTests.setUp(self)
        self.assertEqual(self.app.config["SQLALCHEMY_DATABASE_URI"], "sqlite:///:memory:")
        migration_sqlite()

    def v4(self, meal="lunch", **extra):
        return self.generate(meal, plannerVersion="v4", **extra)

    def intake(self, **extra):
        return self.client.post("/api/nutrition/intake", headers=self.headers, json={
            "requestId": secrets.token_hex(16), "confirmed": True, "mealType": "breakfast",
            "consumedAt": "2026-10-10T08:00:00+07:00", "items": [{"dish_id": "rice", "grams": 200}], **extra})

    def daily(self, headers=None, day="2026-10-10"):
        return self.client.get("/api/nutrition/daily?date=" + day, headers=headers or self.headers).get_json()["data"]

    def swap(self, meal, option, kind, dish, grams, **extra):
        return self.client.post("/api/meals/replace-component", headers=self.headers, json={
            "mealType": meal["mealType"], "optionId": option["optionId"], "componentType": kind,
            "dishId": dish, "grams": grams, "revision": meal["revision"], **extra})

    def test_fallback_composes_all_meals_and_reload_keeps_recipe(self):
        for name in ("breakfast", "lunch", "dinner"):
            response = self.v4(name)
            self.assertEqual(response.status_code, 200)
            body = response.get_json()
            self.assertEqual(body["meta"]["source"], "fallback")
            self.assertEqual(len(body["data"]["options"]), 3)
            for o in body["data"]["options"]:
                self.assertEqual(o["plannerVersion"], "v4")
                values = totals(o["recipe"]["components"])
                self.assertEqual(values["calories"], o["calories"])
                self.assertEqual({k: values[k] for k in o["macros"]}, o["macros"])
            self.assertEqual(self.v4(name).get_json()["data"], body["data"])

    def test_gemini_can_combine_catalog_ids_without_inventing_nutrition(self):
        options = MealPlannerV4.fallback(list(DISHES), "lunch", 800, "maintain", {})
        raw = {"choices": [{"title": "Kết hợp mới " + str(i), "reason": "Đủ nhóm thực phẩm.",
            "components": [{k: c[k] for k in ("type", "dish_id", "grams")} for c in o["recipe"]["components"]]} for i, o in enumerate(options)]}
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", return_value=raw):
            result = self.v4().get_json()
        self.assertEqual(result["meta"]["source"], "gemini")
        self.assertTrue(all(o["title"].startswith("Kết hợp mới") for o in result["data"]["options"]))
        bad = copy.deepcopy(raw)
        bad["choices"][0]["calories"] = 99999
        meal = result["data"]
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", return_value=bad):
            fallback = self.v4(forceRefresh=True, revision=meal["revision"]).get_json()
        self.assertEqual(fallback["meta"]["source"], "fallback")
        self.assertEqual(fallback["meta"]["fallback_reason"], "invalid_output")

    def test_hard_avoid_filters_gemini_fallback_and_replacement(self):
        def reject(candidates, *args):
            self.assertTrue(all(not {"chicken", "fish", "seafood"} & set(d["ingredients"]) for d in candidates))
            raise AIUnavailable("provider_busy", 429)
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=reject):
            body = self.v4(preferences={"avoid": ["gà", "cá"]}).get_json()
        self.assertEqual(body["meta"]["provider_http_status"], 429)
        meal = body["data"]
        self.assertTrue(all(not {"chicken", "fish", "seafood"} & set(CATALOG[c["dish_id"]]["ingredients"]) for o in meal["options"] for c in o["components"]))
        self.assertEqual(self.swap(meal, meal["options"][0], "PROTEIN", "chicken", 130).status_code, 422)

    def test_new_preferences_and_focus_are_not_silently_cached(self):
        meal = self.v4().get_json()["data"]
        for extra in ({"preferences": {"prefer": ["gà"]}}, {"planningFocus": "muscle_gain"}):
            self.assertEqual(self.v4(**extra).get_json()["code"], "PREFERENCES_REQUIRE_REFRESH")
        self.assertEqual(self.v4().get_json()["data"], meal)

    def test_focus_changes_scores_and_dish_ranking_without_profile_writes(self):
        proteins = [d for d in DISHES if d["type"] == "PROTEIN"]
        rankings = {f: [d["dish_id"] for d in sorted(proteins, key=lambda d: -score(d, f, {}))]
                    for f in ("lose", "maintain", "gain", "muscle_gain")}
        self.assertNotEqual(rankings["gain"], rankings["muscle_gain"])
        self.assertNotEqual(score(CATALOG["chicken"], "lose", {}), score(CATALOG["chicken"], "muscle_gain", {}))
        body = self.v4(planningFocus="muscle_gain").get_json()
        self.assertEqual(body["meta"]["planningFocus"], "muscle_gain")
        self.assertEqual(db.session.execute(text("SELECT TargetKcal FROM UserProfiles WHERE UserId=1")).scalar(), 2000)

    def test_single_swap_preserves_other_options_components_and_updates_totals(self):
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        before = copy.deepcopy(option["components"])
        old = next(c for c in before if c["type"] == "PROTEIN")
        dish = "chicken" if old["dish_id"] != "chicken" else "pork"
        response = self.swap(meal, option, "PROTEIN", dish, 130)
        self.assertEqual(response.status_code, 200)
        updated = response.get_json()["data"]
        self.assertNotEqual(updated["revision"], meal["revision"])
        self.assertEqual(updated["options"][1:], meal["options"][1:])
        parts = updated["options"][0]["components"]
        self.assertEqual([c for c in parts if c["type"] != "PROTEIN"], [c for c in before if c["type"] != "PROTEIN"])
        self.assertEqual(totals(parts)["calories"], updated["options"][0]["calories"])
        self.assertIn(CATALOG[dish]["name"], updated["options"][0]["title"])
        self.assertEqual(self.swap(meal, option, "PROTEIN", dish, 130).get_json()["code"], "STALE_MEAL")
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_revision_changes_even_when_replacement_calories_are_equal(self):
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        old = next(c for c in option["components"] if c["type"] == "PROTEIN")
        replacement = copy.deepcopy(CATALOG[old["dish_id"]])
        replacement.update(dish_id="equal_energy_test", name="Món cùng năng lượng")
        with patch.dict(CATALOG, {"equal_energy_test": replacement}):
            updated = self.swap(meal, option, "PROTEIN", "equal_energy_test", old["grams"]).get_json()["data"]
        self.assertEqual(updated["options"][0]["calories"], option["calories"])
        self.assertNotEqual(updated["revision"], meal["revision"])

    def test_decided_stale_and_other_user_protect_component_changes(self):
        meal = self.v4().get_json()["data"]
        chosen = self.choose(meal, 1).get_json()["data"]
        self.assertEqual(self.swap(chosen, chosen["options"][0], "PROTEIN", "chicken", 130).get_json()["code"], "MEAL_DECIDED")
        pending = self.choose(chosen, None).get_json()["data"]
        self.assertEqual(self.swap(pending, pending["options"][0], "CARB", "chicken", 130).status_code, 400)
        self.assertEqual(self.swap(pending, pending["options"][0], "PROTEIN", "chicken", 130, userId=2).status_code, 403)

    def test_legacy_v3_read_and_whole_meal_intake_safe_component_rejection(self):
        meal = self.generate().get_json()["data"]
        self.assertEqual(self.v4().get_json()["code"], "V4_REFRESH_REQUIRED")
        self.assertEqual(self.swap(meal, meal["options"][0], "PROTEIN", "chicken", 130).get_json()["code"], "LEGACY_COMPONENT_NUTRITION_REQUIRED")
        body = self.intake(mealType="lunch", items=None, servings=0.5,
            meal={"optionId": meal["options"][0]["optionId"], "revision": meal["revision"]}).get_json()["data"]
        self.assertEqual(body["source"], "legacy_meal_total")
        self.assertEqual(body["totals"]["calories"], round(meal["options"][0]["calories"] * 0.5, 1))
        self.assertEqual(body["items"], [])

    def test_select_is_planned_and_confirmation_is_required(self):
        meal = self.v4().get_json()["data"]
        self.choose(meal, 1)
        self.assertGreater(self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]["planned"]["calories"], 0)
        self.assertEqual(self.daily()["consumed"]["calories"], 0)
        self.assertEqual(self.intake(confirmed=False).get_json()["code"], "CONFIRMATION_REQUIRED")
        result = self.intake().get_json()["data"]
        self.assertEqual(self.daily()["consumed"], result["totals"])

    def test_retry_is_idempotent_conflict_and_deleted_retry_do_not_recreate(self):
        key = secrets.token_hex(16)
        first = self.intake(requestId=key)
        second = self.intake(requestId=key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        row = first.get_json()["data"]
        self.assertEqual(second.get_json()["data"]["id"], row["id"])
        self.assertEqual(self.intake(requestId=key, items=[{"dish_id": "rice", "grams": 250}]).get_json()["code"], "IDEMPOTENCY_CONFLICT")
        self.client.post(f'/api/nutrition/intake/{row["id"]}/delete', headers=self.headers, json={"version": row["version"]})
        self.assertEqual(self.intake(requestId=key).get_json()["code"], "INTAKE_DELETED")
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_retry_after_meal_refresh_returns_existing_snapshot(self):
        meal = self.v4().get_json()["data"]
        key = secrets.token_hex(16)
        payload = {"requestId": key, "mealType": "lunch", "meal": {"optionId": meal["options"][0]["optionId"], "revision": meal["revision"]}}
        first = self.intake(**payload).get_json()["data"]
        self.v4(forceRefresh=True, revision=meal["revision"])
        second = self.intake(**payload)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.get_json()["data"], first)

    def test_edit_delete_version_and_ownership_recompute_daily_totals(self):
        row = self.intake().get_json()["data"]
        path = f'/api/nutrition/intake/{row["id"]}'
        payload = {"version": 1, "confirmed": True, "mealType": "breakfast", "consumedAt": "2026-10-10T09:00:00+07:00", "items": [{"dish_id": "chicken", "grams": 100}]}
        self.assertEqual(self.client.post(path + "/update", headers=self.other_headers, json=payload).status_code, 404)
        result = self.client.post(path + "/update", headers=self.headers, json=payload).get_json()["data"]
        self.assertEqual(result["version"], 2)
        self.assertEqual(self.daily()["consumed"], totals([component("chicken", 100, actual=True)]))
        self.assertEqual(self.client.post(path + "/delete", headers=self.headers, json={"version": 1}).get_json()["code"], "STALE_INTAKE")
        self.assertEqual(self.client.post(path + "/delete", headers=self.headers, json={"version": 2}).status_code, 200)
        self.assertEqual(self.daily()["logs"], [])

    def test_budget_reserves_snack_and_never_overwrites_decided_meals(self):
        lunch = self.v4().get_json()["data"]
        self.choose(lunch, 1)
        # 600 kcal from a known per-gram dish, not a client supplied calorie.
        grams = 600 / CATALOG["rice"]["calories_per_100g"] * 100
        self.intake(items=[{"dish_id": "rice", "grams": grams}])
        daily = self.daily()
        self.assertEqual(daily["consumed"]["calories"], 600)
        self.assertEqual(daily["remaining"]["calories"], 1400)
        self.assertEqual(daily["suggested_meal_targets"], {"lunch": 746.7, "dinner": 560.0, "snack": 93.3})
        self.assertEqual(self.v4(forceRefresh=True, revision=lunch["revision"]).get_json()["code"], "MEAL_DECIDED")
        self.assertEqual(self.daily()["consumed"]["calories"], 600)

    def test_over_target_remains_visible_and_suggested_meals_are_not_zero(self):
        self.intake(items=[{"dish_id": "rice", "grams": 1900}])
        budget = self.daily()
        self.assertLess(budget["remaining"]["calories"], 0)
        self.assertGreater(budget["over_target"]["calories"], 0)
        self.assertTrue(all(v > 0 for v in budget["suggested_meal_targets"].values()))

    def test_user_and_local_date_isolation_and_timezone_boundary(self):
        self.intake(consumedAt="2026-10-09T20:00:00Z")
        self.assertEqual(len(self.daily()["logs"]), 1)  # UTC+7 => October 10.
        self.assertEqual(self.daily(day="2026-10-09")["logs"], [])
        from app.models.health import UserProfile
        db.session.add(UserProfile(UserId=2, Gender="male", Age=22, HeightCm=172, WeightKg=65,
            ActivityLevel=1.375, Goal="maintain", Bmr=1610, Tdee=2213.8, TargetKcal=2000, TargetWaterMl=2275))
        db.session.commit()
        self.assertEqual(self.daily(headers=self.other_headers)["logs"], [])
        self.assertEqual(self.client.get("/api/nutrition/daily?userId=2", headers=self.headers).status_code, 403)

    def test_missing_migration_does_not_create_tables_and_keeps_v3_working(self):
        # Only this disposable SQLite fixture, never a live database.
        db.session.execute(text("DROP TABLE NutritionMealDetails"))
        db.session.execute(text("DROP TABLE NutritionFoodIntake"))
        db.session.commit()
        self.assertEqual(self.v4().get_json()["code"], "V4_MIGRATION_REQUIRED")
        self.assertEqual(self.generate().status_code, 200)
        self.assertEqual(self.client.get("/api/nutrition/daily", headers=self.headers).get_json()["code"], "V4_MIGRATION_REQUIRED")

    def test_invalid_intake_fields_and_unknown_food_never_write(self):
        for extra in ({"confirmed": False}, {"requestId": "short"}, {"mealType": "invalid"},
            {"consumedAt": "2026-10-10T08:00:00"}, {"items": [{"dish_id": "unknown", "grams": 50}]},
            {"items": [{"dish_id": "rice", "grams": float("nan")}]},
            {"items": [{"dish_id": "rice", "grams": 50, "calories": 1}]}):
            self.assertEqual(self.intake(**extra).status_code, 400)
        self.assertEqual(self.daily()["logs"], [])

    def test_component_suggestions_fallback_and_gemini_ids_are_checked(self):
        meal = self.v4().get_json()["data"]
        payload = {"mealType": "lunch", "optionId": meal["options"][0]["optionId"], "componentType": "PROTEIN", "revision": meal["revision"]}
        path = "/api/meals/component-suggestions"
        first = self.client.post(path, headers=self.headers, json=payload).get_json()["data"]
        self.assertEqual(first["source"], "fallback")
        self.assertEqual(len(first["choices"]), 3)
        raw = {"choices": [{"dish_id": d["dish_id"], "reason": "Món thay thế hợp lệ."} for d in first["choices"]]}
        with patch.object(self.app.extensions["nutrifit_gemini"], "alternatives", return_value=raw):
            self.assertEqual(self.client.post(path, headers=self.headers, json=payload).get_json()["data"]["source"], "gemini")
        raw["choices"][0]["dish_id"] = "invented"
        with patch.object(self.app.extensions["nutrifit_gemini"], "alternatives", return_value=raw):
            self.assertEqual(self.client.post(path, headers=self.headers, json=payload).get_json()["data"]["source"], "fallback")

    def test_legacy_snapshot_can_be_edited_after_original_plan_is_replaced(self):
        meal = self.generate().get_json()["data"]
        row = self.intake(mealType="lunch", items=None, servings=1,
            meal={"optionId": meal["options"][0]["optionId"], "revision": meal["revision"]}).get_json()["data"]
        self.v4(forceRefresh=True, revision=meal["revision"])
        response = self.client.post(f'/api/nutrition/intake/{row["id"]}/update', headers=self.headers,
            json={"version": 1, "confirmed": True, "mealType": "lunch", "servings": 0.5,
                  "consumedAt": "2026-10-10T12:00:00+07:00"})
        self.assertEqual(response.status_code, 200)
        updated = response.get_json()["data"]
        self.assertEqual(updated["source"], "legacy_meal_total")
        self.assertEqual(updated["totals"], {k: round(v * 0.5, 1) for k, v in row["totals"].items()})

    def test_stored_intake_snapshot_survives_catalog_changes_and_session_reload(self):
        row = self.intake().get_json()["data"]
        changed = copy.deepcopy(CATALOG["rice"])
        changed["macros_per_100g"] = {k: 999 for k in changed["macros_per_100g"]}
        with patch.dict(CATALOG, {"rice": changed}):
            db.session.remove()
            self.assertEqual(self.daily()["logs"][0], row)
            self.assertEqual(self.daily()["consumed"], row["totals"])

    def test_component_failure_rolls_back_all_three_storage_layers(self):
        meal = self.v4().get_json()["data"]
        original = NutritionV4Repository.recipes
        calls = 0
        def fail_after_write(suggestion_id):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise SQLAlchemyError("simulated storage failure")
            return original(suggestion_id)
        with patch.object(NutritionV4Repository, "recipes", side_effect=fail_after_write):
            response = self.swap(meal, meal["options"][0], "PROTEIN", "pork", 130)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "DATABASE_ERROR")
        self.assertEqual(self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"], meal)

    def test_v4_whole_replace_keeps_recipe_and_never_changes_core_target(self):
        meal = self.v4().get_json()["data"]
        response = self.client.post("/api/meals/replace", headers=self.headers, json={
            "mealType": "lunch", "plannerVersion": "v4", "revision": meal["revision"],
            "planningFocus": "muscle_gain", "request": "Khoảng 700 kcal, không thích cá, ưu tiên gà"})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["meta"]["target_kcal"], 700)
        self.assertTrue(all(o["recipe"]["focus"] == "muscle_gain" for o in body["data"]["options"]))
        self.assertTrue(all(not {"fish", "seafood"} & set(CATALOG[c["dish_id"]]["ingredients"])
            for o in body["data"]["options"] for c in o["components"]))
        self.assertEqual(db.session.execute(text("SELECT TargetKcal FROM UserProfiles WHERE UserId=1")).scalar(), 2000)
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_invalid_ai_ids_portions_groups_and_duplicate_options_use_fallback(self):
        options = MealPlannerV4.fallback(list(DISHES), "lunch", 800, "maintain", {})
        valid = {"choices": [{"title": "Lựa chọn " + str(i), "reason": "Kết hợp hợp lệ.",
            "components": [{k: c[k] for k in ("type", "dish_id", "grams")} for c in o["recipe"]["components"]]}
            for i, o in enumerate(options)]}
        variants = []
        for field, value in (("dish_id", "invented"), ("grams", 999999), ("grams", True), ("type", "MAIN")):
            bad = copy.deepcopy(valid)
            bad["choices"][0]["components"][0][field] = value
            variants.append(bad)
        duplicate = copy.deepcopy(valid)
        duplicate["choices"][1] = copy.deepcopy(duplicate["choices"][0])
        variants.append(duplicate)
        for bad in variants:
            with self.subTest(bad=bad["choices"][0]["components"][0]):
                with patch.object(self.app.extensions["nutrifit_gemini"], "compose", return_value=bad):
                    existing = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"]
                    result = self.v4(**({"forceRefresh": True, "revision": existing["revision"]} if existing else {})).get_json()
                self.assertEqual(result["meta"]["source"], "fallback")
                self.assertEqual(result["meta"]["fallback_reason"], "invalid_output")


if __name__ == "__main__":
    unittest.main()
