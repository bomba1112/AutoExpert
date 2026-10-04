"""Owner's manuals of models we do not cover, for the library of other markets (owner decision
2026-10-05: the European VW models Polo, Up!, Sharan, Scirocco, T-Roc go to the EU library and
never to the database).

1. The make's carmans.net category page lists the posts; the posts of the named models are taken.
2. Every PDF of a post is downloaded once (one request at a time, 2-5 s pause) to
   RAW_ROOT/manuals/<make>/carmans_library/ and recorded in data_work/_shared/manifest_carmans_library.csv
   (its own manifest: these files are never a source of our lines).
3. Page text is cached (scripts/pdf_text_store.py) and the edition is read from the document
   (scripts/manual_editions.market_of); each file is registered in data_work/_library/manifest.csv
   with the market found. A file found to be a US edition is reported, not used.

  .venv/Scripts/python.exe scripts/carmans_library.py volkswagen polo up sharan scirocco t-roc
  (then: uv run --no-project --with pypdfium2 python scripts/pdf_text_store.py manuals/volkswagen/carmans_library
         uv run --no-project --with pdfplumber --with pypdfium2 python scripts/carmans_library.py volkswagen --register)
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carmans_category import PDF_LINK, category_posts  # noqa: E402
from collect_carmans import FIELDS  # noqa: E402
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256  # noqa: E402

MANIFEST = WORK / "_shared" / "manifest_carmans_library.csv"
LIBRARY = WORK / "_library" / "manifest.csv"
LIBRARY_FIELDS = ["make", "model", "generation_or_years", "market", "market_markers", "source_url", "path",
                  "sha256", "retrieved_at", "pages"]
LIBRARY_MAKE = {"volkswagen": "vw"}


def download(make: str, models: list[str]) -> int:
    fetcher = Fetcher(pause=(2.0, 5.0), timeout=240)
    manifest = Manifest(MANIFEST, FIELDS)
    category = Manifest(WORK / "_shared" / "manifest_carmans.csv", FIELDS)
    try:
        _, posts = category_posts(fetcher, category, make)
        wanted = []
        for url in posts:
            post = url.rstrip("/").rsplit("/", 1)[-1]
            model = re.sub(r"^\d{4}-", "", post)
            model = re.sub(r"-\d$", "", model)
            hit = next((m for m in models if model in (f"{make}-{m}", f"vw-{m}")), None)
            if hit:
                wanted.append((post, url, hit))
        print(f"{len(wanted)} posts of {models}", flush=True)
        for post, url, model in wanted:
            year = re.match(r"(\d{4})-", post)
            response = fetcher.get(url)
            status = response.status_code if response is not None else "ERROR"
            links = []
            for viewer, href in PDF_LINK.findall(response.text if response is not None else ""):
                link = urljoin(url, unquote(viewer or href))
                if link not in links:
                    links.append(link)
            meta = {"make": make, "line": f"library/{model}", "year": year.group(1) if year else "", "post": post, "page_url": url}
            manifest.add({**meta, "kind": "page", "url": url, "http_status": status, "retrieved_at": now(),
                          "status": "ok" if status == 200 else "error", "note": " | ".join(links)})
            for n, pdf_url in enumerate(links):
                if manifest.ok(pdf_url):
                    continue
                r = fetcher.get(pdf_url, headers={"Referer": url})
                code = r.status_code if r is not None else "ERROR"
                if code != 200 or not r.content.startswith(b"%PDF"):
                    manifest.add({**meta, "kind": "pdf", "url": pdf_url, "http_status": code, "retrieved_at": now(), "status": "error"})
                    print("pdf_error", post, code, flush=True)
                    continue
                name = post if len(links) == 1 else f"{post}--{Path(pdf_url).stem}"
                dest = RAW_ROOT / "manuals" / make / "carmans_library" / f"{name}.pdf"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                manifest.add({**meta, "kind": "pdf", "url": pdf_url, "http_status": code, "bytes": len(r.content),
                              "sha256": sha256(r.content), "retrieved_at": now(), "path": dest.relative_to(RAW_ROOT).as_posix(),
                              "status": "ok"})
                print("downloaded", post, len(r.content), flush=True)
    except Blocked as exc:
        print("STOPPED: repeated block", exc, flush=True)
        return 3
    print("requests", fetcher.requests, flush=True)
    return 0


def register(make: str) -> int:
    from manual_editions import market_of

    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["make"] == make and r["kind"] == "pdf" and r["status"] == "ok"]
    with LIBRARY.open(encoding="utf-8", newline="") as handle:
        library = list(csv.DictReader(handle))
    have = {r["sha256"] for r in library}
    by_sha = {}
    for r in rows:
        by_sha.setdefault(r["sha256"], []).append(r)
    added, us = 0, []
    for sha, files in by_sha.items():
        store = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
        if not store.exists():
            print("no page text yet:", files[0]["path"])
            continue
        pages = json.load(gzip.open(store, "rt", encoding="utf-8"))["pages"]
        text = "".join(pages)
        market, marks = market_of(pages) if len(text) > 2000 else ("UNKNOWN", {"rule": "no text layer"})
        if market == "US":
            us.append(files[0]["post"])
        if sha in have:
            continue
        years = sorted({int(f["year"]) for f in files if f["year"]})
        library.append({"make": LIBRARY_MAKE.get(make, make), "model": files[0]["line"].split("/")[-1],
                        "generation_or_years": f"carmans posts {years[0]}-{years[-1]}" if years else "carmans posts",
                        "market": market, "market_markers": json.dumps(marks, ensure_ascii=False),
                        "source_url": files[0]["url"], "path": "rawstore:" + files[0]["path"], "sha256": sha,
                        "retrieved_at": files[0]["retrieved_at"], "pages": len(pages)})
        added += 1
    with LIBRARY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LIBRARY_FIELDS)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in LIBRARY_FIELDS} for r in library)
    print(f"library: {len(by_sha)} files, added {added}; US editions among them (not used): {us}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--register" in args:
        sys.exit(register(args[0]))
    sys.exit(download(args[0], args[1:]))
