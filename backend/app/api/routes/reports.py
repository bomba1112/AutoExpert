from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DBSession
from app.core.config import get_settings
from app.core.report_pricing import configured_report_price
from app.llm import DeterministicLLMProvider
from app.models.analysis import Payment, Report, ReportQuestion
from app.models.enums import PaymentStatus, ReportStatus
from app.providers.analytics import DatabaseAnalyticsProvider
from app.providers.payment import MockPaymentProvider
from app.schemas.analysis import (
    EvidenceBundle,
    PaymentUnlockRequest,
    PaymentUnlockResponse,
    PreviewResponse,
    ReportDetail,
    ReportQuestionCreate,
    ReportQuestionItem,
    ReportQuestionResponse,
    ReportSummary,
)
from app.services.report_access import preview_from_report
from app.services.research_rights import report_uses_restricted_epa

router = APIRouter(prefix="/reports", tags=["reports"])


def _owned_report(db: DBSession, user_id: str, report_id: str) -> Report:
    report = db.scalar(select(Report).where(Report.id == report_id, Report.user_id == user_id))
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if get_settings().environment == "production" and report.is_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report_uses_restricted_epa(db, report):
        raise HTTPException(status_code=409, detail="EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    return report


@router.get("", response_model=list[ReportSummary])
def list_reports(db: DBSession, user: CurrentUser) -> list[ReportSummary]:
    reports = list(
        db.scalars(
            select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
        )
    )
    return [
        ReportSummary(
            id=report.id,
            created_at=report.created_at,
            status=report.status.value,
            language=report.language,
            is_unlocked=report.is_unlocked,
            is_demo=report.is_demo,
            vehicle=report.input_snapshot.get("vehicle", {}),
            verdict=report.generated_sections.get("verdict", "COMPROMISE"),
        )
        for report in reports
        if get_settings().environment != "production" or not report.is_demo
        if not report_uses_restricted_epa(db, report)
    ]


@router.get("/{report_id}/preview", response_model=PreviewResponse)
def get_saved_preview(report_id: str, db: DBSession, user: CurrentUser) -> PreviewResponse:
    return preview_from_report(_owned_report(db, user.id, report_id))


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: str, db: DBSession, user: CurrentUser) -> ReportDetail:
    report = _owned_report(db, user.id, report_id)
    questions = _successful_questions(db, report.id, user.id)
    return ReportDetail(
        id=report.id,
        created_at=report.created_at,
        status=report.status.value,
        language=report.language,
        report_version=report.report_version,
        is_unlocked=report.is_unlocked,
        is_demo=report.is_demo,
        input_snapshot=report.input_snapshot,
        evidence_bundle=report.evidence_bundle if report.is_unlocked else None,
        calculated_data=report.calculated_data if report.is_unlocked else None,
        generated_sections=_locked_sections(report.generated_sections, report.is_unlocked),
        questions=[_question_item(question) for question in questions],
        questions_remaining=max(0, 3 - len(questions)),
    )


