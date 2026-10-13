"""Secure Gemini API key configuration and invalid-key failover.

Fallback is deliberately restricted to authentication/key-rejection errors.
429 RESOURCE_EXHAUSTED and other quota/rate-limit failures are never used as a
reason to switch keys, because doing so can evade provider usage limits.
"""
from __future__ import annotations

import os
import re
from typing import Iterable

_MAX_KEYS = 10
_INVALID_KEY_MARKERS = (
    "api key not valid",
    "api key is invalid",
    "invalid api key",
    "api_key_invalid",
    "key was reported as leaked",
    "reported as leaked",
    "api key expired",
    "key expired",
    "api key blocked",
    "api_key_service_blocked",
    "invalid x-goog-api-key",
)
_QUOTA_MARKERS = (
    "quota",
    "resource_exhausted",
    "rate limit",
    "rate_limit",
    "billing",
    "requests per minute",
    "tokens per minute",
    "daily limit",
)


def get_gemini_api_keys(max_keys: int = _MAX_KEYS) -> list[str]:
    """Return up to 10 unique keys. GEMINI_API_KEY remains the primary key.

    GEMINI_API_KEYS accepts comma, semicolon, or newline separated values.
    Whitespace and blank entries are ignored; keys are never logged.
    """
    raw_values = [os.getenv("GEMINI_API_KEY", "")]
    raw_values.extend(re.split(r"[,;\r\n]+", os.getenv("GEMINI_API_KEYS", "")))
    result: list[str] = []
    seen: set[str] = set()
    try:
        cap = max(1, min(int(max_keys), _MAX_KEYS))
    except (TypeError, ValueError):
        cap = _MAX_KEYS
    for value in raw_values:
        key = (value or "").strip().strip('"').strip("'").strip()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
            if len(result) >= cap:
                break
    return result


def _status_code(obj) -> int | None:
    for attr in ("status_code", "code", "status"):
        value = getattr(obj, attr, None)
        if value is not None:
            try:
                # Some SDK status values are enums or textual names.
                number = int(value)
                if 100 <= number <= 599:
                    return number
            except (TypeError, ValueError):
                pass
    response = getattr(obj, "response", None)
    value = getattr(response, "status_code", None)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _looks_like_invalid_key(text: str) -> bool:
    normalized = (text or "").lower()
    if any(marker in normalized for marker in _QUOTA_MARKERS):
        return False
    return any(marker in normalized for marker in _INVALID_KEY_MARKERS)


def is_invalid_api_key_response(response) -> bool:
    """True only when an HTTP response explicitly indicates a rejected key."""
    status = getattr(response, "status_code", None)
    try:
        status = int(status)
    except (TypeError, ValueError):
        return False
    if status == 401:
        return True
    if status not in (400, 403):
        return False
    parts = []
    try:
        parts.append(str(response.json()))
    except Exception:
        pass
    try:
        parts.append(str(response.text))
    except Exception:
        pass
    return _looks_like_invalid_key(" ".join(parts))


def is_invalid_api_key_exception(exc: BaseException) -> bool:
    """Classify SDK auth/key errors without treating quota errors as key failures."""
    status = _status_code(exc)
    if status == 401:
        return True
    if status not in (400, 403):
        return False
    parts = [str(exc)]
    for attr in ("message", "details", "body"):
        value = getattr(exc, attr, None)
        if value is not None:
            parts.append(str(value))
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            parts.append(str(response.text))
        except Exception:
            pass
        try:
            parts.append(str(response.json()))
        except Exception:
            pass
    return _looks_like_invalid_key(" ".join(parts))
