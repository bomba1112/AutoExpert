"""Collect US press "specifications" documents from two manufacturer newsrooms.

Hosts
- Mercedes-Benz USA media newsroom, media.mbusa.com (NOT www.mbusa.com: never requested here).
  The site is a Livewire app. Every model channel page (``/all-c-class-news-media`` ...) lists its
  news; the list is filtered to "news" and extended with the page's own "Load more" button, which
  the browser sends as a POST to the Livewire update endpoint named in the page (data-update-uri,
  data-csrf). Spec documents are news items titled "<year> ... Specifications", "Specs: ...",
  "<year> <model> Quick Reference Guide" or "<year> Mercedes-Benz/AMG <model>" whose body holds
  the specification tables. They are HTML pages.
- BMW Group PressClub USA, www.press.bmwgroup.com/usa. The full US article list
  (``/usa/article?page=N&type=article``) is walked back to mid-2012; articles whose title names
  one of the registry lines are opened, and their PDF attachments titled "... Specs",
  "... Technical Specifications" ... are downloaded. Global/European press data is not used.

Files (see data_work/_shared/press/FORMAT.md)
- spec documents: RAW_ROOT/press/<host>/<file>.html.gz | .pdf, manifest
  data_work/_shared/manifest_press/<host>.csv (doc_type=press_specifications)
- page text: RAW_ROOT/pagetext/<sha256>.json.gz
- discovery pages (robots, listings, articles that only link to spec PDFs, candidates that turned
  out not to be spec documents): RAW_ROOT/press/<host>/discovery/..., manifest
  data_work/_shared/manifest_press/discovery/<host>.csv, candidate index
  data_work/_shared/manifest_press/discovery/<host>-index.csv

Resumable: URLs already ``ok`` in a manifest are not requested again (the stored copy is reused).
One request at a time per host with 2-5 s pauses (Fetcher). Run the two hosts as two processes.

Run (PDF text needs pdfplumber):
  uv run --no-project --with httpx --with beautifulsoup4 --with pdfplumber --with pypdfium2 \
      python scripts/collect_press_mb_bmw.py --host mb
  (same with --host bmw)
"""

from __future__ import annotations

import argparse
import csv
import html as htmllib
import io
import json
import random
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib import robotparser

sys.path.insert(0, str(Path(__file__).resolve().parent))

from us_tech_common import (  # noqa: E402
    RAW_ROOT,
    WORK,
    Blocked,
    Fetcher,
    Manifest,
    now,
    read_maybe_gz,
    sha256,
    write_gz,
)
from us_tech_lines import BY_KEY  # noqa: E402

FIELDS = ["make", "line", "year", "doc_type", "title", "url", "http_status", "bytes", "sha256",
          "retrieved_at", "path", "status", "note"]
INDEX_FIELDS = ["date", "title", "url", "lines", "year", "decision", "source"]
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
DISCOVERY_DIR = MANIFEST_DIR / "discovery"
PAGETEXT = RAW_ROOT / "pagetext"

MB_HOST = "media.mbusa.com"
MB_BASE = "https://media.mbusa.com"
BMW_HOST = "press.bmwgroup.com"  # served from www.press.bmwgroup.com
BMW_BASE = "https://www.press.bmwgroup.com"
BMW_CUTOFF = date(2012, 7, 1)  # MY2014 launch material starts in 2013; keep a margin
YEARS = (2014, 2026)

# --------------------------------------------------------------------------- line mapping
# Title patterns -> registry line. Patterns are applied to titles as published.
MB_LINE_PATTERNS = [
    ("mercedes-benz/amg-gt-4-door", r"\bAMG GT\b.{0,25}\b(4-Door|4 Door|Four-Door)\b|\bGT (43|53|63)( S)?\b.{0,30}4-Door"),
    ("mercedes-benz/eqs", r"\bEQS\b(?!\s*(SUV|\d{3}\+?\s*(4MATIC\s*)?SUV))"),
    ("mercedes-benz/eqb", r"\bEQB\b"),
    ("mercedes-benz/cla", r"\bCLA\b|\bCLA[ -]?\d{2,3}\b|\bCLA-Class\b"),
    ("mercedes-benz/cls", r"\bCLS\b|\bCLS[ -]?\d{2,3}\b|\bCLS-Class\b"),
    ("mercedes-benz/cle", r"\bCLE\b|\bCLE[ -]?\d{2,3}\b"),
    ("mercedes-benz/gla", r"\bGLA\b|\bGLA[ -]?\d{2,3}\b|\bGLA-Class\b"),
    ("mercedes-benz/glb", r"\bGLB\b|\bGLB[ -]?\d{2,3}\b|\bGLB-Class\b"),
    ("mercedes-benz/glc", r"\bGL[CK]\b|\bGL[CK][ -]?\d{2,3}e?\b|\bGL[CK]-Class\b"),
    ("mercedes-benz/gle", r"\bGLE\b|\bGLE[ -]?\d{2,3}e?\b|\bGLE-Class\b|\bML[ -]?\d{3}\b|\bM-Class\b"),
    ("mercedes-benz/gls", r"\bGLS\b|\bGLS[ -]?\d{2,3}\b|\bGLS-Class\b|\bGL[ -]?\d{3}\b|\bGL-Class\b"),
    ("mercedes-benz/c-class", r"\bC-Class\b|\bC[ -]?(200|250|300|350e?|400|43|450|63)\b"),
    ("mercedes-benz/e-class", r"\bE-Class\b|\bE[ -]?(250|300|350e?|400|43|450|53|550|63)\b"),
    ("mercedes-benz/s-class", r"\bS-Class\b|\bS[ -]?(450|500|550e?|560e?|580e?|600|63|65|650|680)\b"),
    ("mercedes-benz/v-class", r"\bV-Class\b"),
]
MB_EXCLUDE = re.compile(
    r"\bEQS SUV\b|\bEQE\b|\bG-Class\b|\bG ?(550|63)\b|\bSLC?\b|\bAMG GT\b(?!.{0,25}\b(4-Door|4 Door|Four-Door)\b)"
    r"|\bMetris\b|\bSprinter\b|\bsmart\b|\bA-Class\b|\bA ?(220|35|45)\b|\bB-Class\b|\bB ?250e?\b"
    r"|Model Line Updates", re.I)

