"""Publish annual EPA source-confirmed CORE rows from the already cached universe.

The script has no acquisition path. By default it plans without changing the DB;
``--publish`` applies exactly the eligible plan through the existing catalogue
revision publisher. Factory-scoped verification is neither inferred nor changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from contextlib import suppress
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.knowledge_ops import CatalogRevision, ImportJob  # noqa: E402
from app.schemas.knowledge import CatalogRecord  # noqa: E402
from app.services.catalog_verification import (  # noqa: E402
    identity_verified,
    source_confirmed_core_ready,
)
from app.services.knowledge_import import (  # noqa: E402
    apply_revision,
    checksum,
    epa_record,
    normalized,
)
from app.services.knowledge_registry import require_source, utcnow  # noqa: E402

UNIVERSE = ROOT / "deliverables/VerifiedData/us-catalog-universe/candidates.jsonl"
INDEX = UNIVERSE.with_name("index.json")
SOURCE_ZIP = ROOT / ".localdata/epa-bulk-cache/vehicles-current.zip"
EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
RULE_VERSION = "epa-source-confirmed-core-1"
OPTIONAL_FACT_CORRECTION_RULE_VERSION = "epa-source-confirmed-core-optional-facts-2"
CHUNK_SIZE = 50
CORE_FACT_KEYS = frozenset(
    {
        "powertrain",
        "fuel",
        "engine_displacement",
        "transmission_description",
        "drivetrain",
        "motor_description",
    }
)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fact(catalog: dict, name: str) -> object | None:
    fact = catalog.get("facts", {}).get(name) or {}
    return fact.get("value") if fact.get("status") == "CONFIRMED" else None


def _number(value: object) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(Decimal(str(value)).normalize())
    except (InvalidOperation, ValueError):
        return None


def _drive(value: object) -> str | None:
    value = normalized(str(value or ""))
    return {
        "front wheel drive": "FWD",
        "rear wheel drive": "RWD",
        "all wheel drive": "AWD",
        "4 wheel drive": "4WD",
        "part time 4 wheel drive": "PART_TIME_4WD",
        "fwd": "FWD",
        "rwd": "RWD",
        "awd": "AWD",
        "4wd": "4WD",
        "part time 4wd": "PART_TIME_4WD",
    }.get(value)


def _transmission(
    value: object, family: object, powertrain: object
) -> tuple[str, int | None]:
    """Coarse identity only; never claims AT/CVT/DCT construction from EPA."""
    import re

    text = normalized(str(value or ""))
    family = str(family or "").upper()
    count = re.search(r"\b(\d+)\s*(?:speed|spd)\b|\b(?:a|am|av)(\d+)\b", text)
    gears = int(count[1] or count[2]) if count else None
    # EPA's A1 means one forward ratio; it is compatible with an OEM-confirmed
    # single-speed BEV drive, but does not prove torque-converter construction.
    if str(powertrain).upper() == "BEV" and (
        family == "SINGLE_SPEED"
        or (family == "AUTOMATIC_UNSPECIFIED" and gears == 1)
    ):
        return "SINGLE_SPEED", None
    if family == "MANUAL" or text.startswith("manual"):
        kind = "MANUAL"
    elif family in {"CVT", "ECVT", "VARIABLE_UNSPECIFIED"} or "variable" in text:
        kind = "VARIABLE"
    elif family == "SINGLE_SPEED":
        kind = "SINGLE_SPEED"
    elif family in {
        "AT",
        "DCT",
        "AMT",
        "AUTOMATIC_UNSPECIFIED",
        "AMT_UNSPECIFIED",
    } or text.startswith("automatic"):
        kind = "AUTOMATIC"
    else:
        kind = text
    return kind, gears


def core_tuple(catalog: dict) -> tuple | None:
    """Equivalence for suppressing a coarse EPA tuple covered by a factory row."""
    required = ("powertrain", "transmission_description", "drivetrain")
    if any(_fact(catalog, key) in (None, "") for key in required):
        return None
    return (
        normalized(str(catalog.get("make") or "")),
        normalized(str(catalog.get("model") or "")),
        catalog.get("model_year"),
        catalog.get("original_market"),
        str(_fact(catalog, "powertrain")).upper(),
        str(_fact(catalog, "fuel") or "").upper(),
        _number(_fact(catalog, "engine_displacement")),
        _transmission(
            _fact(catalog, "transmission_description"),
            _fact(catalog, "transmission_family"),
            _fact(catalog, "powertrain"),
        ),
        _drive(_fact(catalog, "drivetrain")),
    )


def _epa_ids(catalog: dict) -> set[str]:
    if catalog.get("source_registry_id") != "epa":
        return set()
    ids = set()
    ids.update(
        str(value) for value in (catalog.get("source_provenance") or {}).get("epa_vehicle_ids", [])
    )
    key = str(catalog.get("external_key") or "")
    if key.isdigit():
        ids.add(key)
    note = catalog.get("revision_note") or ""
    if note.startswith("EPA_CORE_PROVENANCE:"):
        with suppress(ValueError, KeyError, TypeError):
            ids.update(str(value) for value in json.loads(note.split(":", 1)[1])["epa_ids"])
    return ids


def _factory_cited_epa_ids(catalog: dict) -> set[str]:
    """Only explicit EPA row citations; a shared BEV drive is not motor identity."""
    ids = set()
    external_key = str(catalog.get("external_key") or "")
    ids.update(re.findall(r"(?:^|-)epa-(\d{4,7})(?:-|$)", external_key, re.I))
    configuration = str(catalog.get("configuration") or "")
    ids.update(re.findall(r"\bEPA\s+(\d{4,7})\b", configuration, re.I))
    url = str(catalog.get("source_url") or "")
    ids.update(re.findall(r"/vehicle/(\d{4,7})(?:$|[/?#])", url, re.I))
    for fact in (catalog.get("facts") or {}).values():
        locator = str((fact or {}).get("locator") or "")
        ids.update(
            re.findall(r"\bEPA\s+vehicles\.csv\s+exact\s+id\s+(\d{4,7})\b", locator, re.I)
        )
    return ids


def existing_publications(
    db: Session,
) -> tuple[dict[str, list[dict]], dict[tuple, list[dict]], dict[str, list[dict]], set[str]]:
    verified_ids: dict[str, list[dict]] = defaultdict(list)
    verified_tuples: dict[tuple, list[dict]] = defaultdict(list)
    published_epa_ids: dict[str, list[dict]] = defaultdict(list)
    published_catalog_keys: set[str] = set()
    for variant in db.scalars(
        select(VehicleVariant).where(
            VehicleVariant.published_revision_id.is_not(None), VehicleVariant.is_demo.is_(False)
        )
    ):
        catalog = (variant.specifications or {}).get("catalog") or {}
        if not catalog or catalog.get("original_market") != "US":
            continue
        if variant.catalog_key:
            published_catalog_keys.add(variant.catalog_key)
        ids = _epa_ids(catalog)
        if identity_verified(catalog):
            ids.update(_factory_cited_epa_ids(catalog))
        for vehicle_id in ids:
            published_epa_ids[vehicle_id].append(catalog)
        if identity_verified(catalog):
            for vehicle_id in ids:
                verified_ids[vehicle_id].append(catalog)
            identity = core_tuple(catalog)
            # BEV motor outputs can differ while the coarse make/year/drive/
            # one-speed tuple is identical. Only explicit EPA row citations
            # suppress BEV groups until a motor-specific mapping is available.
            if identity is not None and _fact(catalog, "powertrain") != "BEV":
                verified_tuples[identity].append(catalog)
    return verified_ids, verified_tuples, published_epa_ids, published_catalog_keys


def read_cached_groups(
    path: Path = UNIVERSE, index_path: Path = INDEX, source_zip: Path = SOURCE_ZIP
) -> tuple[list[list[dict]], dict]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    source = index["source"]
    if source["url"] != EPA_URL or not source["zip_sha256"]:
        raise ValueError("EPA_SOURCE_PROVENANCE_MISMATCH")
    source_digest = hashlib.sha256()
    with source_zip.open("rb") as cached_source:
        for block in iter(lambda: cached_source.read(1024 * 1024), b""):
            source_digest.update(block)
    if source_digest.hexdigest() != source["zip_sha256"]:
        raise ValueError("EPA_CACHED_ZIP_HASH_MISMATCH")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != index["candidate_jsonl_sha256"]:
        raise ValueError("EPA_CANDIDATE_CACHE_HASH_MISMATCH")
    groups: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for line in content.splitlines():
        row = json.loads(line)
        if row["source"]["dataset_sha256"] != source["zip_sha256"]:
            raise ValueError("EPA_ROW_SOURCE_HASH_MISMATCH")
        groups[row["model_year"], row["normalized_powertrain_key"]].append(row)
    if len(content.splitlines()) != index["denominator"]["epa_rows_after_filter"]:
        raise ValueError("EPA_CANDIDATE_COUNT_MISMATCH")
    ordered = sorted(
        groups.values(),
        key=lambda rows: (
            normalized(rows[0]["make"]),
            normalized(rows[0]["model"]),
            rows[0]["model_year"],
            rows[0]["normalized_powertrain_key"],
        ),
    )
    return ordered, index


def make_record(rows: list[dict], source_sha256: str) -> CatalogRecord:
    """Use EPA's conservative parser, collapse only the identical annual core tuple."""
    rows = sorted(rows, key=lambda row: int(row["epa_vehicle_id"]))
    first = rows[0]
    ids = [row["epa_vehicle_id"] for row in rows]
    if len({(r["model_year"], r["normalized_powertrain_key"]) for r in rows}) != 1:
        raise ValueError("NONIDENTICAL_ANNUAL_TUPLE")
    record = epa_record(first["epa_fields"])
    facts = record.facts
    # Raw EPA test rows can share an annual powertrain identity while varying
    # in economy, range, body class or cargo volume. A first-row value must
    # never be presented as a fact about every contributing EPA vehicle ID.
    # Compare parsed values so equivalent source spellings and conversions
    # follow the same rules as consumer-facing facts.
    if len(rows) > 1:
        parsed = [epa_record(row["epa_fields"]).facts for row in rows[1:]]
        for key in tuple(facts):
            if key in CORE_FACT_KEYS:
                continue
            first_fact = facts[key]
            if any(
                (other := row_facts.get(key)) is None
                or (other.value, other.unit, other.status)
                != (first_fact.value, first_fact.unit, first_fact.status)
                for row_facts in parsed
            ):
                facts.pop(key)
    engine = facts.get("engine_displacement")
    powertrain = facts.get("powertrain")
    transmission = facts.get("transmission_description")
    drivetrain = facts.get("drivetrain")
    config = " · ".join(
        str(value)
        for value in (
            first["model"],
            (str(engine.value) + " L") if engine else (powertrain.value if powertrain else ""),
            transmission.value if transmission else "",
            drivetrain.value if drivetrain else "",
        )
        if value not in (None, "")
    )
    provenance = {
        "dataset_sha256": source_sha256,
        "epa_ids": ids,
        "model_year": first["model_year"],
        "normalized_powertrain_key": first["normalized_powertrain_key"],
    }
    key = (
        "core-v1-"
        + hashlib.sha256(
            _json((first["model_year"], first["normalized_powertrain_key"])).encode()
        ).hexdigest()
    )
    payload = record.model_dump(mode="json")
    payload.update(
        external_key=key,
        model=first["model"],
        configuration=config,
        aliases=sorted({row["epa_model"] for row in rows}, key=normalized),
        source_url=EPA_URL,
        revision_note="EPA_CORE_PROVENANCE:" + _json(provenance),
    )
    return CatalogRecord.model_validate(payload)


