"""V3 regression uses the existing SQLite-only, mock-mail fixture."""
import unittest
from unittest.mock import patch
from sqlalchemy import text
from app.extensions import db
from app.data.vietnamese_menus import templates
from app.services.meal_preferences import ingredients, replacement_request, violates, validate_preferences
from app.services.module_errors import ModuleError
from app.ai.gemini_client import AIUnavailable
from app.models.health import UserProfile
import test_meal_api as fixtures


class MealV3Tests(unittest.TestCase):
    setUp = fixtures.ApiTests.setUp
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    generate = fixtures.ApiTests.generate
    choose = fixtures.ApiTests.choose

    def test_breakfast_catalog_and_reference_nutrition(self):
        catalog = templates("breakfast")
        self.assertEqual(len(catalog), 21)
        self.assertEqual(len({t["template_id"] for t in catalog}), 21)
        for day in range(7):
            choices = [t for t in catalog if t["day"] == day]
            self.assertEqual({t["family"] for t in choices}, {"quick", "soup", "balanced"})
        for item in catalog:
            self.assertGreater(item["calories"], 250)
            self.assertLess(item["calories"], 700)
            self.assertTrue(item["ingredients"])
            self.assertTrue(1 <= len(item["components"]) <= 3)
            macros = item["macros"]
            self.assertAlmostEqual(item["calories"], 4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"], delta=0.1)

    def test_breakfast_generate_components_cache_and_stored_target(self):
        body = self.generate("breakfast").get_json()
        self.assertEqual(body["meta"]["source"], "fallback")
        self.assertEqual(body["meta"]["target_kcal"], 500)
        options = body["data"]["options"]
        self.assertEqual(len(options), 3)
        self.assertEqual(len({o["title"] for o in options}), 3)
        self.assertTrue(any(len(o["components"]) != 5 for o in options))
        for option in options:
            self.assertAlmostEqual(option["calories"], 500, delta=1)
            self.assertTrue(all(c["type"] in ("MAIN", "SIDE", "DRINK", "DESSERT") for c in option["components"]))
        self.assertEqual(self.generate("breakfast").get_json()["data"], body["data"])

    def test_three_meal_selection_summary_history_and_refresh(self):
        total = 0
        for name in ("breakfast", "lunch", "dinner"):
            meal = self.generate(name).get_json()["data"]
            chosen = self.choose(meal, 1).get_json()["data"]
            total += chosen["options"][0]["calories"]
            conflict = self.generate(name, forceRefresh=True, revision=meal["revision"])
            self.assertEqual(conflict.get_json()["code"], "MEAL_DECIDED")
        summary = self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]
        self.assertEqual(summary["selected_meals"], 3)
        self.assertAlmostEqual(summary["planned"]["calories"], total, delta=0.1)
        history = self.client.get("/api/meals/history", headers=self.headers).get_json()["history"]
        self.assertEqual({h["mealType"] for h in history}, {"breakfast", "lunch", "dinner"})
        breakfast = next(h for h in history if h["mealType"] == "breakfast")
        pending = self.choose(breakfast, None).get_json()["data"]
        refreshed = self.generate("breakfast", forceRefresh=True, revision=pending["revision"])
        self.assertEqual(refreshed.status_code, 200)
        self.assertNotEqual(refreshed.get_json()["data"]["revision"], pending["revision"])
        self.assertEqual(self.choose(pending, 1).get_json()["code"], "STALE_MEAL")

    def test_legacy_aliases_unknown_component_and_user_isolation(self):
        lunch = self.generate().get_json()["data"]
        self.assertTrue(all(len(o["components"]) == 5 for o in lunch["options"]))
        self.assertEqual(lunch["options"][0]["carb"], lunch["options"][0]["components"][0]["name"])
        db.session.execute(text("INSERT INTO MealComponentDish (OptionId, ComponentType, DishName) VALUES (:oid, 'SIDE_NEW', 'Món cũ bổ sung')"), {"oid": lunch["options"][0]["optionId"]})
        db.session.commit()
        loaded = self.generate().get_json()["data"]
        self.assertEqual(loaded["revision"], lunch["revision"])
        self.assertEqual(loaded["options"][0]["components"][-1]["type"], "SIDE_NEW")
        self.assertEqual(self.client.get("/api/meals/today", headers=self.other_headers).get_json()["todayMeals"], {"breakfast": None, "lunch": None, "dinner": None})

    def test_hard_avoid_applies_to_provider_and_fallback(self):
        def fail(candidates, *args):
            self.assertTrue(all(not {"fish", "seafood", "egg"} & ingredients(t) for t in candidates))
            raise AIUnavailable("provider_busy")
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank", side_effect=fail):
            body = self.generate(preferences={"avoid": ["cá", "trứng"]}).get_json()
        self.assertEqual(body["meta"]["source"], "fallback")
        titles = {t["title"]: t for t in templates("lunch")}
        self.assertTrue(all(not {"fish", "seafood", "egg"} & ingredients(titles[o["title"]]) for o in body["data"]["options"]))
        # cà rốt/cà chua do not become fish after accent normalization.
        beef = next(t for t in templates("lunch") if "Bò kho cà rốt" in t["title"])
        self.assertNotIn("fish", ingredients(beef))

    def test_breakfast_avoid_and_time_are_hard_filters(self):
        body = self.generate("breakfast", preferences={"avoid": ["trứng", "sữa"], "maxPrepMinutes": 25, "preferEasy": True}).get_json()
        self.assertTrue(body["success"])
        catalog = {t["title"]: t for t in templates("breakfast")}
        for option in body["data"]["options"]:
            item = catalog[option["title"]]
            self.assertFalse({"egg", "milk"} & ingredients(item))
            self.assertLessEqual(item["prep_minutes"], 25)

    def test_insufficient_candidates_fail_without_writes(self):
        response = self.generate(preferences={"avoid": ["heo", "bò", "gà", "cá"]})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["code"], "INSUFFICIENT_MENUS")
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar(), 0)

    def test_invalid_or_unsupported_preferences_rejected(self):
        for preferences in ([], {"avoid": "fish"}, {"avoid": ["unknown ingredient"]}, {"avoid": [1]},
                            {"maxPrepMinutes": True}, {"budget": 50000}, {"preferEasy": "yes"},
                            {"avoid": ["<script>"]}):
            self.assertEqual(self.generate("breakfast", preferences=preferences).status_code, 400)
        self.assertEqual(self.generate(preferences={"maxPrepMinutes": 30}).status_code, 400)

    def test_soft_preferences_relax_only_if_insufficient(self):
        body = self.generate(preferences={"dislikes": ["cá"], "prefer": ["gà"]}).get_json()
        self.assertEqual(len(body["data"]["options"]), 3)
        self.assertTrue(all("Gà" in o["title"] for o in body["data"]["options"]))
        # All proteins disliked is a soft constraint, not an empty result.
        self.assertEqual(self.generate("dinner", preferences={"dislikes": ["heo", "bò", "gà", "cá"]}).status_code, 200)

    def test_cache_with_new_hard_avoid_requires_explicit_refresh(self):
        meal = self.generate().get_json()["data"]
        blocked = self.generate(preferences={"avoid": ["cá"]})
        self.assertEqual(blocked.get_json()["code"], "PREFERENCES_REQUIRE_REFRESH")
        self.assertEqual(self.generate().get_json()["data"], meal)
        refreshed = self.generate(forceRefresh=True, revision=meal["revision"], preferences={"avoid": ["cá"]})
        self.assertEqual(refreshed.status_code, 200)
        self.assertTrue(all("Cá" not in o["title"] and "Tôm" not in o["title"] for o in refreshed.get_json()["data"]["options"]))

    def test_hard_filter_does_not_trust_cached_title_over_saved_components(self):
        meal = self.generate(preferences={"avoid": ["cá"]}).get_json()["data"]
        oid = meal["options"][0]["optionId"]
        db.session.execute(text("UPDATE MealComponentDish SET DishName='Cá chiên (~100 g)' WHERE OptionId=:oid AND ComponentType='PROTEIN'"), {"oid": oid})
        db.session.commit()
        self.assertEqual(self.generate(preferences={"avoid": ["cá"]}).get_json()["code"], "PREFERENCES_REQUIRE_REFRESH")
        # Reading without new constraints still preserves the existing row.
        self.assertEqual(self.generate().get_json()["data"]["options"][0]["protein"], "Cá chiên (~100 g)")

    def test_cached_new_soft_preferences_require_refresh_without_writes(self):
        meal = self.generate().get_json()["data"]
        for preferences in ({"dislikes": ["cá"]}, {"prefer": ["gà"]}):
            with self.subTest(preferences=preferences), patch.object(self.app.extensions["nutrifit_gemini"], "rank") as rank:
                response = self.generate(preferences=preferences)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.get_json()["code"], "PREFERENCES_REQUIRE_REFRESH")
                rank.assert_not_called()
                self.assertEqual(self.generate().get_json()["data"], meal)
        refreshed = self.generate(forceRefresh=True, revision=meal["revision"], preferences={"prefer": ["gà"]})
        self.assertEqual(refreshed.status_code, 200)
        self.assertTrue(all("Gà" in o["title"] for o in refreshed.get_json()["data"]["options"]))

    def test_compatible_soft_preferences_keep_cached_revision(self):
        preferences = {"dislikes": ["cá"], "prefer": ["gà"]}
        meal = self.generate(preferences=preferences).get_json()["data"]
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank") as rank:
            cached = self.generate(preferences=preferences).get_json()
        self.assertTrue(cached["meta"]["cached"])
        self.assertEqual(cached["data"], meal)
        rank.assert_not_called()

    def test_cached_soft_preferences_relax_if_fewer_than_three_matches(self):
        meal = self.generate().get_json()["data"]
        cached = self.generate(preferences={"dislikes": ["heo", "bò", "gà", "cá"], "prefer": ["yến mạch"]})
        self.assertEqual(cached.status_code, 200)
        self.assertTrue(cached.get_json()["meta"]["cached"])
        self.assertEqual(cached.get_json()["data"], meal)

    def test_cached_prefer_easy_requires_explicit_refresh(self):
        meal = self.generate("breakfast").get_json()["data"]
        blocked = self.generate("breakfast", preferences={"preferEasy": True})
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.get_json()["code"], "PREFERENCES_REQUIRE_REFRESH")
        self.assertEqual(self.generate("breakfast").get_json()["data"], meal)
        refreshed = self.generate("breakfast", forceRefresh=True, revision=meal["revision"], preferences={"preferEasy": True})
        self.assertEqual(refreshed.status_code, 200)
        self.assertNotEqual(refreshed.get_json()["data"]["revision"], meal["revision"])

    def test_concurrent_cache_winner_must_obey_soft_preferences(self):
        meal = self.generate().get_json()["data"]
        with patch("app.services.meal_service.MealRepository.load", return_value=None), patch(
                "app.services.meal_service.MealRepository.store", return_value=(meal, True)):
            response = self.generate(preferences={"prefer": ["gà"]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "PREFERENCES_REQUIRE_REFRESH")
        self.assertEqual(self.generate().get_json()["data"], meal)

    def replace(self, meal, **extra):
        return self.client.post("/api/meals/replace", headers=self.headers, json={
            "mealType": meal["mealType"], "revision": meal["revision"],
            "request": "Tôi không thích cá, hãy đổi sang gà nhưng vẫn gần 700 kcal.", **extra})

    def test_smart_replace_portions_revision_and_profile_unchanged(self):
        meal = self.generate().get_json()["data"]
        response = self.replace(meal)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["meta"]["target_kcal"], 700)
        self.assertEqual(body["meta"]["profile_target_kcal"], 800)
        self.assertEqual(body["meta"]["applied_preferences"]["prefer"], ["chicken"])
        for option in body["data"]["options"]:
            self.assertIn("Gà", option["title"])
            self.assertAlmostEqual(option["calories"], 700, delta=1)
        self.assertEqual(UserProfile.query.filter_by(UserId=1).first().TargetKcal, 2000)
        self.assertEqual(self.replace(meal).get_json()["code"], "STALE_MEAL")

    def test_smart_replace_keeps_avoid_and_protects_decided(self):
        meal = self.generate().get_json()["data"]
        result = self.replace(meal, preferences={"avoid": ["gà"]})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(all("Gà" not in o["title"] for o in result.get_json()["data"]["options"]))
        chosen = self.choose(result.get_json()["data"], 1).get_json()["data"]
        self.assertEqual(self.replace(chosen).get_json()["code"], "MEAL_DECIDED")
        pending = self.choose(chosen, None).get_json()["data"]
        self.assertEqual(self.replace(pending).status_code, 200)

    def test_replace_session_ownership_validation_and_missing_meal(self):
        self.assertEqual(self.client.post("/api/meals/replace", json={}).status_code, 401)
        meal = self.generate().get_json()["data"]
        self.assertEqual(self.replace(meal, userId=2).status_code, 403)
        self.assertEqual(self.replace(meal, request="Hãy tư vấn bệnh lý").status_code, 400)
        self.assertEqual(self.replace(meal, apiKey="client-credential-not-allowed").status_code, 400)
        self.assertEqual(self.replace(meal, mealType="breakfast").status_code, 404)
        self.assertEqual(self.replace(meal, request="đổi sang gà gần 50000 kcal").status_code, 400)

    def test_provider_cannot_restore_filtered_out_template(self):
        choices = [(t, "Món Việt phù hợp.") for t in templates("lunch")[:3]]
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank", return_value=choices):
            body = self.generate(preferences={"avoid": ["cá"]}).get_json()
        self.assertEqual(body["meta"]["source"], "fallback")
        self.assertEqual(body["meta"]["fallback_reason"], "invalid_output")

    def test_breakfast_gemini_selection_and_legacy_custom_goal(self):
        profile = UserProfile.query.filter_by(UserId=1).first()
        profile.Goal = "giu_can"
        db.session.commit()
        choices = [(t, "Bữa sáng cân đối theo khẩu phần tham khảo.") for t in templates("breakfast")[:3]]
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank", return_value=choices) as rank:
            response = self.generate("breakfast")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["source"], "gemini")
        self.assertEqual(rank.call_args.args[4]["goal"], "maintain")
        self.assertEqual(rank.call_args.args[4]["macro_targets"], {"carbs": 56.2, "protein": 31.2, "fat": 16.7})
        cached = self.generate("breakfast").get_json()["data"]
        self.assertEqual(cached["options"][0]["reason"], choices[0][1])


class PreferenceUnitTests(unittest.TestCase):
    def test_empty_preferences_keep_default_behavior(self):
        self.assertEqual(validate_preferences({"avoid": [], "dislikes": [], "prefer": [], "preferEasy": False}, "breakfast"), {})

    def test_command_never_silently_ignores_unknown_avoid_instruction(self):
        for command in ("tránh cá, trứng", "đổi sang gà, bỏ trứng", "tránh cá, dị ứng đậu phộng"):
            with self.assertRaises(ModuleError):
                replacement_request(command, {}, "lunch")
        preferences, target = replacement_request("đổi sang gà gần 700 kcal", {"avoid": ["trứng"]}, "lunch")
        self.assertEqual(preferences, {"avoid": ["egg"], "prefer": ["chicken"]})
        self.assertEqual(target, 700)

    def test_rice_avoid_includes_reference_rice_noodles(self):
        soup = templates("breakfast")[1]
        self.assertTrue(violates(soup, {"avoid": ["rice"]}))
