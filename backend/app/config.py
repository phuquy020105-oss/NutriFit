"""Environment-driven NutriFit configuration; secrets are kept in the local .env."""
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

class Config:
    NUTRIFIT_ENV = os.getenv("NUTRIFIT_ENV", "production").strip().lower()
    NUTRIFIT_DEMO_REGISTRATION = os.getenv("NUTRIFIT_DEMO_REGISTRATION", "false").strip().lower() in {"1", "true", "yes", "on"}
    # Mail suppression cannot be enabled through environment outside development.
    MAIL_SUPPRESS_SEND = (NUTRIFIT_ENV == "development" and
                         os.getenv("MAIL_SUPPRESS_SEND", "false").strip().lower() in {"1", "true", "yes", "on"})
    SECRET_KEY = os.getenv("SECRET_KEY") or "change-this-local-development-secret"
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "NutriFitDB")
    _encoded_pass = quote_plus(DB_PASS) if DB_PASS else ""
    _auth_part = f"{DB_USER}:{_encoded_pass}" if _encoded_pass else DB_USER
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or (
        f"mysql+pymysql://{_auth_part}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    
    # Flask-Mail: đọc cấu hình SMTP từ file .env
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_TIMEOUT = int(os.getenv("MAIL_TIMEOUT", "20"))

    MAIL_USE_TLS = (
        os.getenv("MAIL_USE_TLS", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    MAIL_USE_SSL = (
        os.getenv("MAIL_USE_SSL", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    MAIL_USERNAME = os.getenv("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = (
        os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME
    )
