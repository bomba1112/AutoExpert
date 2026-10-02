# Auto Expert 2.0 — Stage 6 Android Alpha

## Outcome

- APK build: PASS
- Package: `com.autoexpert.demo`
- Version: `0.6.1-alpha` (`versionCode=61`)
- Android: `minSdk=24`, `targetSdk=35`
- Default development API: `http://127.0.0.1:8000/api/v1`
- Production backend URL embedded: NO
- Provider/payment/model credentials embedded: NO
- DeveloperMode default from backend: ON
- Simulate User Paywall: independent switch

## Reuse and boundaries

The recovered existing Android demo shell was adapted rather than introducing a second client.
It packages the same mobile-first HTML, CSS, JavaScript, and AZ/RU/EN catalogs used by the Web
Preview. FastAPI remains authoritative for research jobs, variant resolution, VIN access,
dossiers, sources, chat, ownership, and mock entitlement. Stage 5 providers and research logic
were not changed.

The device connection is configurable at build time. The default is intended only for:

```text
Windows FastAPI 127.0.0.1:8000
            ↑
adb reverse tcp:8000 tcp:8000
            ↑
Android alpha 127.0.0.1:8000
```

Cleartext traffic is permitted only for the local development hosts declared by the Android
network-security configuration. The packaged UI is served from
`https://appassets.autoexpert.local/preview/`; CORS allows that origin without exposing secrets.

## Verified flow

- Ford example VIN `3FA6P0HD0KR114795` resolves only to the Ford Fusion demo identity.
- Korean VIN `KLABA76BDJB723118` is accepted by the Korea strategy and completes as `PARTIAL`
  with unresolved fields, rather than being rejected by the North-American checksum.
- DeveloperMode returns the full owner-scoped report and unlimited grounded chat without an
  entitlement or price.
- Simulate User Paywall returns the locked teaser, configured `5.0 AZN` price, mock payment,
  and `VIN_REPORT_UNLOCKED` entitlement.
- Full dossier has 17 sections in the focused live smoke, sources are present, and chat answers
  are generated from the current report context.
- My Reports data survives a backend process restart in the persistent SQLite database.
- AZ, RU, and EN catalogs load with identical contracts.
- Backend-unavailable copy and reconnect action are packaged in all three languages.

## Android runtime evidence

The signed APK was accepted by the Android 15/API 35 Package Manager (`Success`), the process
started, and `MainActivity` reached `topResumedActivity`. This Work runtime has no `/dev/kvm` and
blocks socket/ptrace operations used by its AOSP WebView renderer; the system renderer therefore
crashed during visual automation. That is an emulator/runtime limitation, not an application
exception. The remaining product flow was verified against a real Uvicorn process through the
same API paths and packaged asset contract. Final visual/manual acceptance remains the project
owner's physical Android device using `adb reverse`.

## Delivery

- Artifact: `deliverables/AutoExpert_2_0_Alpha.apk`
- SHA-256: `b814c70db05ff70015e8357c38c6d81d65d0e50b664c997f96d79cb8f45df95f`
- Size: `71,181` bytes
- Signing: development certificate; APK Signature Scheme v2 and v3
- Build: `apps/android_demo/build.sh`
- Backend regression: `79 passed`; baseline preserved
- Ruff, JavaScript syntax, locale JSON, APK archive, and packaged-asset checks: PASS
- No next product stage was started.
