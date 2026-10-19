"""Reproducible educational catalog, with estimates explicitly separated from source facts.
Does not connect to any database or authorize production writes.
"""
import copy
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
from build_provenance import ROOT, STAGING, KEYS
from validate_quality import validate_recipe

OUT = STAGING / 'release'

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

# These are explicit formulation/state assumptions from the owner-approved initial
# educational design, not new assays or undisclosed substitutions for missing facts.
ESTIMATES = {
 'F005': 'Rice-only boiled banh canh, drained: approximately 24% available starch and 1.5% protein in a water-rich noodle. Excludes high-tapioca formulations; compare cooked rice-noodle source candidates. Moisture/recipe variation is substantial.',
 'F011': 'Unseasoned lean beef boiled, edible meat: assumed 29g protein and 10g retained fat per100g. Energy210kcal is an approximate cooked lean-meat estimate, not raw-weight conversion. Carbohydrate and fiber zero are explicit animal-muscle composition assumptions.',
 'F016': 'Unseasoned steamed lean minced pork: assumed28g protein and9g retained fat per100g. Not the fattier cooked ground-pork proxy; animal-muscle carbohydrate/fiber zero are explicit assumptions.',
 'F025': 'Boiled peeled shrimp: legacy99-100kcal,24g protein,.2g carbohydrate,.3g fat comparison consistent with USDA175180 cooked shrimp. Fiber0 assumes shell/chitin removed; this is an estimated physiological absence, not missing-data substitution. Species/additives vary.',
 'F026': 'Filtered freshwater-crab edible meat/curd, no shell: assumed18g protein,2g fat,1g available carbohydrate per100g; approximate95kcal. Fiber0 explicitly excludes shell/chitin. Egg/tofu-added commercial curd is outside this definition.',
 'F044': 'Raw edible lemongrass core, minced and consumed: legacy99kcal,1.8g protein,20g available carbohydrate,.5g fat,2.5g fiber. Watery discarded stems are excluded. Published partial lemongrass records do not establish fiber; fiber is a low-confidence fibrous-herb estimate.',
 'F055': 'Raw peeled giant-taro/dọc-mùng edible stem, not mint leaf: very watery stem proxy,14kcal,.7g protein,1.8g available carbohydrate,.1g fat,1.5g fiber. No incorrect mint-species match or raw-to-cooked factor.',
 'F057': 'Raw rice-paddy herb: low-confidence fresh leafy-herb analog25kcal,2g protein,2g available carbohydrate,.4g fat,2.5g fiber. Exact species not analytically matched; amounts in recipes are small.',
 'F058': 'Raw culantro: low-confidence leafy-herb whole-vector estimate25/2/2/.4/2.5. INMU499 confirms Eryngium identity but lacks available carbohydrate/fiber; those gaps are NOT claimed measured. Legacy vector retained rather than mixing incompatible assay methods.',
 'F074': 'Filtered unseasoned final pork stock: assumed2g dissolved protein,1g fat,.5g carbohydrate per100g, approximate20kcal. Fiber0 assumes solids removed. Bones and cooked meat are not counted twice; concentration is not measured.',
 'F077': 'Filtered annatto carrier oil, consumed: assumed100g fat per100g,884kcal like refined vegetable oil. Protein/carbohydrate/fiber0 explicitly assume seed solids removed. Carrier oil must not be added a second time.',
 'F080': 'Prepared fried shallot includes absorbed oil: approximate32g fat,6g protein,45g available carbohydrate,6g fiber per100g,500kcal. Macro+fiber mass89g leaves11g water/ash;4P+4C+9F+2fiber=504kcal, consistent with rounded500. This is an estimated dry fried product; do not count internal frying oil again.'
}
PORTIONS = {
 'R044': 'Large complete lunch:160g cooked chicken,270g raw cabbage/carrot,350g boiled sweet potato,30g peanut plus dressing. Multiple plated components;854g is large but plausible for an active adult, not a universal portion. No calories-driven reduction.',
 'R048': 'Large complete lunch:300g cooked rice,160g cooked beef,330g cooked vegetables plus sauce. Vegetables are water-rich;825g represents a full plate and side dish. Appropriate catalog option for higher-energy targets.',
 'R050': 'Large vegetarian lunch:300g rice,150g tofu,150g corn,100g eggs,120g broccoli plus sauce. Corn is a second starch; this is deliberately a substantial full meal, not a small rice bowl. Fixed835g design retained for higher targets.',
 'R054': 'Complete dinner with250g brown rice,130g chicken,120g cooked mung beans,270g lotus/broccoli plus sesame/sauce.808g includes several water-rich sides; a large but feasible whole meal, not a single small bowl.',
 'R057': 'Plant-based complete dinner:220g rice,220g tofu,330g cooked mushroom/green bean plus retained sauce.823g includes high-water vegetables and tofu; no excessive frying oil. Large plate with side dish.',
 'R060': 'Complete dinner:260g cooked rice,150g beef,360g lotus/broccoli plus sauce.808g is a large meal with separate vegetable sides; retained as a high-energy option, without manipulating grams for scoring.'
}

