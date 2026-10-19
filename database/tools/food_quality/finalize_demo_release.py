"""Seal a technically qualified educational release. This NEVER authorizes or executes Aiven writes."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
from build_demo_release import OUT,ROOT,STAGING,load,write,sha,validate_demo


def finalize():
    catalog=load(OUT/'catalog-C-qualified.json');provenance=load(OUT/'demo-provenance.json')
    validate_demo(catalog,provenance)
    local=load(OUT/'demo-local-trial.json');web=load(OUT/'web-tests.json');benchmark=load(OUT/'demo-benchmark-summary.json')
    tested=load(OUT/'catalog-C-local-trial.json')
    def contract(c):
        return dict(foods=[{k:f[k] for k in ('ref','name','nutrients')} for f in c['foods']],
            recipes=[{k:r[k] for k in ('ref','name','meal_type','base_servings','instructions','image_url','prep_minutes','ingredients')} for r in c['recipes']])
    if contract(tested)!=contract(catalog):raise ValueError('Migration-tested SQL contract differs from final catalog')
    if local['status']!='PASS' or local['catalog_sha256']!=sha(OUT/'catalog-C-local-trial.json') or local['idempotency_writes']!=0:
        raise ValueError('Local migration evidence is missing or stale')
    for field in ('restored_backup_rows_exact','rollback','conflict_rejected','protected_tables_unchanged','old_recipe_ids_preserved','jdbc_calculator_60'):
        if local[field] is not True:raise ValueError('Local gate failed:'+field)
    if web['status']!='PASS' or web['jsp_errors']!=0 or any(t['status']!='PASS' for t in web['browser_tests']):
        raise ValueError('Web verification incomplete')
    reports=list((ROOT/'target/surefire-reports').glob('TEST-*.xml'))
    counts=Counter()
    for path in reports:
        suite=ET.parse(path).getroot()
        for key in ('tests','failures','errors','skipped'):counts[key]+=int(suite.attrib[key])
    if counts['tests']<127 or any(counts[k] for k in ('failures','errors','skipped')) or not (ROOT/'target/nutrifit.war').is_file():
        raise ValueError('Current Maven/JUnit/WAR evidence incomplete')
    verification=load(OUT/'verification-report.json')
    for path,digest in verification['source_hashes'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Runtime source changed after tests:'+path)
    if verification['python_tests']!=38 or not all(verification[k] for k in ('python_pass','maven_build_pass','git_diff_check_pass','powershell_syntax_pass')):
        raise ValueError('Release checks incomplete')
    for ds in benchmark['datasets']:
        if ds['successful']!=432 or ds['avoidable20']!=0:raise ValueError('Cohort gate failed')
    baseline=load(OUT/'catalog-A-baseline.json');old={f['ref']:f for f in baseline['foods']}
    changes=[]
    for food in catalog['foods']:
        previous=old.get(food['ref'])
        if previous is None or previous['nutrients']!=food['nutrients']:
            changes.append(dict(operation='INSERT' if previous is None else 'UPDATE_IF_EXACT_BEFORE_OR_ALREADY_AFTER',food_ref=food['ref'],
                name=food['name'],before=previous['nutrients'] if previous else None,after=food['nutrients']))
    plan=dict(version=catalog['version'],database='nutrifitdb',production_write_authorized=False,
        before=dict(foods=82,recipes=30,links=383),after=dict(foods=100,recipes=60,links=607),
        counts=dict(insert_foods=18,insert_recipes=30,insert_links=224,update_foods=66),
        mutations='Parameterized INSERT foods/recipes/recipeingredients; UPDATE only5nutrient columns of66checked foods. No DDL,DELETE,DROP,TRUNCATE or history writes.',
        transaction='One DML transaction; InnoDB, exact before-or-after check, SELECT FOR UPDATE, generated ID mapping, all60JDBC-calculator/metadata/FK checks beforeCOMMIT. Rollback on any error; never auto retry.',
        authorization='Owner must approve exact final-manifest SHA256 once. Required explicit --go-live-approved-manifest flag; manifest/backup/file hashes checked before opening Aiven.',
        recovery='Catalog-only data backup plus24tableDDL outsideGit; actual isolated local restore exact82/30/383PASS. Does not back up user rows. Never restore over live user data; investigate and plan catalog-only recovery if post-COMMIT issues occur.',
        backup_manifest_sha256=local['backup_manifest_sha256'],food_changes=changes,new_recipes=catalog['recipes'][30:],
        protected='Every existing recipe ID/name/grams/base/image preserved; users/subscriptions/payments/mealentries untouched; no historical snapshot recalculation')
    if sum(x['before'] is not None for x in changes)!=66:raise ValueError('Plan count mismatch')
    write(OUT/'demo-migration-plan.json',plan)
    files=set(p for p in OUT.iterdir() if p.is_file() and (p.suffix in {'.json','.csv'}) and p.name not in {'final-manifest.json','release-manifest.json','candidate-migration-plan.json'})
    files.update(p for p in (ROOT/'database/tools/food_quality').iterdir() if p.suffix in {'.java','.py','.ps1'})
    files.update(STAGING/n for n in ['food-provenance.json','new-food-provenance.json','source-retrieval-manifest.json','image-generation-jobs.json'])
    for r in catalog['recipes']:files.add(ROOT/'src/main/webapp'/r['image_url'].lstrip('/'))
    for relative in ['.gitattributes','database/seed/vietnamese_catalog.json','src/main/java/com/nutrifit/service/MealRecommendationService.java',
        'src/main/java/com/nutrifit/controller/MealRecommendationsServlet.java','src/main/webapp/assets/js/nutrition.js',
        'src/main/webapp/WEB-INF/views/nutrition/meal-recommendations.jsp','src/test/java/com/nutrifit/service/MealSwapTest.java',
        'src/test/java/com/nutrifit/controller/NutritionRecommendationsHttpTest.java','src/test/java/com/nutrifit/service/MealSuggestionSaveTest.java',
        'src/test/java/com/nutrifit/service/FoodQualityCohortBenchmarkTest.java','src/test/resources/nutrition-swap-ui-test.html']:
        files.add(ROOT/relative)
    manifest=dict(version=catalog['version'],status='PRODUCTION_READY_AWAITING_OWNER_GO_LIVE',production_ready=True,
        production_write_authorized=False,production_data_deployed=False,target_database='nutrifitdb',
        counts=plan['after'],changes=plan['counts'],nutrient_provenance=provenance['summary'],
        qualification='Educational estimates accepted2026-10-20; no medical/laboratory claim; original strict-source gaps remain documented',
        backup=dict(scope='Catalog data +24tableDDL; no personal rows',restore_tested=True,manifest_sha256=local['backup_manifest_sha256']),
        verification=dict(junit=dict(counts),python=38,jsp_errors=0,javascript_checks=37,local_mysql='PASS24table restore/transaction/rollback/idempotency/conflict/history/FK/60calculator',benchmark_cases_per_dataset=432),
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)])
    write(OUT/'final-manifest.json',manifest)
    print('PRODUCTION_READY, NOT AUTHORIZED/NOT DATA DEPLOYED. final-manifest SHA256='+sha(OUT/'final-manifest.json'))

if __name__=='__main__':finalize()
