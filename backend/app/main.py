from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.8.1",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )
    # Source-backed search cards repeat provenance; compress transport without
    # removing evidence or changing the public result set.
    application.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-AutoExpert-Simulate-Paywall",
        ],
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    from fastapi.responses import JSONResponse

    from app.services.entitlements import SubscriptionRequired

    @application.exception_handler(SubscriptionRequired)
    async def subscription_required(request: Request, exc: SubscriptionRequired):  # type: ignore[no-untyped-def]
        detail = {"code": "SUBSCRIPTION_REQUIRED", "feature": exc.feature}
        return JSONResponse(status_code=402, content={"detail": detail})

    from app.services import garage as garage_service
    from app.services import public_pages

    site = Path(settings.public_site_dir) / "cars"
    if public_pages.enabled(settings) and site.is_dir():
        application.mount("/cars", StaticFiles(directory=site, html=True), name="public-car-pages")

    if settings.garage_recall_job and garage_service.enabled(settings):
        from app.db.session import SessionLocal
        from app.services.garage_recalls import start_daily

        start_daily(SessionLocal)
    web_preview = Path(__file__).resolve().parents[2] / "apps" / "web_preview"
    if web_preview.is_dir():
        application.mount(
            "/preview",
            StaticFiles(directory=web_preview, html=True),
            name="web-preview",
        )

        @application.get("/", include_in_schema=False)
        def preview_redirect() -> RedirectResponse:
            return RedirectResponse(url="/preview/")

        @application.middleware("http")
        async def secure_web_preview(request: Request, call_next):  # type: ignore[no-untyped-def]
            response = await call_next(request)
            if request.url.path.startswith("/preview"):
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: blob: https:; connect-src 'self'; object-src 'none'; "
                    "base-uri 'self'; frame-ancestors 'none'"
                )
                response.headers["Referrer-Policy"] = "no-referrer"
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                if request.url.path.endswith("/") or request.url.path.endswith("index.html"):
                    response.headers["Cache-Control"] = "no-store"
                elif request.url.path.endswith((".js", ".css", ".json")):
                    response.headers["Cache-Control"] = "no-cache"
            return response

    return application


app = create_app()
