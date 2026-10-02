from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, Field

from app.models.enums import (
    ChatAccessMode,
    ChatRole,
    ConfidenceLevel,
    DataOrigin,
    EvidenceStatus,
    OdometerRisk,
)
from app.schemas.analysis import LocalCostSnapshot
from app.schemas.common import APIModel, SourceSnapshot, SupportedLanguage
from app.schemas.reviews import OwnerFeedbackAggregation
from app.schemas.vin import (
    DossierKnownIssue,
    DossierSection,
    VehicleKnowledgeProfileDTO,
    VINHistoryPayload,
)


class ChatVINSummary(APIModel):
    vin: str
    found: bool
    records_count: int = Field(ge=0)
    photos_count: int = Field(ge=0)
    auctions_count: int = Field(ge=0)
    has_salvage_title: bool
    odometer_risk: OdometerRisk
    history_unlocked: bool
    is_demo: bool
    data_origin: DataOrigin = DataOrigin.DEMO


class ChatMarketAnalysisSnapshot(APIModel):
    status: EvidenceStatus
    confidence: ConfidenceLevel
    sample_count: int = 0
    comparable_count: int = 0
    median: Decimal | None = None
    market_range_low: Decimal | None = None
    market_range_high: Decimal | None = None
    currency: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class ChatOwnerFeedbackSnapshot(APIModel):
    status: EvidenceStatus
    aggregation: OwnerFeedbackAggregation
    wording_rule: str
    source_ids: list[str] = Field(default_factory=list)


class ChatContextSnapshot(APIModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, frozen=True)

    schema_version: str = "2.0.0-chat"
    snapshot_id: str | None = None
    vehicle_profile: VehicleKnowledgeProfileDTO
    vin_summary: ChatVINSummary
    unlocked_vin_history: VINHistoryPayload | None
    dossier_sections: list[DossierSection]
    known_issues: list[DossierKnownIssue]
    owner_feedback: ChatOwnerFeedbackSnapshot
    market_analysis: ChatMarketAnalysisSnapshot
    local_costs: list[LocalCostSnapshot]
    sources: list[SourceSnapshot]
    evidence_statuses: dict[str, EvidenceStatus]
    language: SupportedLanguage
    created_at: datetime
    is_demo: bool


class ChatConversationTurn(APIModel):
    role: ChatRole
    content: str


class GroundedChatDraft(APIModel):
    text: str = Field(min_length=1, max_length=8000)
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ChatAccessPolicyDTO(APIModel):
    mode: ChatAccessMode
    question_limit: int | None
    questions_used: int = Field(ge=0)
    questions_remaining: int | None = Field(default=None, ge=0)
    unlimited: bool


class ChatSourceAttachment(SourceSnapshot):
    pass


class ChatMessageCreate(APIModel):
    question: str = Field(min_length=2, max_length=1000)


class ChatMessageItem(APIModel):
    id: str
    role: ChatRole
    content: str
    status: EvidenceStatus | None = None
    sources: list[ChatSourceAttachment] = Field(default_factory=list)
    created_at: datetime


class ChatSessionResponse(APIModel):
    session_id: str
    vin_check_id: str
    vehicle: VehicleKnowledgeProfileDTO
    vin_masked: str
    language: SupportedLanguage
    policy: ChatAccessPolicyDTO
    suggested_questions: list[str]
    messages: list[ChatMessageItem]
    is_demo: bool


class ChatAnswerResponse(APIModel):
    session_id: str
    message: ChatMessageItem
    policy: ChatAccessPolicyDTO
