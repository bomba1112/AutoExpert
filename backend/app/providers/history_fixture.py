"""Deterministic local VIN-history fixture. No network or paid provider access."""

from __future__ import annotations

from app.core.vin import validate_vin

FIXTURE_VIN = "3FA6P0HD0KR114795"


class HistoryProviderError(Exception):
    def __init__(self, code: str, *, retryable: bool = False):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class FixtureHistoryProvider:
    id = "local_history_fixture"
    is_mock = True
    capabilities = {
        "preflight": True,
        "decode": True,
        "auction": True,
        "photos": True,
        "photo_display_rights": True,
        "odometer": True,
        "damage": True,
        "title": True,
        "theft": True,
        "registration": True,
        "sandbox_only": True,
    }

    def __init__(self, scenario: str = "history"):
        self.scenario = scenario

    def validate_vin(self, vin: str) -> str:
        vin = validate_vin(vin)
        if vin != FIXTURE_VIN:
            raise HistoryProviderError("VIN_NOT_SUPPORTED")
        return vin

    def decode_vin(self, vin: str) -> dict:
        self.validate_vin(vin)
        return {"make": "Ford", "model": "Fusion", "model_year": 2019, "market": "USA"}

    def preflight(self, vin: str) -> dict:
        self.validate_vin(vin)
        if self.scenario == "timeout":
            raise HistoryProviderError("PROVIDER_TIMEOUT", retryable=True)
        if self.scenario == "rate_limit":
            raise HistoryProviderError("PROVIDER_RATE_LIMIT", retryable=True)
        if self.scenario == "no_history":
            return {
                "available_record_types": [],
                "photo_count": 0,
                "odometer_event_count": 0,
                "damage_records_available": False,
                "title_records_available": False,
                "coverage_limitations": ["No fixture history records"],
                "content_determined_after_purchase": False,
                "history_available": False,
            }
        return {
            "available_record_types": [
                "AUCTION",
                "ODOMETER",
                "TITLE",
                *([] if self.scenario == "no_accident" else ["DAMAGE"]),
            ],
            "photo_count": None if self.scenario == "unknown_photos" else 1,
            "odometer_event_count": 2,
            "damage_records_available": self.scenario != "no_accident",
            "title_records_available": True,
            "coverage_limitations": ["Local synthetic fixture; no real VIN lookup"],
            "content_determined_after_purchase": self.scenario == "unknown_photos",
            "history_available": True,
        }

    def quote(self, vin: str, product: str) -> dict:
        self.validate_vin(vin)
        if product != "VIN_HISTORY":
            raise HistoryProviderError("UNSUPPORTED_PRODUCT")
        # Entirely synthetic economic scenario. Real quotes must be obtained
        # from an authorized provider and never inferred from this fixture.
        return {
            "provider_cost_usd": "1.00",
            "retail_price_azn": "15.00",
            "fx_azn_per_usd": "1.70",
            "payment_fee_azn": "0.45",
            "tax_fee_azn": "0",
            "retry_cost_azn": "0.30",
            "minimum_margin_azn": "8.50",
            "currency": "AZN",
            "mock_only": True,
        }

    def purchase_or_fetch(self, vin: str, product: str, idempotency_key: str) -> dict:
        self.validate_vin(vin)
        if product != "VIN_HISTORY" or not idempotency_key:
            raise HistoryProviderError("INVALID_REQUEST")
        if self.scenario == "post_payment_failure":
            raise HistoryProviderError("PROVIDER_TIMEOUT", retryable=True)
        if self.scenario == "post_payment_permanent_failure":
            raise HistoryProviderError("PROVIDER_FINAL_FAILURE")
        return self.get_report(f"fixture:{vin}")

    def get_report(self, provider_report_id: str) -> dict:
        if provider_report_id != f"fixture:{FIXTURE_VIN}":
            raise HistoryProviderError("REPORT_NOT_FOUND")
        events = [
            {
                "type": "ODOMETER",
                "id": "mock-odo-1",
                "date": "2019-09-01",
                "mileage": 30000,
                "mileage_unit": "mi",
                "summary": "Source-reported mileage",
                "country": "USA",
                "state": "TX",
            },
            {
                "type": "ODOMETER",
                "id": "mock-odo-2",
                "date": "2020-09-01",
                "mileage": 25000,
                "mileage_unit": "mi",
                "summary": "Source-reported mileage",
                "country": "USA",
                "state": "TX",
            },
            {
                "type": "AUCTION",
                "id": "mock-auction-1",
                "date": "2021-02-01",
                "summary": "Mock auction record",
                "country": "USA",
                "state": "TX",
            },
            {
                "type": "TITLE",
                "id": "mock-title-1",
                "date": "2021-03-01",
                "summary": "Mock salvage title event",
                "country": "USA",
                "state": "TX",
                "title_type": "SALVAGE",
            },
        ]
        if self.scenario != "no_accident":
            events.append(
                {
                    "type": "DAMAGE",
                    "id": "mock-damage-1",
                    "date": "2021-02-01",
                    "summary": "Mock damage event",
                    "country": "USA",
                    "state": "TX",
                }
            )
        assets = (
            []
            if self.scenario == "unknown_photos"
            else [
                {
                    "id": "mock-photo-1",
                    "event_id": "mock-auction-1",
                    "photo_type": "WHOLESALE_PHOTO",
                    "media_type": "image/svg+xml",
                    "display_rights_confirmed": True,
                    "caption": {"ru": "Учебный макет фотографии", "az": "Nümunə foto maketi"},
                }
            ]
        )
        return {
            "provider_report_id": provider_report_id,
            "vin": FIXTURE_VIN,
            "events": events,
            "assets": assets,
            "source": {"provider": self.id, "record_type": "SYNTHETIC_FIXTURE"},
        }

    def get_assets(self, provider_report_id: str) -> dict[str, bytes]:
        self.get_report(provider_report_id)
        return {
            "mock-photo-1": (
                '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="240">'
                '<rect width="400" height="240" fill="#e9eff6"/>'
                '<text x="200" y="120" text-anchor="middle" font-size="23" fill="#344a62">'
                "MOCK PHOTO — NO VEHICLE</text></svg>"
            ).encode()
        }

    def normalize(self, raw_response: dict) -> dict:
        if raw_response.get("vin") != FIXTURE_VIN:
            raise HistoryProviderError("VIN_MISMATCH")
        allowed = {
            "ODOMETER",
            "DAMAGE",
            "AUCTION",
            "TITLE",
            "THEFT",
            "REGISTRATION",
            "SALE",
            "INSURANCE",
            "TOTAL_LOSS",
            "SALVAGE",
            "LIEN",
            "RECALL",
        }
        events = []
        for row in raw_response.get("events", []):
            if row.get("type") not in allowed or not row.get("id"):
                continue
            events.append(
                {
                    "event_type": row["type"],
                    "source_record_id": row["id"],
                    "event_date": row.get("date"),
                    "country": row.get("country"),
                    "state": row.get("state"),
                    "mileage": row.get("mileage"),
                    "mileage_unit": row.get("mileage_unit"),
                    "normalized_summary": {
                        "ru": row.get("summary", ""),
                        "az": row.get("summary", ""),
                    },
                    "details": {"title_type": row["title_type"]} if row.get("title_type") else {},
                    "confidence": "SOURCE_REPORTED",
                    "status": "REPORTED",
                }
            )
        return {
            "vin": raw_response["vin"],
            "provider_report_id": raw_response["provider_report_id"],
            "events": events,
            "assets": raw_response.get("assets", []),
            "source": raw_response.get("source", {}),
        }
