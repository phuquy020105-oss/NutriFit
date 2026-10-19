import copy
import json
import os
from pathlib import Path
import unittest
from extract_thai import extract, extract_page, number, normalize

class ThaiSourceTest(unittest.TestCase):
    def page(self, changes=None):
        changes=changes or {}
        values={"Energy, by calculation":("kcal","100","Calculated"),
            "Protein, total":("g","10","Analysed"), "Fat, total":("g","2","Analysed"),
            "Carbohydrate, available":("g","7","Calculated"),"Dietary fibre":("g","3","Analysed")}
        values.update(changes)
        table="".join("<tr>"+"".join("<td>"+x+"</td>" for x in [k,u,v,d,"1","-","-","-","","2023"])+"</tr>" for k,(u,v,d) in values.items())
        return ('<div>Food Code:</div><div>F98</div><div>English name:</div><div>Example cooked food</div>'
            '<div>Scientific name:</div><div>Example species</div>Per 100 g edible portion<table>'+table+'</table>')
    def metadata(self):
        return dict(record_id="1020",url="https://inmu.mahidol.ac.th/thaifcd/foodsearch/food_name_result?selected_id=1020&selected_dbcode=STD",
            source_description="Example cooked food",retrieved_date="2026-10-19",sha256="fixture")
    def test_missing_trace_and_negative_values(self):
        for raw in ("-","Tr","", "N/A"): self.assertIsNone(number(raw))
        self.assertEqual("0.0",number("0.0"))
        for raw in ("-1","NaN","Infinity"):
            with self.assertRaises(ValueError): number(raw)
    def test_available_carbs_are_not_subtracted_twice(self):
        record=extract_page(self.page(),self.metadata())
        self.assertEqual("7",normalize("carbs_per_100g",record)["value"])
        self.assertEqual("CALCULATED",normalize("carbs_per_100g",record)["status"])
        self.assertEqual("MATCHED",normalize("protein_per_100g",record)["status"])
    def test_identity_unit_and_basis_fail_closed(self):
        cases=[self.page().replace('Per 100 g edible portion','Per serving'),
            self.page().replace('Example cooked food','A different food'),
            self.page({'Dietary fibre':('mg','3','Analysed')})]
        for page in cases:
            with self.assertRaises(ValueError): extract_page(page,self.metadata())
        meta=self.metadata();meta['record_id']='999'
        with self.assertRaises(ValueError): extract_page(self.page(),meta)
    def test_assumed_zero_and_missing_remain_distinct(self):
        record=extract_page(self.page({'Dietary fibre':('g','0.0','Assumed zero')}),self.metadata())
        self.assertEqual('ESTIMATED',normalize('fiber_per_100g',record)['status'])
        record=extract_page(self.page({'Dietary fibre':('g','-','')}),self.metadata())
        self.assertIsNone(normalize('fiber_per_100g',record)['value'])
    def test_second_energy_field_is_preserved(self):
        record=extract_page(self.page({'Energy, by calculation':('kcal','-',''),
            'Total energy - by calculation':('kcal','41','Calculated')}),self.metadata())
        self.assertEqual('41',record['nutrients']['calories_per_100g']['value'])
        self.assertEqual('Total energy - by calculation',record['nutrients']['calories_per_100g']['source_nutrient_name'])
    @unittest.skipUnless(os.environ.get('THAI_SOURCE_CACHE'),'THAI_SOURCE_CACHE needed for real-source integration')
    def test_real_reviewed_snapshots(self):
        rows=extract(os.environ['THAI_SOURCE_CACHE'])
        self.assertEqual(19,len(rows))
        self.assertEqual('232',rows['149']['nutrients']['calories_per_100g']['value'])
        self.assertEqual('Channa striata',rows['1086']['scientific_name'])
        self.assertEqual('Polygonum odoratum',rows['521']['scientific_name'])
        self.assertIsNone(rows['499']['nutrients']['fiber_per_100g']['value'])
        self.assertEqual('ESTIMATED',normalize('fiber_per_100g',rows['256'])['status'])

if __name__=='__main__': unittest.main()