def planned_catalog(record: CatalogRecord) -> dict:
    """Preflight shape before apply_revision attaches concrete SourceRecord IDs."""
    catalog = record.model_dump(mode="json")
    catalog["source_registry_id"] = "epa"
    catalog["facts"] = {key: {**fact, "source_id": "epa"} for key, fact in catalog["facts"].items()}
    return catalog


def insufficient_reasons(catalog: dict) -> list[str]:
    """Explain the source-core gate without weakening the authoritative predicate."""
    reasons = []
    facts = catalog.get("facts") or {}
    for key in ("powertrain", "transmission_description", "drivetrain"):
        if _fact(catalog, key) in (None, ""):
            reasons.append("MISSING_" + key.upper())
    drive = _fact(catalog, "drivetrain")
    if drive not in (None, "") and _drive(drive) is None:
        reasons.append("AMBIGUOUS_DRIVETRAIN")
    powertrain = _fact(catalog, "powertrain")
    if powertrain not in {"BEV", "FCEV"}:
        if _fact(catalog, "fuel") in (None, ""):
            reasons.append("MISSING_FUEL")
        displacement = _number(_fact(catalog, "engine_displacement"))
        if displacement is None or Decimal(displacement) <= 0:
            reasons.append("MISSING_DISPLACEMENT")
    family = facts.get("transmission_family") or {}
    if family and family.get("value") not in {
        "AT",
        "CVT",
        "DCT",
        "MANUAL",
        "ECVT",
        "SINGLE_SPEED",
        "AMT",
        "AUTOMATIC_UNSPECIFIED",
        "VARIABLE_UNSPECIFIED",
        "AMT_UNSPECIFIED",
    }:
        reasons.append("UNSUPPORTED_TRANSMISSION_FAMILY")
    return reasons or ["SOURCE_CONFIRMED_CORE_PREDICATE_FAILED"]


