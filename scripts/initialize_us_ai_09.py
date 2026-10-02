"""Audit the existing catalogue and apply the owner scope without changing stored facts."""

import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.catalog_scope import catalog_in_active_scope  # noqa: E402
from app.services.catalog_verification import base_catalog_counts, catalog_excluded  # noqa: E402


def main():
    out = ROOT / "deliverables/VerifiedData/us-ai-verify-09"
    destination = out / "scope-baseline.json"
    if destination.exists():
        print("Existing immutable scope baseline reused")
        return
    receipt = json.loads((out / "backup-restore.json").read_text())
    assert receipt["status"] == "PASS"
    backup = ROOT / ".backups" / ("master-" + receipt["timestamp"]) / "database.sqlite3"
    policy_path = ROOT / "data/manifests/az-market-priority-policy.json"
    old = json.loads(policy_path.read_text(encoding="utf-8"))
    new = {
        **old,
        "version": "us-market-base-5",
        "basis": "OWNER_US_AI_DRAFT_SCOPE_2026_09_25",
        "minimum_model_year": 2005,
        "minimum_model_year_overrides": {"Mercedes-Benz": 2000, "BMW": 2000},
        "active_layer": "US_BASE_CATALOG_MAKE_YEAR_SCOPE",
    }
    new["notes"] = [
        *old["notes"],
        "2026-09-25 owner scope: Mercedes-Benz/BMW MY2000+, other allowed makes MY2005+. "
        "Historical rows retained; scope changes are not technical verification.",
    ]
    with sqlite3.connect(backup) as db:
        rows = [
            (key, json.loads(spec)["catalog"])
            for key, spec in db.execute(
                "SELECT catalog_key,specifications FROM vehicle_variants "
                "WHERE published_revision_id IS NOT NULL AND is_demo=0"
            )
            if "catalog" in json.loads(spec)
        ]
    historical = [
        (key, c) for key, c in rows if catalog_in_active_scope(c, old) and not catalog_excluded(c)
    ]
    active = [(key, c) for key, c in historical if catalog_in_active_scope(c, new)]
    excluded = [
        dict(
            catalog_key=key,
            make=c["make"],
            model=c["model"],
            generation=c.get("generation_code"),
            model_year=c["model_year"],
            stored_unchanged=True,
        )
        for key, c in historical
        if not catalog_in_active_scope(c, new)
    ]
    report = {
        "batch_id": "us-ai-verify-09",
        "scope_change_is_verification": False,
        "historical_basic": base_catalog_counts(historical),
        "historical_strict": base_catalog_counts(historical, require_us_seating=True),
        "active_baseline_basic": base_catalog_counts(active),
        "active_baseline_strict": base_catalog_counts(active, require_us_seating=True),
        "scope_excluded_rows": excluded,
        "old_scope": {
            k: old.get(k)
            for k in (
                "primary_makes",
                "allowed_markets",
                "minimum_model_year",
                "minimum_model_year_overrides",
            )
        },
        "new_scope": {
            k: new.get(k)
            for k in (
                "primary_makes",
                "allowed_markets",
                "minimum_model_year",
                "minimum_model_year_overrides",
            )
        },
    }
    baseline = json.loads((ROOT / "deliverables/VerifiedData/us-base-07-baseline.json").read_text())
    baseline["database"] = backup.relative_to(ROOT).as_posix()
    baseline["database_sha256"] = hashlib.sha256(backup.read_bytes()).hexdigest()
    baseline["ui_hashes"] = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in baseline["ui_hashes"]
    }
    baseline["rules_hashes"] = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in baseline["rules_hashes"]
    }
    (out / "baseline.json").write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    history = ROOT / "docs/CHECKPOINT_US_BASE_CATALOG_08.md"
    if not history.exists():
        shutil.copy2(ROOT / "docs/CHECKPOINT_US_BASE_CATALOG.md", history)
    policy_path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k
                in {
                    "historical_basic",
                    "historical_strict",
                    "active_baseline_basic",
                    "active_baseline_strict",
                }
            }
        )
    )


if __name__ == "__main__":
    main()
