import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from app.models.user import User

SECRET_KEY = os.getenv('SECRET_KEY', 'nutrifit-fallback-secret-key-change-in-production')

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, "Thiếu hoặc sai định dạng Bearer token!"

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return None, "Người dùng không tồn tại!"
        return user, None
    except jwt.ExpiredSignatureError:
        return None, "Token đã hết hạn!"
    except jwt.InvalidTokenError:
        return None, "Token không hợp lệ!"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, error = get_current_user()
        if error:
            return jsonify({"success": False, "message": error}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, error = get_current_user()
        if error:
            return jsonify({"success": False, "message": error}), 401
        if user.Role != 'ADMIN':
            return jsonify({"success": False, "message": "Truy cập bị từ chối: Cần quyền Quản trị viên!"}), 403
        return f(*args, **kwargs)
    return decorated