"""Build the complete US EPA candidate universe for the owner-approved 17 makes.

This is a read-only research index. EPA test rows are not factory trims, confirmed
generations, or publishable BASE_READY vehicle configurations. The source is the
already acquired official FuelEconomy.gov bulk ZIP; no per-vehicle API calls occur.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data/manifests/az-market-priority-policy.json"
SOURCE_ZIP = ROOT / ".localdata/epa-bulk-cache/vehicles-current.zip"
SOURCE_INDEX = ROOT / "deliverables/VerifiedData/us-bulk-data-08/epa-index.json"
DEFAULT_OUT = ROOT / "deliverables/VerifiedData/us-catalog-universe"
SOURCE_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
PARSER_VERSION = "us-catalog-candidate-universe-1"
REQUIRED_COLUMNS = {
    "id",
    "make",
    "model",
    "baseModel",
    "year",
    "displ",
    "cylinders",
    "trany",
    "drive",
    "fuelType1",
    "eng_dscr",
    "evMotor",
    "VClass",
}
POWERTRAIN_COLUMNS = (
    "displ",
    "cylinders",
    "fuelType1",
    "fuelType2",
    "atvType",
    "tCharger",
    "sCharger",
    "eng_dscr",
    "evMotor",
    "trany",
    "trans_dscr",
    "drive",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def normalize(value: str | None) -> str:
    return " ".join((value or "").casefold().replace("–", "-").split())


def displacement(value: str | None) -> str:
    """Canonicalize only a numeric EPA displacement; retain source text elsewhere."""
    try:
        return str(Decimal(value).normalize()) if value else ""
    except InvalidOperation:
        return normalize(value)


def approved_scope(policy: dict) -> tuple[list[str], dict[str, int]]:
    makes = policy["primary_makes"]
    assert len(makes) == len(set(makes)) == 17, "APPROVED_MAKE_SCOPE_CHANGED"
    assert policy["allowed_markets"] == ["US"], "US_ONLY_SCOPE_CHANGED"
    years = {
        make: policy.get("minimum_model_year_overrides", {}).get(make, policy["minimum_model_year"])
        for make in makes
    }
    assert years["Mercedes-Benz"] == years["BMW"] == 2000
    assert all(years[make] == 2005 for make in makes if make not in {"Mercedes-Benz", "BMW"})
    return makes, years


def normalized_powertrain(row: dict[str, str]) -> dict[str, str]:
    result = {column: normalize(row.get(column)) for column in POWERTRAIN_COLUMNS}
    result["displ"] = displacement(row.get("displ"))
    return result


def candidate(row: dict[str, str], source_sha256: str) -> dict:
    model = (row.get("baseModel") or row["model"]).strip()
    powertrain = normalized_powertrain(row)
    powertrain_identity = {
        "make": normalize(row["make"]),
        "model": normalize(model),
        **powertrain,
    }
    return {
        "epa_vehicle_id": row["id"],
        "make": row["make"],
        "model": model,
        "epa_model": row["model"],
        "model_year": int(row["year"]),
        "model_basis": "EPA_BASE_MODEL"
        if row.get("baseModel", "").strip()
        else "EPA_RAW_MODEL_FALLBACK",
        "normalized_powertrain": powertrain,
        "normalized_powertrain_key": digest(canonical_json(powertrain_identity)),
        "missing_core_fields": [
            label
            for label, present in (
                ("engine_or_ev_motor", bool(row.get("displ") or row.get("evMotor"))),
                ("fuel_type", bool(row.get("fuelType1") or row.get("fuelType"))),
                ("transmission", bool(row.get("trany"))),
                ("drivetrain", bool(row.get("drive"))),
            )
            if not present
        ],
        "epa_fields": row.copy(),
        "source": {
            "dataset": SOURCE_URL,
            "dataset_sha256": source_sha256,
            "row_locator": f"vehicles.csv:id={row['id']}",
        },
    }


def select_universe(
    reader: csv.DictReader, policy: dict, source_sha256: str
) -> tuple[list[dict], dict, list[str]]:
    columns = reader.fieldnames or []
    if not set(columns) >= REQUIRED_COLUMNS:
        raise ValueError("EPA_SCHEMA_CHANGED")
    makes, min_years = approved_scope(policy)
    make_set = set(makes)
    counts = Counter()
    seen_ids: set[str] = set()
    rows = []
    for row in reader:
        counts["source_rows"] += 1
        if row["make"] not in make_set:
            counts["other_make_rows"] += 1
            continue
        try:
            year = int(row["year"])
        except (ValueError, TypeError):
            counts["invalid_year_in_approved_make"] += 1
            continue
        if year < min_years[row["make"]]:
            counts["below_make_year_boundary"] += 1
            continue
        if not row["id"] or row["id"] in seen_ids:
            raise ValueError(f"EPA_DUPLICATE_OR_EMPTY_ID:{row['id']}")
        seen_ids.add(row["id"])
        rows.append(candidate(row, source_sha256))
    make_order = {make: number for number, make in enumerate(makes)}
    rows.sort(
        key=lambda r: (
            make_order[r["make"]],
            normalize(r["model"]),
            r["model_year"],
            int(r["epa_vehicle_id"]),
        )
    )
    counts["candidate_rows"] = len(rows)
    return rows, dict(sorted(counts.items())), columns


def denominator(rows: list[dict], makes: list[str]) -> dict:
    by_make: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_make[row["make"]].append(row)
    brands = []
    for make in makes:
        subset = by_make[make]
        model_names = sorted({row["model"] for row in subset}, key=normalize)
        years = [row["model_year"] for row in subset]
        brands.append(
            {
                "make": make,
                "models_discovered": len(model_names),
                "model_names": model_names,
                "earliest_my": min(years) if years else None,
                "latest_my": max(years) if years else None,
                "model_year_pairs": len({(row["model"], row["model_year"]) for row in subset}),
                "candidate_combinations": len({row["normalized_powertrain_key"] for row in subset}),
                "candidate_model_year_powertrain_combinations": len(
                    {(row["model_year"], row["normalized_powertrain_key"]) for row in subset}
                ),
                "epa_rows": len(subset),
                "rows_with_missing_core_fields": sum(
                    bool(row["missing_core_fields"]) for row in subset
                ),
            }
        )
    return {
        "unique_brands": len({row["make"] for row in rows}),
        "unique_models": len({(row["make"], row["model"]) for row in rows}),
        "model_year_pairs": len({(row["make"], row["model"], row["model_year"]) for row in rows}),
        "normalized_powertrain_combinations": len(
            {row["normalized_powertrain_key"] for row in rows}
        ),
        "model_year_powertrain_combinations": len(
            {(row["model_year"], row["normalized_powertrain_key"]) for row in rows}
        ),
        "epa_rows_after_filter": len(rows),
        "brands": brands,
    }


def contiguous_powertrain_groups(rows: list[dict], makes: list[str]) -> list[dict]:
    """One candidate group per uninterrupted MY run, preserving absent-year gaps.

    Generation is deliberately unmapped here. A later independent OEM-backed
    generation mapping may split these provisional source groups further.
    """
    by_key: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_key[row["normalized_powertrain_key"]].append(row)
    groups = []
    for key, subset in by_key.items():
        years = sorted({row["model_year"] for row in subset})
        spans = []
        span = [years[0]]
        for year in years[1:]:
            if year == span[-1] + 1:
                span.append(year)
            else:
                spans.append(span)
                span = [year]
        spans.append(span)
        representative = subset[0]
        for span in spans:
            span_rows = [row for row in subset if row["model_year"] in span]
            ids_by_year = {
                str(year): sorted(
                    (row["epa_vehicle_id"] for row in span_rows if row["model_year"] == year),
                    key=int,
                )
                for year in span
            }
            groups.append(
                {
                    "make": representative["make"],
                    "model": representative["model"],
                    "generation": None,
                    "generation_status": "UNMAPPED_CANDIDATE",
                    "market": "USA",
                    "model_year_start": span[0],
                    "model_year_end": span[-1],
                    "model_years": span,
                    "normalized_powertrain_key": key,
                    "normalized_powertrain": representative["normalized_powertrain"],
                    "epa_vehicle_ids_by_year": ids_by_year,
                    "epa_models": sorted({row["epa_model"] for row in span_rows}, key=normalize),
                    "epa_row_count": len(span_rows),
                    "missing_core_fields": sorted(
                        {field for row in span_rows for field in row["missing_core_fields"]}
                    ),
                    "status": "EPA_POWERTRAIN_GROUP_CANDIDATE_NOT_FACTORY_VERIFIED",
                }
            )
    make_order = {make: number for number, make in enumerate(makes)}
    groups.sort(
        key=lambda group: (
            make_order[group["make"]],
            normalize(group["model"]),
            group["model_year_start"],
            group["normalized_powertrain_key"],
        )
    )
    return groups


def report_markdown(index: dict) -> str:
    d = index["denominator"]
    lines = [
        "# US catalog candidate universe — EPA bulk",
        "",
        "Candidate evidence only. These EPA test rows do not certify generation, "
        "factory trim, or BASE_READY.",
        "",
        f"Source: {SOURCE_URL}",
        (
            f"Source ZIP SHA-256: `{index['source']['zip_sha256']}`; "
            f"acquired: {index['source']['acquired_at']}."
        ),
        "",
        (
            f"Brands: **{d['unique_brands']}**; EPA base models: **{d['unique_models']}**; "
            f"model-year pairs: **{d['model_year_pairs']}**; normalized model-powertrain "
            f"combinations: **{d['normalized_powertrain_combinations']}**; contiguous "
            f"powertrain-year groups: **{d['contiguous_powertrain_groups']}**; "
            f"EPA rows: **{d['epa_rows_after_filter']}**."
        ),
        "",
        (
            "The latest model year is taken from this EPA snapshot, including "
            "future-model-year rows where present; no upper-year cap was added "
            "to the owner's lower-bound scope. A base model is EPA's grouping "
            "label, not an independently verified OEM model/generation. Blank "
            "EPA engine/transmission/drive fields remain candidates flagged "
            "for exception handling."
        ),
        "",
        (
            "| Make | Models discovered | Earliest MY | Latest MY | "
            "Candidate combinations | Model-year pairs | EPA rows |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for brand in d["brands"]:
        lines.append(
            f"| {brand['make']} | {brand['models_discovered']} | "
            f"{brand['earliest_my']} | {brand['latest_my']} | "
            f"{brand['candidate_combinations']} | {brand['model_year_pairs']} | "
            f"{brand['epa_rows']} |"
        )
    lines += [
        "",
        (
            "`candidates.jsonl` retains every original CSV column as `epa_fields`, "
            "paired exactly as in the EPA row. `powertrain-groups.jsonl` groups "
            "equal normalized source tuples only across uninterrupted model-year "
            "spans; generation is still unverified. `index.json` contains the "
            "complete per-brand model names and source/provenance. No individual "
            "vehicle API call or database publication occurred."
        ),
        "",
    ]
    return "\n".join(lines)


def run(source: Path, source_index: Path, out: Path) -> dict:
    source_bytes = source.read_bytes()
    source_sha256 = digest(source_bytes)
    prior = json.loads(source_index.read_text(encoding="utf-8"))
    if prior["identity"]["source_sha256"] != source_sha256 or prior["source_url"] != SOURCE_URL:
        raise ValueError("LOCAL_EPA_ZIP_PROVENANCE_MISMATCH")
    policy_bytes = POLICY.read_bytes()
    policy = json.loads(policy_bytes)
    makes, min_years = approved_scope(policy)
    with zipfile.ZipFile(io.BytesIO(source_bytes)) as archive:
        if archive.namelist() != ["vehicles.csv"]:
            raise ValueError("EPA_ZIP_LAYOUT_CHANGED")
        with archive.open("vehicles.csv") as csv_stream:
            text_stream = io.TextIOWrapper(csv_stream, encoding="utf-8-sig", newline="")
            rows, selection_counts, columns = select_universe(
                csv.DictReader(text_stream), policy, source_sha256
            )
    if not rows or len(columns) < 70:
        raise ValueError("EPA_BULK_SOURCE_INCOMPLETE")
    output_bytes = b"".join(canonical_json(row) + b"\n" for row in rows)
    groups = contiguous_powertrain_groups(rows, makes)
    group_bytes = b"".join(canonical_json(group) + b"\n" for group in groups)
    counts = denominator(rows, makes)
    counts["contiguous_powertrain_groups"] = len(groups)
    index = {
        "parser_version": PARSER_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "scope": {
            "market": "USA",
            "approved_makes": makes,
            "minimum_model_year_by_make": min_years,
            "maximum_model_year": None,
            "upper_year_rule": (
                "no owner-specified upper cap; use all model years in source snapshot"
            ),
        },
        "source": {
            "url": SOURCE_URL,
            "zip_sha256": source_sha256,
            "zip_bytes": len(source_bytes),
            "acquired_at": prior.get("source_acquired_at"),
            "csv_columns": columns,
            "network_calls_this_run": 0,
        },
        "selection_counts": selection_counts,
        "denominator": counts,
        "candidate_jsonl_sha256": digest(output_bytes),
        "powertrain_groups_jsonl_sha256": digest(group_bytes),
        "candidate_status": "EPA_RESEARCH_CANDIDATE_NOT_FACTORY_VERIFIED",
        "published_configurations": 0,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidates.jsonl").write_bytes(output_bytes)
    (out / "powertrain-groups.jsonl").write_bytes(group_bytes)
    (out / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "denominator.md").write_text(report_markdown(index), encoding="utf-8")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_ZIP)
    parser.add_argument("--source-index", type=Path, default=SOURCE_INDEX)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    index = run(args.source, args.source_index, args.out)
    print(json.dumps(index["denominator"], ensure_ascii=False))


if __name__ == "__main__":
    main()
