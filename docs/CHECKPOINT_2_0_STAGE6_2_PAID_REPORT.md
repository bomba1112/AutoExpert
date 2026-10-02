# Stage 6.2 - Paid Vehicle Report V1

Date: 2026-09-18. Backend **0.6.6**, Android **0.6.6-alpha**, versionCode **66**.
Active checkout: `STAGE6_1`. Stage 6.1 is preserved as the previous completed checkpoint.
The earlier Stage 6.2 depth-dashboard scope was replaced by the owner's Paid Vehicle Report V1 request.

## Result

Implementation and physical-device acceptance: **PASS**.
Commercial product acceptance: **PARTIAL**, not a blanket paid-report PASS.
The Ford technical report has useful core sections and passes the minimum completeness gate.
Connected sources do not provide this VIN's accident/title/mileage/auction history or real
auction photographs. Substantive independent reliability reviews are also unavailable.
Two genuine My MPG fuel logs do not fill that gap or establish typical real consumption.
The technical report is useful for evaluating the configuration; it does not yet justify
selling a complete US-import history report. The existing zero-VIN-record payment block
remains active. No production payment or paid history provider was connected.

The owner can review the complete technical report and export its PDF in DeveloperMode.
Unknown critical technical data returns `NOT_ENOUGH_DATA_FOR_PAID_REPORT`; no mock
charge or entitlement is created for such a real report, even if history record counts exist.
The separate DEMO payment simulation remains available and is visibly synthetic.

## Ford regression: 3FA6P0HD0KR114795

Live official research produced **34 findings: 32 CONFIRMED, 1 ESTIMATE market scope,
1 INSUFFICIENT_DATA owner fuel sample**. These states are internal diagnostics.
There are 10 source records with retrieval dates, original URLs and evidence references.

| Consumer section | Current content |
| --- | --- |
| Автомобиль | 19 passport rows including VIN, make/model/year, trim, body, seats, engine, transmission, drive and dimensions |
| Двигатель | 13 technical rows; concise reference to the coolant-intrusion issue |
| Коробка и привод | Automatic, 6 gears, FWD, MERCON LV / WSS-M2C938-A |
| Подвеска / рулевое / тормоза | Independent MacPherson front, integral-link rear, electric steering, electric parking brake; service-brake details remain limited |
| Кузов | Length 4872 mm, wheelbase 2850 mm, width including mirrors 2121 mm; no unsupported corrosion claims |
| Электрика | TPMS, camera software campaign, conditional engine block-heater campaign |
| Расход и эксплуатация | EPA city/highway/combined 10.2 / 6.9 / 8.7 L/100 km; owner logs kept separate |
| Слабые места | Coolant intrusion: system, problem, applicable configuration, symptoms and cross-source basis |
| Отзывы владельцев | Two real My MPG logs, explicitly identified as fuel logs; no reliability-review claims or fabricated owner count |
| Отзывные кампании / бюллетени | Two model-level campaigns plus historical service program 19B37; VIN applicability/completion unresolved |
| История VIN / фото | Absent from consumer report because real records/photos were not found |
| Экспертный вывод | Final main section: configuration, practical strengths, engine risk, recall implications, VIN-history gap and specific next action |

Newly populated relative to the previous sparse report: 6-speed automatic and FWD,
MacPherson / integral-link suspension, electric steering and parking brake, TPMS,
five seats, vehicle dimensions, EcoBoost family, timing belt, 87 AKI minimum in the US,
SAE 5W-20 / WSS-M2C945-B1, 4.05 L oil including filter, normal-service oil limit,
MERCON LV and official consumption. Unknown mechanical engine/transmission codes,
colors, exact generation, weight, height, luggage capacity and fitted wheel sizes are not invented.

## Source interpretation

- NHTSA vPIC: VIN identity and primary engine/body attributes.
- EPA configuration 40700: unique matching 1.5 L / four-cylinder gasoline configuration,
  automatic transmission and official consumption. US MPG is converted before rounding.
