# ruff: noqa: E501
"""Preview publication of the US technical configurations of model years 2021-2026 (owner
decision 2026-10-03: prepare the publication and show it in the preview behind a flag, never in
production).

scripts/publish_us_config_preview.py links each configuration to the published EPA catalogue
variant it was built from (identity.epa_ids) and records the pair as a CatalogRevision in state
PREVIEW under one ImportJob in state PREVIEW. Nothing existing changes: no variant, revision,
claim or technical_evidence row is written, and a PREVIEW job can never be published through the
editorial routes (they require STAGED / APPROVED).

While enabled() the consumer routes add these rows (marked "preview") to the production rows;
production never does: enabled() is False in production whatever the setting says.
"""

from __future__ import annotations

import threading

from sqlalchemy import func, select

from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.models.knowledge_ops import CatalogRevision, ImportJob, SourceRegistry

RULE = "us-config-preview-1"
YEARS = (2021, 2026)
JOB_STATE = REVISION_STATE = "PREVIEW"

_CACHE: dict = {}
_LOCK = threading.Lock()


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.environment == "production":
        return False  # hard guard: the preview layer is never served in production
    return settings.preview_us_configurations is not False


def _revisions(db) -> list[CatalogRevision]:
    return list(db.scalars(
        select(CatalogRevision).join(ImportJob, ImportJob.id == CatalogRevision.import_job_id).where(
            ImportJob.state == JOB_STATE, CatalogRevision.state == REVISION_STATE, CatalogRevision.variant_id.is_not(None))))


def _stamp(db) -> tuple:
    from app.services.catalog_scope import POLICY_PATH

    states = []
    for table in (CatalogRevision, VehicleVariant, SourceRegistry):
        count, newest = db.execute(select(func.count(table.id), func.max(table.updated_at))).one()
        states.append((count, str(newest)))
    stat = POLICY_PATH.stat()
    return (*states, stat.st_mtime_ns, stat.st_size)


def preview_rows(db) -> list:
    """(variant, catalog) pairs of the preview layer, each catalog marked preview_only and
    carrying its configuration key; [] while the flag is off. A variant republished since the
    preview record was made (stale), one that production already shows, or one outside
    2021-2026 is left out."""
    if not enabled():
        return []
    from app.services import catalog_buyer as buyer
    from app.services.listing_intake import production_visible_us_rows

    key = str(db.get_bind().url)
    stamp = _stamp(db)
    with _LOCK:
        hit = _CACHE.get(key)
    if hit and hit[0] == stamp:
        return hit[1]
    by_variant: dict[str, list[CatalogRevision]] = {}
    for revision in _revisions(db):
        by_variant.setdefault(revision.variant_id, []).append(revision)
    rows = []
    if by_variant:
        production_ids = {v.id for v, _ in production_visible_us_rows(db)}
        candidates = buyer.active_us_rows(buyer.records(db, production_safe=False, variant_ids=set(by_variant)))
        for variant, catalog in candidates:
            revisions = [r for r in by_variant[variant.id] if (r.payload or {}).get("variant_revision_id") == variant.published_revision_id]
            if len(revisions) != 1 or variant.id in production_ids:
                continue
            if not (YEARS[0] <= int(catalog.get("model_year") or 0) <= YEARS[1]):
                continue
            rows.append((variant, {**catalog, "preview_only": True,
                                   "us_configuration_key": revisions[0].payload.get("configuration_key")}))
    with _LOCK:
        if len(_CACHE) > 4:
            _CACHE.clear()
        _CACHE[key] = (stamp, rows)
    return rows


def configuration_key(db, variant_id: str) -> str | None:
    """The configuration a preview variant was published for (one PREVIEW record only)."""
    if not enabled():
        return None
    keys = {(r.payload or {}).get("configuration_key") for r in db.scalars(
        select(CatalogRevision).join(ImportJob, ImportJob.id == CatalogRevision.import_job_id).where(
            ImportJob.state == JOB_STATE, CatalogRevision.state == REVISION_STATE, CatalogRevision.variant_id == variant_id))}
    keys.discard(None)
    return keys.pop() if len(keys) == 1 else None


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()
