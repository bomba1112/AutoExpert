from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.models.enums import ChatAccessMode


@dataclass(frozen=True)
class ChatAccessGrant:
    allowed: bool
    mode: ChatAccessMode
    question_limit: int | None
    questions_used: int
    questions_remaining: int | None
    unlimited: bool


@dataclass(frozen=True)
class ChatAccessPolicy:
    mode: ChatAccessMode
    question_limit: int
    demo_unlimited: bool

    def grant(
        self,
        *,
        has_unlocked_dossier: bool,
        is_demo: bool,
        questions_used: int,
        developer_unlimited: bool = False,
        simulate_user_paywall: bool = False,
    ) -> ChatAccessGrant:
        if not has_unlocked_dossier:
            return ChatAccessGrant(
                allowed=False,
                mode=self.mode,
                question_limit=None,
                questions_used=questions_used,
                questions_remaining=None,
                unlimited=False,
            )
        unlimited = (
            developer_unlimited
            or (is_demo and self.demo_unlimited and not simulate_user_paywall)
            or self.mode
            in {
                ChatAccessMode.PREMIUM_UNLIMITED,
                ChatAccessMode.SUBSCRIPTION,
            }
        )
        limit = None if unlimited else self.question_limit
        remaining = None if limit is None else max(0, limit - questions_used)
        return ChatAccessGrant(
            allowed=unlimited or bool(remaining),
            mode=self.mode,
            question_limit=limit,
            questions_used=questions_used,
            questions_remaining=remaining,
            unlimited=unlimited,
        )


def configured_chat_access_policy() -> ChatAccessPolicy:
    settings = get_settings()
    return ChatAccessPolicy(
        mode=ChatAccessMode(settings.chat_access_mode),
        question_limit=settings.chat_question_limit,
        demo_unlimited=settings.chat_demo_unlimited,
    )
