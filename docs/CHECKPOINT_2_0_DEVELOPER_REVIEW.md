# Auto Expert 2.0 — Developer review checkpoint

Date: 2026-09-17  
Version: 0.6.1

## STATUS: PASS

The Stage 5 provider registry, router, research jobs, market-aware identifier validation,
variant resolver, evidence pipeline, dossier, and grounded chat remain unchanged. This
checkpoint adds only a developer-review access layer and fixture-consistency corrections.

## DeveloperMode

- Local development defaults to `DeveloperMode=true`.
- Access bypass is evaluated by the backend after authentication and ownership checks.
- The owner can immediately open full VIN history, dossier, all snapshot sources, and
  unlimited grounded chat without a payment or entitlement row.
- Mock payment is rejected while bypass is active; the UI has no price or unlock action.
- Production settings reject `DeveloperMode=true` at startup.
- Public DTOs still exclude app secrets, provider credentials, payment provider payloads,
  raw third-party responses, password hashes, and private chat context snapshots.

## Simulate User Paywall

- A separate UI switch opts the developer into the normal user flow.
- The request header is honored only when server-side DeveloperMode is enabled; it can
  reduce access but cannot grant it.
- Simulation restores the locked safe teaser, backend-configured 5 AZN price, mock
  payment, `VIN_REPORT_UNLOCKED` entitlement, and configured question limit.
- Switching back restores developer bypass without modifying or deleting the entitlement.

## VIN fixture integrity

- Developer example: `3FA6P0HD0KR114795`.
- Identity: 2019 Ford Fusion.
- The Ford fixture never receives the Toyota VIN `4T1…`, Toyota mask, XV70 generation,
  A25A-FKS engine, or 8AT transmission data.
- Powertrain fields in the Ford demo identity shell are explicitly `UNRESOLVED`.
- All history events remain synthetic `DEMO DATA`; the real example VIN is not presented
  as proof that those events occurred.
- The legacy Toyota fixture remains isolated for Toyota regression tests.

## Verification

- Ruff: PASS.
- Full regression suite: `79 passed` (`75/75` Stage 5 baseline preserved plus 4 new tests).
- JavaScript syntax: PASS.
- AZ/RU/EN locale JSON and identical-key contract: PASS.
- Local real-process HTML/CSS/JS/API smoke: PASS.
- Default developer bypass, report ownership, full report, sources, and unlimited chat:
  PASS.
- Simulated locked teaser → mock entitlement → full report: PASS.
- Stop/start persistence and My Reports lookup: PASS.
- 390 px mobile behavior remains covered by the CSS/static test contract. This runtime had
  the Playwright module but no installed Chromium binary, so screenshot automation was not
  claimed.

## Run

```bash
cd backend
uv run python -m app.run_preview --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/preview/` on the same computer. For another device, bind to
`0.0.0.0` and use an actually reachable host address; the application itself uses only
relative same-origin API URLs.
