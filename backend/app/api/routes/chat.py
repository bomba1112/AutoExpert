from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DBSession
from app.core.config import get_settings
from app.llm.chat_deterministic import DeterministicGroundedChatProvider
from app.models.enums import ChatRole, EntitlementStatus, EntitlementType
from app.models.vehicle_knowledge import (
    AutoExpertChatMessage,
    AutoExpertChatSession,
    VINCheck,
    VINEntitlement,
)
from app.providers.analytics import DatabaseAnalyticsProvider
from app.providers.base import ChatLLMProvider
from app.schemas.chat import (
    ChatAccessPolicyDTO,
    ChatAnswerResponse,
    ChatContextSnapshot,
    ChatConversationTurn,
    ChatMessageCreate,
    ChatMessageItem,
    ChatSessionResponse,
    ChatSourceAttachment,
)
from app.services.chat_access import ChatAccessGrant, configured_chat_access_policy
from app.services.chat_context import (
    build_chat_context_snapshot,
    chat_context_digest,
    validate_chat_context_digest,
)
from app.services.chat_grounding import ChatGroundingError, validate_grounded_chat_draft
from app.services.developer_access import DeveloperAccess, DeveloperAccessContext
from app.services.dossier import profile_dto

router = APIRouter(tags=["auto-expert-chat"])


def get_chat_llm_provider() -> ChatLLMProvider:
    return DeterministicGroundedChatProvider()


ChatProvider = Annotated[ChatLLMProvider, Depends(get_chat_llm_provider)]


def _stale_variant_context(session) -> bool:
    if session.is_demo:
        return False
    profile = session.vin_check.profile
    snapshot = session.context_snapshot
    if profile and profile.dossier_seed.get("knowledge_depth"):
        return snapshot.get("vehicle_profile", {}).get(
            "profile_version"
        ) != profile.profile_version or not any(
            s.get("key") == "variant_identity" for s in snapshot.get("dossier_sections", [])
        )
    return False


_SUGGESTIONS = {
    "ru": [
        "Что проверить при этом пробеге?",
        "Эта коробка надёжная?",
        "Стоит ли бояться Salvage?",
        "Что спросить у продавца?",
        "Цена 27 500 AZN нормальная?",
        "Подойдёт ли машина для плохих дорог?",
    ],
    "az": [
        "Bu yürüşdə nəyi yoxlamaq lazımdır?",
        "Bu sürətlər qutusu etibarlıdır?",
        "Salvage statusundan qorxmaq lazımdır?",
        "Satıcıdan nə soruşum?",
        "27 500 AZN normal qiymətdir?",
        "Bu avtomobil pis yollar üçün uyğundur?",
    ],
    "en": [
        "What should I inspect at this mileage?",
        "Is this transmission reliable?",
        "Should I be worried about Salvage?",
        "What should I ask the seller?",
        "Is 27,500 AZN a fair price?",
        "Is this car suitable for poor roads?",
    ],
}


