# Delivery checkpoint

This file records implementation state. Product requirements are governed by the user
checkpoint supplied on 2026-09-11; this document does not replace or reinterpret it.

## Auto Expert 2.0 — Stage 6 Android Alpha

STATUS: APK READY / DEVICE UX REVIEW PENDING

- Existing `com.autoexpert.demo` shell now packages the current 2.0 mobile UI and uses a
  configurable development API endpoint; Stage 5 research/provider code is unchanged.
- Default Windows/USB path is `127.0.0.1:8000` through
  `adb reverse tcp:8000 tcp:8000`.
- Android 15/API 35 Package Manager installation and native Activity launch: PASS.
- DeveloperMode, Ford VIN isolation, Korean VIN acceptance, 17-section dossier, sources,
  grounded chat, simulated 5 AZN paywall, My Reports persistence, and AZ/RU/EN API/assets:
  PASS.
- APK Signature Scheme v2/v3 and archive integrity: PASS.
- The Work emulator's AOSP WebView renderer cannot complete visual automation without KVM
  and permitted socket/ptrace operations; physical-device UX review is the remaining manual
  acceptance step.
- Detailed evidence: `docs/CHECKPOINT_2_0_STAGE6.md`.

## Auto Expert 2.0 — Developer review flow

STATUS: PASS

- Version 0.6.1 adds backend-controlled `DeveloperMode`, enabled by default only for the
  local development configuration.
- Owner-scoped VIN history, dossier, sources, and grounded chat open without payment;
  chat is unlimited and no entitlement row is created.
- **Simulate User Paywall** independently restores the locked teaser, 5 AZN mock-payment
  flow, entitlement enforcement, and configured question limit.
- Ford example VIN `3FA6P0HD0KR114795` resolves to a Ford Fusion identity shell and is
  never paired with Toyota VIN/mask or powertrain data.
- Stage 5 baseline remains intact; full suite: `79 passed`.
- Detailed evidence: `docs/CHECKPOINT_2_0_DEVELOPER_REVIEW.md`.

## Stage A — Foundation

STATUS: PARTIAL

IMPLEMENTED:

- New Git repository and modular monorepo structure.
- FastAPI application, environment configuration, CORS, Scrypt password hashing, JWT,
  owner-scoped report access, and production placeholder-secret rejection.
- SQLAlchemy 2 domain model covering users, country/region profiles, vehicle catalog,
  sources, technical evidence, known issues, listings, costs, owner observations,
  requests, report snapshots, questions, payments, and analytics.
- Alembic initial migration; SQLite development and PostgreSQL connection paths.
- Dockerfile and PostgreSQL/API compose configuration.
- Flutter shared-source scaffold with adaptive Language and Home screens, API client,
  theme, and identical AZ/RU/EN localization catalogs.
- Idempotent, end-to-end synthetic fixture where every row is marked `is_demo=true`.

TESTS:

- Fresh SQLite migration to Alembic head: PASS.
- Alembic schema drift check: PASS (`No new upgrade operations detected`).
- FastAPI real-process HTTP health/OpenAPI smoke: PASS.
- Ruff and Python bytecode compilation: PASS.
- Automated suite is included in the Stage B combined count below.

ISSUES:

- Flutter/Dart and Docker executables are absent from the opened runtime. Client platform
  runners and Android/iOS/Web builds therefore cannot be generated or compiled here.
  The shared Flutter source and Docker configuration exist; this is an environment
  verification blocker, not a backend blocker.

## Stage B — Core Expert Pipeline

STATUS: PASS

IMPLEMENTED:

- DB-backed source provider adapters plus protocols for technical, market, local cost,
  owner review, LLM, payment, and analytics providers.
- Exact/ambiguous vehicle resolution with market and year guards.
- Strict `EvidenceBundle`, traceable source snapshot, raw comparable-listing snapshot,
  owner-observation snapshot, calculated outputs, and generated-section snapshot.
- Deterministic market similarity, currency/country filtering, minimum comparable count,
  1.5×IQR outlier removal, median/interquartile range, price deviation, and confidence.
- Owner-feedback aggregation based on unique materials, obvious mirror/dedup protection,
  sample-only mention shares, and automatic percentage hiding below ten materials.
- Deterministic fuel/maintenance/first-year cost ranges with explicit assumptions.
- Evidence-grounded fit rules and four required ratings with confidence/missing-fact output.
- Replaceable deterministic LLM development provider and anti-hallucination validator
  that rejects unknown evidence IDs and status upgrades.
- Preview API and immutable report persistence. Updating source rows after generation does
  not mutate a saved report.
- Language-invariant calculations: only commentary/presentation changes across AZ/RU/EN.

TESTS:

- `21 passed` covering foundation and Stage B behavior.
- Market calculation, outlier, insufficient sample, mismatch, and Unicode matching: PASS.
- Ownership math and insufficient inputs: PASS.
- Owner feedback share/hide/dedup and DB uniqueness constraint: PASS.
- Fit logic and missing-fact confidence: PASS.
- Evidence source requirement and no ESTIMATE→CONFIRMED upgrade: PASS.
- Snapshot immutability, demo propagation, language invariance, and report permissions: PASS.

ISSUES:

- Two non-failing deprecation warnings originate inside the current Starlette TestClient
  compatibility layer; application checks have no failures.

## Stage C — Phone Web Preview user flow

STATUS: PASS locally / PARTIAL for public deployment

IMPLEMENTED:

- Dependency-free HTML/CSS/JavaScript SPA under `apps/web_preview`, served by the same
  FastAPI process at `/preview/`; the Flutter scaffold remains untouched.
- Mobile-first 320–450 px layout with safe-area support, large controls, sticky actions,
  responsive cards, status badges, and expandable full-report sections.
- AZ/RU/EN UI localization kept independent from report language.
- Database-backed vehicle choices, four-step vehicle wizard, four-step usage profile,
  real synchronous pipeline state, saved preview, backend-configured AZ price, mock
  payment, all 15 report sections, follow-up questions, and My Reports.
- Isolated automatic demo users; report/preview/payment/question access remains owner
  scoped. Demo fixtures and market prices are visibly marked as non-production data.
- Refresh-safe hash routes and local draft state. Saved report access survives a backend
  restart because the client reuses its JWT and the backend reads the immutable snapshot.
- Authenticated, allowlisted web analytics ingestion for MVP funnel events.
- One-command runner that applies migrations and seeds demo data before starting Uvicorn.
- Security headers for the preview, including a self-only CSP and frame denial.

TESTS:

- `27 passed`; the original 21 Stage A/B tests remain green.
- Complete API user flow, price configuration, mock failure/success/idempotency, locked
  content, 15 sections, My Reports, and cross-user denial: PASS.
- Three-question success-only limit and saved Evidence Bundle answers: PASS.
- AZ/RU/EN catalog equality and localization contract: PASS.
- Static mobile contract, CSP, touch sizes, and JavaScript syntax: PASS.
- Fresh database migration/seed plus stop/start persistence of an unlocked report: PASS.

ISSUES:

- No Hetzner address, SSH configuration, private key, `hcloud` token, or repository remote
  is available in this Work session. Public deployment was therefore not attempted.
- The managed cloud browser blocks loopback URLs, so automated visual browser clicking
  against this local server is unavailable here. API behavior and static mobile contracts
  pass; final device-level visual QA requires opening the supplied LAN URL on the phone.
- PDF remains correctly labelled `PDF — Stage D`; no placeholder PDF is generated.
- Comparison remains labelled Coming Soon.

NEXT:

- Perform the hands-on Android pass via the LAN URL, then implement Stage D server PDF
  generation from the immutable report snapshot.
