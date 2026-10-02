"""Collect US press "specifications" pages for Honda, Nissan, Infiniti and Mitsubishi lines.

Hosts (one Fetcher per host, one request at a time, 2-5 s pauses):
  hondanews.com            Honda Accord / Civic / CR-V: the "Specs" tab of each model channel
                           (/en-US/honda-automobiles/channels/<model>?selectedTabId=<model>-specs).
  usa.nissannews.com       Nissan Altima / Sentra / Rogue / Pathfinder: the "Press Kit Archive"
                           page (/en-US/pages/nissan-press-kit-by-model) lists one press kit per
                           model year; each press kit has a "Specifications"/"Specs" tab whose
                           release is fetched as its own page (/en-US/releases/release-<id>).
  usa.infinitinews.com     INFINITI Q50 / QX60 (JX) / QX70 (FX): "Press Kits" and "Specs" tabs
                           of the newsroom root channel (us-united-states-infiniti, the channel
                           the site search uses); press kit "Specs" tabs are fetched as pages.
  media.mitsubishicars.com Mitsubishi Outlander / Outlander Sport (the US newsroom linked from
                           www.mitsubishicars.com): vehicle channels from the newsroom navigation,
                           their default and "Press Kits" listings, press kit "Tech Specs"
                           components and "... Technical Specifications" releases.

Files (data_work/_shared/press/FORMAT.md):
  RAW_ROOT/press/<host>/<release>.html.gz      raw spec page
  RAW_ROOT/pagetext/<sha256>.json.gz           plain text of the spec page (one page; "file" = the
                                               raw file's path relative to RAW_ROOT)
  data_work/_shared/manifest_press/<host>.csv  manifest (status ok / http_error / blocked)
  data_work/_shared/manifest_press/<host>.candidates.json   discovery cache (resume)
  data_work/_shared/manifest_press/<host>.coverage.json     line-years found / not found

Resumable: spec URLs already `ok` in the manifest are not fetched again, and the discovery
result is cached (use --rediscover to crawl the listings again).

Usage:
  .venv/Scripts/python.exe scripts/collect_press_honda_nissan.py --host hondanews.com
  .venv/Scripts/python.exe scripts/collect_press_honda_nissan.py            (all four, in turn)
  .venv/Scripts/python.exe scripts/collect_press_honda_nissan.py --rebuild-text   (page text only)
"""

from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import (RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, read_maybe_gz,  # noqa: E402
                             sha256, write_gz)
from us_tech_lines import LINES  # noqa: E402

FIELDS = ["make", "line", "year", "doc_type", "title", "url", "http_status", "bytes", "sha256",
          "retrieved_at", "path", "status", "note"]
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
MAKES = ("honda", "nissan", "infiniti", "mitsubishi")
LINE_YEARS = {l.key: l.years for l in LINES if l.make in MAKES}

HOSTS = {
    "hondanews.com": {"base": "https://hondanews.com", "make": "honda"},
    "usa.nissannews.com": {"base": "https://usa.nissannews.com", "make": "nissan"},
    "usa.infinitinews.com": {"base": "https://usa.infinitinews.com", "make": "infiniti"},
    "media.mitsubishicars.com": {"base": "https://media.mitsubishicars.com", "make": "mitsubishi"},
}

RELEASE_ID = re.compile(r"release-[0-9a-f]{32}")
YEAR = re.compile(r"(?<![\d.])(20[12]\d)(?![\d])")
SPEC_WORD = re.compile(r"\bspec(s|ifications?)?\b|\btechnical\b", re.I)  # not "Special Edition"


def log(*args):
    print(now(), *args, flush=True)


# --------------------------------------------------------------------------- page text
BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr",
              "table", "tbody", "thead", "section", "article", "blockquote", "pre", "dl", "dt", "dd"}


def cell_lines(cell: Tag) -> list[str]:
    """Text lines of a table cell: strings joined by spaces, new line at <br>/<p>/<div>/<li>."""
    lines, cur = [], []

    def walk(node):
        for child in node.children:
            if isinstance(child, NavigableString):
                if child.__class__.__name__ in ("Comment", "Doctype", "Declaration", "ProcessingInstruction"):
                    continue
                text = str(child).strip()
                if text:
                    cur.append(text)
            elif isinstance(child, Tag):
                if child.name in ("script", "style"):
                    continue
                block = child.name in BLOCK_TAGS
                if block and cur:
                    lines.append(" ".join(cur))
                    cur.clear()
                walk(child)
                if block and cur:
                    lines.append(" ".join(cur))
                    cur.clear()

    walk(cell)
    if cur:
        lines.append(" ".join(cur))
    return [" ".join(l.split()) for l in lines if l.strip()]


