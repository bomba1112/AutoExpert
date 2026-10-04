from fastapi import APIRouter

from app.api.routes import (
    analysis,
    analytics,
    auth,
    buyer,
    catalog,
    chat,
    garage,
    health,
    history_flow,
    knowledge,
    listing_intake,
    meta,
    reports,
    research,
    vin,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(analytics.router)
api_router.include_router(catalog.router)
api_router.include_router(knowledge.router)
api_router.include_router(meta.router)
api_router.include_router(analysis.router)
api_router.include_router(buyer.router)
api_router.include_router(reports.router)
api_router.include_router(vin.router)
api_router.include_router(history_flow.router)
api_router.include_router(listing_intake.router)
api_router.include_router(chat.router)
api_router.include_router(garage.router)
api_router.include_router(research.router)
