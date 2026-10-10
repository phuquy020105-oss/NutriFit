"""Gemini REST adapter: select reference menu IDs with validated structured JSON."""
import json
import re
import threading
import time
from collections import OrderedDict
import requests


class AIUnavailable(Exception):
    """Safe error code only; provider bodies and credentials are never exposed."""

    def __init__(self, code, http_status=None):
        super().__init__(code)
        self.http_status = http_status


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
                    raise AIUnavailable("invalid_output")
                candidate = response.json()["candidates"][0]
                if candidate.get("finishReason") != "STOP":
                    raise AIUnavailable("invalid_output")
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
        from app.data.vietnamese_menus import materialize
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

    def compose(self, catalog, meal_type, target_kcal, user_id, focus, macro_targets):
        component = {"type": "object", "properties": {"type": {"type": "string"},
            "dish_id": {"type": "string"}, "grams": {"type": "number"}}, "required": ["type", "dish_id", "grams"]}
        choice = {"type": "object", "properties": {"title": {"type": "string"}, "reason": {"type": "string"},
            "components": {"type": "array", "items": component}}, "required": ["title", "reason", "components"]}
        return self._request({"task": "Tạo đúng 3 thực đơn Việt khác nhau từ catalog. Chỉ trả ID món, gram, tiêu đề và lý do tiếng Việt. "
            "Không tự tạo dinh dưỡng, không HTML, không tư vấn bệnh. Trưa/tối cần CARB, PROTEIN, VEGGIE; sáng cần MAIN. "
            "Gram nằm trong min_grams/max_grams. Không lặp type. Kcal gần mục tiêu; ưu tiên focus và macro_targets.",
            "meal_type": meal_type, "target_kcal": target_kcal, "focus": focus, "macro_targets": macro_targets,
            "catalog": catalog}, {"type": "object", "properties": {"choices": {"type": "array", "items": choice}},
            "required": ["choices"]}, user_id, max_tokens=4096)

    def alternatives(self, catalog, user_id, focus):
        schema = {"type": "object", "properties": {"choices": {"type": "array", "items": {
            "type": "object", "properties": {"dish_id": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["dish_id", "reason"]}}}, "required": ["choices"]}
        return self._request({"task": "Chọn đúng 3 dish_id khác nhau từ catalog để thay một món. Lý do tiếng Việt, không HTML. "
            "Không thay các món khác; không tự tạo kcal/macro.", "focus": focus, "catalog": catalog}, schema, user_id)

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
