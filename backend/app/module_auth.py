"""Use a signed Flask session established by the existing core login response."""
from functools import wraps
from flask import current_app, request, session
from app.extensions import db
from app.models.user import User
from app.services.module_errors import ModuleError, positive_id


def login_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        user_id = session.get("nutrifit_user_id")
        if type(user_id) is not int or db.session.get(User, user_id) is None:
            session.pop("nutrifit_user_id", None)
            raise ModuleError("Hãy đăng nhập trước khi sử dụng chức năng này.", "AUTH_REQUIRED", 401)
        origin = request.headers.get("Origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin and origin not in current_app.config["NUTRITION_FRONTEND_ORIGINS"]:
            raise ModuleError("Origin không được phép.", "FORBIDDEN", 403)
        return function(*args, **kwargs)
    return wrapped


def check_user_identity(data=None, path_user_id=None):
    user_id = session["nutrifit_user_id"]
    sources = [request.args] + ([data] if data is not None else [])
    ids = [path_user_id] if path_user_id is not None else []
    for source in sources:
        for name in ("user_id", "userId"):
            if name in source:
                ids.append(positive_id(source[name], name))
    if any(value != user_id for value in ids):
        raise ModuleError("Không có quyền truy cập dữ liệu người dùng khác.", "FORBIDDEN", 403)
    return user_id
