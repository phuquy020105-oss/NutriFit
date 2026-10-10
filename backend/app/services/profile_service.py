from app.extensions import db
from app.models.health import UserProfile
from app.services.nutrition_service import NutritionService

class ProfileService:
    @staticmethod
    def calculate_metrics(gender, age, height, weight, activity, goal):
        # Keep Quy's existing four-value contract; Nutrition owns the shared rules.
        result = NutritionService.calculate({"gender": gender, "age": age, "height": height,
                                             "weight": weight, "activity_level": activity, "goal": goal})
        return result['bmr'], result['tdee'], result['target_kcal'], result['target_water_ml']

    @staticmethod
    def save_profile(user_id, data):
        values = NutritionService.normalize(data, defaults=True)
        gender, age = values['gender'], values['age']
        height, weight = values['height'], values['weight']
        activity, goal = values['activity_level'], values['goal']

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
