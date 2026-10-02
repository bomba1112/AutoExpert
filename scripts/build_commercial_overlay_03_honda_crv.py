"""Use Honda's annual trim/drive tables for exact CR-V drive claims only."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from bs4 import BeautifulSoup
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.models.enums import (  # noqa: E402
    ConfidenceLevel,
    DataOrigin,
    SourceTier,
    SourceUsageStatus,
)
from app.models.evidence import SourceRecord  # noqa: E402
from build_commercial_fact_overlay_batch import (  # noqa: E402
    AZ_RIGHTS_REFERENCE,
    RIGHTS_DATE,
    RIGHTS_REFERENCE,
    configuration_keys,
    fact,
)
from catalog_writer_lock import catalog_writer_lock  # noqa: E402

MANIFEST = ROOT / "data/manifests/commercial-overlay-03-honda-crv-2018-drive.json"
REMAINING = (
    ROOT
    / "deliverables/VerifiedData/commercial-fact-overlay-02"
    / "remaining-unresolved-manufacturer.jsonl"
)
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03"


def source_verified(manifest: dict) -> None:
    annual_path = ROOT / ".localdata/raw" / manifest["annual_source_sha256"]
    shared_path = ROOT / ".localdata/raw" / manifest["fwd_definition_sha256"]
    for path, expected in (
        (annual_path, manifest["annual_source_sha256"]),
        (shared_path, manifest["fwd_definition_sha256"]),
    ):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("SOURCE_CACHE_HASH_MISMATCH")
    annual = BeautifulSoup(annual_path.read_bytes(), "html.parser")
    title = annual.title.get_text(" ", strip=True) if annual.title else ""
    tables = [" ".join(t.get_text(" ", strip=True).split()) for t in annual.find_all("table")]
    if title != f"EPA Fuel-Economy Ratings - {manifest['model_year']} Honda CR-V" or not any(
        all(term in table for term in ("LX", "EX-L", "Touring", "CVT", "2WD", "AWD"))
        for table in tables
    ):
        raise ValueError("ANNUAL_DRIVE_MATRIX_NOT_VERIFIED")
    shared = BeautifulSoup(shared_path.read_bytes(), "html.parser")
    if (
        "all honda cars and two-wheel-drive trucks use front-wheel drive"
        not in shared.get_text(" ", strip=True).casefold()
    ):
        raise ValueError("HONDA_2WD_FWD_DEFINITION_NOT_VERIFIED")


def register_source(db_path: Path, manifest: dict) -> str:
    source_verified(manifest)
    engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
    with catalog_writer_lock(), Session(engine) as db:
        source = db.scalar(
            select(SourceRecord).where(SourceRecord.url == manifest["annual_source_url"])
        )
        if source is None:
            source = SourceRecord(
                title=f"Honda CR-V MY{manifest['model_year']} annual trim/drive matrix",
                publisher="American Honda Motor Co.",
                url=manifest["annual_source_url"],
                source_type="CATALOG_PUBLICATION",
                source_tier=SourceTier.A,
                data_origin=DataOrigin.REAL,
                market="US",
                language="en",
                published_at=None,
                retrieved_at=datetime.now(UTC),
                notes=(
                    "Isolated trim/drive availability facts only; annual cached SHA256 "
                    + manifest["annual_source_sha256"]
                    + "; 2WD means FWD per Honda shared technology page SHA256 "
                    + manifest["fwd_definition_sha256"]
                    + ". No EPA numeric data or creative text reused."
                ),
                confidence=ConfidenceLevel.HIGH,
                usage_status=SourceUsageStatus.ACTIVE,
                is_demo=False,
            )
            db.add(source)
            db.commit()
        return source.id


def build(
    db_path: Path = ROOT / "autoexpert.db",
    out: Path = OUT,
    *,
    register: bool = False,
    manifest_path: Path = MANIFEST,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_verified(manifest)
    if register:
        register_source(db_path, manifest)
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    source = db.execute(
        "SELECT id FROM source_records WHERE url=?", (manifest["annual_source_url"],)
    ).fetchone()
    if source is None:
        raise ValueError("ANNUAL_SOURCE_RECORD_NOT_REGISTERED")
    rows = [json.loads(s) for s in REMAINING.read_text(encoding="utf-8").splitlines() if s]
    rows = [
        r
        for r in rows
        if (r["make"], r["model"], r["model_year"])
        == (manifest["make"], manifest["model"], manifest["model_year"])
    ]
    matrix = {(trim, drive) for trim in manifest["included_trims"] for drive in ("FWD", "AWD")}
    matched = defaultdict(list)
    for row in rows:
        variant = db.execute(
            "SELECT id,specifications FROM vehicle_variants WHERE catalog_key=? "
            "AND published_revision_id IS NOT NULL AND is_demo=0",
            (row["catalog_key"],),
        ).fetchone()
        if variant is None:
            raise ValueError("UNPUBLISHED_CANDIDATE")
        catalog = json.loads(variant["specifications"])["catalog"]
        trim = fact(catalog, "trim").get("value")
        drive = fact(catalog, "drivetrain").get("value")
        if trim == manifest["excluded_trim"]:
            continue
        if (trim, drive) not in matrix:
            raise ValueError(("CANDIDATE_NOT_IN_OFFICIAL_MATRIX", row["catalog_key"]))
        matched[(trim, drive)].append((row, variant, catalog))
    if set(matched) != matrix or any(len(items) != 1 for items in matched.values()):
        raise ValueError("OFFICIAL_MATRIX_NOT_BIJECTIVE_WITH_CANDIDATES")
    claims = []
    resolved = []
    for trim, drive in sorted(matrix):
        row, variant, catalog = matched[(trim, drive)][0]
        if (
            catalog["source_registry_id"] != "factory-honda-us"
            or catalog["original_market"] != "US"
            or (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED"
        ):
            raise ValueError(("FACTORY_SCOPE_CHANGED", row["catalog_key"]))
        existing = {
            r["fact_name"]: r
            for r in db.execute(
                "SELECT fact_name,value,reuse_status FROM commercial_fact_claims "
                "WHERE variant_id=? AND source_id='factory-honda-us'",
                (variant["id"],),
            )
        }
        required = [
            "make",
            "model",
            "model_year",
            "original_market",
            "powertrain",
            "fuel",
            "engine_displacement",
            "engine_description",
            "transmission_description",
        ]
        if any(
            n not in existing or existing[n]["reuse_status"] != "COMMERCIAL_OK" for n in required
        ):
            raise ValueError(("SAFE_ANCHOR_MISSING", row["catalog_key"]))
        config = configuration_keys(catalog)
        if config["drivetrain"] != drive or not all(config.values()):
            raise ValueError(("EXACT_CANDIDATE_DISAGREEMENT", row["catalog_key"]))
        scope = {
            "make": "Honda",
            "model": "CR-V",
            "model_year": manifest["model_year"],
            "original_market": "US",
            "granularity": "EXACT_CONFIGURATION",
            "configuration_keys": config,
            "source_record_id": source["id"],
            "source_authenticity": "OFFICIAL_PUBLISHER",
            "extraction_scope": "ISOLATED_FACT",
            "source_document_kind": "SPEC_SHEET",
            "az_rights_reference": AZ_RIGHTS_REFERENCE,
            "annual_source_sha256": manifest["annual_source_sha256"],
            "supporting_fwd_definition_url": manifest["fwd_definition_url"],
            "supporting_fwd_definition_sha256": manifest["fwd_definition_sha256"],
        }
        claims.append(
            {
                "variant_id": variant["id"],
                "catalog_key": row["catalog_key"],
                "fact_name": "drivetrain",
                "value": drive,
                "source_id": "factory-honda-us",
                "evidence_scope": scope,
                "reuse_status": "COMMERCIAL_OK",
                "source_url": manifest["annual_source_url"],
                "locator": (
                    f"overlay03:honda-crv-{manifest['model_year']}:trim:{trim};"
                    f"CVT:{'2WD' if drive == 'FWD' else 'AWD'}"
                ),
                "rights_basis": "FACTUAL_EXTRACTION",
                "rights_reference": RIGHTS_REFERENCE,
                "rights_checked_at": RIGHTS_DATE,
                "unit": None,
            }
        )
        resolved.append(
            {
                "catalog_key": row["catalog_key"],
                "make": "Honda",
                "model": "CR-V",
                "generation": catalog.get("generation"),
                "model_year": manifest["model_year"],
                "trim": trim,
                "engine": fact(catalog, "engine_description").get("value"),
                "transmission": fact(catalog, "transmission_description").get("value"),
                "drivetrain": drive,
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    prefix = (
        "honda-crv" if manifest["model_year"] == 2018 else f"honda-crv-{manifest['model_year']}"
    )
    for name, data in ((f"{prefix}-claims.jsonl", claims), (f"{prefix}-resolved.jsonl", resolved)):
        (out / name).write_text(
            "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in data),
            encoding="utf-8",
        )
    return {"source_record_id": source["id"], "reviewed_rows": len(resolved), "claims": len(claims)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--register-source", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            build(args.db, args.out, register=args.register_source, manifest_path=args.manifest),
            indent=2,
        )
    )
