# Auto Expert phone preview

This preview serves the FastAPI backend and the VIN-first mobile web client from one
process. Model dossiers can contain separately labelled `REAL` evidence; bundled VIN
history is synthetic, marked `is_demo=true` / `DEMO DATA`, and must not be interpreted as
a real history record for the example identifier.

## 1. One-time setup

From the repository root:

```bash
cp .env.example .env
uv sync --group dev
```

Keep `AUTOEXPERT_DEMO_MODE=true` and `AUTOEXPERT_PAYMENT_PROVIDER=mock` for this preview.
Local developer review also defaults to `AUTOEXPERT_DEVELOPER_MODE=true` and
`AUTOEXPERT_DEVELOPER_SIMULATE_USER_PAYWALL_DEFAULT=false`.
Do not expose the development configuration directly to the public internet.

## 2. Start the complete app

```bash
cd backend
uv run python -m app.run_preview --host 0.0.0.0 --port 8000
```

The command applies the current Alembic migration, adds the idempotent demo fixture when
needed, then starts Uvicorn. Leave this terminal open.

First verify on the computer:

```text
http://127.0.0.1:8000/preview/
```

## 3. Find the computer's LAN address

Use the active Wi-Fi adapter's IPv4 address—normally `192.168.x.x` or `10.x.x.x`.

- Windows: run `ipconfig` and read **IPv4 Address** under the Wi-Fi adapter.
- Linux: run `hostname -I` and use the LAN address, not `127.0.0.1`.
- macOS: run `ipconfig getifaddr en0` for the usual Wi-Fi interface.

If the computer address is `192.168.1.25`, open this exact pattern on Android:

```text
http://192.168.1.25:8000/preview/
```

The phone and computer must be on the same Wi-Fi network. Do not use `localhost` on the
phone: that points back to Android itself.

## 4. Demo access

No credentials are required. Choosing a language and continuing creates a new isolated
non-admin demo user and stores its signed token only in that browser. Reports created by
one demo browser session are not accessible from another session. Refreshing the page or
restarting the backend with the same database and secret preserves access while the token
is valid.

By default the blue **DeveloperMode** toolbar is visible. The report owner receives the
full history, dossier, sources, and unlimited chat immediately; no entitlement or payment
record is created. Ownership remains enforced, so another demo account still receives
404 for the report.

Use **Insert test VIN** for `3FA6P0HD0KR114795`, the Ford-compatible 2019 Ford Fusion
example. The attached history remains synthetic demo data and does not claim real events
for that VIN.

Enable **Simulate User Paywall** to test the ordinary product path. Only then does the
browser receive a locked teaser and the configured 5 AZN price; the payment screen creates
a mock `VIN_REPORT_UNLOCKED` entitlement. It never requests card details and no money is
charged. The browser switch sends only an opt-in simulation header and cannot activate
DeveloperMode when the backend flag is disabled.

## 5. If the phone cannot connect

1. Confirm the computer can open `http://127.0.0.1:8000/preview/`.
2. Confirm the terminal says Uvicorn is listening on `0.0.0.0:8000`.
3. Confirm both devices are on the same non-guest Wi-Fi; guest networks often isolate
   devices from each other.
4. Allow inbound TCP port `8000` for the Python/Uvicorn process in the computer firewall,
   limited to the private/local network profile.
5. Recheck the computer's current LAN IPv4 address after changing networks.

## Current intentional limits

- The quick VIN fixture uses a Ford-compatible identity shell. Its powertrain remains
  unresolved instead of borrowing Toyota data.
- Every displayed VIN event, auction value, odometer record, and photo placeholder is
  synthetic demo data. Real model dossier sources are labelled separately.
- Turbo.az / Tap.az parsing is a disabled P1 placeholder.
- Auto Expert Chat is grounded in the stored report context and is unlimited only in the
  default developer review mode.
- There is no public URL until a deployment target and credentials are provided.
