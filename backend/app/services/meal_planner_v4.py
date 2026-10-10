"""Catalog composition and single-component replacement; core targets stay intact."""
import copy
import json
import re
from flask import current_app
from sqlalchemy import text
from app.extensions import db
from app.ai.gemini_client import AIUnavailable
from app.data.food_catalog import DISHES, CATALOG, component, totals
from app.repositories.meal_repository import MealRepository
from app.repositories.nutrition_v4_repository import NutritionV4Repository
from app.services.meal_service import MealService
from app.services import meal_service as core_meals
from app.services.meal_preferences import validate_preferences, violates
from app.services.module_errors import ModuleError


def focus_for(value, goal):
    if value is None or value == "":
        value = "lose" if str(goal).lower() in ("lose", "weight_loss", "giam_can") else "gain" if str(goal).lower() in ("gain", "weight_gain", "tang_can") else "maintain"
    if value not in ("lose", "maintain", "gain", "muscle_gain"):
        raise ModuleError("planningFocus phải là lose, maintain, gain hoặc muscle_gain.")
    return value


def score(item, focus, preferences):
    m = item["macros_per_100g"]
    kcal = item["calories_per_100g"]
    density = m["protein"] / max(kcal, 1) * 100
    base = {"lose": density + m["fiber"] * 2 - m["fat"] * 0.7,
            "maintain": m["fiber"] + density * 0.3 - abs(m["fat"] - 3) * 0.2,
            "gain": kcal * 0.08 + m["carbs"] * 0.2,
            "muscle_gain": density * 2 + m["protein"] * 0.4}[focus]
    tags = set(item["ingredients"])
    base += 100 * len(tags & set(preferences.get("prefer", [])))
    base -= 100 * len(tags & set(preferences.get("dislikes", [])))
    if preferences.get("preferEasy"):
        base -= item["prep_minutes"] * 3
    return round(base, 4)


def eligible(preferences):
    return [d for d in DISHES if not violates(d, preferences)]


def safe_text(value, maximum):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum or any(c in value for c in "<>\r\n") or any(ord(c) < 32 for c in value):
        raise AIUnavailable("invalid_output")
    return value.strip()


def option_from_recipe(recipe, title, reason, source):
    recipe["provider_source"] = source
    values = totals(recipe["components"])
    return {"title": title, "calories": values["calories"],
            "macros": {k: values[k] for k in ("carbs", "protein", "fat", "fiber")},
            "components": {c["type"]: f'{c["name"]} (~{c["grams"]} g)' for c in recipe["components"]},
            "digestibility": f"[{source}] {reason}", "recipe": recipe}


def today():
    return core_meals.today()


