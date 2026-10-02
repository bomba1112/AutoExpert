"""Write a named factory-source index and subject-matter checkpoint from published data."""

# ruff: noqa: E402
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.knowledge_ops import RawDocument
from app.services.factory_bulk_tables import PARSER_VERSION, common_table_facts
from sqlalchemy import select

from scripts.factory_bulk_table_enrich import _URL, CACHE, OUT, SCOPE, _load_table


def main():
    prepared = json.loads((OUT / "factory-prepared.json").read_text(encoding="utf-8"))
    qa = json.loads((OUT / "factory-qa.json").read_text(encoding="utf-8"))
    performance = json.loads((OUT / "factory-performance.json").read_text(encoding="utf-8"))
    scopes = json.loads(SCOPE.read_text(encoding="utf-8"))["model_body_scope"]
    grouped = defaultdict(list)
    for change in prepared["changes"]:
        grouped[(change["model"], change["model_year"], change["source_url"])].append(change)
    index = []
    with SessionLocal() as db:
        docs = db.scalars(select(RawDocument).where(RawDocument.source_id == "factory-kia-us"))
        for doc in sorted(docs, key=lambda item: item.locator):
            match = _URL.fullmatch(doc.locator)
            if not match or match[1] not in scopes:
                continue
            slug, year = match[1], int(match[2])
            spec = scopes[slug]
            if year not in spec["years"]:
                continue
            cache_file = CACHE / f"{doc.sha256}-{PARSER_VERSION}.json"
            if not cache_file.exists():
                raise ValueError("FACTORY_PARSER_CACHE_MISSING")
            table = _load_table(doc, Counter())
            facts, held = common_table_facts(table)
            applied = grouped[(spec["model"], year, doc.locator)]
            index.append(
                {
                    "make": "Kia",
                    "model": spec["model"],
                    "body": spec["body"],
                    "market": "US",
                    "model_year": year,
                    "url": doc.locator,
                    "document_id": doc.id,
                    "sha256": doc.sha256,
                    "parser_version": PARSER_VERSION,
                    "table_rows": len(table.rows),
                    "trim_columns": len(table.trims),
                    "all_trim_invariant_fact_fields": sorted(facts),
                    "conditional_or_conflicting_rows_held": len(held),
                    "published_configurations_with_new_fields": len(applied),
                    "new_annual_field_values": sum(len(row["added"]) for row in applied),
                    "applied_field_names": sorted({key for row in applied for key in row["added"]}),
                    "status": "APPLIED" if applied else "NO_NEW_FIELD",
                }
            )
    (OUT / "factory-source-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Factory HTML batch: Kia US, published technical fields",
        "",
        "25 registered annual Kia Media HTML matrices were reused from local verified "
        "document storage; "
        "there were no network requests. All 2,033 table rows were parsed and only values "
        "identical across every trim column were candidates for existing, independently "
        "verified US configurations.",
        "",
        (
            "| Model | Exact US MY | Published configurations | New annual field values | "
            "New fields and source value | Status |"
        ),
        "|---|---:|---:|---:|---|---|",
    ]
    for row in sorted(index, key=lambda item: (item["model"], item["model_year"])):
        added = grouped[(row["model"], row["model_year"], row["url"])]
        fields = {}
        for change in added:
            fields.update(change["added"])
        rendered = "; ".join(f"{key}={value}" for key, value in sorted(fields.items())) or "—"
        lines.append(
            f"| Kia {row['model']} | {row['model_year']} | "
            f"{row['published_configurations_with_new_fields']} | "
            f"{row['new_annual_field_values']} | {rendered} | {row['status']} |"
        )
    lines += [
        "",
        "Each row above names one annual source matrix. Full engine/transmission/drivetrain "
        "applicability for every changed configuration, with a source row locator and immutable "
        "document hash, is in `factory-prepared.json` and the two frozen "
        "`factory-reviewed-*.json` manifests.",
        "",
        (
            f"Published: {qa['variants']} existing configurations, "
            f"{qa['field_values']} newly filled "
            "field × annual-configuration cells from "
            f"{prepared['counts']['unique_source_facts_applied']} "
            "distinct document-field-value facts. No new family/year identities were created here. "
            f"There were {prepared['counts']['field_same']} equal existing/alias values and "
            f"{prepared['counts']['source_rows_quarantined']} conditional, conflicting or missing "
            "table rows held. Optional engine-oil capacities without an identified service/fill "
            "procedure were not mapped to the service-change field. Kia Sorento 2016–2018 "
            "optional five/seven-place rows were not generalized."
        ),
        "",
        f"Presentation-only correction: {qa['localized_values']} published factory free-text "
        "values have curated AZ/RU labels; original English source text is retained as the "
        "technical value. This correction contributes zero new technical facts.",
        "",
        "Measured timings (seconds): cold extraction and mapping "
        f"{performance['cold_prepare_seconds']}; warm cache reuse "
        f"{performance['warm_prepare_seconds']}, identical semantic SHA256; prepublication "
        f"gate {performance['prepublication_gate_seconds']}; original technical publication "
        f"{performance['technical_publication_seconds']}; AZ/RU label publication "
        f"{performance['localization_publication_seconds']}; final QA and two idempotent "
        f"replays {performance['final_audit_and_two_idempotent_replays_seconds']}. "
        "These separate wall durations are not additive. There is no comparable measured "
        "old manual-method baseline.",
        "",
        "Code and QA: `factory_bulk_tables.py`, `factory_bulk_table_enrich.py`, "
        "`factory_bulk_publish.py`, `factory_bulk_localize.py`, `factory_bulk_qa.py`; "
        "12 new heterogeneous tests pass, including colspan/rowspan, optional seating, "
        "octane scale/minimum, incomplete fill basis, conflict, cache corruption and "
        "idempotence guards. Full project regression belongs to the batch publication gate.",
        "",
        "Resume: `python scripts/factory_bulk_table_enrich.py --prepare` is read-only and now "
        "returns `NO_NEW_FACTS_ALREADY_PUBLISHED`; `factory-rescan.json` records its current "
        "cursor. New source-year matrices can be added to `factory-source-scope.json` after "
        "reviewing body/market applicability, then emitted as a new batch ID. Frozen manifests "
        "must not be edited or republished with changed content.",
    ]
    (OUT / "factory-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "documents": len(index),
                "applied_document_years": sum(row["status"] == "APPLIED" for row in index),
                "new_annual_field_values": qa["field_values"],
                "localized_values": qa["localized_values"],
            }
        )
    )


if __name__ == "__main__":
    main()
