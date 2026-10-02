# Auto Expert · frozen 51-family verification checkpoint

Date: 2026-09-20. Existing backend **0.8.1**, existing Android **0.8.1-alpha81**.
Status: **PARTIAL**. This is a documentary verification batch in the current project, not a new stage or UI.

## Actual counts

| Measure, denominator 51 families | Result |
|---|---:|
| All frozen model-year configurations have scoped identity verification | **1 / 51** |
| Individually verified configurations | **2** |
| Entire generation production-year range and all trims verified | **0 / 51** |
| Additional families with partial factory facts | **9 / 51** |
| Families still at research-only identity | **41 / 51** |
| Full AZ/RU dossier | **0 / 51** |
| Partial documentary AZ/RU dossier | **1 / 51** |
| Full ownership-cost coverage | **0 / 51** |
| Partial conditional maintenance coverage | **1 / 51** |
| Approved image | **0 / 51** |

The verified scope is **BMW 3 Series, US MY2025, 330i Sedan RWD and 330i xDrive Sedan AWD**.
It does not certify other model years, M340i, Touring, packages, an entire production range, or any VIN.
`verified_generations` in the API counts distinct generation labels represented by scoped verified
configurations; it is not a count of fully researched generation histories. `verified_scoped_versions` is 2.

Catalogue size remains **3,655 published configurations, 204 families, 31 makes**.
No model or configuration was added. Twenty-three existing configurations received reviewed corrections.

## Evidence published

