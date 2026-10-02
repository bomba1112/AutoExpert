# Auto Expert Flutter client

The `lib/` tree is the shared client for Android, iOS, and Web. Business calculations
remain on the backend; the client handles validated input, localized presentation, and
authenticated report access.

If generated runner folders are absent, run this once from this directory on a machine
with Flutter installed:

```bash
flutter create --project-name autoexpert_client --platforms=android,ios,web .
flutter pub get
flutter gen-l10n
```

Then start Web with:

```bash
flutter run -d chrome --web-hostname=localhost --web-port=8080 --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Approved buyer and listing flows

The AZ/RU home follows the approved light-blue buyer, dark vehicle-check and
generation-comparison layout. Buyer search uses the existing catalogue
endpoints; production-safe projection is enforced by the backend environment.
Vehicle profiles show only returned confirmed
technical rows; unfilled groups are omitted. Oil facts are grouped once in
"Oils and fluids" when a source-backed value is present.

**Check a vehicle** has separate VIN, Turbo.az and manual tabs. A Turbo.az URL is
validated and saved as a reference only: the client does not fetch or scrape
the listing. The user pastes listing text, selects a local UTF-8 .html/.htm/.txt
snapshot, or enters fields manually. Local file data is bounded to the backend's
60,000-byte text and 256,000-byte HTML limits. The listing response keeps seller
claims distinct from Auto Expert's production-visible catalogue match and shows
ambiguous versions or conflicts as questions rather than technical conclusions.
Only a backend-normalized valid VIN is offered for prefilled VIN history checks.
An original Turbo.az link opens in the external browser on user action.

The listing API shares the isolated demo Bearer session with the VIN flow:
POST `/api/v1/listings/intake` and GET `/api/v1/listings/intake/{id}`.

## VIN-history fixture flow

The **Check a vehicle** card opens VIN input, provider-confirmed preflight,
mock checkout, and an AZ/RU report. **My reports** reopens the last check using
the original isolated demo session. The token and check ID are stored with
platform secure storage; full report events and assets are fetched only after
server-side entitlement checks. The client never embeds provider credentials or
calls a live paid provider.

The current backend history adapter is a local fixture for VIN
`3FA6P0HD0KR114795` only. The client states that limitation before the request
and does not imply coverage for other VINs. `VIN_HISTORY_FIXTURE_ONLY` defaults
to `true`; leave it enabled until a real provider and commercial terms are
approved. English UI currently requests the Russian history report because
this stage defines AZ/RU report projections.

Run the backend in demo mode with the mock payment provider, then start the
Flutter web client:

```bash
flutter pub get
flutter gen-l10n
flutter run -d chrome --web-hostname=localhost --web-port=8080 --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Run `flutter analyze`, `flutter test`, and
`flutter build web --release --no-wasm-dry-run` after editing. The repository
has a Web runner, but no Android/iOS runner folders; platform packaging is a
separate task when those runners are created.
