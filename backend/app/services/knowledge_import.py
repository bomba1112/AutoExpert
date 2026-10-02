"""Bounded raw -> validated staging -> reviewed atomic publication pipeline."""

# ruff: noqa: E501
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import ssl
import unicodedata
import zipfile
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import httpx
from sqlalchemy import or_, select, update

from app.core.config import get_settings
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceCategory,
    EvidenceStatus,
    SourceTier,
)
from app.models.evidence import MarketListing, SourceRecord, TechnicalEvidence
from app.models.knowledge_ops import (
    CatalogRevision,
    EditorialReview,
    ImportJob,
    MarketDiscoveryRevision,
    OwnershipEvidenceRevision,
    RawDocument,
    VehicleAsset,
)
from app.schemas.knowledge import CatalogRecord, ImportManifest
from app.services.knowledge_registry import require_source, utcnow

PARSER_VERSION = "catalog-normalizer-1.4"


def normalized(value):
    value = unicodedata.normalize(
        "NFKD", value.replace("ı", "i").replace("İ", "i").replace("ə", "e").replace("Ə", "e")
    ).casefold()
    return " ".join(
        re.sub(r"[^\w]+", " ", "".join(c for c in value if not unicodedata.combining(c))).split()
    )


def checksum(value):
    raw = (
        value
        if isinstance(value, bytes)
        else json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    )
    return hashlib.sha256(raw).hexdigest()


def catalog_identity_hash(c):
    return checksum(
        {
            "identity": {
                k: c.get(k)
                for k in (
                    "make",
                    "model",
                    "model_year",
                    "original_market",
                    "generation",
                    "facelift",
                    "production_from",
                    "production_to",
                )
                if k not in {"production_from", "production_to"} or c.get(k) is not None
            },
            "facts": {
                k: {
                    "value": c.get("facts", {}).get(k, {}).get("value"),
                    "status": c.get("facts", {}).get(k, {}).get("status"),
                }
                for k in (
                    "engine_displacement",
                    "engine_code",
                    "engine_family",
                    "transmission_code",
                    "powertrain",
                    "transmission_family",
                    "drivetrain",
                    "trim",
                    "body",
                )
                if k not in {"engine_code", "engine_family", "transmission_code"}
                or c.get("facts", {}).get(k, {}).get("value") is not None
            },
        }
    )


def private_path(key):
    root = Path(get_settings().knowledge_data_dir).resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError("UNSAFE_STORAGE_PATH")
    return path


def store_document(
    db, source_id, content, *, locator="manual-upload", media_type="application/json"
):
    require_source(db, source_id)
    if len(content) > get_settings().knowledge_import_max_bytes:
        raise ValueError("DOCUMENT_TOO_LARGE")
    digest = checksum(content)
    existing = db.scalar(
        select(RawDocument).where(RawDocument.source_id == source_id, RawDocument.sha256 == digest)
    )
    if existing:
        return existing
    key = f"raw/{digest}"
    path = private_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    doc = RawDocument(
        source_id=source_id,
        sha256=digest,
        storage_key=key,
        byte_size=len(content),
        media_type=media_type,
        locator=locator,
    )
    db.add(doc)
    db.flush()
    return doc


def enqueue(db, manifest: ImportManifest):
    source = require_source(db, manifest.source_id, acquire=bool(manifest.download_url))
    if manifest.parser.startswith("market-discovery-"):
        from app.services.market_discovery import require_permission

        require_permission(source)
    if manifest.year_min > manifest.year_max:
        raise ValueError("YEAR_RANGE")
    if manifest.download_url and manifest.download_url not in source.config.get(
        "allowed_download_urls", []
    ):
        raise ValueError("DOWNLOAD_URL_NOT_ALLOWLISTED")
    if manifest.document_id:
        doc = db.get(RawDocument, manifest.document_id)
        if not doc or doc.source_id != source.id:
            raise ValueError("DOCUMENT_SOURCE_MISMATCH")
    payload = manifest.model_dump(mode="json")

    def compatible(value):
        if isinstance(value, list):
            return [compatible(v) for v in value]
        if isinstance(value, dict):
            return {
                k: compatible(v)
                for k, v in value.items()
                if v
                or k
                not in {
                    "market_records",
                    "documentary_source",
                    "identity_verification",
                    "documentary_sections",
                    "range_scope",
                    "model_year_from",
                    "model_year_to",
                }
            }
        return value

    key_payload = compatible(payload)
    key = checksum({"manifest": key_payload, "parser_version": PARSER_VERSION})
    existing = db.scalar(select(ImportJob).where(ImportJob.request_key == key))
    if existing:
        return existing
    job = ImportJob(
        request_key=key, source_id=source.id, raw_document_id=manifest.document_id, manifest=payload
    )
    db.add(job)
    db.commit()
    return job


