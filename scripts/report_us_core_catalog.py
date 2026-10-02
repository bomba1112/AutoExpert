"""Read-only US CORE/VERIFIED catalogue snapshot and baseline comparison.

The visible counts use the same source-rights and active-scope predicates as
the buyer's US_BASE_2000 and US_CONFIRMED_2000 queries. No user, account or
session tables are read. The database is opened in SQLite read-only mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.catalog import VehicleMake, VehicleModel  # noqa: E402
from app.services.catalog_buyer import active_us_base_rows, active_us_rows, records  # noqa: E402
from app.services.catalog_verification import identity_verified  # noqa: E402
from app.services.knowledge_import import normalized  # noqa: E402


def _model_key(make: str, model: str) -> str:
    return f"{make} | {model}"


def _canonical_names(db: Session) -> dict[tuple[str, str], tuple[str, str]]:
    """Use the catalogue's own make/model spelling, keyed like buyer facets."""
    rows = db.query(
        VehicleMake.normalized_name,
        VehicleMake.name,
        VehicleModel.normalized_name,
        VehicleModel.name,
    ).join(VehicleModel, VehicleModel.make_id == VehicleMake.id)
    return {
        (normalized(make_key), normalized(model_key)): (make, model)
        for make_key, make, model_key, model in rows
    }


def _visible(rows: list[tuple], canonical_names: dict) -> dict:
    grouped: dict[tuple[str, str], Counter] = defaultdict(Counter)
    spellings: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for _, catalog in rows:
        make, model, year = catalog["make"], catalog["model"], catalog["model_year"]
        key = (normalized(make), normalized(model))
        grouped[key][year] += 1
        spellings[key].add((make, model))
    models_by_name = {}
    for key, counts in grouped.items():
        # The fallback is deterministic even if a row has no VehicleModel yet.
        fallback = min(
            spellings[key], key=lambda pair: (pair[0].casefold(), pair[1].casefold(), pair)
        )
        make, model = canonical_names.get(key, fallback)
        name = _model_key(make, model)
        models_by_name[name] = {
            "years": sorted(counts),
            "configuration_count": sum(counts.values()),
            "configurations_by_year": {
                str(year): count for year, count in sorted(counts.items())
            },
        }
    models = dict(sorted(models_by_name.items(), key=lambda item: item[0].casefold()))
    if len({name.casefold() for name in models}) != len(models):
        raise ValueError("case-insensitive model-name collision in report")
    return {
        "make_count": len({key[0] for key in grouped}),
        "model_count": len(models),
        "model_year_count": sum(len(item["years"]) for item in models.values()),
        "annual_configuration_count": len(rows),
        "models": models,
    }


def _strict_fingerprints(db: Session) -> dict:
    """Hash every published VERIFIED_SCOPED catalogue payload, including inactive rows."""
    result = {}
    rows = db.execute(
        text(
            "SELECT id, catalog_key, specifications FROM vehicle_variants "
            "WHERE published_revision_id IS NOT NULL AND is_demo = 0 "
            "AND json_extract(specifications, '$.catalog.verification_gate.state') "
            "= 'VERIFIED_SCOPED'"
        )
    )
    for variant_id, catalog_key, specifications in rows:
        catalog = json.loads(specifications).get("catalog") or {}
        if not identity_verified(catalog):
            continue
        serialized = json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        key = str(catalog_key or variant_id)
        result[key] = {
            "make": catalog.get("make"),
            "model": catalog.get("model"),
            "model_year": catalog.get("model_year"),
            "sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        }
    return dict(sorted(result.items()))


def snapshot(db_path: Path) -> dict:
    db_path = db_path.resolve()
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    # SQLAlchemy's creator avoids any path/URI translation that could silently
    # create a second SQLite file on Windows. The connection itself is read-only.
    engine = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True),
    )
    try:
        with Session(engine) as db:
            visible = records(db)
            core = active_us_rows(visible)
            verified = active_us_base_rows(visible)
            canonical_names = _canonical_names(db)
            return {
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "database": str(db_path),
                "scope": "buyer active policy and source-rights checks",
                "us_base_2000": _visible(core, canonical_names),
                "us_confirmed_2000": _visible(verified, canonical_names),
                "all_published_verified_scoped": {
                    "count": 0, "fingerprints": {}
                },
            } | _with_fingerprints(db)
    finally:
        engine.dispose()


def _with_fingerprints(db: Session) -> dict:
    fingerprints = _strict_fingerprints(db)
    return {
        "all_published_verified_scoped": {
            "count": len(fingerprints),
            "fingerprints": fingerprints,
        }
    }


