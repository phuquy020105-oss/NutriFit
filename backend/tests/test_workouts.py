"""Test phần TV4. Chạy từ thư mục backend/:  python -m pytest tests/test_workouts.py -v

Dùng SQLite in-memory và app Flask riêng nên không cần MySQL.
"""
from datetime import date, timedelta
from datetime import datetime

import pytest
from flask import Flask
from sqlalchemy import text

from app.extensions import db
from app.routes.workouts import workout_bp, progress_bp, street_food_bp
from app.services import workout_service as ws
from app.services import progress_service as ps
from app.data import street_foods as sfs
from app.data.street_foods import STREET_FOODS, seed_street_foods_if_empty
from app.data.workout_seed import EXTRA_WORKOUTS

SCHEMA = [
    "CREATE TABLE Users (UserId INTEGER PRIMARY KEY, Email TEXT, PasswordHash TEXT, FullName TEXT, Role TEXT, "
    "SubscriptionStatus TEXT, PremiumExpiresAt DATETIME, CreatedAt DATETIME)",
    "INSERT INTO Users (UserId, Email, PasswordHash, FullName, Role, SubscriptionStatus, PremiumExpiresAt) "
    "VALUES (2,'test@example.org','hash','Test user','MEMBER','PREMIUM','2099-01-01 00:00:00')",
    "CREATE TABLE UserProfiles (UserId INTEGER, WeightKg REAL)",
    "CREATE TABLE WorkoutCategories (CategoryId INTEGER PRIMARY KEY, CategoryName TEXT, IconName TEXT)",
    "CREATE TABLE Workouts (WorkoutId INTEGER PRIMARY KEY AUTOINCREMENT, CategoryId INTEGER, WorkoutName TEXT, "
    "DurationMinutes INTEGER, CaloriesBurned REAL, IsCustom INTEGER DEFAULT 0, CreatedBy INTEGER)",
    "CREATE TABLE WorkoutLogs (LogId INTEGER PRIMARY KEY AUTOINCREMENT, UserId INTEGER, WorkoutId INTEGER, "
    "LoggedDate TEXT, DurationMinutes INTEGER, CaloriesBurned REAL)",
    "CREATE TABLE WorkoutGoals (GoalId INTEGER PRIMARY KEY AUTOINCREMENT, UserId INTEGER UNIQUE, "
    "WeeklySessionsTarget INTEGER, WeeklyCaloriesTarget REAL)",
    "CREATE TABLE StreetFoodDish (DishId INTEGER PRIMARY KEY AUTOINCREMENT, Title TEXT, PriceVnd INTEGER, "
    "Calories REAL, CarbsGrams REAL, ProteinGrams REAL, FatGrams REAL, MealType TEXT, ProteinDesc TEXT, "
    "CarbDesc TEXT, SoupDesc TEXT, VeggieDesc TEXT)",
    "INSERT INTO UserProfiles VALUES (2, 65)",
    "INSERT INTO WorkoutCategories VALUES (1,'Cardio',NULL),(2,'Gym',NULL),(5,'Tự chọn',NULL)",
    "INSERT INTO Workouts (CategoryId, WorkoutName, DurationMinutes, CaloriesBurned, IsCustom) VALUES "
    "(1,'Chạy bộ ngoài trời',30,280,0),(2,'Tập ngực',45,260,0)",
]


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", TESTING=True,
                      SECRET_KEY="test-workout-key-not-for-production", NUTRITION_FRONTEND_ORIGINS=[])
    db.init_app(app)
    app.register_blueprint(workout_bp, url_prefix='/api/workouts')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(street_food_bp, url_prefix='/api/street-food')
    with app.app_context():
        for stmt in SCHEMA:
            db.session.execute(text(stmt))
        db.session.commit()
        seed_street_foods_if_empty()
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    with app.test_client() as browser:
        with browser.session_transaction() as session:
            session["nutrifit_user_id"] = 2
        yield browser


# ---------- hàm thuần ----------
def test_calc_calories_met():
    assert ws.calc_calories_met(8, 65, 30) == 260.0


def test_scale_calories():
    assert ws.scale_calories(280, 30, 15) == 140.0
    assert ws.scale_calories(280, 0, 15) == 0.0


def test_data_sizes():
    assert len(STREET_FOODS) == 36
    assert len(EXTRA_WORKOUTS) == 11


