"""Safe, idempotent, insert-only import of 291 curated Vietnamese dishes.

Default: validate JSON locally (NO MySQL access).
--check-db: inspect target DB transaction READ ONLY, no writes.
--apply: require external SQL backup and explicit database confirmation.

Does not create/drop tables, modify Users/PaymentTransactions, or overwrite
existing catalog dishes. Refuses same-name collisions and conflicting IDs.
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'setup/seeds/vietnamese_expansion_2026.json'


def folded_name(value):
    value = unicodedata.normalize('NFD', value.casefold().replace('đ','d'))
    return ' '.join(''.join(c for c in value if not unicodedata.combining(c)).split())


def get_batch():
    from seed_nutrition_catalog import load_seed
    seed = load_seed(CATALOG)
    if seed.get('format') != 'nutrifit-vietnamese-expanded-estimated-recipes-2026' or seed['legacy_menus']:
        raise ValueError('Unexpected batch format')
    if len(seed['dishes']) != 291 or any(not r['estimated'] or not r.get('active') for r in seed['dishes']):
        raise ValueError('Expected 291 active estimated dishes')
    if len({folded_name(r['name']) for r in seed['dishes']}) != 291:
        raise ValueError('Duplicate normalized names in expanded batch')
    if any('Ước tính' not in r['provenance']['source'] for r in seed['dishes']):
        raise ValueError('Recipe source must say estimated')
    baseline=load_seed(ROOT/'setup/seeds/nutrition_catalog.json')
    base_names={folded_name(d['name']) for d in baseline['dishes']}
    base_ids={d['dish_id'] for d in baseline['dishes']}
    if any(d['dish_id'] in base_ids or folded_name(d['name']) in base_names for d in seed['dishes']):
        raise ValueError('Overlaps with baseline catalog')
    return seed


def check_backup(file):
    if file is None:
        raise ValueError('--backup must identify a recent SQL dump outside project')
    path = file.resolve()
    if not path.is_file() or path.stat().st_size < 1024 or path.is_relative_to(ROOT):
        raise ValueError('SQL backup is empty, missing, or inside project')
    with path.open('rb') as stream:
        if not any(b'create table `nutritionfoodcatalog`' in line.lower() for line in stream):
            raise ValueError('SQL backup lacks NutritionFoodCatalog table')


def compare(current, expected):
    """Detect existing ID changes: import must not overwrite or quietly disagree."""
    exact = ('dish_id','name','type','preparation_state','ingredients','meal_types',
             'estimated','active','data_version')
    if any(current[k]!=expected[k] for k in exact):
        return False
    numbers=('reference_grams','min_grams','max_grams','calories_per_100g')
    if any(abs(current[k]-expected[k])>0.00011 for k in numbers):
        return False
    if any(abs(current['macros_per_100g'][k]-expected['macros_per_100g'][k])>0.00011 for k in ('protein','carbs','fat')):
        return False
    # Existing provenance contents are not mutated; serialization may reformat JSON.
    return current['provenance']==expected['provenance']


def db_review(dishes, repo):
    existing=repo.dishes(active=False)
    by_id={d['dish_id']:d for d in existing}
    by_name={folded_name(d['name']):d['dish_id'] for d in existing}
    pending=[]; matched=[]
    for dish in dishes:
        old=by_id.get(dish['dish_id'])
        if old:
            if not compare(old,dish):
                raise ValueError('Existing DishId differs; abort: ' + dish['dish_id'])
            matched.append(dish['dish_id'])
        else:
            conflict=by_name.get(folded_name(dish['name']))
            if conflict:
                raise ValueError(f'Name collision with existing {conflict}; abort: {dish["dish_id"]}')
            pending.append(dish['dish_id'])
    return {'before':len(existing),'before_active':sum(r['active'] for r in existing),
            'already_matching':len(matched),'to_insert':len(pending),
            'expected_total_after':len(existing)+len(pending),
            'pending_ids':pending}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--check-db',action='store_true',help='Read-only check against local MySQL')
    group.add_argument('--apply',action='store_true',help='Insert missing dishes only after backup')
    parser.add_argument('--database',default='NutriFitDB',help='Target DB must be NutriFitDB')
    parser.add_argument('--backup',type=Path,help='External SQL backup, required by --apply')
    args=parser.parse_args()
    try:
        seed=get_batch()
    except (ValueError,KeyError,TypeError) as error:
        parser.error('Invalid data: '+str(error))
    if not (args.check_db or args.apply):
        print(json.dumps({'mode':'VALIDATE_ONLY','dishes':len(seed['dishes']), 'writes':0},ensure_ascii=False))
        return
    if args.database.casefold()!='nutrifitdb':parser.error('Only NutriFitDB allowed')
    if args.apply:
        try:check_backup(args.backup)
        except ValueError as error:parser.error(str(error))
    sys.path.insert(0,str(ROOT/'backend'))
    from app import create_app
    from app.extensions import db
    from app.repositories.food_catalog_repository import FoodCatalogRepository
    from sqlalchemy import inspect,text
    try:
        app=create_app()
        with app.app_context():
            url=db.engine.url
            if url.drivername!='mysql+pymysql' or url.host not in ('127.0.0.1','localhost') or (url.port or 3306)!=3306:
                raise ValueError('Expected localhost MySQL on 3306')
            # Separate explicit READ ONLY transaction, no implicit MySQL DDL.
            if args.check_db:
                db.session.execute(text('START TRANSACTION READ ONLY'))
            actual=db.session.execute(text('SELECT DATABASE()')).scalar()
            if str(actual).casefold()!='nutrifitdb':raise ValueError('Unexpected database')
            columns={c['name'] for c in inspect(db.session.connection()).get_columns('NutritionFoodCatalog')}
            if not {'DishId','NameVi','KcalPer100G','IngredientsJson','ProvenanceJson','IsActive'}<=columns:
                raise ValueError('Invalid catalog schema')
            engine=db.session.execute(text('SELECT ENGINE FROM information_schema.TABLES '
                    'WHERE TABLE_SCHEMA=DATABASE() AND LOWER(TABLE_NAME)=\'nutritionfoodcatalog\'')).scalar()
            if str(engine).casefold()!='innodb':raise ValueError('InnoDB table expected')
            before=db_review(seed['dishes'],FoodCatalogRepository)
            if args.check_db:
                db.session.rollback()
                print(json.dumps({'mode':'READ_ONLY_CHECK','writes':0,**{k:v for k,v in before.items() if k!='pending_ids'},
                    'first_pending_ids':before['pending_ids'][:10]},ensure_ascii=False,indent=2))
                return
            try:
                result=FoodCatalogRepository.insert_missing(seed['dishes'],[])
                after=db_review(seed['dishes'],FoodCatalogRepository)
                if result['dishes']!=before['to_insert'] or after['to_insert']!=0 or after['before']!=before['expected_total_after']:
                    raise ValueError('Post-import verification failed: abort')
                db.session.commit()
                print(json.dumps({'mode':'IMPORTED','inserted':result['dishes'],'total_after':after['before'],
                    'already_present':before['already_matching']},ensure_ascii=False))
            except Exception:
                db.session.rollback()
                raise
    except Exception as error:
        # Do not disclose connection strings or credentials in error logs.
        print('Import stopped; no intentional schema changes. Error type: '+type(error).__name__)
        raise SystemExit(1) from None

if __name__=='__main__':main()
