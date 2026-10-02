# Knowledge operations — existing Auto Expert 0.8.0

## Start and administration

Run Start-Local.ps1 in this project. Keep credentials in ignored .env/environment only.
Clean installation: Python 3.12+, `uv sync --frozen`, Alembic head and registry initialization.
Do not run old demo seeds on a populated database.

```powershell
.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.venv\Scripts\python.exe scripts/knowledge_admin.py seed-registry
# Register your own operator through the app, then grant that existing account:
.venv\Scripts\python.exe scripts/knowledge_admin.py grant-admin --email OPERATOR_EMAIL
```

Registration never auto-grants admin. The inactive local catalog audit actor is not a login;
do not enable it or infer credentials. Authenticated operator uses the profile/editor route
`#/editor`: source policy, documents, import queue/errors/diffs, review/publication, corrections,
locks/rollback, image metadata/preview/approval and AZ/RU publication JSON. Technical JSON keys
remain codes; they are not translated vehicle facts. APIs are protected by actual AdminUser.

## Sources and bounded acquisition

Registry records publisher/owner, data types/markets, access/cost, storage/display/commercial
rights and freshness. Public availability is not commercial permission. EPA is LOCAL_RESEARCH,
commercial reuse denied. NHTSA adapters retained; KR/CN/EU/rating/AZ permissions remain unresolved;
MLIT search was suspended at verification. Sanitized state is in source-registry.json.

Pause blocks acquisition/publication, preserving published facts. 429/503 applies bounded
Retry-After backoff; retries explicit. No paid or arbitrary URL acquisition. EPA bulk allowlist:
https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip . Raw bytes are private, checksum-addressed,
size-bounded and never publicly served. ZIP parser limits inflated size/ratio, accepts one CSV
and does not extract paths. Data freshness policies are metadata; not every category has an
automatic refresh scheduler. Price eligibility actively enforces the 30-day window.

Editable data/manifests/epa-local-research.json bounds years/makes/families/versions with an
editorial selection rationale, not measured AZ popularity. Current 199 families include retained
prior editions; the manifest batch target is not a cap on the database.

```powershell
# Stages only; uses a previously acquired private cache and never auto-publishes:
.venv\Scripts\python.exe scripts/knowledge_admin.py import --manifest data/manifests/epa-local-research.json --reuse-cache --include-published
.venv\Scripts\python.exe scripts/knowledge_admin.py coverage
```

On a clean machine, omit --reuse-cache only for the intended authorized free source download.
No populated database/private raw file is in the source archive. Adding makes/models uses data,
not hardcoded UI cards. Source registry approval is separate from document parsing success.

## Import, review and publish

1. Upload authorized bytes in protected editor; retain SHA256 and source locator privately.
2. Set document_id and parser manifest-json-v1, manifest-csv-v1 or epa-csv-v1. Set dry_run true
   for inspection. JSON records are CatalogRecord values; CSV nested facts are JSON cells.
3. Enqueue bounded import: persistent cursor/lease/errors, resume/dedup/cancel. Malformed data
   quarantined; staging cannot appear as published catalogue.
4. Inspect exact applicability and before/after diff; review batch, then explicitly publish.
   Editor locks fail the whole transaction. Publishing creates source/evidence/revision linkage.
5. Correct with stable external_key and revision_note, stage/review again. Authenticated rollback
   switches active evidence while preserving historical evidence and immutable saved Reports.

Required CatalogRecord fields: external_key, make, model, configuration, original_market,
model_year, HTTPS source_url, nonempty facts. Optional generation/code/facelift/production dates,
assembly country, supply channel and aliases remain unknown unless sourced. Fact requires value
and locator; quantities require correct unit (engine_displacement L, fuel_combined L/100km,
electricity_combined kWh/100km, clearance mm). Schema rejects extra/nonfinite/out-of-range values.
Use backend/app/schemas/knowledge.py as the exact contract and admin draft UI as editable sample.
Do not infer generation, aggregate code, NA aspiration or local price from model names. UNKNOWN
is not ANY; unspecified automatic is not confirmed AT/CVT/DCT; SUV is not confirmed crossover.

## Dated AZ asking-price observations

Append market_observations to a record: source_id, external_key, country, city, currency, price,
mileage_km, observed_at (timezone required), HTTPS source_url, locator, identity_basis explaining
exact-version matching. Independent market source policy is required. Existing MarketListing/
SourceRecord rows are created in the same publication transaction. Stable duplicates reuse rows;
conflicts for the same identity/date fail instead of overwriting. Future timestamps rejected.
Only recent (30 days), permitted REAL exact-version AZN asking prices satisfy budget filters.
Changed version identity invalidates prior price scope through an identity hash.
Asking price is not transaction price, sale/liquidity proof or factory evidence. This delivery
imported no actual AZ prices; fixture observations exist only in isolated tests.

## Optional research worker

Local default disabled. To operate later, set AUTOEXPERT_KNOWLEDGE_WORKER_ENABLED=true for both
API and worker, restart API and run `python -m app.knowledge_worker` with PYTHONPATH=backend under
an operator-managed supervisor. A flag alone is not a running worker. Prepared Compose enables
both services but was not started here.
Research uses existing ResearchJob with owner/day dedup, lease, bounded attempts, cancellation,
status/retry. Explicit free source allowlist only: request budget 12, per-request timeout 8s,
bounded body and cancellation checks. Results require review before catalogue publication.
Missing key/rights/worker has an honest status; no pretend background work.

## Images and editorials

Upload licensed image bytes with make/model/generation/facelift/body/market/year/variant scope,
source URL and rights reference. Private original, checksums/version and 640/1280 WebP renditions.
Bearer-protected preview uses private/no-store. Approval requires manual rights AND identity QA.
Generated illustration still requires explicit manual approval; no generation on user requests.
Wrong facelift or scope change returns asset to IMAGE_QA; approved rendition is reused in all
buyer views/editorials. Originals are never public. Current exact-model images unapproved;
neutral placeholders displayed. buyer-road.svg is decorative, not exact-vehicle/VIN evidence.

Publication JSON requires AZ/RU titles and limitations, linked versions and applicable evidence
IDs; optional scenario/claims/topics/approved assets. Draft hidden until review, old revision
retained in audit. Visible source links accompany the stored article. On changed source facts,
editors must revise/review affected articles: automatic editorial revalidation not implemented.
Three current ICE/HEV articles do not establish generations, reliability, liquidity or local costs.

## Reports, cost and recovery

Existing immutable Report holds the same AZ/RU factual snapshot; chat is a bounded factual
template, not a general LLM. Decimal TCO = depreciation + energy + service + repair reserve +
explicit other costs; purchase separate. Unknown resale makes total unknown; entirely unknown
subtotal also unknown. User prices are dated assumptions; PHEV requires a mode share.
Retail/history photos remain separate from KnownIssue/model facts and never imply damage.
7/+10/17 AZN is inactive concept config; mock payments retained, no paid provider activated.

scripts/local_backup_restore.py restores into a new path and checks hashes/counts/integrity/FKs.
Private backups contain accounts/reports and are excluded from artifacts. Never rehearse over
the running DB. Future PostgreSQL runbook is deploy/README.md; runtime not verified here.

Official references verified 2026-09-19:
- [EPA API](https://www.fueleconomy.gov/feg/ws/index.shtml)
- [EPA use conditions](https://www.fueleconomy.gov/feg/ORNL-disclaimer.htm)
- [NHTSA vPIC](https://vpic.nhtsa.dot.gov/api/)
