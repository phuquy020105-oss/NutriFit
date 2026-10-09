"""Test phần TV4. Chạy từ thư mục backend/:  python -m pytest tests/test_workouts.py -v

Dùng SQLite in-memory và app Flask riêng nên không cần MySQL.
"""
from datetime import date, timedelta

import pytest
from flask import Flask
from sqlalchemy import text

from app.extensions import db
from app.routes.workouts import workout_bp, progress_bp, street_food_bp
from app.services import workout_service as ws
from app.services import progress_service as ps
from app.services import street_food_service as sfs
from app.data.street_foods import STREET_FOODS
from app.data.workout_seed import EXTRA_WORKOUTS

SCHEMA = [
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
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", TESTING=True)
    db.init_app(app)
    app.register_blueprint(workout_bp, url_prefix='/api/workouts')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(street_food_bp, url_prefix='/api/street-food')
    with app.app_context():
        for stmt in SCHEMA:
            db.session.execute(text(stmt))
        db.session.commit()
        from app.data.street_foods import seed_street_foods_if_empty
        seed_street_foods_if_empty()
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


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
