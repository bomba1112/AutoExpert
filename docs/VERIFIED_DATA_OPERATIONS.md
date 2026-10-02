# Verified data 0.8.1 — local operations

This continues STAGE6_1. The existing client, Report/PDF/chat and staged knowledge pipeline remain in use.
Phone, ADB installation and Hetzner deployment are deferred. `Start-Local.ps1` now performs device
commands only with the explicit `-ConnectDevice` or `-InstallApk` switch; the ordinary start/restart
does not query ADB. No such switches are needed for this stage.

## Current data and boundaries

The original 1,423 EPA US source configurations are preserved. Four reviewed NRCan imports added
2,232 CA configurations. A reviewed correction separated 37 rows at overlapping model-name
boundaries, including Corolla Cross and IONIQ 5/9. Total: 3,655 source configurations, 204 normalized
families and 31 makes. These are research candidates with sourced basic facts, not 3,655 complete
factory configurations. Generation, exact aggregate codes and trim are not inferred.

NRCan facts are licensed under the Open Government Licence – Canada. Attribution is attached to
cards, comparison and dossier. EPA and AZ tariffs retain LOCAL_RESEARCH scope: the production
environment does not expose unapproved commercial data. The source package does not grant new rights.

Five dated official energy observations are published: AI-92 and diesel for July 2024–December 2025
and from January 2026, plus 2026 household electricity tiers/fixed charge. AI-95/98 and consumer
public charging prices are not established. Wholesale supply to charger operators is not a consumer
tariff. Fuel grade selection is an explicit scenario input; consult the exact vehicle manual.

No full dossiers, verified generations, maintenance schedules, fitments, local parts offers or labor
quotes were published in this batch. JSON/CSV contracts, calendar/cost rules and UI are implemented;
this mechanism readiness must not be counted as data coverage. The first US technical wave
attempted 52 model families across six makes: 46 PARTIAL, five worker COMPLETE, one source label
unresolved. These are review results, not new full dossiers. Skoda stays in the non-US queue.
Richer generation-specific AZ/RU content remains unfinished implementation/research work.

## Resume without downloading everything

Run from the project root:

```powershell
.\Start-Local.ps1 -Restart
.venv\Scripts\python.exe scripts/audit_verified_catalog.py --phase after
.venv\Scripts\python.exe scripts/checkpoint_az_market_priority.py
# After reviewing current model/year results, advance to another source-year wave:
.venv\Scripts\python.exe scripts/run_az_priority_batch.py --run-free --year-wave 1 --max-models 12 --max-jobs 12
.venv\Scripts\python.exe scripts/export_verified_delivery.py
```

Existing manifests/jobs and cached checksums are reused. The active owner-priority policy is
`data/manifests/az-market-priority-policy.json`; `az-market-batch-queue.json` records model coverage.
The prior uniform DRAFT queue is historical and uniform NRCan expansion is disabled. Turbo is
manual external reference only. No export exists or is awaited; no permission to crawl is assumed.
Model order is an editorial draft within the seven owner-selected brands, not a measured local
top-100. Listing counts and seller-market shares remain unknown optional manual inputs.
`Rəsmi diler` is a sales channel, not an original market. Do not rewrite the baseline or manually
promote all rows. Source receipt details are in `deliverables/VerifiedData/acquisition-ledger.json`.
Acquisition is a separate explicit CLI operation, never a side effect of opening a card.

The NRCan row cap is 12 recent rows per family/dataset within 2015–2026 for this batch. It is a
manifest sampling budget, not a product/model limit. Subsequent imports must follow the AZ policy.
The full source CSV preserves other candidates. Conventional NRCan data does not reliably identify
ICE vs HEV architecture: COMBUSTION_UNSPECIFIED stays explicit. AV/AM codes do not establish belt
CVT/eCVT or DCT internals; AV7 is not seven physical gears. Market-specific names are retained.

## Manual prices, labor and maintenance

Generate blank contracts with `scripts/verified_import_templates.py`; files are under
`data/templates/ownership`. CSV columns are the complete OwnershipRecord fields, with JSON strings
inside `variant_ids`, `limitations` and `data`. Empty `effective_to` means no known end. JSON input
is an array of the same records. Contract keys are technical identifiers, not translated free text.

1. Establish permission/storage/display rights for the source in the existing registry.
2. Upload the permitted CSV/JSON in the protected editor's Document form. The editor can download
   the same schemas from `/knowledge/admin/ownership/contracts`.
3. Enqueue an ImportManifest with `source_id`, `document_id`, `parser: ownership-csv-v1` (or
   ownership-json-v1), and a specific `selection_basis`. Use `dry_run: true` for validation first.
