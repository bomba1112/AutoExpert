"""Download the official manufacturer documents found by the portal research (Appendix B).

Input: data_work/_shared/official_manuals/<make>.json (one file per make, written by the
per-source research agents: verified links on manufacturer domains only).
Documents taken: owner's manuals (PDF), maintenance guides and warranty & maintenance
booklets (PDF; Mopar maintenance schedules as JSON). Quick-reference and other leaflets are
skipped. Mercedes-Benz lists several dated editions per model year; one edition per
line-year is taken (main body, latest edition dated before June of the model year).

Rules: robots.txt is honoured per host; hosts that refuse scripted clients or require a
login/VIN are not worked around (recorded as `skipped`); one process per host, one request
at a time, 2-5 s pause.

Output: RAW_ROOT/official/<make>/<host>/<file>, data_work/_shared/manifest_official/<host>.csv

  .venv/Scripts/python.exe scripts/collect_official.py --list            # plan per host
  .venv/Scripts/python.exe scripts/collect_official.py --host <host>     # download one host
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.robotparser
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, UA, WORK, Blocked, Fetcher, Manifest, now, sha256  # noqa: E402

FIELDS = ["make", "lines", "years", "doc_type", "title", "url", "http_status", "bytes", "sha256",
          "retrieved_at", "path", "status", "note"]
WANTED = {"owners_manual", "maintenance_guide", "warranty_maintenance"}
# Hosts the research found closed to scripted clients (bot protection, robots.txt, login,
# geo-block). They are not retried here; their documents stay gaps for the report.
CLOSED = {
    "www.bmwusa.com": "refuses scripted clients (bot protection); browser-only",
    "www.fordservicecontent.com": "refuses scripted clients (bot protection); browser-only",
    "www.tesla.com": "Akamai refuses scripted clients",
    "owners.hyundaiusa.com": "robots.txt disallows /content/",
    "owners.kia.com": "robots.txt disallows /content/",
    "assets.sia.toyota.com": "AccessDenied from this network (geo-restricted)",
}
MAIN_BODY = re.compile(r"sedan|suv|4 door coupe|4-door", re.I)


def plan() -> dict[str, list[dict]]:
    by_host: dict[str, dict[str, dict]] = defaultdict(dict)
    for path in sorted((WORK / "_shared" / "official_manuals").glob("*.json")):
        make = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        docs = [
            d for d in data.get("documents", [])
            if d.get("doc_type") in WANTED and d.get("url") and d.get("format", "pdf") in ("pdf", "json")
        ]
        if make == "mercedes-benz":
            docs = mercedes_pick(docs)
        for d in docs:
            host = urlparse(d["url"]).netloc
            entry = by_host[host].setdefault(
                d["url"],
                {"make": make, "url": d["url"], "doc_type": d["doc_type"], "title": d.get("title", ""),
                 "lines": set(), "years": set(), "page_url": d.get("page_url", "")},
            )
            entry["lines"].add(d.get("line", ""))
            entry["years"].add(d.get("year"))
    return {h: list(v.values()) for h, v in by_host.items()}


def mercedes_pick(docs: list[dict]) -> list[dict]:
    """One owner's manual per line-year: main body, latest edition dated before June MY."""
    manuals = defaultdict(list)
    keep = [d for d in docs if d["doc_type"] != "owners_manual"]
    for d in docs:
        if d["doc_type"] == "owners_manual":
            manuals[(d.get("line"), d.get("year"))].append(d)
    for (line, year), group in manuals.items():
        main = [d for d in group if MAIN_BODY.search(d.get("body", "") + " " + d.get("title", ""))] or group

        def key(d):
            edition = d.get("edition") or ""
            found = re.match(r"(\d{4})-(\d{2})", edition)
            stamp = (int(found.group(1)), int(found.group(2))) if found else (0, 0)
            before = stamp <= (int(year or 0), 6)
            return (before, stamp if before else (-stamp[0], -stamp[1]))

        keep.append(max(main, key=key))
    return keep


def robots_ok(host: str, url: str) -> bool:
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(f"https://{host}/robots.txt")
    try:
        parser.read()
    except Exception:  # unreachable robots.txt: treat as allowed, as crawlers do
        return True
    return parser.can_fetch(UA, url)


def file_name(url: str, body: bytes) -> str:
    """Unique per URL: several hosts end every URL with the same segment (Kia: /en_US)."""
    path = unquote(urlparse(url).path).strip("/")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path)[-150:] or "document"
    ext = ".pdf" if body.startswith(b"%PDF") else ".json" if body[:1] in (b"{", b"[") else ".bin"
    return stem if stem.lower().endswith(ext) else stem + ext


def download_host(host: str, items: list[dict]) -> int:
    # one manifest per host: the hosts run as parallel processes
    manifest = Manifest(WORK / "_shared" / "manifest_official" / f"{host}.csv", FIELDS)
    fetcher = Fetcher(pause=(2.0, 5.0), timeout=300)
    done = failed = skipped = 0
    for item in sorted(items, key=lambda i: (i["make"], i["url"])):
        meta = {"make": item["make"], "lines": ";".join(sorted(x for x in item["lines"] if x)),
                "years": ";".join(str(y) for y in sorted(y for y in item["years"] if y)),
                "doc_type": item["doc_type"], "title": item["title"][:200], "url": item["url"]}
        if manifest.ok(item["url"]):
            continue
        if host in CLOSED:
            manifest.add({**meta, "retrieved_at": now(), "status": "skipped", "note": CLOSED[host]})
            skipped += 1
            continue
        if not robots_ok(host, item["url"]):
            manifest.add({**meta, "retrieved_at": now(), "status": "skipped", "note": "robots.txt disallows"})
            skipped += 1
            continue
        try:
            response = fetcher.get(item["url"], headers={"Referer": item["page_url"]} if item["page_url"] else None)
        except Blocked as exc:
            manifest.add({**meta, "retrieved_at": now(), "status": "blocked", "note": str(exc)})
            print("STOPPED host", host, exc, flush=True)
            return 3
        status = response.status_code if response is not None else "ERROR"
        body = response.content if response is not None else b""
        is_pdf = body.startswith(b"%PDF")
        is_json = item["url"].lower().endswith(".json") and body[:1] in (b"{", b"[")
        if status != 200 or not (is_pdf or is_json):
            manifest.add({**meta, "http_status": status, "retrieved_at": now(), "status": "error",
                          "note": "not a PDF/JSON body" if status == 200 else ""})
            failed += 1
            continue
        dest = RAW_ROOT / "official" / item["make"] / host / file_name(item["url"], body)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        manifest.add({**meta, "http_status": status, "bytes": len(body), "sha256": sha256(body),
                      "retrieved_at": now(), "path": dest.relative_to(RAW_ROOT).as_posix(), "status": "ok"})
        done += 1
        print("ok", host, dest.name, len(body), flush=True)
    print(f"{host}: ok {done}, failed {failed}, skipped {skipped}, requests {fetcher.requests}", flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--host")
    args = parser.parse_args(argv)
    hosts = plan()
    if args.list or not args.host:
        for host, items in sorted(hosts.items(), key=lambda kv: -len(kv[1])):
            print(f"{host}\t{len(items)}\t{'CLOSED: ' + CLOSED[host] if host in CLOSED else ''}")
        return 0
    return download_host(args.host, hosts.get(args.host, []))


if __name__ == "__main__":
    sys.exit(main())
