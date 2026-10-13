"""Persist unverified signups separately; Users only contains verified accounts."""
from app.extensions import db


class RegistrationOTP(db.Model):
    __tablename__ = 'RegistrationOTPs'

    Email = db.Column(db.String(100), primary_key=True)
    FullName = db.Column(db.String(100), nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    OTPHash = db.Column(db.String(64), nullable=False)
    ExpiresAt = db.Column(db.DateTime, nullable=False)
    LastSentAt = db.Column(db.DateTime, nullable=False)
    Attempts = db.Column(db.Integer, nullable=False, default=0)
    WindowStart = db.Column(db.DateTime, nullable=False)
    SentInWindow = db.Column(db.Integer, nullable=False, default=0)


class RegistrationOTPIPQuota(db.Model):
    __tablename__ = 'RegistrationOTPIPQuota'

    IPHash = db.Column(db.String(64), primary_key=True)
    WindowStart = db.Column(db.DateTime, nullable=False)
    SentInWindow = db.Column(db.Integer, nullable=False, default=0)
