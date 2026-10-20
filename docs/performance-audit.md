# Performance audit — 20/10/2026

Baseline source: `91b37ac` plus the same opt-in instrumentation used for the optimized measurements. No pooling or query changes were present in that baseline; the isolated local database selector was present. Baseline and release WAR SHA256 are recorded in the ignored comparison.json evidence.

Local measurements use JDK21, Tomcat10.1.61, MySQL26.7.0 on loopback, real BCrypt login, the same equivalent Free fixture2/profile (2200kcal), empty journal and catalog100/60/607. The final pair is scoped-before/scoped-after, measured consecutively after the Schedule scope was excluded. Earlier exploratory results are superseded. One client, sequential requests, five warmups and25 timed samples per page. Each run starts a fresh Tomcat; first-page/JSP compilation is excluded from warm samples. These are small local experiments, not production capacity/load tests; host load was not controlled. p95 uses nearest rank.

| Route | Before median ms | After median ms | Before p95 ms | After p95 ms |
|---|---:|---:|---:|---:|
| `/dashboard` | 38.714 | 5.199 | 49.852 | 26.425 |
| `/nutrition/recommendations` | 42.840 | 9.303 | 52.338 | 30.640 |
| `/workout` | 26.538 | 5.177 | 47.081 | 25.449 |
| `/profile` | 26.701 | 14.883 | 34.959 | 23.073 |

Regeneration/swap use10 authenticated preview-only POSTs (p95 equals the largest sample at this size). No writes were made during measurement.

- regenerate: median 59.322 → 37.032ms; p95 85.955 → 68.360ms.
- swap: median 44.751 → 17.778ms; p95 78.076 → 33.656ms.

All timed requests returned their expected status; no observed request errors/timeouts. Cold first-page times included JIT/JSP work: /dashboard 137.624→110.080ms, /nutrition/recommendations 310.313→234.945ms, /workout 218.370→188.226ms, /profile 63.798→57.465ms. They are not Render cold-start measurements. CPU/memory and production authenticated p95 were not collected.

| Route | JDBC acquisitions/request before → after | SQL calls/request before → after | Median total acquisition ms/request before → after |
|---|---:|---:|---:|
| `/dashboard` | 5 → 3 | 8 → 3 | 22.778 → 0.062 |
| `/nutrition/recommendations` | 6 → 5 | 11 → 8 | 23.098 → 0.066 |
| `/workout` | 6 → 5 | 6 → 5 | 20.100 → 0.047 |
| `/profile` | 4 → 2 | 4 → 2 | 12.091 → 0.015 |
| `regenerate` | 4 → 3 | 11 → 8 | 11.101 → 0.018 |
| `swap` | 4 → 3 | 28 → 11 | 13.242 → 0.016 |

Acquisitions are logical borrows after pooling, not new physical sockets. Pool3/minIdle1 is bounded; the baseline opened a new physical connection on every acquisition. Internal SQL timing covers JDBC execute calls (Connector/J buffered results), not a complete server-side query profile. View timing covers dispatcher forward; recommendation/swap spans include their nested JDBC work. `remaining_us` is an approximate residual including mapping/lock/other work, not a CPU profiler.

## Findings and changes

- Connection setup dominated local request time. One lazily created application-owned HikariCP7.0.2 pool now serves existing `DatabaseConfig.getConnection()` callers. Defaults: maximum3/minimumIdle1; acquisition10s, validation3s, lifetime240s, keepalive60s, idle120s. Local `wait_timeout=28800`, `max_connections=151`; Aiven values could not be established from this client. Idle validation/keepalive and fatal-socket eviction/replacement are retained; do not claim that a multi-hour production idle test was performed. Pool shutdown is tied to webapp destruction. No connection is stored in a session. Connections that execute GET_LOCK are physically retired on return, preserving OTP named-lock release semantics even when cleanup fails; the normal query pool remains reusable.

- AuthFilter, NavigationRoleFilter, PaymentSessionFilter and Dashboard/Profile reuse the current DB User only within one request, keyed to session userId/authVersion. Every new request reads current authentication state again. Filter annotation order does not change verification; `/payment/ipn` stays public and signature-checked. AdminFilter itself is unchanged. No shared private-user cache was added.

- Dashboard combines four independent aggregate lookups into one query, avoiding multiplication of water/workout rows. Tests cover multiple logs, today/past, missing profile, owner isolation and latest metric ties. Local EXPLAIN uses existing PRIMARY/user_id/date indexes for the original lookups. No schema/index changes were justified or applied. WorkoutPlanService, its DAOs and plan.jsp remain byte-identical to baseline per the owner’s scope decision; no Schedule-specific optimization is included.

- Nutrition reads the selected three recipes in one parameterized batch; `RecipeReadPort` has a compatible default fallback for other adapters. Swap scores candidates already calculated by NutritionCalculator, then revalidates only the selected replacement. No catalog cache across requests, preference cache or algorithm weights were introduced. Save still refreshes current data inside its original transaction; historical snapshots are untouched. A dedicated per-session Nutrition lock retains draft/save serialization without holding the session monitor across DB/CPU work.

