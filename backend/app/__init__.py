import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv
from app.extensions import db, cors, mail

env_root = Path.cwd() / '.env'
env_backend = Path(__file__).resolve().parent.parent / '.env'

if env_backend.exists():
    load_dotenv(env_backend)
elif env_root.exists():
    load_dotenv(env_root)
else:
    load_dotenv()  

def create_app(test_config=None):
    app = Flask(__name__)

    from app.config import Config
    app.config.from_object(Config)

    # Cấu hình Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    if test_config is not None:
        app.config.update(test_config)

    # Khởi tạo các extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
                  allow_headers=['Content-Type', 'Authorization'])
    mail.init_app(app)

    # Đăng ký Blueprints
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.admin import admin_bp
    from app.routes.nutrition import nutrition_bp
    from app.routes.meals import meals_bp
    from app.ai.gemini_client import GeminiClient

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(profile_bp, url_prefix='/api/profile', name='profile_api')
    app.register_blueprint(admin_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(meals_bp)
    app.extensions['nutrifit_gemini'] = GeminiClient(
        api_key=app.config['GEMINI_API_KEY'], model=app.config['GEMINI_MODEL'],
        timeout=max(1, min(app.config['GEMINI_TIMEOUT_SECONDS'], 30)),
        retries=max(0, min(app.config['GEMINI_MAX_RETRIES'], 2)),
        cooldown=max(1, app.config['GEMINI_COOLDOWN_SECONDS']))

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {"status": "connected", "message": "NutriFit Backend running smoothly"}, 200

    return app
