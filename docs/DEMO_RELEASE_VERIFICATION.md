# Demo release verification

Source root is authoritative. Keep the separate NutriFit-publish package and
tracked demo.zip unchanged on disk; they are not runtime dependencies.

## Offline regression

Python3.12: create a virtual environment and install backend/requirements.txt.
Run `python -B -m pytest backend/tests -q -p no:cacheprovider`. Pytest includes
unittest and the standalone Workout/StreetFood tests. conftest blocks real
MySQL, external HTTP and SMTP. Fixtures use SQLite in-memory. Frontend:
`node frontend/tests/meal-integration.test.js`, or the same harness in Chrome/V8.

## Current and historical data

Runtime canonical seed is158 estimated Vietnamese foods and63 legacy menus.
Research tests explicitly use the frozen102-dish fixture. Historical loaders
still validate arithmetic, source records, duplicates and canonical checksums;
`--baseline-seed` is validate-only and cannot be combined with --apply/check-db.
No historical baseline can replace the active catalog through that override.

## Clean-source setup

`setup/init_demo_test_database.py --database nutrifit_demo_clean_UNIQUE` validates
only. Add --apply only for a NEW disposable local database. Existing databases
are refused. It extracts twenty CREATE TABLE definitions/indexes in dependency
order and never executes source DROP/USE, old user accounts, sample payment
transactions or historical intake inserts. Fresh Payment defaults are PENDING
and its user FK is RESTRICT, matching the current model and approved003 schema.
Only the four public lookup tables (WorkoutCategories, Workouts, StreetFoodDish,
DishCatalog) receive reference seeds; no user-linked historical inserts run.
DDL auto-commits: on any failure keep the isolated partial DB for review; never
reset/retry against NutriFitDB. Seed158/legacy63 then re-runs with zero inserts.

Fill secrets locally using the example configuration. Never copy the developer
.env or a user database into the clean source candidate. Use a generated stable
session key, a local MySQL connection and blank Gemini key/model for offline
verification. Local Demo registration requires explicit development/local flags;
production retains normal email behavior. Payment gateway/email tests are mocked.

## Publishing gate

The immutable tracked archive contains receiver bank details in its nested
package. No values are included here. It also retains old sample identities.
Archive/history privacy review is unresolved; do not stage/commit/push or rewrite
history automatically. The source-only manifest excludes the archive and duplicate
package; this is a tested source proposal, not proof that a future Git commit
has removed the already-tracked archive from its tree/history.

Current legacy Core/Payment/Admin/Workout authorization contracts must not be
represented as production-grade authentication; Nutrition uses signed sessions.
Nutritional values are estimates. This release does not certify allergy safety.

Detailed local test/failure/file audit reports are outside Git under the OS temp
directory. Main NutriFitDB remains read-only during verification.


## Observed results

Baseline pytest:394 cases collected,345 ordinary passes,49 ordinary failures
plus21 failing subtests (70 failed reports). Root-cause inventory:B30 outdated
contract/data reports,C39 duplicate-column fixture reports,D1 environment leak.
Additional application mismatch found: Nutrition invalid-activity fallback1.375
vs current Profile1.2; adapter aligned without changing Core formulas.

Final full pytest:400/400 cases,76 subtests PASS,0 failures/errors/skips.
The same400 cases passed in a separately installed Python3.12 environment built
from exactly131 source-manifest files. Frontend harness55/55 PASS in V8; Python,
JSON and JavaScript syntax and local asset paths checked. Existing deprecation
warnings remain; they were not converted into skipped tests or hidden failures.

Fresh isolated MySQL:20 tables,158 active Vietnamese foods,63 legacy templates;
repeat seed inserts0 rows. Auth/Profile/session/CORS, meal generate/cache/refresh,
unknown/avoid and stale state, no-alternative with controlled pool, pending/signed
mock payment+idempotency, Premium search/preview, Workout logs/Progress and
StreetFood PASS. Chrome headless loaded the candidate, logged in, refreshed/F5,
searched158 foods, checked gram validation, recorded intake and showed/cleared
actual over-target warnings. Runtime JavaScript exceptions:0. Gemini/SMTP/payment
gateway requests were blocked; no live provider success is claimed.

NutriFitDB local: all20 full-table fingerprints unchanged,158 active foods,
63 templates,18 Users,34 meal histories and14 intake logs. Private .env and
immutable demo.zip unchanged. Test databases were kept, never dropped/reset.

Publishing remains blocked by archive/history privacy review. The source-only
candidate excludes demo.zip, but that ZIP still belongs to the tracked parent
Git tree/history. User decision required before changing archive tracking/history.
Five inherited files also contain trailing whitespace; they are listed in the
local audit report rather than being silently reformatted across team modules.
No branch/staging/commit/push was performed.