@router.post(
    "/vin/{check_id}/chat/session",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_resume_chat_session(
    check_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> ChatSessionResponse:
    check = _owned_check(db, user.id, check_id)
    has_entitlement = _has_vin_entitlement(db, check.id, user.id) or access.bypass_paywall
    if not has_entitlement:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Auto Expert Chat requires an unlocked VIN report",
        )
    existing = db.scalar(
        select(AutoExpertChatSession)
        .where(
            AutoExpertChatSession.vin_check_id == check.id,
            AutoExpertChatSession.user_id == user.id,
        )
        .order_by(AutoExpertChatSession.created_at.desc())
    )
    if existing is not None and not _stale_variant_context(existing):
        return _session_response(db, existing, has_entitlement=True, access=access)

    context = build_chat_context_snapshot(db, check, history_unlocked=True)
    policy = configured_chat_access_policy()
    grant = policy.grant(
        has_unlocked_dossier=True,
        is_demo=check.is_demo,
        questions_used=0,
        developer_unlimited=access.bypass_paywall,
        simulate_user_paywall=access.simulate_user_paywall,
    )
    session = AutoExpertChatSession(
        user_id=user.id,
        vin_check_id=check.id,
        language=check.language,
        context_snapshot=context.model_dump(mode="json"),
        context_hash=chat_context_digest(context),
        access_mode=grant.mode,
        question_limit=grant.question_limit,
        is_demo=check.is_demo,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(db, session, has_entitlement=True, access=access)


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> ChatSessionResponse:
    session = _owned_session(db, user.id, session_id)
    has_entitlement = (
        _has_vin_entitlement(
            db,
            session.vin_check_id,
            user.id,
        )
        or access.bypass_paywall
    )
    if not has_entitlement:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="VIN report entitlement is not active",
        )
    return _session_response(db, session, has_entitlement=True, access=access)


@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_auto_expert(
    session_id: str,
    value: ChatMessageCreate,
    db: DBSession,
    user: CurrentUser,
    provider: ChatProvider,
    access: DeveloperAccess,
) -> ChatAnswerResponse:
    session = _owned_session(db, user.id, session_id, for_update=True)
    has_entitlement = (
        _has_vin_entitlement(
            db,
            session.vin_check_id,
            user.id,
        )
        or access.bypass_paywall
    )
    used = _questions_used(db, session.id, user.id)
    grant = configured_chat_access_policy().grant(
        has_unlocked_dossier=has_entitlement,
        is_demo=session.is_demo,
        questions_used=used,
        developer_unlimited=access.bypass_paywall,
        simulate_user_paywall=access.simulate_user_paywall,
    )
    if not has_entitlement:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="VIN report entitlement is not active",
        )
    if not grant.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Auto Expert Chat question limit reached",
        )

    context = ChatContextSnapshot.model_validate(session.context_snapshot)
    if _stale_variant_context(session):
        raise HTTPException(
            status_code=409,
            detail="Vehicle identity has changed; reopen chat for the current report",
        )
    if not validate_chat_context_digest(context, session.context_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chat context integrity check failed",
        )
    conversation = [
        ChatConversationTurn(role=item.role, content=item.content) for item in session.messages
    ]
    try:
        draft = validate_grounded_chat_draft(
            context,
            provider.answer_chat(
                context=context,
                conversation=conversation,
                question=value.question,
            ),
        )
    except ChatGroundingError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auto Expert could not produce a grounded answer",
        ) from error

    next_sequence = max((item.sequence for item in session.messages), default=0) + 1
    user_message = AutoExpertChatMessage(
        session_id=session.id,
        user_id=user.id,
        role=ChatRole.USER,
        sequence=next_sequence,
        content=value.question,
        status=None,
        source_ids=[],
        evidence_ids=[],
        is_demo=session.is_demo,
    )
    answer_message = AutoExpertChatMessage(
        session_id=session.id,
        user_id=user.id,
        role=ChatRole.ASSISTANT,
        sequence=next_sequence + 1,
        content=draft.text,
        status=draft.status,
        source_ids=draft.source_ids,
        evidence_ids=draft.evidence_ids,
        is_demo=session.is_demo,
    )
    db.add_all([user_message, answer_message])
    DatabaseAnalyticsProvider(db).track(
        "followup_question_used",
        user_id=user.id,
        anonymous_id=None,
        properties={
            "vin_check_id": session.vin_check_id,
            "chat_session_id": session.id,
            "question_number": used + 1,
            "provider": provider.name,
        },
    )
    db.commit()
    db.refresh(answer_message)
    updated_grant = configured_chat_access_policy().grant(
        has_unlocked_dossier=True,
        is_demo=session.is_demo,
        questions_used=used + 1,
        developer_unlimited=access.bypass_paywall,
        simulate_user_paywall=access.simulate_user_paywall,
    )
    return ChatAnswerResponse(
        session_id=session.id,
        message=_message_item(answer_message, context),
        policy=_policy_dto(updated_grant),
    )


