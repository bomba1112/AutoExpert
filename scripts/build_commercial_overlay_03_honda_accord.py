"""Corroborate three existing 2017 Accord sedan candidates from Honda's facts guide."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from pypdf import PdfReader
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

MANIFEST = ROOT / "data/manifests/commercial-overlay-03-honda-accord-2017-official.json"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03"
NAMES = (
    "make",
    "model",
    "model_year",
    "original_market",
    "powertrain",
    "fuel",
    "engine_displacement",
    "engine_description",
    "transmission_description",
    "drivetrain",
)


def checked_document(manifest: dict) -> Path:
    path = ROOT / ".localdata/raw" / manifest["sha256"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("HONDA_FACTS_GUIDE_CACHE_HASH_MISMATCH")
    pdf = PdfReader(str(path))
    required = {
        1: ("2017 Accord Facts Guide", "ninth-generation Accord"),
        89: ("2017 ACCORD SEDAN SPECIFICATIONS", "2356 cc", "3471 cc"),
        90: (
            "6-Speed Manual Transmission",
            "Continuously Variable Transmission",
            "6-Speed Automatic Transmission",
        ),
        92: ("Required Fuel", "Regular Unleaded"),
        138: ("Front-Wheel Drive", "All Honda cars", "front-wheel drive"),
    }
    for number, phrases in required.items():
        page = " ".join((pdf.pages[number - 1].extract_text() or "").split())
        clean = page.replace("\xad", "-").replace("‐", "-").casefold()
        if not all(phrase.casefold() in clean for phrase in phrases):
            raise ValueError(("HONDA_FACTS_GUIDE_PAGE_CHECK_FAILED", number))
    return path


def register_source(db_path: Path, manifest: dict) -> str:
    checked_document(manifest)
    engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
    with catalog_writer_lock(), Session(engine) as db:
        source = db.scalar(select(SourceRecord).where(SourceRecord.url == manifest["url"]))
        if source is None:
            source = SourceRecord(
                title="Honda 2017 Accord Facts Guide, sedan specification matrix",
                publisher="American Honda Motor Co.",
                url=manifest["url"],
                source_type="CATALOG_PUBLICATION",
                source_tier=SourceTier.A,
                data_origin=DataOrigin.REAL,
                market="US",
                language="en",
                published_at=None,
                retrieved_at=datetime.now(UTC),
                notes=(
                    "Exact isolated MY2017 Accord sedan factual fields; SHA256 "
                    + manifest["sha256"]
                    + "; locators pp1,89-92,138. No creative text or images reused."
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
) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checked_document(manifest)
    if register:
        register_source(db_path, manifest)
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    source = db.execute("SELECT id FROM source_records WHERE url=?", (manifest["url"],)).fetchone()
    if source is None:
        raise ValueError("HONDA_FACTS_GUIDE_SOURCE_NOT_REGISTERED")
    claims = []
    resolved = []
    for expected in manifest["variants"]:
        row = db.execute(
            "SELECT id,specifications FROM vehicle_variants WHERE catalog_key=? "
            "AND published_revision_id IS NOT NULL AND is_demo=0",
            (expected["catalog_key"],),
        ).fetchone()
        if row is None:
            raise ValueError(("UNPUBLISHED_CANDIDATE", expected["catalog_key"]))
        catalog = json.loads(row["specifications"])["catalog"]
        if (
            (catalog["make"], catalog["model"], catalog["model_year"]) != ("Honda", "Accord", 2017)
            or catalog["original_market"] != "US"
            or catalog.get("generation") != manifest["generation"]
            or catalog.get("source_registry_id") != "factory-honda-us"
            or (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED"
        ):
            raise ValueError(("CANDIDATE_SCOPE_CONFLICT", expected["catalog_key"]))
        for name in (
            "engine_displacement",
            "engine_description",
            "transmission_description",
            "drivetrain",
        ):
            if fact(catalog, name).get("value") != expected[name]:
                raise ValueError(("CANDIDATE_FACT_CONFLICT", expected["catalog_key"], name))
        if (
            fact(catalog, "powertrain").get("value") != "ICE"
            or fact(catalog, "fuel").get("value") != "GASOLINE"
        ):
            raise ValueError(("CANDIDATE_FUEL_CONFLICT", expected["catalog_key"]))
        config = configuration_keys(catalog)
        if not all(config.values()):
            raise ValueError(("EXACT_KEY_INCOMPLETE", expected["catalog_key"]))
        scope = {
            "make": "Honda",
            "model": "Accord",
            "model_year": 2017,
            "original_market": "US",
            "granularity": "EXACT_CONFIGURATION",
            "configuration_keys": config,
            "source_record_id": source["id"],
            "source_authenticity": "OFFICIAL_PUBLISHER",
            "extraction_scope": "ISOLATED_FACT",
            "source_document_kind": "SPEC_SHEET",
            "az_rights_reference": AZ_RIGHTS_REFERENCE,
            "document_sha256": manifest["sha256"],
        }
        for name in NAMES:
            value = (
                catalog[name]
                if name in ("make", "model", "model_year", "original_market")
                else fact(catalog, name)["value"]
            )
            locator = (
                manifest["source_locators"].get(name) or manifest["source_locators"]["identity"]
            )
            claims.append(
                {
                    "variant_id": row["id"],
                    "catalog_key": expected["catalog_key"],
                    "fact_name": name,
                    "value": value,
                    "source_id": "factory-honda-us",
                    "evidence_scope": scope,
                    "reuse_status": "COMMERCIAL_OK",
                    "source_url": manifest["url"],
                    "locator": f"overlay03:honda-accord-2017:{locator};fact:{name}",
                    "rights_basis": "FACTUAL_EXTRACTION",
                    "rights_reference": RIGHTS_REFERENCE,
                    "rights_checked_at": RIGHTS_DATE,
                    "unit": None
                    if name in ("make", "model", "model_year", "original_market")
                    else fact(catalog, name).get("unit"),
                }
            )
        resolved.append(
            {
                "catalog_key": expected["catalog_key"],
                "make": "Honda",
                "model": "Accord",
                "generation": manifest["generation"],
                "model_year": 2017,
                "engine": fact(catalog, "engine_description")["value"],
                "transmission": fact(catalog, "transmission_description")["value"],
                "drivetrain": "FWD",
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (
        ("honda-accord-claims.jsonl", claims),
        ("honda-accord-resolved.jsonl", resolved),
    ):
        (out / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
            encoding="utf-8",
        )
    return {"source_record_id": source["id"], "reviewed_rows": len(resolved), "claims": len(claims)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--register-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.out, register=args.register_source), indent=2))
