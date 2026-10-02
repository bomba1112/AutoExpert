# Auto Expert 2.0

Current delivery: **US base catalogue / AZ-RU, backend 0.8.1**, existing project.
Active scope: 17 owner-priority makes, US only, MY2000+. Skoda is excluded.
Historical other-market records remain preserved. No Turbo crawler or export is required.

Published `us-base-catalog-07`: A-Class177 MY2019–2020, X1E84 MY2013–2015,
X3F25 MY2014–2015, Q7 4L MY2014–2015, A3 8V MY2015–2016, Atlas MY2018–2019,
AccentRB MY2016–2017, OptimaTF/QF MY2012–2013, RAV4IV MY2013/2015,
SentraB17 MY2016–2018, CivicIX sedan MY2013/2015, MalibuVIII MY2013–2015,
RangeRoverL405 SWB MY2014–2016, NX MY2015–2017, QX60L50 MY2014–2016,
CompassMK MY2014–2016, OutlanderSport MY2014–2016, EscaladeIV MY2015–2016,
only the exact evidenced engine/transmission/body/trim/drive combinations.
Complete named delta, cumulative strict/conditional lists and technical fields are in the checkpoint.
**132 new available configurations**, four existing X5 MY2014/2016 records enriched
and nine evidence-only refreshes. Actual new confirmed annual field values:2,521+4;
these are exact-applicability field counts, not independent discoveries.
Cumulative base mechanics: **55 models / 65 generations / 730 year configurations / 16 of 17 makes**.
Unchanged strict criterion including documented seats: **43 models / 500 configurations / 15 makes**.
The old143, batch05 ten, batch06 twenty-four and batch07 fifty-three seating gaps remain separate.
No unknown seats were relabelled. Repeated document hashing within one validation was optimized;
same32-record benchmark21.396s→4.969s. Credibility and publication criteria remain unchanged.
Tesla Model S MY2016 and Model 3 MY2020 remain specific research scopes, not a blanket make hold.
**Overall stage PARTIAL**, not full 17-make coverage. Publication/search rules and all previous
revisions, including the historical batch05 correction, remain intact.
All 17 makes and their current coverage are explicit in the checkpoint.
Ordinary search admits evidenced base cards without seats only when seats are unconstrained;
unknown hard constraints never match. Approved UI files are unchanged in this batch.
Resolver/filter audit PASS; 345 regression tests PASS; browser AZ/RU QA performed.

Approved white/blue flow: home → filters → ranked results → vehicle profile, in AZ/RU.
The top recommendation explains evidence and ties; competitors are grouped by model.
The profile has a summary, four colorful categories and eleven technical groups.
Unknown facts stay unknown. Prices, ownership, deep dossiers and images are not catalogue gates.
Phone/Hetzner remain deferred. Existing APK 0.8.1-alpha (81) was not rebuilt by this batch.

Start with [the current US checkpoint](docs/CHECKPOINT_US_BASE_CATALOG.md),
[batch coverage](deliverables/VerifiedData/us-base-catalog-07/coverage.json),
[current acceptance evidence](docs/BATCH07_VALIDATION.md) and
[deployment runbook](deploy/README.md). Earlier checkpoints are historical records.

Start with a car description, a listing URL or VIN, or a comparison of two/three cars.
VIN is optional. All flows reuse the existing research, evidence, Report/AnalysisRequest,
chat and PDF pipeline. Seller claims, configuration facts and vehicle history stay separate.
RU/AZ/EN use the same saved facts. Local DeveloperMode opens the owner's available data;
Simulate User Paywall remains a separate opt-in. External paid data calls are not authorized.

See [the preceding checkpoint](docs/CHECKPOINT_BUYER_EXPERIENCE_V1.md),
[product rules](docs/BUYER_EXPERIENCE_V1_PRODUCT_RULES.md) and
[acceptance evidence](deliverables/BuyerExperienceV1/acceptance_summary.md).
Do not restore an older stage archive over these changes.

## Current local launch

