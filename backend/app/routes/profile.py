from flask import Blueprint, request, jsonify
from app.services.profile_service import ProfileService
from app.models.health import UserProfile

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/save', methods=['POST'])
def save_profile():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Thiếu user_id"}), 400

    profile = ProfileService.save_profile(user_id, data)
    return jsonify({
        "success": True,
        "message": "Lưu hồ sơ thành công!",
        "data": {
            "bmr": profile.Bmr,
            "tdee": profile.Tdee,
            "target_kcal": profile.TargetKcal,
            "target_water_ml": profile.TargetWaterMl
        }
    }), 200

@profile_bp.route('/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    profile = UserProfile.query.filter_by(UserId=user_id).first()
    if not profile:
        return jsonify({"success": False, "message": "Chưa có dữ liệu hồ sơ"}), 404

    return jsonify({
        "success": True,
        "data": {
            "gender": profile.Gender,
            "age": profile.Age,
            "height": profile.HeightCm,
            "weight": profile.WeightKg,
            "goal": profile.Goal,
            "bmr": profile.Bmr,
            "tdee": profile.Tdee,
            "target_kcal": profile.TargetKcal,
            "target_water_ml": profile.TargetWaterMl
        }
    }), 200