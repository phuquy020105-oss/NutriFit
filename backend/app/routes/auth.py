from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.security import generate_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    if not email or not password or not full_name:
        return jsonify({"success": False, "message": "Vui lòng nhập đầy đủ họ tên, email và mật khẩu!"}), 400

    user, error = AuthService.register(email, password, full_name)
    if error:
        return jsonify({"success": False, "message": error}), 400

    # Tự động tạo token ngay sau khi đăng ký (tiện cho frontend tự đăng nhập luôn)
    token = generate_token(user['id'], user['role'])

    return jsonify({
        "success": True,
        "message": "Đăng ký thành công!",
        "access_token": token,
        "user": user
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Vui lòng nhập email và mật khẩu!"}), 400

    user, error = AuthService.login(email, password)
    if error:
        return jsonify({"success": False, "message": error}), 401

    # Tạo JWT token chứa user_id và role
    token = generate_token(user['id'], user['role'])

    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công!",
        "access_token": token,
        "user": user
    }), 200