"""Validate previously retrieved public NIN responses, offline; never infer a missing zero."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

KEYS = {"protein": "protein_per_100g", "total-lipid-fat": "fat_per_100g",
        "carbohydrate-by-difference": "carbs_per_100g", "fibre-total-dietary": "fiber_per_100g"}
LOOKUP_URL = "https://viendinhduong.vn/vi/cong-cu-va-tien-ich/gia-tri-dinh-duong-thuc-pham"


def extract(cache):
    cache = Path(cache)
    index = json.loads((cache / "retrieval-index.json").read_text(encoding="utf-8"))
    result = {}
    for item in index:
        relative = Path(item["file"])
        if relative.name != item["file"] or relative.suffix != ".json":
            raise ValueError("Unsafe cache filename")
        payload = (cache / relative).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError("NIN response checksum mismatch")
        response = json.loads(payload, parse_float=Decimal)
        if not isinstance(response.get("data"), list):
            raise ValueError("Unexpected NIN response")
        for row in response["data"]:
            code = str(row["code"])
            def value(raw):
                if raw is None:
                    return None
                number = Decimal(str(raw))
                if not number.is_finite() or number < 0:
                    raise ValueError("Invalid NIN numeric value")
                return format(number, "f")
            nutrients = {"calories_per_100g": {"value": value(row.get("energy")),
                "unit": "KCAL", "source_field": "energy", "definition_verified": True}}
            for raw in row["nutrition"]:
                if raw["key"] not in KEYS:
                    continue
                key = KEYS[raw["key"]]
                if key in nutrients or raw["unit"].lower() != "g":
                    raise ValueError("Duplicate nutrient or unexpected NIN unit")
                nutrients[key] = {"value": value(raw.get("value")), "unit": "G",
                    "source_field": raw["key"], "source_label": raw.get("name_en"),
                    "definition_verified": key not in ("carbs_per_100g", "fiber_per_100g")}
            record = {"source": "Vietnam National Institute of Nutrition public lookup",
                "source_id": row["_id"], "food_code": code, "name_vi": row["name_vi"],
                "name_en": row.get("name_en"), "category": row.get("category"),
                "release": "Not specified by live lookup; snapshot " + item["retrieved_date"],
                "retrieved_date": item["retrieved_date"], "source_url": item["url"],
                "response_sha256": item["sha256"], "basis": "100 g edible portion (public lookup UI)",
                "nutrients": nutrients}
            if code in result:
                comparable = lambda r: {k: v for k, v in r.items() if k not in ("source_url", "response_sha256")}
                if comparable(result[code]) != comparable(record):
                    raise ValueError("Conflicting NIN records for same code")
            else:
                result[code] = record
    return result