BMW_LINE_PATTERNS = [
    ("bmw/x5-m", r"\bX5 M\b(?![0-9])"),
    ("bmw/x6-m", r"\bX6 M\b(?![0-9])"),
    ("bmw/x5", r"\bX5\b(?! M\b(?![0-9]))"),
    ("bmw/x6", r"\bX6\b(?! M\b(?![0-9]))"),
    ("bmw/x7", r"\bX7\b|\bXB7\b"),
    ("bmw/m3", r"\bM3\b"),
    ("bmw/m5", r"\bM5\b"),
    ("bmw/3-series", r"\b3 Series\b|\b3-Series\b|\b3[1-4]\d[ide]\b|\bM340i\b|\bActiveHybrid 3\b"),
    ("bmw/5-series", r"\b5 Series\b|\b5-Series\b|\b5[2-5]\d[ide]\b|\bM550i\b|\bActiveHybrid 5\b"),
    ("bmw/7-series", r"\b7 Series\b|\b7-Series\b|\b7[4-6]\d(i|e|Li|Ld|d)\b|\bM760i\b|\bM760Li\b|\bActiveHybrid 7\b|\bALPINA B7\b"),
]
# line-up articles (model-year updates, auto shows) can carry spec sheets for several models
BMW_GENERIC = re.compile(r"model year|update information|model updates?|update measures|technology updates|"
                         r"auto show|\bNAIAS\b|automobility|\bspecs\b|specification|technical data", re.I)
BMW_EXCLUDE = re.compile(r"\bMotorrad\b|\bMINI\b|Rolls-Royce|\bR ?\d{3,4}\b|\bS ?1000\b|\bK ?1600\b|\bF ?\d{3} G", re.I)


def map_lines(title: str, patterns) -> list[str]:
    found = []
    for key, pattern in patterns:
        if re.search(pattern, title):
            found.append(key)
    return found


def model_year(text: str) -> int | None:
    m = re.search(r"\b(20[12]\d)\b", text)
    if m:
        y = int(m.group(1))
        if 2010 <= y <= 2030:
            return y
    return None


def in_years(key: str, year: int | None) -> bool:
    if year is None:
        return False
    lo, hi = BY_KEY[key].years
    lo, hi = max(lo, YEARS[0]), min(hi, YEARS[1])
    return lo <= year <= hi


# --------------------------------------------------------------------------- text rendering
def html_page_text(raw_html: str) -> tuple[str, str]:
    """(title, plain text) of a media.mbusa.com news page: title, date and release body.

    Table rows become one line each, cells separated by a tab; paragraphs/list items/headings
    become lines. The extractor uses the same function, so quotes built from table cells
    (cells joined by a space) are found after whitespace normalisation."""
    from bs4 import BeautifulSoup, NavigableString

    soup = BeautifulSoup(raw_html, "html.parser")
    panel = soup.find(id="news-release-panel") or soup
    article = panel.find("article") or panel
    h1 = article.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    body = article.find("div", class_="news-body-editor")
    date_text = ""
    if h1 is not None:
        span = article.find("span", string=re.compile(r"[A-Z][a-z]+ \d{1,2}, \d{4}"))
        date_text = span.get_text(" ", strip=True) if span else ""
    lines = [title, date_text] if date_text else [title]
    if body is not None:
        lines.extend(block_lines(body))
    lines = [re.sub(r"[^\S\t]+", " ", line).strip() for line in lines]
    text ="\n".join(line for line in lines if line.strip())
    return title, text


def cell_text(cell) -> str:
    return re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()


