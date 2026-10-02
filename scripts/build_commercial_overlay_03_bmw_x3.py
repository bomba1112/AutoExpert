"""Promote only the four existing X3 MY2015 tuples corroborated by BMW USA."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
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

MANIFEST = ROOT / "data/manifests/commercial-overlay-03-bmw-x3-2015-official.json"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03"
IDENTITY = ("make", "model", "model_year", "original_market", "generation")
FACT_NAMES = (
    "powertrain",
    "fuel",
    "engine_displacement",
    "engine_description",
    "transmission_description",
    "drivetrain",
)


def checked_documents(manifest: dict) -> None:
    texts = {}
    for name in ("technical_data", "pricing_guide", "press_kit"):
        item = manifest[name]
        path = ROOT / ".localdata/raw" / item["sha256"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(("BMW_DOCUMENT_HASH_MISMATCH", name))
        if name == "press_kit":
            content = html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8")))
            texts[name] = " ".join(content.split())
        else:
            reader = PdfReader(str(path))
            texts[name] = [" ".join((page.extract_text() or "").split()) for page in reader.pages]
    tech = texts["technical_data"]
    price = texts["pricing_guide"]
    press = texts["press_kit"].casefold()
    if len(tech) != 1 or len(price) != 6:
        raise ValueError("BMW_OFFICIAL_DOCUMENT_PAGE_COUNT")
    if not all(
        token in tech[0]
        for token in (
            "BMW U.S. Media Information",
            "Technical Data 2015 BMW X3",
            "X3 sDrive28i",
            "X3 xDrive28i",
            "X3 xDrive35i",
            "X3 xDrive28d",
            "automatic transmission 8",
            "1997 / 122",
            "1995 / 122",
            "2979 / 182",
            "Ultra Low Sulfur Diesel",
        )
    ):
        raise ValueError("BMW_TECHNICAL_MATRIX_CHANGED")
    if not all(
        token in price[0] + " " + price[3]
        for token in (
            "Pricing Guide X3 (F25)",
            "Model Year 2015",
            "X3 sDrive28i",
            "X3 xDrive28i",
            "X3 xDrive35i",
            "X3 xDrive28d",
            "205 STEPTRONIC automatic transmission STD STD STD STD",
            "203 All-wheel-drive STD STD STD",
        )
    ):
        raise ValueError("BMW_PRICING_MATRIX_CHANGED")
    if not all(
        token in press
        for token in (
            "2015 bmw x3",
            "rear-wheel drive bmw x3 sdrive28i",
            "xdrive intelligent all-wheel drive",
            "2.0-liter twinpower turbo diesel",
        )
    ):
        raise ValueError("BMW_PRESS_KIT_SCOPE_CHANGED")


def register_sources(db_path: Path, manifest: dict) -> None:
    engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
    with catalog_writer_lock(), Session(engine) as db:
        for name in ("technical_data", "pricing_guide", "press_kit"):
            item = manifest[name]
            source = db.scalar(select(SourceRecord).where(SourceRecord.url == item["url"]))
            title = item.get("title") or (
                f"BMW USA {manifest['model_year']} {manifest['model']} "
                f"{name.replace('_', ' ')}"
            )
            if source is None:
                db.add(
                    SourceRecord(
                        title=title,
                        publisher="BMW of North America, LLC",
                        url=item["url"],
                        source_type="CATALOG_PUBLICATION",
                        source_tier=SourceTier.A,
                        data_origin=DataOrigin.REAL,
                        market="US",
                        language="en",
                        published_at=None,
                        retrieved_at=datetime.now(UTC),
                        notes=(
                            "Isolated MY2015 X3 factual fields; SHA256 "
                            + item["sha256"]
                            + "; "
                            + item["locator"]
                            + ". No creative text or images reused."
                        ),
                        confidence=ConfidenceLevel.HIGH,
                        usage_status=SourceUsageStatus.ACTIVE,
                        is_demo=False,
                    )
                )
        db.commit()


def build(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT, *, register: bool = False):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checked_documents(manifest)
    if register:
        register_sources(db_path, manifest)
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    documents = {}
    for name in ("technical_data", "pricing_guide", "press_kit"):
        item = manifest[name]
        row = db.execute("SELECT id FROM source_records WHERE url=?", (item["url"],)).fetchone()
        if row is None:
            raise ValueError(("BMW_OFFICIAL_SOURCE_NOT_REGISTERED", name))
        documents[name] = (item, row["id"])
    claims, resolved = [], []
    for expected in manifest["variants"]:
        row = db.execute(
            "SELECT id,specifications FROM vehicle_variants WHERE catalog_key=? "
            "AND published_revision_id IS NOT NULL AND is_demo=0",
            (expected["catalog_key"],),
        ).fetchone()
        if row is None:
            raise ValueError(("BMW_UNPUBLISHED_CANDIDATE", expected["catalog_key"]))
        catalog = json.loads(row["specifications"])["catalog"]
        if (
            (catalog["make"], catalog["model"], catalog["model_year"])
            != ("BMW", "X3", 2015)
            or catalog["original_market"] != "US"
            or catalog.get("generation") != "F25"
            or catalog.get("source_registry_id") != "factory-bmw-us"
            or (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED"
            or not expected["designation"].startswith("X3 ")
            or fact(catalog, "powertrain").get("value") != "ICE"
            or fact(catalog, "fuel").get("value") != expected["fuel"]
            or fact(catalog, "engine_displacement").get("value")
            != expected["engine_displacement"]
            or fact(catalog, "drivetrain").get("value") != expected["drivetrain"]
            or fact(catalog, "transmission_description").get("value")
            != "8-speed Steptronic automatic"
        ):
            raise ValueError(("BMW_CANDIDATE_SCOPE_CONFLICT", expected["catalog_key"]))
        config = configuration_keys(catalog)
        if not all(config.values()):
            raise ValueError(("BMW_EXACT_KEY_INCOMPLETE", expected["catalog_key"]))
        for name in (*IDENTITY, *FACT_NAMES):
            document_name = (
                "pricing_guide"
                if name in ("generation", "transmission_description")
                else "press_kit"
                if name == "drivetrain"
                else "technical_data"
            )
            item, source_record_id = documents[document_name]
            scope = {
                "make": "BMW",
                "model": "X3",
                "model_year": 2015,
                "original_market": "US",
                "granularity": "EXACT_CONFIGURATION",
                "configuration_keys": config,
                "source_record_id": source_record_id,
                "source_authenticity": "OFFICIAL_PUBLISHER",
                "extraction_scope": "ISOLATED_FACT",
                "source_document_kind": "PRESS_KIT"
                if document_name == "press_kit"
                else "SPEC_SHEET",
                "az_rights_reference": AZ_RIGHTS_REFERENCE,
                "document_sha256": item["sha256"],
            }
            value = catalog[name] if name in IDENTITY else fact(catalog, name)["value"]
            claims.append(
                {
                    "variant_id": row["id"],
                    "catalog_key": expected["catalog_key"],
                    "fact_name": name,
                    "value": value,
                    "source_id": "factory-bmw-us",
                    "evidence_scope": scope,
                    "reuse_status": "COMMERCIAL_OK",
                    "source_url": item["url"],
                    "locator": (
                        f"overlay03:bmw-x3-2015:{document_name}:"
                        f"{expected['designation']}:{name};{item['locator']}"
                    ),
                    "rights_basis": "FACTUAL_EXTRACTION",
                    "rights_reference": RIGHTS_REFERENCE,
                    "rights_checked_at": RIGHTS_DATE,
                    "unit": None if name in IDENTITY else fact(catalog, name).get("unit"),
                }
            )
        resolved.append(
            {
                "catalog_key": expected["catalog_key"],
                "make": "BMW",
                "model": "X3",
                "generation": "F25",
                "model_year": 2015,
                "engine": fact(catalog, "engine_description")["value"],
                "transmission": fact(catalog, "transmission_description")["value"],
                "drivetrain": expected["drivetrain"],
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    for filename, items in (
        ("bmw-x3-claims.jsonl", claims),
        ("bmw-x3-resolved.jsonl", resolved),
    ):
        (out / filename).write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items),
            encoding="utf-8",
        )
    return {"reviewed_rows": len(resolved), "claims": len(claims)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--register-sources", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.out, register=args.register_sources), indent=2))
