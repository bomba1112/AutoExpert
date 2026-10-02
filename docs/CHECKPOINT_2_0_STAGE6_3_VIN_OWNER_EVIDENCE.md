# Auto Expert 2.0 — Stage 6.3 checkpoint

Date: 2026-09-18. Backend **0.6.7**. Android **0.6.7-alpha**, versionCode **67**.
Active checkout remains `STAGE6_1`; this is an incremental delivery, not a replacement
project. Historical checkpoints and APKs are preserved.

**Stage status: PARTIAL. Implementation/regression checks pass; commercial report
readiness for 3FA6P0HD0KR114795 is NO.** No next stage was started.

## Delivered behavior

- A separate VinHistoryProvider contract, seven explicit result states, query scope,
  completion flag, provenance, and cost/auth/market/capability/licensing metadata.
- Generic event normalization and mirror deduplication. Distinct dated relistings
  remain distinct; conflicting values are withheld and retained in diagnostics.
- Exact-VIN/event PhotoEvidence, original reference, order, source page, retrieval
  date, hash and permitted local cache. Provider errors or invalid assets do not
  become NO_RECORDS. No AI photo damage interpretation is implemented.
- A separate OwnerReviewProvider and generic owner normalization/deduplication,
  configuration matching, thirteen topic classes and bounded unique counts.
- Quality thresholds are configurable through SampleThresholds (default SMALL=5,
  USEFUL=20, STRONG=50; below 5 is VERY_SMALL). No failure percentages are inferred.
- Generic KnownIssue aggregation accepts owner evidence separately from official
  complaints; a single owner account cannot upgrade the Ford issue to HIGH.
- Paid Vehicle Report V1 retains the technical Ford content. New owner and history
  sections have RU/AZ/EN copy, provenance and conditional event galleries. Empty
  galleries are suppressed. PDF layout removes redundant breaks and repeated
  history warnings; source links are grouped by publisher/date without dropping URLs.
- Grounded chat covers auctions, photographs before repair, recorded mileage, owner
  engine reports and the difference between an anecdote and frequency evidence.
- Commercial readiness requires technical sufficiency and a successfully completed
  exact-VIN provider result. A verified zero-record result may qualify; unavailable
  or unqueried archives do not. Small owner samples are allowed with explicit limits.

Key implementation modules: `schemas/research_evidence.py`,
`providers/vin_history_public.py`, `providers/owner_reviews.py`,
`providers/public_evidence_http.py`, `services/vin_events.py`,
`services/history_research.py`, `services/report_evidence.py`,
`services/owner_experience.py`, `services/report_evidence_sections.py`.
The developer-dossier path enriches persistent VIN checks and caches model-level owner
research for 24 hours. VIN-specific history remains on its check, not on the shared
model profile. No schema migration is needed for these JSON-backed additions.

## Real data and limits

The [source audit](STAGE6_3_SOURCE_AUDIT.md) records actual requests and restrictions.
Five archive providers have access audits, but **zero completed VIN-history lookups**.
Indexed exact-VIN discovery found no accessible event page. Actual events=0,
actual photos=0, actual NO_RECORDS cases=0. The Ford report correctly says sources
are unavailable and auction/accident/mileage records have not been checked.

AuthorizedHistoryAdapter supports a future permitted connection, including explicit
PAYG authorization. No working live VIN-history API is installed, and no subscription
or paid account was opened. Its positive event/photo results are test fixtures only.

The live CarComplaints provider retrieved 7 materials from 3 public owner pages:
Ford 1 applicable, Toyota 2 applicable, Hyundai 1 applicable. All samples are VERY_SMALL.
The reviewed URL catalogue is intentionally bounded to these regression pages; it
is not an exhaustive review search engine. All three vehicle lookup results are
PARTIAL because this catalogue does not establish complete owner coverage.

