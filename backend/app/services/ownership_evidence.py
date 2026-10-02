"""Ownership records participate in existing ImportJob review and atomic publication."""

from __future__ import annotations

import csv
import io
import json
from datetime import date

from sqlalchemy import select

from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.models.knowledge_ops import OwnershipEvidenceRevision, SourceRegistry
from app.schemas.verified_ownership import OwnershipRecord
from app.services.knowledge_registry import utcnow


def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    required = set(OwnershipRecord.model_fields)
    if set(reader.fieldnames or []) != required:
        raise ValueError("OWNERSHIP_CSV_SCHEMA_DRIFT")
    records = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("OWNERSHIP_CSV_ROW_SHAPE")
        for key in ("variant_ids", "limitations", "data"):
            row[key] = json.loads(row[key])
        row["effective_to"] = row["effective_to"] or None
        records.append(OwnershipRecord.model_validate(row).model_dump(mode="json"))
        if len(records) > get_settings().knowledge_import_max_records:
            raise ValueError("OWNERSHIP_RECORD_BUDGET")
    return records


def stage_batch(db, job, doc, batch_size):
    from app.services.knowledge_import import checksum, document_text, private_path

    rows = job.manifest.get("ownership_records") or []
    if not rows:
        if doc is None:
            raise ValueError("DOCUMENT_REQUIRED")
        content = private_path(doc.storage_key).read_bytes()
        if checksum(content) != doc.sha256:
            raise ValueError("RAW_DOCUMENT_CHANGED")
        text = document_text(content)
        rows = parse_csv(text) if job.manifest["parser"] == "ownership-csv-v1" else json.loads(text)
    if not isinstance(rows, list) or len(rows) > get_settings().knowledge_import_max_records:
        raise ValueError("OWNERSHIP_RECORD_BUDGET")
    end = min(job.cursor + batch_size, len(rows))
    errors = list(job.errors)
    for i in range(job.cursor, end):
        try:
            record = OwnershipRecord.model_validate(rows[i])
            if record.observed_at > utcnow():
                raise ValueError("FUTURE_OBSERVATION")
            payload = record.model_dump(mode="json")
            current = db.scalar(
                select(OwnershipEvidenceRevision).where(
                    OwnershipEvidenceRevision.import_job_id == job.id,
                    OwnershipEvidenceRevision.external_key == record.external_key,
                )
            )
            if current:
                if current.checksum != checksum(payload):
                    raise ValueError("DUPLICATE_EXTERNAL_KEY_CONFLICT")
                continue
            db.add(
                OwnershipEvidenceRevision(
                    import_job_id=job.id,
                    source_id=job.source_id,
                    external_key=record.external_key,
                    kind=record.kind,
                    payload=payload,
                    checksum=checksum(payload),
                    state="STAGING",
                )
            )
            db.flush()
        except (ValueError, TypeError):
            errors.append({"record": i, "code": "OWNERSHIP_SCHEMA_QUARANTINE"})
    job.cursor = end
    job.errors = errors[-1000:]
    job.metrics = {
        "total": len(rows),
        "processed": end,
        "quarantined": len(errors),
        "parser_version": "ownership-v1",
        "publication": "STAGING",
    }
    job.state = (
        ("DRY_RUN" if job.manifest["dry_run"] else "STAGED") if end == len(rows) else "QUEUED"
    )
    job.lease_until = None
    db.commit()
    return job


def publish_revisions(db, revisions, source):
    from app.services.knowledge_import import catalog_identity_hash, checksum

    for revision in revisions:
        value = OwnershipRecord.model_validate(revision.payload)
        if revision.state != "APPROVED" or checksum(revision.payload) != revision.checksum:
            raise ValueError("REVIEW_REQUIRED")
        key = source.id + ":" + value.external_key
        previous = db.scalar(
            select(OwnershipEvidenceRevision).where(OwnershipEvidenceRevision.active_key == key)
        )
        if previous:
            if previous.editorial_locked:
                raise ValueError("EDITORIAL_OVERRIDE_PROTECTED")
            previous.active_key = None
            previous.state = "SUPERSEDED"
            revision.previous_revision_id = previous.id
            db.flush()
        hashes = {}
        for vid in value.variant_ids:
            variant = db.get(VehicleVariant, vid)
            if not variant or not variant.published_revision_id or variant.is_demo:
                raise ValueError("PUBLISHED_VARIANT_REQUIRED")
            hashes[vid] = catalog_identity_hash(variant.specifications["catalog"])
        revision.identity_hashes = hashes
        revision.publication_scope = (
            "COMMERCIAL" if source.config.get("commercial_reuse") else "LOCAL_RESEARCH"
        )
        revision.active_key = key
        revision.state = "PUBLISHED"
        revision.published_at = utcnow()


def available(
    db, *, kind=None, variant_id=None, on_date: date | None = None, production_safe=False
):
    from app.services.knowledge_import import catalog_identity_hash

    sources = {s.id: s for s in db.scalars(select(SourceRegistry))}
    query = select(OwnershipEvidenceRevision).where(
        OwnershipEvidenceRevision.active_key.is_not(None),
        OwnershipEvidenceRevision.state == "PUBLISHED",
    )
    if kind:
        query = query.where(OwnershipEvidenceRevision.kind == kind)
    variant = db.get(VehicleVariant, variant_id) if variant_id else None
    result = []
    for row in db.scalars(query):
        source = sources.get(row.source_id)
        if not source or source.paused or source.state not in {"APPROVED", "LOCAL_RESEARCH"}:
            continue
        if (get_settings().environment == "production" or production_safe) and (
            not source.config.get("commercial_reuse") or row.publication_scope != "COMMERCIAL"
        ):
            continue
        p = row.payload
        if on_date and (
            p["effective_from"] > on_date.isoformat()
            or (p.get("effective_to") and p["effective_to"] < on_date.isoformat())
        ):
            continue
        if variant_id and p["variant_ids"]:
            if not variant or variant_id not in row.identity_hashes:
                continue
            if row.identity_hashes[variant_id] != catalog_identity_hash(
                variant.specifications["catalog"]
            ):
                continue
        result.append(row)
    return result


def view(row):
    return {
        "id": row.id,
        "kind": row.kind,
        "checksum": row.checksum,
        "source_id": row.source_id,
        "scope": row.publication_scope,
        **row.payload,
    }
