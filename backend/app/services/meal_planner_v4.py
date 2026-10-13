"""Catalog composition and single-component replacement; core targets stay intact."""
import copy
import json
import re
import hashlib
from itertools import combinations
from flask import current_app
from sqlalchemy import text
from app.extensions import db
from app.ai.gemini_client import AIUnavailable, COMPOSITION_RULES, COMPOSITION_CALORIE_RANGE, COMPOSITION_TEXT_LIMITS
from app.services.food_catalog_service import catalog_dishes, component, totals, recipe_catalog_compatible
from app.repositories.food_catalog_repository import FoodCatalogRepository
from app.repositories.meal_repository import MealRepository
from app.repositories.nutrition_v4_repository import NutritionV4Repository
from app.services.meal_service import MealService
from app.services import meal_service as core_meals
from app.services.meal_preferences import v4_preferences, violates, ingredients
from app.services.module_errors import ModuleError


def focus_for(value, goal):
    if value is None or value == "":
        value = "lose" if str(goal).lower() in ("lose", "weight_loss", "giam_can") else "gain" if str(goal).lower() in ("gain", "weight_gain", "tang_can") else "maintain"
    if value not in ("lose", "maintain", "gain", "muscle_gain"):
        raise ModuleError("planningFocus phải là lose, maintain, gain hoặc muscle_gain.")
    return value


def score(item, focus, preferences):
    m = item["macros_per_100g"]
    kcal = item["calories_per_100g"]
    density = m["protein"] / max(kcal, 1) * 100
    fiber = m["fiber"] or 0
    base = {"lose": density + fiber * 2 - m["fat"] * 0.7,
            "maintain": fiber + density * 0.3 - abs(m["fat"] - 3) * 0.2,
            "gain": kcal * 0.08 + m["carbs"] * 0.2,
            "muscle_gain": density * 2 + m["protein"] * 0.4}[focus]
    tags = ingredients(item)
    base += 100 * len(tags & (set(preferences.get("prefer", [])) - set(preferences.get("dislikes", [])) - set(preferences.get("avoid", []))))
    base -= 100 * len(tags & set(preferences.get("dislikes", [])))
    return round(base, 4)


def eligible(preferences, meal_type=None):
    return [d for d in catalog_dishes(meal_type) if not violates(d, v4_preferences(preferences, meal_type))]


def candidate_pool(preferences, meal_type, focus, salt, recent=(), target=None, macro_targets=None, diversify=False, fast=False):
    """Bound the prompt while keeping every required role and varied food choices."""
    preferences = v4_preferences(preferences, meal_type)
    groups = {}
    for dish in eligible(preferences, meal_type):
        if meal_type == "breakfast" and dish["type"] not in ("MAIN", "SIDE", "DRINK", "DESSERT"):
            continue
        if meal_type != "breakfast" and dish["type"] not in ("CARB", "PROTEIN", "VEGGIE", "SOUP", "DESSERT"):
            continue
        groups.setdefault(dish["type"], []).append(dish)
    ranked_groups, energy_groups = {}, {}
    for kind, group in groups.items():
        def priority(dish):
            variation = int(hashlib.sha256((salt + dish["dish_id"]).encode()).hexdigest()[:8], 16) / 0xffffffff
            # On an explicit refresh, spread candidates across the *eligible*
            # catalog instead of deterministically reusing the same top eight.
            # Hard avoid/meal restrictions were applied before ranking.
            # New candidates are still portion-fitted and validated downstream.
            variety_weight = 55 if diversify else 10
            return -(score(dish, focus, preferences) - (15 if dish["dish_id"] in recent else 0)
                     + variation * variety_weight)
        ranked = sorted(group, key=priority)
        ranked_groups[kind] = ranked
        energy_groups[kind] = []
        if target and len(ranked) > 8:
            # Keep focus/preferences ranking, but reserve room for energy-capable
            # foods. Hard ingredient avoidance above is never relaxed.
            share = {"MAIN": .85, "CARB": .45, "PROTEIN": .35}.get(kind, .1)
            capacity = lambda d: d["calories_per_100g"] * d["max_grams"] / 100
            energetic = sorted(ranked, key=lambda d: (max(0, target * share - capacity(d)),
                abs(d["calories_per_100g"] * d["reference_grams"] / 100 - target * share), priority(d)))[:2]
            energy_groups[kind] = energetic
    # A local-only refresh will run a second bounded shortlist in fallback().
    # The wide 24-per-role beam here is CPU-heavy for 319+ catalog dishes.
    # Skip that redundant shortlist in fast mode; keep role, meal and avoid filters.
    combinations = composition_shortlist(ranked_groups, meal_type, target, macro_targets,
        role_limit=POOL_SEARCH_ROLE_LIMIT) if not fast and target and macro_targets is not None else []
    result = []
    for kind, ranked in ranked_groups.items():
        complements = []
        for combination in combinations:
            for dish in combination:
                if dish["type"] == kind and dish not in complements:
                    complements.append(dish)
            if len(complements) >= 2:
                break
        # Four focus/history choices, two energy choices and two complementary
        # choices share eight slots; overlapping reservations are refilled.
        preferred_terms = set(preferences.get("prefer", [])) - set(preferences.get("dislikes", [])) - set(preferences.get("avoid", []))
        # A soft preference must not spend every prompt slot on the same food
        # source; retain one alternative for nutrition/diversity when available.
        alternatives = [d for d in ranked if preferred_terms and not preferred_terms & ingredients(d)]
        reserved = ranked[:4] + alternatives[:1] + energy_groups[kind] + complements[:2]
        selected = []
        for dish in reserved + ranked:
            if dish not in selected:
                selected.append(dish)
            if len(selected) == 8:
                break
        result.extend(selected)
    return result


def safe_text(value, maximum, diagnostic_code=None):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum or any(c in value for c in "<>\r\n") or any(ord(c) < 32 for c in value):
        raise AIUnavailable("invalid_output", diagnostic_code=diagnostic_code)
    return value.strip()


