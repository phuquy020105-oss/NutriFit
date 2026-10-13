"""Premium Quick Add integration: disposable SQLite only, no provider calls."""
import secrets
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.services.module_errors import ModuleError
from app.services.premium_access import PremiumAccess
import test_meal_api as fixtures
import test_meal_v4 as v4_fixtures


PREFIX = "/api/nutrition/quick-food"


class QuickFoodTests(unittest.TestCase):
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers
    generate = fixtures.ApiTests.generate
    choose = fixtures.ApiTests.choose

    def setUp(self):
        fixtures.ApiTests.setUp(self)
        self.assertEqual(db.engine.url.drivername, "sqlite")
        self.assertEqual(db.engine.url.database, ":memory:")
        v4_fixtures.migration_sqlite()
        # Only the test DB gets Quy's entitlement columns; core ORM stays unchanged.
        columns = {r[1] for r in db.session.execute(text("PRAGMA table_info(Users)"))}
        for name, sql_type in (("SubscriptionStatus", "VARCHAR(20)"), ("PremiumExpiresAt", "DATETIME")):
            if name not in columns:
                db.session.execute(text(f"ALTER TABLE Users ADD COLUMN {name} {sql_type}"))
        db.session.commit()
        self.set_premium()

    def set_premium(self, status="PREMIUM", expiry="future"):
        if expiry == "future":
            expiry = (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None)
        elif expiry == "past":
            expiry = (datetime.now(timezone.utc) - timedelta(seconds=5)).replace(tzinfo=None)
        db.session.execute(text("UPDATE Users SET SubscriptionStatus=:status,PremiumExpiresAt=:expiry WHERE UserId=1"),
                           {"status": status, "expiry": expiry})
        db.session.commit()

    def preview(self, **data):
        return self.client.post(PREFIX + "/preview", headers=self.headers, json={"dish_id": "rice", **data})

    def confirm(self, **data):
        return self.client.post(PREFIX + "/confirm", headers=self.headers, json={
            "dish_id": "rice", "confirmed": True, "requestId": secrets.token_hex(16),
            "consumedAt": "2026-10-10T15:00:00+07:00", **data})

    def count(self):
        return db.session.execute(text("SELECT COUNT(*) FROM NutritionFoodIntake")).scalar()

    def daily(self):
        return self.client.get("/api/nutrition/daily?date=2026-10-10", headers=self.headers).get_json()["data"]

    def test_search_accents_case_whitespace_and_no_accents(self):
        for query in ("Cơm trắng", "COM TRANG", "  cơm   TRẮNG  ", "Co\u031bm tra\u0306\u0301ng"):
            response = self.client.get(PREFIX + "/search", query_string={"q": query}, headers=self.headers)
            self.assertEqual(response.status_code, 200, query)
            body = response.get_json()["data"]
            self.assertEqual(body["results"][0]["dish_id"], "rice")
            self.assertEqual(body["results"][0]["match"], "exact")
            self.assertTrue(body["requires_selection"])
        self.assertEqual(self.count(), 0)

    def test_search_d_stroke_normalization(self):
        response = self.client.get(PREFIX + "/search?q=dau", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("đậu" in d["name"].lower() for d in response.get_json()["data"]["results"]))

    def test_duplicate_names_return_ids_and_exact_before_partial(self):
        db.session.execute(text("UPDATE NutritionFoodCatalog SET NameVi='Cơm trắng' WHERE DishId='chicken'"))
        db.session.execute(text("UPDATE NutritionFoodCatalog SET NameVi='Cơm trắng thêm rau' WHERE DishId='beef'"))
        db.session.commit()
        body = self.client.get(PREFIX + "/search?q=com%20trang", headers=self.headers).get_json()["data"]
        self.assertEqual({r["dish_id"] for r in body["results"][:2]}, {"rice", "chicken"})
        self.assertEqual(body["results"][2]["dish_id"], "beef")
        self.assertEqual(body["total"], 3)
        self.assertTrue(body["requires_selection"])
        limited = self.client.get(PREFIX + "/search?q=com%20trang&limit=1", headers=self.headers).get_json()["data"]
        self.assertEqual((limited["total"], limited["returned"]), (3, 1))

    def test_missing_similar_and_inactive_names(self):
        self.assertEqual(self.client.get(PREFIX + "/search?q=com", headers=self.headers).status_code, 200)
        for name in ("món không có", "com tragn", "%' OR 1=1 --"):
            response = self.client.get(PREFIX + "/search", query_string={"q": name}, headers=self.headers)
            self.assertEqual(response.get_json()["code"], "FOOD_NOT_FOUND")
        db.session.execute(text("UPDATE NutritionFoodCatalog SET IsActive=0 WHERE DishId='rice'"))
        db.session.commit()
        self.assertEqual(self.client.get(PREFIX + "/search?q=com%20trang", headers=self.headers).status_code, 404)
        self.assertEqual(self.preview().get_json()["code"], "FOOD_NOT_FOUND")
        self.assertEqual(self.confirm().get_json()["code"], "FOOD_NOT_FOUND")
        self.assertEqual(self.count(), 0)

    def test_invalid_search_inputs(self):
        for query in ("", "   ", "a" * 121):
            self.assertEqual(self.client.get(PREFIX + "/search", query_string={"q": query}, headers=self.headers).status_code, 400)
        self.assertEqual(self.client.get(PREFIX + "/search", headers=self.headers).status_code, 400)
        for limit in ("0", "21", "1.5", "bad"):
            self.assertEqual(self.client.get(PREFIX + "/search?q=com&limit=" + limit, headers=self.headers).status_code, 400)

    def test_reference_grams_and_explicit_grams_preview(self):
        for params in ({}, {"grams": None}):
            body = self.preview(**params).get_json()["data"]
            self.assertEqual(body["grams"], 180)
            self.assertTrue(body["used_reference_grams"])
            self.assertEqual(body["totals"]["calories"], 227.3)
        body = self.preview(grams=200).get_json()["data"]
        self.assertEqual(body["totals"], {"calories": 252.6, "protein": 5.4, "carbs": 56.4, "fat": 0.6, "fiber": 0.8})
        self.assertFalse(body["used_reference_grams"])
        self.assertEqual(body["source"], "database")
        self.assertTrue(body["estimated"])
        self.assertEqual(self.count(), 0)

    def test_actual_portions_not_limited_to_planning_bounds(self):
        for grams in (1, 2000, 400):
            self.assertEqual(self.preview(grams=grams).status_code, 200)
        self.assertEqual(self.preview(grams=123.456).get_json()["data"]["grams"], 123.46)

    def test_invalid_grams_never_write(self):
        for grams in (0, -1, 2001, True, [], {}, "bad", float("inf"), float("nan")):
            self.assertEqual(self.preview(grams=grams).status_code, 400, repr(grams))
            self.assertEqual(self.confirm(grams=grams).status_code, 400, repr(grams))
        self.assertEqual(self.count(), 0)

    def test_unknown_ids_and_invalid_catalog_rows(self):
        for identifier in ("unknown", " rice ", "", None, 1):
            self.assertIn(self.preview(dish_id=identifier).status_code, (400, 404))
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=-1 WHERE DishId='rice'"))
        db.session.commit()
        self.assertEqual(self.preview().get_json()["code"], "FOOD_NOT_FOUND")
        self.assertEqual(self.confirm().get_json()["code"], "FOOD_NOT_FOUND")
        self.assertEqual(self.count(), 0)

    def test_free_expired_and_null_expiry_block_all_quick_routes(self):
        for status, expiry in (("FREE", "future"), ("PREMIUM", "past"), ("PREMIUM", None), (None, "future")):
            self.set_premium(status, expiry)
            for response in (self.client.get(PREFIX + "/search?q=com", headers=self.headers), self.preview(), self.confirm()):
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.get_json()["code"], "PREMIUM_REQUIRED")
        self.assertEqual(self.count(), 0)

    def test_entitlement_rechecked_on_each_request(self):
        self.assertEqual(self.preview().status_code, 200)
        self.set_premium("FREE")
        self.assertEqual(self.confirm().status_code, 403)
        self.assertEqual(self.count(), 0)

    def test_entitlement_rechecked_after_user_lock(self):
        with patch.object(PremiumAccess, "require", side_effect=[None, ModuleError("Expired", "PREMIUM_REQUIRED", 403)]) as gate:
            self.assertEqual(self.confirm().status_code, 403)
        self.assertEqual(gate.call_count, 2)
        self.assertEqual(self.count(), 0)

    def test_malformed_expiry_and_db_error_fail_closed(self):
        from types import SimpleNamespace
        original_execute = db.session.execute
        def malformed_metadata(statement, *args, **kwargs):
            if str(statement).startswith("SELECT SubscriptionStatus, PremiumExpiresAt FROM Users"):
                return SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: {
                    "SubscriptionStatus":"PREMIUM", "PremiumExpiresAt":"not-a-date"}))
            return original_execute(statement, *args, **kwargs)
        # Simulate an invalid raw entitlement value without corrupting the current
        # User ORM's typed DATETIME, which cannot represent it on real MySQL.
        with patch.object(db.session, "execute", side_effect=malformed_metadata):
            response = self.preview()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "PREMIUM_UNAVAILABLE")
        with patch("app.services.premium_access.inspect", side_effect=SQLAlchemyError("private details")):
            response = self.preview()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private details", response.get_data(as_text=True))

    def test_expiry_boundary_utc_and_no_admin_bypass(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.set_premium(expiry=now.replace(tzinfo=None))
        with patch("app.services.premium_access.datetime", wraps=datetime) as clock:
            clock.now.return_value = now
            self.assertEqual(self.preview().get_json()["code"], "PREMIUM_REQUIRED")
        self.set_premium(expiry=(now + timedelta(hours=1)).isoformat())
        self.assertEqual(self.preview().status_code, 200)
        db.session.execute(text("UPDATE Users SET Role='ADMIN' WHERE UserId=1"))
        db.session.commit()
        self.set_premium("FREE")
        self.assertEqual(self.preview().status_code, 403)

    def test_caller_id_and_premium_claims_not_trusted(self):
        for key in ("userId", "user_id"):
            self.assertEqual(self.preview(**{key: 2}).get_json()["code"], "FORBIDDEN")
            self.assertEqual(self.confirm(**{key: 2}).get_json()["code"], "FORBIDDEN")
        self.assertEqual(self.client.get(PREFIX + "/search?q=com&userId=2", headers=self.headers).status_code, 403)
        self.assertEqual(self.preview(subscription_status="PREMIUM").status_code, 400)
        self.set_premium("FREE")
        self.assertEqual(self.confirm(premium=True).get_json()["code"], "PREMIUM_REQUIRED")
        self.assertEqual(self.count(), 0)

    def test_session_and_origin_required(self):
        self.assertEqual(self.client.get(PREFIX + "/search?q=com", headers={"X-User-Id": "1"}).status_code, 401)
        self.assertEqual(self.client.post(PREFIX + "/preview", json={"dish_id": "rice"}, headers={"X-User-Id": "1"}).status_code, 401)
        response = self.client.post(PREFIX + "/preview", json={"dish_id": "rice"},
                                    headers={**self.headers, "Origin": "https://invalid.example"})
        self.assertEqual(response.status_code, 403)
        response = self.client.post(PREFIX + "/preview", json={"dish_id": "rice"},
                                    headers={**self.headers, "Origin": "http://127.0.0.1:5500"})
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")

    def test_confirm_requires_explicit_confirmation_and_no_client_nutrients(self):
        for value in (False, None, 1, "true"):
            self.assertEqual(self.confirm(confirmed=value).get_json()["code"], "CONFIRMATION_REQUIRED")
        for extra in ({"calories": 999}, {"macros": {"fat": 999}}, {"name": "Cơm trắng"}):
            self.assertEqual(self.confirm(**extra).status_code, 400)
        self.assertEqual(self.count(), 0)

    def test_confirm_only_changes_consumed_and_retries_once(self):
        plan = self.generate().get_json()["data"]
        self.choose(plan, 1)
        before_plan = self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"]
        before_meals = self.client.get("/api/meals/today", headers=self.headers).get_json()
        before_history = self.client.get("/api/meals/history", headers=self.headers).get_json()
        before_daily = self.daily()
        key = secrets.token_hex(16)
        first, retry = self.confirm(grams=200, requestId=key), self.confirm(grams=200, requestId=key)
        self.assertEqual((first.status_code, retry.status_code), (201, 200))
        self.assertTrue(first.get_json()["created"])
        self.assertFalse(retry.get_json()["created"])
        self.assertEqual(first.get_json()["data"], retry.get_json()["data"])
        self.assertEqual(self.count(), 1)
        after_daily = self.daily()
        self.assertEqual(after_daily["consumed"]["calories"], before_daily["consumed"]["calories"] + 252.6)
        self.assertEqual(after_daily["targets"], before_daily["targets"])
        self.assertEqual(self.client.get("/api/nutrition/summary", headers=self.headers).get_json()["data"], before_plan)
        self.assertEqual(self.client.get("/api/meals/today", headers=self.headers).get_json(), before_meals)
        self.assertEqual(self.client.get("/api/meals/history", headers=self.headers).get_json(), before_history)

    def test_default_grams_retry_survives_reference_nutrients_and_activity_change(self):
        key = secrets.token_hex(16)
        first = self.confirm(requestId=key).get_json()["data"]
        self.assertEqual(first["items"][0]["grams"], 180)
        db.session.execute(text("UPDATE NutritionFoodCatalog SET ReferenceGrams=250,KcalPer100G=999,IsActive=0 WHERE DishId='rice'"))
        db.session.commit()
        retry = self.confirm(requestId=key)
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.get_json()["data"], first)
        self.assertEqual(self.count(), 1)

    def test_confirm_recalculates_after_preview(self):
        self.assertEqual(self.preview(grams=200).get_json()["data"]["totals"]["calories"], 252.6)
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=150 WHERE DishId='rice'"))
        db.session.commit()
        self.assertEqual(self.confirm(grams=200).get_json()["data"]["totals"]["calories"], 300)

    def test_idempotency_conflict_deleted_retry_and_expired_retry(self):
        key = secrets.token_hex(16)
        row = self.confirm(requestId=key).get_json()["data"]
        self.assertEqual(self.confirm(requestId=key, grams=200).get_json()["code"], "IDEMPOTENCY_CONFLICT")
        self.set_premium("FREE")
        self.assertEqual(self.confirm(requestId=key).status_code, 403)
        self.assertEqual(self.count(), 1)
        self.client.post(f'/api/nutrition/intake/{row["id"]}/delete', headers=self.headers, json={"version": 1})
        self.set_premium()
        self.assertEqual(self.confirm(requestId=key).get_json()["code"], "INTAKE_DELETED")

    def test_edit_delete_snapshot_and_ownership_after_expiry(self):
        row = self.confirm(grams=200).get_json()["data"]
        frozen = row["items"][0]["nutrition_per_100g"]
        db.session.execute(text("UPDATE NutritionFoodCatalog SET KcalPer100G=999,IsActive=0 WHERE DishId='rice'"))
        db.session.commit()
        self.set_premium("FREE")
        endpoint = f'/api/nutrition/intake/{row["id"]}'
        response = self.client.post(endpoint + "/update", headers=self.headers, json={
            "version": 1, "confirmed": True, "mealType": "snack", "consumedAt": "2026-10-10T15:00:00+07:00",
            "items": [{"dish_id": "rice", "grams": 100}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["totals"]["calories"], 126.3)
        self.assertEqual(response.get_json()["data"]["items"][0]["nutrition_per_100g"], frozen)
        self.assertEqual(self.daily()["consumed"]["calories"], 126.3)
        self.assertEqual(self.client.post(endpoint + "/delete", headers=self.other_headers, json={"version": 2}).status_code, 404)
        self.assertEqual(self.client.post(endpoint + "/delete", headers=self.headers, json={"version": 1}).status_code, 409)
        self.assertEqual(self.client.post(endpoint + "/delete", headers=self.headers, json={"version": 2}).status_code, 200)
        self.assertEqual(self.daily()["consumed"]["calories"], 0)

    def test_normal_free_intake_remains_available(self):
        self.set_premium("FREE")
        response = self.client.post("/api/nutrition/intake", headers=self.headers, json={
            "confirmed": True, "mealType": "snack", "requestId": secrets.token_hex(16),
            "items": [{"dish_id": "rice", "grams": 200}]})
        self.assertEqual(response.status_code, 201)

    def test_invalid_confirm_fields_never_write(self):
        for data in ({"mealType": "extra"}, {"consumedAt": "bad"}, {"consumedAt": "2026-10-10T15:00:00"}, {"requestId": "short"}):
            self.assertEqual(self.confirm(**data).status_code, 400)
        self.assertEqual(self.count(), 0)

    def test_broken_json_and_oversized_payload_are_rejected(self):
        for value in ([], None, "rice"):
            self.assertEqual(self.client.post(PREFIX + "/preview", headers=self.headers, json=value).status_code, 400)
        response = self.client.post(PREFIX + "/confirm", headers=self.headers,
                                    data='{"dish_id":', content_type="application/json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post(PREFIX + "/confirm", headers=self.headers,
                                    json={"dish_id": "rice", "padding": "x" * 65536})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.count(), 0)


class MissingPremiumSchemaTests(unittest.TestCase):
    setUp = fixtures.ApiTests.setUp
    tearDown = fixtures.ApiTests.tearDown
    login_headers = fixtures.ApiTests.login_headers

    def test_missing_entitlement_metadata_fails_closed_without_core_model_changes(self):
        # The current User ORM requires Premium columns. Exercise the adapter's
        # missing-metadata branch without breaking authentication's own schema.
        with patch("app.services.premium_access.inspect") as inspector:
            inspector.return_value.get_columns.return_value = [{"name":"UserId"}]
            response = self.client.post(PREFIX + "/preview", headers=self.headers, json={"dish_id": "rice"})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.get_json()["code"], "PREMIUM_UNAVAILABLE")
            self.assertEqual(self.client.get(PREFIX + "/search?q=com", headers=self.headers).status_code, 503)
            response = self.client.post(PREFIX + "/confirm", headers=self.headers, json={
                "dish_id": "rice", "confirmed": True, "requestId": secrets.token_hex(16)})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar(), 0)



if __name__ == "__main__":
    unittest.main()
