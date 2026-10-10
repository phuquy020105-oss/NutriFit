"""Integration tests use translated repository DDL in SQLite memory only."""
import re
import secrets
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.health import UserProfile
from app.module_auth import issue_access_token
from app.ai.gemini_client import AIUnavailable
from app.data.vietnamese_menus import fallback_templates, templates
from app.repositories.meal_repository import MealRepository
from app.services.module_errors import ModuleError


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                               "SECRET_KEY": secrets.token_urlsafe(32), "GEMINI_API_KEY": "", "GEMINI_MODEL": "",
                               "MAIL_SUPPRESS_SEND": True, "MAIL_DEFAULT_SENDER": "sender@example.invalid"})
        self.context = self.app.app_context()
        self.context.push()
        db.session.execute(text("PRAGMA foreign_keys=ON"))
        source = (Path(__file__).resolve().parents[2] / "setup/create_database.sql").read_text(encoding="utf-8")
        for statement in re.findall(r"CREATE TABLE .*?;", source, re.S):
            statement = statement.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            statement = statement.replace(" ON UPDATE CURRENT_TIMESTAMP", "")
            statement = re.sub(r"\) ENGINE=.*?;", ");", statement)
            db.session.execute(text(statement))
        self.password = secrets.token_urlsafe(20)
        for uid in (1, 2):
            db.session.add(User(UserId=uid, Email=f"member{uid}@example.invalid", FullName=f"Member {uid}",
                                PasswordHash=generate_password_hash(self.password), Role="MEMBER"))
        db.session.flush()
        db.session.add(UserProfile(UserId=1, Gender="male", Age=22, HeightCm=172, WeightKg=65,
                                   ActivityLevel=1.375, Goal="maintain", Bmr=1610, Tdee=2213.8, TargetKcal=2000,
                                   TargetWaterMl=2275))
        db.session.commit()
        self.headers = {"Authorization": "Bearer " + issue_access_token(1)["access_token"]}
        self.other_headers = {"Authorization": "Bearer " + issue_access_token(2)["access_token"]}
        self.client = self.app.test_client()
        self.day = date(2026, 10, 10)
        self.date_patch = patch("app.services.meal_service.today", return_value=self.day)
        self.date_patch.start()
        # routes imports the function, so freeze both references.
        self.route_date_patch = patch("app.routes.meals.today", return_value=self.day)
        self.route_date_patch.start()

    def tearDown(self):
        self.date_patch.stop()
        self.route_date_patch.stop()
        db.session.remove()
        db.engine.dispose()
        self.context.pop()

    def generate(self, meal="lunch", **extra):
        return self.client.post("/api/meals/generate", json={"userId": 1, "mealType": meal, **extra}, headers=self.headers)

    def choose(self, meal, selected, **extra):
        return self.client.post("/api/meals/select", headers=self.headers, json={
            "mealType": meal["mealType"], "selectedOption": selected, "revision": meal["revision"], **extra})

    def test_all_14_tables_from_unchanged_schema_are_used_in_fixture(self):
        count = db.session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")).scalar()
        self.assertEqual(count, 14)

    def test_login_adds_token_and_preserves_user_contract(self):
        response = self.client.post("/api/auth/login", json={"email": "member1@example.invalid", "password": self.password})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["user"]["id"], 1)
        self.assertEqual(body["token_type"], "Bearer")
        self.assertTrue(body["access_token"])

    def test_register_adds_token_and_preserves_contract(self):
        response = self.client.post("/api/auth/register", json={"email": "new@example.invalid", "password": self.password,
                                                                "full_name": "New member"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user"]["role"], "MEMBER")
        self.assertTrue(response.get_json()["access_token"])

    def test_auth_json_and_types_validated(self):
        for endpoint in ("/api/auth/login", "/api/auth/register"):
            for payload in ([], {"email": 7, "password": {}}, {}):
                self.assertEqual(self.client.post(endpoint, json=payload).status_code, 400)

    def test_stateless_calculate_without_database_profile(self):
        response = self.client.post("/api/nutrition/calculate", json=dict(gender="male", age=22, height=172,
                                                                         weight=65, activity_level=1.375, goal="gain"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["target_kcal"], 2727.5)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar(), 0)

    def test_bearer_required_and_header_id_not_trusted(self):
        for endpoint in ("/api/meals/today", "/api/meals/history", "/api/nutrition/me", "/api/nutrition/summary", "/api/profile/1"):
            self.assertEqual(self.client.get(endpoint, headers={"X-User-Id": "1"}).status_code, 401)

    def test_forged_and_expired_tokens_rejected(self):
        self.assertEqual(self.client.get("/api/meals/today", headers={"Authorization": "Bearer invalid"}).status_code, 401)
        with patch("itsdangerous.timed.TimestampSigner.get_timestamp", return_value=1):
            old = issue_access_token(1)["access_token"]
        self.assertEqual(self.client.get("/api/meals/today", headers={"Authorization": "Bearer " + old}).status_code, 401)

    def test_cross_user_access_blocked(self):
        for endpoint in ("/api/meals/today?userId=2", "/api/meals/history?user_id=2", "/api/profile/2"):
            self.assertEqual(self.client.get(endpoint, headers=self.headers).status_code, 403)
        self.assertEqual(self.generate(userId=2).status_code, 403)

    def test_missing_profile_error(self):
        response = self.client.post("/api/meals/generate", headers=self.other_headers, json={"mealType": "lunch"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["code"], "PROFILE_REQUIRED")

    def test_profile_canonical_and_legacy_routes_aliases(self):
        for endpoint in ("/save", "/api/profile/save"):
            response = self.client.post(endpoint, headers=self.headers, json={"userId": 1, "activity": 1.55})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["data"]["activity_level"], 1.55)
            self.assertIn("bmi", response.get_json()["data"])
            self.assertIn("macros", response.get_json()["data"])
        for endpoint in ("/1", "/api/profile/1"):
            self.assertEqual(self.client.get(endpoint, headers=self.headers).status_code, 200)

    def test_profile_invalid_input_does_not_write(self):
        response = self.client.post("/api/profile/save", headers=self.headers, json={"weight": "bad"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UserProfile.query.filter_by(UserId=1).first().WeightKg, 65)

    def test_nutrition_recomputes_stale_seed_values(self):
        response = self.client.get("/api/nutrition/me", headers=self.headers)
        self.assertEqual(response.get_json()["data"]["target_kcal"], 2227.5)

    def test_initial_today_is_empty(self):
        response = self.client.get("/api/meals/today?userId=1", headers=self.headers)
        self.assertEqual(response.get_json()["todayMeals"], {"lunch": None, "dinner": None})

    def test_generate_persists_three_complete_options(self):
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["meta"]["fallback_reason"], "not_configured")
        self.assertEqual(len(body["data"]["options"]), 3)
        for option in body["data"]["options"]:
            for name in ("carb", "protein", "soup", "veggie", "dessert"):
                self.assertIn("g)", option[name])
            macros = option["macros"]
            self.assertAlmostEqual(option["calories"], 4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"], delta=0.1)
            self.assertAlmostEqual(option["calories"], 891.0, delta=1)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealNutrition")).scalar(), 3)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealComponentDish")).scalar(), 15)

    def test_repeated_generate_returns_same_persisted_options(self):
        first = self.generate().get_json()["data"]
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank") as rank:
            second = self.generate().get_json()
            rank.assert_not_called()
        self.assertEqual(first, second["data"])
        self.assertTrue(second["meta"]["cached"])
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar(), 1)

    def test_generate_json_and_fields_validation(self):
        for payload in ([], {}, {"mealType": "breakfast"}, {"mealType": "lunch", "forceRefresh": "false"},
                        {"mealType": "lunch", "userId": True},
                        {"mealType": "lunch", "meal_type": "dinner"}):
            self.assertEqual(self.client.post("/api/meals/generate", headers=self.headers, json=payload).status_code, 400)
        self.assertEqual(self.client.post("/api/meals/generate", headers=self.headers, data="bad", content_type="application/json").status_code, 400)

    def test_caller_key_rejected(self):
        response = self.generate(apiKey=secrets.token_urlsafe(24))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "SERVER_KEY_REQUIRED")

    def test_snake_case_meal_payload_supported(self):
        response = self.client.post("/api/meals/generate", headers=self.headers,
                                    json={"user_id": 1, "meal_type": "dinner", "force_refresh": False})
        self.assertEqual(response.status_code, 200)

    def test_choose_and_think_later_keep_options(self):
        meal = self.generate().get_json()["data"]
        chosen = self.choose(meal, 2).get_json()["data"]
        self.assertEqual(chosen["status"], "decided")
        pending = self.choose(chosen, None).get_json()["data"]
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["options"], meal["options"])

    def test_selection_validates_revision_number_and_identity(self):
        meal = self.generate().get_json()["data"]
        self.assertEqual(self.choose(meal, 4).status_code, 400)
        self.assertEqual(self.choose(meal, True).status_code, 400)
        self.assertEqual(self.choose(meal, 1, revision="stale" * 4 + "xxxx").status_code, 409)
        self.assertEqual(self.choose(meal, 1, optionId=meal["options"][1]["optionId"]).status_code, 409)
        self.assertEqual(self.choose(meal, 1, suggestionId=999).status_code, 409)
        self.assertEqual(self.client.post("/api/meals/select", headers=self.headers,
                                         json={"mealType": "lunch", "selectedOption": 1}).status_code, 400)

    def test_selection_without_suggestion_returns_404(self):
        self.assertEqual(self.choose({"mealType": "lunch", "revision": "0" * 24}, 1).status_code, 404)

    def test_decided_refresh_rejected_without_losing_data(self):
        meal = self.generate().get_json()["data"]
        self.choose(meal, 1)
        self.assertEqual(self.generate(forceRefresh=True, revision=meal["revision"]).status_code, 409)
        saved = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"]
        self.assertEqual(saved["selectedOption"], 1)
        self.assertEqual(saved["options"], meal["options"])

    def test_pending_refresh_replaces_atomically_and_rejects_stale_selection(self):
        meal = self.generate().get_json()["data"]
        response = self.generate(forceRefresh=True, revision=meal["revision"])
        self.assertEqual(response.status_code, 200)
        new = response.get_json()["data"]
        self.assertNotEqual(new["revision"], meal["revision"])
        self.assertNotEqual(new["options"][0]["title"], meal["options"][0]["title"])
        self.assertEqual(self.choose(meal, 1).status_code, 409)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealOption")).scalar(), 3)

    def test_stale_refresh_rejected(self):
        meal = self.generate().get_json()["data"]
        self.assertEqual(self.generate(forceRefresh=True).status_code, 409)
        self.assertEqual(self.generate(forceRefresh=True, revision="0" * 24).status_code, 409)
        self.assertEqual(self.generate(forceRefresh=True, revision=meal["revision"]).status_code, 200)
        self.assertEqual(self.generate(forceRefresh=True, revision=meal["revision"]).status_code, 409)

    def test_provider_failure_uses_fallback(self):
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank", side_effect=AIUnavailable("provider_busy")):
            response = self.generate()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["source"], "fallback")

    def test_provider_selection_saved_and_source_survives_reload(self):
        choices = [(template, "Mâm cơm đa dạng.") for template in templates("dinner")[:3]]
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank", return_value=choices):
            self.assertEqual(self.generate("dinner").get_json()["data"]["source"], "gemini")
        saved = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["dinner"]
        self.assertEqual(saved["source"], "gemini")

    def test_ai_refresh_excludes_previous_titles(self):
        meal = self.generate().get_json()["data"]
        previous = {option["title"] for option in meal["options"]}
        def choose_new(candidates, *args):
            self.assertFalse(previous.intersection(template["title"] for template in candidates))
            chosen, families = [], set()
            for template in candidates:
                if template["family"] not in families:
                    families.add(template["family"])
                    chosen.append((template, "Mâm cơm khác để đổi vị."))
            return chosen
        with patch.object(self.app.extensions["nutrifit_gemini"], "rank", side_effect=choose_new):
            refreshed = self.generate(forceRefresh=True, revision=meal["revision"])
        self.assertEqual(refreshed.status_code, 200)
        self.assertFalse(previous.intersection(option["title"] for option in refreshed.get_json()["data"]["options"]))

    def test_database_failure_rolls_back_all_new_rows_and_redacts_error(self):
        original = db.session.execute
        def failing(statement, *args, **kwargs):
            if "INSERT INTO MealNutrition" in str(statement):
                raise SQLAlchemyError("private-test-marker")
            return original(statement, *args, **kwargs)
        with patch.object(db.session, "execute", side_effect=failing):
            response = self.generate()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-test-marker", response.get_data(as_text=True))
        for table in ("MealSuggestions", "MealOption", "MealNutrition", "MealComponentDish"):
            self.assertEqual(db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar(), 0)

    def test_failed_refresh_retains_previous_options(self):
        meal = self.generate().get_json()["data"]
        original = db.session.execute
        def failing(statement, *args, **kwargs):
            if "INSERT INTO MealComponentDish" in str(statement):
                raise SQLAlchemyError("private-test-marker")
            return original(statement, *args, **kwargs)
        with patch.object(db.session, "execute", side_effect=failing):
            self.assertEqual(self.generate(forceRefresh=True, revision=meal["revision"]).status_code, 503)
        saved = self.client.get("/api/meals/today", headers=self.headers).get_json()["todayMeals"]["lunch"]
        self.assertEqual(saved, meal)

    def test_write_rechecks_snapshot_revision(self):
        meal = self.generate().get_json()["data"]
        self.generate(forceRefresh=True, revision=meal["revision"])
        with self.assertRaises(ModuleError) as error:
            MealRepository.store(1, self.day, "lunch", [], meal["revision"], True)
        self.assertEqual(error.exception.code, "STALE_MEAL")
        db.session.rollback()

    def test_history_chosen_meal_and_pagination(self):
        meal = self.generate().get_json()["data"]
        self.choose(meal, 3)
        self.generate("dinner")
        response = self.client.get("/api/meals/history?limit=1&page=2", headers=self.headers)
        body = response.get_json()
        self.assertEqual(body["pagination"]["total"], 2)
        self.assertEqual(body["history"][0]["chosenMeal"]["id"], 3)
        self.assertEqual(self.client.get("/api/meals/history?limit=101", headers=self.headers).status_code, 400)

    def test_other_user_history_is_empty(self):
        self.generate()
        self.assertEqual(self.client.get("/api/meals/history", headers=self.other_headers).get_json()["history"], [])

    def test_planned_summary_counts_selected_only(self):
        lunch = self.generate().get_json()["data"]
        self.generate("dinner")
        before = self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]
        self.assertEqual(before["planned"]["calories"], 0)
        self.choose(lunch, 1)
        after = self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]
        self.assertEqual(after["tracking_mode"], "planned")
        self.assertEqual(after["selected_meals"], 1)
        self.assertEqual(after["planned"]["calories"], lunch["options"][0]["calories"])
        self.choose(lunch, None)
        self.assertEqual(self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]["selected_meals"], 0)

    def test_new_day_creates_new_suggestion_and_retains_history(self):
        self.generate()
        tomorrow = self.day + timedelta(days=1)
        with patch("app.services.meal_service.today", return_value=tomorrow):
            self.generate()
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar(), 2)

    def test_seven_day_cycle_and_repeat(self):
        for meal in ("lunch", "dinner"):
            sets = [fallback_templates(meal, self.day + timedelta(days=offset)) for offset in range(7)]
            self.assertEqual(len({items[0]["template_id"] for items in sets}), 7)
            self.assertEqual(sets[0], fallback_templates(meal, self.day + timedelta(days=7)))
            self.assertTrue(all(len(items) == 3 for items in sets))

    def test_payload_limit_and_cors(self):
        response = self.client.post("/api/nutrition/calculate", data="x" * 70000, content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.assertFalse(response.get_json()["success"])
        response = self.client.options("/api/meals/today", headers={"Origin": "http://localhost:5500",
                                      "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "Authorization"})
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:5500")
