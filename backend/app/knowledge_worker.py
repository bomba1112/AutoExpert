"""Run with python -m app.knowledge_worker [--once] [--job ID]."""

import argparse
import time

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import ResearchJobStatus
from app.models.knowledge_ops import ImportJob
from app.models.research import ResearchJob
from app.services.catalog_research import work_research
from app.services.knowledge_import import process_job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--job")
    args = parser.parse_args()
    if not args.once and not get_settings().knowledge_worker_enabled:
        raise SystemExit(
            "Configure AUTOEXPERT_KNOWLEDGE_WORKER_ENABLED=true before starting worker"
        )
    while True:
        with SessionLocal() as db:
            ids = (
                [args.job]
                if args.job
                else list(
                    db.scalars(
                        select(ImportJob.id)
                        .where(ImportJob.state.in_(["QUEUED", "RUNNING"]))
                        .order_by(ImportJob.created_at)
                        .limit(10)
                    )
                )
            )
            for job_id in ids:
                job = process_job(db, job_id)
                print({"job_id": job_id, "state": job.state, "processed": job.cursor}, flush=True)
            if not args.job:
                research_ids = list(
                    db.scalars(
                        select(ResearchJob.id)
                        .where(
                            ResearchJob.status.in_(
                                [ResearchJobStatus.QUEUED, ResearchJobStatus.RUNNING]
                            ),
                            ResearchJob.worker_queue == "CATALOG_REVIEW",
                        )
                        .order_by(ResearchJob.created_at)
                        .limit(1)
                    )
                )
                for research_id in research_ids:
                    result = work_research(db, research_id)
                    print({"research_job_id": research_id, "state": result.status}, flush=True)
        if args.once:
            return
        time.sleep(5)


if __name__ == "__main__":
    main()