def download_document(db, job):
    source = require_source(db, job.source_id, acquire=True)
    url = job.manifest.get("download_url")
    if url not in source.config.get("allowed_download_urls", []):
        raise ValueError("DOWNLOAD_URL_NOT_ALLOWLISTED")
    # No redirects: a reviewed public URL cannot pivot to an internal host.
    job.metrics = {**job.metrics, "network_attempts": job.metrics.get("network_attempts", 0) + 1}
    db.commit()
    with (
        httpx.Client(
            timeout=60, follow_redirects=False, verify=ssl.create_default_context()
        ) as client,
        client.stream(
            "GET", url, headers={"User-Agent": "AutoExpert-local-research/0.8"}
        ) as response,
    ):
        if response.status_code in {429, 503}:
            try:
                seconds = max(60, min(86400, int(response.headers.get("Retry-After", "60"))))
            except ValueError:
                seconds = 60
            source.config = {
                **source.config,
                "backoff_until": (utcnow() + timedelta(seconds=seconds)).isoformat(),
            }
            db.commit()
            raise ValueError("SOURCE_BACKOFF_REQUIRED")
        response.raise_for_status()
        content = bytearray()
        for block in response.iter_bytes():
            content.extend(block)
            if len(content) > get_settings().knowledge_import_max_bytes:
                raise ValueError("DOCUMENT_TOO_LARGE")
    expected = job.manifest.get("expected_sha256")
    if expected and checksum(bytes(content)) != expected:
        raise ValueError("CHECKSUM_MISMATCH")
    doc = store_document(
        db,
        job.source_id,
        bytes(content),
        locator=url,
        media_type="application/zip" if content[:2] == b"PK" else "text/csv",
    )
    job.raw_document_id = doc.id
    source.config = {
        **source.config,
        "last_acquired_at": utcnow().isoformat(),
        "backoff_until": None,
    }
    job.metrics = {
        **job.metrics,
        "network_calls": job.metrics.get("network_calls", 0) + 1,
        "raw_sha256": doc.sha256,
    }
    db.commit()
    return doc


def document_text(content):
    if content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) != 1 or not entries[0].filename.lower().endswith(".csv"):
                raise ValueError("ARCHIVE_SINGLE_CSV_REQUIRED")
            entry = entries[0]
            if (
                entry.file_size > 80 * 1024 * 1024
                or entry.file_size / max(entry.compress_size, 1) > 200
            ):
                raise ValueError("ARCHIVE_EXPANSION_LIMIT")
            content = archive.read(entry)  # Never extract archive paths onto disk.
    return content.decode("utf-8-sig")


