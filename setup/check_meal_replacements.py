"""Read-only NutriFit catalog check for meal replacement counts.

From NutriFit-NextUI:
    ..\\.venv\\Scripts\\python.exe setup\\check_meal_replacements.py --group PROTEIN --meal lunch --avoid ca

Only prints counts; never prints credentials. Does not write to MySQL.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['PROTEIN', 'CARB', 'VEGGIE', 'SOUP', 'MAIN', 'SIDE', 'DESSERT', 'DRINK'], default='PROTEIN')
    parser.add_argument('--meal', choices=['breakfast', 'lunch', 'dinner'], default='lunch')
    parser.add_argument('--avoid', default='cá', help='One avoided food name; supports Vietnamese and ASCII aliases')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'backend'))
    from app import create_app
    from app.extensions import db
    from app.services.food_catalog_service import catalog_dishes
    from app.services.meal_preferences import violates, v4_preferences
    app = create_app()
    with app.app_context():
        items = [dish for dish in catalog_dishes(args.meal) if dish['type'] == args.group]
        strict = v4_preferences({'avoid': [args.avoid]}, args.meal)
        reference = v4_preferences({'avoid': [args.avoid], 'ingredientMode': 'reference'}, args.meal)
        print(json.dumps({
            'group': args.group, 'meal': args.meal, 'all_edible_active': len(items),
            'strict_eligible': sum(not violates(d, strict) for d in items),
            'reference_eligible': sum(not violates(d, reference) for d in items),
            'writes': 0,
            'note': 'Reference filtering is NOT safe for allergy use.'
        }, ensure_ascii=False, indent=2))
        db.session.rollback()


if __name__ == '__main__':
    main()
