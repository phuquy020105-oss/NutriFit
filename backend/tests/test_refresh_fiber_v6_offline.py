"""Offline regression checks for refresh diversity and educational fiber estimates."""
import ast
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _fiber_module():
    path = ROOT / 'setup/estimate_vietnamese_fiber.py'
    spec = importlib.util.spec_from_file_location('nutrifit_estimate_vietnamese_fiber_v6', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fiber_covers_all_existing_source_recipes():
    m = _fiber_module()
    new_dishes, new_estimates = m.data_preview()
    old_estimates = m.legacy_preview()
    assert len(new_dishes) == len(new_estimates) == 291
    assert len(old_estimates) == 158
    assert len(set(new_estimates) & set(old_estimates)) == 0
    assert 0 < old_estimates['rice'] < 5
    assert old_estimates['chicken'] == 0
    assert sum(v > 0 for v in {**new_estimates, **old_estimates}.values()) >= 400


def test_refresh_pool_rotates_without_relaxing_eligible_filter():
    path = ROOT / 'backend/app/services/meal_planner_v4.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'candidate_pool')
    # Extract just the pure ranking function; Flask/MySQL/Gemini are not needed.
    namespace = {'hashlib': hashlib,
                 'v4_preferences': lambda prefs, kind: prefs,
                 'eligible': lambda prefs, meal: [d for d in dishes if d['dish_id'] not in prefs.get('avoid_ids', [])],
                 'score': lambda d, focus, prefs: 5.0,
                 'ingredients': lambda d: set()}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), 'exec'), namespace)
    dishes = [{'dish_id': f'protein_{i}', 'type': 'PROTEIN', 'calories_per_100g': 170,
               'reference_grams': 100, 'max_grams': 250, 'min_grams': 50} for i in range(35)]
    prefs = {'avoid_ids': ['protein_7'], 'avoid': [], 'dislikes': [], 'prefer': []}
    pools = [namespace['candidate_pool'](prefs, 'lunch', 'maintain', f'refresh:{n}',
                                          target=None, macro_targets=None, diversify=True) for n in range(8)]
    assert all(len(p) == 8 for p in pools)
    assert all('protein_7' not in {d['dish_id'] for d in p} for p in pools)
    assert len({tuple(d['dish_id'] for d in p) for p in pools}) >= 4
