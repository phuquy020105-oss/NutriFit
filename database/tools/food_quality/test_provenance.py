import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from build_provenance import normalize_nin, normalized_usda
from extract_nin import extract


class ProvenanceBoundaryTest(unittest.TestCase):
    def test_total_carbohydrate_is_explicitly_converted_with_same_record_fiber(self):
        n = {"carbs_per_100g": {"value": "28.17"}, "fiber_per_100g": {"value": "0.4"}}
        result = normalized_usda("carbs_per_100g", n)
        self.assertEqual("27.77", result["value"])
        self.assertEqual("CALCULATED", result["status"])
        self.assertEqual("28.17", result["inputs"]["total_carbohydrate_g"])
        n["fiber_per_100g"]["value"] = None
        self.assertIsNone(normalized_usda("carbs_per_100g", n)["value"])

    def test_published_assumed_zero_is_estimated_not_a_new_measured_zero(self):
        result = normalized_usda("fiber_per_100g", {"fiber_per_100g": {
            "value": "0", "derivation": {"description": "Assumed zero"}}})
        self.assertEqual(("0", "ESTIMATED"), (result["value"], result["status"]))
        self.assertIsNone(normalized_usda("fiber_per_100g", {})["value"])

    def test_mext_estimated_marker_propagates_to_nutrient_and_derived_carbs(self):
        n = {"fiber_per_100g": {"value": "0.0", "derivation": {"description": "Estimated by source"}},
             "carbs_per_100g": {"value": "85.3"}}
        self.assertEqual("ESTIMATED", normalized_usda("fiber_per_100g", n)["status"])
        self.assertEqual("LOW", normalized_usda("carbs_per_100g", n)["confidence"])

    def test_nin_ambiguous_definition_and_conflicting_species_are_not_normalized(self):
        record = {"nutrients": {"fiber_per_100g": {"value": "7", "definition_verified": False},
            "calories_per_100g": {"value": "30", "definition_verified": True}}}
        self.assertIsNone(normalize_nin("fiber_per_100g", record, "F059")["value"])
        self.assertIsNone(normalize_nin("calories_per_100g", record, "F058")["value"])
        self.assertEqual("30", normalize_nin("calories_per_100g", record, "F034")["value"])

    def test_nin_hash_units_null_and_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = {"code": "test", "_id": "id", "name_vi": "test", "energy": 0,
                "nutrition": [{"key": "protein", "value": None, "unit": "g"},
                    {"key": "total-lipid-fat", "value": 0, "unit": "g"}]}
            def save():
                payload = json.dumps({"data": [row]}).encode()
                (root / "response.json").write_bytes(payload)
                (root / "retrieval-index.json").write_text(json.dumps([{
                    "file": "response.json", "sha256": hashlib.sha256(payload).hexdigest(),
                    "url": "https://viendinhduong.vn/api/fe/foodNatunal/getPageFoodData", "retrieved_date": "2026-10-19"}]))
            save()
            found = extract(root)["test"]["nutrients"]
            self.assertIsNone(found["protein_per_100g"]["value"])
            self.assertEqual("0", found["fat_per_100g"]["value"])
            (root / "response.json").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                extract(root)
            row["nutrition"][1]["unit"] = "mg"
            save()
            with self.assertRaisesRegex(ValueError, "unit"):
                extract(root)

    def test_staging_contains_all_foods_nutrients_without_implicit_approval(self):
        root = Path(__file__).resolve().parents[3]
        data = json.loads((root / "database/staging/food-quality-v1/food-provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(82, len(data["foods"]))
        self.assertEqual(410, sum(len(r["nutrients"]) for r in data["foods"]))
        self.assertEqual(82, len({r["food_ref"] for r in data["foods"]}))
        for food in data["foods"]:
            self.assertFalse(food["production_change_approved"])
            for nutrient in food["nutrients"].values():
                self.assertEqual(nutrient["value"] is None, nutrient["status"] == "MISSING")
                if nutrient["status"] == "MISSING":
                    self.assertIsNone(nutrient["delta_from_current"])


if __name__ == "__main__":
    unittest.main()
