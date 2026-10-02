"""Prepare safe bulk factory-table facts for existing verified US configurations.

Read-only by default: the output is an immutable reviewed import manifest for the
existing catalog publisher. No new vehicle identities or source registrations.
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.knowledge_ops import RawDocument
from app.schemas.knowledge import CatalogRecord, FactInput, ImportManifest
from app.services.catalog_buyer import records
from app.services.catalog_verification import base_catalog_ready, catalog_excluded
from app.services.factory_bulk_tables import (
    PARSER_VERSION,
    FactoryTable,
    TableRow,
    common_table_facts,
    parse_factory_table,
)
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"
CACHE = ROOT / ".localdata/factory-bulk-cache"
SCOPE = OUT / "factory-source-scope.json"
_URL = re.compile(r"^https://www\.kiamedia\.com/us/en/models/([a-z0-9-]+)/(\d{4})/specifications$")
_INCH_VALUE = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s*in\.", re.I)


def _json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _semantic_digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _load_table(doc: RawDocument, counters: Counter) -> FactoryTable:
    cache_file = CACHE / f"{doc.sha256}-{PARSER_VERSION}.json"
    if cache_file.exists():
        parsed = json.loads(cache_file.read_text(encoding="utf-8"))
        result = {"trims": parsed.get("trims"), "rows": parsed.get("rows")}
        if (
            parsed.get("parser") == PARSER_VERSION
            and parsed.get("sha256") == doc.sha256
            and parsed.get("result_sha256") == _semantic_digest(result)
        ):
            counters["cache_hits"] += 1
            return FactoryTable(
                tuple(parsed["trims"]),
                tuple(
                    TableRow(**{**row, "values": tuple(row["values"])})
                    for row in parsed["rows"]
                ),
            )
        counters["cache_invalidated"] += 1
    raw = (ROOT / ".localdata/verified-source-documents" / doc.sha256).read_bytes()
    if hashlib.sha256(raw).hexdigest() != doc.sha256:
        raise ValueError("FACTORY_DOCUMENT_HASH_MISMATCH")
    parsed = parse_factory_table(raw)
    result = {"trims": parsed.trims, "rows": [row.__dict__ for row in parsed.rows]}
    _json(
        cache_file,
        {
            "parser": PARSER_VERSION,
            "sha256": doc.sha256,
            "result_sha256": _semantic_digest(result),
            **result,
        },
    )
    counters["documents_parsed"] += 1
    return parsed


def _alias_evidence(catalog: dict, field: str, value):
    """Prior differently named fact is evidence-only, never a novel data point."""
    facts = catalog["facts"]
    old = facts.get(field)
    if old and old.get("status") == "CONFIRMED":
        return "SAME" if str(old["value"]) == str(value) else "CONFLICT"
    alias = {
        "length_in": "factory_length",
        "width_in": "factory_width",
        "height_in": "factory_height",
        "wheelbase_in": "factory_wheelbase",
        "fuel_tank_us_gal": "fuel_tank_l",
    }.get(field)
    if not alias or alias not in facts or facts[alias].get("status") != "CONFIRMED":
        return "NEW"
    prior = facts[alias]["value"]
    try:
        if field == "fuel_tank_us_gal":
            # Manufacturer may round litres to a whole number.
            return (
                "SAME"
                if abs(Decimal(str(prior)) - Decimal(str(value)) * Decimal("3.785411784"))
                <= Decimal("0.6")
                else "CONFLICT"
            )
        found = _INCH_VALUE.search(str(prior))
        return "SAME" if found and Decimal(found["number"]) == Decimal(str(value)) else "CONFLICT"
    except (ValueError, TypeError):
        return "CONFLICT"


def _reference(doc: RawDocument, catalog: dict, fact: dict):
    locator = (
        f"Kia Media US MY{catalog['model_year']} specifications > "
        f"{fact['group']} > {fact['row']}; all {len(fact['trims'])} trim columns "
        f"agree; source cell: {fact['raw']}"
    )
    if len(locator) > 500:
        raise ValueError("FACTORY_LOCATOR_TOO_LONG")
    return dict(
        registry_id=doc.source_id,
        document_id=doc.id,
        sha256=doc.sha256,
        url=doc.locator,
        locator=locator,
        make=catalog["make"],
        model=catalog["model"],
        market="US",
        model_year=catalog["model_year"],
    )


def _public_record(catalog):
    value = {k: copy.deepcopy(v) for k, v in catalog.items() if k in CatalogRecord.model_fields}
    value["facts"] = {
        k: {a: copy.deepcopy(b) for a, b in fact.items() if a in FactInput.model_fields}
        for k, fact in catalog["facts"].items()
    }
    return value


def prepare():
    started = time.perf_counter()
    metadata = json.loads(SCOPE.read_text(encoding="utf-8"))
    scopes = metadata["model_body_scope"]
    counters = Counter()
    exceptions = []
    changes = []
    source_facts = set()
    manifests = defaultdict(list)
    phase_seconds = defaultdict(float)
    with SessionLocal() as db:
        phase_started = time.perf_counter()
        current = defaultdict(list)
        for variant, catalog in records(db):
            if (
                catalog["make"] != "Kia"
                or catalog["original_market"] != "US"
                or catalog["model_year"] < 2000
                or not base_catalog_ready(catalog)
                or catalog_excluded(catalog)
            ):
                continue
            current[(catalog["model"], catalog["model_year"])].append((variant, catalog))
        docs = list(
            db.scalars(select(RawDocument).where(RawDocument.source_id == metadata["source_id"]))
        )
        phase_seconds["db_scope_scan"] = time.perf_counter() - phase_started
        for doc in sorted(docs, key=lambda value: value.locator):
            match = _URL.fullmatch(doc.locator)
            if not match or match[1] not in scopes:
                continue
            slug, year = match[1], int(match[2])
            spec = scopes[slug]
            if year not in spec["years"]:
                continue
            targets = [
                (v, c)
                for v, c in current[(spec["model"], year)]
                if c["facts"].get("body", {}).get("value") == spec["body"]
                and c["facts"].get("powertrain", {}).get("value") == "ICE"
            ]
            if not targets:
                continue
            counters["documents_selected"] += 1
            phase_started = time.perf_counter()
            table = _load_table(doc, counters)
            phase_seconds["cache_or_parse"] += time.perf_counter() - phase_started
            counters["tables_processed"] += 1
            counters["rows_processed"] += len(table.rows)
            phase_started = time.perf_counter()
            facts, quarantined = common_table_facts(table)
            phase_seconds["whole_table_extraction"] += time.perf_counter() - phase_started
            counters["source_facts_extracted"] += len(facts)
            counters["source_rows_quarantined"] += len(quarantined)
            for item in quarantined:
                exceptions.append({"url": doc.locator, **item})
            phase_started = time.perf_counter()
            for variant, catalog in targets:
                revised = _public_record(catalog)
                added = {}
                for field, fact in facts.items():
                    state = _alias_evidence(catalog, field, fact["value"])
                    counters[f"field_{state.lower()}"] += 1
                    if state == "SAME":
                        continue
                    if state == "CONFLICT":
                        exceptions.append(
                            {
                                "url": doc.locator,
                                "field": field,
                                "reason": "PUBLISHED_VALUE_OR_ALIAS_CONFLICT",
                                "catalog_key": variant.catalog_key,
                                "source_value": fact["value"],
                                "published_value": catalog["facts"].get(field, {}).get("value"),
                            }
                        )
                        continue
                    ref = _reference(doc, catalog, fact)
                    input_fact = dict(
                        value=fact["value"],
                        status="CONFIRMED",
                        locator=ref["locator"],
                        documentary_source=ref,
                    )
                    if fact["unit"]:
                        input_fact["unit"] = fact["unit"]
                    if field == "octane_aki":
                        input_fact["titles"] = {
                            "ru": "Минимальное октановое число AKI (США)",
                            "az": "Minimum AKI oktan ədədi (ABŞ)",
                        }
                    revised["facts"][field] = input_fact
                    added[field] = fact["value"]
                    source_facts.add((doc.sha256, field, str(fact["value"])))
                if not added:
                    continue
                verification = revised.get("identity_verification")
                if verification:
                    verification["previous_revision_id"] = variant.published_revision_id
                revised["revision_note"] = (
                    "Cached Kia Media US whole-table extraction; only invariant values "
                    "across every trim; body and MY anchored to existing verified identity. "
                    "Other conditions and alternative prior field names held."
                )
                checked = CatalogRecord.model_validate(revised)
                source_id = variant.catalog_key.split(":", 1)[0]
                manifests[source_id].append(checked)
                changes.append(
                    {
                        "catalog_key": variant.catalog_key,
                        "make": catalog["make"],
                        "model": catalog["model"],
                        "generation": catalog.get("generation_code") or catalog.get("generation"),
                        "model_year": year,
                        "body": spec["body"],
                        "engine": catalog["facts"]["engine_description"]["value"],
                        "transmission": catalog["facts"]["transmission_description"]["value"],
                        "drivetrain": catalog["facts"]["drivetrain"]["value"],
                        "source_url": doc.locator,
                        "added": added,
                    }
                )
            phase_seconds["variant_mapping"] += time.perf_counter() - phase_started
        counters["catalog_records_changed"] = len(changes)
        counters["new_annual_field_values"] = sum(len(c["added"]) for c in changes)
        counters["unique_source_facts_applied"] = len(source_facts)
        for source_id, items in sorted(manifests.items()):
            manifest = ImportManifest(
                source_id=source_id,
                parser="manifest-json-v1",
                records=items,
                selection_basis=(
                    "Existing verified US Kia variants only; cached Kia Media annual whole-table "
                    "invariants, exact model year and body; unchanged source rules and "
                    "reviewed publication"
                ),
            ).model_dump(mode="json")
            path = OUT / f"factory-reviewed-{source_id}.json"
            if path.exists() and _semantic_digest(
                json.loads(path.read_text(encoding="utf-8"))
            ) != _semantic_digest(manifest):
                raise ValueError("FROZEN_FACTORY_MANIFEST_CHANGED_USE_NEW_BATCH")
            _json(path, manifest)
    result = {
        "status": "PREPARED_NOT_PUBLISHED" if changes else "NO_NEW_FACTS_ALREADY_PUBLISHED",
        "parser_version": PARSER_VERSION,
        "source_scope": str(SCOPE.relative_to(ROOT)),
        "duration_seconds": round(time.perf_counter() - started, 3),
        "generated_at": datetime.now(UTC).isoformat(),
        "counts": dict(counters),
        "phase_seconds": {key: round(value, 3) for key, value in phase_seconds.items()},
        "semantic_sha256": _semantic_digest(changes),
        "manifests": {sid: len(items) for sid, items in manifests.items()},
        "changes": changes,
        "exceptions": exceptions,
    }
    _json(OUT / ("factory-prepared.json" if changes else "factory-rescan.json"), result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("status", "duration_seconds", "counts", "semantic_sha256", "manifests")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare", action="store_true", help="Read-only review preparation (default)"
    )
    parser.parse_args()
    prepare()
