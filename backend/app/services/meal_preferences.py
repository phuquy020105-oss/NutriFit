"""Request-only preferences; deterministic filtering before AI or fallback.

Avoid applies to declared recipe ingredients, not medical allergy guarantees.
Unsupported food terms are rejected instead of silently ignored.
"""
import re
import unicodedata
from app.services.module_errors import ModuleError


def normalized(value):
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())


ALIASES = {
    "fish": ("fish", "ca"), "seafood": ("seafood", "hai san", "tom", "shrimp"),
    "egg": ("egg", "eggs", "trung"), "milk": ("milk", "dairy", "sua", "sua chua"),
    "chicken": ("chicken", "ga"), "beef": ("beef", "bo", "thit bo"),
    "pork": ("pork", "heo", "lon", "thit heo"), "soy": ("soy", "dau phu", "dau nanh", "tofu"),
    "wheat": ("wheat", "lua mi", "banh mi"), "oats": ("oats", "yen mach"),
    "rice": ("rice", "com", "gao", "xoi"), "noodles": ("noodles", "bun", "pho", "mien", "banh cuon"),
    "banana": ("banana", "chuoi"), "sweet_potato": ("sweet_potato", "khoai lang"),
}
LOOKUP = {normalized(alias): key for key, aliases in ALIASES.items() for alias in aliases}


def food_terms(value, field):
    if not isinstance(value, list) or len(value) > 15:
        raise ModuleError(f"{field} phải là danh sách tối đa 15 thực phẩm.")
    result = []
    for term in value:
        if not isinstance(term, str) or not 1 <= len(term.strip()) <= 40:
            raise ModuleError(f"{field} có thực phẩm không hợp lệ.")
        key = LOOKUP.get(normalized(term))
        if key is None:
            raise ModuleError("Thực phẩm chưa được hỗ trợ; dùng cá, hải sản, trứng, sữa, gà, bò, heo, đậu phụ, bánh mì, yến mạch, cơm, bún/phở, chuối hoặc khoai lang.", "UNSUPPORTED_PREFERENCE")
        if key not in result:
            result.append(key)
    return result


def validate_preferences(data, meal_type):
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ModuleError("preferences phải là JSON object.")
    allowed = {"avoid", "dislikes", "prefer", "preferEasy", "maxPrepMinutes"}
    if set(data) - allowed:
        raise ModuleError("Tùy chọn chưa hỗ trợ; chưa có dữ liệu ngân sách.", "UNSUPPORTED_PREFERENCE")
    result = {key: food_terms(data[key], key) for key in ("avoid", "dislikes", "prefer") if key in data}
    if "preferEasy" in data:
        if type(data["preferEasy"]) is not bool:
            raise ModuleError("preferEasy phải là boolean.")
        result["preferEasy"] = data["preferEasy"]
    if "maxPrepMinutes" in data:
        minutes = data["maxPrepMinutes"]
        if type(minutes) is not int or not 1 <= minutes <= 120:
            raise ModuleError("maxPrepMinutes phải là số nguyên từ 1 đến 120.")
        result["maxPrepMinutes"] = minutes
    if meal_type != "breakfast" and (result.get("preferEasy") or "maxPrepMinutes" in result):
        raise ModuleError("Hiện chỉ có ước tính thời gian chuẩn bị cho bữa sáng.", "UNSUPPORTED_PREFERENCE")
    return {key: value for key, value in result.items() if value}


def ingredients(template):
    if "ingredients" in template:
        values = set(template["ingredients"])
        if "bread" in values:
            values.add("wheat")
        if "yogurt" in values:
            values.add("milk")
        if "tofu" in values:
            values.add("soy")
        # Reference noodles are treated as rice-based for conservative avoidance.
        if "noodles" in values:
            values.add("rice")
        return values
    # Lunch/dinner totals stay unchanged; tags follow the existing dish names.
    names = [name for name, grams in template["components"].values()]
    text = " ".join(names).lower()
    values = set()
    for term, key in (("thịt heo", "pork"), ("bò", "beef"), ("gà", "chicken"),
                      ("cá", "fish"), ("tôm", "seafood"), ("trứng", "egg"), ("chuối", "banana"),
                      ("sữa", "milk"), ("đậu phụ", "soy"), ("bánh mì", "wheat"), ("yến mạch", "oats"),
                      ("cơm", "rice"), ("gạo", "rice"), ("xôi", "rice"), ("khoai lang", "sweet_potato"),
                      ("phở", "noodles"), ("bún", "noodles"), ("miến", "noodles"), ("bánh cuốn", "noodles")):
        if re.search(r"\b" + re.escape(term.strip()) + r"\b", text):
            values.add(key)
    # Fish avoidance also removes seafood; seafood avoidance includes fish.
    if "fish" in values:
        values.add("seafood")
    if "noodles" in values:
        values.add("rice")
    return values


