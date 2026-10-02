"""Execute a reviewed basic-catalog manifest through the existing import/review pipeline.

No provider requests and no model-specific application logic. EPA rows are matched as
complete configurations; native factory rows are explicit combinations, never products
of independent engine/transmission lists. Re-runs reuse immutable prepared revisions.
"""
# ruff: noqa: E402, E501

import argparse
import copy
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

from catalog_writer_lock import catalog_writer_lock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.models.knowledge_ops import RawDocument, SourceRegistry
from app.models.user import User
from app.schemas.knowledge import CatalogRecord, FactInput, ImportManifest
from app.services.catalog_verification import (
    IDENTITY_FIELDS,
    base_catalog_ready,
    fingerprint,
    reference_years,
)
from app.services.knowledge_import import (
    document_text,
    enqueue,
    epa_record,
    private_path,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from app.services.market_priority import base_catalog_batch, policy
from sqlalchemy import select


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def matches(row, family, group):
    if row["make"] != family["make"] or (row.get("baseModel") or row["model"]) != family["model"]:
        return False
    if not group["year_from"] <= int(row["year"]) <= group["year_to"]:
        return False
    return all(
        str(row.get(k)) in [str(x) for x in values] for k, values in group["epa_match"].items()
    )


def public_record(c):
    value = {k: copy.deepcopy(v) for k, v in c.items() if k in CatalogRecord.model_fields}
    value["facts"] = {
        k: {a: copy.deepcopy(b) for a, b in f.items() if a in FactInput.model_fields}
        for k, f in c["facts"].items()
    }
    return value


def preflight_reviewed_record(value):
    """Catch readiness and year-scoped evidence gaps before any baseline is published."""
    record = CatalogRecord.model_validate(value)
    verification = record.identity_verification
    if not verification:
        raise ValueError("IDENTITY_EVIDENCE_INCOMPLETE:" + value["external_key"])
    required_years = (
        set(range(verification.range_scope.model_year_from, verification.range_scope.model_year_to + 1))
        if verification.range_scope
        else {record.model_year}
    )
    if record.model_year not in required_years:
        raise ValueError("RECORD_OUTSIDE_IDENTITY_RANGE:" + value["external_key"])
    for field in IDENTITY_FIELDS:
        covered = set()
        for ref in verification.field_evidence.get(field, []):
            overlap = reference_years(ref) & required_years
            if not overlap:
                raise ValueError("IDENTITY_REFERENCE_OUTSIDE_RANGE:" + value["external_key"] + ":" + field)
            covered |= overlap
        if covered != required_years:
            raise ValueError("IDENTITY_RANGE_EVIDENCE_GAP:" + value["external_key"] + ":" + field)
    candidate = copy.deepcopy(value)
    candidate["verification_gate"] = {
        "state": "VERIFIED_SCOPED",
        "fingerprint": fingerprint(candidate),
    }
    if not base_catalog_ready(candidate):
        raise ValueError("BASE_READY_FIELDS_INCOMPLETE:" + value["external_key"])


def epa_drive_references(document, rows, family, group):
    """Use reviewed EPA tuples only for drive; gearbox construction stays factory-sourced."""
    query = group.get("epa_drive_match")
    if query is None:
        return {}
    if not {"model", "displ", "trany"} <= query.keys():
        raise ValueError("EPA_DRIVE_COMPLETE_TUPLE_REQUIRED")
    found = defaultdict(list)
    for row in rows:
        if (
            row["make"] != family["make"]
            or not group["year_from"] <= int(row["year"]) <= group["year_to"]
        ):
            continue
        if not all(str(row.get(k)) in [str(x) for x in values] for k, values in query.items()):
            continue
        drive = epa_record(row).facts["drivetrain"].value
        drive = group.get("drive_normalization", {}).get(drive, drive)
        if drive in group["allowed_drives"]:
            found[(int(row["year"]), drive)].append(row["id"])
    expected = {
        (y, d)
        for y in range(group["year_from"], group["year_to"] + 1)
        for d in group["allowed_drives"]
    }
    if set(found) != expected:
        raise ValueError("EPA_DRIVE_APPLICABILITY_GAP:" + group["id"])
    return {
        (year, drive): dict(
            registry_id=document.source_id,
            document_id=document.id,
            sha256=document.sha256,
            url=document.locator,
            make=family["make"],
            model=family["model"],
            market=family["market"],
            model_year=year,
            locator="EPA vehicles.csv exact reviewed tuple IDs "
            + ",".join(sorted(ids))
            + "; drive="
            + drive
            + ". Drive evidence only; body and gearbox construction from annual factory documents.",
        )
        for (year, drive), ids in found.items()
    }


def prepare(db, manifest):
    receipts = {}
    for name in ("acquisition-ledger.json", "base-catalog-acquisition.json"):
        for r in json.loads(
            (ROOT / "deliverables/VerifiedData" / name).read_text(encoding="utf-8")
        ):
            if r.get("http_status") == 200 and r.get("sha256") and not r.get("error"):
                receipts[r["url"]] = r
    registered = {}
    for key, spec in manifest["documents"].items():
        sid = spec["source_id"]
        if db.get(SourceRegistry, sid) is None:
            db.add(
                SourceRegistry(
                    id=sid,
                    title=spec["publisher"],
                    state="LOCAL_RESEARCH",
                    config={
                        "owner": spec["publisher"],
                        "markets": [spec["market"]],
                        "cost_model": "FREE",
                        "commercial_reuse": False,
                        "factory_identity_evidence": True,
                        "data_types": ["factory_specification"],
                        "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
                        "display_rights": "LOCAL_RESEARCH_ONLY",
                        "rights": "COMMERCIAL_REUSE_NOT_ESTABLISHED",
                        "checked_at": "2026-09-20",
                    },
                )
            )
            db.flush()
        receipt = receipts[spec["url"]]
        content = (ROOT / ".localdata/verified-source-documents" / receipt["sha256"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != receipt["sha256"]:
            raise ValueError("ACQUISITION_HASH_MISMATCH")
        if spec.get("format") == "pdf" and not content.startswith(b"%PDF-"):
            raise ValueError("NOT_A_FACTORY_PDF")
        doc = store_document(
            db, sid, content, locator=spec["url"], media_type=receipt["media_type"]
        )
        if doc.locator != spec["url"]:
            raise ValueError("DUPLICATE_DOCUMENT_DIFFERENT_LOCATOR")
        registered[key] = doc
    epa_doc = db.get(RawDocument, manifest["epa_document_id"])
    epa = list(
        csv.DictReader(document_text(private_path(epa_doc.storage_key).read_bytes()).splitlines())
    )
    current = {
        v.catalog_key: v
        for v in db.scalars(select(VehicleVariant).where(VehicleVariant.catalog_key.is_not(None)))
    }
    targets, occupied = [], set()

    def reference(key, family, locator=None):
        spec, doc = manifest["documents"][key], registered[key]
        return dict(
            registry_id=spec["source_id"],
            document_id=doc.id,
            sha256=doc.sha256,
            url=spec["url"],
            locator=locator or spec["locator"],
            make=family["make"],
            model=family["model"],
            market=family["market"],
            model_year_from=spec["year_from"],
            model_year_to=spec["year_to"],
        )

    for family in base_catalog_batch(manifest=manifest)["families"]:
        for group in family["groups"]:
            records = []
            if group.get("epa_match"):
                for row in epa:
                    if matches(row, family, group) and row["id"] not in family.get(
                        "excluded_epa_ids", []
                    ):
                        records.append(("epa", epa_record(row).model_dump(mode="json")))
            else:
                for year in range(group["year_from"], group["year_to"] + 1):
                    for combination in group["factory_combinations"]:
                        sid = manifest["documents"][family["annual_documents"][str(year)][0]][
                            "source_id"
                        ]
                        value = dict(
                            external_key=f"{family['id']}-{group['id']}-{combination['drivetrain']}-{year}",
                            make=family["make"],
                            model=family["model"],
                            model_year=year,
                            original_market=family["market"],
                            configuration=group["configuration"]
                            + " · "
                            + combination["drivetrain"],
                            source_url=manifest["documents"][
                                family["annual_documents"][str(year)][0]
                            ]["url"],
                            facts={
                                "drivetrain": {
                                    "value": combination["drivetrain"],
                                    "locator": group["locator"][:500],
                                }
                            },
                        )
                        records.append((sid, value))
            if not records:
                raise ValueError("EMPTY_REVIEWED_GROUP:" + group["id"])
            actual_years = {r["model_year"] for _, r in records}
            if actual_years != set(range(group["year_from"], group["year_to"] + 1)):
                raise ValueError("CONFIGURATION_YEAR_GAP:" + group["id"])
            all_refs = [
                reference(
                    key, family, group["locator"] + "; " + manifest["documents"][key]["locator"]
                )
                for year in range(group["year_from"], group["year_to"] + 1)
                for key in family["annual_documents"][str(year)]
            ]
            generation_refs = [
                reference(key, family) for key in family.get("generation_documents", [])
            ] or all_refs
            drive_refs = epa_drive_references(epa_doc, epa, family, group)
            for sid, base in records:
                key = sid + ":" + base["external_key"]
                if key in occupied:
                    raise ValueError("OVERLAPPING_CONFIGURATION_GROUP:" + key)
                occupied.add(key)
                existing = current.get(key)
                value = (
                    public_record(existing.specifications["catalog"])
                    if existing and existing.published_revision_id
                    else copy.deepcopy(base)
                )
                year = value["model_year"]
                ref = reference(
                    family["annual_documents"][str(year)][0],
                    family,
                    group["locator"]
                    + "; "
                    + manifest["documents"][family["annual_documents"][str(year)][0]]["locator"],
                )
                value.update(
                    generation=family["generation"], generation_code=family["generation_code"]
                )
                if family.get("facelift_from"):
                    value["facelift"] = (
                        "FACELIFT" if year >= family["facelift_from"] else "PRE_FACELIFT"
                    )
                changes = {
                    **family.get("facts", {}),
                    **group["facts"],
                    **group.get("annual_facts", {}).get(str(year), {}),
                }
                # The selected complete EPA row supplies drive choice; factory matrix proves its applicability.
                drive = value["facts"]["drivetrain"]["value"]
                drive = group.get("drive_normalization", {}).get(drive, drive)
                if drive not in group["allowed_drives"]:
                    raise ValueError("DRIVE_OUTSIDE_FACTORY_MATRIX:" + key)
                changes["drivetrain"] = drive
                for name, fact in changes.items():
                    fact = {"value": fact} if not isinstance(fact, dict) else copy.deepcopy(fact)
                    document_key = fact.pop("document_key", None)
                    fact_ref = reference(document_key, family) if document_key else ref
                    if name == "drivetrain" and drive_refs:
                        fact_ref = drive_refs[(year, drive)]
                    fact.update(
                        status="CONFIRMED",
                        locator=fact_ref["locator"][:500],
                        documentary_source=fact_ref,
                    )
                    value["facts"][name] = fact
                # Stale labels and claims cannot silently survive replacement of aggregates.
                value["revision_note"] = (
                    "Reviewed basic catalogue scope: "
                    + family["id"]
                    + "/"
                    + group["id"]
                    + ". Preserve source revisions. Images, costs and expert dossiers are not readiness gates."
                )
                verification = dict(
                    previous_revision_id=existing.published_revision_id
                    if existing
                    else "BASELINE_REQUIRED",
                    applicability=family["scope_note"] + " " + group["configuration"],
                    field_evidence={
                        field: generation_refs
                        if field == "generation"
                        else list(drive_refs.values())
                        if field == "drivetrain" and drive_refs
                        else all_refs
                        for field in IDENTITY_FIELDS
                    },
                    review_note=group.get(
                        "review_note",
                        "Reviewed annual manufacturer tables and actual source configurations; no engine/transmission Cartesian product or unsupported year extrapolation.",
                    ),
                )
                if group["year_to"] > group["year_from"]:
                    verification["range_scope"] = dict(
                        family_scope_id=family["id"],
                        configuration_group=group["configuration"],
                        model_year_from=group["year_from"],
                        model_year_to=group["year_to"],
                        exclusions=family["exclude"],
                    )
                value["identity_verification"] = verification
                preflight_reviewed_record(value)
                targets.append(
                    dict(
                        catalog_key=key,
                        source_id=sid,
                        family_id=family["id"],
                        group_id=group["id"],
                        existing_revision_id=existing.published_revision_id if existing else None,
                        baseline=base,
                        reviewed=value,
                    )
                )
    for exclusion in manifest.get("exclusions", []):
        key = exclusion.get("catalog_key") or "epa:" + exclusion["epa_id"]
        existing = current.get(key)
        if not existing or not existing.published_revision_id:
            continue
        value = public_record(existing.specifications["catalog"])
        family = next(f for f in manifest["families"] if f["id"] == exclusion["family_id"])
        if any(
            value[k] != family[f]
            for k, f in (("make", "make"), ("model", "model"), ("original_market", "market"))
        ):
            raise ValueError("EXCLUSION_OUTSIDE_FAMILY:" + key)
        ref = reference(exclusion["document"], family, exclusion["reason"])
        value["identity_verification"] = None
        value["facts"]["catalog_applicability"] = dict(
            value="EXCLUDED",
            status="CONFIRMED",
            locator=exclusion["reason"],
            documentary_source=ref,
        )
        value["revision_note"] = exclusion["reason"]
        targets.append(
            dict(
                catalog_key=key,
                source_id=key.split(":", 1)[0],
                family_id=family["id"],
                group_id="EXCLUDED",
                existing_revision_id=existing.published_revision_id,
                baseline=None,
                reviewed=value,
            )
        )
    db.commit()
    return targets


def execute(db, actor, source_id, records, phase, out):
    # Full references stay in reviewed records. FactInput's display locator has
    # the same 500-character bound for old prepared baselines and new baselines.
    if phase == "baseline":
        records = copy.deepcopy(records)
        for record in records:
            for fact in record["facts"].values():
                fact["locator"] = fact["locator"][:500]
    path = out / f"{phase}-{source_id}.json"
    if path.exists():
        value = ImportManifest.model_validate_json(path.read_text(encoding="utf-8"))
    else:
        value = ImportManifest(
            source_id=source_id,
            parser="manifest-json-v1",
            records=records,
            selection_basis="Owner-priority Azerbaijan basic catalogue; reviewed explicit factory combination manifest; "
            + phase,
        )
        dump(path, value.model_dump(mode="json"))
    job = enqueue(db, value)
    if job.state != "PUBLISHED":
        while job.state in {"QUEUED", "RUNNING"}:
            process_job(db, job.id, batch_size=25)
        if job.state == "STAGED":
            review_job(
                db,
                job,
                actor,
                note="Reviewed complete factory combinations, annual applicability and immutable source documents; basic catalogue only",
                approve=True,
            )
        publish_job(
            db,
            job,
            actor,
            note="Publish local basic catalogue batch; preserve prior revisions and future product workstreams",
        )
    return {
        "source_id": source_id,
        "phase": phase,
        "state": job.state,
        "job_id": job.id,
        "records": len(value.records),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", default=policy()["active_catalog_manifest"])
    p.add_argument("--publish-reviewed", action="store_true")
    args = p.parse_args()
    path = ROOT / args.manifest
    payload = path.read_bytes()
    manifest = json.loads(payload)
    out = ROOT / "deliverables/VerifiedData" / manifest["batch_id"]
    prepared = out / "prepared.json"
    with catalog_writer_lock(), SessionLocal() as db:
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if not actor:
            raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
        digest = hashlib.sha256(payload).hexdigest()
        if prepared.exists():
            data = json.loads(prepared.read_text(encoding="utf-8"))
            if data["manifest_sha256"] != digest:
                raise ValueError("PREPARED_MANIFEST_CHANGED_USE_NEW_BATCH_ID")
            targets = data["targets"]
        else:
            targets = prepare(db, manifest)
            dump(prepared, {"manifest_sha256": digest, "targets": targets})
        if not args.publish_reviewed:
            print(json.dumps({"state": "PREPARED", "records": len(targets)}))
            return
        results = []
        baseline = defaultdict(list)
        for t in targets:
            if not t["existing_revision_id"]:
                baseline[t["source_id"]].append(t["baseline"])
        for sid, rows in baseline.items():
            results.append(execute(db, actor, sid, rows, "baseline", out))
        current = {
            v.catalog_key: v
            for v in db.scalars(
                select(VehicleVariant).where(VehicleVariant.catalog_key.is_not(None))
            )
        }
        groups = defaultdict(list)
        for t in targets:
            value = t["reviewed"]
            if not t["existing_revision_id"]:
                value["identity_verification"]["previous_revision_id"] = current[
                    t["catalog_key"]
                ].published_revision_id
            groups[t["source_id"]].append(value)
        for sid, rows in groups.items():
            results.append(execute(db, actor, sid, rows, "reviewed", out))
        dump(
            out / "publication.json",
            {"state": "PUBLISHED", "manifest_sha256": digest, "jobs": results, "paid_calls": 0},
        )
        print(json.dumps({"state": "PUBLISHED", "records": len(targets), "jobs": results}))


if __name__ == "__main__":
    main()
