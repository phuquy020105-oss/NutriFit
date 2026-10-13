"""Offline-only checks; no database, SMTP, Gemini or Flask required."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'setup'))
from estimate_vietnamese_fiber import data_preview, FIBER_REFERENCE, estimated_fiber_per_100g


def test_all_291_have_an_ingredient_weighted_fiber_estimate():
    dishes, fiber = data_preview()
    assert len(dishes) == len(fiber) == 291
    assert all(0 <= amount <= 20 for amount in fiber.values())
    assert len([v for v in fiber.values() if v > 0]) > 260
    assert all(estimated_fiber_per_100g(d) == fiber[d['dish_id']] for d in dishes)


def test_no_missing_ingredient_reference():
    dishes, _ = data_preview()
    missing = {i['key'] for d in dishes for i in d['provenance']['recipe']['ingredients'] if i['key'] not in FIBER_REFERENCE}
    assert not missing


def test_fiber_uses_ingredient_grams_not_constant_per_group():
    dishes, fiber = data_preview()
    values = {fiber[d['dish_id']] for d in dishes if d['type'] == 'VEGGIE'}
    assert len(values) >= 10
