"""Public published knowledge and authenticated editorial operations."""

# ruff: noqa: E501
from __future__ import annotations

import io
import json
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import Field
from sqlalchemy import select

from app.api.dependencies import AdminUser, CurrentUser, DBSession
from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.models.evidence import TechnicalEvidence
from app.models.knowledge_ops import (
    CatalogRevision,
    EditorialPublication,
    ImportJob,
    MarketDiscoveryRevision,
    OwnershipEvidenceRevision,
    PublicationFavorite,
    SourceRegistry,
    VehicleAsset,
)
from app.schemas.knowledge import (
    BuyerFilters,
    CatalogRecord,
    CostScenario,
    ImportManifest,
    StrictModel,
)
from app.schemas.paid_report import PaidReportSection, ReportParagraph, ReportRow
from app.schemas.research import ResearchJobCreate
from app.schemas.verified_ownership import OperationHistory, OwnershipScenario
from app.services import catalog_buyer as buyer
from app.services.knowledge_import import (
    apply_revision,
    audit,
    checksum,
    enqueue,
    private_path,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from app.services.knowledge_import import (
    revision_model as import_revision_model,
)
from app.services.knowledge_registry import registry_view, require_source, utcnow
from app.services.listing_intake import production_visible_us_rows

router = APIRouter(prefix="/knowledge", tags=["published-knowledge"])


@router.post("/research")
def queue_research(value: ResearchJobCreate, db: DBSession, user: CurrentUser):
    from app.services.catalog_research import enqueue_research

    job = guard(enqueue_research, db, user, value)
    return {"id": job.id, "state": job.status, "publication": "STAGING"}


class ReviewInput(StrictModel):
    action: Literal["approve", "reject", "publish", "cancel", "retry", "rollback", "lock", "unlock"]
    note: str = Field(min_length=10, max_length=2000)


@router.get("/research/{job_id}")
def research_status(job_id: str, db: DBSession, user: CurrentUser):
    from app.models.research import ResearchJob

    job = db.get(ResearchJob, job_id)
    if not job or job.user_id != user.id or job.worker_queue != "CATALOG_REVIEW":
        raise HTTPException(404, "JOB_NOT_FOUND")
    return {
        "id": job.id,
        "state": job.status,
        "attempts": job.worker_attempts,
        "cancel_requested": job.cancel_requested,
        "errors": job.errors,
        "calls": job.metrics.get("network_calls", 0),
        "publication": job.metrics.get("publication", "STAGING"),
    }


@router.post("/research/{job_id}/control")
def research_control(job_id: str, value: ReviewInput, db: DBSession, user: CurrentUser):
    from app.models.enums import ResearchJobStatus
    from app.models.research import ResearchJob

    job = db.get(ResearchJob, job_id)
    if not job or job.user_id != user.id or job.worker_queue != "CATALOG_REVIEW":
        raise HTTPException(404, "JOB_NOT_FOUND")
    if value.action == "cancel" and job.status in {
        ResearchJobStatus.QUEUED,
        ResearchJobStatus.RUNNING,
    }:
        job.cancel_requested = True
        if job.status == ResearchJobStatus.QUEUED:
            job.status = ResearchJobStatus.FAILED
            job.errors = ["CANCELLED"]
    elif (
        value.action == "retry"
        and job.status == ResearchJobStatus.FAILED
        and job.worker_attempts < 2
    ):
        if not get_settings().knowledge_worker_enabled:
            raise HTTPException(409, "RESEARCH_WORKER_NOT_CONFIGURED")
        job.cancel_requested = False
        job.worker_lease_until = None
        job.status = ResearchJobStatus.QUEUED
        job.errors = []
    else:
        raise HTTPException(409, "JOB_ACTION_UNAVAILABLE")
    db.commit()
    return {"id": job.id, "state": job.status, "cancel_requested": job.cancel_requested}


class ResolverInput(StrictModel):
    # The public product is USA MY2012+; the legacy scope identifier remains
    # available so internal historical rows and strict verification are intact.
    catalog_scope: Literal["ALL", "US_BASE_2000", "US_CONFIRMED_2000"] = "US_BASE_2000"
    language: Literal["ru", "az"] = "ru"
    catalog_ready_only: bool = False
    generation: str | None = Field(default=None, max_length=100)
    make: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    year: int | None = Field(default=None, ge=1886, le=2100)
    market: str | None = Field(default=None, max_length=24)
    engine: str | None = Field(default=None, max_length=60)
    transmission: str | None = Field(default=None, max_length=60)
    drivetrain: str | None = Field(default=None, max_length=60)
    trim: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=60)
    seats: int | None = Field(default=None, ge=1, le=30)


class SaveInput(StrictModel):
    language: Literal["ru", "az"] = "ru"
    preferences: BuyerFilters = Field(default_factory=BuyerFilters)


