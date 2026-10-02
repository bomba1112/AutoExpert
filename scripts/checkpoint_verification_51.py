"""Read-only, no-network audit of the frozen verification cohort and preservation baseline."""
# ruff: noqa: E402, E501

import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.models.research import ResearchJob
from app.schemas.catalog_verification import DocumentaryReference
from app.schemas.knowledge import CatalogRecord
from app.services.catalog_buyer import asset_for, coverage, projection, records
from app.services.catalog_verification import (
    FULL_SECTIONS,
    IDENTITY_FIELDS,
    check_reference,
    dossier_full,
    identity_verified,
)
from app.services.ownership_evidence import available
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/verification-51"
COHORT = ROOT / "data/manifests/us-51-verification-cohort.json"
BASELINE = ROOT / ".backups/before-verification-51-20260920T104242Z.sqlite3"


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def preservation(changed_ids):
    current = Path(get_settings().database_url.removeprefix("sqlite:///"))
    summary = {}
    with sqlite3.connect(BASELINE) as before, sqlite3.connect(current) as after:
        before.row_factory = after.row_factory = sqlite3.Row
        for (table,) in before.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            columns = [r[1] for r in before.execute(f'PRAGMA table_info("{table}")')]
            pk = [r[1] for r in before.execute(f'PRAGMA table_info("{table}")') if r[5]]
            if not pk:
                continue
            changed, removed, unexpected = 0, 0, 0
            for row in before.execute(f'SELECT * FROM "{table}"'):
                where = " AND ".join(f'"{col}"=?' for col in pk)
                new = after.execute(
                    f'SELECT * FROM "{table}" WHERE {where}', tuple(row[col] for col in pk)
                ).fetchone()
                if new is None:
                    removed += 1
                    continue
                diff = {col for col in columns if row[col] != new[col]}
                if not diff:
                    continue
                changed += 1
                allowed = (
                    table == "vehicle_variants"
                    and row["id"] in changed_ids
                    and diff
                    <= {
                        "engine",
                        "engine_code",
                        "transmission",
                        "transmission_code",
                        "generation_id",
                        "published_revision_id",
                        "specification_source_id",
                        "specifications",
                        "updated_at",
                    }
                ) or (
                    table == "knowledge_sources"
                    and row["id"] in {"epa", "nhtsa-safety-batch"}
                    and diff <= {"config", "state", "updated_at"}
                )
                if not allowed:
                    unexpected += 1
            summary[table] = {
                "changed": changed,
                "removed": removed,
                "unexpected_changes": unexpected,
            }
        integrity = (
            after.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            and not after.execute("PRAGMA foreign_key_check").fetchall()
        )
        old_count = before.execute("SELECT count(*) FROM vehicle_variants").fetchone()[0]
        new_count = after.execute("SELECT count(*) FROM vehicle_variants").fetchone()[0]
        no_expansion = old_count == new_count
    return {
        "status": "PASS"
        if integrity
        and no_expansion
        and not any(r["removed"] or r["unexpected_changes"] for r in summary.values())
        else "FAIL",
        "integrity": integrity,
        "no_new_variants": no_expansion,
        "tables": summary,
    }


