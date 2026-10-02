"""Repeat the complete USA candidate-universe ingestion without product DB writes.

The official EPA ZIP is reused from the local cache and vPIC make/year responses
are cached. This workflow does not bypass factory-evidence publication gates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-catalog-universe"
STEPS = (
    ("epa_universe", "build_us_catalog_candidate_universe.py"),
    ("candidate_sqlite_index", "index_us_catalog_candidates_sqlite.py"),
    ("read_only_published_join", "us_catalog_universe_join.py"),
    ("cached_vpic_model_year_crosscheck", "crosscheck_us_universe_vpic.py"),
    ("generation_draft_queue", "build_us_generation_hypotheses.py"),
    ("generation_scoped_powertrain_groups", "group_us_candidate_powertrains_by_generation.py"),
    ("exception_router", "route_us_catalog_exceptions.py"),
    ("named_checkpoint", "report_us_catalog_universe.py"),
)


def run(*, python: Path, out: Path = OUT) -> dict:
    source = ROOT / ".localdata/epa-bulk-cache/vehicles-current.zip"
    if not source.exists():
        raise FileNotFoundError(
            "Official EPA bulk ZIP cache is missing: " + str(source)
        )
    steps = []
    for label, script in STEPS:
        started = time.perf_counter()
        try:
            subprocess.run(
                [str(python), str(ROOT / "scripts" / script)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            print((exc.stderr or exc.stdout or "")[-4000:], file=sys.stderr)
            raise
        steps.append(
            {
                "step": label,
                "script": "scripts/" + script,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "status": "PASS",
            }
        )
        print(f"{label}: {steps[-1]['elapsed_seconds']}s", flush=True)
    join = json.loads((out / "candidate-join-summary.json").read_text(encoding="utf-8"))
    vpic = json.loads((out / "vpic-crosscheck-summary.json").read_text(encoding="utf-8"))
    exceptions = json.loads((out / "exception-routing/summary.json").read_text(encoding="utf-8"))
    report = {
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "scope": "17 approved USA makes; Mercedes-Benz/BMW MY2000+, others MY2005+",
        "steps": steps,
        "candidate_rows": join["candidate_rows"],
        "published_base_ready_configurations_observed": join[
            "published_base_ready_configurations"
        ],
        "newly_auto_verified_models": join["newly_auto_verified_models"],
        "vpic_requests_this_run": vpic["counts"].get("network_calls", 0),
        "vpic_cache_hits_this_run": vpic["counts"].get("cache_hits", 0),
        "vpic_make_year_request_keys": vpic["requested_make_years"],
        "manual_exception_route_models": exceptions["counts"]["manual_review_models"],
        "production_database_writes": 0,
        "publication_gate_changed": False,
    }
    (out / "pipeline-run.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    print(json.dumps(run(python=args.python), ensure_ascii=False))
