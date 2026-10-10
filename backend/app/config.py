import os
import secrets
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # An ephemeral local key avoids embedding credentials in source. Set SECRET_KEY
    # in the environment for stable tokens across restarts/multiple workers.
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "NutriFitDB")
    encoded_pass = quote_plus(DB_PASS) if DB_PASS else ""
    auth_part = f"{quote_plus(DB_USER)}:{encoded_pass}" if encoded_pass else quote_plus(DB_USER)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or (
        f"mysql+pymysql://{auth_part}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ACCESS_TOKEN_MAX_AGE = int(os.getenv("ACCESS_TOKEN_MAX_AGE", "3600"))
    MAX_CONTENT_LENGTH = 65536
    NUTRIFIT_TIMEZONE = os.getenv("NUTRIFIT_TIMEZONE", "Asia/Ho_Chi_Minh")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")
    GEMINI_TIMEOUT_SECONDS = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "10"))
    GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "1"))
    GEMINI_COOLDOWN_SECONDS = int(os.getenv("GEMINI_COOLDOWN_SECONDS", "30"))
    CORS_ORIGINS = [origin.strip() for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,http://localhost:8000"
    ).split(",") if origin.strip()]
