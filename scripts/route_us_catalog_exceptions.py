"""Route EPA universe blockers without promoting candidates to verified catalog data.

The 408-model EPA denominator is preserved. Only identity conflicts, unresolved
names/aliases, ambiguous generation, and unparseable source powertrain labels
become manual exceptions. Ordinary unmapped generation is a grouped automated
source-research task; all remaining EPA rows stay nonpublished bulk candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/VerifiedData/us-catalog-universe"
DEFAULT_OUT = SOURCE / "exception-routing"
INPUTS = {
    "candidates": "candidates.jsonl",
    "join": "candidate-join.jsonl",
    "generation": "generation-hypotheses.jsonl",
    "vpic": "vpic-crosscheck.jsonl",
    "powertrain": "powertrain-groups.jsonl",
}
NEW_CLASSIFICATIONS = {"CANDIDATE_NEW", "POSSIBLE_ALIAS", "CONFLICT"}
MANUAL_CODES = {
    "CATALOG_IDENTITY_CONFLICT": 0,
    "MODEL_ALIAS_REVIEW": 1,
    "VPIC_MODEL_NAME_UNRESOLVED": 2,
    "GENERATION_AMBIGUOUS": 3,
    "DRIVETRAIN_SOURCE_AMBIGUOUS": 4,
    "DRIVETRAIN_SOURCE_UNMAPPED": 5,
    "TRANSMISSION_SOURCE_UNMAPPED": 6,
}
AUTO_GENERATION_CODES = {
    "UNRESOLVED_GENERATION": "GENERATION_UNMAPPED",
    "PRIOR_AI_HYPOTHESIS_UNVERIFIED": "GENERATION_DRAFT_NEEDS_SOURCE",
    "EXACT_YEAR_VERIFIED_REFERENCE_REQUIRES_APPLICABILITY": "GENERATION_APPLICABILITY_CHECK",
}
EXACT_DRIVES = {
    "front-wheel drive",
    "rear-wheel drive",
    "all-wheel drive",
    "4-wheel drive",
    "part-time 4-wheel drive",
}
AMBIGUOUS_DRIVES = {"4-wheel or all-wheel drive", "2-wheel drive"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def canonical_lines(rows: list[dict]) -> bytes:
    return b"".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        + b"\n"
        for row in rows
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def year_ranges(years: set[int]) -> list[list[int]]:
    spans: list[list[int]] = []
    for year in sorted(years):
        if spans and year == spans[-1][1] + 1:
            spans[-1][1] = year
        else:
            spans.append([year, year])
    return spans


def transmission_source_status(value: object) -> str:
    """Recognize EPA source notation, never infer a factory gearbox family."""
    text = " ".join(str(value or "").casefold().split())
    if re.fullmatch(r"manual \d+-spd", text):
        return "EPA_MANUAL_LABEL"
    if re.fullmatch(r"automatic \d+-spd", text):
        return "EPA_AUTOMATIC_LABEL"
    if re.fullmatch(r"automatic \((?:s|a|am|am-s|av-s)\d+\)", text):
        return "EPA_AUTOMATIC_CODE"
    if text == "automatic (variable gear ratios)":
        return "EPA_VARIABLE_RATIO_LABEL"
    return "UNMAPPED"


def drivetrain_source_status(value: object) -> str:
    text = " ".join(str(value or "").casefold().split())
    if text in EXACT_DRIVES:
        return "EPA_DRIVE_LABEL"
    if text in AMBIGUOUS_DRIVES:
        return "AMBIGUOUS"
    return "UNMAPPED"


def require_unique(items: list[dict], key: str, source: str) -> dict:
    result = {}
    for item in items:
        value = item[key]
        if value in result:
            raise ValueError(f"DUPLICATE_{source.upper()}_{key.upper()}: {value}")
        result[value] = item
    return result


def issue_store() -> dict:
    return defaultdict(
        lambda: {
            "years": set(),
            "epa_vehicle_ids": set(),
            "source_labels": set(),
            "matched_variant_ids": set(),
            "source_urls": set(),
            "generation_candidates": set(),
        }
    )


def add_issue(
    store: dict,
    model_key: tuple[str, str],
    code: str,
    detail: str,
    years: set[int],
    epa_ids: set[str],
    *,
    source_label: str | None = None,
    matched_variant_id: str | None = None,
    source_url: str | None = None,
    generation_candidates: set[str] | None = None,
) -> None:
    cell = store[model_key][(code, detail)]
    cell["years"].update(years)
    cell["epa_vehicle_ids"].update(epa_ids)
    if source_label:
        cell["source_labels"].add(source_label)
    if matched_variant_id:
        cell["matched_variant_ids"].add(matched_variant_id)
    if source_url:
        cell["source_urls"].add(source_url)
    if generation_candidates:
        cell["generation_candidates"].update(generation_candidates)


def issue_rows(store: dict, model_key: tuple[str, str], *, manual: bool) -> list[dict]:
    result = []
    for (code, detail), cell in store[model_key].items():
        if (code in MANUAL_CODES) != manual:
            continue
        result.append(
            {
                "code": code,
                "detail": detail,
                "model_year_ranges": year_ranges(cell["years"]),
                "model_year_count": len(cell["years"]),
                "epa_vehicle_ids": sorted(cell["epa_vehicle_ids"], key=int),
                "source_labels": sorted(cell["source_labels"]),
                "matched_variant_ids": sorted(cell["matched_variant_ids"]),
                "source_urls": sorted(cell["source_urls"]),
                "generation_candidates": sorted(cell["generation_candidates"]),
            }
        )
    return sorted(
        result,
        key=lambda row: (
            MANUAL_CODES.get(row["code"], 99),
            row["model_year_ranges"],
            row["detail"],
        ),
    )


def build_routes(
    candidates: list[dict],
    joined: list[dict],
    generation: list[dict],
    vpic: list[dict],
    powertrain: list[dict],
    *,
    approved_makes: list[str],
    expected_models: int,
) -> dict:
    by_id = require_unique(candidates, "epa_vehicle_id", "candidates")
    joins = require_unique(joined, "epa_vehicle_id", "join")
    if by_id.keys() != joins.keys():
        raise ValueError("JOIN_EPA_ID_COVERAGE_MISMATCH")
    model_rows: dict[tuple[str, str], list[dict]] = defaultdict(list)
    new_ids: set[str] = set()
    new_pairs: set[tuple[str, str, int]] = set()
    manual = defaultdict(issue_store)
    automated = defaultdict(issue_store)
    for epa_id, candidate in by_id.items():
        make, model, year = candidate["make"], candidate["model"], candidate["model_year"]
        key = (make, model)
        model_rows[key].append(candidate)
        joined_row = joins[epa_id]
        if (make, model, year) != (
            joined_row["make"],
            joined_row["model"],
            joined_row["model_year"],
        ):
            raise ValueError(f"JOIN_IDENTITY_MISMATCH: {epa_id}")
        classification = joined_row["classification"]
        if classification == "ALREADY_VERIFIED":
            continue
        if classification not in NEW_CLASSIFICATIONS:
            raise ValueError(f"UNRECOGNIZED_JOIN_CLASSIFICATION: {classification}")
        new_ids.add(epa_id)
        new_pairs.add((make, model, year))
        if classification == "CONFLICT":
            add_issue(
                manual, key, "CATALOG_IDENTITY_CONFLICT", joined_row["reason"],
                {year}, {epa_id}, matched_variant_id=joined_row.get("matched_variant_id"),
            )
        elif classification == "POSSIBLE_ALIAS":
            add_issue(
                manual, key, "MODEL_ALIAS_REVIEW", joined_row["reason"],
                {year}, {epa_id}, source_label=candidate["epa_model"],
                matched_variant_id=joined_row.get("matched_variant_id"),
            )
        power = candidate["normalized_powertrain"]
        drive = drivetrain_source_status(power.get("drive"))
        if drive != "EPA_DRIVE_LABEL":
            code = (
                "DRIVETRAIN_SOURCE_AMBIGUOUS"
                if drive == "AMBIGUOUS"
                else "DRIVETRAIN_SOURCE_UNMAPPED"
            )
            add_issue(
                manual, key, code, str(power.get("drive") or ""), {year}, {epa_id},
                source_label=str(power.get("drive") or ""),
            )
        if transmission_source_status(power.get("trany")) == "UNMAPPED":
            add_issue(
                manual, key, "TRANSMISSION_SOURCE_UNMAPPED",
                str(power.get("trany") or ""), {year}, {epa_id},
                source_label=str(power.get("trany") or ""),
            )
    if len(model_rows) != expected_models:
        raise ValueError(f"MODEL_DENOMINATOR_MISMATCH: {len(model_rows)} != {expected_models}")
    if {make for make, _ in model_rows} != set(approved_makes):
        raise ValueError("APPROVED_MAKE_SCOPE_MISMATCH")

    grouped_ids = [
        epa_id
        for group in powertrain
        for ids in group["epa_vehicle_ids_by_year"].values()
        for epa_id in ids
    ]
    if len(grouped_ids) != len(set(grouped_ids)) or set(grouped_ids) != by_id.keys():
        raise ValueError("POWERTRAIN_GROUP_EPA_ID_COVERAGE_MISMATCH")
    group_counts = Counter()
    for group in powertrain:
        represented_models = set()
        for year, ids in group["epa_vehicle_ids_by_year"].items():
            for epa_id in ids:
                candidate = by_id[epa_id]
                make, model = candidate["make"], candidate["model"]
                represented_models.add((make, model))
                if (make, int(year)) != (group["make"], candidate["model_year"]):
                    raise ValueError("POWERTRAIN_GROUP_IDENTITY_MISMATCH")
                if model != group["model"] and model.casefold() != group["model"].casefold():
                    raise ValueError("POWERTRAIN_GROUP_IDENTITY_MISMATCH")
        if any(model != group["model"] for _, model in represented_models):
            for key in represented_models:
                affected_ids = {
                    epa_id
                    for ids in group["epa_vehicle_ids_by_year"].values()
                    for epa_id in ids
                    if (by_id[epa_id]["make"], by_id[epa_id]["model"]) == key
                    and epa_id in new_ids
                }
                if affected_ids:
                    add_issue(
                        manual, key, "MODEL_ALIAS_REVIEW",
                        "POWERTRAIN_GROUP_NORMALIZES_DISTINCT_EPA_BASE_NAMES",
                        {by_id[epa_id]["model_year"] for epa_id in affected_ids},
                        affected_ids, source_label=group["model"],
                    )
        group_counts.update(represented_models)

    generation_pairs: set[tuple[str, str, int]] = set()
    generation_ids: set[str] = set()
    generation_research = []
    for segment in generation:
        key = (segment["make"], segment["model"])
        years = set(segment["observed_model_years"])
        ids = {
            epa_id
            for year in years
            for epa_id in segment["epa_vehicle_ids_by_year"][str(year)]
        }
        if generation_ids & ids:
            raise ValueError("GENERATION_EPA_ID_DUPLICATED")
        generation_ids.update(ids)
        if any(
            (by_id[epa_id]["make"], by_id[epa_id]["model"], by_id[epa_id]["model_year"])
            != (key[0], key[1], year)
            for year in years
            for epa_id in segment["epa_vehicle_ids_by_year"][str(year)]
        ):
            raise ValueError("GENERATION_EPA_IDENTITY_MISMATCH")
        if generation_pairs & {(key[0], key[1], year) for year in years}:
            raise ValueError("GENERATION_MODEL_YEAR_DUPLICATED")
        generation_pairs.update((key[0], key[1], year) for year in years)
        resolution = segment["generation_resolution"]
        labels = {choice["label"] for choice in segment["generation_candidates"]}
        if resolution == "AMBIGUOUS_GENERATION":
            add_issue(
                manual, key, "GENERATION_AMBIGUOUS", "COMPETING_GENERATION_LABELS",
                years, ids, generation_candidates=labels,
            )
        elif resolution in AUTO_GENERATION_CODES:
            code = AUTO_GENERATION_CODES[resolution]
            add_issue(
                automated, key, code, resolution, years, ids,
                generation_candidates=labels,
            )
            generation_research.append(
                {
                    "make": key[0], "model": key[1], "market": "USA",
                    "model_year_ranges": year_ranges(years),
                    "resolution": resolution, "route": "AUTOMATED_SOURCE_RESEARCH",
                    "generation_candidates": sorted(labels),
                    "epa_vehicle_ids_by_year": segment["epa_vehicle_ids_by_year"],
                    "publication_eligible": False,
                }
            )
        else:
            raise ValueError(f"UNRECOGNIZED_GENERATION_RESOLUTION: {resolution}")
    if generation_pairs != new_pairs or generation_ids != new_ids:
        raise ValueError("GENERATION_MODEL_YEAR_COVERAGE_MISMATCH")

    vpic_pairs = set()
    vpic_counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for item in vpic:
        make, model, year = item["make"], item["model"], item["model_year"]
        key = (make, model)
        vpic_pairs.add((make, model, year))
        vpic_counts[key][item["status"]] += 1
        if item["status"] == "VPIC_NAME_UNRESOLVED":
            ids = {
                candidate["epa_vehicle_id"]
                for candidate in model_rows[key]
                if candidate["model_year"] == year
                and candidate["epa_vehicle_id"] in new_ids
            }
            add_issue(
                manual, key, "VPIC_MODEL_NAME_UNRESOLVED", "VPIC_NAME_UNRESOLVED",
                {year}, ids, source_label=item.get("epa_model_example"),
                source_url=item.get("vpic_response_url"),
            )
        elif item["status"] == "VPIC_UNAVAILABLE":
            ids = {
                candidate["epa_vehicle_id"]
                for candidate in model_rows[key]
                if candidate["model_year"] == year
                and candidate["epa_vehicle_id"] in new_ids
            }
            add_issue(
                automated, key, "VPIC_RETRY", "SOURCE_UNAVAILABLE", {year}, ids,
                source_url=item.get("vpic_response_url"),
            )
        elif item["status"] not in {"VPIC_EXACT_BASE_MODEL", "VPIC_EXACT_EPA_MODEL"}:
            raise ValueError(f"UNRECOGNIZED_VPIC_STATUS: {item['status']}")
    if vpic_pairs != new_pairs or len(vpic) != len(new_pairs):
        raise ValueError("VPIC_MODEL_YEAR_COVERAGE_MISMATCH")

    make_order = {make: index for index, make in enumerate(approved_makes)}
    ordered_models = sorted(model_rows, key=lambda key: (make_order[key[0]], key[1].casefold()))
    models = []
    for make, model in ordered_models:
        key = (make, model)
        rows = model_rows[key]
        years = {row["model_year"] for row in rows}
        manual_issues = issue_rows(manual, key, manual=True)
        automated_issues = issue_rows(automated, key, manual=False)
        if manual_issues:
            route = "MANUAL_EXCEPTION_REVIEW"
        elif automated_issues:
            route = "AUTOMATED_SOURCE_RESEARCH"
        else:
            route = "AUTOMATED_BULK_CANDIDATE"
        models.append(
            {
                "make": make, "model": model, "market": "USA",
                "model_year_ranges": year_ranges(years),
                "epa_row_count": len(rows),
                "new_candidate_row_count": sum(
                    row["epa_vehicle_id"] in new_ids for row in rows
                ),
                "already_verified_epa_row_count": sum(
                    row["epa_vehicle_id"] not in new_ids for row in rows
                ),
                "powertrain_candidate_group_count": group_counts[key],
                "vpic_model_year_statuses": dict(sorted(vpic_counts[key].items())),
                "route": route,
                "manual_exceptions": manual_issues,
                "automated_research": automated_issues,
                "publication_eligible": False,
            }
        )
    generation_research.sort(
        key=lambda row: (
            make_order[row["make"]], row["model"].casefold(), row["model_year_ranges"]
        )
    )
    manual_codes_by_id: dict[str, set[str]] = defaultdict(set)
    automated_codes_by_id: dict[str, set[str]] = defaultdict(set)
    for model in models:
        for issue in model["manual_exceptions"]:
            for epa_id in issue["epa_vehicle_ids"]:
                manual_codes_by_id[epa_id].add(issue["code"])
        for issue in model["automated_research"]:
            for epa_id in issue["epa_vehicle_ids"]:
                automated_codes_by_id[epa_id].add(issue["code"])
    powertrain_routes = []
    for group in powertrain:
        year_routes = []
        for year, ids in sorted(group["epa_vehicle_ids_by_year"].items(), key=lambda x: int(x[0])):
            manual_ids = [epa_id for epa_id in ids if epa_id in manual_codes_by_id]
            automated_ids = [
                epa_id for epa_id in ids
                if epa_id in new_ids and epa_id not in manual_codes_by_id
            ]
            verified_ids = [epa_id for epa_id in ids if epa_id not in new_ids]
            if manual_ids and automated_ids:
                route = "MIXED_MANUAL_AND_AUTOMATED_CANDIDATES"
            elif manual_ids:
                route = "MANUAL_EXCEPTION_REVIEW"
            elif automated_ids:
                route = "AUTOMATED_BULK_CANDIDATE"
            else:
                route = "ALREADY_VERIFIED_REFERENCE"
            year_routes.append(
                {
                    "model_year": int(year), "route": route,
                    "manual_epa_vehicle_ids": sorted(manual_ids, key=int),
                    "automated_epa_vehicle_ids": sorted(automated_ids, key=int),
                    "already_verified_epa_vehicle_ids": sorted(verified_ids, key=int),
                    "manual_exception_codes": sorted(
                        {code for epa_id in manual_ids for code in manual_codes_by_id[epa_id]}
                    ),
                    "automated_research_codes": sorted(
                        {
                            code for epa_id in ids
                            for code in automated_codes_by_id[epa_id]
                        }
                    ),
                }
            )
        group_routes = {year["route"] for year in year_routes}
        route = next(iter(group_routes)) if len(group_routes) == 1 else "MIXED_YEAR_ROUTES"
        powertrain_routes.append(
            {
                "make": group["make"], "model": group["model"],
                "market": "USA", "model_year_start": group["model_year_start"],
                "model_year_end": group["model_year_end"],
                "normalized_powertrain_key": group["normalized_powertrain_key"],
                "epa_models": group["epa_models"],
                "route": route, "years": year_routes,
                "publication_eligible": False,
            }
        )
    return {
        "models": models,
        "manual_models": [row for row in models if row["manual_exceptions"]],
        "generation_research": generation_research,
        "powertrain_routes": powertrain_routes,
        "new_model_year_pairs": len(new_pairs),
    }


def run(source: Path = SOURCE, out: Path = DEFAULT_OUT) -> dict:
    index_path = source / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paths = {key: source / name for key, name in INPUTS.items()}
    raw = {key: path.read_bytes() for key, path in paths.items()}
    rows = {key: read_jsonl(path) for key, path in paths.items()}
    approved = index["scope"]["approved_makes"]
    result = build_routes(
        rows["candidates"], rows["join"], rows["generation"],
        rows["vpic"], rows["powertrain"],
        approved_makes=approved,
        expected_models=index["denominator"]["unique_models"],
    )
    outputs = {
        "model-routing.jsonl": result["models"],
        "manual-review.jsonl": result["manual_models"],
        "automated-generation-research.jsonl": result["generation_research"],
        "powertrain-routing.jsonl": result["powertrain_routes"],
    }
    payloads = {name: canonical_lines(items) for name, items in outputs.items()}
    manual_counts = Counter(
        issue["code"]
        for model in result["manual_models"]
        for issue in model["manual_exceptions"]
    )
    route_counts = Counter(model["route"] for model in result["models"])
    powertrain_route_counts = Counter(
        route["route"] for route in result["powertrain_routes"]
    )
    powertrain_year_route_counts = Counter(
        year["route"]
        for route in result["powertrain_routes"]
        for year in route["years"]
    )
    summary = {
        "router_version": "us-catalog-exception-router-1",
        "scope": {"market": "USA", "approved_makes": approved},
        "inputs": {
            "index": {
                "path": str(index_path.relative_to(ROOT)),
                "sha256": digest(index_path.read_bytes()),
            },
            **{
                key: {"path": str(path.relative_to(ROOT)), "sha256": digest(raw[key])}
                for key, path in paths.items()
            },
        },
        "counts": {
            "brands": len(approved),
            "models_in_denominator": len(result["models"]),
            "epa_candidate_rows": len(rows["candidates"]),
            "already_verified_epa_rows": sum(
                model["already_verified_epa_row_count"] for model in result["models"]
            ),
            "new_nonpublished_epa_rows": sum(
                model["new_candidate_row_count"] for model in result["models"]
            ),
            "new_model_year_pairs": result["new_model_year_pairs"],
            "powertrain_candidate_groups": len(rows["powertrain"]),
            "model_routes": dict(sorted(route_counts.items())),
            "powertrain_group_routes": dict(sorted(powertrain_route_counts.items())),
            "powertrain_group_year_routes": dict(
                sorted(powertrain_year_route_counts.items())
            ),
            "manual_review_models": len(result["manual_models"]),
            "manual_issue_groups_by_code": {
                code: manual_counts[code] for code in MANUAL_CODES
            },
            "automated_generation_segments": len(result["generation_research"]),
        },
        "definitions": {
            "manual_exception": (
                "Grouped model-level conflict, alias/name mismatch, competing generation "
                "labels, or EPA transmission/drivetrain source label that cannot be assigned "
                "even to a broad source category. This is a review route, not verification."
            ),
            "automated_generation_research": (
                "Contiguous model-year segment with no generation label, an unverified "
                "prior AI label, or a verified reference that still needs tuple applicability."
            ),
            "normal_bulk_candidate": (
                "EPA tuple stays in powertrain-groups.jsonl for batch factory-source "
                "verification, even if another tuple in the same model has an exception. "
                "Similarity, vPIC model presence and EPA labels never publish it."
            ),
        },
        "outputs": {
            name: {"rows": len(outputs[name]), "sha256": digest(content)}
            for name, content in payloads.items()
        },
        "publication_eligible": False,
        "newly_verified_models": 0,
        "db_writes": 0,
        "network_calls": 0,
    }
    out.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        (out / name).write_bytes(content)
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.out)["counts"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
