"""Render named, exact-year US BASE_READY catalogue and delta from frozen DB state."""

# ruff: noqa: E501

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.catalog_buyer import active_us_base_rows, records  # noqa: E402
from app.services.catalog_verification import base_catalog_counts  # noqa: E402
from app.services.market_priority import policy  # noqa: E402

OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"
BASELINE = OUT / "baseline.json"
OPTIONAL_FIELDS = (
    "engine_code",
    "engine_displacement",
    "cylinders",
    "power_hp",
    "torque_lb_ft",
    "aspiration",
    "injection",
    "transmission_code",
    "gears",
    "octane_aki",
    "fuel_tank_us_gal",
    "engine_oil_capacity_l",
    "engine_oil_capacity_us_qt",
    "wheelbase_in",
    "length_in",
    "width_in",
    "height_in",
    "wheels",
    "seats",
)


def value(c, key):
    fact = c.get("facts", {}).get(key) or {}
    return fact.get("value") if fact.get("status") == "CONFIRMED" else None


def text_cell(value):
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def years_text(years):
    numbers = sorted(set(years))
    if not numbers:
        return "—"
    runs = []
    start = last = numbers[0]
    for year in numbers[1:]:
        if year == last + 1:
            last = year
        else:
            runs.append(str(start) if start == last else f"{start}–{last}")
            start = last = year
    runs.append(str(start) if start == last else f"{start}–{last}")
    return ", ".join(runs)


def table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + ["| " + " | ".join(text_cell(v) for v in row) + " |" for row in rows]
    )


def groups(scoped):
    bucket = defaultdict(
        lambda: {
            "years": [],
            "trims": set(),
            "trims_by_year": defaultdict(set),
            "keys": [],
            "sources": set(),
        }
    )
    for variant, c in scoped:
        signature = (
            c["make"],
            c["model"],
            c.get("generation_code") or c["generation"],
            c["original_market"],
            value(c, "body"),
            value(c, "powertrain"),
            value(c, "engine_description"),
            value(c, "transmission_family"),
            value(c, "transmission_description"),
            value(c, "drivetrain"),
        )
        group = bucket[signature]
        group["years"].append(c["model_year"])
        group["keys"].append(variant.catalog_key)
        if value(c, "trim"):
            group["trims"].add(str(value(c, "trim")))
            group["trims_by_year"][c["model_year"]].add(str(value(c, "trim")))
        for field in ("engine_description", "transmission_description", "drivetrain"):
            source = (c.get("facts", {}).get(field, {}).get("documentary_source") or {}).get("url")
            if source:
                group["sources"].add(source)
    make_order = {name: idx for idx, name in enumerate(policy()["primary_makes"])}
    ordered = []
    for signature, item in bucket.items():
        make, model, generation, market, body, powertrain, engine, family, trans, drive = signature
        ordered.append(
            {
                "make": make,
                "model": model,
                "generation": generation,
                "market": market,
                "body": body,
                "powertrain": powertrain,
                "engine": engine,
                "transmission_family": family,
                "transmission": trans,
                "drivetrain": drive,
                "model_years": sorted(set(item["years"])),
                "configuration_count": len(item["keys"]),
                "trims": sorted(item["trims"]),
                "trims_by_year": {
                    str(year): sorted(names)
                    for year, names in sorted(item["trims_by_year"].items())
                },
                "catalog_keys": sorted(item["keys"]),
                "source_urls": sorted(item["sources"]),
                "status": "BASE_READY / exact confirmed subset",
            }
        )
    return sorted(
        ordered,
        key=lambda x: (
            make_order.get(x["make"], 99),
            x["model"],
            x["generation"],
            x["model_years"],
            str(x["engine"]),
            str(x["transmission"]),
            str(x["drivetrain"]),
        ),
    )


def render_group_rows(items):
    return [
        [
            g["make"],
            g["model"],
            g["generation"],
            g["market"],
            f"{g['body']} / {g['powertrain']}",
            years_text(g["model_years"]),
            g["engine"],
            f"{g['transmission']} ({g['transmission_family']})",
            g["drivetrain"],
            g["configuration_count"],
            g["status"],
            "; ".join(f"{year}: {', '.join(trims)}" for year, trims in g["trims_by_year"].items())
            or "—",
        ]
        for g in items
    ]


