"""Database-backed food data. Runtime never loads seed files or creates tables."""
import json
from sqlalchemy import inspect, text
from app.extensions import db
from app.services.module_errors import ModuleError


class FoodCatalogRepository:
    @staticmethod
    def require_schema(legacy=False):
        table = "NutritionLegacyMenus" if legacy else "NutritionFoodCatalog"
        if not inspect(db.session.connection()).has_table(table):
            raise ModuleError("Kho món ăn chưa sẵn sàng. Vui lòng thử lại sau.",
                              "FOOD_CATALOG_MIGRATION_REQUIRED", 503)

    @staticmethod
    def serialize(row):
        try:
            ingredients = json.loads(row["IngredientsJson"])
            meals = json.loads(row["MealTypesJson"])
            provenance = json.loads(row["ProvenanceJson"])
            if (not isinstance(ingredients, list) or any(not isinstance(t, str) for t in ingredients)
                    or not isinstance(meals, list) or not meals or any(m not in ("breakfast", "lunch", "dinner") for m in meals)
                    or not isinstance(provenance, dict)
                    or row["ComponentType"] not in ("MAIN", "CARB", "PROTEIN", "VEGGIE", "SOUP", "SIDE", "DRINK", "DESSERT")
                    or row["PreparationState"] not in ("raw", "raw_edible", "cooked", "ready")
                    or (row["PrepMinutes"] is not None and not 1 <= row["PrepMinutes"] <= 120)):
                raise ValueError()
            number = lambda key: None if row[key] is None else float(row[key])
            # Existing seeded recipes often lack FiberPer100G in MySQL. Estimate
            # it from documented ingredient masses at read time, without DB
            # writes and without falsely treating missing data as zero.
            fiber = number("FiberPer100G")
            if fiber is None:
                from app.services.fiber_estimates import estimate_fiber_per_100g
                fiber = estimate_fiber_per_100g(provenance)
                if fiber is not None:
                    provenance = dict(provenance)
                    provenance["fiber_estimate"] = {
                        "method": "weighted_ingredient_grams",
                        "verified": False,
                        "source": "approximate_reference_values",
                    }
            return {"dish_id": row["DishId"], "name": row["NameVi"], "type": row["ComponentType"],
                    "group": row["ComponentType"].lower(), "preparation_state": row["PreparationState"],
                    "reference_grams": number("ReferenceGrams"), "min_grams": number("MinGrams"),
                    "max_grams": number("MaxGrams"), "calories_per_100g": number("KcalPer100G"),
                    "macros_per_100g": {**{k: number(column) for k, column in (
                        ("carbs", "CarbsPer100G"), ("protein", "ProteinPer100G"),
                        ("fat", "FatPer100G"))}, "fiber": fiber},
                    "ingredients": ingredients, "meal_types": meals, "prep_minutes": row["PrepMinutes"],
                    "provenance": provenance, "estimated": bool(row["Estimated"]),
                    "active": bool(row["IsActive"]), "data_version": row["DataVersion"]}
        except (ValueError, TypeError):
            raise ModuleError("Dữ liệu món ăn chưa hợp lệ.", "INVALID_CATALOG", 503) from None

    @staticmethod
    def dishes(active=True):
        FoodCatalogRepository.require_schema()
        query = "SELECT * FROM NutritionFoodCatalog"
        if active:
            query += " WHERE IsActive=1"
        rows = db.session.execute(text(query + " ORDER BY DishId")).mappings()
        return [FoodCatalogRepository.serialize(row) for row in rows]

    @staticmethod
    def templates(meal_type):
        FoodCatalogRepository.require_schema(legacy=True)
        rows = db.session.execute(text("SELECT TemplateJson FROM NutritionLegacyMenus "
            "WHERE MealType=:meal AND IsActive=1 ORDER BY DayIndex,TemplateId"), {"meal": meal_type}).scalars()
        try:
            return [json.loads(value) for value in rows]
        except (ValueError, TypeError):
            raise ModuleError("Dữ liệu thực đơn cũ chưa hợp lệ.", "INVALID_CATALOG", 503) from None

    @staticmethod
    def recent_dishes(user_id, meal_type, limit=6):
        # Existing snapshots provide variation without another tracking table.
        rows = db.session.execute(text("SELECT d.RecipeJson FROM NutritionMealDetails d "
            "JOIN MealOption o ON o.OptionId=d.OptionId JOIN MealSuggestions s ON s.SuggestionId=o.SuggestionId "
            "WHERE s.UserId=:uid AND s.MealType=:meal ORDER BY s.SuggestionDate DESC,o.OptionId DESC LIMIT :count"),
            {"uid": user_id, "meal": meal_type, "count": limit}).scalars()
        seen = set()
        for value in rows:
            try:
                seen.update(c["dish_id"] for c in json.loads(value).get("components", []))
            except (ValueError, TypeError, KeyError):
                continue
        return seen

    @staticmethod
    def insert_missing(dishes, menus):
        """Explicit seed/test entrypoint; no commit and no overwriting existing IDs."""
        FoodCatalogRepository.require_schema()
        FoodCatalogRepository.require_schema(legacy=True)
        inserted = {"dishes": 0, "menus": 0}
        for dish in dishes:
            if db.session.execute(text("SELECT 1 FROM NutritionFoodCatalog WHERE DishId=:id"),
                                  {"id": dish["dish_id"]}).scalar():
                continue
            macros = dish["macros_per_100g"]
            values = {"id": dish["dish_id"], "name": dish["name"], "type": dish["type"],
                "state": dish["preparation_state"], "ref": dish["reference_grams"], "min": dish["min_grams"],
                "max": dish["max_grams"], "kcal": dish["calories_per_100g"], **macros,
                "ingredients": json.dumps(dish["ingredients"], ensure_ascii=False),
                "meals": json.dumps(dish["meal_types"]), "minutes": dish.get("prep_minutes"),
                "provenance": json.dumps(dish["provenance"], ensure_ascii=False, allow_nan=False),
                "estimated": int(dish["estimated"]), "active": int(dish.get("active", True)),
                "version": dish.get("data_version", 1)}
            db.session.execute(text("INSERT INTO NutritionFoodCatalog (DishId,NameVi,ComponentType,PreparationState,"
                "ReferenceGrams,MinGrams,MaxGrams,KcalPer100G,ProteinPer100G,CarbsPer100G,FatPer100G,FiberPer100G,"
                "IngredientsJson,MealTypesJson,PrepMinutes,ProvenanceJson,Estimated,IsActive,DataVersion) VALUES "
                "(:id,:name,:type,:state,:ref,:min,:max,:kcal,:protein,:carbs,:fat,:fiber,"
                ":ingredients,:meals,:minutes,:provenance,:estimated,:active,:version)"), values)
            inserted["dishes"] += 1
        for menu in menus:
            if db.session.execute(text("SELECT 1 FROM NutritionLegacyMenus WHERE TemplateId=:id"),
                                  {"id": menu["template_id"]}).scalar():
                continue
            db.session.execute(text("INSERT INTO NutritionLegacyMenus(TemplateId,MealType,DayIndex,TemplateJson) "
                "VALUES (:id,:meal,:day,:data)"), {"id": menu["template_id"], "meal": menu["meal_type"],
                    "day": menu["day"], "data": json.dumps(menu, ensure_ascii=False, allow_nan=False)})
            inserted["menus"] += 1
        return inserted
