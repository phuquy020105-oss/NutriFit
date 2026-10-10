"""BMI and macro additions; Quy's ProfileService owns BMR/TDEE and targets."""
import math
from app.services.profile_service import ProfileService


class NutritionValidationError(ValueError):
    pass


class NutritionService:
    MACRO_RATIOS = {"carbs": 0.45, "protein": 0.25, "fat": 0.30}
    MEAL_RATIOS = {"breakfast": 0.25, "lunch": 0.40, "dinner": 0.30, "snack": 0.05}

    @staticmethod
    def number(value, name, low, high, integer=False):
        if isinstance(value, bool):
            raise NutritionValidationError(f"{name} phải là số.")
        try:
            result = float(value)
        except (TypeError, ValueError, OverflowError):
            raise NutritionValidationError(f"{name} phải là số.") from None
        if not math.isfinite(result) or not low <= result <= high:
            raise NutritionValidationError(f"{name} phải trong khoảng {low}–{high}.")
        if integer and not result.is_integer():
            raise NutritionValidationError(f"{name} phải là số nguyên.")
        return int(result) if integer else result

    @classmethod
    def normalize(cls, data, defaults=False):
        if not isinstance(data, dict):
            raise NutritionValidationError("Dữ liệu phải là JSON object.")
        fallback = {"gender": "male", "age": 25, "height": 170, "weight": 65,
                    "activity_level": 1.375, "goal": "maintain"}
        values = {}
        for key in fallback:
            alias = "activity" if key == "activity_level" else key
            if key in data and alias != key and alias in data and data[key] != data[alias]:
                raise NutritionValidationError("activity và activity_level không khớp.")
            if key in data:
                values[key] = data[key]
            elif alias in data:
                values[key] = data[alias]
            elif defaults:
                values[key] = fallback[key]
            else:
                raise NutritionValidationError(f"Thiếu {key}.")
        if not isinstance(values["gender"], str) or values["gender"].lower() not in ("male", "female"):
            raise NutritionValidationError("gender không hợp lệ.")
        if not isinstance(values["goal"], str):
            raise NutritionValidationError("goal phải là chuỗi.")
        values["age"] = cls.number(values["age"], "age", 12, 95, integer=True)
        values["height"] = cls.number(values["height"], "height", 100, 250)
        values["weight"] = cls.number(values["weight"], "weight", 30, 250)
        raw = values["activity_level"]
        if isinstance(raw, str) and raw.upper() in ProfileService.ACTIVITY_MULTIPLIERS:
            activity = ProfileService.ACTIVITY_MULTIPLIERS[raw.upper()]
        else:
            try:
                activity = float(raw)
            except (ValueError, TypeError):
                activity = 1.375  # Same fallback as core save_profile.
        activity = cls.number(activity, "activity_level", 0.1, 10)
        values["activity_level"] = activity
        return values

    @classmethod
    def macro_targets(cls, target_kcal):
        kcal = cls.number(target_kcal, "target_kcal", 0.1, 20000)
        return {name: round(kcal * share / (9 if name == "fat" else 4), 1)
                for name, share in cls.MACRO_RATIOS.items()}

    @classmethod
    def calculate(cls, data, defaults=False):
        values = cls.normalize(data, defaults=defaults)
        bmr, tdee, target, water = ProfileService.calculate_metrics(
            values["gender"], values["age"], values["height"], values["weight"],
            values["activity_level"], values["goal"])
        return cls.enrich(values, bmr, tdee, target, water)

    @classmethod
    def enrich(cls, values, bmr, tdee, target, water):
        weight = cls.number(values["weight"], "weight", 0.1, 1000)
        height = cls.number(values["height"], "height", 0.1, 1000)
        for name, value in (("bmr", bmr), ("tdee", tdee), ("target_water_ml", water)):
            cls.number(value, name, 0.1, 100000)
        macros = cls.macro_targets(target)
        return {**values, "bmi": round(weight / (height / 100) ** 2, 1),
                "bmr": bmr, "tdee": tdee, "target_kcal": target,
                "target_water_ml": water, "macros": macros,
                "target_carbs": macros["carbs"], "target_protein": macros["protein"],
                "target_fat": macros["fat"], "target_fiber": round(weight * 0.45, 1),
                "meal_targets": {meal: round(target * ratio, 1) for meal, ratio in cls.MEAL_RATIOS.items()},
                "calculation_version": "nutrifit-v2-quy-core", "estimated": True}

    @classmethod
    def from_profile(cls, profile):
        values = {"gender": profile.Gender, "age": profile.Age,
                  "height": profile.HeightCm, "weight": profile.WeightKg,
                  "activity_level": profile.ActivityLevel, "goal": profile.Goal}
        return cls.enrich(values, profile.Bmr, profile.Tdee, profile.TargetKcal, profile.TargetWaterMl)
