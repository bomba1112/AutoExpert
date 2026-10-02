# ruff: noqa: E501
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_engine.engine import MarketEngine
from app.models.enums import ConfidenceLevel, EvidenceStatus, SourceUsageStatus
from app.models.evidence import LocalCostItem, MarketListing, SourceRecord
from app.models.vehicle_knowledge import VINCheck
from app.providers.database import DatabaseOwnerReviewProvider
from app.review_engine.engine import OwnerFeedbackEngine
from app.schemas.analysis import LocalCostSnapshot
from app.schemas.chat import (
    ChatContextSnapshot,
    ChatMarketAnalysisSnapshot,
    ChatOwnerFeedbackSnapshot,
    ChatVINSummary,
)
from app.schemas.common import SourceSnapshot
from app.schemas.market import MarketListingInput, MarketVehicle
from app.schemas.reviews import OwnerObservation
from app.schemas.vin import DossierClaim, DossierSection, VehicleDossier, VINHistoryPayload
from app.services.dossier import profile_dto
from app.services.paid_report import build_paid_report
from app.services.report_evidence_sections import history_status_text, tr
from app.services.vehicle_identity import identity_chat_sections

_OWNER_WORDING = {
    "ru": "Только: «упоминалось в X% изученной выборки». Это не процент автомобилей.",
    "az": "Yalnız: «araşdırılmış nümunənin X%-də qeyd olunub». Bu, avtomobillərin faizi deyil.",
    "en": "Only: ‘mentioned in X% of the reviewed sample’. This is not a vehicle failure rate.",
}


