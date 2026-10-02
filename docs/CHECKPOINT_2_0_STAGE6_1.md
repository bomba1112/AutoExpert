# Auto Expert 2.0 — Stage 6.1 checkpoint

Date: 2026-09-17  
Version: `0.6.4-alpha`

## Status

Stage 6.1 — Dossier Synthesis & Consumer UX: **PASS**.

- Existing research, provider routing, ownership, DeveloperMode, and paywall-simulation flows
  remain intact.
- The complete backend suite passes: **85/85**.
- Android WebView client regressions pass: **2/2**.
- Android APK builds for package `com.autoexpert.demo`, minSdk 24, targetSdk 35.
- APK Signature Schemes v2 and v3 verify with the existing alpha certificate.

## Consumer dossier pipeline

The report path is now:

`provider payload -> normalized Evidence -> aggregation -> quality filter -> localized synthesis -> consumer section`

Original provider text remains server-side in Evidence for audit and Developer diagnostics. It
is not rendered as the main report copy.

Implemented behavior:

- exact VIN identity has priority over optional make/model/year hints;
- vPIC identity normalization retains only fields returned by the official decoder, including
  trim/series, engine details, transmission, drivetrain, body, fuel, and plant country;
- recall records are rendered in RU/AZ/EN as problem, consequence, applicability, and action;
- low-information manufacturer communications stay in Evidence with
  `information_quality=LOW` and are excluded from consumer sections;
- duplicate communications are collapsed before synthesis;
- NHTSA complaints are labelled as an official complaint sample, not owner reviews and not a
  fleet failure probability;
- independent Owner Experience remains a separate provider boundary;
- empty sections are compact and collapsed;
- consumer source cards hide tiers, internal confidence enums, raw API URLs, and provider
  diagnostics; raw provenance remains available only in the Developer diagnostics accordion;
- weak points are not generated from a single complaint.

## Ford acceptance

Regression VIN: `3FA6P0HD0KR114795`.

The integration test runs the real production provider implementations over a deterministic
HTTP transport fixture. It verifies exact-VIN priority and confirms that only provider-returned
variant fields enter the profile. Live network validation remains the previously recorded Stage
5 PASS and was not repeated or replaced by the fixture.

## Android artifact

- File: `AutoExpert_2_0_Alpha_0.6.4.apk`
- SHA-256: `715c575d519537c163fcff27509e10b4315e49f1c055a816266cb5a4e0ba056f`
- API base URL: configurable; alpha default is `http://127.0.0.1:8000/api/v1`
- Device connection remains `adb reverse tcp:8000 tcp:8000` for local owner testing.

No emulator or system image was started or downloaded for this stage.