def block_lines(node) -> list[str]:
    """Lines of an HTML fragment: table rows (cells tab-separated) and block elements."""
    from bs4 import NavigableString, Tag

    out: list[str] = []
    buf: list[str] = []

    def flush():
        # inline pieces are joined with a space (as get_text(" ") does for table cells)
        text = re.sub(r"\s+", " ", " ".join(buf)).strip()
        if text:
            out.append(text)
        buf.clear()

    def walk(el):
        for child in el.children:
            if isinstance(child, NavigableString):
                if child.__class__.__name__ in ("Comment", "Doctype", "Declaration", "ProcessingInstruction"):
                    continue
                buf.append(str(child).replace("\n", " "))
                continue
            if not isinstance(child, Tag):
                continue
            name = child.name.lower()
            if name in ("script", "style", "template"):
                continue
            if name == "table":
                flush()
                for tr in child.find_all("tr"):
                    if tr.find_parent("table") is not child:
                        continue
                    cells = [cell_text(c) for c in tr.find_all(["td", "th"], recursive=False)]
                    row = "\t".join(cells).strip()
                    if row.strip():
                        out.append(row)
                continue
            if name == "br":
                flush()
                continue
            block = name in ("p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
                             "section", "article", "blockquote", "tr", "dl", "dt", "dd", "figure")
            if block:
                flush()
            walk(child)
            if block:
                flush()

    walk(node)
    flush()
    return out


def pdf_pages_text(data: bytes) -> list[str]:
    import pdfplumber

    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True) or ""
            pages.append("\n".join(line.rstrip() for line in text.splitlines()).strip("\n"))
    return pages


def write_pagetext(digest: str, rel_file: str, pages: list[str]) -> None:
    path = PAGETEXT / f"{digest}.json.gz"
    payload = {"sha256": digest, "file": rel_file, "pages": pages}
    write_gz(path, json.dumps(payload, ensure_ascii=False).encode("utf-8"))