The backend has already been started for this delivery. `Start-Local.ps1` provides the
repeatable entry point from this project: it starts the existing virtual environment,
checks backend 0.8.1 / buyer API 1, and backs up SQLite before pending migrations.
`-Restart` restarts only this project's identified preview process; `-InstallApk` updates
an attached known HONOR and applies adb reverse. Device commands run only with explicit
`-ConnectDevice` or `-InstallApk`; normal start/restart does not query ADB.
The Android dev origin remains `https://appassets.autoexpert.local`, with API
`http://127.0.0.1:8000/api/v1`. This is a local alpha, not a public deployment.

Earlier 0.8.0 acceptance covered listing/VIN examples. New 0.8.1 browser QA covers source-backed
costs, comparison, saving and AZ/RU at 360/390/430 px and large text. The published catalogue
now separates US and Canadian source rows; choosing one as a reference
never certifies an unknown listing's original market. Maintenance, chassis, owner reviews
and market data have substantial coverage gaps. The configured chat provider is
source-guided deterministic, not a general LLM conversation service.

Artifacts: `deliverables/AutoExpert_2_0_Alpha_0.8.1.apk`, the VerifiedData source/deployment
and QA ZIPs, and `deliverables/VerifiedData/SHA256SUMS.txt`. The source archive excludes
`.env`, SQLite data, sessions, backups, signing keys and generated deliverables.
The previous MasterLocal archives remain unchanged. Deployment requires the separate public
fact bundle or a private local backup; research profiles and accounts are not in the public bundle.

## Historical implementation context

The notes below describe the retained earlier capabilities; they do not replace the
Buyer Experience V1 product rules or the current checkpoint.

Evidence-grounded VIN precheck and Vehicle Knowledge Profile dossier for Azerbaijan
first, with Russia-ready country separation and Azerbaijani, Russian, and English
presentation layers.

The earlier primary slices were:

`Home → VIN resolution → safe precheck teaser → mock entitlement → full VIN history +
vehicle dossier → grounded Auto Expert Chat`.

`Make + model + year → persistent ResearchJob → official provider router → normalized
sources/evidence → quality gate → stored Vehicle Knowledge Profile → dossier`.

Stage 3 adds a separately versioned, source-linked `REAL` model dossier for
`Toyota / Camry / XV70 / USA / 2019 / 2.5 A25A-FKS / 8AT`. The deterministic VIN
history remains `DEMO`; the API and Web Preview display both origins independently.
Stage 4 keeps that reviewed manifest only as a regression fixture and adds an independent
automatic path. Production startup and `/research/jobs` do not import or execute the
Camry seed.

Stage 5 adds market-aware `VIN | CHASSIS_NUMBER | FRAME_NUMBER` validation, a two-phase
identity/enrichment flow, official configuration-label lookup, and a
`RESOLVED | AMBIGUOUS | INSUFFICIENT_DATA` variant resolver. A user selection resumes
the same persistent job and reuses cached provider responses; engine hints remain
unconfirmed unless an official candidate supports them.

Version 0.6.5 includes the Stage 6.1 real-device fixes: startup, Windows TLS trust,
automatic sample-VIN research, localized consumer copy, readable dossier layout, and
contextual inspection advice. The server controls developer access around the research flow.
Local preview defaults to `DeveloperMode=true`: an authenticated owner can open that
owner's VIN history, dossier, sources, and unlimited grounded chat without a payment
entitlement. The independent **Simulate User Paywall** switch restores the locked teaser,
configured 5 AZN price, mock payment, entitlement, and question limit. Production startup
rejects `DeveloperMode=true`.

The original fit, market, owner-feedback, and ownership-cost engines remain available as
reusable backend capabilities, but the fit questionnaire is no longer the primary UI flow.

The LLM is not an automotive database. Deterministic engines prepare immutable evidence
and chat-context snapshots; replaceable `LLMProvider` / `ChatLLMProvider` adapters may
only explain facts contained in those snapshots. Market prices, owner-material mention
shares, and ownership costs are calculated outside the LLM.

## Repository

