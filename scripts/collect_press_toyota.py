"""Collect the US press specification documents of the Toyota and Lexus lines.

Hosts: pressroom.toyota.com (make `toyota` lines) and pressroom.lexus.com (make `lexus` lines),
see data_work/_shared/press/FORMAT.md. Everything is found by navigating the newsrooms' own
pages:

1. robots.txt (both hosts publish `Crawl-delay: 10`, so the pause per host is 10-13 s) and the
   Yoast sitemaps (vehicle-, presskit- and post-sitemaps).
2. Vehicle pages (`/vehicle/<year>-<make>-<model>/`, model years 2019+): the "Product Specs"
   accordion / sidebar links the spec PDF. "Prior Model Years" links are followed too.
3. Press kits (`/presskit/<make>-<model>-<year>/`, model years up to 2019): the press-kit link
   list names the "Product Information" post.
4. Posts whose slug names a model year, a model and a spec word ("product-specs",
   "product-info", "specifications" ...) - from the post sitemaps and the press-kit links.
   The post title is checked ("<year> <make> <model> Product Information/Specs"), the
   "Download Files" link is the spec PDF.

The spec documents themselves are PDFs on Amazon S3 (s3.amazonaws.com/toyota-cms-media,
toyota-cms-media.s3.amazonaws.com, lexus-cms-media.s3.us-east-2.amazonaws.com). They are
downloaded with the newsroom page as Referer, one request at a time per host, and stored as
RAW_ROOT/press/<newsroom host>/pdf/<file>.pdf; their per-page text (pdfplumber) goes to
RAW_ROOT/pagetext/<sha256>.json.gz. Line and model year of a document come from the title of
the newsroom page that links it.

Resumable: URLs that are `ok` in the manifest are not fetched again (stored copies are re-read).

Run (pdfplumber is needed for the page text):
  uv run --offline --no-project --with httpx --with beautifulsoup4 --with pdfplumber \
      --with pypdfium2 python scripts/collect_press_toyota.py [--host pressroom.toyota.com]
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import threading
import traceback
import urllib.robotparser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256, write_gz  # noqa: E402
from us_tech_lines import LINES  # noqa: E402

FIELDS = "make,line,year,doc_type,title,url,http_status,bytes,sha256,retrieved_at,path,status,note".split(",")
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
FIRST_YEAR, LAST_YEAR = 2014, 2026

HOSTS = {
    "pressroom.toyota.com": {"make": "toyota", "brand": "Toyota", "suffix": " - Toyota USA Newsroom"},
    "pressroom.lexus.com": {"make": "lexus", "brand": "Lexus", "suffix": " - Lexus USA Newsroom"},
}

# Which newsroom titles belong to which registry line (titles as published, e.g.
# "2016 Toyota Camry Hybrid Product Information", "2025 LEXUS RX HYBRID", "2022 Lexus NX 350").
TITLE_LINE = {
    "toyota/camry": re.compile(r"\bCamry\b", re.I),
    "toyota/corolla": re.compile(r"\bCorolla(?!\s+Cross)\b", re.I),
    "toyota/rav4": re.compile(r"\bRAV4\b(?!\s+(?:Prime|Plug-in|PHEV)\b)", re.I),
    "toyota/highlander": re.compile(r"(?<!Grand )\bHighlander\b", re.I),
    "toyota/prius": re.compile(r"\bPrius\b(?!\s+(?:c|v|Prime|Plug-in|Plug|PHV)\b)", re.I),
    # Lexus model codes are matched case-sensitively ("ES", "RX 450h", "NX 300h", "GX 460").
    "lexus/es": re.compile(r"\bES(?:\s?\d{3}[a-zA-Z+]*)?\b"),
    "lexus/rx": re.compile(r"\bRX(?:\s?L)?(?:\s?\d{3}[a-zA-Z+]*)?\b"),
    "lexus/nx": re.compile(r"\bNX(?:\s?\d{3}[a-zA-Z+]*)?\b"),
    "lexus/gx": re.compile(r"\bGX(?:\s?\d{3}[a-zA-Z+]*)?\b"),
}
# Titles that are other models although they contain a line name.
TITLE_EXCLUDE = re.compile(
    r"\b(?:Corolla\s+Cross|Grand\s+Highlander|Prius\s+(?:c|v|Prime|Plug-in)|RAV4\s+(?:Prime|Plug-in))\b", re.I
)
# A post is a spec post when its title says so.
SPEC_TITLE = re.compile(
    r"Product\s+(?:Information|Info\b|Specs?\b|Specifications)|\bSpecifications\b|\bSpecs\b|Features\s+(?:and|&)\s+Spec",
    re.I,
)
NOT_US_ENGLISH = re.compile(r"\b(?:Spanish|Chinese|Japanese|Korean|Vietnamese|Español|SEMA)\b", re.I)

# URL slug pre-filters (only to limit the requests; the page title decides).
SLUG_MODEL = {
    "toyota": re.compile(
        r"(?:^|-)(camry|(?:gr-)?corolla(?!-cross)|corollaim|rav4(?!-prime)(?!-plug)|rav-4|"
        r"(?<!grand-)highlander|prius(?!-c\b)(?!-v\b)(?!-c-)(?!-v-)(?!-prime)(?!-plug))(?:-|$)"
    ),
    "lexus": re.compile(r"(?:^|-)(es|rx|nx|gx)(?:-?\d{3}[a-z]*)?(?:-|$)"),
}
SLUG_SPEC = re.compile(r"spec|product-info")
SLUG_YEAR = re.compile(r"(?:^|-)(20\d\d)(?:-|$)")


def log(host: str, msg: str) -> None:
    print(f"{now()} [{host}] {msg}", flush=True)


def title_line(make: str, title: str) -> str | None:
    if TITLE_EXCLUDE.search(title):
        return None
    for key, pattern in TITLE_LINE.items():
        if key.startswith(make + "/") and pattern.search(title):
            return key
    return None


def title_year(title: str) -> int | None:
    found = re.search(r"\b(20\d\d)\b", title)
    return int(found.group(1)) if found else None


def in_years(line_key: str, year: int | None) -> bool:
    line = next(line for line in LINES if line.key == line_key)
    return year is not None and max(line.years[0], FIRST_YEAR) <= year <= min(line.years[1], LAST_YEAR)


def file_name(url: str) -> str:
    path = urlsplit(url).path.strip("/") or "index"
    query = urlsplit(url).query
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", unquote(path).replace("/", "__"))
    if query:
        name += "_" + sha256(query.encode())[:8]
    return name[:150]


class HostPool:
    """One Fetcher per host and one lock per host: at most one request at a time per host,
    also when both newsroom threads download PDFs from the same S3 host."""

    def __init__(self, crawl_delay: dict[str, float]):
        self.crawl_delay = crawl_delay
        self.fetchers: dict[str, Fetcher] = {}
        self.locks: dict[str, threading.Lock] = {}
        self.blocked: dict[str, str] = {}
        self.guard = threading.Lock()

    def _get_fetcher(self, host: str) -> tuple[Fetcher, threading.Lock]:
        with self.guard:
            if host not in self.fetchers:
                if host in self.crawl_delay:
                    delay = self.crawl_delay[host]
                    self.fetchers[host] = Fetcher(pause=(max(2.0, delay), max(5.0, delay + 3.0)))
                else:  # S3 hosts: no robots.txt (AccessDenied), polite 2-5 s; a missing object is a 403
                    self.fetchers[host] = Fetcher(pause=(2.0, 5.0), attempts=1, max_blocks=3)
                self.locks[host] = threading.Lock()
            return self.fetchers[host], self.locks[host]

    def get(self, url: str, headers=None):
        host = urlsplit(url).netloc
        if host in self.blocked:
            raise Blocked(f"{host} stopped earlier: {self.blocked[host]}")
        fetcher, lock = self._get_fetcher(host)
        with lock:
            try:
                return fetcher.get(url, headers=headers)
            except Blocked as exc:
                self.blocked[host] = str(exc)
                raise


def page_title(soup: BeautifulSoup, suffix: str) -> str:
    tag = soup.find("title")
    text = tag.get_text(" ", strip=True) if tag else ""
    if text.endswith(suffix.strip()) or suffix.strip() in text:
        text = text.split(suffix.strip())[0].rstrip(" -|")
    return re.sub(r"\s+", " ", text).strip()


def pdf_links_vehicle(soup: BeautifulSoup, base: str) -> list[tuple[str, str]]:
    """Spec links of a vehicle page: the 'Product Specs' accordion and sidebar box."""
    found: list[tuple[str, str]] = []
    sidebar = soup.find(id="vehicle--sidebar-product-specs-pdf")
    if sidebar:
        for a in sidebar.find_all("a", href=True):
            found.append((urljoin(base, a["href"].strip()), a.get_text(" ", strip=True)))
    for group in soup.select("div.accordion-group"):
        label = group.find("label")
        if label and re.fullmatch(r"\s*Product\s+Specs?\s*", label.get_text(" ", strip=True), re.I):
            for a in group.find_all("a", href=True):
                found.append((urljoin(base, a["href"].strip()), a.get_text(" ", strip=True)))
            for obj in group.find_all("object", attrs={"data": True}):
                found.append((urljoin(base, obj["data"].strip()), "embedded PDF"))
    out, seen = [], set()
    for url, text in found:
        if url not in seen:
            seen.add(url)
            out.append((url, text))
    return out


def prior_year_links(soup: BeautifulSoup, base: str) -> list[str]:
    box = soup.find(id="vehicle--prior-model-years")
    return [urljoin(base, a["href"].strip()) for a in box.find_all("a", href=True)] if box else []


def presskit_spec_links(soup: BeautifulSoup, base: str) -> list[tuple[str, str]]:
    """'Product Information' links of a press kit: the press-kit link list, and in older kits
    the links of the kit text (some still point to the legacy /releases/...htm addresses)."""
    out = []
    anchors = [a for ul in soup.select("ul.presskit-links") for a in ul.find_all("a", href=True)]
    for body in soup.select("div.story-page--article-body--left"):
        if "additional-content" not in (body.get("class") or []):
            anchors += [a for p in body.find_all("p") for a in p.find_all("a", href=True)]
    for a in anchors:
        text = a.get_text(" ", strip=True)
        if re.search(r"Product\s+(?:Information|Info|Specs?|Specifications)|Specifications|Specs", text, re.I):
            url = urljoin(base, a["href"].strip())
            if url not in [u for u, _ in out]:
                out.append((url, text))
    return out


def with_slash(url: str) -> str:
    path = urlsplit(url).path
    return url if url.endswith("/") or "." in path.rsplit("/", 1)[-1] or urlsplit(url).query else url + "/"


def post_download_links(soup: BeautifulSoup, base: str) -> list[tuple[str, str]]:
    """'Download Files' links of a post (the box under the post excerpt)."""
    out = []
    for body in soup.select("div.story-page--article-body--left"):
        for h2 in body.find_all("h2", class_="sidebar-title"):
            if "Download Files" not in h2.get_text(" ", strip=True):
                continue
            for sib in h2.find_next_siblings():
                if sib.name == "h2":
                    break
                anchors = [sib] if sib.name == "a" else sib.find_all("a", href=True)
                for a in anchors:
                    if a.get("href"):
                        out.append((urljoin(base, a["href"].strip()), a.get_text(" ", strip=True)))
    return out


def article_text(soup: BeautifulSoup) -> str:
    parts = [
        node.get_text("\n", strip=True)
        for node in soup.select("div.story-page--article-body--left, div.story-page--article-body")
    ]
    return "\n".join(parts)


def is_pdf_url(url: str) -> bool:
    return urlsplit(url).path.lower().endswith(".pdf")


def write_pagetext(digest: str, rel_file: str, pages: list[str]) -> str:
    target = RAW_ROOT / "pagetext" / f"{digest}.json.gz"
    if target.exists():
        with gzip.open(target, "rt", encoding="utf-8") as handle:
            existing = json.load(handle)
        if not str(existing.get("file", "")).startswith("press/") and existing.get("pages") != pages:
            return f"pagetext exists from {existing.get('file')} and was kept"
    payload = {"sha256": digest, "file": rel_file, "pages": pages}
    write_gz(target, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return ""


def pdf_pages_text(data: bytes) -> list[str]:
    import io

    import pdfplumber

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


class HostCollector:
    def __init__(self, host: str, pool: HostPool):
        self.host = host
        self.cfg = HOSTS[host]
        self.make = self.cfg["make"]
        self.pool = pool
        self.manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        self.raw_dir = RAW_ROOT / "press" / host
        self.stats = {"pages": 0, "pdf_ok": 0, "pdf_failed": 0, "not_found": 0}
        self.spec_docs: dict[str, dict] = {}  # pdf url -> info

    # ---- fetching with manifest -------------------------------------------------------
    def fetch(self, url: str, doc_type: str, *, line="", year="", title="", note="", referer=None,
              suffix=".html.gz") -> tuple[bytes | None, dict | None]:
        """Body and manifest row of `url`. A fresh `ok` row is returned unsaved (`_fresh`) so the
        caller can add title/line/year first and save it once with `save()`; other rows are saved."""
        row = self.manifest.ok(url)
        if row and row.get("path") and (RAW_ROOT / row["path"]).exists():
            path = RAW_ROOT / row["path"]
            data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
            return data, dict(row)
        headers = {"Referer": referer} if referer else None
        base = {"make": self.make, "line": line, "year": year, "doc_type": doc_type, "title": title, "url": url}
        try:
            response = self.pool.get(url, headers=headers)
        except Blocked as exc:
            self.manifest.add({**base, "retrieved_at": now(), "status": "blocked", "note": str(exc)})
            raise
        if response is None:
            self.manifest.add({**base, "retrieved_at": now(), "status": "error",
                               "note": (note + "; " if note else "") + "no answer after retries (timeout/5xx/403)"})
            return None, None
        data = response.content
        status = "ok" if response.status_code == 200 else ("not_found" if response.status_code in (404, 410) else "error")
        row = {**base, "http_status": response.status_code, "bytes": len(data), "sha256": sha256(data),
               "retrieved_at": now(), "status": status, "note": note}
        if str(response.url) != url:
            row["note"] = (row["note"] + "; " if row["note"] else "") + f"final_url={response.url}"
        self.stats["pages"] += 1
        if status != "ok":
            if status == "not_found":
                self.stats["not_found"] += 1
            self.manifest.add(row)
            return None, row
        if suffix == ".pdf":
            name = file_name(url)
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            path = self.raw_dir / "pdf" / name
            if path.exists() and sha256(path.read_bytes()) != row["sha256"]:
                path = path.with_name(path.stem + "-" + row["sha256"][:8] + ".pdf")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        else:
            path = self.raw_dir / (file_name(url) + suffix)
            write_gz(path, data)
        row["path"] = path.relative_to(RAW_ROOT).as_posix()
        row["_fresh"] = True
        return data, row

    def save(self, row: dict, **changes) -> dict:
        """Save a fresh row, or append a corrected row when stored fields differ."""
        fresh = row.pop("_fresh", False)
        changed = {k: v for k, v in changes.items() if str(row.get(k, "")) != str(v)}
        row.update(changed)
        if fresh or changed:
            self.manifest.add(row)
        return row

    # ---- discovery ------------------------------------------------------------------
    def robots(self) -> float:
        url = f"https://{self.host}/robots.txt"
        response = Fetcher(pause=(2.0, 3.0)).get(url)
        if response is None or response.status_code != 200:
            raise SystemExit(f"robots.txt of {self.host} not readable")
        text = response.text
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(text.splitlines())
        self.robots_parser = parser
        delay = parser.crawl_delay("*")
        if delay is None:
            found = re.search(r"(?im)^\s*Crawl-delay:\s*([\d.]+)", text)
            delay = float(found.group(1)) if found else 0.0
        path = self.raw_dir / "_robots.txt.gz"
        write_gz(path, response.content)
        stored = self.manifest.ok(url)
        if stored and stored.get("sha256") == sha256(response.content):
            log(self.host, f"robots.txt unchanged: crawl-delay {delay}")
            return float(delay)
        self.manifest.add({"make": self.make, "doc_type": "robots", "title": "robots.txt", "url": url,
                           "http_status": 200, "bytes": len(response.content), "sha256": sha256(response.content),
                           "retrieved_at": now(), "path": path.relative_to(RAW_ROOT).as_posix(), "status": "ok",
                           "note": f"crawl_delay={delay}; disallow for /: {not parser.can_fetch('*', '/')}"})
        log(self.host, f"robots.txt: crawl-delay {delay}")
        return float(delay)

    def allowed(self, url: str) -> bool:
        return urlsplit(url).netloc != self.host or self.robots_parser.can_fetch("*", url)

    def sitemap_urls(self) -> dict[str, list[str]]:
        index_url = f"https://{self.host}/sitemap_index.xml"
        data, row = self.fetch(index_url, "sitemap", title="sitemap_index.xml", suffix=".xml.gz")
        if row:
            self.save(row)
        if data is None:
            raise SystemExit(f"sitemap index of {self.host} not readable")
        maps = re.findall(r"<loc>([^<]+)</loc>", data.decode("utf-8", "replace"))
        wanted = [m for m in maps if re.search(r"/(vehicle|presskit|post)-sitemap\d*\.xml$", m)]
        out: dict[str, list[str]] = {"vehicle": [], "presskit": [], "post": []}
        for sitemap in wanted:
            kind = re.search(r"/(vehicle|presskit|post)-sitemap", sitemap).group(1)
            body, row = self.fetch(sitemap, "sitemap", title=sitemap.rsplit("/", 1)[1], suffix=".xml.gz")
            if row:
                self.save(row)
            if body is None:
                log(self.host, f"sitemap failed: {sitemap}")
                continue
            out[kind] += re.findall(r"<loc>([^<]+)</loc>", body.decode("utf-8", "replace"))
        log(self.host, "sitemaps: " + ", ".join(f"{k}={len(v)}" for k, v in out.items()))
        return out

    def slug_ok(self, slug: str) -> int | None:
        found = SLUG_YEAR.search(slug)
        if not found or not SLUG_MODEL[self.make].search(slug):
            return None
        year = int(found.group(1))
        return year if FIRST_YEAR <= year <= LAST_YEAR else None

    # ---- processing -------------------------------------------------------------------
    def handle_spec_link(self, pdf_url: str, link_text: str, page_url: str, page_title: str, line: str, year: int,
                         page_kind: str) -> None:
        if pdf_url in self.spec_docs:
            self.spec_docs[pdf_url]["pages"].append(page_url)
            return
        self.spec_docs[pdf_url] = {"line": line, "year": year, "title": page_title, "page_url": page_url,
                                   "link_text": link_text, "kind": page_kind, "pages": [page_url]}

    def process_vehicle(self, url: str, queue: list[str], seen: set[str]) -> None:
        data, row = self.fetch(url, "press_vehicle_page")
        if data is None:
            return
        soup = BeautifulSoup(data.decode("utf-8", "replace"), "html.parser")
        title = page_title(soup, self.cfg["suffix"])
        line, year = title_line(self.make, title), title_year(title)
        for prior in prior_year_links(soup, url):
            prior = with_slash(prior)
            slug = urlsplit(prior).path.strip("/").split("/")[-1]
            if "/vehicle/" in prior and prior not in seen and self.slug_ok(slug) and self.allowed(prior):
                seen.add(prior)
                queue.append(prior)
        if not line or not in_years(line, year):
            self.save(row, title=title, note="title is not a target line/year")
            return
        links = pdf_links_vehicle(soup, url)
        self.save(row, title=title, line=line, year=year, note=f"product_specs_links={len(links)}")
        for link, text in links:
            if is_pdf_url(link):
                self.handle_spec_link(link, text, url, title, line, year, "vehicle")
            elif urlsplit(link).netloc == self.host:
                link = with_slash(link)
                if link not in self.post_seen and self.allowed(link):
                    self.post_seen.add(link)
                    self.posts.append(link)

    def process_presskit(self, url: str) -> None:
        data, row = self.fetch(url, "press_presskit_page")
        if data is None:
            return
        soup = BeautifulSoup(data.decode("utf-8", "replace"), "html.parser")
        title = page_title(soup, self.cfg["suffix"])
        # some kit titles carry no year ("Lexus ES Hybrid"): the kit slug names it
        line, year = title_line(self.make, title), title_year(title) or self.slug_ok(urlsplit(url).path.strip("/").split("/")[-1])
        links = presskit_spec_links(soup, url)
        self.save(row, title=title, line=line or "", year=year or "",
                  note="spec_links=" + " | ".join(f"{t} -> {u}" for u, t in links))
        if not line or not in_years(line, year):
            return
        for link, _text in links:
            if urlsplit(link).netloc == self.host:  # links to other hosts (legacy newsroom, short links) are not followed
                link = with_slash(link)
                if link not in self.post_seen and self.allowed(link):
                    self.post_seen.add(link)
                    self.posts.append(link)

    def process_post(self, url: str) -> None:
        data, row = self.fetch(url, "press_post_page")
        if data is None:
            return
        soup = BeautifulSoup(data.decode("utf-8", "replace"), "html.parser")
        title = page_title(soup, self.cfg["suffix"])
        line, year = title_line(self.make, title), title_year(title)
        if not SPEC_TITLE.search(title) or NOT_US_ENGLISH.search(title) or not line or not in_years(line, year):
            self.save(row, title=title, note="title is not a spec post of a target line/year")
            return
        links = post_download_links(soup, url)
        pdfs = [(u, t) for u, t in links if is_pdf_url(u)]
        if pdfs:
            self.save(row, title=title, line=line, year=year, note=f"download_links={len(pdfs)}")
            for link, text in pdfs:
                self.handle_spec_link(link, text, url, title, line, year, "post")
            return
        # No PDF: the post itself is the spec document when its body carries spec rows.
        body = article_text(soup)
        labels = sum(bool(re.search(p, body, re.I)) for p in (r"Wheelbase", r"Horsepower", r"Curb Weight", r"Tire"))
        if labels >= 3:
            row = self.save(row, title=title, line=line, year=year, doc_type="press_specifications",
                            note="spec rows in the HTML body (no download link)")
            write_pagetext(row["sha256"], row["path"], [body])
        else:
            self.save(row, title=title, line=line, year=year,
                      note="spec post without download link or spec rows: " + "; ".join(u for u, _ in links))

    def download_specs(self) -> None:
        for pdf_url, info in self.spec_docs.items():
            note = f"page_url={info['page_url']}; link_text={info['link_text']}; via={info['kind']}"
            if len(info["pages"]) > 1:
                note += "; also_linked_from=" + " ".join(info["pages"][1:])
            data, row = self.fetch(pdf_url, "press_specifications", line=info["line"], year=info["year"],
                                   title=info["title"], note=note, referer=info["page_url"], suffix=".pdf")
            if data is None or row is None:
                self.stats["pdf_failed"] += 1
                log(self.host, f"PDF failed: {pdf_url}")
                continue
            if not row.get("_fresh"):
                if not (RAW_ROOT / "pagetext" / f"{row['sha256']}.json.gz").exists() and data.startswith(b"%PDF"):
                    write_pagetext(row["sha256"], row["path"], pdf_pages_text(data))
                self.stats["pdf_ok"] += 1
                continue
            if not data.startswith(b"%PDF"):
                self.save(row, status="error", note=row["note"] + "; body is not a PDF")
                self.stats["pdf_failed"] += 1
                continue
            pages = pdf_pages_text(data)
            chars = sum(len(p.strip()) for p in pages)
            extra = f"; pdf_pages={len(pages)}; text_chars={chars}" + ("; no_text_layer" if chars == 0 else "")
            kept = write_pagetext(row["sha256"], row["path"], pages)
            if kept:
                extra += "; " + kept
            self.save(row, note=row["note"] + extra)
            self.stats["pdf_ok"] += 1

    def run(self) -> None:
        maps = self.sitemap_urls()
        seen: set[str] = set()
        vehicles: list[str] = []
        for url in maps["vehicle"]:
            slug = urlsplit(url).path.strip("/").split("/")[-1]
            if self.slug_ok(slug) and self.allowed(url):
                vehicles.append(url)
                seen.add(url)
        presskits = []
        for url in maps["presskit"]:
            slug = urlsplit(url).path.strip("/").split("/")[-1]
            if self.slug_ok(slug) and self.allowed(url):
                presskits.append(url)
        self.posts: list[str] = []
        self.post_seen: set[str] = set()
        for url in maps["post"]:
            slug = urlsplit(url).path.strip("/").split("/")[-1]
            if self.slug_ok(slug) and SLUG_SPEC.search(slug) and self.allowed(url):
                self.posts.append(url)
                self.post_seen.add(url)
        log(self.host, f"candidates: vehicle={len(vehicles)} presskit={len(presskits)} post={len(self.posts)}")
        queue = list(vehicles)
        i = 0
        while i < len(queue):
            self.process_vehicle(queue[i], queue, seen)
            i += 1
        log(self.host, f"vehicle pages done ({len(queue)}); spec links so far {len(self.spec_docs)}")
        for url in presskits:
            self.process_presskit(url)
        log(self.host, f"press kits done ({len(presskits)}); posts to check {len(self.posts)}")
        i = 0
        while i < len(self.posts):
            if self.allowed(self.posts[i]):
                self.process_post(self.posts[i])
            i += 1
        log(self.host, f"posts done ({len(self.posts)}); spec documents {len(self.spec_docs)}")
        self.download_specs()
        log(self.host, f"finished: {self.stats}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--host", action="append", choices=sorted(HOSTS), help="newsroom host (default: both)")
    args = ap.parse_args()
    hosts = args.host or list(HOSTS)
    collectors, delays = {}, {}
    for host in hosts:
        collectors[host] = HostCollector(host, None)  # pool set below
        delays[host] = collectors[host].robots()
    pool = HostPool(delays)
    for c in collectors.values():
        c.pool = pool

    def run(c: HostCollector) -> None:
        try:
            c.run()
        except Blocked as exc:
            log(c.host, f"BLOCKED, host stopped: {exc}")
        except Exception:  # noqa: BLE001 - keep the other host running, report
            log(c.host, "FAILED:\n" + traceback.format_exc())

    threads = [threading.Thread(target=run, args=(c,), name=h) for h, c in collectors.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if pool.blocked:
        print("blocked hosts:", json.dumps(pool.blocked, indent=1))


if __name__ == "__main__":
    main()