def verified_conflict(record: CatalogRecord, verified: dict) -> list[str]:
    issues = []
    if normalized(record.make) != normalized(verified.get("make", "")):
        issues.append("MAKE")
    if record.model_year != verified.get("model_year"):
        issues.append("MODEL_YEAR")
    candidate = planned_catalog(record)
    for key in ("drivetrain", "engine_displacement"):
        one, two = _fact(candidate, key), _fact(verified, key)
        if one is None or two is None:
            continue
        if key == "drivetrain":
            drives = {_drive(one), _drive(two)}
            if len(drives) > 1 and drives != {"AWD", "4WD"}:
                issues.append("DRIVETRAIN")
        elif key == "engine_displacement":
            try:
                if abs(Decimal(str(one)) - Decimal(str(two))) > Decimal("0.25"):
                    issues.append("DISPLACEMENT")
            except InvalidOperation:
                pass
    return issues


def compatible_factory_tuple(rows: list[dict], verified: dict) -> bool:
    """Only suppress a tuple when EPA's differentiating fields are covered."""
    first = rows[0]
    source = first["epa_fields"]
    names = {normalized(row["epa_model"]) for row in rows}
    factory_names = {
        normalized(verified.get("model")),
        *(normalized(name) for name in verified.get("aliases") or []),
    }
    if not names & factory_names:
        return False
    cylinders = source.get("cylinders") or ""
    if cylinders and _number(_fact(verified, "cylinders")) != _number(cylinders):
        return False
    turbo, supercharged = source.get("tCharger") == "T", source.get("sCharger") == "S"
    factory_aspiration = str(_fact(verified, "aspiration") or "").upper()
    if turbo and factory_aspiration not in {"TURBO", "TWIN_TURBO"}:
        return False
    if supercharged and factory_aspiration != "SUPERCHARGED":
        return False
    if not turbo and not supercharged and factory_aspiration in {
        "TURBO", "TWIN_TURBO", "SUPERCHARGED",
    }:
        return False
    engine_detail = normalized(source.get("eng_dscr") or "")
    if engine_detail:
        factory_engine = normalized(str(_fact(verified, "engine_description") or ""))
        if engine_detail not in factory_engine:
            return False
    motor = normalized(source.get("evMotor") or "")
    if motor and motor not in normalized(str(_fact(verified, "motor_description") or "")):
        return False
    fuel2 = normalized(source.get("fuelType2") or "")
    if fuel2 and fuel2 != normalized(str(_fact(verified, "secondary_fuel") or "")):
        return False
    trans_detail = normalized(source.get("trans_dscr") or "")
    return not trans_detail or trans_detail in normalized(
        str(_fact(verified, "transmission_description") or "")
    )


