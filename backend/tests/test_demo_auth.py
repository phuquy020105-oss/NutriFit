"""OTP security regression tests, SQLite memory only, SMTP fully mocked.

Run: python -m pytest backend/tests/test_demo_auth.py -q
"""
import os
import secrets
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.config import Config
from app.extensions import db
from app.models.user import User
from app.models.registration_otp import RegistrationOTP, RegistrationOTPIPQuota
from app.services.auth_service import AuthService
from werkzeug.security import check_password_hash


class RegistrationOTPTests(unittest.TestCase):
    def setUp(self):
        self.password = 'long-secure-password-456'
        self.email = 'test@gmail.com'
        with patch.multiple(Config, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
                            SECRET_KEY=secrets.token_urlsafe(32), NUTRIFIT_ENV='production',
                            NUTRIFIT_DEMO_REGISTRATION=True, MAIL_SUPPRESS_SEND=False,
                            MAIL_USERNAME='sender@gmail.com', MAIL_PASSWORD='dummy-test-password',
                            MAIL_DEFAULT_SENDER='sender@gmail.com'):
            self.app = create_app()
        self.app.config.update(TESTING=True, MAIL_USERNAME='sender@gmail.com',
                               MAIL_PASSWORD='dummy-test-password', MAIL_DEFAULT_SENDER='sender@gmail.com')
        self.context = self.app.app_context()
        self.context.push()
        User.__table__.create(db.engine)
        RegistrationOTP.__table__.create(db.engine)
        RegistrationOTPIPQuota.__table__.create(db.engine)
        self.client = self.app.test_client()
        self.mail_patch = patch('app.services.auth_service.mail.send')
        self.mock_send = self.mail_patch.start()
        self.addCleanup(self.mail_patch.stop)

    def tearDown(self):
        db.session.remove()
        RegistrationOTPIPQuota.__table__.drop(db.engine)
        RegistrationOTP.__table__.drop(db.engine)
        User.__table__.drop(db.engine)
        self.context.pop()

    def begin(self, **overrides):
        data = {'email': self.email, 'password': self.password, 'full_name': 'Demo OTP'}
        data.update(overrides)
        return self.client.post('/api/auth/register', json=data,
                                headers={'Origin': 'http://127.0.0.1:5500'})

    def code(self):
        return self.mock_send.call_args[0][0].body.split('Mã xác minh NutriFit của bạn: ')[1][:6]

    def verify(self, otp, email=None):
        return self.client.post('/api/auth/verify-otp', json={'email': email or self.email, 'otp': otp},
                                headers={'Origin': 'http://127.0.0.1:5500'})

    def test_signup_without_otp_does_not_create_user_or_login(self):
        r = self.begin()
        self.assertEqual(r.status_code, 202)
        self.assertTrue(r.json['requires_otp'])
        self.assertNotIn('user', r.json)
        self.assertNotIn('Set-Cookie', r.headers)
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(RegistrationOTP.query.count(), 1)
        self.assertEqual(self.client.post('/api/auth/login', json={'email': self.email,
                    'password': self.password}).status_code, 401)
        self.mock_send.assert_called_once()
        self.assertNotIn(self.code(), RegistrationOTP.query.one().OTPHash)
        self.assertNotEqual(RegistrationOTP.query.one().PasswordHash, self.password)

    def test_correct_otp_creates_account_once_and_logs_in(self):
        self.assertEqual(self.begin().status_code, 202)
        r = self.verify(self.code())
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.json['success'])
        self.assertEqual(r.json['user']['role'], 'MEMBER')
        self.assertIn('session=', r.headers['Set-Cookie'])
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(RegistrationOTP.query.count(), 0)
        self.assertTrue(check_password_hash(User.query.one().PasswordHash, self.password))
        self.assertEqual(self.verify(self.code()).status_code, 400)
        self.assertEqual(User.query.count(), 1)

    def test_wrong_otp_and_five_attempt_limit(self):
        self.begin()
        code = self.code()
        invalid = '000000' if code != '000000' else '999999'
        for _ in range(5):
            self.assertEqual(self.verify(invalid).status_code, 400)
        self.assertEqual(self.verify(code).status_code, 429)
        self.assertEqual(User.query.count(), 0)

    def test_expired_otp_rejected(self):
        self.begin()
        code = self.code()
        row = RegistrationOTP.query.one()
        row.ExpiresAt = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
        self.assertEqual(self.verify(code).status_code, 400)
        self.assertEqual(User.query.count(), 0)

    def test_resend_revokes_old_code_and_cooldown(self):
        self.begin()
        first = self.code()
        resp = self.client.post('/api/auth/resend-otp', json={'email': self.email})
        self.assertEqual(resp.status_code, 429)
        row = RegistrationOTP.query.one()
        row.LastSentAt = datetime.utcnow() - timedelta(seconds=61)
        db.session.commit()
        resp = self.client.post('/api/auth/resend-otp', json={'email': self.email})
        self.assertEqual(resp.status_code, 202)
        new = self.code()
        if first == new:  # negligible random collision; inject unmatching code safely
            first = '000000' if new != '000000' else '999999'
        self.assertEqual(self.verify(first).status_code, 400)
        self.assertEqual(self.verify(new).status_code, 201)

    def test_non_gmail_and_malformed_input_rejected_without_email(self):
        for email in ['someone@outlook.com', 'someone@nutri.com.vn', 'bad', 'a@gmail.com.evil', 123]:
            with self.subTest(email=email):
                self.assertEqual(self.begin(email=email).status_code, 400)
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(self.mock_send.call_count, 0)

    def test_mail_failure_never_creates_user(self):
        self.mock_send.side_effect = RuntimeError('secret SMTP detail')
        with self.assertLogs(self.app.logger, level='WARNING') as logs:
            r = self.begin()
        self.assertEqual(r.status_code, 503)
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(RegistrationOTP.query.count(), 0)
        self.assertNotIn('secret SMTP detail', ''.join(logs.output))

    def test_demo_mode_never_bypasses_otp(self):
        self.app.config.update(NUTRIFIT_ENV='development', NUTRIFIT_DEMO_REGISTRATION=True)
        self.assertEqual(self.begin().status_code, 202)
        self.assertEqual(User.query.count(), 0)

    def test_mail_suppression_denied(self):
        self.app.config['MAIL_SUPPRESS_SEND'] = True
        self.assertEqual(self.begin().status_code, 503)
        self.assertEqual(self.mock_send.call_count, 0)

    def test_email_rate_limit(self):
        self.assertEqual(self.begin().status_code, 202)
        for n in range(4):
            row = RegistrationOTP.query.one()
            row.LastSentAt = datetime.utcnow() - timedelta(seconds=61)
            db.session.commit()
            self.assertEqual(self.client.post('/api/auth/resend-otp', json={'email': self.email}).status_code, 202)
        row = RegistrationOTP.query.one()
        row.LastSentAt = datetime.utcnow() - timedelta(seconds=61)
        db.session.commit()
        self.assertEqual(self.client.post('/api/auth/resend-otp', json={'email': self.email}).status_code, 429)
        self.assertEqual(User.query.count(), 0)


if __name__ == '__main__':
    unittest.main()
