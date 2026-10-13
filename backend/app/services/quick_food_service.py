"""Name search and confirmed consumption; no planner/provider operations."""
import unicodedata
from app.services.food_catalog_service import catalog_by_id, catalog_dishes, component, totals
from app.services.food_intake_service import FoodIntakeService
from app.services.module_errors import ModuleError
from app.services.nutrition_service import NutritionService
from app.services.premium_access import PremiumAccess


def normalized_name(value, strip_accents=False):
    value = " ".join(value.casefold().split())
    if strip_accents:
        value = "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c))
        value = value.replace("đ", "d")
    return unicodedata.normalize("NFC", value)


def allowed_fields(data, names):
    # Identity, when supplied, is checked against the session in the route.
    if set(data) - set(names) - {"userId", "user_id"}:
        raise ModuleError("Request có field không được hỗ trợ.")


class QuickFoodService:
    @staticmethod
    def preview_item(dish, grams=None):
        used_reference = grams is None
        part = component(dish["dish_id"], dish["reference_grams"] if used_reference else grams,
                         actual=True, catalog={dish["dish_id"]: dish})
        return {"dish_id": dish["dish_id"], "name": dish["name"],
                "reference_grams": dish["reference_grams"], "grams": part["grams"],
                "used_reference_grams": used_reference, "totals": totals([part]),
                "source": "database", "estimated": True, "fiber_complete": part["fiber_complete"]}

    @staticmethod
    def search(query, limit=10):
        if not isinstance(query, str):
            raise ModuleError("q phải là tên món.")
        query = " ".join(query.split())
        if not 1 <= len(query) <= 120:
            raise ModuleError("q cần 1–120 ký tự.")
        limit = NutritionService.number(limit, "limit", 1, 20, integer=True)
        exact, folded = normalized_name(query), normalized_name(query, True)
        if not folded:
            raise ModuleError("q phải là tên món.")
        matches = []
        for dish in catalog_dishes():
            name = normalized_name(dish["name"], True)
            if folded not in name:
                continue
            rank = (0 if normalized_name(dish["name"]) == exact else 1 if name == folded
                    else 2 if name.startswith(folded) else 3)
            matches.append((rank, name, dish["dish_id"], dish))
        if not matches:
            raise ModuleError("Không tìm thấy món phù hợp trong kho món đang hoạt động.", "FOOD_NOT_FOUND", 404)
        matches.sort(key=lambda row: row[:3])
        results = [{**QuickFoodService.preview_item(dish), "match": "exact" if rank < 2 else "partial"}
                   for rank, _, _, dish in matches[:limit]]
        return {"query": query, "total": len(matches), "returned": len(results),
                "requires_selection": True, "results": results}

    @staticmethod
    def selection(data):
        identifier = data.get("dish_id")
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 100 or identifier != identifier.strip():
            raise ModuleError("dish_id phải là ID món đã chọn từ kết quả tìm kiếm.")
        grams = data.get("grams")
        if grams is not None:
            grams = round(NutritionService.number(grams, "grams", 1, 2000), 2)
        return identifier, grams

    @staticmethod
    def preview(data):
        allowed_fields(data, ("dish_id", "grams"))
        identifier, grams = QuickFoodService.selection(data)
        dish = catalog_by_id().get(identifier)
        if dish is None:
            raise ModuleError("Món không tồn tại hoặc không còn hoạt động.", "FOOD_NOT_FOUND", 404)
        return QuickFoodService.preview_item(dish, grams)

    @staticmethod
    def confirm(user_id, data):
        allowed_fields(data, ("dish_id", "grams", "mealType", "consumedAt", "confirmed", "requestId"))
        if data.get("confirmed") is not True:
            raise ModuleError("Cần xác nhận đã thực sự ăn.", "CONFIRMATION_REQUIRED")
        identifier, grams = QuickFoodService.selection(data)
        meal = data.get("mealType", "snack")
        if meal not in ("breakfast", "lunch", "dinner", "snack"):
            raise ModuleError("mealType không hợp lệ.")
        # Hash the user's intent BEFORE resolving default grams or current nutrients.
        # A retry must retrieve its frozen snapshot even if the catalog has changed.
        payload = {"confirmed": True, "mealType": meal, "requestId": data.get("requestId"),
                   "consumedAt": data.get("consumedAt"), "workflow": "premium_quick_food",
                   "items": [{"dish_id": identifier, "grams": grams}]}

        def build_snapshot():
            # Repository has released the read snapshot and locked this user.
            PremiumAccess.require(user_id)
            preview = QuickFoodService.preview({"dish_id": identifier, "grams": grams})
            resolved = {**payload, "items": [{"dish_id": identifier, "grams": preview["grams"]}]}
            return FoodIntakeService.snapshot(user_id, resolved)

        return FoodIntakeService.create(user_id, payload, snapshot_factory=build_snapshot)