def _owned_check(db: DBSession, user_id: str, check_id: str) -> VINCheck:
    check = db.scalar(select(VINCheck).where(VINCheck.id == check_id, VINCheck.user_id == user_id))
    if check is None or (get_settings().environment == "production" and check.is_demo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIN check not found")
    return check


def _owned_session(
    db: DBSession,
    user_id: str,
    session_id: str,
    *,
    for_update: bool = False,
) -> AutoExpertChatSession:
    query = select(AutoExpertChatSession).where(
        AutoExpertChatSession.id == session_id,
        AutoExpertChatSession.user_id == user_id,
    )
    if for_update:
        query = query.with_for_update()
    session = db.scalar(query)
    if session is None or (get_settings().environment == "production" and session.is_demo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


def _has_vin_entitlement(db: DBSession, check_id: str, user_id: str) -> bool:
    entitlement = db.scalar(
        select(VINEntitlement.id).where(
            VINEntitlement.vin_check_id == check_id,
            VINEntitlement.user_id == user_id,
            VINEntitlement.entitlement_type == EntitlementType.VIN_REPORT_UNLOCKED,
            VINEntitlement.status == EntitlementStatus.ACTIVE,
        )
    )
    return entitlement is not None


def _questions_used(db: DBSession, session_id: str, user_id: str) -> int:
    return int(
        db.scalar(
            select(func.count(AutoExpertChatMessage.id)).where(
                AutoExpertChatMessage.session_id == session_id,
                AutoExpertChatMessage.user_id == user_id,
                AutoExpertChatMessage.role == ChatRole.USER,
            )
        )
        or 0
    )


def _session_response(
    db: DBSession,
    session: AutoExpertChatSession,
    *,
    has_entitlement: bool,
    access: DeveloperAccessContext,
) -> ChatSessionResponse:
    context = ChatContextSnapshot.model_validate(session.context_snapshot)
    if _stale_variant_context(session):
        raise HTTPException(
            status_code=409,
            detail="Vehicle identity has changed; reopen chat for the current report",
        )
    if not validate_chat_context_digest(context, session.context_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chat context integrity check failed",
        )
    used = _questions_used(db, session.id, session.user_id)
    grant = configured_chat_access_policy().grant(
        has_unlocked_dossier=has_entitlement,
        is_demo=session.is_demo,
        questions_used=used,
        developer_unlimited=access.bypass_paywall,
        simulate_user_paywall=access.simulate_user_paywall,
    )
    return ChatSessionResponse(
        session_id=session.id,
        vin_check_id=session.vin_check_id,
        vehicle=profile_dto(session.vin_check.profile),
        vin_masked=_mask_vin(session.vin_check.normalized_vin),
        language=context.language,
        policy=_policy_dto(grant),
        suggested_questions=_SUGGESTIONS[context.language],
        messages=[_message_item(item, context) for item in session.messages],
        is_demo=session.is_demo,
    )


def _message_item(
    message: AutoExpertChatMessage,
    context: ChatContextSnapshot,
) -> ChatMessageItem:
    source_map = {item.id: item for item in context.sources}
    return ChatMessageItem(
        id=message.id,
        role=message.role,
        content=message.content,
        status=message.status,
        sources=[
            ChatSourceAttachment.model_validate(source_map[source_id])
            for source_id in message.source_ids
            if source_id in source_map
        ],
        created_at=message.created_at,
    )


def _policy_dto(grant: ChatAccessGrant) -> ChatAccessPolicyDTO:
    return ChatAccessPolicyDTO(
        mode=grant.mode,
        question_limit=grant.question_limit,
        questions_used=grant.questions_used,
        questions_remaining=grant.questions_remaining,
        unlimited=grant.unlimited,
    )


def _mask_vin(vin: str) -> str:
    if not vin:
        return "—"
    return f"{vin[:5]}••••{vin[-4:]}"
