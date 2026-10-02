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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, read_maybe_gz, write_gz  # noqa: E402
from us_tech_lines import MAKES, lines_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_work" / "_mcum"
RAW = RAW_ROOT / "_mcum"
PRIORITY = re.compile(
    r"specification|maintenance|lubric|capacit|fluid|oil|tire|tyre|wheel|fuel|dimension|"
    r"measurement|weight|service|engine|filter|coolant|brake|battery",
    re.I,
)
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
    write_gz(raw_dir / f"{name}.html.gz", data)
    (raw_dir / f"{name}.txt").write_text(page_text(html), encoding="utf-8")
    return hashlib.sha256(data).hexdigest()


def load_saved(raw_dir: Path, name: str) -> str | None:
    for candidate in (raw_dir / f"{name}.html.gz", raw_dir / f"{name}.html"):
        if candidate.exists():
            return read_maybe_gz(candidate).decode("utf-8")
    return None


def crawl(args) -> int:
    manifest_path = OUT / "manifest.csv"
    done = {
        url: row for url, row in load_manifest(manifest_path).items() if row["http_status"] == "200"
    }
    fetcher = Fetcher(args.min_pause, args.max_pause)
    report = []

    def fetch(url, meta, raw_dir, name):
        if url in done:
            return load_saved(raw_dir, name)
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

    if args.all:
        plan = [
            (MAKES[line.make]["mcum"], slug)
            for line in lines_for(include_done=True)
            if MAKES[line.make]["mcum"]
            for slug in line.mcum
        ]
    else:
        plan = [
            (args.make.lower(), m.strip().lower()) for m in args.models.split(",") if m.strip()
        ]

    def generations_of(make, model):
        model_html = fetch(
            f"{BASE}/{make}/{model}", {"make": make, "model": model, "section": "_model"},
            RAW / make / model, "_model",
        )
        if model_html is None:
            report.append(f"{make}/{model}: model page unavailable")
            return []
        found = [
            url
            for url in links_under(model_html, f"{BASE}/{make}/{model}/")
            if re.fullmatch(
                rf"{re.escape(BASE)}/{make}/{model}/[a-z0-9-]+/[0-9]{{4}}(-[0-9]{{4}})?", url
            )
        ]
        if not found:
            report.append(f"{make}/{model}: not_on_site (no generation pages linked)")
        return found

    def walk(make, model, gen_url, priority_only):
        body, years = gen_url.rsplit("/", 2)[-2:]
        meta = {"make": make, "model": model, "body": body, "years": years}
        raw_dir = RAW / make / model / f"{body}_{years}"
        queue, seen, pages = [gen_url], {gen_url}, 0
        while queue:
            url = queue.pop(0)
            section = "_index" if url == gen_url else url[len(gen_url) + 1 :]
            html = fetch(url, {**meta, "section": section}, raw_dir, section or "_index")
            if html is None:
                continue
            pages += 1
            for link in links_under(html, gen_url + "/"):
                if link in seen:
                    continue
                if priority_only and not PRIORITY.search(link[len(gen_url) + 1 :]):
                    continue
                seen.add(link)
                queue.append(link)
        return body, years, pages

    try:
        for priority_only in ((True, False) if args.all else (False,)):
            for make, model in plan:
                for gen_url in generations_of(make, model):
                    body, years = gen_url.rsplit("/", 2)[-2:]
                    if not years_overlap(years, args.year_min, args.year_max):
                        if not priority_only:
                            report.append(
                                f"{make}/{model} {body} {years}: outside "
                                f"{args.year_min}-{args.year_max}, skipped"
                            )
                        continue
                    body, years, pages = walk(make, model, gen_url, priority_only)
                    label = "priority" if priority_only else "full"
                    report.append(f"{make}/{model} {body} {years}: {pages} pages ({label})")
                    print(report[-1], flush=True)
    except Blocked as exc:
        report.append(f"STOPPED: repeated block {exc}")
    finally:
        name = "all" if args.all else args.make.lower()
        summary = OUT / f"crawl_report_{name}.txt"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            "\n".join(report + [f"requests={fetcher.requests}"]) + "\n", encoding="utf-8"
        )
        print("\n".join(report[-5:]), flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--make")
    parser.add_argument("--models")
    parser.add_argument("--year-min", type=int, default=2014)
    parser.add_argument("--year-max", type=int, default=2026)
    parser.add_argument("--min-pause", type=float, default=2.0)
    parser.add_argument("--max-pause", type=float, default=5.0)
    return crawl(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
