"""Read-only EPA universe ↔ published BASE_READY join.

The join never promotes EPA rows to verified records. An EPA id is the strongest
link to an existing publication; model aliases and unclear drivetrains are sent
to review rather than converted into a new factory claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.catalog_scope import in_active_scope  # noqa: E402
from app.services.catalog_verification import base_catalog_ready, catalog_excluded  # noqa: E402

DEFAULT_UNIVERSE = ROOT / "deliverables/VerifiedData/us-catalog-universe/candidates.jsonl"
DEFAULT_OUT = ROOT / "deliverables/VerifiedData/us-catalog-universe"


def name_key(value: object) -> str:
    return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())


def drive_key(value: object) -> str | None:
    normalized = " ".join(str(value or "").casefold().split())
    return {
        "front-wheel drive": "FWD",
        "rear-wheel drive": "RWD",
        "all-wheel drive": "AWD",
        "4-wheel drive": "4WD",
        "part-time 4-wheel drive": "4WD",
        "fwd": "FWD",
        "rwd": "RWD",
        "awd": "AWD",
        "4wd": "4WD",
    }.get(normalized)


def known_fact(catalog: dict, key: str) -> object | None:
    fact = catalog.get("facts", {}).get(key, {})
    if fact.get("status") == "CONFIRMED":
        return fact.get("value")
    return None


def published_ready(db_path: Path) -> list[dict]:
    uri = "file:" + db_path.resolve().as_posix() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        rows = db.execute(
            "SELECT id, catalog_key, specifications FROM vehicle_variants "
            "WHERE published_revision_id IS NOT NULL AND is_demo=0 AND market='US'"
        )
        result = []
        for variant_id, catalog_key, raw in rows:
            catalog = json.loads(raw).get("catalog", {})
            if not catalog or catalog_excluded(catalog) or not base_catalog_ready(catalog):
                continue
            if not in_active_scope(
                catalog.get("make"), catalog.get("original_market"), catalog.get("model_year")
            ):
                continue
            result.append(
                {
                    "variant_id": variant_id,
                    "catalog_key": catalog_key,
                    "epa_vehicle_id": (
                        str(catalog.get("external_key"))
                        if catalog.get("source_registry_id") == "epa"
                        and str(catalog.get("external_key", "")).isdigit()
                        else None
                    ),
                    "make": catalog["make"],
                    "model": catalog["model"],
                    "model_year": catalog["model_year"],
                    "generation": catalog.get("generation_code") or catalog.get("generation"),
                    "generation_code": catalog.get("generation_code"),
                    "body": known_fact(catalog, "body"),
                    "engine": known_fact(catalog, "engine_description"),
                    "displacement_l": known_fact(catalog, "engine_displacement"),
                    "transmission": known_fact(catalog, "transmission_description"),
                    "transmission_family": known_fact(catalog, "transmission_family"),
                    "transmission_gears": known_fact(catalog, "gears"),
                    "drivetrain": known_fact(catalog, "drivetrain"),
                    "aspiration": known_fact(catalog, "aspiration"),
                    "injection": known_fact(catalog, "injection"),
                    "aliases": catalog.get("aliases") or [],
                }
            )
    return result


def mismatch(candidate: dict, published: dict) -> list[str]:
    """Only disagreements that are safe to call identity conflicts."""
    issues = []
    if name_key(candidate["make"]) != name_key(published["make"]):
        issues.append("MAKE")
    if candidate["model_year"] != published["model_year"]:
        issues.append("MODEL_YEAR")
    raw_drive = drive_key(candidate["normalized_powertrain"].get("drive"))
    ready_drive = drive_key(published.get("drivetrain"))
    # EPA's 4WD field is often described as AWD by the manufacturer.
    if (
        raw_drive
        and ready_drive
        and raw_drive != ready_drive
        and {raw_drive, ready_drive} != {"4WD", "AWD"}
    ):
        issues.append("DRIVETRAIN")
    raw_displ = candidate["normalized_powertrain"].get("displ")
    ready_displ = published.get("displacement_l")
    if raw_displ and ready_displ is not None:
        try:
            if abs(float(raw_displ) - float(ready_displ)) > 0.25:
                issues.append("DISPLACEMENT")
        except (TypeError, ValueError):
            pass
    return issues


def gear_count(value: object) -> int | None:
    text = str(value or "").casefold()
    match = re.search(r"(\d+)\s*(?:-speed|-spd|\s*speed|\s*spd)", text)
    if not match:
        match = re.search(r"\([a-z-]*(\d+)\)", text)
    return int(match[1]) if match else None


def possible_existing_tuple(candidate: dict, published: dict) -> bool:
    """A review hint, not an authorization to inherit factory evidence."""
    raw = candidate["normalized_powertrain"]
    if name_key(candidate["epa_model"]) not in {
        name_key(published["model"]),
        *(name_key(x) for x in published["aliases"]),
    }:
        return False
    if mismatch(candidate, published):
        return False
    raw_drive, ready_drive = drive_key(raw.get("drive")), drive_key(published["drivetrain"])
    if not raw_drive or raw_drive != ready_drive:
        return False
    if raw.get("displ") and published["displacement_l"] is not None:
        try:
            if abs(float(raw["displ"]) - float(published["displacement_l"])) > 0.15:
                return False
        except (TypeError, ValueError):
            return False
    elif raw.get("displ") or published["displacement_l"] is not None:
        return False
    raw_gears = gear_count(raw.get("trany"))
    ready_gears = published["transmission_gears"] or gear_count(published["transmission"])
    if raw_gears and ready_gears and raw_gears != int(ready_gears):
        return False
    raw_manual = str(raw.get("trany", "")).startswith("manual")
    if raw_manual != (published["transmission_family"] == "MANUAL"):
        return False
    if raw.get("tCharger") == "t" and published["aspiration"] not in {"TURBO", "TWIN_TURBO"}:
        return False
    if raw.get("sCharger") == "s" and published["aspiration"] != "SUPERCHARGED":
        return False
    return not (
        "sidi" in raw.get("eng_dscr", "")
        and str(published["injection"]).upper() in {"MPI", "PFI"}
    )


def classify(row: dict, by_epa_id: dict, by_model: dict, by_alias: dict) -> dict:
    epa_id = row["epa_vehicle_id"]
    found = by_epa_id.get(epa_id)
    status = "CANDIDATE_NEW"
    reason = "NO_PUBLISHED_READY_EPA_ID"
    matched = None
    if found:
        matched = found[0]
        issues = mismatch(row, matched)
        if issues:
            status, reason = "CONFLICT", "+".join(issues)
        elif name_key(row["model"]) != name_key(matched["model"]):
            # The stable EPA row id is already verified under an editorial family.
            status, reason = "ALREADY_VERIFIED", "REVIEWED_EPA_MODEL_ALIAS"
        else:
            status, reason = "ALREADY_VERIFIED", "EXACT_EPA_ID"
    else:
        key = (name_key(row["make"]), name_key(row["model"]), row["model_year"])
        alias_rows = by_alias.get(key, [])
        possible = [x for x in by_model.get(key, []) if possible_existing_tuple(row, x)]
        if possible:
            status, reason = "POSSIBLE_ALIAS", "POSSIBLE_EXISTING_POWERTRAIN_TUPLE"
            matched = possible[0]
        elif key not in by_model and alias_rows:
            status, reason = "POSSIBLE_ALIAS", "MODEL_NAME_MATCHES_PUBLISHED_ALIAS"
            matched = alias_rows[0]
    return {
        "epa_vehicle_id": epa_id,
        "make": row["make"],
        "model": row["model"],
        "epa_model": row["epa_model"],
        "model_year": row["model_year"],
        "normalized_powertrain_key": row["normalized_powertrain_key"],
        "classification": status,
        "reason": reason,
        "matched_variant_id": matched["variant_id"] if matched else None,
        "matched_catalog_model": matched["model"] if matched else None,
    }


def run(universe_path: Path, db_path: Path, out: Path) -> dict:
    ready = published_ready(db_path)
    by_epa_id = defaultdict(list)
    by_model = defaultdict(list)
    by_alias = defaultdict(list)
    ready_models = set()
    for record in ready:
        if record["epa_vehicle_id"]:
            by_epa_id[record["epa_vehicle_id"]].append(record)
        key = (name_key(record["make"]), name_key(record["model"]), record["model_year"])
        by_model[key].append(record)
        ready_models.add((record["make"], record["model"]))
        for alias in record["aliases"]:
            by_alias[(name_key(record["make"]), name_key(alias), record["model_year"])].append(
                record
            )
    counts = Counter()
    target_models = set()
    model_year_pairs = set()
    by_make = defaultdict(
        lambda: {
            "target_models": set(),
            "ready_models": set(),
            "candidate_configs": 0,
            "ready_configs": 0,
            "status": Counter(),
        }
    )
    out.mkdir(parents=True, exist_ok=True)
    joined_path = out / "candidate-join.jsonl"
    with (
        universe_path.open(encoding="utf-8") as source,
        joined_path.open("w", encoding="utf-8") as sink,
    ):
        for line in source:
            row = json.loads(line)
            result = classify(row, by_epa_id, by_model, by_alias)
            sink.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            counts[result["classification"]] += 1
            make, model = row["make"], row["model"]
            target_models.add((make, model))
            model_year_pairs.add((make, model, row["model_year"]))
            cell = by_make[make]
            cell["target_models"].add(model)
            cell["candidate_configs"] += 1
            cell["status"][result["classification"]] += 1
    for record in ready:
        cell = by_make[record["make"]]
        if record["model"] in cell["target_models"]:
            cell["ready_models"].add(record["model"])
            cell["ready_configs"] += 1
    brand_rows = []
    for make in sorted(by_make):
        cell = by_make[make]
        brand_rows.append(
            {
                "make": make,
                "target_models": len(cell["target_models"]),
                "base_ready_models": len(cell["ready_models"]),
                "remaining_models": len(cell["target_models"] - cell["ready_models"]),
                "candidate_configs": cell["candidate_configs"],
                "base_ready_configs": cell["ready_configs"],
                "classifications": dict(sorted(cell["status"].items())),
                "new_model_names": sorted(cell["target_models"] - cell["ready_models"]),
            }
        )
    published_model_names = {(record["make"], record["model"]) for record in ready}
    outside_names = sorted(published_model_names - target_models)
    summary = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "universe_sha256": hashlib.sha256(universe_path.read_bytes()).hexdigest(),
        "published_db_read_only": str(db_path),
        "classification_policy": "exact verified EPA id; aliases never certify a new tuple",
        "total_target_models": len(target_models),
        "currently_verified_models": len(published_model_names),
        "verified_models_matching_epa_base_name": sum(x["base_ready_models"] for x in brand_rows),
        "verified_editorial_subfamilies_outside_epa_base_names": [
            {"make": make, "model": model} for make, model in outside_names
        ],
        "newly_auto_verified_models": 0,
        "remaining_target_models": sum(x["remaining_models"] for x in brand_rows),
        "exception_review_count_deferred_to_router": True,
        "candidate_rows": sum(counts.values()),
        "published_base_ready_configurations": len(ready),
        "published_base_ready_configurations_matching_epa_base_name": sum(
            x["base_ready_configs"] for x in brand_rows
        ),
        "candidate_classifications": dict(sorted(counts.items())),
        "model_year_pairs": len(model_year_pairs),
        "brands": brand_rows,
    }
    (out / "candidate-join-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = run(args.universe, args.db, args.out)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "total_target_models",
                    "currently_verified_models",
                    "newly_auto_verified_models",
                    "remaining_target_models",
                    "candidate_rows",
                    "candidate_classifications",
                )
            },
            ensure_ascii=False,
        )
    )