def test_build_week_fills_zero_days():
    end = date(2026, 10, 9)
    week = ps.build_week([(end.isoformat(), 2, 75, 540.0)], end)
    assert len(week) == 7
    assert week[-1]["sessions"] == 2 and week[-1]["calories"] == 540.0
    assert all(d["sessions"] == 0 for d in week[:-1])
    assert week[-1]["label"] == "T6"  # 09/10/2026 là thứ 6


def test_rank_filters_budget_and_kcal():
    dishes = [{"id": 1, "title": "A", "price_vnd": 30000, "calories": 400, "protein_g": 30, "meal_type": "all"},
              {"id": 2, "title": "B", "price_vnd": 60000, "calories": 400, "protein_g": 30, "meal_type": "all"},
              {"id": 3, "title": "C", "price_vnd": 30000, "calories": 900, "protein_g": 30, "meal_type": "all"}]
    result = sfs.rank_dishes(dishes, budget=40000, max_kcal=600)
    assert [d["id"] for d in result] == [1]


# ---------- tích hợp qua DB ----------
def test_catalog_groups_by_category(app):
    cats = ws.list_catalog(2)
    assert [c["name"] for c in cats] == ["Cardio", "Gym"]


def test_log_scales_calories_and_rejects_future(app):
    log, err = ws.log_workout(2, 1, duration_minutes=15)
    assert err is None and log["calories_burned"] == 140.0
    _, err = ws.log_workout(2, 1, logged_date=(date.today() + timedelta(days=1)).isoformat())
    assert err and "tương lai" in err
    _, err = ws.log_workout(2, 999)
    assert err == "Không tìm thấy bài tập."


def test_custom_workout_met_uses_profile_weight(app):
    w, err = ws.create_custom_workout(2, "Võ thuật", 60, met=6)
    assert err is None and w["calories_burned"] == 390.0  # 6 x 65 x 1h
    _, err = ws.create_custom_workout(2, "Thiếu calo", 30)
    assert err
    # bài tùy chỉnh của user 2 không hiện với user khác
    assert "Võ thuật" not in [x["name"] for c in ws.list_catalog(3) for x in c["workouts"]]


def test_weekly_stats_and_goal(app):
    today = date.today()
    ws.log_workout(2, 1, 30, today.isoformat())
    ws.log_workout(2, 2, 45, (today - timedelta(days=2)).isoformat())
    ws.log_workout(2, 1, 30, (today - timedelta(days=10)).isoformat())  # ngoài 7 ngày
    stats = ps.weekly_stats(2)
    assert len(stats["days"]) == 7
    assert stats["totals"]["sessions"] == 2 and stats["totals"]["calories"] == 540.0
    assert stats["goal"]["weekly_sessions_target"] == 4  # mặc định
    assert stats["goal"]["sessions_pct"] == 50
    _, err = ws.save_goal(2, 2, 500)
    assert err is None
    assert ps.weekly_stats(2)["goal"]["sessions_pct"] == 100
    _, err = ws.save_goal(2, 0, 500)
    assert err


def test_delete_log_only_owner(app):
    log, _ = ws.log_workout(2, 1)
    assert ws.delete_log(3, log["log_id"]) is False
    assert ws.delete_log(2, log["log_id"]) is True


def test_street_food_recommend(app):
    result, err = sfs.recommend(45000, 550, "dinner", 3)
    assert err is None and 1 <= result["count"] <= 3
    for item in result["items"]:
        assert item["price_vnd"] <= 45000 and item["calories"] <= 550
        assert item["meal_type"] in ("dinner", "all")
    scores = [i["score"] for i in result["items"]]
    assert scores == sorted(scores, reverse=True)
    result, err = sfs.recommend(5000, 100)
    assert err is None and result["count"] == 0
    _, err = sfs.recommend(-1, 500)
    assert err


# ---------- route ----------
def test_routes_end_to_end(client):
    r = client.post('/api/workouts/log', json={"user_id": 2, "workout_id": 1, "duration_minutes": 30})
    assert r.status_code == 201 and r.get_json()["data"]["calories_burned"] == 280.0
    r = client.get('/api/progress/weekly/2')
    assert r.get_json()["data"]["totals"]["sessions"] == 1
    r = client.post('/api/workouts/log', json={"user_id": 2})
    assert r.status_code == 400
    r = client.get('/api/workouts/logs?user_id=2&from=abc')
    assert r.status_code == 400
    r = client.get('/api/street-food?meal_type=dinner&max_price=40000')
    assert r.status_code == 200 and r.get_json()["data"]["count"] > 0
    r = client.post('/api/street-food/recommend', json={"budget": 50000, "max_kcal": 600, "meal_type": "lunch"})
    assert r.status_code == 200 and r.get_json()["data"]["items"]