def cached_compatible(meal, catalog, preferences):
    """Verify new preferences before acknowledging an existing cached set."""
    if not preferences:
        return True
    # Ranking preferences are not persisted. A cached set cannot prove that it
    # was ranked for ease; require an explicit refresh rather than ignore it.
    if preferences.get("preferEasy"):
        return False
    try:
        eligible = {t["template_id"] for t in filter_candidates(list(catalog.values()), preferences)}
    except ModuleError:
        return False
    for option in meal["options"]:
        template = catalog.get(option["title"])
        if template is None or template["template_id"] not in eligible:
            return False
        parts = {c["type"]: c["name"] for c in option.get("components", [])}
        if set(parts) != set(template["components"]):
            return False  # Unknown/missing legacy components cannot be verified.
        for kind, (name, grams) in template["components"].items():
            name = template.get("component_recipes", {}).get(kind, (name,))[0]
            if not parts[kind].startswith(name):
                return False
        persisted = {"components": {kind: (name, 0) for kind, name in parts.items()},
                     "prep_minutes": template.get("prep_minutes")}
        if violates(persisted, preferences):
            return False
    return True


def violates(template, preferences):
    avoided = set(preferences.get("avoid", []))
    if "fish" in avoided:
        avoided.add("seafood")
    if avoided & ingredients(template):
        return True
    maximum = preferences.get("maxPrepMinutes")
    return maximum is not None and (template.get("prep_minutes") is None or template["prep_minutes"] > maximum)


def filter_candidates(candidates, preferences):
    allowed = [t for t in candidates if not violates(t, preferences)]
    if len(allowed) < 3:
        raise ModuleError("Không đủ 3 thực đơn phù hợp điều kiện cần tránh/thời gian. Hãy điều chỉnh điều kiện.", "INSUFFICIENT_MENUS", 422)
    # Soft dislikes/preferences may be relaxed only when fewer than 3 remain.
    liked = [t for t in allowed if not set(preferences.get("dislikes", [])) & ingredients(t)]
    if len(liked) >= 3:
        allowed = liked
    preferred = [t for t in allowed if set(preferences.get("prefer", [])) & ingredients(t)]
    if len(preferred) >= 3:
        allowed = preferred
    return allowed


def fallback_choices(candidates, preferred, preferences, target):
    order = {t["template_id"]: index for index, t in enumerate(preferred)}
    def score(t):
        tags = ingredients(t)
        return (len(set(preferences.get("dislikes", [])) & tags),
                -len(set(preferences.get("prefer", [])) & tags),
                t.get("prep_minutes", 0) if preferences.get("preferEasy") else 0,
                order.get(t["template_id"], 100), abs(t["calories"] - target), t["template_id"])
    sorted_items = sorted(candidates, key=score)
    chosen, families = [], set()
    for item in sorted_items:
        if item["family"] not in families:
            chosen.append(item)
            families.add(item["family"])
        if len(chosen) == 3:
            break
    for item in sorted_items:
        if len(chosen) == 3:
            break
        if item not in chosen:
            chosen.append(item)
    return chosen


def replacement_request(text, preferences, meal_type):
    """A small explicit food-command parser, not a general conversation engine."""
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 250:
        raise ModuleError("request phải có từ 1 đến 250 ký tự.")
    command = normalized(text)
    merged = {**validate_preferences(preferences, meal_type)}
    found = False
    consumed = []
    for phrase, key in (("khong thich", "dislikes"), ("tranh", "avoid"), ("khong an", "avoid"),
                        ("doi sang", "prefer"), ("uu tien", "prefer")):
        # Exact supported food terms; do not silently ignore an unknown instruction.
        for match in re.finditer(r"\b" + phrase + r"\s+([a-z_ ]+?)(?=,|\.|\bnhung\b|\bva\b|\bhay\b|\bgan\b|\bkhoang\b|$)", command):
            food = match.group(1).strip()
            values = food_terms([food], key)
            merged[key] = list(dict.fromkeys(merged.get(key, []) + values))
            found = True
            consumed.append(match.span())
    if not found:
        raise ModuleError("Dùng yêu cầu như: Tôi không thích cá, hãy đổi sang gà nhưng vẫn gần 700 kcal.", "UNSUPPORTED_REPLACEMENT")
    # Reject an unrecognized second instruction instead of silently ignoring it.
    remainder = list(command)
    for start, end in consumed:
        remainder[start:end] = " " * (end - start)
    filler = {"toi", "minh", "hay", "nhung", "van", "gan", "khoang", "kcal", "va", "giup", "cho", "voi", "lam", "on"}
    if any(token not in filler and not token.isdigit() for token in re.findall(r"\w+", "".join(remainder))):
        raise ModuleError("Yêu cầu có phần chưa hỗ trợ. Mỗi cụm dùng một thực phẩm; danh sách cần tránh có thể nhập ở ô riêng.", "UNSUPPORTED_REPLACEMENT")
    if len(re.findall(r"\b\d{2,5}\s*kcal\b", command)) > 1:
        raise ModuleError("Chỉ dùng một mục tiêu kcal cho lần đổi món.")
    kcal_match = re.search(r"\b(\d{2,5})\s*kcal\b", command)
    target = int(kcal_match.group(1)) if kcal_match else None
    if target is not None and not 100 <= target <= 3000:
        raise ModuleError("Mục tiêu đổi món phải trong khoảng 100–3000 kcal.")
    return merged, target