- Public existing assets get300s caching; CSS/JS links include deployment revision and matching versioned URLs get1year immutable caching. Local startup uses a random deployment version. Tomcat ETag/304 remains in use. HTML/API/errors remain no-store, and all60 WebP/checksums are unchanged. Static CSS/JS totals87,000bytes (13CSS/4JS); 60WebP total3,800,516bytes. Existing lazy-loading/defer remains. External Google Fonts imports in Chatbot/Payment were retained to preserve UI; resource requests vary by page/viewport and were not measured as full browser production navigation.

## Reproduce and safety

Use an explicitly approved empty local test database. The measured target is `nutrifit_performance_20261020_test`; no database is automatically dropped or reset. Initial catalog creation still uses the guarded [local setup tool](../database/README.md). Build with JDK21/Maven3.9.16 and set `TOMCAT_HOME` before tests so JSP tests do not skip.

```powershell
mvn clean package
$env:TOMCAT_HOME="C:\tools\apache-tomcat-10.1.61"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/benchmark-local.ps1 -Label before -Setup -WarFile "<instrumented-baseline.war>" -EnvFile "<private-local-config>"
# Build the candidate, then benchmark without recreating fixtures:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/benchmark-local.ps1 -Label after -ServiceChecks -EnvFile "<private-local-config>"
```

The runner loads only local credentials (LOCAL_DB_USER/PASSWORD or NUTRIFIT_DB_USER/PASSWORD) literally; optional LOCAL_DB_HOST/PORT must be127.0.0.1:3306. It never reads Aiven credentials. The test target is fixed/guarded and requires an already initialized24-table database. Setup requires zero users and creates two synthetic fixture accounts. The final paired benchmark uses fixture2, a third equivalent Free account created explicitly to retain the earlier transaction/IPN test evidence without resetting its accounts/journal. -FixtureIndex2 selects it; -NewEquivalentFixture creates it once and refuses duplicates. -WarFile selects the preserved instrumented baseline WAR; omit it for the current candidate. A generated test password is retained only in Windows current-user DPAPI under TEMP; no password is printed or passed in process arguments. Reusing the same fixture preserves before/after authentication. Results/logs are ignored under `target/performance/<label>`; labels cannot overwrite an earlier run. ServiceChecks runs AFTER timing: Dashboard fixture changes roll back, pool concurrency is checked, Nutrition rolls back an injected failure then commits three fixture entries; synthetic signed IPN is checked for bad signature/amount, commit and duplicate handling. Catalog Test/Check must run before these account fixtures: a later Check correctly refused TEST_DATA_ONLY_REQUIRED after users/journals existed; its guard was retained, no data was cleared, and the read-only Verify still passed. These checks deliberately leave local test records/Premium fixture state; do not benchmark them as the original empty-Free scenario afterward and do not rerun automatically. No VNPay network request is made.

An IDE was observed replacing Maven classes with incomplete JDT output (`Unresolved compilation problem: RealCatalog`). Final validation therefore also uses an isolated checkout with exactly the same source. This is separate from source/test regressions; no tests were removed.

## Instrumentation and production limits

Set `NUTRIFIT_PERF_ENABLED=true` to enable normalized route/status/request/JDBC/SQL-group/view/recommendation/swap timing logs; default is false. It adds no public performance endpoint, SQL text/parameters, identity, tokens, cookies, payloads or connection credentials. The DataSource passed to Hikari has no credential-bearing config/toString to print. `NUTRIFIT_LOCAL_DB_NAME` is optional, loopback test-only, and rejected together with a custom URL; cloud configuration/TLS checks remain unchanged.

Public Render baseline at revision91b37ac used four sequential GETs each for health/login/dashboard.css (first + three warm). Warm end-to-end medians were820.88/367.83/823.90ms; these include network/TLS/client effects, have too few samples for a useful p95, and are not authenticated application measurements. CSS had no Cache-Control. There is no legitimate production session available for Dashboard/Nutrition/Workout/Profile profiling, no Render log/dashboard access and no production load test. A bounded direct-client SELECT-only Aiven connection experiment failed with the existing sanitized JDBC connection error; its cause was not established and it supplies no successful cloud benchmark. Do not infer wrong credentials, a TLS diagnosis or production speedup from that failure. No Aiven schema/data writes, environment/secret changes or paid Render changes were made.

## Verification evidence

- Maven/JUnit148 tests,0failures/errors/skips on isolated candidate; real JSP rendering included.
- Python repository validator24tables/100foods/60recipes/607links/60image checksums; JspC0errors; Chrome14+23JavaScript checks PASS.
- Approved local MySQL catalog test: rollback/conflict/idempotency and0new Workout seed rows on rerun PASS.
- Local real pool:40leases/8threads and named-lock release after physical retirement; Dashboard fixture rollback; Nutrition injected second-entry failure rollback and atomic3-meal save; synthetic IPN no double Premium extension PASS.
- Unit pool tests cover concurrency/bounds/return after error, rollback/reset, fatal eviction/reconnect and shutdown; authVersion/current role/request isolation and concurrent duplicate save remain covered.
- Production deployment/health/revision are checked separately after push; a healthy public endpoint alone does not prove authenticated production latency or browser workflows.