def main():
    cohort = json.loads(COHORT.read_text(encoding="utf-8"))["cohort"]
    if len(cohort) != 51:
        raise ValueError("FROZEN_COHORT_CHANGED")
    result, changed_ids, references = [], set(), 0
    with SessionLocal() as db:
        live = {v.id: (v, c) for v, c in records(db)}
        edits = json.loads((OUT / "factory-review-decisions.json").read_text(encoding="utf-8"))
        edited_keys = {(r["make"], r["model"], r["year"], r["external_key"]) for r in edits}
        for family in cohort:
            target = family["target_variant_ids"]
            configs = []
            for vid in target:
                if vid not in live:
                    raise ValueError("COHORT_VARIANT_NOT_AVAILABLE")
                v, c = live[vid]
                record = CatalogRecord.model_validate(
                    {k: v for k, v in c.items() if k in CatalogRecord.model_fields}
                    | {
                        "facts": {
                            k: {
                                a: b
                                for a, b in f.items()
                                if a not in {"source_id", "evidence_id", "retrieved_at"}
                            }
                            for k, f in c["facts"].items()
                        }
                    }
                )
                all_refs = [
                    f.documentary_source for f in record.facts.values() if f.documentary_source
                ]
                all_refs += [
                    ref for section in record.documentary_sections for ref in section.references
                ]
                if record.identity_verification:
                    all_refs += [
                        ref
                        for refs in record.identity_verification.field_evidence.values()
                        for ref in refs
                    ]
                for ref in all_refs:
                    check_reference(db, DocumentaryReference.model_validate(ref), record)
                    references += 1
                if (c["make"], c["model"], c["model_year"], c["external_key"]) in edited_keys:
                    changed_ids.add(vid)
                verified = identity_verified(c)
                own = available(db, variant_id=vid)
                kinds = Counter(r.kind for r in own if r.payload["variant_ids"])
                inputs = any(
                    c["facts"].get(k, {}).get("status") == "CONFIRMED"
                    for k in ("fuel_combined", "electricity_combined")
                )
                covered = {
                    s["key"]
                    for s in c.get("documentary_sections", [])
                    if s["status"] in {"EVIDENCED", "NOT_APPLICABLE"}
                }
                identity = {
                    key: "VERIFIED_SCOPED" if verified else "RESEARCH_ONLY"
                    for key in sorted(IDENTITY_FIELDS)
                }
                for key in ("engine_description", "transmission_description", "drivetrain"):
                    f = c["facts"].get(key, {})
                    if not verified and f.get("documentary_source"):
                        identity[key] = "DOCUMENTED_FIELD_PARTIAL_IDENTITY"
                configs.append(
                    {
                        "variant_id": vid,
                        "configuration": c["configuration"],
                        "external_key": c["external_key"],
                        "verified": verified,
                        "identity_fields": identity,
                        "applicability": (c.get("identity_verification") or {}).get(
                            "applicability"
                        ),
                        "generation": c.get("generation"),
                        "market": c["original_market"],
                        "model_year": c["model_year"],
                        "factory_fact_fields": [
                            k for k, f in c["facts"].items() if f.get("documentary_source")
                        ],
                        "dossier_full": dossier_full(c),
                        "dossier_sections": {
                            s["key"]: s["status"] for s in c.get("documentary_sections", [])
                        },
                        "dossier_gaps": sorted(FULL_SECTIONS - covered),
                        "ownership_records": dict(kinds),
                        "ownership_cost_status": "PARTIAL_CONDITIONAL_MAINTENANCE"
                        if kinds["MAINTENANCE"]
                        else "CONSUMPTION_INPUTS_ONLY"
                        if inputs
                        else "GAPS",
                        "ownership_cost_full": False,
                        "approved_image": asset_for(db, vid).get("state") == "APPROVED",
                    }
                )
                if verified:
                    for language in ("az", "ru"):
                        write(
                            OUT / f"bmw-{c['external_key']}-dossier-{language}.json",
                            projection(c, language).model_dump(mode="json"),
                        )
            job = db.get(ResearchJob, family["job_id"])
            all_verified = all(r["verified"] for r in configs)
            result.append(
                {
                    "make": family["make"],
                    "model": family["model"],
                    "year": family["year"],
                    "turbo_listing_count": None,
                    "market_distribution": None,
                    "local_priority_basis": "OWNER_SELECTION_NO_TURBO_INGESTION",
                    "us_variant_present": True,
                    "us_variant_basis": "PUBLISHED_US_EPA_CONFIGURATION",
                    "research_status": str(job.status),
                    "technical_source_coverage": [
                        {
                            k: s.get(k)
                            for k in (
                                "provider_id",
                                "capability",
                                "status",
                                "records_count",
                                "source_url",
                                "http_status",
                            )
                        }
                        for s in job.provider_steps
                    ],
                    "verification_status": "VERIFIED_FROZEN_YEAR_CONFIGURATIONS"
                    if all_verified
                    else "PARTIAL_FACTORY_FACTS"
                    if any(c["factory_fact_fields"] for c in configs)
                    else "RESEARCH_ONLY",
                    "all_generation_years_verified": False,
                    "dossier_status": "FULL"
                    if all(c["dossier_full"] for c in configs)
                    else "PARTIAL"
                    if any(c["dossier_sections"] for c in configs)
                    else "NOT_REVIEWED",
                    "configurations": configs,
                }
            )
        # No reviewed fitment or labor evidence exists yet. Do not silently turn input coverage into full TCO.
        if available(db, kind="FITMENT") or available(db, kind="LABOR"):
            raise ValueError("OWNERSHIP_COVERAGE_RULE_REVIEW_REQUIRED")
        counts = dict(
            families=51,
            verified_frozen_year_families=sum(
                r["verification_status"] == "VERIFIED_FROZEN_YEAR_CONFIGURATIONS" for r in result
            ),
            entire_generation_year_ranges_verified=0,
            verified_configurations=sum(c["verified"] for r in result for c in r["configurations"]),
            partial_factory_fact_families=sum(
                r["verification_status"] == "PARTIAL_FACTORY_FACTS" for r in result
            ),
            full_dossier_families=sum(r["dossier_status"] == "FULL" for r in result),
            partial_dossier_families=sum(r["dossier_status"] == "PARTIAL" for r in result),
            full_ownership_cost_families=0,
            conditional_maintenance_families=sum(
                any(c["ownership_records"].get("MAINTENANCE") for c in r["configurations"])
                for r in result
            ),
            approved_image_families=sum(
                all(c["approved_image"] for c in r["configurations"]) for r in result
            ),
            updated_existing_configurations=len(changed_ids),
        )
        published = coverage(db)
        # Count all published rows including hidden ones, so source revocation cannot disguise expansion.
        published["all_published_variant_rows"] = len(
            list(
                db.scalars(
                    select(VehicleVariant).where(VehicleVariant.published_revision_id.is_not(None))
                )
            )
        )
    baseline = json.loads((OUT / "ui-baseline.json").read_text())
    actual = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "apps/web_preview").rglob("*")
        if p.is_file()
    }
    audit = preservation(changed_ids)
    payload = {
        "at": datetime.now(UTC).isoformat(),
        "status": "PARTIAL_VERIFICATION_BATCH",
        "counts": counts,
        "counting_scope": "Every existing configuration at the frozen research model year must pass. This is NOT a certification of all generations, production years, trims or individual VINs.",
        "catalog": published,
        "document_references_checked": references,
        "ui_unchanged": baseline == actual,
        "historical_preservation": audit,
        "cohort": result,
        "new_models": 0,
        "new_variants": 0,
        "paid_calls": 0,
        "phone": "DEFERRED_BY_OWNER",
        "hetzner": "DEFERRED_BY_OWNER",
    }
    write(OUT / "coverage.json", payload)
    lines = [
        "# 51-family verification checkpoint",
        "",
        payload["counting_scope"],
        "",
        "Turbo counts/distribution remain unknown manual inputs. US presence below means an official US configuration, not measured local listings.",
        "",
        "| Make | Model | MY | Turbo count | Markets | US variant | Technical sources | Verification | Dossier | Ownership | Image |",
        "|---|---|---:|---|---|---|---|---|---|---|---|",
    ]
    for r in result:
        sources = "; ".join(
            f"{s['capability']}={s['records_count']}"
            if s["status"] == "COMPLETE"
            else f"{s['capability']}=unavailable"
            for s in r["technical_source_coverage"]
            if s["provider_id"] != "none"
        )
        own = (
            "conditional service only"
            if any(c["ownership_records"].get("MAINTENANCE") for c in r["configurations"])
            else "consumption inputs only"
        )
        lines.append(
            f"| {r['make']} | {r['model']} | {r['year']} | unknown | unknown | EPA US | {sources} | {r['verification_status']} | {r['dossier_status']} | {own} | none |"
        )
    (OUT / "family-checkpoint.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "counts": counts,
                "ui_unchanged": payload["ui_unchanged"],
                "preservation": audit["status"],
            }
        )
    )
    if not payload["ui_unchanged"] or audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
