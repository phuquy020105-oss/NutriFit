"""Boundary tests plus explicitly marked real official-archive integration checks."""
import os
from pathlib import Path
import tempfile
import unittest
from extract_usda import available_carbohydrate, extract


class ConversionTests(unittest.TestCase):
    def test_missing_is_not_zero(self):
        self.assertIsNone(available_carbohydrate(None, "0"))
        self.assertIsNone(available_carbohydrate("28.17", None))

    def test_fao_conversion_is_exact_and_explicit(self):
        self.assertEqual("27.77", available_carbohydrate("28.17", "0.4"))
        self.assertEqual("0", available_carbohydrate("0", "0"))

    def test_inconsistent_or_invalid_sources_are_rejected(self):
        for total, fiber in [("3", "4"), ("-1", "0"), ("3", "-1"), ("NaN", "1"), ("4", "Infinity")]:
            with self.assertRaises(ValueError):
                available_carbohydrate(total, fiber)

    def test_unreviewed_archive_does_not_get_imported(self):
        with tempfile.TemporaryDirectory() as folder:
            wrong = Path(folder) / "unreviewed.zip"
            wrong.write_bytes(b"not the official dataset")
            with self.assertRaisesRegex(ValueError, "checksum"):
                extract(wrong)


@unittest.skipUnless(os.environ.get("USDA_SOURCE_ARCHIVE"), "Real USDA archive path not configured; integration NOT RUN")
class OfficialArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = extract(Path(os.environ["USDA_SOURCE_ARCHIVE"]))

    def test_all_official_record_counts_match_archive_manifest(self):
        self.assertEqual(7793, self.data["source_food_count"])
        self.assertEqual(644125, self.data["source_nutrient_row_count"])

    def test_source_kcal_is_preserved_instead_of_forcing_449(self):
        n = self.data["foods"]["171478"]["nutrients"]
        self.assertEqual("151", n["calories_per_100g"]["value"])
        self.assertEqual("KCAL", n["calories_per_100g"]["unit"])
        self.assertEqual("1008", n["calories_per_100g"]["nutrient_id"])

    def test_zero_remains_an_explicit_published_assumption(self):
        n = self.data["foods"]["171478"]["nutrients"]["fiber_per_100g"]
        self.assertEqual("0", n["value"])
        self.assertIn("zero", n["derivation"]["description"].lower())
        self.assertTrue(n["source_nutrient_row_id"])

    def test_missing_nutrients_are_reported_not_backfilled(self):
        incomplete = [f for f in self.data["foods"].values() if f["missing_nutrients"]]
        self.assertTrue(incomplete)
        for food in incomplete:
            for key in food["missing_nutrients"]:
                self.assertIsNone(food["nutrients"].get(key, {}).get("value"))


if __name__ == "__main__":
    unittest.main()
