"""Admin reports confirmed test transactions separately from actual cash receipts.
Run: python -m pytest backend/tests/test_admin_demo_revenue.py -q
"""
from pathlib import Path
import sys

import pytest
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.extensions import db, mail
from app.models.user import User, PaymentTransaction, SubscriptionPlan
from app.routes import admin as admin_routes
from app.routes import payment as payment_routes


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('NUTRIFIT_ENV', 'development')
    monkeypatch.setenv('NUTRIFIT_PAYMENT_DEMO_MODE', 'true')
    monkeypatch.delenv('NUTRIFIT_DEMO_QR_BASE_URL', raising=False)
    app = Flask(__name__)
    app.config.update(SECRET_KEY='local-test-key-only', SQLALCHEMY_DATABASE_URI='sqlite://',
                      SQLALCHEMY_TRACK_MODIFICATIONS=False, TESTING=True,
                      MAIL_SUPPRESS_SEND=True, MAIL_DEFAULT_SENDER='testing@example.com')
    db.init_app(app)
    mail.init_app(app)
    app.register_blueprint(payment_routes.payment_bp)
    app.register_blueprint(admin_routes.admin_bp)
    with app.app_context():
        db.create_all()
        db.session.add_all([
            User(UserId=1, Email='admin@example.com', FullName='Admin', PasswordHash='x', Role='ADMIN'),
            User(UserId=2, Email='buyer@example.com', FullName='Buyer', PasswordHash='x', Role='MEMBER'),
            SubscriptionPlan(PlanId=4, PlanName='Premium 1 Tháng', PriceVnd=99000, DurationDays=30, IsActive=True),
        ])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


def _stats(client):
    response = client.get('/api/admin/dashboard?period=day', headers={'X-User-Id': '1'})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()['data']


def _checkout(client):
    with client.session_transaction() as session:
        session['nutrifit_user_id'] = 2
    response = client.post('/api/payment/demo-checkout', json={'plan_id': 4}, headers={'X-User-Id': '2'})
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()['data']


def test_pending_does_not_increase_confirmed_value(app, monkeypatch):
    monkeypatch.setattr(payment_routes, '_demo_email', lambda txn: None)
    with app.test_client() as client:
        data = _checkout(client)
        initial = _stats(client)
        assert initial['financial']['total_confirmed_value_vnd'] == 0
        assert initial['financial']['simulated_revenue_vnd'] == 0
        assert initial['financial']['total_transactions'] == 1

        path = data['confirm_url'].removeprefix('http://localhost')
        assert client.post(path, data={'agree': 'yes'}).status_code == 200
        confirmed = _stats(client)
        assert confirmed['financial']['total_confirmed_value_vnd'] == 99000
        assert confirmed['financial']['simulated_revenue_vnd'] == 99000
        assert confirmed['financial']['real_revenue_vnd'] == 0
        assert confirmed['financial']['confirmed_transactions'] == 1
        assert confirmed['revenue_chart'][0]['simulated_value'] == 99000

        assert client.post(path, data={'agree': 'yes'}).status_code == 200
        assert _stats(client)['financial']['total_confirmed_value_vnd'] == 99000
        assert db.session.get(User, 2).SubscriptionStatus == 'PREMIUM'


def test_live_income_and_simulated_value_are_distinct(app, monkeypatch):
    monkeypatch.setattr(payment_routes, '_demo_email', lambda txn: None)
    with app.test_client() as client:
        demo = _checkout(client)
        client.post(demo['confirm_url'].removeprefix('http://localhost'), data={'agree': 'yes'})
        db.session.add(PaymentTransaction(UserId=2, PlanId=4, AmountVnd=250000,
                          PaymentMethod='BANK_TRANSFER', Status='SUCCESS', TransactionCode='REAL_001'))
        db.session.add(PaymentTransaction(UserId=2, PlanId=4, AmountVnd=300000,
                          PaymentMethod='DEMO', Status='PENDING', TransactionCode='OLD_DEMO_PENDING'))
        db.session.add(PaymentTransaction(UserId=2, PlanId=4, AmountVnd=50000,
                          PaymentMethod='DEMO', Status='SUCCESS', TransactionCode='OLD_DEMO_SUCCESS'))
        db.session.commit()
        fin = _stats(client)['financial']
        assert fin['real_revenue_vnd'] == 250000
        assert fin['total_revenue_vnd'] == 250000  # Backward-compatible actual receipts
        assert fin['simulated_revenue_vnd'] == 149000
        assert fin['total_confirmed_value_vnd'] == 399000
        assert fin['confirmed_transactions'] == 3


def test_confirmed_payment_is_still_counted_when_mail_fails(app, monkeypatch):
    def fail_email(_txn):
        raise OSError('SMTP offline')
    monkeypatch.setattr(payment_routes, '_demo_email', fail_email)
    with app.test_client() as client:
        demo = _checkout(client)
        url = demo['confirm_url'].removeprefix('http://localhost')
        assert client.post(url, data={'agree': 'yes'}).status_code == 200
        record = db.session.get(PaymentTransaction, demo['transaction_id'])
        assert record.Status == 'DEMO_MAIL_ERROR'
        stats = _stats(client)
        assert stats['financial']['simulated_revenue_vnd'] == 99000
        assert stats['financial']['real_revenue_vnd'] == 0
