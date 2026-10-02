"""Mercedes-Benz operator's manuals: alternative official US editions for line-years whose chosen
edition could not be downloaded (www.mbusa.com gateway 502 / no answer).

The mbusa owner's manual API lists several US editions per model year (other body styles, other
edition dates). For every line-year still without a downloaded manual, up to MAX_TRIES other
editions of that line-year are tried — same body style first, then the smaller file — one request
at a time with a 180 s timeout, until one downloads. Rows go to the same host manifest as
collect_official.py, so documents()/extract_manual_facts.py pick them up.

  .venv/Scripts/python.exe scripts/collect_mbusa_alternatives.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_official import FIELDS, file_name  # noqa: E402
from us_tech_common import RAW_ROOT, WORK, Blocked, Fetcher, Manifest, now, sha256  # noqa: E402

HOST = "www.mbusa.com"
MAX_TRIES = 2


def main() -> int:
    plan = json.loads((WORK / "_shared" / "official_manuals" / "mercedes-benz.json").read_text(encoding="utf-8"))
    manuals = [d for d in plan["documents"] if d.get("doc_type") == "owners_manual" and HOST in d.get("url", "")]
    manifest = Manifest(WORK / "_shared" / "manifest_official" / f"{HOST}.csv", FIELDS)
    ok_line_years = set()
    tried = set()
    primary_body = {}
    for row in manifest.rows.values():
        lines = [x for x in row.get("lines", "").split(";") if x]
        years = [int(y) for y in row.get("years", "").split(";") if y]
        if row.get("doc_type") != "owners_manual":
            continue
        tried.add(row["url"])
        for line in lines:
            for year in years:
                if row.get("status") == "ok":
                    ok_line_years.add((line, year))
    by_line_year = defaultdict(list)
    for d in manuals:
        by_line_year[(d["line"], d["year"])].append(d)
        if d["url"] in tried:
            primary_body[(d["line"], d["year"])] = d.get("body", "")
    todo = sorted(k for k in by_line_year if k not in ok_line_years and k in primary_body)
    fetcher = Fetcher(pause=(2.0, 5.0), timeout=180, attempts=1)
    done = failed = 0
    log = []
    try:
        for line, year in todo:
            body = primary_body[(line, year)]
            candidates = [d for d in by_line_year[(line, year)] if d["url"] not in tried]
            candidates.sort(key=lambda d: (d.get("body", "") != body, d.get("size_bytes") or 10**12))
            got = False
            for d in candidates[:MAX_TRIES]:
                meta = {"make": "mercedes-benz", "lines": line, "years": str(year), "doc_type": "owners_manual",
                        "title": d.get("title", "")[:200], "url": d["url"]}
                response = fetcher.get(d["url"], headers={"Referer": d["page_url"]} if d.get("page_url") else None)
                tried.add(d["url"])
                body_bytes = response.content if response is not None else b""
                if response is None or response.status_code != 200 or not body_bytes.startswith(b"%PDF"):
                    status = response.status_code if response is not None else "ERROR"
                    manifest.add({**meta, "http_status": status, "retrieved_at": now(), "status": "error",
                                  "note": "alternative edition; " + ("not a PDF body" if status == 200 else "")})
                    failed += 1
                    continue
                dest = RAW_ROOT / "official" / "mercedes-benz" / HOST / file_name(d["url"], body_bytes)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(body_bytes)
                manifest.add({**meta, "http_status": 200, "bytes": len(body_bytes), "sha256": sha256(body_bytes),
                              "retrieved_at": now(), "path": dest.relative_to(RAW_ROOT).as_posix(), "status": "ok",
                              "note": "alternative edition for a line-year whose chosen edition did not download"})
                done += 1
                got = True
                print("ok", line, year, d.get("title", "")[:80], len(body_bytes), flush=True)
                break
            log.append({"line": line, "year": year, "downloaded": got, "tried": min(len(candidates), MAX_TRIES),
                        "alternatives_listed": len(candidates)})
            if not got:
                print("none", line, year, f"({min(len(candidates), MAX_TRIES)} of {len(candidates)} alternatives tried)", flush=True)
    except Blocked as exc:
        print("STOPPED:", exc, flush=True)
    (WORK / "_shared" / "manifest_official" / "mbusa_alternatives_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"line-years {len(todo)}; downloaded {done}; failed requests {failed}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
