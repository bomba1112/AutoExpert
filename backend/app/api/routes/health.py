from fastapi import APIRouter
from sqlalchemy import text

from app.api.dependencies import DBSession

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DBSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