def option_from_recipe(recipe, title, reason, source):
    recipe["provider_source"] = source
    values = totals(recipe["components"])
    recipe["fiber_complete"] = all(c.get("fiber_complete", True) for c in recipe["components"])
    return {"title": title, "calories": values["calories"],
            "macros": {k: values[k] for k in ("carbs", "protein", "fat", "fiber")},
            "components": {c["type"]: f'{c["name"]} (~{c["grams"]} g)' for c in recipe["components"]},
            "digestibility": f"[{source}] {reason}", "recipe": recipe}


def today():
    return core_meals.today()


# Engineering preferences, not clinical limits. Doubling all portions costs .25 in R,
# equivalent to 50% error in all macros; another 15% beyond the soft kcal band
# costs 4, so energy still matters without forcing an exact target.
PORTION_OBJECTIVE = {"kcal_outside": 4.0, "macros": 1.0, "reference": .25}
PREFERRED_KCAL_DEVIATION = .15
PORTION_SEARCH_DIVISORS = (4, 8, 16, 32, 64)
# Search budgets bound CPU work independently of future catalog growth.
POOL_SEARCH_ROLE_LIMIT = 24
COMPOSITION_BEAM_WIDTH = 12
FALLBACK_FIT_LIMIT = 6
# Source switching must save both 15% of the bundle score and .02 points.
# .02 is roughly one 14% normalized squared error, not a dietary cutoff.
QUALITY_SWITCH_RELATIVE = .15
QUALITY_SWITCH_ABSOLUTE = .02
# Small engineering tie budgets, below a substantial normalized macro miss.
# CARB and primary repetition each cost at most .03; general overlap at most .01.
DIVERSITY_WEIGHTS = {"carb": .03, "primary": .03, "overlap": .01}
# Relative mass uses this combination's required reference portions, not a
# universal gram ceiling. Doubling that mass costs .02 (the source-switch noise
# margin); an optional dish beyond one costs half that. These are soft tie costs.
PORTION_MASS_WEIGHT = .02
EXTRA_COMPONENT_WEIGHT = .01


def portion_quality(parts, catalog):
    required = {"MAIN"} if any(p.get("type") == "MAIN" for p in parts) else {"CARB", "PROTEIN", "VEGGIE"}
    reference = sum(catalog[p["dish_id"]]["reference_grams"] for p in parts if p.get("type") in required)
    # Also support a partial/test composition without known component roles.
    reference = reference or sum(catalog[p["dish_id"]]["reference_grams"] for p in parts)
    mass = sum(p["grams"] for p in parts)
    optional = sum(p.get("type") not in required for p in parts)
    mass_error = max(0, mass / max(reference, 1) - 1)
    return {"total_grams": round(mass, 2), "required_reference_grams": round(reference, 2),
            "optional_count": optional, "mass_ratio": mass / max(reference, 1),
            "penalty": PORTION_MASS_WEIGHT * mass_error ** 2 + EXTRA_COMPONENT_WEIGHT * max(0, optional - 1)}


def bundle_diversity(options):
    """Soft ID/role diversity; higher score means more diverse, not healthier."""
    parts = [o["recipe"]["components"] for o in options]
    pairs = list(combinations(parts, 2))
    if not pairs:
        return {"score": 1.0, "penalty": 0.0, "shared_components": []}
    repeats = {"carb": 0.0, "primary": 0.0, "overlap": 0.0}
    shared = []
    for left, right in pairs:
        a, b = ({p["dish_id"] for p in group} for group in (left, right))
        shared.append(len(a & b))
        repeats["overlap"] += len(a & b) / max(len(a | b), 1)
        for key, roles in (("carb", {"CARB"}), ("primary", {"PROTEIN", "MAIN"})):
            x, y = ({p["dish_id"] for p in group if p["type"] in roles} for group in (left, right))
            repeats[key] += bool(x & y)
    repeats = {k: v / len(pairs) for k, v in repeats.items()}
    penalty = sum(DIVERSITY_WEIGHTS[k] * v for k, v in repeats.items())
    return {"score": 1 - penalty / sum(DIVERSITY_WEIGHTS.values()), "penalty": penalty,
            "repetition": repeats, "shared_components": shared}


def bundle_score(options):
    return sum(quality_score(o["recipe"]["calorie_adjustment"]) for o in options) / len(options) + bundle_diversity(options)["penalty"]


def dish_bundle_signature(options):
    """Ignore IDs, ordering and grams: refresh must change declared dishes."""
    return tuple(sorted(tuple(sorted((p["type"], p.get("dish_id") or p.get("name", ""))
        for p in (o.get("recipe") or {}).get("components", o.get("components", [])))) for o in options))


def preference_rank(options, preferences, catalog=None):
    disliked, preferred = set(preferences.get("dislikes", [])), set(preferences.get("prefer", []))
    preferred -= disliked | set(preferences.get("avoid", []))
    if not disliked and not preferred:
        return 0, 0
    tags = [ingredients((catalog or {}).get(p["dish_id"]) or
        {"components": {p["type"]: (p.get("name", ""), p["grams"])}})
        for o in options for p in o["recipe"]["components"]]
    return sum(len(t & disliked) for t in tags), -sum(len(t & preferred) for t in tags)