- Ford's public 2019 brochure: common architecture and dimensions; gasoline and hybrid
  layout regions are parsed separately. Hybrid eCVT specifications cannot leak into this VIN.
- Ford owner's manual: page-specific maintenance and technical excerpts, with SHA-256 and locators.
- Ford program 19B37 hosted by NHTSA: historical document, not a current free-repair promise.
  The issue also appears in six separate complaints explicitly mentioning 1.5 L and coolant
  intrusion/replacement symptoms. Anonymous complainant independence is not asserted;
  confidence remains MEDIUM / ESTIMATE, and no failure rate is calculated.
- Recall 23V440000 is explicitly for Fusion PHEV and is excluded from this conventional
  gasoline report. It remains visible in the raw diagnostics.
- 25V442000 concerns rear-camera software. 25V685000 concerns the engine block heater
  **if fitted**. The latter is not evidence that this VIN has the option or the fault.
- My MPG has two fuel logs; they are not called NHTSA owner reviews or used as a statistically
  established consumption average. NHTSA complaints stay in their own evidence class.

## Interfaces and behavior

`PhotoEvidence`, `VehiclePhotoSet`, and `VINHistoryResearchProvider` provide a clean
boundary for an authorized future connection. Import requires exact VIN, genuine source
records, source-linked events, and actual validated image bytes before publishing a gallery.
Assets are stored by checksum; owner-authorized endpoints serve them. The PDF embeds those
same bytes. No URL scraping, login, CAPTCHA, or anti-bot workaround was added.
Photo import and PDF inclusion are tested using isolated fixtures; the Ford report contains no fixture photos.

Consumer report and PDF share `build_paid_report`. Empty optional sections collapse;
there is no model-comparison section or generic pre-purchase checklist. The inspection
caveat appears once, in the conclusion. Provenance/status JSON is behind developer access.
Chat receives the consumer technical findings with their original evidence status and source IDs.

Key endpoints: `GET /vin/{id}`, `GET /vin/{id}/report.pdf`,
`GET /vin/{id}/diagnostics`, `GET /vin/{id}/photos/{photo_id}` under `/api/v1`.
All enforce VIN-check ownership; PDF/photo content additionally requires report access.

## Verification

- 129 backend tests passed. After the last report/PDF refinements, 38 affected tests passed again.
- Ruff passed. Three JavaScript research-flow tests passed.
- Added regressions cover 150 observations / 100 unique materials, contradictions,
  variant mismatch, small owner samples, qualified cross-source issues, missing critical
  data, payment denial before charge, owner isolation, wrong-VIN photos and embedded PDF assets.
- Actual device: HONOR ALI-NX1, Android 15, USB serial AS7J6R4730001975. No emulator.
- RU/AZ/EN report order/content, no horizontal overflow, no consumer status badges,
  no PHEV recall leakage, full diagnostics, 12 unlimited chat questions and the independent
  mock paywall/limited chat flow passed on the device.
- Native PDF export used Android's document-save dialog. The saved file was pulled back,
  parsed and compared with the generated report content. Five pages; Cyrillic/Azerbaijani
  fonts embedded. All pages of all three language samples were rendered and visually inspected.
- Installed APK version and signature verified; same persistent alpha signing certificate,
  update with application data retained. Backend remains running from this checkout.

## Delivery

- APK: `deliverables/AutoExpert_2_0_Alpha_0.6.6.apk`
- APK SHA-256: `b578d42aeabcb67e7f85ec6ff34472610720d923362420abebac01c41fb8829a`
- Samples, page previews, source diagnostics and physical-device captures:
  `deliverables/Stage6_2_PaidReport/`
- Physical acceptance script: `apps/android_demo/validate_paid_report.mjs`
- Source archive: `deliverables/AutoExpert_2_0_Stage6_2_PaidReport_Source_2026-09-18.zip`
- Private signing material, runtime caches, personal databases and `.env` are excluded.

Work stops at this delivery. No Stage 6.3, paid providers, production payments, Damage Risk
Map, B2B, banking or iOS work has started.