# --------------------------------------------------------------------------- shared helpers
class Host:
    def __init__(self, host: str, make: str):
        self.host, self.make = host, make
        self.raw = RAW_ROOT / "press" / host
        self.manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        self.discovery = Manifest(DISCOVERY_DIR / f"{host}.csv", FIELDS)
        self.fetcher = Fetcher(pause=(2.0, 5.0))
        self.robots = None
        self.log_lines = 0

    def log(self, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {self.host}:", *args, flush=True)

    # robots -------------------------------------------------------------
    def load_robots(self, url: str) -> None:
        body = self.get_cached(url, f"discovery/robots.txt.gz", "robots", "robots.txt")
        rp = robotparser.RobotFileParser()
        rp.parse(body.decode("utf-8", "replace").splitlines() if body else [])
        self.robots = rp

    def allowed(self, url: str) -> bool:
        return self.robots is None or self.robots.can_fetch("*", url)

    # GET with discovery cache ------------------------------------------
    def get_cached(self, url: str, rel: str, doc_type: str, title: str = "") -> bytes | None:
        row = self.discovery.ok(url)
        if row:
            path = RAW_ROOT / row["path"]
            if path.exists():
                return read_maybe_gz(path)
        if self.robots is not None and not self.allowed(url):
            self.discovery.add({"make": self.make, "doc_type": doc_type, "title": title, "url": url,
                                "retrieved_at": now(), "status": "robots_disallowed"})
            return None
        response = self.fetcher.get(url)
        if response is None:
            self.discovery.add({"make": self.make, "doc_type": doc_type, "title": title, "url": url,
                                "retrieved_at": now(), "status": "error", "note": "no response"})
            return None
        body = response.content
        path = self.raw / rel
        status = "ok" if response.status_code == 200 else "http_error"
        if status == "ok":
            write_gz(path, body)
        self.discovery.add({"make": self.make, "doc_type": doc_type, "title": title, "url": url,
                            "http_status": response.status_code, "bytes": len(body),
                            "sha256": sha256(body), "retrieved_at": now(),
                            "path": path.relative_to(RAW_ROOT).as_posix() if status == "ok" else "",
                            "status": status, "note": "" if str(response.url) == url else f"final_url={response.url}"})
        return body if status == "ok" else None

    def write_index(self, rows: list[dict]) -> None:
        path = DISCOVERY_DIR / f"{self.host}-index.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in INDEX_FIELDS})

    def store_spec(self, url: str, body: bytes, rel: str, lines: list[str], year: int | None, title: str,
                   http_status: int, pages: list[str], note: str = "", gz: bool = True,
                   retrieved_at: str | None = None) -> None:
        path = self.raw / rel
        if gz:
            write_gz(path, body)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        digest = sha256(body)
        rel_file = path.relative_to(RAW_ROOT).as_posix()
        write_pagetext(digest, rel_file, pages)
        self.manifest.add({"make": self.make, "line": ";".join(lines), "year": year or "",
                           "doc_type": "press_specifications", "title": title, "url": url,
                           "http_status": http_status, "bytes": len(body), "sha256": digest,
                           "retrieved_at": retrieved_at or now(), "path": rel_file, "status": "ok", "note": note})


def polite_post(fetcher: Fetcher, url: str, payload: dict, headers: dict):
    """POST with the same politeness rules as Fetcher.get (pause, retries, stop on 403/429)."""
    import httpx

    extra = 0.0
    for attempt in range(fetcher.attempts):
        time.sleep(random.uniform(*fetcher.pause) + extra)
        fetcher.requests += 1
        try:
            response = fetcher.client.post(url, json=payload, headers=headers)
        except httpx.HTTPError:
            extra = 5.0 * (attempt + 1)
            continue
        if response.status_code in (403, 429):
            fetcher.blocks += 1
            if fetcher.blocks >= fetcher.max_blocks:
                raise Blocked(f"{response.status_code} on POST {url}")
            fetcher.pause = (fetcher.pause[0] * 2, fetcher.pause[1] * 2)
            extra = 15.0 * (attempt + 1)
            continue
        fetcher.blocks = 0
        if response.status_code >= 500:
            extra = 5.0 * (attempt + 1)
            continue
        return response
    return None


# --------------------------------------------------------------------------- Mercedes-Benz
MB_CHANNEL_RE = re.compile(r"^https://media\.mbusa\.com/(all-[a-z0-9-]+-news-media|archive)$")
MB_CHANNEL_KEEP = re.compile(r"c-class|cla-class|cle|cls-class|e-class|eq-|gla-class|glb-class|glc-class|gle-class|"
                             r"gls-class|gt-news|maybach|s-class|amg|van|^archive$")
MB_SPEC_TITLE = re.compile(r"specification|\bspecs\b|quick reference guide|\bQRG\b", re.I)
MB_YEAR_TITLE = re.compile(r"^(specs:\s*)?20[12]\d (mercedes|mercedes-benz|mercedes-amg|mercedes-maybach|amg|maybach)\b",
                           re.I)
MB_SPEC_LABELS = re.compile(r"^(wheelbase|length|width|height|curb weight|horsepower|output|torque|turning circle|"
                            r"ground clearance|engine|displacement|transmission|fuel tank|cargo)", re.I)
# the site's own news search (full text) finds spec pages that are not filed under a model channel
MB_SEARCH_TERMS = ["Quick Reference Guide", "Specifications"]


def mb_has_spec_table(text: str) -> bool:
    """At least three table rows (tab-separated cells) labelled like specification rows."""
    rows = [line.split("\t") for line in text.splitlines() if "\t" in line]
    hits = {cells[0].strip().lower()[:12] for cells in rows if MB_SPEC_LABELS.match(cells[0].strip())}
    return len(hits) >= 3


def mb_listing_items(fragment: str) -> list[dict]:
    items = []
    for block in re.split(r'wire:key="public-result-', fragment)[1:]:
        kind = re.match(r"(\w+)-(\d+)", block)
        link = re.search(r'href="(https://media\.mbusa\.com/news/[^"]+)"[^>]*aria-label="([^"]*)"', block)
        if not kind or not link:
            continue
        when = re.search(r'<span class="text-xs[^"]*">\s*([A-Z][a-z]+ \d{1,2}, \d{4})\s*</span>', block)
        title = re.sub(r"\s+", " ", htmllib.unescape(link.group(2))).strip()
        items.append({"id": kind.group(2), "url": link.group(1), "title": title,
                      "date": when.group(1) if when else ""})
    return items


def mb_channel_news(h: Host, channel_url: str, search: str | None = None) -> list[dict]:
    """All news items of a channel (or of the site search on that page): GET the page, then the
    page's own Livewire calls (contentType=news [, searchTerm], loadMore until the button is gone)."""
    name = channel_url.rsplit("/", 1)[-1]
    tag = "news-all" if search is None else "search-" + re.sub(r"\W+", "-", search.lower()).strip("-")
    list_key = f"{channel_url}#livewire-{tag}"
    row = h.discovery.ok(list_key)
    if row and (RAW_ROOT / row["path"]).exists():
        return mb_listing_items(read_maybe_gz(RAW_ROOT / row["path"]).decode("utf-8"))
    response = h.fetcher.get(channel_url)
    if response is None or response.status_code != 200:
        h.discovery.add({"make": h.make, "doc_type": "listing", "url": channel_url, "retrieved_at": now(),
                         "status": "error", "http_status": getattr(response, "status_code", "")})
        return []
    page = response.text
    write_gz(h.raw / "discovery" / f"channel-{name}.html.gz", response.content)
    h.discovery.add({"make": h.make, "doc_type": "listing", "title": name, "url": channel_url,
                     "http_status": 200, "bytes": len(response.content), "sha256": sha256(response.content),
                     "retrieved_at": now(), "path": f"press/{h.host}/discovery/channel-{name}.html.gz",
                     "status": "ok"})
    csrf = re.search(r'data-csrf="([^"]+)"', page)
    update_uri = re.search(r'data-update-uri="([^"]+)"', page)
    snapshot = None
    for raw in re.findall(r'wire:snapshot="([^"]+)"', page):
        if "&quot;name&quot;:&quot;public-news&quot;" in raw:
            snapshot = htmllib.unescape(raw)
    if not (csrf and update_uri and snapshot):
        h.log("no Livewire list component on", channel_url)
        return mb_listing_items(page)
    headers = {"X-Livewire": "1", "Referer": channel_url, "Accept": "application/json"}
    fragment = ""
    for step in range(200):
        calls = [] if step == 0 else [{"method": "loadMore", "params": [], "metadata": {}}]
        updates = {} if step else ({"contentType": "news"} if search is None
                                   else {"contentType": "news", "searchTerm": search})
        payload = {"_token": csrf.group(1),
                   "components": [{"snapshot": snapshot, "updates": updates, "calls": calls}]}
        response = polite_post(h.fetcher, update_uri.group(1), payload, headers)
        if response is None or response.status_code != 200:
            h.log("livewire update failed", channel_url, getattr(response, "status_code", None))
            break
        component = response.json()["components"][0]
        snapshot = component["snapshot"]
        fragment = component.get("effects", {}).get("html", "") or fragment
        if 'wire:click="loadMore"' not in fragment:
            break
    body = fragment.encode("utf-8")
    rel = f"discovery/channel-{name}-{tag}.html.gz"
    write_gz(h.raw / rel, body)
    h.discovery.add({"make": h.make, "doc_type": "listing", "title": f"{name} ({tag}, all loaded)", "url": list_key,
                     "http_status": 200, "bytes": len(body), "sha256": sha256(body), "retrieved_at": now(),
                     "path": f"press/{h.host}/{rel}", "status": "ok",
                     "note": "Livewire contentType=news" + (f" searchTerm={search!r}" if search else "")
                             + " + loadMore until no more"})
    return mb_listing_items(fragment)


def mb_body_year(text: str) -> int | None:
    """Model year named in the release body ("2022 Mercedes-AMG EQS ...")."""
    m = re.search(r"\b(20[12]\d)\s+(Mercedes|AMG|Maybach|[A-Z]{1,3}[ -]?Class|E[QV][A-Z]|GL[A-Z]|CL[A-Z])", text)
    return int(m.group(1)) if m else None


def run_mb(limit: int | None = None) -> None:
    h = Host(MB_HOST, "mercedes-benz")
    h.load_robots(f"{MB_BASE}/robots.txt")
    home = h.get_cached(f"{MB_BASE}/", "discovery/home.html.gz", "listing", "home")
    if home is None:
        h.log("home page not available; stop")
        return
    channels = sorted({u for u in re.findall(r'href="([^"]+)"', home.decode("utf-8", "replace"))
                       if MB_CHANNEL_RE.match(u)})
    channels = [u for u in channels if MB_CHANNEL_KEEP.search(u.rsplit("/", 1)[-1])]
    h.log("channels:", ", ".join(c.rsplit("/", 1)[-1] for c in channels))
    items: dict[str, dict] = {}
    for channel in channels:
        found = mb_channel_news(h, channel)
        h.log(f"{channel.rsplit('/', 1)[-1]}: {len(found)} news items")
        for item in found:
            item.setdefault("source", channel.rsplit("/", 1)[-1])
            items.setdefault(item["url"], item)
    for term in MB_SEARCH_TERMS:
        found = mb_channel_news(h, f"{MB_BASE}/all-releases", search=term)
        new = [i for i in found if i["url"] not in items]
        h.log(f"search {term!r}: {len(found)} news items, {len(new)} not in a model channel")
        for item in found:
            item.setdefault("source", f"search {term}")
            items.setdefault(item["url"], item)
    index = []
    candidates = []
    for item in items.values():
        title = item["title"]
        lines = map_lines(title, MB_LINE_PATTERNS)
        year = model_year(title)
        spec_like = bool(MB_SPEC_TITLE.search(title) or MB_YEAR_TITLE.search(title))
        # a title naming a non-registry model (G-Class, SL, AMG GT 2-door, vans ...) is skipped
        # unless it also names a registry model; multi-model "Model Line Updates" are skipped
        excluded = bool(MB_EXCLUDE.search(title)) and (not lines or bool(re.search("Model Line Updates", title, re.I)))
        decision = "skip"
        if spec_like and lines and not excluded:
            if year is None:
                decision = "candidate_no_year"
            else:
                decision = "candidate" if any(in_years(k, year) for k in lines) else "out_of_years"
        elif spec_like and not lines:
            decision = "spec_other_model"
        row = {"date": item["date"], "title": title, "url": item["url"], "lines": ";".join(lines),
               "year": year or "", "decision": decision, "source": item.get("source", "")}
        index.append(row)
        if decision.startswith("candidate"):
            candidates.append(row)
    index.sort(key=lambda r: (r["decision"], r["lines"], str(r["year"]), r["title"]))
    h.write_index(index)
    h.log(f"{len(items)} news items, {len(candidates)} spec candidates")
    done = 0
    for row in sorted(candidates, key=lambda r: (r["lines"], str(r["year"]), r["url"])):
        if limit is not None and done >= limit:
            break
        url = row["url"]
        if h.manifest.ok(url) or h.discovery.ok(url):
            continue
        done += 1
        slug = url.rsplit("/", 1)[-1]
        response = h.fetcher.get(url)
        if response is None or response.status_code != 200:
            h.manifest.add({"make": h.make, "line": row["lines"], "year": row["year"],
                            "doc_type": "press_specifications", "title": row["title"], "url": url,
                            "http_status": getattr(response, "status_code", ""), "retrieved_at": now(),
                            "status": "error", "note": "no response" if response is None else "http error"})
            continue
        body = response.content
        title, text = html_page_text(response.text)
        year = int(row["year"]) if row["year"] else None
        note = f"listed {row['date']}"
        if year is None:
            year = mb_body_year(text.split("\n", 1)[-1])
            note += "; model year from release text" if year else "; model year not stated"
        lines = row["lines"].split(";")
        has_table = mb_has_spec_table(text)
        if not has_table or (year is not None and not any(in_years(k, year) for k in lines)):
            rel = f"discovery/news-{slug}.html.gz"
            write_gz(h.raw / rel, body)
            reason = "candidate without specification table" if not has_table else "model year out of range"
            h.discovery.add({"make": h.make, "line": row["lines"], "year": year or "", "doc_type": "press_release",
                             "title": title or row["title"], "url": url, "http_status": 200, "bytes": len(body),
                             "sha256": sha256(body), "retrieved_at": now(), "path": f"press/{h.host}/{rel}",
                             "status": "ok", "note": reason})
            h.log(f"{reason}:", row["title"])
            continue
        h.store_spec(url, body, f"news-{slug}.html.gz", lines, year, title or row["title"], 200, [text], note=note)
        h.log("spec:", year, row["lines"], title)
    h.log(f"done; {h.fetcher.requests} requests")


# --------------------------------------------------------------------------- BMW
BMW_DATE_RE = re.compile(r"\w{3} (\w{3}) (\d{2}) [\d:]+ \w+ (\d{4})")
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                                      "Nov", "Dec"], 1)}
BMW_SPEC_ATTACH = re.compile(r"spec|technical data|tech data|technical", re.I)
BMW_NOT_SPEC = re.compile(r"pric|msrp|press release|speech|statement|media alert|update information|"
                          r"model year changes|order guide|press kit|fact sheet", re.I)
