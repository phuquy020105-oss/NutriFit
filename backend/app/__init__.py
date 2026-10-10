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

def create_app():
    app = Flask(__name__)

    # Cấu hình Database
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # Giá trị dự phòng chuẩn xác theo cấu hình của bạn
        db_url = "mysql+pymysql://root:Quy020105%40@localhost:3306/NutriFitDB"

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Cấu hình Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Khởi tạo các extensions
    db.init_app(app)
    cors.init_app(app)
    mail.init_app(app)

    # Đăng ký Blueprints
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)

    from app.nutrition_module import init_nutrition
    init_nutrition(app)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {"status": "connected", "message": "NutriFit Backend running smoothly"}, 200

    return app
