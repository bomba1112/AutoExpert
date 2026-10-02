"""Audit published factory facts and optionally replay the frozen import jobs."""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.services.catalog_buyer import vehicle_profile
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"


def audit(prepared):
    labels = json.loads((OUT / "factory-value-labels.json").read_text(encoding="utf-8"))
    keys = [change["catalog_key"] for change in prepared["changes"]]
    with SessionLocal() as db:
        variants = {
            row.catalog_key: row
            for row in db.scalars(
                select(VehicleVariant).where(VehicleVariant.catalog_key.in_(keys))
            )
        }
        if set(variants) != set(keys):
            raise ValueError("FACTORY_PUBLISHED_VARIANT_MISSING")
        revisions = {}
        field_counts = Counter()
        localized = 0
        preview = []
        for change in prepared["changes"]:
            variant = variants[change["catalog_key"]]
            catalog = variant.specifications["catalog"]
            revisions[variant.catalog_key] = variant.published_revision_id
            ru = vehicle_profile(catalog, "ru")
            az = vehicle_profile(catalog, "az")
            ru_rows = {row["key"]: row for section in ru["technical"] for row in section["rows"]}
            az_rows = {row["key"]: row for section in az["technical"] for row in section["rows"]}
            for field, expected in change["added"].items():
                fact = catalog["facts"].get(field)
                if not fact or fact["status"] != "CONFIRMED" or fact["value"] != expected:
                    raise ValueError(
                        "FACTORY_FACT_NOT_PUBLISHED:" + variant.catalog_key + ":" + field
                    )
                reference = fact.get("documentary_source") or {}
                if reference.get("url") != change["source_url"] or not reference.get("sha256"):
                    raise ValueError("FACTORY_FACT_PROVENANCE_MISSING:" + variant.catalog_key)
                for rows, language in ((ru_rows, "ru"), (az_rows, "az")):
                    if field not in rows or rows[field]["source_url"] != change["source_url"]:
                        raise ValueError(
                            "FACTORY_PROFILE_FIELD_MISSING:"
                            + variant.catalog_key
                            + ":"
                            + field
                            + ":"
                            + language
                        )
                    if isinstance(expected, str) and expected in labels:
                        if fact.get("labels", {}).get(language) != labels[expected][language]:
                            raise ValueError("FACTORY_LOCALIZED_LABEL_MISSING")
                        if rows[field]["value"] != labels[expected][language]:
                            raise ValueError("FACTORY_LOCALIZED_PROFILE_MISSING")
                if isinstance(expected, str) and expected in labels:
                    localized += 1
                field_counts[field] += 1
            if len(preview) < 6:
                preview.append(
                    {
                        "catalog_key": variant.catalog_key,
                        "make": change["make"],
                        "model": change["model"],
                        "year": change["model_year"],
                        "ru_categories": [section["title"] for section in ru["technical"]],
                        "az_categories": [section["title"] for section in az["technical"]],
                        "new_fields": list(change["added"]),
                    }
                )
    return revisions, {
        "variants": len(revisions),
        "field_values": sum(field_counts.values()),
        "localized_values": localized,
        "fields": dict(field_counts),
        "sample": preview,
    }


def main(*, replay):
    started = time.perf_counter()
    prepared = json.loads((OUT / "factory-prepared.json").read_text(encoding="utf-8"))
    before, details = audit(prepared)
    if replay:
        from scripts.factory_bulk_publish import run

        run(publish_reviewed=True)
        run(publish_reviewed=True, localization=True)
        after, _ = audit(prepared)
        if before != after:
            raise ValueError("FACTORY_REPLAY_CHANGED_PUBLISHED_REVISIONS")
    result = {
        "status": "PASS",
        "seconds": round(time.perf_counter() - started, 3),
        "replay": replay,
        "unchanged_revisions": len(before) if replay else None,
        **details,
    }
    (OUT / "factory-qa.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "seconds",
                    "replay",
                    "unchanged_revisions",
                    "variants",
                    "field_values",
                    "localized_values",
                )
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    main(replay=args.replay)
