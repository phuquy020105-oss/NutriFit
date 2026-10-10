from flask import Blueprint, jsonify, session, request
from app.module_auth import login_required, check_user_identity
from app.services.module_errors import api_errors, json_object
from app.services.nutrition_service import NutritionService
from app.services.meal_service import MealService

nutrition_bp = Blueprint("nutrition", __name__, url_prefix="/api/nutrition")


@nutrition_bp.post("/calculate")
@api_errors
def calculate():
    """Stateless calculator; no account/profile writes and no provider calls."""
    return jsonify(success=True, data=NutritionService.calculate(json_object()))


@nutrition_bp.get("/me")
@api_errors
@login_required
def my_nutrition():
    return jsonify(success=True, data=MealService.profile(check_user_identity()))


@nutrition_bp.get("/summary")
@api_errors
@login_required
def summary():
    return jsonify(success=True, data=MealService.summary(check_user_identity()))


@nutrition_bp.post("/logout")
@api_errors
@login_required
def logout():
    session.clear()
    return jsonify(success=True)


@nutrition_bp.get("/catalog")
@api_errors
@login_required
def food_catalog():
    from app.data.food_catalog import DISHES
    check_user_identity()
    return jsonify(success=True, data=DISHES, estimated=True)


@nutrition_bp.get("/daily")
@api_errors
@login_required
def daily_intake():
    from app.services.food_intake_service import FoodIntakeService, parse_day
    uid = check_user_identity()
    return jsonify(success=True, data=FoodIntakeService.daily(uid, parse_day(request.args.get("date"))))


@nutrition_bp.post("/intake")
@api_errors
@login_required
def add_intake():
    from app.services.food_intake_service import FoodIntakeService
    data = json_object()
    result, created = FoodIntakeService.create(check_user_identity(data), data)
    return jsonify(success=True, data=result, created=created), 201 if created else 200


@nutrition_bp.post("/intake/<int:intake_id>/update")
@api_errors
@login_required
def update_intake(intake_id):
    from app.services.food_intake_service import FoodIntakeService
    data = json_object()
    return jsonify(success=True, data=FoodIntakeService.edit(check_user_identity(data), intake_id, data))


@nutrition_bp.post("/intake/<int:intake_id>/delete")
@api_errors
@login_required
def delete_intake(intake_id):
    from app.services.food_intake_service import FoodIntakeService
    data = json_object()
    return jsonify(success=True, data=FoodIntakeService.edit(check_user_identity(data), intake_id, data, delete=True))
