"""Daily check of new NHTSA recall campaigns for the cars in the garages (product phase, stage 2).
Run once a day by the server's scheduler (cron / Task Scheduler) from the repository root:

    AUTOEXPERT_DATABASE_URL=sqlite:///.../autoexpert.db python scripts/garage_recall_job.py

See app/services/garage_recalls.py. Asks only api.nhtsa.gov for the make / model / year of the cars
in the garages; writes garage_recall_notices and the garage feed, nothing else.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.services.garage_recalls import run  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as db:
        print(json.dumps(run(db)))
