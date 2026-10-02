# Stage 6.1 real-device acceptance — 2026-09-18

Active checkout: `STAGE6_1`. Backend `0.6.5`; Android `0.6.5-alpha` (65),
package `com.autoexpert.demo`, minSdk 24, targetSdk 35.

## Final acceptance

Owner-confirmed acceptance on 2026-09-18, following the automated and physical-device
checks recorded below:

```text
REAL DEVICE: PASS
BACKEND: 0.6.5 PASS
APK: 0.6.5-alpha PASS
DEVELOPER MODE: PASS
DOSSIER: PASS
SOURCES: PASS
CHAT: PASS
SIMULATE USER PAYWALL: PASS
REMAINING BLOCKERS: NONE
```

## Verified

- HONOR ALI-NX1 / Android 15, serial `AS7J6R4730001975`, physical USB device.
- Backend runs at `127.0.0.1:8000`; health and database report `ok`.
- `run-preview.ps1` starts successfully from an unrelated directory; migrations reach
  `d942f4c1a6e8`. Repeated preparation is idempotent.
- Live CORS preflights pass for the Android asset origin and localhost ports 3000/8080.
- USB reverse maps device TCP 8000 to host TCP 8000.
- Actual APK WebView flow: sample VIN → live official research → vehicle profile →
  full dossier → sources → contextual chat. Developer flow makes no precheck, demo-precheck,
  payment, or unlock request and creates no entitlement requirement.
- Research VIN `3FA6P0HD0KR114795` resolves to Ford Fusion 2019. Five official source
  records support the dossier; no synthetic history is attached to developer research.
  Initial provider retrieval was live; subsequent language/regression runs reuse its cache.
- All 16 consumer sections are present. Unknown sections remain compact and collapsed.
  Three model-level recall records are localized, with VIN applicability caveats.
  The 100 reviewed official complaints remain distinct from independent owner experience.
- Sources show publisher, purpose, retrieval date and an external link; raw provenance is
  restricted to the collapsed developer diagnostics.
- Developer chat accepts 12 consecutive questions with no question limit. Inspection
  answers retain the dossier checklist; recall answers attach their sources.
- Simulate User Paywall separately shows a locked 5 AZN teaser, mock payment, then
  restores the normal 10-question policy (9 remaining after the first question).
- RU/AZ/EN research, dossier, and contextual chat pass on the actual installed WebView.
  Changing language preserves the owner session. Evidence IDs and statuses agree across
  the three language dossiers. No WebView JavaScript errors or horizontal overflow.
- Backend: **98 tests pass**. Android flow regressions: **3 tests pass**. Ruff passes.
- APK v2/v3 signatures verify. No emulator or system image was used.

Automated testing confirmed that the external source button launches Chrome. The owner
subsequently confirmed `SOURCES: PASS` and `REAL DEVICE: PASS`, closing the outstanding
physical app-lock verification. This final external-source acceptance is owner-confirmed;
it is not a new automated observation. Remaining blockers: none.

## Fixes

1. Restored the missing `backend/alembic.ini`. The calculated project root was already
   correct; the file was absent from this extracted checkout. Alembic paths now resolve
   relative to the configuration, and the Windows launcher selects its checkout explicitly.
2. Added an installed preview entry point and startup/CORS regressions. Added `uv.toml`
   system-certificate support and OS-trusted TLS for official HTTP clients; certificate
   verification remains enabled. This fixes the observed Windows unknown-issuer errors.
3. Removed the developer sample-VIN shortcut into synthetic precheck. Simulation keeps
   its separate mock history/payment flow.
4. Localized consumer labels and removed internal terminology, raw provider errors, and
   unresolved sentinels from normal screens. Improved report-cover contrast and metrics.
5. Grouped official complaint component aliases before counting unique materials; fixed
   rear-camera component classification and the `installed`/`stall` substring error.
6. Preserved inspection actions and applicability in grounded chat, removed unsupported
   claims that service bulletins were found, and kept official complaints outside the
   independent-owner feedback context. Explained ABS and SRS in all three languages.
7. Preserved session ownership on language changes and prevented stale asynchronous
   screen responses from overwriting a newer route.
8. Added a native SDK/JDK Python APK builder and physical-WebView acceptance script.

## Artifacts and operation

- APK: `deliverables/AutoExpert_2_0_Alpha_0.6.5.apk`
- SHA-256: `1f5697f6fd590c46ea14f9162d318f276b1235fc757811326ca7ff0bdd3ef209`
- Real-device JSON, screenshots and sanitized request paths: `.runtime/device-acceptance/`
- Backend logs: `.runtime/backend.stdout.log`, `.runtime/backend.stderr.log`
- Original APK and complete app-data backup: `.runtime/original-0.6.4/`
- Persistent replacement test signing key: `.signing/autoexpert-alpha.jks`

The original private signing key was not supplied, so the first local 0.6.5 installation
used a new alpha key. Application data was backed up before replacement and restored;
backend records were retained. Subsequent APK updates use `adb install -r` with this key.
Do not distribute `.runtime/`, `.signing/`, local databases, or `.env` in source archives.

The backend remains running. USB reconnection requires reapplying the reverse mapping.
This is local development acceptance, not production payment or external AI-provider
acceptance. Chat still uses the deterministic, evidence-grounded adapter. Unsupported
technical fields and unavailable independent owner data remain explicitly unknown.
