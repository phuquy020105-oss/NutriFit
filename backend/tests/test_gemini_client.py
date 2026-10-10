import json
import secrets
import unittest
from unittest.mock import Mock, patch
import requests
from app.ai.gemini_client import GeminiClient, AIUnavailable
from app.data.vietnamese_menus import templates


class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.catalog = templates("lunch")
        self.client = GeminiClient(secrets.token_urlsafe(24), "model-for-contract-test", retries=1)
        self.choices = {"choices": [{"template_id": item["template_id"], "reason": "Mâm cơm đa dạng."}
                                    for item in self.catalog[:3]]}

    def response(self, data=None, status=200):
        response = Mock(status_code=status, content=b"small-test-response")
        response.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {
            "parts": [{"text": json.dumps(self.choices if data is None else data)}]}}]}
        return response

    def test_no_configuration_never_calls_network(self):
        with patch("app.ai.gemini_client.requests.post") as post:
            with self.assertRaises(AIUnavailable):
                GeminiClient().rank(self.catalog, "lunch", 800, 1)
            post.assert_not_called()

    def test_success_and_private_server_header(self):
        with patch("app.ai.gemini_client.requests.post", return_value=self.response()) as post:
            result = self.client.rank(self.catalog, "lunch", 800, 991)
            self.assertEqual(len(result), 3)
            call = post.call_args
            self.assertEqual(call.kwargs["headers"]["x-goog-api-key"], self.client.api_key)
            self.assertNotIn(self.client.api_key, call.args[0])
            self.assertFalse(call.kwargs["allow_redirects"])
            prompt = json.loads(call.kwargs["json"]["contents"][0]["parts"][0]["text"])
            self.assertNotIn("user_id", prompt)
            self.assertNotIn("email", prompt)

    def test_transient_failure_retries_once(self):
        with patch("app.ai.gemini_client.requests.post", side_effect=[self.response(status=429), self.response()]) as post:
            self.assertEqual(len(self.client.rank(self.catalog, "lunch", 800, 1)), 3)
            self.assertEqual(post.call_count, 2)

    def test_timeout_bounded_and_redacted(self):
        with patch("app.ai.gemini_client.requests.post", side_effect=requests.Timeout("private-test-marker")) as post:
            with self.assertRaises(AIUnavailable) as error:
                self.client.rank(self.catalog, "lunch", 800, 1)
            self.assertEqual(post.call_count, 2)
            self.assertNotIn("private-test-marker", str(error.exception))

    def test_unauthorized_does_not_retry_or_expose_body(self):
        with patch("app.ai.gemini_client.requests.post", return_value=self.response(status=401)) as post:
            with self.assertRaises(AIUnavailable) as error:
                self.client.rank(self.catalog, "lunch", 800, 1)
            self.assertEqual(str(error.exception), "provider_error")
            self.assertEqual(post.call_count, 1)

    def test_cooldown_prevents_duplicate_provider_calls(self):
        with patch("app.ai.gemini_client.requests.post", return_value=self.response()) as post:
            self.client.rank(self.catalog, "lunch", 800, 1)
            with self.assertRaises(AIUnavailable) as error:
                self.client.rank(self.catalog, "dinner", 600, 1)
            self.assertEqual(str(error.exception), "cooldown")
            self.assertEqual(post.call_count, 1)

    def test_bad_model_never_calls_network(self):
        with patch("app.ai.gemini_client.requests.post") as post:
            self.client.model = "../../other-host"
            with self.assertRaises(AIUnavailable):
                self.client.rank(self.catalog, "lunch", 800, 1)
            post.assert_not_called()

    def test_invalid_choices_are_rejected(self):
        for bad in ({}, {"choices": []}, {"choices": self.choices["choices"] * 2},
                    {"choices": [self.choices["choices"][0]] * 3},
                    {"choices": [{"template_id": "missing", "reason": "test"}] * 3},
                    {"choices": [{**self.choices["choices"][0], "reason": "<script>"}, *self.choices["choices"][1:]]},
                    {"choices": [None, *self.choices["choices"][1:]]}):
            with self.assertRaises(AIUnavailable):
                GeminiClient.validate_choices(bad, self.catalog)

    def test_truncated_and_oversized_output_falls_back(self):
        response = self.response()
        response.json.return_value["candidates"][0]["finishReason"] = "MAX_TOKENS"
        with patch("app.ai.gemini_client.requests.post", return_value=response):
            with self.assertRaises(AIUnavailable):
                self.client.rank(self.catalog, "lunch", 800, 2)
        response = self.response()
        response.content = b"x" * 65537
        with patch("app.ai.gemini_client.requests.post", return_value=response):
            with self.assertRaises(AIUnavailable):
                self.client.rank(self.catalog, "lunch", 800, 3)

    def test_breakfast_context_contains_estimates_without_identity(self):
        catalog = templates("breakfast")
        choices = {"choices": [{"template_id": t["template_id"], "reason": "Bữa sáng đa dạng, khẩu phần tham khảo."} for t in catalog[:3]]}
        with patch("app.ai.gemini_client.requests.post", return_value=self.response(choices)) as post:
            result = self.client.rank(catalog, "breakfast", 500, 7654,
                                      {"goal": "lose", "preferences": {"avoid": ["fish"]}, "user_id": 7654, "email": "private@example.invalid"})
        self.assertEqual(len(result), 3)
        prompt = json.loads(post.call_args.kwargs["json"]["contents"][0]["parts"][0]["text"])
        self.assertEqual(prompt["goal"], "lose")
        self.assertEqual(prompt["macro_targets"], {"carbs": 56.2, "protein": 31.2, "fat": 16.7})
        self.assertEqual(prompt["preferences"]["avoid"], ["fish"])
        self.assertNotIn("private@example.invalid", json.dumps(prompt))
        self.assertNotIn("7654", json.dumps(prompt))
        self.assertTrue(all("estimated_calories" in t and "estimated_macros" in t for t in prompt["candidates"]))

    def test_filtered_catalog_may_have_fewer_families_but_unique_ids(self):
        catalog = [t for t in self.catalog if t["family"] == "poultry"]
        choices = {"choices": [{"template_id": t["template_id"], "reason": "Ưu tiên món gà theo sở thích."} for t in catalog[:3]]}
        self.assertEqual(len(GeminiClient.validate_choices(choices, catalog)), 3)

    def test_provider_cannot_supply_nutrient_values(self):
        bad = {"choices": [{**self.choices["choices"][0], "calories": 1}, *self.choices["choices"][1:]]}
        with self.assertRaises(AIUnavailable):
            GeminiClient.validate_choices(bad, self.catalog)

    def test_server_errors_are_bounded(self):
        with patch("app.ai.gemini_client.requests.post", return_value=self.response(status=500)) as post:
            with self.assertRaises(AIUnavailable) as error:
                self.client.rank(self.catalog, "lunch", 800, 1)
            self.assertEqual(str(error.exception), "provider_busy")
            self.assertEqual(post.call_count, 2)

    def test_two_remaining_families_still_require_available_diversity(self):
        catalog = [t for t in self.catalog if t["family"] != "fish_seafood"]
        poultry = [t for t in catalog if t["family"] == "poultry"]
        choices = {"choices": [{"template_id": t["template_id"], "reason": "Theo sở thích."} for t in poultry[:3]]}
        with self.assertRaises(AIUnavailable):
            GeminiClient.validate_choices(choices, catalog)

    def test_v4_transport_uses_structured_catalog_prompt_without_identity_or_sampling(self):
        from app.data.food_catalog import DISHES
        with patch("app.ai.gemini_client.requests.post", return_value=self.response({"choices": []})) as post:
            self.client.compose(list(DISHES), "lunch", 800, 7654321, "muscle_gain", {"protein": 50})
        payload = post.call_args.kwargs["json"]
        prompt = json.loads(payload["contents"][0]["parts"][0]["text"])
        self.assertEqual(prompt["focus"], "muscle_gain")
        self.assertEqual(prompt["macro_targets"], {"protein": 50})
        self.assertNotIn("7654321", json.dumps(prompt))
        self.assertNotIn(self.client.api_key, json.dumps(payload))
        config = payload["generationConfig"]
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertEqual(config["maxOutputTokens"], 4096)
        self.assertFalse({"temperature", "topP", "topK"} & set(config))

    def test_provider_error_exposes_only_status_and_never_response_body(self):
        for status in (400, 403, 404, 429):
            with self.subTest(status=status), patch("app.ai.gemini_client.requests.post", return_value=self.response(status=status)) as post:
                with self.assertRaises(AIUnavailable) as error:
                    self.client.alternatives([], status, "maintain")
                self.assertEqual(error.exception.http_status, status)
                self.assertEqual(post.call_count, 2 if status == 429 else 1)
                self.assertIn(str(error.exception), ("provider_error", "provider_busy"))
