"""21 breakfast recipes with explicit reference portions and estimated nutrients.

These rounded ingredient profiles are teaching estimates per 100 g of edible
food (cooked except dry oats/bread). They are not certified food composition
records. Energy is derived consistently from carbs/protein/fat at 4/4/9.
Mixed dishes include the listed meat, vegetables and oil, not invented AI totals.
"""

# carbs, protein, fat, fiber per 100 g. Water/broth has no estimated energy.
FOODS = {
    "bread": (49, 9, 3.2, 2.7), "rice": (28.2, 2.7, 0.3, 0.4),
    "noodles": (25, 1.8, 0.2, 1), "oats": (67, 13, 7, 10),
    "egg": (0.7, 12.6, 10.6, 0), "chicken": (0, 31, 3.6, 0),
    "beef": (0, 26, 10, 0), "pork": (0, 27, 9, 0),
    "tofu": (1.9, 8, 4.8, 0.3), "milk": (5, 3.3, 3.2, 0),
    "yogurt": (4.7, 3.5, 3.3, 0), "banana": (23, 1.1, 0.3, 2.6),
    "sweet_potato": (20, 1.6, 0.1, 3), "vegetables": (5, 2, 0.2, 2),
    "oil": (0, 0, 100, 0), "water": (0, 0, 0, 0),
}
LABELS = {"bread": "bánh mì", "rice": "cơm", "noodles": "bánh phở/bún/miến",
          "oats": "yến mạch khô", "egg": "trứng", "chicken": "gà", "beef": "bò",
          "pork": "heo", "tofu": "đậu phụ", "milk": "sữa", "yogurt": "sữa chua",
          "banana": "chuối", "sweet_potato": "khoai lang", "vegetables": "rau",
          "oil": "dầu", "water": "nước dùng"}


def part(kind, name, **ingredients):
    return kind, name, ingredients


# Each day: quick, soup, balanced. The main dish recipe has explicit edible grams.
RECIPES = (
    (("Bánh mì trứng và chuối", 10, [part("MAIN", "Bánh mì trứng", bread=80, egg=100, vegetables=30, oil=3), part("SIDE", "Chuối", banana=100)]),
     ("Phở bò", 30, [part("MAIN", "Phở bò", noodles=200, beef=80, vegetables=50, water=250)]),
     ("Yến mạch sữa chua và chuối", 5, [part("MAIN", "Yến mạch với sữa chua", oats=60, yogurt=150), part("SIDE", "Chuối", banana=100)])),
    (("Xôi gà và rau", 20, [part("MAIN", "Xôi gà (ước tính theo cơm chín)", rice=220, chicken=80, oil=3), part("SIDE", "Rau ăn kèm", vegetables=80)]),
     ("Phở gà", 25, [part("MAIN", "Phở gà", noodles=220, chicken=90, vegetables=60, water=250)]),
     ("Khoai lang, trứng và sữa", 20, [part("MAIN", "Khoai lang hấp", sweet_potato=250), part("SIDE", "Trứng luộc", egg=100), part("DRINK", "Sữa không đường", milk=150)])),
    (("Bánh cuốn thịt và chuối", 25, [part("MAIN", "Bánh cuốn thịt (ước tính bánh gạo chín)", noodles=220, pork=70, vegetables=30, oil=5), part("SIDE", "Chuối", banana=80)]),
     ("Bún mọc", 30, [part("MAIN", "Bún mọc (thịt heo nạc)", noodles=220, pork=90, vegetables=60, water=250)]),
     ("Yến mạch trứng và rau", 12, [part("MAIN", "Cháo yến mạch trứng", oats=60, egg=100, water=180), part("SIDE", "Rau hấp", vegetables=100)])),
    (("Bánh mì gà và sữa chua", 10, [part("MAIN", "Bánh mì gà", bread=90, chicken=80, vegetables=50), part("SIDE", "Sữa chua không đường", yogurt=100)]),
     ("Miến gà", 25, [part("MAIN", "Miến gà (ước tính sợi chín)", noodles=230, chicken=90, vegetables=60, water=250)]),
     ("Khoai lang, đậu phụ và chuối", 20, [part("MAIN", "Khoai lang hấp", sweet_potato=230), part("SIDE", "Đậu phụ hấp", tofu=150), part("DESSERT", "Chuối", banana=80)])),
    (("Cơm trứng và rau", 12, [part("MAIN", "Cơm trứng", rice=180, egg=100, oil=3), part("SIDE", "Rau luộc", vegetables=100)]),
     ("Cháo gà", 30, [part("MAIN", "Cháo gà", rice=180, chicken=100, vegetables=60, water=300)]),
     ("Yến mạch sữa và trứng", 12, [part("MAIN", "Yến mạch sữa", oats=55, milk=200), part("SIDE", "Trứng luộc", egg=50)])),
    (("Bánh mì đậu phụ và chuối", 10, [part("MAIN", "Bánh mì đậu phụ", bread=90, tofu=150, vegetables=50), part("SIDE", "Chuối", banana=80)]),
     ("Bún bò rau cải", 30, [part("MAIN", "Bún bò rau cải", noodles=200, beef=90, vegetables=80, water=250)]),
     ("Khoai lang, sữa chua và trứng", 20, [part("MAIN", "Khoai lang hấp", sweet_potato=220), part("SIDE", "Trứng luộc", egg=100), part("DRINK", "Sữa chua không đường", yogurt=100)])),
    (("Xôi trứng và rau", 20, [part("MAIN", "Xôi trứng (ước tính theo cơm chín)", rice=200, egg=100, oil=3), part("SIDE", "Rau ăn kèm", vegetables=80)]),
     ("Cháo thịt heo", 30, [part("MAIN", "Cháo thịt heo", rice=180, pork=100, vegetables=60, water=300)]),
     ("Yến mạch chuối và đậu phụ", 10, [part("MAIN", "Yến mạch nấu nước", oats=65, water=180), part("SIDE", "Đậu phụ hấp", tofu=150), part("DESSERT", "Chuối", banana=100)])),
)


def breakfast_templates():
    result = []
    for day, recipes in enumerate(RECIPES):
        for option, (title, minutes, parts) in enumerate(recipes):
            totals = [0.0] * 4
            ingredients = set()
            components = {}
            component_recipes = {}
            for kind, name, recipe in parts:
                ingredients.update(recipe)
                detail = ", ".join(f"{LABELS[food]} {grams} g" for food, grams in recipe.items() if food != "water")
                components[kind] = (f"{name} ({detail})", sum(recipe.values()))
                component_recipes[kind] = (name, recipe)
                for food, grams in recipe.items():
                    for index, value in enumerate(FOODS[food]):
                        totals[index] += value * grams / 100
            macros = dict(zip(("carbs", "protein", "fat", "fiber"), [round(v, 1) for v in totals]))
            result.append({"template_id": f"breakfast-d{day + 1}-o{option + 1}", "day": day,
                           "family": ("quick", "soup", "balanced")[option], "title": title,
                           "components": components, "component_recipes": component_recipes,
                           "ingredients": sorted(ingredients - {"water"}),
                           "prep_minutes": minutes, "macros": macros,
                           "calories": round(4 * macros["carbs"] + 4 * macros["protein"] + 9 * macros["fat"], 1)})
    return result
