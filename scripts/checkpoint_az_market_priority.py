# ruff: noqa: E501
"""Public, reproducible per-model checkpoint; no user/account/session identifiers."""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402
from app.services.market_priority import current_queue  # noqa: E402


def main():
    output = ROOT / "deliverables/VerifiedData/market-priority"
    output.mkdir(parents=True, exist_ok=True)
    batch = (
        json.loads((output / "batch-status.json").read_text())
        if (output / "batch-status.json").exists()
        else {"jobs": []}
    )
    latest = {(r["make"], r["model"]): r for r in batch["jobs"]}
    with SessionLocal() as db:
        source = db.get(SourceRegistry, "turbo-market-reference")
        if source is None:
            db.add(
                SourceRegistry(
                    id="turbo-market-reference",
                    title="Turbo.az · manual local market reference",
                    state="REFERENCE_ONLY",
                    config={
                        "owner": "Digital Classifieds MMC",
                        "markets": ["AZ"],
                        "data_types": ["manual_market_reference"],
                        "documentation_url": "https://turbo.az/",
                        "rights_url": "https://turbo.az/pages/terms-and-conditions",
                        "checked_at": "2026-09-20",
                        "automation": "DISABLED_BY_OWNER",
                        "ingestion": "NOT_REQUIRED_NO_EXPORT_AVAILABLE",
                        "commercial_reuse": False,
                        "allowed_download_urls": [],
                        "research_provider_ids": [],
                        "cost_model": "NO_AUTOMATED_CALLS",
                        "count_freshness": None,
                        "limitations": "Terms 2.20/2.21.2 require written permission for automated access/copying; owner selected brands manually; counts not collected.",
                    },
                )
            )
            db.commit()
        q = current_queue(db)
    for row in q["models"]:
        r = latest.get((row["make"], row["model"]))
        row["batch_result"] = (
            {
                k: r.get(k)
                for k in ("job_id", "year", "status", "calls", "source_identity", "errors")
            }
            if r
            else {"status": "NOT_RUN"}
        )
        if r:
            row["technical_source_coverage"]["batch_providers"] = [
                {
                    k: s.get(k)
                    for k in ("provider_id", "status", "records_count", "from_cache", "http_status")
                }
                for s in r.get("provider_steps", [])
                if s["provider_id"] != "none"
            ]
            row["dossier_status"] = "RESEARCH_RESULT_REQUIRES_EDITORIAL_REVIEW_NOT_FULL"
    q["batch_summary"] = {
        "attempts": len(batch["jobs"]),
        "models_attempted": len(latest),
        "latest_model_statuses": dict(Counter(r["status"] for r in latest.values())),
        "request_attempts_recorded": sum(r.get("calls", 0) for r in batch["jobs"]),
        "receipted_http_requests": sum(
            s.get("network_calls", 0)
            for r in batch["jobs"] for s in r.get("source_requests", [])
        ),
        "additional_isolated_diagnostic_attempts": 8,
        "accounting_note": "Attempt counters include failures before HTTP; early receipts lack HTTP status. Diagnostic total is from two isolated runs; only one has full receipts. Web-reader transport counts are unavailable.",
        "paid_calls": 0,
        "running_status": batch.get("status", "NOT_RUN"),
    }
    (output / "az-market-queue.json").write_text(
        json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "data/manifests/az-market-batch-queue.json").write_text(
        json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Azerbaijan market priority — local checkpoint",
        "",
        "Priority brands are owner-selected. No Turbo export exists or is awaited; no crawler was built or run.",
        "Turbo listing counts and market shares below are unknown optional manual inputs, not zero.",
        "First US wave uses published US source configurations. Model order is an editorial draft, not measured local popularity.",
        "Skoda remains prioritized for appropriate non-US factory sources; no US version is invented.",
        "",
        "Research COMPLETE means the existing worker finished a result; it does not mean a full verified dossier.",
        "Recalls, complaints and manufacturer communications remain distinct. HTTP errors do not establish absence.",
        "One official source-year per family was attempted, not all years/trims. Complaint samples are capped at 100 records and cannot establish prevalence or reliability rates.",
        "Batch summary: " + json.dumps(q["batch_summary"], ensure_ascii=False),
        "",
        "| Make | Model | Turbo count | Market distribution | US basis | Technical coverage | Verification / dossier |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in q["models"]:
        providers = r["technical_source_coverage"].get("batch_providers", [])
        coverage = ", ".join(
            f"{p['provider_id']}: {p['status']} / {p['records_count']}" for p in providers
        ) or str(r["technical_source_coverage"].get("source_rows_by_market", {}))
        values = [
            r["make"],
            r["model"],
            "unknown",
            "not collected",
            r["us_variant_present"],
            coverage,
            r["batch_result"]["status"] + "; " + r["verification_status"] + "; " + r["dossier_status"],
        ]
        lines.append("| " + " | ".join(str(v).replace("|", "/") for v in values) + " |")
    lines += [
        "",
        "## Resume",
        "",
        "```powershell",
        ".venv\\Scripts\\python.exe scripts/run_az_priority_batch.py --run-free --max-models 52 --max-jobs 52",
        "# Next source-year wave, after reviewing current results:",
        ".venv\\Scripts\\python.exe scripts/run_az_priority_batch.py --run-free --year-wave 1 --max-models 12 --max-jobs 12",
        ".venv\\Scripts\\python.exe scripts/checkpoint_az_market_priority.py",
        "```",
        "",
        "Existing jobs and checksummed shared NHTSA archives are reused. Results are retained in batch-status.json; reruns skip completed model/year entries.",
        "Exact Turbo counts/secondary US prevalence remain optional manual research work; they are not a blocker for these seven brands.",
        "Next correctness work: review source-specific model labels, failed jobs and unresolved variant candidates before publishing new technical conclusions.",
    ]
    (ROOT / "docs/CHECKPOINT_AZ_MARKET_PRIORITY.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(q["batch_summary"]))


if __name__ == "__main__":
    main()
