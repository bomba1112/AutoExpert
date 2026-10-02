# Auto Expert 2.0 — Stage 2 checkpoint

Date: 2026-09-14

## STAGE: Grounded Auto Expert Chat

STATUS: PASS

IMPLEMENTED:

- Owner-scoped, versioned, immutable chat-context snapshots containing the Vehicle
  Knowledge Profile, VIN summary and entitled history, dossier, known issues, owner
  feedback, market analysis, local costs, sources, evidence statuses, and language.
- Canonical SHA-256 snapshot integrity verification before every read and answer.
- Replaceable `ChatLLMProvider` boundary and deterministic AZ/RU/EN demo provider.
- Grounding validation that rejects unknown evidence/sources, locked VIN claims, internal
  payload markers, and evidence-status upgrades.
- Conversation memory isolated by VIN check and user; messages persist in the database.
- Configurable `ChatAccessPolicy` for included, limited, premium-unlimited, and subscription
  modes. Demo sessions remain unlimited without real billing.
- Source attachments, first-use technical abbreviation explanations, explicit inspection
  boundaries, and insufficient-evidence responses.
- Mobile Web Preview chat with a masked VIN header, report-grounded indicator, suggested
  questions, conversation bubbles, loading state, status badges, source expansion, and
  sticky composer.

TESTS:

- 46 backend tests pass: the preserved 36-test Stage 1 baseline plus 10 Stage 2 tests.
- Ownership, vehicle isolation, locked-history non-disclosure, malicious prompt handling,
  insufficient evidence, status preservation, sources, AZ/RU/EN, memory, and database
  reload persistence are covered.
- Fresh SQLite migration to Alembic head and `alembic check`: PASS.
- Ruff, JavaScript syntax, JSON localization parity, and real-process HTTP flow: PASS.
- Real-process restart persistence for the chat session and its messages: PASS.

SECURITY:

- Chat endpoints enforce both report ownership and an active VIN entitlement.
- Locked VIN history is absent from locked context and cannot be retrieved through chat.
- The browser receives relative same-origin API paths and no model key or backend snapshot.

ISSUES:

- Vehicle, VIN history, sources, and chat answers remain explicitly synthetic DEMO data.
- The deterministic provider validates the complete product flow; no paid or production
  LLM is connected.
- Two non-blocking deprecation warnings originate from the current Starlette TestClient.

NEXT:

- Add a production `ChatLLMProvider` behind environment configuration and evaluate grounded
  answer quality against a larger evidence corpus before enabling any real model traffic.
