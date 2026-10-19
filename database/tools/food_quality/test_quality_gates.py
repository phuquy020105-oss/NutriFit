import copy
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image
from validate_quality import validate_food, validate_recipe, validate_duplicates, STAGING

class QualityGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provenance=json.loads((STAGING/'food-provenance.json').read_text(encoding='utf-8'))
        cls.catalog=json.loads((STAGING/'catalog-C-exploratory.json').read_text(encoding='utf-8'))
    def test_rejects_negative_nonfinite_wrong_units_and_missing_evidence(self):
        food=self.provenance['foods'][0]
        for value in ('-1','NaN','Infinity','1001'):
            bad=copy.deepcopy(food);bad['nutrients']['calories_per_100g']['value']=value
            with self.assertRaises(ValueError):validate_food(bad)
        bad=copy.deepcopy(food);bad['nutrients']['fiber_per_100g']['unit']='mg'
        with self.assertRaises(ValueError):validate_food(bad)
        bad=copy.deepcopy(food);bad['source']=None
        with self.assertRaises(ValueError):validate_food(bad)
    def test_raw_source_and_unreviewed_duplicate_mapping_are_rejected(self):
        bad=copy.deepcopy(self.provenance['foods'][0]);bad['source']['english_name']='Rice, raw'
        with self.assertRaises(ValueError):validate_food(bad)
        extra=copy.deepcopy(self.provenance['foods'][0]);extra['food_ref']='F099'
        with self.assertRaises(ValueError):validate_duplicates([self.provenance['foods'][0],extra])
        validate_duplicates(self.provenance['foods'])
    def test_mass_balance_and_invalid_recipe_grams_are_rejected(self):
        bad=copy.deepcopy(self.provenance['foods'][0])
        for key in ('protein_per_100g','fat_per_100g','carbs_per_100g'):bad['nutrients'][key]['value']='40'
        with self.assertRaises(ValueError):validate_food(bad)
        foods={r['ref']:r for r in self.catalog['foods']}
        for quantity in ('0','-1','NaN','10000000'):
            recipe=copy.deepcopy(self.catalog['recipes'][0]);recipe['ingredients'][0]['quantity_grams']=quantity
            with self.assertRaises(ValueError):validate_recipe(recipe,foods)
        recipe=copy.deepcopy(self.catalog['recipes'][0]);recipe['ingredients'][0]['food_ref']='MISSING'
        with self.assertRaises(ValueError):validate_recipe(recipe,foods)
    def test_thirty_images_are_decodable_unique_separate_from_runtime_and_disclosed(self):
        jobs=json.loads((STAGING/'image-generation-jobs.json').read_text(encoding='utf-8'))['recipes']
        self.assertEqual(30,len(jobs));self.assertEqual(30,len({r['recipe_ref'] for r in jobs}))
        self.assertEqual(30,len({r['sha256'] for r in jobs}))
        total=0
        for j in jobs:
            self.assertEqual('VISUALLY_REVIEWED_STAGING_ILLUSTRATION',j['status'])
            self.assertFalse(j['production_approved']);self.assertIsNone(j['image_url'])
            self.assertIn('Ảnh minh họa AI',j['alt']);self.assertTrue(j['prompt']);self.assertTrue(j['source_rights'])
            p=STAGING/'images'/j['filename'];self.assertEqual(j['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
            with Image.open(p) as image:
                image.load();self.assertEqual('WEBP',image.format);self.assertEqual((800,450),image.size)
            total+=p.stat().st_size
        self.assertLess(total,4_000_000)
        self.assertEqual(30,len(list((STAGING/'images').glob('*.webp'))))
        self.assertTrue(all(r.get('image_url') is None for r in self.catalog['recipes'][30:]))
    def test_large_soup_is_not_rejected_only_because_of_total_weight(self):
        review=json.loads((STAGING/'recipe-portion-review.json').read_text(encoding='utf-8'))
        rows={r['recipe_ref']:r for r in review['recipes']}
        self.assertEqual(24,review['staging_method_qualified'])
        for ref in ('R047','R053'):
            self.assertTrue(rows[ref]['nutritional_method_qualified_for_staging'])
            self.assertEqual('200.00',rows[ref]['separately_added_water_to_be_consumed_g'])
            self.assertIsNone(rows[ref]['final_served_mass_measured_g'])
        self.assertEqual(6,len(review['pending_practical_plate_review']))
        self.assertTrue(all(not r['production_change_approved'] for r in rows.values()))

class ProductionHoldTest(unittest.TestCase):
    def test_production_mode_fails_before_modifying_release_artifacts(self):
        from prepare_release import build
        release=STAGING/'release'
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in release.glob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError,'PRODUCTION_NOT_READY'):
            build(production=True)
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in release.glob('*') if p.is_file()}
        self.assertEqual(before,after)
        self.assertFalse((release/'catalog-B-qualified.json').exists())
        self.assertFalse((release/'catalog-C-qualified.json').exists())

if __name__=='__main__':unittest.main()