def epa_record(row):
    rid = row["id"]
    facts = {}

    def add(key, value, locator, unit=None):
        if value is not None and value != "":
            facts[key] = {"value": value, "locator": f"EPA vehicle {rid}: {locator}", "unit": unit}

    fuel = row.get("fuelType1", "")
    atv = row.get("atvType", row.get("atvtype", "")).casefold()
    powertrain = (
        "FCEV"
        if atv in {"fcv", "efcv"}
        else "MHEV"
        if atv == "mild hybrid"
        else "EREV"
        if atv == "range extended ev"
        else "BEV"
        if atv == "ev"
        else "PHEV"
        if "plug-in" in atv
        else "HEV"
        if atv == "hybrid"
        else "ICE"
    )
    add("powertrain", powertrain, "atvType / fuelType1")
    add(
        "fuel",
        "ELECTRICITY"
        if fuel == "Electricity"
        else "GASOLINE"
        if "gasoline" in fuel.casefold()
        else "DIESEL"
        if fuel == "Diesel"
        else fuel,
        "fuelType1",
    )
    add("fuel_grade", fuel, "fuelType1")
    add("engine_displacement", row.get("displ"), "displ", "L")
    add("cylinders", row.get("cylinders"), "cylinders")
    add("engine_description", row.get("eng_dscr"), "eng_dscr")
    if row.get("tCharger") == "T":
        add("aspiration", "TURBO", "tCharger")
    elif row.get("sCharger") == "S":
        add("aspiration", "SUPERCHARGED", "sCharger")
    trans = row.get("trany", "")
    add("transmission_description", trans, "trany")
    # EPA A/AV/AM are not proof of torque converter / belt CVT / dual-clutch construction.
    family = (
        "MANUAL"
        if trans.startswith("Manual")
        else "VARIABLE_UNSPECIFIED"
        if "variable" in trans.casefold() or "(AV" in trans
        else "AMT_UNSPECIFIED"
        if "(AM" in trans
        else "AUTOMATIC_UNSPECIFIED"
        if trans.startswith("Automatic")
        else None
    )
    add("transmission_family", family, "trany; construction not provided")
    gears = re.search(r"(\d+)-spd", trans)
    if gears:
        add("gears", int(gears[1]), "trany")
    drive = row.get("drive")
    add(
        "drivetrain",
        {
            "Front-Wheel Drive": "FWD",
            "Rear-Wheel Drive": "RWD",
            "All-Wheel Drive": "AWD",
            "4-Wheel Drive": "4WD",
            "Part-time 4-Wheel Drive": "PART_TIME_4WD",
        }.get(drive, drive),
        "drive",
    )
    vclass = row.get("VClass", "")
    add("size_class", vclass, "VClass")
    body = next(
        (
            value
            for text, value in [
                ("Station Wagon", "WAGON"),
                ("Minivan", "MINIVAN"),
                ("Pickup", "PICKUP"),
                ("Sport Utility", "SUV"),
                ("Cargo Van", "VAN"),
                ("Passenger Van", "VAN"),
            ]
            if text in vclass
        ),
        None,
    )
    add("body", body, "VClass")
    if (
        fuel in {"Regular Gasoline", "Premium Gasoline", "Midgrade Gasoline", "Diesel"}
        and Decimal(row.get("comb08") or "0") > 0
    ):
        add(
            "fuel_combined",
            str((Decimal("235.214583") / Decimal(row["comb08"])).quantize(Decimal("0.01"))),
            "comb08 converted from US mpg; EPA cycle",
            "L/100km",
        )
    if Decimal(row.get("combE") or "0") > 0:
        add(
            "electricity_combined",
            str((Decimal(row["combE"]) / Decimal("1.609344")).quantize(Decimal("0.01"))),
            "combE converted from kWh/100mi; EPA cycle",
            "kWh/100km",
        )
    add("motor_description", row.get("evMotor"), "evMotor")
    for raw_key, fact_key, unit in [
        ("charge240", "charge_ac_240v_hours", "h"),
        ("range", "epa_range_miles", "mi"),
        ("hlv", "hatch_cargo", "ft3"),
        ("lv4", "four_door_cargo", "ft3"),
        ("lv2", "two_door_cargo", "ft3"),
    ]:
        if Decimal(row.get(raw_key) or "0") > 0:
            add(fact_key, row[raw_key], raw_key, unit)
    return CatalogRecord(
        external_key=rid,
        make=row["make"],
        model=row.get("baseModel") or row.get("basemodel") or row["model"],
        configuration=row["model"]
        + " · "
        + (row.get("displ") or powertrain)
        + " · "
        + trans
        + " · "
        + (drive or ""),
        aliases=[row["model"]],
        original_market="US",
        model_year=int(row["year"]),
        facts=facts,
        source_url=f"https://www.fueleconomy.gov/ws/rest/vehicle/{rid}",
    )


