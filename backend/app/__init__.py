from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, cors

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Khởi tạo extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Đăng ký Blueprints của TV1
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')

    # Endpoint kiểm tra kết nối hệ thống
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "connected",
            "message": "NutriFit Backend & Database 3NF hoạt động bình thường!"
        }), 200

    return app