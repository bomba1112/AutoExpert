# One VIN-history report: unit economics

Checked 2026-09-29. Calculation code:
[`backend/app/services/vin_unit_economics.py`](../backend/app/services/vin_unit_economics.py).
This is a configurable sale gate, not a retail price decision. The existing
`VIN_CHECK_1=5.00 AZN` and `full_report=2.99 AZN` settings belong to the legacy
mock/demo product and do **not** price a commercial VIN-history report.

For each product/provider quote, save the quote's scope and currency, the dated
AZN-per-USD FX snapshot and source, the proposed retail price, payment fixed and
percentage fees, tax/other fixed and percentage fees, expected retry/fallback
cost, and minimum margin. The required minimum margin is passed explicitly to
`evaluate(...)`; unknown provider cost returns `NEEDS_COMMERCIAL_QUOTE` with
`sellable=False`, never a fictitious zero. USD quotes without an explicit FX rate
return `NEEDS_FX_SNAPSHOT`. Rights/coverage/payment availability are additional
gates outside this arithmetic. The calculation uses `Decimal` and preserves a
negative result.

`provider_cost_azn = provider_cost_usd × FX` (or an AZN quote);
`gross_margin_azn = retail_azn − provider_cost_azn − payment_fee_azn
− tax_fee_azn − retry/fallback_cost_azn`;
`gross_margin_pct = gross_margin_azn / retail_azn`.
The configured rule is `sellable = gross_margin_azn >= minimum_margin_azn`.
The percentage is a fraction in the Python return value; presentation can
multiply by 100. Compare the unrounded Decimal margin to the threshold.

## Current providers, with no invented API price

| Provider | Verified full-history provider cost | Possible retail scenario | Gross margin | Economic/product status |
| --- | --- | --- | --- | --- |
| ClearVin API | **Unknown**; no written project quote | Owner hypothesis: 15 AZN or more, not a set price | Cannot calculate | `NEEDS_COMMERCIAL_QUOTE`; also needs resale/photo rights |
| API Auctions PAYG | [Published](https://apiauctions.io/) USD 0.01/**request**, minimum $25 wallet top-up; total calls for a saleable report and allocation of unused wallet not established | Owner hypothesis: 15 AZN or more | Cannot calculate a complete report margin without actual request plan, fees, FX and rights | `NEEDS_COMMERCIAL_TERMS`; auction-only scope and photo rights unresolved |
| Auto.dev | Published low-cost decode/listing/photo calls are **not** a full VIN-history report | n/a for full history | Cannot calculate a history margin | `NOT_SUITABLE` for this product; standard commercial terms also restrict redistribution |
| NHTSA/vPIC | Public technical/recall endpoints, not paid ownership history | n/a | n/a | `NOT_SUITABLE` as full report provider |
| Stat.vin, Bid.cars, Bidfax, Vinfax, FinalBid | No authorized paid API cost established | n/a | n/a | `BLOCKED` by recorded access/rights audit |

The earlier `$0.30–$0.50/request` figure in
[product rules](BUYER_EXPERIENCE_V1_PRODUCT_RULES.md) is an unaccepted negotiation
hypothesis, not a supplier tariff. ClearVin's public consumer report price is not
an API quote. Auto.dev's published price per endpoint cannot be summed into an
unoffered comprehensive history product. The provider matrix has links and rights
details in [VIN_PROVIDER_CAPABILITY_MATRIX.md](VIN_PROVIDER_CAPABILITY_MATRIX.md).

## Explicit illustration, not a current quote or live FX rate

If one **hypothetical** provider request cost USD 10, retail were AZN 15, and a
**hypothetical** FX snapshot were 1 USD = 1.70 AZN, the provider cost alone would
be AZN 17.00 and margin before payment/tax/retry costs would be **AZN −2.00**.
It is unsuitable even before aiming for roughly USD 5 (in this illustration,
AZN 8.50) minimum gross margin. For any real provider, use its signed quote and
a dated actual FX snapshot; leave the margin unresolved until both exist.

Payment fees, taxes and retries are included in the code path and tested. Their
current real commercial amounts are not established. A product configuration
must explicitly supply them, even when an agreed fee is zero. Subscription fees,
minimum commitments, unused-credit risk and refunds must be allocated to the
unit cost once supplier terms exist; do not treat them as free.
