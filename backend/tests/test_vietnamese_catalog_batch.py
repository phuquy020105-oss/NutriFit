"""Review-only Vietnamese batch integration in disposable SQLite; never local MySQL."""
import json
import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch
from sqlalchemy import text
from app.extensions import db
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.services.food_catalog_service import catalog_dishes, component, snapshot_component, totals
from app.services.meal_planner_v4 import MealPlannerV4, candidate_pool
from app.services.meal_preferences import violates
from catalog_fixture import load_seed
import seed_nutrition_catalog as seed_tool
import test_meal_api as fixtures
import test_quick_food as quick_fixtures


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "backend/tests/fixtures/pre_rebuild_catalog.json"


class ReviewBatchIntegrationTests(unittest.TestCase):
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    set_premium = quick_fixtures.QuickFoodTests.set_premium
    daily = quick_fixtures.QuickFoodTests.daily
    count = quick_fixtures.QuickFoodTests.count

    def setUp(self):
        quick_fixtures.QuickFoodTests.setUp(self)
        self.assertEqual(db.engine.url.drivername, "sqlite")
        self.assertEqual(db.engine.url.database, ":memory:")
        seed = load_seed()
        FoodCatalogRepository.insert_missing(seed["dishes"], seed["legacy_menus"])
        db.session.commit()
        self.batch = json.loads((ROOT / "setup/drafts/vietnamese_catalog_v2/review_batch.json").read_text(encoding="utf-8"))

    def install_batch(self):
        result = FoodCatalogRepository.insert_missing(self.batch["dishes"], [])
        db.session.commit()
        return result

    def test_insert_batch_is_idempotent_and_existing_pho_is_untouched(self):
        before = db.session.execute(text("SELECT * FROM NutritionFoodCatalog WHERE DishId='pho_beef'")).mappings().one()
        before = dict(before)
        self.assertEqual(self.install_batch(), {"dishes": 11, "menus": 0})
        self.assertEqual(self.install_batch(), {"dishes": 0, "menus": 0})
        after = dict(db.session.execute(text("SELECT * FROM NutritionFoodCatalog WHERE DishId='pho_beef'")).mappings().one())
        self.assertEqual(before, after)
        self.assertEqual(len(catalog_dishes()), 113)

    def test_database_review_detects_pending_and_matching_without_writes(self):
        before = seed_tool.inspect_review_batch(self.batch, FoodCatalogRepository)
        self.assertEqual((before["active_before"], before["expected_active_after"]), (102, 113))
        self.assertEqual(len(catalog_dishes()), 102)
        self.install_batch()
        after = seed_tool.inspect_review_batch(self.batch, FoodCatalogRepository)
        self.assertEqual(after["pending_ids"], [])
        self.assertEqual(len(after["already_matching_ids"]), 11)

    def test_database_review_rejects_name_collision(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET NameVi='Thịt kho tiêu' WHERE DishId='rice'"))
        db.session.commit()
        with self.assertRaises(ValueError):
            seed_tool.inspect_review_batch(self.batch, FoodCatalogRepository)

    def test_database_review_rejects_changed_existing_batch_profile(self):
        self.install_batch()
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999 WHERE DishId='vn_thit_kho_tieu'"))
        db.session.commit()
        with self.assertRaises(ValueError):
            seed_tool.inspect_review_batch(self.batch, FoodCatalogRepository)

    def test_new_food_search_and_default_or_custom_preview_never_record_intake(self):
        self.install_batch()
        response = self.client.get("/api/nutrition/quick-food/search?q=dau phu sot ca chua", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["results"][0]["dish_id"], "vn_dau_phu_sot_ca_chua")
        expected = next(d for d in self.batch["dishes"] if d["dish_id"] == "vn_dau_phu_sot_ca_chua")
        for grams in (None, 200):
            body = {"dish_id": expected["dish_id"]}
            if grams is not None:
                body["grams"] = grams
            preview = self.client.post("/api/nutrition/quick-food/preview", headers=self.headers, json=body)
            self.assertEqual(preview.status_code, 200)
            data = preview.get_json()["data"]
            self.assertAlmostEqual(data["totals"]["calories"], round(expected["calories_per_100g"] * (grams or expected["reference_grams"]) / 100, 1))
            self.assertTrue(data["estimated"])
        self.assertEqual(self.count(), 0)

    def test_confirm_retries_once_preserves_targets_and_planned_summary(self):
        self.install_batch()
        before = self.daily()
        planned = self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]
        request = {"dish_id": "vn_canh_ca_chua_trung", "grams": 240, "confirmed": True,
                   "requestId": "vietnamese-review-batch-01", "consumedAt": "2026-10-10T12:00:00+07:00"}
        first = self.client.post("/api/nutrition/quick-food/confirm", headers=self.headers, json=request)
        retry = self.client.post("/api/nutrition/quick-food/confirm", headers=self.headers, json=request)
        self.assertEqual((first.status_code, retry.status_code), (201, 200))
        self.assertEqual(first.get_json()["data"], retry.get_json()["data"])
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.daily()["targets"], before["targets"])
        self.assertEqual(self.daily()["consumed"]["calories"], first.get_json()["data"]["totals"]["calories"])
        self.assertEqual(self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"], planned)

    def test_new_food_snapshot_scaling_uses_frozen_values_after_catalog_update(self):
        self.install_batch()
        previous = component("vn_rau_muong_xao_toi", 170, actual=True)
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999 WHERE DishId='vn_rau_muong_xao_toi'"))
        db.session.commit()
        changed = snapshot_component(previous, 340)
        self.assertEqual(changed["nutrition_per_100g"], previous["nutrition_per_100g"])
        self.assertEqual(changed["calories"], round(previous["calories"] * 2, 4))
        self.assertFalse(changed["fiber_complete"])

    def test_curated_available_foods_can_compose_diverse_meals_with_avoid(self):
        self.install_batch()
        targets = json.loads((ROOT / "setup/drafts/vietnamese_catalog_v2/targets.json").read_text(encoding="utf-8"))
        ids = {d["dish_id"] for d in targets["targets"]}
        rows = [d for d in catalog_dishes() if d["dish_id"] in ids]
        self.assertEqual(len(rows), 71)
        macros = {"protein": 55.7, "carbs": 100.2, "fat": 29.7}
        for meal in ("breakfast", "lunch", "dinner"):
            preferences = {"avoid": ["fish"]}
            with patch("app.services.meal_planner_v4.catalog_dishes", return_value=rows):
                pool = candidate_pool(preferences, meal, "maintain", "review-batch", target=891, macro_targets=macros)
            options = MealPlannerV4.fallback(pool, meal, 891, "maintain", preferences, macro_targets=macros)
            self.assertEqual(len(options), 3)
            signatures = []
            for option in options:
                parts = option["recipe"]["components"]
                signatures.append(tuple(sorted(p["dish_id"] for p in parts)))
                self.assertEqual(totals(parts)["calories"], option["calories"])
                self.assertTrue(all(not violates(next(d for d in pool if d["dish_id"] == p["dish_id"]), preferences) for p in parts))
            self.assertEqual(len(set(signatures)), 3)


class ImportPreparationTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "setup/drafts/vietnamese_catalog_v2/review_batch.json"
        self.batch = json.loads(self.path.read_text(encoding="utf-8"))

    def test_offline_batch_mode_does_not_create_app_or_connect_database(self):
        output = io.StringIO()
        with patch("sys.argv", ["seed", "--batch", str(self.path), "--baseline-seed", str(ARCHIVE)]), patch("app.create_app") as factory, redirect_stdout(output):
            seed_tool.main()
        factory.assert_not_called()
        self.assertEqual(json.loads(output.getvalue()), {"mode": "validate_only", "dishes": 11,
                                                       "legacy_menus": 0, "database_writes": 0})

    def test_batch_cannot_include_existing_pho_or_pending_dishes(self):
        self.batch["dishes"].append(self.batch["review_existing"][0]["dish"])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "review.json"
            path.write_text(json.dumps(self.batch), encoding="utf-8")
            with self.assertRaises(ValueError):
                seed_tool.load_review_batch(path, ARCHIVE)

    def test_batch_nutrients_cannot_differ_from_ready_draft(self):
        self.batch["dishes"][0]["calories_per_100g"] += 1
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "review.json"
            path.write_text(json.dumps(self.batch), encoding="utf-8")
            with self.assertRaises(ValueError):
                seed_tool.load_review_batch(path, ARCHIVE)

    def test_backup_must_be_nonempty_sql_outside_repository(self):
        with self.assertRaises(ValueError):
            seed_tool.require_external_backup(ROOT / "setup/migrations/002_nutrition_food_catalog.sql")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "backup.sql"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                seed_tool.require_external_backup(path)
            path.write_text("CREATE TABLE `NutritionFoodCatalog` (...);\n", encoding="utf-8")
            self.assertEqual(seed_tool.require_external_backup(path), path.resolve())

    def test_batch_apply_requires_backup_before_app_is_created(self):
        with patch("sys.argv", ["seed", "--batch", str(self.path), "--apply", "--database", "NutriFitDB"]), \
                patch("app.create_app") as factory, patch.object(seed_tool, "load_review_batch", return_value=self.batch), redirect_stdout(io.StringIO()), patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                seed_tool.main()
        factory.assert_not_called()

    def test_current_runtime_rejects_stale_historical_batch(self):
        with self.assertRaises(ValueError):
            seed_tool.load_review_batch(self.path)
        self.assertEqual(len(seed_tool.load_seed()["dishes"]), 158)

    def test_archival_baseline_override_never_allows_database_modes(self):
        for action in ("--apply", "--check-db"):
            with patch("sys.argv", ["seed", "--batch", str(self.path), "--baseline-seed", str(ARCHIVE), action]), patch("app.create_app") as factory, patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    seed_tool.main()
            factory.assert_not_called()

    def test_seed_checksum_is_identical_for_lf_and_crlf_checkout(self):
        source = seed_tool.SEED_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
        with tempfile.TemporaryDirectory() as folder:
            lf, crlf = Path(folder) / "lf.json", Path(folder) / "crlf.json"
            lf.write_bytes(source.encode("utf-8"))
            crlf.write_bytes(source.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(seed_tool.seed_checksum(lf), seed_tool.seed_checksum(crlf))
            self.assertEqual(seed_tool.seed_checksum(lf), seed_tool.seed_checksum())
            self.assertNotEqual(seed_tool.seed_checksum(lf), self.batch["seed_baseline_sha256"])
            self.assertEqual(seed_tool.seed_checksum(ARCHIVE), self.batch["seed_baseline_sha256"])


class CompletionBatchTests(unittest.TestCase):
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    set_premium = quick_fixtures.QuickFoodTests.set_premium
    daily = quick_fixtures.QuickFoodTests.daily
    count = quick_fixtures.QuickFoodTests.count

    def setUp(self):
        ReviewBatchIntegrationTests.setUp(self)
        self.first_batch = self.batch
        FoodCatalogRepository.insert_missing(self.first_batch["dishes"], [])
        db.session.commit()
        self.path = ROOT / "setup/drafts/vietnamese_catalog_v2/completion_batch.json"
        self.batch = seed_tool.load_review_batch(self.path, ARCHIVE)

    def install(self):
        result = FoodCatalogRepository.insert_missing(self.batch["dishes"], [])
        db.session.commit()
        return result

    def test_completion_preserves_all_old_rows_and_is_insert_only_idempotent(self):
        old = [dict(r) for r in db.session.execute(text("SELECT * FROM NutritionFoodCatalog ORDER BY DishId")).mappings()]
        legacy = [dict(r) for r in db.session.execute(text("SELECT * FROM NutritionLegacyMenus ORDER BY TemplateId")).mappings()]
        self.assertEqual(self.install(), {"dishes": 28, "menus": 0})
        self.assertEqual(self.install(), {"dishes": 0, "menus": 0})
        new_ids = {d["dish_id"] for d in self.batch["dishes"]}
        after = [dict(r) for r in db.session.execute(text("SELECT * FROM NutritionFoodCatalog ORDER BY DishId")).mappings() if r["DishId"] not in new_ids]
        self.assertEqual(old, after)
        self.assertEqual(legacy, [dict(r) for r in db.session.execute(text("SELECT * FROM NutritionLegacyMenus ORDER BY TemplateId")).mappings()])
        targets = json.loads((ROOT / "setup/drafts/vietnamese_catalog_v2/targets.json").read_text(encoding="utf-8"))
        available = {d["dish_id"] for d in catalog_dishes()}
        self.assertEqual(len(available), 141)
        self.assertEqual({d["dish_id"] for d in targets["targets"]} - available, {"vn_com_tam_suon_bi_cha"})

    def test_every_completion_food_search_and_preview_scale_without_writes(self):
        from app.services.quick_food_service import QuickFoodService, normalized_name
        self.install()
        before = self.count()
        for dish in self.batch["dishes"]:
            for query in (dish["name"], normalized_name(dish["name"], True).upper()):
                results = QuickFoodService.search(query)["results"]
                self.assertEqual(results[0]["dish_id"], dish["dish_id"])
            for grams in (None, 123.45):
                result = QuickFoodService.preview({"dish_id": dish["dish_id"], "grams": grams})
                used = dish["reference_grams"] if grams is None else grams
                self.assertEqual(result["grams"], used)
                self.assertTrue(result["estimated"])
                for key in ("calories", "protein", "carbs", "fat"):
                    value = dish["calories_per_100g"] if key == "calories" else dish["macros_per_100g"][key]
                    # Components round to4 decimals, public totals to1 decimal.
                    # Half-ties may differ from directly rounding the raw product.
                    self.assertLessEqual(abs(result["totals"][key] - value * used / 100), .05005)
        self.assertEqual(self.count(), before)

    def test_new_roles_portions_and_avoid_are_read_by_existing_planner(self):
        from app.services.meal_planner_v4 import eligible
        self.install()
        for dish in self.batch["dishes"]:
            for meal in dish["meal_types"]:
                rows = {d["dish_id"]: d for d in eligible({}, meal)}
                self.assertEqual(rows[dish["dish_id"]]["type"], dish["type"])
            part = component(dish["dish_id"], dish["reference_grams"], dish["type"])
            self.assertGreaterEqual(part["grams"], dish["min_grams"])
            self.assertLessEqual(part["grams"], dish["max_grams"])
        self.assertFalse(any("fish" in d["ingredients"] for d in eligible({"avoid": ["fish"]}, "lunch")))

    def test_new_confirm_retry_changes_only_consumed_and_freezes_snapshot(self):
        self.install()
        before = self.daily()
        plan = self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]
        body = {"dish_id": "vn_trung_chien_hanh", "grams": 105, "confirmed": True,
                "requestId": "completion-reference-intake", "consumedAt": "2026-10-10T12:00:00+07:00"}
        first = self.client.post("/api/nutrition/quick-food/confirm", headers=self.headers, json=body)
        retry = self.client.post("/api/nutrition/quick-food/confirm", headers=self.headers, json=body)
        self.assertEqual((first.status_code, retry.status_code), (201, 200))
        self.assertEqual(first.get_json()["data"], retry.get_json()["data"])
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.daily()["targets"], before["targets"])
        self.assertEqual(self.daily()["consumed"]["calories"], first.get_json()["data"]["totals"]["calories"])
        self.assertEqual(self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"], plan)
        saved = component("vn_trung_chien_hanh", 105, actual=True)
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999 WHERE DishId='vn_trung_chien_hanh'"))
        db.session.commit()
        self.assertEqual(snapshot_component(saved, 210)["calories"], round(saved["calories"] * 2, 4))
        self.assertEqual(self.client.post("/api/nutrition/quick-food/confirm", headers=self.headers, json=body).get_json()["data"], first.get_json()["data"])

    def test_completion_offline_validation_never_creates_factory(self):
        output = io.StringIO()
        with patch("sys.argv", ["seed", "--batch", str(self.path), "--baseline-seed", str(ARCHIVE)]), patch("app.create_app") as factory, redirect_stdout(output):
            seed_tool.main()
        factory.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["dishes"], 28)

    def test_completion_loader_rejects_pending_initial_and_tampered_foods(self):
        import copy
        for bad in ("vn_com_tam_suon_bi_cha", "vn_thit_kho_tieu", "pho_beef"):
            batch = copy.deepcopy(self.batch)
            batch["dishes"][0]["dish_id"] = bad
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "batch.json"
                path.write_text(json.dumps(batch), encoding="utf-8")
                with self.assertRaises(ValueError):
                    seed_tool.load_review_batch(path, ARCHIVE)
        self.batch["dishes"][0]["macros_per_100g"]["fat"] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "batch.json"
            path.write_text(json.dumps(self.batch), encoding="utf-8")
            with self.assertRaises(ValueError):
                seed_tool.load_review_batch(path, ARCHIVE)


if __name__ == "__main__":
    unittest.main()