def plan_groups(groups: list[list[dict]], index: dict, db: Session) -> tuple[list[dict], dict]:
    verified_ids, verified_tuples, published_ids, published_keys = existing_publications(db)
    source_sha256 = index["source"]["zip_sha256"]
    plan = []
    counts = Counter()
    by_make: dict[str, Counter] = defaultdict(Counter)
    for rows in groups:
        first = rows[0]
        ids = {row["epa_vehicle_id"] for row in rows}
        base = {
            "make": first["make"],
            "model": first["model"],
            "model_year": first["model_year"],
            "normalized_powertrain_key": first["normalized_powertrain_key"],
            "epa_ids": sorted(ids, key=int),
        }
        try:
            record = make_record(rows, source_sha256)
            candidate = planned_catalog(record)
            base["external_key"] = record.external_key
            if any(
                verified_conflict(record, verified)
                for vehicle_id in ids
                for verified in verified_ids.get(vehicle_id, [])
            ):
                status, reason = "CONFLICT", "EXACT_EPA_ID_DISAGREES_WITH_VERIFIED"
            elif any(vehicle_id in verified_ids for vehicle_id in ids) or any(
                compatible_factory_tuple(rows, verified)
                for verified in verified_tuples.get(core_tuple(candidate), [])
            ):
                status, reason = "SUPPRESSED_VERIFIED", "EQUIVALENT_VERIFIED_SCOPED"
            elif not source_confirmed_core_ready(candidate):
                status, reason = "INSUFFICIENT_CORE", "+".join(insufficient_reasons(candidate))
            elif "epa:" + record.external_key in published_keys:
                status, reason = "ALREADY_CORE", "STABLE_CATALOG_KEY"
            elif any(
                source_confirmed_core_ready(existing)
                and core_tuple(existing) == core_tuple(candidate)
                for vehicle_id in ids
                for existing in published_ids.get(vehicle_id, [])
            ):
                status, reason = "SUPPRESSED_EXISTING_EPA", "ALREADY_PUBLISHED_SOURCE_ROW"
            else:
                status, reason = "PUBLISH_CORE", "SOURCE_CONFIRMED_CORE"
            if status == "PUBLISH_CORE":
                base["record"] = record.model_dump(mode="json")
        except (ValueError, TypeError, KeyError) as exc:
            status, reason = "INSUFFICIENT_CORE", str(exc).splitlines()[0][:180]
        base["status"] = status
        base["reason"] = reason
        plan.append(base)
        counts[status] += 1
        by_make[first["make"]][status] += 1
    return plan, {
        "rule_version": RULE_VERSION,
        "source_sha256": source_sha256,
        "annual_configurations_considered": len(groups),
        "counts": dict(sorted(counts.items())),
        "by_make": {make: dict(sorted(values.items())) for make, values in sorted(by_make.items())},
    }


