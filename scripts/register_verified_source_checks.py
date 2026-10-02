"""Record checked sources/blockers without upgrading rights or publishing claims."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402

m = json.loads((ROOT / "data/manifests/verified-source-checks.json").read_text())
with SessionLocal() as db:
    for row in m["sources"]:
        current = db.get(SourceRegistry, row["id"])
        if current is not None:
            current.config = {**current.config, "latest_discovery_check": row}
            continue
        if current is None:
            current = SourceRegistry(
                id=row["id"], title=row["title"], state=row["status"], config={}
            )
            db.add(current)
        current.config = {
            **current.config,
            "checked_at": m["checked_at"],
            "owner": row["title"],
            "documentation_url": row["url"],
            "markets": [row["market"]],
            "data_types": [row["type"]],
            "limitations": row["reason"],
            "adapter": "manual",
            "authentication": "NONE_PUBLIC",
            "cost_model": "FREE",
            "storage_rights": "VERIFY_PER_DOCUMENT",
            "display_rights": "NOT_GRANTED",
            "commercial_reuse": False,
            "verified_rate_limit": None,
        }
    db.commit()
print(json.dumps({"source_checks": len(m["sources"]), "claims_published": 0}))
