"""Reviewed market discovery on the existing ImportJob pipeline; no network collector."""

import csv
import io
import json
from urllib.parse import urlsplit

from sqlalchemy import select

from app.core.config import get_settings
from app.models.knowledge_ops import MarketDiscoveryRevision
from app.schemas.market_discovery import MarketDiscoveryRecord
from app.services.knowledge_registry import require_source, utcnow


def require_permission(source):
    p = source.config.get("market_discovery_permission", {})
    if (
        not p.get("reference")
        or not p.get("local_storage")
        or p.get("method") not in {"PERMITTED_EXPORT", "WRITTEN_AUTOMATION_PERMISSION"}
    ):
        raise ValueError("MARKET_DISCOVERY_PERMISSION_REQUIRED")


def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    if set(reader.fieldnames or []) != set(MarketDiscoveryRecord.model_fields):
        raise ValueError("MARKET_CSV_SCHEMA_DRIFT")
    result = []
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("MARKET_CSV_ROW_SHAPE")
        for key in ("listings", "market_counts", "limitations"):
            row[key] = json.loads(row[key])
        row["listing_count"] = int(row["listing_count"]) if row["listing_count"] else None
        result.append(MarketDiscoveryRecord.model_validate(row).model_dump(mode="json"))
        if len(result) > get_settings().knowledge_import_max_records:
            raise ValueError("MARKET_RECORD_BUDGET")
    return result


def validate_records(rows, source):
    require_permission(source)
    if not isinstance(rows, list) or len(rows) > get_settings().knowledge_import_max_records:
        raise ValueError("MARKET_RECORD_BUDGET")
    hosts = set(source.config.get("allowed_observation_hosts", []))
    seen, keys, models, result = {}, {}, {}, []
    for data in rows:
        record = MarketDiscoveryRecord.model_validate(data)
        payload = record.model_dump(mode="json")
        if record.external_key in keys:
            if keys[record.external_key] != payload:
                raise ValueError("DUPLICATE_MODEL_OBSERVATION_CONFLICT")
            continue
        model_key = (record.make.casefold(), record.model.casefold())
        if model_key in models:
            raise ValueError("ONE_MODEL_SNAPSHOT_PER_BATCH")
        models[model_key] = record.external_key
        keys[record.external_key] = payload
        urls = [
            record.source_url,
            *[r.source_url for r in record.listings],
            *[r.source_url for r in record.market_counts],
        ]
        if not hosts or any(urlsplit(u).hostname not in hosts for u in urls):
            raise ValueError("MARKET_SOURCE_HOST_MISMATCH")
        for listing in record.listings:
            if listing.listing_id in seen:
                raise ValueError("LISTING_ASSIGNED_TO_MULTIPLE_MODELS")
            seen[listing.listing_id] = model_key
        result.append(payload)
    return result


def stage_batch(db, job, doc, batch_size):
    from app.services.knowledge_import import checksum, document_text, private_path

    source = require_source(db, job.source_id)
    rows = job.manifest.get("market_records") or []
    if not rows:
        if doc is None:
            raise ValueError("DOCUMENT_REQUIRED")
        content = private_path(doc.storage_key).read_bytes()
        if checksum(content) != doc.sha256:
            raise ValueError("RAW_DOCUMENT_CHANGED")
        text = document_text(content)
        rows = parse_csv(text) if job.manifest["parser"].endswith("csv-v1") else json.loads(text)
    # Validate the complete batch before writing; a repeated listing cannot inflate another model.
    rows = validate_records(rows, source)
    end = min(job.cursor + batch_size, len(rows))
    for payload in rows[job.cursor : end]:
        old = db.scalar(
            select(MarketDiscoveryRevision).where(
                MarketDiscoveryRevision.import_job_id == job.id,
                MarketDiscoveryRevision.external_key == payload["external_key"],
            )
        )
        if old:
            if old.checksum != checksum(payload):
                raise ValueError("MARKET_STAGING_CHANGED")
            continue
        db.add(
            MarketDiscoveryRevision(
                import_job_id=job.id,
                source_id=source.id,
                external_key=payload["external_key"],
                payload=payload,
                checksum=checksum(payload),
            )
        )
    job.cursor = end
    job.metrics = {
        **job.metrics,
        "total": len(rows),
        "processed": end,
        "quarantined": 0,
        "parser_version": "market-discovery-v1",
        "publication": "DISCOVERY_ONLY",
    }
    job.state = (
        ("DRY_RUN" if job.manifest["dry_run"] else "STAGED") if end == len(rows) else "QUEUED"
    )
    job.lease_until = None
    db.commit()
    return job


def publish_revisions(db, revisions, source):
    from app.services.knowledge_import import checksum

    validate_records([r.payload for r in revisions], source)
    for revision in revisions:
        if revision.state != "APPROVED" or checksum(revision.payload) != revision.checksum:
            raise ValueError("REVIEW_REQUIRED")
        key = source.id + ":" + revision.external_key
        old = db.scalar(
            select(MarketDiscoveryRevision).where(MarketDiscoveryRevision.active_key == key)
        )
        if old:
            if revision.payload["observed_at"] <= old.payload["observed_at"]:
                raise ValueError("NEWER_MARKET_SNAPSHOT_REQUIRED")
            old.state, old.active_key = "SUPERSEDED", None
            revision.previous_revision_id = old.id
            db.flush()
        revision.active_key, revision.state, revision.published_at = key, "PUBLISHED", utcnow()


def published(db):
    rows = []
    for row in db.scalars(
        select(MarketDiscoveryRevision).where(
            MarketDiscoveryRevision.state == "PUBLISHED",
            MarketDiscoveryRevision.active_key.is_not(None),
        )
    ):
        try:
            source = require_source(db, row.source_id)
            require_permission(source)
        except ValueError:
            continue
        rows.append(
            {
                "revision_id": row.id,
                "source_id": row.source_id,
                "checksum": row.checksum,
                **row.payload,
            }
        )
    return rows
