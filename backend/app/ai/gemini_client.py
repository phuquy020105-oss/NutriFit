"""Gemini REST adapter: select reference menu IDs with validated structured JSON."""
import json
import re
import threading
import time
from collections import OrderedDict
import requests


# Shared with the validator; these preserve the existing business limits.
COMPOSITION_RULES = {
    "breakfast": {"required": ("MAIN",), "allowed": ("MAIN", "SIDE", "DRINK", "DESSERT")},
    "lunch": {"required": ("CARB", "PROTEIN", "VEGGIE"), "allowed": ("CARB", "PROTEIN", "VEGGIE", "SOUP", "DESSERT")},
    "dinner": {"required": ("CARB", "PROTEIN", "VEGGIE"), "allowed": ("CARB", "PROTEIN", "VEGGIE", "SOUP", "DESSERT")},
}
COMPOSITION_CALORIE_RANGE = (0.65, 1.35)
COMPOSITION_TEXT_LIMITS = {"title": 140, "reason": 220}


class AIUnavailable(Exception):
    """Safe error code only; provider bodies and credentials are never exposed."""

    def __init__(self, code, http_status=None, diagnostic_code=None):
        super().__init__(code)
        self.http_status = http_status
        self.diagnostic_code = diagnostic_code


class GeminiClient:
    def __init__(self, api_key="", model="", timeout=10, retries=1, cooldown=30):
        self.api_key, self.model = api_key, model
        self.timeout, self.retries, self.cooldown = timeout, retries, cooldown
        self._lock = threading.Lock()
        self._last_request = OrderedDict()

    def rank(self, candidates, meal_type, target_kcal, user_id, context=None):
        self._check_configuration()
        return self.validate_choices(self._request(self._rank_prompt(candidates, meal_type, target_kcal, context),
            {"type": "object", "properties": {"choices": {"type": "array", "items": {
                "type": "object", "properties": {"template_id": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["template_id", "reason"]}}}, "required": ["choices"]}, user_id), candidates)

    def _check_configuration(self):
        if not self.api_key or not self.model:
            raise AIUnavailable("not_configured")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.model):
            raise AIUnavailable("invalid_model")

    def _request(self, prompt, schema, user_id, max_tokens=1024):
        self._check_configuration()
        now = time.monotonic()
        with self._lock:
            previous = self._last_request.get(user_id)
            if previous is not None and now - previous < self.cooldown:
                raise AIUnavailable("cooldown")
            self._last_request[user_id] = now
            self._last_request.move_to_end(user_id)
            if len(self._last_request) > 2048:
                self._last_request.popitem(last=False)
        payload = {"contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
                   "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema,
                                        "maxOutputTokens": max_tokens}}
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(endpoint, headers={"x-goog-api-key": self.api_key},
                                         json=payload, timeout=self.timeout, allow_redirects=False)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.retries:
                        continue
                    raise AIUnavailable("provider_busy", response.status_code)
                if response.status_code != 200:
                    raise AIUnavailable("provider_error", response.status_code)
                if len(response.content) > 65536:
                    raise AIUnavailable("invalid_output", diagnostic_code="RESPONSE_TOO_LARGE")
                candidate = response.json()["candidates"][0]
                if candidate.get("finishReason") != "STOP":
                    raise AIUnavailable("invalid_output", diagnostic_code="INCOMPLETE_RESPONSE")
                value = "".join(part.get("text", "") for part in candidate["content"]["parts"] if not part.get("thought"))
                return json.loads(value)
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, AttributeError):
                if attempt == self.retries:
                    raise AIUnavailable("invalid_or_unavailable") from None
        raise AIUnavailable("provider_error")

    @staticmethod
    def _rank_prompt(candidates, meal_type, target_kcal, context):
        diverse = len({t["family"] for t in candidates}) >= 3
        diversity = "Mỗi nhóm một lựa chọn (sáng: nhanh gọn/món nước/cân bằng; trưa/tối: nhóm đạm)." if diverse else "Ưu tiên đa dạng trong các nhóm còn phù hợp; không chọn thực phẩm bị loại."
        from app.services.food_catalog_service import materialize
        from app.services.meal_preferences import ingredients, validate_preferences
        from app.services.nutrition_service import NutritionService
        context = context or {}
        safe_context = {"goal": context.get("goal") if context.get("goal") in ("lose", "gain", "maintain") else "maintain",
                        "macro_targets": NutritionService.macro_targets(target_kcal),
                        "preferences": validate_preferences(context.get("preferences"), meal_type)}
        prompt = {"task": "Chọn đúng 3 template_id khác nhau. " + diversity + " "
                          "Giải thích ngắn bằng tiếng Việt, không HTML, không chẩn đoán hay tuyên bố điều trị. "
                          "Chỉ chọn từ dữ liệu; không tự tạo món hoặc thay đổi số dinh dưỡng.",
                  "meal_type": meal_type, "target_kcal": target_kcal, **safe_context,
                  "candidates": [{"template_id": item["template_id"], "title": item["title"],
                                  "family": item["family"], "ingredients": sorted(ingredients(item)),
                                  "prep_minutes": item.get("prep_minutes"),
                                  "estimated_calories": materialize(item, target_kcal)["calories"],
                                  "estimated_macros": materialize(item, target_kcal)["macros"]} for item in candidates]}
        return prompt

    def compose(self, catalog, meal_type, target_kcal, user_id, focus, macro_targets, context=None):
        rules = COMPOSITION_RULES[meal_type]
        bounds = [target_kcal * ratio for ratio in COMPOSITION_CALORIE_RANGE]
        component = {"type": "object", "properties": {
            "type": {"type": "string", "enum": list(rules["allowed"])},
            "dish_id": {"type": "string", "enum": [d["dish_id"] for d in catalog]},
            "grams": {"type": "number", "minimum": min(d["min_grams"] for d in catalog),
                      "maximum": max(d["max_grams"] for d in catalog)}}, "required": ["type", "dish_id", "grams"]}
        choice = {"type": "object", "properties": {
            "title": {"type": "string", "description": "Tiếng Việt, một dòng, 1–140 ký tự, không HTML."},
            "reason": {"type": "string", "description": "Tiếng Việt, một dòng, 1–220 ký tự, không HTML."},
            "components": {"type": "array", "minItems": len(rules["required"]),
                           "maxItems": len(rules["allowed"]), "items": component}},
            "required": ["title", "reason", "components"]}
        return self._request({"task": "Tạo đúng 3 thực đơn Việt khác nhau từ catalog. Chỉ trả choices; mỗi choice chỉ có title, reason, components. "
            "Mỗi component chỉ có type, dish_id, grams. Không trả kcal/macro hay field khác; Backend tự tính từ MySQL. "
            "Chỉ dùng dish_id có trong catalog, type phải đúng type của món đó. Có đủ required_roles và chỉ dùng allowed_roles, mỗi type tối đa một món. "
            "Tập dish_id của ba choice phải khác nhau: chỉ đổi gram hoặc tiêu đề không tạo thực đơn khác. Không dùng món bị tránh. "
            "Gram là số, từ min_grams đến max_grams của đúng món, tối đa hai chữ số thập phân. "
            "Ước tính kcal = tổng(calories_per_100g * grams / 100); mỗi choice phải nằm trong calorie_bounds, cố gắng gần target_kcal. "
            "Ưu tiên mỗi choice trong preferred_calorie_bounds (±15%); có thể dùng practical_calorie_bounds (±20%) khi bị giới hạn khẩu phần. "
            "Calorie_bounds chỉ là biên an toàn, không phải mục tiêu để nhắm sát đáy. Target đã phản ánh goal, không tự giảm target cho lose hay tăng target cho gain. "
            "Nếu thiếu kcal, tăng gram trong giới hạn hoặc thêm nhóm tùy chọn; nếu thừa, giảm gram hoặc đổi món. "
            "Dùng calories_per_100g của đúng món, không dùng kcal suy ra từ 4/4/9 hay kiến thức bên ngoài. "
            "Kiểm tra tổng kcal cho cả ba choice trước khi trả; ưu tiên nguồn đạm khác nhau hoặc MAIN khác nhau và tránh ba bộ giống nhau. "
            "Với mỗi choice, bắt đầu gần reference_grams và xét tổng protein, carbs và fat bằng tổng(macros_per_100g * grams / 100), so với macro_targets. "
            "Trước khi tăng gram, kiểm tra trần từng macro = tổng(macros_per_100g * max_grams / 100). Nếu trần vẫn thấp hơn target, tăng gram không thể giải quyết phần thiếu; cần xét đổi món hoặc thêm role tùy chọn còn trống. Trần riêng không chứng minh cả ba macro đồng thời khả thi. "
            "required_roles là tối thiểu, không phải danh sách duy nhất: optional_roles cũng được phép. optional_macro_support chỉ gợi ý món bổ trợ theo lượng macro ở reference_grams, không phải recipe hoặc yêu cầu phải chọn. "
            "Khi thiếu fat, xét món bổ trợ fat trong pool thay vì chỉ chọn CARB/PROTEIN/VEGGIE ít béo rồi tăng đạm để bù kcal. Sau khi đổi/thêm món, kiểm tra lại kcal và cả ba macro; giảm phần khác trong min/max nếu cần, không gây thừa macro khác hay khẩu phần lớn. "
            "Nếu các nhóm bắt buộc đã đủ cân đối, không thêm component dư thừa. Không luôn chọn món fat cao nhất; chọn theo phần thiếu của cả tổ hợp. Ưu tiên gram gần reference_grams, không tăng đồng loạt hoặc ép đúng kcal. "
            "Các macro là mục tiêu mềm, không ngưỡng từ chối. Ưu tiên gần target khi khả thi; đa dạng CARB, PROTEIN/MAIN và thành phần bổ trợ giữa ba bộ, không chỉ đổi gram hay cách chế biến cùng nguồn. "
            "Nếu catalog bị giới hạn, giữ các điều kiện an toàn và mô tả giới hạn ngắn gọn trong reason, không tạo thêm ID hay giá trị dinh dưỡng. "
            "Title 1–140 ký tự, reason 1–220 ký tự; tiếng Việt một dòng, không HTML/ký tự điều khiển, không tư vấn bệnh. Ưu tiên focus và macro_targets.",
            "meal_type": meal_type, "target_kcal": target_kcal, "focus": focus, "macro_targets": macro_targets,
            "required_roles": list(rules["required"]), "allowed_roles": list(rules["allowed"]),
            "optional_roles": [role for role in rules["allowed"] if role not in rules["required"]],
            "optional_macro_support": self.optional_macro_support(catalog, meal_type, macro_targets,
                (context or {}).get("preferences", {})),
            "calorie_bounds": {"minimum": bounds[0], "maximum": bounds[1]}, "text_limits": COMPOSITION_TEXT_LIMITS,
            "preferred_calorie_bounds": {"minimum": round(target_kcal * .85, 2), "maximum": round(target_kcal * 1.15, 2)},
            "practical_calorie_bounds": {"minimum": round(target_kcal * .80, 2), "maximum": round(target_kcal * 1.20, 2)},
            "remaining": (context or {}).get("remaining", {}), "preferences": (context or {}).get("preferences", {}),
            "catalog": self.prompt_catalog(catalog)}, {"type": "object", "properties": {"choices": {
                "type": "array", "minItems": 3, "maxItems": 3, "items": choice}},
            "required": ["choices"]}, user_id, max_tokens=4096)

    def alternatives(self, catalog, user_id, focus):
        schema = {"type": "object", "properties": {"choices": {"type": "array", "items": {
            "type": "object", "properties": {"dish_id": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["dish_id", "reason"]}}}, "required": ["choices"]}
        return self._request({"task": "Chọn đúng 3 dish_id khác nhau từ catalog để thay một món. Lý do tiếng Việt, không HTML. "
            "Không thay các món khác; không tự tạo kcal/macro.", "focus": focus, "catalog": self.prompt_catalog(catalog)}, schema, user_id)

    @staticmethod
    def optional_macro_support(catalog, meal_type, macro_targets, preferences):
        """Small per-role lookup, not assembled recipes or a feasibility promise."""
        from app.services.meal_preferences import violates
        rules = COMPOSITION_RULES[meal_type]
        result = {}
        for role in rules["allowed"]:
            if role in rules["required"]:
                continue
            dishes = [d for d in catalog if d["type"] == role and meal_type in d["meal_types"]
                and d.get("preparation_state") != "raw" and not violates(d, preferences)]
            support = {}
            for macro in ("protein", "carbs", "fat"):
                if macro_targets.get(macro, 0) <= 0:
                    continue
                contribution = lambda d: (d["macros_per_100g"].get(macro) or 0) * d["reference_grams"] / 100
                useful = [d for d in dishes if contribution(d) > 0]
                if useful:
                    best = min(useful, key=lambda d: (-contribution(d), d["dish_id"]))
                    support[macro] = best["dish_id"]
            if support:
                result[role] = support
        return result

    @staticmethod
    def prompt_catalog(catalog):
        # Do not send provenance blobs, history, credentials or user identity.
        return [{key: dish[key] for key in ("dish_id", "name", "type", "min_grams", "max_grams",
            "reference_grams", "calories_per_100g", "macros_per_100g", "ingredients", "meal_types")}
            for dish in catalog]

    @staticmethod
    def validate_choices(data, candidates):
        if not isinstance(data, dict) or set(data) != {"choices"} or not isinstance(data.get("choices"), list) or len(data["choices"]) != 3:
            raise AIUnavailable("invalid_output")
        catalog = {item["template_id"]: item for item in candidates}
        ids, families, result = set(), set(), []
        diverse = len({t["family"] for t in candidates}) >= 3
        for choice in data["choices"]:
            if not isinstance(choice, dict) or set(choice) != {"template_id", "reason"}:
                raise AIUnavailable("invalid_output")
            identifier, reason = choice.get("template_id"), choice.get("reason")
            if not isinstance(identifier, str) or identifier not in catalog or identifier in ids:
                raise AIUnavailable("invalid_output")
            if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 220:
                raise AIUnavailable("invalid_output")
            if any(character in reason for character in "<>\r\n") or any(ord(c) < 32 for c in reason):
                raise AIUnavailable("invalid_output")
            template = catalog[identifier]
            if diverse and template["family"] in families:
                raise AIUnavailable("invalid_output")
            ids.add(identifier)
            families.add(template["family"])
            result.append((template, reason.strip()))
        if len(families) < min(3, len({t["family"] for t in candidates})):
            raise AIUnavailable("invalid_output")
        return result
