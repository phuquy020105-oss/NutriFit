"""NutriFit application factory integrating core, nutrition, workout and chatbot APIs."""
import os
import time
from flask import Flask, jsonify, request, g
from app.config import Config
from app.extensions import db, cors, mail


def _frontend_origins():
    raw = os.getenv(
        "NUTRITION_FRONTEND_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,http://localhost:8000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # These extensions are initialized once on the combined app.
    db.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": _frontend_origins()}},
        supports_credentials=True,
    )
    mail.init_app(app)

    # Lightweight latency diagnostics: no request body, session, credentials or
    # API keys are written to the log. See X-NutriFit-Request-Ms in Network.
    @app.before_request
    def _start_api_timer():
        if request.path.startswith('/api/'):
            g.nutrifit_started = time.perf_counter()

    @app.after_request
    def _record_api_timer(response):
        start = getattr(g, 'nutrifit_started', None)
        if start is not None:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            response.headers['X-NutriFit-Request-Ms'] = str(elapsed_ms)
            if elapsed_ms >= 3000:
                app.logger.warning('SLOW_API %s %s status=%s duration_ms=%.1f',
                                   request.method, request.path, response.status_code, elapsed_ms)
        return response

    # Base project: authentication, profile, admin and payment.
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.admin import admin_bp
    from app.routes.payment import payment_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)

    # TV4: Workout, weekly Progress and Street Food.
    from app.routes.workouts import workout_bp, progress_bp, street_food_bp
    app.register_blueprint(workout_bp, url_prefix="/api/workouts")
    app.register_blueprint(progress_bp, url_prefix="/api/progress")
    app.register_blueprint(street_food_bp, url_prefix="/api/street-food")

    # Chatbox AI.
    from app.routes.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp)

    # TV3: Nutrition V4, meal planner, food intake/catalog and Premium Quick Food.
    from app.nutrition_module import init_nutrition
    init_nutrition(app)

    @app.route("/api/health/db", methods=["GET"])
    def database_health():
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        from app.extensions import db
        start = time.perf_counter()
        try:
            db.session.execute(text('SELECT 1')).scalar()
            return jsonify(status='connected', component='database',
                db_ms=round((time.perf_counter()-start)*1000, 1)), 200
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception('Database health query failed')
            return jsonify(status='unavailable', component='database'), 503

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "connected",
            "build": "premium-workout-daily-plan-20261014",
            "message": "NutriFit Backend: core, nutrition, workout and chatbot modules loaded",
        }), 200

    return app
