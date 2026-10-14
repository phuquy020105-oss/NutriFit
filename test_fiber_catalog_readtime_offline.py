"""Offline checks for non-destructive fiber estimates in the active catalog."""
import json
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / 'backend/app/services/fiber_estimates.py'


def _estimator():
    spec = importlib.util.spec_from_file_location('nutrifit_fiber_estimates_offline', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.estimate_fiber_per_100g


def test_all_291_expansion_dishes_receive_recipe_weighted_estimate():
    estimate = _estimator()
    dishes = json.loads((ROOT / 'setup/seeds/vietnamese_expansion_2026.json').read_text(encoding='utf-8'))['dishes']
    assert len(dishes) == 291
    values = [estimate(d['provenance']) for d in dishes]
    assert all(value is not None and 0 <= value <= 35 for value in values)
    assert sum(value > 0 for value in values) >= 280


def test_older_seed_recipes_also_supported():
    estimate = _estimator()
    dishes = json.loads((ROOT / 'setup/seeds/nutrition_catalog.json').read_text(encoding='utf-8'))['dishes']
    assert len(dishes) >= 150
    assert all(estimate(d['provenance']) is not None for d in dishes)


def test_missing_or_invalid_ingredient_must_not_be_reported_as_zero():
    estimate = _estimator()
    base = {'recipe': {'finished_edible_grams': 100, 'ingredients': [
        {'key': 'rice', 'retained_edible_grams': 50},
        {'key': 'unknown_fruit', 'retained_edible_grams': 50},
    ]}}
    assert estimate(base) is None
    assert estimate({'recipe': {'finished_edible_grams': 0, 'ingredients': [{'key': 'rice', 'retained_edible_grams': 1}]}}) is None
    assert estimate({'recipe': {'finished_edible_grams': 100, 'ingredients': [{'key': 'rice', 'retained_edible_grams': -1}]}}) is None
    assert estimate({'recipe': {'finished_edible_grams': 100, 'ingredients': [{'key': 'chicken', 'retained_edible_grams': 100}]}}) == 0


def test_known_value_never_overwritten_in_repository_serialize():
    import ast
    tree = ast.parse((ROOT / 'backend/app/repositories/food_catalog_repository.py').read_text(encoding='utf-8'))
    # Test the serializer with isolated stubs, so no Flask/MySQL needed.
    namespace = {'__name__': 'app.repositories.food_catalog_repository'}
    import types
    from unittest.mock import patch
    app = types.ModuleType('app')
    app.__path__ = []
    repositories = types.ModuleType('app.repositories')
    repositories.__path__ = []
    services = types.ModuleType('app.services')
    services.__path__ = []
    extensions = types.ModuleType('app.extensions')
    extensions.db = object()
    module_errors = types.ModuleType('app.services.module_errors')
    module_errors.ModuleError = type('ModuleError', (Exception,), {})
    estimator_mod = types.ModuleType('app.services.fiber_estimates')
    estimator_mod.estimate_fiber_per_100g = _estimator()
    with patch.dict(sys.modules, {'app': app, 'app.repositories': repositories,
        'app.services': services, 'app.extensions': extensions,
        'app.services.module_errors': module_errors,
        'app.services.fiber_estimates': estimator_mod}):
        module_path = ROOT / 'backend/app/repositories/food_catalog_repository.py'
        spec = importlib.util.spec_from_file_location('app.repositories.food_catalog_repository', module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        seed = json.loads((ROOT / 'setup/seeds/vietnamese_expansion_2026.json').read_text(encoding='utf-8'))['dishes'][0]
        row = {'DishId': seed['dish_id'], 'NameVi': seed['name'], 'ComponentType': seed['type'],
               'PreparationState': seed['preparation_state'],
               'ReferenceGrams': seed['reference_grams'], 'MinGrams': seed['min_grams'],
               'MaxGrams': seed['max_grams'], 'KcalPer100G': seed['calories_per_100g'],
               'CarbsPer100G': seed['macros_per_100g']['carbs'],
               'ProteinPer100G': seed['macros_per_100g']['protein'],
               'FatPer100G': seed['macros_per_100g']['fat'], 'FiberPer100G': None,
               'IngredientsJson': json.dumps(seed['ingredients']), 'MealTypesJson': json.dumps(seed['meal_types']),
               'ProvenanceJson': json.dumps(seed['provenance']), 'PrepMinutes': seed['prep_minutes'],
               'Estimated': 1, 'IsActive': 1, 'DataVersion': 1}
        derived = module.FoodCatalogRepository.serialize(row)
        assert derived['macros_per_100g']['fiber'] > 0
        assert derived['provenance']['fiber_estimate']['verified'] is False
        row['FiberPer100G'] = 7.25
        known = module.FoodCatalogRepository.serialize(row)
        assert known['macros_per_100g']['fiber'] == 7.25
        assert 'fiber_estimate' not in known['provenance']
