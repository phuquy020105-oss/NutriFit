"""Confirmed consumption snapshots, idempotent writes and daily remaining budget."""
import hashlib
import json
import re
from datetime import date, datetime, timezone, timedelta
from app.data.food_catalog import component, totals
from app.services.nutrition_service import NutritionService
from app.services.meal_service import MealService
from app.services import meal_service as core_meals
from app.services.module_errors import ModuleError, positive_id
from app.repositories.meal_repository import MealRepository
from app.repositories.nutrition_v4_repository import NutritionV4Repository

ZONE = timezone(timedelta(hours=7))


def parse_day(value):
    if value is None:
        return core_meals.today()
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ModuleError("date phải là YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ModuleError("Ngày không hợp lệ.") from None


class FoodIntakeService:
    @staticmethod
    def snapshot(user_id, data, previous=None):
        if data.get("confirmed") is not True:
            raise ModuleError("Cần xác nhận đã thực sự ăn.", "CONFIRMATION_REQUIRED")
        meal = data.get("mealType")
        if meal not in ("breakfast", "lunch", "dinner", "snack"):
            raise ModuleError("mealType không hợp lệ.")
        value = data.get("consumedAt")
        try:
            if value is None:
                when = datetime.now(timezone.utc)
            else:
                if not isinstance(value, str) or len(value) > 40:
                    raise ValueError()
                when = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if when.tzinfo is None:
                    raise ValueError()
        except (ValueError, TypeError):
            raise ModuleError("consumedAt phải là ISO datetime có múi giờ.") from None
        source = data.get("meal")
        if source is not None:
            if not isinstance(source, dict) or meal == "snack":
                raise ModuleError("Tham chiếu thực đơn không hợp lệ.")
            original = MealRepository.load(user_id, core_meals.today(), meal)
            if not original:
                raise ModuleError("Chưa có thực đơn của bạn.", "MEAL_NOT_FOUND", 404)
            if original["revision"] != source.get("revision"):
                raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
            option_id = positive_id(source.get("optionId"), "optionId")
            option = next((o for o in original["options"] if o["optionId"] == option_id), None)
            if option is None:
                raise ModuleError("Option không thuộc tài khoản của bạn.", "OPTION_NOT_FOUND", 404)
        else:
            option = None
        items = data.get("items")
        if items is not None:
            if not isinstance(items, list) or not 1 <= len(items) <= 20:
                raise ModuleError("items cần 1–20 món và gram thực tế.")
            parts = []
            for item in items:
                if not isinstance(item, dict) or set(item) != {"dish_id", "grams"}:
                    raise ModuleError("Mỗi món chỉ có dish_id và grams; dinh dưỡng do backend tính.")
                parts.append(component(item["dish_id"], item["grams"], actual=True))
            snapshot = {"items": parts, "totals": totals(parts), "source": "catalog", "estimated": True}
        elif option is not None and not option.get("recipe"):
            servings = NutritionService.number(data.get("servings"), "servings", 0.1, 4)
            values = {"calories": round(option["calories"] * servings, 1),
                **{k: round(v * servings, 1) for k, v in option["macros"].items()}}
            snapshot = {"items": [], "title": option["title"], "servings": servings, "totals": values,
                "source": "legacy_meal_total", "estimated": True,
                "note": "Tổng dinh dưỡng ước tính của nguyên bộ V3; không tách gram hoặc dinh dưỡng từng món."}
        elif previous and previous.get("source") == "legacy_meal_total":
            servings = NutritionService.number(data.get("servings"), "servings", 0.1, 4)
            factor = servings / previous["servings"]
            snapshot = {k: previous[k] for k in ("items", "title", "source", "estimated", "note")}
            snapshot.update(servings=servings, totals={k: round(v * factor, 1) for k, v in previous["totals"].items()})
        else:
            raise ModuleError("Cần món và gram thực tế từ catalog, hoặc số phần của nguyên bộ V3.")
        if option is not None:
            snapshot["meal_reference"] = {"optionId": option["optionId"], "revision": source["revision"]}
        return {"day": when.astimezone(ZONE).date(), "time": when.astimezone(timezone.utc).replace(tzinfo=None),
            "meal": meal, "snapshot": json.dumps(snapshot, ensure_ascii=False, allow_nan=False)}

    @staticmethod
    def create(user_id, data):
        NutritionV4Repository.require_schema()
        key = data.get("requestId")
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", key):
            raise ModuleError("requestId phải có 16–64 ký tự để chống ghi trùng.")
        # Identity fields have already been checked against the signed session.
        fingerprint = {k: v for k, v in data.items() if k not in ("requestId", "userId", "user_id")}
        try:
            request_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        except (ValueError, TypeError):
            raise ModuleError("Dữ liệu nhật ký không hợp lệ.") from None
        return NutritionV4Repository.create(user_id, key, request_hash, lambda: FoodIntakeService.snapshot(user_id, data))

    @staticmethod
    def edit(user_id, intake_id, data, delete=False):
        version = NutritionService.number(data.get("version"), "version", 1, 2147483647, integer=True)
        values = None if delete else lambda row: FoodIntakeService.snapshot(user_id, data, NutritionV4Repository.serialize(row))
        return NutritionV4Repository.edit(user_id, intake_id, version, values)

    @staticmethod
    def daily(user_id, day):
        nutrition = MealService.profile(user_id)
        logs = NutritionV4Repository.logs(user_id, day)
        keys = ("calories", "carbs", "protein", "fat", "fiber")
        consumed = {k: round(sum(r["totals"][k] for r in logs), 1) for k in keys}
        targets = {"calories": nutrition["target_kcal"], **nutrition["macros"], "fiber": nutrition["target_fiber"]}
        remaining = {k: round(targets[k] - consumed[k], 1) for k in keys}
        eaten = {r["mealType"] for r in logs}
        waiting = {m: ratio for m, ratio in NutritionService.MEAL_RATIOS.items() if m not in eaten}
        denominator = sum(waiting.values())
        # Do not recommend zero kcal or skipping meals after exceeding the target.
        suggested = {m: round(remaining["calories"] * ratio / denominator, 1) if remaining["calories"] > 0 else nutrition["meal_targets"][m]
                     for m, ratio in waiting.items()} if denominator else {}
        # Small positive remainder is also not a suitable full-meal recommendation.
        for meal in suggested:
            if meal != "snack" and suggested[meal] < 100:
                suggested[meal] = nutrition["meal_targets"][meal]
        return {"date": day.isoformat(), "targets": nutrition, "consumed": consumed, "remaining": remaining,
            "over_target": {k: round(max(0, -remaining[k]), 1) for k in keys}, "logs": logs,
            "consumed_meals": sorted(eaten), "suggested_meal_targets": suggested,
            "snack_reserve_kcal": suggested.get("snack", 0), "requires_confirmation": True,
            "note": "Gợi ý cập nhật, không tự đổi bộ đã chốt. Phần dư quá thấp hoặc vượt mục tiêu không dùng để khuyên bỏ bữa.",
            "tracking_mode": "consumed", "estimated": True}
