"""Map candidate US EPA model years to non-publishable generation hypotheses.

Only exact-year published generations and earlier explicitly scoped AI drafts may
seed a label. Missing years remain null; neighbouring years are never filled by
interpolation. EPA body strings are retained as candidate aliases, not identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-catalog-universe"
UNIVERSE = OUT / "candidates.jsonl"
JOIN = OUT / "candidate-join.jsonl"
PRIOR_QUEUE = ROOT / "data/manifests/us-ai-verify-09-queue.json"
PRIOR_DRAFTS = (
    ROOT / "deliverables/VerifiedData/us-ai-verify-09/ai-drafts.jsonl",
    ROOT / "deliverables/VerifiedData/us-base-catalog-07/ai-work/ai-drafts-07.jsonl",
)
PARSER_VERSION = "us-generation-hypotheses-1"
TARGET_CLASSIFICATIONS = {"CANDIDATE_NEW", "POSSIBLE_ALIAS", "CONFLICT"}
BODY_ALIASES = (
    (r"\b(?:coupe|coupé)\b", "COUPE"),
    (r"\b(?:convertible|cabriolet|cabrio)\b", "CONVERTIBLE"),
    (r"\b(?:wagon|station wagon|avant|estate)\b", "WAGON"),
    (r"\b(?:hatchback|hatch)\b", "HATCHBACK"),
    (r"\b(?:sport utility vehicle|suv)\b", "SUV"),
    (r"\b(?:pickup|pick-up)\b", "PICKUP"),
    (r"\b(?:minivan)\b", "MINIVAN"),
    (r"\b(?:roadster)\b", "ROADSTER"),
    (r"\b(?:sportback)\b", "SPORTBACK"),
    (r"\b(?:sedan)\b", "SEDAN"),
)


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(value: str | None) -> str:
    return " ".join((value or "").casefold().replace("–", "-").split())


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def model_year_key(make: str, model: str, year: int) -> tuple[str, str, int]:
    return normalize(make), normalize(model), int(year)


def index_published(published: list[dict]) -> dict[tuple, list[dict]]:
    result: dict[tuple, list[dict]] = defaultdict(list)
    for record in published:
        generation = record.get("generation")
        if not generation or record.get("market") not in {"US", "USA"}:
            continue
        key = model_year_key(record["make"], record["model"], record["model_year"])
        result[key].append(
            {
                "label": generation,
                "origin": "PUBLISHED_BASE_READY_EXACT_YEAR_REFERENCE",
                "source_ref": record["variant_id"],
                "body": record.get("body"),
            }
        )
    return result


def index_prior_drafts(queue: dict, draft_sources: list[tuple[str, list[dict]]]) -> dict:
    result: dict[tuple, list[dict]] = defaultdict(list)
    for item in queue["queue"]:
        label = item.get("generation_candidate")
        if not label or item.get("market") != "US":
            continue
        for year in item.get("target_model_years", []):
            key = model_year_key(item["make"], item["model"], year)
            result[key].append(
                {
                    "label": label,
                    "origin": "PRIOR_AI_DRAFT",
                    "source_ref": f"{PRIOR_QUEUE.relative_to(ROOT)}#{item['queue_id']}",
                    "body": None,
                }
            )
    for path, drafts in draft_sources:
        for draft in drafts:
            fields = draft.get("fields", {})

            def value(name, source_fields=fields):
                return source_fields.get(name, {}).get("value")

            label = value("generation")
            if not label or value("market") != "US":
                continue
            for year in value("model_years") or []:
                key = model_year_key(value("make"), value("model"), year)
                result[key].append(
                    {
                        "label": label,
                        "origin": "PRIOR_AI_DRAFT",
                        "source_ref": f"{path}#{draft['id']}",
                        "body": value("body"),
                    }
                )
    return result


def epa_body_aliases(source_rows: list[dict]) -> list[dict]:
    aliases: set[tuple[str, str]] = set()
    for row in source_rows:
        fields = row["epa_fields"]
        for basis, text in (
            ("EPA_RAW_MODEL_STRING", row["epa_model"]),
            ("EPA_VCLASS_STRING", fields.get("VClass", "")),
        ):
            for pattern, alias in BODY_ALIASES:
                if re.search(pattern, text or "", flags=re.IGNORECASE):
                    aliases.add((alias, basis))
    return [
        {"alias": alias, "basis": basis, "status": "CANDIDATE_ONLY"}
        for alias, basis in sorted(aliases)
    ]


def generation_choices(references: list[dict]) -> list[dict]:
    grouped: dict[tuple, dict] = {}
    for ref in references:
        key = ref["label"], ref["origin"]
        item = grouped.setdefault(
            key,
            {
                "label": ref["label"],
                "origin": ref["origin"],
                "source_refs": set(),
                "body_values": set(),
            },
        )
        item["source_refs"].add(ref["source_ref"])
        if ref.get("body"):
            item["body_values"].add(ref["body"])
    return [
        {
            **{
                key: value
                for key, value in item.items()
                if key not in {"source_refs", "body_values"}
            },
            "source_refs": sorted(item["source_refs"]),
            "body_values": sorted(item["body_values"]),
        }
        for _, item in sorted(grouped.items())
    ]


def year_resolution(choices: list[dict]) -> tuple[str, str | None]:
    labels = {choice["label"] for choice in choices}
    if not labels:
        return "UNRESOLVED_GENERATION", None
    if len(labels) > 1:
        return "AMBIGUOUS_GENERATION", None
    if any(choice["origin"].startswith("PUBLISHED") for choice in choices):
        return "EXACT_YEAR_VERIFIED_REFERENCE_REQUIRES_APPLICABILITY", next(iter(labels))
    return "PRIOR_AI_HYPOTHESIS_UNVERIFIED", next(iter(labels))


def candidate_years(
    candidates: list[dict],
    joined: list[dict],
    published_index: dict,
    draft_index: dict,
) -> list[dict]:
    by_id = {row["epa_vehicle_id"]: row for row in candidates}
    if len(by_id) != len(candidates) or len(joined) != len(candidates):
        raise ValueError("UNIVERSE_JOIN_ROW_COUNT_MISMATCH")
    if {row["epa_vehicle_id"] for row in joined} != set(by_id):
        raise ValueError("UNIVERSE_JOIN_ID_MISMATCH")
    grouped: dict[tuple, list[tuple[dict, dict]]] = defaultdict(list)
    for item in joined:
        if item["classification"] not in TARGET_CLASSIFICATIONS:
            continue
        source = by_id[item["epa_vehicle_id"]]
        key = model_year_key(item["make"], item["model"], item["model_year"])
        grouped[key].append((item, source))
    result = []
    for key, pairs in sorted(grouped.items()):
        first = pairs[0][0]
        choices = generation_choices(published_index.get(key, []) + draft_index.get(key, []))
        resolution, label = year_resolution(choices)
        source_rows = [source for _, source in pairs]
        result.append(
            {
                "make": first["make"],
                "model": first["model"],
                "model_year": first["model_year"],
                "generation_hypothesis": label,
                "generation_candidates": choices,
                "generation_resolution": resolution,
                "epa_vehicle_ids": sorted(
                    (item["epa_vehicle_id"] for item, _ in pairs), key=int
                ),
                "epa_model_strings": sorted(
                    {source["epa_model"] for source in source_rows}, key=normalize
                ),
                "epa_vclasses": sorted(
                    {source["epa_fields"].get("VClass", "") for source in source_rows}
                    - {""},
                    key=normalize,
                ),
                "body_aliases_candidate": epa_body_aliases(source_rows),
                "join_classifications": dict(
                    sorted(Counter(item["classification"] for item, _ in pairs).items())
                ),
            }
        )
    return result


def segment_years(years: list[dict]) -> list[dict]:
    """Coalesce only consecutive observed MYs with identical generation choices."""
    by_model: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for year in years:
        by_model[(year["make"], year["model"])].append(year)
    segments = []
    for (make, model), model_years in sorted(by_model.items()):
        model_years.sort(key=lambda row: row["model_year"])
        runs: list[list[dict]] = []
        current: list[dict] = []
        for item in model_years:
            signature = (
                item["generation_resolution"],
                item["generation_hypothesis"],
                tuple(
                    sorted(
                        (choice["label"], choice["origin"])
                        for choice in item["generation_candidates"]
                    )
                ),
            )
            prior_signature = None
            if current:
                prior = current[-1]
                prior_signature = (
                    prior["generation_resolution"],
                    prior["generation_hypothesis"],
                    tuple(
                        sorted(
                            (choice["label"], choice["origin"])
                            for choice in prior["generation_candidates"]
                        )
                    ),
                )
            if current and (
                item["model_year"] != current[-1]["model_year"] + 1
                or signature != prior_signature
            ):
                runs.append(current)
                current = []
            current.append(item)
        if current:
            runs.append(current)
        for run in runs:
            choices = generation_choices(
                [
                    {
                        "label": choice["label"],
                        "origin": choice["origin"],
                        "source_ref": ref,
                        "body": body,
                    }
                    for year in run
                    for choice in year["generation_candidates"]
                    for ref in choice["source_refs"]
                    for body in (choice["body_values"] or [None])
                ]
            )
            aliases = {
                (entry["alias"], entry["basis"])
                for year in run
                for entry in year["body_aliases_candidate"]
            }
            classifications = Counter()
            for year in run:
                classifications.update(year["join_classifications"])
            segments.append(
                {
                    "make": make,
                    "model": model,
                    "market": "USA",
                    "generation": run[0]["generation_hypothesis"],
                    "year_start": run[0]["model_year"],
                    "year_end": run[-1]["model_year"],
                    "observed_model_years": [year["model_year"] for year in run],
                    "generation_candidates": choices,
                    "generation_resolution": run[0]["generation_resolution"],
                    "generation_boundaries_verified": False,
                    "body_aliases_candidate": [
                        {"alias": alias, "basis": basis, "status": "CANDIDATE_ONLY"}
                        for alias, basis in sorted(aliases)
                    ],
                    "epa_vclasses": sorted(
                        {name for year in run for name in year["epa_vclasses"]},
                        key=normalize,
                    ),
                    "epa_models": sorted(
                        {name for year in run for name in year["epa_model_strings"]},
                        key=normalize,
                    ),
                    "epa_vehicle_ids_by_year": {
                        str(year["model_year"]): year["epa_vehicle_ids"] for year in run
                    },
                    "join_classifications": dict(sorted(classifications.items())),
                    "status": "AI_GENERATION_DRAFT",
                    "publication_eligible": False,
                }
            )
    return segments


def load_published() -> list[dict]:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.db.session import SessionLocal  # noqa: PLC0415
    from app.services.catalog_buyer import active_us_base_rows, records  # noqa: PLC0415

    with SessionLocal() as db:
        return [
            {
                "make": catalog["make"],
                "model": catalog["model"],
                "model_year": catalog["model_year"],
                "generation": catalog.get("generation"),
                "market": catalog["original_market"],
                "body": catalog.get("facts", {}).get("body", {}).get("value"),
                "variant_id": variant.id,
            }
            for variant, catalog in active_us_base_rows(records(db))
        ]


def run(out: Path) -> dict:
    source_bytes = UNIVERSE.read_bytes()
    join_bytes = JOIN.read_bytes()
    candidates = read_jsonl(UNIVERSE)
    joined = read_jsonl(JOIN)
    published = load_published()
    queue = json.loads(PRIOR_QUEUE.read_text(encoding="utf-8"))
    drafts = [(str(path.relative_to(ROOT)), read_jsonl(path)) for path in PRIOR_DRAFTS]
    years = candidate_years(
        candidates,
        joined,
        index_published(published),
        index_prior_drafts(queue, drafts),
    )
    segments = segment_years(years)
    segment_bytes = b"".join(canonical_json(segment) + b"\n" for segment in segments)
    resolution_counts = dict(
        sorted(Counter(year["generation_resolution"] for year in years).items())
    )
    models = {(year["make"], year["model"]) for year in years}
    resolved_models = {
        (year["make"], year["model"])
        for year in years
        if year["generation_resolution"] != "UNRESOLVED_GENERATION"
    }
    makes = sorted({year["make"] for year in years})
    by_make = [
        {
            "make": make,
            "candidate_models": len({year["model"] for year in years if year["make"] == make}),
            "candidate_model_year_pairs": sum(year["make"] == make for year in years),
            "exact_year_published_references": sum(
                year["make"] == make
                and year["generation_resolution"]
                == "EXACT_YEAR_VERIFIED_REFERENCE_REQUIRES_APPLICABILITY"
                for year in years
            ),
            "prior_ai_year_hypotheses": sum(
                year["make"] == make
                and year["generation_resolution"] == "PRIOR_AI_HYPOTHESIS_UNVERIFIED"
                for year in years
            ),
            "ambiguous_years": sum(
                year["make"] == make
                and year["generation_resolution"] == "AMBIGUOUS_GENERATION"
                for year in years
            ),
            "unresolved_years": sum(
                year["make"] == make
                and year["generation_resolution"] == "UNRESOLVED_GENERATION"
                for year in years
            ),
        }
        for make in makes
    ]
    ambiguous = [
        {
            "make": year["make"],
            "model": year["model"],
            "model_year": year["model_year"],
            "candidate_labels": sorted(
                {choice["label"] for choice in year["generation_candidates"]}
            ),
        }
        for year in years
        if year["generation_resolution"] == "AMBIGUOUS_GENERATION"
    ]
    summary = {
        "parser_version": PARSER_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "input": {
            "universe_path": str(UNIVERSE.relative_to(ROOT)),
            "universe_sha256": digest(source_bytes),
            "join_path": str(JOIN.relative_to(ROOT)),
            "join_sha256": digest(join_bytes),
            "published_base_ready_reference_rows": len(published),
            "prior_queue_path": str(PRIOR_QUEUE.relative_to(ROOT)),
            "prior_ai_draft_paths": [str(path.relative_to(ROOT)) for path in PRIOR_DRAFTS],
        },
        "counts": {
            "candidate_models": len(models),
            "candidate_models_with_any_generation_reference": len(resolved_models),
            "candidate_model_year_pairs": len(years),
            "hypothesis_segments": len(segments),
            "segments_with_null_generation": sum(
                segment["generation"] is None for segment in segments
            ),
            "model_year_resolutions": resolution_counts,
            "candidate_epa_rows": sum(
                len(year["epa_vehicle_ids"]) for year in years
            ),
        },
        "brands": by_make,
        "ambiguous_generation_years": ambiguous,
        "output_sha256": digest(segment_bytes),
        "status": "AI_GENERATION_DRAFT_ONLY",
        "publication_eligible": False,
        "db_writes": 0,
        "network_calls": 0,
        "method_limit": (
            "Exact-year published scope is a reference for candidate review, not a "
            "verified assignment to an unmatched EPA tuple. Prior AI labels remain "
            "unverified; absent years and competing labels are unresolved."
        ),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "generation-hypotheses.jsonl").write_bytes(segment_bytes)
    (out / "generation-hypotheses-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps(result["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
