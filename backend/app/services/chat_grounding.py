from __future__ import annotations

from app.models.enums import EvidenceStatus
from app.schemas.chat import ChatContextSnapshot, GroundedChatDraft


class ChatGroundingError(ValueError):
    pass


_ALLOWED_OUTPUTS = {
    EvidenceStatus.CONFIRMED: {
        EvidenceStatus.CONFIRMED,
        EvidenceStatus.ESTIMATE,
        EvidenceStatus.NEEDS_INSPECTION,
        EvidenceStatus.INSUFFICIENT_DATA,
    },
    EvidenceStatus.ESTIMATE: {
        EvidenceStatus.ESTIMATE,
        EvidenceStatus.NEEDS_INSPECTION,
        EvidenceStatus.INSUFFICIENT_DATA,
    },
    EvidenceStatus.NEEDS_INSPECTION: {
        EvidenceStatus.NEEDS_INSPECTION,
        EvidenceStatus.INSUFFICIENT_DATA,
    },
    EvidenceStatus.INSUFFICIENT_DATA: {EvidenceStatus.INSUFFICIENT_DATA},
}

_INTERNAL_PAYLOAD_MARKERS = (
    "full_history_payload",
    "context_snapshot",
    "system_constraints",
    "provider_payload",
    '"sale_price":',
    '"odometer_records":',
)


def validate_grounded_chat_draft(
    context: ChatContextSnapshot,
    draft: GroundedChatDraft,
) -> GroundedChatDraft:
    allowed_sources = {item.id for item in context.sources}
    unknown_sources = set(draft.source_ids) - allowed_sources
    if unknown_sources:
        raise ChatGroundingError(f"Unknown chat source IDs: {sorted(unknown_sources)}")

    unknown_evidence = set(draft.evidence_ids) - set(context.evidence_statuses)
    if unknown_evidence:
        raise ChatGroundingError(f"Unknown chat evidence IDs: {sorted(unknown_evidence)}")

    if draft.status in {EvidenceStatus.CONFIRMED, EvidenceStatus.ESTIMATE}:
        if not draft.source_ids:
            raise ChatGroundingError("Grounded chat answers must attach a source")
        if not draft.evidence_ids:
            raise ChatGroundingError("Grounded chat answers must reference evidence")

    for evidence_id in draft.evidence_ids:
        input_status = context.evidence_statuses[evidence_id]
        if draft.status not in _ALLOWED_OUTPUTS[input_status]:
            raise ChatGroundingError(
                f"Chat answer upgrades {evidence_id} from {input_status} to {draft.status}"
            )
        if (
            evidence_id.startswith(("vin_history.", "event-"))
            and not context.vin_summary.history_unlocked
        ):
            raise ChatGroundingError("Locked VIN history cannot be used by chat")

    normalized_text = draft.text.casefold()
    if any(marker in normalized_text for marker in _INTERNAL_PAYLOAD_MARKERS):
        raise ChatGroundingError("Chat answer exposes an internal payload marker")
    return draft
