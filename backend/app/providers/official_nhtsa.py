from __future__ import annotations

import csv
import io
import re
import ssl
import threading
import time
import zipfile
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from urllib.parse import quote, urlencode

import httpx

from app.models.enums import EvidenceStatus
from app.schemas.research import ProviderResult, VehicleResearchRequest
from app.schemas.us_data import NHTSAComplaintRecord, NHTSARecallRecord, NHTSAVINDecodeRecord


class OfficialProviderUnavailable(RuntimeError):
    def __init__(self, message: str, *, api_requests: int = 0) -> None:
        super().__init__(message)
        self.api_requests = api_requests


class OfficialHTTPClient:
    """Bounded HTTP client shared by official providers.

    The client has a finite retry count, honors Retry-After only within a small bound,
    and applies a process-local minimum interval between outbound calls.
    """

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 8.0,
        max_attempts: int = 2,
        min_interval_seconds: float = 0.1,
        max_response_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        self.client = client or httpx.Client(
            # Include the OS trust store (not just certifi), including Windows roots.
            # Certificate and hostname verification remain mandatory.
            verify=ssl.create_default_context(),
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": "AutoExpert/0.5 (+vehicle-research)"},
        )
        self.max_attempts = max(1, min(max_attempts, 4))
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self.max_response_bytes = max_response_bytes
        self._lock = threading.Lock()
        self._last_request_at = 0.0

    def get_json(self, url: str) -> tuple[dict, int]:
        content, request_count = self._request(url, headers={"Accept": "application/json"})
        try:
            payload = httpx.Response(200, content=content).json()
        except ValueError as error:
            raise OfficialProviderUnavailable(
                "official provider returned invalid JSON", api_requests=request_count
            ) from error
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise OfficialProviderUnavailable(
                "official provider returned an unexpected payload", api_requests=request_count
            )
        return payload, request_count

    def get_bytes(self, url: str) -> tuple[bytes, int]:
        return self._request(url)

    def _request(self, url: str, *, headers: dict | None = None) -> tuple[bytes, int]:
        last_error: Exception | None = None
        requests_made = 0
        for attempt in range(self.max_attempts):
            self._wait_for_rate_slot()
            requests_made += 1
            try:
                response = self.client.get(url, headers=headers)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                content = response.content
                if len(content) > self.max_response_bytes:
                    raise OfficialProviderUnavailable(
                        "official provider response exceeded the configured size limit",
                        api_requests=requests_made,
                    )
                return content, requests_made
            except (httpx.HTTPError, OfficialProviderUnavailable) as error:
                last_error = error
                if isinstance(error, httpx.HTTPStatusError) and error.response.status_code in {
                    401,
                    403,
                    404,
                }:
                    break
                if attempt + 1 < self.max_attempts:
                    time.sleep(0.15 * (attempt + 1))
        raise OfficialProviderUnavailable(
            f"official provider unavailable: {type(last_error).__name__}",
            api_requests=requests_made,
        ) from last_error

    def _wait_for_rate_slot(self) -> None:
        with self._lock:
            now = time.monotonic()
            remaining = self.min_interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
            self._last_request_at = time.monotonic()


class OfficialVehicleProvider(ABC):
    id: str
    capability: str

    def __init__(self, http: OfficialHTTPClient) -> None:
        self.http = http

    def fetch(self, request: VehicleResearchRequest) -> ProviderResult:
        started = time.perf_counter()
        url = "urn:autoexpert:official-provider"
        try:
            url = self.source_url(request)
            records, raw_payload, api_requests = self._fetch(request, url)
            return ProviderResult(
                provider_id=self.id,
                capability=self.capability,
                status=(
                    EvidenceStatus.CONFIRMED
                    if records or self.empty_is_confirmed
                    else EvidenceStatus.INSUFFICIENT_DATA
                ),
                records=records,
                raw_payload=raw_payload,
                source_url=url,
                retrieved_at=datetime.now(UTC),
                api_requests=api_requests,
                duration_ms=max(0, round((time.perf_counter() - started) * 1000)),
                http_status=200,
            )
        except OfficialProviderUnavailable as error:
            return ProviderResult(
                provider_id=self.id,
                capability=self.capability,
                status=EvidenceStatus.INSUFFICIENT_DATA,
                source_url=url,
                retrieved_at=datetime.now(UTC),
                error=str(error),
                api_requests=error.api_requests,
                duration_ms=max(0, round((time.perf_counter() - started) * 1000)),
                http_status=None,
            )
        except (KeyError, TypeError, ValueError, csv.Error) as error:
            return ProviderResult(
                provider_id=self.id,
                capability=self.capability,
                status=EvidenceStatus.INSUFFICIENT_DATA,
                source_url=url,
                retrieved_at=datetime.now(UTC),
                error=f"official provider normalization failed: {type(error).__name__}",
                api_requests=1,
                duration_ms=max(0, round((time.perf_counter() - started) * 1000)),
                http_status=None,
            )

    @property
    def empty_is_confirmed(self) -> bool:
        return True

    @abstractmethod
    def source_url(self, request: VehicleResearchRequest) -> str: ...

    @abstractmethod
    def _fetch(
        self, request: VehicleResearchRequest, url: str
    ) -> tuple[list[dict], dict | list, int]: ...


