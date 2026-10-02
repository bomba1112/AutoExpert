"""Batch collection from the public US government APIs for every line of Appendix A.

Two hosts, two independent processes (one request stream per host):

  nhtsa   api.nhtsa.gov
          1. products/vehicle/models per make x year x issue type (recalls r, complaints c)
          2. names mapped to lines (scripts/us_tech_lines.py); unmapped names are listed in
             data_work/_shared/nhtsa_unmapped_models.json for review
          3. recalls/recallsByVehicle and complaints/complaintsByVehicle per mapped name x year
  vpic    vpic.nhtsa.dot.gov
          GetModelsForMakeYear and GetCanadianVehicleSpecifications (metric, all models of a
          make in one call) per make x year

Responses are stored gzip-compressed under RAW_ROOT/nhtsa and RAW_ROOT/vpic and recorded
in data_work/_shared/manifest_<host>.csv; cached URLs are not requested again.

Usage:
  .venv/Scripts/python.exe scripts/collect_us_apis.py nhtsa [--make hyundai]
  .venv/Scripts/python.exe scripts/collect_us_apis.py vpic  [--make hyundai]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))

from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256, write_gz  # noqa: E402
from us_tech_lines import LINES, MAKE_ORDER, MAKES, nhtsa_line  # noqa: E402

FIELDS = [
    "kind", "make", "line", "model", "year", "url", "http_status", "bytes", "sha256",
    "retrieved_at", "path", "status", "note",
]
YEARS = range(2014, 2027)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def fetch_json(fetcher: Fetcher, manifest: Manifest, url: str, dest: Path, meta: dict):
    """Return the parsed JSON (cached or fresh) or None; record every request."""
    hit = manifest.ok(url)
    if hit:
        from us_tech_common import read_maybe_gz

        return json.loads(read_maybe_gz(RAW_ROOT / hit["path"]))
    response = fetcher.get(url)
    row = {**meta, "url": url, "retrieved_at": now()}
    if response is None:
        manifest.add({**row, "http_status": "ERROR", "status": "error"})
        return None
    row["http_status"] = response.status_code
    body = response.content
    # api.nhtsa.gov answers "no results" with HTTP 400 and a successful empty body.
    empty = response.status_code == 400 and b"Results returned successfully" in body
    if response.status_code != 200 and not empty:
        manifest.add({**row, "status": "not_found" if response.status_code == 404 else "error"})
        return None
    write_gz(dest, body)
    manifest.add(
        {
            **row,
            "bytes": len(body),
            "sha256": sha256(body),
            "path": dest.relative_to(RAW_ROOT).as_posix(),
            "status": "ok",
            "note": "empty result (HTTP 400 for zero matches)" if empty else "",
        }
    )
    return json.loads(body)


def selected_makes(make: str | None) -> list[str]:
    return [make] if make else MAKE_ORDER


def run_nhtsa(args) -> int:
    fetcher = Fetcher(pause=(1.0, 2.0))
    manifest = Manifest(WORK / "_shared" / "manifest_nhtsa.csv", FIELDS)
    base = "https://api.nhtsa.gov"
    unmapped: dict[str, list] = {}
    targets: list[tuple] = []
    # 1. model names per make/year/issue type
    for make in selected_makes(args.make):
        nhtsa_make = MAKES[make]["nhtsa"]
        for year in YEARS:
            for issue in ("r", "c"):
                url = f"{base}/products/vehicle/models?" + urlencode(
                    {"modelYear": year, "make": nhtsa_make, "issueType": issue}
                )
                data = fetch_json(
                    fetcher,
                    manifest,
                    url,
                    RAW_ROOT / "nhtsa" / "products" / make / f"{year}_{issue}.json.gz",
                    {"kind": f"products_{issue}", "make": make, "year": year},
                )
                for item in (data or {}).get("results", []):
                    model = item.get("model", "")
                    line = nhtsa_line(make, model)
                    if line is None:
                        unmapped.setdefault(make, []).append(model)
                        continue
                    if line.done or not (line.years[0] - 1 <= year <= line.years[1] + 1):
                        continue
                    targets.append((issue, line, model, year))
        print(make, "products done", flush=True)
    unmapped_path = WORK / "_shared" / f"nhtsa_unmapped_models{'_' + args.make if args.make else ''}.json"
    unmapped_path.write_text(
        json.dumps({k: sorted(set(v)) for k, v in unmapped.items()}, indent=1), encoding="utf-8"
    )
    # 2. recalls and complaints per mapped model name and year
    seen = set()
    for issue, line, model, year in targets:
        if (issue, model, year) in seen:
            continue
        seen.add((issue, model, year))
        kind = "recalls" if issue == "r" else "complaints"
        endpoint = "recalls/recallsByVehicle" if issue == "r" else "complaints/complaintsByVehicle"
        url = f"{base}/{endpoint}?" + urlencode(
            {"make": MAKES[line.make]["nhtsa"], "model": model, "modelYear": year}
        )
        data = fetch_json(
            fetcher,
            manifest,
            url,
            RAW_ROOT / "nhtsa" / kind / line.make / f"{slug(model)}_{year}.json.gz",
            {"kind": kind, "make": line.make, "line": line.key, "model": model, "year": year},
        )
        count = len((data or {}).get("results", [])) if data else "-"
        print(kind, line.key, model, year, count, flush=True)
    print("requests", fetcher.requests, flush=True)
    return 0


def run_vpic(args) -> int:
    fetcher = Fetcher(pause=(1.5, 3.0))
    manifest = Manifest(WORK / "_shared" / "manifest_vpic.csv", FIELDS)
    base = "https://vpic.nhtsa.dot.gov/api/vehicles"
    for make in selected_makes(args.make):
        vpic_make = MAKES[make]["vpic"]
        for year in YEARS:
            url = f"{base}/GetModelsForMakeYear/make/{vpic_make}/modelyear/{year}?format=json"
            fetch_json(
                fetcher,
                manifest,
                url,
                RAW_ROOT / "vpic" / "models" / make / f"{year}.json.gz",
                {"kind": "vpic_models", "make": make, "year": year},
            )
            url = f"{base}/GetCanadianVehicleSpecifications/?" + urlencode(
                {"year": year, "make": vpic_make, "model": "", "units": "Metric", "format": "json"}
            )
            data = fetch_json(
                fetcher,
                manifest,
                url,
                RAW_ROOT / "vpic" / "canada" / make / f"{year}.json.gz",
                {"kind": "vpic_canada_specs", "make": make, "year": year},
            )
            print(make, year, len((data or {}).get("Results", [])) if data else "-", flush=True)
    print("requests", fetcher.requests, flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("host", choices=["nhtsa", "vpic"])
    parser.add_argument("--make")
    args = parser.parse_args(argv)
    try:
        return run_nhtsa(args) if args.host == "nhtsa" else run_vpic(args)
    except Blocked as exc:
        print("STOPPED: repeated block", exc, flush=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
