"""Prepare a separate AZ/RU value-label correction for published Kia factory facts.

This does not add or change mechanical facts. Source strings remain stored verbatim.
"""

# ruff: noqa: E402
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.schemas.knowledge import CatalogRecord, FactInput, ImportManifest
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def main():
    labels = json.loads((OUT / "factory-value-labels.json").read_text(encoding="utf-8"))
    prepared = json.loads((OUT / "factory-prepared.json").read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    counters = Counter()
    with SessionLocal() as db:
        for change in prepared["changes"]:
            variant = db.scalar(
                select(VehicleVariant).where(VehicleVariant.catalog_key == change["catalog_key"])
            )
            if variant is None:
                raise ValueError("FACTORY_VARIANT_MISSING")
            original = variant.specifications["catalog"]
            value = {
                k: copy.deepcopy(v) for k, v in original.items() if k in CatalogRecord.model_fields
            }
            value["facts"] = {
                k: {a: copy.deepcopy(b) for a, b in fact.items() if a in FactInput.model_fields}
                for k, fact in original["facts"].items()
            }
            added = 0
            for key, expected in change["added"].items():
                if not isinstance(expected, str) or expected not in labels:
                    continue
                fact = value["facts"].get(key)
                if (
                    fact is None
                    or fact["value"] != expected
                    or fact["status"] != "CONFIRMED"
                    or fact.get("documentary_source", {}).get("url") != change["source_url"]
                ):
                    raise ValueError("FACTORY_LOCALIZATION_SOURCE_MISMATCH")
                if fact.get("labels") == labels[expected]:
                    continue
                if fact.get("labels") and fact["labels"] != labels[expected]:
                    raise ValueError("FACTORY_LOCALIZATION_CONFLICT")
                fact["labels"] = labels[expected]
                added += 1
            if not added:
                continue
            value["identity_verification"]["previous_revision_id"] = variant.published_revision_id
            value["revision_note"] = (
                "AZ/RU presentation labels for already published source-backed Kia "
                "factory facts; original technical values and applicability unchanged."
            )
            source_id = variant.catalog_key.split(":", 1)[0]
            grouped[source_id].append(CatalogRecord.model_validate(value))
            counters["records"] += 1
            counters["localized_values"] += added
        for source_id, records in sorted(grouped.items()):
            manifest = ImportManifest(
                source_id=source_id,
                parser="manifest-json-v1",
                records=records,
                selection_basis=(
                    "AZ/RU labels for existing Kia factory text values; no new technical facts, "
                    "no changed mechanical values or applicability"
                ),
            ).model_dump(mode="json")
            path = OUT / f"factory-localized-{source_id}.json"
            if path.exists() and _digest(json.loads(path.read_text(encoding="utf-8"))) != _digest(
                manifest
            ):
                raise ValueError("FROZEN_LOCALIZATION_MANIFEST_CHANGED")
            path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "state": "PREPARED_NOT_PUBLISHED",
        "counts": dict(counters),
        "source_value_labels": len(labels),
        "manifests": {source_id: len(rows) for source_id, rows in grouped.items()},
    }
    (OUT / "factory-localization-prepared.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