def build_chat_context_snapshot(
    db: Session,
    check: VINCheck,
    *,
    history_unlocked: bool,
) -> ChatContextSnapshot:
    if check.profile is None or not check.dossier_snapshot:
        raise ValueError("VIN check does not contain a vehicle dossier")
    dossier = VehicleDossier.model_validate(check.dossier_snapshot)
    sources = [SourceSnapshot.model_validate(item) for item in check.source_snapshot]
    known_issues = [issue for section in dossier.sections for issue in section.known_issues]
    owner_feedback = _owner_feedback(db, check, check.language)
    market_analysis = _market_analysis(db, check)
    local_costs = _local_costs(db, check)
    history = (
        VINHistoryPayload.model_validate(check.full_history_payload) if history_unlocked else None
    )
    statuses = _evidence_statuses(
        check,
        dossier,
        history,
        owner_feedback=owner_feedback,
        market_analysis=market_analysis,
        local_costs=local_costs,
    )
    if not check.is_demo and check.profile.dossier_seed.get("knowledge_depth"):
        # New conversations use the same consumer content and immutable evidence IDs.
        # Existing signed contexts remain unchanged.
        mapping = {"recalls": "recalls_tsb", "vehicle": "general_information"}
        consumer = build_paid_report(check)
        extra = check.full_history_payload
        owners = extra.get("owner_reliability", {}).get("sample", {})
        for material in owners.get("materials", []):
            for eid in material["evidence_ids"]:
                statuses[eid] = EvidenceStatus.ESTIMATE
        if history_unlocked:
            for event in extra.get("events", []):
                statuses[event["id"]] = EvidenceStatus.ESTIMATE
        by_key = {s.key: s for s in dossier.sections}
        for section in consumer.sections:
            target = by_key.get(mapping.get(section.key, section.key))
            if target is None:
                if section.key not in {"owner_reviews", "history"}:
                    continue
                if section.key == "history" and not history_unlocked:
                    continue
                target = DossierSection(key=section.key, title=section.title, summary="")
                dossier.sections.append(target)
            claims = []
            for item in [*section.paragraphs, *section.rows]:
                if not item.evidence_ids or not item.source_ids:
                    if section.key in {"history", "owner_reviews"}:
                        claims.append(
                            DossierClaim(
                                text=item.text
                                if hasattr(item, "text")
                                else f"{item.label}: {item.value}",
                                status=EvidenceStatus.INSUFFICIENT_DATA,
                            )
                        )
                    continue
                input_statuses = {statuses[e] for e in item.evidence_ids}
                weakest = next(
                    s
                    for s in (
                        EvidenceStatus.INSUFFICIENT_DATA,
                        EvidenceStatus.NEEDS_INSPECTION,
                        EvidenceStatus.ESTIMATE,
                        EvidenceStatus.CONFIRMED,
                    )
                    if s in input_statuses
                )
                claims.append(
                    DossierClaim(
                        text=item.text if hasattr(item, "text") else f"{item.label}: {item.value}",
                        status=weakest,
                        source_ids=item.source_ids,
                        evidence_ids=item.evidence_ids,
                    )
                )
            target.claims = claims
        if history_unlocked and extra.get("history_research"):
            message, caution = history_status_text(extra, check.language)
            for kind, predicate in (
                ("vin_auction", lambda e: e["event_type"] in {"AUCTION", "SALE"}),
                ("vin_mileage", lambda e: e.get("odometer") is not None),
            ):
                selected = {e["id"] for e in extra.get("events", []) if predicate(e)}
                claims = []
                for section in consumer.sections:
                    for event in section.events:
                        if event.id in selected:
                            text = (
                                event.title
                                + ". "
                                + "; ".join(
                                    f"{r.label}: {r.value}"
                                    for r in event.rows
                                    if kind != "vin_mileage"
                                    or r.key.endswith((".odometer", ".odometer_status"))
                                )
                            )
                            claims.append(
                                DossierClaim(
                                    text=text,
                                    status=EvidenceStatus.ESTIMATE,
                                    evidence_ids=[event.id],
                                    source_ids=event.source_ids,
                                )
                            )
                if not claims:
                    claims = [
                        DossierClaim(
                            text=message + " " + caution, status=EvidenceStatus.INSUFFICIENT_DATA
                        )
                    ]
                dossier.sections.append(
                    DossierSection(key=kind, title=kind, summary="", claims=claims)
                )
            photographs = [p for group in extra.get("photo_sets", []) for p in group["photos"]]
            if photographs:
                photo_sources = sorted({p["source_id"] for p in photographs})
                photo_eids = sorted({p["event_id"] for p in photographs if p.get("event_id")})
                photo_text = tr(
                    check.language,
                    f"В отчёте {len(photographs)} фотографий из источников, связанных с событиями этого VIN. Они доступны в галерее. Без отдельного подтверждения нельзя утверждать, что все снимки сделаны до ремонта, или определять по ним скрытые повреждения.",
                    f"Hesabatda bu VIN-in hadisələrinə bağlı {len(photographs)} mənbə şəkli var. Şəkillər qalereyadadır. Ayrı təsdiq olmadan hamısının təmirdən əvvəl çəkildiyini və ya gizli zədələri müəyyən etmək olmaz.",
                    f"The report contains {len(photographs)} source photographs linked to this VIN's events, available in the gallery. Without separate evidence, their pre-repair timing and hidden damage cannot be established.",
                )
                photo_claim = DossierClaim(
                    text=photo_text,
                    status=EvidenceStatus.ESTIMATE,
                    evidence_ids=photo_eids,
                    source_ids=photo_sources,
                )
            else:
                photo_claim = DossierClaim(
                    text=tr(
                        check.language,
                        "Фотографии этого VIN в отчёт не получены. Это не подтверждает отсутствие аукциона или ремонта. ",
                        "Bu VIN-in şəkilləri hesabata daxil olmayıb. Bu, hərrac və ya təmirin olmadığını təsdiqləmir. ",
                        "No photographs for this VIN were retrieved for the report. This does not establish that no auction or repair occurred. ",
                    )
                    + message,
                    status=EvidenceStatus.INSUFFICIENT_DATA,
                )
            dossier.sections.append(
                DossierSection(
                    key="vin_photos", title="vin_photos", summary="", claims=[photo_claim]
                )
            )
    if not check.is_demo:
        dossier.sections.extend(identity_chat_sections(check.profile, check.language))
    return ChatContextSnapshot(
        snapshot_id=str(uuid4()),
        vehicle_profile=profile_dto(check.profile),
        vin_summary=ChatVINSummary(
            vin=check.normalized_vin,
            found=check.found,
            records_count=check.records_count,
            photos_count=check.photos_count,
            auctions_count=check.auctions_count,
            has_salvage_title=check.has_salvage_title,
            odometer_risk=check.odometer_risk,
            history_unlocked=history_unlocked,
            is_demo=check.is_demo,
            data_origin=check.data_origin,
        ),
        unlocked_vin_history=history,
        dossier_sections=dossier.sections,
        known_issues=known_issues,
        owner_feedback=owner_feedback,
        market_analysis=market_analysis,
        local_costs=local_costs,
        sources=sources,
        evidence_statuses=statuses,
        language=check.language,
        created_at=datetime.now(UTC),
        is_demo=check.is_demo,
    )


