from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import CurrentUser, DBSession
from app.providers.analytics import ALLOWED_EVENTS, DatabaseAnalyticsProvider
from app.schemas.analytics import AnalyticsEventCreate

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
def record_event(value: AnalyticsEventCreate, db: DBSession, user: CurrentUser) -> Response:
    if value.event_name not in ALLOWED_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported analytics event",
        )
    DatabaseAnalyticsProvider(db).track(
        value.event_name,
        user_id=user.id,
        anonymous_id=None,
        properties=value.properties,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
