"""Split EPA powertrain runs at observed generation-hypothesis boundaries.

This is a draft grouping artifact. A published generation label from an exact
model year is a review hint for a new EPA tuple, not transferred verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-catalog-universe"


def source_years(segments: Path) -> dict[tuple[str, str, int], tuple[str | None, str]]:
    mapping = {}
    for line in segments.open(encoding="utf-8"):
        segment = json.loads(line)
        for year in segment["observed_model_years"]:
            key = segment["make"], segment["model"], year
            if key in mapping:
                raise ValueError(f"DUPLICATE_GENERATION_YEAR: {key}")
            mapping[key] = (
                segment["generation"],
                segment["generation_resolution"],
            )
    return mapping


def split_group(group: dict, mapping: dict) -> list[dict]:
    """Preserve source rows and year gaps while splitting at label changes."""
    outputs = []
    current = None
    for year in group["model_years"]:
        key = group["make"], group["model"], year
        generation, resolution = mapping.get(key, (None, "NO_CANDIDATE_MAPPING"))
        identity = generation, resolution
        if (
            current is None
            or year != current["model_years"][-1] + 1
            or identity != (current["generation_candidate"], current["generation_resolution"])
        ):
            if current:
                outputs.append(current)
            current = {
                **{
                    k: v
                    for k, v in group.items()
                    if k
                    not in {
                        "epa_vehicle_ids_by_year",
                        "epa_row_count",
                        "model_year_start",
                        "model_year_end",
                        "model_years",
                        "generation",
                        "generation_status",
                        "epa_models",
                        "status",
                    }
                },
                "generation_candidate": generation,
                "generation_resolution": resolution,
                "model_years": [],
                "epa_vehicle_ids_by_year": {},
                "status": "GENERATION_SCOPED_POWERTRAIN_DRAFT_NOT_FACTORY_VERIFIED",
                "publication_eligible": False,
            }
        current["model_years"].append(year)
        current["epa_vehicle_ids_by_year"][str(year)] = group["epa_vehicle_ids_by_year"][str(year)]
    if current:
        outputs.append(current)
    for item in outputs:
        item["model_year_start"] = item["model_years"][0]
        item["model_year_end"] = item["model_years"][-1]
        item["epa_row_count"] = sum(len(ids) for ids in item["epa_vehicle_ids_by_year"].values())
    return outputs


def run(groups: Path, segments: Path, out: Path) -> dict:
    mapping = source_years(segments)
    inputs = [json.loads(line) for line in groups.open(encoding="utf-8")]
    result = [part for group in inputs for part in split_group(group, mapping)]
    before = [
        vehicle_id
        for group in inputs
        for ids in group["epa_vehicle_ids_by_year"].values()
        for vehicle_id in ids
    ]
    after = [
        vehicle_id
        for group in result
        for ids in group["epa_vehicle_ids_by_year"].values()
        for vehicle_id in ids
    ]
    if len(before) != len(set(before)) or sorted(before) != sorted(after):
        raise ValueError("EPA_ROW_COVERAGE_MISMATCH")
    out.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in result)
    output = out / "generation-scoped-powertrain-groups.jsonl"
    output.write_text(payload, encoding="utf-8")
    counts = Counter(x["generation_resolution"] for x in result)
    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_group_count": len(inputs),
        "derived_group_count": len(result),
        "epa_rows_preserved": len(after),
        "generation_resolution_groups": dict(sorted(counts.items())),
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "publication_eligible": False,
        "method_limit": (
            "Exact observed-year generation hints split candidate groups; "
            "they do not verify new tuples or infer missing years."
        ),
    }
    (out / "generation-scoped-powertrain-groups-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", type=Path, default=OUT / "powertrain-groups.jsonl")
    parser.add_argument("--generations", type=Path, default=OUT / "generation-hypotheses.jsonl")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.groups, args.generations, args.out), ensure_ascii=False))