4. Process via the existing knowledge worker command described in KNOWLEDGE_OPERATIONS.md.
   Inspect differences and quarantine errors; approve then publish through the ordinary editor.

No sample price observations are included in production templates. Exact variant IDs are mandatory
for maintenance/fitment, and identity hashes invalidate applicability when aggregate/market identity
changes. Seller claims are excluded from confirmed fitment. A labor quote must specify dated offer,
operation, region, unit, material inclusion and overlap; a package is charged once per service date.
Only fresh comparable new-part offers with a confirmed fitment enter costs; at least three distinct
sellers are required for the displayed sample median. Unknown delivery/additional cost stays a gap.

## Calculation and reporting

The dossier and 2–3 vehicle comparison call the same existing OwnershipCostEngine.
Calculation uses Decimal, calendar-month day counts and ROUND_HALF_UP to 0.01 AZN after summing.
Time/distance whichever comes first, first service, overdue service and unknown history are distinct.
Inspection does not become replacement. Severe conditions must be chosen from the applicable schedule.

Fuel is allocated daily around tariff effective dates. Household charging is the incremental bill
after baseline household usage; the existing meter's fixed fee is not charged to the car again.
GRID consumption already includes charging losses; BATTERY consumption needs explicit losses.
PHEV requires an electric-distance share and retains any gasoline used in that mode. A household
tariff change within a billing month remains partial until billing allocation is specified.

The snapshot includes source facts, revision IDs, scenario, quantities/units, tariff structures,
operation/material/package breakdown, unrounded amounts, rounded totals, missing items and rules
version. Future prices are the last known price held as an explicit assumption. Purchase, depreciation
and repair reserve are separate. Missing values never imply zero. A winner is not inferred from gaps.

Save uses the existing Report with both AZ/RU projections. A hash check rejects saving if evidence
changed after the visible calculation; the user must recalculate. Saved snapshots remain unchanged
after subsequent price publication. The dossier PDF uses this stored Report data, not another model.
Eight exported 24-month scenarios are samples with stated assumptions; all are PARTIAL.

## Offline transfer, verification and recovery

`deliverables/VerifiedData/published-data` contains normalized source facts and scoped registry
configuration without user/account/session data. On a clean migrated local database:

```powershell
.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.venv\Scripts\python.exe scripts/replay_verified_data.py deliverables/VerifiedData/published-data
# After inspecting staged facts and rights, explicitly publish:
.venv\Scripts\python.exe scripts/replay_verified_data.py deliverables/VerifiedData/published-data --publish-reviewed
```

The current portable bundle has only global tariff records. Future variant-scoped maintenance or
fitment exports require remapping target IDs; do not transplant IDs between unrelated databases.
Replay does not import existing users; it creates an inactive technical audit actor with an unknown
random credential. This actor is not a human image reviewer and cannot be used to log in.

```powershell
.venv\Scripts\python.exe scripts/verify_verified_data.py
.venv\Scripts\python.exe scripts/validate_verified_replay.py
.venv\Scripts\python.exe scripts/local_backup_restore.py --output deliverables/VerifiedData
.venv\Scripts\python.exe apps/android_demo/build.py
.venv\Scripts\python.exe scripts/package_verified_data.py
```

Backup/restore includes the SQLite database and private knowledge files with checksums and manifest,
restoring into a new local directory. Private backups are not in deliverable archives. PostgreSQL
migrations compile offline; PostgreSQL runtime/Docker and server deployment remain untested/deferred.
APK signing/build is not real-device acceptance. New evidence goes to VerifiedData; MasterLocal
archives and the previous checkpoint remain unchanged.

## Images and remaining source actions

Four source/rights URL candidates are in `vehicle-image-candidates.json`; all original-file downloads
returned HTTP403. Zero files reached VehicleAsset and zero images are approved. The generated review
index is a blocked-source index, not a completed photographic contact sheet. Do not retry with
credentials, altered access controls or fabricated images. When a permitted file is available, the
existing upload stores renditions permanently in IMAGE_QA; only a real reviewer event can approve it.

`verified-source-checks.json` separates permission blockers, technical failures, insufficient
applicability and work not yet executed. The next independent work is the factory generation/service
and review of the NHTSA model-year batch, followed by source-specific identity mappings and later
years/markets. B-Class Electric Drive 2017 has no safe automatic vPIC mapping. Some family labels
produce recall endpoint errors; do not infer zero recalls. Complaint rows are capped at 100 per
query, so recorded counts are not complaint totals or reliability rates.
A recall/TSB/complaint must remain distinct from a KnownIssue
and from any defect on a particular vehicle. Do not treat this checkpoint as completed acceptance.
