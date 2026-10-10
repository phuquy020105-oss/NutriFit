from flask import Blueprint, jsonify
from app.services.profile_service import ProfileService
from app.models.health import UserProfile
from app.module_auth import login_required, check_user_identity
from app.services.module_errors import api_errors, json_object
from app.services.nutrition_service import NutritionService

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/save', methods=['POST'])
@api_errors
@login_required
def save_profile():
    data = json_object()
    user_id = check_user_identity(data)

    profile = ProfileService.save_profile(user_id, data)
    return jsonify({
        "success": True,
        "message": "Lưu hồ sơ thành công!",
        "data": NutritionService.from_profile(profile)
    }), 200

@profile_bp.route('/<int:user_id>', methods=['GET'])
@api_errors
@login_required
def get_profile(user_id):
    check_user_identity(path_user_id=user_id)
    profile = UserProfile.query.filter_by(UserId=user_id).first()
    if not profile:
        return jsonify({"success": False, "message": "Chưa có dữ liệu hồ sơ"}), 404

    return jsonify({
        "success": True,
        "data": NutritionService.from_profile(profile)
    }), 200
