import copy
import hashlib
import json
import unittest
from PIL import Image
from build_demo_release import OUT, ROOT, STAGING, validate_demo

class DemoReleaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads((OUT/'catalog-C-qualified.json').read_text(encoding='utf-8'))
        cls.p=json.loads((OUT/'demo-provenance.json').read_text(encoding='utf-8'))
    def test_complete_demo_is_documented_without_claiming_analytical_verification(self):
        validate_demo(self.c,self.p)
        self.assertEqual(500,self.p['summary']['nutrient_facts'])
        self.assertEqual(103,self.p['summary']['statuses']['ESTIMATED'])
        self.assertEqual(12,self.p['summary']['whole_food_legacy_estimates'])
        self.assertNotIn('VERIFIED',self.p['summary']['statuses'])
        self.assertFalse(self.c['quality_gate']['production_write_permitted'])
        strict=json.loads((STAGING/'food-provenance.json').read_text(encoding='utf-8'))
        self.assertEqual(47,strict['summary']['statuses']['MISSING'])
        for f in self.p['foods']:
            for n in f['nutrients'].values():
                if n['status']=='ESTIMATED':self.assertTrue(n['confidence']);self.assertTrue(n['method'])
    def test_unknown_values_and_false_status_or_undocumented_estimates_fail(self):
        for value in (None,'NaN','Infinity','-1','1001'):
            c=copy.deepcopy(self.c);p=copy.deepcopy(self.p)
            c['foods'][0]['nutrients']['calories_per_100g']=value;p['foods'][0]['nutrients']['calories_per_100g']['value']=value
            with self.assertRaises(Exception):validate_demo(c,p)
        p=copy.deepcopy(self.p);p['foods'][0]['nutrients']['calories_per_100g']['method']=''
        with self.assertRaises(ValueError):validate_demo(self.c,p)
    def test_original_recipes_and_their_30_images_are_unchanged(self):
        old=json.loads((OUT/'catalog-A-baseline.json').read_text(encoding='utf-8'))
        for a,c in zip(old['recipes'],self.c['recipes'][:30]):
            for key in ('ref','name','meal_type','base_servings','instructions','prep_minutes','image_url','ingredients'):
                self.assertEqual(a[key],c[key])
        images=json.loads((ROOT/'docs/nutrition/recipe-image-sources.json').read_text(encoding='utf-8'))['images']
        for i in images:self.assertEqual(i['sha256'],hashlib.sha256((ROOT/'src/main/webapp'/i['image_url'].lstrip('/')).read_bytes()).hexdigest())
    def test_all60_runtime_webps_and_new30_reviewed_mappings(self):
        images=json.loads((OUT/'runtime-image-manifest.json').read_text(encoding='utf-8'))['images']
        self.assertEqual(30,len(images));self.assertEqual(30,len({i['sha256'] for i in images}))
        by_ref={i['recipe_ref']:i for i in images}
        for r in self.c['recipes']:
            path=ROOT/'src/main/webapp'/r['image_url'].lstrip('/')
            with Image.open(path) as image:
                image.load();self.assertEqual('WEBP',image.format);self.assertEqual((800,450),image.size)
            if r['ref'] in by_ref:
                i=by_ref[r['ref']];self.assertEqual(r['image_url'],i['image_url'])
                self.assertEqual(i['sha256'],hashlib.sha256(path.read_bytes()).hexdigest());self.assertIn('AI',i['disclosure'])
    def test_all30_portions_reviewed_without_invented_measurements_or_gram_reduction(self):
        p=json.loads((OUT/'demo-portion-review.json').read_text(encoding='utf-8'))
        self.assertEqual(30,p['educational_portions_accepted']);self.assertFalse(p['pending_practical_plate_review'])
        self.assertEqual(0,p['measured_servings'])
        for r in p['recipes']:self.assertIsNone(r['final_served_mass_measured_g']);self.assertEqual([],r['gram_changes']);self.assertTrue(r['demo_portion_note'])
    def test_production_entry_requires_exact_manifest_flag_and_no_destructive_sql(self):
        text=(ROOT/'database/tools/food_quality/CatalogReleaseMigration.java').read_text(encoding='utf-8')
        self.assertIn('--go-live-approved-manifest',text);self.assertIn('PRODUCTION_CHANGED_SINCE_BACKUP_STOP',text)
        self.assertIn('EXACT_APPROVED_MANIFEST_SHA_REQUIRED',text)
        for forbidden in ('DROP TABLE','DROP DATABASE','TRUNCATE','DELETE FROM','FOREIGN_KEY_CHECKS=0'):
            self.assertNotIn(forbidden,text)

if __name__=='__main__':unittest.main()
