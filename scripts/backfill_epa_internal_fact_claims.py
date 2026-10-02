"""Index existing EPA facts as INTERNAL_RESEARCH without changing catalogue rows.

This is a local SQLite metadata backfill over previously published source rows.
It does not download data, re-publish configurations, or confer commercial rights.
The production query reads only independently COMMERCIAL_OK claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

from catalog_writer_lock import catalog_writer_lock

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "autoexpert.db"
REPORT = (
    ROOT
    / "deliverables/VerifiedData/commercial-fact-overlay-01/epa-internal-claims-summary.json"
)
FALLBACK_URL = "https://www.fueleconomy.gov/feg/download.shtml"
IDENTITY = ("make", "model", "model_year", "original_market")


def scalar(value: object) -> bool:
    return (
        value is not None
        and not isinstance(value, (dict, list, bool))
        and bool(str(value).strip())
        and len(str(value)) <= 120
    )


def https_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and parsed.hostname else None


def source_for(fact: dict, catalog: dict, known_sources: set[str]) -> tuple[str, str]:
    documentary = fact.get("documentary_source") or {}
    registry_id = documentary.get("registry_id")
    if registry_id in known_sources:
        return registry_id, https_url(documentary.get("url")) or FALLBACK_URL
    return "epa", https_url(catalog.get("source_url")) or FALLBACK_URL


def research_scope(catalog: dict, fact: dict | None = None) -> dict:
    provenance = catalog.get("source_provenance") or {}
    scope = {
        "make": catalog.get("make"),
        "model": catalog.get("model"),
        "model_year": catalog.get("model_year"),
        "original_market": catalog.get("original_market"),
        "granularity": "EXACT_CONFIGURATION",
        "catalog_revision_id": catalog.get("revision_id"),
        "dataset_sha256": provenance.get("dataset_sha256"),
        # The original revision retains every contributing ID. Claims only need a
        # stable pointer to that revision; repeating ID arrays for every fact
        # would needlessly multiply local storage.
        "configuration_keys": {
            name: (catalog.get("facts") or {}).get(name, {}).get("value")
            for name in (
                "powertrain", "engine_displacement", "engine_description",
                "transmission_description", "drivetrain",
            )
        },
    }
    if fact:
        scope["source_record_id"] = fact.get("source_id")
        scope["source_locator_sha256"] = hashlib.sha256(
            str(fact.get("locator") or "").encode("utf-8")
        ).hexdigest()
    return scope


def claim_row(
    variant_id: str, catalog: dict, name: str, value: object, source_id: str,
    source_url: str, scope: dict, unit: str | None, now: str,
) -> tuple:
    locator = f"legacy-research:{catalog.get('revision_id') or 'unknown'}:{name}"
    claim_id = str(uuid5(NAMESPACE_URL, f"{variant_id}|{name}|{source_id}|{locator}"))
    return (
        claim_id, now, now, variant_id, name,
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        source_id, json.dumps(scope, ensure_ascii=False, separators=(",", ":")),
        "INTERNAL_RESEARCH", source_url, locator, None, None, None, unit,
    )


def run(db_path: Path = DB, report_path: Path = REPORT) -> dict:
    now = datetime.now(UTC).isoformat()
    counts: Counter[str] = Counter()
    with catalog_writer_lock(), sqlite3.connect(db_path) as db:
        db.execute("PRAGMA busy_timeout=30000")
        known_sources = {row[0] for row in db.execute("SELECT id FROM knowledge_sources")}
        if "epa" not in known_sources:
            raise RuntimeError("EPA_SOURCE_REGISTRY_MISSING")
        if not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='commercial_fact_claims'"
        ).fetchone():
            raise RuntimeError("COMMERCIAL_FACT_MIGRATION_REQUIRED")
        before = db.execute(
            "SELECT COUNT(*) FROM commercial_fact_claims WHERE reuse_status='INTERNAL_RESEARCH'"
        ).fetchone()[0]
        insert_sql = (
            "INSERT OR IGNORE INTO commercial_fact_claims "
            "(id,created_at,updated_at,variant_id,fact_name,value,source_id,"
            "evidence_scope,reuse_status,source_url,locator,rights_basis,"
            "rights_reference,rights_checked_at,unit) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        )
        batch: list[tuple] = []
        for variant_id, raw in db.execute(
            "SELECT id,specifications FROM vehicle_variants "
            "WHERE published_revision_id IS NOT NULL AND is_demo=0 "
            "AND json_extract(specifications,'$.catalog.source_registry_id')='epa'"
        ):
            catalog = (json.loads(raw or "{}")).get("catalog") or {}
            counts["epa_variants_considered"] += 1
            for name in IDENTITY:
                value = catalog.get(name)
                if not scalar(value):
                    counts["identity_values_skipped"] += 1
                    continue
                batch.append(claim_row(
                    variant_id, catalog, name, value, "epa",
                    https_url(catalog.get("source_url")) or FALLBACK_URL,
                    research_scope(catalog), None, now,
                ))
                counts["identity_claims_considered"] += 1
            for name, fact in (catalog.get("facts") or {}).items():
                if not isinstance(fact, dict) or fact.get("status") != "CONFIRMED":
                    continue
                value = fact.get("value")
                if not scalar(value) or len(name) > 100:
                    counts["fact_values_skipped"] += 1
                    continue
                source_id, source_url = source_for(fact, catalog, known_sources)
                batch.append(claim_row(
                    variant_id, catalog, name, value, source_id, source_url,
                    research_scope(catalog, fact), fact.get("unit"), now,
                ))
                counts["fact_claims_considered"] += 1
                if len(batch) >= 2000:
                    db.executemany(insert_sql, batch)
                    batch.clear()
        if batch:
            db.executemany(insert_sql, batch)
        after = db.execute(
            "SELECT COUNT(*) FROM commercial_fact_claims WHERE reuse_status='INTERNAL_RESEARCH'"
        ).fetchone()[0]
        counts["internal_claims_before"] = before
        counts["internal_claims_after"] = after
        counts["internal_claims_inserted"] = after - before
        db.commit()
    summary = {
        **dict(counts),
        "generated_at_utc": now,
        "rights_status": "INTERNAL_RESEARCH",
        "vehicle_catalog_rows_modified": 0,
        "new_network_requests": 0,
        "commercial_ok_claims_created": 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(run(args.db, args.report), ensure_ascii=False, indent=2))