def validate_demo(catalog, provenance):
    foods={f['ref']:f for f in catalog['foods']}
    if len(foods)!=100 or len(catalog['recipes'])!=60:
        raise ValueError('Expected100foods/60recipes')
    if Counter(r['meal_type'] for r in catalog['recipes'])!=dict(BREAKFAST=20,LUNCH=20,DINNER=20):
        raise ValueError('Expected20 recipes per meal')
    if len({f['name'].casefold() for f in foods.values()})!=100 or len({r['name'].casefold() for r in catalog['recipes']})!=60:
        raise ValueError('Duplicate names')
    facts={f['food_ref']:f for f in provenance['foods']}
    for ref, food in foods.items():
        evidence=facts[ref]
        for key in KEYS:
            fact=evidence['nutrients'][key]
            value=Decimal(str(fact['value']))
            if not value.is_finite() or value<0 or value>(1000 if key==KEYS[0] else 100):
                raise ValueError('Invalid value '+ref+'/'+key)
            if fact['status'] not in {'MATCHED','CALCULATED','ESTIMATED'} or not fact.get('method'):
                raise ValueError('Unqualified or undocumented fact')
            if str(fact['value'])!=str(food['nutrients'][key]):
                raise ValueError('Catalog/provenance mismatch')
            if fact['status']=='ESTIMATED' and not fact.get('confidence'):
                raise ValueError('Estimate without confidence')
        if sum(Decimal(food['nutrients'][k]) for k in KEYS[1:])>Decimal('100.5'):
            raise ValueError('Invalid mass balance')
    for recipe in catalog['recipes']:
        validate_recipe(recipe,foods)
        if recipe['base_servings']!='1.00' or not recipe['image_url'].startswith('/assets/images/recipes/'):
            raise ValueError('Invalid portion/image')
        path=ROOT/'src/main/webapp'/recipe['image_url'].lstrip('/')
        if not path.is_file():raise ValueError('Missing runtime image')
    if sum(len(r['ingredients']) for r in catalog['recipes'])!=607:
        raise ValueError('Expected607 links')


