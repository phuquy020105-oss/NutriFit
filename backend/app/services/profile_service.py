from app.extensions import db
from app.models.health import UserProfile

class ProfileService:
    # Bảng ánh xạ mức độ hoạt động sang hệ số số thực (DOUBLE)
    ACTIVITY_MULTIPLIERS = {
        'SEDENTARY': 1.2,
        'LIGHT': 1.375,
        'MODERATE': 1.55,
        'VERY_ACTIVE': 1.725,
        'EXTRA_ACTIVE': 1.9
    }

    @staticmethod
    def calculate_nutrition_targets(gender, weight, height, age, activity_multiplier, goal):
        """
        Tính toán BMR, TDEE, TargetKcal và TargetWaterMl dựa trên activity_multiplier (float)
        """
        # 1. BMR (Mifflin-St Jeor)
        if gender and str(gender).upper() == 'MALE':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # 2. TDEE
        multiplier = float(activity_multiplier) if activity_multiplier else 1.2
        tdee = bmr * multiplier

        # 3. TargetKcal (±500 kcal theo mục tiêu)
        target_kcal = tdee
        goal_upper = str(goal or '').upper()
        if goal_upper in ['WEIGHT_LOSS', 'LOSE_WEIGHT', 'GIAM_CAN']:
            target_kcal = tdee - 500
        elif goal_upper in ['WEIGHT_GAIN', 'GAIN_WEIGHT', 'TANG_CAN']:
            target_kcal = tdee + 500

        # 4. TargetWaterMl (35ml / kg thể trọng)
        target_water_ml = round(weight * 35)

        return round(bmr, 1), round(tdee, 1), round(target_kcal, 1), target_water_ml

    @staticmethod
    def save_profile(user_id, data):
        profile = UserProfile.query.filter_by(UserId=user_id).first()
        if not profile:
            profile = UserProfile(UserId=user_id)
            db.session.add(profile)

        # Cập nhật thông tin cơ bản
        profile.Age = data.get('age', getattr(profile, 'Age', None))
        profile.Gender = data.get('gender', getattr(profile, 'Gender', None))
        profile.HeightCm = data.get('height', getattr(profile, 'HeightCm', None))
        profile.WeightKg = data.get('weight', getattr(profile, 'WeightKg', None))
        profile.Goal = data.get('goal', getattr(profile, 'Goal', None))

        # Chuẩn hóa ActivityLevel về kiểu số thực DOUBLE cho MySQL
        raw_activity = data.get('activity_level', getattr(profile, 'ActivityLevel', None))
        if isinstance(raw_activity, str) and raw_activity.upper() in ProfileService.ACTIVITY_MULTIPLIERS:
            activity_val = ProfileService.ACTIVITY_MULTIPLIERS[raw_activity.upper()]
        elif raw_activity is not None:
            try:
                activity_val = float(raw_activity)
            except (ValueError, TypeError):
                activity_val = 1.2
        else:
            activity_val = 1.2

        profile.ActivityLevel = activity_val

        # Tính toán và lưu ngay vào database để đảm bảo Single Source of Truth
        if profile.HeightCm and profile.WeightKg and profile.Age and profile.Gender:
            bmr, tdee, target_kcal, water_ml = ProfileService.calculate_nutrition_targets(
                profile.Gender,
                float(profile.WeightKg),
                float(profile.HeightCm),
                int(profile.Age),
                profile.ActivityLevel,
                profile.Goal
            )
            profile.Bmr = bmr
            profile.Tdee = tdee
            profile.TargetKcal = target_kcal
            profile.TargetWaterMl = water_ml

        try:
            db.session.commit()
            return profile, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi lưu hồ sơ: {str(e)}"

    # Alias để tương thích mọi nơi gọi
    update_profile = save_profile

    @staticmethod
    def get_profile(user_id):
        profile = UserProfile.query.filter_by(UserId=user_id).first()
        if not profile:
            return None, "Hồ sơ chưa được tạo!"
        return profile, None