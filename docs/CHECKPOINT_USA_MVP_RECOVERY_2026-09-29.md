# USA MY2012+ MVP catalog — recovery checkpoint (2026-09-29)

**USA_MVP_CATALOG_COMPLETE: 75/75 target models have at least one production-visible configuration.** The production projection contains 644 configurations. This is minimum model coverage, not a claim that every year, trim, generation, or drivetrain is covered. Catalog expansion stops here.

The [cumulative model list](../deliverables/VerifiedData/usa-mvp-catalog-12-local-01/cumulative-models.md) names all 75 production-visible models and their exact visible model years. The [configuration export](../deliverables/VerifiedData/usa-mvp-catalog-12-local-01/production-visible-us-my2012plus.jsonl) contains all 644 production-visible rows and their displayed engine, transmission, drive, and provenance identifiers. Those exports come from the production buyer projection, not raw EPA labels.

## Recovery audit

The last chat-observed state before power loss was **66 models / 635 configurations**. The first read of the surviving live DB found **70 / 639**. BMW 3 Series MY2016, Kia Sorento MY2016, and Kia Sportage MY2017 were present as previously reported. Four Tesla records had also committed before the outage: Model 3 MY2020 AWD, Model S MY2016 AWD, Model X MY2018 AWD, and Model Y MY2021 AWD. Their four source records and 16 production-eligible fact claims survived. The Tesla source plan and script in `deliverables/VerifiedData/usa-mvp-catalog-12-local-01/` also survived. The one-time script was replayed after backup and inserted no duplicate source record or claim.

The live SQLite database passed `PRAGMA quick_check` and `PRAGMA integrity_check` both before continuation and after completion (`ok`). The Alembic head recorded by the DB is `f084_commercial_fact_claims`, with its migration file present. The latest pre-recovery 2026-09-29 import job `4e69b7d6-3c67-41c8-ab50-c603bbaf6e17` was `PUBLISHED`, with cursor 9, nine published revisions, and no active lease. The surviving prepared, reviewed, publication, manufacturer-claim, source-cache, and raw-document files were reused. The latest `.runtime` log was dated 2026-09-28; no 2026-09-29 run log was found. A stale `.localdata/catalog-writer.lock` pathname did not hold an OS lock. Four older 2026-09-26 approved jobs and 509 older EPA staging revisions were outside this recovery and were left untouched. There was no evidence that an already committed MVP publication had rolled back; the five remaining model promotions had not been applied at first inspection.

Before continuing, SQLite's backup API produced `.localdata/backups/autoexpert_recovery_20260929_165447.sqlite` (1,085,452,288 bytes; `quick_check=ok`). A second backup before the Tesla correction is `.localdata/backups/autoexpert_pre_tesla_transmission_correction.sqlite`. The completed-state backup is `.localdata/backups/autoexpert_usa_mvp_75_20260929.sqlite` (1,085,804,544 bytes; `quick_check=ok`). These are local live-data backups, not deployment artifacts.

## Resumed publication: 70 / 639 → 75 / 644

Only existing candidates received fact-level manufacturer evidence. No new EPA CORE candidate, model, rights rule, resolver rule, or UI change was made.