def chat_context_digest(snapshot: ChatContextSnapshot) -> str:
    value = snapshot.model_dump(mode="json")
    if value.get("snapshot_id") is None:
        value.pop("snapshot_id", None)
    # Preserve hashes of historical contexts that predate optional source wording.
    for source in value.get("sources", []):
        if source.get("applicability_summary") is None:
            source.pop("applicability_summary", None)
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_chat_context_digest(snapshot: ChatContextSnapshot, expected: str) -> bool:
    return chat_context_digest(snapshot) == expected


def _owner_feedback(
    db: Session,
    check: VINCheck,
    language: str,
) -> ChatOwnerFeedbackSnapshot:
    observations = []
    if check.profile and check.profile.vehicle_variant_id:
        rows = DatabaseOwnerReviewProvider(db).observations_for(check.profile.vehicle_variant_id)
        observations = [
            OwnerObservation(
                id=item.id,
                material_identity_key=item.material_identity_key,
                owner_identity_key=item.owner_identity_key,
                topic=item.topic,
                component=item.component,
                sentiment=item.sentiment,
                summary=item.summary,
                source_id=item.source_id,
                mileage_km=item.mileage_km,
                observed_at=item.observed_at.isoformat() if item.observed_at else None,
                is_demo=item.is_demo,
            )
            for item in rows
            if item.source.source_type != "OWNER_SUBMISSIONS_GOVERNMENT_REPOSITORY"
        ]
    aggregation = OwnerFeedbackEngine().aggregate(observations)
    return ChatOwnerFeedbackSnapshot(
        status=(
            EvidenceStatus.ESTIMATE
            if aggregation.unique_material_count
            else EvidenceStatus.INSUFFICIENT_DATA
        ),
        aggregation=aggregation,
        wording_rule=_OWNER_WORDING.get(language, _OWNER_WORDING["en"]),
        source_ids=list(dict.fromkeys(item.source_id for item in observations if item.source_id)),
    )


