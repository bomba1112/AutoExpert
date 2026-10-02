"""Promote one existing MY2018 Grand Cherokee 3.6/8AT/RWD fact bundle.

The FCA spec sheet is cached and checked before any database mutation.  The
default command is a dry run.  --apply adds isolated claims and a source
record through the existing overlay service; it never edits vehicle facts or
the EPA CORE.  Re-running --apply uses the same source/locator keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

from pypdf import PdfReader
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.enums import (  # noqa: E402
    ConfidenceLevel,
    DataOrigin,
    SourceTier,
    SourceUsageStatus,
)
from app.models.evidence import SourceRecord  # noqa: E402
from app.models.knowledge_ops import CommercialFactClaim, SourceRegistry  # noqa: E402
from app.services.commercial_fact_overlay import (  # noqa: E402
    claim_valid_for_candidate,
    project_commercial_catalog,
    upsert_claim,
)
from build_commercial_fact_overlay_batch import (  # noqa: E402
    AZ_RIGHTS_REFERENCE,
    RIGHTS_REFERENCE,
)
from catalog_writer_lock import catalog_writer_lock  # noqa: E402

MANIFEST = ROOT / "data/manifests/usa-mvp-jeep-grand-cherokee-2018-rwd.json"
DB = ROOT / "autoexpert.db"
OUT = ROOT / "deliverables/VerifiedData/usa-mvp-jeep-2018-rwd/official-claims.jsonl"
RIGHTS_DATE = "2026-09-29"
MECHANICAL = frozenset(
    {
        "powertrain",
        "fuel",
        "engine_displacement",
        "engine_description",
        "transmission_description",
        "transmission_family",
        "drivetrain",
    }
)


def _text(page) -> str:
    return " ".join((page.extract_text() or "").replace("\xad", "").split()).casefold()


def verify_cached_spec(manifest: dict) -> Path:
    path = ROOT / ".localdata/raw" / manifest["document_sha256"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["document_sha256"]:
        raise ValueError("FCA_SPEC_CACHE_MISSING_OR_HASH_MISMATCH")
    reader = PdfReader(path)
    if len(reader.pages) != 17:
        raise ValueError("FCA_SPEC_PAGE_COUNT_CHANGED")
    checks = {
        0: (
            "2018 jeep",
            "grand cherokee",
            "layout front engine, rear- or four-wheel drive",
            "engine: 3.6-liter pentastar v-6",
            "unleaded regular",
        ),
        1: ("2wd and 4wd",),
        4: ("torqueflite 8hp70 automatic, eight-speed overdrive", "3.6-liter"),
        6: ("v-6 4x2", "rear", "standard on 4x4 models"),
        12: ("2wd laredo 3.6-liter", "4wd limited"),
    }
    for page, phrases in checks.items():
        text = _text(reader.pages[page])
        if not all(phrase in text for phrase in phrases):
            raise ValueError(("FCA_SPEC_APPLICABILITY_CHECK_FAILED", page + 1))
    return path


def _catalog_from_sqlite(db_path: Path, manifest: dict) -> tuple[dict, str, SimpleNamespace]:
    connection = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT id,catalog_key,specifications,published_revision_id,is_demo "
            "FROM vehicle_variants WHERE id=?",
            (manifest["variant_id"],),
        ).fetchone()
        if (
            not row
            or row["catalog_key"] != manifest["catalog_key"]
            or not row["published_revision_id"]
            or row["is_demo"]
        ):
            raise ValueError("JEEP_CANDIDATE_MISSING_OR_CHANGED")
        catalog = json.loads(row["specifications"])["catalog"]
        for key in ("make", "model", "model_year", "original_market"):
            if catalog.get(key) != manifest[key]:
                raise ValueError(("JEEP_IDENTITY_CHANGED", key))
        if catalog.get("source_registry_id") != manifest["source_id"]:
            raise ValueError("JEEP_SOURCE_REGISTRY_CHANGED")
        if (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED":
            raise ValueError("JEEP_STRICT_FACTORY_CANDIDATE_CHANGED")
        for name, expected in manifest["facts"].items():
            if name in MECHANICAL:
                fact = (catalog.get("facts") or {}).get(name) or {}
                if fact.get("status") != "CONFIRMED" or fact.get("value") != expected["value"]:
                    raise ValueError(("JEEP_MECHANICAL_TUPLE_CHANGED", name))
        source_row = connection.execute(
            "SELECT id,state,paused,config FROM knowledge_sources WHERE id=?",
            (manifest["source_id"],),
        ).fetchone()
        if not source_row:
            raise ValueError("JEEP_SOURCE_REGISTRY_MISSING")
        source = SimpleNamespace(
            id=source_row["id"],
            state=source_row["state"],
            paused=bool(source_row["paused"]),
            config=json.loads(source_row["config"]),
        )
        record = connection.execute(
            "SELECT id FROM source_records WHERE url=?", (manifest["document_url"],)
        ).fetchone()
        record_id = record["id"] if record else str(uuid5(NAMESPACE_URL, manifest["document_url"]))
        return catalog, record_id, source
    finally:
        connection.close()


def build_claims(manifest: dict, source_record_id: str) -> list[dict]:
    config = {
        key: manifest["facts"][key]["value"]
        for key in (
            "engine_displacement",
            "engine_description",
            "transmission_description",
            "drivetrain",
        )
    }
    scope = {
        "make": manifest["make"],
        "model": manifest["model"],
        "model_year": manifest["model_year"],
        "original_market": manifest["original_market"],
        "granularity": "EXACT_CONFIGURATION",
        "configuration_keys": config,
        "source_record_id": source_record_id,
        # This accessible FCA media mirror is outside Jeep's publisher-host
        # allowlist.  Record an explicit document-authenticity review.
        "source_authenticity": "REVIEWED_MIRROR",
        "reviewer": manifest["reviewer"],
        "authenticity_review_note": (
            "Cached SHA256 matches the 17-page 2018 Jeep Grand Cherokee FCA North "
            "America specification, including media.fcanorthamerica.com footer, "
            "US EPA and US emissions context. Identical manufacturer sheet is "
            "indexed on the official Stellantis Media URL in this manifest. "
            "The 3.6L 2WD variant is rear drive; no 4x4-to-AWD promotion."
        ),
        "extraction_scope": "ISOLATED_FACT",
        "source_document_kind": "SPEC_SHEET",
        "source_document_sha256": manifest["document_sha256"],
        "official_publication_url": manifest["official_publication_url"],
        "az_rights_reference": AZ_RIGHTS_REFERENCE,
    }
    return [
        {
            "variant_id": manifest["variant_id"],
            "catalog_key": manifest["catalog_key"],
            "fact_name": name,
            "value": spec["value"],
            "source_id": manifest["source_id"],
            "evidence_scope": scope,
            "reuse_status": "COMMERCIAL_OK",
            "source_url": manifest["document_url"],
            "locator": f"usa-mvp-jeep-2018-rwd:{name}:{spec['locator']}",
            "rights_basis": "FACTUAL_EXTRACTION",
            "rights_reference": RIGHTS_REFERENCE,
            "rights_checked_at": RIGHTS_DATE,
            "unit": spec.get("unit"),
        }
        for name, spec in manifest["facts"].items()
    ]


def _validate_projection(catalog: dict, source, claims: list[dict]) -> bool:
    now = datetime.now(UTC)
    provisional = [
        SimpleNamespace(
            **{k: v for k, v in item.items() if k != "catalog_key"},
            id=str(uuid5(NAMESPACE_URL, item["locator"])),
            updated_at=now,
        )
        for item in claims
    ]
    if not all(claim_valid_for_candidate(claim, catalog, source) for claim in provisional):
        raise ValueError("JEEP_CLAIM_VALIDATION_FAILED")
    projected = project_commercial_catalog(catalog, provisional, {source.id: source})
    if projected is None or projected["facts"]["drivetrain"]["value"] != "RWD":
        raise ValueError("JEEP_PRODUCTION_PROJECTION_NOT_READY")
    return True


def dry_run(db_path: Path, manifest_path: Path, out: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_cached_spec(manifest)
    catalog, record_id, source = _catalog_from_sqlite(db_path, manifest)
    claims = build_claims(manifest, record_id)
    _validate_projection(catalog, source, claims)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in claims),
        encoding="utf-8",
    )
    return {
        "mode": "DRY_RUN",
        "variant_id": manifest["variant_id"],
        "source_record_id": record_id,
        "source_sha256": manifest["document_sha256"],
        "claim_count": len(claims),
        "projection_ready": True,
        "claims_file": str(out),
    }


def apply(db_path: Path, manifest_path: Path, out: Path) -> dict:
    # The dry run verifies source bytes, exact candidate tuple, claim rights,
    # and production projection without writing the application database.
    prepared = dry_run(db_path, manifest_path, out)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    engine = create_engine("sqlite:///" + db_path.resolve().as_posix())
    with catalog_writer_lock(), Session(engine) as db:
        variant = db.get(VehicleVariant, manifest["variant_id"])
        if variant is None or variant.catalog_key != manifest["catalog_key"]:
            raise ValueError("JEEP_CANDIDATE_CHANGED_BEFORE_APPLY")
        source = db.get(SourceRegistry, manifest["source_id"])
        if source is None:
            raise ValueError("JEEP_SOURCE_REGISTRY_MISSING_BEFORE_APPLY")
        record = db.scalar(select(SourceRecord).where(SourceRecord.url == manifest["document_url"]))
        if record is None:
            record = SourceRecord(
                id=prepared["source_record_id"],
                title="FCA North America MY2018 Jeep Grand Cherokee specifications",
                publisher="FCA US LLC / Jeep",
                url=manifest["document_url"],
                source_type="MANUFACTURER_SPEC_SHEET",
                source_tier=SourceTier.A,
                data_origin=DataOrigin.REAL,
                market="US",
                language="en",
                published_at=None,
                retrieved_at=datetime.now(UTC),
                notes=(
                    "Reviewed FCA media mirror of the 2018 US sheet; cached SHA256 "
                    + manifest["document_sha256"]
                    + "; official Stellantis Media copy: "
                    + manifest["official_publication_url"]
                    + ". Isolated vehicle facts only; no creative text/images reused."
                ),
                confidence=ConfidenceLevel.HIGH,
                usage_status=SourceUsageStatus.ACTIVE,
                is_demo=False,
            )
            db.add(record)
            db.flush()
        claims = build_claims(manifest, record.id)
        _validate_projection(variant.specifications["catalog"], source, claims)
        before = db.scalar(
            select(func.count()).select_from(CommercialFactClaim).where(
                CommercialFactClaim.variant_id == variant.id,
                CommercialFactClaim.source_id == manifest["source_id"],
                CommercialFactClaim.locator.like("usa-mvp-jeep-2018-rwd:%"),
            )
        )
        for item in claims:
            upsert_claim(
                db,
                **{k: v for k, v in item.items() if k != "catalog_key"},
            )
        after = db.scalar(
            select(func.count()).select_from(CommercialFactClaim).where(
                CommercialFactClaim.variant_id == variant.id,
                CommercialFactClaim.source_id == manifest["source_id"],
                CommercialFactClaim.locator.like("usa-mvp-jeep-2018-rwd:%"),
            )
        )
        if after != len(claims):
            raise ValueError(("JEEP_FACT_DUPLICATION", after, len(claims)))
        commercial_claims = list(
            db.scalars(
                select(CommercialFactClaim).where(
                    CommercialFactClaim.variant_id == variant.id,
                    CommercialFactClaim.reuse_status == "COMMERCIAL_OK",
                )
            )
        )
        if project_commercial_catalog(
            variant.specifications["catalog"], commercial_claims, {source.id: source}
        ) is None:
            raise ValueError("JEEP_APPLIED_PRODUCTION_PROJECTION_NOT_READY")
        record_id = record.id
        db.commit()
    return {
        "mode": "APPLY",
        "variant_id": manifest["variant_id"],
        "source_record_id": record_id,
        "claims_before": before,
        "claims_after": after,
        "claims_added": after - before,
        "production_projection_ready": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = (
        apply(args.db, args.manifest, args.out)
        if args.apply
        else dry_run(args.db, args.manifest, args.out)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
