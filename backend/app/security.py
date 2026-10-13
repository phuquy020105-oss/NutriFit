from functools import wraps
from flask import request, jsonify
from app.models.user import User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Lấy UserId từ header của request (Frontend gửi lên)
        user_id = request.headers.get('X-User-Id')
        
        if not user_id:
            return jsonify({
                "success": False, 
                "message": "Vui lòng đăng nhập để thực hiện chức năng này!"
            }), 401
            
        user = User.query.get(user_id)
        if not user or user.Role != 'ADMIN':
            return jsonify({
                "success": False, 
                "message": "Truy cập bị từ chối! Yêu cầu quyền Quản trị viên (ADMIN)."
            }), 403

        return f(*args, **kwargs)
    return decorated_function