def select_fallback_bundle(options, meal_type, target, preferences=None, previous_options=(), catalog=None):
    primary = "MAIN" if meal_type == "breakfast" else "PROTEIN"
    def scores(group):
        return [quality_score(o["recipe"]["calorie_adjustment"]) for o in group]
    def unsafe(group):
        return sum(not target * COMPOSITION_CALORIE_RANGE[0] <= o["calories"] <= target * COMPOSITION_CALORIE_RANGE[1] for o in group)
    bundles = [list(group) for group in combinations(options, 3)
        if len({next(p["dish_id"] for p in o["recipe"]["components"] if p["type"] == primary) for o in group}) == 3]
    if previous_options:
        changed = [g for g in bundles if dish_bundle_signature(g) != dish_bundle_signature(previous_options)
                   and unsafe(g) == 0]
        if changed:
            bundles = changed
    # At most C(6,3)=20 bundles. Diversity can spend only the existing .02
    # quality noise budget on the mean AND worst option; safety never loses.
    best = min(bundles, key=lambda g: (unsafe(g), sum(scores(g)) / len(g)))
    mean, worst = sum(scores(best)) / len(best), max(scores(best))
    close = [g for g in bundles if unsafe(g) == unsafe(best)
        and sum(scores(g)) / len(g) <= mean + QUALITY_SWITCH_ABSOLUTE
        and max(scores(g)) <= worst + QUALITY_SWITCH_ABSOLUTE]
    return min(close, key=lambda g: (preference_rank(g, preferences or {}, catalog), bundle_score(g)))


def portion_objective(parts, catalog, target, macro_targets=None):
    """Normalized, dimensionless quality terms; DB limits are checked separately."""
    from app.services.nutrition_service import NutritionService
    goals = macro_targets if macro_targets is not None else NutritionService.macro_targets(target)
    values = totals(parts)
    error = abs(values["calories"] - target) / max(target, 1)
    kcal = error ** 2 + PORTION_OBJECTIVE["kcal_outside"] * (
        max(0, error - PREFERRED_KCAL_DEVIATION) / PREFERRED_KCAL_DEVIATION) ** 2
    macro = sum(((values[k] - goals[k]) / max(goals[k], 1)) ** 2
                for k in ("protein", "carbs", "fat")) / 3
    reference = sum((p["grams"] / catalog[p["dish_id"]]["reference_grams"] - 1) ** 2
                    for p in parts) / len(parts)
    practical = portion_quality(parts, catalog)["penalty"]
    return {"kcal": kcal, "macros": macro, "reference": reference, "portion_quality": practical,
            "total": kcal + PORTION_OBJECTIVE["macros"] * macro + PORTION_OBJECTIVE["reference"] * reference + practical}


def quality_score(quality):
    # Count the worst macro once more at the same weight as one mean term.
    # This makes an isolated large miss visible without changing gram fitting.
    return quality["objective"]["total"] + quality.get("worst_macro_error", 0) ** 2 / 3


def composition_shortlist(groups, meal_type, target, macro_targets, role_limit=8):
    """Bounded beam over required roles then optional roles, never a full product.

    Partial choices are compared with three reference partner completions.
    Keep different primary IDs and complementary CARB partners in the beam.
    Cheap bounded reference scales shortlist combinations before expensive fitting.
    """
    from app.services.nutrition_service import NutritionService
    goals = macro_targets if macro_targets is not None else NutritionService.macro_targets(target)
    rules = COMPOSITION_RULES[meal_type]
    primary = "MAIN" if meal_type == "breakfast" else "PROTEIN"
    required = [primary] + [r for r in rules["required"] if r != primary]
    if any(not groups.get(r) for r in required):
        return []
    bounded = {r: list(groups.get(r, []))[:role_limit] for r in rules["allowed"]}
    catalog = {d["dish_id"]: d for items in bounded.values() for d in items}
    estimates = {}

    def estimate(dishes):
        key = tuple(sorted(d["dish_id"] for d in dishes))
        if key not in estimates:
            ranks = []
            for scale in (.75, 1, 1.25, 1.5, 2):
                parts = []
                for d in dishes:
                    grams = round(min(d["max_grams"], max(d["min_grams"], d["reference_grams"] * scale)), 2)
                    parts.append({"dish_id": d["dish_id"], "type": d["type"], "grams": grams,
                        "calories": round(d["calories_per_100g"] * grams / 100, 4),
                        "macros": {k: round((v or 0) * grams / 100, 4) for k, v in d["macros_per_100g"].items()}})
                values = totals(parts)
                worst = max(abs(values[k] - goals[k]) / max(goals[k], 1) for k in ("protein", "carbs", "fat"))
                objective = portion_objective(parts, catalog, target, goals)
                unsafe = not target * COMPOSITION_CALORIE_RANGE[0] <= values["calories"] <= target * COMPOSITION_CALORIE_RANGE[1]
                ranks.append((unsafe, quality_score({"objective": objective, "worst_macro_error": worst})))
            estimates[key] = min(ranks)
        return estimates[key]

    beam = [[]]
    order = required + [r for r in rules["allowed"] if r not in required]
    for role in order:
        choices = bounded[role] if role in required else [None, *bounded[role]]
        proposals = [parts + ([d] if d is not None else []) for parts in beam for d in choices]
        def rank(parts):
            missing = [r for r in required if r not in {d["type"] for d in parts}]
            completions = [parts + [bounded[r][offset % len(bounded[r])] for r in missing] for offset in range(3)] if missing else [parts]
            return min(estimate(c) for c in completions)
        proposals.sort(key=rank)
        diverse, seen = [], set()
        for parts in proposals:
            identifier = next(d["dish_id"] for d in parts if d["type"] == primary)
            if identifier not in seen:
                diverse.append(parts)
                seen.add(identifier)
        # Keep six primary choices first, then retain alternative CARB/primary
        # pairs. Protecting only primary IDs previously pruned every other CARB.
        beam = diverse[:6]
        partners = [p for p in proposals if p not in beam]
        while partners and len(beam) < min(9, COMPOSITION_BEAM_WIDTH):
            used_carbs = {d["dish_id"] for p in beam for d in p if d["type"] == "CARB"}
            used_primary = [d["dish_id"] for p in beam for d in p if d["type"] == primary]
            def partner_rank(p):
                carb = next((d["dish_id"] for d in p if d["type"] == "CARB"), None)
                main = next(d["dish_id"] for d in p if d["type"] == primary)
                unsafe, value = rank(p)
                return unsafe, value + DIVERSITY_WEIGHTS["carb"] * (carb is not None and carb in used_carbs) + DIVERSITY_WEIGHTS["primary"] / 3 * used_primary.count(main)
            chosen = min(partners, key=partner_rank)
            beam.append(chosen)
            partners.remove(chosen)
        beam = (beam + [p for p in diverse + proposals if p not in beam])[:COMPOSITION_BEAM_WIDTH]
    return sorted(beam, key=estimate)


