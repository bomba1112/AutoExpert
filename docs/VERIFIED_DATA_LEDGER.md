# Verified data implementation ledger · 20 September 2026

Overall PARTIAL. Existing STAGE6_1, backend 0.8.1 / Android 0.8.1-alpha. No new project,
paid provider calls or deployment. Device acceptance deferred by owner.

| Requirement | Code | Real data | Verification / evidence | Status |
|---|---|---|---|---|
| Preserve baseline | audit_verified_catalog.py; verify_verified_data.py | 1,423 EPA source candidates and historical rows retained | 267 baseline tests; historical-preservation PASS; no broken provenance | PASS |
| AZ market priority | market_priority.py; az-market-priority-policy.json | Seven owner-selected brands; 52 US source families, three Skoda non-US draft candidates | test_market_priority.py; CHECKPOINT_AZ_MARKET_PRIORITY.md | ACTIVE; exact local counts unknown |
| Turbo role and optional import | market_discovery.py; strict schema; f083 | Zero Turbo records imported; REFERENCE_ONLY registry entry | No crawler; no export required; official-dealer channel separate | PASS for owner override; secondary prevalence queue unpopulated |
| Batch technical research | run_az_priority_batch.py; PriorityHTTP; existing ResearchJob worker | 52 families attempted, 51 have results; 46 PARTIAL, five COMPLETE, one unresolved label | 58 recorded attempts; per-source receipts/status; canonical-name failure fixed and retried | REVIEW REQUIRED; not full dossiers |
| Source normalization/publication | NRCan adapter; existing ImportJob; reviewed boundary corrections | 2,232 CA rows; 37 corrected model-boundary assignments; 3,655 total, 204 families | Actual four imports; no Cartesian products; no missing fact provenance | PASS for source facts; factory identity partial |
| Dated ownership evidence | verified_ownership.py; ownership_evidence.py; f082 | Five AZ official energy observations | Strict schema, review/publication gate, source links | Energy populated; other ownership categories empty |
| 24-month costs | existing OwnershipCostEngine → ownership_cost.py | Eight source-based sample snapshots, all PARTIAL | Decimal/calendar/tariff boundaries, service history, fitment, prices, package overlap | Mechanism implemented; full actual costs unavailable |
| Existing reports/AZ/RU | ownership-panel.js; catalog_buyer.save_dossier; PDF projection | Source-linked cost snapshot stored in existing Report | Browser numeric parity and saved-report check; immutable snapshots in tests | PASS for tested paths |
| UI/accessibility | existing AZ/RU client and comparison | Published source data; partial labels | 15 width/overflow checks at 360/390/430, normal and large text; screenshots | PASS for changed flows |
| Asset pipeline | existing VehicleAsset workflow; prepare_verified_assets.py | Four rights-page candidates; downloads HTTP403; zero stored/pending/approved | Source index explicitly says blocked, not a photo contact sheet | BLOCKED original downloads; human approval not performed |
| Factory dossiers and maintenance | existing resolver/editorial/evidence framework | Zero new verified generations/full dossiers/schedules/fitments/parts/labor | No unsupported promotion; sources/gaps recorded | NOT COMPLETE; independent factory research remains |
| Portability/recovery | export/replay/backup scripts; package_verified_data.py | 3,655 catalog rows + five ownership records replayed twice; private backup separately | No duplicate replay; 39 tables/137 files restored; integrity/FK PASS | PASS local; PostgreSQL runtime untested |
| Regression/build | verify_verified_data.py; Android build.py | APK 81 | 305 tests, ruff, JS, SQLite up/down/up and PostgreSQL offline SQL PASS; APK v2/v3 signatures | PASS local; real device deferred |

The uniform NRCan queue is historical and paused by the AZ-first policy. Owner-selected makes do
not need Turbo proof before technical research. Exact listing counts are optional manual input,
not a blocker for independent work. Seller market claims never overwrite official technical identity.

Resume and specific limitations: CHECKPOINT_VERIFIED_DATA.md, CHECKPOINT_AZ_MARKET_PRIORITY.md,
VERIFIED_DATA_OPERATIONS.md. MasterLocal delivery remains unchanged.
