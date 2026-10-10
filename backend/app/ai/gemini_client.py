"""Gemini REST adapter: select reference menu IDs with validated structured JSON."""
import json
import re
import threading
import time
from collections import OrderedDict
import requests


class AIUnavailable(Exception):
    """Safe error code only; provider bodies and credentials are never exposed."""


class GeminiClient:
    def __init__(self, api_key="", model="", timeout=10, retries=1, cooldown=30):
        self.api_key, self.model = api_key, model
        self.timeout, self.retries, self.cooldown = timeout, retries, cooldown
        self._lock = threading.Lock()
        self._last_request = OrderedDict()

    def rank(self, candidates, meal_type, target_kcal, user_id, context=None):
        if not self.api_key or not self.model:
            raise AIUnavailable("not_configured")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.model):
            raise AIUnavailable("invalid_model")
        now = time.monotonic()
        with self._lock:
            previous = self._last_request.get(user_id)
            if previous is not None and now - previous < self.cooldown:
                raise AIUnavailable("cooldown")
            self._last_request[user_id] = now
            self._last_request.move_to_end(user_id)
            if len(self._last_request) > 2048:
                self._last_request.popitem(last=False)
        schema = {"type": "object", "properties": {"choices": {"type": "array", "items": {
            "type": "object", "properties": {"template_id": {"type": "string"},
                                               "reason": {"type": "string"}},
            "required": ["template_id", "reason"]}}}, "required": ["choices"]}
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
        payload = {"contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
                   "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema,
                                        "temperature": 0.3, "maxOutputTokens": 1024}}
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(endpoint, headers={"x-goog-api-key": self.api_key},
                                         json=payload, timeout=self.timeout, allow_redirects=False)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.retries:
                        continue
                    raise AIUnavailable("provider_busy")
                if response.status_code != 200:
                    raise AIUnavailable("provider_error")
                # Limit response parsing; do not log the request, response, or exception text.
                if len(response.content) > 65536:
                    raise AIUnavailable("invalid_output")
                body = response.json()
                candidate = body["candidates"][0]
                if candidate.get("finishReason") != "STOP":
                    raise AIUnavailable("invalid_output")
                text = "".join(part.get("text", "") for part in candidate["content"]["parts"]
                               if not part.get("thought"))
                return self.validate_choices(json.loads(text), candidates)
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, AttributeError):
                if attempt == self.retries:
                    raise AIUnavailable("invalid_or_unavailable") from None
        raise AIUnavailable("provider_error")

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