def quality_metadata(parts, catalog, target, goals, before, adjusted):
    """Explain current snapshot quality; independent bounds do not prove joint feasibility."""
    values = totals(parts)
    complete = all(p["dish_id"] in catalog for p in parts)
    ranges = {k: {"minimum": round(sum(catalog[p["dish_id"]]["macros_per_100g"][k] * catalog[p["dish_id"]]["min_grams"] / 100 for p in parts), 1),
                  "maximum": round(sum(catalog[p["dish_id"]]["macros_per_100g"][k] * catalog[p["dish_id"]]["max_grams"] / 100 for p in parts), 1)}
              for k in ("protein", "carbs", "fat")} if complete else {}
    diagnostics = {}
    for k in ("protein", "carbs", "fat"):
        diagnostics[k] = {"target": goals[k], "actual": values[k], "difference_grams": round(values[k] - goals[k], 1),
            "normalized_error": round(abs(values[k] - goals[k]) / max(goals[k], 1), 6),
            "target_within_individual_bounds": ranges[k]["minimum"] <= goals[k] <= ranges[k]["maximum"] if complete else None}
    result = {"target_kcal": target, "before_kcal": before, "after_kcal": values["calories"], "adjusted": adjusted,
        "deviation_percent": round((values["calories"] - target) / max(target, 1) * 100, 2),
        "within_preferred_range": abs(values["calories"] - target) <= target * .15,
        "within_practical_range": abs(values["calories"] - target) <= target * .20,
        "macro_targets": copy.deepcopy(goals),
        "macro_deviation_percent": {k: round((values[k] - goals[k]) / goals[k] * 100, 2) if goals[k] > 0 else None for k in diagnostics},
        "macro_feasible_ranges": ranges, "macro_diagnostics": diagnostics,
        "unmet_macros": [k for k in diagnostics if values[k] < goals[k]],
        "macro_limited": any(d["target_within_individual_bounds"] is False for d in diagnostics.values()),
        "joint_feasibility": "not_proven", "reference_data_complete": complete,
        "worst_macro_error": max(d["normalized_error"] for d in diagnostics.values()),
        "reference_ratios": {p["type"]: round(p["grams"] / catalog[p["dish_id"]]["reference_grams"], 3) if p["dish_id"] in catalog else None for p in parts},
        "portion_quality": portion_quality(parts, catalog) if complete else None,
        "objective": portion_objective(parts, catalog, target, goals) if complete else None}
    result["selection_score"] = quality_score(result) if complete else None
    return result


def better_fallback(options, fallback, target, preferences=None, catalog=None):
    if not all(target * COMPOSITION_CALORIE_RANGE[0] <= o["calories"] <= target * COMPOSITION_CALORIE_RANGE[1] for o in fallback):
        return False
    old = [quality_score(o["recipe"]["calorie_adjustment"]) for o in options]
    new = [quality_score(o["recipe"]["calorie_adjustment"]) for o in fallback]
    # Among nutritionally comparable bundles, respect dislikes before likes.
    # The existing quality noise budget prevents soft taste overriding nutrition.
    if preferences and sum(new) / len(new) <= sum(old) / len(old) + QUALITY_SWITCH_ABSOLUTE and max(new) <= max(old) + QUALITY_SWITCH_ABSOLUTE:
        if preference_rank(fallback, preferences, catalog) < preference_rank(options, preferences, catalog):
            return True
    gain = bundle_score(options) - bundle_score(fallback)
    # Also protect the worst option: an excellent first choice cannot conceal
    # making another choice worse merely to lower the bundle average.
    return gain >= max(QUALITY_SWITCH_ABSOLUTE, bundle_score(options) * QUALITY_SWITCH_RELATIVE) and max(new) <= max(old)


def fit_portions(parts, catalog, target, macro_targets=None):
    """Bounded coordinate search: change grams independently, never food IDs.

    Start from the proposed portions, DB references and an energy-feasible seed.
    The existing safety band takes precedence over quality. If it is impossible,
    retain the best bounded result for the caller's validation/fallback handling.
    """
    def at(grams):
        return [component(p["dish_id"], round(min(catalog[p["dish_id"]]["max_grams"],
            max(catalog[p["dish_id"]]["min_grams"], g)), 2), p["type"], catalog=catalog)
            for p, g in zip(parts, grams)]

    def rank(proposal):
        energy = totals(proposal)["calories"]
        unsafe = not target * COMPOSITION_CALORIE_RANGE[0] <= energy <= target * COMPOSITION_CALORIE_RANGE[1]
        return unsafe, portion_objective(proposal, catalog, target, macro_targets)["total"]

    # This seed prevents a coordinate search getting stranded below the safety
    # band when several components must grow together. It is not the objective.
    low = min(catalog[p["dish_id"]]["min_grams"] / p["grams"] for p in parts)
    high = max(catalog[p["dish_id"]]["max_grams"] / p["grams"] for p in parts)
    for _ in range(24):
        mid = (low + high) / 2
        proposal = at([p["grams"] * mid for p in parts])
        if totals(proposal)["calories"] < target:
            low = mid
        else:
            high = mid
    seeds = [at([p["grams"] for p in parts]),
             at([catalog[p["dish_id"]]["reference_grams"] for p in parts]),
             at([p["grams"] * high for p in parts])]
    best = min(seeds, key=rank)
    for seed in seeds:
        current = seed
        for divisor in PORTION_SEARCH_DIVISORS:
            # Two sweeps at each step, bounded even for six components.
            for _ in range(2):
                for i, part in enumerate(parts):
                    dish = catalog[part["dish_id"]]
                    step = (dish["max_grams"] - dish["min_grams"]) / divisor
                    candidates = [current]
                    for value in (current[i]["grams"] - step, current[i]["grams"] + step,
                                  dish["reference_grams"], dish["min_grams"], dish["max_grams"]):
                        grams = [p["grams"] for p in current]
                        grams[i] = value
                        candidates.append(at(grams))
                    current = min(candidates, key=rank)
        best = min((best, current), key=rank)
    return best