def _market_analysis(db: Session, check: VINCheck) -> ChatMarketAnalysisSnapshot:
    if check.profile is None or check.profile.vehicle_variant_id is None:
        return _empty_market()
    rows = list(
        db.scalars(
            select(MarketListing)
            .join(SourceRecord, MarketListing.source_id == SourceRecord.id)
            .where(
                MarketListing.vehicle_variant_id == check.profile.vehicle_variant_id,
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
            )
        )
    )
    if not rows:
        return _empty_market()
    groups = Counter((item.country, item.currency) for item in rows)
    country, currency = sorted(groups, key=lambda key: (-groups[key], key))[0]
    candidates = [
        MarketListingInput(
            id=item.id,
            country=item.country,
            city=item.city,
            make=item.make,
            model=item.model,
            generation=item.generation,
            year=item.year,
            engine=item.engine,
            displacement_l=item.displacement_l,
            transmission=item.transmission,
            drivetrain=item.drivetrain,
            mileage_km=item.mileage_km,
            price=item.price,
            currency=item.currency,
            observed_at=item.observed_at.isoformat(),
            source_id=item.source_id,
            url=item.url,
            is_demo=item.is_demo,
        )
        for item in rows
        if item.country == country and item.currency == currency
    ]
    variant = check.profile.variant
    result = MarketEngine().analyze(
        MarketVehicle(
            country=country,
            make=check.profile.make,
            model=check.profile.model,
            generation=check.profile.generation,
            year=check.profile.year,
            engine=check.profile.engine,
            displacement_l=variant.displacement_l if variant else None,
            transmission=check.profile.transmission,
            drivetrain=check.profile.drivetrain,
            currency=currency,
        ),
        candidates,
    )
    return ChatMarketAnalysisSnapshot(
        status=result.status,
        confidence=result.confidence,
        sample_count=result.sample_count,
        comparable_count=result.comparable_count,
        median=result.median,
        market_range_low=result.market_range_low,
        market_range_high=result.market_range_high,
        currency=result.currency,
        assumptions=result.assumptions,
        source_ids=list(dict.fromkeys(item.source_id for item in candidates if item.source_id)),
    )


def _empty_market() -> ChatMarketAnalysisSnapshot:
    return ChatMarketAnalysisSnapshot(
        status=EvidenceStatus.INSUFFICIENT_DATA,
        confidence=ConfidenceLevel.LOW,
        assumptions=["No comparable local-market sample is linked to this vehicle profile."],
    )


def _local_costs(db: Session, check: VINCheck) -> list[LocalCostSnapshot]:
    if check.profile is None or check.profile.vehicle_variant_id is None:
        return []
    rows = list(
        db.scalars(
            select(LocalCostItem)
            .join(SourceRecord, LocalCostItem.source_id == SourceRecord.id)
            .where(
                LocalCostItem.vehicle_variant_id == check.profile.vehicle_variant_id,
                SourceRecord.usage_status == SourceUsageStatus.ACTIVE,
            )
        )
    )
    return [
        LocalCostSnapshot(
            id=item.id,
            category=item.category,
            operation=item.operation,
            applicability=item.applicability,
            part_price_low=item.part_price_low,
            part_price_high=item.part_price_high,
            labor_price_low=item.labor_price_low,
            labor_price_high=item.labor_price_high,
            currency=item.currency,
            source_id=item.source_id,
            updated_at=item.updated_at_source.isoformat(),
            is_demo=item.is_demo,
        )
        for item in rows
    ]


def _evidence_statuses(
    check: VINCheck,
    dossier: VehicleDossier,
    history: VINHistoryPayload | None,
    *,
    owner_feedback: ChatOwnerFeedbackSnapshot,
    market_analysis: ChatMarketAnalysisSnapshot,
    local_costs: list[LocalCostSnapshot],
) -> dict[str, EvidenceStatus]:
    statuses = {
        item.id: item.status
        for item in (check.profile.evidence if check.profile is not None else [])
    }
    for section in dossier.sections:
        for claim in section.claims:
            for evidence_id in claim.evidence_ids:
                statuses.setdefault(evidence_id, claim.status)
        for issue in section.known_issues:
            for evidence_id in issue.evidence_ids:
                statuses.setdefault(evidence_id, issue.status)
    statuses["vin_summary.salvage"] = EvidenceStatus.ESTIMATE
    statuses["vin_summary.odometer_risk"] = EvidenceStatus.ESTIMATE
    statuses["market_analysis"] = market_analysis.status
    statuses["owner_feedback"] = owner_feedback.status
    for item in local_costs:
        statuses[f"local_cost.{item.id}"] = EvidenceStatus.ESTIMATE
    if history is not None:
        for collection_name in (
            "timeline",
            "auctions",
            "photos",
            "damage_details",
            "odometer_records",
        ):
            for index, item in enumerate(getattr(history, collection_name)):
                statuses[f"vin_history.{collection_name}.{index}"] = item.status
    return statuses
