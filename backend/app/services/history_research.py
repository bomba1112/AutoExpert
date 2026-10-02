"""Run independent history providers, combine evidence and retain failures."""

import hashlib
from datetime import UTC, datetime

from app.providers.vin_history import VINHistoryResearch
from app.providers.vin_history_public import default_history_providers
from app.schemas.research_evidence import ProviderAttempt, ResearchState, VinHistoryResult
from app.schemas.vin import VINHistoryPayload
from app.services.vin_events import deduplicate_events
from app.services.vin_history_assets import attach_history, validate_photo_assets


def research_history(check, providers=None):
    providers = default_history_providers() if providers is None else providers
    results, assets = [], {}
    for provider in providers:
        try:
            result = provider.lookup(check.normalized_vin)
            if result.vin != check.normalized_vin:
                raise ValueError("VIN_MISMATCH")
            obtained = provider.photo_assets(result)
            validate_photo_assets(result.photo_sets, obtained)
            # Require real bytes and permission before a photo can reach the report.
            for group in result.photo_sets:
                for photo in group.photos:
                    if not photo.cache_permission or photo.id not in obtained:
                        raise ValueError("PHOTO_PERMISSION_OR_ASSET_MISSING")
            assets.update(obtained)
            results.append(result)
        except Exception as error:
            results.append(
                VinHistoryResult(
                    vin=check.normalized_vin,
                    attempt=ProviderAttempt(
                        provider=provider.metadata,
                        state=ResearchState.ERROR,
                        query={"vin": check.normalized_vin},
                        scope="VIN history",
                        reason=type(error).__name__,
                        provenance={"failure": str(error)[:180]},
                    ),
                )
            )
    events, aliases = deduplicate_events([e for r in results for e in r.events])
    groups = []
    seen_photos = set()
    for result in results:
        for supplied in result.photo_sets:
            group = supplied.model_copy(deep=True)
            group.event_id = aliases[group.event_id]
            group.photos = sorted(group.photos, key=lambda p: p.order)
            photos = []
            for photo in group.photos:
                photo.event_id = group.event_id
                digest = hashlib.sha256(assets[photo.id]).hexdigest()
                key = (group.event_id, digest)
                if key not in seen_photos:
                    seen_photos.add(key)
                    photos.append(photo)
            group.photos = photos
            if photos:
                groups.append(group)
    completed = [
        r
        for r in results
        if r.attempt.query_completed
        and r.attempt.state in {ResearchState.AVAILABLE, ResearchState.NO_RECORDS}
    ]
    if events:
        state = "AVAILABLE" if len(completed) == len(results) else "PARTIAL"
    elif completed:
        state = "NO_RECORDS" if len(completed) == len(results) else "PARTIAL"
    else:
        state = "PROVIDER_UNAVAILABLE"
    sources = {s.id: s for r in results for s in r.sources}
    history = VINHistoryPayload(
        vin=check.normalized_vin,
        timeline=[],
        auctions=[],
        photos=[],
        damage_details=[],
        odometer_records=[],
        is_demo=False,
        data_origin="REAL",
    )
    # Legacy import validation has no normalized event list; event-level validation
    # already happened at the new VinHistoryResult boundary above.
    attach_history(
        check,
        VINHistoryResearch(
            vin=check.normalized_vin,
            provider_id="history_router_v1",
            history=history,
            sources=list(sources.values()),
            photo_sets=groups,
        ),
        assets,
    )
    check.full_history_payload = {
        **check.full_history_payload,
        "events": [e.model_dump(mode="json") for e in events],
        "history_research": {
            "version": "6.3.0",
            "state": state,
            "researched_at": datetime.now(UTC).isoformat(),
            "coverage_complete": bool(results) and len(completed) == len(results),
            "successful_provider_count": len(completed),
            "attempts": [r.attempt.model_dump(mode="json") for r in results],
        },
    }
    check.records_count = len(events)
    check.auctions_count = sum(e.event_type == "AUCTION" for e in events)
    check.found = bool(events)
    check.has_salvage_title = any("salvage" in (e.title or "").casefold() for e in events)
    return check.full_history_payload["history_research"]
