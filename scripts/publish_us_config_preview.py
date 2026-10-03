"""Prepare the publication of the US technical configurations of model years 2021-2026 for the
preview catalogue (owner decision 2026-10-03: shown in the preview behind a flag, never in
production; rehearsal on a copy first).

Each configuration (technical_evidence, fact_key='configuration') is matched through its EPA
vehicle ids (conditions.identity.epa_ids) to the published EPA catalogue variants it was built
from. Status per configuration:
  PRODUCTION_LINKED  its catalogue variant is already shown in production: nothing to add
  LINK               one or more EPA variants that map back to this configuration only
  SHARED_VARIANT     every matching variant also matches another configuration (X5 / X5 M ...)
  NO_VARIANT         no published EPA variant carries its EPA ids
  NOT_CORE_READY     the matching variants lack the core facts the catalogue requires
  PRODUCTION_TWIN    production already shows the same car (make, model, year, drive,
                     displacement, gearbox family): the preview would duplicate it
--apply writes, for LINK pairs only, one CatalogRevision in state PREVIEW per (configuration,
variant) under one ImportJob in state PREVIEW. Nothing existing is changed: the script checks
before / after fingerprints of vehicle_variants and commercial_fact_claims and the number of
production rows, and a rerun adds nothing (idempotent). A record whose variant was republished
since (stale) gets its variant revision refreshed and is counted.

  .venv/Scripts/python.exe scripts/publish_us_config_preview.py --db C:/AutoExpertData/work/rehearsal_batch.db [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data_work" / "_preview_publication"
RULE = "us-config-preview-1"


def epa_ids_of(catalog: dict) -> set[str]:
    """EPA vehicle ids a published EPA variant carries (as scripts/publish_us_epa_core._epa_ids)."""
    if catalog.get("source_registry_id") != "epa":
        return set()
    ids = {str(v) for v in (catalog.get("source_provenance") or {}).get("epa_vehicle_ids", [])}
    key = str(catalog.get("external_key") or "")
    if key.isdigit():
        ids.add(key)
    note = catalog.get("revision_note") or ""
    if note.startswith("EPA_CORE_PROVENANCE:"):
        with suppress(ValueError, KeyError, TypeError):
            ids.update(str(v) for v in json.loads(note.split(":", 1)[1])["epa_ids"])
    return ids


def gearbox_family(text: str) -> str | None:
    t = str(text or "").lower()
    if not t:
        return None
    if t.startswith("manual") or t == "manual":
        return "MANUAL"
    if "(av" in t or "variable" in t or "cvt" in t:
        return "CVT"
    if "(am" in t or "dual-clutch" in t or "dct" in t:
        return "DCT"
    if "(a1" in t or "single" in t:
        return "SINGLE"
    return "AT"


def norm(text) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", str(text or "").lower()).strip()


def fingerprint(db) -> dict:
    from sqlalchemy import text

    variants = hashlib.sha256()
    for row in db.execute(text("select id, published_revision_id, specifications from vehicle_variants order by id")):
        variants.update("|".join(str(x) for x in row).encode())
    claims = hashlib.sha256()
    for row in db.execute(text("select id, variant_id, fact_name, value, reuse_status, updated_at from commercial_fact_claims order by id")):
        claims.update("|".join(str(x) for x in row).encode())
    return {"vehicle_variants": variants.hexdigest(), "commercial_fact_claims": claims.hexdigest(),
            "technical_evidence": db.execute(text("select count(*), max(updated_at) from technical_evidence")).one()._tuple()}


def plan(db, years: tuple[int, int]) -> tuple[list[dict], dict]:
    from sqlalchemy import select

    from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
    from app.models.evidence import TechnicalEvidence
    from app.services import catalog_buyer as buyer
    from app.services.listing_intake import production_visible_us_rows

    production = production_visible_us_rows(db)
    production_ids = {v.id for v, _ in production}
    twins = set()
    for _, c in production:
        facts = c.get("facts") or {}
        value = lambda k: (facts.get(k) or {}).get("value")  # noqa: E731
        twins.add((norm(c.get("make")), norm(c.get("model")), int(c.get("model_year") or 0), norm(value("drivetrain"))[:3],
                   norm(value("engine_displacement")).split(" ")[0], gearbox_family(value("transmission_description")) or norm(value("transmission_family"))))
    variants = {}
    by_epa = defaultdict(set)
    for v in db.scalars(select(VehicleVariant).where(VehicleVariant.published_revision_id.is_not(None), VehicleVariant.is_demo.is_(False),
                                                     VehicleVariant.market == "US")):
        catalog = (v.specifications or {}).get("catalog") or {}
        year = int(catalog.get("model_year") or v.year_from or 0)
        if not (years[0] <= year <= years[1]):
            continue
        ids = epa_ids_of(catalog)
        if ids:
            variants[v.id] = (v, catalog, ids)
            for i in ids:
                by_epa[i].add(v.id)
    ready = {v.id for v, _ in buyer.active_us_rows(buyer.records(db, production_safe=False, variant_ids=set(variants)))} if variants else set()
    configs = db.execute(
        select(TechnicalEvidence, VehicleMake.name, VehicleModel.name)
        .join(VehicleGeneration, VehicleGeneration.id == TechnicalEvidence.generation_id)
        .join(VehicleModel, VehicleModel.id == VehicleGeneration.model_id)
        .join(VehicleMake, VehicleMake.id == VehicleModel.make_id)
        .where(TechnicalEvidence.fact_key == "configuration", TechnicalEvidence.year_from >= years[0],
               TechnicalEvidence.year_from <= years[1])).all()
    variant_configs = defaultdict(set)
    matches = {}
    for row, _, _ in configs:
        ident = (row.conditions or {}).get("identity") or {}
        found = set().union(*(by_epa.get(str(i), set()) for i in ident.get("epa_ids") or [])) if ident.get("epa_ids") else set()
        matches[row.configuration_key] = found
        for vid in found:
            variant_configs[vid].add(row.configuration_key)
    out = []
    for row, make, model in configs:
        ident = (row.conditions or {}).get("identity") or {}
        key = row.configuration_key
        entry = {"configuration_key": key, "technical_evidence_id": row.id, "make": make, "model": model, "year": row.year_from,
                 "epa_ids": ident.get("epa_ids") or [], "pairs": []}
        found = matches[key]
        twin = (norm(make), norm(model), int(row.year_from), norm(ident.get("drivetrain"))[:3],
                norm(ident.get("displacement_l")).split(" ")[0], gearbox_family(ident.get("epa_transmission")))
        if row.vehicle_variant_id and row.vehicle_variant_id in production_ids:
            entry["status"] = "PRODUCTION_LINKED"
        elif not found:
            entry["status"] = "NO_VARIANT"
        elif twin in twins:
            entry["status"] = "PRODUCTION_TWIN"
        else:
            own = [vid for vid in found if variant_configs[vid] == {key}]
            if not own:
                entry["status"] = "SHARED_VARIANT"
                entry["shared_with"] = sorted(set().union(*(variant_configs[vid] for vid in found)) - {key})[:5]
            else:
                ok = [vid for vid in own if vid in ready]
                if not ok:
                    entry["status"] = "NOT_CORE_READY"
                else:
                    entry["status"] = "LINK"
                    for vid in sorted(ok):
                        v, catalog, ids = variants[vid]
                        entry["pairs"].append({"variant_id": vid, "variant_catalog_key": v.catalog_key,
                                               "variant_revision_id": v.published_revision_id,
                                               "epa_ids_matched": sorted(ids & {str(i) for i in entry["epa_ids"]})})
        out.append(entry)
    summary = {"years": list(years), "configurations": len(out), "status": dict(Counter(e["status"] for e in out)),
               "pairs": sum(len(e["pairs"]) for e in out), "production_rows": len(production_ids)}
    return out, summary


def apply(db, entries: list[dict], years: tuple[int, int]) -> dict:
    from sqlalchemy import select

    from app.models.catalog import VehicleVariant
    from app.models.knowledge_ops import CatalogRevision, ImportJob
    from app.services.knowledge_import import checksum

    request_key = checksum({"rule": RULE, "years": list(years)})
    job = db.scalar(select(ImportJob).where(ImportJob.request_key == request_key))
    if job is None:
        job = ImportJob(request_key=request_key, source_id="epa", raw_document_id=None, state="PREVIEW",
                        manifest={"parser": RULE, "years": list(years), "preview_only": True, "production_visible": False,
                                  "factory_verification": False,
                                  "decision": "owner 2026-10-03: prepare publication, show in the preview behind a flag, not in production"},
                        metrics={}, errors=[])
        db.add(job)
        db.flush()
    existing = {r.external_key: r for r in db.scalars(select(CatalogRevision).where(CatalogRevision.import_job_id == job.id))}
    now = datetime.now(UTC)
    added = refreshed = 0
    for entry in entries:
        for pair in entry["pairs"]:
            external_key = f"{entry['configuration_key']}:{pair['variant_id'][:8]}"
            payload = {"configuration_key": entry["configuration_key"], "technical_evidence_id": entry["technical_evidence_id"],
                       "epa_ids": entry["epa_ids"], "variant_catalog_key": pair["variant_catalog_key"],
                       "variant_revision_id": pair["variant_revision_id"], "match": {"epa_ids": pair["epa_ids_matched"]}, "rule": RULE}
            current = existing.get(external_key)
            if current is None:
                db.add(CatalogRevision(import_job_id=job.id, variant_id=pair["variant_id"], external_key=external_key,
                                       payload=payload, checksum=checksum(payload), state="PREVIEW",
                                       reviewer="AUTOMATED_US_CONFIG_PREVIEW", reviewed_at=now,
                                       review_note="preview only: EPA ids of the US technical configuration match this published EPA variant"))
                added += 1
            elif (current.payload or {}).get("variant_revision_id") != pair["variant_revision_id"]:
                current.payload = payload
                current.checksum = checksum(payload)
                refreshed += 1
    job.metrics = {"records": len(existing) + added, "added": added, "refreshed": refreshed, "at": now.isoformat()}
    db.commit()
    stale = sum(1 for r in db.scalars(select(CatalogRevision).where(CatalogRevision.import_job_id == job.id))
                if (v := db.get(VehicleVariant, r.variant_id)) is None or v.published_revision_id != (r.payload or {}).get("variant_revision_id"))
    return {"job_id": job.id, "added": added, "refreshed": refreshed, "stale_after": stale}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--years", nargs=2, type=int, default=[2021, 2026])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import get_settings
    from app.services import catalog_preview
    from app.services.listing_intake import production_visible_us_rows

    db_path = Path(args.db).resolve()
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    years = (args.years[0], args.years[1])
    tag = "live" if db_path == (ROOT / "autoexpert.db").resolve() else "rehearsal"
    OUT.mkdir(parents=True, exist_ok=True)
    with Session(engine) as db:
        entries, summary = plan(db, years)
        (OUT / f"plan_{tag}.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
        print("plan", json.dumps(summary, ensure_ascii=False))
        if not args.apply:
            (OUT / f"summary_{tag}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
            return 0
        from catalog_writer_lock import catalog_writer_lock

        before = fingerprint(db)
        production_before = len(production_visible_us_rows(db))
        with catalog_writer_lock():
            result = apply(db, entries, years)
        after = fingerprint(db)
        production_after = len(production_visible_us_rows(db))
        settings = get_settings()
        settings.preview_us_configurations = None
        catalog_preview.clear_cache()
        preview = catalog_preview.preview_rows(db)
        rerun = apply(db, entries, years)
        checks = {"variants_unchanged": before["vehicle_variants"] == after["vehicle_variants"],
                  "claims_unchanged": before["commercial_fact_claims"] == after["commercial_fact_claims"],
                  "technical_evidence_unchanged": before["technical_evidence"] == after["technical_evidence"],
                  "production_rows": [production_before, production_after],
                  "preview_rows": len(preview), "rerun_added": rerun["added"], "rerun_refreshed": rerun["refreshed"]}
        summary.update({"apply": result, "checks": checks,
                        "preview_by_year": dict(Counter(int(c["model_year"]) for _, c in preview)),
                        "preview_by_make": dict(Counter(c["make"] for _, c in preview))})
        (OUT / f"summary_{tag}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        print("apply", json.dumps(result), "checks", json.dumps(checks))
        ok = (checks["variants_unchanged"] and checks["claims_unchanged"] and checks["technical_evidence_unchanged"]
              and production_before == production_after and rerun["added"] == 0)
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
