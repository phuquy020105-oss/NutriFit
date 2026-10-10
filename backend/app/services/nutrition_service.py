"""Nutrition rules shared by Profile and Meal. No database or AI dependency."""
import math


class NutritionValidationError(ValueError):
    pass


class NutritionService:
    ACTIVITY_LEVELS = (1.2, 1.375, 1.55, 1.725, 1.9)
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
        for key, allowed in (("gender", ("male", "female")), ("goal", ("lose", "maintain", "gain"))):
            value = values[key]
            if not isinstance(value, str) or value.strip().lower() not in allowed:
                raise NutritionValidationError(f"{key} không hợp lệ.")
            values[key] = value.strip().lower()
        values["age"] = cls.number(values["age"], "age", 12, 95, integer=True)
        values["height"] = cls.number(values["height"], "height", 100, 250)
        values["weight"] = cls.number(values["weight"], "weight", 30, 250)
        activity = cls.number(values["activity_level"], "activity_level", 1.2, 1.9)
        if activity not in cls.ACTIVITY_LEVELS:
            raise NutritionValidationError("activity_level không thuộc các mức hỗ trợ.")
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
        weight, height, age = values["weight"], values["height"], values["age"]
        bmr = 10 * weight + 6.25 * height - 5 * age + (5 if values["gender"] == "male" else -161)
        tdee = bmr * values["activity_level"]
        target = tdee + {"lose": -500, "maintain": 0, "gain": 500}[values["goal"]]
        if target <= 0:
            raise NutritionValidationError("Mục tiêu calorie phải lớn hơn 0; hãy kiểm tra hồ sơ.")
        target = round(target, 1)
        macros = cls.macro_targets(target)
        return {**values, "bmi": round(weight / (height / 100) ** 2, 1),
                "bmr": round(bmr, 1), "tdee": round(tdee, 1), "target_kcal": target,
                "target_water_ml": int(weight * 35), "macros": macros,
                "target_carbs": macros["carbs"], "target_protein": macros["protein"],
                "target_fat": macros["fat"], "target_fiber": round(weight * 0.45, 1),
                "meal_targets": {meal: round(target * ratio, 1) for meal, ratio in cls.MEAL_RATIOS.items()},
                "calculation_version": "nutrifit-v1", "estimated": True}

    @classmethod
    def from_profile(cls, profile):
        return cls.calculate({"gender": profile.Gender, "age": profile.Age,
                              "height": profile.HeightCm, "weight": profile.WeightKg,
                              "activity_level": profile.ActivityLevel, "goal": profile.Goal})
