from flask import Blueprint, jsonify
from app.models.user import User
from app.security import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Chỉ Admin mới có quyền xem toàn bộ người dùng trong hệ thống"""
    users = User.query.all()
    user_list = [u.to_dict() for u in users]
    
    return jsonify({
        "success": True,
        "total": len(user_list),
        "data": user_list
    }), 200