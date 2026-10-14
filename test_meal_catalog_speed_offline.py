"""Offline tests for request-local catalog snapshot and one-time preference validation.

Run: python test_meal_catalog_speed_offline.py
No Flask, MySQL, Gemini, or credentials required.
"""
import ast
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2] if HERE.parent.name == "tests" else HERE.parent


def extract(source, name, namespace):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace[name]


class CatalogPerformanceTests(unittest.TestCase):
    def test_eligible_validates_preferences_once(self):
        calls = {"validated": 0, "scanned": 0}
        dishes = [{"dish_id": str(i), "ingredients": ["fish"] if i % 7 == 0 else ["chicken"]}
                  for i in range(319)]

        def validate(prefs, meal):
            calls["validated"] += 1
            return prefs

        def catalog(meal):
            calls["scanned"] += 1
            return dishes

        ns = {"v4_preferences": validate, "catalog_dishes": catalog,
              "violates": lambda d, p: bool(set(d["ingredients"]) & set(p["avoid"]))}
        eligible = extract(ROOT / "backend/app/services/meal_planner_v4.py", "eligible", ns)
        result = eligible({"avoid": ["fish"]}, "lunch")
        self.assertEqual(calls, {"validated": 1, "scanned": 1})
        self.assertEqual(len(result), 319 - len([i for i in range(319) if i % 7 == 0]))
        self.assertTrue(all("fish" not in d["ingredients"] for d in result))

    def test_catalog_reads_once_per_request_and_filters_each_meal(self):
        calls = []
        context = {"enabled": True, "g": types.SimpleNamespace()}
        dishes = [
            {"dish_id": "a", "meal_types": ["breakfast"], "preparation_state": "cooked"},
            {"dish_id": "b", "meal_types": ["lunch", "dinner"], "preparation_state": "ready"},
            {"dish_id": "c", "meal_types": ["lunch"], "preparation_state": "raw"},
        ]

        class Repo:
            @staticmethod
            def dishes():
                calls.append(True)
                return list(dishes)

        ns = {"g": context["g"], "has_request_context": lambda: context["enabled"],
              "FoodCatalogRepository": Repo, "usable": lambda d: True}
        catalog = extract(ROOT / "backend/app/services/food_catalog_service.py", "catalog_dishes", ns)
        self.assertEqual([d["dish_id"] for d in catalog("breakfast")], ["a"])
        self.assertEqual([d["dish_id"] for d in catalog("lunch")], ["b"])
        self.assertEqual(len(catalog()), 3)
        self.assertEqual(len(calls), 1, "repeated calls within one request must reuse snapshot")
        # A new request has its own flask.g, so it cannot reuse old data.
        ns["g"] = types.SimpleNamespace()
        self.assertEqual(len(catalog("dinner")), 1)
        self.assertEqual(len(calls), 2)
        # Running without a request never retains a stale global snapshot.
        context["enabled"] = False
        catalog("lunch")
        catalog("lunch")
        self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
