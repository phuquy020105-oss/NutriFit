import os
import unittest
from unittest.mock import Mock, patch

from app.ai.api_key_pool import (
    get_gemini_api_keys,
    is_invalid_api_key_response,
    is_invalid_api_key_exception,
)


class ApiKeyPoolTests(unittest.TestCase):
    def test_reads_primary_and_extras_unique_up_to_ten(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": " primary ",
            "GEMINI_API_KEYS": "secondary,primary;third\nfourth",
        }, clear=False):
            self.assertEqual(
                get_gemini_api_keys(),
                ["primary", "secondary", "third", "fourth"],
            )

    def test_maximum_ten_keys(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "key0",
            "GEMINI_API_KEYS": ",".join(f"key{i}" for i in range(1, 15)),
        }, clear=False):
            keys = get_gemini_api_keys()
            self.assertEqual(len(keys), 10)
            self.assertEqual(keys[-1], "key9")

    def test_does_not_classify_quota_as_bad_key(self):
        response = Mock(status_code=403)
        response.json.return_value = {"error": {"message": "Quota exceeded for this project"}}
        response.text = "Quota exceeded for this project"
        self.assertFalse(is_invalid_api_key_response(response))

    def test_detects_explicit_bad_key_response(self):
        response = Mock(status_code=400)
        response.json.return_value = {"error": {"message": "API key not valid. Please pass a valid API key."}}
        response.text = "API key not valid"
        self.assertTrue(is_invalid_api_key_response(response))

    def test_detects_auth_error_exception(self):
        exc = RuntimeError("API key was reported as leaked")
        exc.code = 403
        self.assertTrue(is_invalid_api_key_exception(exc))

    def test_does_not_rotate_on_quota_exception(self):
        exc = RuntimeError("Quota exceeded: RESOURCE_EXHAUSTED")
        exc.code = 403
        self.assertFalse(is_invalid_api_key_exception(exc))


if __name__ == "__main__":
    unittest.main()
