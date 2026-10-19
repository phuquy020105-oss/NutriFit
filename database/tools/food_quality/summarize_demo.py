"""Persist the actual Maven cohort/swap outputs; no synthetic benchmark results."""
import csv
import math
import statistics
from build_demo_release import OUT, ROOT, load, write, sha


def summarize():
    target=ROOT/'target/food-quality'
    for name in ['cohort-A.csv','cohort-demo-B.csv','cohort-demo-C.csv','swap-benchmark.csv','web-tests.json']:
        (OUT/name).write_text((target/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    datasets=[]
    for file,label,catalog in [('cohort-A.csv','A_CURRENT_PRODUCTION30','catalog-A-baseline.json'),('cohort-demo-B.csv','B_DEMO30_REFERENCES','catalog-B-qualified.json'),('cohort-demo-C.csv','C_DEMO60','catalog-C-qualified.json')]:
        rows=list(csv.DictReader((OUT/file).open(encoding='utf-8')))
        if len(rows)!=432:raise ValueError('Missing cohort rows')
        item=dict(label=label,cases=len(rows),successful=sum(r['success']=='true' for r in rows),
            feasible10=sum(r['energy_feasible_10pct']=='true' for r in rows),avoidable20=sum(r['large_error_despite_feasible']=='true' for r in rows),
            catalog_sha256=sha(OUT/catalog),csv_sha256=sha(OUT/file))
        for key in ['absolute_error_kcal','relative_error','protein_g','available_carbs_g','fat_g','fiber_g','runtime_ms']:
            values=sorted(float(r[key]) for r in rows)
            if any(not math.isfinite(v) for v in values):raise ValueError('Invalid benchmark')
            item[key]=dict(mean=statistics.mean(values),median=statistics.median(values),p90=values[math.ceil(.9*len(values))-1])
        datasets.append(item)
    rows=list(csv.DictReader((OUT/'swap-benchmark.csv').open(encoding='utf-8')));swaps=[]
    for catalog in ['30','60']:
        selected=[r for r in rows if r['catalog']==catalog]
        swaps.append(dict(catalog_recipes=int(catalog),scenarios=len(selected),attempt_limit=6,
            successful_swaps=sum(int(r['changes']) for r in selected),no_alternative_scenarios=sum(int(r['changes'])==0 for r in selected),
            max_single_swap_relative_kcal=max(float(r['max_relative_calorie_change']) for r in selected)))
    result=dict(status='PASS_EDUCATIONAL_ACCEPTANCE',datasets=datasets,swaps=swaps,
        algorithm_sha256=sha(ROOT/'src/main/java/com/nutrifit/service/MealRecommendationService.java'),
        notes=['Same actual Onboarding targets, scorer and historical snapshots, fixed1.00portions;432cases per dataset',
            'No forced poor substitution when acceptable novel choices are exhausted',
            'Numeric data matches the previous exploratory C; educational qualification is an owner policy change, not new analytical measurement',
            'Not a clinical qualification or a load test'])
    write(OUT/'demo-benchmark-summary.json',result)
    for d in datasets:print(d['label'],'meanAbsKcalError',round(d['absolute_error_kcal']['mean'],3),'feasible10',d['feasible10'])

if __name__=='__main__':summarize()
