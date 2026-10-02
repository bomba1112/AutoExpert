from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.models.evidence import (
    KnownIssue,
    LocalCostItem,
    MarketListing,
    OwnerEvidence,
    TechnicalEvidence,
)
from app.schemas.analysis import EvidenceBundle, GeneratedReport
from app.schemas.chat import ChatContextSnapshot, ChatConversationTurn, GroundedChatDraft


class TechnicalDataProvider(Protocol):
    def evidence_for(self, variant_id: str, market: str) -> list[TechnicalEvidence]: ...

    def issues_for(self, variant_id: str) -> list[KnownIssue]: ...


class MarketDataProvider(Protocol):
    def listings_for(self, *, country: str, make: str, model: str) -> list[MarketListing]: ...


class LocalCostProvider(Protocol):
    def costs_for(
        self, *, country: str, city: str | None, variant_id: str
    ) -> list[LocalCostItem]: ...


class OwnerExperienceProvider(Protocol):
    """Independent owner/community material, separate from official complaint repositories."""

    def observations_for(self, variant_id: str) -> list[OwnerEvidence]: ...


# Compatibility name retained for the Stage A/B database adapter.
OwnerReviewProvider = OwnerExperienceProvider


class LLMProvider(Protocol):
    def generate_report(self, bundle: EvidenceBundle, language: str) -> GeneratedReport: ...

    def answer_question(self, bundle: EvidenceBundle, question: str, language: str) -> str: ...


class ChatLLMProvider(Protocol):
    """Provider boundary for context-only Auto Expert conversation generation."""

    name: str

    def answer_chat(
        self,
        *,
        context: ChatContextSnapshot,
        conversation: list[ChatConversationTurn],
        question: str,
    ) -> GroundedChatDraft: ...


@dataclass(frozen=True)
class PaymentResult:
    succeeded: bool
    external_id: str | None
    provider_payload: dict


class PaymentProvider(Protocol):
    name: str

    def charge(
        self, *, report_id: str, user_id: str, amount: Decimal, currency: str
    ) -> PaymentResult: ...


class AnalyticsProvider(Protocol):
    def track(
        self,
        event_name: str,
        *,
        user_id: str | None,
        anonymous_id: str | None,
        properties: dict,
    ) -> None: ...
