"""Public factual exports and reproducible scenario samples; no accounts or private reports."""
# ruff: noqa: E501

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import ImportJob, SourceRegistry, VehicleAsset  # noqa: E402
from app.schemas.knowledge import CatalogRecord, ImportManifest  # noqa: E402
from app.schemas.verified_ownership import OwnershipScenario  # noqa: E402
from app.services.catalog_buyer import coverage, records  # noqa: E402
from app.services.ownership_cost import calculate  # noqa: E402
from app.services.ownership_evidence import available  # noqa: E402
from sqlalchemy import select  # noqa: E402

OUT = ROOT / "deliverables/VerifiedData"
DATA = OUT / "published-data"
DATA.mkdir(parents=True, exist_ok=True)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


with SessionLocal() as db:
    rows = records(db)
    write(OUT / "catalogue-coverage.json", coverage(db, rows))
    groups = defaultdict(list)
    for _, c in rows:
        payload = {k: c[k] for k in CatalogRecord.model_fields if k in c}
        payload["facts"] = {
            key: {
                k: value
                for k, value in fact.items()
                if k in {"value", "unit", "status", "locator", "source_date", "labels", "titles"}
            }
            for key, fact in c["facts"].items()
        }
        # Source facts only; no account, VIN, reports, sessions, or original acquisition headers.
        groups[c["source_registry_id"]].append(CatalogRecord.model_validate(payload))
    for source_id, data in groups.items():
        manifest = ImportManifest(
            source_id=source_id,
            parser="manifest-json-v1",
            records=data,
            selection_basis="Portable normalized published source facts; preserve original market and source locators; review again before publication",
        )
        write(DATA / (source_id + "-catalog.json"), manifest.model_dump(mode="json"))
    ownership = available(db)
    for sid in {r.source_id for r in ownership}:
        manifest = ImportManifest(
            source_id=sid,
            parser="ownership-json-v1",
            ownership_records=[r.payload for r in ownership if r.source_id == sid],
            selection_basis="Portable dated ownership evidence; local scope and rights preserved",
        )
        write(DATA / (sid + "-ownership.json"), manifest.model_dump(mode="json"))
    source_keys = {
        "owner",
        "markets",
        "data_types",
        "documentation_url",
        "adapter",
        "checked_at",
        "commercial_reuse",
        "rights",
        "rights_url",
        "storage_rights",
        "display_rights",
        "resale_rights",
        "authentication",
        "cost_model",
        "verified_rate_limit",
        "freshness_days",
        "limitations",
        "attribution",
    }
    sources = [
        {
            "id": s.id,
            "title": s.title,
            "state": s.state,
            "paused": s.paused,
            "config": {k: v for k, v in s.config.items() if k in source_keys},
        }
        for s in db.scalars(select(SourceRegistry))
    ]
    write(OUT / "source-registry.json", sources)
    write(
        DATA / "source-registry.json",
        [s for s in sources if s["id"] in {*groups, *(r.source_id for r in ownership)}],
    )
    sample_groups = {}
    for variant, c in rows:
        power = c["facts"].get("powertrain", {}).get("value")
        key = (c["original_market"], power)
        if key not in sample_groups:
            sample_groups[key] = (variant, c)
    samples = []
    for (market, power), (v, c) in sorted(sample_groups.items()):
        grade = c["facts"].get("fuel_grade", {}).get("value", "")
        fuel = (
            "DIESEL"
            if c["facts"].get("fuel", {}).get("value") == "DIESEL"
            else "AI95"
            if "Premium" in grade
            else "AI92"
        )
        s = OwnershipScenario(
            start_date=date(2026, 9, 20),
            months=24,
            monthly_km=1000,
            current_odometer_km=75000,
            fuel_energy=fuel,
            consumption_side="GRID",
            household_monthly_kwh=150,
            electric_distance_share="0.5" if power in {"PHEV", "EREV"} else None,
        )
        result = calculate(db, v, c, s)
        samples.append(
            {
                "variant_id": v.id,
                "market": market,
                "powertrain": power,
                "sample_basis": "One existing published row per market/powertrain category. Odometer, grid measurement, household load, grade and PHEV share are explicit test scenario assumptions, not observed vehicle facts.",
                "calculation": result,
            }
        )
    write(OUT / "calculation-snapshots.json", samples)
    jobs = [
        {
            "id": j.id,
            "source_id": j.source_id,
            "state": j.state,
            "cursor": j.cursor,
            "metrics": j.metrics,
            "errors": j.errors,
        }
        for j in db.scalars(select(ImportJob))
    ]
    write(OUT / "import-status.json", jobs)
    matrix = json.loads((OUT / "coverage-after.json").read_text(encoding="utf-8"))
    queue_path = ROOT / "data/manifests/verified-data-work-queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue["execution_checkpoint"] = {
        "at": "2026-09-20",
        "published_rows": len(rows),
        "markets": sorted({c["original_market"] for _, c in rows}),
        "next_step": "Source-scoped factory generation/aggregate/service evidence, NHTSA safety batch adapter and technical dossier publication. Do not rerun cached successful downloads.",
        "family_market_coverage": matrix,
    }
    write(queue_path, queue)
    counts = Counter(r.kind for r in ownership)
    summary = {
        "catalogue": coverage(db, rows),
        "ownership_records": dict(counts),
        "maintenance_schedules": counts["MAINTENANCE"],
        "confirmed_fitments": counts["FITMENT"],
        "price_observations": counts["PART_PRICE"],
        "labor_quotes": counts["LABOR"],
        "calculations_sampled": len(samples),
        "calculation_statuses": dict(Counter(s["calculation"]["status"] for s in samples)),
        "images_stored": len(list(db.scalars(select(VehicleAsset.id)))),
        "new_paid_calls": 0,
        "new_paid_cost_usd": "0.00",
        "overall": "PARTIAL",
    }
    write(OUT / "data-summary.json", summary)
    ledger = json.loads((OUT / "acquisition-ledger.json").read_text())
    attempts = sum(
        1
        + len(r.get("redirects", []))
        - int(bool(r.get("redirects")) and r.get("http_status") in {301, 302, 303, 307, 308})
        for r in ledger
    )
    write(
        OUT / "acquisition-economics.json",
        {
            "logged_direct_request_attempts": attempts,
            "additional_readonly_redirect_diagnostic": 1,
            "successful_final_responses": sum(r.get("http_status") == 200 for r in ledger),
            "web_reader_requests": "Separate search/open/click discovery calls; transport count unavailable",
            "paid_calls": 0,
            "cost_usd": "0.00",
            "rate_limit": "Provider limits unverified; local sequential requests, 0.5 second spacing, max 2 attempts, 25 second timeout, 20 MB cap",
            "new_autodev_calls": 0,
            "new_vin_history_calls": 0,
        },
    )
print(
    json.dumps(
        {
            "catalogue_rows": len(rows),
            "ownership_records": dict(counts),
            "sample_calculations": len(samples),
        }
    )
)