class VPICVehicleProvider(OfficialVehicleProvider):
    normalization_version = "6.4-powertrain"
    id = "nhtsa_vpic"
    capability = "vehicle_identity"
    base_url = "https://vpic.nhtsa.dot.gov/api/vehicles"

    @property
    def empty_is_confirmed(self) -> bool:
        return False

    def source_url(self, request: VehicleResearchRequest) -> str:
        if request.vin:
            query = {"format": "json"}
            return f"{self.base_url}/DecodeVinValues/{quote(request.vin, safe='*')}?" + urlencode(
                query
            )
        if not request.make or not request.year:
            raise ValueError("vPIC model lookup requires make and year")
        return (
            f"{self.base_url}/GetModelsForMakeYear/make/{quote(request.make)}/"
            f"modelyear/{request.year}?format=json"
        )

    def _fetch(self, request: VehicleResearchRequest, url: str) -> tuple[list[dict], dict, int]:
        payload, api_requests = self.http.get_json(url)
        rows = payload.get("Results") or payload.get("results") or []
        normalized: list[dict] = []
        if request.vin and rows:
            row = rows[0]
            year = _integer(row.get("ModelYear"))
            decoded = NHTSAVINDecodeRecord(
                vin=request.vin,
                make=_value(row, "Make"),
                model=_value(row, "Model"),
                model_year=year,
                engine_model=_value(row, "EngineModel"),
                displacement_l=_value(row, "DisplacementL"),
                transmission_speeds=_value(row, "TransmissionSpeeds"),
                error_code=_value(row, "ErrorCode"),
                error_text=_value(row, "ErrorText"),
            ).model_dump(mode="json")
            decoded.update(
                body_class=_value(row, "BodyClass"),
                drive_type=_value(row, "DriveType"),
                fuel_type_primary=_value(row, "FuelTypePrimary"),
                fuel_type_secondary=_value(row, "FuelTypeSecondary"),
                transmission_style=_value(row, "TransmissionStyle"),
                vehicle_type=_value(row, "VehicleType"),
                series=_value(row, "Series"),
                series2=_value(row, "Series2"),
                trim=_value(row, "Trim"),
                trim2=_value(row, "Trim2"),
                engine_cylinders=_value(row, "EngineCylinders"),
                engine_configuration=_value(row, "EngineConfiguration"),
                engine_hp=_value(row, "EngineHP"),
                engine_kw=_value(row, "EngineKW"),
                turbo=_value(row, "Turbo"),
                electrification_level=_value(row, "ElectrificationLevel"),
                battery_type=_value(row, "BatteryType"),
                battery_kwh=_value(row, "BatteryKWh"),
                battery_info=_value(row, "BatteryInfo"),
                other_engine_info=_value(row, "OtherEngineInfo"),
                doors=_value(row, "Doors"),
                seats=_value(row, "Seats"),
                plant_country=_value(row, "PlantCountry"),
            )
            # A successfully decoded full VIN is authoritative for identity. Optional
            # make/model/year input is a hint and must not override the VIN result.
            if decoded.get("make") and decoded.get("model"):
                normalized.append(decoded)
        else:
            for row in rows:
                model_name = row.get("Model_Name") or row.get("ModelName")
                make_name = row.get("Make_Name") or row.get("MakeName")
                if _same(model_name, request.model) and _same(make_name, request.make):
                    normalized.append(
                        {
                            "make_id": row.get("Make_ID") or row.get("MakeId"),
                            "make": str(make_name).strip(),
                            "model_id": row.get("Model_ID") or row.get("ModelId"),
                            "model": str(model_name).strip(),
                            "model_year": request.year,
                            "evidence_status": EvidenceStatus.CONFIRMED.value,
                            "data_origin": "REAL",
                        }
                    )
        return normalized, payload, api_requests


