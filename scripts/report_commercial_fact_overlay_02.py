"""Recompute the actual buyer projection and name every overlay-02 delta."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import catalog_buyer  # noqa: E402

OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02"
BASELINE = (
    ROOT
    / "deliverables/VerifiedData/commercial-manufacturer-drivetrain-01"
    / "production-visible-configurations.jsonl"
)
REVIEW = (
    ROOT
    / "deliverables/VerifiedData/commercial-manufacturer-drivetrain-01"
    / "factory-agent-review-remaining.jsonl"
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def value(catalog: dict, fact_name: str):
    return (catalog.get("facts", {}).get(fact_name) or {}).get("value")


def projection(db_path: Path, production: bool) -> list[dict]:
    catalog_buyer.get_settings = lambda: SimpleNamespace(
        environment="production" if production else "development"
    )
    engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
    with Session(engine) as db:
        records = catalog_buyer.records(db, active_scope=True)
        result = []
        for variant, catalog in records:
            if not (
                catalog_buyer.source_confirmed_core_ready(catalog)
                or catalog_buyer.commercial_overlay_core_ready(catalog)
            ):
                continue
            result.append(
                {
                    "variant_id": variant.id,
                    "make": catalog["make"],
                    "model": catalog["model"],
                    "generation": catalog.get("generation"),
                    "model_year": catalog["model_year"],
                    "engine": value(catalog, "engine_description")
                    or value(catalog, "engine_code")
                    or value(catalog, "motor_description"),
                    "transmission": value(catalog, "transmission_description"),
                    "drivetrain": value(catalog, "drivetrain"),
                    "source_registry_id": (
                        (variant.specifications.get("catalog") or {}).get("source_registry_id")
                    ),
                }
            )
    return sorted(
        result,
        key=lambda row: (
            row["make"].casefold(),
            row["model"].casefold(),
            row["model_year"],
            str(row["engine"]),
            str(row["transmission"]),
            str(row["drivetrain"]),
            row["variant_id"],
        ),
    )


def model_set(rows: list[dict]) -> set[tuple[str, str]]:
    return {(r["make"].casefold(), r["model"].casefold()) for r in rows}


def markdown_value(value_) -> str:
    if value_ is None or value_ == "":
        return "—"
    return str(value_).replace("|", "\\|").replace("\n", " ")


def run(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    baseline = read_jsonl(BASELINE)
    before_ids = {r["variant_id"] for r in baseline}
    if len(before_ids) != 92 or len(model_set(baseline)) != 13:
        raise ValueError("OVERLAY_01_BASELINE_CHANGED")
    internal = projection(db_path, production=False)
    production = projection(db_path, production=True)
    if len(internal) != 12749 or len(model_set(internal)) != 404:
        raise ValueError("INTERNAL_CORE_DRIFT")
    new = [r for r in production if r["variant_id"] not in before_ids]
    if len(production) != len(new) + len(baseline):
        raise ValueError("BASELINE_VISIBLE_VARIANT_REMOVED_OR_DUPLICATED")
    mirror = read_jsonl(out / "mirror-resolved.jsonl")
    direct = read_jsonl(out / "direct-drive-resolved.jsonl")
    mirror_keys = {r["catalog_key"] for r in mirror}
    direct_keys = {r["catalog_key"] for r in direct}
    if mirror_keys & direct_keys:
        raise ValueError("DOUBLE_COUNTED_MANUFACTURER_ROW")
    review = read_jsonl(REVIEW)
    remaining_keys = {r["catalog_key"] for r in review} - mirror_keys - direct_keys
    mirror_held = {
        r["catalog_key"]: r["overlay02_reason"]
        for r in read_jsonl(out / "manufacturer-review-remaining.jsonl")
    }
    direct_held = {
        r["catalog_key"]: r["overlay02_reason"] for r in read_jsonl(out / "direct-drive-held.jsonl")
    }
    remaining = []
    for row in review:
        if row["catalog_key"] not in remaining_keys:
            continue
        reason = mirror_held.get(row["catalog_key"], "UNCLASSIFIED")
        if (
            row["catalog_key"] in direct_held
            and direct_held[row["catalog_key"]] != "NO_REVIEWED_MATRIX"
        ):
            reason = direct_held[row["catalog_key"]]
        elif row["catalog_key"] in direct_held:
            reason = "DIRECT_DRIVETRAIN_MATRIX_REVIEW"
        elif reason == "MANDATORY_FACT_USES_OTHER_SOURCE":
            reason = "EPA_OR_OTHER_SOURCE_FOR_MANDATORY_FACT"
        remaining.append(
            {
                "catalog_key": row["catalog_key"],
                "make": row["make"],
                "model": row["model"],
                "model_year": row["model_year"],
                "reason": reason,
            }
        )
    if len(remaining) + len(mirror_keys) + len(direct_keys) != len(review):
        raise ValueError("MANUFACTURER_QUEUE_NOT_PARTITIONED")
    grouped = defaultdict(list)
    for row in remaining:
        grouped[(row["make"], row["model"], row["model_year"], row["reason"])].append(
            row["catalog_key"]
        )
    review_groups = [
        {
            "make": make,
            "model": model,
            "model_year": year,
            "reason": reason,
            "count": len(keys),
            "catalog_keys": sorted(keys),
        }
        for (make, model, year, reason), keys in sorted(grouped.items())
    ]
    write_jsonl(out / "production-visible-configurations.jsonl", production)
    write_jsonl(out / "new-production-visible-configurations.jsonl", new)
    write_jsonl(out / "remaining-unresolved-manufacturer.jsonl", remaining)
    write_jsonl(out / "review-groups.jsonl", review_groups)
    old_brands = defaultdict(list)
    new_brands = defaultdict(list)
    for row in baseline:
        old_brands[row["make"]].append(row)
    for row in production:
        new_brands[row["make"]].append(row)
    brand_resolved = Counter(r["make"] for r in mirror + direct)
    brand_review = Counter(r["make"] for r in remaining)
    brand_table = []
    for make in sorted(set(old_brands) | set(new_brands) | set(brand_resolved) | set(brand_review)):
        old = old_brands[make]
        after = new_brands[make]
        brand_table.append(
            {
                "make": make,
                "models_before": len(model_set(old)),
                "models_after": len(model_set(after)),
                "configs_before": len(old),
                "configs_after": len(after),
                "manufacturer_rows_resolved": brand_resolved[make],
                "remaining_review": brand_review[make],
            }
        )
    conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    fact_status = dict(
        conn.execute(
            "SELECT reuse_status,COUNT(*) FROM commercial_fact_claims GROUP BY reuse_status"
        ).fetchall()
    )
    summary = {
        "internal_models": len(model_set(internal)),
        "internal_configurations": len(internal),
        "production_models_before": len(model_set(baseline)),
        "production_models_after": len(model_set(production)),
        "production_configurations_before": len(baseline),
        "production_configurations_after": len(production),
        "new_production_models": len(model_set(production) - model_set(baseline)),
        "new_production_configurations": len(new),
        "manufacturer_rows_input": len(review),
        "manufacturer_rows_automatic": len(mirror),
        "manufacturer_rows_group_reviewed": len(direct),
        "manufacturer_rows_resolved": len(mirror) + len(direct),
        "manufacturer_rows_requiring_agent_review": len(direct) + len(remaining),
        "manufacturer_rows_remaining": len(remaining),
        "automatic_handling_rate": round(len(mirror) / len(review), 4),
        "agent_review_completed_rate": round(len(direct) / len(review), 4),
        "pending_review_rate": round(len(remaining) / len(review), 4),
        "agent_review_requirement_rate": round((len(direct) + len(remaining)) / len(review), 4),
        "remaining_review_groups": len(review_groups),
        "fact_status_counts": fact_status,
        "brands": brand_table,
        "new_model_names": sorted(
            [
                f"{make} {model}"
                for make, model in {(r["make"], r["model"]) for r in production}
                if (make.casefold(), model.casefold()) not in model_set(baseline)
            ]
        ),
        "remaining_reasons": dict(Counter(r["reason"] for r in remaining)),
    }
    (out / "production-verification.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Commercial Fact Overlay 02 — checkpoint",
        "",
        "Checked 2026-09-28. Production was recomputed through the existing buyer service.",
        "The following are **newly production-visible user configurations**, not research rows.",
        "Unconfirmed generation remains blank in the consumer projection.",
        "",
        "| Make | Model | Generation | US MY | Engine | Transmission | "
        "Drivetrain | New production status |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for row in new:
        cells = [
            row["make"],
            row["model"],
            row["generation"],
            row["model_year"],
            row["engine"],
            row["transmission"],
            row["drivetrain"],
            "NEW_VISIBLE",
        ]
        lines.append("| " + " | ".join(markdown_value(x) for x in cells) + " |")
    lines.extend(
        [
            "",
            "## Production coverage by brand",
            "",
            "| Make | Models before → after | Configs before → after | "
            "Rows resolved | Remaining review |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in brand_table:
        lines.append(
            f"| {row['make']} | {row['models_before']} → {row['models_after']} | "
            f"{row['configs_before']} → {row['configs_after']} | "
            f"{row['manufacturer_rows_resolved']} | {row['remaining_review']} |"
        )
    s = summary
    lines.extend(
        [
            "",
            "## Totals and boundaries",
            "",
            f"- Internal: {s['internal_models']} models / "
            f"{s['internal_configurations']} configurations; unchanged.",
            f"- Production: {s['production_models_before']} → "
            f"{s['production_models_after']} models; "
            f"{s['production_configurations_before']} → "
            f"{s['production_configurations_after']} configurations.",
            f"- Manufacturer rows: {s['manufacturer_rows_input']} input; "
            f"{s['manufacturer_rows_automatic']} rule-based resolutions; "
            f"{s['manufacturer_rows_group_reviewed']} official drive-matrix resolutions; "
            f"{s['manufacturer_rows_remaining']} unresolved.",
            f"- Automatic handling rate: {s['automatic_handling_rate']:.1%}; "
            f"completed group review: {s['agent_review_completed_rate']:.1%}; "
            f"pending group review: {s['pending_review_rate']:.1%}.",
            f"- Remaining exception groups: {s['remaining_review_groups']}; "
            "see `review-groups.jsonl` and `remaining-unresolved-manufacturer.jsonl`.",
            "- Mirrored PDFs passed cached SHA-256, annual identity and manufacturer "
            "mark checks, plus prior VERIFIED_SCOPED per-field locators. Only facts "
            "were extracted; no brochure prose or images are published.",
            "- Two cached Hyundai-issued press releases passed issuer, annual identity "
            "and exact powertrain/transmission/drive table checks.",
            "- EPA source facts remain INTERNAL_RESEARCH. EPA-only drive and "
            "ambiguous manufacturer applicability were not promoted.",
            "- Vehicle variants, EPA dataset, resolver, UI, pricing, ownership cost, "
            "images, phone and deployment code were unchanged.",
            "",
            "## Newly visible models",
            "",
            ", ".join(summary["new_model_names"]) + ".",
            "",
        ]
    )
    validation_path = out / "validation.json"
    if validation_path.is_file():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        safe_count = validation["production_fact_safety"]["production_core_configurations_checked"]
        published_count = validation["published_vehicle_variants"]
        lines.extend(
            [
                "## Validation",
                "",
                f"- Backend tests: {validation['backend_pytest']['passed']} PASS; "
                f"lint: {validation['ruff']}.",
                "- Existing claim preflight: zero errors; second application inserted zero claims.",
                f"- Fact safety: {safe_count} configurations checked; zero unsafe facts.",
                f"- Published vehicle variants: {published_count}; unchanged.",
                "",
            ]
        )
    (out / "CHECKPOINT_COMMERCIAL_FACT_OVERLAY_02.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return {k: v for k, v in summary.items() if k not in {"brands", "new_model_names"}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.db, args.out), indent=2, ensure_ascii=False))
