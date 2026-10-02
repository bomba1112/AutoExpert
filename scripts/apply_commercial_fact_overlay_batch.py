"""Validate and optionally apply the reviewed fact-overlay JSONL without touching EPA rows.

Default is read-only preflight. ``--apply`` uses the existing application
upsert service under the catalogue writer lock, committing bounded chunks so
an interrupted run can be resumed idempotently.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.knowledge_ops import CommercialFactClaim, SourceRegistry  # noqa: E402
from app.services.commercial_fact_overlay import (  # noqa: E402
    claim_valid_for_candidate,
    upsert_claim,
)
from catalog_writer_lock import catalog_writer_lock  # noqa: E402

DEFAULT_DB = ROOT / "autoexpert.db"
DEFAULT_PLAN = (
    ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01/factory-fact-claims-dry-run.jsonl"
)
DEFAULT_REPORT = (
    ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01/factory-claim-application.json"
)
ARGUMENTS = (
    "variant_id",
    "fact_name",
    "value",
    "source_id",
    "evidence_scope",
    "reuse_status",
    "source_url",
    "locator",
    "rights_basis",
    "rights_reference",
    "rights_checked_at",
    "unit",
)


def read_plan(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    if not rows:
        raise ValueError("EMPTY_CLAIM_PLAN")
    keys = [(row["variant_id"], row["fact_name"], row["source_id"], row["locator"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_CLAIM_PLAN_KEY")
    return rows


def preflight(db: Session, rows: list[dict]) -> dict:
    sources = {row.id: row for row in db.scalars(select(SourceRegistry))}
    variant_ids = {row["variant_id"] for row in rows}
    variants = {
        row.id: (row.specifications or {}).get("catalog") or {}
        for row in db.scalars(select(VehicleVariant).where(VehicleVariant.id.in_(variant_ids)))
    }
    errors = []
    counts = Counter()
    for row in rows:
        counts[row["reuse_status"]] += 1
        catalog = variants.get(row["variant_id"])
        if not catalog or not row.get("catalog_key", "").startswith("factory-"):
            errors.append(
                (row.get("catalog_key"), row["fact_name"], "NON_FACTORY_OR_MISSING_VARIANT")
            )
            continue
        if catalog.get("source_registry_id") != row["source_id"]:
            errors.append((row["catalog_key"], row["fact_name"], "SOURCE_MISMATCH"))
            continue
        if row["source_id"] not in sources:
            errors.append((row["catalog_key"], row["fact_name"], "SOURCE_NOT_REGISTERED"))
            continue
        if row["reuse_status"] == "COMMERCIAL_OK":
            claim = SimpleNamespace(**{name: row.get(name) for name in ARGUMENTS})
            if not claim_valid_for_candidate(claim, catalog, sources[row["source_id"]]):
                errors.append(
                    (
                        row["catalog_key"],
                        row["fact_name"],
                        "RUNTIME_RIGHTS_OR_APPLICABILITY_REJECTED",
                    )
                )
    return {
        "plan_claims": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "unique_variants": len(variant_ids),
        "preflight_error_count": len(errors),
        "preflight_error_examples": errors[:10],
    }


def run(
    db_path: Path = DEFAULT_DB,
    plan: Path = DEFAULT_PLAN,
    report: Path = DEFAULT_REPORT,
    *,
    apply: bool = False,
    chunk_size: int = 400,
) -> dict:
    if chunk_size < 1:
        raise ValueError("CHUNK_SIZE")
    rows = read_plan(plan)
    engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
    with Session(engine) as db:
        result = preflight(db, rows)
    if result["preflight_error_count"]:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    result["mode"] = "APPLY" if apply else "PREFLIGHT_ONLY"
    if apply:
        with catalog_writer_lock(), Session(engine) as db:
            before = db.scalar(select(func.count()).select_from(CommercialFactClaim)) or 0
            for offset in range(0, len(rows), chunk_size):
                for row in rows[offset : offset + chunk_size]:
                    upsert_claim(db, **{name: row.get(name) for name in ARGUMENTS})
                db.commit()
                print(f"fact claims {min(offset + chunk_size, len(rows))}/{len(rows)}", flush=True)
            after = db.scalar(select(func.count()).select_from(CommercialFactClaim)) or 0
            result.update(
                database_claims_before=before,
                database_claims_after=after,
                newly_inserted_claims=after - before,
                already_present_or_updated_claims=len(rows) - (after - before),
            )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=400)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.db, args.plan, args.report, apply=args.apply, chunk_size=args.chunk_size),
            ensure_ascii=False,
            indent=2,
        )
    )
