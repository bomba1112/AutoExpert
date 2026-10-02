from sqlalchemy.orm import Session

from app.models.analytics import AnalyticsEvent

ALLOWED_EVENTS = {
    "app_open",
    "language_selected",
    "analysis_started",
    "vehicle_completed",
    "usage_profile_completed",
    "preview_generated",
    "paywall_viewed",
    "payment_started",
    "payment_success",
    "report_opened",
    "pdf_generated",
    "pdf_downloaded",
    "followup_question_used",
    "second_analysis_started",
}


class DatabaseAnalyticsProvider:
    def __init__(self, session: Session):
        self.session = session

    def track(
        self,
        event_name: str,
        *,
        user_id: str | None,
        anonymous_id: str | None,
        properties: dict,
    ) -> None:
        if event_name not in ALLOWED_EVENTS:
            raise ValueError(f"Unknown analytics event: {event_name}")
        self.session.add(
            AnalyticsEvent(
                event_name=event_name,
                user_id=user_id,
                anonymous_id=anonymous_id,
                properties=properties,
            )
        )
