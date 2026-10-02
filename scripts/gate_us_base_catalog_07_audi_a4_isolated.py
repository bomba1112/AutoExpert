"""Run the real publication gate for every A4 candidate in an isolated DB.

Uses acquired immutable bytes and the production validation function, while
leaving the live database and shared acquisition ledger untouched.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.knowledge_ops import RawDocument, SourceRegistry  # noqa: E402
from app.schemas.knowledge import CatalogRecord  # noqa: E402
from app.services.catalog_verification import IDENTITY_FIELDS, validate_publication  # noqa: E402
from app.services.knowledge_import import store_document  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-audi-a4-8w.json"
RECEIPT = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work/acquisition-audi-a4.json"
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work/publication-gate-audi-a4.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    receipts = {row["url"]: row for row in json.loads(RECEIPT.read_text(encoding="utf-8"))}
    settings = get_settings()
    original_dir = settings.knowledge_data_dir
    with tempfile.TemporaryDirectory(prefix="autoexpert-a4-gate-") as isolated_dir:
        settings.knowledge_data_dir = isolated_dir
        try:
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine, tables=[SourceRegistry.__table__, RawDocument.__table__])
            with Session(engine) as db:
                db.add(SourceRegistry(
                    id="factory-audi-us", title="Audi of America, Inc.", state="LOCAL_RESEARCH",
                    config={"factory_identity_evidence": True, "commercial_reuse": False, "cost_model": "FREE"},
                ))
                db.flush()
                docs = {}
                for key, spec in manifest["documents"].items():
                    receipt = receipts[spec["url"]]
                    raw = (ROOT / receipt["path"]).read_bytes()
                    doc = store_document(db, spec["source_id"], raw, locator=spec["url"], media_type=receipt["media_type"])
                    docs[key] = doc

                def ref(key: str, family: dict) -> dict:
                    spec = manifest["documents"][key]
                    doc = docs[key]
                    return {
                        "registry_id": spec["source_id"], "document_id": doc.id,
                        "sha256": doc.sha256, "url": spec["url"], "locator": spec["locator"],
                        "make": family["make"], "model": family["model"], "market": family["market"],
                        "model_year_from": spec["year_from"], "model_year_to": spec["year_to"],
                    }

                results = []
                for family in manifest["families"]:
                    for group in family["groups"]:
                        year = group["year_from"]
                        assert year == group["year_to"]
                        annual_keys = family["annual_documents"][str(year)]
                        first_key = annual_keys[0]
                        first_ref = ref(first_key, family)
                        annual_refs = [ref(key, family) for key in annual_keys]
                        generation_refs = [ref(key, family) for key in family["generation_documents"]]
                        facts = {}
                        for name, incoming in {**family["facts"], **group["facts"], "drivetrain": group["allowed_drives"][0]}.items():
                            fact = copy.deepcopy(incoming) if isinstance(incoming, dict) else {"value": incoming}
                            document_key = fact.pop("document_key", None)
                            fact_ref = ref(document_key, family) if document_key else first_ref
                            facts[name] = {
                                **fact,
                                "status": "CONFIRMED", "locator": fact_ref["locator"][:500],
                                "documentary_source": fact_ref,
                            }
                        record = CatalogRecord.model_validate({
                            "external_key": family["id"] + "-" + group["id"] + "-" + str(year),
                            "make": family["make"], "model": family["model"],
                            "configuration": group["configuration"],
                            "original_market": family["market"], "model_year": year,
                            "generation": family["generation"], "generation_code": family["generation_code"],
                            "facts": facts, "source_url": manifest["documents"][first_key]["url"],
                            "identity_verification": {
                                "previous_revision_id": "ISOLATED_BASELINE",
                                "applicability": family["scope_note"] + " " + group["configuration"],
                                "field_evidence": {
                                    key: generation_refs if key == "generation" else annual_refs
                                    for key in IDENTITY_FIELDS
                                },
                                "review_note": "Isolated production publication gate using real acquired Audi documents and exact annual source scope.",
                            },
                        })
                        result = validate_publication(db, record, SimpleNamespace(published_revision_id="ISOLATED_BASELINE"))
                        assert result and result["state"] == "VERIFIED_SCOPED"
                        results.append({
                            "group": group["id"], "year": year, "power_hp": (group["facts"]["power_hp"]["value"] if isinstance(group["facts"]["power_hp"], dict) else group["facts"]["power_hp"]),
                            "transmission": group["facts"]["transmission_family"],
                            "drivetrain": group["allowed_drives"][0], "gate": result["state"],
                        })
            engine.dispose()
        finally:
            settings.knowledge_data_dir = original_dir
    output = {
        "result": "PASS", "actual_production_function": "app.services.catalog_verification.validate_publication",
        "environment": "isolated in-memory SQLite and temporary document store",
        "model_year_rows": results, "verified_scoped_rows": len(results),
        "note": "Factory references are exercised against real acquired bytes. Production runner will substitute reviewed exact EPA rows for drivetrain references; its own preflight and publication remain required.",
        "live_db_writes": 0, "shared_ledger_writes": 0,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": "PASS", "verified_scoped_rows": len(results), "live_db_writes": 0}))


if __name__ == "__main__":
    main()
