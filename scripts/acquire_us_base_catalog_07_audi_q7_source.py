"""Acquire manufacturer-authored Audi Q7 US brochures into private source cache."""

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
RECEIPT = WORK / "acquisition-audi-q7.json"
URLS = {
    "audi-q7-2017": "https://www.auto-brochures.com/makes/Audi/Q7/Audi_US%20Q7_2017.pdf",
    "audi-q7-2018": "https://s3.amazonaws.com/cdn.autoipacket.com/brochures/audi/2018/2018.audi.q7.1532617022.005508.pdf",
    "audi-q7-2019": "https://www.auto-brochures.com/makes/Audi/Q7/Audi_US%20Q7_2019.pdf",
    "audi-q7-4m-generation": "https://static.nhtsa.gov/odi/tsbs/2025/MC-11016516-0001.pdf",
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
        with urllib.request.urlopen(request, timeout=50) as response:
            raw = response.read()
            status = response.status
        expected_pdf = True
        assert status == 200 and raw.startswith(b"%PDF-"), (name, status)
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
