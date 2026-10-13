"""Optional NutriFit project-only rough fiber estimates for the 291 expansion recipes.

No medical/nutritional reference is claimed. Uses each dish's assumed edible
ingredient masses and approximate fiber/100g reference values. No hard-coded
single fiber total per dish. Never changes a non-null fiber value. Preview is
read-only; --apply requires an existing external SQL backup and an exact DB name.

Run from NutriFit-NextUI:
    python setup/estimate_vietnamese_fiber.py
    python setup/estimate_vietnamese_fiber.py --check-db
    python setup/estimate_vietnamese_fiber.py --apply --backup "C:\\...\\NutriFitDB_before_fiber.sql"
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / 'setup/seeds/vietnamese_expansion_2026.json'

# Illustrative grams total dietary fiber / 100g EDIBLE prepared ingredients.
# Rounded educational assumptions (not source-certified or allergy-safe).
# Animal-only and oil/sugar/water ingredients have no dietary fiber.
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

# Legacy 158-dish source uses older ingredient keys/units. These are deliberately
# approximate educational assumptions; no unverified ingredients are silently
# assigned a fiber value. Dry/raw keys use separate reference estimates.
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


def legacy_preview():
    source = ROOT / 'setup/seeds/nutrition_catalog.json'
    dishes = json.loads(source.read_text(encoding='utf-8'))['dishes']
    references = {**FIBER_REFERENCE, **LEGACY_FIBER_REFERENCE}
    estimates = {}
    for dish in dishes:
        recipe = dish.get('provenance', {}).get('recipe', {})
        parts = recipe.get('ingredients', [])
        mass = float(recipe.get('finished_edible_grams') or 0)
        if mass <= 0 or not parts or any(i.get('ingredient') not in references for i in parts):
            # Unknown recipe ingredients stay NULL until they can be checked.
            continue
        total = sum(references[i['ingredient']] * float(i.get('retained_grams', 0)) / 100
                    for i in parts)
        estimates[dish['dish_id']] = round(100 * total / mass, 3)
    return estimates


def estimated_fiber_per_100g(dish):
    recipe = dish['provenance']['recipe']
    components = recipe['ingredients']
    mass = float(recipe['finished_edible_grams'])
    if not 0 < mass <= 1600:
        raise ValueError('Invalid recipe mass: ' + dish['dish_id'])
    if not components or any(i['key'] not in FIBER_REFERENCE for i in components):
        unknown = [i['key'] for i in components if i['key'] not in FIBER_REFERENCE]
        raise ValueError('Missing reference for ' + dish['dish_id'] + ': ' + ', '.join(unknown))
    grams = sum(FIBER_REFERENCE[i['key']] * float(i['retained_edible_grams']) / 100
                for i in components)
    return round(100 * grams / mass, 3)


def data_preview():
    dishes = json.loads(SEED.read_text(encoding='utf-8'))['dishes']
    if len(dishes) != 291:
        raise ValueError('Expected 291 recipes')
    values = {d['dish_id']: estimated_fiber_per_100g(d) for d in dishes}
    if len(values) != len(dishes):
        raise ValueError('Duplicate dish IDs')
    return dishes, values


def check_backup(file):
    if not file:
        raise ValueError('Use --backup with an exported, nonempty SQL dump outside project')
    path = file.resolve()
    if not path.is_file() or path.stat().st_size < 1024 or path.is_relative_to(ROOT):
        raise ValueError('Backup missing, too small, or stored inside project')
    with path.open('rb') as handle:
        if not any(b'create table `nutritionfoodcatalog`' in line.lower() for line in handle):
            raise ValueError('Backup lacks NutritionFoodCatalog table')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-db', action='store_true', help='Read-only MySQL preview')
    parser.add_argument('--apply', action='store_true', help='Update only previously NULL fiber values')
    parser.add_argument('--backup', type=Path, help='Required outside-project MySQL SQL dump for --apply')
    args = parser.parse_args()
    dishes, values = data_preview()
    old_values = legacy_preview()
    values = {**values, **old_values}
    positive = sum(value > 0 for value in values.values())
    print(json.dumps({'estimated_recipes': len(values), 'new_expansion': len(dishes), 'legacy_estimates': len(old_values), 'positive_fiber_estimates': positive,
                      'min_per_100g': min(values.values()), 'max_per_100g': max(values.values()),
                      'reference': 'Educational ingredient-mass estimates, not laboratory nutrition facts',
                      'writes': 0}, ensure_ascii=False, indent=2))
    if not (args.apply or args.check_db):
        return
    if args.apply:
        check_backup(args.backup)
    sys.path.insert(0, str(ROOT / 'backend'))
    from app import create_app
    from app.extensions import db
    from sqlalchemy import text
    app = create_app()
    with app.app_context():
        if (db.engine.url.database or '').lower() != 'nutrifitdb':
            raise ValueError('Refusing another database; expected NutriFitDB')
        rows = db.session.execute(text('SELECT DishId, FiberPer100G, ProvenanceJson, DataVersion '
            'FROM NutritionFoodCatalog')).mappings().all()
        by_id = {r['DishId']: r for r in rows if r['DishId'] in values}
        pending = [dish_id for dish_id, row in by_id.items() if row['FiberPer100G'] is None]
        print(json.dumps({'db_dishes_with_estimates': len(by_id), 'missing_fiber': len(pending),
                          'already_has_fiber': sum(r['FiberPer100G'] is not None for r in by_id.values()),
                          'planned_updates': len(pending), 'mode': 'APPLY' if args.apply else 'READ_ONLY'},
                         ensure_ascii=False, indent=2))
        if not args.apply:
            db.session.rollback()
            return
        updated = 0
        for dish_id in pending:
            r = by_id[dish_id]
            provenance = json.loads(r['ProvenanceJson'])
            provenance['fiber_estimate'] = {
                'method': 'Weighted ingredient gram fiber approximation',
                'source': 'NutriFit school-project assumed fiber reference values (291 expansion + supported base recipes)',
                'verified': False,
                'warning': 'Rough estimate, not clinical nutrition data; varies by cooking/brand'}
            # Increment revision so pre-update meal snapshots are not reused as fresh.
            result = db.session.execute(text('UPDATE NutritionFoodCatalog '
                'SET FiberPer100G=:fiber, ProvenanceJson=:provenance, DataVersion=DataVersion+1 '
                'WHERE DishId=:id AND FiberPer100G IS NULL AND DataVersion=:old_version'),
                {'fiber': values[dish_id], 'provenance': json.dumps(provenance, ensure_ascii=False),
                 'id': dish_id, 'old_version': r['DataVersion']})
            if result.rowcount != 1:
                db.session.rollback()
                raise RuntimeError('Concurrent update; transaction rolled back. ' + dish_id)
            updated += 1
        db.session.commit()
        print(json.dumps({'updated_rows': updated, 'transaction': 'COMMITTED'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
