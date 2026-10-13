# Vietnamese catalog for the local student Demo

Only source root of `D:/Web/NutriFit-Demo-Check`, branch `demo`.

## Reviewed data

`setup/seeds/nutrition_catalog.json` is the fresh-runtime seed: 77 active dishes,
63 unchanged legacy templates. `setup/seeds/demo_catalog_rebuild_review.json`
classifies **every** original 141 dish and lists all 70 retired IDs.

- 71 stable IDs retained, names/meal eligibility/tags normalized, nutrients recalculated.
- 63 direct external-source IDs removed; five oat meals removed from the curated
  Vietnamese demo, two duplicate sweet-potato MAIN entries removed.
- Six common snacks added: orange, guava, dragon fruit, ripe papaya, watermelon, peanuts.
- The 38 previously external-source-derived Vietnamese recipes and the one
  mixed-research leafy-green entry were independently recalculated. Old nutrition
  values were not just relabeled. Quantities/yields from previous draft recipes
  can be reused as **assumptions**, not measured facts.

All active profiles use rounded NutriFit **engineering assumptions** for ingredient
P/C/F. They are not independently verified food-table data. Each provenance stores
input state, edible/retained grams, the input macro values, estimated finished mass,
servings and limitations. Reproduce: sum(retained grams * ingredient macros/100),
then divide by assumed finished edible grams and multiply by100. Kcal=4P+4C+9F.
The validator checks calculations, units, mass balance, roles, portions, duplicates
and retired provenance. Fiber is unknown (NULL), not assumed zero intake;
numeric fiber totals represent only a known lower bound. Sodium and allergy/cross-
contamination safety are not certified. Completeness means THIS reference recipe.

## Safety and application

No schema DDL. `setup/rebuild_demo_food_catalog.py` defaults to validation only.
Actual DML is one InnoDB transaction touching only NutritionFoodCatalog:
71 reviewed updates, six inserts,70 ID-scoped deletes. Preflight checks all text/JSON
columns for retired ID references, rejects any catalog FK or unknown/unfrozen
reference, and verifies unchanged hashes for the other19 tables before commit.
An already matching target returns zero writes. Unexpected state stops.

Backup outside Git with a new filename (enter password in terminal):

```cmd
"C:\Program Files\MySQL\MySQL Server 26.7\bin\mysqldump.exe" -h127.0.0.1 -P3306 -uroot -p --single-transaction --skip-lock-tables --routines --events --triggers --hex-blob --no-tablespaces --set-gtid-purged=OFF --result-file="D:\NutriFitBackups\NutriFitDB_UNIQUE_NAME.sql" NutriFitDB
```

Require exit0, nonempty dump, expected table set, completion footer, SHA-256 and
actual restore into a **new, empty, uniquely named test database**. Never restore
onto NutriFitDB as a rehearsal. Recheck live fingerprints before applying.

```cmd
.venv\Scripts\python.exe -B setup\rebuild_demo_food_catalog.py
.venv\Scripts\python.exe -B setup\rebuild_demo_food_catalog.py --check-db --database TEST_DATABASE_NAME
.venv\Scripts\python.exe -B setup\rebuild_demo_food_catalog.py --apply --database TEST_DATABASE_NAME --backup BACKUP_PATH
```

Test database name must start `nutrifit_catalog_rebuild_`. Main apply additionally
requires an external JSON attestation from the verified restore/API rehearsal:
backup SHA, restore/test PASS, complete before-table fingerprints and seed SHA.
Never fabricate this attestation to bypass testing.

```cmd
.venv\Scripts\python.exe -B setup\rebuild_demo_food_catalog.py --check-db --database NutriFitDB
.venv\Scripts\python.exe -B setup\rebuild_demo_food_catalog.py --apply --database NutriFitDB --backup BACKUP_PATH --attestation VERIFIED_REHEARSAL_STATE_PATH
```

Failure before commit rolls back catalog DML. After commit, recovery is a separate
approved operation: restore backup into another empty database, compare/archive
catalog records, and restore ONLY the reviewed catalog rows in a transaction.
Do not restore whole NutriFitDB over newer users or intake logs. Keep old backups
and the original catalog archive outside Git. No automated destructive rollback.

## Runtime compatibility and UI

History and intake use frozen snapshots; even early portion-only snapshots scale
from original grams/kcal/macros. No historical row is rewritten by catalog rebuild.
Retired/revised cached recipes remain viewable but cannot be selected/used for new
intake/partial replacement: `CATALOG_REFRESH_REQUIRED` (409). Explicit Think later
and refresh is required, preserving decided-plan/revision guards. Store rechecks
catalog versions if it changed while composition was pending.

Both ordinary FREE intake and component replacement search the full database
catalog. Accent folding, exact/prefix relevance and scrolling hide no valid result.
Only replacement restricts role/meal type. UI says **Bữa phụ**, internal value snack.
Avoid uses canonical ingredient/sauce tags and rejects incomplete declared recipes;
dislikes/prefer stay soft. Unknown terms return UNSUPPORTED_PREFERENCE. No allergy
safety guarantee. Archived draft import batches are blocked by the seed CLI; they
are research material, not the current seed.

MAIN foods are discoverable/loggable for all three meals. Current lunch/dinner
composition still requires CARB+PROTEIN+VEGGIE; it does not mix a complete MAIN
with redundant components. A later minimal extension could permit MAIN(+optional
side) as an alternative ruleset; not implemented in this cleanup.

`backend/tests/fixtures/pre_rebuild_catalog.json` is isolated historical regression
input; it is never runtime seed/import data. New focused tests use the current seed.
Run focused backend tests from backend with `..\.venv\Scripts\python.exe -B -m
unittest discover -s tests -p test_demo_catalog_rebuild.py`. Frontend tests use a fake
DOM/mock API (`frontend/tests/meal-integration.test.js`); browser Chrome behavior
must be reported separately from that evidence.