class NHTSAVariantProvider(OfficialVehicleProvider):
    """Returns official NHTSA configuration labels without inferring missing mechanics."""

    id = "nhtsa_safety_ratings_variants"
    capability = "vehicle_variants"
    base_url = "https://api.nhtsa.gov/SafetyRatings"

    @property
    def empty_is_confirmed(self) -> bool:
        return False

    def source_url(self, request: VehicleResearchRequest) -> str:
        make, model, year = _required_identity(request)
        return (
            f"{self.base_url}/modelyear/{year}/make/{quote(make)}/model/{quote(model)}?format=json"
        )

    def _fetch(self, request: VehicleResearchRequest, url: str) -> tuple[list[dict], dict, int]:
        payload, api_requests = self.http.get_json(url)
        records: list[dict] = []
        for row in payload.get("Results", []) or payload.get("results", []):
            vehicle_id = row.get("VehicleId") or row.get("vehicleId")
            label = _optional_text(row.get("VehicleDescription") or row.get("vehicleDescription"))
            if vehicle_id is None or label is None:
                continue
            upper = label.upper()
            drivetrain = next(
                (value for value in ("AWD", "FWD", "RWD", "4WD") if value in upper),
                None,
            )
            body = "4-door" if "4 DR" in upper or "4-DR" in upper else None
            engine = "Hybrid" if "HYBRID" in upper else None
            explicit_displacement = re.search(r"(?<!\d)([1-9]\.\d)\s*L\b", upper)
            if engine is None and explicit_displacement:
                engine = f"{explicit_displacement.group(1)}L"
            records.append(
                {
                    "candidate_id": f"nhtsa-safety-rating:{vehicle_id}",
                    "label": label,
                    "generation": None,
                    "production_year_start": request.year,
                    "production_year_end": request.year,
                    "market": request.market,
                    "engine": engine,
                    "engine_code": None,
                    "transmission": None,
                    "drivetrain": drivetrain,
                    "body": body,
                    "evidence_ids": [f"nhtsa-safety-rating:{vehicle_id}"],
                    "confidence": "HIGH",
                    "evidence_status": EvidenceStatus.CONFIRMED.value,
                    "data_origin": "REAL",
                }
            )
        return records, payload, api_requests


class NHTSARecallProvider(OfficialVehicleProvider):
    id = "nhtsa_recalls"
    capability = "recalls"
    base_url = "https://api.nhtsa.gov/recalls/recallsByVehicle"

    def source_url(self, request: VehicleResearchRequest) -> str:
        make, model, year = _required_identity(request)
        query = {"make": make, "model": model, "modelYear": year}
        return f"{self.base_url}?{urlencode(query)}"

    def _fetch(self, request: VehicleResearchRequest, url: str) -> tuple[list[dict], dict, int]:
        payload, api_requests = self.http.get_json(url)
        records = [
            NHTSARecallRecord(
                campaign_number=str(row["NHTSACampaignNumber"]),
                manufacturer=str(row.get("Manufacturer") or ""),
                report_received_date=row.get("ReportReceivedDate"),
                component=str(row.get("Component") or ""),
                summary=" ".join(str(row.get("Summary") or "").split()),
                consequence=_optional_text(row.get("Consequence")),
                remedy=_optional_text(row.get("Remedy")),
                notes=_optional_text(row.get("Notes")),
                make=str(row.get("Make") or request.make).upper(),
                model=str(row.get("Model") or request.model).upper(),
                model_year=_integer(row.get("ModelYear")) or request.year,
            ).model_dump(mode="json")
            for row in payload.get("results", [])
        ]
        return records, payload, api_requests


class NHTSAComplaintProvider(OfficialVehicleProvider):
    id = "nhtsa_complaints"
    capability = "owner_complaints"
    base_url = "https://api.nhtsa.gov/complaints/complaintsByVehicle"

    def __init__(self, http: OfficialHTTPClient, *, max_records: int = 100) -> None:
        super().__init__(http)
        self.max_records = max(1, min(max_records, 500))

    def source_url(self, request: VehicleResearchRequest) -> str:
        make, model, year = _required_identity(request)
        query = {"make": make, "model": model, "modelYear": year}
        return f"{self.base_url}?{urlencode(query)}"

    def _fetch(self, request: VehicleResearchRequest, url: str) -> tuple[list[dict], dict, int]:
        payload, api_requests = self.http.get_json(url)
        records = []
        for row in payload.get("results", [])[: self.max_records]:
            records.append(
                NHTSAComplaintRecord(
                    odi_number=str(row["odiNumber"]),
                    incident_date=row.get("dateOfIncident"),
                    components=str(row.get("components") or ""),
                    normalized_summary=" ".join(str(row.get("summary") or "").split()),
                    crash=bool(row.get("crash", False)),
                    fire=bool(row.get("fire", False)),
                    injuries=_integer(row.get("numberOfInjuries")) or 0,
                    deaths=_integer(row.get("numberOfDeaths")) or 0,
                ).model_dump(mode="json")
            )
        return records, payload, api_requests


