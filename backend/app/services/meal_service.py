"""Meal generation, seven-day fallback, selection and planned nutrition summary."""
import math
from datetime import datetime
from flask import current_app
from app.models.health import UserProfile
from app.data.vietnamese_menus import templates, fallback_templates, materialize, COMPONENT_FIELDS
from app.ai.gemini_client import AIUnavailable
from app.repositories.meal_repository import MealRepository
from app.services.nutrition_service import NutritionService, NutritionValidationError
from app.services.module_errors import ModuleError


def today():
    # Fixed UTC+7 default is usable on Windows without downloading tzdata.
    from datetime import timezone, timedelta
    name = current_app.config["NUTRIFIT_TIMEZONE"]
    if name in ("Asia/Ho_Chi_Minh", "Asia/Bangkok"):
        zone = timezone(timedelta(hours=7))
    elif name == "UTC":
        zone = timezone.utc
    else:
        raise ModuleError("Múi giờ ứng dụng chưa được hỗ trợ.", "INVALID_TIMEZONE", 503)
    return datetime.now(zone).date()


class MealService:
    @staticmethod
    def meal_type(value):
        if not isinstance(value, str) or value not in ("lunch", "dinner"):
            raise ModuleError("mealType phải là lunch hoặc dinner.")
        return value

    @staticmethod
    def profile(user_id):
        profile = UserProfile.query.filter_by(UserId=user_id).first()
        if profile is None:
            raise ModuleError("Hãy hoàn thành hồ sơ trước khi nhận mục tiêu dinh dưỡng.", "PROFILE_REQUIRED", 404)
        try:
            return NutritionService.from_profile(profile)
        except NutritionValidationError:
            raise ModuleError("Chỉ số hồ sơ chưa đầy đủ hoặc không hợp lệ; hãy cập nhật hồ sơ.",
                              "PROFILE_INCOMPLETE", 400) from None

    @staticmethod
    def validate_options(options):
        if not isinstance(options, list) or len(options) != 3:
            raise ModuleError("Bộ thực đơn phải có đúng 3 lựa chọn.", "INVALID_MENU", 503)
        for option in options:
            if set(option.get("components", {})) != set(COMPONENT_FIELDS):
                raise ModuleError("Thực đơn thiếu thành phần.", "INVALID_MENU", 503)
            strings = [option.get("title"), option.get("digestibility"), *option["components"].values()]
            if any(not isinstance(value, str) or not 1 <= len(value) <= 255 or "<" in value or ">" in value
                   for value in strings):
                raise ModuleError("Nội dung thực đơn không hợp lệ.", "INVALID_MENU", 503)
            numbers = [option.get("calories"), *option.get("macros", {}).values()]
            if set(option.get("macros", {})) != {"carbs", "protein", "fat", "fiber"} or any(
                    type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in numbers):
                raise ModuleError("Dinh dưỡng thực đơn không hợp lệ.", "INVALID_MENU", 503)
            if option["calories"] <= 0:
                raise ModuleError("Calorie thực đơn phải lớn hơn 0.", "INVALID_MENU", 503)
        return options

    @staticmethod
    def get_today(user_id):
        day = today()
        return {meal: MealRepository.load(user_id, day, meal) for meal in ("lunch", "dinner")}

    @staticmethod
    def generate(user_id, meal_type, force_refresh=False, expected_revision=None):
        day = today()
        existing = MealRepository.load(user_id, day, meal_type)
        if existing and not force_refresh:
            return existing, {"cached": True}
        if existing and (existing["status"] == "decided" or existing["selectedOption"] is not None):
            raise ModuleError("Thực đơn đã chốt được giữ nguyên; hãy chọn Nghĩ sau trước khi làm mới.", "MEAL_DECIDED", 409)
        if existing and force_refresh and expected_revision != existing["revision"]:
            raise ModuleError("Cần revision hiện tại để làm mới thực đơn.", "STALE_MEAL", 409)
        if not existing and expected_revision is not None:
            raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
        nutrition = MealService.profile(user_id)
        target = nutrition["meal_targets"][meal_type]
        # A refresh advances the local cycle. The revision checks stop stale writes.
        variant = max((option["optionId"] for option in existing["options"]), default=0) if existing else 0
        old_title = existing["options"][0]["title"] if existing and existing["options"] else None
        fallback = fallback_templates(meal_type, day, variant)
        if old_title == fallback[0]["title"]:
            fallback = fallback_templates(meal_type, day, variant + 1)
        candidates = templates(meal_type)
        if existing and force_refresh:
            old_titles = {option["title"] for option in existing["options"]}
            candidates = [template for template in candidates if template["title"] not in old_titles]
        MealRepository.release_read_transaction()  # No DB transaction while waiting for Gemini.
        meta = {"cached": False, "source": "fallback", "target_kcal": target}
        try:
            choices = current_app.extensions["nutrifit_gemini"].rank(candidates, meal_type, target, user_id)
            options = [materialize(template, target, "gemini", reason) for template, reason in choices]
            meta["source"] = "gemini"
        except AIUnavailable as error:
            options = [materialize(template, target) for template in fallback]
            meta["fallback_reason"] = str(error)
        MealService.validate_options(options)
        result, cached = MealRepository.store(user_id, day, meal_type, options,
                                              existing["revision"] if existing else None, force_refresh)
        meta["cached"] = cached
        meta["source"] = result["source"]
        if cached:
            meta = {"cached": True, "source": result["source"]}
        return result, meta

    @staticmethod
    def summary(user_id):
        target = MealService.profile(user_id)
        meals = MealService.get_today(user_id)
        totals = {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "fiber": 0.0}
        count = 0
        for meal in meals.values():
            if not meal or meal["status"] != "decided":
                continue
            selected = next((option for option in meal["options"] if option["id"] == meal["selectedOption"]), None)
            if selected:
                count += 1
                totals["calories"] += selected["calories"]
                for key in ("carbs", "protein", "fat", "fiber"):
                    totals[key] += selected["macros"][key]
        totals = {key: round(value, 1) for key, value in totals.items()}
        return {"date": today().isoformat(), "targets": target, "planned": totals,
                "selected_meals": count, "remaining_planned_kcal": round(target["target_kcal"] - totals["calories"], 1),
                "tracking_mode": "planned", "estimated": True}
