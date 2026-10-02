"""Download and cache the public US sources used by the US tech database prompt.

Every response is stored once under data_work/ (raw/ folders are git-ignored) and
recorded in a manifest CSV with URL, HTTP status, size, sha256 and retrieval time.
Cached files are not downloaded again.

Subcommands:
  epa                      EPA fueleconomy.gov vehicles.csv.zip -> data_work/_shared/raw/epa/
  vpic-models MAKE Y1 Y2   vPIC GetModelsForMakeYear per year -> data_work/_shared/raw/vpic/
  vpic-canada MAKE MODEL Y1 Y2   vPIC Canadian specifications (metric) per year
  recalls MAKE MODEL Y1 Y2       NHTSA recallsByVehicle per year
  complaints MAKE MODEL Y1 Y2    NHTSA complaintsByVehicle per year
  carmans MAKE SLUG Y1 Y2        carmans.net owner-manual PDF copies (Appendix B fallback)
  url DEST URL                   one arbitrary public file (e.g. NHTSA flat file)
"""

from __future__ import annotations

import csv
import hashlib
import random
import re
import ssl
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urljoin

import httpx

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data_work"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
FIELDS = [
    "kind",
    "make",
    "model",
    "year",
    "page_url",
    "url",
    "http_status",
    "bytes",
    "sha256",
    "retrieved_at",
    "path",
    "status",
    "note",
]


def client():
    return httpx.Client(
        headers={"User-Agent": UA},
        timeout=120,
        follow_redirects=True,
        verify=ssl.create_default_context(),  # system roots, as backend providers do
    )


def record(manifest: Path, row: dict) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    new = not manifest.exists()
    for attempt in range(5):  # OneDrive sync can briefly lock the manifest
        try:
            with manifest.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                if new:
                    writer.writeheader()
                writer.writerow({k: row.get(k, "") for k in FIELDS})
            return
        except PermissionError:
            time.sleep(2 * (attempt + 1))
    raise PermissionError(f"manifest locked: {manifest}")


def cached(manifest: Path, url: str) -> dict | None:
    if not manifest.exists():
        return None
    with manifest.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["url"] == url and row["status"] == "ok" and (ROOT / row["path"]).exists():
                return row
    return None


def download(
    http, url, dest: Path, manifest: Path, meta: dict, pause=(1.0, 2.0), referer=None
) -> dict:
    hit = cached(manifest, url)
    if hit:
        return hit
    time.sleep(random.uniform(*pause))
    row = {**meta, "url": url, "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds")}
    try:
        response = http.get(url, headers={"Referer": referer} if referer else None)
    except httpx.HTTPError as exc:
        row.update(http_status="ERROR", status="error", note=type(exc).__name__)
        record(manifest, row)
        return row
    row["http_status"] = response.status_code
    # api.nhtsa.gov answers "no results" with HTTP 400 and a successful empty body.
    empty_nhtsa = (
        response.status_code == 400 and b"Results returned successfully" in response.content
    )
    if empty_nhtsa:
        row["note"] = "empty result (NHTSA returns HTTP 400 for zero matches)"
    if response.status_code != 200 and not empty_nhtsa:
        row.update(status="not_found" if response.status_code == 404 else "error")
        record(manifest, row)
        return row
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)
    row.update(
        bytes=len(response.content),
        sha256=hashlib.sha256(response.content).hexdigest(),
        path=dest.relative_to(ROOT).as_posix(),
        status="ok",
    )
    record(manifest, row)
    return row


def years(a, b):
    return range(int(a), int(b) + 1)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def cmd_epa(http, _args):
    raw = WORK / "_shared" / "raw" / "epa"
    row = download(
        http,
        "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
        raw / "vehicles.csv.zip",
        WORK / "_shared" / "manifest.csv",
        {"kind": "epa_vehicles_csv"},
    )
    print(row["status"], row.get("sha256"), row.get("bytes"))


def cmd_vpic_models(http, args):
    make, y1, y2 = args
    for year in years(y1, y2):
        url = (
            "https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/"
            f"make/{quote(make)}/modelyear/{year}?format=json"
        )
        row = download(
            http,
            url,
            WORK / "_shared" / "raw" / "vpic" / f"models_{slug(make)}_{year}.json",
            WORK / "_shared" / "manifest.csv",
            {"kind": "vpic_models", "make": make, "year": year},
        )
        print(year, row["status"])


