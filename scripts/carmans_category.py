"""carmans.net category page of one make against what is already downloaded (owner request
2026-10-04, Volkswagen).

1. The make's category page (https://www.carmans.net/category/<make>/) and its model
   sub-categories list the posts; each post is matched to our lines (us_tech_lines) for
   2014-2026 — also outside the line's US years, so that a post of one of our models from a year
   the US did not get it (2023 Passat, 2023 Touareg) is looked at and goes to the library.
2. Every matched post page is fetched again and ALL PDF links are taken from it (viewer
   `?file=`, direct `.pdf` links), not only the first one.
3. A PDF URL already downloaded is not fetched again; a new one is downloaded (one request at a
   time, 2-5 s pause) to RAW_ROOT/manuals/<make>/carmans/<post>[--<pdf name>].pdf and recorded
   in data_work/_shared/manifest_carmans.csv. Identical bytes (sha256) are recorded as such.

Output: data_work/_shared/carmans_<make>_category_<date>.json

  .venv/Scripts/python.exe scripts/carmans_category.py volkswagen [--list-only]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_carmans import FIELDS  # noqa: E402
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256  # noqa: E402
from us_tech_lines import LINES, MAKES  # noqa: E402

BASE = "https://www.carmans.net"
YEARS = (2014, 2026)
PDF_LINK = re.compile(r"""(?:viewer\.html\?file=([^#"'&\s]+\.pdf))|(?:href=["']([^"']+\.pdf)["'])""", re.I)


def our_line(post: str, make: str):
    """(line, year, in_us_years) for a post of one of our lines' models, any year 2014-2026."""
    found = re.fullmatch(r"(\d{4})-([a-z0-9-]+)", post)
    if not found:
        return None
    year = int(found.group(1))
    if not (YEARS[0] <= year <= YEARS[1]):
        return None
    for rest in (found.group(2), re.sub(r"-\d$", "", found.group(2))):
        rest = re.sub(r"-incl-[a-z-]+$", "", rest)
        hits = [line for line in LINES if line.make == make and line.carmans and re.fullmatch(line.carmans, rest)]
        if hits:
            line = max(hits, key=lambda ln: len(ln.carmans))
            return line, year, line.years[0] <= year <= line.years[1]
    return None


def category_posts(fetcher: Fetcher, manifest: Manifest, make: str) -> tuple[list[str], list[str]]:
    slug = MAKES[make]["carmans"]
    start = f"{BASE}/category/{slug}/"
    pages, posts, seen = [start], [], set()
    aliases = [slug] + (["vw-"] if slug == "volkswagen" else [])  # "vw-golf-8"
    while pages:
        url = pages.pop(0)
        if url in seen:
            continue
        seen.add(url)
        response = fetcher.get(url)
        status = response.status_code if response is not None else "ERROR"
        manifest.add({"kind": "category", "make": make, "url": url, "http_status": status, "retrieved_at": now(),
                      "status": "ok" if status == 200 else "error"})
        if status != 200:
            continue
        for link in re.findall(r'href="(https://www\.carmans\.net/[^"#?]+)"', response.text):
            link = link if link.endswith("/") else link + "/"
            if link.startswith(f"{BASE}/category/{slug}/") and link not in seen:
                pages.append(link)  # model sub-categories and their /page/N/
            elif "/category/" not in link and any(alias in link.rsplit("/", 2)[-2] for alias in aliases) and link not in posts:
                posts.append(link)
    return sorted(seen), sorted(posts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("make")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args(argv)
    make = args.make
    fetcher = Fetcher(pause=(2.0, 5.0), timeout=240)
    manifest = Manifest(WORK / "_shared" / "manifest_carmans.csv", FIELDS)
    by_sha = defaultdict(list)
    for row in manifest.rows.values():
        if row["kind"] == "pdf" and row["status"] == "ok" and row.get("sha256"):
            by_sha[row["sha256"]].append(row["post"])
    downloaded_before = {u: r for u, r in manifest.rows.items() if r["kind"] == "pdf" and r["status"] == "ok" and r["make"] == make}
    out = {"make": make, "checked_at": now(), "category_pages": [], "posts_on_page": 0, "posts_by_model": {},
           "our_posts": [], "other_posts": [], "pdf_files_before": len(downloaded_before),
           "unique_pdfs_before": len({r["sha256"] for r in downloaded_before.values()})}
    try:
        pages, posts = category_posts(fetcher, manifest, make)
        out["category_pages"], out["posts_on_page"] = pages, len(posts)
        models = defaultdict(list)
        for url in posts:
            post = url.rstrip("/").rsplit("/", 1)[-1]
            year = re.match(r"(\d{4})-", post)
            model = re.sub(r"^\d{4}-|-\d$", "", post)
            models[model].append(int(year.group(1)) if year else None)
            hit = our_line(post, make)
            if hit:
                line, y, in_years = hit
                out["our_posts"].append({"post": post, "page_url": url, "line": line.key, "year": y, "in_us_years": in_years})
            else:
                out["other_posts"].append({"post": post, "page_url": url, "model": model, "year": int(year.group(1)) if year else None})
        out["posts_by_model"] = {m: sorted(y for y in ys if y) for m, ys in sorted(models.items())}
        print(f"category pages {len(pages)}; posts {len(posts)}; ours 2014-2026 {len(out['our_posts'])}", flush=True)
        if args.list_only:
            return write(out, make)
        for item in out["our_posts"]:
            response = fetcher.get(item["page_url"])
            status = response.status_code if response is not None else "ERROR"
            links = []
            for viewer, href in PDF_LINK.findall(response.text if response is not None else ""):
                link = urljoin(item["page_url"], unquote(viewer or href))
                if link not in links:
                    links.append(link)
            item["pdf_urls"] = links
            manifest.add({"kind": "page", "make": make, "line": item["line"], "year": item["year"], "post": item["post"],
                          "page_url": item["page_url"], "url": item["page_url"] + "#rescan-" + datetime.now(UTC).strftime("%Y%m%d"),
                          "http_status": status, "retrieved_at": now(), "status": "ok" if status == 200 else "error",
                          "note": " | ".join(links)})
            item["files"] = []
            for n, pdf_url in enumerate(links):
                hit = manifest.ok(pdf_url)
                if hit and (RAW_ROOT / hit["path"]).exists():
                    item["files"].append({"url": pdf_url, "status": "already", "post_saved_as": hit["post"], "sha256": hit["sha256"]})
                    continue
                response = fetcher.get(pdf_url, headers={"Referer": item["page_url"]})
                code = response.status_code if response is not None else "ERROR"
                meta = {"make": make, "line": item["line"], "year": item["year"], "post": item["post"], "page_url": item["page_url"]}
                if code != 200 or not response.content.startswith(b"%PDF"):
                    manifest.add({**meta, "kind": "pdf", "url": pdf_url, "http_status": code, "retrieved_at": now(),
                                  "status": "not_found" if code == 404 else "error"})
                    item["files"].append({"url": pdf_url, "status": f"error {code}"})
                    print("pdf_error", item["post"], code, pdf_url, flush=True)
                    continue
                digest = sha256(response.content)
                name = item["post"] if len(links) == 1 else f"{item['post']}--{Path(pdf_url).stem}"
                dest = RAW_ROOT / "manuals" / make / "carmans" / f"{name}.pdf"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(response.content)
                same = sorted(set(by_sha.get(digest, [])))
                manifest.add({**meta, "kind": "pdf", "url": pdf_url, "http_status": code, "bytes": len(response.content),
                              "sha256": digest, "retrieved_at": now(), "path": dest.relative_to(RAW_ROOT).as_posix(),
                              "status": "ok", "note": f"same bytes as {', '.join(same)}" if same else ""})
                by_sha[digest].append(item["post"])
                item["files"].append({"url": pdf_url, "status": "downloaded", "sha256": digest, "bytes": len(response.content),
                                      "same_bytes_as": same})
                print("downloaded", item["post"], len(response.content), "same as " + ",".join(same) if same else "new", flush=True)
    except Blocked as exc:
        out["stopped"] = str(exc)
        print("STOPPED: repeated block", exc, flush=True)
    out["requests"] = fetcher.requests
    return write(out, make)


def write(out: dict, make: str) -> int:
    path = WORK / "_shared" / f"carmans_{make}_category_{datetime.now(UTC).strftime('%Y%m%d')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("->", path.relative_to(WORK.parent), flush=True)
    return 3 if out.get("stopped") else 0


if __name__ == "__main__":
    sys.exit(main())
