# Auto Expert 2.0 — Stage 4 checkpoint

Date: 2026-09-15

## STAGE: Automatic Vehicle Research Pipeline

STATUS: PASS (deterministic integration); live provider smoke unavailable from this
restricted runtime.

AUTOMATIC PROFILE BUILD: PASS

- Test vehicle: Toyota Camry 2019 2.5 USA
- Preexisting profile: NO
- Manual seed used: NO
- Production providers: vPIC, NHTSA recalls, NHTSA complaints, NHTSA manufacturer
  communications
- Deterministic integration HTTP requests: 6 (four capabilities; manufacturer
  communications spans three official date-partition archives)
- Profile created: YES
- Sources created: 4
- Evidence created: 5
- Owner submissions normalized: 2
- Known Issues promoted from complaints: 0
- Dossier generated: 16 sections
- Measured deterministic research time: 0.0266 seconds
- Second request cache hit: YES
- Second request external calls: 0
- Measured second request time: 0.0046 seconds
- Restart persistence: PASS using a file-backed SQLite database and a new application
  client process.

## Implementation

- Persistent `ResearchJob` and `ProviderCacheEntry` models plus Alembic migration.
- Free/cost-ready `ProviderRegistry` with market/capability metadata and a router that
  avoids duplicate capability calls and caches successful normalized responses.
- Production HTTP implementations for vPIC identity, NHTSA recalls, NHTSA complaints,
  and official manufacturer-communication bulk archives.
- Bounded timeout, finite retry, response-size guard, local rate control, normalized
  errors, source URL, retrieval timestamp, and raw audit payload.
- Automatic source, technical evidence, owner evidence, catalog variant, profile, and
  dossier persistence.
- Quality gate rejects conflicting official identities and any REAL profile containing
  DEMO evidence. `CONFIRMED` claims remain source-linked; user engine hints and unsupported
  fields remain unresolved.
- Web Preview make/model/year flow now uses `/research/jobs`; it no longer calls the
  Stage 3 `real-pilot` endpoint. Six visible stages reflect backend result state without
  artificial timers.

## Tests

- Full suite: 64 passed.
- Ruff: PASS.
- JavaScript syntax: PASS.
- Fresh Alembic upgrade through `d942f4c1a6e8`: PASS.
- Fresh DB automatic build, normalized evidence, dossier generation, ownership,
  provider failure, owner-claim status boundary, process restart, and profile reuse:
  PASS.

## Live smoke

The production provider code was invoked directly against both official URLs. The Work
runtime rejected outbound connections with `ConnectError`; each provider correctly
returned `INSUFFICIENT_DATA`, zero records, a source URL, and no fabricated fallback.
Official documentation and the NHTSA web-access channel independently confirmed the
endpoint syntax and live 2019 Camry recall/complaint responses.

## Reproduce

```bash
uv sync --locked --group dev
uv run alembic -c backend/alembic.ini upgrade head
uv run ruff check .
uv run pytest -q
cd backend && uv run python -m app.run_preview --host 127.0.0.1 --port 8000
```
