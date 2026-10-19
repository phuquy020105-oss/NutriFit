"""Fail-closed structural/source/normalization checks. Technical PASS is not production approval."""
import argparse
from collections import defaultdict, Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from build_provenance import build, KEYS, ROOT, STAGING

SHARED_SOURCE_GROUPS={frozenset(("F001","F081")):"Cooked plain white rice proxy for broken rice; grain/hydration difference retained",
    frozenset(("F002","F003","F004")):"Generic cooked rice noodle proxy; width/moisture/fermentation differences require release review"}

def validate_food(food):
    if set(food["nutrients"])!=set(KEYS):raise ValueError("Five nutrient contract required")
    values={}
    for key,n in food["nutrients"].items():
        if n.get("unit")!=("KCAL" if key=="calories_per_100g" else "G") or n.get("basis")!="100 g edible portion":
            raise ValueError("Nutrient unit/basis mismatch")
        if (n["value"] is None)!=(n["status"]=="MISSING"):raise ValueError("Missing/status mismatch")
        if n["value"] is None:continue
        value=Decimal(n["value"])
        if not value.is_finite() or value<0 or value>(Decimal(1000) if key==KEYS[0] else Decimal(100)):
            raise ValueError("Out-of-range per100g nutrient")
        if food.get("source") is None or not n.get("original_source_value") or not n.get("method"):
            raise ValueError("Nutrient lacks source evidence/method")
        if n["original_source_value"].get("unit")!=n["unit"]:raise ValueError("Source unit mismatch")
        values[key]=value
    if all(k in values for k in KEYS[1:]) and sum(values[k] for k in KEYS[1:])>Decimal('100.5'):
        raise ValueError("Protein+availablecarbs+fat+fiber exceed100g beyond rounding tolerance")
    source=food.get("source") or {}
    description=source.get('description') or source.get('english_name') or source.get('name_en') or ''
    if food['state']=='CHÍN' and re.search(r'\b(raw|uncooked)\b',description,re.I):raise ValueError("Raw source for cooked food")
    if food['state']=='SỐNG' and re.search(r'\b(boiled|steamed|fried|roasted|cooked)\b',description,re.I):raise ValueError("Cooked source for raw food")

def validate_duplicates(foods):
    groups=defaultdict(list)
    for f in foods:
        s=f.get('source')
        if s:groups[(s.get('publisher') or s.get('source'),str(s.get('record_id') or s.get('source_id')))].append(f['food_ref'])
    for refs in groups.values():
        if len(refs)>1 and frozenset(refs) not in SHARED_SOURCE_GROUPS:raise ValueError("Unreviewed duplicate source mapping")

def validate_recipe(recipe,foods):
    if recipe['meal_type'] not in ('BREAKFAST','LUNCH','DINNER') or Decimal(recipe['base_servings'])!=1:
        raise ValueError("Invalid fixed standard serving/meal type")
    used=set()
    for i in recipe['ingredients']:
        grams=Decimal(i['quantity_grams']);ref=i['food_ref']
        if ref not in foods or ref in used or not grams.is_finite() or grams<=0 or grams>Decimal('9999999.999'):
            raise ValueError("Invalid/duplicate ingredient grams/reference")
        used.add(ref)
    if not used or not recipe.get('instructions'):raise ValueError("Empty recipe/preparation")

def run(cache):
    actual=json.loads((STAGING/'food-provenance.json').read_text(encoding='utf-8'))
    rebuilt=build(cache)
    if actual!=rebuilt:raise ValueError("Provenance is not reproducible from reviewed source archive/records/decisions")
    for food in actual['foods']:validate_food(food)
    validate_duplicates(actual['foods'])
    catalog=json.loads((STAGING/'catalog-C-exploratory.json').read_text(encoding='utf-8'))
    foods={f['ref']:f for f in catalog['foods']}
    if len(foods)!=100 or len(catalog['recipes'])!=60:raise ValueError("Catalog counts")
    for recipe in catalog['recipes']:validate_recipe(recipe,foods)
    if len({r['ref'] for r in catalog['recipes']})!=60 or len({r['name'].casefold() for r in catalog['recipes']})!=60:raise ValueError("Duplicate recipes")
    if Counter(r['meal_type'] for r in catalog['recipes'])!=dict(BREAKFAST=20,LUNCH=20,DINNER=20):raise ValueError("Meal balance")
    if sum(len(r['ingredients']) for r in catalog['recipes'])!=607:raise ValueError("Link count")
    review=json.loads((STAGING/'recipe-portion-review.json').read_text(encoding='utf-8'))
    if review['catalog_sha256']!=hashlib.sha256((STAGING/'catalog-C-exploratory.json').read_bytes()).hexdigest():raise ValueError("Stale serving review")
    print('PASS technical checks:82/410 provenance reproducible;100/60/607 structure; reviewed duplicates/state/units/normalization. Production qualification still gated.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-cache',type=Path,required=True);run(p.parse_args().source_cache)
