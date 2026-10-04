"""Edition of every carmans.net PDF: market and the model year(s) the document itself states.

Owner decision 2026-10-04: when one PDF is posted on the pages of several model years, it is
bound only to the model years stated inside the document (cover, edition number); the other
years count as having no owner's manual. A document whose cover names another model year than
the page it was posted on is bound to its own year as well (a "2021 Atlas" post serving the
"2019 Volkswagen Atlas" manual is the 2019 manual).

Per document (one entry per sha256, every post that serves it listed):
  stated years   "model year 2021" / "Model Year 2016" on the cover (first pages)
                 a title "2019 Volkswagen Atlas", "2016 Accord Owner's Manual" on the cover
                 an edition number "Edition 01/2023" (VW prints the model year this way) —
                 used only when the cover states no model year
                 print dates ("Print status", copyright, "Printed in") are not model years
  years used     stated years (within the line's US years); none stated: the year of the
                 post when the document is posted for one year only, else none
  market         scripts/extract_manual_facts.py edition_market, plus: a document with US
                 units and the US defect-reporting text naming NHTSA (or "United States
                 version" on the cover) is a US edition even when it names ACEA oils only —
                 VW US manuals give ACEA only for the emergency top-up
                 An English edition for other markets ("tyres", "petrol", right-hand drive, no
                 US text) is EU (the owner's library grouping of European editions).
  doc type       owner's manual, quick-start guide, supplement, or no text layer (scan)
  REVIEWED       files read by hand (a scan read by OCR): market and years with the quote

Every file that is not a US edition is registered in the library of other markets
(data_work/_library/manifest.csv); the PDF stays in the raw store.

Output: data_work/<make>/manual_editions_carmans.json (read by extract_manual_facts.documents).

  .venv/Scripts/python.exe scripts/manual_editions.py volkswagen [more makes]
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

COVER_PAGES = 3
MODEL_YEAR = re.compile(r"\b(?:model year|MY)\s*(20[1-2]\d)\b|\b(20[1-2]\d)\s+model year\b", re.I)
EDITION = re.compile(r"\bEdition:?\s*(\d{2})\s*[/.]\s*(20[1-2]\d)\b")
PRINT_DATE = re.compile(r"Print status|Printed in|©|Copyright|\(c\)\s*20", re.I)
SCAN = re.compile(r"Scanned by CamScanner", re.I)
LIBRARY_FIELDS = ["make", "model", "generation_or_years", "market", "market_markers", "source_url", "path",
                  "sha256", "retrieved_at", "pages"]
LIBRARY_MAKE = {"volkswagen": "vw"}  # the spelling the library already uses
# files read by hand: a scan without a text layer, its cover and last page read by OCR (RapidOCR,
# 2026-10-04); the quotes are the OCR text
REVIEWED = {
    "bb5ea3dc4dec46da81db69d7da0e9e9e724d22af9292f851383472fada288aa0": {
        "market": "EU", "doc_type": "no_text_layer", "stated_years": [],
        "market_markers": {"ocr_cover": "Owner's manual | Passat, Passat Estate, Passat Alltrack | Edition05.2016",
                           "ocr_last_page": "Owner'smanual: Passat, Passat Estate, PassatAlltrack | Stand:01.04.2016 | Englisch:05.2016 | Teile-Nr:3G0012720AC",
                           "ocr_page_2": "Volkswagen AG", "rule": "European English edition (Estate / Alltrack bodies, Volkswagen AG, 'Englisch')"},
    },
    # a 9-page US quick-start guide: too short for the unit counts of edition_market
    "7b66330a87522183eab11bddd66f15bb55beaa5b426cc0adcd2ddfa8af155242": {
        "market": "US", "doc_type": "quick_start_guide", "stated_years": [2021], "years_used": [2021],
        "market_markers": {"cover": "2021 Arteon Quick-Start Guide",
                           "last_page": "MY21-Arteon-01 Volkswagen Customer Care Center (800) 822-8987 © 2021 Volkswagen of America, Inc.",
                           "rule": "US quick-start guide (Volkswagen of America, US customer care number)"},
    },
}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pages_of(sha: str) -> list[str] | None:
    path = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"]


def flat(text: str) -> str:
    return " ".join(text.split())


def title_years(cover: str, names: list[str]) -> list[tuple[int, str]]:
    """A title on the cover: a year next to the make or a model name ("2019 Volkswagen Atlas",
    "2016 Accord Owner's Manual", "Owner's Manual 2017 Altima")."""
    out = []
    alternatives = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    pattern = re.compile(rf"\b(20[1-2]\d)\s+(?:{alternatives})\b|\b(?:{alternatives})\s+(20[1-2]\d)\b(?!\s*[/.-]\d)", re.I)
    for m in pattern.finditer(cover):
        before = cover[max(0, m.start() - 40): m.start()]
        if PRINT_DATE.search(before):
            continue
        out.append((int(m.group(1) or m.group(2)), cover[max(0, m.start() - 30): m.end() + 30]))
    return out


def market_of(pages: list[str]) -> tuple[str, dict]:
    from extract_manual_facts import edition_market

    market, marks = edition_market(pages)
    text = "\n".join(pages)
    cover = flat(" ".join(pages[:COVER_PAGES]))
    marks = dict(marks)
    marks["nhtsa_defect_reporting"] = int(any(
        re.search(r"Reporting Safety Defects", p, re.I) and re.search(r"National Highway Traffic Safety Administration|NHTSA", p)
        for p in pages))
    marks["united_states_version_cover"] = int(bool(re.search(r"United States version|USA version", cover, re.I)))
    marks["volkswagen_of_america"] = len(re.findall(r"Volkswagen (?:Group )?of America", text))
    us_units = marks["usa"] >= 3 and (marks["quarts"] + marks["gallons"]) >= 2 and marks["mph"] >= 3
    if market != "US" and us_units and (marks["nhtsa_defect_reporting"] or marks["united_states_version_cover"]):
        return "US", {**marks, "rule": "US units and the US defect-reporting text / US version cover (ACEA named for the top-up only)"}
    marks["tyres"] = len(re.findall(r"\btyres?\b", text, re.I))
    marks["tires"] = len(re.findall(r"\btires?\b", text, re.I))
    marks["petrol"] = len(re.findall(r"\bpetrol\b", text, re.I))
    marks["right_hand_drive"] = len(re.findall(r"right-hand drive", text, re.I))
    if (market == "UNKNOWN" and marks["tyres"] > 10 * (marks["tires"] + 1) and marks["petrol"] and not marks["nhtsa_defect_reporting"]
            and not marks["united_states_version_cover"]):
        return "EU", {**marks, "rule": "English edition for other markets (tyres, petrol), no US text"}
    return market, marks


def doc_type(pages: list[str]) -> str:
    text = flat(" ".join(pages))
    cover = flat(" ".join(pages[:COVER_PAGES]))[:600]
    if len(text) < 200 * max(1, len(pages)) / 10 or SCAN.search(text[:400]):
        return "no_text_layer"
    if re.search(r"Quick[- ]?Start Guide|Quick Reference Guide", cover, re.I):
        return "quick_start_guide"
    if re.search(r"^\W*Supplement\b", cover, re.I) and len(pages) < 80:
        return "supplement"
    return "owners_manual"


def editions(make: str) -> dict:
    manifest = [r for r in read_csv(WORK / "_shared" / "manifest_carmans.csv") if r["make"] == make]
    rows = [r for r in manifest if r["kind"] == "pdf" and r["status"] == "ok"]
    by_sha = defaultdict(list)
    for r in rows:
        by_sha[r["sha256"]].append(r)
    # a post whose page embeds a PDF already downloaded for another post has no pdf row of its
    # own: the page rows (their note lists the embedded PDF URLs) say which posts serve a file
    sha_of_url = {r["url"]: r["sha256"] for r in rows}
    file_of_sha = {r["sha256"]: r for r in rows}
    for page in manifest:
        if page["kind"] != "page" or page["status"] != "ok" or not page.get("note"):
            continue
        for url in [u.strip() for u in page["note"].split(" | ") if u.strip()]:
            sha = sha_of_url.get(url)
            if sha and page["post"] not in {r["post"] for r in by_sha[sha]}:
                by_sha[sha].append({**file_of_sha[sha], "post": page["post"], "year": page["year"], "line": page["line"],
                                    "page_url": page["page_url"], "url": url, "served_only": True})
    out = {}
    for sha, posts in sorted(by_sha.items(), key=lambda kv: min(int(r["year"]) for r in kv[1])):
        line_keys = sorted({r["line"] for r in posts})
        post_years = sorted({int(r["year"]) for r in posts})
        entry = {"sha256": sha, "posts": [{"post": r["post"], "year": int(r["year"]), "line": r["line"], "url": r["url"],
                                            "page_url": r["page_url"], "path": r["path"],
                                            **({"file_saved_for": file_of_sha[sha]["post"]} if r.get("served_only") else {})}
                                           for r in sorted(posts, key=lambda r: (int(r["year"]), r["post"]))],
                 "post_years": post_years, "lines": line_keys}
        pages = pages_of(sha)
        if sha in REVIEWED:
            review = REVIEWED[sha]
            out[sha] = {**entry, "status": "ok", "pages": len(pages or []), "doc_type": review["doc_type"], "market": review["market"],
                        "market_markers": review["market_markers"], "year_evidence": [], "stated_years": review["stated_years"],
                        "stated_by": "cover" if review.get("years_used") else None, "rule": "read by hand (see market_markers)",
                        "years_used": review.get("years_used", []),
                        "posts_without_manual": sorted({r["post"] for r in posts if int(r["year"]) not in review.get("years_used", [])})}
            continue
        if pages is None:
            out[sha] = {**entry, "status": "no_page_cache", "years_used": [], "market": "UNKNOWN"}
            continue
        entry["pages"] = len(pages)
        entry["doc_type"] = doc_type(pages)
        entry["cover"] = flat(" ".join(pages[:2]))[:300]
        entry["market"], entry["market_markers"] = market_of(pages) if entry["doc_type"] != "no_text_layer" else ("UNKNOWN", {})
        names = [BY_KEY[k].name for k in line_keys if k in BY_KEY] + [make.replace("-", " ").title()]
        names += [a for k in line_keys if k in BY_KEY for a in BY_KEY[k].epa_base]
        evidence = []
        for n, page in enumerate(pages[:COVER_PAGES]):
            cover = flat(page)
            for m in MODEL_YEAR.finditer(cover):
                evidence.append({"page": n + 1, "year": int(m.group(1) or m.group(2)), "method": "model year on the cover",
                                 "quote": cover[max(0, m.start() - 40): m.end() + 20]})
            for year, quote in title_years(cover, names):
                evidence.append({"page": n + 1, "year": year, "method": "title on the cover", "quote": quote})
            for m in EDITION.finditer(cover):
                evidence.append({"page": n + 1, "year": int(m.group(2)), "method": "edition number on the cover",
                                 "quote": cover[max(0, m.start() - 20): m.end() + 40]})
        strong = sorted({e["year"] for e in evidence if e["method"] != "edition number on the cover"})
        weak = sorted({e["year"] for e in evidence if e["method"] == "edition number on the cover"})
        stated = strong or weak
        entry["year_evidence"] = evidence
        entry["stated_years"] = stated
        entry["stated_by"] = ("cover" if strong else "edition number" if weak else None)
        years_window = set()
        for k in line_keys:
            if k in BY_KEY:
                years_window |= set(range(BY_KEY[k].years[0], BY_KEY[k].years[1] + 1))
        if stated:
            used = [y for y in stated if y in years_window]
            entry["rule"] = "years stated in the document"
        elif len(post_years) == 1:
            used = post_years
            entry["rule"] = "no year stated; posted for one model year only: that year"
        else:
            used = []
            entry["rule"] = "no year stated and posted for several model years: bound to none (owner decision 2026-10-04)"
        entry["years_used"] = used
        entry["posts_without_manual"] = sorted({r["post"] for r in posts if int(r["year"]) not in used})
        entry["status"] = "ok"
        out[sha] = entry
    return out


def register_library(make: str, result: dict) -> int:
    """Files of other markets go to the library (data_work/_library/manifest.csv), once per file."""
    path = WORK / "_library" / "manifest.csv"
    rows = read_csv(path) if path.exists() else []
    have = {r["sha256"] for r in rows}
    added = 0
    for sha, e in result.items():
        if e.get("market") in ("US", "UNKNOWN", None) or sha in have:
            continue
        posts = e["posts"]
        model = sorted({p["line"].split("/")[-1] for p in posts})
        rows.append({"make": LIBRARY_MAKE.get(make, make), "model": ";".join(model),
                     "generation_or_years": f"carmans posts {min(e['post_years'])}-{max(e['post_years'])}"
                                            + (f", edition {e['stated_years'][0]}" if e.get("stated_years") else ""),
                     "market": e["market"], "market_markers": json.dumps(e.get("market_markers", {}), ensure_ascii=False),
                     "source_url": posts[0]["url"], "path": "rawstore:" + next(p["path"] for p in posts if p.get("path")),
                     "sha256": sha, "retrieved_at": next((r.get("retrieved_at") for r in read_csv(WORK / "_shared" / "manifest_carmans.csv")
                                                          if r.get("sha256") == sha and r["kind"] == "pdf"), ""),
                     "pages": e.get("pages", "")})
        added += 1
    if added:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=LIBRARY_FIELDS)
            writer.writeheader()
            writer.writerows({k: r.get(k, "") for k in LIBRARY_FIELDS} for r in rows)
    return added


def main(argv: list[str]) -> int:
    for make in argv:
        result = editions(make)
        path = WORK / make / "manual_editions_carmans.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(make, "library: added", register_library(make, result))
        for sha, e in result.items():
            print(f"{make} {sha[:8]} {e.get('doc_type', '-'):18} {e.get('market'):8} posts {e['post_years']} "
                  f"stated {e.get('stated_years')} ({e.get('stated_by')}) used {e.get('years_used')} | {e.get('cover', '')[:70]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
