"""Conservative approximate dietary fiber (grams per 100g of prepared food).

For educational NutriFit recipes only, calculated from retained edible ingredient
weights. Missing, implausible, or unrecognized ingredient data returns None,
not 0.0. This does not certify ingredients for allergy avoidance.
"""
import math

FIBER_REFERENCE = {
    'rice': .4, 'brown_rice': 1.8, 'glutinous': .6, 'noodles': .7,
    'pho': .6, 'mien': .5, 'hu_tieu': .7, 'mi': 1.6, 'banh_canh': .6,
    'bread': 2.7, 'banh_trang': 1.4, 'flour': 2.0, 'corn': 2.4,
    'oat': 8.0, 'sweet_potato': 3.0, 'potato': 1.8, 'taro': 3.6, 'cassava': 1.8,
    'pork': 0, 'belly': 0, 'ribs': 0, 'beef': 0, 'chicken': 0, 'duck': 0,
    'frog': 0, 'eel': 0, 'fish': 0, 'catfish': 0, 'tuna': 0, 'salmon': 0,
    'shrimp': 0, 'squid': 0, 'crab': 0, 'clam': 0, 'oyster': 0,
    'egg': 0, 'snail': 0, 'jellyfish': 0, 'scallop': 0,
    'tofu': .3, 'mung': 5.0, 'peanut': 8.0, 'mushroom': 2.0,
    'cabbage': 2.3, 'bok_choy': 1.0, 'spinach': 2.2, 'mustard': 2.6,
    'watercress': .5, 'ngot': 2.4, 'malabar': 2.0, 'jute': 2.2,
    'muong': 2.1, 'lettuce': 1.3, 'sprouts': 1.8, 'carrot': 2.8,
    'cucumber': .5, 'tomato': 1.2, 'onion': 1.7, 'scallion': 2.6,
    'garlic': 2.1, 'ginger': 2.0, 'lemongrass': 2.0, 'herbs': 2.0,
    'pumpkin': 1.1, 'gourd': .7, 'luffa': 1.1, 'bitter': 2.8,
    'eggplant': 3.0, 'broccoli': 2.6, 'green_bean': 3.4,
    'chayote': 1.7, 'lotus': 4.9, 'bamboo': 2.2,
    'papaya': 1.7, 'mango': 1.6, 'banana': 2.6, 'pineapple': 1.4,
    'orange': 2.4, 'pomelo': 1.0, 'avocado': 6.7, 'coconut': 1.0,
    'milk': 0, 'yogurt': 0, 'sugar': 0, 'oil': 0, 'fish_sauce': 0,
    'soy_sauce': .5, 'shrimp_paste': 0, 'chili': 1.5,
    'tamarind': 2.0, 'sesame': 11.8, 'salt': 0, 'water': 0,
    'rice_flour': .5, 'tapioca': .2,
    'shallot': 2.6, 'turmeric': 2.0, 'celery': 1.6, 'seaweed': 1.3,
    'chives': 2.5, 'okra': 3.2, 'sau': 2.0, 'durian': 3.8,
    'jackfruit': 1.5, 'guava': 5.4, 'lime': 2.8,
    'galangal': 2.0, 'starfruit': 2.8, 'banana_flower': 5.0,
    'amaranth': 2.1, 'sweet_leaves': 2.2, 'kohlrabi': 3.6,
    'radish': 1.6, 'gac': 2.0, 'sour_leaf': 2.3,
    'wheat_flour': 2.7, 'banana_green': 2.8,
    'red_bean': 7.0, 'black_bean': 8.0, 'lotus_seed': 2.0,
}

LEGACY_FIBER_REFERENCE = {
    'annatto': 1.5, 'beef_raw': 0, 'bok_choy_raw': 1.0,
    'cabbage_cooked': 2.3, 'cabbage_raw': 2.3, 'cane_juice': 0,
    'chicken_raw': 0, 'chicken_skin': 0, 'choy_sum_cooked': 1.5,
    'coconut_milk': 0.5, 'coconut_water': 0, 'coffee': 0,
    'condensed_milk': 0, 'dill': 2.1, 'dragon': 1.7,
    'fermented_fish': 0, 'fish_fat_raw': 0, 'fish_raw': 0,
    'glass_dry': 0.5, 'herb': 2.0, 'liver': 0,
    'longan': 1.1, 'lot_leaf': 2.0, 'lotus_stem': 2.6,
    'lychee': 1.3, 'mackerel': 0, 'mung_cooked': 5.0,
    'mung_dry': 12.0, 'offal': 0, 'papaya_green': 1.7,
    'pea': 5.0, 'pepper': 2.0, 'pork_fat': 0,
    'pork_leg': 0, 'pork_raw': 0, 'rambutan': 0.9,
    'rib_raw': 0, 'rice_dry': 1.3, 'sesame_oil': 0,
    'shrimp_raw': 0, 'soymilk': 0.3, 'sticky': 0.6,
    'sweet': 3.0, 'tea': 0, 'tilapia_raw': 0,
    'veg_cooked': 2.0, 'watermelon': 0.4,
}

ALL_FIBER_REFERENCES = {**FIBER_REFERENCE, **LEGACY_FIBER_REFERENCE}


def estimate_fiber_per_100g(provenance):
    """Return rounded g/100g, or None when any ingredient is unknown.

    Both 291 expansion recipes (key/retained_edible_grams) and the older
    catalog (ingredient/retained_grams) are supported.
    """
    if not isinstance(provenance, dict):
        return None
    recipe = provenance.get('recipe')
    if not isinstance(recipe, dict):
        return None
    items = recipe.get('ingredients')
    if not isinstance(items, list) or not items:
        return None
    try:
        mass = float(recipe.get('finished_edible_grams'))
        if not math.isfinite(mass) or mass <= 0 or mass > 10000:
            return None
        fiber = 0.0
        for part in items:
            if not isinstance(part, dict):
                return None
            key = part.get('key', part.get('ingredient'))
            if key not in ALL_FIBER_REFERENCES:
                return None
            grams = float(part.get('retained_edible_grams', part.get('retained_grams')))
            if not math.isfinite(grams) or grams < 0 or grams > 2000:
                return None
            fiber += ALL_FIBER_REFERENCES[key] * grams / 100
        value = fiber * 100 / mass
        if not math.isfinite(value) or value < 0 or value > 35:
            return None
        return round(value, 3)
    except (ValueError, TypeError, OverflowError):
        return None
