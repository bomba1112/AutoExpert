"""Targeted live DB, resolver and AZ/RU filter audit for this publication delta."""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.schemas.knowledge import BuyerFilters  # noqa: E402
from app.services.catalog_buyer import (  # noqa: E402
    active_us_base_rows,
    fact_value,
    records,
    resolve,
    search,
)
from app.services.catalog_verification import base_catalog_ready, identity_verified  # noqa: E402

OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"


def main():
    started = time.perf_counter()
    baseline = json.loads((OUT / "baseline.json").read_text(encoding="utf-8"))
    old = set(baseline["rows"])
    with SessionLocal() as db:
        scoped = active_us_base_rows(records(db))
        live = {variant.catalog_key: (variant, catalog) for variant, catalog in scoped}
        delta = {key: row for key, row in live.items() if key not in old}
        assert len(delta) > 0 and old <= set(live)
        for key, (variant, c) in delta.items():
            assert (
                variant.published_revision_id and base_catalog_ready(c) and identity_verified(c)
            ), key
            assert c["original_market"] == "US" and c["make"] != "Skoda", key
            assert c["model_year"] >= (2000 if c["make"] in {"BMW", "Mercedes-Benz"} else 2005), key
            for field in (
                "body",
                "powertrain",
                "fuel",
                "engine_description",
                "transmission_description",
                "transmission_family",
                "drivetrain",
            ):
                fact = c["facts"].get(field, {})
                assert fact.get("status") == "CONFIRMED" and fact.get("documentary_source"), (
                    key,
                    field,
                )

        representative = {}
        for _key, (variant, c) in sorted(delta.items()):
            signature = (c["make"], c["model"], c.get("generation_code"))
            representative.setdefault(signature, (variant, c))
        resolved = []
        for signature, (variant, c) in representative.items():
            query = {
                "catalog_scope": "US_CONFIRMED_2000",
                "catalog_ready_only": True,
                "make": c["make"],
                "model": c["model"],
                "year": c["model_year"],
                "market": "US",
                "generation": c.get("generation_code") or c["generation"],
                "transmission": fact_value(c, "transmission_family"),
                "drivetrain": fact_value(c, "drivetrain"),
            }
            if fact_value(c, "engine_displacement") is not None:
                query["engine"] = fact_value(c, "engine_displacement")
            if fact_value(c, "trim") is not None:
                query["trim"] = fact_value(c, "trim")
            result = resolve(db, query)
            assert result["status"] in {"EXACT", "MULTIPLE"}, (signature, result["status"])
            assert variant.id in {candidate["id"] for candidate in result["candidates"]}, signature
            resolved.append(
                {
                    "make": c["make"],
                    "model": c["model"],
                    "year": c["model_year"],
                    "status": result["status"],
                }
            )

        filter_checks = []
        make_model_year = defaultdict(list)
        for variant, c in representative.values():
            make_model_year[(c["make"], c["model"], c["model_year"])].append(variant.id)
        for (make, model, year), ids in sorted(make_model_year.items()):
            for language in ("ru", "az"):
                result = search(
                    db,
                    BuyerFilters(
                        catalog_scope="US_CONFIRMED_2000",
                        catalog_ready_only=True,
                        makes=[make],
                        models=[model],
                        year_min=year,
                        year_max=year,
                        limit=100,
                    ),
                    language=language,
                )
                matched_ids = {item["id"] for item in result["matches"]}
                assert set(ids) <= matched_ids, (
                    make,
                    model,
                    year,
                    language,
                    set(ids) - matched_ids,
                )
                filter_checks.append(
                    {
                        "make": make,
                        "model": model,
                        "year": year,
                        "language": language,
                        "matches": len(matched_ids),
                    }
                )
        optima_unknown = [
            (v, c)
            for v, c in delta.values()
            if c["make"] == "Kia"
            and c["model"] == "Optima"
            and c["model_year"] == 2014
            and fact_value(c, "seats") is None
        ]
        if optima_unknown:
            filtered = search(
                db,
                BuyerFilters(
                    catalog_scope="US_CONFIRMED_2000",
                    makes=["Kia"],
                    models=["Optima"],
                    year_min=2014,
                    year_max=2014,
                    min_seats=7,
                    limit=100,
                ),
                language="ru",
            )
            assert not {v.id for v, _ in optima_unknown} & {m["id"] for m in filtered["matches"]}
    report = {
        "status": "PASS",
        "new_base_ready_records_checked": len(delta),
        "representative_resolver_checks": len(resolved),
        "az_ru_exact_model_year_filter_checks": len(filter_checks),
        "unknown_seating_strict_filter": "PASS" if optima_unknown else "NOT_APPLICABLE",
        "resolver": resolved,
        "filters": filter_checks,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (OUT / "mass-scale-targeted-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "new_base_ready_records_checked",
                    "representative_resolver_checks",
                    "az_ru_exact_model_year_filter_checks",
                    "unknown_seating_strict_filter",
                    "elapsed_seconds",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
