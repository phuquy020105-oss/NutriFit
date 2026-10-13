"""Offline regression: local meal suggestions avoid a redundant wide search.

No Flask, Gemini or database required.
"""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'backend/app/services/meal_planner_v4.py'


def load_candidate_pool():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'candidate_pool')
    calls = []
    dishes = []
    for kind in ('CARB', 'PROTEIN', 'VEGGIE'):
        for i in range(36):
            dishes.append({'dish_id': f'{kind.lower()}_{i}', 'type': kind,
                           'calories_per_100g': 120 + i,
                           'reference_grams': 120, 'min_grams': 50, 'max_grams': 300,
                           'ingredients': ['fish'] if i == 35 else ['chicken']})

    def eligible(prefs, meal_type):
        return [dish for dish in dishes if not (set(dish['ingredients']) & set(prefs.get('avoid', [])))]

    def wide_search(*args, **kwargs):
        calls.append(True)
        return []

    namespace = {'hashlib': hashlib, 'eligible': eligible,
                 'v4_preferences': lambda preferences, meal_type: preferences,
                 'score': lambda dish, focus, preferences: 1.,
                 'ingredients': lambda dish: set(dish['ingredients']),
                 'composition_shortlist': wide_search,
                 'POOL_SEARCH_ROLE_LIMIT': 24}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace['candidate_pool'], calls


def test_local_catalog_skips_redundant_wide_search_but_keeps_safe_foods():
    pool, calls = load_candidate_pool()
    prefs = {'avoid': ['fish'], 'prefer': [], 'dislikes': []}
    result = pool(prefs, 'lunch', 'maintain', 'salt1',
                  target=850, macro_targets={'protein': 45, 'carbs': 90, 'fat': 26}, fast=True)
    assert len(result) == 24  # Eight candidates for each required role.
    assert all('fish' not in dish['ingredients'] for dish in result)
    assert not calls


def test_ai_path_can_use_regular_wide_search():
    pool, calls = load_candidate_pool()
    pool({'avoid': [], 'prefer': [], 'dislikes': []}, 'lunch', 'maintain',
         'salt2', target=850, macro_targets={'protein': 45, 'carbs': 90, 'fat': 26})
    assert len(calls) == 1


def test_frontend_uses_fast_local_generator_and_preserves_premium():
    ui = (ROOT / 'frontend/js/studio.js').read_text(encoding='utf-8')
    assert "case 'generate-meal':return generateMeal(false,undefined,true);" in ui
    assert "case 'refresh-meal':return generateMeal(true,undefined,true);" in ui
    assert '/api/meals/daily-plan' in ui
    assert 'AI ước tính và lưu bữa ăn' in ui