| Make | Model | Exact US MY | Production-visible configuration added | Evidence | Result |
| --- | --- | ---: | --- | --- | --- |
| Volkswagen | Passat | 2015 | 3.6L FSI narrow-angle VR6; 6-speed DSG dual-clutch; FWD | [VW US brochure](https://www.auto-brochures.com/makes/Volkswagen/Passat/VW_US%20Passat_2015.pdf), [VW technical specifications (mirror)](https://www.motor-talk.de/forum/aktion/Attachment.html?attachmentId=748552); cached copies and OEM cross-check | +1 |
| Jeep | Grand Cherokee | 2018 | 3.6L Pentastar V6; 8-speed automatic; **RWD/4×2 only** | [FCA factory technical sheet](https://www.media.stellantis.com/uploads/me/ME/2018/Jeep/Technical-Sheet/1806_Jeep_Grand-Cherokee.pdf) | +1 |
| Hyundai | Elantra | 2017 | Nu 2.0L MPI Atkinson inline-4; 6-speed SHIFTRONIC automatic; FWD | [Hyundai Motor America release](https://www.prnewswire.com/news-releases/all-new-2017-hyundai-elantra-priced-at-100-less-than-the-award-winning-model-it-replaces---starts-at-17150-300205153.html), [factory features sheet](https://downloads.regulations.gov/NHTSA-2018-0067-12522/attachment_3.pdf) and cached US brochure | +1 |
| Hyundai | Accent | 2018 | 1.6L Gamma GDI (CORE shorthand `SIDI`); 6-speed manual; FWD | [Hyundai Motor America features sheet](https://www.multivu.com/players/English/75060516-hyundai-all-new-2018-accent/docs/features-1505252157506-706486750.pdf) and [press kit](https://www.multivu.com/players/English/75060516-hyundai-all-new-2018-accent/) | +1 |
| Chevrolet | Cruze | 2017 | 1.4L turbo gasoline inline-4; 6-speed automatic; FWD | [GM-authored 2017 Fleet Guide (mirror), p. 30](https://xr793.com/wp-content/uploads/2020/03/2017-GM-Fleet-Guide.pdf) | +1 |

The [manufacturer fact-claim plan](../deliverables/VerifiedData/usa-mvp-catalog-12-local-01/remaining-ice-fact-claims.jsonl) and [idempotent bulk promoter](../deliverables/VerifiedData/usa-mvp-catalog-12-local-01/promote_remaining_ice.py) preserve exact candidate scope. The Jeep [manifest](../data/manifests/usa-mvp-jeep-grand-cherokee-2018-rwd.json) and [promoter](../scripts/promote_usa_mvp_jeep_2018_rwd.py) bind the factory evidence to 4×2/RWD only. The fleet sheet also describes 4×4, but it was not mapped to the existing AWD candidate without proof that the application's AWD taxonomy matched this Jeep configuration.

The 2017 Elantra factory features PDF could not be fetched directly during recovery (HTTP 403). Its indexed official content and an already cached Hyundai US brochure were used with this access limit recorded in the source metadata; no raw document bytes or hash were fabricated. Mirrors are marked as reviewed mirrors with cross-checks, rather than represented as first-party hosting.

The four persisted Tesla configurations remain visible. Their previously displayed transmission text included the research-only EPA `A1` suffix. The [correction script](../scripts/normalize_tesla_mvp_transmission.py) and [four-row manifest](../deliverables/VerifiedData/usa-mvp-catalog-12-local-01/tesla-transmission-correction-manifest.json) narrowed the displayed value to `Electric drive-unit gearbox`, backed by cached Tesla service data. The old EPA-suffixed transmission facts became `INTERNAL_RESEARCH`; the four replacement transmission facts are `COMMERCIAL_OK`. The correction changed **zero** model/configuration counts, and did not alter any of the 12,074 `epa:%` variants.

## Twelve-model target and final status

| Model | Exact visible US MY | Engine / powertrain | Transmission | Drive | Visible configs | Status |
| --- | ---: | --- | --- | --- | ---: | --- |
| BMW 3 Series | 2016 | 320i 2.0L TwinPower Turbo gasoline | 8-speed Steptronic automatic | RWD, AWD | 2 | PRODUCTION |
| Volkswagen Passat | 2015 | 3.6L FSI narrow-angle VR6 | 6-speed DSG dual-clutch | FWD | 1 | PRODUCTION |
| Hyundai Accent | 2018 | 1.6L Gamma GDI; displayed CORE engine shorthand `SIDI` | 6-speed manual | FWD | 1 | PRODUCTION |
| Hyundai Elantra | 2017 | Nu 2.0L MPI Atkinson inline-4 | 6-speed SHIFTRONIC automatic | FWD | 1 | PRODUCTION |
| Kia Sorento | 2016 | 2.4L GDI inline-4 | 6-speed Sportmatic automatic | FWD, AWD | 2 | PRODUCTION |
| Kia Sportage | 2017 | 2.4L GDI inline-4 | 6-speed Sportmatic automatic | FWD, AWD | 2 | PRODUCTION |
| Chevrolet Cruze | 2017 | 1.4L turbo gasoline inline-4 | 6-speed automatic | FWD | 1 | PRODUCTION |
| Jeep Grand Cherokee | 2018 | 3.6L Pentastar V6 | 8-speed automatic | RWD | 1 | PRODUCTION |
| Tesla Model 3 | 2020 | dual electric drive units, BEV | Electric drive-unit gearbox | AWD | 1 | PRODUCTION |
| Tesla Model S | 2016 | dual AC induction electric drive units, BEV | Electric drive-unit gearbox | AWD | 1 | PRODUCTION |
| Tesla Model X | 2018 | dual electric drive units, BEV | Electric drive-unit gearbox | AWD | 1 | PRODUCTION |
| Tesla Model Y | 2021 | dual electric drive units, BEV | Electric drive-unit gearbox | AWD | 1 | PRODUCTION |

## Verification and stop condition

- Production buyer projection, USA MY2012+: **75 models / 644 configurations**. At first recovery inspection: **70 / 639**. Last chat observation before outage: **66 / 635**.
- Final `quick_check=ok`, `integrity_check=ok`, and Alembic head `f084_commercial_fact_claims`; final backup `quick_check=ok`.
- No duplicate catalog keys and no duplicate commercial fact-claim unique keys. Replaying the four-case ICE promoter left 214,304 claims and 24,539 source records unchanged; replaying the Jeep and Tesla operations also added no duplicate publication or claim.
- Targeted regression: `pytest backend/tests/test_commercial_fact_overlay.py backend/tests/test_catalog_buyer_core_scope.py backend/tests/test_factory_bulk_pipeline.py -q` → **18 passed** (two unrelated deprecation warnings).
- All 12 required models now have at least one production-visible configuration. Generation, trim, battery capacity, range, seats, fluids, prices, images, and ownership costs were not used as admission gates. Unknown optional values were not inferred.

**USA_MVP_CATALOG_COMPLETE.** No further US catalog expansion was performed after reaching 75/75.
