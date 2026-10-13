"""Stable, safe errors for Nutrition/Meal and their integration points."""
from functools import wraps
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from app.extensions import db
from app.services.nutrition_service import NutritionValidationError


class ModuleError(Exception):
    def __init__(self, message, code="INVALID_INPUT", status=400):
        super().__init__(message)
        self.message, self.code, self.status = message, code, status


def json_object():
    if request.content_length and request.content_length > 65536:
        raise ModuleError("Body vượt giới hạn 64 KiB.", "PAYLOAD_TOO_LARGE", 413)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ModuleError("Body phải là JSON object hợp lệ.")
    return data


def positive_id(value, field="id"):
    from app.services.nutrition_service import NutritionService
    return NutritionService.number(value, field, 1, 2147483647, integer=True)


def api_errors(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except NutritionValidationError as error:
            db.session.rollback()
            return jsonify(success=False, code="INVALID_INPUT", message=str(error)), 400
        except ModuleError as error:
            db.session.rollback()
            return jsonify(success=False, code=error.code, message=error.message), error.status
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify(success=False, code="DATABASE_ERROR", message="Không thể xử lý dữ liệu lúc này."), 503
        except HTTPException as error:
            return jsonify(success=False, code="HTTP_ERROR", message=error.name), error.code
    return wrapped
