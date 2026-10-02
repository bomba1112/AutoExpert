# ruff: noqa: E501
from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import Field
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.api.routes.chat import ChatProvider
from app.models.analysis import AnalysisRequest, Report, ReportQuestion
from app.models.enums import ChatRole
from app.models.research import ResearchJob
from app.schemas.chat import ChatContextSnapshot, ChatConversationTurn, ChatMessageCreate
from app.schemas.common import APIModel, SupportedLanguage
from app.schemas.paid_report import PaidVehicleReport
from app.services.buyer_experience import comparison_projection, create_dossier, persist_report
from app.services.chat_grounding import validate_grounded_chat_draft
from app.services.developer_access import DeveloperAccess
from app.services.listing_intake import ListingInputError, _plain, validate_turbo_url
from app.services.paid_report import tr
from app.services.report_pdf import render_report_pdf
from app.services.research_rights import job_uses_restricted_epa, report_uses_restricted_epa

router = APIRouter(prefix="/reports/buyer", tags=["buyer-experience"])


class ListingInput(APIModel):
    url: str = Field(min_length=8, max_length=2000)
    description: str | None = Field(default=None, max_length=12000)
    language: SupportedLanguage = "ru"


def import_listing(url: str) -> dict:
    """Legacy buyer listing route now records a reference without an HTTP request."""
    return {
        "source_url": url,
        "status": "UNAVAILABLE",
        "reason": "USER_CONTENT_REQUIRED",
        "data": {},
    }


class Preferences(APIModel):
    original_market: str | None = Field(default=None, max_length=12)
    priorities: list[
        Literal[
            "economy", "reliability", "comfort", "maintenance", "space", "performance", "resale"
        ]
    ] = Field(default_factory=list, max_length=7)
    country: str = Field(default="AZ", max_length=2)
    city: str | None = Field(default=None, max_length=100)
    roads: str | None = Field(default=None, max_length=100)
    monthly_km: int | None = Field(default=None, ge=0, le=30000)


class DossierInput(APIModel):
    job_id: str
    listing_id: str | None = None
    parent_report_id: str | None = None
    language: SupportedLanguage = "ru"
    preferences: Preferences = Field(default_factory=Preferences)


class ComparisonInput(APIModel):
    report_ids: list[str] = Field(min_length=2, max_length=3)
    language: SupportedLanguage = "ru"
    preferences: Preferences = Field(default_factory=Preferences)


