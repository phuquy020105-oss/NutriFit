r"""Diagnose NutriFit /api/meals latency on a LOCAL development machine.

Run from NutriFit-UI (with backend/ and .env):
    ..\.venv\Scripts\python.exe run_meal_diagnostics.py

Does not change MySQL tables, account data, or business logic. It logs only
function names, request paths, and elapsed milliseconds (no request body).
"""
from __future__ import annotations

import functools
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if not (ROOT / "backend" / "app").is_dir():
    raise SystemExit("Place this file at the NutriFit-UI project root, next to backend/.")
sys.path.insert(0, str(ROOT / "backend"))

from flask import has_request_context, request, current_app
from app import create_app
import app.services.meal_planner_v4 as planner
from app.services.meal_planner_v4 import MealPlannerV4
from app.services.meal_service import MealService
from app.services.food_intake_service import FoodIntakeService
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.repositories.meal_repository import MealRepository
from app.repositories.nutrition_v4_repository import NutritionV4Repository


def trace(label, original):
    @functools.wraps(original)
    def wrapped(*args, **kwargs):
        if not has_request_context() or not request.path.startswith("/api/meals/"):
            return original(*args, **kwargs)
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            # No user IDs, request bodies, secrets or SQL bind values in logs.
            current_app.logger.warning("MEAL_STAGE %s %s %.1fms", request.path, label, elapsed)
    return wrapped


def trace_static(cls, name):
    original = getattr(cls, name)
    setattr(cls, name, staticmethod(trace(f"{cls.__name__}.{name}", original)))


for name in ("candidate_pool", "composition_shortlist", "fit_portions", "refine_options"):
    setattr(planner, name, trace(name, getattr(planner, name)))
for cls, names in (
    (MealPlannerV4, ("generate", "fallback")),
    (MealService, ("profile",)),
    (FoodIntakeService, ("daily",)),
    (FoodCatalogRepository, ("dishes", "recent_dishes")),
    (NutritionV4Repository, ("require_schema",)),
    (MealRepository, ("load", "store", "lock_user")),
):
    for name in names:
        trace_static(cls, name)

app = create_app()

if __name__ == "__main__":
    host = os.getenv("NUTRIFIT_BACKEND_HOST", "127.0.0.1")
    print(f"NutriFit diagnostic backend: http://{host}:5000")
    print("Only /api/meals/ steps are timed; press Ctrl+C to stop.")
    app.run(host=host, port=5000, debug=False, use_reloader=False, threaded=True)
