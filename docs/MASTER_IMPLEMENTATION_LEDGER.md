# Master AZ/RU implementation ledger — 19 September 2026

Existing project `STAGE6_1`; backend 0.8.0; APK 0.8.0-alpha (80).
Requirements and visual reference preserved in `docs/reference/`.
Overall product acceptance: **PARTIAL**. Local implementation, actual data coverage,
material rights and device/server verification have separate statuses.

## A. Baseline and preservation

Baseline 0.7.0: 222 pytest PASS, two dependency deprecations, 38.81 s. No Git repository.
Private SHA-256 file baseline and consistent SQLite backup were taken before changes.
Final verification compares every original primary-key row, including composite keys.
Old reports, chats, payments, profiles, evidence and sources remain intact. Officially
confirmed canonical make/model names were promoted from demo; old demo variants remain distinct.

Reused FastAPI, SQLAlchemy/Alembic, VehicleMake/Model/Generation/Variant, source/evidence,
ResearchJob, Report/AnalysisRequest, chat, PDF, provider/payment interfaces and Android WebView.
Flutter retained; no new project/framework migration. Master supersedes old teal/three-tab,
EN new-flow and verdict-last rules. Historical immutable reports keep their saved content.

## Requirement → Code → Test → Evidence → Status

Code paths below refer to existing `backend/app/` or `apps/web_preview/`. New tests are in
`backend/tests/test_published_knowledge.py`; full baseline regression is also required.
Evidence directory: `deliverables/MasterLocal/`.

| Requirement | Code | Test | Evidence | Status |
|---|---|---|---|---|
| A audit/preservation | `scripts/verify_master_local.py` | full regression; original row comparison | `verification.json` | PASS |
| B contracts/domain | `models/knowledge_ops.py`, `schemas/knowledge.py`, f080/f081 | fresh SQLite down/up; PostgreSQL offline SQL | migration logs | PASS local; PG runtime NOT_RUN |
| B identity/markets | `knowledge_import.py`, `catalog_buyer.py` | aliases, transition year, contradictions, source scope | coverage matrix | PASS mechanism; real US coverage only |
| B AZ/RU/design | `catalog-copy.js`, `catalog-views.js`, `styles.css` | browser AZ/RU, 360/390/430, 150% text | `screens/`, `browser-qa.json` | PASS sampled browser; physical QA deferred |
| C bounded importer | `knowledge_import.py`, editable manifest | checksum/dedup/resume/lease/cancel/ZIP/SSRF/quarantine/dry-run | real cached EPA + tests | PASS |
| C publication/admin | `routes/knowledge.py`, revisions/reviews | staged correction diff, atomic locks, rollback active evidence | pytest, editor controls | PASS API; complete browser admin walk-through not performed |
| C source policy | `knowledge_registry.py` | pause, rights, source-specific allowlist | `source-registry.json` | PASS gates; external rights unresolved |
| C fallback research | `catalog_research.py`, `knowledge_worker.py` | owner/cancel/lease/retry/budget/sync bypass | pytest | PASS mechanism; local worker disabled |
| C full catalogue content | EPA + generic JSON/CSV imports | conservative mapping incl. FCEV | coverage/matrix | PARTIAL: 1,423 configs, zero complete dossiers/generations |
| D buyer filters/state | `catalog-views.js`, `catalog_buyer.py` | strict budget/AT/NA/UNKNOWN; home→wizard→results→dossier | five screens × AZ/RU | PASS |
| D resolver/ranking | deterministic service | exact/ambiguous/conflict/absent/unsupported; no silent relaxation | browser: 0 confirmed, 87 uncertain versions under selected filters | PASS; unsupported priorities unscored |
| D AZ asking prices | `MarketObservationInput`, existing MarketListing | reviewed import, immutable duplicates/conflicts, freshness/identity hash | isolated tests | PASS mechanism; zero real AZ observations imported |
| E dossier | `catalog_buyer.py`, same Report | immutable bilingual snapshots, grounded chat | actual dossier | PASS factual template; full expert content incomplete |
| E comparison/TCO | CostScenario, Decimal, same Report | 2/3 cars, PHEV/BEV, unknown != 0, purchase separate | actual UI 7,304.64 AZN/24mo | PASS |
| E editorials/favorites | EditorialPublication + admin/API/UI | applicable evidence, draft gate, visible source links, owner favorites | three stored AZ/RU research articles | PASS mechanism; cross-generation content awaiting evidence |
| F VIN/listing/plate | existing history/payment stack | baseline auth/callback/idempotency; AZ plate UI fallback | pytest + screenshot | PASS regression; no new live history call |
| F concept products | configurable 7/+10/17 AZN | baseline mock payment tests | inactive concept configuration | PREPARED; not live |
| Assets | private originals/WebP/rights/scope | wrong facelift rejects, auth preview, approval/revocation | `asset-manifest.json` | PASS mechanism; actual vehicle images pending IMAGE_QA |
| G builds | existing builder, release module cache | APK signature, pytest, Ruff, JS regression/syntax | APK + verification | PASS local |
| G backup/restore | `local_backup_restore.py` | new destination, SHA/counts/integrity/FKs | `backup-restore.json` | PASS SQLite; PG restore NOT_RUN |
| G deployment | isolated Compose PG/API/worker/Caddy + dependency hashes | static YAML + PG offline SQL | package/runbook | READY_NOT_DEPLOYED; owner deferred |

## Actual coverage and costs

31 makes, 199 model families, 1,423 published US local research configurations.
0 verified generations, complete dossiers, commercial versions, approved vehicle images.
737 body, 1,290 displacement, 1,423 transmission family/drive, 1,289 combustion consumption,
174 electricity values; zero seats/clearance values. Unspecified automatic does not prove AT;
missing aspiration does not prove NA. SUV class does not prove crossover. No missing facts invented.

One successful free EPA ZIP download in three attempts (two TLS failures); subsequent cached
normalization/correction made no HTTP calls. Paid cost USD 0.00, no new Auto.dev/ClearVIN/history
request. Provider rate limits unverified. Public availability is not a commercial licence.
Other regional sources retain permission/availability blockers. No account/session metadata exported.

Local worker is disabled and UI says so. Deployment config enables API/worker queue together
only after future operator start. Physical HONOR, keyboard/insets and PostgreSQL/Docker runtime
have not passed. Owner deferred phone and Hetzner; they did not block independent local work.

Next incomplete step: acquire permitted generation/aggregate/service and dated AZ market evidence,
stage/review/publish it through existing imports; approve exact-model image rights/applicability.
Then resume physical-device and isolated PostgreSQL verification in the later authorized phase.
No automatic deployment, paid request or fabricated PASS.
