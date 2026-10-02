"""Name every Overlay 03 exception and recompute production/target coverage."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from report_commercial_fact_overlay_02 import model_set, projection

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03"
TARGET = ROOT / "data/manifests/US_PRODUCT_TARGET_MANIFEST.json"
BLOCKERS = {
    "DOCUMENT_AUTHENTICITY_NOT_CLEARED": "SOURCE_AUTHENTICITY",
    "EPA_OR_OTHER_SOURCE_FOR_MANDATORY_FACT": "MISSING_COMMERCIAL_MANDATORY_FACT",
    "DIRECT_DRIVETRAIN_MATRIX_REVIEW": "DRIVETRAIN_APPLICABILITY",
    "FACTORY_VERIFICATION_NOT_SCOPED": "FACTORY_APPLICABILITY",
    "MANDATORY_FACTS_SPLIT_ACROSS_DOCUMENTS": "MULTISOURCE_APPLICABILITY_AND_AUTHENTICITY",
    "OTHER_HOST_REQUIRES_SEPARATE_REVIEW": "SOURCE_AUTHENTICITY",
}
FACTS = (
    "powertrain",
    "fuel",
    "engine_displacement",
    "engine_description",
    "engine_code",
    "motor_description",
    "transmission_description",
    "drivetrain",
)


def jsonl(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows),
        encoding="utf-8",
    )


def md(value: object) -> str:
    return (
        str(value if value is not None and value != "" else "—")
        .replace("|", "\\|")
        .replace("\n", " ")
    )


def run(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    before = jsonl(PRIOR / "production-visible-configurations.jsonl")
    after = projection(db_path, production=True)
    internal = projection(db_path, production=False)
    if (len(before), len(model_set(before))) != (609, 56):
        raise ValueError("OVERLAY_02_BASELINE_CHANGED")
    if (len(internal), len(model_set(internal))) != (12749, 404):
        raise ValueError("INTERNAL_EPA_CORE_DRIFT")
    before_ids = {r["variant_id"] for r in before}
    after_ids = {r["variant_id"] for r in after}
    if not before_ids <= after_ids:
        raise ValueError("PRODUCTION_CONFIGURATION_DISAPPEARED")
    new = [r for r in after if r["variant_id"] not in before_ids]
    write_jsonl(out / "production-visible-configurations.jsonl", after)
    write_jsonl(out / "new-production-visible-configurations.jsonl", new)
    resolved = (
        jsonl(out / "reviewed-drive-resolved.jsonl")
        + jsonl(out / "honda-crv-resolved.jsonl")
        + jsonl(out / "honda-crv-2019-resolved.jsonl")
        + jsonl(out / "honda-accord-resolved.jsonl")
        + jsonl(out / "bmw-x3-resolved.jsonl")
        + jsonl(out / "bmw-4-series-resolved.jsonl")
    )
    resolved_keys = {r["catalog_key"] for r in resolved}
    if len(resolved_keys) != len(resolved):
        raise ValueError("OVERLAY_03_RESOLUTION_DOUBLE_COUNT")

    def configuration_signature(row: dict) -> tuple:
        return tuple(
            row[name]
            for name in ("make", "model", "model_year", "engine", "transmission", "drivetrain")
        )

    resolved_signatures = {configuration_signature(row) for row in resolved}
    new_signatures = {configuration_signature(row) for row in new}
    if resolved_signatures != new_signatures or len(new) != len(new_signatures):
        raise ValueError("REVIEWED_ROWS_DO_NOT_MATCH_DEDUPLICATED_PRODUCTION_DELTA")
    source_groups = jsonl(PRIOR / "review-groups.jsonl")
    all_keys = {key for group in source_groups for key in group["catalog_keys"]}
    if len(source_groups) != 87 or len(all_keys) != 427 or not resolved_keys <= all_keys:
        raise ValueError("OVERLAY_02_EXCEPTION_UNIVERSE_CHANGED")
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    audit_docs = json.loads((PRIOR / "document-audit.json").read_text(encoding="utf-8"))[
        "documents"
    ]
    audit_by_key = {key: doc for doc in audit_docs for key in doc["catalog_keys"]}
    drive_audit_path = out / "drive-candidate-audit.json"
    drive_audit = {}
    if drive_audit_path.is_file():
        drive_audit = {
            x["group_id"]: x
            for x in json.loads(drive_audit_path.read_text(encoding="utf-8"))["items"]
        }
    group_rows = []
    unresolved = []
    for index, group in enumerate(source_groups, 1):
        group_id = f"G{index:03d}"
        keys = group["catalog_keys"]
        done = sorted(set(keys) & resolved_keys)
        held = sorted(set(keys) - resolved_keys)
        result = "RESOLVED" if not held else "PARTIALLY_RESOLVED" if done else "BLOCKED"
        missing = Counter()
        source_urls = set()
        for key in held:
            record = db.execute(
                "SELECT specifications FROM vehicle_variants WHERE catalog_key=?", (key,)
            ).fetchone()
            if not record:
                raise ValueError(("MISSING_VARIANT", key))
            catalog = json.loads(record[0])["catalog"]
            for name in FACTS:
                fact = (catalog.get("facts") or {}).get(name) or {}
                if fact.get("status") != "CONFIRMED" or fact.get("value") in (None, "", "UNKNOWN"):
                    continue
                ref = fact.get("documentary_source") or {}
                if ref.get("registry_id") != catalog.get("source_registry_id"):
                    missing[name] += 1
                if name == "transmission_description" and ref.get("url"):
                    source_urls.add(ref["url"])
            unresolved.append(
                {
                    "catalog_key": key,
                    "make": group["make"],
                    "model": group["model"],
                    "model_year": group["model_year"],
                    "group_id": group_id,
                    "blocker": (
                        "SOURCE_CONFLICT"
                        if group_id == "G083"
                        and ("-sel-2019-FWD-" in key or "-sel-r-line-2019-FWD-" in key)
                        else BLOCKERS[group["reason"]]
                    ),
                }
            )
        blocker = BLOCKERS[group["reason"]]
        if group["reason"] == "EPA_OR_OTHER_SOURCE_FOR_MANDATORY_FACT":
            if missing.get("motor_description") or missing.get("powertrain"):
                blocker = "MISSING_MANUFACTURER_POWERTRAIN_FACT"
            elif missing.get("transmission_description"):
                blocker = "TRANSMISSION_APPLICABILITY"
            elif missing.get("drivetrain"):
                blocker = "DRIVETRAIN_APPLICABILITY"
        if group_id == "G083" and held:
            blocker = "SOURCE_CONFLICT_AND_DRIVE_SCOPE"
        document = next((audit_by_key[k] for k in keys if k in audit_by_key), None)
        audit_fail = []
        if document and not document.get("machine_authenticity_pass"):
            audit_fail = [
                field
                for field in (
                    "cache_exists",
                    "sha256_matches",
                    "brand_in_document",
                    "model_in_document",
                    "year_in_document",
                    "manufacturer_mark_in_document",
                )
                if not document.get(field)
            ]
            if document.get("extracted_chars", 0) < 1000:
                audit_fail.append("insufficient_machine_readable_text")
        group_rows.append(
            {
                "group_id": group_id,
                "make": group["make"],
                "model": group["model"],
                "model_year": group["model_year"],
                "original_reason": group["reason"],
                "blocker": blocker,
                "rows": group["count"],
                "resolved_rows": len(done),
                "remaining_rows": len(held),
                "result": result,
                "missing_factory_fact_counts": dict(missing),
                "manufacturer_source_urls": sorted(source_urls),
                "document_audit_failed_checks": audit_fail,
                "source_disagreement": (
                    "MY2019 VW matrix shows 4MOTION standard for SEL/SEL R-Line, "
                    "while held candidate keys encode FWD; SE FWD remains uncorroborated."
                    if group_id == "G083"
                    else None
                ),
                "cached_source_drive_term_pages": (
                    drive_audit.get(group_id, {}).get("term_pages") or {}
                ),
            }
        )
    write_jsonl(out / "exception-groups-87.jsonl", group_rows)
    write_jsonl(out / "remaining-unresolved-manufacturer.jsonl", unresolved)
    target = json.loads(TARGET.read_text(encoding="utf-8"))
    brands = []
    for make in target["brands"]:
        b = [r for r in before if r["make"] == make]
        a = [r for r in after if r["make"] == make]
        scoped = [m for m in target["models"] if m["make"] == make]
        brands.append(
            {
                "make": make,
                "production_models_before": len(model_set(b)),
                "production_models_after": len(model_set(a)),
                "production_configurations_before": len(b),
                "production_configurations_after": len(a),
                "target_models": len(scoped),
                "partial_names": [
                    m["canonical_model"]
                    for m in scoped
                    if m["production_coverage"]["status"] == "MODEL_PARTIAL"
                ],
                "base_complete_names": [],
                "not_started_names": [
                    m["canonical_model"]
                    for m in scoped
                    if m["production_coverage"]["status"] == "MODEL_NOT_STARTED"
                ],
                "reviewed_rows_resolved": sum(r["make"] == make for r in resolved),
                "rows_still_blocked": sum(r["make"] == make for r in unresolved),
            }
        )
    status_counts = dict(
        db.execute("SELECT reuse_status,COUNT(*) FROM commercial_fact_claims GROUP BY reuse_status")
    )
    published = db.execute(
        "SELECT COUNT(*) FROM vehicle_variants "
        "WHERE published_revision_id IS NOT NULL AND is_demo=0"
    ).fetchone()[0]
    summary = {
        "internal_models": 404,
        "internal_configurations": 12749,
        "production_models_before": len(model_set(before)),
        "production_models_after": len(model_set(after)),
        "production_configurations_before": len(before),
        "production_configurations_after": len(after),
        "new_production_models": len(model_set(after) - model_set(before)),
        "new_production_configurations": len(new),
        "resolved_rows_deduplicated_configurations": len(resolved_signatures),
        "manufacturer_rows_input": len(all_keys),
        "manufacturer_rows_group_resolved": len(resolved),
        "manufacturer_rows_remaining": len(unresolved),
        "exception_groups_input": len(source_groups),
        "groups_resolved": sum(g["result"] == "RESOLVED" for g in group_rows),
        "groups_partially_resolved": sum(g["result"] == "PARTIALLY_RESOLVED" for g in group_rows),
        "groups_blocked": sum(g["result"] == "BLOCKED" for g in group_rows),
        "group_reviewed_batch_application_rate": round(len(resolved) / len(all_keys), 4),
        "unguided_automatic_promotion_rate": 0.0,
        "target_model_count": len(target["models"]),
        "target_generation_scopes": sum(
            len(m["target_generation_scopes"]) for m in target["models"]
        ),
        "target_generation_scopes_with_production_year_hit": sum(
            bool(scope["production_year_hits"])
            for m in target["models"]
            for scope in m["target_generation_scopes"]
        ),
        "target_generation_scopes_confirmed_complete": 0,
        "target_model_year_pairs": sum(len(m["target_us_model_years"]) for m in target["models"]),
        "visible_target_model_year_pairs": sum(
            len(m["production_coverage"]["visible_target_model_years"]) for m in target["models"]
        ),
        "target_models_with_selected_year_visible": sum(
            bool(m["production_coverage"]["visible_target_model_years"]) for m in target["models"]
        ),
        "target_models_partial": sum(
            m["production_coverage"]["status"] == "MODEL_PARTIAL" for m in target["models"]
        ),
        "target_models_base_complete": 0,
        "target_models_not_started": sum(
            m["production_coverage"]["status"] == "MODEL_NOT_STARTED" for m in target["models"]
        ),
        "fact_status_counts": status_counts,
        "published_vehicle_variants": published,
        "brands": brands,
        "new_model_names": sorted(
            {
                f"{r['make']} {r['model']}"
                for r in after
                if (r["make"].casefold(), r["model"].casefold())
                in model_set(after) - model_set(before)
            }
        ),
        "remaining_blockers": dict(
            Counter(g["blocker"] for g in group_rows if g["remaining_rows"])
        ),
    }
    (out / "production-verification.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Commercial Fact Overlay 03 — group review and US product target",
        "",
        "Checked 2026-09-29 against the current SQLite buyer projection. "
        "EPA CORE remains internal research.",
        "A group marked BLOCKED lacks exact commercial manufacturer evidence "
        "for the held rows; a drive-word hit does not clear it.",
        "",
        "## All 87 prior exception groups",
        "",
        "| Group | Make | Model | US MY | Blocker | Rows | Resolved rows | Result |",
        "|---|---|---|---:|---|---:|---:|---|",
    ]
    for g in group_rows:
        lines.append(
            "| "
            + " | ".join(
                md(x)
                for x in (
                    g["group_id"],
                    g["make"],
                    g["model"],
                    g["model_year"],
                    g["blocker"],
                    g["rows"],
                    g["resolved_rows"],
                    g["result"],
                )
            )
            + " |"
        )
    lines += [
        "",
        "G083: the MY2019 Volkswagen Arteon matrix lists 4MOTION as standard "
        "for SEL and SEL R-Line, conflicting with their held FWD candidate keys. "
        "The SE FWD key remains uncorroborated; no FWD fact was promoted. "
        "G084: MY2020 AWD was confirmed for the listed trims; SE FWD remains held.",
        "",
        "## Newly production-visible configurations",
        "",
        "| Make | Model | Generation | US MY | Engine | Transmission | Drivetrain | "
        "Configuration count | Status |",
        "|---|---|---|---:|---|---|---|---:|---|",
    ]
    for r in new:
        lines.append(
            "| "
            + " | ".join(
                md(x)
                for x in (
                    r["make"],
                    r["model"],
                    r["generation"],
                    r["model_year"],
                    r["engine"],
                    r["transmission"],
                    r["drivetrain"],
                    1,
                    "NEW_VISIBLE",
                )
            )
            + " |"
        )
    lines += [
        "",
        "## Product target by approved brand",
        "",
        "| Make | Production models | Production configs | Target models | Partial names | "
        "Base complete names | Not started names | Rows resolved | Rows remaining |",
        "|---|---:|---:|---:|---|---|---|---:|---:|",
    ]
    for b in brands:
        lines.append(
            f"| {md(b['make'])} | {b['production_models_before']} → "
            f"{b['production_models_after']} | "
            f"{b['production_configurations_before']} → {b['production_configurations_after']} | "
            f"{b['target_models']} | {md(', '.join(b['partial_names']))} | "
            f"{md(', '.join(b['base_complete_names']))} | "
            f"{md(', '.join(b['not_started_names']))} | "
            f"{b['reviewed_rows_resolved']} | {b['rows_still_blocked']} |"
        )
    lines += [
        "",
        "## Approved target models with no production-visible version",
        "",
        "| Make | Model | Selected US MY | Held manufacturer rows | Status |",
        "|---|---|---|---:|---|",
    ]
    for model in target["models"]:
        if model["production_coverage"]["status"] != "MODEL_NOT_STARTED":
            continue
        held = sum(
            row["make"] == model["make"] and row["model"] == model["canonical_model"]
            for row in unresolved
        )
        lines.append(
            "| "
            + " | ".join(
                md(value)
                for value in (
                    model["make"],
                    model["canonical_model"],
                    ", ".join(map(str, model["target_us_model_years"])),
                    held,
                    "MODEL_NOT_STARTED",
                )
            )
            + " |"
        )
    lines += [
        "",
        "## Totals and exact limits",
        "",
        "- Internal EPA CORE: 404 models / 12,749 configurations; unchanged.",
        (
            f"- {len(resolved)} manufacturer source rows map to "
            f"{len(resolved_signatures)} unique engine/transmission/drivetrain "
            "configurations after trim-level deduplication."
        ),
        (
            f"- Production: {summary['production_models_before']} → "
            f"{summary['production_models_after']} models; "
            f"{summary['production_configurations_before']} → "
            f"{summary['production_configurations_after']} configurations."
        ),
        f"- Prior exceptions: 87 groups / 427 rows; {summary['groups_resolved']} resolved, "
        f"{summary['groups_partially_resolved']} partial, {summary['groups_blocked']} blocked; "
        f"{summary['manufacturer_rows_group_resolved']} reviewed rows resolved, "
        f"{summary['manufacturer_rows_remaining']} held.",
        (
            "- Bulk application after group evidence review: "
            f"{summary['group_reviewed_batch_application_rate']:.1%} "
            "of prior exception rows. Unguided automatic promotion: 0; "
            "no claim was inferred from an EPA drive value."
        ),
        f"- Canonical product target: {summary['target_model_count']} models / 17 brands; "
        f"{summary['target_models_partial']} MODEL_PARTIAL, 0 MODEL_BASE_COMPLETE, "
        f"{summary['target_models_not_started']} MODEL_NOT_STARTED.",
        (
            "- Selected target-year pairs: "
            f"{summary['visible_target_model_year_pairs']} / "
            f"{summary['target_model_year_pairs']}; target models with at least "
            f"one selected year visible: {summary['target_models_with_selected_year_visible']} / "
            f"{summary['target_model_count']}."
        ),
        (
            "- Target generation scopes: "
            f"{summary['target_generation_scopes_confirmed_complete']} / "
            f"{summary['target_generation_scopes']} confirmed complete; "
            f"{summary['target_generation_scopes_with_production_year_hit']} have "
            "at least one production year hit."
        ),
        (
            "- Target planning generation labels remain hypotheses. No model is called "
            "base complete until every selected generation/year and major "
            "engine/transmission variant has production evidence."
        ),
        (
            "- MODEL_PARTIAL means any production-visible year of the canonical model. "
            "It does not imply a hit within that model's selected target-year scope; "
            "the selected-year and generation-hit counts are reported separately."
        ),
        (
            "- Honda CR-V MY2018 and MY2019 annual pages were separately checked by "
            "page title and trim/drive matrix. MY2018 EX-L Navi remains held "
            "because the annual drive table names EX-L without that subvariant."
        ),
        (
            "- Jeep Cherokee MY2015–2016: 12 representative rows cover distinct "
            "annual 2.4L/3.2L × FWD/Active Drive I/Trailhawk Active Drive Lock "
            "combinations. The other 22 source rows remain held because trim-level "
            "or wording duplicates would inflate the buyer projection without a "
            "distinct technical configuration."
        ),
        (
            "- BMW X3 MY2015: four F25 engine/gearbox/drive tuples were independently "
            "corroborated by the official BMW USA technical-data sheet, MY2015 "
            "pricing guide and press kit. The MY2014 brochure remains held because "
            "its model-year identity is not proved by the cached document itself."
        ),
        (
            "- BMW 4 Series F32 Coupe MY2015: seven exact 428i/435i manual/automatic "
            "RWD/AWD tuples were corroborated by official BMW USA MY2015 technical "
            "data and pricing guide. The older press kit defines the drivetrain "
            "terms and engine family; it alone does not establish MY2015 scope."
        ),
        (
            "- EPA factual rows, rights registry, publication rules, resolver, UI, "
            "images, prices, dossiers, phone and deployment remain unchanged."
        ),
        "",
        "## Newly visible target models",
        "",
        ", ".join(summary["new_model_names"]) + ".",
        "",
        "## Remaining product target gaps",
        "",
        (
            "The exact selected target-year gaps and the research-only EPA aliases "
            "for each of the 74 models are in `US_PRODUCT_TARGET_MANIFEST.json`; "
            "no Turbo.az counts were inferred."
        ),
        "",
    ]
    (out / "CHECKPOINT_COMMERCIAL_FACT_OVERLAY_03.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return {
        k: v
        for k, v in summary.items()
        if k not in {"brands", "new_model_names", "remaining_blockers"}
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.db, args.out), ensure_ascii=False, indent=2))
