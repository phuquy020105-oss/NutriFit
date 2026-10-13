"""Local integration tests for the explicitly opted-in mock payment flow."""
import os
import re
import sys
from pathlib import Path

import pytest
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.extensions import db, mail
from app.models.user import User, SubscriptionPlan, PaymentTransaction
from app.routes import payment as payment_routes


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("NUTRIFIT_ENV", "development")
    monkeypatch.setenv("NUTRIFIT_PAYMENT_DEMO_MODE", "true")
    monkeypatch.delenv("NUTRIFIT_DEMO_QR_BASE_URL", raising=False)
    app = Flask(__name__)
    app.config.update(SECRET_KEY="strong-secret-for-test-not-production", SQLALCHEMY_DATABASE_URI="sqlite://",
                      SQLALCHEMY_TRACK_MODIFICATIONS=False, TESTING=True,
                      MAIL_SUPPRESS_SEND=True, MAIL_DEFAULT_SENDER="fake@example.com")
    db.init_app(app)
    mail.init_app(app)
    app.register_blueprint(payment_routes.payment_bp)
    with app.app_context():
        db.create_all()
        user = User(UserId=1, Email="realuser@gmail.com", FullName="Test User", PasswordHash="hashed")
        plan = SubscriptionPlan(PlanId=4, PlanName="Gói Premium 1 Tháng", PriceVnd=99000, DurationDays=30, IsActive=True)
        db.session.add_all([user, plan]); db.session.commit()
        yield app
        db.session.remove(); db.drop_all()


def _checkout(client):
    with client.session_transaction() as session:
        session["nutrifit_user_id"] = 1
    result = client.post("/api/payment/demo-checkout", json={"plan_id": 4}, headers={"X-User-Id": "1"})
    assert result.status_code == 201
    return result.get_json()["data"]


def test_demo_checkout_creates_qr_without_real_payment(env):
    with env.test_client() as client:
        data = _checkout(client)
        assert data["amount_vnd"] == 99000
        assert data["recipient_name"] == "NUTRIFIT"
        assert data["account_number"].startswith("NF-DEMO")
        assert data["qr_data_url"].startswith("data:image/png;base64,")
        assert data["confirm_url"].startswith("http://localhost/api/payment/confirm/")
        txn = db.session.get(PaymentTransaction, data["transaction_id"])
        assert txn.Status == "DEMO_PENDING"
        assert txn.PaymentMethod == "DEMO_QR"
        user = db.session.get(User, 1)
        assert user.SubscriptionStatus != "PREMIUM"


def test_confirm_requires_user_agreement_and_sends_only_once(env, monkeypatch):
    sent = []
    monkeypatch.setattr(payment_routes, "_demo_email", lambda txn: sent.append(txn.TransactionCode))
    with env.test_client() as client:
        data = _checkout(client)
        path = data["confirm_url"].replace("http://localhost", "")
        page = client.get(path)
        assert page.status_code == 200
        assert "99.000" in page.get_data(as_text=True)
        assert client.post(path, data={}).status_code == 400
        assert sent == []
        assert client.post(path, data={"agree":"yes"}).status_code == 200
        assert len(sent) == 1
        assert client.post(path, data={"agree":"yes"}).status_code == 200
        assert len(sent) == 1
        status = client.get("/api/payment/demo-status/"+str(data["transaction_id"]), headers={"X-User-Id":"1"})
        assert status.get_json()["data"]["status"] == "DEMO_SUCCESS"
        assert status.get_json()["data"]["premium_active"] is True
        assert db.session.get(User,1).SubscriptionStatus == "PREMIUM"
        assert db.session.get(User,1).PremiumExpiresAt is not None
        first_expiry = db.session.get(User,1).PremiumExpiresAt
        assert client.post(path, data={"agree": "yes"}).status_code == 200
        assert db.session.get(User,1).PremiumExpiresAt == first_expiry


def test_disabled_when_production(env, monkeypatch):
    monkeypatch.setenv("NUTRIFIT_ENV", "production")
    with env.test_client() as client:
        with client.session_transaction() as session:
            session["nutrifit_user_id"] = 1
        result = client.post("/api/payment/demo-checkout", json={"plan_id":4}, headers={"X-User-Id":"1"})
        assert result.status_code == 403


def test_limit_three_transactions_in_15_minutes(env):
    with env.test_client() as client:
        for i in range(3):
            _checkout(client)
        assert client.post("/api/payment/demo-checkout", json={"plan_id":4}, headers={"X-User-Id":"1"}).status_code == 429


def test_email_failure_does_not_undo_premium(env, monkeypatch):
    def smtp_down(_txn):
        raise ConnectionError('SMTP unavailable')
    monkeypatch.setattr(payment_routes, '_demo_email', smtp_down)
    with env.test_client() as client:
        data = _checkout(client)
        path = data['confirm_url'].replace('http://localhost', '')
        assert client.post(path, data={'agree':'yes'}).status_code == 200
        user = db.session.get(User, 1)
        assert user.SubscriptionStatus == 'PREMIUM'
        assert user.PremiumExpiresAt > __import__('datetime').datetime.utcnow()
        status = client.get('/api/payment/demo-status/'+str(data['transaction_id']))
        assert status.get_json()['data']['status'] == 'DEMO_MAIL_ERROR'
        assert status.get_json()['data']['premium_active'] is True
        assert status.get_json()['data']['email_sent'] is False
        expiry = user.PremiumExpiresAt
        assert client.post(path, data={'agree':'yes'}).status_code == 200
        assert db.session.get(User, 1).PremiumExpiresAt == expiry


def test_checkout_rejects_browser_backend_account_mismatch(env):
    with env.test_client() as client:
        with client.session_transaction() as session:
            session['nutrifit_user_id'] = 1
        response = client.post('/api/payment/demo-checkout', json={'plan_id': 4}, headers={'X-User-Id': '2'})
        assert response.status_code == 403
        assert PaymentTransaction.query.count() == 0
