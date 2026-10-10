"""Small cooked-food catalog. Rounded teaching estimates, not lab measurements."""
from app.data.breakfast_menus import FOODS
from app.services.nutrition_service import NutritionService
from app.services.module_errors import ModuleError

NUTRIENTS = {**FOODS, "fish": (0, 22, 5, 0), "seafood": (0, 24, 0.3, 0)}
NOTE = "Ước tính NutriFit từ khẩu phần nguyên liệu chín; không phải số liệu xét nghiệm."


def dish(identifier, name, role, recipe, tags, minutes):
    weight = sum(recipe.values())
    totals = [sum(NUTRIENTS[food][i] * grams / 100 for food, grams in recipe.items()) for i in range(4)]
    per100 = dict(zip(("carbs", "protein", "fat", "fiber"), [round(v / weight * 100, 4) for v in totals]))
    return {"dish_id": identifier, "name": name, "type": role, "group": role.lower(),
            "reference_grams": weight, "min_grams": round(weight * 0.5), "max_grams": min(1000, round(weight * 2)),
            "macros_per_100g": per100, "calories_per_100g": round(4 * per100["carbs"] + 4 * per100["protein"] + 9 * per100["fat"], 4),
            "ingredients": tags, "prep_minutes": minutes, "provenance": NOTE, "estimated": True}


DISHES = (
    dish("rice", "Cơm trắng", "CARB", {"rice": 180}, ["rice"], 15),
    dish("sweet_potato", "Khoai lang hấp", "CARB", {"sweet_potato": 230}, ["sweet_potato"], 20),
    dish("rice_noodles", "Bún chín", "CARB", {"noodles": 200}, ["rice", "noodles"], 10),
    dish("chicken", "Ức gà hấp", "PROTEIN", {"chicken": 130}, ["chicken"], 20),
    dish("chicken_oil", "Gà áp chảo ít dầu", "PROTEIN", {"chicken": 130, "oil": 5}, ["chicken"], 20),
    dish("beef", "Bò áp chảo", "PROTEIN", {"beef": 130, "oil": 4}, ["beef"], 20),
    dish("pork", "Heo nạc hấp", "PROTEIN", {"pork": 130}, ["pork"], 20),
    dish("fish", "Cá hấp", "PROTEIN", {"fish": 150}, ["fish", "seafood"], 20),
    dish("shrimp", "Tôm hấp", "PROTEIN", {"seafood": 150}, ["seafood"], 15),
    dish("tofu", "Đậu phụ hấp", "PROTEIN", {"tofu": 180}, ["soy"], 10),
    dish("eggs", "Trứng luộc", "PROTEIN", {"egg": 100}, ["egg"], 10),
    dish("vegetables", "Rau luộc", "VEGGIE", {"vegetables": 150}, ["vegetables"], 10),
    dish("vegetables_oil", "Rau xào ít dầu", "VEGGIE", {"vegetables": 150, "oil": 5}, ["vegetables"], 15),
    dish("tofu_vegetables", "Rau hấp với đậu phụ", "VEGGIE", {"vegetables": 100, "tofu": 80}, ["soy", "vegetables"], 15),
    dish("soup", "Canh rau", "SOUP", {"vegetables": 80, "water": 200}, ["vegetables"], 15),
    dish("chicken_soup", "Canh rau thịt gà", "SOUP", {"chicken": 40, "vegetables": 80, "water": 200}, ["chicken", "vegetables"], 20),
    dish("banana", "Chuối", "DESSERT", {"banana": 100}, ["banana"], 5),
    dish("yogurt", "Sữa chua không đường", "DESSERT", {"yogurt": 150}, ["milk"], 5),
    dish("bread_egg", "Bánh mì trứng", "MAIN", {"bread": 80, "egg": 100, "vegetables": 30, "oil": 3}, ["wheat", "egg", "vegetables"], 10),
    dish("bread_chicken", "Bánh mì gà", "MAIN", {"bread": 90, "chicken": 80, "vegetables": 50}, ["wheat", "chicken", "vegetables"], 10),
    dish("oats_yogurt", "Yến mạch sữa chua", "MAIN", {"oats": 60, "yogurt": 150}, ["oats", "milk"], 5),
    dish("oats_tofu", "Yến mạch đậu phụ", "MAIN", {"oats": 60, "tofu": 120, "water": 100}, ["oats", "soy"], 15),
    dish("pho_chicken", "Phở gà", "MAIN", {"noodles": 220, "chicken": 90, "vegetables": 60, "water": 250}, ["rice", "noodles", "chicken"], 25),
    dish("pho_beef", "Phở bò", "MAIN", {"noodles": 200, "beef": 80, "vegetables": 50, "water": 250}, ["rice", "noodles", "beef"], 30),
)
CATALOG = {d["dish_id"]: d for d in DISHES}


def component(identifier, grams, role=None, actual=False):
    item = CATALOG.get(identifier) if isinstance(identifier, str) else None
    if item is None:
        raise ModuleError("Món không có trong catalog dinh dưỡng.", "UNKNOWN_DISH")
    if role is not None and role != item["type"]:
        raise ModuleError("Món thay thế không cùng nhóm thành phần.", "INVALID_COMPONENT")
    grams = NutritionService.number(grams, "grams", 1 if actual else item["min_grams"], 2000 if actual else item["max_grams"])
    macros = {k: round(v * grams / 100, 4) for k, v in item["macros_per_100g"].items()}
    return {"type": item["type"], "dish_id": identifier, "name": item["name"], "grams": round(grams, 2),
            "calories": round(4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"], 4),
            "macros": macros, "estimated": True, "provenance": item["provenance"]}


def totals(parts):
    return {key: round(sum(part["calories"] if key == "calories" else part["macros"][key] for part in parts), 1)
            for key in ("calories", "carbs", "protein", "fat", "fiber")}
