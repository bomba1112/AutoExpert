"""Owner-manual copies from carmans.net for every line of Appendix A (Appendix B fallback).

Page addresses come from the site's own WordPress sitemap (wp-sitemap-posts-post-N.xml),
not from guessed slugs. Each manual page embeds a PDF viewer; the file is taken from its
`viewer.html?file=...pdf` parameter. One request at a time, 2-5 s pause.

Outputs:
  RAW_ROOT/manuals/<make>/carmans/<post-slug>.pdf
  data_work/_shared/manifest_carmans.csv          every request (page and PDF)
  data_work/_shared/carmans_posts.json            sitemap posts matched to lines, plus the
                                                  unmatched posts of Appendix A makes and
                                                  any maintenance / warranty guide posts

Usage:
  .venv/Scripts/python.exe scripts/collect_carmans.py [--make hyundai] [--list-only]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))

from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256  # noqa: E402
from us_tech_lines import MAKE_ORDER, MAKES, carmans_line  # noqa: E402

FIELDS = [
    "kind", "make", "line", "year", "post", "page_url", "url", "http_status", "bytes",
    "sha256", "retrieved_at", "path", "status", "note",
]
SITEMAP = "https://www.carmans.net/wp-sitemap.xml"
GUIDE = re.compile(r"maintenance|warranty|service-guide|scheduled", re.I)


def sitemap_posts(fetcher: Fetcher, manifest: Manifest) -> list[str]:
    index = fetcher.get(SITEMAP)
    manifest.add({"kind": "sitemap", "url": SITEMAP, "http_status": index.status_code if index else "ERROR",
                  "retrieved_at": now(), "status": "ok" if index is not None and index.status_code == 200 else "error"})
    posts = []
    for sub in re.findall(r"<loc>([^<]+)</loc>", index.text if index is not None else ""):
        if "posts-post" not in sub and "posts-page" not in sub:
            continue
        response = fetcher.get(sub)
        manifest.add({"kind": "sitemap", "url": sub, "http_status": response.status_code if response else "ERROR",
                      "retrieved_at": now(), "status": "ok" if response is not None and response.status_code == 200 else "error"})
        if response is not None:
            posts += re.findall(r"<loc>(https://www\.carmans\.net/[^<]+)</loc>", response.text)
    return posts


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args(argv)
    fetcher = Fetcher(pause=(2.0, 5.0), timeout=180)
    manifest = Manifest(WORK / "_shared" / "manifest_carmans.csv", FIELDS)
    posts = sitemap_posts(fetcher, manifest)
    makes = [args.make] if args.make else MAKE_ORDER
    carmans_makes = {MAKES[m]["carmans"]: m for m in makes}
    matched, unmatched, guides = [], [], []
    for url in posts:
        post = url.rstrip("/").rsplit("/", 1)[-1]
        if GUIDE.search(post):
            guides.append(url)
        hit = carmans_line(post)
        if hit and hit[0].make in makes:
            line, year, _ = hit
            matched.append({"line": line.key, "make": line.make, "year": year, "post": post, "page_url": url,
                            "done": line.done})
        elif any(f"-{cm}-" in f"-{post}-" for cm in carmans_makes):
            unmatched.append(url)
    order = {m: i for i, m in enumerate(MAKE_ORDER)}
    matched.sort(key=lambda r: (order[r["make"]], r["line"], r["year"], r["post"]))
    (WORK / "_shared" / "carmans_posts.json").write_text(
        json.dumps({"posts_in_sitemap": len(posts), "matched": matched, "unmatched_same_make": sorted(unmatched),
                    "maintenance_or_warranty_posts": sorted(guides)}, indent=1),
        encoding="utf-8",
    )
    print(f"sitemap posts {len(posts)}; matched {len(matched)}; guides {len(guides)}", flush=True)
    if args.list_only:
        return 0
    try:
        for item in matched:
            if item["done"]:
                continue
            dest = RAW_ROOT / "manuals" / item["make"] / "carmans" / f"{item['post']}.pdf"
            meta = {k: item[k] for k in ("make", "line", "year", "post", "page_url")}
            page_hit = manifest.ok(item["page_url"])
            pdf_url = page_hit["note"] if page_hit else None
            if not pdf_url:
                response = fetcher.get(item["page_url"])
                status = response.status_code if response is not None else "ERROR"
                found = re.search(r"viewer\.html\?file=([^#\"&]+\.pdf)", response.text if response is not None else "")
                if status != 200 or not found:
                    manifest.add({**meta, "kind": "page", "url": item["page_url"], "http_status": status,
                                  "retrieved_at": now(), "status": "not_found"})
                    print("not_found", item["post"], flush=True)
                    continue
                pdf_url = urljoin(item["page_url"], found.group(1))
                manifest.add({**meta, "kind": "page", "url": item["page_url"], "http_status": status,
                              "retrieved_at": now(), "status": "ok", "note": pdf_url})
            hit = manifest.ok(pdf_url)
            if hit and (RAW_ROOT / hit["path"]).exists():
                continue
            response = fetcher.get(pdf_url, headers={"Referer": item["page_url"]})
            status = response.status_code if response is not None else "ERROR"
            if status != 200 or not response.content.startswith(b"%PDF"):
                manifest.add({**meta, "kind": "pdf", "url": pdf_url, "http_status": status, "retrieved_at": now(),
                              "status": "not_found" if status == 404 else "error"})
                print("pdf_error", item["post"], status, flush=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(response.content)
            manifest.add({**meta, "kind": "pdf", "url": pdf_url, "http_status": status, "bytes": len(response.content),
                          "sha256": sha256(response.content), "retrieved_at": now(),
                          "path": dest.relative_to(RAW_ROOT).as_posix(), "status": "ok"})
            print("ok", item["post"], len(response.content), flush=True)
    except Blocked as exc:
        print("STOPPED: repeated block", exc, flush=True)
        return 3
    print("requests", fetcher.requests, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
