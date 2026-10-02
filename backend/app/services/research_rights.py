"""Publication checks for research sources that remain internal-only."""

from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_ops import SourceRegistry
from app.services.commercial_fact_overlay import _source_has_dataset_rights
from app.services.provider_registry import ProviderRegistry

EPA_PROVIDER_SOURCES = {
    "epa_vehicle_configuration": "epa-vehicle-api",
    "epa_my_mpg": "epa-my-mpg",
}
EPA_VEHICLE_SOURCE_TYPES = frozenset(
    {"GOVERNMENT_FUEL_ECONOMY", "GOVERNMENT_FUEL_ECONOMY_DATA"}
)


def epa_provider_allowed(db: Session, provider_id: str) -> bool:
    """The EPA CSV, vehicle API, and contributed My MPG logs have separate rights."""
    if provider_id in EPA_PROVIDER_SOURCES:
        umbrella = db.get(SourceRegistry, "epa")
        if umbrella is not None and umbrella.paused:
            return False
    if get_settings().environment != "production":
        return True
    source_id = EPA_PROVIDER_SOURCES.get(provider_id)
    return source_id is None or _source_has_dataset_rights(db.get(SourceRegistry, source_id))


def permitted_research_registry(db: Session, registry: ProviderRegistry) -> ProviderRegistry:
    return ProviderRegistry(
        [p for p in registry.providers if epa_provider_allowed(db, p.definition.id)]
    )


def _epa_provider_for_source(source) -> str | None:
    if isinstance(source, dict):
        source_type = source.get("source_type")
        url = source.get("url") or source.get("source_url")
    else:
        source_type = getattr(source, "source_type", None)
        url = getattr(source, "url", None)
    host = urlparse(str(url or "")).hostname
    if source_type == "PUBLIC_OWNER_LOG" and host in {
        "fueleconomy.gov",
        "www.fueleconomy.gov",
    }:
        return "epa_my_mpg"
    if source_type in EPA_VEHICLE_SOURCE_TYPES or host in {
        "fueleconomy.gov",
        "www.fueleconomy.gov",
    }:
        return "epa_vehicle_configuration"
    return None


def source_uses_restricted_epa(db: Session, source) -> bool:
    provider_id = _epa_provider_for_source(source)
    return bool(provider_id and not epa_provider_allowed(db, provider_id))


def profile_uses_restricted_epa(db: Session, profile) -> bool:
    if profile is None:
        return False
    seed = profile.dossier_seed or {}
    depth = seed.get("knowledge_depth") or {}
    return bool(
        (
            depth.get("epa_candidates")
            and not epa_provider_allowed(db, "epa_vehicle_configuration")
        )
        or any(
            not epa_provider_allowed(db, item.get("provider_id"))
            for item in (depth.get("provenance") or {}).values()
        )
        or any(source_uses_restricted_epa(db, source) for source in profile.sources)
    )


def job_uses_restricted_epa(db: Session, job) -> bool:
    resolution = job.resolution_snapshot or {}
    return bool(
        profile_uses_restricted_epa(db, job.profile)
        or any(
            not epa_provider_allowed(db, step.get("provider_id"))
            and step.get("records_count", 0) > 0
            for step in (job.provider_steps or [])
        )
        or (
            str(resolution.get("selected_candidate_id") or "").startswith("epa:")
            and not epa_provider_allowed(db, "epa_vehicle_configuration")
        )
        or any(
            str(candidate.get("id") or "").startswith("epa:")
            and not epa_provider_allowed(db, "epa_vehicle_configuration")
            for candidate in resolution.get("candidates", [])
        )
    )


def report_uses_restricted_epa(db: Session, report) -> bool:
    evidence = report.evidence_bundle or {}
    return bool(
        (
            (evidence.get("official_consumption") is not None
             or evidence.get("official_electricity") is not None)
            and not epa_provider_allowed(db, "epa_vehicle_configuration")
        )
        or any(
            source_uses_restricted_epa(db, source)
            for source in evidence.get("sources", [])
        )
    )
