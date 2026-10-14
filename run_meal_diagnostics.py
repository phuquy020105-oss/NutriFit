# cspell:ignore NutriFit NUTRIFIT Nutri
r"""NutriFit local /api/meals performance diagnostics.

Run from the NutriFit-UI project root (the folder containing backend/):
    ..\.venv\Scripts\python.exe run_meal_diagnostics.py

This script does NOT update MySQL or user data. It wraps selected Python
functions to accumulate timings and emits one compact summary per request.
Dynamic imports are intentional: this script lives outside backend/ and Pylance
cannot resolve `app` statically without an extra analysis path.
"""
from __future__ import annotations

from collections import defaultdict
from functools import wraps
from importlib import import_module
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if not (BACKEND / "app" / "__init__.py").is_file():
    raise SystemExit(
        "Khong tim thay backend/app/__init__.py. "
        "Hay dat run_meal_diagnostics.py vao thu muc NutriFit-UI (ngang backend/)."
    )

# Runtime lookup. Static analysis can use python.analysis.extraPaths=["./backend"].
sys.path.insert(0, str(BACKEND))

from flask import current_app, g, has_request_context, request  # noqa: E402


def load_module(module_name: str):
    """Import backend modules at runtime without unresolved-import warnings."""
    try:
        return import_module(module_name)
    except ImportError as exc:
        raise SystemExit(
            f"Khong nap duoc module {module_name}: {exc}. "
            "Kiem tra Python interpreter va dependencies trong requirements.txt."
        ) from exc


planner = load_module("app.services.meal_planner_v4")
meal_service = load_module("app.services.meal_service")
intake_service = load_module("app.services.food_intake_service")
catalog_repo = load_module("app.repositories.food_catalog_repository")
meal_repo = load_module("app.repositories.meal_repository")
nutrition_repo = load_module("app.repositories.nutrition_v4_repository")
app_module = load_module("app")


def is_meal_request() -> bool:
    return has_request_context() and request.path.startswith("/api/meals/")


def timed(name, original):
    @wraps(original)
    def wrapper(*args, **kwargs):
        if not is_meal_request():
            return original(*args, **kwargs)
        start = perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            duration_ms = (perf_counter() - start) * 1000
            if not hasattr(g, "nutrifit_meal_timings"):
                g.nutrifit_meal_timings = defaultdict(lambda: [0, 0.0])
            stats = g.nutrifit_meal_timings[name]
            stats[0] += 1
            stats[1] += duration_ms
    return wrapper


def wrap_function(module, name):
    original = getattr(module, name, None)
    if callable(original):
        setattr(module, name, timed(name, original))


def wrap_static_method(cls, name):
    # V6 methods are staticmethods. Keep that descriptor when wrapping.
    descriptor = vars(cls).get(name)
    if isinstance(descriptor, staticmethod):
        setattr(cls, name, staticmethod(timed(f"{cls.__name__}.{name}", descriptor.__func__)))
    elif isinstance(descriptor, classmethod):
        setattr(cls, name, classmethod(timed(f"{cls.__name__}.{name}", descriptor.__func__)))
    elif callable(descriptor):
        setattr(cls, name, timed(f"{cls.__name__}.{name}", descriptor))


for name in ("candidate_pool", "composition_shortlist", "fit_portions", "refine_options"):
    wrap_function(planner, name)

for cls, method_names in (
    (planner.MealPlannerV4, ("generate", "fallback")),
    (meal_service.MealService, ("profile",)),
    (intake_service.FoodIntakeService, ("daily",)),
    (catalog_repo.FoodCatalogRepository, ("dishes", "recent_dishes")),
    (nutrition_repo.NutritionV4Repository, ("require_schema",)),
    (meal_repo.MealRepository, ("load", "store", "lock_user")),
):
    for method_name in method_names:
        wrap_static_method(cls, method_name)

app = app_module.create_app()


@app.after_request
def report_meal_timings(response):
    if not is_meal_request():
        return response
    stats = getattr(g, "nutrifit_meal_timings", {})
    for name, (calls, total) in sorted(stats.items(), key=lambda item: -item[1][1]):
        current_app.logger.warning(
            "MEAL_STAGE %s %s %.1fms calls=%d",
            request.path, name, total, calls,
        )
    return response


if __name__ == "__main__":
    host = os.getenv("NUTRIFIT_BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("NUTRIFIT_BACKEND_PORT", "5000"))
    print(f"NutriFit diagnostic backend: http://{host}:{port}", flush=True)
    print("Timings appear after each /api/meals/ request; press Ctrl+C to stop.", flush=True)
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
