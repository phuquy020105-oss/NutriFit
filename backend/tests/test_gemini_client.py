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
