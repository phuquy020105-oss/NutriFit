"""Signed bearer identity for Nutrition/Meal; never trust caller-supplied user IDs."""
from functools import wraps
from flask import current_app, g, request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.extensions import db
from app.models.user import User
from app.services.module_errors import ModuleError, positive_id


def serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="nutrifit-access-v1")


def issue_access_token(user_id):
    return {"access_token": serializer().dumps({"user_id": user_id}), "token_type": "Bearer",
            "expires_in": current_app.config["ACCESS_TOKEN_MAX_AGE"]}


def login_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ModuleError("Cần đăng nhập bằng Bearer token.", "AUTH_REQUIRED", 401)
        try:
            payload = serializer().loads(parts[1], max_age=current_app.config["ACCESS_TOKEN_MAX_AGE"])
        except (BadSignature, SignatureExpired):
            raise ModuleError("Phiên đăng nhập không hợp lệ hoặc đã hết hạn.", "INVALID_TOKEN", 401) from None
        if not isinstance(payload, dict) or type(payload.get("user_id")) is not int:
            raise ModuleError("Phiên đăng nhập không hợp lệ.", "INVALID_TOKEN", 401)
        user = db.session.get(User, payload["user_id"])
        if user is None:
            raise ModuleError("Tài khoản không còn tồn tại.", "INVALID_TOKEN", 401)
        g.current_user_id = user.UserId
        return function(*args, **kwargs)
    return wrapped


def check_user_identity(data=None, path_user_id=None):
    sources = [request.args]
    if data is not None:
        sources.append(data)
    ids = [path_user_id] if path_user_id is not None else []
    for source in sources:
        for name in ("user_id", "userId"):
            if name in source:
                ids.append(positive_id(source[name], name))
    if any(value != g.current_user_id for value in ids):
        raise ModuleError("Không có quyền truy cập dữ liệu người dùng khác.", "FORBIDDEN", 403)
    return g.current_user_id
