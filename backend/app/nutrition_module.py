"""Small integration point; core database, mail and profile remain unchanged."""
import os
import secrets
import math
from flask import request, session
from app.ai.gemini_client import GeminiClient

_DEMO_SESSION_KEY = secrets.token_urlsafe(32)


def bounded_env(name, default, low, high, integer=False):
    try:
        value = float(os.getenv(name, str(default)))
        if not math.isfinite(value):
            return default
        value = max(low, min(value, high))
        return int(value) if integer else value
    except (ValueError, TypeError, OverflowError):
        return default


def init_nutrition(app):
    if not app.secret_key:
        app.secret_key = os.getenv("SECRET_KEY") or _DEMO_SESSION_KEY
    app.config.setdefault("NUTRIFIT_TIMEZONE", os.getenv("NUTRIFIT_TIMEZONE", "Asia/Ho_Chi_Minh"))
    app.config.setdefault("NUTRITION_FRONTEND_ORIGINS", [value.strip() for value in os.getenv(
        "NUTRITION_FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
    ).split(",") if value.strip()])
    app.extensions["nutrifit_gemini"] = GeminiClient(
        api_key=os.getenv("GEMINI_API_KEY", ""), model=os.getenv("GEMINI_MODEL", ""),
        timeout=bounded_env("GEMINI_TIMEOUT_SECONDS", 10, 1, 30),
        retries=bounded_env("GEMINI_MAX_RETRIES", 1, 0, 2, integer=True),
        cooldown=bounded_env("GEMINI_COOLDOWN_SECONDS", 30, 1, 3600))
    from app.routes.nutrition import nutrition_bp
    from app.routes.meals import meals_bp
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(meals_bp)

    @app.after_request
    def core_login_session(response):
        endpoint = request.endpoint or ""
        origin = request.headers.get("Origin")
        allowed = not origin or origin in app.config["NUTRITION_FRONTEND_ORIGINS"]
        if endpoint in ("auth.login", "auth.register") and request.method == "POST" and allowed:
            body = response.get_json(silent=True)
            if response.status_code in (200, 201) and isinstance(body, dict) and body.get("success") is True:
                user = body.get("user") or {}
                if type(user.get("id")) is int:
                    session.clear()
                    session["nutrifit_user_id"] = user["id"]
        if endpoint.startswith(("nutrition.", "meals.", "profile_bp.")) or endpoint in ("auth.login", "auth.register"):
            if origin and allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.vary.add("Origin")
        return response
