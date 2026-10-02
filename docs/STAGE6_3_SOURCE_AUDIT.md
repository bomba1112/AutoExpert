# Stage 6.3 source access audit — 2026-09-18

Primary VIN: **3FA6P0HD0KR114795**. All counts below describe observed results,
not a claim that every possible source has been searched.

## Exact VIN discovery

Public indexed searches used the quoted full VIN, the full VIN with auction/history
terms, domain-restricted searches for Stat.vin / Bid.cars / Bidfax, and partial serial
queries. No exact-VIN event page was found. Search-index absence is **not NO_RECORDS**.
It does not prove that a vehicle was never auctioned, damaged or repaired.

| Source | Access evidence | Outcome |
| --- | --- | --- |
| [Stat.vin](https://stat.vin/terms-of-service) | Terms prohibit automated extraction and restrict reuse; robots were also inspected | Restricted; no VIN lookup |
| [Bid.cars](https://bid.cars/robots.txt) | Robots exclude search/results and archived search/results | Restricted; no VIN lookup |
| [Bidfax](https://bidfax.info/robots.txt) | HTTP 403 / access challenge | Stopped; no VIN lookup |
| [Vinfax](https://www.vinfax.net/faq) | FAQ permits respectful public-page crawlers, but the public VIN-check entry returned HTTP 403 | Stopped; no VIN lookup |
| [FinalBid](https://finalbid.vin/en/terms) | Terms prohibit automated collection and commercial reuse | Restricted; no VIN lookup |

The default registry stores these five dated access audits as PROVIDER_UNAVAILABLE,
`query_completed=false`, `audit_kind=SOURCE_ACCESS_NOT_VIN_LOOKUP`. Calling an audited
adapter does not repeat a forbidden request or update the original audit date.
There is **no working authorized live VIN-history connection in this delivery**.

[APIauctions documentation](https://devnew.apiauctions.io/docs) was also inspected.
Its public sandbox is a fixed set of ten VINs; the regression VIN is not among them.
Production requires authentication. It was not registered as a connected provider,
and no credentials, subscription, trial requiring a card, or charges were created.
The normalized AuthorizedHistoryAdapter is an integration boundary, tested with
explicit fixtures; it is not presented as a live APIauctions integration.

No CAPTCHA, login, paywall, robots restriction or anti-bot response was bypassed.
No alternative IP, disguised user agent or challenge workaround was used.

## Owner materials

CarComplaints owner-submission pages were accessible over HTTPS and allowed by
[robots.txt](https://www.carcomplaints.com/robots.txt). The
[terms](https://www.carcomplaints.com/termsofuse.shtml) were reviewed. The provider
stores factual classifications, applicability, source URLs, dates and one-way text
fingerprints. It does not republish full narratives, scrape its restricted search/API,
or use its noncommercial RSS feed. `FACTUAL_SUMMARY_ONLY` is our limited-use policy,
not a claim of an unrestricted commercial licence or an agreement with the publisher.

| Regression configuration | Public owner page | Retrieved | Applicable unique |
| --- | --- | ---: | ---: |
| Ford Fusion 2019, 1.5 L, automatic, USA | [Coolant intrusion / cracked short block](https://www.carcomplaints.com/Ford/Fusion/2019/engine/coolant_intrusion_cracked_short_block.shtml) | 1 | 1 |
| Toyota Camry 2019, 2.5 L I4, automatic, USA | [Transmission total failure](https://www.carcomplaints.com/Toyota/Camry/2019/transmission/total_failure.shtml) | 4 | 2 |
| Hyundai Sonata 2019, 2.4 L, automatic, USA | [High oil consumption](https://www.carcomplaints.com/Hyundai/Sonata/2019/engine/high_oil_consumption.shtml) | 2 | 1 |

The Toyota exclusions are one contradictory V8 entry and one entry without a known
engine. The Hyundai exclusion lacks engine details. Missing attributes are not
filled from the requested variant. Generation and drivetrain are retained when
known; these owner pages do not establish all of them.

All applicable samples are VERY_SMALL and come from one publisher group. The pages
are selected for reported problems, not a representative owner survey. Positive
qualities were not assessed. These are model/variant materials, **not records of the
regression VIN**. One material contributes at most once to each topic. Toyota's
transmission topic has two materials, maintenance one; Ford has one material each
for engine, cooling and maintenance; Hyundai has one engine material.

Raw owner narratives are not included in the distributable source archive or evidence
exports. The raw research cache stays in `.runtime`, excluded from packaging.

Additional access checks:

| Source | Restriction / result |
| --- | --- |
| [Reddit](https://www.reddit.com/robots.txt) | Automated access disallowed |
| [ToyotaNation](https://www.toyotanation.com/robots.txt) | Assistant/crawler access disallowed |
| [Hyundai Forums](https://www.hyundai-forums.com/robots.txt) | Assistant/crawler access disallowed |
| [Cars.com](https://www.cars.com/about/terms/) | Automated-use terms restriction and robots HTTP 403 |
| [Edmunds](https://www.edmunds.com/robots.txt) | AI crawler restrictions; no material imported |
| [Carsurvey](https://www.carsurvey.org/robots.txt) | Robots request timed out; no material imported |
| [Ford Fusion Forum](https://www.fordfusionforum.com/robots.txt) | Robots returned 404; no owner material fetched or claimed |

NHTSA complaints remain OFFICIAL_COMPLAINT evidence. Their mirrors on owner sites
are rejected by the owner parser. My MPG measurements are never counted as owner
reliability reviews. Restricted sources contribute neither materials nor zero-record
claims.

## Ford known issue provenance

Generic `aggregate_issues` joins applicable manufacturer program 19B37, six existing
official complaint signals, and the one independently published owner submission.
Result: source_count=3, independent_source_count=3 publisher groups,
owner_material_count=1, official_complaint_count=6, official_support=true.
Publisher-group independence does not establish that every anonymous complainant is
a different person; identity limitations are retained.

Applicability is 2019 Fusion / 1.5 L / USA, conditional on build date and the program's
VIN list. The new owner material specifies 1.5 L and automatic transmission. The
issue remains **MEDIUM / ESTIMATE**. It does not establish this VIN's defect, current
warranty coverage, or a vehicle failure rate. Hybrid, PHEV, 2.0 L and incompatible
transmission materials are excluded by the generic applicability rules.

## Observed no-record cases

Actual completed VIN-history queries: **0**. Actual NO_RECORDS outcomes: **0**.
True NO_RECORDS and all other provider states are exercised with labelled automated
fixtures. AVAILABLE event/photo fixtures prove normalization and rendering, not
that real photographs or auction records were found for this car.
