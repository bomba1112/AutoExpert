"""Index the existing official EPA CSV for approved US master models.

This is a research candidate index, never a factory configuration publisher. The
EPA row's paired engine/gearbox/drive descriptions are retained as source text;
they are not converted to a factory trim or joined to another EPA row.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import RawDocument  # noqa: E402
from app.services.knowledge_import import document_text, private_path  # noqa: E402
from sqlalchemy import select  # noqa: E402

PARSER_VERSION = "epa-us-master-candidates-2"
DEFAULT_OUT = ROOT / "deliverables" / "VerifiedData" / "us-bulk-data-08"
DEFAULT_CACHE = ROOT / ".localdata" / "epa-bulk-cache"
MASTER = ROOT / "data" / "manifests" / "az-market-priority-policy.json"
ALIASES = ROOT / "scripts" / "epa_master_aliases.json"
REQUIRED_COLUMNS = {"id", "make", "model", "year", "trany", "drive", "fuelType1", "comb08"}
RETAINED_COLUMNS = (
    "id",
    "make",
    "model",
    "baseModel",
    "basemodel",
    "year",
    "displ",
    "cylinders",
    "trany",
    "trans_dscr",
    "drive",
    "fuelType1",
    "fuelType2",
    "atvType",
    "engId",
    "eng_dscr",
    "tCharger",
    "sCharger",
    "VClass",
    "city08",
    "highway08",
    "comb08",
    "cityA08",
    "highwayA08",
    "combA08",
    "cityE",
    "highwayE",
    "combE",
    "range",
    "rangeA",
    "rangeCity",
    "rangeHwy",
    "rangeCityA",
    "rangeHwyA",
    "charge240",
    "charge240b",
    "c240Dscr",
    "c240bDscr",
    "charge120",
    "evMotor",
    "phevCity",
    "phevHwy",
    "phevComb",
    "phevBlended",
    "startStop",
    "createdOn",
    "modifiedOn",
)
SOURCE_FIELD_UNITS = {
    "displ": "L",
    "city08": "mpg_US_EPA",
    "highway08": "mpg_US_EPA",
    "comb08": "mpg_US_EPA",
    "cityA08": "mpg_US_EPA_alternative_fuel",
    "highwayA08": "mpg_US_EPA_alternative_fuel",
    "combA08": "mpg_US_EPA_alternative_fuel",
    "cityE": "kWh/100mi_EPA",
    "highwayE": "kWh/100mi_EPA",
    "combE": "kWh/100mi_EPA",
    "range": "mi_EPA",
    "rangeA": "mi_EPA_alternative_fuel",
    "charge240": "h_at_240V",
    "charge120": "h_at_120V",
    "rangeCity": "mi_EPA",
    "rangeHwy": "mi_EPA",
    "rangeCityA": "mi_EPA_alternative_fuel",
    "rangeHwyA": "mi_EPA_alternative_fuel",
    "charge240b": "h_at_240V_alternate_charger",
    "phevCity": "MPGe_EPA",
    "phevHwy": "MPGe_EPA",
    "phevComb": "MPGe_EPA",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def key(value: str) -> str:
    return " ".join(value.casefold().replace("–", "-").split())


def has_prefix(value: str, prefix: str) -> bool:
    value, prefix = key(value), key(prefix)
    return value == prefix or value.startswith(prefix + " ") or value.startswith(prefix + "(")


def scopes(policy: dict) -> dict[str, dict[str, str]]:
    approved = policy["primary_makes"]
    order = policy["first_wave_model_order"]
    assert set(approved) == set(order), "MASTER_MAKE_SCOPE_MISMATCH"
    assert policy["allowed_markets"] == ["US"]
    assert policy["minimum_model_year"] >= 2000
    return {make: {key(model): model for model in order[make]} for make in approved}


def match_master(row: dict, scope: dict, aliases: dict) -> tuple[str, str] | None:
    """Conservative family selection; never asserts a trim or a factory tuple."""
    make = row["make"]
    if make not in scope:
        return None
    raw = row["model"]
    base = row.get("baseModel") or row.get("basemodel") or raw
    for rule in aliases["raw_prefixes"]:
        if (
            rule["make"] == make
            and key(rule["model"]) in scope[make]
            and any(has_prefix(raw, prefix) for prefix in rule["prefixes"])
        ):
            return scope[make][key(rule["model"])], "REVIEWED_RAW_FAMILY_PREFIX"
    for rule in aliases["base_aliases"]:
        if (
            rule["make"] == make
            and key(rule["model"]) in scope[make]
            and key(base) in {key(value) for value in rule["epa_base_models"]}
        ):
            return scope[make][key(rule["model"])], "REVIEWED_EPA_BASE_ALIAS"
    if key(base) not in scope[make]:
        return None
    model = scope[make][key(base)]
    for rule in aliases["base_model_exclusions"]:
        if (
            rule["make"] == make
            and rule["model"] == model
            and any(has_prefix(raw, prefix) for prefix in rule["raw_prefixes"])
        ):
            return None
    return model, "EXACT_EPA_BASE_NAME"


def candidate(row: dict, model: str, basis: str, source_sha: str) -> dict:
    fields = {
        k: row[k]
        for k in RETAINED_COLUMNS
        if k not in {"id", "make", "year"} and row.get(k) not in (None, "")
    }
    # engId is an EPA index, not a factory engine code. trany is a source
    # descriptor, not a verified transmission construction or factory trim.
    if "engId" in fields:
        fields["epa_engine_index"] = fields.pop("engId")
    return {
        "epa_vehicle_id": row["id"],
        "master_make": row["make"],
        "master_model_candidate": model,
        "model_year": int(row["year"]),
        "family_match_basis": basis,
        "source": {
            "registry_id": "epa",
            "dataset_sha256": source_sha,
            "row_locator": f"vehicles.csv:id={row['id']}",
        },
        "raw_fields": fields,
    }


def select_candidates(
    csv_text: str, policy: dict, aliases: dict, source_sha: str, max_year: int
) -> tuple[list[dict], dict]:
    scope = scopes(policy)
    reader = csv.DictReader(io.StringIO(csv_text))
    columns = reader.fieldnames or []
    if not set(columns) >= REQUIRED_COLUMNS:
        raise ValueError("EPA_SCHEMA_CHANGED")
    counts = Counter()
    rows = []
    seen = set()
    make_order = {make: i for i, make in enumerate(policy["primary_makes"])}
    model_order = {
        (make, model): i
        for make, models in policy["first_wave_model_order"].items()
        for i, model in enumerate(models)
    }
    for row in reader:
        counts["source_rows"] += 1
        if not row["year"].isdigit():
            counts["bad_year"] += 1
            continue
        year = int(row["year"])
        year_min = policy.get("minimum_model_year_overrides", {}).get(
            row["make"], policy["minimum_model_year"]
        )
        if year < year_min or year > max_year:
            counts["outside_year_scope"] += 1
            continue
        if row["make"] not in scope:
            counts["outside_make_scope"] += 1
            continue
        counts["approved_make_year_rows"] += 1
        match = match_master(row, scope, aliases)
        if match is None:
            counts["outside_master_models_or_excluded_subfamily"] += 1
            continue
        if not row["id"].isdigit() or row["id"] in seen:
            counts["invalid_or_duplicate_epa_id"] += 1
            continue
        seen.add(row["id"])
        model, basis = match
        counts["matched_research_candidates"] += 1
        counts[f"basis:{basis}"] += 1
        rows.append(candidate(row, model, basis, source_sha))
    rows.sort(
        key=lambda r: (
            make_order[r["master_make"]],
            model_order[(r["master_make"], r["master_model_candidate"])],
            r["model_year"],
            int(r["epa_vehicle_id"]),
        )
    )
    return rows, {"counts": dict(sorted(counts.items())), "columns": columns}


def source_document(db) -> RawDocument:
    documents = db.scalars(
        select(RawDocument)
        .where(RawDocument.source_id == "epa", RawDocument.media_type == "application/zip")
        .order_by(RawDocument.created_at.desc())
    ).all()
    for doc in documents:
        if doc.locator == "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip":
            return doc
    raise ValueError("OFFICIAL_EPA_ZIP_SNAPSHOT_NOT_FOUND")


def run(out: Path, cache: Path, *, force: bool = False, max_year: int = 2026) -> dict:
    started = time.perf_counter()
    policy_bytes = MASTER.read_bytes()
    alias_bytes = ALIASES.read_bytes()
    policy = json.loads(policy_bytes)
    aliases = json.loads(alias_bytes)
    with SessionLocal() as db:
        doc = source_document(db)
        raw = private_path(doc.storage_key).read_bytes()
        if sha256(raw) != doc.sha256:
            raise ValueError("RAW_DOCUMENT_CHANGED")
        identity = {
            "parser_version": PARSER_VERSION,
            "source_sha256": doc.sha256,
            "master_sha256": sha256(policy_bytes),
            "alias_sha256": sha256(alias_bytes),
            "max_year": max_year,
        }
        cache_key = sha256(canonical_bytes(identity))
        cache.mkdir(parents=True, exist_ok=True)
        cache_json = cache / f"{cache_key}.json"
        cache_jsonl = cache / f"{cache_key}.jsonl"
        cache_hit = False
        if not force and cache_json.exists() and cache_jsonl.exists():
            cached = json.loads(cache_json.read_text(encoding="utf-8"))
            candidate_bytes = cache_jsonl.read_bytes()
            cache_hit = cached.get("identity") == identity and sha256(
                candidate_bytes
            ) == cached.get("semantic_sha256")
        if cache_hit:
            result = cached
        else:
            parse_started = time.perf_counter()
            candidates, meta = select_candidates(
                document_text(raw), policy, aliases, doc.sha256, max_year
            )
            parse_seconds = time.perf_counter() - parse_started
            candidate_bytes = b"".join(canonical_bytes(row) + b"\n" for row in candidates)
            by_model = defaultdict(list)
            for item in candidates:
                by_model[(item["master_make"], item["master_model_candidate"])].append(
                    item["model_year"]
                )
            coverage = [
                {
                    "make": make,
                    "model": model,
                    "epa_row_count": len(by_model.get((make, model), [])),
                    "epa_years": sorted(set(by_model.get((make, model), []))),
                }
                for make in policy["primary_makes"]
                for model in policy["first_wave_model_order"][make]
            ]
            result = {
                "identity": identity,
                "source_document_id": doc.id,
                "source_url": doc.locator,
                "source_vehicle_url_template": "https://www.fueleconomy.gov/ws/rest/vehicle/{epa_vehicle_id}",
                "source_acquired_at": doc.created_at.isoformat() if doc.created_at else None,
                "source_bytes": len(raw),
                "source_market": "US EPA testing/rating data; not an exact retail trim",
                "candidate_status": "RESEARCH_CANDIDATE_REQUIRES_FACTORY_APPLICABILITY",
                "source_field_units": SOURCE_FIELD_UNITS,
                "schema_columns": meta["columns"],
                "retained_columns": [x for x in RETAINED_COLUMNS if x in meta["columns"]],
                "unprocessed_columns": [x for x in meta["columns"] if x not in RETAINED_COLUMNS],
                "counts": meta["counts"],
                "master_coverage": coverage,
                "semantic_sha256": sha256(candidate_bytes),
                "parse_seconds": round(parse_seconds, 6),
                "publication": {
                    "factory_configurations": 0,
                    "reason": "EPA rows are candidate evidence pending exact OEM applicability",
                },
            }
            cache_jsonl.write_bytes(candidate_bytes)
            cache_json.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        out.mkdir(parents=True, exist_ok=True)
        (out / "epa-candidates.jsonl").write_bytes(candidate_bytes)
        (out / "epa-index.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return {
            "cache_hit": cache_hit,
            "wall_seconds": round(time.perf_counter() - started, 6),
            "candidate_rows": result["counts"]["matched_research_candidates"],
            "master_models": len(result["master_coverage"]),
            "master_models_with_candidates": sum(
                x["epa_row_count"] > 0 for x in result["master_coverage"]
            ),
            "semantic_sha256": result["semantic_sha256"],
            "source_sha256": doc.sha256,
            "network_calls": 0,
            "external_inference_calls": 0,
            "published_factory_configurations": 0,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--max-year", type=int, default=2026)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reparse the same local raw document for a cold comparison",
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run cold and warm on the same local snapshot"
    )
    args = parser.parse_args()
    if args.max_year < 2000 or args.max_year > datetime.now(UTC).year:
        raise SystemExit("MAX_YEAR_MUST_BE_A_FINAL_OR_CURRENT_MODEL_YEAR")
    if args.benchmark:
        cold = run(args.out, args.cache, force=True, max_year=args.max_year)
        warm = run(args.out, args.cache, max_year=args.max_year)
        if cold["semantic_sha256"] != warm["semantic_sha256"]:
            raise RuntimeError("COLD_WARM_SEMANTIC_MISMATCH")
        measured = {
            "cold": cold,
            "warm": warm,
            "semantic_match": True,
            "speedup_cold_over_warm": round(
                cold["wall_seconds"] / max(warm["wall_seconds"], 1e-9), 3
            ),
        }
        (args.out / "epa-benchmark.json").write_text(
            json.dumps(measured, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(measured, ensure_ascii=False))
    else:
        print(
            json.dumps(
                run(args.out, args.cache, force=args.force, max_year=args.max_year),
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
