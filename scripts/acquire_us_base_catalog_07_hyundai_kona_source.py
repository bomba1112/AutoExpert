"""Acquire Hyundai Motor America-authored Kona releases and OS-code bulletin privately."""

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
RECEIPT = WORK / "acquisition-hyundai-kona.json"
URLS = {
    "hyundai-kona-2018-pricing": "https://www.prnewswire.com/news-releases/2018-hyundai-kona-suv-pricing-released-a-crossover-for-urban-adventurers-300590920.html",
    "hyundai-kona-2019-pricing": "https://www.prnewswire.com/news-releases/hyundai-announces-pricing-for-2019-kona-300723441.html",
    "hyundai-kona-os-generation": "https://static.nhtsa.gov/odi/tsbs/2023/MC-10233547-0001.pdf",
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
        is_pdf = name == "hyundai-kona-os-generation"
        assert status == 200 and (raw.startswith(b"%PDF-") if is_pdf else b"Hyundai Motor America" in raw and b"Kona" in raw), (name, status)
        digest = hashlib.sha256(raw).hexdigest()
        path = PRIVATE / digest
        path.write_bytes(raw)
        rows.append({
            "name": name, "url": url, "http_status": status, "sha256": digest,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "media_type": "application/pdf" if is_pdf else "text/html", "byte_size": len(raw),
            "observed_at": datetime.now(UTC).isoformat(),
            "latency_ms": round((time.perf_counter() - start) * 1000), "cost_usd": "0.00",
        })
    RECEIPT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"documents": len(rows), "bytes": sum(row["byte_size"] for row in rows)}))


if __name__ == "__main__":
    main()