- `backend/` — FastAPI, SQLAlchemy, Alembic, provider adapters, report pipeline, tests.
- `apps/client/` — Flutter client shared by Android, iOS, and Web.
- `apps/android_demo/` — Android 2.0 alpha shell that packages the current mobile UI and
  connects to the existing backend through a configurable development endpoint.
- `apps/web_preview/` — dependency-free mobile-first client served by FastAPI.
- `data/seed/` — explicitly marked development/demo fixtures only.
- `data/seed/real_camry_2019_us_manifest.json` — reviewed Stage 3 source manifest and
  expected quality counts for the real Camry model dossier; fixture only, not production
  initialization.
- `docs/` — architecture, workspace audit, and delivery checkpoints.
- `docker/` — backend container definition.

## Backend development

Requirements: Python 3.12 and `uv`.

```bash
cp .env.example .env
uv sync --group dev
uv run alembic -c backend/alembic.ini upgrade head
uv run python -m app.db.seed_demo
uv run uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000/docs` in development. Run checks with:

```bash
uv run pytest
uv run ruff check backend
```

SQLite is the development default. For PostgreSQL, set
`AUTOEXPERT_DATABASE_URL=postgresql+psycopg://...`; business services and ORM models do
not change.

## VIN-first Phone Web Preview

The Web Preview is an additional client for hands-on MVP testing; it does not replace
the Flutter application. The runner applies migrations, idempotently seeds only rows
marked `is_demo=true`, and serves the API and mobile UI in one process. The listing-link
parser is intentionally disabled at P1; VIN input and automatic USA make/model/year
research are live.

One-time setup from the repository root:

```bash
cp .env.example .env
uv sync --group dev
```

Start from the repository root (the runner resolves its own paths before loading settings):

```bash
uv run autoexpert-preview --host 127.0.0.1 --port 8000
```

On Windows, `run-preview.ps1` also works when invoked by absolute path from any directory.
It selects this checkout explicitly with `uv --project`; migrations, `.env`, and the default
SQLite database belong to this Stage 6.1 root. `-BindAddress`, `-Port`, and `-Reload` are
optional. The original `cd backend; uv run python -m app.run_preview` command still works.
Use `--host 0.0.0.0` explicitly only when LAN access is needed.

On the same computer open `http://127.0.0.1:8000/preview/`. From a phone on the same
Wi-Fi network use the computer's LAN IPv4 address, for example
`http://192.168.1.25:8000/preview/`—never the phone's `localhost`. The language screen
creates a separate protected demo user automatically; no username or password is needed.
See [`docs/PHONE_PREVIEW.md`](docs/PHONE_PREVIEW.md) for exact phone and firewall steps.

Choose “VIN or chassis number” or “Make, model, and year” to create a persistent
`/api/v1/research/jobs` job. On a cache miss the USA router calls vPIC, NHTSA vehicle
configuration labels, recalls, complaints, and the official manufacturer-communications
bulk archives. Successful normalized results are cached for 24 hours and become linked
`SourceRecord`, `TechnicalEvidence`, and owner observations.
Unknown generation/powertrain fields remain unresolved rather than being copied from the
Stage 3 fixture. The combined test flow may then pair this real model dossier with the
explicitly synthetic VIN-history fixture; the UI never presents the latter as a record for
an actual VIN.

The developer-review example `3FA6P0HD0KR114795` is a Ford-compatible 2019 Ford Fusion
VIN. Its bundled history remains explicitly synthetic `DEMO DATA`; unresolved powertrain
fields stay unresolved. The legacy Toyota fixture remains associated only with Toyota
profiles and is never substituted into a Ford report or VIN mask.

### Developer review controls

The local `.env.example` defaults are:

```text
AUTOEXPERT_DEVELOPER_MODE=true
AUTOEXPERT_DEVELOPER_SIMULATE_USER_PAYWALL_DEFAULT=false
```

With these defaults, **Insert test VIN** runs automatic research against official sources;
**Open full dossier** then opens the owner-scoped report without a precheck or payment.
Use **Simulate User Paywall** in the blue developer toolbar to
review the normal locked flow and mock payment. Set
`AUTOEXPERT_DEVELOPER_MODE=false` to verify ordinary access rules without the toolbar.