def refine_options(options, candidates, target, macro_targets=None):
    """Apply only to new generated menus, never cached/selected/history rows."""
    catalog = {d["dish_id"]: d for d in candidates}
    result = []
    for option in options:
        recipe = copy.deepcopy(option["recipe"])
        before = option["calories"]
        recipe["components"] = fit_portions(recipe["components"], catalog, target, macro_targets)
        from app.services.nutrition_service import NutritionService
        goals = macro_targets if macro_targets is not None else NutritionService.macro_targets(target)
        recipe["calorie_adjustment"] = quality_metadata(recipe["components"], catalog, target, goals, before,
            recipe["components"] != option["recipe"]["components"])
        reason = option["digestibility"].split("] ", 1)[-1]
        result.append(option_from_recipe(recipe, option["title"], reason, recipe["provider_source"]))
    return result


class MealPlannerV4:
    @staticmethod
    def validate_composition(data, candidates, meal_type, target, focus, preferences, adjust_portions=False, macro_targets=None):
        preferences = v4_preferences(preferences, meal_type)
        def reject(code):
            # Never include provider text, request context or private values.
            raise AIUnavailable("invalid_output", diagnostic_code=code)

        if not isinstance(data, dict) or set(data) != {"choices"} or not isinstance(data["choices"], list):
            reject("INVALID_RESPONSE_SCHEMA")
        if len(data["choices"]) != 3:
            reject("INVALID_CHOICE_COUNT")
        catalog = {d["dish_id"]: d for d in candidates}
        rules = COMPOSITION_RULES[meal_type]
        result, seen = [], set()
        for choice in data["choices"]:
            if not isinstance(choice, dict) or set(choice) != {"title", "reason", "components"}:
                reject("INVALID_RESPONSE_SCHEMA")
            title = safe_text(choice["title"], COMPOSITION_TEXT_LIMITS["title"], "INVALID_TITLE")
            reason = safe_text(choice["reason"], COMPOSITION_TEXT_LIMITS["reason"], "INVALID_REASON")
            if not isinstance(choice["components"], list) or not 1 <= len(choice["components"]) <= 6:
                reject("INVALID_COMPONENT_COUNT")
            parts, roles = [], set()
            for raw in choice["components"]:
                if not isinstance(raw, dict) or set(raw) != {"type", "dish_id", "grams"}:
                    reject("INVALID_RESPONSE_SCHEMA")
                if not isinstance(raw["dish_id"], str) or raw["dish_id"] not in catalog:
                    reject("INVALID_DISH_ID")
                dish = catalog[raw["dish_id"]]
                if not isinstance(raw["type"], str) or raw["type"] not in rules["allowed"] or raw["type"] != dish["type"]:
                    reject("INVALID_COMPONENT_ROLE")
                if raw["type"] in roles:
                    reject("DUPLICATE_COMPONENT_ROLE")
                if meal_type not in dish["meal_types"] or dish["preparation_state"] == "raw":
                    reject("INVALID_DISH_ELIGIBILITY")
                if violates(dish, preferences):
                    reject("AVOID_CONFLICT")
                if type(raw["grams"]) not in (int, float):
                    reject("INVALID_PORTION")
                try:
                    part = component(raw["dish_id"], raw["grams"], raw["type"], catalog=catalog)
                except (ModuleError, ValueError):
                    raise AIUnavailable("invalid_output", diagnostic_code="INVALID_PORTION") from None
                roles.add(part["type"])
                parts.append(part)
            if not set(rules["required"]) <= roles:
                reject("MISSING_REQUIRED_GROUP")
            signature = tuple(sorted(c["dish_id"] for c in parts))
            if signature in seen:
                reject("DUPLICATE_COMPOSITION")
            seen.add(signature)
            option = option_from_recipe({"version": 4, "change": 0, "focus": focus,
                "preferences": preferences, "components": parts}, title, reason, "gemini")
            if adjust_portions:
                # All IDs, roles, eligibility and initial grams passed above.
                # The final energy check applies AFTER bounded DB-based fitting.
                option = refine_options([option], candidates, target, macro_targets)[0]
            if not target * COMPOSITION_CALORIE_RANGE[0] <= option["calories"] <= target * COMPOSITION_CALORIE_RANGE[1]:
                reject("CALORIE_TARGET_MISMATCH")
            result.append(option)
        return result

    @staticmethod
    def fallback(candidates, meal_type, target, focus, preferences, variant=0, macro_targets=None, previous_options=(), fast=False):
        preferences = v4_preferences(preferences, meal_type)
        groups = {}
        for d in candidates:
            if d["type"] in COMPOSITION_RULES[meal_type]["allowed"] and meal_type in d["meal_types"] and d["preparation_state"] != "raw" and not violates(d, preferences):
                groups.setdefault(d["type"], []).append(d)
        for items in groups.values():
            items.sort(key=lambda d: (-score(d, focus, preferences),
                hashlib.sha256((str(variant) + d["dish_id"]).encode()).hexdigest()))
        roles = ["MAIN"] if meal_type == "breakfast" else ["CARB", "PROTEIN", "VEGGIE"]
        primary = "MAIN" if meal_type == "breakfast" else "PROTEIN"
        if any(not groups.get(role) for role in roles) or len(groups[primary]) < 3:
            raise ModuleError("Catalog không đủ ba lựa chọn cân bằng thỏa điều kiện tránh món.", "INSUFFICIENT_MENUS", 422)
        shortlist = composition_shortlist(groups, meal_type, target, macro_targets, role_limit=5 if fast else 8)
        # Reserve three distinct primaries, then spend the remaining fit budget
        # on alternative CARBs. Do not fit every beam node.
        proposals, used = [], set()
        for dishes in shortlist:
            identifier = next(d["dish_id"] for d in dishes if d["type"] == primary)
            if identifier not in used:
                proposals.append(dishes)
                used.add(identifier)
            if len(proposals) == 3:
                break
        remaining = [p for p in shortlist if p not in proposals]
        while remaining and len(proposals) < (4 if fast else FALLBACK_FIT_LIMIT):
            carbs = {d["dish_id"] for p in proposals for d in p if d["type"] == "CARB"}
            mains = [d["dish_id"] for p in proposals for d in p if d["type"] == primary]
            # Shortlist order already reflects bounded nutrient/portion quality.
            # Rank coverage only inside this small shortlist; final bundle scores
            # below decide whether the diversity is worth the quality trade-off.
            def coverage(p):
                carb = next((d["dish_id"] for d in p if d["type"] == "CARB"), None)
                main = next(d["dish_id"] for d in p if d["type"] == primary)
                return carb is not None and carb in carbs, mains.count(main), shortlist.index(p)
            chosen = min(remaining, key=coverage)
            proposals.append(chosen)
            remaining.remove(chosen)
        result = []
        catalog = {d["dish_id"]: d for d in candidates}
        for selected in proposals:
            selected = sorted(selected, key=lambda d: COMPOSITION_RULES[meal_type]["allowed"].index(d["type"]))
            parts = [component(d["dish_id"], d["reference_grams"], catalog=catalog) for d in selected]
            recipe = {"version": 4, "change": 0, "focus": focus, "preferences": preferences, "components": parts}
            note = {"lose": "Ưu tiên đạm, chất xơ và món ít dầu.", "maintain": "Kết hợp các nhóm món cân bằng.",
                "gain": "Ưu tiên món có mật độ năng lượng phù hợp.", "muscle_gain": "Ưu tiên nguồn đạm; năng lượng ngày vẫn theo hồ sơ."}[focus]
            result.append(option_from_recipe(recipe, "Kết hợp: " + ", ".join(d["name"] for d in selected[:3]), note, "fallback"))
        fitted = refine_options(result, candidates, target, macro_targets)
        return select_fallback_bundle(fitted, meal_type, target, preferences, previous_options, catalog)

    @staticmethod
    def generate(user_id, meal_type, force=False, expected=None, preferences=None, focus=None, target_override=None, catalog_only=False):
        NutritionV4Repository.require_schema()
        preferences = v4_preferences(preferences, meal_type)
        nutrition = MealService.profile(user_id)
        focus = focus_for(focus, nutrition["goal"])
        existing = MealRepository.load(user_id, today(), meal_type)
        if existing and not force:
            if any(not recipe_catalog_compatible(o.get("recipe")) for o in existing["options"]):
                raise ModuleError("Danh sách món đã cập nhật. Giữ lịch sử cũ; chọn Nghĩ sau rồi Đổi thực đơn để tạo gợi ý mới.", "CATALOG_REFRESH_REQUIRED", 409)
            if any(not o.get("recipe") for o in existing["options"]):
                raise ModuleError("Bộ V3 vẫn được giữ. Chọn Nghĩ sau nếu đã chốt, rồi Đổi thực đơn để tạo bộ V4.", "V4_REFRESH_REQUIRED", 409)
            if any(v4_preferences(o["recipe"]["preferences"], meal_type) != preferences or o["recipe"]["focus"] != focus for o in existing["options"]):
                raise ModuleError("Điều kiện mới cần Đổi thực đơn với revision hiện tại.", "PREFERENCES_REQUIRE_REFRESH", 409)
            return existing, {"cached": True, "plannerVersion": "v4", "source": "cached",
                              "provider_source": existing["source"]}
        if existing and (existing["status"] == "decided" or existing["selectedOption"] is not None):
            raise ModuleError("Chọn Nghĩ sau trước khi đổi bộ đã chốt.", "MEAL_DECIDED", 409)
        if (existing and expected != existing["revision"]) or (not existing and expected is not None):
            raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
        from app.services.food_intake_service import FoodIntakeService
        budget = FoodIntakeService.daily(user_id, today())
        target = target_override if target_override is not None else budget["suggested_meal_targets"].get(meal_type, nutrition["meal_targets"][meal_type])
        variant = max((o["optionId"] for o in existing["options"]), default=0) if existing else 0
        recent = FoodCatalogRepository.recent_dishes(user_id, meal_type)
        salt = f"{user_id}:{today().isoformat()}:{variant}:{focus}"
        from app.services.nutrition_service import NutritionService
        remaining = budget["remaining"]["calories"]
        macro_target = {k: round(max(0, budget["remaining"][k]) * target / remaining, 1) for k in ("carbs", "protein", "fat")} if remaining > 0 else NutritionService.macro_targets(target)
        candidates = candidate_pool(preferences, meal_type, focus, salt, recent, target=target,
                                    macro_targets=macro_target, diversify=bool(existing and force), fast=catalog_only)
        fallback = MealPlannerV4.fallback(candidates, meal_type, target, focus, preferences,
                                         int(hashlib.sha256(salt.encode()).hexdigest()[:8], 16), macro_target,
                                         previous_options=existing["options"] if existing and force else (), fast=catalog_only)
        MealRepository.release_read_transaction()
        conflicts = set(preferences.get("prefer", [])) & (set(preferences.get("avoid", [])) | set(preferences.get("dislikes", [])))
        meta = {"cached": False, "plannerVersion": "v4", "source": "gemini", "target_kcal": target,
                "preference_notices": sorted(conflicts),
                "planningFocus": focus, "budget": budget, "estimated": True}
        try:
            if catalog_only:
                # Applying filters / refreshing choices must not wait for the
                # remote AI service. Fall back to local validated catalog.
                raise AIUnavailable("catalog_only")
            raw = current_app.extensions["nutrifit_gemini"].compose(candidates, meal_type, target, user_id, focus, macro_target,
                {"remaining": budget["remaining"], "preferences": preferences})
            options = MealPlannerV4.validate_composition(raw, candidates, meal_type, target, focus, preferences,
                                                       adjust_portions=True, macro_targets=macro_target)
            # The quality band is soft: use fallback only if it is objectively
            # better, rather than discard a safer, more reasonable AI combination.
            repeated = existing and force and dish_bundle_signature(options) == dish_bundle_signature(existing["options"])
            fallback_changed = existing and dish_bundle_signature(fallback) != dish_bundle_signature(existing["options"])
            if repeated and fallback_changed:
                options = fallback
                meta.update(source="fallback", fallback_reason="repeated_composition")
            elif not (existing and force and not repeated and not fallback_changed) and better_fallback(options, fallback, target, preferences, {d["dish_id"]: d for d in candidates}):
                energy_limited = not all(o["recipe"]["calorie_adjustment"]["within_practical_range"] for o in options)
                options = fallback
                meta.update(source="fallback", fallback_reason="calorie_quality" if energy_limited else "composition_quality",
                            fallback_diagnostic="SELECTED_COMBINATION_ENERGY_LIMIT" if energy_limited else "BETTER_MACRO_PORTION_COMBINATION")
        except AIUnavailable as error:
            options = fallback
            meta.update(source="fallback", fallback_reason=str(error), provider_http_status=error.http_status)
            if error.diagnostic_code:
                meta["fallback_diagnostic"] = error.diagnostic_code
        MealService.validate_options(options)
        changed = not existing or dish_bundle_signature(options) != dish_bundle_signature(existing["options"])
        # A provider/fallback may return the exact same combination on refresh.
        # Try other deterministic catalog rotations before reporting exhaustion.
        # Every candidate still passes through meal type, recipe and preference filters.
        if existing and force and not changed:
            previous_signature = dish_bundle_signature(existing["options"])
            # Bounded refresh work. The UI stays responsive even with 319+ dishes.
            for rotation in range(1, 5 if catalog_only else 13):
                alternate_salt = f"{salt}:rotation:{rotation}"
                alternate_pool = candidate_pool(preferences, meal_type, focus, alternate_salt,
                    recent, target=target, macro_targets=macro_target, diversify=True, fast=catalog_only)
                if not alternate_pool:
                    break
                alternate = MealPlannerV4.fallback(alternate_pool, meal_type, target, focus,
                    preferences, int(hashlib.sha256(alternate_salt.encode()).hexdigest()[:8], 16),
                    macro_target, previous_options=existing["options"], fast=catalog_only)
                if dish_bundle_signature(alternate) != previous_signature:
                    MealService.validate_options(alternate)
                    options = alternate
                    changed = True
                    meta.update(source="fallback", fallback_reason="refresh_rotation")
                    break
        same_settings = existing and all(o.get("recipe") and
            o["recipe"]["preferences"] == preferences and o["recipe"]["focus"] == focus for o in existing["options"])
        if existing and force and not changed and same_settings:
            # No-op refresh preserves revisions, history and intake. Recheck races
            # under the same parent lock used by the repository's write path.
            MealRepository.release_read_transaction()
            MealRepository.lock_user(user_id)
            current = MealRepository.load(user_id, today(), meal_type)
            if current is None or current["revision"] != expected:
                raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
            if current["status"] == "decided" or current["selectedOption"] is not None:
                raise ModuleError("Chọn Nghĩ sau trước khi đổi bộ đã chốt.", "MEAL_DECIDED", 409)
            db.session.rollback()
            return current, {"cached": True, "source": "cached", "provider_source": current["source"],
                "plannerVersion": "v4", "changed": False, "refresh_status": "no_alternative",
                "reason": "BOUNDED_SEARCH_EXHAUSTED", "target_kcal": target}
        meta.update(changed=changed, refresh_status="updated" if changed else "preferences_applied")
        result, cached = MealRepository.store(user_id, today(), meal_type, options, expected, force)
        if cached and any(not o.get("recipe") or v4_preferences(o["recipe"]["preferences"], meal_type) != preferences or o["recipe"]["focus"] != focus for o in result["options"]):
            raise ModuleError("Request khác đã lưu một bộ khác. Hãy tải lại trước khi đổi.", "PREFERENCES_REQUIRE_REFRESH", 409)
        meta.update(cached=cached, source="cached" if cached else result["source"],
                    provider_source=result["source"])
        quality = [o["recipe"].get("calorie_adjustment", {}) for o in result["options"]]
        meta["calorie_quality"] = {"target_kcal": target, "options": quality,
            "limited": any(not q.get("within_practical_range", False) for q in quality)}
        if meta["calorie_quality"]["limited"]:
            meta["calorie_quality"]["reason"] = "COMBINATION_PORTION_LIMIT"
        meta["composition_quality"] = {"options": quality,
            "macro_limited": any(q.get("macro_limited", False) for q in quality),
            "diversity": bundle_diversity(result["options"]),
            "estimated": True, "criteria": "kcal_macros_reference_mass_components_worst_macro_diversity"}
        return result, meta

    @staticmethod
    def selected_component(user_id, meal_type, option_id, kind, expected):
        NutritionV4Repository.require_schema()
        meal = MealRepository.load(user_id, today(), meal_type)
        if not meal:
            raise ModuleError("Chưa có thực đơn.", "MEAL_NOT_FOUND", 404)
        if meal["revision"] != expected:
            raise ModuleError("Thực đơn đã thay đổi. Hãy tải lại.", "STALE_MEAL", 409)
        if meal["status"] == "decided" or meal["selectedOption"] is not None:
            raise ModuleError("Chọn Nghĩ sau trước khi đổi món trong bộ đã chốt.", "MEAL_DECIDED", 409)
        option = next((o for o in meal["options"] if o["optionId"] == option_id), None)
        if option is None:
            raise ModuleError("Option không thuộc thực đơn của bạn.", "OPTION_NOT_FOUND", 404)
        if not option.get("recipe"):
            raise ModuleError("Thực đơn V3 chỉ có tổng dinh dưỡng; không thể tách chính xác từng món. Hãy tạo bộ V4.", "LEGACY_COMPONENT_NUTRITION_REQUIRED", 409)
        if not recipe_catalog_compatible(option["recipe"]):
            raise ModuleError("Bộ này dùng danh sách món cũ. Hãy đổi cả bộ trước khi thay từng món.", "CATALOG_REFRESH_REQUIRED", 409)
        part = next((c for c in option["recipe"]["components"] if c["type"] == kind), None)
        if part is None:
            raise ModuleError("Không tìm thấy thành phần.", "COMPONENT_NOT_FOUND", 404)
        return meal, option, part

    @staticmethod
    def alternatives(user_id, meal_type, option_id, kind, expected):
        meal, option, part = MealPlannerV4.selected_component(user_id, meal_type, option_id, kind, expected)
        recipe = option["recipe"]
        candidates = [d for d in eligible(recipe["preferences"], meal_type) if d["type"] == kind and d["dish_id"] != part["dish_id"]]
        if not candidates:
            raise ModuleError("Chưa có món khác cùng nhóm phù hợp điều kiện tránh món.", "NO_REPLACEMENT", 422)
        candidates.sort(key=lambda d: (-score(d, recipe["focus"], recipe["preferences"]), d["dish_id"]))
        # Show up to 15 DIFFERENT, database-backed foods of the same group.
        # The full list already passed meal-time, active/edible and avoid filters.
        # Keep the AI's three priority picks independent from the UI list; AI
        # downtime must not shrink the alternatives to three choices.
        maximum_choices = 15
        available_count = len(candidates)
        catalog_choices = candidates[:maximum_choices]
        # A list of known catalog items is a database lookup, not a creative
        # generation task. The old code waited for Gemini (~18 seconds in the
        # reported case) to rank three items, despite having a list of 15.
        # Return immediately and deterministically; the actual swap endpoint
        # still validates group, amount and saved avoid preferences.
        catalog_choices = [
            {**d, "reason": "Món cùng nhóm, được lọc theo khẩu vị đã lưu."}
            for d in catalog_choices
        ]
        return {"choices": catalog_choices[:3], "catalog_choices": catalog_choices,
                "max_choices": maximum_choices, "available_count": available_count,
                "component_group": kind, "revision": meal["revision"],
                "source": "catalog", "fallback_reason": None}

    @staticmethod
    def replace_component(user_id, meal_type, option_id, kind, expected, dish_id, grams):
        NutritionV4Repository.require_schema()
        MealRepository.release_read_transaction()
        MealRepository.lock_user(user_id)
        meal, option, old = MealPlannerV4.selected_component(user_id, meal_type, option_id, kind, expected)
        recipe = copy.deepcopy(option["recipe"])
        recipe["preferences"] = v4_preferences(recipe["preferences"], meal_type)
        available = {d["dish_id"]: d for d in catalog_dishes(meal_type)}
        replacement = component(dish_id, grams, kind, catalog=available)
        if violates(available[dish_id], recipe["preferences"]):
            raise ModuleError("Món thay thế vi phạm điều kiện tránh món.", "AVOID_CONFLICT", 422)
        if old["dish_id"] == dish_id and old["grams"] == replacement["grams"]:
            raise ModuleError("Bạn chưa thay đổi món hoặc khẩu phần.", "NO_CHANGE")
        recipe["components"] = [replacement if c["type"] == kind else c for c in recipe["components"]]
        recipe["change"] += 1
        from app.services.nutrition_service import NutritionService
        previous_quality = recipe.get("calorie_adjustment", {})
        target = previous_quality.get("target_kcal")
        if target is None:
            target = MealService.profile(user_id)["meal_targets"][meal_type]
        goals = previous_quality.get("macro_targets") or NutritionService.macro_targets(target)
        # Unchanged foods retain their frozen nutrient profiles, even if today's
        # catalog changed. Missing reference data is explicit rather than invented.
        quality_catalog = copy.deepcopy(available)
        for part in recipe["components"]:
            if part["dish_id"] in quality_catalog and part.get("nutrition_per_100g"):
                item = quality_catalog[part["dish_id"]]
                item["calories_per_100g"] = part["nutrition_per_100g"]["calories"]
                item["macros_per_100g"] = {k: part["nutrition_per_100g"][k] for k in ("carbs", "protein", "fat", "fiber")}
        recipe["calorie_adjustment"] = quality_metadata(recipe["components"], quality_catalog, target, goals,
            option["calories"], False)
        title = "Kết hợp: " + ", ".join(c["name"] for c in recipe["components"][:3])
        updated = option_from_recipe(recipe, title, "Đã thay một thành phần; tổng dinh dưỡng tính lại từ catalog.", option_source(option))
        db.session.execute(text("UPDATE MealComponentDish SET DishName=:name WHERE OptionId=:oid AND ComponentType=:kind"),
            {"name": updated["components"][kind], "oid": option_id, "kind": kind})
        db.session.execute(text("UPDATE MealNutrition SET TotalCalories=:cal,CarbsGrams=:carbs,ProteinGrams=:protein,FatGrams=:fat,FiberGrams=:fiber WHERE OptionId=:oid"),
            {"cal": updated["calories"], **updated["macros"], "oid": option_id})
        db.session.execute(text("UPDATE NutritionMealDetails SET RecipeJson=:recipe,Version=Version+1 WHERE OptionId=:oid"),
            {"recipe": json.dumps(recipe, ensure_ascii=False, allow_nan=False), "oid": option_id})
        db.session.execute(text("UPDATE MealOption SET Title=:title,DigestibilityNote=:note WHERE OptionId=:oid"),
            {"title": updated["title"], "note": updated["digestibility"], "oid": option_id})
        result = MealRepository.load(user_id, today(), meal_type)
        db.session.commit()
        return result


def option_source(option):
    # Keep provider provenance rather than claiming this arithmetic called AI.
    return "gemini" if option["recipe"].get("provider_source") == "gemini" else "fallback"
