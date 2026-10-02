"""Read-only, named handoff for the existing AI/source bulk publication run."""

# ruff: noqa: E402, E501
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal
from app.services import catalog_buyer as buyer
from app.services.catalog_verification import base_catalog_ready
from app.services.catalog_verification import us_catalog_with_confirmed_seating as us_catalog_ready
from catalog_checkpoint_report import year_ranges

OUT = ROOT / "deliverables/VerifiedData/us-ai-verify-09"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    baseline = read(OUT / "baseline.json")
    coverage = read(OUT / "coverage.json")
    tables = read(OUT / "catalog-tables.json")
    policy = read(ROOT / "data/manifests/az-market-priority-policy.json")
    delta_keys = {
        m["catalog_key"] for r in tables["delta_from_previous_batch"] for m in r["members"]
    }
    with sqlite3.connect(ROOT / baseline["database"]) as db:
        before_documents = {row[0] for row in db.execute("SELECT sha256 FROM raw_documents")}
        before = {
            key: json.loads(spec).get("catalog", {})
            for key, spec in db.execute(
                "SELECT catalog_key,specifications FROM vehicle_variants WHERE catalog_key IS NOT NULL"
            )
        }
    with SessionLocal() as db:
        live = buyer.records(db)
        target_rows = [(v, c) for v, c in live if v.catalog_key in delta_keys]
        assert all(base_catalog_ready(c) for _, c in target_rows)
        assert {v.catalog_key for v, _ in target_rows} == delta_keys
        cumulative = defaultdict(lambda: {"strict": set(), "conditional": set()})
        for _, c in buyer.active_us_base_rows(live):
            key = (c["make"], c["model"], c.get("generation") or c.get("generation_code"))
            cumulative[key]["strict" if us_catalog_ready(c) else "conditional"].add(c["model_year"])
        named = [
            dict(
                make=k[0],
                model=k[1],
                generation=k[2],
                strict_years=sorted(v["strict"]),
                conditional_years=sorted(v["conditional"]),
            )
            for k, v in sorted(
                cumulative.items(),
                key=lambda x: (policy["primary_makes"].index(x[0][0]), *x[0][1:]),
            )
        ]
        delta = []
        used_documents = set()
        technical = defaultdict(lambda: defaultdict(set))
        new_cells = Counter()
        for v, c in target_rows:
            for fact in c["facts"].values():
                ref = fact.get("documentary_source") or {}
                if ref.get("sha256"):
                    used_documents.add(ref["sha256"])
            for refs in c.get("identity_verification", {}).get("field_evidence", {}).values():
                used_documents.update(ref["sha256"] for ref in refs)
            prior = before.get(v.catalog_key)
            fields = []
            for key, fact in c["facts"].items():
                old = (prior or {}).get("facts", {}).get(key, {})
                if fact.get("status") != "CONFIRMED":
                    continue
                if any(old.get(k) != fact.get(k) for k in ("value", "unit", "status")):
                    fields.append(key)
                    new_cells[
                        "new_configuration" if prior is None else "existing_configuration"
                    ] += 1
            profile = buyer.vehicle_profile(c, "ru")
            model_key = (c["make"], c["model"], c["model_year"])
            for group in profile["technical"]:
                for row in group["rows"]:
                    technical[model_key][group["key"]].add(row["key"])
            delta.append(
                dict(
                    catalog_key=v.catalog_key,
                    make=c["make"],
                    model=c["model"],
                    generation=c["generation"],
                    year=c["model_year"],
                    new=prior is None,
                    new_confirmed_fields=sorted(fields),
                    strict=us_catalog_ready(c),
                    revision_id=v.published_revision_id,
                )
            )
        strict_keys = {v.catalog_key for v, c in live if us_catalog_ready(c)}
        old04 = read(ROOT / "deliverables/VerifiedData/us-base-catalog-04/coverage.json")
        old05 = read(ROOT / "deliverables/VerifiedData/us-base-catalog-05/coverage.json")
        old143 = {r["catalog_key"] for r in old04["seating_gaps"]}
        new10 = {r["catalog_key"] for r in old05["seating_gaps"]} - old143
        cohorts = {
            name: dict(
                initial=len(keys),
                closed=len(keys & strict_keys),
                remaining=len(keys - strict_keys),
                remaining_catalog_keys=sorted(keys - strict_keys),
            )
            for name, keys in (("historical_143", old143), ("batch05_new_10", new10))
        }
    rules = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        == baseline["rules_hashes"][name]
        for name in (
            "backend/app/services/catalog_verification.py",
            "backend/app/schemas/knowledge.py",
        )
    }
    assert all(rules.values())
    report = dict(
        at=datetime.now(UTC).isoformat(),
        status="PASS",
        audited_batches=coverage["audited_batches"],
        scope_baseline=read(OUT / "scope-baseline.json"),
        new_configurations=sum(r["new"] for r in delta),
        enriched_existing_configurations=sum(
            not r["new"] and bool(r["new_confirmed_fields"]) for r in delta
        ),
        evidence_only_refreshes=sum(not r["new"] and not r["new_confirmed_fields"] for r in delta),
        new_strict_configurations=sum(r["new"] and r["strict"] for r in delta),
        confirmed_field_cells_added=dict(new_cells),
        source_documents_used=len(used_documents),
        source_documents_already_registered_before_run=len(used_documents & before_documents),
        source_documents_new_to_registry=len(used_documents - before_documents),
        registry_note="New registration is not necessarily a new download; acquisition receipts separately record cache reuse.",
        field_count_note="A cell is a field on one exact annual configuration; repeated trim/year applicability is not a distinct source discovery.",
        cumulative_named=named,
        delta=delta,
        technical_coverage=[
            dict(
                make=k[0],
                model=k[1],
                year=k[2],
                categories={n: sorted(fields) for n, fields in v.items()},
            )
            for k, v in sorted(technical.items())
        ],
        seating_cohorts=cohorts,
        trust_files_unchanged=rules,
        approved_design="PRESERVED; two copy-only edits state the new make-specific year scope",
        paid_external_calls=0,
        external_api_cost_usd=0,
        codex_session_cost="Not available; native Codex work is not represented as free",
    )
    dump("run-summary.json", report)
    dump(
        "publication-audit.json",
        dict(
            status="PASS",
            audited_batches=coverage["audited_batches"],
            corrections=coverage["published_corrections"],
            new_configurations=report["new_configurations"],
            target_keys=sorted(delta_keys),
            original_09_interrupted=True,
            recovery="09-completion corrects generation evidence; 09-manual corrects MT taxonomy. Original manifests and failed attempts retained; not counted as new records.",
        ),
    )
    lines = [
        "Накопительный каталог; годы относятся только к опубликованным версиям. S — места подтверждены, C — без ограничения по местам.",
        "",
    ]
    for r in named:
        pieces = (["S " + year_ranges(r["strict_years"])] if r["strict_years"] else []) + (
            ["C " + year_ranges(r["conditional_years"])] if r["conditional_years"] else []
        )
        lines.append(f"- {r['make']} {r['model']} — {r['generation']}: {'; '.join(pieces)}.")
    (OUT / "cumulative-named.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "status",
                    "new_configurations",
                    "enriched_existing_configurations",
                    "new_strict_configurations",
                    "confirmed_field_cells_added",
                )
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
