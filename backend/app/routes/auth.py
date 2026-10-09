from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    if not email or not password or not full_name:
        return jsonify({"success": False, "message": "Vui lòng nhập đủ thông tin."}), 400

    user, error = AuthService.register(email, password, full_name)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({
        "success": True,
        "message": "Đăng ký thành công!",
        "user": {"id": user.UserId, "email": user.Email, "full_name": user.FullName}
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    user, error = AuthService.login(email, password)
    if error:
        return jsonify({"success": False, "message": error}), 401

    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công!",
        "user": {"id": user.UserId, "email": user.Email, "full_name": user.FullName}
    }), 200