from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DBSession
from app.repositories.vehicles import VehicleNotResolvedError
from app.schemas.analysis import AnalysisCreate, PreviewResponse
from app.services.report_pipeline import ReportPipeline

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/preview", response_model=PreviewResponse, status_code=status.HTTP_201_CREATED)
def create_preview(value: AnalysisCreate, db: DBSession, user: CurrentUser) -> PreviewResponse:
    try:
        return ReportPipeline(db).create_preview(user, value)
    except VehicleNotResolvedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
