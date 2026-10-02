"""Audit published batch coverage, full combination queries and preservation, offline."""

# ruff: noqa: E402, E501
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.catalog import VehicleGeneration, VehicleVariant
from app.models.knowledge_ops import RawDocument
from app.schemas.catalog_verification import DocumentaryReference
from app.schemas.knowledge import BuyerFilters
from app.services import catalog_buyer as buyer
from app.services.catalog_verification import (
    base_catalog_counts,
    base_catalog_ready,
    catalog_excluded,
    identity_verified,
    reference_years,
    us_catalog_ready,
)
from app.services.knowledge_import import private_path
from app.services.market_priority import policy
from catalog_checkpoint_report import build_report, write_tables
from sqlalchemy import select


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def additive_enrichment(before_spec, after_spec):
    """Previously confirmed values and scoped identity must survive enrichment."""
    old = json.loads(before_spec).get("catalog", {})
    new = json.loads(after_spec).get("catalog", {})
    for name in ("make", "model", "generation", "generation_code", "original_market", "model_year"):
        if old.get(name) != new.get(name):
            return False
    old_facts, new_facts = old.get("facts", {}), new.get("facts", {})
    for name, fact in old_facts.items():
        replacement = new_facts.get(name)
        if replacement is None:
            return False
        if fact.get("status") == "CONFIRMED" and any(
            fact.get(field) != replacement.get(field) for field in ("value", "unit", "status")
        ):
            return False
    return True