The Ford coolant issue has 3 source/publisher groups, 1 owner material, 6 official
complaint signals and manufacturer support. Confidence remains MEDIUM / ESTIMATE.
Build-date/program-VIN conditions remain explicit. No VIN defect or failure rate
is asserted, and NHTSA/My MPG are excluded from the owner count.

## Verification

- Backend: **173 passed** (129 previous tests plus 44 new cases). Four previous
  readiness expectations were updated for the new required VIN-history gate;
  no previous tests were removed. Existing technical-section assertions still pass.
- Client: **3 passed**. Ruff check of backend and Android Python scripts passes.
- New coverage: event dedup/relisting/conflicts; exact VIN/photo provenance and hash;
  unavailable vs NO_RECORDS; all provider states; robots, auth and rate limits;
  owner dedup/reposts/text similarity; variant and hybrid isolation; unique topic
  counts; quality thresholds; generic three-brand parser; official/owner separation;
  known-issue confidence; conditional photo PDF and RU/AZ/EN.
- Physical HONOR ALI-NX1, Android 15: installed signed APK, real Ford report in all
  three languages, 12 sections and 11 sources, owner/history sections, diagnostics,
  no empty gallery, no horizontal overflow or JavaScript errors.
- Physical chat: five new questions plus twelve technical questions with developer
  access; separate Simulate User Paywall retains the ten-question policy and mock
  entitlement flow. No production payment was made.
- Actual gallery with this VIN: **N/A, no source photos**. Conditional positive photo
  rendering is verified by automated fixtures; it is not claimed as a live-data
  gallery acceptance pass.
- RU/AZ/EN PDF: **5 readable pages each**, embedded fonts and all 11 source links;
  all pages rendered and visually reviewed. Actual VIN images are absent, correctly.
- PDF HTTP download and Android native save are verified separately in device
  evidence. During the long session a 60-minute preview token expired; a fresh demo
  session was created through the ordinary app flow and device checks repeated.

The final test run emits two dependency deprecation warnings; an earlier run also
reported a Windows/OneDrive pytest cache warning. There are no test failures.
PDF page count is descriptive, not a quota.

## Artifacts

- `deliverables/AutoExpert_2_0_Alpha_0.6.7.apk`
- `deliverables/AutoExpert_2_0_Stage6_3_VinOwner_Source_2026-09-18.zip`
- `deliverables/Stage6_3_Evidence/Ford_Fusion_2019_{ru,az,en}.pdf` and JSON
- `deliverables/Stage6_3_Evidence/evidence-diagnostics.json`
- `deliverables/Stage6_3_Evidence/chat-regression.json` (15 questions across RU/AZ/EN)
- `deliverables/Stage6_3_Evidence/owner-research/` (three real normalized collections)
- `deliverables/Stage6_3_Evidence/provider-access-audit.json`
- `deliverables/Stage6_3_Evidence/device/` (real-device results and screenshots)
- `deliverables/Stage6_3_Evidence/verification.json` and `sha256.json`

The source ZIP excludes credentials, signing keys, `.env`, databases, runtime/raw
research caches, build outputs and deliverables. The signing certificate remains
the existing alpha certificate; its SHA-256 is
`1ecb2639b71e02d2014118caa703300d4316ea067532cea3072a1b4be4cc6acb`.

## Remaining blockers

An authorized, reachable VIN-history source must actually answer this VIN's query.
If it returns records, real event/photo provenance and the physical gallery must be
validated. If it honestly returns NO_RECORDS, the gate can accept that result without
inventing events. Current unavailable sources cannot satisfy this requirement.

Owner evidence is real but narrow and problem-selected. It does not yet constitute
a broad reliability review corpus. This limitation is visible in the report; small
sample size alone is not a commercial-gate failure under the Stage 6.3 contract.

COMMERCIAL REPORT READY: **NO**. No Damage Risk Map, image diagnosis, production
payments, B2B/banking/iOS expansion or listing parser was started.
