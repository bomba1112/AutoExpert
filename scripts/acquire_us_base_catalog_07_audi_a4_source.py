"""Acquire Audi-authored US A4 B9 MY2017-18 evidence; no shared ledger writes."""

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
RECEIPT = WORK / "acquisition-audi-a4.json"
URLS = {
    "audi-a4-2017-brochure": "https://salesrater.com/uploads/brochures/2018_Audi_A4.pdf?brochureId=2823",
    "audi-a4-2017-ultra-window-label": "https://monroneylabels.com/cars/13678935-2017-audi-a4/window_sticker.pdf?cfl=5247144447",
    "audi-a4-2017-manual-release": "https://www.autospies.com/iphone/article.aspx?submissionId=89690",
    "audi-a4-2017-engines": "https://static.nhtsa.gov/odi/tsbs/2016/SB-10105867-2280.pdf",
    "audi-a4-2018-ultra-window-label": "https://monroneylabels.com/cars/14193012-2018-audi-a4/window_sticker.pdf?cfl=5101225076",
    "audi-a4-2018-quattro-window-label": "https://monroneylabels.com/cars/3698965-2018-audi-a4/window_sticker.pdf?cfl=3396240023",
    "audi-a4-2018-pricing-release": "https://jomomag.blogspot.com/2017/05/usa-audi-announces-2018-model-year.html",
    "audi-a4-2018-tire-chart": "https://static.nhtsa.gov/odi/tsbs/2017/MC-10128253-9999.pdf",
    "audi-a4-8w-generation": "https://static.nhtsa.gov/odi/tsbs/2024/MC-10253261-0001.pdf",
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
        started = time.perf_counter()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AutoExpert local source review"})
        with urllib.request.urlopen(req, timeout=70) as response:
            raw, status = response.read(), response.status
            media_type = response.headers.get_content_type()
        assert status == 200, (name, status)
        assert raw.startswith(b"%PDF-") if media_type == "application/pdf" else raw.lstrip().lower().startswith(b"<!doctype html"), name
        digest = hashlib.sha256(raw).hexdigest()
        path = PRIVATE / digest
        path.write_bytes(raw)
        rows.append({
            "name": name, "url": url, "http_status": status, "sha256": digest,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "media_type": media_type, "byte_size": len(raw),
            "observed_at": datetime.now(UTC).isoformat(),
            "latency_ms": round((time.perf_counter() - started) * 1000), "cost_usd": "0.00",
        })
        RECEIPT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"documents": len(rows), "bytes": sum(row["byte_size"] for row in rows), "receipt": str(RECEIPT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
