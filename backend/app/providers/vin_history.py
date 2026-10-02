"""Authorized VIN history boundary, including provider access and empty states."""

from typing import Protocol

from pydantic import Field, model_validator

from app.schemas.common import APIModel, SourceSnapshot
from app.schemas.paid_report import VehiclePhotoSet
from app.schemas.vin import VINHistoryPayload


class VINHistoryResearch(APIModel):
    vin: str
    provider_id: str
    history: VINHistoryPayload
    sources: list[SourceSnapshot] = Field(default_factory=list)
    photo_sets: list[VehiclePhotoSet] = Field(default_factory=list)

    @model_validator(mode="after")
    def real_exact_history(self):
        if (
            self.history.vin != self.vin
            or self.history.is_demo
            or self.history.data_origin != "REAL"
            or any(s.is_demo or s.data_origin != "REAL" for s in self.sources)
        ):
            raise ValueError("Real history providers cannot return demo material")
        if self.history.photos:
            raise ValueError("Real photographs must use PhotoEvidence, not legacy placeholders")
        source_ids = {s.id for s in self.sources}
        if any(p.vin != self.vin or p.source_id not in source_ids for p in self.photo_sets):
            raise ValueError("Photo sets require exact VIN and a supplied source record")
        for key in ("timeline", "auctions", "damage_details", "odometer_records"):
            for item in getattr(self.history, key):
                if item.is_demo or not item.source_ids or not set(item.source_ids) <= source_ids:
                    raise ValueError("Every real VIN event must link to supplied provenance")
        return self


class VINHistoryResearchProvider(Protocol):
    id: str

    def lookup(self, vin: str) -> VINHistoryResearch: ...


# The legacy import contract above remains readable for Stage 6.2 snapshots.
from app.schemas.research_evidence import (  # noqa: E402
    EvidenceProviderMetadata,
    VinHistoryResult,
)


class VinHistoryProvider(Protocol):
    metadata: EvidenceProviderMetadata

    def lookup(self, vin: str) -> VinHistoryResult: ...

    def photo_assets(self, result: VinHistoryResult) -> dict[str, bytes]: ...

    # Checkout-capable adapters implement these additional methods. The
    # existing research-only lookup adapters remain separate and are never
    # implicitly promoted into purchasable consumer providers.
    def validate_vin(self, vin: str) -> str: ...

    def decode_vin(self, vin: str) -> dict: ...

    def preflight(self, vin: str) -> dict: ...

    def quote(self, vin: str, product: str) -> dict: ...

    def purchase_or_fetch(self, vin: str, product: str, idempotency_key: str) -> dict: ...

    def get_report(self, provider_report_id: str) -> dict: ...

    def get_assets(self, provider_report_id: str) -> dict[str, bytes]: ...

    def normalize(self, raw_response: dict) -> dict: ...
