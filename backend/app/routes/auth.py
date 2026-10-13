from flask import Blueprint, jsonify, request
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@auth_bp.route('/register', methods=['POST'])
def register():
    data = _payload()
    result, error, status = AuthService.register(data.get('email'), data.get('password'), data.get('full_name'))
    if error:
        return jsonify(success=False, message=error), status
    return jsonify(success=True, requires_otp=True,
                   message='Đã gửi mã xác minh. Vui lòng kiểm tra Gmail.', **result), status


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = _payload()
    user, error, status = AuthService.verify_otp(data.get('email'), data.get('otp'))
    if error:
        return jsonify(success=False, message=error), status
    return jsonify(success=True, user=user, message='Xác minh thành công. Tài khoản đã được kích hoạt.'), status


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = _payload()
    result, error, status = AuthService.resend_otp(data.get('email'))
    if error:
        return jsonify(success=False, message=error), status
    return jsonify(success=True, message='Đã gửi mã OTP mới.', **result), status


@auth_bp.route('/login', methods=['POST'])
def login():
    data = _payload()
    user, error = AuthService.login(data.get('email'), data.get('password'))
    if error:
        return jsonify(success=False, message=error), 401
    return jsonify(success=True, user=user, message='Đăng nhập thành công!'), 200
