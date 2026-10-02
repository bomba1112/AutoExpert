"""Snapshot and report the live US BASE_READY catalogue without changing vehicle data."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.catalog_buyer import active_us_base_rows, records  # noqa: E402
from app.services.catalog_verification import base_catalog_counts  # noqa: E402

OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"
BASELINE = OUT / "baseline.json"


def _fact(catalog: dict, name: str):
    fact = catalog.get("facts", {}).get(name) or {}
    if fact.get("status") != "CONFIRMED":
        return None
    return {"value": fact.get("value"), "unit": fact.get("unit")}


def _row(variant, catalog: dict) -> dict:
    return {
        "variant_id": variant.id,
        "revision_id": variant.published_revision_id,
        "make": catalog["make"],
        "model": catalog["model"],
        "generation": catalog.get("generation_code") or catalog["generation"],
        "market": catalog["original_market"],
        "model_year": catalog["model_year"],
        "configuration": catalog["configuration"],
        "confirmed_facts": {
            name: _fact(catalog, name)
            for name in catalog.get("facts", {})
            if _fact(catalog, name) is not None
        },
    }


def _state() -> dict:
    with SessionLocal() as db:
        rows = active_us_base_rows(records(db))
        keys = {v.catalog_key: _row(v, c) for v, c in rows}
        makes = {}
        for make in sorted({c["make"] for _, c in rows}):
            scoped = [(v, c) for v, c in rows if c["make"] == make]
            counts = base_catalog_counts(scoped)
            makes[make] = {
                **{k: v for k, v in counts.items() if k != "scope_note"},
                "earliest_model_year": min(c["model_year"] for _, c in scoped),
                "latest_model_year": max(c["model_year"] for _, c in scoped),
                "models_available": sorted({c["model"] for _, c in scoped}),
            }
        return {
            "observed_at": datetime.now(UTC).isoformat(),
            "counts": base_catalog_counts(rows),
            "by_make": makes,
            "rows": keys,
        }


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture_baseline() -> None:
    if BASELINE.exists():
        raise SystemExit("Baseline already exists; refusing to replace the frozen pre-batch state")
    started = time.perf_counter()
    state = _state()
    source_path = Path(get_settings().database_url.removeprefix("sqlite:///"))
    if not get_settings().database_url.startswith("sqlite:///"):
        raise SystemExit("SQLite baseline snapshot required for this local stage")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot = ROOT / ".backups" / f"us-base-catalog-07-pre-{stamp}.sqlite3"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source_path) as source, sqlite3.connect(snapshot) as target:
        source.backup(target)
        assert target.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not target.execute("PRAGMA foreign_key_check").fetchall()
    state["database_snapshot"] = snapshot.relative_to(ROOT).as_posix()
    state["snapshot_bytes"] = snapshot.stat().st_size
    state["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    _save(BASELINE, state)
    print(json.dumps({k: state[k] for k in ("counts", "database_snapshot", "elapsed_seconds")}))


def report() -> None:
    before = json.loads(BASELINE.read_text(encoding="utf-8"))
    after = _state()
    old, new = before["rows"], after["rows"]
    additions = [{"catalog_key": key, **new[key]} for key in sorted(new.keys() - old.keys())]
    changed_values = []
    evidence_only = []
    for key in sorted(old.keys() & new.keys()):
        previous, current = old[key], new[key]
        facts = {
            name: {"before": previous["confirmed_facts"].get(name), "after": fact}
            for name, fact in current["confirmed_facts"].items()
            if previous["confirmed_facts"].get(name) != fact
        }
        if facts:
            changed_values.append({"catalog_key": key, **current, "changed_facts": facts})
        elif previous["revision_id"] != current["revision_id"]:
            evidence_only.append(key)
    removed = sorted(old.keys() - new.keys())
    result = {
        "observed_at": after["observed_at"],
        "baseline_at": before["observed_at"],
        "before": before["counts"],
        "after": after["counts"],
        "by_make": after["by_make"],
        "new_base_ready": len(additions),
        "new_rows": additions,
        "existing_rows_with_new_or_corrected_values": changed_values,
        "evidence_only_revisions": evidence_only,
        "removed_from_active_scope": removed,
        "note": "Only source-backed active US BASE_READY rows count; changed facts are annual cells, not unique discoveries.",
    }
    _save(OUT / "progress.json", result)
    print(
        json.dumps(
            {
                "before": before["counts"],
                "after": after["counts"],
                "new_base_ready": len(additions),
                "changed_existing": len(changed_values),
                "evidence_only": len(evidence_only),
                "removed": len(removed),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("baseline", "report"))
    args = parser.parse_args()
    capture_baseline() if args.mode == "baseline" else report()
