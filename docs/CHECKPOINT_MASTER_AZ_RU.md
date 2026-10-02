# Checkpoint — Master AZ/RU 0.8.0, 19 September 2026

Existing STAGE6_1 continued. Local implementation ready for review; overall product acceptance
PARTIAL; deployment READY_NOT_DEPLOYED. Owner explicitly deferred Hetzner and phone checks.
No new project, framework migration, paid integration or live payment.

Implemented AZ/RU home, two buyer entry paths, persistent filters, resolver/results/dossier,
2/3 comparison and Decimal costs; private raw/source registry, generic JSON/CSV/EPA imports,
durable jobs, staging/review/atomic publication, locks/rollback, protected images/QA,
editorials/favorites and reviewed dated asking-price imports. Same Report/chat/PDF and Android
WebView shell. f080/f081 migrations; isolated deployment package and backup/verification tools.

Actual data: 31 makes / 199 model families / 1,423 US configurations; zero verified generations,
complete dossiers, commercial versions or approved vehicle images. One free EPA bulk download,
three attempts, paid cost USD 0.00. Three stored research articles compare source-backed ICE/HEV
consumption with limitations; they are not three fully researched generations.

## Reproduce from the project root

```powershell
.\Start-Local.ps1 -Restart
.venv\Scripts\python.exe apps/android_demo/build.py
.venv\Scripts\python.exe scripts/verify_master_local.py
.venv\Scripts\python.exe scripts/export_master_evidence.py
.venv\Scripts\python.exe scripts/local_backup_restore.py
.venv\Scripts\python.exe scripts/package_master_local.py
```

Preview http://127.0.0.1:8000/preview/; backend 0.8.0 / buyer API 1.
APK 0.8.0-alpha code80 uses local API 127.0.0.1:8000. Device connectivity needs a later authorized
adb reverse or reachable API. Built/signed does not mean phone-tested. Old device PASS is not
acceptance of this APK. Local worker is disabled; no background work is promised.

Final results/hashes: deliverables/MasterLocal/verification.json, acceptance_summary.md and
SHA256SUMS.txt. Real AZ/RU application screenshots are under screens/. Baseline was 222 tests.
SQLite backup restored into a new directory with hashes/counts/integrity/FKs. Docker/PostgreSQL
runtime remains unverified. All original DB rows are checked against the private baseline.

Do not restore older archives over this project. Private .env/.localdata/.backups/.runtime/.signing
are excluded from delivery. Source ZIP has no live database/accounts. The current local database
remains populated; a clean machine needs reviewed imports (KNOWLEDGE_OPERATIONS.md).

Next incomplete step: permitted generation/aggregate/service/dated AZ market evidence and
manual exact-model image approval through the existing pipeline. Device and isolated PostgreSQL/
Hetzner checks remain for the later phase. No deployment was performed.
