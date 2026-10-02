"""Read-only, field-level fact delta for the US bulk batch.

Counts published configuration/field cells, not document mentions or repeated
import jobs.  The baseline is a private SQLite backup supplied at run time.
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"
SOURCES = ("epa", "factory-kia-us")


def confirmed(field):
    return field.get("status") == "CONFIRMED" and field.get("value") is not None


def scalar(field):
    return field.get("value"), field.get("unit"), field.get("status")


def catalog(connection, key):
    row = connection.execute(
        "SELECT specifications FROM vehicle_variants WHERE catalog_key=?", (key,)
    ).fetchone()
    return json.loads(row[0]).get("catalog", {}) if row else None


def run(baseline, current):
    prepared = json.loads((OUT / "prepared.json").read_text(encoding="utf-8"))
    new_keys = {item["catalog_key"] for item in prepared["targets"]}
    localization_keys = set()
    for source in SOURCES:
        path = OUT / f"factory-localized-{source}.json"
        rows = json.loads(path.read_text(encoding="utf-8"))["records"]
        localization_keys.update(f"{source}:{row['external_key']}" for row in rows)
    assert len(localization_keys) == 92
    assert not (new_keys & localization_keys)

    new_fields = Counter()
    enrichment_fields = Counter()
    all_enrichment_changes = Counter()
    value_conflicts = []
    with sqlite3.connect(baseline) as before, sqlite3.connect(current) as after:
        for key in sorted(new_keys):
            assert catalog(before, key) is None, f"BATCH_TARGET_ALREADY_EXISTED: {key}"
            present = catalog(after, key)
            assert present is not None, f"BATCH_TARGET_MISSING: {key}"
            for name, fact in present.get("facts", {}).items():
                if confirmed(fact):
                    new_fields[name] += 1
        for key in sorted(localization_keys):
            prior, present = catalog(before, key), catalog(after, key)
            assert prior is not None and present is not None, f"ENRICHMENT_TARGET_MISSING: {key}"
            old_facts, new_facts = prior.get("facts", {}), present.get("facts", {})
            for name, fact in new_facts.items():
                old = old_facts.get(name, {})
                if scalar(old) == scalar(fact):
                    continue
                all_enrichment_changes[name] += 1
                if not confirmed(old) and confirmed(fact):
                    enrichment_fields[name] += 1
                elif confirmed(old) and confirmed(fact):
                    value_conflicts.append(
                        {
                            "catalog_key": key,
                            "field": name,
                            "before": {k: old.get(k) for k in ("value", "unit")},
                            "after": {k: fact.get(k) for k in ("value", "unit")},
                        }
                    )
    report = {
        "count_unit": "published configuration-field cell",
        "batch_new_configurations": len(new_keys),
        "batch_new_configuration_confirmed_fact_cells": sum(new_fields.values()),
        "batch_new_configuration_fact_fields": dict(sorted(new_fields.items())),
        "existing_configurations_enriched": len(localization_keys),
        "existing_configuration_newly_confirmed_fact_cells": sum(enrichment_fields.values()),
        "existing_configuration_newly_confirmed_fields": dict(sorted(enrichment_fields.items())),
        "existing_configuration_scalar_changes": sum(all_enrichment_changes.values()),
        "existing_configuration_scalar_change_fields": dict(sorted(all_enrichment_changes.items())),
        "existing_configuration_confirmed_value_conflicts": value_conflicts,
        "newly_confirmed_fact_cells_total": sum(new_fields.values())
        + sum(enrichment_fields.values()),
        "research_rows_counted": 0,
        "republication_jobs_counted": 0,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, default=ROOT / "autoexpert.db")
    args = parser.parse_args()
    report = run(args.baseline, args.current)
    (OUT / "fact-delta.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if isinstance(v, int)}))


if __name__ == "__main__":
    main()