def owned_report(db, uid, rid):
    report = db.scalar(select(Report).where(Report.id == rid, Report.user_id == uid))
    if report is None or "buyer" not in report.generated_sections:
        raise HTTPException(404, "Report not found")
    if report_uses_restricted_epa(db, report):
        raise HTTPException(409, "EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    return report


def owned_listing(db, uid, lid):
    record = db.scalar(
        select(AnalysisRequest).where(AnalysisRequest.id == lid, AnalysisRequest.user_id == uid)
    )
    if record is None or "listing" not in record.vehicle_input:
        raise HTTPException(404, "Listing not found")
    return {**record.vehicle_input["listing"], "id": record.id}


def permitted(report, access):
    if not access.bypass_paywall and not report.is_unlocked:
        raise HTTPException(
            402, "Full buyer preview is available in local DeveloperMode; purchases are not enabled"
        )


def dto(report, language=None):
    lang = language or report.language
    return {
        "id": report.id,
        "kind": report.input_snapshot["kind"],
        "created_at": report.created_at,
        "projection": report.generated_sections["translations"][lang],
        "input": report.input_snapshot,
        "sources": report.evidence_bundle.get("sources", []),
        "chat_mode": "SOURCE_GUIDED",
        "photos": (report.input_snapshot.get("listing") or {}).get("data", {}).get("photos", []),
        "questions": [
            {"id": q.id, "question": q.question, "answer": q.answer}
            for q in report.questions
            if q.succeeded
        ],
    }


@router.post("/listings")
def import_offer(value: ListingInput, db: DBSession, user: CurrentUser):
    try:
        source_url, _ = validate_turbo_url(value.url)
    except ListingInputError as exc:
        raise HTTPException(422, str(exc)) from exc
    if value.description:
        snapshot = {
            "source_url": source_url,
            "status": "USER_PASTED",
            "reason": None,
            "data": {
                "description": _plain(value.description),
                "claim_type": "SELLER_CLAIM",
                "photos": [],
            },
        }
    else:
        snapshot = import_listing(source_url)
    analysis = AnalysisRequest(
        user_id=user.id,
        country="AZ",
        language=value.language,
        vehicle_input={"listing": snapshot},
        usage_profile={},
    )
    db.add(analysis)
    db.commit()
    return {**snapshot, "id": analysis.id}


@router.get("/listings/{listing_id}")
def get_offer(listing_id: str, db: DBSession, user: CurrentUser):
    return owned_listing(db, user.id, listing_id)


@router.post("/dossiers")
def create_buyer_dossier(
    value: DossierInput, db: DBSession, user: CurrentUser, access: DeveloperAccess
):
    job = db.scalar(
        select(ResearchJob).where(ResearchJob.id == value.job_id, ResearchJob.user_id == user.id)
    )
    if job is None or job.profile is None or not job.dossier_snapshot:
        raise HTTPException(409, "Vehicle research must have a completed dossier")
    if job_uses_restricted_epa(db, job):
        raise HTTPException(409, "EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    if job.is_demo or job.profile.is_demo:
        raise HTTPException(409, "Real buyer reports cannot use demo profiles")
    listing = owned_listing(db, user.id, value.listing_id) if value.listing_id else None
    if value.parent_report_id:
        parent = owned_report(db, user.id, value.parent_report_id)
        listing = parent.input_snapshot.get("listing")
    if listing:
        claims = listing.get("data", {})
        for key, actual in (
            ("make", job.profile.make),
            ("model", job.profile.model),
            ("year", job.profile.year),
        ):
            if claims.get(key) and str(claims[key]).casefold() != str(actual).casefold():
                raise HTTPException(409, "Listing and selected vehicle identity differ")
        if (
            claims.get("vin")
            and claims["vin"] != job.requested_vehicle.get("vin")
            and job.requested_vehicle.get("vin")
        ):
            raise HTTPException(409, "Listing VIN mismatch")
    report = create_dossier(
        db,
        user.id,
        job,
        language=value.language,
        listing=listing,
        preferences=value.preferences.model_dump(),
        parent_id=value.parent_report_id,
    )
    # Capture normalized consumption in this immutable report for comparisons.
    findings = job.profile.dossier_seed.get("knowledge_depth", {}).get("findings", [])
    official = next(
        (
            f["value"]
            for f in findings
            if f["topic"] == "fuel_consumption"
            and f["subtopic"] == "official"
            and f["status"] == "CONFIRMED"
        ),
        {},
    )
    bundle = {**report.evidence_bundle, "official_consumption": official.get("combined")}
    bundle["official_electricity"] = next(
        (
            f["value"]
            for f in findings
            if f["topic"] == "fuel_consumption"
            and f["subtopic"] == "electric_kwh_100km"
            and f["status"] == "CONFIRMED"
        ),
        None,
    )
    report.evidence_bundle = bundle
    db.commit()
    permitted(report, access)
    return dto(report)


@router.post("/comparisons")
def create_comparison(
    value: ComparisonInput, db: DBSession, user: CurrentUser, access: DeveloperAccess
):
    if len(set(value.report_ids)) != len(value.report_ids):
        raise HTTPException(422, "Choose different reports")
    members = [owned_report(db, user.id, rid) for rid in value.report_ids]
    for member in members:
        permitted(member, access)
        if member.input_snapshot["kind"] == "COMPARISON":
            raise HTTPException(422, "A comparison cannot be a vehicle")
    preferences = value.preferences.model_dump()
    projections = {
        lang: comparison_projection(members, lang, preferences).model_dump(mode="json")
        for lang in ("ru", "az", "en")
    }
    sources = {s["id"]: s for m in members for s in m.evidence_bundle.get("sources", [])}
    report = persist_report(
        db,
        user.id,
        value.language,
        {"kind": "COMPARISON", "member_ids": value.report_ids, "preferences": preferences},
        projections,
        {"sources": list(sources.values())},
    )
    permitted(report, access)
    return dto(report)


@router.get("")
def list_buyer_reports(db: DBSession, user: CurrentUser):
    reports = db.scalars(
        select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
    )
    return [
        {
            "id": r.id,
            "kind": r.input_snapshot["kind"],
            "title": r.generated_sections["buyer"]["title"],
            "subtitle": r.generated_sections["buyer"]["subtitle"],
            "language": r.language,
            "created_at": r.created_at,
        }
        for r in reports
        if "buyer" in r.generated_sections and not report_uses_restricted_epa(db, r)
    ]


@router.get("/{report_id}")
def get_buyer_report(
    report_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
    language: SupportedLanguage | None = None,
):
    report = owned_report(db, user.id, report_id)
    permitted(report, access)
    return dto(report, language)


@router.get("/{report_id}/pdf")
def export_buyer_pdf(
    report_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
    language: SupportedLanguage | None = None,
):
    report = owned_report(db, user.id, report_id)
    permitted(report, access)
    projection = PaidVehicleReport.model_validate(dto(report, language)["projection"])
    data = render_report_pdf(projection, sources=report.evidence_bundle.get("sources", []))
    return Response(
        data,
        media_type="application/pdf",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'attachment; filename="AutoExpert_{report.id}.pdf"',
        },
    )


@router.post("/{report_id}/questions")
def ask_buyer(
    report_id: str,
    value: ChatMessageCreate,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
    provider: ChatProvider,
    language: SupportedLanguage | None = None,
):
    report = owned_report(db, user.id, report_id)
    permitted(report, access)
    lang = language or report.language
    if not access.bypass_paywall and len([q for q in report.questions if q.succeeded]) >= 3:
        raise HTTPException(402, "Question allowance exhausted")
    conversation = [
        turn
        for q in report.questions[-20:]
        if q.succeeded
        for turn in (
            ChatConversationTurn(role=ChatRole.USER, content=q.question),
            ChatConversationTurn(role=ChatRole.ASSISTANT, content=q.answer),
        )
    ]
    answers, evidence = [], []
    comparison = report.input_snapshot["kind"] == "COMPARISON"
    members = (
        [owned_report(db, user.id, rid) for rid in report.input_snapshot["member_ids"]]
        if comparison
        else [report]
    )
    if comparison and any(
        k in value.question.casefold()
        for k in ("почему", "лучше", "выб", "why", "better", "choose", "niyə", "yaxşı", "seç")
    ):
        projection = report.generated_sections["translations"][lang]
        verdict = next(s for s in projection["sections"] if s["key"] == "expert_verdict")
        answers.append("\n\n".join(p["text"] for p in verdict["paragraphs"]))
    for member in members:
        if member.evidence_bundle.get("catalog_snapshot"):
            from app.services.catalog_buyer import answer_catalog_question

            text, grounding = answer_catalog_question(member, value.question, lang)
            answers.append(
                (member.generated_sections["buyer"]["title"] + "\n" if comparison else "") + text
            )
            evidence.append({"report_id": member.id, **grounding})
            continue
        context = ChatContextSnapshot.model_validate(member.evidence_bundle["contexts"][lang])
        monthly = None
        for utterance in [
            value.question,
            *[q.question for q in reversed(report.questions) if q.succeeded],
        ]:
            if re.search(r"месяц|month|\bay\b|ayda|aylıq", utterance, re.I):
                found = re.search(r"(?<!\d)(\d[\d ]{0,5})\s*(?:км|km)", utterance, re.I)
                if found:
                    monthly = int(found[1].replace(" ", ""))
                    break
        if monthly is not None and any(
            k in value.question.casefold()
            for k in ("месяц", "month", "ay", "при мо", "my mileage", "yürüş")
        ):
            consumption = member.evidence_bundle.get("official_consumption")
            electric = (
                consumption is None
                and member.evidence_bundle.get("official_electricity") is not None
            )
            if electric:
                consumption = member.evidence_bundle["official_electricity"]
            if consumption:
                quantity = round(consumption * monthly / 100, 1)
                text = tr(
                    lang,
                    f"При {monthly} км в месяц и официальных {consumption} л/100 км получается {quantity} л/месяц. Расчёт: пробег × расход / 100. Фактическое потребление зависит от маршрута и условий; цена топлива не задана, поэтому денежная стоимость не рассчитана.",
                    f"Ayda {monthly} km və rəsmi {consumption} l/100 km üçün {quantity} l/ay alınır. Hesablama: yürüş × sərfiyyat / 100. Faktiki sərfiyyat marşrut və şəraitdən asılıdır; yanacaq qiyməti verilmədiyi üçün pul xərci hesablanmayıb.",
                    f"At {monthly} km per month and official consumption of {consumption} L/100 km, the scenario uses {quantity} L/month. Calculation: distance × consumption / 100. Actual consumption depends on routes and conditions; no fuel price was supplied, so monetary cost is not calculated.",
                )
                if electric:
                    text = tr(
                        lang,
                        f"При {monthly} км в месяц и {consumption} кВт·ч/100 км по EPA расчёт составляет {quantity} кВт·ч/месяц. Это расчёт электрического режима; температура, скорость и условия зарядки меняют реальный результат. Денежная стоимость без вашего тарифа не рассчитана.",
                        f"Ayda {monthly} km və EPA üzrə {consumption} kWh/100 km üçün hesablama {quantity} kWh/ay təşkil edir. Bu elektrik rejiminin hesablamasıdır; temperatur, sürət və şarj şəraiti real nəticəni dəyişir. Tarifiniz olmadan pul xərci hesablanmayıb.",
                        f"At {monthly} km/month and EPA consumption of {consumption} kWh/100 km, the scenario uses {quantity} kWh/month. This covers electric operation; temperature, speed and charging conditions affect actual results. No monetary cost is calculated without your tariff.",
                    )
                answers.append(
                    (member.generated_sections["buyer"]["title"] + "\n" if comparison else "")
                    + text
                )
                fuel_rows = [
                    r
                    for s in member.generated_sections["translations"][lang]["sections"]
                    if s["key"] == "fuel"
                    for r in s["rows"]
                    if r["key"]
                    == (
                        "fuel_consumption.electric_kwh_100km"
                        if electric
                        else "fuel_consumption.official"
                    )
                ]
                evidence.append(
                    {
                        "report_id": member.id,
                        "source_ids": [sid for r in fuel_rows for sid in r["source_ids"]],
                        "evidence_ids": [eid for r in fuel_rows for eid in r["evidence_ids"]],
                        "calculation": {
                            "monthly_km": monthly,
                            "consumption_per_100km": consumption,
                            "quantity": quantity,
                            "unit": "kWh" if electric else "L",
                        },
                    }
                )
                continue
        draft = validate_grounded_chat_draft(
            context,
            provider.answer_chat(
                context=context,
                conversation=conversation if not comparison else [],
                question=value.question,
            ),
        )
        answers.append(
            (member.generated_sections["buyer"]["title"] + "\n" if comparison else "") + draft.text
        )
        evidence.append(
            {
                "report_id": member.id,
                "source_ids": draft.source_ids,
                "evidence_ids": draft.evidence_ids,
            }
        )
    answer = "\n\n".join(answers)
    question = ReportQuestion(
        report_id=report.id,
        user_id=user.id,
        question=value.question,
        answer=answer,
        evidence_snapshot={"members": evidence, "provider": provider.name, "language": lang},
        succeeded=True,
    )
    db.add(question)
    db.commit()
    return {
        "id": question.id,
        "question": question.question,
        "answer": answer,
        "mode": "SOURCE_GUIDED",
        "evidence": evidence,
    }
