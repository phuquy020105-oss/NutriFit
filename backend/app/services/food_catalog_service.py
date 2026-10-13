"""One database source for recipes and food intake; estimates keep provenance."""
import math
from copy import deepcopy
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.services.nutrition_service import NutritionService
from app.services.module_errors import ModuleError

# Actual-intake bounds are unchanged; expose them for legacy snapshot editing.
ACTUAL_INTAKE_GRAMS = {"min": 1, "max": 2000}


def usable(dish):
    values = [dish.get("calories_per_100g"), *(dish.get("macros_per_100g", {}).get(k)
               for k in ("carbs", "protein", "fat"))]
    fiber = dish.get("macros_per_100g", {}).get("fiber")
    if fiber is not None:
        values.append(fiber)
    portions = [dish.get(k) for k in ("min_grams", "reference_grams", "max_grams")]
    return (all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in values)
            and all(type(v) in (int, float) and math.isfinite(v) for v in portions)
            and 1 <= portions[0] <= portions[1] <= portions[2] <= 2000)


def catalog_dishes(meal_type=None):
    dishes = [dish for dish in FoodCatalogRepository.dishes() if usable(dish)]
    if meal_type is not None:
        dishes = [dish for dish in dishes if meal_type in dish["meal_types"]
                  and dish["preparation_state"] != "raw"]
    return dishes


def catalog_by_id():
    return {dish["dish_id"]: dish for dish in catalog_dishes()}


def component(identifier, grams, role=None, actual=False, catalog=None):
    item = (catalog if catalog is not None else catalog_by_id()).get(identifier) if isinstance(identifier, str) else None
    if item is None:
        raise ModuleError("Món chưa có trong kho dinh dưỡng đang hoạt động.", "UNKNOWN_DISH")
    if role is not None and role != item["type"]:
        raise ModuleError("Món thay thế không cùng nhóm thành phần.", "INVALID_COMPONENT")
    grams = round(NutritionService.number(grams, "grams", ACTUAL_INTAKE_GRAMS["min"] if actual else item["min_grams"],
                                          ACTUAL_INTAKE_GRAMS["max"] if actual else item["max_grams"]), 2)
    # Unknown fiber stays explicit; numeric fiber is only the known lower bound.
    macros = {k: round((v or 0) * grams / 100, 4) for k, v in item["macros_per_100g"].items()}
    return {"type": item["type"], "dish_id": identifier, "name": item["name"], "grams": round(grams, 2),
            "calories": round(item["calories_per_100g"] * grams / 100, 4), "macros": macros,
            "nutrition_per_100g": {"calories": item["calories_per_100g"], **item["macros_per_100g"]},
            "fiber_complete": item["macros_per_100g"].get("fiber") is not None,
            "estimated": item["estimated"], "provenance": deepcopy(item["provenance"]),
            "catalog_data_version": item.get("data_version", 1),
            "portion_limits": {"min": item["min_grams"], "max": item["max_grams"]}}


def snapshot_component(previous, grams):
    """Editing an existing intake scales its frozen nutrition, not today's catalog."""
    grams = round(NutritionService.number(grams, "grams", 1, 2000), 2)
    result = deepcopy(previous)
    baseline = previous.get("nutrition_per_100g") or {
        "calories": previous["calories"] / previous["grams"] * 100,
        **{k: value / previous["grams"] * 100 for k, value in previous["macros"].items()}}
    result.update(grams=round(grams, 2), calories=round(baseline["calories"] * grams / 100, 4),
                  macros={k: round((baseline[k] or 0) * grams / 100, 4) for k in ("carbs", "protein", "fat", "fiber")},
                  nutrition_per_100g=baseline)
    return result


def totals(parts):
    return {key: round(sum(part["calories"] if key == "calories" else part["macros"][key] for part in parts), 1)
            for key in ("calories", "carbs", "protein", "fat", "fiber")}


def templates(meal_type):
    if meal_type not in ("breakfast", "lunch", "dinner"):
        raise ValueError("Unknown meal type")
    return FoodCatalogRepository.templates(meal_type)


def fallback_templates(meal_type, day, variant=0):
    day_index = (day.toordinal() + variant) % 7
    return [item for item in templates(meal_type) if item["day"] == day_index]


def materialize(template, target_kcal, source="fallback", reason=None):
    # Compatibility for the old API: templates are now seeded database records.
    scale = min(2.0, max(0.5, target_kcal / template["calories"]))
    components = {kind: f"{name} (~{round(grams * scale)} g)"
                  for kind, (name, grams) in template["components"].items()}
    labels = template.get("ingredient_labels", {})
    for kind, (name, recipe) in template.get("component_recipes", {}).items():
        detail = ", ".join(f"{labels[food]} ~{round(grams * scale)} g" for food, grams in recipe.items() if food != "water")
        components[kind] = f"{name}: {detail} (tổng ~{round(sum(recipe.values()) * scale)} g)"
    macros = {key: round(value * scale, 1) for key, value in template["macros"].items()}
    calories = round(4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"], 1)
    note = reason or ("Khẩu phần bữa sáng ước tính từ nguyên liệu tham khảo." if template["template_id"].startswith("breakfast")
                      else "Ưu tiên món hấp/luộc, ít dầu." if template["template_id"].startswith("dinner")
                      else "Mâm cơm đa dạng thành phần.")
    return {"title": template["title"], "calories": calories, "macros": macros,
            "components": components, "digestibility": f"[{source}] {note}"[:255]}


def recipe_catalog_compatible(recipe, catalog=None):
    """Historical snapshots stay readable, but retired/revised foods cannot be selected anew."""
    if not recipe:
        return True  # Legacy totals have no live dish-ID dependency.
    available = catalog if catalog is not None else catalog_by_id()
    from app.services.meal_preferences import violates
    preferences = recipe.get("preferences", {})
    if recipe.get("version") == 4:
        preferences = {key: value for key, value in preferences.items() if key not in ("preferEasy", "maxPrepMinutes")}
    for part in recipe.get("components", []):
        dish = available.get(part.get("dish_id"))
        if dish is None or violates(dish, preferences):
            return False
        if part.get("catalog_data_version", 1) != dish.get("data_version", 1):
            return False
    return bool(recipe.get("components"))
