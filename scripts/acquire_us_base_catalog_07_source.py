"""Acquire independently located factory documents for source batch 07 only."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".localdata/us-base-catalog-07-source-documents"
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
URLS = {
    "toyota-corolla-2017": "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2017.pdf",
    "toyota-corolla-2018": "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2018.pdf",
    "toyota-corolla-2019": "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2019.pdf",
    "volkswagen-jetta-2019-order-guide": "https://www.auto-brochures.com/makes/Volkswagen/Jetta/VW_US%20Jetta_2019-og.pdf",
    "volkswagen-jetta-seventh-generation": "https://www.volkswagen-newsroom.com/en/press-releases/world-premiere-of-the-completely-new-jetta-in-detroit-580",
    "toyota-corolla-eleventh-generation": "https://pressroom.toyota.com/toyota-reveals-next-generation-corolla-june6/",
    "toyota-corolla-2020-successor": "https://pressroom.toyota.com/all-new-2020-toyota-corolla-sedan-greater-than-ever/",
    "toyota-corolla-2020": "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2020-3.pdf",
    "toyota-corolla-2021": "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2021.pdf",
    "toyota-corolla-twelfth-generation": "https://pressroom.toyota.com/all-new-2020-toyota-corolla-ready-to-rock-the-sedan-world/",
}


def main() -> None:
    PRIVATE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    receipt_path = OUT / "acquisition-receipts.json"
    existing = {
        row["name"]: row
        for row in json.loads(receipt_path.read_text(encoding="utf-8"))
    } if receipt_path.exists() else {}
    rows = []
    for name, url in URLS.items():
        if name in existing and (ROOT / existing[name]["path"]).exists():
            rows.append(existing[name])
            continue
        started = time.perf_counter()
        request = urllib.request.Request(
            url, headers={"User-Agent": "AutoExpert/1.0 local catalog source review"}
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        media_type = "application/pdf" if raw.startswith(b"%PDF-") else "text/html"
        expected = b"jetta" if "jetta" in name else b"corolla"
        if status != 200 or (media_type == "text/html" and expected not in raw.lower()):
            raise ValueError(f"INVALID_SOURCE:{name}:{status}:{content_type}")
        digest = hashlib.sha256(raw).hexdigest()
        path = PRIVATE / digest
        path.write_bytes(raw)
        rows.append(
            {
                "name": name,
                "url": url,
                "http_status": status,
                "sha256": digest,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "media_type": media_type,
                "byte_size": len(raw),
                "observed_at": datetime.now(UTC).isoformat(),
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "cost_usd": "0.00",
            }
        )
    (OUT / "acquisition-receipts.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"documents": len(rows), "bytes": sum(row["byte_size"] for row in rows)}))


if __name__ == "__main__":
    main()
