"""US owner's manuals from Hyundai's official web-manual service (ownersmanual.hyundai.com).

The service's own public JSON API (no login, no VIN; no robots.txt on the host) lists, per
model name and country U.S.A (countryCode B28, langCode en_US), the model years and project
codes; the owner's-manual PDF of a project/year comes from the same API. This mirrors the
Kia service found by the portal research (ownersmanual.kia.com, same platform).

Output: RAW_ROOT/official/hyundai/ownersmanual.hyundai.com/<proj>_<year>_<fuel>.pdf and
data_work/_shared/manifest_official/ownersmanual.hyundai.com.csv (same format as
collect_official.py), so extract_manual_facts.py picks the PDFs up.

  .venv/Scripts/python.exe scripts/collect_hmc_manuals.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_official import FIELDS  # noqa: E402
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256  # noqa: E402

BASE = "https://ownersmanual.hyundai.com"
HOST = "ownersmanual.hyundai.com"
MODELS = {  # API model name -> registry line
    "SONATA": "hyundai/sonata", "SONATA HYBRID": "hyundai/sonata", "ELANTRA": "hyundai/elantra",
    "ELANTRA HYBRID": "hyundai/elantra", "ELANTRA N": "hyundai/elantra", "TUCSON": "hyundai/tucson",
    "TUCSON HYBRID": "hyundai/tucson", "TUCSON PLUG-IN HYBRID": "hyundai/tucson", "SANTA FE": "hyundai/santa-fe",
    "SANTA FE HYBRID": "hyundai/santa-fe", "SANTA FE PLUG-IN HYBRID": "hyundai/santa-fe",
    "SANTA FE SPORT": "hyundai/santa-fe-sport", "ACCENT": "hyundai/accent", "KONA": "hyundai/kona",
    "KONA ELECTRIC": "hyundai/kona", "KONA N": "hyundai/kona",
}


def main() -> int:
    fetcher = Fetcher(pause=(2.0, 4.0), timeout=180, headers={"Accept": "application/json"})
    manifest = Manifest(WORK / "_shared" / "manifest_official" / f"{HOST}.csv", FIELDS)
    log = []
    try:
        for name, line in MODELS.items():
            url = f"{BASE}/api/v3/hmc/model?" + urlencode({"modelName": name, "countryCode": "B28", "langCode": "en_US"})
            response = fetcher.get(url)
            if response is None or response.status_code != 200:
                log.append(f"{name}: model list HTTP {response.status_code if response else 'ERROR'}")
                continue
            data = response.json()
            for year, entries in (data.get("yearModels") or {}).items():
                if not 2014 <= int(year) <= 2026:
                    continue
                for entry in entries:
                    proj, fuel = entry["projCode"], entry.get("fuel") or ""
                    query = {"projectCode": proj, "year": year, "langCode": "en_US", "countryCode": "B28", "fuel": fuel}
                    api = f"{BASE}/api/v2/hmc/model/owners-manuals?" + urlencode(query)
                    reply = fetcher.get(api)
                    pdf_url = None
                    if reply is not None and reply.status_code == 200:
                        try:
                            payload = reply.json()
                        except json.JSONDecodeError:
                            payload = {}
                        manual = (payload.get("omManual") or {}) if isinstance(payload, dict) else {}
                        pdf = manual.get("pdfManual") or manual.get("pdfUrl")
                        if isinstance(pdf, dict):
                            pdf = pdf.get("url") or pdf.get("path")
                        if pdf:
                            pdf_url = pdf if pdf.startswith("http") else BASE + pdf
                    if not pdf_url:
                        log.append(f"{name} {year} {proj} {fuel}: no PDF in the API answer")
                        continue
                    meta = {"make": "hyundai", "lines": line, "years": year, "doc_type": "owners_manual",
                            "title": f"{year} {name.title()} Owner's Manual ({proj}, {fuel}, U.S.A en_US)", "url": pdf_url}
                    if manifest.ok(pdf_url):
                        continue
                    pdf_response = fetcher.get(pdf_url)
                    body = pdf_response.content if pdf_response is not None else b""
                    if pdf_response is None or pdf_response.status_code != 200 or not body.startswith(b"%PDF"):
                        manifest.add({**meta, "http_status": pdf_response.status_code if pdf_response else "ERROR",
                                      "retrieved_at": now(), "status": "error"})
                        continue
                    dest = RAW_ROOT / "official" / "hyundai" / HOST / f"{proj}_{year}_{fuel or 'na'}_{name.replace(' ', '-')}.pdf"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(body)
                    manifest.add({**meta, "http_status": 200, "bytes": len(body), "sha256": sha256(body),
                                  "retrieved_at": now(), "path": dest.relative_to(RAW_ROOT).as_posix(), "status": "ok"})
                    log.append(f"{name} {year} {proj} {fuel}: ok {len(body)}")
                    print(log[-1], flush=True)
    except Blocked as exc:
        log.append(f"STOPPED: {exc}")
    (WORK / "_shared" / "official_manuals" / "hyundai_hmc_api_log.txt").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log[-10:]), "requests", fetcher.requests)
    return 0


if __name__ == "__main__":
    sys.exit(main())
