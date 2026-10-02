"""Corroborate seven existing F32 Coupe MY2015 tuples from BMW USA documents."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sqlite3
from pathlib import Path

from build_commercial_fact_overlay_batch import (
    AZ_RIGHTS_REFERENCE,
    RIGHTS_DATE,
    RIGHTS_REFERENCE,
    configuration_keys,
    fact,
)
from build_commercial_overlay_03_bmw_x3 import register_sources
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/commercial-overlay-03-bmw-4-series-2015-official.json"
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
    text = {}
    for name in ("technical_data", "pricing_guide", "press_kit"):
        item = manifest[name]
        path = ROOT / ".localdata/raw" / item["sha256"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(("BMW_4_SERIES_DOCUMENT_HASH_MISMATCH", name))
        if name == "press_kit":
            raw = html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8")))
            text[name] = " ".join(raw.split())
        else:
            pdf = PdfReader(str(path))
            text[name] = [" ".join((p.extract_text() or "").split()) for p in pdf.pages]
    tech = " ".join(text["technical_data"])
    price = text["pricing_guide"]
    press = text["press_kit"].casefold()
    if (
        len(text["technical_data"]) != 2
        or len(price) != 9
        or "2015 BMW 4 Series Coupe" not in tech
        or tech.count("automatic transmission 8") != 4
        or tech.count("manual transmission 6") != 3
        or not all(
            token in tech
            for token in ("428i xDrive", "435i xDrive", "N20B20O0", "N55B30M0")
        )
    ):
        raise ValueError("BMW_4_SERIES_TECHNICAL_MATRIX_CHANGED")
    layout = PdfReader(str(ROOT / ".localdata/raw" / manifest["pricing_guide"]["sha256"]))
    page_six = layout.pages[5].extract_text(extraction_mode="layout")
    if not all(
        token in price[0] + " " + page_six
        for token in (
            "Pricing Guide 4 Series Coupe (F32)",
            "Model Year 2015",
            "ZMT",
            "Manual Transmission",
            "2TB",
            "Sport automatic transmission with shift paddles",
        )
    ):
        raise ValueError("BMW_4_SERIES_PRICING_MATRIX_CHANGED")
    zmt = next(line for line in page_six.splitlines() if line.startswith("ZMT"))
    if zmt.count("NC") != 3 or not all(
        token in press
        for token in (
            "twinpower turbo 2.0-liter 4-cylinder",
            "twin power turbo 3.0-liter inline six",
            "six-speed manual transmission",
            "rear-wheel drive",
            "xdrive, bmw’s intelligent all-wheel drive system",
        )
    ):
        raise ValueError("BMW_4_SERIES_APPLICABILITY_CHANGED")


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
            raise ValueError(("BMW_4_SERIES_SOURCE_NOT_REGISTERED", name))
        documents[name] = (item, row["id"])
    claims, resolved = [], []
    for expected in manifest["variants"]:
        row = db.execute(
            "SELECT id,specifications FROM vehicle_variants WHERE catalog_key=? "
            "AND published_revision_id IS NOT NULL AND is_demo=0",
            (expected["catalog_key"],),
        ).fetchone()
        if row is None:
            raise ValueError(("BMW_4_SERIES_UNPUBLISHED_CANDIDATE", expected["catalog_key"]))
        catalog = json.loads(row["specifications"])["catalog"]
        if (
            (catalog["make"], catalog["model"], catalog["model_year"])
            != ("BMW", "4 Series", 2015)
            or catalog["original_market"] != "US"
            or catalog.get("generation") != "F32"
            or catalog.get("source_registry_id") != "factory-bmw-us"
            or (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED"
            or fact(catalog, "powertrain").get("value") != "ICE"
            or fact(catalog, "fuel").get("value") != "GASOLINE"
            or fact(catalog, "engine_displacement").get("value")
            != expected["engine_displacement"]
            or fact(catalog, "transmission_description").get("value")
            != expected["transmission_description"]
            or fact(catalog, "drivetrain").get("value") != expected["drivetrain"]
            or (
                expected["designation"].startswith("428i")
                and "428i" not in expected["catalog_key"]
            )
            or (
                expected["designation"].startswith("435i")
                and "435i" not in expected["catalog_key"]
            )
        ):
            raise ValueError(("BMW_4_SERIES_CANDIDATE_SCOPE_CONFLICT", expected["catalog_key"]))
        config = configuration_keys(catalog)
        if not all(config.values()):
            raise ValueError(("BMW_4_SERIES_EXACT_KEY_INCOMPLETE", expected["catalog_key"]))
        for name in (*IDENTITY, *FACT_NAMES):
            document_name = (
                "press_kit"
                if name in ("engine_description", "drivetrain")
                else "pricing_guide"
                if name == "generation"
                else "technical_data"
            )
            item, source_record_id = documents[document_name]
            scope = {
                "make": "BMW",
                "model": "4 Series",
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
                "my2015_technical_document_sha256": manifest["technical_data"]["sha256"],
                "my2015_pricing_document_sha256": manifest["pricing_guide"]["sha256"],
            }
            value = catalog[name] if name in IDENTITY else fact(catalog, name)["value"]
            locator = (
                f"overlay03:bmw-4-series-2015:{document_name}:"
                f"{expected['designation']}:{expected['transmission_description']}:"
                f"{expected['drivetrain']}:{name};{item['locator']}"
            )
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
                    "locator": locator,
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
                "model": "4 Series",
                "generation": "F32",
                "model_year": 2015,
                "engine": fact(catalog, "engine_description")["value"],
                "transmission": expected["transmission_description"],
                "drivetrain": expected["drivetrain"],
            }
        )
    out.mkdir(parents=True, exist_ok=True)
    for filename, items in (
        ("bmw-4-series-claims.jsonl", claims),
        ("bmw-4-series-resolved.jsonl", resolved),
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
