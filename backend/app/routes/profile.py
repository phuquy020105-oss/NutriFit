from flask import Blueprint, request, jsonify
import math
from app.services.profile_service import ProfileService
from app.models.health import UserProfile

# Keep existing Frontend route contract (/save and /<user_id>) for compatibility.
profile_bp = Blueprint('profile_bp', __name__)


def calculate_profile_bmi(profile):
    """Tính BMI từ dữ liệu hồ sơ, không cần thêm cột trong database."""
    try:
        weight = float(profile.WeightKg)
        height_m = float(profile.HeightCm) / 100.0
    except (TypeError, ValueError, OverflowError):
        return None
    if not (math.isfinite(weight) and math.isfinite(height_m)) or weight <= 0 or height_m <= 0:
        return None
    return round(weight / (height_m ** 2), 1)


@profile_bp.route('/save', methods=['POST'])
def save_profile():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or data.get('userId')
    if not user_id:
        return jsonify({"success": False, "message": "Thiếu user_id"}), 400

    profile, error = ProfileService.save_profile(user_id, data)
    if error:
        return jsonify({"success": False, "message": error}), 400
    if profile is None:
        return jsonify({"success": False, "message": "Không thể lưu hồ sơ."}), 500

    return jsonify({
        "success": True,
        "message": "Lưu hồ sơ thành công!",
        "data": {
            "bmi": calculate_profile_bmi(profile),
            "bmr": profile.Bmr,
            "tdee": profile.Tdee,
            "target_kcal": profile.TargetKcal,
            "target_water_ml": profile.TargetWaterMl,
        },
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
            "bmi": calculate_profile_bmi(profile),
            "activity_level": profile.ActivityLevel,
            "goal": profile.Goal,
            "bmr": profile.Bmr,
            "tdee": profile.Tdee,
            "target_kcal": profile.TargetKcal,
            "target_water_ml": profile.TargetWaterMl,
        },
    }), 200
