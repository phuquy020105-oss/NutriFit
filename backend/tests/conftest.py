"""Offline pytest defaults; every DB fixture must explicitly use disposable data."""
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "setup")]


@pytest.fixture(autouse=True)
def offline_test_environment():
    from app.config import Config
    with patch.object(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"), \
            patch.dict(os.environ, {"GEMINI_API_KEY":""}), \
            patch("pymysql.connect", side_effect=AssertionError("Live MySQL prohibited in unit/regression tests")), \
            patch("requests.sessions.Session.request", side_effect=requests.ConnectionError("External HTTP prohibited in tests")), \
            patch("flask_mail.smtplib.SMTP", side_effect=AssertionError("SMTP prohibited in tests")), \
            patch("flask_mail.smtplib.SMTP_SSL", side_effect=AssertionError("SMTP prohibited in tests")):
        yield
