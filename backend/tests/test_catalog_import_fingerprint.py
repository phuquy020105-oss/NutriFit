"""Driver-container fingerprint regressions; disposable SQLite SELECT only."""
import sys
import unittest
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from sqlalchemy import create_engine, select, literal, Numeric, DateTime, Date, LargeBinary
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "setup"))
from expand_demo_food_catalog import digest_rows


class FingerprintTests(unittest.TestCase):
    def test_select_one_row_tuple_and_list_equivalent(self):
        engine = create_engine("sqlite:///:memory:")
        try:
            with engine.connect() as c:
                row = c.execute(select(literal(1).label("value"))).one()
                self.assertEqual(digest_rows([row]), digest_rows([(1,)]))
                self.assertEqual(digest_rows([row]), digest_rows([[1]]))
        finally:
            engine.dispose()

    def test_row_preserves_decimal_datetime_date_bytes_null_unicode(self):
        values = (Decimal("12.3400"), datetime(2026, 10, 13, 8, 9, 10, 123456),
                  date(2026, 10, 13), b"\x00\xffABC", None, "Rau muống · đậu phụ")
        engine = create_engine("sqlite:///:memory:")
        try:
            with engine.connect() as c:
                row = c.execute(select(literal(values[0], Numeric(12, 4)), literal(values[1], DateTime()),
                    literal(values[2], Date()), literal(values[3], LargeBinary()), literal(None), literal(values[5]))).one()
                self.assertEqual(tuple(row), values)
                self.assertEqual(digest_rows([row]), digest_rows([values]))
        finally:
            engine.dispose()

    def test_each_real_value_change_changes_hash(self):
        original = (Decimal("12.3400"), datetime(2026, 10, 13, 8), b"\x00ABC", None, "Thịt heo", 1)
        changed = (Decimal("12.3500"), datetime(2026, 10, 13, 9), b"\x00ABD", 0, "Thịt bò", 2)
        for i, value in enumerate(changed):
            row = list(original); row[i] = value
            self.assertNotEqual(digest_rows([original]), digest_rows([row]))

    def test_record_order_ignored_but_columns_and_duplicates_significant(self):
        self.assertEqual(digest_rows([(1,"A"),(2,"B")]), digest_rows([(2,"B"),(1,"A")]))
        self.assertNotEqual(digest_rows([(1,"A")]), digest_rows([("A",1)]))
        self.assertNotEqual(digest_rows([(1,"A")]), digest_rows([(1,"A"),(1,"A")]))

    def test_mapping_cursor_requires_explicit_column_order(self):
        row = {"name":"Đậu phụ", "value":Decimal("1.00")}
        self.assertEqual(digest_rows([row], ["value","name"]), digest_rows([(Decimal("1.00"),"Đậu phụ")]))
        with self.assertRaises(ValueError):
            digest_rows([row])

    def test_binary_containers_are_equivalent(self):
        raw=b"\x00\xffabc"
        self.assertEqual(digest_rows([(raw,)]), digest_rows([(memoryview(raw),)]))
        self.assertEqual(digest_rows([(raw,)]), digest_rows([(bytearray(raw),)]))

    def test_time_null_unicode_and_empty_dataset(self):
        row=(time(8,9,10),None,"Đậu phộng")
        self.assertEqual(digest_rows([tuple(row)]),digest_rows([list(row)]))
        self.assertNotEqual(digest_rows([]),digest_rows([row]))
        self.assertNotEqual(digest_rows([(None,)]),digest_rows([("NULL",)]))
