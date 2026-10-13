"""Premium AI meals: each request estimates one selected slot only."""
import json
from datetime import datetime
import pytest
from flask import Flask
from app.extensions import db
from app.models.user import User
from app.models.premium_manual_plan import PremiumManualDailyPlan
from app.routes.meals import meals_bp
from app.services import premium_daily_plan

ONE_MEAL = {"breakfast": "1 tô phở bò"}
SECOND_MEAL = {"snack": "1 hộp sữa chua"}


def estimated(meals):
    return {"meals": [{"key": key, "is_food": True, "calories": 350,
            "protein": 20, "carbs": 43, "fat": 11, "portion": "1 phần", "note": "Ước tính"}
            for key in meals]}


@pytest.fixture
def client(monkeypatch):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-key-only", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                      NUTRIFIT_TIMEZONE="Asia/Ho_Chi_Minh", NUTRITION_FRONTEND_ORIGINS=[])
    db.init_app(app)
    app.register_blueprint(meals_bp)
    monkeypatch.setattr(premium_daily_plan, "_ask_ai", estimated)
    with app.app_context():
        User.__table__.create(db.engine)
        PremiumManualDailyPlan.__table__.create(db.engine)
        db.session.add(User(UserId=5, Email="test@example.org", FullName="Test premium",
                            PasswordHash="hashed", SubscriptionStatus="PREMIUM", PremiumExpiresAt=datetime(2099, 1, 1)))
        db.session.commit()
        with app.test_client() as c:
            with c.session_transaction() as session: session["nutrifit_user_id"] = 5
            yield c
        db.session.remove()


def post_meal(client, meals):
    return client.post('/api/meals/daily-plan', json={"user_id": 5, "meals": meals})


def test_one_meal_only_saved(client):
    resp = post_meal(client, ONE_MEAL)
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['total_kcal'] == 350
    assert len(data['meals']) == 1
    assert data['meals'][0]['key'] == 'breakfast'
    assert client.get('/api/meals/daily-plan').get_json()['data'] == data


def test_second_slot_preserves_first_and_totals(client):
    post_meal(client, ONE_MEAL)
    resp = post_meal(client, SECOND_MEAL)
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert [m['key'] for m in data['meals']] == ['breakfast', 'snack']
    assert data['total_kcal'] == 700
    assert data['totals'] == {'protein': 40, 'carbs': 86, 'fat': 22}
    assert client.get('/api/meals/daily-plan').get_json()['data'] == data


def test_replace_one_slot_does_not_duplicate_or_erase_other(client):
    post_meal(client, ONE_MEAL)
    post_meal(client, SECOND_MEAL)
    resp = post_meal(client, {"breakfast": "2 quả trứng luộc"})
    assert resp.status_code == 200
    entries = resp.get_json()['data']['meals']
    assert len(entries) == 2
    assert entries[0]['title'] == '2 quả trứng luộc'
    assert entries[1]['title'] == '1 hộp sữa chua'


def test_old_four_meals_remain_when_one_slot_changed(client):
    old = premium_daily_plan._build_plan(ONE_MEAL, estimated(ONE_MEAL))
    for slot in ('lunch', 'dinner', 'snack'):
        old = premium_daily_plan._build_plan({slot: f'Món ăn {slot}'}, estimated({slot: f'Món ăn {slot}'}), old)
    with client.application.app_context():
        db.session.add(PremiumManualDailyPlan(UserId=5, PlanDate=premium_daily_plan.today(),
                                              PlanData=json.dumps(old)))
        db.session.commit()
    resp = post_meal(client, {"lunch": "150g thịt gà"})
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert len(data['meals']) == 4
    assert data['meals'][1]['title'] == '150g thịt gà'
    assert data['meals'][0]['title'] == '1 tô phở bò'


def test_free_user_rejected(client):
    with client.application.app_context():
        user = db.session.get(User, 5)
        user.SubscriptionStatus = 'FREE'
        db.session.commit()
    assert post_meal(client, ONE_MEAL).status_code == 403
    assert client.get('/api/meals/daily-plan').status_code == 403


def test_other_user_cannot_forge_id(client):
    assert client.post('/api/meals/daily-plan', json={"user_id": 6, "meals": ONE_MEAL}).status_code == 403


@pytest.mark.parametrize('meals', [None, {}, {"breakfast": ""}, {"breakfast": "ab"},
                                    {"unknown": "1 bát cháo"}, {"breakfast": "phở", "lunch": "cơm"}])
def test_invalid_selection_rejected_without_saving(client, meals):
    assert post_meal(client, meals).status_code == 400
    assert client.get('/api/meals/daily-plan').get_json()['data'] is None


def test_ai_rejects_nonfood_without_overwriting_old_meal(client, monkeypatch):
    post_meal(client, ONE_MEAL)
    before = client.get('/api/meals/daily-plan').get_json()['data']
    def reject(meals):
        result = estimated(meals)
        result['meals'][0]['is_food'] = False
        return result
    monkeypatch.setattr(premium_daily_plan, '_ask_ai', reject)
    assert post_meal(client, SECOND_MEAL).status_code == 422
    assert client.get('/api/meals/daily-plan').get_json()['data'] == before


def test_ai_unavailable_does_not_overwrite_old_plan(client, monkeypatch):
    post_meal(client, ONE_MEAL)
    before = client.get('/api/meals/daily-plan').get_json()['data']
    def fail(meals):
        from app.services.module_errors import ModuleError
        raise ModuleError('AI không khả dụng', 'AI_UNAVAILABLE', 503)
    monkeypatch.setattr(premium_daily_plan, '_ask_ai', fail)
    assert post_meal(client, SECOND_MEAL).status_code == 503
    assert client.get('/api/meals/daily-plan').get_json()['data'] == before


def test_ai_wrong_slot_response_rejected(client, monkeypatch):
    monkeypatch.setattr(premium_daily_plan, '_ask_ai', lambda meals: estimated({"dinner": "1 bữa khác"}))
    assert post_meal(client, ONE_MEAL).status_code == 503
    assert client.get('/api/meals/daily-plan').get_json()['data'] is None
