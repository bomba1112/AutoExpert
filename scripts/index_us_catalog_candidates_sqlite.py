"""Create a standalone, queryable SQLite index of EPA research candidates.

The database is an artifact derived from the immutable JSONL universe. It is
never attached to the application database and does not publish vehicles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "deliverables/VerifiedData/us-catalog-universe"
PARSER_VERSION = "us-catalog-candidate-sqlite-index-1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def prepared_rows(source_bytes: bytes, expected_columns: set[str]):
    for line_number, line in enumerate(source_bytes.splitlines(), start=1):
        if not line:
            continue
        row = json.loads(line)
        fields = row["epa_fields"]
        if set(fields) != expected_columns:
            raise ValueError(f"EPA_FIELD_SET_MISMATCH:line={line_number}")
        if row["epa_vehicle_id"] != fields["id"]:
            raise ValueError(f"EPA_ID_MISMATCH:line={line_number}")
        if row["make"] != fields["make"] or row["model_year"] != int(fields["year"]):
            raise ValueError(f"EPA_IDENTITY_MISMATCH:line={line_number}")
        yield (
            row["epa_vehicle_id"],
            row["make"],
            row["model"],
            row["model_year"],
            row["epa_model"],
            row["normalized_powertrain_key"],
            fields.get("displ") or None,
            fields.get("cylinders") or None,
            fields.get("fuelType1") or fields.get("fuelType") or None,
            fields.get("trany") or None,
            fields.get("drive") or None,
            fields.get("evMotor") or None,
            fields.get("VClass") or None,
            canonical_json(row["missing_core_fields"]),
            canonical_json(row["normalized_powertrain"]),
            canonical_json(fields),
            row["source"]["dataset_sha256"],
            row["source"]["row_locator"],
        )


def build_index(
    source_bytes: bytes,
    output_path: Path,
    *,
    expected_sha256: str,
    expected_rows: int,
    expected_brands: int,
    expected_columns: set[str],
    epa_source_sha256: str,
) -> dict:
    if digest(source_bytes) != expected_sha256:
        raise ValueError("CANDIDATE_JSONL_SHA_MISMATCH")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output_path.parent, suffix=".building.sqlite", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with closing(sqlite3.connect(temporary_path)) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.executescript(
                """
                CREATE TABLE candidate_rows (
                    epa_vehicle_id TEXT PRIMARY KEY,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    model_year INTEGER NOT NULL,
                    epa_model TEXT NOT NULL,
                    normalized_powertrain_key TEXT NOT NULL,
                    engine_displacement_l TEXT,
                    cylinders TEXT,
                    fuel_type TEXT,
                    transmission TEXT,
                    drivetrain TEXT,
                    ev_motor TEXT,
                    vclass TEXT,
                    missing_core_fields_json TEXT NOT NULL,
                    normalized_powertrain_json TEXT NOT NULL,
                    epa_fields_json TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    row_locator TEXT NOT NULL
                );
                CREATE TABLE index_metadata (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL
                );
                """
            )
            db.executemany(
                """
                INSERT INTO candidate_rows VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                prepared_rows(source_bytes, expected_columns),
            )
            db.executescript(
                """
                CREATE INDEX idx_candidate_make_model_year
                    ON candidate_rows(make, model, model_year);
                CREATE INDEX idx_candidate_model
                    ON candidate_rows(model);
                CREATE INDEX idx_candidate_year
                    ON candidate_rows(model_year);
                CREATE INDEX idx_candidate_powertrain
                    ON candidate_rows(normalized_powertrain_key);
                """
            )
            found_rows = db.execute("SELECT COUNT(*) FROM candidate_rows").fetchone()[0]
            found_brands = db.execute(
                "SELECT COUNT(DISTINCT make) FROM candidate_rows"
            ).fetchone()[0]
            source_count = db.execute(
                "SELECT COUNT(*) FROM candidate_rows WHERE source_sha256 = ?",
                (epa_source_sha256,),
            ).fetchone()[0]
            if (found_rows, found_brands, source_count) != (
                expected_rows,
                expected_brands,
                expected_rows,
            ):
                raise ValueError("SQLITE_INDEX_COUNT_OR_SOURCE_MISMATCH")
            metadata = {
                "parser_version": PARSER_VERSION,
                "candidate_jsonl_sha256": expected_sha256,
                "epa_source_sha256": epa_source_sha256,
                "candidate_rows": found_rows,
                "brands": found_brands,
                "source_columns": sorted(expected_columns),
                "publication_eligible": False,
            }
            db.executemany(
                "INSERT INTO index_metadata(key, value_json) VALUES (?, ?)",
                [(key, canonical_json(value)) for key, value in metadata.items()],
            )
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("SQLITE_INTEGRITY_CHECK_FAILED")
            db.commit()
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return {
        "parser_version": PARSER_VERSION,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "sqlite_path": str(output_path.relative_to(ROOT))
        if output_path.is_relative_to(ROOT)
        else str(output_path),
        "sqlite_bytes": output_path.stat().st_size,
        "sqlite_sha256": digest(output_path.read_bytes()),
        "candidate_jsonl_sha256": expected_sha256,
        "epa_source_sha256": epa_source_sha256,
        "candidate_rows": expected_rows,
        "brands": expected_brands,
        "source_columns": len(expected_columns),
        "index_names": [
            "sqlite_autoindex_candidate_rows_1 (epa_vehicle_id PRIMARY KEY)",
            "idx_candidate_make_model_year",
            "idx_candidate_model",
            "idx_candidate_year",
            "idx_candidate_powertrain",
        ],
        "production_database_modified": False,
        "published_configurations": 0,
    }


