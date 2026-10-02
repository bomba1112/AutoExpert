"""Build exact fact claims for independently reviewed annual drive groups.

The manifest contains the manufacturer's drive assertion. EPA is only checked
for agreement with that assertion and never supplies the promoted value.
Existing publication and commercial eligibility rules remain unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from audit_manufacturer_cache_02 import audit_document
from build_commercial_fact_overlay_batch import (
    AZ_RIGHTS_REFERENCE,
    RIGHTS_DATE,
    RIGHTS_REFERENCE,
    configuration_keys,
    document_kind,
    fact,
    publisher_host,
)
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/commercial-overlay-03-reviewed-drive-groups.json"
REMAINING = (
    ROOT
    / "deliverables/VerifiedData/commercial-fact-overlay-02"
    / "remaining-unresolved-manufacturer.jsonl"
)
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03"
REQUIRED = ("powertrain", "fuel", "engine_displacement", "transmission_description")
IDENTITY = ("make", "model", "model_year", "original_market")


def jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
        encoding="utf-8",
    )


def build(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    groups = json.loads(MANIFEST.read_text(encoding="utf-8"))["groups"]
    group_index = {(g["make"], g["model"], g["model_year"]): g for g in groups}
    if len(group_index) != len(groups):
        raise ValueError("DUPLICATE_REVIEWED_GROUP")
    remaining = jsonl(REMAINING)
    by_group = defaultdict(list)
    for row in remaining:
        key = row["make"], row["model"], row["model_year"]
        if key in group_index:
            by_group[key].append(row)
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    claims: list[dict] = []
    resolved: list[dict] = []
    audits: list[dict] = []
    for key, group in group_index.items():
        rows = by_group[key]
        suffix_drives = group.get("catalog_key_suffixes") or {}
        if suffix_drives:
            rows = [
                row
                for row in rows
                if any(row["catalog_key"].endswith(suffix) for suffix in suffix_drives)
            ]
            if (
                len(rows) != group["expected_rows"]
                or any(
                    sum(row["catalog_key"].endswith(suffix) for suffix in suffix_drives) != 1
                    for row in rows
                )
                or any(
                    not any(row["catalog_key"].endswith(suffix) for row in rows)
                    for suffix in suffix_drives
                )
            ):
                raise ValueError(("REVIEWED_SUFFIX_SCOPE", key))
        if len(rows) != group["expected_rows"]:
            raise ValueError(("GROUP_SIZE_CHANGED", key, len(rows)))
        path = ROOT / ".localdata/raw" / group["sha256"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != group["sha256"]:
            raise ValueError(("DOCUMENT_HASH_MISMATCH", key))
        audit = audit_document(
            path,
            {
                "sha256": group["sha256"],
                "url": group["url"],
                "make": group["make"],
                "model": group["model"],
                "model_year": group["model_year"],
                "row_count": len(rows),
            },
        )
        audits.append(audit)
        if group["source_type"] == "REVIEWED_MIRROR" and not audit["machine_authenticity_pass"]:
            manual = group.get("manual_authenticity") or {}
            if key != ("Jeep", "Compass", 2018) or not manual:
                raise ValueError(("MIRROR_AUTHENTICITY_FAILED", key))
            header = " ".join(
                (PdfReader(str(path)).pages[0].extract_text() or "").split()
            ).casefold()
            if (
                manual["required_header"].casefold() not in header
                or manual["required_title"].casefold() not in header
                or not all(
                    audit[field]
                    for field in (
                        "sha256_matches",
                        "brand_in_document",
                        "model_in_document",
                        "year_in_document",
                        "us_mark_in_document",
                    )
                )
            ):
                raise ValueError(("MANUAL_AUTHENTICITY_CROSSCHECK_FAILED", key))
            audit["manual_authenticity_pass"] = True
            audit["manual_authenticity_crosscheck_url"] = manual["crosscheck_url"]
        for row in rows:
            reviewed_drive = (
                next(
                    (
                        drive
                        for suffix, drive in suffix_drives.items()
                        if row["catalog_key"].endswith(suffix)
                    ),
                    None,
                )
                if suffix_drives
                else group["drivetrain"]
            )
            if reviewed_drive is None:
                raise ValueError(("REVIEWED_DRIVE_NOT_FOUND", row["catalog_key"]))
            record = db.execute(
                "SELECT id,catalog_key,specifications FROM vehicle_variants WHERE catalog_key=? "
                "AND published_revision_id IS NOT NULL AND is_demo=0",
                (row["catalog_key"],),
            ).fetchone()
            if record is None:
                raise ValueError(("UNPUBLISHED_ROW", row["catalog_key"]))
            catalog = json.loads(record["specifications"])["catalog"]
            if (
                (catalog["make"], catalog["model"], catalog["model_year"]) != key
                or catalog.get("original_market") != "US"
                or (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED"
                or not row["catalog_key"].startswith("factory-")
                or fact(catalog, "drivetrain").get("value") != reviewed_drive
            ):
                raise ValueError(("CANDIDATE_SCOPE_CONFLICT", row["catalog_key"]))
            source_id = catalog["source_registry_id"]
            official = group["source_type"] == "OFFICIAL_PUBLISHER"
            if publisher_host(source_id, group["url"]) != official:
                raise ValueError(("PUBLISHER_HOST_CLASSIFICATION", key))
            names = list(REQUIRED)
            engine = "engine_description" if fact(catalog, "engine_description") else "engine_code"
            names.append(engine)
            refs = {name: (fact(catalog, name).get("documentary_source") or {}) for name in names}
            drive_anchor = refs["transmission_description"]
            if (
                any(
                    ref.get("registry_id") != source_id
                    or ref.get("make") != catalog["make"]
                    or ref.get("model") != catalog["model"]
                    or ref.get("market") != "US"
                    or not (
                        ref.get("model_year") == catalog["model_year"]
                        or (
                            isinstance(ref.get("model_year_from"), int)
                            and isinstance(ref.get("model_year_to"), int)
                            and ref["model_year_from"]
                            <= catalog["model_year"]
                            <= ref["model_year_to"]
                        )
                    )
                    for ref in refs.values()
                )
                or drive_anchor.get("url") != group["url"]
                or drive_anchor.get("sha256") != group["sha256"]
            ):
                raise ValueError(("MANDATORY_MANUFACTURER_SCOPE_SPLIT", row["catalog_key"]))
            if not official and any(
                ref.get("url") != group["url"] or ref.get("sha256") != group["sha256"]
                for ref in refs.values()
            ):
                raise ValueError(("MIRROR_MANDATORY_SOURCE_SPLIT", row["catalog_key"]))
            if not official and len({fact(catalog, name).get("source_id") for name in names}) != 1:
                raise ValueError(("SOURCE_RECORD_SPLIT", row["catalog_key"]))
            source_record_id = fact(catalog, "transmission_description").get("source_id")
            if not source_record_id:
                raise ValueError(("TRANSMISSION_SOURCE_RECORD_MISSING", row["catalog_key"]))
            source_record = db.execute(
                "SELECT url FROM source_records WHERE id=?", (source_record_id,)
            ).fetchone()
            if source_record is None or source_record["url"] != group["url"]:
                raise ValueError(("SOURCE_RECORD_URL", row["catalog_key"]))
            config = configuration_keys(catalog)
            if config["drivetrain"] != reviewed_drive or not all(config.values()):
                raise ValueError(("EXACT_KEY_INCOMPLETE", row["catalog_key"]))
            scope = {
                "make": catalog["make"],
                "model": catalog["model"],
                "model_year": catalog["model_year"],
                "original_market": "US",
                "granularity": "EXACT_CONFIGURATION",
                "configuration_keys": config,
                "source_record_id": source_record_id,
                "source_authenticity": group["source_type"],
                "extraction_scope": "ISOLATED_FACT",
                "source_document_kind": document_kind(group["url"]) or "SPEC_SHEET",
                "az_rights_reference": AZ_RIGHTS_REFERENCE,
            }
            if not official:
                scope["reviewer"] = "Codex annual cached-document group review 2026-09-28"
                scope["authenticity_review_note"] = (
                    (group.get("manual_authenticity") or {}).get("note")
                    or "Matching SHA256, annual model identity, publisher mark and US scope; "
                    "previous VERIFIED_SCOPED field locators retained; factual values only."
                )
            prior = {
                r["fact_name"]: r
                for r in db.execute(
                    "SELECT fact_name,value,reuse_status,source_url FROM commercial_fact_claims "
                    "WHERE variant_id=? AND source_id=?",
                    (record["id"], source_id),
                )
            }
            if official:
                if any(
                    name not in prior or prior[name]["reuse_status"] != "COMMERCIAL_OK"
                    for name in names
                ):
                    raise ValueError(("OFFICIAL_SAFE_ANCHOR_MISSING", row["catalog_key"]))
            else:
                if any(name not in prior for name in names):
                    raise ValueError(("PRIOR_FACT_MISSING", row["catalog_key"]))
                for name in [*names, *IDENTITY]:
                    value = catalog[name] if name in IDENTITY else fact(catalog, name)["value"]
                    claims.append(
                        {
                            "variant_id": record["id"],
                            "catalog_key": row["catalog_key"],
                            "fact_name": name,
                            "value": value,
                            "source_id": source_id,
                            "evidence_scope": scope,
                            "reuse_status": "COMMERCIAL_OK",
                            "source_url": group["url"],
                            "locator": (
                                f"overlay03:document:{refs[names[0]]['document_id']};fact:{name}"
                            ),
                            "rights_basis": "FACTUAL_EXTRACTION",
                            "rights_reference": RIGHTS_REFERENCE,
                            "rights_checked_at": RIGHTS_DATE,
                            "unit": fact(catalog, name).get("unit")
                            if name not in IDENTITY
                            else None,
                        }
                    )
            claims.append(
                {
                    "variant_id": record["id"],
                    "catalog_key": row["catalog_key"],
                    "fact_name": "drivetrain",
                    "value": reviewed_drive,
                    "source_id": source_id,
                    "evidence_scope": scope,
                    "reuse_status": "COMMERCIAL_OK",
                    "source_url": group["url"],
                    "locator": (
                        f"overlay03:document:{refs['transmission_description']['document_id']};"
                        f"drive:{reviewed_drive};year:{group['model_year']}"
                    ),
                    "rights_basis": "FACTUAL_EXTRACTION",
                    "rights_reference": RIGHTS_REFERENCE,
                    "rights_checked_at": RIGHTS_DATE,
                    "unit": None,
                }
            )
            resolved.append(
                {
                    "catalog_key": row["catalog_key"],
                    "make": catalog["make"],
                    "model": catalog["model"],
                    "generation": catalog.get("generation"),
                    "model_year": catalog["model_year"],
                    "engine": fact(catalog, engine)["value"],
                    "transmission": fact(catalog, "transmission_description")["value"],
                    "drivetrain": reviewed_drive,
                    "reviewed_source_url": group["url"],
                    "reviewed_locator": group["locator"],
                }
            )
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "reviewed-drive-claims.jsonl", claims)
    write_jsonl(out / "reviewed-drive-resolved.jsonl", resolved)
    (out / "reviewed-source-audit.json").write_text(
        json.dumps(audits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "groups_resolved": len(groups),
        "rows_resolved": len(resolved),
        "claims": len(claims),
        "by_make": dict(Counter(r["make"] for r in resolved)),
    }
    (out / "reviewed-drive-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.out), ensure_ascii=False, indent=2))
