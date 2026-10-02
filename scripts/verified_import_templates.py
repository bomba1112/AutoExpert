"""Generate blank contracts, never demonstration observations."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.schemas.verified_ownership import DATA_TYPES, OwnershipRecord  # noqa: E402

out = ROOT / "data/templates/ownership"
out.mkdir(parents=True, exist_ok=True)
(out / "observations.csv").write_text(
    ",".join(OwnershipRecord.model_fields) + "\n", encoding="utf-8"
)
(out / "record.schema.json").write_text(
    json.dumps(OwnershipRecord.model_json_schema(), indent=2), encoding="utf-8"
)
for kind, model in DATA_TYPES.items():
    (out / (kind.lower() + ".schema.json")).write_text(
        json.dumps(model.model_json_schema(), indent=2), encoding="utf-8"
    )
print("Empty CSV header and 6 typed contracts generated; no observations imported")
