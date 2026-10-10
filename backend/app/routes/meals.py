from flask import Blueprint, jsonify, request
from app.module_auth import login_required, check_user_identity
from app.repositories.meal_repository import MealRepository
from app.services.meal_service import MealService, today
from app.services.module_errors import api_errors, json_object, positive_id, ModuleError
from app.services.nutrition_service import NutritionService
from app.services.meal_preferences import replacement_request

meals_bp = Blueprint("meals", __name__, url_prefix="/api/meals")


def field(data, camel, snake):
    if camel in data and snake in data and data[camel] != data[snake]:
        raise ModuleError(f"{camel} và {snake} không khớp.")
    return data[camel] if camel in data else data.get(snake)


@meals_bp.get("/today")
@api_errors
@login_required
def today_meals():
    meals = MealService.get_today(check_user_identity())
    return jsonify(success=True, todayMeals=meals, date=today().isoformat())


@meals_bp.post("/generate")
@api_errors
@login_required
def generate():
    data = json_object()
    user_id = check_user_identity(data)
    meal_type = MealService.meal_type(field(data, "mealType", "meal_type"))
    # Old clients may send an empty key, but real credentials belong on the server.
    if data.get("apiKey") or data.get("api_key"):
        raise ModuleError("Gemini key phải được cấu hình ở backend.", "SERVER_KEY_REQUIRED")
    force = field(data, "forceRefresh", "force_refresh")
    if force is None:
        force = False
    if type(force) is not bool:
        raise ModuleError("forceRefresh phải là boolean.")
    result, meta = MealService.generate(user_id, meal_type, force, data.get("revision"), data.get("preferences"))
    return jsonify(success=True, data=result, meta=meta)


@meals_bp.post("/replace")
@api_errors
@login_required
def replace():
    data = json_object()
    user_id = check_user_identity(data)
    meal_type = MealService.meal_type(field(data, "mealType", "meal_type"))
    if data.get("apiKey") or data.get("api_key"):
        raise ModuleError("Gemini key phải được cấu hình ở backend.", "SERVER_KEY_REQUIRED")
    expected = data.get("revision")
    if not isinstance(expected, str) or len(expected) != 24:
        raise ModuleError("Cần revision hiện tại để đổi món.")
    if MealRepository.load(user_id, today(), meal_type) is None:
        raise ModuleError("Hãy tạo thực đơn trước khi đổi món.", "MEAL_NOT_FOUND", 404)
    preferences, target = replacement_request(data.get("request"), data.get("preferences"), meal_type)
    result, meta = MealService.generate(user_id, meal_type, True, expected, preferences, target)
    meta["applied_preferences"] = preferences
    return jsonify(success=True, data=result, meta=meta)


@meals_bp.post("/select")
@api_errors
@login_required
def select_option():
    data = json_object()
    user_id = check_user_identity(data)
    meal_type = MealService.meal_type(field(data, "mealType", "meal_type"))
    if "selectedOption" not in data and "selected_option" not in data:
        raise ModuleError("Thiếu selectedOption; dùng null để Nghĩ sau.")
    selected = field(data, "selectedOption", "selected_option")
    if selected is not None:
        selected = NutritionService.number(selected, "selectedOption", 1, 3, integer=True)
    expected = data.get("revision")
    if not isinstance(expected, str) or len(expected) != 24:
        raise ModuleError("Cần revision từ dữ liệu thực đơn vừa tải.")
    suggestion_id = field(data, "suggestionId", "suggestion_id")
    option_id = field(data, "optionId", "option_id")
    if suggestion_id is not None:
        suggestion_id = positive_id(suggestion_id, "suggestionId")
    if option_id is not None:
        option_id = positive_id(option_id, "optionId")
    result = MealRepository.choose(user_id, today(), meal_type, selected, expected, suggestion_id, option_id)
    return jsonify(success=True, data=result)


@meals_bp.get("/history")
@api_errors
@login_required
def history():
    user_id = check_user_identity()
    page = NutritionService.number(request.args.get("page", 1), "page", 1, 100000, integer=True)
    limit = NutritionService.number(request.args.get("limit", 20), "limit", 1, 100, integer=True)
    items, total = MealRepository.history(user_id, (page - 1) * limit, limit, today())
    return jsonify(success=True, history=items, pagination={"page": page, "limit": limit, "total": total})
