"""Reproduce descriptive cohort metrics from persisted CSV and exact catalog hashes."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
from build_provenance import ROOT,STAGING

FIELDS=['projected_kcal','absolute_error_kcal','relative_error','protein_g','available_carbs_g','fat_g','fiber_g','protein_energy_ratio','carb_energy_ratio','fat_energy_ratio','fiber_gap_g','unique_food_count','runtime_ms']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def summarize():
    result=[]
    configs=[('A_before','cohort-A-unconstrained.csv',ROOT/'database/seed/vietnamese_catalog.json'),
        ('A_guarded','cohort-A-guarded.csv',ROOT/'database/seed/vietnamese_catalog.json'),
        ('B_exploratory','cohort-B-guarded.csv',STAGING/'catalog-B-exploratory.json'),
        ('C_exploratory','cohort-C-guarded.csv',STAGING/'catalog-C-exploratory.json')]
    for label,name,catalog_path in configs:
        with (STAGING/name).open(encoding='utf-8',newline='') as handle:rows=list(csv.DictReader(handle))
        if len(rows)!=432:raise ValueError('Expected432 cohort cases')
        catalog=json.loads(catalog_path.read_text(encoding='utf-8'));recipes={int(r['ref'][1:]):r for r in catalog['recipes']}
        ids={int(value.strip()) for row in rows for value in row['recipe_ids'].strip('[]').split('/')}
        foodrefs={i['food_ref'] for recipe in ids for i in recipes[recipe]['ingredients']}
        item=dict(label=label,cases=len(rows),success=sum(r['success']=='true' for r in rows),
            feasible_10pct=sum(r['energy_feasible_10pct']=='true' for r in rows),
            avoidable_gap_over20pct=sum(r['large_error_despite_feasible']=='true' for r in rows),
            unique_recipes_selected=len(ids),unique_ingredients_selected=len(foodrefs),catalog_sha256=sha(catalog_path),
            csv_sha256=sha(STAGING/name),food_source_qualified=False,
            fat_over_25pct=sum(float(r['fat_energy_ratio'])>.25 for r in rows),
            carbs_outside_50_65pct=sum(not .50<=float(r['carb_energy_ratio'])<=.65 for r in rows))
        for field in FIELDS:
            values=sorted(float(r[field]) for r in rows)
            if any(not math.isfinite(x) for x in values):raise ValueError('Nonfinite benchmark result')
            item[field]=dict(mean=statistics.mean(values),median=statistics.median(values),p90=values[math.ceil(.9*len(values))-1])
        result.append(item)
    summary=dict(status='EXPLORATORY_NOT_PRODUCTION_VERIFICATION',guarded_algorithm_sha256=sha(ROOT/'src/main/java/com/nutrifit/service/MealRecommendationService.java'),same_algorithm_for_guarded_A_B_C=True,same_baseline_historical_snapshots=True,qualified_B_C_available=False,datasets=result)
    (STAGING/'cohort-comparison-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    lines=['# Benchmark continuation — dữ liệu thăm dò, không phải qualification','',
        '432 tình huống/dataset; cùng6 hồ sơ giả lập,3 activity,3 goal,4 trạng thái gói/sở thích,2 nhật ký. Target từ OnboardingService không đổi. Cùng lịch sử A và cùng thuật toán cho guarded A/B/C. A_before lưu từ lần thực tế trước guard, không chạy lại bằng code mới. B hiện thay70 Food đủ số nguồn,12 Food còn thiếu giữ baseline ước tính có nhãn. C thêm18 Food/30 thiết kế.','',
        '| Chỉ số | A trước guard (cũ) | A guarded | B70 nguồn thăm dò | C60 thiết kế thăm dò |','|---|---:|---:|---:|---:|']
    metrics=[('Đủ3 bữa','success'),('Có tổ hợp trong10%target','feasible_10pct'),('Lệch>20% dù có tổ hợp trong10%','avoidable_gap_over20pct')]
    metrics += [(field+' '+stat,field+'.'+stat) for field in FIELDS for stat in ('mean','median','p90')]
    metrics += [('Đa dạng món','unique_recipes_selected'),('Đa dạng Food','unique_ingredients_selected'),('Fat>25%energy số case','fat_over_25pct'),('Carbs ngoài50–65%energy số case','carbs_outside_50_65pct')]
    for title,key in metrics:
        values=[]
        for item in result:
            if '.' in key:
                field,stat=key.split('.');values.append(format(item[field][stat],'.4f'))
            else:values.append(str(item[key]))
        lines.append('| '+title+' | '+' | '.join(values)+' |')
    lines+=['','P90 nearest-rank; runtime là service-call wall-time trên một máy, không phải load test. Macro tỷ lệ4/4/9 chia kcal nguồn, không ép tổng100%. NIN là tham chiếu mềm: fat20–25%,carbs50–65%,fiber nam trẻ21g/nữ18g,50+20g/17g; không phải khuyến nghị y khoa cá nhân. [Nguồn NIN](https://viendinhduong.vn/vi/proper-nutrition-and-health/nguoi-truong-thanh-19-59-tuoi/nhung-diem-cap-nhat-ve-nhu-cau-dinh-duong-khuyen-nghi-cho-nguoi-viet-nam-6a70094d06fb0c475f0ac123).','',
        'So với checkpoint: A guarded mean absolute error598.575kcal; C cũ161.362kcal. Những thay đổi trong B/C lần này là dữ liệu thăm dò, không sửa scorer. Không xem cải thiện benchmark là bằng chứng nguồn/khẩu phần đã đúng.24 thiết kế qua review phương pháp staging,6 suất đặc lớn còn pending; không phát hành partial30 mới để đủ60.','',
        'CSV/SHA, mean/median/P90 đủ năm nutrient, sai lệch, diversity và runtime ở cohort-comparison-summary.json. Dataset qualified B/C chưa được tạo vì còn47MISSING và gates khác.']
    (ROOT/'docs/nutrition/data-quality-benchmark.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    for r in result:print(r['label'],'mean absolute kcalerror',round(r['absolute_error_kcal']['mean'],3),'feasible',r['feasible_10pct'],'avoidable',r['avoidable_gap_over20pct'])

if __name__=='__main__':summarize()