# attachments titled only "<model year> <model>" ("MY16 320i", "2015 3 Series Gran Turismo") are
# downloaded too and kept only when the PDF is a specification sheet
BMW_YEAR_MODEL_TITLE = re.compile(r"^(MY\s?\d{2}|20[12]\d)\s+\S.{0,50}$", re.I)
BMW_MODEL_NAME = re.compile(r"\b([1-8] ?Series|X[1-7]|M[1-8]|Z4|i[3-8]|iX\d?|XM|[1-8]\d{2}[a-zA-Z]{1,3}|ALPINA|"
                            r"M\d{3}[a-zA-Z]{1,2}|X\d M\d{2}[a-z])\b")
BMW_PDF_SPEC_LABELS = re.compile(r"wheelbase|curb weight|length|displacement|max\.? output|horsepower|torque|"
                                 r"track|turning circle|fuel tank|ground clearance", re.I)


def bmw_spec_candidate(att: dict, article_title: str) -> bool:
    title = att["title"]
    if not att["details"].upper().startswith("PDF") or BMW_NOT_SPEC.search(title):
        return False
    if re.sub(r"\W+", "", title).lower() == re.sub(r"\W+", "", article_title).lower():
        return False  # the release itself as PDF
    return bool(BMW_SPEC_ATTACH.search(title) or BMW_YEAR_MODEL_TITLE.match(title))


