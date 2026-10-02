"""Correct four Tesla MVP transmission facts using cached Tesla service pages.

Preparation is read-only. Publish the generated manifest with the existing
factory_bulk_publish runner, then use --apply-claims to replace only the four
commercial transmission claims. EPA candidate rows and source rights stay intact.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

from catalog_writer_lock import catalog_writer_lock
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.evidence import SourceRecord  # noqa: E402
from app.models.knowledge_ops import CommercialFactClaim, SourceRegistry  # noqa: E402
from app.schemas.knowledge import CatalogRecord, FactInput, ImportManifest  # noqa: E402
from app.services.catalog_verification import validate_publication  # noqa: E402
from app.services.commercial_fact_overlay import (  # noqa: E402
    claim_valid_for_candidate,
    upsert_claim,
)

OUT = ROOT / "deliverables/VerifiedData/usa-mvp-catalog-12-local-01"
MANIFEST = OUT / "tesla-transmission-correction-manifest.json"
OLD_VALUE = "Single-speed electric drive-unit reduction gearbox (Tesla gearbox + EPA A1)"
NEW_VALUE = "Electric drive-unit gearbox"
RIGHTS = "https://www.copyright.gov/help/faq/faq-protect.html"
AZ_RIGHTS = "https://www.copat.gov.az/docs/Qanunvericilik/Qanunlar/English/Law-Database.pdf"
CASES = (
    ("Model 3", 2020, "87112077-3e8a-49a8-a834-3ec307439652"),
    ("Model S", 2016, "8a122dde-ff61-4cfe-84f6-aea71096db56"),
    ("Model X", 2018, "32a88c98-61ce-45fc-bd06-68a344e6120c"),
    ("Model Y", 2021, "bff35d1a-42dc-49bd-ae4c-a96514603ab5"),
)


def engine():
    return create_engine("sqlite:///" + (ROOT / "autoexpert.db").as_posix())


def source_text(model: str) -> str:
    return f"Tesla {model} Service Manual, Gearbox Fluid - Rear Drive Unit."


def record_for(db: Session, model: str, year: int, variant_id: str) -> CatalogRecord:
    variant = db.get(VehicleVariant, variant_id)
    if not variant or not variant.catalog_key.startswith("factory-tesla-us:"):
        raise ValueError(("TESLA_VARIANT_MISSING", model))
    catalog = variant.specifications["catalog"]
    if (
        catalog["make"],
        catalog["model"],
        catalog["model_year"],
        catalog["original_market"],
        catalog["facts"]["powertrain"]["value"],
        catalog["facts"]["drivetrain"]["value"],
        catalog["facts"]["transmission_description"]["value"],
    ) != ("Tesla", model, year, "US", "BEV", "AWD", OLD_VALUE):
        raise ValueError(("TESLA_MVP_SCOPE_CHANGED", model))
    candidate = {
        key: copy.deepcopy(value)
        for key, value in catalog.items()
        if key in CatalogRecord.model_fields
    }
    candidate["facts"] = {
        name: {
            key: copy.deepcopy(value)
            for key, value in fact.items()
            if key in FactInput.model_fields
        }
        for name, fact in catalog["facts"].items()
    }
    transmission = candidate["facts"]["transmission_description"]
    ref = transmission["documentary_source"]
    if ref["registry_id"] != "factory-tesla-us" or "service.tesla.com" not in ref["url"]:
        raise ValueError(("TESLA_SERVICE_REFERENCE_MISSING", model))
    raw = ROOT / ".localdata" / "raw" / ref["sha256"]
    if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest() != ref["sha256"]:
        raise ValueError(("TESLA_SERVICE_CACHE_MISMATCH", model))
    if b"Gearbox Fluid" not in raw.read_bytes() and b"Gearbox" not in raw.read_bytes():
        raise ValueError(("TESLA_GEARBOX_HEADING_MISSING", model))
    transmission["value"] = NEW_VALUE
    transmission["locator"] = source_text(model)
    ref["locator"] = source_text(model)
    candidate["identity_verification"]["previous_revision_id"] = variant.published_revision_id
    candidate["identity_verification"]["field_evidence"]["transmission_description"] = [
        copy.deepcopy(ref)
    ]
    candidate["identity_verification"]["review_note"] = (
        "MVP transmission correction: cached official Tesla service page confirms "
        "drive-unit gearbox; EPA A1 annotation is not a commercial transmission value."
    )
    candidate["revision_note"] = (
        "Tesla MVP commercial fact correction: publish only the drive-unit gearbox "
        "description supported by the immutable official Tesla service document."
    )
    record = CatalogRecord.model_validate(candidate)
    result = validate_publication(db, record, variant)
    if not result or result["state"] != "VERIFIED_SCOPED":
        raise ValueError(("TESLA_CORRECTION_PREFLIGHT_FAILED", model))
    return record


def prepare() -> None:
    with Session(engine()) as db:
        records = [record_for(db, *case) for case in CASES]
        manifest = ImportManifest(
            source_id="factory-tesla-us",
            parser="manifest-json-v1",
            year_min=2016,
            year_max=2021,
            makes=["Tesla"],
            selection_basis=(
                "Reviewed four existing Tesla US BEV MVP variants; replace an EPA-labelled "
                "consumer transmission description with the narrow gearbox fact directly "
                "supported by cached Tesla service pages. No new vehicle rows."
            ),
            records=records,
        )
    OUT.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        existing = ImportManifest.model_validate_json(MANIFEST.read_text(encoding="utf-8"))
        if existing.model_dump(mode="json") != manifest.model_dump(mode="json"):
            raise ValueError("TESLA_CORRECTION_MANIFEST_CHANGED")
    else:
        MANIFEST.write_text(
            manifest.model_dump_json(indent=2, exclude_none=False), encoding="utf-8"
        )
    print(
        json.dumps({"state": "PREFLIGHT_PASS", "records": len(records), "manifest": str(MANIFEST)})
    )


def apply_claims() -> None:
    manifest = ImportManifest.model_validate_json(MANIFEST.read_text(encoding="utf-8"))
    expected = {record.model: record for record in manifest.records}
    if set(expected) != {case[0] for case in CASES}:
        raise ValueError("TESLA_CORRECTION_MANIFEST_SCOPE")
    with catalog_writer_lock(), Session(engine()) as db:
        registry = db.get(SourceRegistry, "factory-tesla-us")
        if not registry:
            raise ValueError("TESLA_REGISTRY_MISSING")
        for model, year, variant_id in CASES:
            variant = db.get(VehicleVariant, variant_id)
            if (
                not variant
                or variant.specifications["catalog"]["revision_id"]
                == expected[model].identity_verification.previous_revision_id
            ):
                raise ValueError(("TESLA_CORRECTION_NOT_PUBLISHED", model))
            catalog = variant.specifications["catalog"]
            facts = catalog["facts"]
            if (
                catalog["make"],
                catalog["model"],
                catalog["model_year"],
                facts["transmission_description"]["value"],
            ) != ("Tesla", model, year, NEW_VALUE):
                raise ValueError(("TESLA_CORRECTION_PUBLICATION_MISMATCH", model))
            prior_claims = list(
                db.scalars(
                    select(CommercialFactClaim).where(
                        CommercialFactClaim.variant_id == variant_id,
                        CommercialFactClaim.locator.like(f"usa-mvp-12:{model}:MY{year}:%"),
                    )
                )
            )
            for required in ("powertrain", "engine_description", "drivetrain"):
                if sum(prior.fact_name == required for prior in prior_claims) != 1:
                    raise ValueError(("TESLA_COMPANION_CLAIM_COUNT", model, required))
            if (
                sum(
                    prior.fact_name == "transmission_description" and prior.value == OLD_VALUE
                    for prior in prior_claims
                )
                != 1
            ):
                raise ValueError(("TESLA_OLD_TRANSMISSION_CLAIM_MISSING", model))
            for prior in prior_claims:
                if prior.fact_name == "transmission_description" and prior.value == OLD_VALUE:
                    prior.reuse_status = "INTERNAL_RESEARCH"
                elif prior.fact_name in {"powertrain", "engine_description", "drivetrain"}:
                    scope = copy.deepcopy(prior.evidence_scope)
                    if scope["configuration_keys"]["transmission_description"] not in {
                        OLD_VALUE,
                        NEW_VALUE,
                    }:
                        raise ValueError(("TESLA_CLAIM_SCOPE_CHANGED", model, prior.fact_name))
                    scope["configuration_keys"]["transmission_description"] = NEW_VALUE
                    prior.evidence_scope = scope
                    if not claim_valid_for_candidate(prior, catalog, registry):
                        raise ValueError(("TESLA_COMPANION_CLAIM_INVALID", model, prior.fact_name))
            ref = facts["transmission_description"]["documentary_source"]
            linked = db.get(SourceRecord, facts["transmission_description"]["source_id"])
            if not linked or linked.url != ref["url"]:
                raise ValueError(("TESLA_SOURCE_RECORD_MISMATCH", model))
            keys = {
                "engine_displacement": None,
                "engine_description": facts["engine_description"]["value"],
                "transmission_description": NEW_VALUE,
                "drivetrain": facts["drivetrain"]["value"],
            }
            scope = {
                "make": "Tesla",
                "model": model,
                "model_year": year,
                "original_market": "US",
                "granularity": "EXACT_CONFIGURATION",
                "configuration_keys": keys,
                "source_record_id": linked.id,
                "extraction_scope": "ISOLATED_FACT",
                "source_document_kind": "SPEC_SHEET",
                "source_authenticity": "OFFICIAL_PUBLISHER",
                "az_rights_reference": AZ_RIGHTS,
                "document_sha256": ref["sha256"],
            }
            claim = upsert_claim(
                db,
                variant_id=variant_id,
                fact_name="transmission_description",
                value=NEW_VALUE,
                source_id="factory-tesla-us",
                evidence_scope=scope,
                reuse_status="COMMERCIAL_OK",
                source_url=ref["url"],
                locator=f"usa-mvp-12:{model}:MY{year}:Tesla-Service-Manual:Gearbox-Fluid-Rear-Drive-Unit",
                rights_basis="FACTUAL_EXTRACTION",
                rights_reference=RIGHTS,
                rights_checked_at=date.today().isoformat(),
            )
            if not claim_valid_for_candidate(claim, catalog, registry):
                raise ValueError(("TESLA_CORRECTION_CLAIM_INVALID", model))
        db.commit()
    print(json.dumps({"state": "CLAIMS_APPLIED", "records": len(CASES), "value": NEW_VALUE}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-claims", action="store_true")
    args = parser.parse_args()
    apply_claims() if args.apply_claims else prepare()
