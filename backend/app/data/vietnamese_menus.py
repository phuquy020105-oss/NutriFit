"""Seven-day Vietnamese menu cycle, three alternatives per lunch/dinner.

Nutrition is a product estimate, not a laboratory food composition database.
Portions and estimated totals are explicit and remain usable without Gemini.
"""
from copy import deepcopy

COMPONENT_FIELDS = {"CARB": "carb", "PROTEIN": "protein", "SOUP": "soup",
                    "VEGGIE": "veggie", "DESSERT": "dessert"}

LUNCH_PROTEINS = (
    ("Thịt heo nạc kho tiêu", "Cá thu kho cà chua", "Gà kho gừng"),
    ("Bò xào hành tây", "Cá hồi áp chảo", "Gà luộc bỏ da"),
    ("Thịt heo nạc rim sả", "Cá basa kho nghệ", "Gà kho nấm"),
    ("Bò xào bông cải", "Tôm hấp sả", "Gà nướng lá chanh"),
    ("Thịt heo nạc luộc", "Cá rô phi hấp gừng", "Gà xào ớt chuông"),
    ("Bò kho cà rốt", "Cá lóc kho tiêu", "Gà hấp hành"),
    ("Thịt heo nạc kho trứng", "Cá diêu hồng sốt cà", "Gà kho sả"),
)
DINNER_PROTEINS = (
    ("Thịt heo nạc hấp gừng", "Cá lóc hấp hành", "Gà luộc bỏ da"),
    ("Bò luộc cuốn rau", "Tôm hấp", "Gà hấp nấm"),
    ("Thịt heo nạc luộc", "Cá diêu hồng hấp", "Gà hấp lá chanh"),
    ("Bò áp chảo ít dầu", "Cá thu hấp gừng", "Gà luộc gừng"),
    ("Thịt heo nạc hấp nấm", "Cá hồi hấp", "Gà hấp hành"),
    ("Bò hầm rau củ", "Cá basa hấp sả", "Gà luộc bỏ da"),
    ("Thịt heo nạc luộc sả", "Cá rô phi hấp", "Gà hấp gừng"),
)
SOUPS = ("Canh bí xanh", "Canh rau ngót", "Canh cải xanh", "Canh bầu",
         "Canh mồng tơi", "Canh nấm", "Canh bí đỏ")
VEGETABLES = ("Rau muống luộc", "Bông cải hấp", "Cải thìa luộc", "Đậu que luộc",
              "Cải ngọt hấp", "Rau dền luộc", "Su su luộc")
FRUITS = ("Thanh long", "Đu đủ", "Cam", "Chuối", "Ổi", "Dưa hấu", "Táo")


def templates(meal_type):
    proteins = LUNCH_PROTEINS if meal_type == "lunch" else DINNER_PROTEINS
    result = []
    for day in range(7):
        for option in range(3):
            # Totals come from the reference template, never from AI-generated numbers.
            carbs, protein, fat = ((78, 38, 20), (75, 40, 19), (80, 37, 18))[option]
            if meal_type == "dinner":
                carbs, protein, fat = carbs * 0.75, protein * 0.85, fat * 0.70
            result.append({"template_id": f"{meal_type}-d{day + 1}-o{option + 1}",
                           "day": day, "family": ("pork_beef", "fish_seafood", "poultry")[option],
                           "title": f"Mâm cơm {'trưa' if meal_type == 'lunch' else 'tối'}: {proteins[day][option]}",
                           "components": {"CARB": ("Cơm gạo lứt" if option == 1 else "Cơm gạo trắng", 180),
                                          "PROTEIN": (proteins[day][option], 130),
                                          "SOUP": (SOUPS[day], 200), "VEGGIE": (VEGETABLES[day], 150),
                                          "DESSERT": (FRUITS[day], 100)},
                           "macros": {"carbs": carbs, "protein": protein, "fat": fat, "fiber": 7.0},
                           "calories": round(4 * carbs + 4 * protein + 9 * fat, 1)})
    return result


def fallback_templates(meal_type, day, variant=0):
    day_index = (day.toordinal() + variant) % 7
    return [deepcopy(item) for item in templates(meal_type) if item["day"] == day_index]


def materialize(template, target_kcal, source="fallback", reason=None):
    # A capped portion multiplier avoids silently suggesting unbounded servings.
    scale = min(2.0, max(0.5, target_kcal / template["calories"]))
    components = {kind: f"{name} (~{round(grams * scale)} g)"
                  for kind, (name, grams) in template["components"].items()}
    macros = {key: round(value * scale, 1) for key, value in template["macros"].items()}
    calories = round(4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"], 1)
    note = reason or ("Ưu tiên món hấp/luộc, ít dầu." if template["template_id"].startswith("dinner")
                      else "Mâm cơm đa dạng thành phần.")
    # Persist provenance inside an existing text column, without a schema migration.
    return {"title": template["title"], "calories": calories, "macros": macros,
            "components": components, "digestibility": f"[{source}] {note}"[:255]}