def cell_text(cell: Tag) -> str:
    return " ".join(cell_lines(cell))


def content_root(soup: BeautifulSoup) -> Tag:
    """The release body of a newsroom release page (same platform on all four hosts)."""
    art = soup.find("article", id="release") or soup
    for finder in (lambda a: a.find("div", id="release-main"),
                   lambda a: a.find("w-release"),
                   lambda a: a.find("div", class_="release__body-copy")):
        node = finder(art)
        if node is not None:
            return node
    return art


def page_title(soup: BeautifulSoup) -> str:
    t = soup.find("title")
    return " ".join(t.get_text(" ", strip=True).split()) if t else ""


def leaf_tables(root: Tag) -> list[Tag]:
    return [t for t in root.find_all("table") if t.find("table") is None]


def row_cells(tr: Tag) -> list[Tag]:
    return tr.find_all(["td", "th"], recursive=False)


def render_text(html_bytes: bytes) -> str:
    """Plain text of the spec page: title line, then the release body; every table row of a
    leaf table on its own line with its cells separated by tabs."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    title = page_title(soup)
    root = content_root(soup)
    for tag in root.find_all(["script", "style"]):
        tag.decompose()
    for table in leaf_tables(root):
        rows = []
        for tr in table.find_all("tr"):
            cells = [cell_text(c) for c in row_cells(tr)]
            if any(cells):
                rows.append("\t".join(cells))
        table.replace_with(NavigableString("\n" + "\n".join(rows) + "\n"))
    body = []
    for line in root.get_text("\n").split("\n"):
        line = " ".join(line.split()) if "\t" not in line else "\t".join(" ".join(c.split()) for c in line.split("\t"))
        if line.strip():
            body.append(line)
    return title + "\n" + "\n".join(body)


# --------------------------------------------------------------------------- helpers
class Host:
    def __init__(self, host: str):
        self.host = host
        self.base = HOSTS[host]["base"]
        self.make = HOSTS[host]["make"]
        self.fetcher = Fetcher(pause=(2.0, 5.0))
        self.manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)

    def get(self, url, referer=None):
        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": referer} if referer else None
        r = self.fetcher.get(url, headers=headers)
        if r is None:
            log("  no response", url)
            return None
        if r.status_code != 200:
            log("  HTTP", r.status_code, url)
            return None
        return r

    def absolute(self, href: str) -> str:
        href = htmllib.unescape(href)
        if href.startswith("http"):
            return re.sub(r"^http://", "https://", href)
        if not href.startswith("/"):
            href = "/" + href
        return self.base + href

    def listing(self, url: str, max_pages: int = 60) -> list[tuple[str, str]]:
        """(href, title) of release links of a channel/search listing, following "Load More"."""
        items, seen, first = [], set(), url
        for page in range(max_pages):
            r = self.get(url, referer=first if page else None)
            if r is None:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/releases/" not in href or "/download" in href or "/attachment/" in href:
                    continue
                if "selectedTabId" in href or "gallery=" in href or "/images/" in href:
                    continue
                title = " ".join(a.get_text(" ", strip=True).split())
                if not title or title in ("...", "Read More"):
                    continue
                key = href.split("?")[0]
                if key in seen:
                    continue
                seen.add(key)
                items.append((self.absolute(key), title))
            m = re.search(r'<a href="([^"]*)" id="next" class="[^"]*load-more-btn', r.text)
            if not m:
                break
            url = self.absolute(m.group(1))
        return items


def title_year(title: str) -> int | None:
    m = YEAR.search(title)
    return int(m.group(1)) if m else None


def in_range(line: str, year: int | None) -> bool:
    if year is None or line not in LINE_YEARS:
        return False
    lo, hi = LINE_YEARS[line]
    return lo <= year <= hi


def spec_tabs(html_text: str) -> list[tuple[str, str]]:
    """(release id, tab label) of the specification tab(s) of a press kit page."""
    soup = BeautifulSoup(html_text, "html.parser")
    found = {}
    for opt in soup.find_all("option", value=RELEASE_ID):
        found.setdefault(opt["value"], opt.get_text(" ", strip=True))
    for lab in soup.find_all("label", attrs={"for": RELEASE_ID}):
        found.setdefault(lab["for"], lab.get_text(" ", strip=True))
    for a in soup.find_all("a", href=re.compile(r"^#pk-release-release-[0-9a-f]{32}$")):
        found.setdefault(RELEASE_ID.search(a["href"][len("#pk-release"):]).group(0), a.get_text(" ", strip=True))
    for art in soup.find_all("article", class_="presskit-component-release"):
        h1 = art.find("h1")
        rid = RELEASE_ID.search(" ".join(art.get("class", [])))
        if h1 and rid:
            found.setdefault(rid.group(0), h1.get_text(" ", strip=True))
    return [(rid, label) for rid, label in found.items() if SPEC_WORD.search(label)]


# --------------------------------------------------------------------------- discovery
def discover_honda(h: Host) -> list[dict]:
    """Specs tab of each model channel of the Honda Automobiles division."""
    lines = {"honda/accord": r"^honda-accord$", "honda/civic": r"^honda-civic$",
             "honda/cr-v": r"^(honda-cr-v|cr-v-e-fcev)$"}
    names = {"honda/accord": r"accord", "honda/civic": r"civic", "honda/cr-v": r"cr-?v"}
    r = h.get(h.base + "/en-US/honda-automobiles")
    channels = {}
    for href in re.findall(r'href="([^"]*/honda-automobiles/channels/([a-z0-9-]+))"', r.text if r else ""):
        for line, pat in lines.items():
            if re.match(pat, href[1]):
                channels.setdefault(href[1], line)
    log("honda channels", channels)
    out = []
    for slug, line in channels.items():
        url = f"{h.base}/en-US/honda-automobiles/channels/{slug}"
        r = h.get(url)
        if r is None:
            continue
        m = re.search(r"selectedTabId=([a-z0-9-]+-specs)\b", r.text)
        if not m:
            log("  no specs tab in", url)
            continue
        listing = h.listing(f"{url}?selectedTabId={m.group(1)}")
        for href, title in listing:
            year = title_year(title)
            if SPEC_WORD.search(title) and re.search(names[line], title, re.I) and in_range(line, year):
                out.append({"line": line, "year": year, "title": title, "url": href,
                            "via": f"{url}?selectedTabId={m.group(1)}"})
    return out


NISSAN_GROUPS = [("nissan/altima", r"^Altima\b"), ("nissan/sentra", r"^Sentra\b"),
                 ("nissan/rogue", r"^Rogue\b(?! Sport)"), ("nissan/pathfinder", r"^Pathfinder\b")]


def discover_presskit_specs(h: Host, kits: list[dict]) -> list[dict]:
    """Fetch every press kit and turn its specification tab(s) into spec page candidates."""
    out = []
    for kit in kits:
        r = h.get(kit["url"])
        if r is None:
            kit["note"] = "press kit not fetched"
            out.append({**kit, "url": "", "status": "kit_error"})
            continue
        tabs = spec_tabs(r.text)
        if not tabs:
            log("  no spec tab:", kit["url"])
            out.append({**kit, "url": "", "status": "no_spec_tab", "kit": kit["url"]})
            continue
        for rid, label in tabs:
            out.append({**kit, "url": f"{h.base}/en-US/releases/{rid}", "kit": kit["url"], "tab": label})
    return out


def discover_nissan(h: Host) -> list[dict]:
    url = h.base + "/en-US/pages/nissan-press-kit-by-model"
    r = h.get(url)
    if r is None:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    kits, group, seen = [], None, set()
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        href = a["href"]
        if re.search(r"/channels/", href) and text:
            group = text
            continue
        if "/releases/" not in href or not group or "gallery=" in href:
            continue
        m = re.match(r"^(20\d\d)\b", text)
        if not m:
            continue
        line = next((k for k, pat in NISSAN_GROUPS if re.search(pat, group)), None)
        year = int(m.group(1))
        target = h.absolute(href.split("?")[0])
        if line and in_range(line, year) and target not in seen:
            seen.add(target)
            kits.append({"line": line, "year": year, "title": f"{group} {text}", "kit_url": target,
                         "url": target, "via": url})
    log("nissan press kits in range:", len(kits))
    return discover_presskit_specs(h, kits)


INFINITI_MODELS = [("infiniti/q50", r"\bQ50\b"), ("infiniti/qx60", r"\b(QX60|JX\d*)\b"),
                   ("infiniti/fx-qx70", r"\b(QX70|FX\d*)\b")]


def discover_infiniti(h: Host) -> list[dict]:
    root = h.base + "/en-US/channels/us-united-states-infiniti"
    kits, out = [], []
    for href, title in h.listing(root + "?selectedTabId=us-united-states-infiniti-release-presskit"):
        line = next((k for k, pat in INFINITI_MODELS if re.search(pat, title)), None)
        year = title_year(title)
        if line and in_range(line, year) and re.search(r"press kit", title, re.I):
            kits.append({"line": line, "year": year, "title": title, "kit_url": href, "url": href,
                         "via": root + "?selectedTabId=us-united-states-infiniti-release-presskit"})
    for href, title in h.listing(root + "?selectedTabId=us-united-states-infiniti-specs"):
        line = next((k for k, pat in INFINITI_MODELS if re.search(pat, title)), None)
        year = title_year(title)
        if line and in_range(line, year) and SPEC_WORD.search(title):
            out.append({"line": line, "year": year, "title": title, "url": href,
                        "via": root + "?selectedTabId=us-united-states-infiniti-specs"})
    log("infiniti press kits in range:", len(kits), "spec releases:", len(out))
    return out + discover_presskit_specs(h, kits)


def mitsu_line(title: str) -> str | None:
    if not re.search(r"outlander", title, re.I) or re.search(r"canad", title, re.I):
        return None
    return "mitsubishi/outlander-sport" if re.search(r"outlander sport", title, re.I) else "mitsubishi/outlander"


def discover_mitsubishi(h: Host) -> list[dict]:
    channels = {}
    for page in ("/en-US", "/en-US/channels/vehicles"):
        r = h.get(h.base + page)
        if r is None:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=re.compile(r"/en-US/channels/[A-Za-z0-9-]+$")):
            text = " ".join(a.get_text(" ", strip=True).split())
            if re.search(r"outlander|archive|^20\d\d$", text, re.I) or re.search(r"outlander", a["href"], re.I):
                channels.setdefault(h.absolute(a["href"]), text)
        # model channels named only in the page source (e.g. the home page's commented-out
        # "Learn more" link to /en-US/channels/all-new-2022-outlander)
        for href in re.findall(r'href="((?:https://media\.mitsubishicars\.com)?/en-US/channels/[a-z0-9-]*outlander[a-z0-9-]*)"',
                               r.text):
            channels.setdefault(h.absolute(href), href.rsplit("/", 1)[1])
    log("mitsubishi channels:", len(channels))
    items = {}
    for url, name in channels.items():
        tab = url.rsplit("/", 1)[1] + "-presskits"
        for listing_url in (url, f"{url}?selectedTabId={tab}"):
            for href, title in h.listing(listing_url, max_pages=40):
                items.setdefault(href, (title, listing_url))
    kits, specs = [], []
    for href, (title, via) in items.items():
        line, year = mitsu_line(title), title_year(title)
        if not line or not in_range(line, year):
            continue
        if SPEC_WORD.search(title):
            specs.append({"line": line, "year": year, "title": title, "url": href, "via": via})
        elif re.search(r"press kit|press information", title, re.I):
            kits.append({"line": line, "year": year, "title": title, "kit_url": href, "url": href, "via": via})
    log("mitsubishi press kits in range:", len(kits), "spec releases:", len(specs))
    out = discover_presskit_specs(h, kits)
    # press kits whose specifications live in a separate channel ("Back" link of the kit page)
    for cand in [c for c in out if c.get("status") == "no_spec_tab"]:
        r = h.get(cand["kit"])
        if r is None:
            continue
        body = content_root(BeautifulSoup(r.text, "html.parser"))
        for a in body.find_all("a", href=re.compile(r"/channels/channel-[0-9a-f]+$")):
            for href, title in h.listing(h.absolute(a["href"]), max_pages=5):
                line, year = mitsu_line(title), title_year(title)
                if line and in_range(line, year) and SPEC_WORD.search(title):
                    specs.append({"line": line, "year": year, "title": title, "url": href,
                                  "via": h.absolute(a["href"])})
    return specs + out


DISCOVER = {"hondanews.com": discover_honda, "usa.nissannews.com": discover_nissan,
            "usa.infinitinews.com": discover_infiniti, "media.mitsubishicars.com": discover_mitsubishi}


# --------------------------------------------------------------------------- fetch
def file_name(url: str) -> str:
    seg = url.rstrip("/").rsplit("/", 1)[1]
    seg = re.sub(r"[^A-Za-z0-9._-]+", "-", seg)[:120]
    return seg


def fetch_spec(h: Host, cand: dict) -> None:
    url = cand["url"]
    if h.manifest.ok(url):
        return
    r = h.fetcher.get(url)
    row = {"make": h.make, "line": cand["line"], "year": cand["year"], "doc_type": "press_specifications",
           "title": cand["title"], "url": url, "retrieved_at": now(), "note": ""}
    if r is None or r.status_code != 200:
        row.update({"http_status": r.status_code if r is not None else "", "status": "http_error",
                    "note": "no response" if r is None else f"HTTP {r.status_code}"})
        h.manifest.add(row)
        log("  FAIL", url, row["note"])
        return
    body = r.content
    soup = BeautifulSoup(body, "html.parser")
    title = page_title(soup) or cand["title"]
    digest = sha256(body)
    rel = Path("press") / h.host / f"{file_name(url)}.html.gz"
    write_gz(RAW_ROOT / rel, body)
    write_pagetext(body, digest, rel)
    notes = []
    if cand.get("kit"):
        notes.append(f"spec tab '{cand.get('tab', '')}' of press kit {cand['kit']}")
    if cand.get("via"):
        notes.append(f"listed on {cand['via']}")
    if not leaf_tables(content_root(soup)):
        notes.append("no table in release body")
    row.update({"title": title, "http_status": r.status_code, "bytes": len(body), "sha256": digest,
                "path": rel.as_posix(), "status": "ok", "note": "; ".join(notes)})
    h.manifest.add(row)
    log("  ok", cand["line"], cand["year"], title)


def write_pagetext(body: bytes, digest: str, rel: Path) -> None:
    write_gz(RAW_ROOT / "pagetext" / f"{digest}.json.gz",
             json.dumps({"sha256": digest, "file": rel.as_posix(), "pages": [render_text(body)]},
                        ensure_ascii=False).encode("utf-8"))


def rebuild_text(host: str) -> None:
    """Re-render the page text of every stored page of a host (no network)."""
    manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
    n = 0
    for row in manifest.rows.values():
        if row.get("status") == "ok":
            body = read_maybe_gz(RAW_ROOT / row["path"])
            assert sha256(body) == row["sha256"], row["path"]
            write_pagetext(body, row["sha256"], Path(row["path"]))
            n += 1
    log(f"page text rebuilt for {n} pages of {host}")


def coverage(h: Host, cands: list[dict]) -> dict:
    found = {}
    for row in h.manifest.rows.values():
        if row.get("status") == "ok":
            found.setdefault(f"{row['line']}|{row['year']}", []).append(row["title"])
    result = {"host": h.host, "generated_at": now(), "lines": {}}
    for line, (lo, hi) in LINE_YEARS.items():
        if not line.startswith(h.make + "/"):
            continue
        per = {}
        for year in range(lo, hi + 1):
            titles = found.get(f"{line}|{year}")
            if titles:
                per[year] = {"status": "found", "titles": titles}
            else:
                kits = [c.get("kit") or c.get("kit_url") for c in cands
                        if c["line"] == line and c["year"] == year and c.get("status")]
                per[year] = {"status": "not_found",
                             "note": ("press kit without specification tab: " + ", ".join(kits)) if kits else
                             "no specification page listed on the newsroom"}
        result["lines"][line] = per
    return result


def run_host(host: str, rediscover: bool) -> None:
    h = Host(host)
    cache = MANIFEST_DIR / f"{host}.candidates.json"
    log("=== host", host)
    try:
        if cache.exists() and not rediscover:
            cands = json.loads(cache.read_text(encoding="utf-8"))
            log("candidates from cache:", len(cands))
        else:
            cands = DISCOVER[host](h)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
            log("candidates discovered:", len(cands))
        for cand in cands:
            if cand.get("url") and not cand.get("status"):
                fetch_spec(h, cand)
    except Blocked as exc:
        h.manifest.add({"make": h.make, "line": "", "year": "", "doc_type": "press_specifications",
                        "title": "", "url": f"{h.base}/#blocked", "retrieved_at": now(),
                        "status": "blocked", "note": f"host stopped: {exc}"})
        log("BLOCKED", host, exc)
        cands = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else []
    cov = coverage(h, cands)
    (MANIFEST_DIR / f"{host}.coverage.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
    ok = sum(1 for r in h.manifest.rows.values() if r.get("status") == "ok")
    missing = sum(1 for per in cov["lines"].values() for v in per.values() if v["status"] != "found")
    log(f"done {host}: ok pages {ok}, line-years without spec page {missing}, requests {h.fetcher.requests}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", action="append", choices=list(HOSTS), help="host(s) to collect; default all")
    ap.add_argument("--rediscover", action="store_true", help="crawl the listings again")
    ap.add_argument("--rebuild-text", action="store_true", help="only re-render page text of stored pages")
    args = ap.parse_args()
    for host in args.host or list(HOSTS):
        if args.rebuild_text:
            rebuild_text(host)
        else:
            run_host(host, args.rediscover)


if __name__ == "__main__":
    main()