class MealPlannerV4:
    @staticmethod
    def validate_composition(data, candidates, meal_type, target, focus, preferences):
        if not isinstance(data, dict) or set(data) != {"choices"} or not isinstance(data["choices"], list) or len(data["choices"]) != 3:
            raise AIUnavailable("invalid_output")
        allowed = {d["dish_id"] for d in candidates}
        result, seen = [], set()
        for choice in data["choices"]:
            if not isinstance(choice, dict) or set(choice) != {"title", "reason", "components"}:
                raise AIUnavailable("invalid_output")
            title, reason = safe_text(choice["title"], 140), safe_text(choice["reason"], 220)
            if not isinstance(choice["components"], list) or not 1 <= len(choice["components"]) <= 6:
                raise AIUnavailable("invalid_output")
            parts, roles = [], set()
            for raw in choice["components"]:
                if not isinstance(raw, dict) or set(raw) != {"type", "dish_id", "grams"} or not isinstance(raw["type"], str) or not isinstance(raw["dish_id"], str) or raw["dish_id"] not in allowed:
                    raise AIUnavailable("invalid_output")
                try:
                    part = component(raw["dish_id"], raw["grams"], raw["type"])
                except (ModuleError, ValueError):
                    raise AIUnavailable("invalid_output") from None
                if part["type"] in roles:
                    raise AIUnavailable("invalid_output")
                roles.add(part["type"])
                parts.append(part)
            required = {"MAIN"} if meal_type == "breakfast" else {"CARB", "PROTEIN", "VEGGIE"}
            if not required <= roles or (meal_type != "breakfast" and "MAIN" in roles):
                raise AIUnavailable("invalid_output")
            signature = tuple(sorted(c["dish_id"] for c in parts))
            if signature in seen or not target * 0.65 <= totals(parts)["calories"] <= target * 1.35:
                raise AIUnavailable("invalid_output")
            seen.add(signature)
            result.append(option_from_recipe({"version": 4, "change": 0, "focus": focus,
                "preferences": preferences, "components": parts}, title, reason, "gemini"))
        return result

    @staticmethod
    def fallback(candidates, meal_type, target, focus, preferences, variant=0):
        groups = {}
        for d in candidates:
            groups.setdefault(d["type"], []).append(d)
        for items in groups.values():
            items.sort(key=lambda d: (-score(d, focus, preferences), d["dish_id"]))
        roles = ["MAIN"] if meal_type == "breakfast" else ["CARB", "PROTEIN", "VEGGIE"]
        primary = "MAIN" if meal_type == "breakfast" else "PROTEIN"
        if any(not groups.get(role) for role in roles) or len(groups[primary]) < 3:
            raise ModuleError("Catalog không đủ ba lựa chọn cân bằng thỏa điều kiện tránh món.", "INSUFFICIENT_MENUS", 422)
        result = []
        for i in range(3):
            selected = [groups[r][(i + variant) % len(groups[r])] if r == primary else groups[r][i % len(groups[r])] for r in roles]
            if meal_type == "breakfast" and groups.get("DESSERT"):
                selected.append(groups["DESSERT"][i % len(groups["DESSERT"])])
            base = sum(d["calories_per_100g"] * d["reference_grams"] / 100 for d in selected)
            scale = min(2, max(0.5, target / base))
            parts = [component(d["dish_id"], round(min(d["max_grams"], max(d["min_grams"], d["reference_grams"] * scale)), 2)) for d in selected]
            recipe = {"version": 4, "change": 0, "focus": focus, "preferences": preferences, "components": parts}
            note = {"lose": "Ưu tiên đạm, chất xơ và món ít dầu.", "maintain": "Kết hợp các nhóm món cân bằng.",
                "gain": "Ưu tiên món có mật độ năng lượng phù hợp.", "muscle_gain": "Ưu tiên nguồn đạm; năng lượng ngày vẫn theo hồ sơ."}[focus]
            result.append(option_from_recipe(recipe, "Kết hợp: " + ", ".join(d["name"] for d in selected[:3]), note, "fallback"))
        return result

    @staticmethod
    def generate(user_id, meal_type, force=False, expected=None, preferences=None, focus=None, target_override=None):
        NutritionV4Repository.require_schema()
        preferences = validate_preferences(preferences, meal_type)
        nutrition = MealService.profile(user_id)
        focus = focus_for(focus, nutrition["goal"])
        existing = MealRepository.load(user_id, today(), meal_type)
        if existing and not force:
            if any(not o.get("recipe") for o in existing["options"]):
                raise ModuleError("Bộ V3 vẫn được giữ. Chọn Nghĩ sau nếu đã chốt, rồi Đổi thực đơn để tạo bộ V4.", "V4_REFRESH_REQUIRED", 409)
            if any(o["recipe"]["preferences"] != preferences or o["recipe"]["focus"] != focus for o in existing["options"]):
                raise ModuleError("Điều kiện mới cần Đổi thực đơn với revision hiện tại.", "PREFERENCES_REQUIRE_REFRESH", 409)
            return existing, {"cached": True, "plannerVersion": "v4"}
        if existing and (existing["status"] == "decided" or existing["selectedOption"] is not None):
            raise ModuleError("Chọn Nghĩ sau trước khi đổi bộ đã chốt.", "MEAL_DECIDED", 409)
        if (existing and expected != existing["revision"]) or (not existing and expected is not None):
            raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
        from app.services.food_intake_service import FoodIntakeService
        budget = FoodIntakeService.daily(user_id, today())
        target = target_override if target_override is not None else budget["suggested_meal_targets"].get(meal_type, nutrition["meal_targets"][meal_type])
        candidates = eligible(preferences)
        variant = max((o["optionId"] for o in existing["options"]), default=0) if existing else 0
        fallback = MealPlannerV4.fallback(candidates, meal_type, target, focus, preferences, variant)
        MealRepository.release_read_transaction()
        meta = {"cached": False, "plannerVersion": "v4", "source": "gemini", "target_kcal": target,
                "planningFocus": focus, "budget": budget, "estimated": True}
        try:
            from app.services.nutrition_service import NutritionService
            remaining = budget["remaining"]["calories"]
            macro_target = {k: round(max(0, budget["remaining"][k]) * target / remaining, 1) for k in ("carbs", "protein", "fat")} if remaining > 0 else NutritionService.macro_targets(target)
            raw = current_app.extensions["nutrifit_gemini"].compose(candidates, meal_type, target, user_id, focus, macro_target)
            options = MealPlannerV4.validate_composition(raw, candidates, meal_type, target, focus, preferences)
        except AIUnavailable as error:
            options = fallback
            meta.update(source="fallback", fallback_reason=str(error), provider_http_status=error.http_status)
        MealService.validate_options(options)
        result, cached = MealRepository.store(user_id, today(), meal_type, options, expected, force)
        if cached and any(not o.get("recipe") or o["recipe"]["preferences"] != preferences or o["recipe"]["focus"] != focus for o in result["options"]):
            raise ModuleError("Request khác đã lưu một bộ khác. Hãy tải lại trước khi đổi.", "PREFERENCES_REQUIRE_REFRESH", 409)
        meta.update(cached=cached, source=result["source"])
        return result, meta

    @staticmethod
    def selected_component(user_id, meal_type, option_id, kind, expected):
        NutritionV4Repository.require_schema()
        meal = MealRepository.load(user_id, today(), meal_type)
        if not meal:
            raise ModuleError("Chưa có thực đơn.", "MEAL_NOT_FOUND", 404)
        if meal["revision"] != expected:
            raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
        if meal["status"] == "decided" or meal["selectedOption"] is not None:
            raise ModuleError("Chọn Nghĩ sau trước khi đổi món trong bộ đã chốt.", "MEAL_DECIDED", 409)
        option = next((o for o in meal["options"] if o["optionId"] == option_id), None)
        if option is None:
            raise ModuleError("Option không thuộc thực đơn của bạn.", "OPTION_NOT_FOUND", 404)
        if not option.get("recipe"):
            raise ModuleError("Thực đơn V3 chỉ có tổng dinh dưỡng; không thể tách chính xác từng món. Hãy tạo bộ V4.", "LEGACY_COMPONENT_NUTRITION_REQUIRED", 409)
        part = next((c for c in option["recipe"]["components"] if c["type"] == kind), None)
        if part is None:
            raise ModuleError("Không tìm thấy thành phần.", "COMPONENT_NOT_FOUND", 404)
        return meal, option, part

    @staticmethod
    def alternatives(user_id, meal_type, option_id, kind, expected):
        meal, option, part = MealPlannerV4.selected_component(user_id, meal_type, option_id, kind, expected)
        recipe = option["recipe"]
        candidates = [d for d in eligible(recipe["preferences"]) if d["type"] == kind and d["dish_id"] != part["dish_id"]]
        if not candidates:
            raise ModuleError("Chưa có món khác cùng nhóm phù hợp điều kiện tránh món.", "NO_REPLACEMENT", 422)
        candidates.sort(key=lambda d: (-score(d, recipe["focus"], recipe["preferences"]), d["dish_id"]))
        source, reason = "gemini", None
        MealRepository.release_read_transaction()
        try:
            if len(candidates) < 3:
                raise AIUnavailable("limited_catalog")
            raw = current_app.extensions["nutrifit_gemini"].alternatives(candidates, user_id, recipe["focus"])
            if not isinstance(raw, dict) or set(raw) != {"choices"} or not isinstance(raw["choices"], list) or len(raw["choices"]) != 3:
                raise AIUnavailable("invalid_output")
            index, seen, choices = {d["dish_id"]: d for d in candidates}, set(), []
            for c in raw["choices"]:
                if not isinstance(c, dict) or set(c) != {"dish_id", "reason"} or not isinstance(c["dish_id"], str) or c["dish_id"] not in index or c["dish_id"] in seen:
                    raise AIUnavailable("invalid_output")
                seen.add(c["dish_id"])
                choices.append({**index[c["dish_id"]], "reason": safe_text(c["reason"], 220)})
        except AIUnavailable as error:
            source, reason = "fallback", str(error)
            choices = [{**d, "reason": "Món cùng nhóm, thỏa điều kiện tránh món đã lưu."} for d in candidates[:3]]
        return {"choices": choices, "revision": meal["revision"], "source": source, "fallback_reason": reason}

    @staticmethod
    def replace_component(user_id, meal_type, option_id, kind, expected, dish_id, grams):
        NutritionV4Repository.require_schema()
        MealRepository.release_read_transaction()
        MealRepository.lock_user(user_id)
        meal, option, old = MealPlannerV4.selected_component(user_id, meal_type, option_id, kind, expected)
        recipe = copy.deepcopy(option["recipe"])
        replacement = component(dish_id, grams, kind)
        if violates(CATALOG[dish_id], recipe["preferences"]):
            raise ModuleError("Món thay thế vi phạm điều kiện tránh món/thời gian.", "AVOID_CONFLICT", 422)
        if old["dish_id"] == dish_id and old["grams"] == replacement["grams"]:
            raise ModuleError("Bạn chưa thay đổi món hoặc khẩu phần.", "NO_CHANGE")
        recipe["components"] = [replacement if c["type"] == kind else c for c in recipe["components"]]
        recipe["change"] += 1
        title = "Kết hợp: " + ", ".join(c["name"] for c in recipe["components"][:3])
        updated = option_from_recipe(recipe, title, "Đã thay một thành phần; tổng dinh dưỡng tính lại từ catalog.", option_source(option))
        db.session.execute(text("UPDATE MealComponentDish SET DishName=:name WHERE OptionId=:oid AND ComponentType=:kind"),
            {"name": updated["components"][kind], "oid": option_id, "kind": kind})
        db.session.execute(text("UPDATE MealNutrition SET TotalCalories=:cal,CarbsGrams=:carbs,ProteinGrams=:protein,FatGrams=:fat,FiberGrams=:fiber WHERE OptionId=:oid"),
            {"cal": updated["calories"], **updated["macros"], "oid": option_id})
        db.session.execute(text("UPDATE NutritionMealDetails SET RecipeJson=:recipe,Version=Version+1 WHERE OptionId=:oid"),
            {"recipe": json.dumps(recipe, ensure_ascii=False, allow_nan=False), "oid": option_id})
        db.session.execute(text("UPDATE MealOption SET Title=:title,DigestibilityNote=:note WHERE OptionId=:oid"),
            {"title": updated["title"], "note": updated["digestibility"], "oid": option_id})
        result = MealRepository.load(user_id, today(), meal_type)
        db.session.commit()
        return result


def option_source(option):
    # Keep provider provenance rather than claiming this arithmetic called AI.
    return "gemini" if option["recipe"].get("provider_source") == "gemini" else "fallback"