def _per_year(http, args, kind, url_fn, folder):
    make, model, y1, y2 = args
    for year in years(y1, y2):
        row = download(
            http,
            url_fn(make, model, year),
            WORK / slug(make) / "raw" / folder / f"{slug(model)}_{year}.json",
            WORK / slug(make) / "manifest.csv",
            {"kind": kind, "make": make, "model": model, "year": year},
        )
        print(kind, model, year, row["status"], row.get("bytes"))


def cmd_vpic_canada(http, args):
    _per_year(
        http,
        args,
        "vpic_canada_specs",
        lambda mk, md, y: (
            "https://vpic.nhtsa.dot.gov/api/vehicles/GetCanadianVehicleSpecifications/"
            f"?year={y}&make={quote(mk)}&model={quote(md)}&units=Metric&format=json"
        ),
        "vpic_canada",
    )


def cmd_recalls(http, args):
    _per_year(
        http,
        args,
        "nhtsa_recalls",
        lambda mk, md, y: (
            "https://api.nhtsa.gov/recalls/recallsByVehicle"
            f"?make={quote(mk)}&model={quote(md)}&modelYear={y}"
        ),
        "nhtsa_recalls",
    )


def cmd_complaints(http, args):
    _per_year(
        http,
        args,
        "nhtsa_complaints",
        lambda mk, md, y: (
            "https://api.nhtsa.gov/complaints/complaintsByVehicle"
            f"?make={quote(mk)}&model={quote(md)}&modelYear={y}"
        ),
        "nhtsa_complaints",
    )


def cmd_carmans(http, args):
    """Owner-manual copies; the page's PDF viewer reveals the file via its `file=` parameter."""
    make, page_slug, y1, y2 = args
    manifest = WORK / slug(make) / "raw" / "manuals" / "manifest.csv"
    for year in years(y1, y2):
        page = f"https://www.carmans.net/{year}-{page_slug}/"
        time.sleep(random.uniform(2, 5))
        try:
            response = http.get(page)
        except httpx.HTTPError as exc:
            record(
                manifest,
                {
                    "kind": "carmans_manual",
                    "make": make,
                    "model": page_slug,
                    "year": year,
                    "page_url": page,
                    "status": "error",
                    "note": type(exc).__name__,
                },
            )
            continue
        found = re.search(r"viewer\.html\?file=([^#\"&]+\.pdf)", response.text or "")
        if response.status_code != 200 or not found:
            record(
                manifest,
                {
                    "kind": "carmans_manual",
                    "make": make,
                    "model": page_slug,
                    "year": year,
                    "page_url": page,
                    "http_status": response.status_code,
                    "status": "not_found",
                },
            )
            print(year, page_slug, "not_found")
            continue
        pdf = urljoin(page, found.group(1))
        row = download(
            http,
            pdf,
            WORK / slug(make) / "raw" / "manuals" / f"{year}-{page_slug}.pdf",
            manifest,
            {
                "kind": "carmans_manual",
                "make": make,
                "model": page_slug,
                "year": year,
                "page_url": page,
            },
            pause=(2, 5),
        )
        print(year, page_slug, row["status"], row.get("bytes"))


def cmd_pages(http, args):
    """HTML pages with a site-specific crawl delay: pages MAKE FOLDER DELAY_S URL [URL ...]."""
    make, folder, delay, *urls = args
    for url in urls:
        name = slug(url.split("://", 1)[1])[:150] + ".html"
        row = download(
            http,
            url,
            WORK / slug(make) / "raw" / folder / name,
            WORK / slug(make) / "manifest.csv",
            {"kind": folder, "make": make, "page_url": url},
            pause=(float(delay), float(delay) + 2),
        )
        print(row["status"], row.get("bytes"), url)


def cmd_url(http, args):
    """url DEST URL [REFERER]: the referer is the official page that links the file."""
    dest, url, *rest = args
    referer = rest[0] if rest else None
    row = download(
        http,
        url,
        ROOT / dest,
        WORK / "_shared" / "manifest.csv",
        {"kind": "file", "page_url": referer or ""},
        pause=(1, 2),
        referer=referer,
    )
    print(row["status"], row.get("bytes"), row.get("sha256"))


COMMANDS = {
    "epa": cmd_epa,
    "vpic-models": cmd_vpic_models,
    "vpic-canada": cmd_vpic_canada,
    "recalls": cmd_recalls,
    "complaints": cmd_complaints,
    "carmans": cmd_carmans,
    "pages": cmd_pages,
    "url": cmd_url,
}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    with client() as http:
        COMMANDS[argv[0]](http, argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
