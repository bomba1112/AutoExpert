# Verified data baseline · 20 September 2026

Existing project STAGE6_1, backend 0.8.0. No Git repository or AGENTS.md found in this checkout.
Fresh SQLite backup preceded this stage; private receipt is `.runtime/verified-data-baseline.json`.
267 baseline tests passed (two dependency deprecation warnings).

| Exists | Requires extension | Missing real coverage |
|---|---|---|
| Existing AZ/RU UI, Report/chat/PDF, 199-family catalogue, reviewed import pipeline | Scoped ownership evidence, dated Decimal/calendar costs, per-fact document provenance | Manufacturer generations, complete dossiers, maintenance/fitment and dated local quotes |
| Private source/raw storage, revisions, editorial locks, image review | Resumable verification queue and before/after evidence | Human-approved exact vehicle images; commercial reuse rights |

The 1,423 published entries are source-specific EPA model-year test/configuration candidates.
They cover 31 normalized makes and 199 normalized model families in the US market, years 2012–2026.
They are not 1,423 distinct engines or exact commercial trims. There are zero verified generations,
engine codes, transmission codes and full dossiers. The database also retains 25 older variant rows.
MINI/Mini case variants normalize to one make; aliases and source names remain preserved.

All 1,423 EPA IDs join to the cached original CSV. Make/model-year mismatch count is zero;
duplicate catalogue keys, missing publication links and facts lacking source/locator are zero.
The parser constructs each configuration from one EPA row. It does not multiply independent
engine and transmission lists. Similar source test entries remain separate and are not silently merged.
EPA transmission descriptions do not establish torque converter, belt CVT or DCT construction.

Reproducible queries, field completeness and anonymized examples:
`deliverables/VerifiedData/catalog-baseline-audit.json`, `coverage-baseline.json` and
`scripts/audit_verified_catalog.py`. The DRAFT queue contains the existing 199 families, not an
approved Azerbaijan top-100. Listing counts and local fleet observations are separately unknown.

Original variants, report snapshots and source links are preserved. No bulk promotion to a
verified-generation status and no deletion of candidates is authorized by this audit.
