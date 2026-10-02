# VIN/history provider capability and rights audit

Checked 2026-09-29. This is an audit of the existing checkout plus current public
provider documentation and terms. It does **not** authorize a paid call, subscription,
redistribution, or end-customer photo display. `?` means **not established**, rather
than no data. `—` means that the reviewed product does not document that capability.
API capability is different from coverage for a particular VIN; the Ford pilot VIN
returned no listing or photos from Auto.dev. No current production VIN-history
provider credentials or signed resale/display agreement were found in the project.

## Access, commercial terms and operational evidence

| Provider | API documentation available | Credentials available in project | Sandbox available | Cost per request/report | Volume tiers | Preflight/coverage endpoint | Country/market coverage | Rate limits | SLA/latency | Status for a paid Auto Expert history report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ClearVin | [Partner API](https://www.clearvin.com/en/api-subscribers/), [auction](https://www.clearvin.com/en/api-subscribers/auction-history-api/), [NMVTIS](https://www.clearvin.com/en/api-subscribers/nmvtis-history-api/) | No usable project credential verified | Public sandbox not documented; [business page](https://www.clearvin.com/en/custom-solutions/) mentions a trial | **Unknown API quote**; public consumer report price is not an API price | Negotiated/bulk, exact rates unknown | Not documented in reviewed pages | US vehicle history; specific record coverage VIN-dependent | ? | No contractual SLA/latency available locally | **NEEDS_COMMERCIAL_TERMS** |
| Auto.dev | [v2 reference](https://docs.auto.dev/v2/reference), [photos](https://docs.auto.dev/v2/products/vehicle-photos) | Growth trial used in 2026-09-18 pilot; current access not re-tested and trial ended 2026-09-25 | Trial existed, but metered fees applied | [Published](https://www.auto.dev/pricing) endpoint rates are **decode/listing/photos**, not a full history-report quote | Free/Growth/Scale/Enterprise | `/photos/coverage/{vin}` worked in old pilot; no paid history preflight documented | VIN decode global; listings/photos chiefly US | Growth 10 req/s per published plan; no load test | No guaranteed SLA in reviewed standard terms | **NOT_SUITABLE** as full VIN-history supplier; current commercial redistribution also blocked absent different agreement |
| API Auctions | [Developer docs](https://apiauctions.io/docs) | No production credential verified | 2026-09-18 `devnew` docs had a fixed 10-VIN public sandbox; current main site advertises a card-gated 10-requests/hour demo. No current access tested | [Public PAYG](https://apiauctions.io/) $0.01/request with $25 minimum wallet top-up; actual multi-call report cost/contract not established | Public packs: 100k requests/$100 and 1m/$250, each 30-day expiry; Active Lots $150/mo excludes sold-history calls | v1 `get-car-count-history` gives sale count; no documented photo/title/insurance preflight | US/Canada/Finland/UAE public auction lots; source claims not independently verified here | Public PAYG 5 req/s; main-site demo 10/hour; contract not tested | No contractual SLA established locally; Enterprise SLA is advertised, not contracted | **NEEDS_DISPLAY_RIGHTS** and plan-specific resale terms; auction-only candidate |
| NHTSA/vPIC | Existing project [provider registry](../backend/app/services/provider_registry.py); [vPIC](https://vpic.nhtsa.dot.gov/api/) | Public technical/recall access, no history account | Public API | Public access does not equal priced history product | n/a | VIN decode only, not history coverage | US federal vehicle identity/recall domain | Not assessed in this audit | Not assessed | **NOT_SUITABLE** for paid ownership/auction history |
| Stat.vin | Public site only; [terms](https://stat.vin/terms-of-service) | No authorized API credential | Not documented | ? | ? | No authorized preflight | US auction archive claimed, no completed lookup | ? | ? | **BLOCKED** by recorded access/reuse audit |
| Bid.cars | Public site only; [robots](https://bid.cars/robots.txt) | No authorized API credential | Not documented | ? | ? | No authorized preflight | Auction archive claimed, no completed lookup | ? | ? | **BLOCKED** by archived-search robots audit |
| Bidfax | Public site only; [robots](https://bidfax.info/robots.txt) | No authorized API credential | Not documented | ? | ? | No authorized preflight | Auction archive claimed, no completed lookup | ? | ? | **BLOCKED**: access challenge / HTTP 403 in local audit |
| Vinfax | Public site only; [entry](https://www.vinfax.net/vin/check) | No authorized API credential | Not documented | ? | ? | No authorized preflight | Auction archive claimed, no completed lookup | ? | ? | **BLOCKED**: HTTP 403 in local audit |
| FinalBid | Public site only; [terms](https://finalbid.vin/en/terms) | No authorized API credential | Not documented | ? | ? | No authorized preflight | Auction archive claimed, no completed lookup | ? | ? | **BLOCKED** by recorded automated-collection/commerce terms audit |

## Documented data capability, not a promise about any VIN

| Provider | VIN decoding | Auction records | Auction photos | Accident/damage history | Odometer events | Title/salvage/total loss | Theft | Lien/finance | Registration history | Sales history | Recall data |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ClearVin | Yes | Auction API | Auction API | Auction damage and report categories | NMVTIS/vehicle report | NMVTIS API, distinct event types | Report category | Report category | Title/registration states | Auction sales; wider sales coverage ? | [Business page](https://www.clearvin.com/en/custom-solutions/) lists recalls |
| Auto.dev | Yes; old Ford pilot 200 | No confirmed auction *event* API in reviewed endpoints | Photo API; Ford pilot count 0; wholesale/historical coverage flags are not event proof | — | — | — | — | — | — | Current dealer listings only, not vehicle-life sales chronology | Growth endpoint documented, not tested here |
| API Auctions | VIN decoder documented | Public auction-lot index | Photo URLs documented | Lot damage fields; not a comprehensive accident file | Lot odometer snapshots | Lot title text only; not authoritative NMVTIS/total-loss file | — | — | — | Auction sale events | — |
| NHTSA/vPIC | Yes | — | — | — | — | — | — | — | — | — | NHTSA recall dataset separate from vPIC decode |
| Stat.vin | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | ? | ? | ? | Public page claim only | ? |
| Bid.cars | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | ? | ? | ? | Public page claim only | ? |
| Bidfax | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | ? | ? | ? | Public page claim only | ? |
| Vinfax | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | ? | ? | ? | Public page claim only | ? |
| FinalBid | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | Public page claim only | ? | ? | ? | Public page claim only | ? |

The five public auction sites above are **recorded access audits**, not successful
VIN lookups. Their capability labels came from the existing adapter metadata and
must not be used to create a preview count or `NO_RECORDS` result. See the saved
[access audit](../deliverables/Stage6_3_Evidence/provider-access-audit.json) and
[source checkpoint](STAGE6_3_SOURCE_AUDIT.md).

## Rights to retain and show data

| Provider | Raw data retention allowed | Display to end customer allowed | Resale allowed | Photo display rights |
| --- | --- | --- | --- | --- |
| ClearVin | ?; obtain API agreement | ?; obtain product-specific agreement | [Website terms](https://www.clearvin.com/en/terms-and-conditions/) prohibit resale without express written authorization | ?; explicit image display, cache, PDF and thumbnail rights needed |
| Auto.dev | Standard [terms](https://www.auto.dev/terms) grant internal-business use, not a derivative database | Ambiguous against app-integration language; require written product licence | Standard terms prohibit resale/redistribution/sublicensing of Automotive Data | Not granted merely by Photos API availability; written clarification needed |
| API Auctions | [Terms](https://apiauctions.io/terms_and_conditions/) permit storing responses for own product, subject to plan/use | Responses in own product under terms, subject to source-platform restrictions | Site FAQ says Pro/Enterprise resale, but applicable PAYG/pack product rights need written clarification; API itself may not be resold/rebranded | [Legal page](https://apiauctions.io/legal) says third-party URLs are passed through, not re-hosted; no independent copyright licence established |
| NHTSA/vPIC | Dataset-specific rights assessment outside this paid-history audit | Only applicable federal facts, after dataset rights check | Not a resaleable history service | n/a |
| Stat.vin | Not authorized | Not authorized | Not authorized | Not authorized |
| Bid.cars | Not authorized | Not authorized | Not authorized | Not authorized |
| Bidfax | Not authorized | Not authorized | Not authorized | Not authorized |
| Vinfax | Not authorized | Not authorized | Not authorized | Not authorized |
| FinalBid | Not authorized | Not authorized | Not authorized | Not authorized |

## Commercial decision and exact blockers

No reviewed live history provider is ready for production activation. ClearVin is the
closest **documented product-category match**, but needs an API account/test access,
per-product/per-VIN price and volume schedule, charge/refund/retry behavior, sample
preflight/coverage semantics, webhook or polling details, permitted retention, explicit
paid end-user report/resale rights, and separate auction-photo display/cache/PDF rights.
The historical `$0.30–$0.50` discussion in
[product rules](BUYER_EXPERIENCE_V1_PRODUCT_RULES.md) is a negotiation hypothesis,
**not** a quote. The website's consumer report price must not be inserted as API cost.

API Auctions has a previously documented fixed sandbox and a published PAYG call price, but the project
has no production token, accepted account terms, proven arbitrary-VIN coverage or
third-party photo grant. Its documented count endpoint can preflight **auction sales
count only** and might itself consume a metered call. Its lot title/odometer/damage fields are auction observations,
not substitutes for an NMVTIS title or comprehensive insurance/theft/registration
record. Auto.dev's prior exact-VIN pilot found only decode, no listing/photos; its
current standard terms and product mix do not justify a paid history-report sale.
No paid endpoint, sign-up, billing action or photo download was performed in this audit.
