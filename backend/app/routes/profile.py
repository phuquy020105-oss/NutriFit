from flask import Blueprint, request, jsonify
from app.services.profile_service import ProfileService
from app.models.health import UserProfile
from app.security import login_required, get_current_user

# Đặt prefix chuẩn /api/profile
profile_bp = Blueprint('profile_bp', __name__, url_prefix='/api/profile')

@profile_bp.route('/me', methods=['GET'])
@login_required
def get_my_profile():
    # Lấy thông tin user an toàn từ Bearer Token
    current_user, _ = get_current_user()
    profile = UserProfile.query.filter_by(UserId=current_user.UserId).first()
    if not profile:
        return jsonify({"success": False, "message": "Chưa có dữ liệu hồ sơ"}), 404

    # Đọc trực tiếp từ DB - không tự tính đè số khác
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

@profile_bp.route('/save', methods=['POST', 'PUT'])
@login_required
def save_profile():
    # Lấy user từ token, không tin tưởng user_id do client tự gửi lên
    current_user, _ = get_current_user()
    data = request.get_json() or {}

    profile, error = ProfileService.save_profile(current_user.UserId, data)
    if error:
        return jsonify({"success": False, "message": error}), 400

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

# Giữ lại route cũ kèm theo bảo mật để tránh gãy code frontend cũ (nếu có)
@profile_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_profile_by_id(user_id):
    current_user, _ = get_current_user()
    # Chỉ cho phép xem nếu là chính mình hoặc là ADMIN
    if current_user.UserId != user_id and current_user.Role != 'ADMIN':
        return jsonify({"success": False, "message": "Không có quyền truy cập hồ sơ này!"}), 403

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