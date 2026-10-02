"""Export public catalogue coverage, source policy and asset provenance, excluding accounts."""

import hashlib
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import ImportJob, SourceRegistry, VehicleAsset  # noqa: E402
from app.services.catalog_buyer import coverage, fact_value, records  # noqa: E402
from sqlalchemy import select  # noqa: E402

OUT = ROOT / "deliverables/MasterLocal"
OUT.mkdir(parents=True, exist_ok=True)


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


with SessionLocal() as db:
    rows = records(db)
    write("catalogue-coverage.json", coverage(db, rows))
    families = defaultdict(list)
    for _, c in rows:
        families[(c["make"].casefold(), c["model"].casefold())].append(c)
    matrix = []
    for cars in families.values():
        first = cars[0]
        matrix.append(
            {
                "make": first["make"],
                "model": first["model"],
                "versions": len(cars),
                "markets": sorted({c["original_market"] for c in cars}),
                "years": sorted({c["model_year"] for c in cars}),
                "verified_generations": sorted(
                    {c["generation"] for c in cars if c.get("generation")}
                ),
                "confirmed_fields": {
                    key: sum(fact_value(c, key) is not None for c in cars)
                    for key in (
                        "body",
                        "engine_displacement",
                        "transmission_family",
                        "drivetrain",
                        "fuel_combined",
                        "electricity_combined",
                        "seats",
                        "ground_clearance",
                    )
                },
                "technical_reliability": "INSUFFICIENT_DATA",
                "az_market": "INSUFFICIENT_DATA",
                "image": "IMAGE_QA",
                "az_ru": "FACTUAL_TEMPLATE_AVAILABLE",
                "last_publication": max(c["published_at"] for c in cars),
                "publication_scopes": sorted({c["publication_scope"] for c in cars}),
                "fully_supported_dossier": False,
            }
        )
    write("coverage-matrix.json", sorted(matrix, key=lambda r: (r["make"], r["model"])))
    allowed = {
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
        "access",
        "cost_model",
        "verified_rate_limit",
        "request_budget",
        "research_provider_ids",
        "freshness_days",
        "last_acquired_at",
        "last_successful_publication_at",
        "limitations",
    }
    write(
        "source-registry.json",
        [
            {
                "id": s.id,
                "title": s.title,
                "state": s.state,
                "paused": s.paused,
                **{k: v for k, v in s.config.items() if k in allowed},
            }
            for s in db.scalars(select(SourceRegistry))
        ],
    )
    jobs = list(db.scalars(select(ImportJob)))
    write(
        "acquisition-economics.json",
        {
            "at": datetime.now(UTC).isoformat(),
            "provider_paid_calls": 0,
            "provider_cost": "0.00",
            "currency": "USD",
            "bulk_download_attempts": sum(j.metrics.get("network_attempts", 0) for j in jobs),
            "successful_bulk_downloads": sum(j.metrics.get("network_calls", 0) for j in jobs),
            "rate_limit": "UNVERIFIED: no throughput claim; one cached public dataset",
            "new_autodev_calls": 0,
            "new_vin_history_calls": 0,
            "local_cached_normalization": True,
        },
    )
    art = ROOT / "apps/web_preview/assets/buyer-road.svg"
    write(
        "asset-manifest.json",
        {
            "catalogue_assets": [
                {
                    "id": a.id,
                    "state": a.state,
                    "sha256": a.sha256,
                    "version": a.version,
                    "applicability": a.applicability,
                    "commercial_reuse": a.rights.get("commercial_reuse", False),
                }
                for a in db.scalars(select(VehicleAsset))
            ],
            "decorative_assets": [
                {
                    "path": "apps/web_preview/assets/buyer-road.svg",
                    "sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
                    "origin": "PROJECT_ORIGINAL_SVG",
                    "purpose": "Generic decorative car and city illustration; "
                    "no exact model or VIN applicability",
                    "is_vehicle_evidence": False,
                }
            ],
            "approved_vehicle_images": sum(
                a.state == "APPROVED" and bool(a.rights.get("commercial_reuse"))
                for a in db.scalars(select(VehicleAsset))
            ),
            "blocker": "No licensed and verified generation/facelift references approved; "
            "neutral placeholders are intentional.",
        },
    )
print(f"Exported {len(matrix)} family coverage rows; account/session metadata excluded")
