# VIN/history commercial core — local mock checkpoint (2026-09-29)

This checkpoint follows `USA_MVP_CATALOG_COMPLETE`. The frozen USA product catalog
remains **75 production-visible models / 644 configurations**. No model, model year,
EPA CORE row, catalog right, resolver rule, or approved home design was changed.
There were **no paid provider calls and no real payments**.

## Existing implementation audit

| Component | Before | After this checkpoint |
| --- | --- | --- |
| VIN input/validation | Legacy VIN/dossier flow and validation existed | Existing check entrance now reaches an isolated VIN-history fixture flow for the explicit regression VIN; bad check digit and unsupported VIN are rejected by the new adapter |
| Provider contract | Research-oriented `VinHistoryProvider.lookup` and adapters | Same protocol extended with decode, preflight, quote, idempotent fetch, report/assets and normalization; legacy adapters are not silently made commercial |
| Provider commercial audit | Individual research notes and pilots | [Capability/rights matrix](VIN_PROVIDER_CAPABILITY_MATRIX.md); no provider approved for live paid resale |
| Unit economics | Legacy demo product prices, no sale gate for complete history | [Decimal-based configurable model](VIN_REPORT_UNIT_ECONOMICS.md); missing quote/FX blocks sale and negative margin is preserved |
| Payment | Existing legacy mock unlock routes | Separate VIN-history mock transaction and entitlement, unique idempotency keys, retry and refund-required states; production fixture routes disabled |
| Report storage | Legacy dossier and VIN snapshots | Migration `f085_vin_history_flow` adds separate check, transaction, capability, normalized report/event/asset, entitlement and cost tables; private raw payload stays in the transaction |
| Consumer report | Existing model report | Rights-filtered VIN-specific AZ/RU projection; dated odometer graph and anomaly wording; only confirmed display-right assets are served after entitlement |
| Client | Approved web preview and Flutter shell | Targeted VIN-history preview, mock checkout, report, saved access and gallery; existing three product entrances remain |

## Working local flow

From the existing **Check a specific car** entrance, input `3FA6P0HD0KR114795`
in the local demo. The fixture identifies a synthetic 2019 Ford Fusion, reports only
its known preflight counts, shows a **mock-only** 15 AZN scenario, then grants a
server-checked entitlement after mock payment. It normalizes synthetic auction,
damage, odometer and title events; the two dated odometer readings produce an
**anomaly**, not an assertion of rollback. The SVG asset explicitly says
`MOCK PHOTO — NO VEHICLE`, is fetched only after entitlement, and is never a
claim about this real VIN. AZ/RU views read the same stored events. The owner can
reopen the report without a second mock charge. A failed post-payment fetch can
be retried; a final failure goes to `REFUND_REQUIRED`.

The fixture accepts only that regression VIN. A real paid supplier adapter is
**not** connected. For a supported future VIN that is outside the 75-model catalog,
the history path is designed to remain independent; the optional technical join
reads only production-safe model/year facts, and it exposes an exact engine/box/
drive only when all three are independently identified and match one eligible
variant. The internal EPA candidate universe never becomes consumer evidence.

Endpoints are under `/api/v1/vin/history`: `POST /checks`, `GET /checks`,
`GET /checks/{id}`, mock-only `POST /checks/{id}/payments/mock`,
`POST /checks/{id}/retry`, test callback, and entitlement-protected
`GET /checks/{id}/report` and `GET /checks/{id}/assets/{asset_id}`. The server
checks owner scope on every route. Full events, raw response, and asset bytes
are absent from the pre-payment response. Mock rows are hidden when the app is
configured as production.

## Provider and economics decision

| Provider | Cost for a complete saleable history report | 15 AZN owner scenario | Decision |
| --- | --- | --- | --- |
| ClearVin | No signed API quote | Margin unknown | Closest documented full-history category; needs credentials/test access, quote and explicit resale/photo rights |
| API Auctions | Public USD 0.01 **per request**, not total report cost | Margin unknown | Auction-only candidate; plan-specific redistribution and third-party photo rights unresolved |
| Auto.dev | Decode/listing/photo endpoint prices do not constitute history pricing | Not applicable | Standard terms and product coverage do not support this full paid report |
| NHTSA/vPIC | Public technical data, not paid ownership history | Not applicable | Technical supplement only |
| Stat.vin, Bid.cars, Bidfax, Vinfax, FinalBid | No authorized commercial API cost | Not applicable | Access/reuse blocked in saved audit |

The hypothetical USD 10 cost at 15 AZN retail and a hypothetical 1.70 FX rate
leaves **−2 AZN before fees**, below a roughly USD 5 minimum margin. This is an
illustration, not a provider quote or current FX snapshot. The model additionally
deducts payment fees, taxes and retry/fallback costs. Unknown supplier cost is
`NEEDS_COMMERCIAL_QUOTE`, never zero.

See [provider capability matrix](VIN_PROVIDER_CAPABILITY_MATRIX.md) for each
field/permission and [unit economics](VIN_REPORT_UNIT_ECONOMICS.md) for the
calculation and source links.

## Persistence and verification

The current local DB was backed up to
`.localdata/backups/autoexpert_pre_vin_history_f085_20260929.sqlite` before the
new migration. The backup and post-migration DB passed SQLite quick/integrity
checks; Alembic head is `f085_vin_history_flow`. The production catalog projection
remained **75 / 644 before and after**. The live DB has **zero** VIN-history check
rows; browser QA used the isolated `.localdata/vin_history_browser_qa.sqlite`.

- Backend: **504 passed**; Ruff on new backend files passed. The exact PowerShell
  test invocation from this project root was:

  ```powershell
  $env:PYTHONPATH=((Resolve-Path '.venv/Lib/site-packages').Path + ';' + (Resolve-Path 'backend').Path + ';' + (Resolve-Path 'scripts').Path)
  $env:PYTHONIOENCODING='utf-8'
  & 'C:\Users\jalil\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe' -m pytest backend/tests -q
  ```
- Flutter: `flutter analyze` **0 issues**, `flutter test` **9 passed**,
  `flutter build web --release --no-wasm-dry-run` passed. Android/iOS runner
  directories are not in this checkout; no phone/device check was attempted.
- Web: `node --check` passed for `app-v2.js`, `buyer-views.js`, and
  `vin-history-views.js`. Manual local browser QA passed RU/AZ preview, mock
  payment, entitled report/asset and saved-report reopen.
- Security tests cover invalid/unsupported VIN, unavailable and unknown preflight,
  damage/no-damage, odometer/title, timeout/rate-limit/failure, repeat payment
  and callbacks, owner separation, closed assets, production mock isolation,
  internal EPA exclusion, margin gate and AZ/RU fact parity.

## External blockers before any real launch

Choose a supplier under a signed product-specific agreement. Obtain API
credentials and test access, a per-product/per-VIN quote plus volume tiers,
precise preflight/coverage semantics, charge/retry/refund behavior, webhook or
polling and authentication details, raw retention rights, paid end-user display
and resale rights, and separate photo thumbnail/full-size/cache/PDF rights.
Configure a dated real FX snapshot and payment/tax/retry costs before setting
a retail price. Implement and test a real adapter and payment provider only after
those prerequisites and separate owner authorization for billable requests.

This checkpoint establishes a provider-agnostic **mock** path. It is not a live
VIN-history integration.
