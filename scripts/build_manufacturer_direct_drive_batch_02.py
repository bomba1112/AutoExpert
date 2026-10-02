"""Apply reviewed annual official drive matrices to existing exact factory rows.

The manifest supplies independent manufacturer assertions. EPA values are only
compared after selecting a matching manufacturer variant; never used to choose
a claim. This leaves all non-matching rows in review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

from build_commercial_fact_overlay_batch import (
    AZ_RIGHTS_REFERENCE,
    RIGHTS_DATE,
    RIGHTS_REFERENCE,
    configuration_keys,
    document_kind,
    fact,
    publisher_host,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/commercial-manufacturer-drive-02.json"
REVIEW = (
    ROOT
    / "deliverables/VerifiedData/commercial-manufacturer-drivetrain-01"
    / "factory-agent-review-remaining.jsonl"
)
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]


def build(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = {(g["make"], g["model"], g["model_year"]): g for g in manifest["groups"]}
    if len(groups) != len(manifest["groups"]):
        raise ValueError("DUPLICATE_DOCUMENT_GROUP")
    for group in groups.values():
        path = ROOT / ".localdata" / "raw" / group["sha256"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != group["sha256"]:
            raise ValueError("MANUFACTURER_CACHE_HASH_MISMATCH")
        if not publisher_host("factory-kia-us", group["url"]):
            raise ValueError("NOT_OFFICIAL_HOST")
    review = [r for r in read_jsonl(REVIEW) if r["reason_codes"] == ["MISSING_SAFE_DRIVETRAIN"]]
    keys = {r["catalog_key"] for r in review}
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    variants = {}
    for variant_id, key, specs in db.execute(
        "SELECT id,catalog_key,specifications FROM vehicle_variants "
        "WHERE published_revision_id IS NOT NULL AND is_demo=0"
    ):
        if key in keys:
            variants[key] = (variant_id, json.loads(specs)["catalog"])
    claims = []
    resolved = []
    held = []
    used_variants = Counter()
    for row in review:
        key = row["catalog_key"]
        item = variants.get(key)
        if not item:
            held.append({**row, "overlay02_reason": "VARIANT_MISSING"})
            continue
        variant_id, catalog = item
        group = groups.get((catalog["make"], catalog["model"], catalog["model_year"]))
        if not group:
            held.append({**row, "overlay02_reason": "NO_REVIEWED_MATRIX"})
            continue
        engine = fact(catalog, "engine_description").get("value")
        transmission = fact(catalog, "transmission_description").get("value")
        expected_drive = fact(catalog, "drivetrain").get("value")
        matches = [
            variant
            for variant in group["variants"]
            if variant["engine"] == engine
            and variant["transmission"] == transmission
            and expected_drive in variant["drives"]
        ]
        if len(matches) != 1:
            held.append({**row, "overlay02_reason": "OFFICIAL_VARIANT_NOT_UNIQUE"})
            continue
        assertion = matches[0]
        ref = fact(catalog, "transmission_description").get("documentary_source") or {}
        drive_ref = fact(catalog, "drivetrain").get("documentary_source") or {}
        if (
            ref.get("url") != group["url"]
            or ref.get("sha256") != group["sha256"]
            or ref.get("registry_id") != catalog.get("source_registry_id")
            or drive_ref.get("registry_id") != "epa"
            or ref.get("market") != "US"
            or not (
                ref.get("model_year") == catalog["model_year"]
                or (
                    isinstance(ref.get("model_year_from"), int)
                    and isinstance(ref.get("model_year_to"), int)
                    and ref["model_year_from"] <= catalog["model_year"] <= ref["model_year_to"]
                )
            )
        ):
            held.append({**row, "overlay02_reason": "SOURCE_APPLICABILITY_MISMATCH"})
            continue
        source_record_id = fact(catalog, "transmission_description").get("source_id")
        record = db.execute(
            "SELECT url FROM source_records WHERE id=?", (source_record_id,)
        ).fetchone()
        if not record or record[0] != group["url"]:
            held.append({**row, "overlay02_reason": "SOURCE_RECORD_MISMATCH"})
            continue
        existing = db.execute(
            "SELECT value,evidence_scope,source_url FROM commercial_fact_claims "
            "WHERE variant_id=? AND fact_name='transmission_description' "
            "AND reuse_status='COMMERCIAL_OK' LIMIT 1",
            (variant_id,),
        ).fetchone()
        if not existing or json.loads(existing[0]) != transmission or existing[2] != group["url"]:
            held.append({**row, "overlay02_reason": "NO_SAFE_TRANSMISSION_ANCHOR"})
            continue
        config = configuration_keys(catalog)
        if config.get("drivetrain") != expected_drive or not all(config.values()):
            held.append({**row, "overlay02_reason": "EXACT_KEY_INCOMPLETE"})
            continue
        scope = json.loads(existing[1])
        scope.update(
            configuration_keys=config,
            source_record_id=source_record_id,
            source_authenticity="OFFICIAL_PUBLISHER",
            extraction_scope="ISOLATED_FACT",
            source_document_kind=document_kind(group["url"]) or "SPEC_SHEET",
            az_rights_reference=AZ_RIGHTS_REFERENCE,
        )
        claim = {
            "variant_id": variant_id,
            "catalog_key": key,
            "fact_name": "drivetrain",
            "value": expected_drive,
            "source_id": catalog["source_registry_id"],
            "evidence_scope": scope,
            "reuse_status": "COMMERCIAL_OK",
            "source_url": group["url"],
            "locator": (
                f"manufacturer-drive-02:document:{ref['document_id']};"
                f"variant:{assertion['official_variant']};drive:{expected_drive}"
            ),
            "rights_basis": "FACTUAL_EXTRACTION",
            "rights_reference": RIGHTS_REFERENCE,
            "rights_checked_at": RIGHTS_DATE,
            "unit": None,
        }
        claims.append(claim)
        resolved.append(
            {
                "catalog_key": key,
                "make": catalog["make"],
                "model": catalog["model"],
                "generation": catalog.get("generation"),
                "model_year": catalog["model_year"],
                "engine": engine,
                "transmission": transmission,
                "drivetrain": expected_drive,
                "official_variant": assertion["official_variant"],
                "document_url": group["url"],
            }
        )
        used_variants[
            (
                catalog["make"],
                catalog["model"],
                catalog["model_year"],
                assertion["official_variant"],
                expected_drive,
            )
        ] += 1
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (
        ("direct-drive-claims.jsonl", claims),
        ("direct-drive-resolved.jsonl", resolved),
        ("direct-drive-held.jsonl", held),
    ):
        (out / name).write_text(
            "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
    result = {
        "direct_drive_input_rows": len(review),
        "direct_drive_resolved_rows": len(resolved),
        "direct_drive_remaining_rows": len(held),
        "official_document_groups_used": len(
            {(r["make"], r["model"], r["model_year"]) for r in resolved}
        ),
        "held_reasons": dict(Counter(x["overlay02_reason"] for x in held)),
    }
    (out / "direct-drive-summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.out), ensure_ascii=False, indent=2))
