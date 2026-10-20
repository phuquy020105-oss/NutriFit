"""Offline catalog, provenance, assets and local dependency checks. No network or DB access."""
import hashlib
import json
from pathlib import Path
import re
from decimal import Decimal
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
KEYS = ('calories_per_100g','protein_per_100g','carbs_per_100g','fat_per_100g','fiber_per_100g')
def require(ok, code):
    if not ok:
        raise ValueError(code)
def load(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))
def schema_contract(sql):
    tables=re.findall(r'CREATE TABLE IF NOT EXISTS ([a-z_]+) \(.*?\) ENGINE=[^;]+;',sql,re.S)
    require(len(tables)==24 and len(set(tables))==24,'Expected24 unique schema tables')
    def definition(name):
        match=re.search(r'CREATE TABLE IF NOT EXISTS '+name+r' \(.*?\) ENGINE=[^;]+;',sql,re.S)
        require(match is not None,'Missing table '+name)
        return re.sub(r'\s+',' ',match.group(0))
    users=definition('users')
    require('auth_version BIGINT NOT NULL DEFAULT 0' in users,'users.auth_version contract')
    require(not re.search(r'ALTER\s+TABLE\s+users',sql,re.I),'Schema must define auth_version directly')
    reset=definition('password_reset_otps')
    for fragment in ['email VARCHAR(255) NOT NULL PRIMARY KEY','otp_hash VARCHAR(255) NOT NULL','expires_at DATETIME NOT NULL',
                     'attempts INT UNSIGNED NOT NULL DEFAULT 0','last_sent_at DATETIME NOT NULL','window_start DATETIME NOT NULL',
                     'sent_in_window INT UNSIGNED NOT NULL DEFAULT 0',
                     'FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE',
                     'ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci']:
        require(fragment in reset,'Reset OTP contract: '+fragment)
    require(sql.index('CREATE TABLE IF NOT EXISTS users (')<sql.index('CREATE TABLE IF NOT EXISTS password_reset_otps ('),'FK parent creation order')

def verify():
    schema_contract((ROOT/'database/schema.sql').read_text(encoding='utf-8'))
    catalog=load('database/seed/catalog.json'); provenance=load('database/seed/provenance.json')
    foods={f['ref']:f for f in catalog['foods']}; recipes=catalog['recipes']
    require(len(foods)==len(catalog['foods'])==100 and len(recipes)==60,'Expected100/60')
    require(len({r['ref'] for r in recipes})==60,'Duplicate recipe ref')
    for rows in (list(foods.values()),recipes):
        require(len({r['name'].casefold() for r in rows})==len(rows),'Duplicate name')
    require(Counter(r['meal_type'] for r in recipes)==dict(BREAKFAST=20,LUNCH=20,DINNER=20),'Meal counts')
    evidence={f['food_ref']:f for f in provenance['foods']}; require(set(evidence)==set(foods),'Provenance references')
    statuses=Counter(); estimated_foods=0
    for ref,f in foods.items():
        e=evidence[ref]; require(e['state']==f['state'] and bool(e['source']),'State/source missing')
        estimated=False
        for k in KEYS:
            n=Decimal(f['nutrients'][k]); fact=e['nutrients'][k]
            require(n.is_finite() and 0<=n<=Decimal('999999.99'),'Food numeric range')
            require(n==Decimal(fact['value']) and fact['status'] in ('MATCHED','CALCULATED','ESTIMATED'),'Fact mismatch')
            require(bool(fact['method']) and bool(fact['confidence']),'Missing method/confidence')
            statuses[fact['status']]+=1; estimated |= fact['status']=='ESTIMATED'
        estimated_foods+=estimated
    require(dict(statuses)==provenance['summary']['statuses'] and estimated_foods==provenance['summary']['foods_with_any_estimate'],'Evidence summary drift')
    images={i['recipe_ref']:i for i in provenance['images']};require(len(images)==60,'Image manifest count')
    urls=set(); hashes=set(); links=0
    for r in recipes:
        require(Decimal(r['base_servings'])==1 and bool(r['instructions']),'Recipe portion/instructions')
        seen=set(); totals={k:Decimal(0)for k in KEYS}
        for i in r['ingredients']:
            ref=i['food_ref']; grams=Decimal(i['quantity_grams']);require(ref in foods and ref not in seen and grams>0 and grams==grams.quantize(Decimal('.01')),'Ingredient reference/grams')
            seen.add(ref);links+=1
            for k in KEYS:totals[k]+=Decimal(foods[ref]['nutrients'][k])*grams/100
        require(bool(seen) and all(0<=v<=Decimal('999999999.999')for v in totals.values()),'Recipe totals')
        url=r['image_url'];require(url.startswith('/assets/images/recipes/') and '..'not in url and url not in urls,'Image URL')
        raw=(ROOT/'src/main/webapp'/url.lstrip('/')).read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        require(raw[:4]==b'RIFF' and raw[8:12]==b'WEBP' and digest==images[r['ref']]['sha256'] and digest not in hashes,'WebP/checksum')
        urls.add(url);hashes.add(digest)
    require(links==607,'Expected607 links')
    web=ROOT/'src/main/webapp'
    for p in list(web.rglob('*.jsp'))+list(web.rglob('*.jspf'))+list(web.rglob('*.css'))+list(web.rglob('*.js')):
        text=p.read_text('utf-8')
        for match in re.finditer(r'/assets/([A-Za-z0-9_./-]+\.(?:css|js|svg|webp|png|jpg|ico))',text):
            require((web/'assets'/match[1]).is_file(),'Missing asset '+str(p.relative_to(ROOT))+':'+match[1])
        for match in re.finditer(r'<%@\s*include\s+file="([^"]+)"',text):
            path=match[1];require((web/path.lstrip('/') if path.startswith('/') else p.parent/path).is_file(),'Missing JSP include')
    docs=[ROOT/'README.md',ROOT/'database/README.md',*list((ROOT/'docs').rglob('*.md'))]
    for p in docs:
        for dest in re.findall(r'\]\(([^)]+)\)',p.read_text('utf-8')):
            if re.match(r'^[a-z]+://',dest) or dest.startswith('#'): continue
            dest=dest.split('#')[0].strip('<>');require((p.parent/dest).exists(),'Broken document link '+str(p.relative_to(ROOT))+':'+dest)
    # Runtime/build must never depend on development-only staging tools or private local files.
    for p in [ROOT/'Dockerfile',ROOT/'pom.xml',*list((ROOT/'src').rglob('*.java'))]:
        text=p.read_text('utf-8');require('database/staging/'not in text and 'database/tools/food_quality'not in text,'Retired dependency '+str(p.relative_to(ROOT)))
    print('PASS24table schema/auth/OTP;100foods/60recipes/607links/20permeal/60WebP+SHA; provenance/assets/dependencies')
if __name__=='__main__': verify()
