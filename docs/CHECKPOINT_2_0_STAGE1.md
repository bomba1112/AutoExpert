# Auto Expert 2.0 — Stage 1 checkpoint

Date: 2026-09-14

## STAGE: VIN precheck + Vehicle Dossier

STATUS: PASS

IMPLEMENTED:

- Central `VehicleKnowledgeProfile` with source/evidence relationships, version, and
  freshness metadata.
- ISO-compatible 17-character VIN normalization, forbidden-letter validation, and check
  digit validation.
- Replaceable `VINPrecheckProvider`, deterministic demo provider, and future
  `USVehicleDataProvider` boundary for NHTSA/vPIC, recalls, complaints, and manufacturer
  communications.
- Owner-scoped `VINCheck`, `VINEntitlement`, and `AutoExpertChatContext` snapshots.
- Server-only full history storage and a safe locked teaser DTO.
- Zero-record rule that removes price/purchase actions and returns the required caveat.
- Configured `MODEL_DOSSIER`, `VIN_CHECK_1`, and `VIN_CHECK_3` prices.
- Seventeen-section AZ/RU/EN dossier with evidence status preservation, source IDs,
  inspection boundaries, and first-use abbreviation explanations.
- VIN-first mobile Web Preview with language, VIN/manual entry, precheck, mock unlock,
  full history, full dossier, sources, and saved VIN checks.
- Legacy Stage A/B engines and the old Web Preview JavaScript remain in the repository.

TESTS:

- 36 backend tests pass (27 preserved plus 9 Auto Expert 2.0 tests).
- Fresh SQLite migration to Alembic head and `alembic check`: PASS.
- Ruff, JavaScript syntax, localization key parity, and Python compile: PASS.
- Real-process HTTP flow and database restart persistence: PASS.

ISSUES:

- All Stage 1 VIN data is synthetic and marked `is_demo=true`.
- Listing URL parsing is a disabled P1 placeholder.
- Auto Expert Chat context is prepared; interactive chat is the next P0.
- No paid data or real payment provider is connected.

NEXT:

- Implement grounded Auto Expert Chat using the stored context and source constraints.
