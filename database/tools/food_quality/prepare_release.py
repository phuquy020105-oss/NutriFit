"""Prepare a reviewable candidate plan; refuse qualified/production output while gates are closed."""
import argparse
from decimal import Decimal
import hashlib
import json
import re
from pathlib import Path
from build_provenance import ROOT,STAGING

def read(name):return json.loads((STAGING/name).read_text(encoding="utf-8"))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def production_blockers(provenance,review):
    blockers=[]
    if provenance['summary']['statuses'].get('MISSING',0):blockers.append('MISSING_NUTRIENTS:'+str(provenance['summary']['statuses']['MISSING']))
    if review['pending_practical_plate_review']:blockers.append('PENDING_PRACTICAL_PORTIONS:'+','.join(review['pending_practical_plate_review']))
    blockers+=['COMPOUND_PRODUCT_PROXY_REVIEW_REQUIRED:F032,F075,F076,F082',
        'OLD_RECIPE_COOKING_AND_SOURCE_VARIANCE_SIGNOFF_PENDING',
        'FULL_BACKUP_RESTORE_REHEARSAL_NOT_PERFORMED',
        'NEW_ASSETS_NOT_PACKAGED_FOR_PRODUCTION',
        'OWNER_PRODUCTION_WRITE_HOLD_ACTIVE']
    return blockers

def build(production=False):
    provenance=read('food-provenance.json');review=read('recipe-portion-review.json');c=read('catalog-C-exploratory.json')
    b=read('catalog-B-exploratory.json');a=json.loads((ROOT/'database/seed/vietnamese_catalog.json').read_text(encoding='utf-8'))
    blockers=production_blockers(provenance,review)
    if production and blockers:raise ValueError('PRODUCTION_NOT_READY: '+';'.join(blockers))
    image_map={r['ref']:r['image_url'] for r in json.loads((ROOT/'docs/nutrition/recipe-image-sources.json').read_text(encoding='utf-8'))['images']}
    for r in a['recipes']:r['image_url']=image_map[r['ref']]
    old={f['ref']:f for f in a['foods']};changes=[]
    for f in c['foods']:
        previous=old.get(f['ref'])
        if previous is None or previous['nutrients']!=f['nutrients']:
            changes.append(dict(operation='INSERT_FOOD' if previous is None else 'UPDATE_FOOD_IF_EXACT_BEFORE_OR_EQUIVALENT_AFTER',
                food_ref=f['ref'],name=f['name'],before=previous['nutrients'] if previous else None,after=f['nutrients']))
    new=c['recipes'][30:]
    plan=dict(status='STAGING_CANDIDATE_PLAN_NOT_EXECUTABLE_PRODUCTION_MIGRATION',target_database='nutrifitdb',
        production_write_permitted=False,version='food-quality-v1-continuation-20261019',
        preconditions=blockers,before_catalog_sha256=sha(ROOT/'database/seed/vietnamese_catalog.json'),
        after_catalog_sha256=sha(STAGING/'catalog-C-exploratory.json'),provenance_sha256=sha(STAGING/'food-provenance.json'),
        counts=dict(update_foods=sum(r['before'] is not None for r in changes),insert_foods=sum(r['before'] is None for r in changes),
            insert_recipes=len(new),insert_ingredient_links=sum(len(r['ingredients']) for r in new)),
        unchanged_tables=sorted(set(re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)',(ROOT/'database/schema.sql').read_text(encoding='utf-8')))-{'foods','recipes','recipeingredients'}),
        mapping='Resolve exact checked names/meal types, preserve existing IDs; generated keys for inserts, never assume AUTO_INCREMENT values',
        conflict_policy='Abort on any unexpected before value, duplicate name/type, gram, active status or image mapping; no overwrite/delete/retry',
        transaction='Single DML transaction with SELECT FOR UPDATE and exact pre/post verification; rollback on error; no DDL/force or partial30recipe release',
        food_changes=changes,new_recipes=new)
    out=STAGING/'release';out.mkdir(exist_ok=True)
    write(out/'catalog-A-baseline.json',a);write(out/'candidate-migration-plan.json',plan)
    audit=read('recipe-audit.json')
    result=dict(status='STAGING_READY_TECHNICAL_ONLY',production_ready=False,deployed=False,production_write_authorized=False,
        qualified_B_status='BLOCKED_NO_QUALIFIED_CATALOG_EMITTED',qualified_C_status='BLOCKED_NO_QUALIFIED_CATALOG_EMITTED',
        original_recipes_source_complete=audit['source_complete_recipe_count'],new_recipes_staging_method_qualified=review['staging_method_qualified'],
        qualified_new_recipes_approved_for_production=0,illustrations_staging=30,
        catalogs=[dict(label=label,path=path.as_posix(),sha256=sha(path)) for label,path in
            [('A_BASELINE',out/'catalog-A-baseline.json'),('B_EXPLORATORY',STAGING/'catalog-B-exploratory.json'),('C_EXPLORATORY',STAGING/'catalog-C-exploratory.json')]],
        reviewed_source_manifest_sha256=sha(STAGING/'source-retrieval-manifest.json'),
        recipe_review_sha256=sha(STAGING/'recipe-portion-review.json'),image_manifest_sha256=sha(STAGING/'image-generation-jobs.json'),
        local_delta_report_sha256=sha(STAGING/'local-delta-result.json'),blockers=blockers)
    write(out/'release-manifest.json',result)
    print('STAGING_READY only;qualifiedB/C blocked;planned foodupdates='+str(plan['counts']['update_foods'])+';no production SQL or database write')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--production',action='store_true');build(p.parse_args().production)
