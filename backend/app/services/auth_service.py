"""Email-OTP registration: send code, verify inbox ownership, create account.

OTP is always enforced, including local development. Demo flags cannot bypass it.
"""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

from flask import current_app, request
from flask_mail import Message
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, mail
from app.models.user import User
from app.models.registration_otp import RegistrationOTP, RegistrationOTPIPQuota

OTP_LIFETIME = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
RATE_WINDOW = timedelta(hours=1)
MAX_EMAIL_SENDS = 5
MAX_IP_SENDS = 15
MAX_VERIFY_ATTEMPTS = 5


class AuthService:
    @staticmethod
    def validate_email_format(email):
        return isinstance(email, str) and re.fullmatch(r'[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9.-]+', email) is not None

    @staticmethod
    def _email(email):
        return email.strip().lower() if isinstance(email, str) else ''

    @staticmethod
    def _gmail(email):
        # The user explicitly wants Gmail-only signups. OTP proves ownership.
        return len(email) <= 100 and re.fullmatch(r'[a-z0-9][a-z0-9.+-]*@gmail\.com', email) is not None

    @staticmethod
    def _digest(subject, code):
        secret = current_app.config['SECRET_KEY'].encode('utf-8')
        return hmac.new(secret, f'{subject}:{code}'.encode('utf-8'), hashlib.sha256).hexdigest()

    @staticmethod
    def _mail_ready():
        config = current_app.config
        extension = current_app.extensions.get('mail')
        return (bool(config.get('MAIL_USERNAME')) and bool(config.get('MAIL_PASSWORD')) and
                bool(config.get('MAIL_DEFAULT_SENDER')) and
                not bool(config.get('MAIL_SUPPRESS_SEND')) and
                not bool(getattr(extension, 'suppress', False)))

    @staticmethod
    def _send_code(email, code):
        msg = Message(subject='[NutriFit] Mã xác minh đăng ký', recipients=[email])
        msg.body = (f'Mã xác minh NutriFit của bạn: {code}\n\n'
                    'Mã có hiệu lực 10 phút và chỉ dùng một lần.\n'
                    'Nếu bạn không đăng ký, vui lòng bỏ qua email này.\n'
                    'Không cung cấp mã cho bất kỳ ai.\n')
        mail.send(msg)

    @staticmethod
    def _start_code(email, full_name=None, password=None, resend=False):
        now = datetime.utcnow()
        if not AuthService._gmail(email):
            return None, 'NutriFit chỉ hỗ trợ đăng ký bằng Gmail (@gmail.com).', 400
        if User.query.filter_by(Email=email).first():
            return None, 'Gmail này đã được đăng ký.', 409
        if not AuthService._mail_ready():
            return None, 'Chưa cấu hình SMTP thật. Kiểm tra MAIL_USERNAME / MAIL_PASSWORD.', 503

        row = RegistrationOTP.query.filter_by(Email=email).with_for_update().first()
        if resend and row is None:
            return None, 'Không tìm thấy yêu cầu đăng ký. Vui lòng bắt đầu lại.', 400
        if row and now - row.LastSentAt < RESEND_COOLDOWN:
            return None, 'Vui lòng chờ 60 giây trước khi gửi mã mới.', 429
        if row and now - row.WindowStart < RATE_WINDOW and row.SentInWindow >= MAX_EMAIL_SENDS:
            return None, 'Gmail này đã yêu cầu quá nhiều mã. Hãy thử lại sau một giờ.', 429

        # Never trust X-Forwarded-For on a direct Flask deployment.
        source_ip = request.remote_addr or 'unknown'
        ip_digest = AuthService._digest('ip', source_ip)
        quota = RegistrationOTPIPQuota.query.filter_by(IPHash=ip_digest).with_for_update().first()
        if quota and now - quota.WindowStart < RATE_WINDOW and quota.SentInWindow >= MAX_IP_SENDS:
            return None, 'Quá nhiều yêu cầu gửi OTP từ kết nối này. Hãy thử lại sau.', 429

        if not resend:
            if (not isinstance(full_name, str) or not full_name.strip() or len(full_name.strip()) > 100 or
                    not isinstance(password, str) or not 8 <= len(password) <= 128):
                return None, 'Nhập họ tên và mật khẩu từ 8 đến 128 ký tự.', 400
            new_name = full_name.strip()
            new_password_hash = generate_password_hash(password)
        else:
            new_name, new_password_hash = row.FullName, row.PasswordHash

        code = f'{secrets.randbelow(1000000):06d}'
        try:
            AuthService._send_code(email, code)
        except Exception as exc:
            db.session.rollback()
            current_app.logger.warning('OTP_MAIL_SEND_FAILED type=%s', type(exc).__name__)
            return None, 'Không gửi được OTP. Kiểm tra Gmail SMTP và thử lại.', 503

        if row is None:
            row = RegistrationOTP(Email=email, WindowStart=now, SentInWindow=0)
            db.session.add(row)
        elif now - row.WindowStart >= RATE_WINDOW:
            row.WindowStart, row.SentInWindow = now, 0
        row.FullName = new_name
        row.PasswordHash = new_password_hash
        row.OTPHash = AuthService._digest(email, code)
        row.ExpiresAt = now + OTP_LIFETIME
        row.LastSentAt = now
        row.Attempts = 0
        row.SentInWindow += 1
        if quota is None:
            quota = RegistrationOTPIPQuota(IPHash=ip_digest, WindowStart=now, SentInWindow=0)
            db.session.add(quota)
        elif now - quota.WindowStart >= RATE_WINDOW:
            quota.WindowStart, quota.SentInWindow = now, 0
        quota.SentInWindow += 1
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None, 'Có yêu cầu trùng lặp, vui lòng thử lại sau 60 giây.', 409
        return {'email': email, 'expires_in_seconds': 600, 'resend_after_seconds': 60}, None, 202

    @staticmethod
    def register(email, password, full_name):
        email = AuthService._email(email)
        return AuthService._start_code(email, full_name, password)

    @staticmethod
    def resend_otp(email):
        return AuthService._start_code(AuthService._email(email), resend=True)

    @staticmethod
    def verify_otp(email, otp):
        email = AuthService._email(email)
        if not AuthService._gmail(email) or not isinstance(otp, str) or not re.fullmatch(r'\d{6}', otp):
            return None, 'Gmail hoặc OTP không hợp lệ.', 400
        row = RegistrationOTP.query.filter_by(Email=email).with_for_update().first()
        if not row:
            return None, 'Không tìm thấy mã. Hãy yêu cầu đăng ký lại.', 400
        now = datetime.utcnow()
        if now > row.ExpiresAt:
            db.session.delete(row)
            db.session.commit()
            return None, 'Mã OTP hết hạn. Vui lòng đăng ký lại.', 400
        if row.Attempts >= MAX_VERIFY_ATTEMPTS:
            return None, 'Bạn đã nhập sai quá nhiều lần. Hãy yêu cầu mã mới.', 429
        if not hmac.compare_digest(row.OTPHash, AuthService._digest(email, otp)):
            row.Attempts += 1
            db.session.commit()
            return None, ('Mã OTP không đúng.' if row.Attempts < MAX_VERIFY_ATTEMPTS
                          else 'Bạn đã nhập sai 5 lần. Hãy yêu cầu mã mới.'), 400
        if User.query.filter_by(Email=email).first():
            db.session.delete(row)
            db.session.commit()
            return None, 'Gmail này đã được đăng ký.', 409

        new_user = User(Email=email, PasswordHash=row.PasswordHash,
                        FullName=row.FullName, Role='MEMBER')
        db.session.add(new_user)
        db.session.delete(row)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None, 'Gmail này đã được đăng ký.', 409
        return new_user.to_dict(), None, 201

    @staticmethod
    def login(email, password):
        if not isinstance(email, str) or not isinstance(password, str):
            return None, 'Email hoặc mật khẩu không chính xác!'
        user = User.query.filter_by(Email=email.strip().lower()).first()
        if not user or not check_password_hash(user.PasswordHash, password):
            return None, 'Email hoặc mật khẩu không chính xác!'
        return user.to_dict(), None
