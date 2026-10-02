# ruff: noqa: E501
"""Use the existing free worker for owner-prioritized US configurations."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.providers.official_nhtsa import (  # noqa: E402
    OfficialProviderUnavailable,
    VPICVehicleProvider,
)
from app.schemas.research import ResearchJobCreate, VehicleResearchRequest  # noqa: E402
from app.services.catalog_buyer import records  # noqa: E402
from app.services.catalog_research import (  # noqa: E402
    enqueue_research,
    retry_failed_research,
    work_research,
)
from app.services.market_priority import current_queue, policy  # noqa: E402
from app.services.priority_research_http import PriorityHTTP  # noqa: E402
from app.services.priority_source_identity import source_model  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-free",
        action="store_true",
        help="Execute existing free providers; otherwise only plan",
    )
    parser.add_argument("--max-models", type=int, default=10, choices=range(1, 101))
    parser.add_argument("--max-jobs", type=int, default=20, choices=range(1, 101))
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--year-wave", type=int, default=0, choices=range(0, 12))
    args = parser.parse_args()
    if policy().get("work_mode") == "BUILD_BASE_CATALOG":
        raise SystemExit(
            "Use scripts/run_base_catalog_batch.py and active_catalog_manifest. Single-year discovery waves are inactive during basic catalogue construction."
        )
    if policy().get("work_mode") in {"VERIFY_EXISTING_51", "VERIFY_LOCAL_USABLE_FAMILIES"}:
        raise SystemExit(
            "Research expansion is frozen. Continue active_verification_manifest from data/manifests/az-market-priority-policy.json; BMW MY2025 is pipeline proof only."
        )
    output = ROOT / "deliverables/VerifiedData/market-priority/batch-status.json"
    if not args.run_free:
        output = output.with_name("batch-plan.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = (
        json.loads(output.read_text()).get("jobs", []) if output.exists() and args.run_free else []
    )
    seen = {
        (r["make"], r["model"], r.get("year"))
        for r in completed
        if not (
            args.retry_failed
            and r["status"] in {"FAILED", "SOURCE_MODEL_UNRESOLVED", "SOURCE_UNAVAILABLE"}
        )
    }
    new_jobs = 0
    with SessionLocal() as db:
        queue = current_queue(db)  # Never execute a stale file edited to inflate local prevalence.
        candidates = queue["PRIMARY_US_MARKET_QUEUE"] + queue["SECONDARY_US_MARKET_QUEUE"]
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        catalogue = [c for _, c in records(db)]
        model_count = 0
        for member in candidates:
            if member["batch_status"] != "READY_FOR_US_DISCOVERY":
                continue
            if model_count >= args.max_models or new_jobs >= args.max_jobs:
                break
            years = member.get("research_model_years") or member["market_distribution"][
                "observed_model_years"
            ].get("US", [])
            if not years:
                completed.append(
                    {
                        "make": member["make"],
                        "model": member["model"],
                        "status": "OBSERVED_US_MODEL_YEAR_REQUIRED",
                    }
                )
            # First wave: one source-backed used-car model-year per family, then resume later waves.
            ordered_years = sorted(years, key=lambda y: (abs(y - 2020), y))[
                args.year_wave : args.year_wave + 1
            ]
            for year in ordered_years:
                key = (member["make"], member["model"], year)
                if key in seen or year < 1981 or new_jobs >= args.max_jobs:
                    continue
                seen.add(key)
                model_count += 1
                new_jobs += 1
                result = {
                    "make": key[0],
                    "model": key[1],
                    "year": year,
                    "market_basis": member.get(
                        "research_year_basis", "SELLER_CLAIM_VERIFY_WITH_OFFICIAL_SOURCES"
                    ),
                    "status": "PLANNED",
                    "discovery_revision": member["revision_id"],
                }
                if args.run_free:
                    from app.core.config import get_settings

                    # Enable only this explicitly requested CLI worker, not the public app process.
                    get_settings().knowledge_worker_enabled = True
                    if actor is None:
                        raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
                    lookup = PriorityHTTP()
                    request = VehicleResearchRequest(
                        make=key[0], model=key[1], year=year, market="USA"
                    )
                    try:
                        lookup_url = VPICVehicleProvider(lookup).source_url(request)
                        data, _ = lookup.get_json(lookup_url)
                        identity = source_model(
                            key[0], key[1], year, data.get("Results", []), catalogue
                        )
                        result["source_identity"] = identity
                        result["identity_source_url"] = lookup_url
                    except OfficialProviderUnavailable:
                        identity = None
                        result["status"] = "SOURCE_UNAVAILABLE"
                    finally:
                        lookup.client.close()
                    if identity is None:
                        result.update(
                            status="SOURCE_MODEL_UNRESOLVED"
                            if result["status"] == "PLANNED"
                            else result["status"],
                            calls=lookup.used,
                            source_requests=lookup.receipts,
                        )
                        completed.append(result)
                        output.write_text(
                            json.dumps(
                                {"jobs": completed, "status": "RUNNING", "paid_calls": 0}, indent=2
                            ),
                            encoding="utf-8",
                        )
                        continue
                    value = ResearchJobCreate(
                        vehicle=VehicleResearchRequest(
                            make=identity["make"], model=identity["model"], year=year, market="USA"
                        ),
                        language="ru",
                    )
                    job = enqueue_research(db, actor, value)
                    if args.retry_failed:
                        retry_failed_research(db, job)
                    clients = []

                    def http_factory(clients=clients, **kw):
                        client = PriorityHTTP(**kw)
                        clients.append(client)
                        return client

                    job = work_research(db, job.id, http_factory=http_factory)
                    result.update(
                        job_id=job.id,
                        status=job.status.value,
                        calls=lookup.used + sum(c.used for c in clients),
                        publication=job.metrics.get("publication", "STAGING"),
                    )
                    result["shared_cache_hits"] = lookup.cache_hits + sum(
                        c.cache_hits for c in clients
                    )
                    result["source_requests"] = lookup.receipts + [
                        r for c in clients for r in c.receipts
                    ]
                    result["provider_steps"] = job.provider_steps
                    result["errors"] = job.errors
                completed.append(result)
                output.write_text(
                    json.dumps({"jobs": completed, "status": "RUNNING", "paid_calls": 0}, indent=2),
                    encoding="utf-8",
                )
        result = {
            "status": "NO_ELIGIBLE_LOCAL_EVIDENCE"
            if not candidates
            else "BATCH_PROCESSED"
            if args.run_free
            else "PLAN_ONLY",
            "jobs": completed,
            "eligible_models": len(candidates),
            "new_jobs_this_run": new_jobs,
            "year_wave": args.year_wave,
            "paid_calls": 0,
            "other_markets": "Preserved in PRIMARY_OTHER_MARKET_QUEUE; market-specific adapters required",
            "publication": "REVIEW_REQUIRED_NO_AUTOMATIC_KNOWN_ISSUES",
        }
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": result["status"], "jobs": len(completed), "paid_calls": 0}))


if __name__ == "__main__":
    main()