class ConsumerBuyerFilters(BuyerFilters):
    catalog_scope: Literal["ALL", "US_BASE_2000", "US_CONFIRMED_2000"] = "US_BASE_2000"
    year_min: int | None = Field(default=2012, ge=1886, le=2100)


class ComparisonInput(StrictModel):
    variant_ids: list[str] = Field(min_length=2, max_length=3)
    scenarios: list[CostScenario] = Field(default_factory=list, max_length=3)
    language: Literal["ru", "az"] = "ru"


def guard(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None


def published(db, variant_id, *, production_safe=True):
    rows = production_visible_us_rows(db) if production_safe else buyer.records(db)
    row = next(((v, c) for v, c in rows if v.id == variant_id), None)
    if row is None:
        raise HTTPException(404, "CATALOG_VERSION_UNAVAILABLE")
    return row


@router.get("/facets")
def get_facets(
    db: DBSession,
    catalog_scope: Literal["ALL", "US_BASE_2000", "US_CONFIRMED_2000"] = "US_BASE_2000",
):
    return buyer.facets(db, catalog_scope, rows=production_visible_us_rows(db))


@router.post("/search")
def search(value: ConsumerBuyerFilters, db: DBSession, language: Literal["ru", "az"] = "ru"):
    return buyer.search(db, value, language, rows=production_visible_us_rows(db))


@router.post("/resolve")
def resolve(value: ResolverInput, db: DBSession):
    return buyer.resolve(db, value.model_dump(), rows=production_visible_us_rows(db))


@router.get("/vehicles/{variant_id}")
def vehicle(variant_id: str, db: DBSession, language: Literal["ru", "az"] = "ru"):
    v, c = published(db, variant_id, production_safe=True)
    return {
        **buyer.card(db, v, c, language),
        "projection": buyer.projection(c, language).model_dump(mode="json"),
        "profile": buyer.vehicle_profile(c, language),
        "source_url": c["source_url"],
        "source_date": c.get("source_date"),
        "published_at": c["published_at"],
        "llm_mode": "FACTUAL_TEMPLATE",
        "research_available": get_settings().knowledge_worker_enabled,
    }


@router.post("/vehicles/{variant_id}/save")
def save(variant_id: str, value: SaveInput, db: DBSession, user: CurrentUser):
    v, c = published(db, variant_id)
    report = buyer.save_dossier(
        db, user, v, c, value.language, value.preferences.model_dump(mode="json")
    )
    return {"id": report.id, "saved": True}


@router.get("/ownership/evidence")
def ownership_evidence(db: DBSession, variant_id: str | None = None):
    from app.services.ownership_evidence import available, view

    if variant_id:
        published(db, variant_id)
    return [view(r) for r in available(db, variant_id=variant_id, production_safe=True)]


class OwnershipMember(StrictModel):
    variant_id: str
    current_odometer_km: int = Field(ge=0, le=5000000)
    fuel_energy: Literal["AI92", "AI95", "AI98", "DIESEL"] | None = None
    history: list[OperationHistory] = Field(default_factory=list, max_length=100)
    first_registration: date | None = None


class OwnershipCompare(StrictModel):
    scenario: OwnershipScenario
    members: list[OwnershipMember] = Field(min_length=2, max_length=3)


@router.post("/ownership/compare")
def ownership_comparison(value: OwnershipCompare, db: DBSession):
    from app.pricing.ownership import OwnershipCostEngine

    if len({m.variant_id for m in value.members}) != len(value.members):
        raise HTTPException(409, "DISTINCT_VERSIONS_REQUIRED")
    if value.scenario.history or value.scenario.first_registration:
        raise HTTPException(422, "HISTORY_MUST_BE_PER_VEHICLE")
    results = []
    cycles = set()
    for member in value.members:
        v, c = published(db, member.variant_id)
        scenario = guard(
            OwnershipScenario.model_validate,
            {
                **value.scenario.model_dump(mode="json"),
                "current_odometer_km": member.current_odometer_km,
                "fuel_energy": member.fuel_energy,
                "history": member.history,
                "first_registration": member.first_registration,
            },
        )
        cycles.add(c["facts"].get("source_cycle", {}).get("value") or c.get("source_registry_id"))
        results.append(
            {
                "variant_id": v.id,
                "title": c["make"] + " " + c["model"],
                "calculation": OwnershipCostEngine().calculate_verified(
                    db, v, c, scenario, production_safe=True
                ),
            }
        )
    return {
        "members": results,
        "shared_scenario": value.scenario.model_dump(mode="json"),
        "coverage_comparable": all(r["calculation"]["status"] == "COMPLETE" for r in results),
        "different_test_cycles": len(cycles) > 1,
        "winner": None,
    }


@router.post("/vehicles/{variant_id}/ownership")
def ownership_calculation(variant_id: str, value: OwnershipScenario, db: DBSession):
    from app.pricing.ownership import OwnershipCostEngine

    variant, catalog = published(db, variant_id)
    return guard(
        OwnershipCostEngine().calculate_verified,
        db, variant, catalog, value, production_safe=True,
    )


class OwnershipSaveInput(StrictModel):
    language: Literal["ru", "az"] = "ru"
    scenario: OwnershipScenario
    expected_scenario_id: str = Field(min_length=64, max_length=64)


@router.post("/vehicles/{variant_id}/ownership/save")
def save_ownership(variant_id: str, value: OwnershipSaveInput, db: DBSession, user: CurrentUser):
    from app.pricing.ownership import OwnershipCostEngine

    variant, catalog = published(db, variant_id)
    snapshot = guard(
        OwnershipCostEngine().calculate_verified,
        db, variant, catalog, value.scenario, production_safe=True,
    )
    if snapshot["scenario_id"] != value.expected_scenario_id:
        raise HTTPException(409, "EVIDENCE_CHANGED_RECALCULATE")
    report = buyer.save_dossier(db, user, variant, catalog, value.language, {}, ownership=snapshot)
    return {"id": report.id, "saved": True, "scenario_id": snapshot["scenario_id"]}


@router.post("/compare")
def compare(value: ComparisonInput, db: DBSession):
    if len(set(value.variant_ids)) != len(value.variant_ids):
        raise HTTPException(422, "DISTINCT_VEHICLES_REQUIRED")
    if value.scenarios and len(value.scenarios) != len(value.variant_ids):
        raise HTTPException(422, "ONE_SCENARIO_PER_VEHICLE")
    rows = [published(db, rid) for rid in value.variant_ids]
    scenarios = value.scenarios or [CostScenario() for _ in rows]
    members = [
        {**buyer.card(db, v, c, value.language), "costs": buyer.costs(c, s)}
        for (v, c), s in zip(rows, scenarios, strict=True)
    ]
    keys = sorted({k for _, c in rows for k in c["facts"]})
    differences = [k for k in keys if len({str(buyer.fact_value(c, k)) for _, c in rows}) > 1]
    return {
        "version": "catalog-compare-1.0",
        "members": members,
        "differences": differences,
        "winner": None,
        "verdict": buyer.comparison_conclusion(value.language),
        "same_cycle_required": True,
    }


@router.post("/compare/save")
def save_comparison(value: ComparisonInput, db: DBSession, user: CurrentUser):
    from app.services.buyer_experience import comparison_projection, persist_report

    result = compare(value, db)
    members = [
        buyer.save_dossier(db, user, *published(db, rid), value.language, {})
        for rid in value.variant_ids
    ]
    projections = {}
    for lang in ("az", "ru", "en"):
        projection = comparison_projection(members, lang, {})
        verdict = next(s for s in projection.sections if s.key == "expert_verdict")
        cost_section = PaidReportSection(
            key="ownership_cost",
            title=buyer.tr(lang, "Расходы по вашему сценарию", "Ssenariniz üzrə xərclər"),
        )
        for item in result["members"]:
            cost = item["costs"]
            cost_section.rows.append(
                ReportRow(
                    key=item["id"],
                    label=item["make"] + " " + item["model"],
                    value=(cost["total"] + " AZN")
                    if cost["total"]
                    else buyer.tr(
                        lang,
                        "Полная стоимость неизвестна; известная часть: ",
                        "Tam xərc məlum deyil; məlum hissə: ",
                    )
                    + (cost["known_subtotal"] or "—")
                    + " AZN",
                )
            )
            for key, ru, az in [
                ("depreciation", "Потеря стоимости", "Dəyər itkisi"),
                ("energy", "Энергия", "Enerji"),
                ("maintenance", "Обслуживание", "Texniki xidmət"),
                ("repair_reserve", "Резерв ремонта", "Təmir ehtiyatı"),
                ("other", "Прочее", "Digər"),
            ]:
                amount = cost["components"][key]
                cost_section.rows.append(
                    ReportRow(
                        key=item["id"] + "_" + key,
                        label=item["model"] + " · " + buyer.tr(lang, ru, az),
                        value=amount + " AZN" if amount is not None else "—",
                    )
                )
            cost_section.rows.append(
                ReportRow(
                    key=item["id"] + "_purchase",
                    label=item["model"] + " · " + buyer.tr(lang, "Покупка отдельно", "Alış ayrıca"),
                    value=(cost["purchase_separate"] + " AZN")
                    if cost["purchase_separate"]
                    else "—",
                )
            )
            assumptions = cost["assumptions"]
            cost_section.paragraphs.append(
                ReportParagraph(
                    text=item["make"]
                    + " "
                    + item["model"]
                    + " · "
                    + str(cost["months"])
                    + buyer.tr(lang, " мес.", " ay")
                    + " · "
                    + cost["distance_km"]
                    + " km · "
                    + assumptions["region"]
                    + " · "
                    + str(assumptions.get("price_date") or "—")
                    + " · "
                    + str(
                        assumptions.get("price_source")
                        or buyer.tr(lang, "Источник цены не задан", "Qiymət mənbəyi verilməyib")
                    )
                )
            )
        cost_section.paragraphs.append(
            ReportParagraph(
                text=buyer.tr(
                    lang,
                    "Покупка показана отдельно. Стоимость владения включает потерю стоимости, энергию, обслуживание, резерв ремонта и заданные прочие расходы. Цены и перепродажа — допущения пользователя; неизвестное не считается нулём.",
                    "Alış ayrıca göstərilir. İstifadə xərci dəyər itkisi, enerji, xidmət, təmir ehtiyatı və daxil edilmiş digər xərclərdən ibarətdir. Qiymətlər və təkrar satış istifadəçinin fərziyyələridir; naməlum sıfır sayılmır.",
                )
            )
        )
        projection.sections = [
            verdict,
            cost_section,
            *[s for s in projection.sections if s is not verdict],
        ]
        projections[lang] = projection.model_dump(mode="json")
    sources = {s["id"]: s for m in members for s in m.evidence_bundle["sources"]}
    report = persist_report(
        db,
        user.id,
        value.language,
        {
            "kind": "COMPARISON",
            "member_ids": [m.id for m in members],
            "variant_ids": value.variant_ids,
            "scenarios": [s.model_dump(mode="json") for s in value.scenarios],
            "preferences": {},
        },
        projections,
        {
            "sources": list(sources.values()),
            "ownership_costs": [m["costs"] for m in result["members"]],
        },
    )
    return {"id": report.id, "saved": True}


@router.get("/publications")
def publications(db: DBSession, language: Literal["ru", "az"] = "ru", topic: str | None = None):
    # Legacy editorial prose and claims lack per-claim commercial rights review.
    # Keep authored publications in admin storage, hidden from every consumer
    # environment until their content (not just variant IDs) has been cleared.
    return []


@router.get("/favorites")
def favorites(db: DBSession, user: CurrentUser):
    return list(
        db.scalars(
            select(PublicationFavorite.publication_id).where(PublicationFavorite.user_id == user.id)
        )
    )


@router.put("/favorites/{publication_id}")
def favorite(publication_id: str, db: DBSession, user: CurrentUser):
    if not db.get(EditorialPublication, publication_id):
        raise HTTPException(404, "PUBLICATION_NOT_FOUND")
    existing = db.scalar(
        select(PublicationFavorite).where(
            PublicationFavorite.user_id == user.id,
            PublicationFavorite.publication_id == publication_id,
        )
    )
    if not existing:
        db.add(PublicationFavorite(user_id=user.id, publication_id=publication_id))
        db.commit()
    return {"saved": True}


@router.delete("/favorites/{publication_id}")
def unfavorite(publication_id: str, db: DBSession, user: CurrentUser):
    existing = db.scalar(
        select(PublicationFavorite).where(
            PublicationFavorite.user_id == user.id,
            PublicationFavorite.publication_id == publication_id,
        )
    )
    if existing:
        db.delete(existing)
        db.commit()
    return {"saved": False}


@router.get("/assets/{asset_id}/{rendition}")
def asset(asset_id: str, rendition: Literal["card", "hero"], db: DBSession):
    item = db.get(VehicleAsset, asset_id)
    if not item or item.state != "APPROVED" or not item.rights.get("commercial_reuse"):
        raise HTTPException(404, "ASSET_UNAVAILABLE")
    key = item.renditions.get(rendition)
    if not key or not private_path(key).is_file():
        raise HTTPException(404, "ASSET_UNAVAILABLE")
    return FileResponse(
        private_path(key),
        media_type="image/webp",
        headers={
            "Cache-Control": "public, max-age=86400",
            "ETag": f'"{item.sha256}-{item.version}-{rendition}"',
        },
    )


@router.get("/admin")
def dashboard(db: DBSession, user: AdminUser):
    return {
        "sources": registry_view(db),
        "coverage": buyer.coverage(db),
        "worker_enabled": get_settings().knowledge_worker_enabled,
        "concept_products": get_settings().concept_products,
        "jobs": [
            {
                "id": j.id,
                "source_id": j.source_id,
                "state": j.state,
                "cursor": j.cursor,
                "metrics": j.metrics,
                "errors": j.errors,
                "created_at": j.created_at,
            }
            for j in db.scalars(select(ImportJob).order_by(ImportJob.created_at.desc()).limit(50))
        ],
        "assets": [
            {"id": a.id, "state": a.state, "applicability": a.applicability, "rights": a.rights}
            for a in db.scalars(select(VehicleAsset))
        ],
    }


@router.post("/admin/imports")
def import_manifest(value: ImportManifest, db: DBSession, user: AdminUser):
    job = guard(enqueue, db, value)
    return {
        "id": job.id,
        "state": job.state,
        "worker_enabled": get_settings().knowledge_worker_enabled,
    }


@router.get("/admin/ownership/contracts")
def ownership_contracts(user: AdminUser):
    from app.schemas.verified_ownership import DATA_TYPES, OwnershipRecord

    return {
        "csv_header": ",".join(OwnershipRecord.model_fields) + "\n",
        "record_schema": OwnershipRecord.model_json_schema(),
        "data_schemas": {kind: model.model_json_schema() for kind, model in DATA_TYPES.items()},
        "workflow": "Upload permitted CSV/JSON as document; enqueue ownership-csv-v1 or ownership-json-v1; process, inspect, review, publish. Never include accounts or credentials.",
    }


@router.get("/admin/imports/{job_id}")
def import_detail(job_id: str, db: DBSession, user: AdminUser):
    job = db.get(ImportJob, job_id)
    if not job:
        raise HTTPException(404, "JOB_NOT_FOUND")
    revision_model = import_revision_model(job)
    return {
        "id": job.id,
        "state": job.state,
        "manifest": job.manifest,
        "errors": job.errors,
        "metrics": job.metrics,
        "revisions": [
            {
                "id": r.id,
                "state": r.state,
                "payload": r.payload,
                "checksum": r.checksum,
                "changes": market_revision_changes(db, r)
                if revision_model is MarketDiscoveryRevision
                else ownership_revision_changes(db, r)
                if revision_model is OwnershipEvidenceRevision
                else revision_changes(db, job, r),
            }
            for r in db.scalars(
                select(revision_model).where(revision_model.import_job_id == job.id)
            )
        ],
    }


def ownership_revision_changes(db, revision):
    previous = db.scalar(
        select(OwnershipEvidenceRevision).where(
            OwnershipEvidenceRevision.active_key == revision.source_id + ":" + revision.external_key
        )
    )
    return {"before": previous.payload if previous else None, "after": revision.payload}


def market_revision_changes(db, revision):
    previous = db.scalar(
        select(MarketDiscoveryRevision).where(
            MarketDiscoveryRevision.active_key == revision.source_id + ":" + revision.external_key
        )
    )
    return {
        "before": previous.payload if previous else None,
        "after": revision.payload,
        "scope": "MARKET_DISCOVERY_ONLY_NOT_FACTORY_IDENTITY",
    }


@router.get("/admin/market-discovery/contracts")
def market_discovery_contracts(user: AdminUser):
    from app.schemas.market_discovery import MarketDiscoveryRecord

    return {
        "record_schema": MarketDiscoveryRecord.model_json_schema(),
        "csv_header": ",".join(MarketDiscoveryRecord.model_fields) + "\n",
        "workflow": "Permitted minimal export -> existing ImportJob -> review -> discovery publication. No accounts, contact details, photos or seller technical facts.",
    }


@router.get("/admin/market-discovery/queue")
def market_discovery_queue(db: DBSession, user: AdminUser):
    from app.services.market_priority import current_queue

    return current_queue(db)


def revision_changes(db, job, revision):
    variant = db.scalar(
        select(VehicleVariant).where(
            VehicleVariant.catalog_key == job.source_id + ":" + revision.external_key
        )
    )
    old = db.get(CatalogRevision, variant.published_revision_id) if variant else None
    before = old.payload if old else {}
    result = {
        key: {"before": before.get(key), "after": value}
        for key, value in revision.payload.items()
        if key != "facts" and value != before.get(key)
    }
    old_facts, new_facts = before.get("facts", {}), revision.payload.get("facts", {})
    result["facts"] = {
        key: {"before": old_facts.get(key), "after": new_facts.get(key)}
        for key in sorted(set(old_facts) | set(new_facts))
        if old_facts.get(key) != new_facts.get(key)
    }
    return result


@router.get("/admin/variants/{variant_id}")
def editorial_variant(variant_id: str, db: DBSession, user: AdminUser):
    variant = db.get(VehicleVariant, variant_id)
    if not variant or not variant.published_revision_id:
        raise HTTPException(404, "VARIANT_NOT_FOUND")
    revision = db.get(CatalogRevision, variant.published_revision_id)
    return {
        "id": variant.id,
        "locked": variant.editorial_locked,
        "revision_id": revision.id,
        "record": revision.payload,
        "previous_revision_id": revision.previous_revision_id,
    }


@router.post("/admin/variants/{variant_id}/draft")
def draft_variant(variant_id: str, value: CatalogRecord, db: DBSession, user: AdminUser):
    variant = db.get(VehicleVariant, variant_id)
    if not variant or not variant.published_revision_id:
        raise HTTPException(404, "VARIANT_NOT_FOUND")
    revision = db.get(CatalogRevision, variant.published_revision_id)
    if value.external_key != revision.external_key:
        raise HTTPException(409, "EXTERNAL_ID_IMMUTABLE")
    if len(value.revision_note) < 10:
        raise HTTPException(422, "EDITORIAL_NOTE_REQUIRED")
    source_id = db.get(ImportJob, revision.import_job_id).source_id
    manifest = ImportManifest(
        source_id=source_id,
        parser="manifest-json-v1",
        records=[value],
        selection_basis="Editorial correction: " + value.revision_note,
    )
    job = guard(enqueue, db, manifest)
    if job.state == "QUEUED":
        guard(process_job, db, job.id)
    audit(
        db,
        user,
        "VARIANT",
        variant.id,
        "DRAFT",
        value.revision_note,
        before={"revision_id": revision.id},
        after={"job_id": job.id},
    )
    db.commit()
    return {"job_id": job.id, "state": job.state, "published": False}


@router.post("/admin/imports/{job_id}/review")
def import_review(job_id: str, value: ReviewInput, db: DBSession, user: AdminUser):
    job = db.get(ImportJob, job_id)
    if not job:
        raise HTTPException(404, "JOB_NOT_FOUND")
    if value.action in {"approve", "reject"}:
        guard(review_job, db, job, user, note=value.note, approve=value.action == "approve")
    elif value.action == "publish":
        guard(publish_job, db, job, user, note=value.note)
    elif value.action == "cancel":
        if job.state not in {"QUEUED", "RUNNING", "FAILED"}:
            raise HTTPException(409, "JOB_NOT_CANCELLABLE")
        job.cancel_requested = True
        if job.state != "RUNNING":
            job.state = "CANCELLED"
        audit(db, user, "IMPORT", job.id, "CANCEL_REQUESTED", value.note)
        db.commit()
    elif value.action == "retry":
        if job.state not in {"FAILED", "CANCELLED"}:
            raise HTTPException(409, "JOB_NOT_RETRYABLE")
        job.state, job.cancel_requested, job.lease_until = "QUEUED", False, None
        job.errors = []
        audit(db, user, "IMPORT", job.id, "RETRY", value.note)
        db.commit()
    else:
        raise HTTPException(422, "INVALID_JOB_ACTION")
    return {"id": job.id, "state": job.state}


class SourcePatch(StrictModel):
    paused: bool
    note: str = Field(min_length=10, max_length=2000)
    rights_reference: str | None = Field(default=None, max_length=2000)
    commercial_reuse: bool | None = None


@router.patch("/admin/sources/{source_id}")
def patch_source(source_id: str, value: SourcePatch, db: DBSession, user: AdminUser):
    source = db.get(SourceRegistry, source_id)
    if not source:
        raise HTTPException(404, "SOURCE_NOT_FOUND")
    before = {"paused": source.paused, "config": source.config, "state": source.state}
    if value.commercial_reuse is not None:
        if not value.rights_reference or len(value.rights_reference) < 10:
            raise HTTPException(422, "RIGHTS_REFERENCE_REQUIRED")
        source.config = {
            **source.config,
            "commercial_reuse": value.commercial_reuse,
            "rights_reference": value.rights_reference,
            "rights_reviewer": user.id,
            "rights_reviewed_at": utcnow().isoformat(),
        }
        source.state = "APPROVED" if value.commercial_reuse else "NEEDS_PERMISSION"
    source.paused = value.paused
    audit(
        db,
        user,
        "SOURCE",
        source.id,
        "UPDATED",
        value.note,
        before=before,
        after={"paused": source.paused, "config": source.config, "state": source.state},
    )
    db.commit()
    return {"id": source.id, "state": source.state, "paused": source.paused}


@router.post("/admin/documents/{source_id}")
async def upload_document(source_id: str, request: Request, db: DBSession, user: AdminUser):
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > get_settings().knowledge_import_max_bytes:
            raise HTTPException(413, "DOCUMENT_TOO_LARGE")
    doc = guard(
        store_document,
        db,
        source_id,
        bytes(content),
        media_type=request.headers.get("content-type", "application/octet-stream")[:80],
    )
    audit(db, user, "DOCUMENT", doc.id, "UPLOADED", "Protected manual source document upload")
    db.commit()
    return {"id": doc.id, "sha256": doc.sha256, "size": doc.byte_size}


@router.post("/admin/variants/{variant_id}/review")
def variant_review(variant_id: str, value: ReviewInput, db: DBSession, user: AdminUser):
    variant = db.get(VehicleVariant, variant_id)
    if not variant or not variant.published_revision_id:
        raise HTTPException(404, "VARIANT_NOT_FOUND")
    if value.action in {"lock", "unlock"}:
        variant.editorial_locked = value.action == "lock"
    elif value.action == "rollback":
        current = db.get(CatalogRevision, variant.published_revision_id)
        prior = (
            db.get(CatalogRevision, current.previous_revision_id)
            if current.previous_revision_id
            else None
        )
        if not prior:
            raise HTTPException(409, "NO_PREVIOUS_REVISION")
        source = guard(require_source, db, db.get(ImportJob, prior.import_job_id).source_id)
        old_previous = prior.previous_revision_id
        guard(apply_revision, db, prior, source)
        prior.previous_revision_id = old_previous
        current.state = "ROLLED_BACK"
    else:
        raise HTTPException(422, "INVALID_VARIANT_ACTION")
    audit(db, user, "VARIANT", variant.id, value.action.upper(), value.note)
    db.commit()
    return {
        "id": variant.id,
        "revision_id": variant.published_revision_id,
        "locked": variant.editorial_locked,
    }


class AssetMetadata(StrictModel):
    variant_ids: list[str] = Field(min_length=1, max_length=100)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    source_url: str = Field(max_length=2000)
    rights_reference: str = Field(min_length=10, max_length=2000)
    generated: bool = False
    commercial_reuse: bool = False
    generation: str = Field(min_length=1, max_length=100)
    facelift: str | None = Field(default=None, max_length=80)
    body: str = Field(min_length=1, max_length=60)
    market: str = Field(min_length=2, max_length=24)
    year_from: int = Field(ge=1886, le=2100)
    year_to: int = Field(ge=1886, le=2100)


@router.post("/admin/assets")
async def upload_asset(request: Request, db: DBSession, user: AdminUser):
    from PIL import Image, ImageOps, UnidentifiedImageError

    # Metadata is a JSON query parameter; body is bounded binary, never a fetched arbitrary URL.
    try:
        meta = AssetMetadata.model_validate_json(request.query_params.get("metadata", "{}"))
    except ValueError:
        raise HTTPException(422, "INVALID_ASSET_METADATA") from None
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "IMAGE_TOO_LARGE")
    digest = checksum(bytes(content))
    existing = db.scalar(select(VehicleAsset).where(VehicleAsset.sha256 == digest))
    if existing:
        return {"id": existing.id, "state": existing.state}
    try:
        with Image.open(io.BytesIO(content)) as opened:
            if (
                opened.format not in {"JPEG", "PNG", "WEBP"}
                or opened.width * opened.height > 24000000
                or getattr(opened, "n_frames", 1) != 1
            ):
                raise ValueError("UNSUPPORTED_IMAGE")
            opened.verify()
        with Image.open(io.BytesIO(content)) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            if min(image.size) < 200:
                raise ValueError("IMAGE_TOO_SMALL")
    except (ValueError, UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(422, "INVALID_IMAGE") from None
    original = f"assets/{digest}/original"
    path = private_path(original)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    renditions = {}
    for name, size in [("card", (640, 420)), ("hero", (1280, 840))]:
        output = image.copy()
        output.thumbnail(size)
        key = f"assets/{digest}/{name}.webp"
        output.save(private_path(key), "WEBP", quality=82)
        renditions[name] = key
    asset = VehicleAsset(
        sha256=digest,
        original_key=original,
        applicability=meta.model_dump(
            exclude={"source_url", "rights_reference", "generated", "commercial_reuse"}
        ),
        rights={"reference": meta.rights_reference, "commercial_reuse": meta.commercial_reuse},
        provenance={
            "source_url": meta.source_url,
            "generated": meta.generated,
            "retrieved_at": utcnow().isoformat(),
            "width": image.width,
            "height": image.height,
            "byte_size": len(content),
        },
        renditions=renditions,
    )
    db.add(asset)
    db.flush()
    audit(
        db,
        user,
        "ASSET",
        asset.id,
        "IMAGE_QA",
        "Uploaded image requires applicability and rights review",
    )
    db.commit()
    return {"id": asset.id, "state": asset.state}


@router.post("/admin/assets/{asset_id}/review")
def asset_review(asset_id: str, value: ReviewInput, db: DBSession, user: AdminUser):
    asset = db.get(VehicleAsset, asset_id)
    if not asset:
        raise HTTPException(404, "ASSET_NOT_FOUND")
    if value.action not in {"approve", "reject"}:
        raise HTTPException(422, "INVALID_ASSET_ACTION")
    if value.action == "approve":
        if not asset.rights.get("commercial_reuse"):
            raise HTTPException(409, "IMAGE_RIGHTS_REQUIRED")
        for variant_id in asset.applicability["variant_ids"]:
            _, c = published(db, variant_id, production_safe=False)
            a = asset.applicability
            if (
                buyer.normalized(c["make"]) != buyer.normalized(a["make"])
                or buyer.normalized(c["model"]) != buyer.normalized(a["model"])
                or c.get("generation") != a["generation"]
                or c.get("facelift") != a.get("facelift")
                or buyer.fact_value(c, "body") != a["body"]
                or c["original_market"] != a["market"]
                or not a["year_from"] <= c["model_year"] <= a["year_to"]
            ):
                raise HTTPException(409, "IMAGE_APPLICABILITY_UNVERIFIED")
    asset.state = "APPROVED" if value.action == "approve" else "REJECTED"
    asset.reviewer = user.id
    audit(db, user, "ASSET", asset.id, asset.state, value.note)
    db.commit()
    return {"id": asset.id, "state": asset.state}


@router.get("/admin/assets/{asset_id}/preview")
def private_asset_preview(asset_id: str, db: DBSession, user: AdminUser):
    asset = db.get(VehicleAsset, asset_id)
    if not asset or not asset.renditions.get("hero"):
        raise HTTPException(404, "ASSET_NOT_FOUND")
    path = private_path(asset.renditions["hero"])
    if not path.is_file():
        raise HTTPException(404, "ASSET_NOT_FOUND")
    return FileResponse(
        path, media_type="image/webp", headers={"Cache-Control": "private, no-store"}
    )


class PublicationInput(StrictModel):
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9-]+$")
    translations: dict
    variant_ids: list[str] = Field(min_length=2, max_length=3)
    asset_ids: list[str] = Field(default_factory=list, max_length=3)
    scenario: dict = Field(default_factory=dict)
    claims: list[dict] = Field(default_factory=list, max_length=40)
    topics: list[str] = Field(default_factory=list, max_length=10)


