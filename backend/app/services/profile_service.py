from app.extensions import db
from app.models.health import UserProfile

class ProfileService:
    @staticmethod
    def calculate_metrics(gender, age, height, weight, activity, goal):
        # Công thức tính Mifflin-St Jeor
        if gender.lower() == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        tdee = bmr * activity

        if goal == 'lose':
            target_kcal = tdee - 500
        elif goal == 'gain':
            target_kcal = tdee + 500
        else:
            target_kcal = tdee

        target_water = int(weight * 35)

        return round(bmr, 1), round(tdee, 1), round(target_kcal, 1), target_water

    @staticmethod
    def save_profile(user_id, data):
        gender = data.get('gender', 'male')
        age = int(data.get('age', 25))
        height = float(data.get('height', 170))
        weight = float(data.get('weight', 65))
        activity = float(data.get('activity_level', 1.375))
        goal = data.get('goal', 'maintain')

        bmr, tdee, target_kcal, target_water = ProfileService.calculate_metrics(
            gender, age, height, weight, activity, goal
        )

        profile = UserProfile.query.filter_by(UserId=user_id).first()
        if not profile:
            profile = UserProfile(UserId=user_id)
            db.session.add(profile)

        profile.Gender = gender
        profile.Age = age
        profile.HeightCm = height
        profile.WeightKg = weight
        profile.ActivityLevel = activity
        profile.Goal = goal
        profile.Bmr = bmr
        profile.Tdee = tdee
        profile.TargetKcal = target_kcal
        profile.TargetWaterMl = target_water

        db.session.commit()
        return profile