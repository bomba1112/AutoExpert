# Auto Expert 2.0 — Stage 5 checkpoint

Date: 2026-09-16

## STAGE: Real Network & Variant Resolution

STATUS: PASS — implementation, deterministic acceptance, and live production-provider
validation all pass. The earlier Work-runtime egress restriction was environment-specific
and is not a project blocker.

- REAL NETWORK: PASS
- LIVE VPIC: PASS
- LIVE RECALLS: PASS
- LIVE COMPLAINTS: PASS
- LIVE COMMUNICATIONS: PASS

## Preserved baseline

- Stage 4 automatic research, source/evidence quality gate, dossier, grounded chat,
  entitlement, ownership, and REAL/DEMO separation remain intact.
- Manual Camry seed is not imported or executed by the production research path.
- Full suite: 75 tests pass (64 prior tests plus 11 Stage 5 regression tests).

## Identifier validation

- `VehicleIdentifierType`: `VIN`, `CHASSIS_NUMBER`, `FRAME_NUMBER`.
- USA/Canada: 17 characters, I/O/Q rejected, North-American check digit required.
- Korea: international 17-character format; North-American check digit is not applied.
- Regression identifier `KLABA76BDJB723118`: ACCEPTED for Korea.
- Japan: VIN plus typed 5–30 character chassis/frame identifiers.
- Europe/China use an extensible international VIN strategy.

## Variant resolution

- Production `VehicleVariantResolver` returns `RESOLVED`, `AMBIGUOUS`, or
  `INSUFFICIENT_DATA`.
- Official NHTSA Safety Ratings configuration labels are normalized as candidates.
- A user engine hint filters supported candidates but cannot create an engine fact.
- Ambiguous candidates are saved in `ResearchJob`; owner-scoped selection resumes the
  same job and uses the 24-hour provider cache.
- Generation, engine code, transmission, drivetrain, or body stay unknown when no
  selected provider record proves them.

## Deterministic fresh-database acceptance

This acceptance uses production providers with a mocked HTTP transport only for
repeatable CI; it is separate from the live-network result below.

- Test vehicle: Toyota Camry 2019 2.5 USA.
- Preexisting profile: NO.
- Manual seed used: NO.
- First HTTP requests: 7.
- Profile created: YES.
- Sources created: 5.
- Evidence created: 6.
- First request time: 0.0644 seconds.
- Second request cache/profile hit: YES.
- Second external requests: 0.
- Second request time: 0.0069 seconds.

## Live provider smoke

Live validation was completed locally on Windows using the unchanged Stage 5 source,
production `httpx` transport, real official endpoints, and no `MockTransport`.

| Provider | HTTP | Latency | Normalized records | Result |
|---|---:|---:|---:|---|
| vPIC | 200 | ~12,424 ms | 1 | PASS |
| NHTSA recalls | 200 | ~709 ms | 6 | PASS |
| NHTSA complaints | 200 | ~1,708 ms | 100 | PASS |
| Manufacturer communications | 200 | ~40,670 ms | 17 | PASS |

- `live_pass=true`.
- Second identical request: cache HIT for all four providers.
- Second-request external calls: 0.
- No provider code changes were required for the successful local validation.
- `artifacts/stage5_live_smoke.json` remains the audit record of the earlier restricted
  Work-runtime attempt; the successful Windows result supersedes it for Stage 5 status.

Reproduce on a host with ordinary internet egress:

```bash
uv run python backend/scripts/live_provider_smoke.py
```

## Web Preview

- Input supports market plus VIN/chassis/frame type.
- The progress view renders actual backend state for identity, official databases,
  variants, user refinement, evidence, and dossier.
- An ambiguous job renders touch-friendly official candidate labels and posts the
  selection to `/research/jobs/{id}/variant-selection`.
- AZ/RU/EN locale keys remain structurally identical.

## Reproduce

```bash
uv sync --locked --group dev
uv run alembic -c backend/alembic.ini upgrade head
uv run ruff check backend/app backend/tests
uv run pytest -q
node --check apps/web_preview/app-v2.js
uv run python backend/scripts/live_provider_smoke.py
```
