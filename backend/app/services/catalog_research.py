"""Durable fallback on existing ResearchJob; explicit opt-in, bounded free providers."""

import time
import traceback
from datetime import timedelta
from pathlib import Path

from sqlalchemy import or_, select, update

from app.core.config import get_settings
from app.models.enums import ProviderCostModel, ResearchJobStatus
from app.models.knowledge_ops import SourceRegistry
from app.models.research import ResearchJob
from app.providers.official_nhtsa import OfficialHTTPClient, OfficialProviderUnavailable
from app.schemas.research import ResearchJobCreate
from app.services.knowledge_registry import utcnow
from app.services.provider_registry import ProviderRegistry, default_provider_registry
from app.services.research_pipeline import ResearchPipeline, _request_key
from app.services.research_rights import permitted_research_registry


class BudgetHTTP(OfficialHTTPClient):
    def __init__(self, cancelled=lambda: False):
        super().__init__(timeout_seconds=8, max_attempts=1, max_response_bytes=8 * 1024 * 1024)
        self.started = time.monotonic()
        self.used = 0
        self.cancelled = cancelled

    def _request(self, url, *, headers=None):
        if self.cancelled():
            raise OfficialProviderUnavailable("RESEARCH_CANCELLED", api_requests=0)
        if self.used >= 12 or time.monotonic() - self.started >= 90:
            raise OfficialProviderUnavailable("RESEARCH_BUDGET_EXHAUSTED", api_requests=0)
        self.used += 1
        return super()._request(url, headers=headers)


def permitted_registry(db, http):
    """Only explicitly registered providers; pause and production rights apply to research too."""
    allowed = set()
    for source in db.scalars(select(SourceRegistry)):
        if source.paused or source.state not in {"APPROVED", "LOCAL_RESEARCH", "EXISTING_ADAPTER"}:
            continue
        if get_settings().environment == "production" and not source.config.get("commercial_reuse"):
            continue
        allowed.update(source.config.get("research_provider_ids", []))
    return permitted_research_registry(
        db,
        ProviderRegistry(
            [
                p
                for p in default_provider_registry(http=http).providers
                if p.definition.id in allowed
                and p.definition.cost_model == ProviderCostModel.FREE
                and not p.definition.requires_api_key
            ]
        ),
    )


def enqueue_research(db, user, value: ResearchJobCreate):
    if not get_settings().knowledge_worker_enabled:
        raise ValueError("RESEARCH_WORKER_NOT_CONFIGURED")
    key = _request_key(value.vehicle)
    existing = db.scalar(
        select(ResearchJob)
        .where(
            ResearchJob.user_id == user.id,
            ResearchJob.request_key == key,
            ResearchJob.worker_queue == "CATALOG_REVIEW",
            ResearchJob.language == value.language,
            ResearchJob.created_at >= utcnow() - timedelta(days=1),
        )
        .order_by(ResearchJob.created_at.desc())
    )
    if existing:
        return existing
    # Existing provider construction is deferred until the worker claims the job.
    job = ResearchPipeline(db, ProviderRegistry([])).create_job(user_id=user.id, value=value)
    job.worker_queue = "CATALOG_REVIEW"
    job.metrics = {
        "queue_kind": "CATALOG_REVIEW",
        "attempts": 0,
        "request_budget": 12,
        "time_budget_seconds": 90,
        "money_budget": "0",
        "publication": "STAGING",
    }
    db.commit()
    return job


def retry_failed_research(db, job):
    """Explicit bounded retry; preserve the prior failure without duplicating jobs."""
    if (
        job.worker_queue != "CATALOG_REVIEW"
        or job.status != ResearchJobStatus.FAILED
        or job.cancel_requested
        or job.worker_attempts >= 2
    ):
        return False
    job.metrics = {
        **job.metrics,
        "retry_history": [
            *job.metrics.get("retry_history", []),
            {
                "attempt": job.worker_attempts,
                "errors": list(job.errors),
                "network_calls": job.metrics.get("network_calls"),
                "worker_failure": job.metrics.get("worker_failure"),
            },
        ],
    }
    job.status = ResearchJobStatus.QUEUED
    job.completed_at = None
    job.worker_lease_until = None
    db.commit()
    return True


def work_research(db, job_id, *, http_factory=None):
    job = db.get(ResearchJob, job_id)
    if not job or job.worker_queue != "CATALOG_REVIEW":
        return None
    metrics = dict(job.metrics)
    if job.cancel_requested or job.worker_attempts >= 2:
        job.status = ResearchJobStatus.FAILED
        job.errors = ["CANCELLED" if job.cancel_requested else "RETRY_BUDGET_EXHAUSTED"]
        db.commit()
        return job
    claimed = db.execute(
        update(ResearchJob)
        .where(
            ResearchJob.id == job_id,
            or_(
                ResearchJob.status == ResearchJobStatus.QUEUED,
                (ResearchJob.status == ResearchJobStatus.RUNNING)
                & (ResearchJob.worker_lease_until < utcnow()),
            ),
            ResearchJob.cancel_requested.is_(False),
        )
        .values(
            status=ResearchJobStatus.RUNNING,
            worker_lease_until=utcnow() + timedelta(minutes=3),
            worker_attempts=ResearchJob.worker_attempts + 1,
            started_at=utcnow(),
        )
    )
    db.commit()
    if not claimed.rowcount:
        return job
    http = (http_factory or BudgetHTTP)(
        cancelled=lambda: bool(
            db.scalar(select(ResearchJob.cancel_requested).where(ResearchJob.id == job_id))
        )
    )
    try:
        free = permitted_registry(db, http)
        if not free.providers:
            raise ValueError("NO_PERMITTED_RESEARCH_SOURCE")
        job = ResearchPipeline(db, free).execute(job)
        db.refresh(job)
        if job.cancel_requested:
            job.status = ResearchJobStatus.FAILED
            job.errors = ["CANCELLED"]
        job.worker_lease_until = None
        job.metrics = {
            **job.metrics,
            **metrics,
            "attempts": job.worker_attempts,
            "network_calls": http.used,
            "publication": "REVIEW_REQUIRED",
        }
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(ResearchJob, job_id)
        job.status = ResearchJobStatus.FAILED
        job.worker_lease_until = None
        job.errors = [
            "NO_PERMITTED_RESEARCH_SOURCE"
            if str(exc) == "NO_PERMITTED_RESEARCH_SOURCE"
            else "WORKER_FAILED"
        ]
        job.metrics = {
            **metrics,
            "network_calls": http.used,
            "publication": "STAGING",
            "worker_failure": {
                "type": type(exc).__name__,
                "frames": [
                    {
                        "file": Path(frame.filename).name,
                        "line": frame.lineno,
                        "function": frame.name,
                    }
                    for frame in traceback.extract_tb(exc.__traceback__)[-6:]
                ],
            },
        }
        db.commit()
    finally:
        http.client.close()
    return job