def parse_records(job, doc):
    manifest = ImportManifest.model_validate(job.manifest)
    if manifest.records:
        return [r.model_dump(mode="json") for r in manifest.records]
    if doc is None:
        raise ValueError("DOCUMENT_REQUIRED")
    content = private_path(doc.storage_key).read_bytes()
    if checksum(content) != doc.sha256:
        raise ValueError("RAW_DOCUMENT_CHANGED")
    text = document_text(content)
    if manifest.parser == "nrcan-csv-v1":
        from app.services.nrcan_catalog import parse_nrcan

        return parse_nrcan(text, manifest, doc.locator)
    if manifest.parser == "manifest-json-v1":
        rows = json.loads(text)
        if not isinstance(rows, list):
            raise ValueError("JSON_RECORD_LIST_REQUIRED")
        return rows
    reader = csv.DictReader(io.StringIO(text))
    if manifest.parser == "manifest-csv-v1":
        return [
            {
                **row,
                "facts": json.loads(row["facts"]),
                "aliases": json.loads(row.get("aliases") or "[]"),
            }
            for row in reader
        ]
    if not {"id", "make", "model", "year", "trany", "fuelType1", "comb08"} <= set(
        reader.fieldnames or []
    ):
        raise ValueError("EPA_SCHEMA_CHANGED")
    families = defaultdict(list)
    makes = {normalized(m) for m in manifest.makes}
    for row in reader:
        if not manifest.year_min <= int(row["year"]) <= manifest.year_max or (
            makes and normalized(row["make"]) not in makes
        ):
            continue
        families[
            (
                normalized(row["make"]),
                normalized(row.get("baseModel") or row.get("basemodel") or row["model"]),
            )
        ].append(row)
    # Round-robin makes, then alphabetic families; explicit editorial sampling, not AZ popularity.
    by_make = defaultdict(list)
    for key in sorted(families):
        by_make[key[0]].append(key)
    chosen = []
    for index in range(max((len(v) for v in by_make.values()), default=0)):
        for make in sorted(by_make):
            if index < len(by_make[make]):
                chosen.append(by_make[make][index])
    priority = {normalized(name): index for index, name in enumerate(manifest.priority_families)}
    chosen.sort(key=lambda key: priority.get(normalized(" ".join(key)), len(priority)))
    records = []
    for key in chosen[: manifest.family_limit]:
        rows = sorted(families[key], key=lambda r: (-int(r["year"]), r["id"]))
        for row in rows[: manifest.versions_per_family]:
            records.append(epa_record(row).model_dump(mode="json"))
    return records


def process_job(db, job_id, *, batch_size=100):
    now = utcnow()
    claimed = db.execute(
        update(ImportJob)
        .where(
            ImportJob.id == job_id,
            ImportJob.state.in_(["QUEUED", "RUNNING"]),
            or_(ImportJob.lease_until.is_(None), ImportJob.lease_until < now),
        )
        .values(state="RUNNING", lease_until=now + timedelta(minutes=3))
    )
    db.commit()
    if not claimed.rowcount:
        return db.get(ImportJob, job_id)
    job = db.get(ImportJob, job_id)
    try:
        require_source(db, job.source_id)
        if job.cancel_requested:
            job.state = "CANCELLED"
            job.lease_until = None
            db.commit()
            return job
        doc = db.get(RawDocument, job.raw_document_id) if job.raw_document_id else None
        if doc is None and job.manifest.get("download_url"):
            doc = download_document(db, job)
        if job.manifest.get("parser", "").startswith("ownership-"):
            from app.services.ownership_evidence import stage_batch

            return stage_batch(db, job, doc, batch_size)
        if job.manifest.get("parser", "").startswith("market-discovery-"):
            from app.services.market_discovery import stage_batch

            return stage_batch(db, job, doc, batch_size)
        records = parse_records(job, doc)
        if len(records) > get_settings().knowledge_import_max_records:
            raise ValueError("RECORD_BUDGET_EXCEEDED")
        end = min(len(records), job.cursor + batch_size)
        errors = list(job.errors)
        for index in range(job.cursor, end):
            try:
                record = CatalogRecord.model_validate(records[index])
                payload = record.model_dump(mode="json")
                existing = db.scalar(
                    select(CatalogRevision).where(
                        CatalogRevision.import_job_id == job.id,
                        CatalogRevision.external_key == record.external_key,
                    )
                )
                if existing:
                    if existing.checksum != checksum(payload):
                        raise ValueError("DUPLICATE_EXTERNAL_KEY_CONFLICT")
                    continue
                db.add(
                    CatalogRevision(
                        import_job_id=job.id,
                        external_key=record.external_key,
                        payload=payload,
                        checksum=checksum(payload),
                    )
                )
            except (ValueError, TypeError, KeyError):
                errors.append({"row": index + 1, "code": "INVALID_RECORD_QUARANTINED"})
        job.cursor = end
        job.errors = errors[:1000]
        job.metrics = {
            **job.metrics,
            "total": len(records),
            "processed": end,
            "quarantined": len(errors),
            "parser_version": PARSER_VERSION,
        }
        job.state = (
            ("DRY_RUN" if job.manifest["dry_run"] else "STAGED")
            if end == len(records)
            else "QUEUED"
        )
        job.lease_until = None
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(ImportJob, job_id)
        code = (
            str(exc)
            if isinstance(exc, ValueError) and re.fullmatch(r"[A-Z_]+", str(exc))
            else "IMPORT_FAILED"
        )
        job.errors = [*job.errors, {"code": code}][-1000:]
        job.state = "FAILED"
        job.lease_until = None
        db.commit()
    return job


