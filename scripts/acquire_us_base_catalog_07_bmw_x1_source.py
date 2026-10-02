"""Acquire official BMW USA X1 F48 sources into the private source cache."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".localdata/us-base-catalog-07-source-documents"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
RECEIPT = WORK / "acquisition-bmw-x1.json"
URLS = {
    "bmw-x1-2016-launch": "https://www.press.bmwgroup.com/usa/article/detail/T0220582EN_US/the-all-new-bmw-x1",
    "bmw-x1-2017-tech": "https://www.press.bmwgroup.com/usa/article/attachment/T0220582EN_US/391951",
    "bmw-x1-2018-tech": "https://www.press.bmwgroup.com/usa/article/attachment/T0220582EN_US/391953",
    "bmw-x1-2020-update": "https://www.press.bmwgroup.com/usa/article/detail/T0296549EN_US/the-2020-bmw-x1-sports-activity-vehicle",
}


def main() -> None:
    PRIVATE.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    existing = {row["name"]: row for row in json.loads(RECEIPT.read_text(encoding="utf-8"))} if RECEIPT.exists() else {}
    rows = []
    for name, url in URLS.items():
        if name in existing and (ROOT / existing[name]["path"]).exists():
            rows.append(existing[name])
            continue
        start = time.perf_counter()
        request = urllib.request.Request(url, headers={"User-Agent": "AutoExpert/1.0 local catalog source review"})
        with urllib.request.urlopen(request, timeout=35) as response:
            raw = response.read()
            status = response.status
        expected_pdf = name.endswith("-tech")
        assert status == 200 and (raw.startswith(b"%PDF-") if expected_pdf else b"BMW X1" in raw), (name, status)
        digest = hashlib.sha256(raw).hexdigest()
        path = PRIVATE / digest
        path.write_bytes(raw)
        rows.append({
            "name": name, "url": url, "http_status": status, "sha256": digest,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "media_type": "application/pdf" if expected_pdf else "text/html",
            "byte_size": len(raw), "observed_at": datetime.now(UTC).isoformat(),
            "latency_ms": round((time.perf_counter() - start) * 1000), "cost_usd": "0.00",
        })
    RECEIPT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"documents": len(rows), "bytes": sum(row["byte_size"] for row in rows)}))


if __name__ == "__main__":
    main()
