"""Build fact-level claims from already verified factory rows and audited cache.

One cached annual brochure is authenticated once for all of its previously
published exact-scoped variants. This never derives a mechanical value from an
EPA candidate, joins independent brochure option lists, or copies source text.
The generated plan is read-only until the existing claim applier is invoked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

from build_commercial_fact_overlay_batch import (
    AZ_RIGHTS_REFERENCE,
    RIGHTS_DATE,
    RIGHTS_REFERENCE,
    configuration_keys,
    document_kind,
    fact,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW = (
    ROOT
    / "deliverables/VerifiedData/commercial-manufacturer-drivetrain-01"
    / "factory-agent-review-remaining.jsonl"
)
PRIOR = (
    ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01/factory-fact-claims-dry-run.jsonl"
)
AUDIT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02/document-audit.json"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02"
REQUIRED = ("powertrain", "fuel", "engine_displacement", "transmission_description", "drivetrain")
IDENTITY = ("make", "model", "model_year", "original_market")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _local_blob_valid(sha: str) -> bool:
    path = ROOT / ".localdata" / "raw" / sha
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == sha


def build(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    review = read_jsonl(REVIEW)
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    audited = {
        (d["sha256"], d["url"], d["make"], d["model"], d["model_year"]): d
        for d in audit["documents"]
    }
    prior = defaultdict(dict)
    for claim in read_jsonl(PRIOR):
        prior[claim["catalog_key"]][claim["fact_name"]] = claim
    wanted = {r["catalog_key"] for r in review}
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    variants = {}
    for variant_id, key, specs in db.execute(
        "SELECT id,catalog_key,specifications FROM vehicle_variants "
        "WHERE published_revision_id IS NOT NULL AND is_demo=0"
    ):
        if key in wanted:
            variants[key] = (variant_id, json.loads(specs)["catalog"])
    claims = []
    resolved = []
    held = []
    groups = defaultdict(list)
    checked_blobs = {}
    for row in review:
        key = row["catalog_key"]
        item = variants.get(key)
        if not item:
            held.append({**row, "overlay02_reason": "VARIANT_NOT_PUBLISHED"})
            continue
        variant_id, catalog = item
        if (catalog.get("verification_gate") or {}).get("state") != "VERIFIED_SCOPED":
            held.append({**row, "overlay02_reason": "FACTORY_VERIFICATION_NOT_SCOPED"})
            continue
        if catalog.get("original_market") != "US" or not key.startswith("factory-"):
            held.append({**row, "overlay02_reason": "NOT_US_FACTORY"})
            continue
        names = list(REQUIRED)
        engine_name = "engine_description" if fact(catalog, "engine_description") else "engine_code"
        names.append(engine_name)
        refs = []
        for name in names:
            entry = fact(catalog, name)
            refs.append(entry.get("documentary_source") or {})
        if not all(ref.get("registry_id") == catalog.get("source_registry_id") for ref in refs):
            held.append({**row, "overlay02_reason": "MANDATORY_FACT_USES_OTHER_SOURCE"})
            continue
        if len({(ref.get("url"), ref.get("sha256"), ref.get("document_id")) for ref in refs}) != 1:
            held.append({**row, "overlay02_reason": "MANDATORY_FACTS_SPLIT_ACROSS_DOCUMENTS"})
            continue
        ref = refs[0]
        if urlparse(ref.get("url") or "").hostname not in {
            "www.auto-brochures.com", "pictures.dealer.com", "www.prnewswire.com"
        }:
            held.append({**row, "overlay02_reason": "OTHER_HOST_REQUIRES_SEPARATE_REVIEW"})
            continue
        group_id = (
            ref["sha256"],
            ref["url"],
            catalog["make"],
            catalog["model"],
            catalog["model_year"],
        )
        document = audited.get(group_id)
        if (
            not document
            or not document.get("machine_authenticity_pass")
            or key not in document["catalog_keys"]
        ):
            held.append({**row, "overlay02_reason": "DOCUMENT_AUTHENTICITY_NOT_CLEARED"})
            continue
        if ref["sha256"] not in checked_blobs:
            checked_blobs[ref["sha256"]] = _local_blob_valid(ref["sha256"])
        if not checked_blobs[ref["sha256"]]:
            held.append({**row, "overlay02_reason": "CACHE_HASH_MISMATCH"})
            continue
        if not all(
            r.get("make") == catalog["make"]
            and r.get("model") == catalog["model"]
            and r.get("market") == "US"
            and (
                r.get("model_year") == catalog["model_year"]
                or (
                    isinstance(r.get("model_year_from"), int)
                    and isinstance(r.get("model_year_to"), int)
                    and r["model_year_from"] <= catalog["model_year"] <= r["model_year_to"]
                )
            )
            for r in refs
        ):
            held.append({**row, "overlay02_reason": "REFERENCE_APPLICABILITY_MISMATCH"})
            continue
        source_record_ids = {fact(catalog, name).get("source_id") for name in names}
        if len(source_record_ids) != 1 or None in source_record_ids:
            held.append({**row, "overlay02_reason": "SOURCE_RECORD_SPLIT"})
            continue
        source_record_id = next(iter(source_record_ids))
        source_record = db.execute(
            "SELECT url FROM source_records WHERE id=?", (source_record_id,)
        ).fetchone()
        if not source_record or source_record[0] != ref["url"]:
            held.append({**row, "overlay02_reason": "SOURCE_RECORD_URL_MISMATCH"})
            continue
        config = configuration_keys(catalog)
        if not all(config.values()):
            held.append({**row, "overlay02_reason": "INCOMPLETE_EXACT_CONFIGURATION_KEY"})
            continue
        row_claims = []
        for name, old in prior[key].items():
            entry = fact(catalog, name)
            doc_ref = entry.get("documentary_source") or {}
            if (
                not entry
                or old.get("value") != entry["value"]
                or doc_ref.get("url") != ref["url"]
                or doc_ref.get("sha256") != ref["sha256"]
                or doc_ref.get("registry_id") != catalog["source_registry_id"]
                or doc_ref.get("make") != catalog["make"]
                or doc_ref.get("model") != catalog["model"]
                or doc_ref.get("market") != "US"
                or not (
                    doc_ref.get("model_year") == catalog["model_year"]
                    or (
                        isinstance(doc_ref.get("model_year_from"), int)
                        and isinstance(doc_ref.get("model_year_to"), int)
                        and doc_ref["model_year_from"]
                        <= catalog["model_year"]
                        <= doc_ref["model_year_to"]
                    )
                )
                or entry.get("source_id") != source_record_id
            ):
                continue
            claim = json.loads(json.dumps(old))
            claim["reuse_status"] = "COMMERCIAL_OK"
            claim["rights_basis"] = "FACTUAL_EXTRACTION"
            claim["rights_reference"] = RIGHTS_REFERENCE
            claim["rights_checked_at"] = RIGHTS_DATE
            claim["evidence_scope"].update(
                source_authenticity="REVIEWED_MIRROR",
                extraction_scope="ISOLATED_FACT",
                source_document_kind=document_kind(ref["url"]),
                reviewer="Codex cached-document group review 2026-09-28",
                authenticity_review_note=(
                    "Exact SHA256 cached manufacturer-issued document; brand, model, "
                    "MY and issuer/mark pass document audit; prior published "
                    "VERIFIED_SCOPED field/variant locator retained. "
                    "Facts only; no text/image licence."
                ),
                az_rights_reference=AZ_RIGHTS_REFERENCE,
                source_record_id=source_record_id,
                configuration_keys=config,
            )
            row_claims.append(claim)
        if not all(name in {c["fact_name"] for c in row_claims} for name in names):
            held.append({**row, "overlay02_reason": "MISSING_PREVIOUSLY_EXTRACTED_MANDATORY_FACT"})
            continue
        anchor = row_claims[0]
        for name in IDENTITY:
            claim = json.loads(json.dumps(anchor))
            claim["fact_name"] = name
            claim["value"] = catalog[name]
            claim["unit"] = None
            claim["locator"] = f"mirror-group-02:document:{ref['document_id']};fact:{name}"
            row_claims.append(claim)
        claims.extend(row_claims)
        resolved.append(
            {
                "catalog_key": key,
                "make": catalog["make"],
                "model": catalog["model"],
                "generation": catalog.get("generation"),
                "model_year": catalog["model_year"],
                "engine": fact(catalog, engine_name).get("value"),
                "transmission": fact(catalog, "transmission_description").get("value"),
                "drivetrain": fact(catalog, "drivetrain").get("value"),
                "document_sha256": ref["sha256"],
                "document_url": ref["url"],
                "facts_promoted": [c["fact_name"] for c in row_claims],
            }
        )
        groups[group_id].append(key)
    out.mkdir(parents=True, exist_ok=True)
    (out / "mirror-fact-claims.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in claims),
        encoding="utf-8",
    )
    (out / "mirror-resolved.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in resolved),
        encoding="utf-8",
    )
    (out / "manufacturer-review-remaining.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in held),
        encoding="utf-8",
    )
    summary = {
        "input_rows": len(review),
        "mirror_rows_resolved": len(resolved),
        "mirror_claims": len(claims),
        "document_groups_resolved": len(groups),
        "remaining_rows": len(held),
        "held_reasons": dict(Counter(x["overlay02_reason"] for x in held)),
    }
    (out / "mirror-batch-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.out), ensure_ascii=False, indent=2))
