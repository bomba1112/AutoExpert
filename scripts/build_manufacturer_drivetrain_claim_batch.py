"""Build an additive, review-locked manufacturer drivetrain claim plan.

The source catalogue and its EPA drivetrain observations remain unchanged.  The
12 annual publisher documents in the manifest were reviewed for exact drive
applicability; this builder only emits claims for their frozen 102 factory keys.
Its SQL connection is read-only.  Apply the resulting plan with
``apply_commercial_fact_overlay_batch.py --plan ... --apply``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
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
DEFAULT_DB = ROOT / "autoexpert.db"
DEFAULT_MANIFEST = ROOT / "data/manifests/commercial-manufacturer-drivetrain-01.json"
DEFAULT_REVIEW = (
    ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01/factory-agent-review.jsonl"
)
DEFAULT_PRIOR_PLAN = (
    ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01/factory-fact-claims-dry-run.jsonl"
)
DEFAULT_OUT = ROOT / "deliverables/VerifiedData/commercial-manufacturer-drivetrain-01"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def document_check(document: dict) -> None:
    path = (ROOT / document["cache_path"]).resolve()
    if not path.is_relative_to(ROOT / ".localdata"):
        raise ValueError("DOCUMENT_CACHE_OUTSIDE_LOCALDATA")
    if hashlib.sha256(path.read_bytes()).hexdigest() != document["sha256"]:
        raise ValueError(f"DOCUMENT_SHA_MISMATCH:{document['url']}")
    if not publisher_host(document["source_id"], document["url"]):
        raise ValueError(f"NON_PUBLISHER_HOST:{document['url']}")
    if document_kind(document["url"]) not in {"BROCHURE", "SPEC_SHEET", "PRESS_KIT"}:
        raise ValueError(f"DOCUMENT_KIND_UNRESOLVED:{document['url']}")


def _read_variants(db: sqlite3.Connection, keys: set[str]) -> dict[str, dict]:
    result = {}
    for variant_id, key, specs in db.execute(
        "SELECT id,catalog_key,specifications FROM vehicle_variants "
        "WHERE published_revision_id IS NOT NULL AND is_demo=0 "
        "AND json_extract(specifications,'$.catalog.original_market')='US'"
    ):
        if key in keys:
            result[key] = {"variant_id": variant_id, "catalog": json.loads(specs)["catalog"]}
    if result.keys() != keys:
        raise ValueError(f"MISSING_PUBLISHED_FACTORY_KEYS:{sorted(keys - result.keys())[:3]}")
    return result


def reviewed_drive_value(assertion: dict, candidate_value: str) -> str:
    """Return the per-key manufacturer assertion, using the candidate only for QA."""
    key = assertion["catalog_key"]
    if not all(
        assertion.get(name)
        for name in ("official_variant", "official_drive_term", "locator", "drivetrain")
    ):
        raise ValueError(f"INCOMPLETE_MANUFACTURER_ASSERTION:{key}")
    official_value = assertion["drivetrain"]
    if official_value not in {"FWD", "RWD", "AWD", "4WD"}:
        raise ValueError(f"INVALID_MANUFACTURER_DRIVE:{key}")
    if candidate_value != official_value:
        raise ValueError(f"EPA_CANDIDATE_CONFLICTS_WITH_MANUFACTURER:{key}")
    return official_value


def _drive_claim(
    db: sqlite3.Connection, document: dict, assertion: dict, variant: dict, prior: dict
) -> dict:
    key = assertion["catalog_key"]
    catalog = variant["catalog"]
    source_id = document["source_id"]
    if (
        (catalog["make"], catalog["model"], catalog["model_year"])
        != (document["make"], document["model"], document["model_year"])
        or catalog.get("source_registry_id") != source_id
        or catalog.get("original_market") != "US"
    ):
        raise ValueError(f"CATALOG_SCOPE_MISMATCH:{key}")
    transmission = fact(catalog, "transmission_description")
    drive = fact(catalog, "drivetrain")
    ref = transmission.get("documentary_source") or {}
    drive_ref = drive.get("documentary_source") or {}
    if (
        ref.get("registry_id") != source_id
        or ref.get("url") != document["url"]
        or ref.get("sha256") != document["sha256"]
        or ref.get("document_id") != document["document_id"]
        or drive_ref.get("registry_id") != "epa"
    ):
        raise ValueError(f"EXACT_DOCUMENT_OR_OLD_DRIVE_SOURCE_MISMATCH:{key}")
    source_record_id = transmission.get("source_id")
    source_record = db.execute(
        "SELECT url FROM source_records WHERE id=?", (source_record_id,)
    ).fetchone()
    if not source_record or source_record[0] != document["url"]:
        raise ValueError(f"SOURCE_RECORD_MISMATCH:{key}")
    # The value is a reviewed assertion transcribed from the exact annual
    # manufacturer matrix row. The EPA-backed catalogue value is a conflict
    # check only; it cannot select or change the commercial claim.
    drive_value = reviewed_drive_value(assertion, drive["value"])
    if drive_value not in document["drive_counts"]:
        raise ValueError(f"DRIVE_OUTSIDE_DOCUMENT_SCOPE:{key}")
    existing = prior.get("transmission_description")
    if (
        not existing
        or existing["reuse_status"] != "COMMERCIAL_OK"
        or existing["source_url"] != document["url"]
        or existing["evidence_scope"]["source_record_id"] != source_record_id
    ):
        raise ValueError(f"MISSING_SAFE_TRANSMISSION_ANCHOR:{key}")
    required = {
        "make",
        "model",
        "model_year",
        "original_market",
        "powertrain",
        "fuel",
        "engine_displacement",
        "transmission_description",
    }
    required.add("engine_description" if fact(catalog, "engine_description") else "engine_code")
    if any(prior.get(name, {}).get("reuse_status") != "COMMERCIAL_OK" for name in required):
        raise ValueError(f"OTHER_REQUIRED_FACT_NOT_SAFE:{key}")
    config = configuration_keys(catalog)
    if config["drivetrain"] != drive_value or not all(config.values()):
        raise ValueError(f"INCOMPLETE_CONFIGURATION_KEY:{key}")
    config["drivetrain"] = drive_value
    scope = dict(existing["evidence_scope"])
    scope.update(
        configuration_keys=config,
        source_record_id=source_record_id,
        source_authenticity="OFFICIAL_PUBLISHER",
        extraction_scope="ISOLATED_FACT",
        source_document_kind=document_kind(document["url"]),
        az_rights_reference=AZ_RIGHTS_REFERENCE,
    )
    return {
        "variant_id": variant["variant_id"],
        "catalog_key": key,
        "fact_name": "drivetrain",
        "value": drive_value,
        "source_id": source_id,
        "evidence_scope": scope,
        "reuse_status": "COMMERCIAL_OK",
        "source_url": document["url"],
        "locator": (
            f"manufacturer-drive:document:{document['document_id']};"
            f"variant:{assertion['official_variant']};"
            f"term:{assertion['official_drive_term']};{assertion['locator']}"
        ),
        "rights_basis": "FACTUAL_EXTRACTION",
        "rights_reference": RIGHTS_REFERENCE,
        "rights_checked_at": RIGHTS_DATE,
        "unit": None,
    }


def build_plan(
    db_path: Path = DEFAULT_DB,
    manifest_path: Path = DEFAULT_MANIFEST,
    review_path: Path = DEFAULT_REVIEW,
    prior_plan_path: Path = DEFAULT_PRIOR_PLAN,
) -> tuple[list[dict], dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = manifest["documents"]
    if len(documents) != 12:
        raise ValueError("DOCUMENT_BATCH_SCOPE_CHANGED")
    for document in documents:
        document_check(document)
    exceptions = [
        row for row in read_jsonl(review_path) if row["reason_codes"] == ["MISSING_SAFE_DRIVETRAIN"]
    ]
    by_scope = defaultdict(list)
    for row in exceptions:
        by_scope[(row["make"], row["model"], row["model_year"])].append(row["catalog_key"])
    selected = {}
    for document in documents:
        scope = (document["make"], document["model"], document["model_year"])
        rows = document["rows"]
        keys = sorted(row["catalog_key"] for row in rows)
        keyset_sha = hashlib.sha256("\n".join(keys).encode()).hexdigest()
        if (
            len(keys) != len(set(keys))
            or len(keys) != document["expected_rows"]
            or keyset_sha != document["keyset_sha256"]
            or not set(keys).issubset(set(by_scope[scope]))
            or any(key in selected for key in keys)
        ):
            raise ValueError(f"REVIEWED_KEYSET_CHANGED:{scope}")
        selected.update({row["catalog_key"]: (document, row) for row in rows})
    if len(selected) != 102:
        raise ValueError("FACTORY_BATCH_SCOPE_CHANGED")
    held = manifest["held_catalog_keys"]
    if len(held) != 1 or any(row["catalog_key"] in selected for row in held):
        raise ValueError("HELD_REVIEW_SCOPE_CHANGED")
    prior = defaultdict(dict)
    for claim in read_jsonl(prior_plan_path):
        if claim["catalog_key"] in selected:
            prior[claim["catalog_key"]][claim["fact_name"]] = claim
    uri = db_path.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        variants = _read_variants(db, set(selected))
        claims = []
        counts = defaultdict(Counter)
        for key in sorted(selected):
            document, assertion = selected[key]
            claim = _drive_claim(db, document, assertion, variants[key], prior[key])
            claims.append(claim)
            counts[(document["make"], document["model"], document["model_year"])][
                claim["value"]
            ] += 1
    for document in documents:
        scope = (document["make"], document["model"], document["model_year"])
        if dict(counts[scope]) != document["drive_counts"]:
            raise ValueError(f"DRIVE_MATRIX_SCOPE_CHANGED:{scope}")
    distinct = set()
    for claim in claims:
        scope = claim["evidence_scope"]
        keys = scope["configuration_keys"]
        distinct.add(
            (
                scope["make"].casefold(),
                scope["model"].casefold(),
                scope["model_year"],
                prior[claim["catalog_key"]]["powertrain"]["value"],
                keys["engine_displacement"],
                keys.get("engine_description") or keys.get("engine_code"),
                keys["transmission_description"],
                keys["drivetrain"],
            )
        )
    if len(distinct) != 45:
        raise ValueError(f"DISTINCT_CONFIGURATION_SCOPE_CHANGED:{len(distinct)}")
    summary = {
        "batch_id": manifest["batch_id"],
        "writes_to_application_database": False,
        "manufacturer_documents": len(documents),
        "manufacturer_drivetrain_claims": len(claims),
        "held_for_review": len(held),
        "distinct_mechanical_configurations": len(distinct),
        "all_source_ids": sorted({c["source_id"] for c in claims}),
        "epa_commercial_claims": sum(c["source_id"] == "epa" for c in claims),
        "reviewed_document_groups": [
            {
                "make": d["make"],
                "model": d["model"],
                "model_year": d["model_year"],
                "rows": d["expected_rows"],
                "drives": d["drive_counts"],
                "url": d["url"],
                "sha256": d["sha256"],
                "locator": d["locator"],
            }
            for d in documents
        ],
    }
    return claims, summary


def run(
    db_path: Path = DEFAULT_DB,
    manifest_path: Path = DEFAULT_MANIFEST,
    review_path: Path = DEFAULT_REVIEW,
    prior_plan_path: Path = DEFAULT_PRIOR_PLAN,
    out: Path = DEFAULT_OUT,
) -> dict:
    claims, summary = build_plan(db_path, manifest_path, review_path, prior_plan_path)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manufacturer-drivetrain-claims.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in claims),
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--prior-plan", type=Path, default=DEFAULT_PRIOR_PLAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.db, args.manifest, args.review, args.prior_plan, args.out),
            ensure_ascii=False,
            indent=2,
        )
    )