def main():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    old = set(baseline["rows"])
    with SessionLocal() as db:
        scoped = active_us_base_rows(records(db))
        after = base_catalog_counts(scoped)
    current = {v.catalog_key for v, _ in scoped}
    added = [(v, c) for v, c in scoped if v.catalog_key not in old]
    missing = sorted(old - current)
    delta = groups(added)
    cumulative = groups(scoped)
    assert sum(g["configuration_count"] for g in delta) == len(added)
    assert sum(g["configuration_count"] for g in cumulative) == after["model_year_configurations"]
    assert not missing, "Previously BASE_READY rows disappeared: " + repr(missing[:5])
    listed = policy()["first_wave_model_order"]
    present = {(c["make"], c["model"]) for _, c in scoped}
    remaining = [
        {
            "make": make,
            "model": model,
            "reason": "No BASE_READY annual configuration in current US scope",
        }
        for make, models in listed.items()
        for model in models
        if (make, model) not in present
    ]
    by_make = []
    for make in policy()["primary_makes"]:
        rows = [(v, c) for v, c in scoped if c["make"] == make]
        if rows:
            counts = base_catalog_counts(rows)
            years = [c["model_year"] for _, c in rows]
            models = sorted({c["model"] for _, c in rows})
            by_make.append(
                {
                    "make": make,
                    "models_available": models,
                    "generations": counts["generations"],
                    "earliest_model_year": min(years),
                    "latest_model_year": max(years),
                    "engines": counts["engine_variants"],
                    "transmissions": counts["transmission_variants"],
                    "base_ready_annual_configurations": counts["model_year_configurations"],
                    "remaining_major_families": [
                        x["model"] for x in remaining if x["make"] == make
                    ],
                }
            )
        else:
            by_make.append(
                {
                    "make": make,
                    "models_available": [],
                    "generations": 0,
                    "earliest_model_year": None,
                    "latest_model_year": None,
                    "engines": 0,
                    "transmissions": 0,
                    "base_ready_annual_configurations": 0,
                    "remaining_major_families": listed.get(make, []),
                }
            )
    summary = {
        "observed_at": datetime.now(UTC).isoformat(),
        "baseline_at": baseline["observed_at"],
        "before": baseline["counts"],
        "after": after,
        "new_base_ready": len(added),
        "removed_from_base_ready": missing,
        "named_delta_groups": len(delta),
        "cumulative_groups": len(cumulative),
        "by_make": by_make,
        "remaining_major_families": remaining,
        "new_row_optional_fact_coverage": {
            field: sum(value(c, field) is not None for _, c in added)
            for field in OPTIONAL_FIELDS
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, content in (
        ("mass-scale-delta.json", delta),
        ("mass-scale-cumulative.json", cumulative),
        ("mass-scale-summary.json", summary),
        ("mass-scale-remaining.json", remaining),
    ):
        (OUT / filename).write_text(
            json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    headers = [
        "Make",
        "Model",
        "Generation",
        "USA market",
        "Body / powertrain",
        "Model years",
        "Engine",
        "Transmission",
        "Drivetrain",
        "Configuration count",
        "Status",
        "Confirmed trim by model year",
    ]
    report = [
        "# US base catalog 07 — mass scale AI draft and source verification",
        "",
        "Only active US BASE_READY rows from the local database are listed. Each row covers exactly the shown years and source-confirmed variants; it does not claim complete model coverage. Unknown optional seats do not affect readiness. Historical records and failed drafts remain outside this output.",
        "",
        "## Delta from frozen pre-batch database",
        "",
        table(headers, render_group_rows(delta)),
        "",
        "## Cumulative active US BASE_READY catalogue",
        "",
        table(headers, render_group_rows(cumulative)),
        "",
        "## Coverage by approved make",
        "",
        table(
            [
                "Make",
                "Models available",
                "Generations",
                "First MY",
                "Last MY",
                "Engines",
                "Transmissions",
                "BASE_READY annual configurations",
                "Remaining major model families",
            ],
            [
                [
                    r["make"],
                    ", ".join(r["models_available"]) or "—",
                    r["generations"],
                    r["earliest_model_year"],
                    r["latest_model_year"],
                    r["engines"],
                    r["transmissions"],
                    r["base_ready_annual_configurations"],
                    ", ".join(r["remaining_major_families"]) or "—",
                ]
                for r in by_make
            ],
        ),
        "",
        "## Optional factory fields in newly published rows",
        "",
        "Counts below are row coverage, not completeness gates. A missing optional value remains absent from the ordinary user card.",
        "",
        table(
            ["Factory field", "New rows with a confirmed value"],
            [
                [field, count]
                for field, count in summary["new_row_optional_fact_coverage"].items()
                if count
            ],
        ),
        "",
        "## Aggregate totals after named records",
        "",
        table(
            ["Metric", "Before", "After", "Delta"],
            [
                [
                    name,
                    baseline["counts"].get(name, 0),
                    after.get(name, 0),
                    after.get(name, 0) - baseline["counts"].get(name, 0),
                ]
                for name in (
                    "makes",
                    "models",
                    "generations",
                    "market_variants",
                    "engine_variants",
                    "transmission_variants",
                    "engine_transmission_combinations",
                    "drivetrain_combinations",
                    "model_year_configurations",
                )
            ],
        ),
        "",
        "Per-configuration source URLs and catalogue keys are retained in the two JSON tables alongside this checkpoint. Phone and Hetzner: DEFERRED_BY_USER.",
        "",
    ]
    (ROOT / "docs/CHECKPOINT_US_BASE_CATALOG_07_MASS.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "new_base_ready": len(added),
                "total_base_ready": after["model_year_configurations"],
                "delta_groups": len(delta),
                "cumulative_groups": len(cumulative),
                "remaining_major_models": len(remaining),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
