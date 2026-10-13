"""Compose contracts against the 102-dish SQLite fixture; no live network."""
import copy
import unittest
from unittest.mock import patch
from app.ai.gemini_client import GeminiClient, AIUnavailable, COMPOSITION_RULES
from app.services.meal_planner_v4 import (MealPlannerV4, candidate_pool, fit_portions, refine_options,
    portion_objective, quality_score, better_fallback, composition_shortlist, FALLBACK_FIT_LIMIT,
    portion_quality, bundle_diversity, bundle_score, select_fallback_bundle)
from app.services.food_catalog_service import totals, catalog_dishes, component
from app.extensions import db
from sqlalchemy import text
import test_database_catalog as fixtures


class ComposeValidationTests(unittest.TestCase):
    tearDown = fixtures.DatabaseCatalogTests.tearDown
    login_headers = fixtures.DatabaseCatalogTests.login_headers
    generate = fixtures.DatabaseCatalogTests.generate
    v4 = fixtures.DatabaseCatalogTests.v4

    def setUp(self):
        fixtures.DatabaseCatalogTests.setUp(self)
        self.candidates = candidate_pool({}, "lunch", "maintain", "compose-contract")
        self.raw = fixtures.DatabaseCatalogTests.raw(self.candidates, "lunch", 800, "maintain")

    def validate(self, raw=None, target=800, preferences=None):
        return MealPlannerV4.validate_composition(self.raw if raw is None else raw,
            self.candidates, "lunch", target, "maintain", preferences or {})

    def rejected(self, raw, code, **kwargs):
        with self.assertRaises(AIUnavailable) as caught:
            MealPlannerV4.validate_composition(raw, self.candidates, "lunch",
                kwargs.get("target", 800), "maintain", kwargs.get("preferences", {}))
        self.assertEqual(str(caught.exception), "invalid_output")
        self.assertEqual(caught.exception.diagnostic_code, code)

    def test_valid_database_composition_uses_backend_totals(self):
        options = self.validate()
        self.assertEqual(len(options), 3)
        for option in options:
            values = totals(option["recipe"]["components"])
            self.assertEqual(option["calories"], values["calories"])
            self.assertEqual(option["macros"], {k: values[k] for k in ("carbs", "protein", "fat", "fiber")})

    def test_sanitized_live_compose_portions_replay_against_database(self):
        # Only public catalog IDs/roles/grams from the successful controlled call.
        # No provider free text, user data or credentials are stored in fixtures.
        compositions = [
            [("CARB", "rice", 250), ("PROTEIN", "chicken", 130), ("VEGGIE", "usda_169967", 200)],
            [("CARB", "rice_noodles", 300), ("PROTEIN", "tofu", 250), ("VEGGIE", "usda_170397", 250)],
            [("CARB", "usda_169704", 280), ("PROTEIN", "beef", 120), ("VEGGIE", "usda_168390", 200)],
        ]
        raw = {"choices": [{"title": "Thực đơn kiểm thử " + str(i), "reason": "Dữ liệu đã lược bỏ phần văn bản AI.",
                "components": [{"type": role, "dish_id": identifier, "grams": grams} for role, identifier, grams in parts]}
                for i, parts in enumerate(compositions)]}
        options = MealPlannerV4.validate_composition(raw, catalog_dishes("lunch"), "lunch", 891, "maintain", {"avoid": ["fish"]})
        self.assertEqual([o["calories"] for o in options], [589.1, 591.5, 646.5])
        refined = refine_options(options, catalog_dishes("lunch"), 891)
        self.assertTrue(all(891 * .65 <= o["calories"] <= 891 * 1.35 for o in refined))
        self.assertTrue(all(o["recipe"]["calorie_adjustment"]["within_practical_range"] for o in refined))

    def test_response_schema_code(self):
        for raw in (None, [], {}, {**self.raw, "calories": 42}, {"choices": {}}):
            self.rejected(raw, "INVALID_RESPONSE_SCHEMA")

    def test_exactly_three_choices_code(self):
        for choices in ([], self.raw["choices"][:2], self.raw["choices"] * 2):
            self.rejected({"choices": choices}, "INVALID_CHOICE_COUNT")

    def test_extra_choice_fields_code(self):
        self.raw["choices"][0]["calories"] = 123
        self.rejected(self.raw, "INVALID_RESPONSE_SCHEMA")

    def test_component_schema_code(self):
        self.raw["choices"][0]["components"][0]["name"] = "Do not trust provider nutrition"
        self.rejected(self.raw, "INVALID_RESPONSE_SCHEMA")

    def test_component_count_code(self):
        for components in ([], {}, [None] * 7):
            raw = copy.deepcopy(self.raw)
            raw["choices"][0]["components"] = components
            self.rejected(raw, "INVALID_COMPONENT_COUNT")

    def test_unknown_id_code(self):
        self.raw["choices"][0]["components"][0]["dish_id"] = "not-in-mysql"
        self.rejected(self.raw, "INVALID_DISH_ID")

    def test_wrong_role_for_real_dish_code(self):
        self.raw["choices"][0]["components"][0]["type"] = "PROTEIN"
        self.rejected(self.raw, "INVALID_COMPONENT_ROLE")

    def test_duplicate_role_code(self):
        self.raw["choices"][0]["components"].append(copy.deepcopy(self.raw["choices"][0]["components"][0]))
        self.rejected(self.raw, "DUPLICATE_COMPONENT_ROLE")

    def test_required_group_code(self):
        self.raw["choices"][0]["components"] = [p for p in self.raw["choices"][0]["components"] if p["type"] != "VEGGIE"]
        self.rejected(self.raw, "MISSING_REQUIRED_GROUP")

    def test_invalid_gram_code(self):
        for grams in (0, -1, 100000, True, None, "150", float("nan"), float("inf")):
            raw = copy.deepcopy(self.raw)
            raw["choices"][0]["components"][0]["grams"] = grams
            self.rejected(raw, "INVALID_PORTION")

    def test_per_dish_portion_bounds_code(self):
        part = self.raw["choices"][0]["components"][0]
        dish = next(d for d in self.candidates if d["dish_id"] == part["dish_id"])
        for grams in (dish["min_grams"] - .01, dish["max_grams"] + .01):
            part["grams"] = grams
            self.rejected(self.raw, "INVALID_PORTION")

    def test_titles_have_safe_specific_code(self):
        for title in ("x" * 141, "<script>", "two\nlines", "", None):
            raw = copy.deepcopy(self.raw)
            raw["choices"][0]["title"] = title
            self.rejected(raw, "INVALID_TITLE")

    def test_reasons_have_safe_specific_code(self):
        self.raw["choices"][0]["reason"] = "x" * 221
        self.rejected(self.raw, "INVALID_REASON")

    def test_portion_changes_do_not_make_duplicate_ids_distinct(self):
        self.raw["choices"][1] = copy.deepcopy(self.raw["choices"][0])
        self.raw["choices"][1]["title"] = "A different title is insufficient"
        self.rejected(self.raw, "DUPLICATE_COMPOSITION")

    def test_calorie_mismatch_is_distinct_from_schema(self):
        self.rejected(self.raw, "CALORIE_TARGET_MISMATCH", target=100)
        self.rejected(self.raw, "CALORIE_TARGET_MISMATCH", target=10000)

    def test_avoid_is_checked_even_when_candidate_prefilter_is_missing(self):
        part = self.raw["choices"][0]["components"][0]
        dish = next(d for d in self.candidates if d["dish_id"] == part["dish_id"])
        self.rejected(self.raw, "AVOID_CONFLICT", preferences={"avoid": [dish["ingredients"][0]]})

    def test_raw_or_wrong_meal_food_is_ineligible(self):
        part = self.raw["choices"][0]["components"][0]
        dish = next(d for d in self.candidates if d["dish_id"] == part["dish_id"])
        dish["preparation_state"] = "raw"
        self.rejected(self.raw, "INVALID_DISH_ELIGIBILITY")
        dish["preparation_state"] = "cooked"
        dish["meal_types"] = ["breakfast"]
        self.rejected(self.raw, "INVALID_DISH_ELIGIBILITY")

    def test_prompt_schema_matches_validator_constraints(self):
        client = GeminiClient()
        with patch.object(client, "_request", return_value=self.raw) as request:
            client.compose(self.candidates, "lunch", 800, 999, "maintain", {}, {"preferences": {"avoid": ["fish"]}})
        prompt, schema = request.call_args.args[:2]
        choices = schema["properties"]["choices"]
        self.assertEqual((choices["minItems"], choices["maxItems"]), (3, 3))
        properties = choices["items"]["properties"]["components"]["items"]["properties"]
        self.assertEqual(set(properties["dish_id"]["enum"]), {d["dish_id"] for d in self.candidates})
        self.assertEqual(set(properties["type"]["enum"]), set(COMPOSITION_RULES["lunch"]["allowed"]))
        self.assertEqual(prompt["calorie_bounds"], {"minimum": 520, "maximum": 1080})
        self.assertEqual(prompt["preferred_calorie_bounds"], {"minimum": 680, "maximum": 920})
        self.assertEqual(prompt["practical_calorie_bounds"], {"minimum": 640, "maximum": 960})
        self.assertEqual(prompt["text_limits"], {"title": 140, "reason": 220})
        self.assertEqual(prompt["required_roles"], ["CARB", "PROTEIN", "VEGGIE"])
        self.assertNotIn("user_id", prompt)
        self.assertIn("calories_per_100g * grams / 100", prompt["task"])

    def test_three_feasible_menus_exist_for_each_meal_and_focus(self):
        for meal, target in (("breakfast", 500), ("lunch", 800), ("dinner", 600)):
            for focus in ("lose", "maintain", "gain", "muscle_gain"):
                with self.subTest(meal=meal, focus=focus):
                    prefs = {"avoid": ["fish"]}
                    candidates = candidate_pool(prefs, meal, focus, "feasibility")
                    raw = fixtures.DatabaseCatalogTests.raw(candidates, meal, target, focus, prefs)
                    self.assertEqual(len(MealPlannerV4.validate_composition(raw, candidates, meal, target, focus, prefs)), 3)

    def test_fallback_exposes_safe_code_not_provider_output(self):
        def compose(candidates, meal, target, uid, focus, *args):
            raw = fixtures.DatabaseCatalogTests.raw(candidates, meal, target, focus)
            raw["choices"][0]["reason"] = "private-marker" * 30
            return raw
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=compose):
            body = self.v4().get_json()
        self.assertEqual(body["meta"]["source"], "fallback")
        self.assertEqual(body["meta"]["fallback_diagnostic"], "INVALID_REASON")
        self.assertNotIn("private-marker", str(body))

    def test_low_calorie_valid_menus_are_refined_without_changing_ids(self):
        original = self.validate()
        refined = refine_options(original, self.candidates, 891)
        catalog = {d["dish_id"]: d for d in self.candidates}
        for old, new in zip(original, refined):
            self.assertLessEqual(portion_objective(new["recipe"]["components"], catalog, 891)["total"],
                                 portion_objective(old["recipe"]["components"], catalog, 891)["total"])
            self.assertEqual([p["dish_id"] for p in new["recipe"]["components"]],
                             [p["dish_id"] for p in old["recipe"]["components"]])
            self.assertEqual(new["recipe"]["provider_source"], "gemini")
        self.assertEqual(original, self.validate())  # No in-place mutation.

    def test_refinement_respects_db_gram_limits_and_recalculates_macros(self):
        catalog = {d["dish_id"]: d for d in self.candidates}
        for target in (100, 800, 891, 10000):
            for option in refine_options(self.validate(), self.candidates, target):
                parts = option["recipe"]["components"]
                for p in parts:
                    dish = catalog[p["dish_id"]]
                    self.assertTrue(dish["min_grams"] <= p["grams"] <= dish["max_grams"])
                    self.assertEqual(p["grams"], round(p["grams"], 2))
                self.assertEqual(option["calories"], totals(parts)["calories"])
                self.assertEqual(option["macros"], {k: totals(parts)[k] for k in ("carbs", "protein", "fat", "fiber")})

    def test_impossible_target_is_reported_not_fabricated(self):
        options = refine_options(self.validate(), self.candidates, 10000)
        self.assertTrue(all(not o["recipe"]["calorie_adjustment"]["within_practical_range"] for o in options))
        for o in options:
            self.assertLess(o["calories"], 10000)

    def test_refinement_reduces_excess_calories_when_feasible(self):
        original = self.validate()
        adjusted = refine_options(original, self.candidates, 500)
        self.assertTrue(all(abs(o["calories"] - 500) <= 500 * .20 for o in adjusted))

    def test_refinement_keeps_three_distinct_combinations(self):
        refined = refine_options(self.validate(), self.candidates, 891)
        signatures = {tuple(sorted(p["dish_id"] for p in o["recipe"]["components"])) for o in refined}
        self.assertEqual(len(signatures), 3)

    def test_reserve_energy_candidates_without_losing_focus_ranking(self):
        rows = []
        example = next(d for d in self.candidates if d["type"] == "PROTEIN")
        for i in range(10):
            dish = copy.deepcopy(example)
            dish.update(dish_id="candidate_" + str(i), calories_per_100g=20 if i < 8 else 300)
            rows.append(dish)
        with patch("app.services.meal_planner_v4.eligible", return_value=rows):
            chosen = candidate_pool({}, "lunch", "muscle_gain", "same", target=891)
        self.assertEqual(len(chosen), 8)
        self.assertTrue(any(d["calories_per_100g"] == 300 for d in chosen))
        self.assertTrue(any(d["calories_per_100g"] == 20 for d in chosen))

    def test_fallback_calorie_quality_across_meals_and_goals(self):
        signatures = []
        for meal, target in (("breakfast", 500), ("lunch", 891), ("dinner", 700)):
            for focus in ("lose", "maintain", "gain", "muscle_gain"):
                with self.subTest(meal=meal, focus=focus):
                    prefs = {"avoid": ["fish"]}
                    candidates = candidate_pool(prefs, meal, focus, "quality", target=target)
                    options = MealPlannerV4.fallback(candidates, meal, target, focus, prefs)
                    self.assertEqual(len({tuple(sorted(p["dish_id"] for p in o["recipe"]["components"])) for o in options}), 3)
                    self.assertTrue(all(abs(o["calories"] - target) <= target * .20 for o in options))
                    signatures.append([o["recipe"]["components"][0]["dish_id"] for o in options])
        self.assertGreater(len({tuple(s) for s in signatures}), 3)

    def test_bad_energy_combination_uses_better_fallback(self):
        compositions = [
            [("CARB", "rice", 250), ("PROTEIN", "chicken", 130), ("VEGGIE", "usda_169967", 200)],
            [("CARB", "rice_noodles", 300), ("PROTEIN", "tofu", 250), ("VEGGIE", "usda_170397", 250)],
            [("CARB", "usda_169704", 280), ("PROTEIN", "beef", 120), ("VEGGIE", "usda_168390", 200)],
        ]
        for parts in compositions:
            for _, identifier, grams in parts:
                db.session.execute(text("UPDATE NutritionFoodCatalog SET MinGrams=:g,ReferenceGrams=:g,MaxGrams=:g WHERE DishId=:id"), {"g": grams, "id": identifier})
        db.session.commit()
        raw = {"choices": [{"title": "Bộ hạn chế " + str(i), "reason": "Khẩu phần thử nghiệm.",
            "components": [{"type": role, "dish_id": identifier, "grams": grams} for role, identifier, grams in parts]}
            for i, parts in enumerate(compositions)]}
        with patch("app.services.meal_planner_v4.candidate_pool", return_value=catalog_dishes("lunch")), \
                patch.object(self.app.extensions["nutrifit_gemini"], "compose", return_value=raw):
            body = self.v4().get_json()
        self.assertEqual(body["meta"]["source"], "fallback")
        self.assertEqual(body["meta"]["fallback_diagnostic"], "SELECTED_COMBINATION_ENERGY_LIMIT")
        self.assertEqual(len(body["data"]["options"]), 3)

    def test_new_quality_metadata_is_persisted_and_cache_does_not_refine_again(self):
        body = self.v4().get_json()
        self.assertIn("calorie_quality", body["meta"])
        recipes = [o["recipe"] for o in body["data"]["options"]]
        with patch("app.services.meal_planner_v4.refine_options", side_effect=AssertionError("Cached menu must stay unchanged")):
            again = self.v4().get_json()
        self.assertEqual(recipes, [o["recipe"] for o in again["data"]["options"]])
        self.assertTrue(again["meta"]["cached"])

    def test_unreachable_target_keeps_fallback_and_reports_portion_limit(self):
        meal, meta = MealPlannerV4.generate(1, "lunch", target_override=10000)
        self.assertEqual(meta["source"], "fallback")
        self.assertTrue(meta["calorie_quality"]["limited"])
        self.assertEqual(meta["calorie_quality"]["reason"], "COMBINATION_PORTION_LIMIT")
        self.assertEqual(len(meal["options"]), 3)

    def test_live_under_target_response_is_fitted_before_final_energy_validation(self):
        compositions = [
            [("CARB", "usda_169704", 250), ("PROTEIN", "chicken", 120), ("VEGGIE", "vegetables_oil", 150)],
            [("CARB", "sweet_potato", 250), ("PROTEIN", "beef", 100), ("VEGGIE", "usda_170397", 200)],
            [("CARB", "rice", 220), ("PROTEIN", "usda_167904", 110), ("VEGGIE", "tofu_vegetables", 180)],
        ]
        raw = {"choices": [{"title": "Replay kiểm thử " + str(i), "reason": "Không lưu văn bản AI.",
            "components": [{"type": role, "dish_id": identifier, "grams": grams} for role, identifier, grams in parts]}
            for i, parts in enumerate(compositions)]}
        candidates = catalog_dishes("lunch")
        with self.assertRaises(AIUnavailable) as error:
            MealPlannerV4.validate_composition(raw, candidates, "lunch", 891, "maintain", {})
        self.assertEqual(error.exception.diagnostic_code, "CALORIE_TARGET_MISMATCH")
        fitted = MealPlannerV4.validate_composition(raw, candidates, "lunch", 891, "maintain", {}, adjust_portions=True)
        self.assertTrue(all(891 * .65 <= o["calories"] <= 891 * 1.35 for o in fitted))
        self.assertEqual([o["recipe"]["calorie_adjustment"]["before_kcal"] for o in fitted], [582, 479.3, 595])

    def test_adjustment_cannot_bypass_ids_grams_or_final_energy_validation(self):
        for field, value, code in (("dish_id", "invented", "INVALID_DISH_ID"),
                                    ("grams", 999999, "INVALID_PORTION"),
                                    ("type", "WRONG", "INVALID_COMPONENT_ROLE")):
            raw = copy.deepcopy(self.raw)
            raw["choices"][0]["components"][0][field] = value
            with self.assertRaises(AIUnavailable) as error:
                MealPlannerV4.validate_composition(raw, self.candidates, "lunch", 891, "maintain", {}, adjust_portions=True)
            self.assertEqual(error.exception.diagnostic_code, code)
        with self.assertRaises(AIUnavailable) as error:
            MealPlannerV4.validate_composition(self.raw, self.candidates, "lunch", 10000, "maintain", {}, adjust_portions=True)
        self.assertEqual(error.exception.diagnostic_code, "CALORIE_TARGET_MISMATCH")

    def stored_portion_replay(self):
        # Public dish IDs and portions only, from the three previously saved
        # 891-kcal menus. This creates no MySQL rows and makes no provider call.
        compositions = [
            [("CARB", "rice", 305.77), ("PROTEIN", "usda_171477", 220.16), ("VEGGIE", "vegetables_oil", 244.62)],
            [("CARB", "sweet_potato", 367.68), ("PROTEIN", "usda_167904", 235.31), ("VEGGIE", "usda_170407", 294.14)],
            [("CARB", "usda_169704", 298.4), ("PROTEIN", "beef", 176.32), ("VEGGIE", "tofu_vegetables", 271.27)],
        ]
        raw = {"choices": [{"title": "Replay khẩu phần " + str(i), "reason": "Không có văn bản riêng tư.",
            "components": [{"type": role, "dish_id": identifier, "grams": grams} for role, identifier, grams in parts]}
            for i, parts in enumerate(compositions)]}
        candidates = catalog_dishes("lunch")
        options = MealPlannerV4.validate_composition(raw, candidates, "lunch", 891, "maintain", {"avoid": ["fish"]})
        return options, candidates, {d["dish_id"]: d for d in candidates}

    def test_real_portions_prefer_soft_energy_error_over_exact_kcal(self):
        original, candidates, catalog = self.stored_portion_replay()
        for old, new in zip(original, refine_options(original, candidates, 891)):
            self.assertEqual(old["calories"], 891)
            self.assertLess(new["calories"], 891 - 1)
            self.assertLessEqual(abs(new["calories"] - 891), 891 * .15)
            before = portion_objective(old["recipe"]["components"], catalog, 891)
            after = new["recipe"]["calorie_adjustment"]["objective"]
            self.assertLess(after["macros"], before["macros"])
            self.assertLess(after["reference"], before["reference"])
            self.assertLess(after["total"], before["total"])

    def test_doubling_all_reference_portions_has_explicit_penalty(self):
        original, _, catalog = self.stored_portion_replay()
        parts = original[0]["recipe"]["components"]
        reference = [component(p["dish_id"], catalog[p["dish_id"]]["reference_grams"], p["type"], catalog=catalog) for p in parts]
        doubled = [component(p["dish_id"], p["grams"] * 2, p["type"], catalog=catalog) for p in reference]
        self.assertEqual(portion_objective(reference, catalog, 891)["reference"], 0)
        self.assertEqual(portion_objective(doubled, catalog, 891)["reference"], 1)

    def test_optimizer_preserves_distinct_dishes_preferences_and_snapshots(self):
        original, candidates, catalog = self.stored_portion_replay()
        snapshot = copy.deepcopy(original)
        refined = refine_options(original, candidates, 891)
        signatures = set()
        for old, new in zip(original, refined):
            old_parts, new_parts = old["recipe"]["components"], new["recipe"]["components"]
            self.assertEqual([(p["type"], p["dish_id"]) for p in new_parts],
                             [(p["type"], p["dish_id"]) for p in old_parts])
            self.assertEqual(new["recipe"]["preferences"], {"avoid": ["fish"]})
            self.assertEqual(new["recipe"]["provider_source"], "gemini")
            self.assertTrue(all("fish" not in catalog[p["dish_id"]]["ingredients"] for p in new_parts))
            signatures.add(tuple(sorted(p["dish_id"] for p in new_parts)))
            self.assertLess(sum(p["grams"] for p in new_parts), sum(p["grams"] for p in old_parts))
        self.assertEqual(len(signatures), 3)
        self.assertEqual(original, snapshot)

    def test_actual_meal_macro_budget_changes_portions_without_changing_ids(self):
        original, candidates, catalog = self.stored_portion_replay()
        goals = {"protein": 40, "carbs": 110, "fat": 35}
        normal = refine_options(original, candidates, 891)
        adjusted = refine_options(original, candidates, 891, goals)
        self.assertNotEqual([o["macros"] for o in normal], [o["macros"] for o in adjusted])
        for old, new in zip(original, adjusted):
            self.assertEqual(new["recipe"]["calorie_adjustment"]["macro_targets"], goals)
            self.assertEqual([p["dish_id"] for p in old["recipe"]["components"]],
                             [p["dish_id"] for p in new["recipe"]["components"]])
            self.assertEqual(new["recipe"]["calorie_adjustment"]["objective"],
                             portion_objective(new["recipe"]["components"], catalog, 891, goals))

    def test_generate_passes_remaining_macro_budget_to_optimizer(self):
        budget = {"remaining": {"calories": 2000, "protein": 90, "carbs": 230, "fat": 80},
                  "suggested_meal_targets": {"lunch": 800}}
        def compose(candidates, meal, target, uid, focus, *args):
            return fixtures.DatabaseCatalogTests.raw(candidates, meal, target, focus, macro_targets=args[0])
        with patch("app.services.food_intake_service.FoodIntakeService.daily", return_value=budget), \
                patch("app.services.meal_planner_v4.fit_portions", wraps=fit_portions) as optimize, \
                patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=compose):
            response = self.v4()
        self.assertEqual(response.status_code, 200)
        expected = {"protein": 36, "carbs": 92, "fat": 32}
        self.assertTrue(optimize.call_count >= 3)
        # The provider fixture also uses the real macro budget: otherwise the
        # new quality gate can correctly replace a poorer default-goal recipe.
        actual_calls = [call for call in optimize.call_args_list if call.args[3] is not None]
        self.assertGreaterEqual(len(actual_calls), 6)  # Fallback and Gemini paths.
        self.assertTrue(all(call.args[3] == expected for call in actual_calls))
        self.assertEqual(response.get_json()["meta"]["source"], "gemini")
        self.assertTrue(all(o["recipe"]["calorie_adjustment"]["macro_targets"] == expected
                            for o in response.get_json()["data"]["options"]))

    def test_macro_feasibility_exposes_fixed_low_fat_combination(self):
        original, candidates, _ = self.stored_portion_replay()
        refined = refine_options(original, candidates, 891)
        for option in refined[:2]:
            quality = option["recipe"]["calorie_adjustment"]
            self.assertLess(quality["macro_feasible_ranges"]["fat"]["maximum"], quality["macro_targets"]["fat"])
            self.assertLess(quality["macro_deviation_percent"]["fat"], 0)
        self.assertLess(refined[2]["recipe"]["calorie_adjustment"]["macro_feasible_ranges"]["fat"]["minimum"], 29.7)
        self.assertGreater(refined[2]["recipe"]["calorie_adjustment"]["macro_feasible_ranges"]["fat"]["maximum"], 29.7)

    def test_zero_remaining_macro_target_has_finite_score_and_no_fake_percentage(self):
        import math
        original, candidates, _ = self.stored_portion_replay()
        goals = {"protein": 0, "carbs": 100, "fat": 30}
        for option in refine_options(original, candidates, 891, goals):
            quality = option["recipe"]["calorie_adjustment"]
            self.assertIsNone(quality["macro_deviation_percent"]["protein"])
            self.assertTrue(math.isfinite(quality["objective"]["total"]))
            self.assertTrue(891 * .65 <= option["calories"] <= 891 * 1.35)

    def test_per_dish_fixed_gram_limit_is_preserved(self):
        original, _, catalog = self.stored_portion_replay()
        parts = original[0]["recipe"]["components"]
        fixed = copy.deepcopy(catalog)
        dish = fixed[parts[0]["dish_id"]]
        dish["min_grams"] = dish["max_grams"] = dish["reference_grams"]
        optimized = fit_portions(parts, fixed, 891)
        self.assertEqual(optimized[0]["grams"], dish["reference_grams"])
        self.assertTrue(all(fixed[p["dish_id"]]["min_grams"] <= p["grams"] <= fixed[p["dish_id"]]["max_grams"] for p in optimized))

    def test_soft_quality_failure_keeps_gemini_when_fallback_is_worse(self):
        real_validate = MealPlannerV4.validate_composition
        real_fallback = MealPlannerV4.fallback
        def limited(*args, **kwargs):
            options = real_validate(*args, **kwargs)
            for option in options:
                option["recipe"]["calorie_adjustment"]["within_practical_range"] = False
                option["recipe"]["calorie_adjustment"]["objective"]["total"] = .5
            return options
        def worse(*args, **kwargs):
            options = real_fallback(*args, **kwargs)
            for option in options:
                option["recipe"]["calorie_adjustment"]["objective"]["total"] = 1
            return options
        def compose(candidates, meal, target, uid, focus, *args):
            return fixtures.DatabaseCatalogTests.raw(candidates, meal, target, focus)
        with patch.object(MealPlannerV4, "validate_composition", side_effect=limited), \
                patch.object(MealPlannerV4, "fallback", side_effect=worse), \
                patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=compose):
            body = self.v4().get_json()
        self.assertEqual(body["meta"]["source"], "gemini")
        self.assertTrue(body["meta"]["calorie_quality"]["limited"])
        self.assertNotIn("fallback_reason", body["meta"])

    def test_portion_objective_normalizes_each_macro_by_its_own_target(self):
        _, _, catalog = self.stored_portion_replay()
        goals = {"protein": 40, "carbs": 100, "fat": 20}
        with patch("app.services.meal_planner_v4.totals", return_value={"calories": 891, "protein": 60, "carbs": 150, "fat": 30}):
            parts = [component("rice", catalog["rice"]["reference_grams"], catalog=catalog)]
            quality = portion_objective(parts, catalog, 891, goals)
        self.assertEqual(quality["macros"], .25)  # 50% error for each, despite different gram scales.

    def test_v41_prompt_explains_joint_macros_and_reference_without_new_fields(self):
        client = GeminiClient()
        goals = {"protein": 55.7, "carbs": 100.2, "fat": 29.7}
        with patch.object(client, "_request", return_value=self.raw) as request:
            client.compose(self.candidates, "lunch", 891, 1, "lose", goals)
        self.assertEqual(request.call_count, 1)
        prompt, schema = request.call_args.args[:2]
        self.assertEqual(prompt["macro_targets"], goals)
        for phrase in ("protein, carbs và fat", "reference_grams", "không", "allowed_role", "không tự giảm target"):
            self.assertIn(phrase, prompt["task"])
        self.assertEqual(set(schema["properties"]["choices"]["items"]["properties"]), {"title", "reason", "components"})

    def test_v41_valid_low_fat_composition_gets_diagnostics_not_rejection(self):
        original, candidates, _ = self.stored_portion_replay()
        refined = refine_options(original, candidates, 891)
        for option in refined[:2]:
            q = option["recipe"]["calorie_adjustment"]
            self.assertTrue(q["macro_limited"])
            self.assertIn("fat", q["unmet_macros"])
            self.assertFalse(q["macro_diagnostics"]["fat"]["target_within_individual_bounds"])
            self.assertEqual(q["joint_feasibility"], "not_proven")
            self.assertGreater(q["worst_macro_error"], .4)
            self.assertTrue(q["within_practical_range"])

    def test_v41_worst_macro_is_visible_even_with_same_mean_objective(self):
        mean = {"total": .1}
        self.assertGreater(quality_score({"objective": mean, "worst_macro_error": .6}),
                           quality_score({"objective": mean, "worst_macro_error": .2}))

    def test_v41_balanced_fallback_can_replace_ai_already_within_kcal_band(self):
        old, candidates, _ = self.stored_portion_replay()
        ai = refine_options(old, candidates, 891)
        fallback = MealPlannerV4.fallback(candidates, "lunch", 891, "maintain", {"avoid": ["fish"]})
        self.assertTrue(all(o["recipe"]["calorie_adjustment"]["within_practical_range"] for o in ai))
        self.assertTrue(better_fallback(ai, fallback, 891))

    def test_v41_small_score_difference_keeps_ai(self):
        old, candidates, _ = self.stored_portion_replay()
        ai = refine_options(old, candidates, 891)
        slightly_better = copy.deepcopy(ai)
        for option in slightly_better:
            option["recipe"]["calorie_adjustment"]["objective"]["total"] -= .001
        self.assertFalse(better_fallback(ai, slightly_better, 891))

    def test_v41_worse_fallback_and_unsafe_fallback_keep_ai(self):
        old, candidates, _ = self.stored_portion_replay()
        ai = refine_options(old, candidates, 891)
        worse = copy.deepcopy(ai)
        for option in worse:
            option["recipe"]["calorie_adjustment"]["objective"]["total"] += 1
        self.assertFalse(better_fallback(ai, worse, 891))
        unsafe = copy.deepcopy(ai)
        unsafe[0]["calories"] = 2000
        self.assertFalse(better_fallback(ai, unsafe, 891))

    def test_v41_bundle_average_cannot_hide_a_worse_option(self):
        old, candidates, _ = self.stored_portion_replay()
        ai = refine_options(old, candidates, 891)
        misleading = copy.deepcopy(ai)
        for option in misleading:
            option["recipe"]["calorie_adjustment"]["objective"]["total"] = 0
            option["recipe"]["calorie_adjustment"]["worst_macro_error"] = 0
        misleading[0]["recipe"]["calorie_adjustment"]["objective"]["total"] = max(quality_score(o["recipe"]["calorie_adjustment"]) for o in ai) + .01
        self.assertFalse(better_fallback(ai, misleading, 891))

    def test_v41_zero_targets_have_explicit_finite_diagnostics(self):
        import math
        old, candidates, _ = self.stored_portion_replay()
        options = refine_options(old, candidates, 891, {"protein": 0, "carbs": 100, "fat": 30})
        for option in options:
            q = option["recipe"]["calorie_adjustment"]
            self.assertIsNone(q["macro_deviation_percent"]["protein"])
            self.assertEqual(q["macro_diagnostics"]["protein"]["target"], 0)
            self.assertTrue(math.isfinite(q["selection_score"]))

    def test_v41_fallback_fits_at_most_six_and_keeps_distinct_primary_ids(self):
        with patch("app.services.meal_planner_v4.fit_portions", wraps=fit_portions) as fit:
            options = MealPlannerV4.fallback(catalog_dishes("lunch"), "lunch", 891, "maintain", {})
        self.assertLessEqual(fit.call_count, FALLBACK_FIT_LIMIT)
        self.assertEqual(len({next(p["dish_id"] for p in o["recipe"]["components"] if p["type"] == "PROTEIN") for o in options}), 3)

    def test_v41_optional_partners_depend_on_macro_budget(self):
        candidates = catalog_dishes("lunch")
        sets = []
        for fat in (5, 30):
            options = MealPlannerV4.fallback(candidates, "lunch", 891, "maintain", {},
                macro_targets={"protein": 55.7, "carbs": 100.2, "fat": fat})
            sets.append({p["dish_id"] for o in options for p in o["recipe"]["components"] if p["type"] in ("DESSERT", "SOUP")})
        self.assertNotEqual(sets[0], sets[1])

    def test_v41_search_budget_does_not_grow_with_catalog_size(self):
        groups = {}
        for role in COMPOSITION_RULES["lunch"]["allowed"]:
            prototype = next(d for d in self.candidates if d["type"] == role)
            groups[role] = [dict(prototype, dish_id=role + str(i)) for i in range(100)]
        with patch("app.services.meal_planner_v4.portion_objective", wraps=portion_objective) as objective:
            shortlist = composition_shortlist(groups, "lunch", 891, None, role_limit=24)
        # <= 1,200 beam expansions; at most 3 completed estimates and 5 scales.
        self.assertLessEqual(objective.call_count, 1200 * 3 * 5)
        self.assertLessEqual(len(shortlist), 12)

    def test_v41_generate_reports_macro_quality_switch_and_one_provider_call(self):
        old, candidates, _ = self.stored_portion_replay()
        raw = {"choices": [{"title": "Replay " + str(i), "reason": "Mock Gemini",
            "components": [{k: p[k] for k in ("type", "dish_id", "grams")} for p in o["recipe"]["components"]]} for i, o in enumerate(old)]}
        budget = {"remaining": {"calories": 891, "protein": 55.7, "carbs": 100.2, "fat": 29.7}, "suggested_meal_targets": {"lunch": 891}}
        with patch("app.services.food_intake_service.FoodIntakeService.daily", return_value=budget), \
                patch("app.services.meal_planner_v4.candidate_pool", return_value=candidates), \
                patch.object(self.app.extensions["nutrifit_gemini"], "compose", return_value=raw) as provider:
            response = self.v4(preferences={"avoid": ["fish"]})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(body["meta"]["source"], "fallback")
        self.assertEqual(body["meta"]["fallback_reason"], "composition_quality")
        self.assertEqual(body["meta"]["fallback_diagnostic"], "BETTER_MACRO_PORTION_COMBINATION")
        self.assertIn("composition_quality", body["meta"])
        self.assertTrue(all(o["recipe"]["provider_source"] == "fallback" for o in body["data"]["options"]))

    def test_v41_generate_passes_actual_macro_budget_to_pool(self):
        budget = {"remaining": {"calories": 2000, "protein": 90, "carbs": 230, "fat": 80}, "suggested_meal_targets": {"lunch": 800}}
        with patch("app.services.food_intake_service.FoodIntakeService.daily", return_value=budget), \
                patch("app.services.meal_planner_v4.candidate_pool", wraps=candidate_pool) as pool:
            self.assertEqual(self.v4().status_code, 200)
        self.assertEqual(pool.call_args.kwargs["macro_targets"], {"protein": 36, "carbs": 92, "fat": 32})

    def test_v41_replace_recomputes_quality_without_touching_other_foods(self):
        from test_meal_v4 import V4Tests
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        protein = next(p for p in option["components"] if p["type"] == "PROTEIN")
        new_id = "chicken" if protein["dish_id"] != "chicken" else "pork"
        with patch("app.services.meal_planner_v4.fit_portions", side_effect=AssertionError("Replace must not refit")), \
                patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=AssertionError("Replace must not generate")):
            response = V4Tests.swap(self, meal, option, "PROTEIN", new_id, 130)
        self.assertEqual(response.status_code, 200)
        updated = response.get_json()["data"]
        changed = updated["options"][0]
        self.assertEqual(updated["options"][1:], meal["options"][1:])
        self.assertEqual([p for p in changed["components"] if p["type"] != "PROTEIN"], [p for p in option["components"] if p["type"] != "PROTEIN"])
        q = changed["recipe"]["calorie_adjustment"]
        self.assertEqual(q["after_kcal"], changed["calories"])
        self.assertEqual(q["before_kcal"], option["calories"])
        self.assertEqual(q["macro_targets"], option["recipe"]["calorie_adjustment"]["macro_targets"])
        for k in ("protein", "carbs", "fat"):
            self.assertEqual(q["macro_diagnostics"][k]["actual"], changed["macros"][k])
        self.assertNotEqual(updated["revision"], meal["revision"])
        self.assertEqual(self.client.get("/api/nutrition/daily?date=2026-10-10", headers=self.headers).get_json()["data"]["consumed"]["calories"], 0)

    def test_v41_replace_reads_old_snapshot_without_quality_metadata(self):
        import json
        from test_meal_v4 import V4Tests
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        recipe = copy.deepcopy(option["recipe"])
        recipe.pop("calorie_adjustment")
        db.session.execute(text("UPDATE NutritionMealDetails SET RecipeJson=:r WHERE OptionId=:id"), {"r": json.dumps(recipe), "id": option["optionId"]})
        db.session.commit()
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        old = next(p for p in option["components"] if p["type"] == "PROTEIN")
        new_id = "chicken" if old["dish_id"] != "chicken" else "pork"
        updated = V4Tests.swap(self, meal, option, "PROTEIN", new_id, 130)
        self.assertEqual(updated.status_code, 200)
        self.assertIn("macro_diagnostics", updated.get_json()["data"]["options"][0]["recipe"]["calorie_adjustment"])

    def test_phase3_diversity_prefers_different_carbs_at_equal_quality(self):
        options = self.validate()
        repeated = copy.deepcopy(options)
        distinct = copy.deepcopy(options)
        for i, (a, b) in enumerate(zip(repeated, distinct)):
            for group in (a, b):
                group["recipe"]["calorie_adjustment"] = {"objective": {"total": .1}}
            next(p for p in a["recipe"]["components"] if p["type"] == "CARB")["dish_id"] = "same-carb"
            next(p for p in b["recipe"]["components"] if p["type"] == "CARB")["dish_id"] = "carb-" + str(i)
        # Pure bundle scoring fixture: IDs here intentionally have no DB lookup.
        self.assertLess(bundle_score(distinct), bundle_score(repeated))
        self.assertEqual(bundle_diversity(distinct)["repetition"]["carb"], 0)

    def test_phase3_diversity_prefers_different_proteins_at_equal_quality(self):
        repeated = self.validate()
        distinct = copy.deepcopy(repeated)
        for i, (a, b) in enumerate(zip(repeated, distinct)):
            next(p for p in a["recipe"]["components"] if p["type"] == "PROTEIN")["dish_id"] = "same-primary"
            next(p for p in b["recipe"]["components"] if p["type"] == "PROTEIN")["dish_id"] = "primary-" + str(i)
        self.assertLess(bundle_diversity(distinct)["penalty"], bundle_diversity(repeated)["penalty"])

    def test_phase3_diversity_budget_cannot_hide_large_macro_quality_loss(self):
        good = self.validate()
        bad = copy.deepcopy(good)
        for i, (a, b) in enumerate(zip(good, bad)):
            a["recipe"]["calorie_adjustment"] = {"objective": {"total": .1}}
            b["recipe"]["calorie_adjustment"] = {"objective": {"total": .3}}
            for part in b["recipe"]["components"]:
                part["dish_id"] += "-unique-" + str(i)
        self.assertLess(bundle_score(good), bundle_score(bad))

    def test_phase3_equal_nutrition_pool_selects_three_carbs_and_primaries(self):
        rows = []
        for role in ("CARB", "PROTEIN", "VEGGIE"):
            template = copy.deepcopy(next(d for d in self.candidates if d["type"] == role))
            for i in range(3 if role != "VEGGIE" else 1):
                rows.append(dict(template, dish_id=role + str(i)))
        options = MealPlannerV4.fallback(rows, "lunch", 800, "maintain", {})
        for role in ("CARB", "PROTEIN"):
            self.assertEqual(len({next(p["dish_id"] for p in o["recipe"]["components"] if p["type"] == role) for o in options}), 3)

    def test_phase3_single_valid_carb_does_not_prevent_three_menus(self):
        carb = next(d for d in self.candidates if d["type"] == "CARB")
        rows = [d for d in self.candidates if d["type"] != "CARB" or d["dish_id"] == carb["dish_id"]]
        options = MealPlannerV4.fallback(rows, "lunch", 800, "maintain", {})
        self.assertEqual(len(options), 3)
        self.assertEqual(bundle_diversity(options)["repetition"]["carb"], 1)

    def test_phase3_bundle_diversity_cannot_spend_more_than_quality_noise_budget(self):
        def option(i, carb, value):
            return {"calories": 891, "recipe": {"components": [
                {"type": "CARB", "dish_id": carb}, {"type": "PROTEIN", "dish_id": "primary" + str(i)}],
                "calorie_adjustment": {"objective": {"total": value}}}}
        good = [option(i, "shared", .1) for i in range(3)]
        diverse = [option(i, "carb" + str(i), .125) for i in range(3)]
        self.assertLess(bundle_score(diverse), bundle_score(good))
        chosen = select_fallback_bundle(good + diverse, "lunch", 891)
        self.assertTrue(all(o["recipe"]["calorie_adjustment"]["objective"]["total"] <= .12 for o in chosen))

    def test_phase3_diverse_fallback_preserves_avoid_and_preferences(self):
        from app.services.meal_preferences import violates
        prefs = {"avoid": ["fish"], "prefer": ["chicken"], "preferEasy": True}
        rows = candidate_pool(prefs, "lunch", "maintain", "phase3-preferences", target=891,
                              macro_targets={"protein": 55.7, "carbs": 100.2, "fat": 29.7})
        index = {d["dish_id"]: d for d in rows}
        options = MealPlannerV4.fallback(rows, "lunch", 891, "maintain", prefs)
        for option in options:
            self.assertEqual(option["recipe"]["preferences"], {k:v for k,v in prefs.items() if k != "preferEasy"})
            for part in option["recipe"]["components"]:
                dish = index[part["dish_id"]]
                self.assertFalse(violates(dish, prefs))
                self.assertIn("lunch", dish["meal_types"])
                self.assertTrue(dish["min_grams"] <= part["grams"] <= dish["max_grams"])

    def test_phase3_mass_penalty_increases_for_uniform_portion_inflation(self):
        original, _, catalog = self.stored_portion_replay()
        parts = original[0]["recipe"]["components"]
        reference = [component(p["dish_id"], catalog[p["dish_id"]]["reference_grams"], catalog=catalog) for p in parts]
        doubled = [dict(p, grams=p["grams"] * 2) for p in reference]
        self.assertGreater(portion_quality(doubled, catalog)["penalty"], portion_quality(reference, catalog)["penalty"])

    def test_phase3_optional_soup_is_not_free_even_at_reference(self):
        index = {d["dish_id"]: d for d in catalog_dishes("lunch")}
        parts = [component(next(d["dish_id"] for d in index.values() if d["type"] == role),
            next(d["reference_grams"] for d in index.values() if d["type"] == role), catalog=index)
            for role in ("CARB", "PROTEIN", "VEGGIE", "DESSERT")]
        soup = next(d for d in index.values() if d["type"] == "SOUP")
        extra = parts + [component(soup["dish_id"], soup["reference_grams"], catalog=index)]
        self.assertGreater(portion_quality(extra, index)["penalty"], portion_quality(parts, index)["penalty"])
        self.assertEqual(portion_quality(extra, index)["optional_count"], 2)

    def test_phase3_mass_score_uses_references_not_universal_gram_limit(self):
        original, _, catalog = self.stored_portion_replay()
        parts = original[0]["recipe"]["components"]
        larger = [dict(p, grams=p["grams"] * 2) for p in parts]
        scaled = copy.deepcopy(catalog)
        for dish in scaled.values():
            dish["reference_grams"] *= 2
        self.assertAlmostEqual(portion_quality(larger, scaled)["penalty"], portion_quality(parts, catalog)["penalty"])

    def test_phase3_diversity_only_minor_gain_does_not_switch_source(self):
        original, candidates, _ = self.stored_portion_replay()
        ai = refine_options(original, candidates, 891)
        fallback = copy.deepcopy(ai)
        for option in fallback:
            option["recipe"]["calorie_adjustment"]["objective"]["total"] -= .001
        self.assertFalse(better_fallback(ai, fallback, 891))

    def test_phase3_generate_keeps_good_gemini_and_reports_bundle_diversity(self):
        def compose(candidates, meal, target, uid, focus, *args):
            return fixtures.DatabaseCatalogTests.raw(candidates, meal, target, focus, macro_targets=args[0])
        with patch.object(self.app.extensions["nutrifit_gemini"], "compose", side_effect=compose) as provider:
            response = self.v4()
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["meta"]["source"], "gemini")
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(body["meta"]["composition_quality"]["diversity"], bundle_diversity(body["data"]["options"]))
        self.assertTrue(all(o["recipe"]["provider_source"] == "gemini" for o in body["data"]["options"]))

    def test_phase3_new_quality_does_not_rewrite_cached_snapshot_or_intake(self):
        meal = self.v4().get_json()["data"]
        with patch("app.services.meal_planner_v4.fit_portions", side_effect=AssertionError("Cached meal cannot refit")):
            again = self.v4().get_json()
        self.assertEqual(again["data"], meal)
        self.assertEqual(again["meta"]["source"], "cached")
        self.assertEqual(self.client.get("/api/nutrition/daily?date=2026-10-10", headers=self.headers).get_json()["data"]["consumed"]["calories"], 0)

    def test_compose_fix_support_is_dynamic_and_uses_only_supplied_optional_dishes(self):
        rows = catalog_dishes("lunch")
        goals = {"protein": 55.7, "carbs": 100.2, "fat": 29.7}
        support = GeminiClient.optional_macro_support(rows, "lunch", goals, {})
        self.assertEqual(support["DESSERT"]["fat"], "usda_171705")
        reduced = [d for d in rows if d["dish_id"] != support["DESSERT"]["fat"]]
        different = GeminiClient.optional_macro_support(reduced, "lunch", goals, {})
        self.assertNotEqual(different["DESSERT"]["fat"], support["DESSERT"]["fat"])
        ids = {d["dish_id"] for d in reduced}
        self.assertTrue(all(i in ids for role in different.values() for i in role.values()))
        self.assertFalse(set(different) & set(COMPOSITION_RULES["lunch"]["required"]))

    def test_compose_fix_support_excludes_avoid_wrong_meal_and_raw_food(self):
        base = copy.deepcopy(next(d for d in self.candidates if d["type"] == "DESSERT"))
        base["macros_per_100g"]["fat"] = 10
        rows = [dict(base, dish_id="avoided", ingredients=["milk"]),
                dict(base, dish_id="wrong-meal", meal_types=["breakfast"]),
                dict(base, dish_id="raw-only", preparation_state="raw"),
                dict(base, dish_id="permitted", ingredients=[])]
        support = GeminiClient.optional_macro_support(rows, "dinner", {"fat": 20}, {"avoid": ["milk"]})
        self.assertEqual(support, {"DESSERT": {"fat": "permitted"}})

    def test_compose_fix_no_fat_support_is_not_invented_after_avoid(self):
        prototype = copy.deepcopy(next(d for d in self.candidates if d["type"] == "DESSERT"))
        rich = dict(prototype, dish_id="rich", ingredients=["soy"])
        rich["macros_per_100g"] = {"protein": 2, "carbs": 8, "fat": 15, "fiber": 1}
        lean = dict(prototype, dish_id="lean", ingredients=[])
        lean["macros_per_100g"] = {"protein": 1, "carbs": 20, "fat": 0, "fiber": 1}
        support = GeminiClient.optional_macro_support([rich, lean], "lunch", {"fat": 30, "carbs": 100}, {"avoid": ["soy"]})
        self.assertNotIn("fat", support["DESSERT"])
        self.assertEqual(support["DESSERT"]["carbs"], "lean")

    def test_compose_fix_zero_macro_goals_and_no_optional_roles_have_no_hint(self):
        self.assertEqual(GeminiClient.optional_macro_support(self.candidates, "lunch", {"fat": 0}, {}), {})
        required = [d for d in self.candidates if d["type"] in COMPOSITION_RULES["lunch"]["required"]]
        self.assertEqual(GeminiClient.optional_macro_support(required, "lunch", {"fat": 30}, {}), {})

    def test_compose_fix_prompt_explains_optional_use_and_avoids_redundant_components(self):
        client = GeminiClient()
        with patch.object(client, "_request", return_value=self.raw) as request:
            client.compose(self.candidates, "lunch", 891, 1, "maintain", {"protein": 55.7, "carbs": 100.2, "fat": 29.7})
        prompt, schema = request.call_args.args[:2]
        self.assertEqual(request.call_count, 1)
        self.assertEqual(prompt["optional_roles"], ["SOUP", "DESSERT"])
        for phrase in ("trần từng macro", "max_grams", "không thể giải quyết", "không thêm component dư thừa", "không phải recipe", "giảm phần khác trong min/max"):
            self.assertIn(phrase, prompt["task"])
        self.assertEqual(set(schema["properties"]["choices"]["items"]["properties"]), {"title", "reason", "components"})
        self.assertNotIn("recipes", prompt)
        self.assertNotIn("user_id", prompt)

    def test_compose_fix_balanced_required_only_choices_remain_valid(self):
        rows = catalog_dishes("lunch")
        compositions = [
            [("CARB", "usda_169704", 180), ("PROTEIN", "beef", 134), ("VEGGIE", "usda_168390", 150)],
            [("CARB", "rice", 180), ("PROTEIN", "beef", 134), ("VEGGIE", "usda_169229", 150)],
            [("CARB", "usda_168928", 180), ("PROTEIN", "beef", 134), ("VEGGIE", "usda_169238", 150)]]
        raw = {"choices": [{"title": "Đủ nhóm " + str(i), "reason": "Không cần món bổ sung.",
            "components": [{"type": r, "dish_id": d, "grams": g} for r,d,g in parts]} for i,parts in enumerate(compositions)]}
        options = MealPlannerV4.validate_composition(raw, rows, "lunch", 600, "maintain", {},
            adjust_portions=True, macro_targets={"protein": 37.5, "carbs": 67.5, "fat": 20})
        self.assertTrue(all(len(o["recipe"]["components"]) == 3 for o in options))

    def test_compose_fix_replays_phase4_with_optional_fat_without_changing_schema_or_source(self):
        scenarios = [("lunch", 891, {"protein": 55.7, "carbs": 100.2, "fat": 29.7}, {"avoid": ["fish"]},
            [[("usda_169704",250), ("chicken",130), ("vegetables_oil",150)],
             [("sweet_potato",230), ("usda_172388",130), ("usda_169238",150)],
             [("rice",220), ("tofu",180), ("usda_170397",150)]]),
            ("dinner", 600, {"protein":37.5,"carbs":67.5,"fat":20}, {"avoid":["fish","milk"]},
            [[("sweet_potato",180), ("chicken",130), ("usda_169967",150)],
             [("usda_169704",180), ("beef",134), ("usda_168390",150)],
             [("rice",180), ("tofu",180), ("usda_170397",150)]])]
        for meal,target,goals,prefs,compositions in scenarios:
            with self.subTest(meal=meal):
                salt = "v41-replay" if meal == "lunch" else "phase4-dinner"
                rows = candidate_pool(prefs, meal, "maintain", salt, target=target, macro_targets=goals)
                index = {d["dish_id"]:d for d in rows}
                # Controlled provider fixture illustrates supplementation; it
                # does not prove that a real model follows the new prompt.
                def raw(extra):
                    return {"choices": [{"title": "Replay " + str(i), "reason": "Mock bổ trợ macro.",
                        "components": [{"type":index[d]["type"], "dish_id":d, "grams":g} for d,g in parts + extra]}
                        for i,parts in enumerate(compositions)]}
                original = MealPlannerV4.validate_composition(raw([]), list(index.values()), meal, target,
                    "maintain", prefs, adjust_portions=True, macro_targets=goals)
                enriched_raw = raw([("usda_171705",100)])
                with patch.object(GeminiClient, "_request", return_value=enriched_raw) as provider:
                    response = GeminiClient().compose(rows, meal, target, 1, "maintain", goals, {"preferences":prefs})
                enriched = MealPlannerV4.validate_composition(response, list(index.values()), meal, target,
                    "maintain", prefs, adjust_portions=True, macro_targets=goals)
                self.assertEqual(provider.call_count,1)
                self.assertLess(sum(abs(o["macros"]["fat"]-goals["fat"]) for o in enriched),
                                sum(abs(o["macros"]["fat"]-goals["fat"]) for o in original))
                self.assertTrue(all(o["recipe"]["calorie_adjustment"]["macro_feasible_ranges"]["fat"]["maximum"] >= goals["fat"] for o in enriched))
                self.assertTrue(all(o["recipe"]["provider_source"]=="gemini" for o in enriched))
                self.assertEqual(len({tuple(p["dish_id"] for p in o["recipe"]["components"]) for o in enriched}),3)

    def test_compose_fix_signal_is_bounded_by_optional_roles_and_three_macros(self):
        goals={"protein":55.7,"carbs":100.2,"fat":29.7}
        rows=catalog_dishes("lunch")
        first=GeminiClient.optional_macro_support(rows,"lunch",goals,{})
        self.assertEqual(first,GeminiClient.optional_macro_support(list(reversed(rows)),"lunch",goals,{}))
        self.assertLessEqual(sum(len(v) for v in first.values()),6)

    def test_v41_retired_recipe_requires_refresh_and_preserves_snapshot(self):
        from test_meal_v4 import V4Tests
        meal = self.v4().get_json()["data"]
        option = meal["options"][0]
        untouched = next(p for p in option["components"] if p["type"] == "CARB")
        db.session.execute(text("UPDATE NutritionFoodCatalog SET IsActive=0 WHERE DishId=:id"), {"id": untouched["dish_id"]})
        db.session.commit()
        old = next(p for p in option["components"] if p["type"] == "PROTEIN")
        updated = V4Tests.swap(self, meal, option, "PROTEIN", "chicken" if old["dish_id"] != "chicken" else "pork", 130)
        self.assertEqual(updated.status_code, 409)
        self.assertEqual(updated.get_json()["code"], "CATALOG_REFRESH_REQUIRED")
        stored = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"]
        self.assertEqual(stored["revision"], meal["revision"])
        self.assertEqual(stored["options"], meal["options"])
        self.assertEqual(next(p for p in stored["options"][0]["components"] if p["type"] == "CARB"), untouched)


if __name__ == "__main__":
    unittest.main()
