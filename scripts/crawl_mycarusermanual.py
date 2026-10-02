"""Polite, resumable full crawl of mycarusermanual.com for one make (prompt Appendix E).

Navigation follows links found on the site only (make page -> model page -> generation
pages -> every section/subsection linked under the generation prefix). Raw HTML and
extracted text are stored under data_work/_mcum/raw/ (git-ignored); every request is
recorded in data_work/_mcum/manifest.csv. Pages already recorded with HTTP 200 are not
fetched again, so the crawl can be interrupted and resumed.

Usage:
  .venv/Scripts/python.exe scripts/crawl_mycarusermanual.py --make toyota \
      --models camry,corolla,rav4,highlander,prius --year-min 2014 --year-max 2026
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
import re
import ssl
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "_mcum"
BASE = "https://www.mycarusermanual.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
FIELDS = [
    "make",
    "model",
    "body",
    "years",
    "section",
    "url",
    "http_status",
    "sha256",
    "retrieved_at",
    "edition_market",
    "note",
]
MAX_CONSECUTIVE_BLOCKS = 3


class Blocked(RuntimeError):
    pass


def load_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["url"]: row for row in csv.DictReader(handle)}


def append_manifest(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in FIELDS})


class Fetcher:
    def __init__(self, min_pause: float, max_pause: float):
        self.client = httpx.Client(
            headers={"User-Agent": UA},
            timeout=40,
            follow_redirects=True,
            verify=ssl.create_default_context(),
        )
        self.min_pause, self.max_pause = min_pause, max_pause
        self.blocks = 0
        self.requests = 0

    def get(self, url: str) -> httpx.Response | None:
        delay = 0.0
        for attempt in range(4):
            time.sleep(random.uniform(self.min_pause, self.max_pause) + delay)
            self.requests += 1
            try:
                response = self.client.get(url)
            except httpx.HTTPError:
                delay = 5.0 * (attempt + 1)
                continue
            if response.status_code in (403, 429):
                self.blocks += 1
                if self.blocks >= MAX_CONSECUTIVE_BLOCKS:
                    raise Blocked(f"{response.status_code} on {url}")
                self.min_pause, self.max_pause = self.min_pause * 2, self.max_pause * 2
                delay = 10.0 * (attempt + 1)
                continue
            self.blocks = 0
            if response.status_code >= 500:
                delay = 5.0 * (attempt + 1)
                continue
            return response
        return None


def years_overlap(label: str, year_min: int, year_max: int) -> bool:
    numbers = [int(n) for n in re.findall(r"\d{4}", label)]
    if not numbers:
        return False
    start, end = numbers[0], numbers[-1]
    return start <= year_max and end >= year_min


def links_under(html: str, prefix: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].split("#")[0].rstrip("/")
        if href.startswith("/"):
            href = BASE + href
        if href.startswith(prefix) and href not in found:
            found.append(href)
    return found


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    main = soup.find("main") or soup.body or soup
    return "\n".join(line.strip() for line in main.get_text("\n").splitlines() if line.strip())


def save(raw_dir: Path, name: str, html: str) -> str:
    raw_dir.mkdir(parents=True, exist_ok=True)
    data = html.encode("utf-8")
    (raw_dir / f"{name}.html").write_bytes(data)
    (raw_dir / f"{name}.txt").write_text(page_text(html), encoding="utf-8")
    return hashlib.sha256(data).hexdigest()


def crawl(args) -> int:
    manifest_path = OUT / "manifest.csv"
    done = {
        url: row for url, row in load_manifest(manifest_path).items() if row["http_status"] == "200"
    }
    fetcher = Fetcher(args.min_pause, args.max_pause)
    report = []

    def fetch(url, meta, raw_dir, name):
        if url in done:
            path = raw_dir / f"{name}.html"
            return path.read_text(encoding="utf-8") if path.exists() else None
        response = fetcher.get(url)
        status = response.status_code if response is not None else "ERROR"
        row = {
            **meta,
            "url": url,
            "http_status": status,
            "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        html = None
        if response is not None and response.status_code == 200:
            html = response.text
            row["sha256"] = save(raw_dir, name, html)
            done[url] = row
        append_manifest(manifest_path, row)
        return html

    make = args.make.lower()
    try:
        for model in [m.strip().lower() for m in args.models.split(",") if m.strip()]:
            model_meta = {"make": make, "model": model, "section": "_model"}
            model_html = fetch(
                f"{BASE}/{make}/{model}", model_meta, OUT / "raw" / make / model, "_model"
            )
            if model_html is None:
                report.append(f"{model}: model page unavailable")
                continue
            generations = [
                url
                for url in links_under(model_html, f"{BASE}/{make}/{model}/")
                if re.fullmatch(
                    rf"{re.escape(BASE)}/{make}/{model}/[a-z0-9-]+/[0-9]{{4}}(-[0-9]{{4}})?", url
                )
            ]
            if not generations:
                report.append(f"{model}: not_on_site (no generation pages linked)")
                continue
            for gen_url in generations:
                body, years = gen_url.rsplit("/", 2)[-2:]
                if not years_overlap(years, args.year_min, args.year_max):
                    report.append(
                        f"{model} {body} {years}: outside {args.year_min}-{args.year_max}, skipped"
                    )
                    continue
                meta = {"make": make, "model": model, "body": body, "years": years}
                raw_dir = OUT / "raw" / make / model / f"{body}_{years}"
                queue, seen, pages = [gen_url], {gen_url}, 0
                while queue:
                    url = queue.pop(0)
                    section = "_index" if url == gen_url else url[len(gen_url) + 1 :]
                    html = fetch(url, {**meta, "section": section}, raw_dir, section or "_index")
                    if html is None:
                        continue
                    pages += 1
                    for link in links_under(html, gen_url + "/"):
                        if link not in seen:
                            seen.add(link)
                            queue.append(link)
                report.append(f"{model} {body} {years}: {pages} pages")
                print(report[-1], flush=True)
    except Blocked as exc:
        report.append(f"STOPPED: repeated block {exc}")
    finally:
        summary = OUT / f"crawl_report_{make}.txt"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            "\n".join(report + [f"requests={fetcher.requests}"]) + "\n", encoding="utf-8"
        )
        print("\n".join(report), flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--year-min", type=int, default=2014)
    parser.add_argument("--year-max", type=int, default=2026)
    parser.add_argument("--min-pause", type=float, default=2.0)
    parser.add_argument("--max-pause", type=float, default=5.0)
    return crawl(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