def publish_plan(
    db: Session, plan: list[dict], index: dict, *, chunk_size: int = CHUNK_SIZE
) -> dict:
    """Chunked, resumable publication; each tuple has one stable catalog key."""
    if chunk_size < 1:
        raise ValueError("CHUNK_SIZE")
    source = require_source(db, "epa")
    request_key = checksum({"rule": RULE_VERSION, "source": index["source"]["zip_sha256"]})
    job = db.scalar(select(ImportJob).where(ImportJob.request_key == request_key))
    if job is None:
        job = ImportJob(
            request_key=request_key,
            source_id="epa",
            manifest={
                "parser": RULE_VERSION,
                "source_url": EPA_URL,
                "source_sha256": index["source"]["zip_sha256"],
                "automated_core_admission": True,
                "factory_verification": False,
            },
            state="APPROVED",
            metrics={"candidate_annual_configurations": len(plan)},
        )
        db.add(job)
        db.commit()
    elif (
        job.source_id != "epa" or job.manifest.get("source_sha256") != index["source"]["zip_sha256"]
    ):
        raise ValueError("BULK_JOB_IDENTITY_CONFLICT")
    metrics = Counter()
    pending = [item for item in plan if item["status"] == "PUBLISH_CORE"]
    for offset in range(0, len(pending), chunk_size):
        for item in pending[offset : offset + chunk_size]:
            record = CatalogRecord.model_validate(item["record"])
            key = source.id + ":" + record.external_key
            existing_variant = db.scalar(
                select(VehicleVariant).where(VehicleVariant.catalog_key == key)
            )
            if existing_variant and existing_variant.published_revision_id:
                metrics["already_core_on_rerun"] += 1
                continue
            revision = db.scalar(
                select(CatalogRevision).where(
                    CatalogRevision.import_job_id == job.id,
                    CatalogRevision.external_key == record.external_key,
                )
            )
            payload = record.model_dump(mode="json")
            if revision is None:
                revision = CatalogRevision(
                    import_job_id=job.id,
                    external_key=record.external_key,
                    payload=payload,
                    checksum=checksum(payload),
                    state="APPROVED",
                    reviewer="AUTOMATED_SOURCE_CONFIRMED_CORE",
                    review_note="Official EPA source tuple; no factory identity claim",
                    reviewed_at=utcnow(),
                )
                db.add(revision)
                db.flush()
            elif revision.checksum != checksum(payload):
                raise ValueError("STABLE_CORE_REVISION_PAYLOAD_CHANGED")
            elif revision.state == "PUBLISHED":
                metrics["already_core_on_rerun"] += 1
                continue
            variant = apply_revision(db, revision, source)
            attach_source_provenance(variant, record)
            metrics["core_published"] += 1
        job.cursor = min(offset + chunk_size, len(pending))
        job.metrics = {**job.metrics, **metrics}
        db.commit()
    job.state = "PUBLISHED"
    job.metrics = {**job.metrics, **metrics, "planned_core_count": len(pending)}
    db.commit()
    return dict(metrics)