class NHTSACommunicationProvider(OfficialVehicleProvider):
    normalization_version = "2-concise-summary"
    id = "nhtsa_manufacturer_communications"
    capability = "manufacturer_communications"
    base_url = "https://static.nhtsa.gov/odi/ffdd/tsbs"

    def source_url(self, request: VehicleResearchRequest) -> str:
        del request
        return "https://www.nhtsa.gov/nhtsa-datasets-and-apis#manufacturer-communications"

    def _fetch(self, request: VehicleResearchRequest, url: str) -> tuple[list[dict], dict, int]:
        del url
        all_records: list[dict] = []
        queried_urls: list[str] = []
        archive_members: list[str] = []
        archive_bytes = 0
        api_requests = 0
        seen: set[tuple[str, str]] = set()
        for archive_url in self._archive_urls(request):
            content, request_count = self.http.get_bytes(archive_url)
            api_requests += request_count
            queried_urls.append(archive_url)
            archive_bytes += len(content)
            records, member = self._parse_archive(request, content, api_requests)
            archive_members.append(member)
            for record in records:
                key = (record["nhtsa_id"], record["document_id"])
                if key not in seen:
                    seen.add(key)
                    all_records.append(record)
        return (
            all_records,
            {
                "queried_urls": queried_urls,
                "archive_members": archive_members,
                "archive_size_bytes": archive_bytes,
                "matched_records": len(all_records),
            },
            api_requests,
        )

    def _archive_urls(self, request: VehicleResearchRequest) -> list[str]:
        first = max(1995, request.year - request.year % 5)
        current_year = datetime.now(UTC).year
        urls = []
        for start in range(first, current_year + 1, 5):
            end = min(start + 4, current_year)
            urls.append(f"{self.base_url}/MFR_COMMS_RECEIVED_{start}-{end}.zip")
        return urls

    def _parse_archive(
        self,
        request: VehicleResearchRequest,
        content: bytes,
        api_requests: int,
    ) -> tuple[list[dict], str]:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                members = [name for name in archive.namelist() if name.casefold().endswith(".csv")]
                if not members:
                    raise OfficialProviderUnavailable(
                        "manufacturer communication archive has no CSV",
                        api_requests=api_requests,
                    )
                raw = archive.read(members[0])
        except (zipfile.BadZipFile, OSError) as error:
            raise OfficialProviderUnavailable(
                "invalid manufacturer communication archive", api_requests=api_requests
            ) from error
        text = raw.decode("utf-8-sig", errors="replace")
        rows = csv.DictReader(io.StringIO(text))
        records: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for row in rows:
            make = _column(row, "Make", "MAKETXT")
            model = _column(row, "Model", "MODELTXT")
            year = _integer(_column(row, "Model Year", "YEARTXT"))
            if not (
                _same(make, request.make) and _same(model, request.model) and year == request.year
            ):
                continue
            nhtsa_id = (
                _column(row, "NHTSA ID Number", "ID")
                or _column(row, "TSB/Document ID")
                or "UNKNOWN"
            )
            document_id = _column(row, "TSB/Document ID", "BULNO") or "UNKNOWN"
            key = (nhtsa_id, document_id)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                {
                    "nhtsa_id": nhtsa_id,
                    "document_id": document_id,
                    "communication_date": _column(row, "Mfr Communication Date", "BULDTE"),
                    "communication_type": _column(row, "Communication Type"),
                    "component": _column(row, "NHTSA Components", "COMPNAME"),
                    "summary": " ".join(
                        (_column(row, "Summary", "SUMMARY", "Concise Summary") or "").split()
                    ),
                    "make": make,
                    "model": model,
                    "model_year": year,
                    "evidence_status": EvidenceStatus.CONFIRMED.value,
                    "data_origin": "REAL",
                }
            )
        return records, members[0]


def _same(left: object, right: object) -> bool:
    return _normalized(left) == _normalized(right)


def _normalized(value: object) -> str:
    return "".join(character for character in str(value or "").casefold() if character.isalnum())


def _integer(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _value(row: dict, key: str) -> str | None:
    return _optional_text(row.get(key))


def _optional_text(value: object) -> str | None:
    text = " ".join(str(value or "").split())
    return text or None


def _column(row: dict[str, str], *names: str) -> str | None:
    normalized = {_normalized(key): value for key, value in row.items()}
    for name in names:
        value = normalized.get(_normalized(name))
        if value is not None:
            return _optional_text(value)
    return None


def _required_identity(request: VehicleResearchRequest) -> tuple[str, str, int]:
    if not request.make or not request.model or not request.year:
        raise ValueError("provider requires make, model, and year")
    return request.make, request.model, request.year