@router.post("/admin/publications")
def save_publication(value: PublicationInput, db: DBSession, user: AdminUser):
    if set(value.translations) != {"az", "ru"} or any(
        not value.translations[lang].get("title") or not value.translations[lang].get("limitations")
        for lang in ("az", "ru")
    ):
        raise HTTPException(422, "AZ_RU_TRANSLATIONS_REQUIRED")
    if len(json.dumps(value.model_dump(), ensure_ascii=False)) > 60000:
        raise HTTPException(413, "PUBLICATION_TOO_LARGE")
    for variant_id in value.variant_ids:
        published(db, variant_id, production_safe=False)
    for claim in value.claims:
        ids = claim.get("evidence_ids", [])
        if not ids:
            raise HTTPException(422, "CLAIM_EVIDENCE_REQUIRED")
        for eid in ids:
            evidence = db.get(TechnicalEvidence, eid)
            if not evidence or evidence.vehicle_variant_id not in value.variant_ids:
                raise HTTPException(422, "CLAIM_APPLICABILITY_MISMATCH")
    pub = db.scalar(select(EditorialPublication).where(EditorialPublication.slug == value.slug))
    if pub:
        audit(
            db,
            user,
            "PUBLICATION",
            pub.id,
            "REVISED",
            "Publication revised; review required",
            before={"translations": pub.translations, "claims": pub.claims, "version": pub.version},
        )
        pub.version += 1
        for k, v in value.model_dump().items():
            setattr(pub, k, v)
        pub.state = "DRAFT"
    else:
        pub = EditorialPublication(**value.model_dump())
        db.add(pub)
    db.commit()
    return {"id": pub.id, "state": pub.state}


@router.post("/admin/publications/{publication_id}/review")
def publication_review(publication_id: str, value: ReviewInput, db: DBSession, user: AdminUser):
    pub = db.get(EditorialPublication, publication_id)
    if not pub:
        raise HTTPException(404, "PUBLICATION_NOT_FOUND")
    if value.action != "publish":
        raise HTTPException(422, "INVALID_PUBLICATION_ACTION")
    if not pub.claims:
        raise HTTPException(409, "GROUNDED_CLAIMS_REQUIRED")
    for aid in pub.asset_ids:
        asset = db.get(VehicleAsset, aid)
        if (
            not asset
            or asset.state != "APPROVED"
            or not set(asset.applicability["variant_ids"]) & set(pub.variant_ids)
        ):
            raise HTTPException(409, "ASSET_REVIEW_REQUIRED")
    pub.state = "PUBLISHED"
    audit(db, user, "PUBLICATION", pub.id, "PUBLISHED", value.note, after={"version": pub.version})
    db.commit()
    return {"id": pub.id, "state": pub.state}
