"""Prepare reviewed documentary corrections for the frozen cohort, using cached official bytes."""
# ruff: noqa: E402, E501

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal
from app.models.knowledge_ops import SourceRegistry
from app.models.user import User
from app.schemas.knowledge import CatalogRecord, FactInput, ImportManifest
from app.services.catalog_buyer import records
from app.services.catalog_verification import IDENTITY_FIELDS
from app.services.factory_tables import columns, common_facts, matched_columns
from app.services.knowledge_import import (
    enqueue,
    normalized,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/verification-51"
MANIFEST = ROOT / "data/manifests/us-51-factory-reviewed.json"
COHORT = ROOT / "data/manifests/us-51-verification-cohort.json"
BMW = "https://www.press.bmwgroup.com/usa/article/detail/T0442407EN_US/the-new-2025-bmw-3-series"
MAINTENANCE = "https://www.bmwusa.com/content/dam/bmw/marketUS/common/warranty-books/2025/BMW_MY25_Maintenance_with_BEVs.pdf"


def public_record(c):
    value = {k: copy.deepcopy(v) for k, v in c.items() if k in CatalogRecord.model_fields}
    value["facts"] = {
        k: {a: copy.deepcopy(b) for a, b in f.items() if a in FactInput.model_fields}
        for k, f in c["facts"].items()
    }
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-reviewed", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    with SessionLocal() as db:
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if actor is None:
            raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
        if not MANIFEST.exists():
            prepare(db)
        manifest = ImportManifest.model_validate_json(MANIFEST.read_text(encoding="utf-8"))
        if not args.publish_reviewed:
            print(json.dumps({"status": "REVIEW_MANIFEST_READY", "records": len(manifest.records)}))
            return
        job = enqueue(db, manifest)
        if job.state != "PUBLISHED":
            while job.state in {"QUEUED", "RUNNING"}:
                process_job(db, job.id, batch_size=25)
            if job.state == "STAGED":
                review_job(
                    db,
                    job,
                    actor,
                    note="Reviewed cached manufacturer table cells; exact cohort/year, ambiguous trims only contribute invariant fields; BMW HEV to MHEV refinement and Sportage conflict documented",
                    approve=True,
                )
            publish_job(
                db,
                job,
                actor,
                note="Publish documentary corrections to existing variants; preserve EPA source facts and old revisions; scoped verification only",
            )
        (OUT / "publication.json").write_text(
            json.dumps(
                {
                    "status": job.state,
                    "job_id": job.id,
                    "records": len(manifest.records),
                    "new_models": 0,
                    "new_variants": 0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(json.dumps({"status": job.state, "records": len(manifest.records)}))


def prepare(db):
    cohort = json.loads(COHORT.read_text())
    keys = {(normalized(r["make"]), normalized(r["model"]), r["year"]): r for r in cohort["cohort"]}
    all_rows = [
        (v, c)
        for v, c in records(db)
        if c["original_market"] == "US"
        and (normalized(c["make"]), normalized(c["model"]), c["model_year"]) in keys
    ]
    if not all("target_variant_ids" in r for r in cohort["cohort"]):
        for r in cohort["cohort"]:
            r["target_variant_ids"] = [
                v.id
                for v, c in all_rows
                if normalized(c["make"]) == normalized(r["make"])
                and normalized(c["model"]) == normalized(r["model"])
                and c["model_year"] == r["year"]
            ]
        COHORT.write_text(json.dumps(cohort, indent=2), encoding="utf-8")
    for sid, title in [
        ("factory-bmw-us", "BMW of North America · factory documents"),
        ("factory-kia-us", "Kia America · factory specifications"),
    ]:
        if db.get(SourceRegistry, sid) is None:
            db.add(
                SourceRegistry(
                    id=sid,
                    title=title,
                    state="LOCAL_RESEARCH",
                    config={
                        "owner": title,
                        "markets": ["US"],
                        "cost_model": "FREE",
                        "commercial_reuse": False,
                        "factory_identity_evidence": True,
                        "data_types": ["factory_specification", "maintenance"],
                        "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
                        "display_rights": "LOCAL_RESEARCH_ONLY",
                        "rights": "COMMERCIAL_REUSE_NOT_ESTABLISHED",
                        "checked_at": "2026-09-20",
                    },
                )
            )
    db.flush()
    epa = db.get(SourceRegistry, "epa")
    epa.config = {**epa.config, "identity_evidence_fields": ["market", "model_year", "drivetrain"]}
    receipts = {
        r["url"]: r
        for r in json.loads(
            (ROOT / "deliverables/VerifiedData/acquisition-ledger.json").read_text()
        )
        if r.get("http_status") == 200 and r.get("sha256")
    }
    docs = {}

    def reference(c, url, sid, locator):
        key = (sid, url)
        if key not in docs:
            receipt = receipts[url]
            content = (
                ROOT / ".localdata/verified-source-documents" / receipt["sha256"]
            ).read_bytes()
            docs[key] = store_document(
                db, sid, content, locator=url, media_type=receipt.get("media_type", "text/html")
            )
        doc = docs[key]
        return dict(
            registry_id=sid,
            document_id=doc.id,
            sha256=doc.sha256,
            url=url,
            locator=locator,
            make=c["make"],
            model=c["model"],
            market="US",
            model_year=c["model_year"],
        )

    revised, decisions = [], []
    for variant, c in all_rows:
        value = public_record(c)
        if c["make"] == "BMW" and c["model"] == "3 Series" and c["model_year"] == 2025:
            # This is reviewed source mapping data, not product/UI behavior.
            if c["external_key"] not in {"48163", "48164"}:
                continue
            ref = reference(
                c,
                BMW,
                "factory-bmw-us",
                "US MY2025 330i / 330i xDrive columns; seventh generation paragraph; B48B20O2 paragraph",
            )
            drive = reference(
                c,
                c["source_url"],
                "epa",
                "EPA vehicle " + c["external_key"] + ": drive field, matched make/model/year",
            )
            changes = {
                "engine_description": "B48B20O2 · 1998 cm3 · I4 turbo · 48V MHEV",
                "engine_code": "B48B20O2",
                "powertrain": "MHEV",
                "transmission_description": "8-speed Steptronic automatic",
                "transmission_family": "AT",
                "gears": 8,
            }
            for key, data in changes.items():
                value["facts"][key] = {
                    "value": data,
                    "locator": ref["locator"],
                    "documentary_source": ref,
                }
            value["facts"]["drivetrain"]["documentary_source"] = drive
            value["generation"] = "Seventh generation · US sedan"
            value["identity_verification"] = {
                "previous_revision_id": variant.published_revision_id,
                "applicability": "US model year 2025, 330i Sedan or 330i xDrive Sedan as individually identified by the existing EPA configuration. No other years, Touring, M340i, trim packages or individual VIN certified.",
                "field_evidence": {
                    k: [drive if k == "drivetrain" else ref] for k in IDENTITY_FIELDS
                },
                "review_note": "Manufacturer specifies seventh generation, B48B20O2, 48V mild hybrid and 8-speed Steptronic; EPA confirms individual RWD/AWD configuration. EPA HEV is refined to MHEV. Gearbox internal code and entire generation production interval remain unknown.",
            }
            value["documentary_sections"] = [
                {
                    "key": "engine",
                    "status": "EVIDENCED",
                    "references": [ref],
                    "text": {
                        "ru": "Для этих версий 2025 года BMW указывает B48B20O2: 1998 см³, четыре цилиндра, турбонаддув и мягкий гибрид 48 В. Это уточнение общей категории HEV исходной записи EPA.",
                        "az": "Bu 2025 versiyaları üçün BMW B48B20O2 göstərir: 1998 sm³, dörd silindr, turbo və 48 V yumşaq hibrid. EPA qeydindəki ümumi HEV kateqoriyası dəqiqləşdirilib.",
                    },
                },
                {
                    "key": "transmission",
                    "status": "EVIDENCED",
                    "references": [ref],
                    "text": {
                        "ru": "Подтверждена 8-ступенчатая автоматическая Steptronic. Внутренний код коробки пока не подтверждён; вывод не распространяется на другие годы или модели.",
                        "az": "8-pilləli avtomatik Steptronic təsdiqlənib. Qutunun daxili kodu hələ təsdiqlənməyib; nəticə başqa illərə və modellərə aid deyil.",
                    },
                },
                {
                    "key": "applicability",
                    "status": "EVIDENCED",
                    "references": [ref, drive],
                    "text": {
                        "ru": "Область проверки: США, 2025 год, седан 330i с задним приводом либо 330i xDrive с полным приводом. Пакеты комплектации и состояние конкретного автомобиля не установлены.",
                        "az": "Yoxlama sahəsi: ABŞ, 2025, arxa ötürücülü 330i və ya tam ötürücülü 330i xDrive sedan. Təchizat paketləri və konkret avtomobilin vəziyyəti müəyyən edilməyib.",
                    },
                },
            ]
            value["revision_note"] = (
                "Factory verification review: retain EPA consumption; refine HEV to documented 48V MHEV and add scoped factory identity. No whole-generation or VIN certification."
            )
            decisions.append(
                {
                    "make": c["make"],
                    "model": c["model"],
                    "year": c["model_year"],
                    "external_key": c["external_key"],
                    "decision": "VERIFIED_SCOPED",
                    "refinement": {"powertrain": {"before": "HEV", "after": "MHEV"}},
                }
            )
            revised.append(value)
        elif c["make"] == "Kia":
            power = c["facts"].get("powertrain", {}).get("value")
            slug = c["model"].lower().replace(" ", "-")
            if slug == "optima" and power in {"HEV", "PHEV"}:
                slug += "-hybrid" if power == "HEV" else "-phev"
            if slug == "niro":
                slug = (
                    "niro-hev" if power == "HEV" else "niro-phev" if power == "PHEV" else "niro-ev"
                )
            if power in {"HEV", "PHEV"} and c["model"] not in {"Optima", "Niro"}:
                continue  # Do not bind an ICE specifications document to its hybrid sibling.
            url = f"https://www.kiamedia.com/us/en/models/{slug}/{c['model_year']}/specifications"
            if url not in receipts:
                continue
            content = (
                ROOT / ".localdata/verified-source-documents" / receipts[url]["sha256"]
            ).read_bytes()
            matched = matched_columns(c, columns(content))
            updates = common_facts(matched)
            if not updates:
                continue
            ref = reference(
                c,
                url,
                "factory-kia-us",
                "US specifications table; common cells across matched trims: "
                + ", ".join(col["trim"] for col in matched),
            )
            for key, data in updates.items():
                value["facts"][key] = {
                    "value": data,
                    "locator": ref["locator"],
                    "documentary_source": ref,
                }
            value["revision_note"] = (
                "Reviewed factory table: only invariant engine/transmission descriptions across matching displacement/aspiration candidates. No exact trim, generation, drivetrain or mechanical construction inferred."
            )
            decisions.append(
                {
                    "make": c["make"],
                    "model": c["model"],
                    "year": c["model_year"],
                    "external_key": c["external_key"],
                    "decision": "FACTORY_FACTS_PARTIAL",
                    "fields": updates,
                    "candidate_trims": [col["trim"] for col in matched],
                    "gaps": [
                        "generation",
                        "exact_trim_applicability",
                        "factory_drivetrain",
                        "maintenance",
                    ],
                }
            )
            revised.append(value)
    db.commit()
    manifest = ImportManifest(
        source_id="epa",
        parser="manifest-json-v1",
        records=revised,
        selection_basis="Frozen existing 51-family US verification cohort; reviewed documentary corrections only, no new families or versions",
    )
    MANIFEST.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    (OUT / "factory-review-decisions.json").write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