- BMW's [US MY2025 3 Series factory release](https://www.press.bmwgroup.com/usa/article/detail/T0442407EN_US/the-new-2025-bmw-3-series)
  identifies the seventh generation, US model year, B48B20O2, 1,998 cm³, turbo four-cylinder,
  48 V mild hybrid and eight-speed Steptronic. Individual EPA records
  [48163](https://www.fueleconomy.gov/ws/rest/vehicle/48163) and
  [48164](https://www.fueleconomy.gov/ws/rest/vehicle/48164) corroborate RWD/AWD configuration scope.
  The general EPA HEV classification was explicitly refined to MHEV. Old facts/revisions were retained.
  Generation chassis code, full production boundaries and internal gearbox code remain unconfirmed.
- Twenty-one existing Kia configurations across **Optima, Cadenza, Rio, Forte, Sportage, Sorento,
  Soul, Niro and Telluride** received only invariant engine/transmission fields from the applicable
  US factory tables. These nine families remain partial. A table shared by several trims does not
  establish an exact trim, generation or drivetrain.
- [BMW US MY2025 maintenance booklet](https://www.bmwusa.com/content/dam/bmw/marketUS/common/warranty-books/2025/BMW_MY25_Maintenance_with_BEVs.pdf):
  printed pages 1–3 and 11–13 were reviewed, including the 3 Series columns in the rotated table.
  Four published conditional operations cover oil/filter by CBS, cabin microfilter every second
  oil service, spark plugs every sixth oil service, and brake fluid by CBS.
  Approximate mileage is not a fixed due interval. No assumed oil capacity, part number, material
  quantity, severe-service rule, or AZ labor price was added.
- Existing cached [NHTSA recall response](https://api.nhtsa.gov/recalls/recallsByVehicle?make=BMW&model=330i&modelYear=2025)
  provides campaign **25V202000**, explicitly naming certain 330i and 330i xDrive MY2025 vehicles.
  The AZ/RU dossier describes the starter-generator connection risk conditionally. VIN applicability,
  production boundaries and completed repairs were not checked.
- The cached [NHTSA manufacturer communications archive](https://static.nhtsa.gov/odi/ffdd/tsbs/MFR_COMMS_RECEIVED_2025-2026.zip)
  contains **27 BMW 330I MY2025 rows and one 330I XDRIVE MY2025 row**. The latter, document **11030312**,
  concerns Automate My Habits after software 25-07-5XX. For RWD, **11013062** describes HUD view behavior.
  These are concise summaries, not full bulletins. Parts-return requests are not counted as failures.
  **No generalized KnownIssue records were automatically published.** Two conditional candidates are
  documented in partial sections pending full bulletin/equipment applicability review.

All references retain source URL, document SHA-256, exact locator and reviewed model-year/market scope.
Factory and safety source registrations permit this local research; commercial reuse is not asserted.
No new paid provider calls or Turbo requests were made. NHTSA content above was reused from local cache.

## Unresolved evidence and conflicts

1. Kia Sportage MY2026 factory table says eight-speed automatic but its FWD clutch cell says
   `Dry Single Plate Diaphragm`; AWD says `Torque Converter`. The discrepancy is recorded in
   `verification-51/conflicts.json`. Mechanical transmission construction remains unresolved;
   the family is not verified.
2. Kia K5's 2.5-litre normally aspirated and turbo candidates cannot be resolved by displacement
   alone. Their engine/transmission pairs were not merged. EV6/EV9 require motor/battery matching
   evidence; the ICE table matcher intentionally does not assign them an engine configuration.
3. Carnival needs a reviewed mapping of its differently labelled factory table. Hyundai's fetched
   page is a JavaScript shell: HTTP 200 alone did not supply technical evidence.
4. The remaining Mercedes-Benz, BMW, Audi, Hyundai and Volkswagen scopes need applicable official
   generation and powertrain documents. Model-name presence in vPIC and source-worker COMPLETE
   status cannot replace this evidence. A failed NHTSA complaints request is not zero complaints.
5. Missing dossier coverage includes full bulletin applicability, owners' evidence, complete service
   requirements, local market analysis and cost evidence. CBS observations alone do not determine
   future service dates or costs. Model photos remain IMAGE_QA; placeholders are not approved images.

## Reproducible local work

The frozen manifest is `data/manifests/us-51-verification-cohort.json`. Every family has existing
target variant IDs at the model year used in its research job. The old new-year research runner is
blocked while `az-market-priority-policy.json` has `work_mode: VERIFY_EXISTING_51`.
Skoda/non-US work, the phone and Hetzner remain deferred. Turbo counts and market distributions
remain unknown optional manual inputs and do not block technical verification.

From the project directory:

```powershell
.\.venv\Scripts\python.exe scripts/checkpoint_verification_51.py
.\.venv\Scripts\python.exe scripts/prepare_factory_51.py --publish-reviewed
.\.venv\Scripts\python.exe scripts/enrich_verified_51.py --publish-reviewed
```

The last two commands reuse their already-published jobs; they do not perform network acquisition.
For the next evidence batch, create a new reviewed manifest against each current published revision,
preserve conflicting facts, include all seven identity fields and applicability, then stage/review/publish
through ImportJob. Do not edit a published manifest or set a verification flag directly.
The next work is documentary resolution of the existing 50 incomplete families; prioritize already
partially documented Kia scopes while retaining the owner's brand queue. No new family discovery.

Publication rejects missing proof, mismatched market/year/document hash, stale base revisions,
unresolved identity conflicts and unresolved transmission construction. A record's verification is
bound to its facts and scope fingerprint. Revoking a linked source hides the mixed-source record,
including when that source is used only for generation evidence. Saved dossiers retain all source
references and immutable facts; later research does not rewrite historical reports.

## Validation and delivery

- **320 pytest tests pass**; Ruff passes. New tests cover stale/conflicting proof, source revocation,
  saved AZ/RU multi-source reports, trim-column alignment and ambiguous powertrain matching.
- `verification-51/coverage.json` audits all 51 families, **80 documentary references**, image status
  and ownership gaps. `family-checkpoint.md` provides the requested per-family matrix.
- Preservation audit: **0 removed historical rows**, **0 unexpected changes**. Only the 23 reviewed
  variants and two existing source-registry entries changed; historical revisions/reports remain intact.
  SQLite integrity and foreign keys pass.
- The 18 existing web-preview files match their pre-batch hashes. No frontend/native UI code changed;
  the existing APK is retained. The local backend was restarted with current code.
- Five live local API checks pass, including AZ/RU dossiers for both configurations and a cost
  scenario that keeps scheduled service and total ownership cost unknown. Browser checks confirm
  AZ/RU text in the existing accordions. The unsaved preview's existing Sources accordion still shows
  the base EPA link; documentary URLs are in catalog JSON and the saved report's full source bundle.
  No frontend changes were made to expand this presentation.
- New documentary manifests contain local document/revision IDs. They are **not a portable replay
  certification**. The earlier public data bundle is the preceding research baseline and has no new
  verified factory state. Rebinding documentary IDs and re-review are required before using these
  corrections in another database. Local raw documents and the private database remain together.
  Source/deployment packaging includes code and manifests, excludes secrets, accounts, sessions,
  live DB, private raw documents and backups. Hetzner deployment was not attempted.

The baseline private backup is `.backups/before-verification-51-20260920T104242Z.sqlite3`.
Do not restore it over the current database merely to reproduce tests. Use an isolated database.
Use `verification-51` evidence for this batch; older checkpoints and QA files describe their own snapshots.