North-American check-digit validation is applied only to USA/Canada VINs. Korean VINs
remain 17-character identifiers but are not rejected by that regional checksum. The
Japan strategy accepts a VIN or a separately typed chassis/frame number. Markets without
an active provider finish `PARTIAL` with unknown fields rather than calling a USA adapter.

## Android 2.0 Alpha

The Android alpha reuses the current Web Preview assets inside the existing
`com.autoexpert.demo` shell. Business logic, provider calls, ownership, DeveloperMode, and
paywall simulation remain in FastAPI; the APK contains no provider credentials or production
server URL. Its default development API endpoint is `http://127.0.0.1:8000/api/v1`.

On Windows, start the backend, connect the phone with USB debugging, and map the phone's
loopback port to Windows before opening the app:

```powershell
.\run-preview.ps1

adb reverse tcp:8000 tcp:8000
adb install -r deliverables\AutoExpert_2_0_Alpha_0.6.6.apk
```

Re-run `adb reverse tcp:8000 tcp:8000` after reconnecting or rebooting the phone. To build an
APK for a different development endpoint without editing source:

```bash
AUTOEXPERT_API_BASE_URL=http://127.0.0.1:8000/api/v1 apps/android_demo/build.sh
```

The alpha targets Android API 35, has a minimum API level of 24, uses portrait orientation,
and is test-signed. See [`apps/android_demo/README.md`](apps/android_demo/README.md) and
[`docs/CHECKPOINT_2_0_STAGE6.md`](docs/CHECKPOINT_2_0_STAGE6.md).

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The API container applies migrations before starting. The compose profile uses
PostgreSQL; secrets in the example are development-only.

## Flutter client

Requirements: a Flutter SDK with Android/Web toolchains and Xcode for iOS builds.

```bash
cd apps/client
flutter pub get
flutter gen-l10n
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

No server or model key is embedded in the client. Platform folders should be generated
once with `flutter create --platforms=android,ios,web .` on a machine with Flutter if the
checked-out environment does not already contain generated platform runners.

## Data integrity

- Every material fact carries `CONFIRMED`, `ESTIMATE`, `NEEDS_INSPECTION`, or
  `INSUFFICIENT_DATA`.
- In ordinary/user-paywall mode, a locked VIN endpoint exposes only counts and flags.
  Auction details, prices, photos, damage, odometer records, and the full timeline stay in
  the backend snapshot until a `VIN_REPORT_UNLOCKED` entitlement exists. Explicit local
  DeveloperMode may bypass that entitlement only after the same ownership check.
- Auto Expert Chat is always owner-scoped and ordinarily requires entitlement. Each session
  stores a versioned context snapshot and SHA-256 digest; its public DTO omits the context
  and raw VIN history. DeveloperMode makes the owner session unlimited; paywall simulation
  restores the configured user question policy.
- Chat answers are validated against snapshot evidence/source IDs and their original
  statuses. Missing market or cost data returns an explicit insufficient-data answer.
- Demo chat uses a deterministic `ChatLLMProvider`; no external model key or request is
  needed. `ChatAccessPolicy` can later select included, limited, unlimited, or subscription
  access without changing chat routes.
- A zero-record precheck cannot be purchased and explicitly warns that no connected
  record does not guarantee a clean history.
- `CONFIRMED` evidence and claims require traceable evidence/source identifiers.
- A report stores input, evidence, calculations, and generated text snapshots.
- Owner mention percentages refer only to the reviewed sample and are hidden for fewer
  than ten unique materials.
- Demo fixtures are flagged `is_demo=true` and `data_origin=DEMO`; real model evidence is
  marked `is_demo=false` and `data_origin=REAL` throughout source, catalog, dossier, and UI.
- A model-level fit result never certifies the physical condition of a specific vehicle.
- The Camry model dossier uses reviewed real sources. The current Camry VIN/history
  content is still deterministic synthetic demo data, never a claim about a real VIN.
