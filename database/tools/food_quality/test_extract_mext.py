import os
from pathlib import Path
import unittest
from extract_mext import extract, parse_amount


class MextSymbolsTest(unittest.TestCase):
    def test_trace_and_missing_are_not_zero(self):
        for symbol in ("Tr", "(Tr)", "-", None):
            self.assertIsNone(parse_amount(symbol)[0])
        self.assertEqual(("0.0", "ESTIMATED"), parse_amount("(0)"))
        self.assertEqual(("0.0", "PUBLISHED"), parse_amount("0"))

    def test_excel_binary_tail_is_normalized_to_documented_presentation(self):
        self.assertEqual(("17.9", "PUBLISHED"), parse_amount("17.899999999999999"))
        self.assertEqual(("346", "PUBLISHED"), parse_amount("346", energy=True))
        for value in ("-1", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                parse_amount(value)


@unittest.skipUnless(os.environ.get("MEXT_SOURCE_ARCHIVE"), "NOT RUN: set MEXT_SOURCE_ARCHIVE to official2015 English workbook")
class MextOfficialWorkbookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foods = extract(Path(os.environ["MEXT_SOURCE_ARCHIVE"]))

    def test_only_main_table_is_indexed_and_published_symbols_are_retained(self):
        self.assertEqual(2191, len(self.foods))
        starch = self.foods["02028"]
        self.assertEqual("346", starch["nutrients"]["calories_per_100g"]["value"])
        self.assertEqual("(0)", starch["nutrients"]["fiber_per_100g"]["original_excel_text"])
        self.assertEqual("ESTIMATED", starch["nutrients"]["fiber_per_100g"]["source_qualifier"])
        self.assertEqual("Q210", starch["nutrients"]["carbs_per_100g"]["source_cell"])

    def test_chinese_chive_is_distinct_from_common_chive_and_food_is_raw(self):
        row = self.foods["06207"]
        self.assertEqual("Chinese chive, leaves, raw", row["description"])
        self.assertEqual("2.7", row["nutrients"]["fiber_per_100g"]["value"])
        self.assertIn("Removed portion: base", row["remarks"])


if __name__ == "__main__":
    unittest.main()
