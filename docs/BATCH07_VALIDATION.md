# Batch07: publication, correctness and measured performance

The batch is published in the existing local database after batch06. Source coverage remains partial. See the [complete named delta and cumulative catalogue](CHECKPOINT_US_BASE_CATALOG.md) before interpreting totals. All scope is US MY2000+; no other-market records or existing modules were removed.

## New evidence, not repeated publication

- 132 new exact model-year configurations across 18 new generation scopes (17 additional model names; Optima already existed with JF).
- Four existing X5 F15 configurations gained confirmed displacement in cubic centimetres: sDrive35i/xDrive35i MY2014 and MY2016. MY2015 was not assigned a single displacement because the official update identifies an October2014 production change.
- Nine existing X5 configurations received evidence refresh only and contribute zero new technical values.
- 2,521 confirmed field values belong to the 132 new annual configurations; four further values enrich existing configurations. These are field × exact annual applicability counts, not 2,525 independent discoveries. Repeated values across applicable years/drives are disclosed in the counting method.
- Research holds, source downloads, import jobs and historical revisions contribute zero to new confirmed configurations.

The read-only [before/after reconciliation](../deliverables/VerifiedData/us-base-catalog-07/new-confirmed-data.json) contains each value, applicability and source. It compares with the consistent pre-batch SQLite backup, not with an earlier report's rounded totals.

## Checks actually completed

- 345 backend regression tests PASS; two dependency deprecation warnings, no failures.
- All 730 available base configurations resolve to their expected IDs. Twenty-three invalid combinations return no exact candidates.
- Rogue2014–2016 seven-seat filtering on AZ/RU returns only six documented Family Package records. Five-seat versions do not acquire seven seats.
- Live HTTP smoke: 47 checks PASS, including AZ/RU profiles and matching rules.
- Ordinary batch07 replay is idempotent: no new rows/revisions/jobs/documents and identical catalogue digest.
- Strict-readiness function hash, buyer/search implementation, knowledge schema and all 18 approved UI files match the pre-batch baseline. Publication criteria are AST-equivalent after normalizing the documented hashing optimization only.
- `ruff check backend scripts` PASS. Three specific cache-integrity tests pass: validation-local reuse, invalidation after file change, and rejection of change during hashing.
- Consistent backup restore into an in-memory database passed integrity and foreign-key checks before publication. The backup stays private.
- Browser QA uses the real local app at 415px: new Mitsubishi MY2014 profile in RU/AZ, oil viscosity and explicitly unspecified fill basis, normal filter/search flow and new Malibu results. PNG files are in `deliverables/VerifiedData/us-base-catalog-07/screenshots/`.

## Performance diagnosis and correction

Profiling found repeated complete PDF reads and SHA256 hashing for every documentary reference within one record validation. The same 32-record sample took 21.396s before and 4.969s after the fix: 4.306× for this validation benchmark only. Hash calls fell from1,327 to127 and bytes hashed from13,072,586,783 to1,128,891,392. Input sample SHA256 is identical in both benchmark files.

`catalog_verification._document_checksum` reuses the digest only during one record validation. Cache identity includes path and device/inode/size/mtime_ns/ctime_ns. Changed signatures cause a new full-byte hash; a file changed during reading is rejected. The cache does not survive across records, jobs or transactions. Registry, URL, stored hash, make/model/market/year, trust, identity and review checks still run for each reference. No search or credibility criterion was relaxed.

The extraction step also reused saved text by document hash. A bounded scan of98 existing cached documents found123 seating-related contexts; context alone was never treated as an applicable seat count. Old gaps143, batch05 gaps10 and batch06 gaps24 remain separate and unclosed; batch07 introduces53 additional unknown-seat configurations. These remain available only under the existing rules for unconstrained seats.

The measured operation ledger is [operation-timings.json](../deliverables/VerifiedData/us-base-catalog-07/operation-timings.json). Each program execution has UTC start/end, monotonic elapsed time and exit status. Agent review windows are in [work-clock.json](../deliverables/VerifiedData/us-base-catalog-07/work-clock.json); they include interleaved tools and must not be added to program durations as if disjoint. Final timing report is emitted beside the archives after packaging, so it can include the completed packaging measurement.

One preliminary audit attempt failed because its AST comparator still expected an unused `checksum` import. The comparator was corrected; the application criteria did not change. Its1.964s failed attempt remains in the ledger.

## Technical scope and holds

The published profiles include actual engine/gearbox/drive/body fields and available dimensions, fuel tanks, chassis, seats and factory equipment. Mitsubishi has SAE0W-20 and separate MT/CVT table oil capacities. Audi A3/Q7 have applicable annual oil table capacities with unspecified fill basis kept explicit. Jeep Compass2016 retains US AKI87 `(R+M)/2`. Missing oil approvals, gearbox fluids and service-fill quantities were not invented or transferred from neighboring engines/years.

Important exclusions remain explicit in the manifest: A3 cabrio/S3/TDI; Atlas2.0AWD; Civic2014 and unverified2015LX transmission/body combinations; Optima2013manual retail applicability; NX300hFWD2017; SentraSR TurboMT2018; OutlanderSportMT AWD; RangeRoverLWB/diesel disputed fields; EscaladeESV and unverified seating packages. EscaladeMY2015 early6L80 and late8L90 are distinct groups without a guessed VIN cutover. No deep dossier or ownership layer was declared complete.

Unpublished annual scopes: X3MY2016, OptimaMY2011, RAV4MY2014, CivicMY2014 and TeslaModelSMY2016. Tesla has insufficient dated technical applicability in the cached brochure; its research rows do not contribute to this batch. The rest of the master-list continues in the [remaining queue](../deliverables/VerifiedData/us-base-catalog-07/remaining-master-queue.md).

## Delivery and restore boundary

The source/deployment archive contains the current code, reviewed manifests and documentation. QA archive contains named lists, source locators, technical values and screenshots. Neither contains the live database, private source cache, credentials or account/session metadata. Exact secret scanning and archive integrity checks run during packaging.

Replay on the existing local database is idempotent. A fresh database needs document acquisition, RawDocument/revision ID remapping and renewed review; these manifests are not a portable live-DB restore. Historical correction manifests remain in the sequence. APK was not rebuilt. Phone, Hetzner, prices, ownership, deep dossiers and commercial functions remain deferred.
