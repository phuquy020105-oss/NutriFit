from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.module_auth import issue_access_token
from app.services.module_errors import api_errors, json_object, ModuleError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@api_errors
def register():
    data = json_object()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    if any(not isinstance(value, str) or not value.strip() for value in (email, password, full_name)):
        return jsonify({"success": False, "message": "Vui lòng nhập đầy đủ thông tin!"}), 400
    if len(email) > 100 or len(full_name) > 100 or not 6 <= len(password) <= 256:
        raise ModuleError("Thông tin đăng ký vượt giới hạn cho phép.")

    user, error = AuthService.register(email, password, full_name)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({
        "success": True,
        "message": "Đăng ký thành công!",
        "user": user,
        **issue_access_token(user['id'])
    }), 201

@auth_bp.route('/login', methods=['POST'])
@api_errors
def login():
    data = json_object()
    email = data.get('email')
    password = data.get('password')

    if any(not isinstance(value, str) or not value.strip() for value in (email, password)):
        return jsonify({"success": False, "message": "Vui lòng nhập email và mật khẩu!"}), 400

    if len(email) > 100 or len(password) > 256:
        raise ModuleError("Thông tin đăng nhập vượt giới hạn cho phép.")
    user, error = AuthService.login(email, password)
    if error:
        return jsonify({"success": False, "message": error}), 401

    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công!",
        "user": user,
        **issue_access_token(user['id'])
    }), 200
