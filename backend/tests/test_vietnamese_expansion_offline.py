"""Offline, no Flask/MySQL/SMTP/Gemini required; validate expansion input."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'setup'))
from import_vietnamese_expansion import get_batch,folded_name,db_review
from seed_nutrition_catalog import load_seed


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed=get_batch()
        cls.records=cls.seed['dishes']

    def test_no_duplicate_names_ids_or_baseline_overlap(self):
        baseline=load_seed()['dishes']
        self.assertEqual(len(self.records),291)
        self.assertEqual(len({r['dish_id'] for r in self.records}),291)
        self.assertFalse({folded_name(r['name']) for r in self.records}&{folded_name(r['name']) for r in baseline})

    def test_balanced_catalog_for_v4(self):
        roles=Counter(r['type'] for r in self.records)
        self.assertGreaterEqual(roles['MAIN'],60)
        self.assertGreaterEqual(roles['PROTEIN'],65)
        self.assertGreaterEqual(roles['VEGGIE'],50)
        self.assertGreaterEqual(roles['SOUP'],30)
        self.assertTrue(all(r['preparation_state']=='ready' and r['estimated'] for r in self.records))
        self.assertTrue(all('breakfast' in r['meal_types'] for r in self.records if r['type']=='MAIN'))
        self.assertTrue(all({'lunch','dinner'}<=set(r['meal_types']) for r in self.records if r['type']=='PROTEIN'))

    def test_energy_and_ingredients_are_consistent(self):
        for r in self.records:
            with self.subTest(dish_id=r['dish_id']):
                macros=r['macros_per_100g']
                total=4*macros['protein']+4*macros['carbs']+9*macros['fat']
                self.assertAlmostEqual(total,r['calories_per_100g'],delta=.015)
                self.assertLess(r['calories_per_100g'],900)
                self.assertLessEqual(r['max_grams'],1600)
                self.assertLessEqual(r['min_grams'],r['reference_grams'])
                self.assertLessEqual(r['reference_grams'],r['max_grams'])
                self.assertEqual(r['macros_per_100g']['fiber'],None)
                self.assertTrue(r['provenance']['limitations'])
                self.assertTrue(r['ingredients'])

    def test_illustrative_food_does_not_mislabel_main_ingredient(self):
        lookup={r['name']:r for r in self.records}
        self.assertIn('snail',lookup['Bún ốc']['ingredients'])
        self.assertIn('guava',lookup['Nước ép ổi không đường']['ingredients'])
        self.assertIn('galangal',lookup['Cá trắm kho riềng']['ingredients'])
        self.assertIn('amaranth',lookup['Rau dền xào tỏi']['ingredients'])
        self.assertIn('duck',lookup['Bún măng vịt']['ingredients'])

    def test_import_check_is_read_only_and_idempotent_logic(self):
        class EmptyRepo:
            @staticmethod
            def dishes(active=False):return []
        class AlreadyRepo:
            @staticmethod
            def dishes(active=False):return self.records
        first=db_review(self.records,EmptyRepo)
        self.assertEqual(first['to_insert'],291)
        self.assertEqual(first['before'],0)
        second=db_review(self.records,AlreadyRepo)
        self.assertEqual(second['to_insert'],0)
        self.assertEqual(second['already_matching'],291)

if __name__=='__main__':unittest.main()