@router.post("/{report_id}/payments/mock", response_model=PaymentUnlockResponse)
def mock_unlock(
    report_id: str,
    value: PaymentUnlockRequest,
    db: DBSession,
    user: CurrentUser,
) -> PaymentUnlockResponse:
    settings = get_settings()
    if (
        settings.environment == "production"
        or not settings.demo_mode
        or settings.payment_provider != "mock"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock payment disabled")
    report = db.scalar(
        select(Report).where(Report.id == report_id, Report.user_id == user.id).with_for_update()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if get_settings().environment == "production" and report.is_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report_uses_restricted_epa(db, report):
        raise HTTPException(status_code=409, detail="EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    country = report.input_snapshot["vehicle"]["country"]
    amount, currency = configured_report_price(country)
    if amount is None or currency is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No configured report price for this market",
        )
    if report.is_unlocked:
        return PaymentUnlockResponse(
            report_id=report.id,
            provider="mock",
            status="ALREADY_UNLOCKED",
            is_unlocked=True,
            amount=amount,
            currency=currency,
            is_demo=report.is_demo,
        )

    analytics = DatabaseAnalyticsProvider(db)
    analytics.track(
        "payment_started",
        user_id=user.id,
        anonymous_id=None,
        properties={"report_id": report.id, "provider": "mock"},
    )
    provider = MockPaymentProvider(should_succeed=not value.simulate_failure)
    result = provider.charge(
        report_id=report.id,
        user_id=user.id,
        amount=amount,
        currency=currency,
    )
    payment = Payment(
        report_id=report.id,
        user_id=user.id,
        provider=provider.name,
        external_payment_id=result.external_id,
        status=PaymentStatus.SUCCEEDED if result.succeeded else PaymentStatus.FAILED,
        amount=amount,
        currency=currency,
        provider_payload=result.provider_payload,
    )
    db.add(payment)
    if result.succeeded:
        report.is_unlocked = True
        report.status = ReportStatus.FULL
        analytics.track(
            "payment_success",
            user_id=user.id,
            anonymous_id=None,
            properties={"report_id": report.id, "provider": "mock"},
        )
    db.commit()
    db.refresh(payment)
    return PaymentUnlockResponse(
        report_id=report.id,
        payment_id=payment.id,
        provider=provider.name,
        status=payment.status.value,
        is_unlocked=report.is_unlocked,
        amount=amount,
        currency=currency,
        is_demo=report.is_demo,
    )


@router.post("/{report_id}/questions", response_model=ReportQuestionResponse)
def ask_report_question(
    report_id: str,
    value: ReportQuestionCreate,
    db: DBSession,
    user: CurrentUser,
) -> ReportQuestionResponse:
    report = db.scalar(
        select(Report).where(Report.id == report_id, Report.user_id == user.id).with_for_update()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if get_settings().environment == "production" and report.is_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report_uses_restricted_epa(db, report):
        raise HTTPException(status_code=409, detail="EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    if not report.is_unlocked:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Report is locked")
    used = db.scalar(
        select(func.count(ReportQuestion.id)).where(
            ReportQuestion.report_id == report.id,
            ReportQuestion.user_id == user.id,
            ReportQuestion.succeeded.is_(True),
        )
    )
    if used >= 3:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The three-question limit has been reached",
        )

    bundle = EvidenceBundle.model_validate(report.evidence_bundle)
    answer = (
        DeterministicLLMProvider().answer_question(bundle, value.question, report.language).strip()
    )
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The report question could not be answered",
        )
    question = ReportQuestion(
        report_id=report.id,
        user_id=user.id,
        question=value.question,
        answer=answer,
        evidence_snapshot={
            "report_id": report.id,
            "report_version": report.report_version,
            "evidence_schema_version": bundle.schema_version,
        },
        succeeded=True,
    )
    db.add(question)
    DatabaseAnalyticsProvider(db).track(
        "followup_question_used",
        user_id=user.id,
        anonymous_id=None,
        properties={"report_id": report.id, "question_number": used + 1},
    )
    db.commit()
    db.refresh(question)
    return ReportQuestionResponse(
        report_id=report.id,
        item=_question_item(question),
        questions_remaining=2 - used,
    )


def _locked_sections(generated: dict, is_unlocked: bool) -> dict:
    if is_unlocked:
        return generated
    allowed = {"expert_verdict", "vehicle"}
    return {
        **{key: value for key, value in generated.items() if key != "sections"},
        "sections": [
            section for section in generated.get("sections", []) if section.get("key") in allowed
        ],
    }


def _successful_questions(db: DBSession, report_id: str, user_id: str) -> list[ReportQuestion]:
    return list(
        db.scalars(
            select(ReportQuestion)
            .where(
                ReportQuestion.report_id == report_id,
                ReportQuestion.user_id == user_id,
                ReportQuestion.succeeded.is_(True),
            )
            .order_by(ReportQuestion.created_at)
        )
    )


def _question_item(value: ReportQuestion) -> ReportQuestionItem:
    return ReportQuestionItem(
        id=value.id,
        question=value.question,
        answer=value.answer or "",
        created_at=value.created_at,
    )