def documentation(summary: dict) -> str:
    return "\n".join(
        [
            "# Standalone EPA candidate SQLite index",
            "",
            "This is a read-only research artifact for bulk queries, separate from "
            "`autoexpert.db`. EPA rows do not establish factory trim, generation "
            "or publishable BASE_READY applicability.",
            "",
            f"Rows: **{summary['candidate_rows']}**; makes: **{summary['brands']}**; "
            f"original EPA columns per row: **{summary['source_columns']}**.",
            f"SQLite SHA-256: `{summary['sqlite_sha256']}`.",
            f"EPA ZIP SHA-256: `{summary['epa_source_sha256']}`.",
            "",
            "`candidate_rows` has `epa_vehicle_id` as primary key, "
            "`(make, model, model_year)` and separate model/year/powertrain-key "
            "indexes. `epa_fields_json` retains every original EPA CSV value; "
            "`normalized_powertrain_json` records the candidate grouping tuple. "
            "`index_metadata` stores source hashes and row counts.",
            "",
            "Example queries:",
            "",
            "```sql",
            "SELECT epa_vehicle_id, model_year, engine_displacement_l, transmission, drivetrain",
            "FROM candidate_rows",
            "WHERE make = 'Toyota' AND model = 'Camry' AND model_year = 2018;",
            "",
            "SELECT make, model, MIN(model_year), MAX(model_year), COUNT(*)",
            "FROM candidate_rows",
            "WHERE normalized_powertrain_key = ?",
            "GROUP BY make, model;",
            "```",
            "",
            "Generated from the saved official FuelEconomy.gov bulk CSV. No individual "
            "EPA API calls, product DB writes, or changes to publication gates occurred.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    root = args.dir
    universe = json.loads((root / "index.json").read_text(encoding="utf-8"))
    output = root / "candidates-index.sqlite"
    summary = build_index(
        (root / "candidates.jsonl").read_bytes(),
        output,
        expected_sha256=universe["candidate_jsonl_sha256"],
        expected_rows=universe["denominator"]["epa_rows_after_filter"],
        expected_brands=universe["denominator"]["unique_brands"],
        expected_columns=set(universe["source"]["csv_columns"]),
        epa_source_sha256=universe["source"]["zip_sha256"],
    )
    (root / "candidate-index-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "candidate-index.md").write_text(documentation(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
