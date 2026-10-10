import math
import unittest
from app.services.nutrition_service import NutritionService, NutritionValidationError
from app.services.profile_service import ProfileService


class NutritionTests(unittest.TestCase):
    def setUp(self):
        self.profile = dict(gender="male", age=22, height=172, weight=65,
                            activity_level=1.375, goal="maintain")

    def test_known_male_profile(self):
        result = NutritionService.calculate(self.profile)
        self.assertEqual((result["bmr"], result["tdee"], result["target_kcal"], result["target_water_ml"]),
                         (1620.0, 2227.5, 2227.5, 2275))
        self.assertEqual(result["bmi"], 22.0)

    def test_female_formula(self):
        result = NutritionService.calculate({**self.profile, "gender": "female"})
        self.assertEqual(result["bmr"], 1454.0)

    def test_goals_preserve_quy_behavior(self):
        for goal, adjustment in (("lose", -500), ("maintain", 0), ("gain", 500)):
            with self.subTest(goal=goal):
                result = NutritionService.calculate({**self.profile, "goal": goal})
                self.assertEqual(result["target_kcal"], 2227.5 + adjustment)

    def test_legacy_profile_four_value_contract(self):
        self.assertEqual(ProfileService.calculate_metrics("male", 22, 172, 65, 1.375, "maintain"),
                         (1620.0, 2227.5, 2227.5, 2275))

    def test_macro_energy_and_daily_allocation(self):
        result = NutritionService.calculate(self.profile)
        macros = result["macros"]
        self.assertAlmostEqual(4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"],
                               result["target_kcal"], delta=1)
        self.assertAlmostEqual(sum(result["meal_targets"].values()), result["target_kcal"], delta=0.2)
        self.assertEqual(sum(NutritionService.MEAL_RATIOS.values()), 1)

    def test_numeric_strings_and_normalized_enums(self):
        result = NutritionService.calculate({**self.profile, "age": "22", "weight": "65", "gender": " MALE "})
        self.assertEqual(result["bmr"], 1620)

    def test_input_validation(self):
        for field, value in (("age", 22.5), ("age", True), ("height", 0), ("weight", math.nan),
                             ("weight", math.inf), ("weight", "invalid"), ("gender", "unknown"),
                             ("goal", "invalid"), ("activity_level", 1.4), ("height", {})):
            with self.subTest(field=field, value=str(value)):
                with self.assertRaises(NutritionValidationError):
                    NutritionService.calculate({**self.profile, field: value})

    def test_missing_fields_and_invalid_objects(self):
        for value in ([], None, {}, {"height": 172}):
            with self.assertRaises(NutritionValidationError):
                NutritionService.calculate(value)

    def test_nonpositive_calorie_target_rejected(self):
        with self.assertRaises(NutritionValidationError):
            NutritionService.calculate(dict(gender="female", age=95, height=100, weight=30,
                                            activity_level=1.2, goal="lose"))

    def test_profile_defaults_and_activity_alias(self):
        values = NutritionService.normalize({"activity": 1.55}, defaults=True)
        self.assertEqual(values["activity_level"], 1.55)
        with self.assertRaises(NutritionValidationError):
            NutritionService.normalize({"activity": 1.2, "activity_level": 1.55}, defaults=True)
