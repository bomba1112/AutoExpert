# Auto Expert 2.0 — Stage 3 checkpoint

Date: 2026-09-14

## STAGE: Real Vehicle Knowledge Pilot

STATUS: PASS

REAL VEHICLE:

`Toyota / Camry / XV70 / USA / 2019 / 2.5 L A25A-FKS / UB80E 8AT / FWD`

IMPLEMENTED:

- A separately versioned `REAL` Vehicle Knowledge Profile and variant; the existing
  deterministic providers and all Stage 1/2 flows remain intact.
- Nine normalized source records across official Tier A, reputable technical Tier B,
  and owner-experience Tier C sources.
- Nineteen normalized evidence items, including six model-year recall campaigns and one
  Toyota manufacturer communication. Eighteen items are `CONFIRMED`; the model-level
  expert verdict remains an `ESTIMATE`.
- Four source-linked Known Issues. Mileage and repair cost are deliberately absent where
  the reviewed evidence does not support them.
- Ten deduplicated NHTSA ODI owner submissions. They remain allegations in a pilot sample;
  aggregation reports “X of Y reviewed materials,” never a fleet failure rate.
- A 16-section AZ/RU/EN real dossier and existing grounded chat responses carrying real
  evidence/source IDs.
- `NHTSAUSDataProvider` for vPIC decode, recalls, and complaints with normalized DTOs,
  24-hour bounded process cache, and safe `INSUFFICIENT_DATA` failure behavior.
- Explicit `data_origin=REAL|DEMO` separation through persistence, API DTOs, dossier,
  chat context, source attachments, and Web Preview.

REAL DATA COUNTS:

- Real sources: 9
- Confirmed evidence items: 18
- Known issues: 4
- Owner materials: 10
- Recalls: 6
- Manufacturer communications: 1
- Dossier sections with real data: 16/16

DATA QUALITY:

- Every real evidence item is linked to an active real source.
- `CONFIRMED` dossier claims require both source and evidence identifiers.
- Recall entries are explicitly model-level; exact VIN applicability and completed remedy
  require a VIN-specific check.
- Owner materials cannot automatically create a `CONFIRMED` Known Issue.
- The dossier makes no engine-life, repair-cost, or fleet failure-rate claim.
- The real model dossier and synthetic demo VIN history are visibly and structurally
  distinct; demo Salvage/photos are not represented as real Camry history.

TESTS:

- Full suite: 57 passed.
- Stage 3 coverage includes origin isolation, required source linkage, NHTSA
  normalization/cache/failure, owner deduplication, weak-evidence boundaries, Camry
  resolution, 16-section dossier quality, abbreviation localization, grounded source IDs,
  paywall/origin separation, retrieval dates, and source-manifest consistency.
- Ruff, JavaScript syntax, Alembic head, real-process HTTP assets/API flow, and restart
  persistence: PASS.

LIMITATIONS:

- VIN history is still an explicitly synthetic `DEMO` fixture; no paid history provider
  is connected.
- Owner experience is a deliberately small NHTSA complaint pilot and is not representative
  of all owners or vehicles.
- Manufacturer communications are seeded from one reviewed official Toyota/NHTSA PDF;
  the provider does not invent a public JSON endpoint where none is stable.
- No production LLM, real payment, local market pricing, or repair-cost data is enabled.

REPRODUCE:

```bash
uv sync --locked --group dev
uv run alembic -c backend/alembic.ini upgrade head
uv run pytest -q
uv run ruff check backend
cd backend && uv run python -m app.run_preview --host 127.0.0.1 --port 8000
```

The frozen source inventory and expected counts are in
`data/seed/real_camry_2019_us_manifest.json`.
