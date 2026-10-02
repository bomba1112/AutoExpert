"""Compare published technical values with the pre-batch database, read-only."""

import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"


def catalogs(path):
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        return {
            key: json.loads(specs).get("catalog", {})
            for key, specs in db.execute(
                "SELECT catalog_key, specifications FROM vehicle_variants "
                "WHERE catalog_key IS NOT NULL"
            )
        }


def value(fact):
    return {k: fact.get(k) for k in ("value", "unit")}


def main():
    baseline = json.loads((OUT.parent / "us-base-07-baseline.json").read_text(encoding="utf-8"))
    before, after = catalogs(ROOT / baseline["database"]), catalogs(ROOT / "autoexpert.db")
    tables = json.loads((OUT / "catalog-tables.json").read_text(encoding="utf-8"))
    changes, actions, keys = [], Counter(), set()
    for group in tables["delta_from_previous_batch"]:
        for member in group["members"]:
            key = member["catalog_key"]
            assert key not in keys
            keys.add(key)
            old, new = before.get(key), after[key]
            differences = []
            for field, fact in new["facts"].items():
                if fact.get("status") != "CONFIRMED":
                    continue
                previous = old.get("facts", {}).get(field, {}) if old else {}
                if previous.get("status") != "CONFIRMED" or value(previous) != value(fact):
                    differences.append(
                        {
                            "field": field,
                            "change": "NEW_CONFIGURATION_FACT"
                            if old is None
                            else (
                                "NEWLY_CONFIRMED_FIELD"
                                if previous.get("status") != "CONFIRMED"
                                else "CORRECTED_VALUE"
                            ),
                            "before": value(previous) if previous else None,
                            "after": value(fact),
                            "documentary_source": fact.get("documentary_source"),
                        }
                    )
            action = (
                "NEW_CONFIGURATION"
                if old is None
                else ("EXISTING_CONFIGURATION_NEW_VALUES" if differences else "EVIDENCE_ONLY")
            )
            actions[action] += 1
            changes.append(
                {
                    "catalog_key": key,
                    "make": new["make"],
                    "model": new["model"],
                    "generation": new["generation_code"],
                    "year": new["model_year"],
                    "configuration": new["configuration"],
                    "action": action,
                    "new_confirmed_values": differences,
                }
            )
    counts = Counter(f["change"] for row in changes for f in row["new_confirmed_values"])
    metrics = {
        "batch_id": "us-base-catalog-07",
        "status": "PASS",
        "configuration_actions": dict(actions),
        "annual_fact_values": dict(counts),
        "counting_basis": (
            "One confirmed field value per exact model-year configuration. "
            "Shared values across years/drive variants are counted per applicability; "
            "this is not a count of independent discoveries or documents. "
            "Evidence-only changes and research rows contribute zero."
        ),
        "records": changes,
    }
    assert actions["NEW_CONFIGURATION"] == 132
    assert actions["EXISTING_CONFIGURATION_NEW_VALUES"] == 4
    assert actions["EVIDENCE_ONLY"] == 9
    (OUT / "new-confirmed-data.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in metrics.items() if k != "records"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
