"""Frozen 102-dish historical research checks; current runtime is 158; no app factory, database or HTTP calls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("vietnamese_draft_validator", ROOT / "setup/validate_vietnamese_catalog_draft.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class VietnameseDraftTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT / "setup/drafts/vietnamese_catalog_v2"
        load = lambda p: json.loads(p.read_text(encoding="utf-8"))
        self.targets = load(folder / "targets.json")
        self.drafts = load(folder / "draft_dishes.json")
        self.seed = load(ROOT / "backend/tests/fixtures/pre_rebuild_catalog.json")
        self.sources = load(folder / "ingredient_sources.json")

    def check(self):
        return VALIDATOR.validate(self.targets, self.drafts, self.seed, self.sources)

    def test_100_curated_targets_preserve_all_102_runtime_ids(self):
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertEqual((result["targets"], result["retained_ids"], result["new_targets"]), (100, 60, 40))
        self.assertEqual(result["preserved_runtime_ids"], 102)
        self.assertEqual(len(self.targets["research_archive"]["targets_snapshot"]["targets"]), 250)

    def test_unknown_data_remains_pending_not_importable_or_zero_filled(self):
        result = self.check()
        self.assertEqual(result["statuses"], {"PENDING": 9, "READY_ESTIMATED": 40})
        self.assertFalse(result["authorized_for_import"])
        self.assertTrue(all(d["calories_per_100g"] is None for d in self.drafts["drafts"] if d["review_status"] == "PENDING"))

    def test_promoting_incomplete_record_to_ready_is_rejected(self):
        self.drafts["drafts"][0]["review_status"] = "READY"
        self.assertTrue(any("READY_WITH_MISSING_EVIDENCE" in e for e in self.check()["errors"]))

    def test_duplicate_ids_and_substantially_identical_new_recipes_are_rejected(self):
        new = [t for t in self.targets["targets"] if not t["existing_dish_id"]]
        new[1]["dish_id"] = new[0]["dish_id"]
        new[1]["recipe_identity"] = new[0]["recipe_identity"]
        errors = self.check()["errors"]
        self.assertIn("TARGET_DUPLICATE_OR_INVALID_ID", errors)
        self.assertIn("DUPLICATE_NEW_RECIPE", errors)

    def test_existing_id_must_not_be_replaced(self):
        self.targets["targets"][0]["dish_id"] = "vn_replacement"
        self.assertIn("EXISTING_IDS_MUST_BE_PRESERVED", self.check()["errors"])

    def test_fish_sauce_and_peanuts_are_declared_without_allergy_guarantee(self):
        dish = next(d for d in self.drafts["drafts"] if d["name"] == "Nộm đu đủ xanh")
        self.assertTrue({"fish", "seafood", "peanut"} <= set(dish["ingredients"]))
        self.assertTrue(dish["provenance"]["recipe"]["allergen_review_complete"])
        self.assertTrue(any("allergy" in s for s in dish["provenance"]["limitations"]))
        dish["ingredients"].remove("fish")
        self.assertTrue(any("INGREDIENT_TAG_MISSING" in e for e in self.check()["errors"]))

    def test_invalid_grams_and_nonfinite_nutrients_are_rejected(self):
        d = self.drafts["drafts"][0]
        d.update(min_grams=100, reference_grams=50, max_grams=300)
        d["macros_per_100g"]["fat"] = float("nan")
        errors = self.check()["errors"]
        self.assertTrue(any("PORTION_ORDER" in e for e in errors))
        self.assertTrue(any("NUTRIENT_UNIT_OR_VALUE" in e for e in errors))

    def test_complete_lunch_main_is_not_silently_accepted_by_existing_rules(self):
        d = next(d for d in self.drafts["drafts"] if d["type"] == "MAIN")
        d["meal_types"] = ["lunch"]
        self.assertTrue(any("CURRENT_MAIN_RULES" in e for e in self.check()["errors"]))

    def test_published_grams_do_not_invent_yield_or_convert_household_measures(self):
        d = next(d for d in self.drafts["drafts"] if d["name"] == "Canh tôm rau ngót bắp")
        # Original observations remain archived; the usable reference variant
        # discloses chosen gram amounts and an assumed (never measured) yield.
        d = next(h for h in d["research_history"] if h["phase"] == "before_catalog_completion")
        items = {i["name"]: i for i in d["provenance"]["recipe"]["ingredients"]}
        self.assertEqual(items["Dầu ăn"]["edible_grams"], 12)
        self.assertIsNone(items["Nước dùng"]["edible_grams"])
        self.assertIsNone(d["provenance"]["recipe"]["finished_edible_grams"])

    def test_drafts_cannot_be_marked_active_even_when_status_is_pending(self):
        self.drafts["drafts"][0]["active"] = True
        self.assertTrue(any("DRAFT_CANNOT_BE_ACTIVE_OR_IMPORT_READY" in e for e in self.check()["errors"]))

    def test_phase2_keeps_twelve_existing_ids_and_archives_prior_research(self):
        batch = self.drafts["phase2_batch_ids"]
        self.assertEqual(len(batch), 12)
        self.assertEqual(len(set(batch)), 12)
        for identifier in batch:
            d = next(d for d in self.drafts["drafts"] if d["dish_id"] == identifier)
            self.assertEqual(d["review_status"], "READY_ESTIMATED")
            self.assertEqual(d["research_history"][0]["phase"], 1)
            self.assertTrue(d["research_history"][0]["provenance"]["recipe"]["ingredients"])
            archived = next(h for h in d["research_history"] if h["phase"] == "strict_research_before_practical_estimates")
            self.assertTrue(archived["provenance"]["recipe"]["ingredients"])
            self.assertIsNotNone(d["calories_per_100g"])
            self.assertFalse(d["provenance"]["recipe"]["finished_weight_measured"])
        self.assertEqual(self.check()["errors"], [])

    def test_primary_ingredient_values_are_not_complete_dish_values(self):
        sources = {s["source_id"]: s for s in self.sources["sources"]}
        self.assertGreaterEqual(len(sources), 28)
        self.assertEqual(sources["vnt2007_3025"]["nutrients_per_100g"]["calories"], 95)
        self.assertIsNone(sources["vnt2007_4086"]["nutrients_per_100g"]["fat"])
        self.assertIsNone(sources["vnt2007_4002"]["nutrients_per_100g"]["fat"])
        self.assertTrue(all(s["nutrients_per_100g"]["fiber"] is None for s in sources.values() if s["source_id"].startswith("vnt2007_")))
        for identifier in self.drafts["phase2_batch_ids"]:
            dish = next(d for d in self.drafts["drafts"] if d["dish_id"] == identifier)
            self.assertEqual(VALIDATOR.calculate_recipe(dish["provenance"]["recipe"], sources, estimated=True)["status"], "CALCULATED")

    def test_aliases_are_draft_only_and_bun_rieu_is_a_broader_name(self):
        dish = next(d for d in self.drafts["drafts"] if d["dish_id"] == "vn_bun_rieu_cua")
        generic = next(a for a in dish["provenance"]["name_aliases"] if a["name"] == "Bún riêu")
        self.assertEqual(generic["equivalence"], "broader")
        self.assertFalse(generic["approved_for_runtime"])
        generic["approved_for_runtime"] = True
        self.assertTrue(any("DRAFT_ALIAS_NOT_RUNTIME_APPROVED" in e for e in self.check()["errors"]))

    def test_recipe_added_sauces_and_sesame_keep_avoid_tags(self):
        tofu = next(d for d in self.drafts["drafts"] if d["dish_id"] == "vn_dau_phu_sot_ca_chua")
        self.assertTrue({"soy", "fish", "seafood"} <= set(tofu["ingredients"]))
        cabbage = next(d for d in self.drafts["drafts"] if d["dish_id"] == "vn_cai_thia_xao_nam")
        self.assertIn("sesame", cabbage["ingredients"])
        cabbage["ingredients"].remove("sesame")
        self.assertTrue(any("INGREDIENT_TAG_MISSING" in e for e in self.check()["errors"]))

    def test_unknown_source_duplicate_source_and_cellulose_mapping_fail(self):
        self.sources["sources"].append(copy.deepcopy(self.sources["sources"][0]))
        self.assertIn("DUPLICATE_SOURCE_ID", self.check()["errors"])
        self.sources["sources"][0]["nutrients_per_100g"]["fiber"] = .4
        self.assertIn("CELLULOSE_IS_NOT_TOTAL_DIETARY_FIBER", self.check()["errors"])
        d = next(d for d in self.drafts["drafts"] if d["dish_id"] == "vn_thit_kho_tieu")
        d["provenance"]["recipe"]["ingredients"][0]["nutrient_source"] = "invented_source"
        self.assertTrue(any("UNKNOWN_INGREDIENT_SOURCE" in e for e in self.check()["errors"]))

    def test_new_draft_cannot_duplicate_an_existing_runtime_name(self):
        d = next(d for d in self.drafts["drafts"] if d["dish_id"] == "vn_thit_kho_tieu")
        d["name"] = "Cơm trắng"
        self.assertTrue(any("NEW_NAME_COLLIDES_WITH_EXISTING" in e for e in self.check()["errors"]))

    def test_previous_pho_snapshot_cannot_be_rewritten(self):
        d = next(d for d in self.drafts["drafts"] if d["dish_id"] == "pho_beef")
        d["baseline_snapshot"]["reference_grams"] = 1
        self.assertTrue(any("BASELINE_SNAPSHOT_CHANGED" in e for e in self.check()["errors"]))


class PracticalEstimateTests(unittest.TestCase):
    setUp = VietnameseDraftTests.setUp
    check = VietnameseDraftTests.check

    def ready(self, identifier="vn_thit_kho_tieu"):
        return next(d for d in self.drafts["drafts"] if d["dish_id"] == identifier)

    def sources_by_id(self):
        return {s["source_id"]: s for s in self.sources["sources"]}

    def test_twelve_estimates_reproduce_all_macros_and_servings(self):
        for identifier in self.drafts["phase2_batch_ids"]:
            dish = self.ready(identifier)
            self.assertEqual(VALIDATOR.readiness_blockers(dish, self.sources_by_id()), [])
            recipe = dish["provenance"]["recipe"]
            result = VALIDATOR.calculate_recipe(recipe, self.sources_by_id(), estimated=True)
            self.assertEqual(result["status"], "CALCULATED")
            self.assertAlmostEqual(result["per_100g"]["calories"], dish["calories_per_100g"], places=4)
            for macro in ("protein", "carbs", "fat", "fiber"):
                self.assertEqual(result["per_100g"][macro], dish["macros_per_100g"][macro])
            self.assertAlmostEqual(recipe["finished_edible_grams"] / recipe["servings"], dish["reference_grams"], places=2)

    def test_estimates_do_not_claim_measured_yields(self):
        dish = self.ready()
        recipe = dish["provenance"]["recipe"]
        self.assertFalse(recipe["finished_weight_measured"])
        self.assertFalse(recipe["finished_weight_verified"])
        self.assertTrue(recipe["finished_weight_evidence"]["not_measured"])
        self.assertEqual(VALIDATOR.calculate_recipe(recipe, self.sources_by_id())["status"], "BLOCKED")
        self.assertEqual(VALIDATOR.calculate_recipe(recipe, self.sources_by_id(), estimated=True)["status"], "CALCULATED")

    def test_missing_assumptions_or_estimate_disclosure_blocks_ready(self):
        dish = self.ready()
        dish["provenance"]["recipe"]["assumptions"] = []
        self.assertIn("ESTIMATE_ASSUMPTIONS_REQUIRED", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))
        dish["provenance"]["recipe"]["finished_weight_evidence"]["not_measured"] = False
        self.assertIn("ESTIMATED_WEIGHT_DISCLOSURE_REQUIRED", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))

    def test_missing_fat_is_not_filled_by_estimate_mode(self):
        dish = self.ready()
        self.sources_by_id()["smiling2013_7018"]["nutrients_per_100g"]["fat"] = None
        self.assertIn("INGREDIENT_NUTRIENTS_INCOMPLETE", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))
        self.assertTrue(any("READY_WITH_MISSING_EVIDENCE" in e for e in self.check()["errors"]))

    def test_finished_mass_discard_and_evaporation_must_balance(self):
        dish = self.ready()
        dish["provenance"]["recipe"]["mass_balance"]["evaporated_grams"] += 100
        self.assertIn("ESTIMATED_MASS_BALANCE_MISMATCH", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))

    def test_negative_nonfinite_grams_and_retention_over_one_fail(self):
        recipe = self.ready()["provenance"]["recipe"]
        item = recipe["ingredients"][0]
        for value in (-1, float("nan"), float("inf"), None):
            item["edible_grams"] = value
            self.assertEqual(VALIDATOR.calculate_recipe(recipe, self.sources_by_id(), estimated=True)["status"], "BLOCKED")
        item["edible_grams"] = 500
        item["retention_factors"]["fat"] = 1.1
        self.assertIn("RETENTION_EVIDENCE_REQUIRED", VALIDATOR.readiness_blockers(self.ready(), self.sources_by_id()))

    def test_tampered_output_and_omitted_oil_are_detected(self):
        dish = self.ready()
        dish["calories_per_100g"] += 10
        self.assertIn("RECIPE_NUTRIENT_MISMATCH", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))
        dish["provenance"]["recipe"]["ingredients"] = [i for i in dish["provenance"]["recipe"]["ingredients"] if "oil" not in i["tags"]]
        self.assertIn("ESTIMATED_MASS_BALANCE_MISMATCH", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))

    def test_source_code_and_url_cannot_be_fabricated_in_references(self):
        dish = self.ready()
        dish["provenance"]["nutrition_references"][0]["food_code"] = "made-up"
        self.assertIn("SOURCE_REFERENCE_MISMATCH", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))
        self.sources["sources"][0]["url"] = "https://example.invalid/fake"
        self.assertIn("SOURCE_URL_NOT_REAL", self.check()["errors"])

    def test_published_cooked_profile_cannot_receive_yield_or_retention_twice(self):
        dish = self.ready("vn_cai_ngot_luoc")
        dish["provenance"]["recipe"]["ingredients"][0]["retention_factors"]["protein"] = .9
        self.assertIn("COOKED_PROFILE_DOUBLE_CORRECTION", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))

    def test_estimated_portions_and_declared_serving_count_agree(self):
        dish = self.ready()
        dish["reference_grams"] = 150
        self.assertIn("ESTIMATED_SERVING_MISMATCH", VALIDATOR.readiness_blockers(dish, self.sources_by_id()))

    def test_review_batch_contains_eleven_new_ids_and_one_separate_update(self):
        batch = json.loads((ROOT / "setup/drafts/vietnamese_catalog_v2/review_batch.json").read_text(encoding="utf-8"))
        self.assertFalse(batch["apply_authorized"])
        self.assertEqual(len(batch["dishes"]), 11)
        self.assertEqual(len(batch["review_existing"]), 1)
        self.assertEqual(batch["review_existing"][0]["dish"]["dish_id"], "pho_beef")
        self.assertFalse({d["dish_id"] for d in batch["dishes"]} & {d["dish_id"] for d in self.seed["dishes"]})
        self.assertEqual(batch["legacy_menus"], [])
        for row in batch["dishes"]:
            original = self.ready(row["dish_id"])
            self.assertEqual(row["provenance"], original["provenance"])
            self.assertTrue(row["estimated"])
            self.assertFalse(original["active"])

    def test_curated_list_cannot_discard_existing_runtime_id(self):
        self.targets["preserved_runtime_ids"].remove("rice")
        self.assertIn("EXISTING_IDS_MUST_BE_PRESERVED", self.check()["errors"])


class RecipeArithmeticTests(unittest.TestCase):
    """Artificial arithmetic fixtures only; these are not researched food profiles."""
    def setUp(self):
        self.sources = {"toy": {"verified": True, "state": "cooked", "state_verified": True,
                               "nutrients_per_100g": {"calories": 165, "protein": 10, "carbs": 20, "fat": 5, "fiber": 2}}}
        self.recipe = {"finished_edible_grams": 150, "finished_weight_verified": True,
                       "finished_weight_evidence": "Artificial unit-test denominator, not a kitchen measurement",
                       "ingredient_list_complete": True,
                       "ingredients": [{"state": "cooked", "nutrient_source": "toy", "nutrient_match_verified": True,
                                        "edible_grams": 100, "state_or_edible_basis_verified": True,
                                        "retention_factors": {k: 1 for k in ("calories", "protein", "carbs", "fat", "fiber")},
                                        "retention_evidence": "Artificial as-served fixture, no additional cooking"}]}

    def calculate(self):
        return VALIDATOR.calculate_recipe(self.recipe, self.sources)

    def test_finished_edible_denominator_and_macro_arithmetic(self):
        result = self.calculate()
        self.assertEqual(result["status"], "CALCULATED")
        self.assertEqual(result["per_100g"]["calories"], 110)
        self.assertAlmostEqual(result["per_100g"]["protein"], 6.6667)
        self.assertAlmostEqual(result["per_100g"]["fat"], 3.3333)

    def test_retention_applies_once_and_total_input_weight_is_not_denominator(self):
        self.recipe["ingredients"][0]["retention_factors"]["fat"] = .8
        result = self.calculate()
        self.assertAlmostEqual(result["per_100g"]["fat"], 2.6667)
        self.assertEqual(result["finished_edible_grams"], 150)

    def test_unknown_or_zero_finished_weight_cannot_produce_nutrients(self):
        for weight in (None, 0, -1, float("nan")):
            self.recipe["finished_edible_grams"] = weight
            self.assertIsNone(self.calculate()["per_100g"])
        self.recipe["finished_edible_grams"] = 150
        self.recipe["finished_weight_verified"] = False
        self.assertIsNone(self.calculate()["per_100g"])

    def test_raw_cooked_mismatch_and_household_units_cannot_be_calculated(self):
        self.recipe["ingredients"][0]["state"] = "raw"
        self.assertIn("INGREDIENT_SOURCE_STATE_MISMATCH", self.calculate()["blockers"])
        self.recipe["ingredients"][0]["edible_grams"] = None
        self.recipe["ingredients"][0]["reported_quantity"] = 1
        self.recipe["ingredients"][0]["reported_unit"] = "muỗng canh"
        self.assertIn("INGREDIENT_GRAMS_REQUIRED", self.calculate()["blockers"])

    def test_missing_fat_is_not_zero_and_missing_fiber_stays_unknown(self):
        self.sources["toy"]["nutrients_per_100g"]["fat"] = None
        self.assertIsNone(self.calculate()["per_100g"])
        self.sources["toy"]["nutrients_per_100g"]["fat"] = 5
        self.sources["toy"]["nutrients_per_100g"]["fiber"] = None
        self.assertIsNone(self.calculate()["per_100g"]["fiber"])
        self.assertFalse(self.calculate()["fiber_complete"])

    def test_unknown_source_or_missing_retention_cannot_be_treated_as_zero_loss(self):
        self.recipe["ingredients"][0]["nutrient_source"] = "missing"
        self.assertIsNone(self.calculate()["per_100g"])
        self.recipe["ingredients"][0]["nutrient_source"] = "toy"
        self.recipe["ingredients"][0]["retention_factors"] = None
        self.assertIn("RETENTION_EVIDENCE_REQUIRED", self.calculate()["blockers"])

    def test_ready_boolean_claims_do_not_override_recipe_calculation(self):
        dish = {"reference_grams": 100, "min_grams": 50, "max_grams": 200, "review_status": "READY",
                "calories_per_100g": 165, "macros_per_100g": {"protein": 10, "carbs": 20, "fat": 5},
                "ingredients": [], "provenance": {"recipe": self.recipe, "method": "unit-test-calculation",
                "license_status": "VERIFIED_FOR_REUSE", "portion_evidence": "unit-test", "portion_verified": True,
                "nutrition_references": [{"verified": True, "url": "https://example.invalid/toy", "food_code": "toy"}]}}
        self.recipe["allergen_review_complete"] = True
        self.recipe["ingredients"][0]["tags"] = []
        self.sources["toy"]["reuse_status"] = "VERIFIED_FOR_REUSE"
        self.assertIn("RECIPE_NUTRIENT_MISMATCH", VALIDATOR.readiness_blockers(dish, self.sources))
        dish["calories_per_100g"] = 110
        dish["macros_per_100g"] = {"protein": 6.6667, "carbs": 13.3333, "fat": 3.3333}
        self.assertEqual(VALIDATOR.readiness_blockers(dish, self.sources), [])


if __name__ == "__main__":
    unittest.main()