def audit(db, actor, target_type, target_id, action, note, before=None, after=None):
    db.add(
        EditorialReview(
            actor_id=actor.id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            note=note,
            before=before or {},
            after=after or {},
        )
    )


def revision_model(job):
    parser = job.manifest.get("parser", "")
    if parser.startswith("ownership-"):
        return OwnershipEvidenceRevision
    if parser.startswith("market-discovery-"):
        return MarketDiscoveryRevision
    return CatalogRevision


def review_job(db, job, actor, *, note, approve):
    if job.state != "STAGED" or job.errors:
        raise ValueError("CLEAN_STAGING_REQUIRED")
    require_source(db, job.source_id)
    state = "APPROVED" if approve else "REJECTED"
    model = revision_model(job)
    for revision in db.scalars(select(model).where(model.import_job_id == job.id)):
        revision.state, revision.reviewer, revision.review_note, revision.reviewed_at = (
            state,
            actor.id,
            note,
            utcnow(),
        )
    audit(db, actor, "IMPORT", job.id, state, note)
    job.state = state
    db.commit()


def apply_revision(db, revision, source):
    from app.services.catalog_verification import fingerprint, validate_publication

    record = CatalogRecord.model_validate(revision.payload)
    key = source.id + ":" + record.external_key
    variant = db.scalar(select(VehicleVariant).where(VehicleVariant.catalog_key == key))
    if variant and variant.editorial_locked:
        raise ValueError("EDITORIAL_OVERRIDE_PROTECTED")
    verification_gate = validate_publication(db, record, variant)
    from app.services.catalog_names import existing_name

    make = existing_name(db, record.make)
    if not make:
        make = VehicleMake(name=record.make, normalized_name=normalized(record.make), is_demo=False)
        db.add(make)
        db.flush()
    # Reuse a canonical name introduced by a demo; no demo technical facts are copied.
    make.is_demo = False
    model = existing_name(db, record.model, make_id=make.id)
    if not model:
        model = VehicleModel(
            make_id=make.id,
            name=record.model,
            normalized_name=normalized(record.model),
            is_demo=False,
        )
        db.add(model)
        db.flush()
    model.is_demo = False
    gen_code = record.generation_code or record.generation or "UNRESOLVED"
    generation = db.scalar(
        select(VehicleGeneration).where(
            VehicleGeneration.model_id == model.id, VehicleGeneration.code == gen_code
        )
    )
    if not generation:
        generation = VehicleGeneration(
            model_id=model.id,
            name=record.generation or "Generation unverified",
            code=gen_code,
            is_demo=False,
        )
        db.add(generation)
        db.flush()
    if variant is None:
        variant = VehicleVariant(
            catalog_key=key,
            generation_id=generation.id,
            name=record.configuration,
            market=record.original_market,
            data_origin=DataOrigin.REAL,
            is_demo=False,
        )
        db.add(variant)
        db.flush()
    revision.variant_id = variant.id
    for observation in record.market_observations:
        market_source = require_source(db, observation.source_id)
        observation_key = "knowledge-market:" + checksum(
            {
                "source": observation.source_id,
                "external_key": observation.external_key,
                "observed_at": observation.observed_at.isoformat(),
            }
        )
        payload_hash = checksum(observation.model_dump(mode="json"))
        existing = db.scalar(
            select(MarketListing).where(MarketListing.external_key == observation_key)
        )
        if existing:
            if existing.vehicle_variant_id != variant.id or f"payload={payload_hash}" not in (
                existing.source.notes or ""
            ):
                raise ValueError("MARKET_OBSERVATION_CONFLICT")
            continue
        observation_source = SourceRecord(
            title=f"{record.make} {record.model} {record.model_year} · dated asking price",
            publisher=market_source.title,
            url=observation.source_url,
            source_type="KNOWLEDGE_MARKET_OBSERVATION",
            source_tier=SourceTier.B,
            data_origin=DataOrigin.REAL,
            market=observation.country,
            published_at=observation.observed_at,
            retrieved_at=utcnow(),
            confidence=ConfidenceLevel.HIGH,
            is_demo=False,
            notes=f"registry={market_source.id}; payload={payload_hash}; scope={catalog_identity_hash(record.model_dump(mode='json'))}; locator={observation.locator}; identity={observation.identity_basis}",
        )
        db.add(observation_source)
        db.flush()
        db.add(
            MarketListing(
                vehicle_variant_id=variant.id,
                source_id=observation_source.id,
                external_key=observation_key,
                country=observation.country,
                city=observation.city,
                make=record.make,
                model=record.model,
                generation=record.generation,
                year=record.model_year,
                price=observation.price,
                currency=observation.currency,
                mileage_km=observation.mileage_km,
                url=observation.source_url,
                observed_at=observation.observed_at,
                is_demo=False,
                data_origin=DataOrigin.REAL,
            )
        )
        db.flush()
    for asset in db.scalars(select(VehicleAsset).where(VehicleAsset.state == "APPROVED")):
        a = asset.applicability
        if variant.id not in a.get("variant_ids", []):
            continue
        body = record.facts.get("body")
        if (
            normalized(a.get("make", "")) != normalized(record.make)
            or normalized(a.get("model", "")) != normalized(record.model)
            or a.get("generation") != record.generation
            or a.get("facelift") != record.facelift
            or a.get("market") != record.original_market
            or not body
            or body.status != "CONFIRMED"
            or body.value != a.get("body")
            or not a.get("year_from", 0) <= record.model_year <= a.get("year_to", 0)
        ):
            asset.state = "IMAGE_QA"
            asset.version += 1
    revision.previous_revision_id = variant.published_revision_id
    fact_source = SourceRecord(
        title=f"{record.make} {record.model} {record.model_year} · {source.title}",
        publisher=source.title,
        url=record.source_url,
        source_type="CATALOG_PUBLICATION",
        source_tier=SourceTier.A if source.id == "epa" else SourceTier.B,
        data_origin=DataOrigin.REAL,
        market=record.original_market if len(record.original_market) == 2 else None,
        language="en",
        retrieved_at=utcnow(),
        confidence=ConfidenceLevel.HIGH,
        is_demo=False,
        notes=f"revision={revision.id}; rights={source.config.get('rights')}; document={revision.import_job_id}",
    )
    db.add(fact_source)
    db.flush()
    documentary_sources = {}

    def documentary_source(ref):
        key = (ref.registry_id, ref.document_id)
        if key not in documentary_sources:
            registry = require_source(db, ref.registry_id)
            linked = SourceRecord(
                title=f"{record.make} {record.model} {record.model_year} · {registry.title}",
                publisher=registry.title,
                url=ref.url,
                source_type="FACTORY_DOCUMENTARY_EVIDENCE",
                source_tier=SourceTier.A,
                data_origin=DataOrigin.REAL,
                market=record.original_market,
                language="en",
                retrieved_at=utcnow(),
                confidence=ConfidenceLevel.HIGH,
                is_demo=False,
                notes=f"registry={ref.registry_id}; document={ref.document_id}; sha256={ref.sha256}; revision={revision.id}",
            )
            db.add(linked)
            db.flush()
            documentary_sources[key] = linked
        return documentary_sources[key]

    facts = {}
    for fact_key, fact in record.facts.items():
        linked_source = (
            documentary_source(fact.documentary_source) if fact.documentary_source else fact_source
        )
        category = (
            "engine"
            if fact_key.startswith("engine")
            or fact_key in {"cylinders", "aspiration", "powertrain"}
            else "transmission"
            if fact_key.startswith("transmission") or fact_key == "gears"
            else "fuel"
            if fact_key.startswith(("fuel", "electricity"))
            else "body"
            if fact_key in {"body", "size_class"}
            else "other"
        )
        evidence = TechnicalEvidence(
            vehicle_variant_id=variant.id,
            source_id=linked_source.id,
            category=EvidenceCategory(category),
            title=fact_key,
            statement=str(fact.value),
            status=EvidenceStatus(fact.status),
            confidence=ConfidenceLevel.HIGH if fact.status == "CONFIRMED" else ConfidenceLevel.LOW,
            market=linked_source.market,
            conditions={
                "fact": fact.model_dump(mode="json"),
                "revision_id": revision.id,
                "original_market": record.original_market,
                "year": record.model_year,
                "generation": record.generation,
                "configuration": record.configuration,
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        db.add(evidence)
        db.flush()
        facts[fact_key] = {
            **fact.model_dump(mode="json"),
            "evidence_id": evidence.id,
            "source_id": linked_source.id,
            "retrieved_at": utcnow().isoformat(),
        }

    def value(key):
        fact = facts.get(key, {})
        return fact.get("value") if fact.get("status") == "CONFIRMED" else None

    variant.generation_id = generation.id
    variant.name, variant.market = record.configuration, record.original_market
    variant.year_from = variant.year_to = record.model_year
    variant.engine = str(value("engine_description") or value("powertrain") or "") or None
    variant.engine_code = value("engine_code")
    variant.transmission = value("transmission_description")
    variant.transmission_code = value("transmission_code")
    variant.drivetrain, variant.body, variant.fuel = (
        value("drivetrain"),
        value("body"),
        value("fuel"),
    )
    variant.displacement_l = (
        Decimal(str(value("engine_displacement")))
        if value("engine_displacement") is not None
        else None
    )
    variant.specification_source_id = fact_source.id
    documentary_evidence = {}
    for section in record.documentary_sections:
        section_sources = [documentary_source(ref) for ref in section.references]
        evidence = TechnicalEvidence(
            vehicle_variant_id=variant.id,
            source_id=section_sources[0].id,
            category=EvidenceCategory("other"),
            title="dossier:" + section.key,
            statement=section.text["ru"],
            status=EvidenceStatus.CONFIRMED,
            confidence=ConfidenceLevel.HIGH,
            market=record.original_market,
            conditions={
                "section": section.model_dump(mode="json"),
                "revision_id": revision.id,
                "model_year": record.model_year,
                "configuration": record.configuration,
            },
            is_demo=False,
            data_origin=DataOrigin.REAL,
        )
        db.add(evidence)
        db.flush()
        documentary_evidence[section.key] = {
            "source_ids": list(dict.fromkeys(s.id for s in section_sources)),
            "evidence_ids": [evidence.id],
        }
    variant.specifications = {
        "catalog": {
            **record.model_dump(mode="json"),
            "facts": facts,
            "revision_id": revision.id,
            "source_registry_id": source.id,
            "publication_scope": "COMMERCIAL"
            if source.config.get("commercial_reuse")
            else "LOCAL_RESEARCH",
            "published_at": utcnow().isoformat(),
            "normalizer_version": PARSER_VERSION,
            "documentary_evidence": documentary_evidence,
        }
    }
    if verification_gate:
        catalog = variant.specifications["catalog"]
        variant.specifications = {
            "catalog": {
                **catalog,
                "verification_gate": {**verification_gate, "fingerprint": fingerprint(catalog)},
            }
        }
    variant.published_revision_id = revision.id
    revision.state, revision.published_at = "PUBLISHED", utcnow()
    return variant


def publish_job(db, job, actor, *, note):
    source = require_source(db, job.source_id)
    if job.state != "APPROVED":
        raise ValueError("REVIEW_REQUIRED")
    model = revision_model(job)
    revisions = list(db.scalars(select(model).where(model.import_job_id == job.id)))
    if not revisions or any(r.state != "APPROVED" for r in revisions):
        raise ValueError("REVIEW_REQUIRED")
    try:
        if model is OwnershipEvidenceRevision:
            from app.services.ownership_evidence import publish_revisions

            publish_revisions(db, revisions, source)
        elif model is MarketDiscoveryRevision:
            from app.services.market_discovery import publish_revisions

            publish_revisions(db, revisions, source)
        else:
            for revision in revisions:
                apply_revision(db, revision, source)
        job.state = "PUBLISHED"
        source.config = {**source.config, "last_successful_publication_at": utcnow().isoformat()}
        audit(
            db,
            actor,
            "IMPORT",
            job.id,
            "PUBLISHED",
            note,
            after={
                "versions": len(revisions),
                "scope": "COMMERCIAL"
                if source.config.get("commercial_reuse")
                else "LOCAL_RESEARCH",
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return len(revisions)
