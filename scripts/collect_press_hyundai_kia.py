"""Collect the US press "specifications" documents of the Hyundai and Kia lines.

Hosts (US newsrooms only, see data_work/_shared/press/FORMAT.md):
  www.hyundainews.com  Hyundai Motor America media center. A client-rendered Nuxt app; its own
                       pages load JSON from https://www.hyundainews.com/api (routes and calls read
                       from the site's JS bundle): /api/models (model tree: line > model year >
                       model), /api/models/<slug> (tabs + documents of a model page),
                       /api/models/<slug>/specifications|specs-and-features (tab documents),
                       /api/press-kits/<slug> (press kit with attached documents). The spec
                       sheets are PDF documents under /assets/... linked from the "Specifications"
                       / "Specs and Features" tab of the model-year page.
  www.kiamedia.com     Kia America media site. Its robots.txt disallows "/" for the AI agents
                       ClaudeBot, Claude-Web and anthropic-ai. This collector is run by an
                       Anthropic AI agent, so the host is not crawled: one manifest row with
                       status=blocked records the reason.

For every line of make hyundai/kia in scripts/us_tech_lines.py and every model year
2014-2026 within Line.years, the collector walks the model tree, opens every model page of
that line and year, and downloads the documents whose tab or title names specifications.

Files (FORMAT.md):
  data_work/_shared/manifest_press/<host>.csv            manifest (resumable; ok URLs are reused)
  RAW_ROOT/press/<host>/<document>.pdf                    spec PDFs as published
  RAW_ROOT/press/<host>/api/<name>.json.gz                API answers used for discovery
  RAW_ROOT/press/<host>/robots.txt.gz                     robots.txt as fetched
  RAW_ROOT/pagetext/<sha256>.json.gz                      {"sha256","file","pages":[text per PDF page]}
Manifest doc_type: press_specifications (spec documents), press_index (API discovery
answers), robots (robots.txt). Line-years without a spec document get a row with
status=not_found whose url is the model-year page on the site.

Run (pdfplumber is needed for the page text):
  uv run --no-project --with httpx --with pdfplumber --with pypdfium2 python scripts/collect_press_hyundai_kia.py
  options: --host www.hyundainews.com|www.kiamedia.com  --refresh-index (re-fetch API answers)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
import urllib.robotparser
from pathlib import Path
from urllib.parse import quote, urlsplit

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
from us_tech_lines import LINES  # noqa: E402

FIELDS = [
    "make", "line", "year", "doc_type", "title", "url", "http_status", "bytes", "sha256",
    "retrieved_at", "path", "status", "note",
]
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
YEARS = (2014, 2026)
# Product tokens of Anthropic agents; a robots.txt group that disallows one of them applies here.
AI_AGENT_TOKENS = ("ClaudeBot", "Claude-User", "Claude-Web", "anthropic-ai")
SPEC_TITLE = re.compile(r"(?i)\bspec(s|ifications?)?\b")

HYUNDAI = "www.hyundainews.com"
KIA = "www.kiamedia.com"
HOST_MAKE = {HYUNDAI: "hyundai", KIA: "kia"}

# hyundainews model tree: name of the line node -> registry line keys. A model page (child of a
# model-year node) goes to the first key whose pattern matches the model page name.
HYUNDAI_LINE_NODES = {
    "SONATA": [("hyundai/sonata", r".")],
    "ELANTRA": [("hyundai/elantra", r"^(?!.*\bTCR\b)")],  # ELANTRA N TCR is a race car
    "TUCSON": [("hyundai/tucson", r"^(?!.*FUEL CELL)")],
    "SANTA FE": [("hyundai/santa-fe-sport", r"(?i)\bSANTA FE SPORT\b"), ("hyundai/santa-fe", r".")],
    "ACCENT": [("hyundai/accent", r".")],
    "KONA": [("hyundai/kona", r".")],
}


def log(message: str) -> None:
    print(message, flush=True)


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


class Host:
    def __init__(self, host: str, refresh_index: bool):
        self.host = host
        self.make = HOST_MAKE[host]
        self.base = f"https://{host}"
        self.manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        self.fetcher = Fetcher(headers={"Accept-Language": "en_US"})
        self.refresh_index = refresh_index
        self.lines = {line.key: line for line in LINES if line.make == self.make}
        self.robots: urllib.robotparser.RobotFileParser | None = None

    # ---- robots -----------------------------------------------------------------------------
    def check_robots(self) -> str | None:
        """Fetch robots.txt; return a block reason or None. Always re-fetched."""
        url = f"{self.base}/robots.txt"
        response = self.fetcher.get(url)
        if response is None:
            return "robots.txt not reachable"
        body = response.content
        rel = Path("press") / self.host / "robots.txt.gz"
        write_gz(RAW_ROOT / rel, body)
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(body.decode("utf-8", errors="replace").splitlines() if response.status_code == 200 else [])
        self.robots = parser
        denied = [token for token in AI_AGENT_TOKENS if not parser.can_fetch(token, f"{self.base}/")]
        reason = None
        if denied:
            reason = (
                "robots.txt disallows / for " + ", ".join(denied)
                + " (Anthropic AI agents); host not crawled"
            )
        self.manifest.add({
            "make": self.make, "doc_type": "robots", "title": "robots.txt", "url": url,
            "http_status": response.status_code, "bytes": len(body), "sha256": sha256(body),
            "retrieved_at": now(), "path": rel.as_posix(), "status": "blocked" if reason else "ok",
            "note": reason or "no rule against the pages used",
        })
        return reason

    def allowed(self, url: str) -> bool:
        return self.robots is None or self.robots.can_fetch(self.fetcher.client.headers["User-Agent"], url)

    # ---- API answers (discovery) ------------------------------------------------------------
    def api(self, path: str, line: str = "", year: str = "", title: str = "") -> object | None:
        url = f"{self.base}/api{path}"
        rel = Path("press") / self.host / "api" / (re.sub(r"[^A-Za-z0-9._-]+", "_", path.strip("/")) + ".json.gz")
        row = self.manifest.ok(url)
        if row and not self.refresh_index and (RAW_ROOT / row["path"]).exists():
            return json.loads(read_maybe_gz(RAW_ROOT / row["path"]))
        if not self.allowed(url):
            self.manifest.add({"make": self.make, "line": line, "year": year, "doc_type": "press_index",
                               "title": title, "url": url, "status": "robots_disallowed", "retrieved_at": now()})
            return None
        response = self.fetcher.get(url, headers={"accept": "application/json"})
        status = response.status_code if response is not None else ""
        body = response.content if response is not None else b""
        is_json = response is not None and "json" in response.headers.get("content-type", "")
        ok = status == 200 and is_json
        if ok:
            write_gz(RAW_ROOT / rel, body)
        self.manifest.add({
            "make": self.make, "line": line, "year": year, "doc_type": "press_index", "title": title,
            "url": url, "http_status": status, "bytes": len(body), "sha256": sha256(body) if body else "",
            "retrieved_at": now(), "path": rel.as_posix() if ok else "",
            "status": "ok" if ok else ("not_found" if status == 404 else "error"),
            "note": "" if ok else clean(body[:200].decode("utf-8", errors="replace")),
        })
        return json.loads(body) if ok else None

    # ---- documents ----------------------------------------------------------------------------
    def doc_uses(self, url: str) -> set[tuple[str, str]]:
        """(line, year) of every ok manifest row of a document (the CSV keeps all rows)."""
        uses = set()
        if self.manifest.path.exists():
            with self.manifest.path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    if row["url"] == url and row["status"] == "ok":
                        uses.add((row["line"], row["year"]))
        return uses

    def download(self, url: str, line: str, year: int, title: str, note: str) -> dict:
        row = self.manifest.ok(url)
        if row and (RAW_ROOT / row["path"]).exists():
            ensure_pagetext(row)
            if (row["line"], str(row["year"])) != (line, str(year)) and (line, str(year)) not in self.doc_uses(url):
                # the same document is linked from another line-year: one more row for it
                row = {**row, "line": line, "year": year, "note": note}
                self.manifest.add(row)
            return row
        if not self.allowed(url):
            row = {"make": self.make, "line": line, "year": year, "doc_type": "press_specifications",
                   "title": title, "url": url, "status": "robots_disallowed", "retrieved_at": now(), "note": note}
            self.manifest.add(row)
            return row
        response = self.fetcher.get(url)
        status = response.status_code if response is not None else ""
        body = response.content if response is not None else b""
        ctype = response.headers.get("content-type", "") if response is not None else ""
        name = Path(urlsplit(url).path).name
        ok = status == 200 and bool(body)
        rel = Path("press") / self.host / (name if name.lower().endswith(".pdf") else name + ".gz")
        digest = sha256(body) if body else ""
        if ok:
            target = RAW_ROOT / rel
            if name.lower().endswith(".pdf"):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            else:
                write_gz(target, body)
            if body[:5] == b"%PDF-":
                pages = pdf_pages(body)
                store_pagetext(digest, rel.as_posix(), pages)
                note = f"{note}; {len(pages)} PDF pages"
            else:
                note = f"{note}; not a PDF ({ctype}), no page text"
        row = {
            "make": self.make, "line": line, "year": year, "doc_type": "press_specifications", "title": title,
            "url": url, "http_status": status, "bytes": len(body), "sha256": digest, "retrieved_at": now(),
            "path": rel.as_posix() if ok else "", "status": "ok" if ok else "error", "note": note,
        }
        self.manifest.add(row)
        return row


TEXT_ENGINE = "pypdfium2 get_text_range"  # content-stream order, as scripts/pdf_text_store.py


def pdf_pages(body: bytes) -> list[str]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(body)
    pages = []
    for index in range(len(pdf)):
        page = pdf[index]
        pages.append(page.get_textpage().get_text_range())
        page.close()
    pdf.close()
    return pages


def store_pagetext(digest: str, file: str, pages: list[str]) -> None:
    target = RAW_ROOT / "pagetext" / f"{digest}.json.gz"
    if target.exists():
        with gzip.open(target, "rt", encoding="utf-8") as handle:
            existing = json.load(handle)
        if existing.get("file") != file:
            log(f"  pagetext {digest[:12]} already stored for {existing.get('file')}; kept")
            return
    target.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(target, "wt", encoding="utf-8") as handle:
        json.dump({"sha256": digest, "file": file, "pages": pages, "text_engine": TEXT_ENGINE}, handle)


def ensure_pagetext(row: dict) -> None:
    """Page text of an already stored PDF: (re)built when missing or made by another engine."""
    target = RAW_ROOT / "pagetext" / f"{row['sha256']}.json.gz"
    if target.exists():
        with gzip.open(target, "rt", encoding="utf-8") as handle:
            existing = json.load(handle)
        if existing.get("text_engine") == TEXT_ENGINE or existing.get("file") != row["path"]:
            return
    body = (RAW_ROOT / row["path"]).read_bytes()
    if body[:5] == b"%PDF-":
        store_pagetext(row["sha256"], row["path"], pdf_pages(body))


# ---- www.hyundainews.com ------------------------------------------------------------------------
def hyundai_model_pages(tree: dict, lines: dict) -> tuple[dict, dict]:
    """(line, year) -> [(model page slug, name, year slug)], and (line, year) -> year-node slug."""
    pages: dict[tuple[str, int], list[tuple[str, str, str]]] = {}
    year_nodes: dict[tuple[str, int], str] = {}
    seen: set[str] = set()

    def visit(node: dict) -> None:
        name = clean(node.get("name")).upper()
        if name in HYUNDAI_LINE_NODES:
            for year_node in node.get("children") or []:
                found = re.fullmatch(r"(\d{4})", clean(year_node.get("name")))
                if not found:
                    continue
                year = int(found.group(1))
                for model in year_node.get("children") or []:
                    model_name = clean(model.get("name"))
                    for key, pattern in HYUNDAI_LINE_NODES[name]:
                        line = lines.get(key)
                        if not line or not re.search(pattern, model_name.upper()):
                            continue
                        if not (max(YEARS[0], line.years[0]) <= year <= min(YEARS[1], line.years[1])):
                            break
                        year_nodes.setdefault((key, year), year_node["slug"])
                        if model["slug"] not in seen:
                            seen.add(model["slug"])
                            pages.setdefault((key, year), []).append((model["slug"], model_name, year_node["slug"]))
                        break
        for child in node.get("children") or []:
            visit(child)

    for root in tree.get("data") or []:
        visit(root)
    return pages, year_nodes


def hyundai_spec_docs(host: Host, slug: str, key: str, year: int, kits_seen: dict) -> list[tuple[str, str, str]]:
    """Spec documents of one model page: [(absolute url, title, how found)]."""
    detail = host.api(f"/models/{slug}", key, str(year), f"model page {slug}")
    if not isinstance(detail, dict) or not isinstance(detail.get("data"), dict):
        return []
    data = detail["data"]
    docs: dict[str, tuple[str, str]] = {}
    by_id = {doc.get("id"): doc for doc in data.get("documents") or []}

    def add(doc_url: str, title: str, how: str) -> None:
        if doc_url:
            url = host.base + quote(doc_url, safe="/%:@&=+$,;~-_.!*'()")
            docs.setdefault(url, (clean(title), how))

    for tab in data.get("tabs") or []:
        tab_name = clean(tab.get("name"))
        if not SPEC_TITLE.search(tab_name):
            continue
        tab_slug = tab.get("slug") or ""
        if tab_slug.startswith("/assets/"):
            doc = by_id.get(tab.get("id")) or {}
            add(tab_slug, doc.get("title") or tab_name, f"tab '{tab_name}' of /models/{slug}")
        elif tab_slug in ("/specifications", "/specs-and-features"):
            listing = host.api(f"/models/{slug}{tab_slug}", key, str(year), f"{tab_name} tab of {slug}")
            for doc in listing if isinstance(listing, list) else (listing or {}).get("data") or []:
                add(doc.get("url"), doc.get("title") or tab_name, f"tab '{tab_name}' of /models/{slug}")
    for doc in data.get("documents") or []:
        if SPEC_TITLE.search(doc.get("title") or ""):
            add(doc.get("url"), doc.get("title"), f"documents of /models/{slug}")
    for kit in data.get("pressKits") or []:
        kit_slug = kit.get("slug")
        if not kit_slug or kit_slug.startswith("/"):
            continue  # a kit entry that links to a page path is not a press kit slug
        if kit_slug not in kits_seen:
            answer = host.api(f"/press-kits/{kit_slug}", key, str(year), f"press kit {kit_slug}")
            kit_data = answer.get("data") if isinstance(answer, dict) else None
            kits_seen[kit_slug] = [
                (doc.get("url"), doc.get("title"))
                for doc in (kit_data or {}).get("documents") or []
                if SPEC_TITLE.search(doc.get("title") or "")
            ]
        for doc_url, title in kits_seen[kit_slug]:
            add(doc_url, title, f"press kit {kit_slug}")
    return [(url, title, how) for url, (title, how) in docs.items()]


def collect_hyundai(host: Host) -> dict:
    tree = host.api("/models", title="model tree")
    if not isinstance(tree, dict):
        raise RuntimeError("model tree not available")
    pages, year_nodes = hyundai_model_pages(tree, host.lines)
    kits_seen: dict[str, list] = {}
    summary: dict[str, dict[int, str]] = {}
    for key, line in host.lines.items():
        summary[key] = {}
        for year in range(max(YEARS[0], line.years[0]), min(YEARS[1], line.years[1]) + 1):
            models = pages.get((key, year), [])
            if not models:
                summary[key][year] = "no model-year page on the site"
                continue
            found: dict[str, tuple[str, list[str]]] = {}
            for slug, name, _ in models:
                for url, title, how in hyundai_spec_docs(host, slug, key, year, kits_seen):
                    found.setdefault(url, (title, []))[1].append(f"{name} ({how})")
            if not found:
                url = f"{host.base}/models/{year_nodes[(key, year)]}"
                note = "no Specifications tab or spec document on model pages: " + ", ".join(slug for slug, _, _ in models)
                prev = host.manifest.rows.get(url)
                if not (prev and prev.get("status") == "not_found" and prev.get("note") == note):
                    host.manifest.add({
                        "make": host.make, "line": key, "year": year, "doc_type": "press_specifications",
                        "title": "", "url": url, "retrieved_at": now(), "status": "not_found", "note": note,
                    })
                summary[key][year] = "no spec document"
                log(f"{key} {year}: no spec document ({len(models)} model pages)")
                continue
            results = []
            for url, (title, where) in found.items():
                row = host.download(url, key, year, title, "; ".join(where))
                results.append(f"{row['status']}:{title}")
                log(f"{key} {year}: {row['status']} {title} <{url}>")
            summary[key][year] = " | ".join(results)
    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=[HYUNDAI, KIA], action="append")
    parser.add_argument("--refresh-index", action="store_true")
    args = parser.parse_args(argv)
    for name in args.host or [HYUNDAI, KIA]:
        host = Host(name, args.refresh_index)
        log(f"== {name}")
        try:
            reason = host.check_robots()
            if reason:
                log(f"{name}: blocked - {reason}")
                continue
            if name == HYUNDAI:
                summary = collect_hyundai(host)
                for key, years in summary.items():
                    for year, text in years.items():
                        log(f"SUMMARY {key} {year}: {text}")
        except Blocked as exc:
            host.manifest.add({"make": host.make, "doc_type": "robots", "url": f"{host.base}/",
                               "retrieved_at": now(), "status": "blocked",
                               "note": f"repeated 403/429, stopped: {exc}"})
            log(f"{name}: blocked - {exc}")
        log(f"{name}: {host.fetcher.requests} requests")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
