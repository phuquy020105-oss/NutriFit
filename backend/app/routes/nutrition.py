from flask import Blueprint, jsonify, session
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