def compare(before: dict, after: dict) -> dict:
    old = before["us_base_2000"]
    new = after["us_base_2000"]
    legacy = before["us_confirmed_2000"]
    metrics = (
        "make_count", "model_count", "model_year_count", "annual_configuration_count"
    )
    old_models, new_models = old["models"], new["models"]
    introduced = {name: new_models[name] for name in sorted(new_models.keys() - old_models.keys())}
    expanded = {}
    for name in sorted(new_models.keys() & old_models.keys()):
        old_years = set(old_models[name]["years"])
        new_years = set(new_models[name]["years"])
        count_delta = (
            new_models[name]["configuration_count"] - old_models[name]["configuration_count"]
        )
        if count_delta or new_years != old_years:
            expanded[name] = {
                "new_years": sorted(new_years - old_years),
                "removed_years": sorted(old_years - new_years),
                "configuration_delta": count_delta,
                "after": new_models[name],
            }
    baseline_fingerprints = before["all_published_verified_scoped"]["fingerprints"]
    current_fingerprints = after["all_published_verified_scoped"]["fingerprints"]
    changed_strict = sorted(
        key
        for key in baseline_fingerprints.keys() & current_fingerprints.keys()
        if baseline_fingerprints[key]["sha256"] != current_fingerprints[key]["sha256"]
    )
    return {
        "us_base_2000_deltas": {
            key: new[key] - old[key] for key in metrics
        },
        "pre_fix_strict_us_base_2000_to_current": {
            "note": "Before the CORE code fix, US_BASE_2000 used the strict VERIFIED gate.",
            "before": {key: legacy[key] for key in metrics},
            "after": {key: new[key] for key in metrics},
            "deltas": {key: new[key] - legacy[key] for key in metrics},
        },
        "introduced_models": introduced,
        "expanded_existing_models": expanded,
        "removed_models": sorted(old_models.keys() - new_models.keys()),
        "strict_unchanged": not (
            changed_strict
            or baseline_fingerprints.keys() - current_fingerprints.keys()
        ),
        "strict_changed_keys": changed_strict,
        "strict_missing_keys": sorted(
            baseline_fingerprints.keys() - current_fingerprints.keys()
        ),
        "strict_added_keys": sorted(
            current_fingerprints.keys() - baseline_fingerprints.keys()
        ),
    }


def _year_ranges(years: list[int]) -> str:
    runs: list[list[int]] = []
    for year in sorted(set(years)):
        if runs and year == runs[-1][-1] + 1:
            runs[-1].append(year)
        else:
            runs.append([year])
    return ", ".join(
        str(run[0]) if len(run) == 1 else f"{run[0]}–{run[-1]}" for run in runs
    )


def markdown(result: dict) -> str:
    base = result["us_base_2000"]
    strict = result["us_confirmed_2000"]
    lines = [
        "# US source-confirmed CORE catalogue checkpoint",
        "",
        "Counts reflect the buyer's active US scope and source-rights checks. "
        "Configuration counts are annual published variants, not raw EPA test rows.",
        "The backup is evaluated with the new CORE predicate; before the code fix, "
        "US_BASE_2000 used the strict gate and matched US_CONFIRMED_2000.",
        "",
        "| Scope | Makes | Models | Make/model/year pairs | Annual configurations |",
        "|---|---:|---:|---:|---:|",
        f"| US_BASE_2000 | {base['make_count']} | {base['model_count']} | "
        f"{base['model_year_count']} | {base['annual_configuration_count']} |",
        f"| US_CONFIRMED_2000 | {strict['make_count']} | {strict['model_count']} | "
        f"{strict['model_year_count']} | {strict['annual_configuration_count']} |",
        "",
    ]
    comparison = result.get("comparison_to_baseline")
    if comparison:
        delta = comparison["us_base_2000_deltas"]
        lines.extend(
            [
                "## Delta from pre-publication backup",
                "",
                "The new CORE predicate applied to the backup is the publication-only "
                "baseline. The end-to-end pre-fix user-visible baseline was the strict "
                "US_CONFIRMED_2000 count above.",
                "",
                f"Models: {delta['model_count']:+}; make/model/year pairs: "
                f"{delta['model_year_count']:+}; annual configurations: "
                f"{delta['annual_configuration_count']:+}.",
                f"Existing VERIFIED_SCOPED payloads unchanged: "
                f"{'YES' if comparison['strict_unchanged'] else 'NO'}.",
                "",
                "### Newly visible models",
                "",
                "| Make | Model | Exact model years | Annual configurations |",
                "|---|---|---|---:|",
            ]
        )
        for name, item in comparison["introduced_models"].items():
            make, model = name.split(" | ", 1)
            lines.append(
                f"| {make} | {model} | {_year_ranges(item['years'])} | "
                f"{item['configuration_count']} |"
            )
        lines.extend(
            [
                "",
                "### Expanded existing models",
                "",
                "| Make | Model | Newly visible years | Annual configuration delta |",
                "|---|---|---|---:|",
            ]
        )
        for name, item in comparison["expanded_existing_models"].items():
            make, model = name.split(" | ", 1)
            lines.append(
                f"| {make} | {model} | {_year_ranges(item['new_years']) or '—'} | "
                f"{item['configuration_delta']:+} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Cumulative user-visible US_BASE_2000 models",
            "",
            "| Make | Model | Exact model years | Annual configurations |",
            "|---|---|---|---:|",
        ]
    )
    for name, item in base["models"].items():
        make, model = name.split(" | ", 1)
        lines.append(
            f"| {make} | {model} | {_year_ranges(item['years'])} | "
            f"{item['configuration_count']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--output", type=Path, help="Write snapshot JSON outside the database")
    parser.add_argument("--compare", type=Path, help="Compare with a previous snapshot JSON")
    parser.add_argument("--markdown-output", type=Path, help="Write named model/year checkpoint")
    args = parser.parse_args()
    result = snapshot(args.db)
    if args.compare:
        baseline = json.loads(args.compare.read_text(encoding="utf-8"))
        result["comparison_to_baseline"] = compare(baseline, result)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
