"""US press "specifications" material for the Chevrolet, Cadillac and Ford lines (GM and Ford newsrooms).

Hosts and what the collector does with them (spec: data_work/_shared/press/FORMAT.md):

  media.gm.com, media.chevrolet.com, media.cadillac.com, pressroom.chevrolet.com
      GM's US media site with the per-vehicle "Specifications" tabs. Only robots.txt is
      requested; when it disallows our client (`User-agent: *` -> `Disallow: /`) the host is
      recorded as status=blocked and no page of it is requested.
  news.gm.com
      GM's current US newsroom (articles from 2021 on). robots.txt is checked, the site's own
      sitemap (sitemap-gmnews.xml) and its own Solr search (the POST the search page sends)
      are used to find the articles whose title names a line. Each candidate article is
      downloaded; an article whose body has a "... Specifications ..." heading followed by
      tables is a `press_specifications` document (year and model from that heading),
      other articles are kept as `press_release` with a note.
  media.ford.com
      robots.txt is requested once; a 403 (Akamai "Access Denied") stops the host
      (status=blocked).

Files:
  RAW_ROOT/press/<host>/robots.txt.gz                robots.txt as fetched
  RAW_ROOT/press/news.gm.com/index/<name>.gz         sitemap and search answers used for discovery
  RAW_ROOT/press/news.gm.com/<article>.html.gz       article pages as published
  RAW_ROOT/pagetext/<sha256>.json.gz                 {"sha256","file","pages":[plain text]}
  data_work/_shared/manifest_press/<host>.csv        one row per request / decision

Resumable: URLs already `ok` in a host manifest (with their raw file present) are not fetched
again; `--refresh-index` re-reads robots.txt, the sitemap and the search answers.

Usage:
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/collect_press_gm_ford.py [--refresh-index]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.robotparser
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, NavigableString

sys.path.insert(0, str(Path(__file__).resolve().parent))

from us_tech_common import (  # noqa: E402
    RAW_ROOT,
    UA,
    WORK,
    Blocked,
    Fetcher,
    Manifest,
    now,
    read_maybe_gz,
    sha256,
    write_gz,
)
from us_tech_lines import LINES  # noqa: E402

FIELDS = [
    "make", "line", "year", "doc_type", "title", "url", "http_status", "bytes", "sha256",
    "retrieved_at", "path", "status", "note",
]
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
MAKES = ("chevrolet", "cadillac", "ford")
GM_MEDIA_HOSTS = ("media.gm.com", "media.chevrolet.com", "media.cadillac.com", "pressroom.chevrolet.com")
NEWS = "news.gm.com"
FORD = "media.ford.com"
SITEMAP = "https://news.gm.com/sitemap-gmnews.xml"
SOLR = ("https://news.gm.com/content/public/us/en/gm-news/home/search/jcr:content/par/"
        "channelbox_1738069849/par/multicollectionsolrs.search.solr")
SEARCH_PAGE = "https://news.gm.com/home/search.html"

# How each GM line is named in article titles and spec headings. The separate electric models
# that share a name (us_tech_lines notes: Equinox EV, Escalade IQ; also Escalade IQL) are cut
# off by the look-aheads.
LINE_NAMES = {
    "chevrolet/malibu": r"\bMalibu\b",
    "chevrolet/cruze": r"\bCruze\b",
    "chevrolet/equinox": r"\bEquinox\b(?!\s+EV\b)",
    "chevrolet/trax": r"\bTrax\b",
    "cadillac/cts": r"\bCTS\b",
    "cadillac/srx": r"\bSRX\b",
    "cadillac/escalade": r"\bEscalade\b(?!\s+(IQL?|EV)\b)",
}
SPEC_HEADING = re.compile(r"\bSpecifications?\b|\bSpecs\b", re.I)


def log(message: str) -> None:
    print(message, flush=True)


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def our_lines() -> list:
    return [line for line in LINES if line.make in MAKES]


# --------------------------------------------------------------------------- page text
BLOCKS = (
    "p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "table", "tr", "section",
    "article", "header", "footer", "nav", "blockquote", "dd", "dt", "dl", "figure", "figcaption",
)


def prepare(soup: BeautifulSoup) -> BeautifulSoup:
    """Mark up a parsed page for text output (in place): block elements on their own lines,
    table rows on one line with the cells separated by a tab. The parser runs the same
    preparation, so the cell texts it quotes are the ones in the stored page text."""
    for tag in soup(["script", "style", "noscript", "template", "svg", "head"]):
        tag.decompose()
    for string in list(soup.find_all(string=True)):  # source line breaks are not text (as rendered)
        if type(string) is NavigableString and not string.find_parent(["pre", "textarea"]) and "\n" in string:
            string.replace_with(NavigableString(re.sub(r"\s+", " ", str(string))))
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for cell in soup.find_all(["td", "th"]):
        cell.append("\t")
    for block in soup.find_all(BLOCKS):
        if block.name not in ("table", "tr") and block.find_parent(["td", "th"]):
            block.append(" ")
            continue
        block.insert_before("\n")
        block.append("\n")
    return soup


def page_text(html: bytes) -> str:
    """Plain text of an HTML page (see prepare), one line per block / table row."""
    soup = prepare(BeautifulSoup(html, "html.parser"))
    lines = []
    for raw in soup.get_text().split("\n"):
        line = re.sub(r"[ \t\xa0\r\f\v]+", " ", raw).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def store_pagetext(digest: str, file: str, pages: list[str]) -> None:
    """Write the page text; an existing file is replaced only when it was written for the same raw
    file (this collector's own output) and its text differs."""
    target = RAW_ROOT / "pagetext" / f"{digest}.json.gz"
    if target.exists():
        existing = json.loads(read_maybe_gz(target))
        if existing.get("file") != file or existing.get("pages") == pages:
            return
    write_gz(target, json.dumps({"sha256": digest, "file": file, "pages": pages}, ensure_ascii=False).encode("utf-8"))


# --------------------------------------------------------------------------- hosts
class Host:
    def __init__(self, host: str, refresh_index: bool, fetcher: Fetcher | None = None):
        self.host = host
        self.refresh_index = refresh_index
        self.fetcher = fetcher or Fetcher(pause=(2.0, 5.0), timeout=90)
        self.manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        self.robots: urllib.robotparser.RobotFileParser | None = None

    def row_ok(self, url: str) -> dict | None:
        row = self.manifest.ok(url)
        if row and row.get("path") and (RAW_ROOT / row["path"]).exists():
            return row
        return None

    def check_robots(self, make: str = "") -> tuple[bool, str]:
        """Fetch robots.txt; return (allowed for the site root, reason)."""
        url = f"https://{self.host}/robots.txt"
        rel = Path("press") / self.host / "robots.txt.gz"
        last = self.manifest.rows.get(url)
        if last and last.get("status") == "blocked" and not self.refresh_index:
            return False, last.get("note", "") + f" (recorded {last.get('retrieved_at')}; --refresh-index re-checks)"
        row = self.row_ok(url)
        body = None
        status: int | str = ""
        if row and not self.refresh_index:
            body, status = read_maybe_gz(RAW_ROOT / row["path"]), int(row["http_status"] or 200)
        else:
            try:
                response = self.fetcher.get(url)
            except Blocked as exc:
                reason = f"robots.txt answered {exc}; scripted access refused, host stopped"
                self.manifest.add({"make": make, "doc_type": "robots", "title": "robots.txt", "url": url,
                                   "http_status": str(exc).split()[0], "retrieved_at": now(),
                                   "status": "blocked", "note": reason})
                return False, reason
            if response is None:
                reason = "robots.txt not reachable (network errors / 5xx after retries); host stopped"
                self.manifest.add({"make": make, "doc_type": "robots", "title": "robots.txt", "url": url,
                                   "http_status": "ERROR", "retrieved_at": now(), "status": "blocked",
                                   "note": reason})
                return False, reason
            status, body = response.status_code, response.content
        parser = urllib.robotparser.RobotFileParser(url)
        if status == 200:
            parser.parse(body.decode("utf-8", errors="replace").splitlines())
        elif status in (401, 403):
            parser.disallow_all = True
        else:  # 404 and other 4xx: no robots rules
            parser.allow_all = True
        self.robots = parser
        allowed = parser.can_fetch(UA, f"https://{self.host}/")
        if status in (401, 403):
            reason = f"robots.txt answered HTTP {status}; scripted access refused, host stopped"
        elif not allowed:
            reason = ("robots.txt: the group that applies to this client (User-agent: *) has "
                      "'Disallow: /'; no page of the host requested")
        elif status == 200:
            reason = "robots.txt allows the pages used (no group applies to this client)"
        else:
            reason = f"robots.txt HTTP {status}: no rules"
        if not (row and not self.refresh_index):
            if status == 200:
                write_gz(RAW_ROOT / rel, body)
            self.manifest.add({"make": make, "doc_type": "robots", "title": "robots.txt", "url": url,
                               "http_status": status, "bytes": len(body or b""),
                               "sha256": sha256(body) if body else "", "retrieved_at": now(),
                               "path": rel.as_posix() if status == 200 else "",
                               "status": "ok" if allowed else "blocked", "note": reason})
        return allowed, reason

    def allowed(self, url: str) -> bool:
        return self.robots is None or self.robots.can_fetch(UA, url)

    def post(self, url: str, data: dict, headers: dict, pause=(5.0, 8.0)) -> httpx.Response | None:
        """POST with the politeness rules of Fetcher.get: a pause before every request, bounded
        retries with growing pauses, back-off on 403/429 and a stop (Blocked) after
        `max_blocks` such answers in a row. No challenge is solved and no header is forged."""
        extra = 0.0
        low, high = max(pause[0], self.fetcher.pause[0]), max(pause[1], self.fetcher.pause[1])
        for attempt in range(self.fetcher.attempts):
            time.sleep(random.uniform(low, high) + extra)
            self.fetcher.requests += 1
            try:
                response = self.fetcher.client.post(url, data=data, headers=headers)
            except httpx.HTTPError:
                extra = 5.0 * (attempt + 1)
                continue
            if response.status_code in (403, 429):
                self.fetcher.blocks += 1
                log(f"  {response.status_code} on POST (block {self.fetcher.blocks}/{self.fetcher.max_blocks}); backing off")
                if self.fetcher.blocks >= self.fetcher.max_blocks:
                    raise Blocked(f"{response.status_code} on POST {url}")
                low, high = low * 2, high * 2
                extra = 15.0 * (attempt + 1)
                continue
            self.fetcher.blocks = 0
            if response.status_code >= 500:
                extra = 5.0 * (attempt + 1)
                continue
            return response
        return None


# --------------------------------------------------------------------------- news.gm.com
def news_index(host: Host) -> tuple[list[str], dict[str, dict]]:
    """Sitemap URLs and Solr hits per line (both stored raw)."""
    rel = Path("press") / NEWS / "index" / "sitemap-gmnews.xml.gz"
    row = host.row_ok(SITEMAP)
    if row and not host.refresh_index:
        body = read_maybe_gz(RAW_ROOT / row["path"])
    else:
        response = host.fetcher.get(SITEMAP)
        status = response.status_code if response is not None else "ERROR"
        body = response.content if response is not None and status == 200 else b""
        if body:
            write_gz(RAW_ROOT / rel, body)
        host.manifest.add({"doc_type": "press_index", "title": "sitemap-gmnews.xml", "url": SITEMAP,
                           "http_status": status, "bytes": len(body), "sha256": sha256(body) if body else "",
                           "retrieved_at": now(), "path": rel.as_posix() if body else "",
                           "status": "ok" if body else "error"})
    sitemap = re.findall(r"<loc>([^<]+)</loc>", body.decode("utf-8", errors="replace"))
    log(f"{NEWS}: sitemap {len(sitemap)} URLs")

    hits: dict[str, dict] = {}
    terms = {"Specifications": None}
    for line in our_lines():
        if line.key in LINE_NAMES:
            terms[line.name] = line.key
    for term, key in terms.items():
        url = f"{SOLR}#searchTerm={term}"
        rel = Path("press") / NEWS / "index" / f"search_{re.sub(r'[^A-Za-z0-9]+', '_', term)}.json.gz"
        row = host.row_ok(url)
        if row and not host.refresh_index:
            answer = read_maybe_gz(RAW_ROOT / row["path"])
        else:
            form = {"searchTerm": term, "collection": "", "collectionIndex": "0", "resultsPageSize": "1000",
                    "page": "1", "sort": "", "searchScope": "", "tags": "", "searchtaggroup": ""}
            response = host.post(SOLR, form, {"Accept": "application/json, text/plain, */*", "Referer": SEARCH_PAGE})
            status = response.status_code if response is not None else "ERROR"
            answer = response.content if response is not None and status == 200 else b""
            try:
                json.loads(answer)
            except ValueError:
                answer = b""
            if answer:
                write_gz(RAW_ROOT / rel, answer)
            host.manifest.add({"make": key.split("/")[0] if key else "", "line": key or "", "doc_type": "press_index",
                               "title": f"site search '{term}'", "url": url, "http_status": status,
                               "bytes": len(answer), "sha256": sha256(answer) if answer else "",
                               "retrieved_at": now(), "path": rel.as_posix() if answer else "",
                               "status": "ok" if answer else "error",
                               "note": "POST form searchTerm=" + term + " resultsPageSize=1000 (as the search page sends)"})
        if not answer:
            continue
        docs = json.loads(answer)[0]["response"]["docs"]
        log(f"{NEWS}: search '{term}': {len(docs)} hits")
        for doc in docs:
            hits.setdefault(doc["id"], {"id": doc["id"], "title": clean(" ".join(doc.get("title") or [])),
                                        "date": (doc.get("DC.date.issued") or [""])[0]})
    return sitemap, hits


def article_url(hit_id: str, sitemap: list[str]) -> str:
    """The published article URL (sitemap form) for a search hit id."""
    tail = hit_id.split("/Pages/", 1)[-1]
    for url in sitemap:
        if url.endswith("/Pages/" + tail):
            return url
    return hit_id


HEADING_TAGS = ["b", "strong", "h1", "h2", "h3", "h4", "h5", "h6"]
BLOCK_PARENTS = ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th"]


def spec_headings(soup: BeautifulSoup) -> list:
    """Stand-alone heading paragraphs that open a specifications section, e.g. '2025 Escalade/Escalade
    ESV Specifications (North America)' or 'SPECIFICATIONS': the heading is the whole text of its
    paragraph (not prose that mentions specifications), outside tables, and a table follows within
    the next few paragraphs. Returns the heading block elements in document order."""
    found = []
    for tag in soup.find_all(HEADING_TAGS):
        text = clean(tag.get_text(" "))
        if not SPEC_HEADING.search(text) or len(text) > 160:
            continue
        block = tag if tag.name.startswith("h") else tag.find_parent(BLOCK_PARENTS)
        if block is None or block.name in ("td", "th") or block.find_parent("table"):
            continue
        if clean(block.get_text(" ")) != text or block in found:
            continue
        table = block.find_next("table")
        if table is None:
            continue
        paragraphs = 0
        for element in block.find_all_next(["p", "table"]):
            if element is table:
                break
            if element.name == "p" and not element.find_parent("table"):
                paragraphs += 1
        if paragraphs <= 5:
            found.append(block)
    return found


def heading_targets(heading: str, title: str, keys, lines: dict) -> list[tuple[str, int, str]]:
    """(line key, model year, how) for a spec heading. A heading that names a model and/or a year
    is used as published; a generic heading ('SPECIFICATIONS') takes the line and the year from
    the article title, and only when the title names exactly one model year."""
    generic = re.sub(r"(?i)specifications?|specs|\(north america\)|[^A-Za-z0-9]", "", heading) == ""
    years = sorted(set(re.findall(r"\b(20\d\d)\b", heading)))
    names = [key for key in sorted(keys) if re.search(LINE_NAMES[key], heading, re.I)]
    how = "heading"
    if generic:
        years = sorted(set(re.findall(r"\b(20\d\d)\b", title)))
        names = [key for key in sorted(keys) if re.search(LINE_NAMES[key], title, re.I)]
        how = "article title"
    if len(years) != 1:
        return []
    year = int(years[0])
    return [(key, year, how) for key in names if lines[key].years[0] <= year <= lines[key].years[1]]


def page_title(soup: BeautifulSoup) -> str:
    return clean(soup.title.get_text()) if soup.title else ""


def classify(body: bytes, keys, lines: dict) -> tuple[str, list[tuple[str, int, str]]]:
    """(page title, [(line key, year, note)]) for the spec sections of a stored article;
    without a usable section: [("", 0, reason)]."""
    soup = BeautifulSoup(body, "html.parser")
    title = page_title(soup)
    matched = []
    headings = [clean(block.get_text(" ")) for block in spec_headings(soup)]
    for heading in headings:
        for key, year, how in heading_targets(heading, title, keys, lines):
            matched.append((key, year, f"'{heading}' (line/year from the {how})"))
    if not matched:
        note = ("no specifications section" if not headings else
                "specifications section not for a registry line-year: " + " || ".join(headings))
        return title, [("", 0, note)]
    return title, matched


def collect_news(host: Host) -> list[dict]:
    allowed, reason = host.check_robots()
    log(f"{NEWS}: robots {'allowed' if allowed else 'BLOCKED'} - {reason}")
    if not allowed:
        return []
    sitemap, hits = news_index(host)
    lines = {line.key: line for line in our_lines()}
    candidates: dict[str, set] = {}
    for hit in hits.values():
        for key, name_re in LINE_NAMES.items():
            if key not in lines or not re.search(name_re, hit["title"], re.I):
                continue
            candidates.setdefault(article_url(hit["id"], sitemap), set()).add(key)
    log(f"{NEWS}: {len(candidates)} candidate articles name a line in the title")
    docs = []
    for url, keys in sorted(candidates.items()):
        tail = url.split("/Pages/", 1)[-1]
        rel = Path("press") / NEWS / (re.sub(r"[^A-Za-z0-9._-]+", "_", tail.removesuffix(".html")) + ".html.gz")
        row = host.row_ok(url)
        if row:
            body = read_maybe_gz(RAW_ROOT / row["path"])
            base = {k: row[k] for k in ("url", "title", "http_status", "bytes", "sha256", "retrieved_at", "path")}
            store_pagetext(row["sha256"], row["path"], [page_text(body)])
        else:
            if not host.allowed(url):
                host.manifest.add({"url": url, "doc_type": "press_release", "status": "robots_disallowed",
                                   "retrieved_at": now()})
                continue
            response = host.fetcher.get(url)
            status = response.status_code if response is not None else "ERROR"
            body = response.content if response is not None and status == 200 else b""
            digest = sha256(body) if body else ""
            if body:
                write_gz(RAW_ROOT / rel, body)
                store_pagetext(digest, rel.as_posix(), [page_text(body)])
            base = {"url": url, "title": "", "http_status": status, "bytes": len(body), "sha256": digest,
                    "retrieved_at": now(), "path": rel.as_posix() if body else ""}
            if not body:
                key = sorted(keys)[0]
                host.manifest.add({**base, "make": key.split("/")[0], "line": ";".join(sorted(keys)),
                                   "doc_type": "press_release", "status": "not_found" if status == 404 else "error"})
                log(f"  {status} {url}")
                continue
        title, matched = classify(body, keys, lines)
        spec = [m for m in matched if m[0]]
        if spec:
            new = {**base, "title": title, "make": spec[0][0].split("/")[0],
                   "line": ";".join(sorted({m[0] for m in spec})), "year": ";".join(sorted({str(m[1]) for m in spec})),
                   "doc_type": "press_specifications", "status": "ok",
                   "note": "spec section heading: " + " || ".join(dict.fromkeys(m[2] for m in spec))}
            for key, year, _ in spec:
                docs.append({"url": url, "line": key, "year": year, "path": base["path"], "sha256": base["sha256"],
                             "title": title})
            log(f"  SPEC {new['line']} {new['year']}: {title}")
        else:
            key = sorted(keys)[0]
            new = {**base, "title": title, "make": key.split("/")[0], "line": ";".join(sorted(keys)), "year": "",
                   "doc_type": "press_release", "status": "ok", "note": matched[0][2]}
            log(f"  no spec: {title} ({matched[0][2][:80]})")
        changed = any(str(row.get(k, "")) != str(new.get(k, "")) for k in ("doc_type", "line", "year", "note", "title")) if row else True
        if changed:
            host.manifest.add(new)  # first fetch, or a stored page classified anew (no refetch)
    return docs


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-index", action="store_true")
    args = parser.parse_args(argv)
    blocked: dict[str, str] = {}

    for name in GM_MEDIA_HOSTS:
        host = Host(name, args.refresh_index)
        allowed, reason = host.check_robots()
        log(f"{name}: robots {'allowed' if allowed else 'BLOCKED'} - {reason}")
        if not allowed:
            blocked[name] = reason
        else:
            # Not expected: the GM media site disallowed every unnamed client when this was written.
            blocked[name] = "robots.txt allows access but no collection is implemented for this host; rerun after review"

    news = Host(NEWS, args.refresh_index)
    try:
        docs = collect_news(news)
        previous = news.manifest.rows.get(f"https://{NEWS}/")
        if previous and previous.get("status") != "ok":
            news.manifest.add({"url": f"https://{NEWS}/", "doc_type": "press_index", "status": "ok",
                               "retrieved_at": now(),
                               "note": f"host completed; supersedes the earlier row ({previous.get('note')})"})
    except Blocked as exc:
        blocked[NEWS] = f"stopped after {exc}"
        news.manifest.add({"url": f"https://{NEWS}/", "doc_type": "press_index", "status": "blocked",
                           "retrieved_at": now(), "note": f"stopped after {exc}"})
        docs = []

    ford = Host(FORD, args.refresh_index, Fetcher(pause=(2.0, 5.0), timeout=60, max_blocks=1, attempts=2))
    allowed, reason = ford.check_robots(make="ford")
    log(f"{FORD}: robots {'allowed' if allowed else 'BLOCKED'} - {reason}")
    if not allowed:
        blocked[FORD] = reason
    else:
        blocked[FORD] = "robots.txt reachable but no Fusion collection is implemented for this host; rerun after review"

    found = {(d["line"], d["year"]): d for d in docs}
    log("\n== coverage (US model years of the registry)")
    missing = []
    for line in our_lines():
        for year in range(line.years[0], line.years[1] + 1):
            doc = found.get((line.key, year))
            if doc:
                log(f"  {line.key} {year}: {doc['url']}")
            else:
                missing.append(f"{line.key} {year}")
    log(f"  spec documents: {len(found)}; line-years without a spec page: {len(missing)}")
    for item in missing:
        log(f"    missing {item}")
    log("\n== blocked hosts")
    for name, reason in blocked.items():
        log(f"  {name}: {reason}")
    log(f"\nrequests: news.gm.com {news.fetcher.requests}, media.ford.com {ford.fetcher.requests}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
