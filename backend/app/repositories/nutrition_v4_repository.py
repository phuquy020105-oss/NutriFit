"""Only additive V4 tables. Runtime never creates tables or runs migrations."""
import json
from sqlalchemy import inspect, text
from app.extensions import db
from app.repositories.meal_repository import MealRepository
from app.services.module_errors import ModuleError


class NutritionV4Repository:
    @staticmethod
    def available():
        inspector = inspect(db.session.connection())
        return all(inspector.has_table(t) for t in ("NutritionMealDetails", "NutritionFoodIntake"))

    @staticmethod
    def require_schema():
        if not NutritionV4Repository.available():
            raise ModuleError("V4 cần migration 001_nutrition_v4 đã được phê duyệt. V3 vẫn dùng được.", "V4_MIGRATION_REQUIRED", 503)

    @staticmethod
    def recipes(suggestion_id):
        if not inspect(db.session.connection()).has_table("NutritionMealDetails"):
            return {}
        rows = db.session.execute(text("SELECT d.OptionId,d.RecipeJson FROM NutritionMealDetails d "
            "JOIN MealOption o ON o.OptionId=d.OptionId WHERE o.SuggestionId=:sid"), {"sid": suggestion_id}).mappings()
        try:
            result = {r["OptionId"]: json.loads(r["RecipeJson"]) for r in rows}
            if any(not isinstance(v, dict) or v.get("version") != 4 or not isinstance(v.get("components"), list) for v in result.values()):
                raise ValueError()
            return result
        except (ValueError, TypeError):
            raise ModuleError("Chi tiết dinh dưỡng chưa hợp lệ.", "INVALID_RECIPE", 503) from None

    @staticmethod
    def save_recipe(option_id, recipe):
        NutritionV4Repository.require_schema()
        db.session.execute(text("INSERT INTO NutritionMealDetails(OptionId,RecipeJson) VALUES (:oid,:recipe)"),
            {"oid": option_id, "recipe": json.dumps(recipe, ensure_ascii=False, allow_nan=False)})

    @staticmethod
    def logs(user_id, day):
        NutritionV4Repository.require_schema()
        rows = db.session.execute(text("SELECT * FROM NutritionFoodIntake WHERE UserId=:uid "
            "AND IntakeDate=:day AND Deleted=0 ORDER BY OccurredAt,IntakeId"), {"uid": user_id, "day": day}).mappings()
        return [NutritionV4Repository.serialize(r) for r in rows]

    @staticmethod
    def serialize(row):
        snapshot = json.loads(row["SnapshotJson"])
        return {"id": row["IntakeId"], "version": row["Version"], "date": str(row["IntakeDate"]),
            "consumedAtUtc": str(row["OccurredAt"]), "mealType": row["MealType"], **snapshot}

    @staticmethod
    def row(user_id, intake_id):
        row = db.session.execute(text("SELECT * FROM NutritionFoodIntake WHERE UserId=:uid AND IntakeId=:id"),
            {"uid": user_id, "id": intake_id}).mappings().first()
        if row is None:
            raise ModuleError("Không tìm thấy nhật ký của bạn.", "INTAKE_NOT_FOUND", 404)
        return row

    @staticmethod
    def create(user_id, key, request_hash, values):
        NutritionV4Repository.require_schema()
        MealRepository.release_read_transaction()
        MealRepository.lock_user(user_id)
        row = db.session.execute(text("SELECT * FROM NutritionFoodIntake WHERE UserId=:uid AND RequestKey=:key"),
            {"uid": user_id, "key": key}).mappings().first()
        if row:
            if row["Deleted"]:
                raise ModuleError("Nhật ký này đã xóa; retry không tạo lại.", "INTAKE_DELETED", 409)
            if row["RequestHash"] != request_hash:
                raise ModuleError("requestId đã dùng với nội dung khác.", "IDEMPOTENCY_CONFLICT", 409)
            result = NutritionV4Repository.serialize(row)
            db.session.commit()
            return result, False
        values = values() if callable(values) else values
        result = db.session.execute(text("INSERT INTO NutritionFoodIntake "
            "(UserId,RequestKey,RequestHash,IntakeDate,OccurredAt,MealType,SnapshotJson) "
            "VALUES (:uid,:key,:hash,:day,:time,:meal,:snapshot)"),
            {"uid": user_id, "key": key, "hash": request_hash, **values})
        record = NutritionV4Repository.serialize(NutritionV4Repository.row(user_id, result.lastrowid))
        db.session.commit()
        return record, True

    @staticmethod
    def edit(user_id, intake_id, version, values=None):
        NutritionV4Repository.require_schema()
        MealRepository.release_read_transaction()
        MealRepository.lock_user(user_id)
        row = NutritionV4Repository.row(user_id, intake_id)
        if row["Deleted"] or row["Version"] != version:
            raise ModuleError("Nhật ký đã thay đổi. Hãy tải lại.", "STALE_INTAKE", 409)
        values = values(row) if callable(values) else values
        if values is None:
            db.session.execute(text("UPDATE NutritionFoodIntake SET Deleted=1,Version=Version+1, "
                "UpdatedAt=CURRENT_TIMESTAMP WHERE IntakeId=:id"), {"id": intake_id})
            db.session.commit()
            return {"id": intake_id, "deleted": True}
        db.session.execute(text("UPDATE NutritionFoodIntake SET IntakeDate=:day,OccurredAt=:time,MealType=:meal, "
            "SnapshotJson=:snapshot,Version=Version+1,UpdatedAt=CURRENT_TIMESTAMP WHERE IntakeId=:id"), {"id": intake_id, **values})
        result = NutritionV4Repository.serialize(NutritionV4Repository.row(user_id, intake_id))
        db.session.commit()
        return result
