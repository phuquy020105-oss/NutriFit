"""Read/write existing Meal tables. This module never creates or alters tables."""
import hashlib
import json
from datetime import date
from sqlalchemy import select, text
from app.extensions import db
from app.models.user import User
from app.data.vietnamese_menus import COMPONENT_FIELDS
from app.services.module_errors import ModuleError


def revision(options):
    content = [(o["optionId"], o["title"], o["calories"]) for o in options]
    if any(o.get("recipe") for o in options):
        content.append([(o["optionId"], o.get("recipe")) for o in options])
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode()).hexdigest()[:24]


class MealRepository:
    @staticmethod
    def release_read_transaction():
        # These endpoints only read core identity/profile before writing Meals.
        # Do not silently discard pending ORM edits from another caller.
        if db.session.new or db.session.dirty or db.session.deleted:
            raise ModuleError("Còn thay đổi chưa lưu trong transaction.", "TRANSACTION_CONFLICT", 409)
        db.session.rollback()

    @staticmethod
    def load(user_id, day, meal_type):
        row = db.session.execute(text(
            "SELECT SuggestionId, SuggestionDate, MealType, SelectedOption, Status "
            "FROM MealSuggestions WHERE UserId=:uid AND SuggestionDate=:day AND MealType=:meal"
        ), {"uid": user_id, "day": day, "meal": meal_type}).mappings().first()
        return MealRepository.serialize(row) if row else None

    @staticmethod
    def serialize(row):
        rows = db.session.execute(text(
            "SELECT o.OptionId, o.OptionNumber, o.Title, o.DigestibilityNote, "
            "n.TotalCalories, n.CarbsGrams, n.ProteinGrams, n.FatGrams, n.FiberGrams "
            "FROM MealOption o JOIN MealNutrition n ON n.OptionId=o.OptionId "
            "WHERE o.SuggestionId=:sid ORDER BY o.OptionNumber, o.OptionId"
        ), {"sid": row["SuggestionId"]}).mappings().all()
        component_rows = db.session.execute(text(
            "SELECT c.OptionId, c.ComponentType, c.DishName FROM MealComponentDish c "
            "JOIN MealOption o ON c.OptionId=o.OptionId WHERE o.SuggestionId=:sid "
            "ORDER BY c.ComponentId"
        ), {"sid": row["SuggestionId"]}).mappings().all()
        components = {}
        flexible_components = {}
        for component in component_rows:
            flexible_components.setdefault(component["OptionId"], []).append({
                "type": component["ComponentType"], "name": component["DishName"]})
            field = COMPONENT_FIELDS.get(component["ComponentType"])
            if field:
                components.setdefault(component["OptionId"], {})[field] = component["DishName"]
        options = []
        from app.repositories.nutrition_v4_repository import NutritionV4Repository
        recipes = NutritionV4Repository.recipes(row["SuggestionId"])
        sources = set()
        for option in rows:
            note = option["DigestibilityNote"] or ""
            source = "gemini" if note.startswith("[gemini]") else "fallback" if note.startswith("[fallback]") else "seed"
            sources.add(source)
            options.append({"id": option["OptionNumber"], "optionId": option["OptionId"],
                            "title": option["Title"], "calories": float(option["TotalCalories"]),
                            "macros": {"carbs": float(option["CarbsGrams"]),
                                       "protein": float(option["ProteinGrams"]),
                                       "fat": float(option["FatGrams"]), "fiber": float(option["FiberGrams"] or 0)},
                            **components.get(option["OptionId"], {}),
                            "components": flexible_components.get(option["OptionId"], []),
                            "reason": note.removeprefix(f"[{source}] "),
                            "digestibility": note.removeprefix(f"[{source}] "),
                            "nutritionNotes": "Dinh dưỡng ước tính cho khẩu phần hiển thị; lựa chọn là kế hoạch ăn.",
                            "estimated": True})
            if option["OptionId"] in recipes:
                recipe = recipes[option["OptionId"]]
                options[-1]["recipe"] = recipe
                options[-1]["plannerVersion"] = "v4"
                options[-1]["components"] = recipe["components"]
        day = row["SuggestionDate"]
        return {"suggestionId": row["SuggestionId"], "date": day.isoformat() if isinstance(day, date) else str(day),
                "mealType": row["MealType"], "selectedOption": row["SelectedOption"],
                "status": row["Status"], "options": options, "revision": revision(options),
                "source": next(iter(sources)) if len(sources) == 1 else "mixed", "estimated": True}

    @staticmethod
    def lock_user(user_id):
        # Lock the existing parent even on the first generation (no suggestion yet).
        if db.session.execute(select(User.UserId).where(User.UserId == user_id).with_for_update()).scalar() is None:
            raise ModuleError("Không tìm thấy tài khoản.", "USER_NOT_FOUND", 404)

    @staticmethod
    def store(user_id, day, meal_type, options, expected_revision, force_refresh):
        # Authentication reads may have opened a MySQL REPEATABLE READ snapshot.
        # Start fresh before the parent lock so all subsequent reads see the winner.
        MealRepository.release_read_transaction()
        MealRepository.lock_user(user_id)
        existing = MealRepository.load(user_id, day, meal_type)
        if existing and not force_refresh:
            db.session.commit()
            return existing, True
        if existing:
            if existing["status"] == "decided" or existing["selectedOption"] is not None:
                raise ModuleError("Thực đơn đã chốt được giữ nguyên; hãy chọn Nghĩ sau trước khi làm mới.", "MEAL_DECIDED", 409)
            if existing["revision"] != expected_revision:
                raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại trước khi làm mới.", "STALE_MEAL", 409)
            suggestion_id = existing["suggestionId"]
            db.session.execute(text("UPDATE MealSuggestions SET SelectedOption=NULL, Status='pending', "
                                    "UpdatedAt=CURRENT_TIMESTAMP WHERE SuggestionId=:sid"), {"sid": suggestion_id})
            option_ids = db.session.execute(text("SELECT OptionId FROM MealOption WHERE SuggestionId=:sid"),
                                            {"sid": suggestion_id}).scalars().all()
            for option_id in option_ids:
                db.session.execute(text("DELETE FROM MealComponentDish WHERE OptionId=:oid"), {"oid": option_id})
                db.session.execute(text("DELETE FROM MealNutrition WHERE OptionId=:oid"), {"oid": option_id})
            db.session.execute(text("DELETE FROM MealOption WHERE SuggestionId=:sid"), {"sid": suggestion_id})
        else:
            if expected_revision is not None:
                raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
            result = db.session.execute(text(
                "INSERT INTO MealSuggestions (UserId, SuggestionDate, MealType, Status) "
                "VALUES (:uid, :day, :meal, 'pending')"
            ), {"uid": user_id, "day": day, "meal": meal_type})
            suggestion_id = result.lastrowid
        for number, option in enumerate(options, 1):
            result = db.session.execute(text(
                "INSERT INTO MealOption (SuggestionId, OptionNumber, Title, DigestibilityNote) "
                "VALUES (:sid, :number, :title, :note)"
            ), {"sid": suggestion_id, "number": number, "title": option["title"], "note": option["digestibility"]})
            option_id = result.lastrowid
            macros = option["macros"]
            db.session.execute(text(
                "INSERT INTO MealNutrition (OptionId, TotalCalories, CarbsGrams, ProteinGrams, FatGrams, FiberGrams) "
                "VALUES (:oid, :cal, :carbs, :protein, :fat, :fiber)"
            ), {"oid": option_id, "cal": option["calories"], **macros})
            for kind, name in option["components"].items():
                db.session.execute(text(
                    "INSERT INTO MealComponentDish (OptionId, ComponentType, DishName) VALUES (:oid, :kind, :name)"
                ), {"oid": option_id, "kind": kind, "name": name})
            if option.get("recipe"):
                from app.repositories.nutrition_v4_repository import NutritionV4Repository
                NutritionV4Repository.save_recipe(option_id, option["recipe"])
        result = MealRepository.load(user_id, day, meal_type)
        db.session.commit()
        return result, False

    @staticmethod
    def choose(user_id, day, meal_type, selected, expected_revision, suggestion_id=None, option_id=None):
        MealRepository.release_read_transaction()
        MealRepository.lock_user(user_id)
        meal = MealRepository.load(user_id, day, meal_type)
        if meal is None:
            raise ModuleError("Chưa có gợi ý cho bữa này.", "MEAL_NOT_FOUND", 404)
        if meal["revision"] != expected_revision or (suggestion_id is not None and suggestion_id != meal["suggestionId"]):
            raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại trước khi chọn.", "STALE_MEAL", 409)
        option = next((item for item in meal["options"] if item["id"] == selected), None)
        if selected is not None and option is None:
            raise ModuleError("Lựa chọn không thuộc thực đơn này.")
        if option_id is not None and (option is None or option["optionId"] != option_id):
            raise ModuleError("Lựa chọn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
        status = "pending" if selected is None else "decided"
        db.session.execute(text("UPDATE MealSuggestions SET SelectedOption=:selected, Status=:status, "
                                "UpdatedAt=CURRENT_TIMESTAMP WHERE SuggestionId=:sid"),
                           {"selected": selected, "status": status, "sid": meal["suggestionId"]})
        result = MealRepository.load(user_id, day, meal_type)
        db.session.commit()
        return result

    @staticmethod
    def history(user_id, offset, limit, today):
        args = {"uid": user_id, "today": today, "offset": offset, "limit": limit}
        rows = db.session.execute(text(
            "SELECT SuggestionId, SuggestionDate, MealType, SelectedOption, Status "
            "FROM MealSuggestions WHERE UserId=:uid AND SuggestionDate<=:today "
            "ORDER BY SuggestionDate DESC, SuggestionId DESC LIMIT :limit OFFSET :offset"
        ), args).mappings().all()
        total = db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions "
                                        "WHERE UserId=:uid AND SuggestionDate<=:today"), args).scalar()
        result = []
        for row in rows:
            meal = MealRepository.serialize(row)
            meal["chosenMeal"] = next((option for option in meal["options"] if option["id"] == meal["selectedOption"]), None)
            result.append(meal)
        return result, total