def bmw_year(text: str) -> int | None:
    m = re.search(r"\bMY\s?(\d{2})\b", text)
    if m:
        return 2000 + int(m.group(1))
    return model_year(text)


def bmw_pdf_year(pages: list[str]) -> int | None:
    first = "\n".join(pages[:1])
    m = re.search(r"\b(?:MY|Model Year)\s*(20[12]\d)\b|\b(20[12]\d)\s+(?:BMW|ALPINA|M\d)\b|\bMY\s?(\d{2})\b", first)
    if not m:
        return None
    if m.group(3):
        return 2000 + int(m.group(3))
    return int(m.group(1) or m.group(2))


def bmw_pdf_is_spec(pages: list[str]) -> bool:
    text = "\n".join(pages[:2])
    return len({m.lower()[:6] for m in BMW_PDF_SPEC_LABELS.findall(text)}) >= 4


def bmw_listing_items(page: str) -> list[dict]:
    items = []
    for block in re.findall(r"<article (.*?)</article>", page, flags=re.S):
        link = re.search(r'<h3[^>]*>\s*<a[^>]*href="(/usa/article/detail/[^"]+)"[^>]*>(.*?)</a>', block, flags=re.S)
        if not link:
            continue
        when = re.search(r'class="date"[^>]*>([^<]*)', block)
        d = None
        if when:
            m = BMW_DATE_RE.search(when.group(1))
            if m and m.group(1) in MONTHS:
                d = date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
        category = re.search(r'data-category="(\d+)"', block)
        title = htmllib.unescape(re.sub(r"<[^>]+>", "", link.group(2))).strip()
        items.append({"url": BMW_BASE + link.group(1), "title": title, "date": d,
                      "category": category.group(1) if category else ""})
    return items


def bmw_attachments(page: str) -> list[dict]:
    out = []
    for m in re.finditer(r'<a rel="nofollow" href="(/usa/article/attachment/[^"]+)" class="download" title="([^"]*)"'
                         r'.*?<span class="details">([^<]*)</span>', page, flags=re.S):
        out.append({"url": BMW_BASE + m.group(1), "title": htmllib.unescape(m.group(2)).strip(),
                    "details": m.group(3).strip()})
    return out


BMW_TABLE_LABELS = re.compile(r"^(wheelbase|length|width|height|curb weight|engine power|engine torque|output|"
                              r"torque|turning circle|ground clearance|displacement|fuel tank|track|no\.? of doors)",
                              re.I)


