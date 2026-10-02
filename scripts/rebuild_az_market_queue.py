"""Rebuild dated AZ-first queue from published observations, without network calls."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.services.market_priority import current_queue  # noqa: E402


def main():
    with SessionLocal() as db:
        result = current_queue(db)
    output = ROOT / "deliverables/VerifiedData/market-priority"
    output.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    (output / "az-market-queue.json").write_text(encoded, encoding="utf-8")
    (ROOT / "data/manifests/az-market-batch-queue.json").write_text(encoded, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["overall"],
                "observed_models": result["discovery_records"],
                "primary_us": len(result["PRIMARY_US_MARKET_QUEUE"]),
                "secondary_us": len(result["SECONDARY_US_MARKET_QUEUE"]),
                "calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
