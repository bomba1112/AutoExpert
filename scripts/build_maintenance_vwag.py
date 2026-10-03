"""Volkswagen and Audi maintenance schedules from the official US Maintenance Cards
(ownersliterature.vw.com, "VW / Audi Maintenance Card", one per model year, all models).

Layout (2014-2026, both makes): the US section of the gas/hybrid schedule (the Canada and
battery-electric sections are not read), a mileage grid whose services are defined in footnotes,
e.g.
  1) First minor maintenance service at 10,000 miles (15,000 km) or 1 year after delivery,
     whichever occurs first. Minor maintenance services thereafter occur at intervals of 20,000
     miles (30,000 km) or every 2 years after the last minor maintenance service ...
  2) Standard maintenance services occur at intervals of 20,000 miles ... or every 2 years ...
  3) Extended maintenance services occur at intervals of 40,000 miles ...
then the items of each service ("Engine Oil, Change and Replace Oil Filter  All Vehicles") and
"Additional Maintenance Items" with their own interval and applicability per row ("Spark Plugs -
Replace  Every 40,000 miles (60K km), or 4 years, whichever occurs first  Arteon, Golf R").

Items: the service items whose job is a maintenance job (oil, brakes, filters, fluids, belts,
plugs …) carry the service ({"service": "Minor Maintenance"}) and its footnote interval
(FIRST / SUBSEQUENT or EVERY); additional items carry their own interval. Applicability names
("A4 40 TFSI", "S4", "Atlas", "All Vehicles except: RS 6 …") are mapped to our lines through the
EPA model names of the line; a row naming none of our models is not written. A service whose
interval the card does not print in a footnote (the 2014 Audi card) gives a gap. km as printed
by the card; a printed km that does not fit the miles (a typo such as "40,000 miles (60 km)")
is replaced by the miles converted by the units module, with a note.

  .venv/Scripts/python.exe scripts/build_maintenance_vwag.py
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import (  # noqa: E402
    action_of, gen_for, generations_of, interval_of, item, job_of, merge_years, miles_to_km, norm, our_lines,
    page_text, pdf_source, sha_of, write,
)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MANIFEST = WORK / "_shared" / "manifest_official" / "ownersliterature.vw.com.csv"
BULLET = ""
REGISTRY = {"volkswagen": "factory-vw-us", "audi": "factory-audi-us"}
PUBLISHER = {"volkswagen": "Volkswagen of America (ownersliterature.vw.com)", "audi": "Audi of America (ownersliterature.vw.com)"}
US_START = re.compile(r"^\d+(?:\.\d+)*\s+(?:MY \d{4} )?(?:Audi |VW )?Maintenance Schedule(?! \(Battery| \(Routan)(?!.*Canada)", re.M)
US_END = re.compile(r"^\d+(?:\.\d+)*\s+(?:MY \d{4} )?(?:Audi |VW )?Maintenance Schedule.*(?:Canada|Battery Electric|Routan Only)", re.M)
FOOT_FIRST = re.compile(r"(?P<n>\d)\)\s*First (?P<svc>\w+) maintenance service at (?P<m1>[\d,]+) miles(?: \((?P<k1>[\d,]+) km\))? or (?P<y1>\d+) years? after delivery, whichever occurs first\.\s*"
                        r"\w+ maintenance services thereafter occur at intervals of (?P<m2>[\d,]+) miles(?: \((?P<k2>[\d,]+) km\))?(?: or every (?P<y2>\d+) years?)?", re.I)
FOOT_EVERY = re.compile(r"(?P<n>\d)\)\s*(?P<svc>\w+) maintenance services occur at intervals of (?P<m>[\d,]+) miles(?: \((?P<k>[\d,]+) km\))?(?: or every (?P<y>\d+) years?)?", re.I)
GRID = re.compile(r"⇒\s*(?P<svc>[A-Za-z ]+?) Maintenance(?: - small)?\s*(?P<n>\d)\)")
SECTION = re.compile(r"^\d+(?:\.\d+)+\s+(?P<name>(?:Minor|Standard|Extended|Major) Maintenance|Additional Maintenance Items)\s*$", re.M)
APPLIES_ALL = re.compile(r"All (?:Applicable )?Vehicles|All applicable (?:engines|vehicles)", re.I)
INTERVAL_START = re.compile(r"(?<!then )(?=\bEvery \d|\bOnly once at |\b\d+ years? aft\.)", re.I)


# the interval phrase of an additional item; what follows it is the applicability
INTERVAL_PHRASE = re.compile(
    r"(?:Every\s+[\d,]+\s+miles(?:\s*\([^)]*\))?(?:,?\s*or\s+(?:every\s+)?\d+\s+years?)?(?:,?\s*whichever\s+occurs\s+first)?"
    r"|Every\s+\d+\s+years?(?:\s+regardless\s+of\s+mileage(?:\s+driven)?)?"
    r"|\d+\s+years?\s+aft\.\s+registration,?\s+then\s+every\s+\d+\s+years?\s*-?\s*USA"
    r"|Only\s+once\s+at\s+first\s+[\d,]+\s+miles(?:\s*\([^)]*\))?)"
    r"(?:\s*-\s*Severe\s+driving\s+condi\s*tions\s+only\s*\([^)]*\))?", re.I)


def dehyphen(text: str) -> str:
    """Join words the layout broke ("Ti‐ guan", "Ve‐ hicles", "re￾place")."""
    return re.sub(r"[‐­￾]\s*", "", text)


def plausible(interval: dict | None, text: str) -> dict | None:
    """A printed km that does not fit the miles ("40,000 miles (60 km)") is not used."""
    if not interval or not interval.get("interval_miles_original") or not interval.get("interval_km"):
        return interval
    ratio = interval["interval_km"] / interval["interval_miles_original"]
    if not 1.4 <= ratio <= 1.8:
        interval = {**interval, "interval_km": miles_to_km(interval["interval_miles_original"]),
                    "km_note": f"the card prints «{interval['matched']}»; km converted from the miles"}
    return interval


def line_index(make: str) -> dict:
    """First word of every EPA model name of our lines ("RS 6 Avant" -> "RS6") -> line slug."""
    import json
    out = {}
    for slug, line in our_lines(make).items():
        path = WORK / make / "staging" / slug / "staging.json"
        if not path.exists():
            continue
        st = json.loads(path.read_text(encoding="utf-8"))
        names = {line.name} | {v["epa_model"] for c in st["configurations"] for v in c.get("epa_vehicles", [])}
        for name in names:
            first = re.sub(r"^(RS|S|SQ)\s+(\d)", r"\1\2", name).split()[0].upper()
            out.setdefault(first, slug)
    return out


def lines_named(text: str, index: dict, doc_lines: list[str]) -> tuple[list[str], dict]:
    """Our lines an applicability cell names, and per line the names it gives."""
    if APPLIES_ALL.search(text):
        excepted = re.search(r"except:?\s*(.*)$", text, re.I | re.S)
        note = {"except": " ".join(excepted.group(1).split())} if excepted and excepted.group(1).strip() else {}
        return list(doc_lines), {slug: note for slug in doc_lines}
    per_line = defaultdict(list)
    text = dehyphen(text)
    code = None
    for token in re.split(r",|\n|/", text):
        token = " ".join(token.replace("￾", "").split()).strip(" *")
        if not token or token.lower().startswith(("only vehicles", "engines w")):
            continue
        token = re.sub(r"^Only\s+", "", token)
        # transmission codes heading a model list ("09P: Atlas, Tiguan", "0GC (DSG): Arteon")
        lead = re.match(r"^([0-9][0-9A-Z]{2})(?:\s*\([^)]*\))?:\s*", token)
        if lead:
            code = lead.group(1)
            token = token[lead.end():]
        if not token:
            continue
        if code:
            token = f"{token} ({code})"
        first = re.sub(r"^(RS|S|SQ)\s+(\d)", r"\1\2", token).split()[0].upper() if token.split() else ""
        slug = index.get(first)
        if slug and slug in doc_lines:
            per_line[slug].append(token)
    return list(per_line), {slug: {"models": "; ".join(names)} for slug, names in per_line.items()}


def us_section(pages: list[str]) -> list[tuple[int, str]]:
    """(page number, line) of the US gas/hybrid schedule."""
    out, inside = [], False
    for number, text in enumerate(pages, start=1):
        for line in text.split("\n"):
            if not inside and US_START.match(line.strip()) and "Canada" not in line:
                inside = True
            elif inside and US_END.match(line.strip()):
                return out
            if inside:
                out.append((number, line))
    return out


def rows_of(lines: list[tuple[int, str]]) -> list[tuple[int, str, str]]:
    """(page, section, row text) for every bulleted row of the item lists."""
    rows, section, current = [], None, None
    for number, line in lines:
        m = SECTION.match(line.strip())
        if m:
            section = m.group("name")
            current = None
            continue
        if line.strip().startswith(BULLET):
            current = [number, section, line.strip().lstrip(BULLET).strip()]
            rows.append(current)
        elif current is not None and section and line.strip() and not re.match(r"^\d+\s+\d{1,2}\.\d{4}$|^Service Item|^Labor Item|^\d+$", line.strip()):
            current[2] += "\n" + line.strip()
    return [(n, s, t) for n, s, t in rows if s]


def build_doc(row: dict, index: dict, lines_meta: dict) -> tuple[list[dict], list[dict], dict]:
    make = row["make"]
    path = RAW_ROOT / row["path"]
    sha = sha_of(path)
    pages = page_text(sha)
    year = int(row["years"])
    doc_lines = [l for l in row["lines"].split(";") if l in lines_meta]
    key = f"{make}-maintenance-card-{year}"
    section = us_section(pages)
    text = norm(" ".join(l for _, l in section))
    services = {}
    for m in GRID.finditer(text):
        services[m.group("n")] = m.group("svc").strip().title() + " Maintenance"
    footnotes = {}
    for m in FOOT_FIRST.finditer(text):
        k1 = int(m.group("k1").replace(",", "")) if m.group("k1") else None
        k2 = int(m.group("k2").replace(",", "")) if m.group("k2") else None
        footnotes[m.group("n")] = {"quote": m.group(0), "first": plausible(interval_of(f"{m.group('m1')} miles{f' ({k1:,} km)' if k1 else ''} or {m.group('y1')} years whichever"), m.group(0)),
                                   "subsequent": plausible(interval_of(f"{m.group('m2')} miles{f' ({k2:,} km)' if k2 else ''}" + (f" or {m.group('y2')} years whichever" if m.group("y2") else "")), m.group(0))}
    for m in FOOT_EVERY.finditer(text):
        if m.group("n") in footnotes:
            continue
        k = int(m.group("k").replace(",", "")) if m.group("k") else None
        footnotes[m.group("n")] = {"quote": m.group(0), "every": plausible(interval_of(f"{m.group('m')} miles{f' ({k:,} km)' if k else ''}" + (f" or {m.group('y')} years whichever" if m.group("y") else "")), m.group(0))}
    names = {m.group("n"): m.group("svc") for m in FOOT_FIRST.finditer(text)}
    names.update({m.group("n"): m.group("svc") for m in FOOT_EVERY.finditer(text) if m.group("n") not in names})
    # the service name comes from the grid or from the footnote itself ("Extended" has no grid number)
    service_interval = {services.get(n) or f"{names[n].title()} Maintenance": f for n, f in footnotes.items() if n in names}
    # "Perform Minor Maintenance" in the standard list: the minor items are due at the standard interval too
    section_rows = rows_of(section)
    extra_rows = []
    for _, sec, t in section_rows:
        m = re.search(r"Perform (Minor|Standard) Maintenance", norm(t), re.I)
        if m:
            inner = m.group(1).title() + " Maintenance"
            extra_rows += [(pg, sec, rt) for pg, s2, rt in section_rows if s2 == inner and job_of(norm(rt))]
    items, gaps, used_pages = [], [], set()
    foot_page = next((p for p, l in section if re.match(r"\s*1\)\s*First|\s*\d\)\s*\w+ maintenance services", l)), section[0][0] if section else 1)
    for page, sec, row_text in section_rows + extra_rows:
        flat = norm(row_text)
        job = job_of(flat.split("  ")[0])
        if sec == "Additional Maintenance Items":
            head, *blocks = INTERVAL_START.split(row_text)
            job = job_of(norm(head))
            if not job or not blocks:
                continue
            for block in blocks:
                interval = plausible(interval_of(norm(block)), block)
                first_two = re.search(r"(\d+) years? aft\. registration, then every (\d+) years?\s*-?USA", norm(block), re.I)
                once = re.search(r"Only once at first ([\d,]+) miles", norm(block), re.I)
                if re.search(r"Canada", norm(block), re.I) and not re.search(r"USA", norm(block)):
                    continue
                raw_block = dehyphen(block)
                phrase = INTERVAL_PHRASE.search(raw_block)
                if not phrase:
                    continue
                applies_text = raw_block[phrase.end():].strip(" -\n\r")
                if not applies_text:
                    continue  # no applicability printed after the interval: not assigned
                slugs, apps = lines_named(applies_text, index, doc_lines)
                # the quote as the page prints it: item and interval, or the interval alone when the
                # row runs over a page break (the page is the one that holds it)
                quote, cite_page = None, page
                for candidate in (f"{head} {phrase.group(0)}", phrase.group(0)):
                    for pg in (page, page + 1):
                        if pg <= len(pages) and norm(candidate) in norm(pages[pg - 1]):
                            quote, cite_page = norm(candidate), pg
                            break
                    if quote:
                        break
                if quote is None:
                    for slug in slugs:
                        gaps.append({"scope": f"{make}/{slug} MY{year} ({key} p.{page})", "field": f"maintenance:{job}",
                                     "reason": f"row text not found again on one page: {norm(head)[:80]}"})
                    continue
                for slug in slugs:
                    gens = generations_of(make, slug)
                    gen = gen_for(gens, year)
                    if not gen:
                        continue
                    common = dict(page=cite_page, source=key, quote=quote, locator="Additional Maintenance Items", applicability={**apps.get(slug, {})})
                    action = action_of(norm(head))
                    if first_two:
                        items.append(item(slug, gen, year, job, action, occurrence="FIRST", interval={"interval_months": int(first_two.group(1)) * 12}, **common))
                        items.append(item(slug, gen, year, job, action, occurrence="SUBSEQUENT", interval={"interval_months": int(first_two.group(2)) * 12}, **common))
                    elif once:
                        miles = int(once.group(1).replace(",", ""))
                        items.append(item(slug, gen, year, job, action, occurrence="FIRST",
                                          interval={"interval_km": miles_to_km(miles), "interval_miles_original": miles}, note="only once", **common))
                    elif interval:
                        note = interval.pop("km_note", None)
                        severe = bool(re.search(r"severe driving", norm(block), re.I))
                        items.append(item(slug, gen, year, job, action, condition="SEVERE" if severe else "NORMAL",
                                          interval={k: v for k, v in interval.items() if k != "matched"}, note=note, **common))
                    used_pages.add(cite_page)
            continue
        if not job or sec not in service_interval:
            continue
        if re.search(r"Canada Only", flat, re.I):
            continue
        foot = service_interval[sec]
        slugs, apps = lines_named(flat, index, doc_lines)
        for slug in slugs:
            gen = gen_for(generations_of(make, slug), year)
            if not gen:
                continue
            app = {"service": sec, **apps.get(slug, {})}
            common = dict(source=key, locator=sec, applicability=app)
            action = action_of(flat)
            if "first" in foot:
                for occ, iv in (("FIRST", foot["first"]), ("SUBSEQUENT", foot["subsequent"])):
                    note = (iv or {}).pop("km_note", None) if iv else None
                    items.append(item(slug, gen, year, job, action, occurrence=occ, interval={k: v for k, v in (iv or {}).items() if k != "matched"},
                                      quote=flat, page=page, note=f"{sec}: {foot['quote']}"[:600] if not note else note, **common))
            else:
                iv = foot["every"]
                items.append(item(slug, gen, year, job, action, interval={k: v for k, v in iv.items() if k not in ("matched", "km_note")},
                                  quote=flat, page=page, note=f"{sec}: {foot['quote']}"[:600], **common))
            used_pages.update({page, foot_page})
    for sec_name in {s for _, s, _ in rows_of(section)} - set(service_interval) - {"Additional Maintenance Items"}:
        for slug in doc_lines:
            gaps.append({"scope": f"{make}/{slug} MY{year} ({key})", "field": f"maintenance:{sec_name}",
                         "reason": "the card lists the service items but prints no interval for this service (grid only)"})
    source = pdf_source(key, path, sha, row["url"], f"{make.title()} Maintenance Card MY{year} ({row['title'][:80]})",
                        PUBLISHER[make], REGISTRY[make], [year], used_pages or {1}, row["retrieved_at"])
    return items, gaps, source


def main() -> int:
    rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8", newline=""))
            if r.get("status") == "ok" and r.get("doc_type") == "maintenance_guide" and r["make"] in REGISTRY]
    for make in sorted({r["make"] for r in rows}):
        lines_meta = our_lines(make)
        index = line_index(make)
        per_line, gaps_line, sources = defaultdict(list), defaultdict(list), {}
        for row in sorted((r for r in rows if r["make"] == make), key=lambda r: r["years"]):
            items, gaps, source = build_doc(row, index, lines_meta)
            sources[source["key"]] = source
            for it in items:
                per_line[it["id"].split("-")[0] if False else None]  # placeholder (kept for clarity)
            for it in items:
                slug = next(s for s in lines_meta if it["id"].startswith(f"{s}-"))
                per_line[slug].append(it)
            for g in gaps:
                gaps_line[g["scope"].split()[0].split("/")[1]].append(g)
            print(make, row["years"], "items", len(items), "gaps", len(gaps), flush=True)
        for slug in lines_meta:
            merged = merge_years(per_line.get(slug, []))
            if merged or gaps_line.get(slug):
                write(make, slug, "card", sources, merged, gaps_line.get(slug, []))
                print("  ", make, slug, "items", len(merged), "gaps", len(gaps_line.get(slug, [])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