def build():
    OUT.mkdir(exist_ok=True)
    baseline=load(OUT/'catalog-A-baseline.json')
    strict=load(STAGING/'food-provenance.json')
    c=copy.deepcopy(load(STAGING/'catalog-C-exploratory.json'))
    strict_by={f['food_ref']:f for f in strict['foods']}
    legacy={f['ref']:f for f in baseline['foods']}
    new={f['ref']:f for f in load(STAGING/'new-food-provenance.json')['foods']}
    evidence=[]
    for food in c['foods']:
        ref=food['ref']
        if ref in new:
            row=new[ref]
            nutrients=copy.deepcopy(row['nutrient_provenance'])
            source={'url':row['source_record']['source_url'],'release':row['source_release'],'archive_sha256':row['source_archive_sha256']}
        else:
            old=strict_by[ref]
            source=copy.deepcopy(old['source'])
            if old['source_complete']:
                nutrients=copy.deepcopy(old['nutrients'])
            else:
                if ref not in ESTIMATES:raise ValueError('No documented estimate '+ref)
                nutrients={k:dict(value=legacy[ref]['nutrients'][k],status='ESTIMATED',confidence='LOW',
                    method=ESTIMATES[ref],unit='KCAL' if k==KEYS[0] else 'G',basis='100g edible portion in stated state',
                    original_source_value=None,not_analytical=True) for k in KEYS}
                source={'type':'OWNER_ACCEPTED_EDUCATIONAL_FORMULATION_OR_ANALOG',
                    'design_reference':'docs/nutrition/vietnamese-food-nutrition-data.md',
                    'baseline_sha256':sha(ROOT/'database/seed/vietnamese_catalog.json'),
                    'partial_official_comparison':source,
                    'uncertainty':'LOW confidence; variety, water, cut, formulation and cooking vary; not a medical database'}
        # A source measured a different variety/formulation. Its raw values remain
        # traceable, but applying the whole vector to our food is an estimate.
        if ref in {'F024','F032','F075','F076','F082'}:
            for fact in nutrients.values():
                fact['source_status']=fact['status']
                fact['source_method']=fact['method']
                fact['status']='ESTIMATED'
                fact['confidence']='LOW'
                fact['method']='Educational category/process/variety analog; all5values kept from one source, not an identified product assay. '+source['match_differences']
            source['demo_qualification']='Analog estimate accepted for course demo2026-10-20; earlier production-block wording is a historical source-only gate, not an analytical claim'
        food['nutrients']={k:nutrients[k]['value'] for k in KEYS}
        food['status']='EDUCATIONAL_ESTIMATE' if any(n['status']=='ESTIMATED' for n in nutrients.values()) else 'MATCHED_OR_CALCULATED_REFERENCE'
        food['provenance_file']='demo-provenance.json'
        food.pop('production_change_approved',None)
        evidence.append(dict(food_ref=ref,name=food['name'],state=food['state'],source=source,nutrients=nutrients))
    jobs=load(STAGING/'image-generation-jobs.json')['recipes']
    assets=[]
    by_ref={r['ref']:r for r in c['recipes']}
    for job in jobs:
        source=ROOT/job['staging_path'];destination=ROOT/'src/main/webapp/assets/images/recipes'/job['filename']
        if sha(source)!=job['sha256']:raise ValueError('Staged image checksum changed')
        if destination.exists() and sha(destination)!=job['sha256']:raise ValueError('Runtime image conflict')
        if not destination.exists():shutil.copyfile(source,destination)
        recipe=by_ref[job['recipe_ref']]
        recipe['image_url']='/assets/images/recipes/'+job['filename']
        recipe['image_status']='REVIEWED_AI_ILLUSTRATION'
        recipe['portion_status']='REVIEWED_EDUCATIONAL_STANDARD_PORTION'
        recipe.pop('production_change_approved',None)
        assets.append(dict(recipe_ref=job['recipe_ref'],image_url=recipe['image_url'],sha256=job['sha256'],
            alt=job['alt'],rights=job['source_rights'],disclosure=job['disclosure']))
    portions=copy.deepcopy(load(STAGING/'recipe-portion-review.json'))
    portions['status']='DEMO_PORTIONS_REVIEWED_NOT_KITCHEN_MEASURED'
    portions['pending_practical_plate_review']=[]
    portions['educational_portions_accepted']=30
    portions['measured_servings']=0
    for r in portions['recipes']:
        r['demo_review_status']='ACCEPTED_WITH_EXPLICIT_STATE_MASS_AND_RETENTION_ASSUMPTIONS'
        r['demo_portion_note']=PORTIONS.get(r['recipe_ref'],r['note'])
        r['gram_changes']=[]
    c['version']='nutrifit-educational-60-v1-20261020'
    c['purpose']='Educational nutrition estimates for a Web Programming demo; not medical advice'
    c['quality_gate']=dict(status='DEMO_DATA_QUALIFIED',production_write_permitted=False,
        qualification='Documented MATCHED/CALCULATED/ESTIMATED facts accepted by owner2026-10-20; no laboratory/VERIFIED requirement',
        unresolved_strict_source_facts=47,explicit_whole_food_estimates=12,standard_servings='1.00',
        baseline_sha256=sha(ROOT/'database/seed/vietnamese_catalog.json'))
    statuses=Counter(n['status'] for f in evidence for n in f['nutrients'].values())
    provenance=dict(status='EDUCATIONAL_QUALIFIED_NOT_ANALYTICAL_VERIFICATION',foods=evidence,
        summary=dict(foods=100,nutrient_facts=500,statuses=dict(statuses),
            foods_with_any_estimate=sum(any(n['status']=='ESTIMATED' for n in f['nutrients'].values()) for f in evidence),
            whole_food_legacy_estimates=12,strict_source_missing_facts_retained_in_separate_audit=47),
        references=['food-provenance.json','new-food-provenance.json','../../../../docs/nutrition/vietnamese-food-nutrition-data.md'])
    validate_demo(c,provenance)
    b=copy.deepcopy(c);b['foods']=b['foods'][:82];b['recipes']=b['recipes'][:30]
    b['version']='nutrifit-educational-30-references-v1-20261020'
    write(OUT/'catalog-B-qualified.json',b);write(OUT/'catalog-C-qualified.json',c)
    write(OUT/'demo-provenance.json',provenance);write(OUT/'demo-portion-review.json',portions)
    write(OUT/'runtime-image-manifest.json',dict(images=assets,status='PACKAGED_REVIEWED_AI_ILLUSTRATIONS'))
    print('DEMO_DATA_QUALIFIED100/60/607;30newassets; estimates='+str(statuses['ESTIMATED'])+'of500facts; production writes still not authorized')

if __name__=='__main__':build()