def preservation(changed_keys, baseline, enrichment_keys=frozenset()):
    current = Path(get_settings().database_url.removeprefix("sqlite:///"))
    summary = {}
    with sqlite3.connect(baseline) as before, sqlite3.connect(current) as after:
        before.row_factory = after.row_factory = sqlite3.Row
        for (table,) in before.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            info = list(before.execute(f'PRAGMA table_info("{table}")'))
            columns, pk = [r[1] for r in info], [r[1] for r in info if r[5]]
            if not pk:
                continue
            changed = removed = unexpected = 0
            for row in before.execute(f'SELECT * FROM "{table}"'):
                where = " AND ".join(f'"{col}"=?' for col in pk)
                new = after.execute(
                    f'SELECT * FROM "{table}" WHERE {where}', tuple(row[col] for col in pk)
                ).fetchone()
                if new is None:
                    removed += 1
                    continue
                diff = {col for col in columns if row[col] != new[col]}
                if diff:
                    changed += 1
                    allowed = (
                        table == "vehicle_variants"
                        and row["catalog_key"] in changed_keys
                        and diff
                        <= {
                            "engine",
                            "engine_code",
                            "body",
                            "transmission",
                            "transmission_code",
                            "generation_id",
                            "published_revision_id",
                            "specification_source_id",
                            "specifications",
                            "updated_at",
                        }
                    )
                    if table == "vehicle_variants" and row["catalog_key"] in enrichment_keys:
                        allowed = allowed or (
                            diff
                            <= {
                                "specification_source_id",
                                "specifications",
                                "updated_at",
                                "published_revision_id",
                            }
                            and additive_enrichment(row["specifications"], new["specifications"])
                        )
                    if table == "knowledge_sources" and (
                        row["id"] == "epa" or row["id"].startswith("factory-")
                    ):
                        old_config, new_config = (
                            json.loads(row["config"]),
                            json.loads(new["config"]),
                        )
                        config_changes = {
                            k
                            for k in old_config.keys() | new_config.keys()
                            if old_config.get(k) != new_config.get(k)
                        }
                        allowed = diff <= {"config", "updated_at"} and config_changes <= {
                            "last_successful_publication_at"
                        }
                    if not allowed:
                        unexpected += 1
            added = (
                after.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
                - before.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
                + removed
            )
            summary[table] = dict(
                changed=changed, removed=removed, unexpected_changes=unexpected, added=added
            )
        integrity = (
            after.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            and not after.execute("PRAGMA foreign_key_check").fetchall()
        )
    return {
        "status": "PASS"
        if integrity and not any(x["removed"] or x["unexpected_changes"] for x in summary.values())
        else "FAIL",
        "integrity": integrity,
        "tables": summary,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=policy()["active_catalog_manifest"])
    parser.add_argument(
        "--additional-manifest",
        action="append",
        default=None,
        help="Audit more published batches in this checkpoint without republishing records",
    )
    parser.add_argument("--baseline", help="JSON with database backup path and UI hashes")
    parser.add_argument(
        "--previous-coverage",
        help="Previous immutable batch coverage JSON for growth and seating audit",
    )
    parser.add_argument(
        "--checkpoint",
        help="Markdown checkpoint to refresh with the required complete tables first",
    )
    parser.add_argument(
        "--enrichment-manifest",
        action="append",
        default=[],
        help="Reviewed existing-variant manifests whose fact updates are additive",
    )
    args = parser.parse_args()
    if args.additional_manifest is None:
        args.additional_manifest = policy().get("active_catalog_additional_manifests", [])
    args.enrichment_manifest = list(
        dict.fromkeys(
            args.enrichment_manifest + policy().get("catalog_fact_correction_manifests", [])
        )
    )
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    out = ROOT / "deliverables/VerifiedData" / manifest["batch_id"]
    prepared = json.loads((out / "prepared.json").read_text(encoding="utf-8"))
    targets = {t["catalog_key"]: t for t in prepared["targets"]}
    batch_ids = {manifest["batch_id"]}
    for manifest_path in args.additional_manifest:
        additional_path = ROOT / manifest_path
        additional = json.loads(additional_path.read_text(encoding="utf-8"))
        additional_out = ROOT / "deliverables/VerifiedData" / additional["batch_id"]
        additional_prepared = json.loads(
            (additional_out / "prepared.json").read_text(encoding="utf-8")
        )
        publication = json.loads((additional_out / "publication.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(additional_path.read_bytes()).hexdigest()
        assert publication["state"] == "PUBLISHED"
        assert additional_prepared["manifest_sha256"] == publication["manifest_sha256"] == digest
        new_targets = {t["catalog_key"]: t for t in additional_prepared["targets"]}
        assert not targets.keys() & new_targets.keys(), "BATCH_TARGET_OVERLAP"
        targets.update(new_targets)
        batch_ids.add(additional["batch_id"])
        for family in additional["families"]:
            existing = next((f for f in manifest["families"] if f["id"] == family["id"]), None)
            if existing is None:
                manifest["families"].append(family)
            else:
                assert all(
                    existing[k] == family[k] for k in ("make", "model", "market", "generation_code")
                )
                existing["year_from"] = min(existing["year_from"], family["year_from"])
                existing["year_to"] = max(existing["year_to"], family["year_to"])
        for name in ("exclusions", "source_conflicts", "source_discrepancies", "research_holds"):
            manifest.setdefault(name, []).extend(additional.get(name, []))
    enrichment_keys = set()
    for manifest_path in args.enrichment_manifest:
        enrichment = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
        source_id = enrichment["source_id"]
        enrichment_keys.update(
            f"{source_id}:{record['external_key']}" for record in enrichment["records"]
        )
        metadata_path = (ROOT / manifest_path).with_suffix(".meta.json")
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            manifest.setdefault("source_conflicts", []).extend(metadata.get("source_conflicts", []))
    corrections = []
    for correction_path in policy().get("catalog_correction_manifests", []):
        correction = json.loads((ROOT / correction_path).read_text(encoding="utf-8"))
        if correction.get("parent_batch") not in batch_ids:
            continue
        correction_out = ROOT / "deliverables/VerifiedData" / correction["batch_id"]
        correction_prepared = json.loads(
            (correction_out / "prepared.json").read_text(encoding="utf-8")
        )
        correction_published = json.loads(
            (correction_out / "publication.json").read_text(encoding="utf-8")
        )
        assert correction_published["state"] == "PUBLISHED"
        assert (
            correction_prepared["manifest_sha256"]
            == hashlib.sha256((ROOT / correction_path).read_bytes()).hexdigest()
        )
        assert {t["catalog_key"] for t in correction_prepared["targets"]} <= targets.keys()
        targets.update({t["catalog_key"]: t for t in correction_prepared["targets"]})
        corrections.append(correction_path)
        manifest.setdefault("source_conflicts", []).extend(correction.get("source_conflicts", []))
        manifest["exclusions"].extend(correction.get("exclusions", []))
    query_results, family_rows, doc_checks = [], [], {}
    with SessionLocal() as db:
        live = buyer.records(db)
        variants = {
            v.catalog_key: v
            for v in db.scalars(
                select(VehicleVariant).where(
                    VehicleVariant.catalog_key.in_(set(targets) | enrichment_keys)
                )
            )
        }
        ready_rows = []
        for key, t in targets.items():
            v = variants[key]
            c = v.specifications["catalog"]
            if t["group_id"] == "EXCLUDED":
                assert catalog_excluded(c)
                assert key not in {x.catalog_key for x, _ in live}
                ref = c["facts"]["catalog_applicability"]["documentary_source"]
                doc = db.get(RawDocument, ref["document_id"])
                assert (
                    doc.sha256
                    == ref["sha256"]
                    == hashlib.sha256(private_path(doc.storage_key).read_bytes()).hexdigest()
                )
                assert doc.locator == ref["url"] and doc.source_id == ref["registry_id"]
                continue
            assert base_catalog_ready(c), key
            assert v.generation_id and db.get(VehicleGeneration, v.generation_id).code == (
                c["generation_code"] or c["generation"]
            ), key
            assert v.year_from == v.year_to == c["model_year"], key
            ready_rows.append((v, c))
            refs = [
                f["documentary_source"] for f in c["facts"].values() if f.get("documentary_source")
            ]
            required = {c["model_year"]}
            scope = c["identity_verification"].get("range_scope")
            if scope:
                required = set(range(scope["model_year_from"], scope["model_year_to"] + 1))
            for field, values in c["identity_verification"]["field_evidence"].items():
                assert required <= set().union(
                    *(reference_years(DocumentaryReference(**r)) for r in values)
                ), (key, field)
                refs.extend(values)
            for ref in refs:
                doc = db.get(RawDocument, ref["document_id"])
                assert (
                    doc.source_id == ref["registry_id"]
                    and doc.sha256 == ref["sha256"]
                    and doc.locator == ref["url"]
                )
                assert (
                    ref["make"] == c["make"]
                    and ref["model"] == c["model"]
                    and ref["market"] == c["original_market"]
                )
                if doc.id not in doc_checks:
                    assert (
                        hashlib.sha256(private_path(doc.storage_key).read_bytes()).hexdigest()
                        == doc.sha256
                    )
                    doc_checks[doc.id] = dict(
                        source_id=doc.source_id, url=doc.locator, sha256=doc.sha256, status="PASS"
                    )
        # Same public query functions, same complete published rows; cache only input reads.
        # This avoids repeatedly hydrating thousands of rows while testing every combination.
        with patch.object(buyer, "records", return_value=live):
            for v, c in ready_rows:
                q = dict(
                    make=c["make"],
                    model=c["model"],
                    generation=c["generation_code"],
                    market=c["original_market"],
                    year=c["model_year"],
                    engine=str(c["facts"]["engine_displacement"]["value"]),
                    transmission=c["facts"]["transmission_family"]["value"],
                    drivetrain=c["facts"]["drivetrain"]["value"],
                    body=c["facts"]["body"]["value"],
                    catalog_ready_only=True,
                )
                if us_catalog_ready(c):
                    q.update(catalog_scope="US_BASE_2000", seats=c["facts"]["seats"]["value"])
                result = buyer.resolve(db, q)
                ok = (
                    result["status"] in {"EXACT", "MULTIPLE"}
                    and v.id in {x["id"] for x in result["candidates"]}
                    and not result["missing"]
                )
                assert ok, (v.catalog_key, result["status"])
                query_results.append(
                    dict(
                        catalog_key=v.catalog_key,
                        query=q,
                        status=result["status"],
                        expected_candidate_found=True,
                    )
                )
            for f in manifest["families"]:
                members = [
                    (v, c) for v, c in ready_rows if targets[v.catalog_key]["family_id"] == f["id"]
                ]
                expected = {v.id for v, _ in members}
                filters = BuyerFilters(
                    makes=[f["make"]],
                    models=[f["model"]],
                    generations=[f["generation_code"]] if f["generation_code"] else [],
                    year_min=f["year_from"],
                    year_max=f["year_to"],
                    market_preference="SELECTED",
                    markets=[f["market"]],
                    catalog_ready_only=True,
                    limit=100,
                )
                for language in ("ru", "az"):
                    found = buyer.search(db, filters, language)
                    assert expected == {c["id"] for c in found["matches"]}, f["id"]
                    assert not found["needs_confirmation"], f["id"]
                    strict_found = buyer.search(
                        db, filters.model_copy(update={"catalog_scope": "US_BASE_2000"}), language
                    )
                    assert {v.id for v, c in members if us_catalog_ready(c)} == {
                        x["id"] for x in strict_found["matches"]
                    }, f["id"]
                wrong = buyer.resolve(
                    db,
                    dict(
                        make=f["make"],
                        model=f["model"],
                        generation=f["generation_code"],
                        market=f["market"],
                        year=f["year_from"],
                        engine="11.9",
                        catalog_ready_only=True,
                    ),
                )
                assert wrong["status"] == "CONTRADICTION", f["id"]
                family_rows.append(
                    {
                        "id": f["id"],
                        "make": f["make"],
                        "model": f["model"],
                        "generation": f["generation_code"],
                        "market": f["market"],
                        "years": [f["year_from"], f["year_to"]],
                        "counts": base_catalog_counts(members),
                        "us_with_seating_counts": base_catalog_counts(
                            members, require_us_seating=True
                        ),
                        "filter_ru": "PASS",
                        "filter_az": "PASS",
                        "resolver_all_configurations": "PASS",
                        "status": "BASE_CATALOG_READY_SCOPED",
                        "exclude": f.get("exclude", []),
                    }
                )
        counts = base_catalog_counts(ready_rows)
        totals = buyer.coverage(db, live)
        scoped_live = [
            (v, c)
            for v, c in live
            if c["make"] in policy()["primary_makes"]
            and c["original_market"] == "US"
            and c["model_year"] >= 2000
        ]
        cumulative = base_catalog_counts(scoped_live)
        strict = base_catalog_counts(scoped_live, require_us_seating=True)
        brands = [
            dict(
                make=make,
                basic=base_catalog_counts([(v, c) for v, c in scoped_live if c["make"] == make]),
                us_with_seating=base_catalog_counts(
                    [(v, c) for v, c in scoped_live if c["make"] == make], require_us_seating=True
                ),
            )
            for make in policy()["primary_makes"]
        ]
        seating_gaps = [
            dict(
                make=c["make"],
                model=c["model"],
                generation=c.get("generation_code"),
                year=c["model_year"],
                catalog_key=v.catalog_key,
            )
            for v, c in scoped_live
            if base_catalog_ready(c) and not us_catalog_ready(c)
        ]
        # Previous BMW MY2025 proof remains valid, independently of the new batch.
        assert (
            sum(
                identity_verified(c)
                for _, c in live
                if c.get("external_key") in {"48163", "48164"}
                and c.get("source_registry_id") == "epa"
            )
            == 2
        )
    baseline_info = (
        json.loads((ROOT / args.baseline).read_text(encoding="utf-8")) if args.baseline else None
    )
    baseline = ROOT / (
        baseline_info["database"]
        if baseline_info
        else ".backups/before-local-usable-01-20260920T131112Z.sqlite3"
    )
    preserved = preservation(set(targets), baseline, enrichment_keys)
    dump(out / "preservation.json", preserved)
    assert preserved["status"] == "PASS", preserved
    catalog_tables = build_report(
        targets,
        variants,
        buyer.active_us_rows(live),
        baseline,
        policy()["primary_makes"],
        base_rows=buyer.active_us_base_rows(live),
        enrichment_keys=enrichment_keys,
    )
    assert (
        catalog_tables["reconciliation"]["strict_output_configuration_count"]
        == strict["model_year_configurations"]
    )
    hashes = (
        baseline_info["ui_hashes"]
        if baseline_info
        else json.loads(
            (ROOT / "deliverables/VerifiedData/local-usable-batch-01/ui-baseline.json").read_text()
        )
    )
    changed_ui = [
        name
        for name, digest in hashes.items()
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
    ]
    allowed_ui = (
        {
            "apps/web_preview/catalog-views.js",
            "apps/web_preview/catalog-copy.js",
            "apps/web_preview/styles.css",
        }
        if baseline_info
        else set()
    )
    assert set(changed_ui) <= allowed_ui, "UI_OUTSIDE_AUTHORIZED_FLOW_CHANGED"
    unchanged = not changed_ui
    report = dict(
        status="PASS",
        at=datetime.now(UTC).isoformat(),
        batch_id=manifest["batch_id"],
        published_corrections=corrections,
        audited_batches=sorted(batch_ids),
        fact_enrichment_manifests=args.enrichment_manifest,
        counts=counts,
        cumulative_basic_counts=cumulative,
        cumulative_us_with_seating_counts=strict,
        priority_make_coverage=brands,
        seating_gaps=seating_gaps,
        models_usable_in_filter_and_resolver=counts["models"],
        families=family_rows,
        full_catalog=totals,
        documents_verified=len(doc_checks),
        source_conflicts=manifest.get("source_conflicts", [])
        + manifest.get("source_discrepancies", []),
        research_holds=manifest.get("research_holds", []),
        exclusions=manifest["exclusions"],
        UI_UNCHANGED=unchanged,
        authorized_ui_changes=changed_ui,
        ui_files_verified=len(hashes),
        phone="DEFERRED",
        hetzner="DEFERRED",
        paid_calls=0,
        reporting_format=catalog_tables["format"],
        configuration_tables="catalog-tables.json",
        configuration_tables_reconciliation=catalog_tables["reconciliation"],
        remaining_primary_makes=[r["make"] for r in brands if not r["us_with_seating"]["models"]],
        basic_covered_makes=[r["make"] for r in brands if r["basic"]["models"]],
        basic_uncovered_makes=[r["make"] for r in brands if not r["basic"]["models"]],
        deferred_workstreams=manifest.get("excluded_workstreams", policy()["deferred_workstreams"]),
    )
    if args.previous_coverage:
        previous = json.loads((ROOT / args.previous_coverage).read_text(encoding="utf-8"))
        before_gaps = {r["catalog_key"]: r for r in previous["seating_gaps"]}
        after_gaps = {r["catalog_key"]: r for r in seating_gaps}
        strict_keys = {v.catalog_key for v, c in scoped_live if us_catalog_ready(c)}
        closed = before_gaps.keys() & strict_keys
        remaining = before_gaps.keys() & after_gaps.keys()
        assert closed | remaining == before_gaps.keys(), (
            "PREVIOUS_SEATING_GAP_DISAPPEARED_WITHOUT_VERIFICATION"
        )
        report["previous_checkpoint"] = {
            "batch_id": previous["batch_id"],
            "basic_covered_makes": [
                r["make"] for r in previous["priority_make_coverage"] if r["basic"]["models"]
            ],
            "basic_uncovered_makes": [
                r["make"] for r in previous["priority_make_coverage"] if not r["basic"]["models"]
            ],
        }
        report["growth"] = {
            name: {
                k: current[k] - previous[name][k] for k in current if isinstance(current[k], int)
            }
            for name, current in [
                ("cumulative_basic_counts", cumulative),
                ("cumulative_us_with_seating_counts", strict),
            ]
        }
        report["previous_seating_gap_progress"] = {
            "initial": len(before_gaps),
            "closed": len(closed),
            "remaining": len(remaining),
            "closed_configurations": [before_gaps[k] for k in sorted(closed)],
            "new_batch_gaps": len(after_gaps.keys() - before_gaps.keys()),
            "total_remaining_gaps": len(after_gaps),
        }
    write_tables(
        out,
        catalog_tables,
        manifest["batch_id"],
        checkpoint=ROOT / args.checkpoint if args.checkpoint else None,
    )
    dump(out / "coverage.json", report)
    dump(out / "resolver-matrix.json", query_results)
    dump(out / "documents.json", list(doc_checks.values()))
    print(
        json.dumps(
            {
                "status": "PASS",
                "counts": counts,
                "documents": len(doc_checks),
                "preservation": "PASS",
                "ui": "AUTHORIZED_FLOW_EXTENSION" if changed_ui else "UNCHANGED",
                "cumulative_basic_counts": cumulative,
                "cumulative_us_with_seating_counts": strict,
            }
        )
    )


if __name__ == "__main__":
    main()
