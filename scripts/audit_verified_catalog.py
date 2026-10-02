"""Read-only catalogue audit and draft family queue; no user/account/VIN data exported."""

from __future__ import annotations

# ruff: noqa: E501
import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.knowledge_ops import CatalogRevision, RawDocument  # noqa: E402
from app.services.catalog_buyer import records  # noqa: E402
from app.services.knowledge_import import (  # noqa: E402
    document_text,
    epa_record,
    normalized,
    private_path,
)
from sqlalchemy import select  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["baseline", "after"], default="baseline")
    args = parser.parse_args()
    out = ROOT / "deliverables/VerifiedData"
    out.mkdir(exist_ok=True, parents=True)
    with SessionLocal() as db:
        rows = records(db)
        catalogs = [c for _, c in rows]
        epa_ids = {c["external_key"] for c in catalogs if c["source_registry_id"] == "epa"}
        source_rows = {}
        for doc in db.scalars(select(RawDocument).where(RawDocument.source_id == "epa")):
            text = document_text(private_path(doc.storage_key).read_bytes())
            for row in csv.DictReader(io.StringIO(text)):
                if row.get("id") in epa_ids:
                    source_rows[row["id"]] = row
        missing_links = []
        mismatched = []
        aggregate_mismatches = []
        for variant, catalog in rows:
            if not db.get(CatalogRevision, variant.published_revision_id):
                missing_links.append(variant.catalog_key)
            if catalog["source_registry_id"] == "epa":
                original = source_rows.get(catalog["external_key"])
                if not original or any(
                    original[k] != str(catalog[field])
                    for k, field in [("make", "make"), ("year", "model_year")]
                ):
                    mismatched.append(catalog["external_key"])
                if original:
                    extracted = epa_record(original)
                    for field, expected in extracted.facts.items():
                        actual = catalog["facts"].get(field, {})
                        if any(
                            actual.get(k) != getattr(expected, k)
                            for k in ("value", "unit", "status")
                        ):
                            aggregate_mismatches.append(
                                {"row": catalog["external_key"], "field": field}
                            )
        keys = Counter(v.catalog_key for v, _ in rows)
        fields = sorted({key for c in catalogs for key in c["facts"]})
        canonical = {}
        for c in catalogs:
            key = (normalized(c["make"]), normalized(c["model"]), c["original_market"])
            canonical.setdefault(key, (c["make"], c["model"], c["original_market"]))
        families = sorted(canonical.values())

        def same(c, make, model, market):
            return (normalized(c["make"]), normalized(c["model"]), c["original_market"]) == (
                normalized(make),
                normalized(model),
                market,
            )

        matrix = [
            {
                "make": make,
                "model": model,
                "market": market,
                "rows": sum(same(c, make, model, market) for c in catalogs),
                "years": sorted(
                    {c["model_year"] for c in catalogs if same(c, make, model, market)}
                ),
                "priority_status": "DRAFT",
                "local_listing_count": None,
                "listing_observed_at": None,
                "local_fleet_observation": None,
                "source_ids": sorted(
                    {c["source_registry_id"] for c in catalogs if same(c, make, model, market)}
                ),
                "state": "NEEDS_DOCUMENTS",
                "cursor": 0,
                "blockers": [
                    "generation",
                    "aggregate_codes",
                    "maintenance",
                    "fitment",
                    "local_part_prices",
                    "labor",
                    "image_review",
                ],
            }
            for make, model, market in families
        ]
        result = {
            "phase": args.phase,
            "row_unit": "Source-specific model-year test/configuration candidate; not exact trim, generation or dossier",
            "published_candidate_rows": len(rows),
            "all_variant_rows_including_legacy": len(list(db.scalars(select(VehicleVariant)))),
            "makes": len({normalized(c["make"]) for c in catalogs}),
            "models": len({(normalized(c["make"]), normalized(c["model"])) for c in catalogs}),
            "years": sorted({c["model_year"] for c in catalogs}),
            "markets": dict(Counter(c["original_market"] for c in catalogs)),
            "generations_named": len(
                {
                    (c["make"], c["model"], c.get("generation"))
                    for c in catalogs
                    if c.get("generation")
                }
            ),
            "engine_codes": sorted({v.engine_code for v, _ in rows if v.engine_code}),
            "transmission_codes": sorted(
                {v.transmission_code for v, _ in rows if v.transmission_code}
            ),
            "duplicate_catalog_keys": {k: v for k, v in keys.items() if v > 1},
            "missing_revision_links": missing_links,
            "epa_original_rows_matched": len(source_rows),
            "epa_model_year_mismatches": mismatched,
            "cartesian_product": "No generated cross-product: each EPA catalog key refers to one raw EPA vehicle ID; similar rows are distinct source test entries",
            "fields": {
                key: {
                    "present": sum(key in c["facts"] for c in catalogs),
                    "confirmed": sum(
                        c["facts"].get(key, {}).get("status") == "CONFIRMED" for c in catalogs
                    ),
                }
                for key in fields
            },
            "facts_without_locator_or_source": sum(
                not f.get("locator") or not f.get("source_id")
                for c in catalogs
                for f in c["facts"].values()
            ),
            "anonymous_examples": catalogs[:2],
            "epa_aggregate_field_mismatches": aggregate_mismatches,
            "queries": [
                "SELECT * FROM vehicle_variants WHERE published_revision_id IS NOT NULL AND is_demo=0",
                "SELECT * FROM catalog_revisions WHERE id=:published_revision_id",
                "SELECT * FROM raw_documents WHERE source_id='epa'",
                "Source rows joined by catalog.external_key == EPA CSV id; no engine x transmission join",
            ],
        }
    (out / f"catalog-{args.phase}-audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / f"coverage-{args.phase}.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    queue = ROOT / "data/manifests/verified-data-work-queue.json"
    if not queue.exists():
        queue.write_text(
            json.dumps(
                {"status": "DRAFT", "user_approved_priority_list": False, "families": matrix},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k
                in {
                    "published_candidate_rows",
                    "makes",
                    "models",
                    "generations_named",
                    "facts_without_locator_or_source",
                    "epa_original_rows_matched",
                    "epa_model_year_mismatches",
                }
            }
        )
    )


if __name__ == "__main__":
    main()
