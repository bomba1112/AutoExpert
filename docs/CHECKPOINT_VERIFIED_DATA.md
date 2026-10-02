# Auto Expert 0.8.1 · local checkpoint · 20 September 2026

Overall **PARTIAL**, not acceptance of the entire verified-data assignment. Existing project,
existing UI/Report/worker/import architecture. No new stage/project was created.

## Actual data and completed work

- Baseline retained: 1,423 EPA US source rows and all historical data. Added 2,232 licensed Canadian
  NRCan configurations through reviewed imports. Total 3,655 rows, 31 makes, 204 model families.
  A separate reviewed correction fixed 37 prefix-based model assignments without deleting history.
- Five dated official AZ energy observations published. Ownership calculation, scoped evidence,
  calendar/Decimal rules and existing report/comparison UI implemented. No invented service rates,
  parts prices or fitments; all eight exported scenarios are explicitly PARTIAL.
- Owner override is active: Mercedes-Benz, BMW, Audi, Hyundai, Kia, Volkswagen, Skoda. Uniform
  all-brand expansion disabled. Turbo is manual external market reference only; no export exists
  or is awaited, no crawler or bulk listing database was built. Optional import contracts remain
  inactive and require real source rights; no fictional export/permission was created.
- First US wave executed on 52 families, one official source-year each. Latest results: 46 PARTIAL,
  five worker COMPLETE, one SOURCE_MODEL_UNRESOLVED. Mercedes-Benz canonical-name collision fixed;
  failed attempts preserved and bounded retries succeeded. BMW source lookup uses the same-year
  official configuration label, without renaming the model family or asserting all trims match.
- Source receipt log contains 540 request attempts / 537 receipted HTTP requests, plus eight
  isolated diagnostic attempts. Early receipts lack HTTP status; they were not reconstructed.
  Paid calls zero. Archive reuse is checksummed and recorded, not charged as network calls.

## Queue cursor and next concrete work

The first US source-year wave is finished; no batch is running at this checkpoint. Journal:
`deliverables/VerifiedData/market-priority/batch-status.json` (58 attempts retained).
The per-model coverage/status table is `CHECKPOINT_AZ_MARKET_PRIORITY.md`.

1. Review source-specific lookup/applicability before publication: B-Class Electric Drive 2017
   cannot be safely mapped to vPIC B-Class automatically. Some NHTSA recall endpoints reject
   broad family names; source errors do not mean zero recalls. BMW 330i lookup covers that label,
   not every 3 Series version. Ambiguous candidates require variant-scoped research.
2. Add applicable manufacturer model-year/generation/engine/transmission/service documents for
   these priority models. Skoda Octavia/Superb/Kodiaq stay in non-US discovery; no US version is
   invented. Then advance later source-year waves and KR/EU/CN versions of the same families.
3. Populate maintenance → confirmed fitments → comparable dated AZ parts/labor evidence;
   complete rich AZ/RU dossiers and the remaining ownership/UI scenarios. These are unfinished
   implementation/research tasks, not solely external-access blockers.
4. Secondary US queue stays empty until actual manual market observations support its order.
   Exact Turbo counts/market distributions are optional manual inputs. Their absence does not
   stop the primary queue. Do not turn catalogue size into local popularity.

Resume commands (no provider download is triggered by opening the app):

```powershell
.\Start-Local.ps1 -Restart
.venv\Scripts\python.exe scripts/checkpoint_az_market_priority.py
# Review current evidence first; this selects a different existing official source-year per family:
.venv\Scripts\python.exe scripts/run_az_priority_batch.py --run-free --year-wave 1 --max-models 12 --max-jobs 12
.venv\Scripts\python.exe scripts/checkpoint_az_market_priority.py
```

Default wave-0 reruns skip recorded model/year entries. `--retry-failed` is explicit and does not
reset the worker's two-attempt cap. Shared vPIC/archive bytes are reused for one day with checksum
verification. The public app's background worker flag remains unchanged.

## Verification and artifacts

305 tests PASS; ruff/JS PASS; SQLite fresh/up/down/up PASS; PostgreSQL migrations compile offline.
Historical-preservation and database integrity PASS. Public factual replay twice: 3,655 catalog
rows + five energy records, no duplicate jobs/rows. Backup/restore: 39 tables, 137 checked files,
206,299,910 bytes, separate restore directory; live DB never overwritten.

Browser checks cover cost/source/save/comparison, AZ/RU numeric parity, 360/390/430 px and large
text. APK 0.8.1-alpha/81 rebuilt and v2/v3 signature verified. Phone installation/real-device QA
are deferred, and Hetzner was not touched. PostgreSQL runtime is untested (Docker unavailable).

Acceptance report, snapshots, screenshots, public fact bundle, coverage and packages are in
`deliverables/VerifiedData`; APK is `deliverables/AutoExpert_2_0_Alpha_0.8.1.apk`.
Private DB/raw caches/backups/signing/environment files are excluded from public packages.
The public portable bundle contains published catalogue and energy facts, not account data or
the private research/profile history. Deployment remains a separate owner-deferred action.

No new verified factory generations, full dossiers, maintenance schedules, confirmed fitments,
local part-price observations, labor quotes or approved vehicle images are claimed. Four image
source candidates have blocked downloads and zero stored files. This checkpoint preserves the
cursor and remaining work; it is not a claim that the full data-stage is complete.