def attach_source_provenance(variant: VehicleVariant, record: CatalogRecord) -> None:
    """Keep every contributing EPA ID when a core row is created or corrected."""
    provenance = json.loads(record.revision_note.split(":", 1)[1])
    catalog = variant.specifications["catalog"]
    variant.specifications = {
        "catalog": {
            **catalog,
            "source_provenance": {
                "dataset_url": EPA_URL,
                "dataset_sha256": provenance["dataset_sha256"],
                "epa_vehicle_ids": provenance["epa_ids"],
                "normalized_powertrain_key": provenance["normalized_powertrain_key"],
            },
        }
    }


def plan_optional_fact_corrections(
    groups: list[list[dict]], index: dict, db: Session
) -> tuple[list[dict], dict]:
    """Find published CORE rows containing a first-row-only optional EPA fact.

    This is a separate, read-only plan. It never rewrites an old published
    revision and will not touch a verified or editorially amended variant.
    """
    existing = {
        variant.catalog_key: variant
        for variant in db.scalars(
            select(VehicleVariant).where(
                VehicleVariant.catalog_key.like("epa:core-v1-%"),
                VehicleVariant.published_revision_id.is_not(None),
                VehicleVariant.is_demo.is_(False),
            )
        )
    }
    plan: list[dict] = []
    counts = Counter()
    by_make: dict[str, Counter] = defaultdict(Counter)
    for rows in groups:
        if len(rows) < 2:
            continue
        rows = sorted(rows, key=lambda row: int(row["epa_vehicle_id"]))
        first = rows[0]
        record = make_record(rows, index["source"]["zip_sha256"])
        variant = existing.get("epa:" + record.external_key)
        if variant is None:
            continue
        catalog = (variant.specifications or {}).get("catalog") or {}
        if catalog.get("source_registry_id") != "epa" or identity_verified(catalog):
            counts["SKIPPED_NOT_CORE"] += 1
            continue
        if variant.editorial_locked:
            counts["SKIPPED_EDITORIAL_LOCK"] += 1
            continue
        original_fact_keys = set(epa_record(first["epa_fields"]).facts)
        current_fact_keys = set(catalog.get("facts") or {})
        if current_fact_keys - original_fact_keys:
            counts["SKIPPED_ENRICHED_CORE"] += 1
            continue
        removed = sorted((original_fact_keys - set(record.facts)) & current_fact_keys)
        if not removed:
            counts["ALREADY_CONSENSUS_SAFE"] += 1
            continue
        # Corrections only prune unsafe first-row facts. Do not add facts that
        # the previous publisher conservatively omitted.
        payload = record.model_dump(mode="json")
        payload["facts"] = {
            key: fact for key, fact in payload["facts"].items() if key in current_fact_keys
        }
        item = {
            "status": "CORRECT_OPTIONAL_FACTS",
            "make": first["make"],
            "model": first["model"],
            "model_year": first["model_year"],
            "external_key": record.external_key,
            "epa_ids": [row["epa_vehicle_id"] for row in rows],
            "removed_facts": removed,
            "previous_revision_id": variant.published_revision_id,
            "record": payload,
        }
        plan.append(item)
        counts[item["status"]] += 1
        by_make[first["make"]][item["status"]] += 1
    return plan, {
        "rule_version": OPTIONAL_FACT_CORRECTION_RULE_VERSION,
        "source_sha256": index["source"]["zip_sha256"],
        "published_core_variants": len(existing),
        "correction_count": len(plan),
        "counts": dict(sorted(counts.items())),
        "by_make": {make: dict(sorted(values.items())) for make, values in sorted(by_make.items())},
    }


