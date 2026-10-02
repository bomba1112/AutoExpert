# Auto Expert 2.0 Android Alpha

This is the recovered source form of the existing `com.autoexpert.demo` WebView shell.
It packages the current mobile Web Preview and connects it to the existing FastAPI backend.
It does not introduce a second business-logic client or duplicate the research pipeline.

## Build

The default development endpoint is `http://127.0.0.1:8000/api/v1` and is intended for:

```bash
adb reverse tcp:8000 tcp:8000
```

Build from the repository root:

```bash
apps/android_demo/build.sh
```

Windows can use the installed Android SDK and Android Studio JDK directly:

```powershell
uv run python apps/android_demo/build.py
```

No emulator, Gradle download, or system image is required. The Python builder reads the
version from `AndroidManifest.xml`, packages the existing Web Preview, and verifies the
APK signature. The persistent local test key lives in `.signing/` and must be retained for
future updates. Stage 6.1 delivery lacked the previous private signing key; the first local
0.6.5 installation used a new test key after backing up the installed APK and application
data. The original backup remains in `.runtime/original-0.6.4/`.

Override the endpoint without changing source:

```bash
AUTOEXPERT_API_BASE_URL=https://example.invalid/api/v1 apps/android_demo/build.sh
```

The current alpha version is `0.6.6-alpha` (`versionCode=66`). It uses package
`com.autoexpert.demo`, minSdk 24, targetSdk 35, portrait mode,
local WebView assets, persistent WebView local storage, and debug/test signing. No
production server, provider key, payment key, or other secret is embedded.

## Install and run against a Windows backend

Start FastAPI on Windows at `127.0.0.1:8000`, enable USB debugging on the test phone, then:

```powershell
adb devices
adb reverse tcp:8000 tcp:8000
adb install -r deliverables\AutoExpert_2_0_Alpha_0.6.6.apk
```

The reverse mapping is intentionally a development concern and is not baked into the APK.
If the cable is disconnected or the phone restarts, run the `adb reverse` command again.
The app then reconnects with the visible **Подключиться снова / Yenidən qoşul / Reconnect**
action instead of losing locally retained WebView state.

## Verification

From the repository root:

```bash
uv run pytest -q
apps/android_demo/build.sh
.tooling/android-sdk/build-tools/35.0.0/apksigner verify --verbose --print-certs \
  deliverables/AutoExpert_2_0_Alpha_0.6.6.apk
```

`validate_alpha.mjs` is an optional browser-level replay of the packaged UI against a running
backend. It requires Playwright plus a compatible local Chromium executable supplied in
`CHROME_BIN`; it does not replace the API regression suite or on-device acceptance test.

`validate_device.mjs` connects to an already running physical Android WebView over its ADB
forwarded debug socket (`AUTOEXPERT_DEVICE_CDP`, default `http://127.0.0.1:9223`). It requires
Playwright on the Node module path and never launches a browser or emulator. It checks live
VIN research, all 16 dossier sections, sources, 12 unlimited developer chat questions,
separate simulated payment and its question limit, and RU/AZ/EN dossier/chat flows.
Screenshots, sanitized request paths, and result JSON are saved under
`.runtime/device-acceptance/` (override with `AUTOEXPERT_ARTIFACT_DIR`).
