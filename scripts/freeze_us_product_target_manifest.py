"""Freeze the owner-approved 17-brand US product target and measure coverage.

The target comes from the existing owner priority policy and its pre-existing
generation/year planning queue. EPA aliases and annual rows remain research
references; they never become target facts or commercial evidence here.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from report_commercial_fact_overlay_02 import projection

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data/manifests/az-market-priority-policy.json"
QUEUE = ROOT / "data/manifests/us-ai-verify-09-queue.json"
ALIASES = ROOT / "scripts/epa_master_aliases.json"
CANDIDATES = ROOT / "deliverables/VerifiedData/us-catalog-universe/candidates.jsonl"
MANIFEST = ROOT / "data/manifests/US_PRODUCT_TARGET_MANIFEST.json"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03"


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def build(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    aliases = json.loads(ALIASES.read_text(encoding="utf-8"))
    approved = [
        (make, model)
        for make, models in policy["first_wave_model_order"].items()
        for model in models
    ]
    if len(policy["primary_makes"]) != 17 or len(approved) != 74 or len(set(approved)) != 74:
        raise ValueError("APPROVED_TARGET_SIZE_CHANGED")
    if set(policy["first_wave_model_order"]) != set(policy["primary_makes"]):
        raise ValueError("OWNER_BRAND_SCOPE_MISMATCH")
    if any(make == "Skoda" for make, _ in approved):
        raise ValueError("NON_US_BRAND_IN_TARGET")
    planned = defaultdict(list)
    for item in queue["queue"]:
        key = item["make"], item["model"]
        if key not in approved or item["market"] != "US":
            raise ValueError(("UNAPPROVED_QUEUE_ITEM", key))
        planned[key].append(item)
    if set(planned) != set(approved):
        raise ValueError("OWNER_TARGET_MISSING_PLANNING_SCOPE")
    alias_map = defaultdict(list)
    for item in aliases["base_aliases"]:
        alias_map[(item["make"], item["model"])].extend(item["epa_base_models"])
    for item in aliases["raw_prefixes"]:
        alias_map[(item["make"], item["model"])].extend(item["prefixes"])
    research_years = defaultdict(set)
    research_labels = defaultdict(set)
    for row in load_jsonl(CANDIDATES):
        key = row["make"], row["model"]
        if key in approved:
            research_years[key].add(row["model_year"])
            research_labels[key].add(row["epa_fields"].get("baseModel") or row["model"])
    production = projection(db_path, production=True)
    visible = defaultdict(list)
    for row in production:
        key = row["make"], row["model"]
        if key in approved:
            visible[key].append(row)
    models = []
    for make, model in approved:
        key = make, model
        minimum = 2000 if make in {"Mercedes-Benz", "BMW"} else 2005
        scopes = [
            {
                "generation_candidate": p["generation_candidate"],
                "generation_status": p["generation_status"],
                "target_us_model_years": sorted(set(p["target_model_years"])),
                "planning_queue_id": p["queue_id"],
            }
            for p in planned[key]
        ]
        target_years = sorted({year for p in planned[key] for year in p["target_model_years"]})
        if not target_years or min(target_years) < minimum:
            raise ValueError(("INVALID_MODEL_YEAR_TARGET", key))
        years_visible = sorted(
            {r["model_year"] for r in visible[key] if r["model_year"] >= minimum}
        )
        for scope in scopes:
            matched_years = sorted(set(scope["target_us_model_years"]) & set(years_visible))
            scope["production_year_hits"] = matched_years
            scope["generation_confirmed_complete"] = False
        target_years_visible = sorted(set(target_years) & set(years_visible))
        missing = sorted(set(target_years) - set(years_visible))
        # The planning queue does not enumerate every major factory variant.
        # Therefore even a year hit cannot by itself prove base completion.
        status = "MODEL_PARTIAL" if years_visible else "MODEL_NOT_STARTED"
        models.append(
            {
                "make": make,
                "canonical_model": model,
                "market": "US",
                "minimum_model_year": minimum,
                "target_generation_scopes": scopes,
                "target_us_model_years": target_years,
                "target_us_model_year_span": [min(target_years), max(target_years)],
                "known_epa_aliases": sorted(set(alias_map[key])),
                "epa_research_base_labels": sorted(research_labels[key]),
                "epa_research_model_years": sorted(research_years[key]),
                "production_coverage": {
                    "status": status,
                    "visible_model_years": years_visible,
                    "visible_target_model_years": target_years_visible,
                    "missing_target_model_years": missing,
                    "visible_configuration_count": len(visible[key]),
                    "major_engine_transmission_variant_completeness": "NOT_ASSESSED",
                    "base_complete": False,
                    "visible_generation_labels": sorted(
                        {r["generation"] for r in visible[key] if r.get("generation")}
                    ),
                },
            }
        )
    manifest = {
        "manifest_id": "US_PRODUCT_TARGET_MANIFEST",
        "frozen_at": "2026-09-28",
        "market": "US",
        "source_of_authority": [str(POLICY.relative_to(ROOT)), str(QUEUE.relative_to(ROOT))],
        "epa_role": "INTERNAL_RESEARCH_CANDIDATE_AND_ALIAS_REFERENCE_ONLY",
        "scope_note": (
            "Owner-approved model denominator and selected planning years, not an assertion "
            "that all US lifecycle years or major engine/transmission variants are known. "
            "Unverified generation labels remain planning hypotheses."
        ),
        "completion_rule": (
            "MODEL_BASE_COMPLETE requires commercial-safe production coverage for every "
            "target generation/year and all major engine/transmission variants; a mere "
            "production hit or EPA candidate is insufficient."
        ),
        "brands": policy["primary_makes"],
        "models": models,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_brand = defaultdict(list)
    for item in models:
        by_brand[item["make"]].append(item)
    brand_coverage = []
    for make in policy["primary_makes"]:
        scoped = by_brand[make]
        partial = [
            m["canonical_model"]
            for m in scoped
            if m["production_coverage"]["status"] == "MODEL_PARTIAL"
        ]
        not_started = [
            m["canonical_model"]
            for m in scoped
            if m["production_coverage"]["status"] == "MODEL_NOT_STARTED"
        ]
        brand_coverage.append(
            {
                "make": make,
                "target_model_count": len(scoped),
                "partial_models": partial,
                "base_complete_models": [],
                "not_started_models": not_started,
                "visible_target_model_year_pairs": sum(
                    len(m["production_coverage"]["visible_target_model_years"]) for m in scoped
                ),
                "target_model_year_pairs": sum(len(m["target_us_model_years"]) for m in scoped),
            }
        )
    report = {
        "target_brands": len(policy["primary_makes"]),
        "target_models": len(models),
        "target_generation_scopes": sum(len(m["target_generation_scopes"]) for m in models),
        "target_model_year_pairs": sum(len(m["target_us_model_years"]) for m in models),
        "visible_target_models": sum(
            m["production_coverage"]["status"] == "MODEL_PARTIAL" for m in models
        ),
        "model_partial": sum(m["production_coverage"]["status"] == "MODEL_PARTIAL" for m in models),
        "model_base_complete": 0,
        "model_not_started": sum(
            m["production_coverage"]["status"] == "MODEL_NOT_STARTED" for m in models
        ),
        "visible_target_model_year_pairs": sum(
            len(m["production_coverage"]["visible_target_model_years"]) for m in models
        ),
        "target_generation_scopes_with_production_year_hit": sum(
            bool(scope["production_year_hits"])
            for model in models
            for scope in model["target_generation_scopes"]
        ),
        "target_generation_scopes_confirmed_complete": 0,
        "target_models_with_selected_year_visible": sum(
            bool(m["production_coverage"]["visible_target_model_years"]) for m in models
        ),
        "brands": brand_coverage,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "target-coverage.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {k: v for k, v in report.items() if k != "brands"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.out), ensure_ascii=False, indent=2))