# ---------- AI verification contract (không gọi Gemini hoặc MySQL thật) ----------
def test_ai_rejects_non_exercise_without_fallback(app, monkeypatch):
    def reject(_name):
        raise ws._NotExercise()
    monkeypatch.setattr(ws, "_ask_gemini_for_met", reject)
    result, error = ws.estimate_workout(2, "abc xyz 123", 30)
    assert result is None and "không phải bài tập thể chất" in error


def test_ai_does_not_fallback_for_unknown_when_offline(app, monkeypatch):
    def offline(_name):
        raise RuntimeError("offline")
    monkeypatch.setattr(ws, "_ask_gemini_for_met", offline)
    result, error = ws.estimate_workout(2, "Chạy bằng giày lò xo", 30)
    assert result is None and "Không kết nối được dịch vụ AI" in error


def test_basketball_is_known_without_gemini(app, monkeypatch):
    monkeypatch.setattr(ws, "_ask_gemini_for_met", lambda _: (_ for _ in ()).throw(RuntimeError("offline")))
    result, error = ws.estimate_workout(2, "chơi bóng rổ", 30)
    assert error is None
    assert result["source"] == "catalog"
    assert result["met"] == 6.5
    assert result["calories_burned"] == 211.2  # 6.5 * 65 * 30 / 60 -> banker's rounding
    assert ws._known_workout("abc chơi bóng rổ xyz") is None
    assert ws._known_workout("không chơi bóng rổ") is None


def test_custom_requires_valid_ai_signature(client, app, monkeypatch):
    app.config["SECRET_KEY"] = "test-workout-key-not-for-production"
    no_token = client.post('/api/workouts/custom', json={
        "user_id": 2, "name": "Chèo kayak", "duration_minutes": 30, "calories_burned": 9999})
    assert no_token.status_code == 400
    assert no_token.get_json()["success"] is False

    monkeypatch.setattr(ws, "_ask_gemini_for_met", lambda name: (6.0, "Cường độ vừa"))
    estimate = client.post('/api/workouts/estimate', json={
        "user_id": 2, "name": "Chèo kayak", "duration_minutes": 30})
    assert estimate.status_code == 200
    result = estimate.get_json()["data"]
    assert result["calories_burned"] == 195.0  # 6 MET x 65 kg x 0.5 h
    assert result["source"] == "ai"

    params = {"user_id": 2, "name": "Chèo kayak", "duration_minutes": 30,
              "estimate_token": result["estimate_token"], "calories_burned": 9999,
              "met": 19}
    tampered_name = client.post('/api/workouts/custom', json={**params, "name": "Ăn bánh"})
    assert tampered_name.status_code == 400
    tampered_time = client.post('/api/workouts/custom', json={**params, "duration_minutes": 60})
    assert tampered_time.status_code == 400
    tampered_user = client.post('/api/workouts/custom', json={**params, "user_id": 3})
    assert tampered_user.status_code == 403

    created = client.post('/api/workouts/custom', json=params)
    assert created.status_code == 201
    assert created.get_json()["data"]["calories_burned"] == 195.0
    assert ws.list_catalog(2)[-1]["workouts"][-1]["calories_burned"] == 195.0

    # Cập nhật không được dùng kcal do client bịa ra.
    workout_id = created.get_json()["data"]["id"]
    changed = client.put(f'/api/workouts/custom/{workout_id}', json={
        **params, "duration_minutes": 60, "calories_burned": 3000})
    assert changed.status_code == 400


def test_free_user_cannot_create_or_verify_ai_exercise(client, app):
    from sqlalchemy import text
    from app.extensions import db
    with app.app_context():
        db.session.execute(text("UPDATE Users SET SubscriptionStatus='FREE' WHERE UserId=2"))
        db.session.commit()
    for route in ("/api/workouts/estimate", "/api/workouts/custom"):
        result = client.post(route, json={"user_id": 2, "name": "chơi bóng rổ", "duration_minutes": 30})
        assert result.status_code == 403
        assert result.get_json()["code"] == "PREMIUM_REQUIRED"


def test_other_account_cannot_use_own_premium_rights(client):
    result = client.post("/api/workouts/estimate",
                         json={"user_id": 1, "name": "chơi bóng rổ", "duration_minutes": 30})
    assert result.status_code == 403
    assert result.get_json()["code"] == "FORBIDDEN"