def publish_optional_fact_corrections(
    db: Session, plan: list[dict], index: dict, *, chunk_size: int = CHUNK_SIZE
) -> dict:
    """Republish affected rows through a new immutable revision on the same variant."""
    if chunk_size < 1:
        raise ValueError("CHUNK_SIZE")
    if not plan:
        return {}
    source = require_source(db, "epa")
    request_key = checksum(
        {"rule": OPTIONAL_FACT_CORRECTION_RULE_VERSION, "source": index["source"]["zip_sha256"]}
    )
    job = db.scalar(select(ImportJob).where(ImportJob.request_key == request_key))
    if job is None:
        job = ImportJob(
            request_key=request_key,
            source_id="epa",
            manifest={
                "parser": OPTIONAL_FACT_CORRECTION_RULE_VERSION,
                "source_url": EPA_URL,
                "source_sha256": index["source"]["zip_sha256"],
                "correction": "PRUNE_CONFLICTING_OPTIONAL_EPA_FACTS",
                "factory_verification": False,
            },
            state="APPROVED",
            metrics={"planned_corrections": len(plan)},
        )
        db.add(job)
        db.commit()
    elif (
        job.source_id != "epa"
        or job.manifest.get("source_sha256") != index["source"]["zip_sha256"]
    ):
        raise ValueError("OPTIONAL_FACT_CORRECTION_JOB_IDENTITY_CONFLICT")
    metrics = Counter()
    for offset in range(0, len(plan), chunk_size):
        for item in plan[offset : offset + chunk_size]:
            record = CatalogRecord.model_validate(item["record"])
            key = "epa:" + record.external_key
            variant = db.scalar(select(VehicleVariant).where(VehicleVariant.catalog_key == key))
            if variant is None or not variant.published_revision_id:
                raise ValueError("PUBLISHED_CORE_REQUIRED_FOR_CORRECTION")
            catalog = (variant.specifications or {}).get("catalog") or {}
            if (
                variant.editorial_locked
                or catalog.get("source_registry_id") != "epa"
                or identity_verified(catalog)
            ):
                raise ValueError("CORE_CORRECTION_SCOPE_CHANGED")
            if not set(item["removed_facts"]) & set(catalog.get("facts") or {}):
                metrics["already_safe_on_rerun"] += 1
                continue
            if variant.published_revision_id != item["previous_revision_id"]:
                raise ValueError("CORE_CORRECTION_STALE_REVISION")
            revision = db.scalar(
                select(CatalogRevision).where(
                    CatalogRevision.import_job_id == job.id,
                    CatalogRevision.external_key == record.external_key,
                )
            )
            payload = record.model_dump(mode="json")
            if revision is None:
                revision = CatalogRevision(
                    import_job_id=job.id,
                    external_key=record.external_key,
                    payload=payload,
                    checksum=checksum(payload),
                    state="APPROVED",
                    reviewer="AUTOMATED_EPA_OPTIONAL_FACT_CONSENSUS",
                    review_note="Prune optional facts not shared by all contributing EPA IDs",
                    reviewed_at=utcnow(),
                )
                db.add(revision)
                db.flush()
            elif revision.checksum != checksum(payload) or revision.state != "APPROVED":
                raise ValueError("CORE_CORRECTION_REVISION_CONFLICT")
            variant = apply_revision(db, revision, source)
            attach_source_provenance(variant, record)
            metrics["corrected"] += 1
        job.cursor = min(offset + chunk_size, len(plan))
        job.metrics = {**job.metrics, **metrics}
        db.commit()
    job.state = "PUBLISHED"
    job.metrics = {**job.metrics, **metrics}
    db.commit()
    return dict(metrics)


