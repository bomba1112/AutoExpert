from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlencode

import httpx

from app.models.enums import EvidenceStatus
from app.schemas.us_data import (
    NHTSAComplaintRecord,
    NHTSAFetchResult,
    NHTSARecallRecord,
    NHTSAVINDecodeRecord,
)


class USVehicleDataProvider(Protocol):
    name: str

    def decode_vin(self, vin: str) -> NHTSAFetchResult | dict: ...

    def recalls_by_vehicle(self, *, make: str, model: str, year: int) -> NHTSAFetchResult: ...

    def complaints(self, *, make: str, model: str, year: int) -> NHTSAFetchResult | list[dict]: ...

    def manufacturer_communications(
        self, *, make: str, model: str, year: int
    ) -> NHTSAFetchResult | list[dict]: ...


class NHTSAUSDataProvider:
    """Free official NHTSA/vPIC adapter with bounded caching and safe failures."""

    name = "nhtsa"
    base_url = "https://api.nhtsa.gov"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        cache_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        self._client = client or httpx.Client(timeout=15.0, follow_redirects=True)
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[datetime, NHTSAFetchResult]] = {}

    def decode_vin(self, vin: str) -> NHTSAFetchResult:
        url = f"{self.base_url}/vehicles/DecodeVinValues/{vin}?format=json"

        def normalize(payload: dict) -> list[dict]:
            rows = payload.get("Results") or payload.get("results") or []
            if not rows:
                return []
            row = rows[0]
            model_year = row.get("ModelYear")
            record = NHTSAVINDecodeRecord(
                vin=vin,
                make=row.get("Make") or None,
                model=row.get("Model") or None,
                model_year=int(model_year) if str(model_year).isdigit() else None,
                engine_model=row.get("EngineModel") or None,
                displacement_l=row.get("DisplacementL") or None,
                transmission_speeds=row.get("TransmissionSpeeds") or None,
                error_code=row.get("ErrorCode") or None,
                error_text=row.get("ErrorText") or None,
            )
            return [record.model_dump(mode="json")]

        return self._fetch(url, normalize)

    def recalls_by_vehicle(self, *, make: str, model: str, year: int) -> NHTSAFetchResult:
        query = urlencode({"make": make, "model": model, "modelYear": year})
        url = f"{self.base_url}/recalls/recallsByVehicle?{query}"

        def normalize(payload: dict) -> list[dict]:
            return [
                NHTSARecallRecord(
                    campaign_number=str(row["NHTSACampaignNumber"]),
                    manufacturer=str(row.get("Manufacturer") or ""),
                    report_received_date=row.get("ReportReceivedDate"),
                    component=str(row.get("Component") or ""),
                    summary=str(row.get("Summary") or ""),
                    consequence=row.get("Consequence"),
                    remedy=row.get("Remedy"),
                    notes=row.get("Notes"),
                    make=str(row.get("Make") or make).upper(),
                    model=str(row.get("Model") or model).upper(),
                    model_year=int(row.get("ModelYear") or year),
                ).model_dump(mode="json")
                for row in payload.get("results", [])
            ]

        return self._fetch(url, normalize)

    def complaints(self, *, make: str, model: str, year: int) -> NHTSAFetchResult:
        query = urlencode({"make": make, "model": model, "modelYear": year})
        url = f"{self.base_url}/complaints/complaintsByVehicle?{query}"

        def normalize(payload: dict) -> list[dict]:
            return [
                NHTSAComplaintRecord(
                    odi_number=str(row["odiNumber"]),
                    incident_date=row.get("dateOfIncident"),
                    components=str(row.get("components") or ""),
                    normalized_summary=" ".join(str(row.get("summary") or "").split()),
                    crash=bool(row.get("crash", False)),
                    fire=bool(row.get("fire", False)),
                    injuries=int(row.get("numberOfInjuries") or 0),
                    deaths=int(row.get("numberOfDeaths") or 0),
                ).model_dump(mode="json")
                for row in payload.get("results", [])
            ]

        return self._fetch(url, normalize)

    def manufacturer_communications(self, *, make: str, model: str, year: int) -> NHTSAFetchResult:
        del make, model, year
        return NHTSAFetchResult(
            status=EvidenceStatus.INSUFFICIENT_DATA,
            retrieved_at=datetime.now(UTC),
            error=(
                "No stable public JSON endpoint is available; ingest manufacturer "
                "communications from official NHTSA document records."
            ),
            source_url="https://www.nhtsa.gov/resources-investigations-recalls",
        )

    def _fetch(self, url: str, normalize) -> NHTSAFetchResult:  # noqa: ANN001
        now = datetime.now(UTC)
        cached = self._cache.get(url)
        if cached and cached[0] > now:
            result = deepcopy(cached[1])
            result.from_cache = True
            return result
        try:
            response = self._client.get(url)
            response.raise_for_status()
            records = normalize(response.json())
            result = NHTSAFetchResult(
                status=EvidenceStatus.CONFIRMED if records else EvidenceStatus.INSUFFICIENT_DATA,
                records=records,
                retrieved_at=now,
                source_url=url,
            )
            self._cache[url] = (now + self._cache_ttl, deepcopy(result))
            return result
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            return NHTSAFetchResult(
                status=EvidenceStatus.INSUFFICIENT_DATA,
                retrieved_at=now,
                error=f"NHTSA provider unavailable: {type(error).__name__}",
                source_url=url,
            )


class DeterministicUSDataFixtureProvider:
    name = "deterministic_us_fixture"

    def decode_vin(self, vin: str) -> dict:
        return {"vin": vin, "fixture": "decode", "is_demo": True}

    def recalls(self, vin: str) -> list[dict]:
        return [{"vin": vin, "fixture": "recall-shell", "is_demo": True}]

    def recalls_by_vehicle(self, *, make: str, model: str, year: int) -> list[dict]:
        return [
            {
                "make": make,
                "model": model,
                "year": year,
                "fixture": "recall-shell",
                "is_demo": True,
            }
        ]

    def complaints(self, *, make: str, model: str, year: int) -> list[dict]:
        return [
            {
                "make": make,
                "model": model,
                "year": year,
                "fixture": "complaint-shell",
                "is_demo": True,
            }
        ]

    def manufacturer_communications(self, *, make: str, model: str, year: int) -> list[dict]:
        return [
            {
                "make": make,
                "model": model,
                "year": year,
                "fixture": "manufacturer-communication-shell",
                "is_demo": True,
            }
        ]