def bmw_article_text(raw_html: str) -> tuple[str, str, int]:
    """(title, plain text, number of specification-table rows) of a PressClub USA article page.

    The text is the article title followed by the release text (div#article-text); table rows
    become one line each with tab-separated cells, as for media.mbusa.com."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(raw_html, "html.parser")
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    body = soup.find(id="article-text")
    lines = [title]
    n_rows = 0
    if body is not None:
        lines.extend(block_lines(body))
        for table in body.find_all("table"):
            for tr in table.find_all("tr"):
                first = tr.find(["td", "th"])
                if first is not None and BMW_TABLE_LABELS.match(cell_text(first)):
                    n_rows += 1
    lines = [re.sub(r"[^\S\t]+", " ", line).strip() for line in lines]
    return title, "\n".join(line for line in lines if line.strip()), n_rows


def bmw_text_year(text: str) -> int | None:
    m = re.search(r"\b(20[12]\d)\s+(?:BMW|ALPINA)\b", text)
    return int(m.group(1)) if m else None


def bmw_store_article(h: "Host", row: dict, tid: str, body: bytes, title: str, text: str, index: list) -> None:
    """Store a release whose text holds the US technical-specification table as a spec document."""
    url = row["url"]
    lines = [k for k in row["lines"].split(";") if k]
    entry = {"date": row["date"], "title": title or row["title"], "url": url, "lines": ";".join(lines), "year": "",
             "decision": "", "source": "release text with specification table"}
    index.append(entry)
    if h.manifest.ok(url):
        entry["decision"] = "stored"
        return
    if not lines:
        entry["decision"] = "no registry model in the title"
        return
    year = bmw_year(row["title"])
    note = "specification table in the release text"
    if year is None:
        year = bmw_text_year(text.split("\n", 1)[-1])
        if year is not None:
            note += "; model year from release text"
    entry["year"] = year or ""
    if year is None or not any(in_years(k, year) for k in lines):
        entry["decision"] = "model year not stated" if year is None else "out of years"
        return
    disc = h.discovery.ok(url) or {}
    h.store_spec(url, body, f"{tid}.html.gz", lines, year, title or row["title"], int(disc.get("http_status") or 200),
                 [text], note=note, retrieved_at=disc.get("retrieved_at"))
    entry["decision"] = "spec"
    h.log("spec (release text):", year, ";".join(lines), title)


def run_bmw(limit: int | None = None, max_pages: int = 400) -> None:
    h = Host(BMW_HOST, "bmw")
    h.load_robots(f"{BMW_BASE}/robots.txt")
    articles: dict[str, dict] = {}
    for page_no in range(1, max_pages + 1):
        url = f"{BMW_BASE}/usa/article" if page_no == 1 else f"{BMW_BASE}/usa/article?page={page_no}&type=article"
        body = h.get_cached(url, f"discovery/list-{page_no:04d}.html.gz", "listing", f"article list page {page_no}")
        if body is None:
            h.log("listing page failed:", url)
            break
        items = bmw_listing_items(body.decode("utf-8", "replace"))
        for item in items:
            articles.setdefault(item["url"], item)
        dates = [i["date"] for i in items if i["date"]]
        if page_no % 10 == 0:
            h.log(f"list page {page_no}: oldest {min(dates) if dates else None}")
        if not items or (dates and max(dates) < BMW_CUTOFF):
            h.log(f"listing stops at page {page_no} (oldest {min(dates) if dates else None})")
            break
    index = []
    candidates = []
    for item in articles.values():
        title = item["title"]
        lines = [] if BMW_EXCLUDE.search(title) else map_lines(title, BMW_LINE_PATTERNS)
        recent = item["date"] is None or item["date"] >= BMW_CUTOFF
        generic = bool(BMW_GENERIC.search(title)) and not BMW_EXCLUDE.search(title)
        decision = "candidate" if (lines or generic) and recent else "skip"
        row = {"date": item["date"].isoformat() if item["date"] else "", "title": title, "url": item["url"],
               "lines": ";".join(lines), "year": model_year(title) or "", "decision": decision,
               "source": f"category {item['category']}"}
        index.append(row)
        if decision == "candidate":
            candidates.append(row)
    h.log(f"{len(articles)} articles listed, {len(candidates)} with a registry model in the title")
    done = 0
    spec_rows = []
    for row in sorted(candidates, key=lambda r: r["date"]):
        if limit is not None and done >= limit:
            break
        url = row["url"]
        tid = re.search(r"/detail/(T\d+EN_US)/", url)
        tid = tid.group(1) if tid else sha256(url.encode())[:12]
        if not h.discovery.ok(url):
            done += 1
        body = h.get_cached(url, f"discovery/article-{tid}.html.gz", "press_release", row["title"])
        if body is None:
            row["decision"] = "article_error"
            continue
        page_html = body.decode("utf-8", "replace")
        art_title, art_text, n_spec_rows = bmw_article_text(page_html)
        if n_spec_rows >= 3:
            bmw_store_article(h, row, tid, body, art_title, art_text, index)
        attachments = bmw_attachments(page_html)
        specs = [a for a in attachments if bmw_spec_candidate(a, row["title"])]
        row["decision"] = f"article: {len(attachments)} attachments, {len(specs)} spec candidates"
        for att in specs:
            spec_rows.append((row, att, tid))
    seen: dict[tuple[str, str], str] = {}
    for row, att, tid in spec_rows:
        url = att["url"]
        entry = {"date": row["date"], "title": att["title"], "url": url, "lines": "", "year": "",
                 "decision": "", "source": row["url"]}
        index.append(entry)
        same = seen.get((att["title"], att["details"]))
        if same:
            entry["decision"] = f"duplicate of {same}"
            continue
        seen[(att["title"], att["details"])] = url
        title = att["title"]
        att_lines = [] if BMW_EXCLUDE.search(title) else map_lines(title, BMW_LINE_PATTERNS)
        if not att_lines and BMW_MODEL_NAME.search(title):
            entry["decision"] = "other model"
            continue
        lines = att_lines or [k for k in row["lines"].split(";") if k]
        entry["lines"] = ";".join(lines)
        if not lines:
            entry["decision"] = "no model named"
            continue
        year = bmw_year(title)
        entry["year"] = year or ""
        if year is not None and not any(in_years(k, year) for k in lines):
            entry["decision"] = "out of years"
            continue
        if h.manifest.ok(url):
            entry["decision"] = "stored"
            continue
        cached = h.discovery.ok(url)
        if cached and cached.get("path") and (RAW_ROOT / cached["path"]).exists():
            # downloaded earlier and kept aside: classify again from the stored copy (no request)
            body = (RAW_ROOT / cached["path"]).read_bytes()
            http_status, retrieved_at = int(cached.get("http_status") or 200), cached.get("retrieved_at") or now()
        else:
            response = h.fetcher.get(url)
            if response is None or response.status_code != 200:
                h.manifest.add({"make": h.make, "line": ";".join(lines), "year": year or "",
                                "doc_type": "press_specifications", "title": title, "url": url,
                                "http_status": getattr(response, "status_code", ""), "retrieved_at": now(),
                                "status": "error", "note": f"article {row['url']}"})
                entry["decision"] = "download error"
                continue
            body = response.content
            http_status, retrieved_at = response.status_code, now()
            cached = None
        att_id = url.rstrip("/").rsplit("/", 1)[-1]
        if not body.startswith(b"%PDF"):
            entry["decision"] = "not a PDF"
            if cached is None:
                h.discovery.add({"make": h.make, "line": ";".join(lines), "year": year or "", "doc_type": "attachment",
                                 "title": title, "url": url, "http_status": http_status, "bytes": len(body),
                                 "sha256": sha256(body), "retrieved_at": retrieved_at, "status": "not_pdf",
                                 "note": "not a PDF"})
            continue
        pages = pdf_pages_text(body)
        note = f"article {row['url']}"
        if year is None:
            year = bmw_pdf_year(pages)
            if year is not None:
                note += "; model year from PDF text"
            else:
                year = bmw_year(row["title"])
                if year is not None:
                    note += "; model year from article title"
                else:
                    cached = h.discovery.ok(row["url"])
                    if cached and (RAW_ROOT / cached["path"]).exists():
                        art = read_maybe_gz(RAW_ROOT / cached["path"]).decode("utf-8", "replace")
                        year = bmw_text_year(bmw_article_text(art)[1].split("\n", 1)[-1])
                        if year is not None:
                            note += "; model year from release text"
        entry["year"] = year or ""
        in_range = year is not None and any(in_years(k, year) for k in lines)
        if not bmw_pdf_is_spec(pages) or not in_range:
            reason = "not a specification sheet" if not bmw_pdf_is_spec(pages) else (
                "model year not stated" if year is None else "model year out of range")
            entry["decision"] = reason
            if cached is None:
                rel = f"discovery/attachment-{tid}-{att_id}.pdf"
                (h.raw / "discovery").mkdir(parents=True, exist_ok=True)
                (h.raw / rel).write_bytes(body)
                h.discovery.add({"make": h.make, "line": ";".join(lines), "year": year or "", "doc_type": "attachment",
                                 "title": title, "url": url, "http_status": http_status, "bytes": len(body),
                                 "sha256": sha256(body), "retrieved_at": retrieved_at, "path": f"press/{h.host}/{rel}",
                                 "status": "ok", "note": f"{reason}; {note}"})
                h.log(f"{reason}:", title)
            continue
        h.store_spec(url, body, f"{tid}-{att_id}.pdf", lines, year, title, http_status, pages,
                     note=note, gz=False, retrieved_at=retrieved_at)
        entry["decision"] = "spec"
        h.log("spec:", year, ";".join(lines), title)
    index.sort(key=lambda r: (r["decision"], r["lines"], str(r["year"]), r["title"]))
    h.write_index(index)
    h.log(f"done; {h.fetcher.requests} requests")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", choices=["mb", "bmw"], required=True)
    parser.add_argument("--limit", type=int, default=None, help="max new documents/articles this run")
    args = parser.parse_args()
    try:
        if args.host == "mb":
            run_mb(args.limit)
        else:
            run_bmw(args.limit)
    except Blocked as exc:
        host = MB_HOST if args.host == "mb" else BMW_HOST
        Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS).add(
            {"make": "mercedes-benz" if args.host == "mb" else "bmw", "doc_type": "press_specifications",
             "url": f"blocked:{now()}", "retrieved_at": now(), "status": "blocked", "note": str(exc)})
        print(f"BLOCKED: {exc}", flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