def run(
    db: Session, universe: Path, index_path: Path, *, publish: bool = False
) -> tuple[list[dict], dict]:
    groups, index = read_cached_groups(universe, index_path)
    plan, summary = plan_groups(groups, index, db)
    if publish:
        summary["publication"] = publish_plan(db, plan, index)
    else:
        summary["publication"] = {"dry_run": True, "database_writes": 0}
    return plan, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--universe", type=Path, default=UNIVERSE)
    parser.add_argument("--index", type=Path, default=INDEX)
    parser.add_argument(
        "--output", type=Path, default=UNIVERSE.with_name("core-publication-plan.jsonl")
    )
    parser.add_argument(
        "--repair-optional-facts",
        action="store_true",
        help="Plan or apply a new revision removing conflicting optional EPA facts",
    )
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if not args.db.is_file():
        raise ValueError("EXISTING_DATABASE_REQUIRED")
    engine = create_engine(
        "sqlite:///" + args.db.resolve().as_posix(), connect_args={"timeout": 60}
    )
    try:
        with Session(engine, autoflush=False, expire_on_commit=False) as db:
            if args.repair_optional_facts:
                groups, index = read_cached_groups(args.universe, args.index)
                plan, summary = plan_optional_fact_corrections(groups, index, db)
                summary["publication"] = (
                    publish_optional_fact_corrections(db, plan, index)
                    if args.publish
                    else {"dry_run": True, "database_writes": 0}
                )
            else:
                plan, summary = run(db, args.universe, args.index, publish=args.publish)
    finally:
        engine.dispose()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(
            _json({key: value for key, value in row.items() if key != "record"}) + "\n"
            for row in plan
        ),
        encoding="utf-8",
    )
    summary_name = (
        "core-optional-fact-correction-summary.json"
        if args.repair_optional_facts
        else "core-publication-summary.json"
    )
    summary_path = args.output.with_name(summary_name)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
