"""Fluids and capacities from mycarusermanual.com pages (Appendix E), US editions only.

The site serves each manual section as absolutely positioned text blocks (PDF rendered to
HTML: <div style="left:..em;top:..em">), not as HTML tables. The blocks are turned into
positioned "words" and run through the same row geometry and field rules as the PDF parser
(scripts/extract_manual_facts.py), so a label and its value are paired by the row they sit on.

Only generations classified US by scripts/classify_mcum.py are used. Values apply to the
generation's year range on the site; build_manual_facts.py lets a year-specific manual win
over them when they disagree (Appendix E.6).

Output: data_work/<make>/extracted/mcum-<model>-<body>-<years>.json (same format as the PDF
extractions; "pages" are the crawled sections in manifest order).

  .venv/Scripts/python.exe scripts/extract_mcum_facts.py
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import html as htmlmod
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_manual_facts import (  # noqa: E402
    EXTRACTOR,
    PageState,
    engine_codes,
    extract_page,
    group_rows,
    merge_values,
    norm,
    render,
    split_columns,
)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import LINES, MAKES  # noqa: E402

EM_TO_PT = 12.0  # the row/column thresholds of the PDF parser are in points
CHAR_EM = 0.5
# a block may carry more style after its position ("z-index:973;"): its text belongs to the page too
BLOCK = re.compile(r'<div class="stl_01" style="left:([\d.]+)em;top:([\d.]+)em;[^"]*">(.*?)</div>', re.S)
PRIORITY = re.compile(r"specification|lubric|capacit|maintenance-data|fuel|fluid|engine-oil|oil", re.I)


PAGE_SPLIT = re.compile(r'<div class="stl_03">')


def pages_of(raw_html: str) -> list[tuple[list[dict], str]]:
    """One section holds several manual pages, each in its own container whose blocks
    restart at the top; they are parsed one page at a time."""
    parts = PAGE_SPLIT.split(raw_html)
    return [words_of(part) for part in (parts[1:] if len(parts) > 1 else parts)]


def words_of(raw_html: str) -> tuple[list[dict], str]:
    words, chunks = [], []
    for left, top, inner in BLOCK.findall(raw_html):
        text = norm(htmlmod.unescape(re.sub(r"<[^>]+>", "", inner)))
        if not text:
            continue
        x0, y0 = float(left) * EM_TO_PT, float(top) * EM_TO_PT
        words.append({"text": text, "x0": x0, "x1": x0 + len(text) * CHAR_EM * EM_TO_PT,
                      "top": y0, "bottom": y0 + EM_TO_PT})
        chunks.append(text)
    return words, " ".join(chunks)


# ---- owner's amendment (VW/Audi/BMW, 2026-10-03): fields the US editions print besides the
# oil table, kept as their own fields and never taken for an approval or an oil capacity
SERVICE_PASS = "service-1"
OIL_STD = re.compile(r"VW (?:standard )?\d{3}\s?\d{2}|ACEA [A-C]\d(?:/[A-C]\d)?|API S[A-Z](?: or (?:superior|higher)(?: oil rating)?)?"
                     r"|ILSAC GF-\d[AB]?|BMW Longlife-\d{2}(?: FE)?|\bLL-\d{2}(?: FE)?|dexos\s?\d", re.I)
# the emergency top-up paragraph: "not available … in an emergency / can be added / may be
# added" near "oil", then within the paragraph the amount (litres) and the standards
TOPUP_TRIGGER = re.compile(r"(?:If|When)\s[^.]{0,160}?oil[^.]{0,220}?(?:not available|unavailable)"
                           r"|If no (?:engine )?oil[^.]{0,120}?is available", re.I)
TOPUP_AMOUNT = re.compile(r"(?:up to|no more than|a maximum of|max(?:imum)?\.?)\s*(?:(?P<q>\d+(?:[.,]\d+)?)\s*(?:US )?(?:quarts?|qt)\.?\s*\(\s*)?"
                          r"(?P<amt>\d+(?:[.,]\d+)?)\s*(?P<unit>US quart/liter|liters?|litres?|l)\b", re.I)
TOPUP_END = re.compile(r"All viscosity|Changing the engine oil|Engine oil change:|Please add max|Oil level sensor|Checking the engine oil", re.I)
SENTENCE = r"(?:[^.]|\.(?=\d))"  # a sentence: a full stop inside a number ("0.5") does not end it
CONSUMPTION = re.compile(SENTENCE + r"{0,200}?(?:oil consumption|consume[sd]? (?:engine )?oil|considered normal)" + SENTENCE + r"{0,200}\.", re.I)
METRIC_RATE = re.compile(r"(?P<a>\d+(?:[.,]\d+)?)\s*(?:l|liters?|litres?)\b(?:\s*\([^)]*\))?\s*(?:per|/)\s*(?P<d>\d[\d,]*)\s*(?:km|kilometers|kilometres)\b", re.I)
FUEL_TANK = re.compile(r"(?:The fuel tank has the following volume|Fuel tank(?: capacity)?)\s*:?\s*(?P<approx>approx\.?\s*)?(?P<l>\d+(?:[.,]\d+)?)\s*(?:l|liters?)\s*\((?P<gal>\d+(?:\.\d+)?)\s*(?:gal|gallons|US gal)\.?\)"
                       r"(?P<more>(?:\s*(?:approx\.?\s*)?\d+(?:[.,]\d+)?\s*(?:l|liters?)\s*\(\d+(?:\.\d+)?\s*(?:gal|gallons)\)\s*for [^.]{0,60}?vehicles)*)", re.I)
FUEL_TANK_MORE = re.compile(r"(?P<approx>approx\.?\s*)?(?P<l>\d+(?:[.,]\d+)?)\s*(?:l|liters?)\s*\((?P<gal>\d+(?:\.\d+)?)\s*(?:gal|gallons)\)\s*for (?P<who>[^.]{0,60}?vehicles)", re.I)
OIL_LABEL = re.compile(r"There is a label on the lock carrier[^.]{0,120}?that shows which engine oil should be added"
                       r"|There is a label[^.]{0,120}engine compartment[^.]{0,80}engine oil[^.]{0,60}"
                       r"|Sticker for engine oil specifications"
                       r"|engine oil (?:specification|standard)s?[^.]{0,40}(?:label|sticker)[^.]{0,80}engine compartment", re.I)


def litres_of(amount: str, unit: str) -> float | None:
    """Litres as printed; BMW prints "1 US quart/liter" as one figure."""
    if re.match(r"l|liter|litre|US quart/liter", unit, re.I):
        return float(amount.replace(",", "."))
    return None


def standards_in(text: str) -> list[str]:
    out = []
    for std in OIL_STD.findall(text):
        std = " ".join(std.split())
        if std.lower() not in [x.lower() for x in out]:
            out.append(std)
    return out


def service_facts(number: int, text: str, next_text: str = "") -> tuple[list[dict], list[dict]]:
    """(facts, notes) of one page: emergency top-up amount and standards, oil consumption norm,
    fuel tank capacities (Tank capacities section), and the statement that the oil
    specification is on a label in the engine compartment (a note, not a value)."""
    facts, notes = [], []
    flat = " ".join(text.split())
    following = " ".join(next_text.split())
    for trig in TOPUP_TRIGGER.finditer(flat):
        window = flat[trig.start(): trig.start() + 520]
        cut = TOPUP_END.search(window, len(trig.group(0)))
        window = window[: cut.start()] if cut else window
        amount = TOPUP_AMOUNT.search(window)
        if not amount:
            continue
        common = {"row": "emergency top-up", "engine_text": None, "source_layout": "mcum_service"}
        litres = litres_of(amount.group("amt"), amount.group("unit"))
        if litres is not None:
            facts.append({"key": "engine_oil_topup_limit_l", "value": litres, "unit": "L", "page": number,
                          "quote": window[: amount.end()].strip(), "label": "emergency top-up limit",
                          "original": amount.group(0), **common})
        standards = standards_in(window[amount.end():])
        if standards:
            last = list(OIL_STD.finditer(window[amount.end():]))[-1]
            facts.append({"key": "engine_oil_topup_standards", "value": "; ".join(standards), "unit": None, "page": number,
                          "quote": window[: amount.end() + last.end()].strip(), "label": "emergency top-up standards",
                          "note": "for topping up when the prescribed oil is not available", **common})
        elif following and len(flat) - trig.start() < 520:
            # the list continues on the next manual page
            head = following[:320]
            cut = TOPUP_END.search(head)
            head = head[: cut.start()] if cut else head
            standards = standards_in(head)
            if standards:
                last = list(OIL_STD.finditer(head))[-1]
                facts.append({"key": "engine_oil_topup_standards", "value": "; ".join(standards), "unit": None, "page": number + 1,
                              "quote": head[: last.end()].strip(), "label": "emergency top-up standards",
                              "note": "for topping up when the prescribed oil is not available (list continued from the previous page)",
                              **common})
    for m in CONSUMPTION.finditer(flat):
        rate = METRIC_RATE.search(m.group(0))
        if not rate:
            continue
        amount, distance = float(rate.group("a").replace(",", ".")), int(rate.group("d").replace(",", ""))
        if not distance:
            continue
        rs = re.search(r"\bIn (RS|M|AMG) models\b", m.group(0))
        facts.append({"key": "engine_oil_consumption_max_l_per_1000km", "value": round(amount * 1000 / distance, 3), "unit": "L/1000 km",
                      "page": number, "quote": m.group(0).strip(), "row": "engine oil consumption", "label": "oil consumption norm",
                      "engine_text": None, "source_layout": "mcum_service", "original": rate.group(0),
                      **({"variant": f"{rs.group(1)} models"} if rs else {})})
    for m in FUEL_TANK.finditer(flat):
        approx = bool(m.group("approx"))
        facts.append({"key": "fuel_tank_l", "value": float(m.group("l").replace(",", ".")), "unit": "L", "page": number,
                      "quote": m.group(0).strip(), "row": "tank capacities", "label": "fuel tank", "engine_text": None,
                      "source_layout": "mcum_service", "approx_in_source": approx, "original": f"{m.group('l')} l ({m.group('gal')} gal)"})
        for more in FUEL_TANK_MORE.finditer(m.group("more") or ""):
            who = " ".join(more.group("who").split())
            facts.append({"key": "fuel_tank_l", "value": float(more.group("l").replace(",", ".")), "unit": "L", "page": number,
                          "quote": m.group(0).strip(), "row": "tank capacities", "label": "fuel tank", "engine_text": None,
                          "source_layout": "mcum_service", "approx_in_source": bool(more.group("approx")),
                          "variant": who, **({"drive": "AWD"} if re.search(r"all-wheel|4MOTION|quattro", who, re.I) else {}),
                          "original": f"{more.group('l')} l ({more.group('gal')} gal) for {who}"})
    for m in OIL_LABEL.finditer(flat):
        notes.append({"page": number, "quote": m.group(0).strip(),
                      "fields": ["engine_oil_oem_approval", "engine_oil_capacity_l"],
                      "reason": "не публикуется производителем в руководстве: руководство ссылается на наклейку в моторном отсеке"})
    return facts, notes


def squeezed(text: str) -> tuple[str, list[int]]:
    """The text without whitespace, lower case, and for each kept character its position in the
    original (to quote the original OCR text)."""
    chars, pos = [], []
    for i, ch in enumerate(text):
        if not ch.isspace():
            chars.append(ch.lower())
            pos.append(i)
    return "".join(chars), pos


# "If the recommended engine oil is not available" / "If engine oil that meets the recommended
# specification is not available"; OCR may print full-width brackets
OCR_TOPUP_CONDITION = (r"(?:(?:recommended|specified|prescribed)engineoil(?:that\w+)?"
                   r"|engineoilthatmeetsthe(?:recommended|specified|prescribed)speci-?fication)isnotavailable")
OCR_TOPUP_AMOUNT = (r"maximumof(?:(?P<q>\d+(?:[.,]\d+)?)(?:us)?quarts?)?[(（]?(?P<l>\d+(?:[.,]\d+)?)liters?[)）]?"
                r"(?:of|ofan)?(?P<list>.{0,60}?)engineoil")
OCR_TOPUP = re.compile(OCR_TOPUP_CONDITION + r".{0,80}?" + OCR_TOPUP_AMOUNT)
OCR_TOPUP_TRIGGER = re.compile(OCR_TOPUP_CONDITION + r",?inanemergency(?:you)?(?:may)?\d{0,4}$")
OCR_TOPUP_TAIL = re.compile(r"^(?:checkingandfilling)?(?:you)?(?P<tail>mayadda" + OCR_TOPUP_AMOUNT + ")")  # a page header may come first
OCR_CONSUMPTION = re.compile(r"oilconsumptionmaybeupto(?P<q>\d+(?:[.,]\d+)?)quarts?/(?P<mi>[\d,]+)miles\((?P<a>\d+(?:[.,]\d+)?)liters?/(?P<d>[\d,]+)km\)")
OCR_LABEL = re.compile(r"useanoilthatislistedonthesticker|engineoilcapacitiesfortheusa")
OCR_STD = [(re.compile(r"acea([a-c]\d)"), "ACEA {}"), (re.compile(r"api(s[a-z])"), "API {}"), (re.compile(r"ilsacgf-?(\d[ab]?)"), "ILSAC GF-{}"),
           (re.compile(r"vw(?:standard)?(\d{3})(\d{2})"), "VW {} {}")]


def ocr_service_facts(number: int, text: str, next_text: str = "") -> tuple[list[dict], list[dict]]:
    """The service-pass fields on OCR text: rules on the text without spaces, quotes cut from
    the original OCR text."""
    facts, notes = [], []
    sq, pos = squeezed(text)

    def quote(m) -> str:
        return text[pos[m.start()]: pos[m.end() - 1] + 1]

    common = {"engine_text": None, "source_layout": "mcum_service_ocr"}
    found = [(m, number, quote(m)) for m in OCR_TOPUP.finditer(sq)]
    if not found and next_text and OCR_TOPUP_TRIGGER.search(sq[-160:]):
        # the sentence runs over the page break ("... is not available, in an emergency you" | "may add
        # a maximum of 1 quart (1 liter) of ACEA C3 or API SN engine oil one time ..."): the amount and
        # the standards are cited on the next page, where they are printed
        nsq, npos = squeezed(next_text)
        m = OCR_TOPUP_TAIL.search(nsq[:400])
        if m:
            found.append((m, number + 1, next_text[npos[m.start("tail")]: npos[m.end() - 1] + 1]))
    for m, page, cited in found:
        facts.append({"key": "engine_oil_topup_limit_l", "value": float(m.group("l").replace(",", ".")), "unit": "L", "page": page,
                      "quote": cited, "row": "emergency top-up", "label": "emergency top-up limit", **common})
        standards = []
        for pattern, form in OCR_STD:
            for g in pattern.finditer(m.group("list")):
                value = form.format(*[x.upper() for x in g.groups()])
                if value not in standards:
                    standards.append(value)
        if standards:
            facts.append({"key": "engine_oil_topup_standards", "value": "; ".join(standards), "unit": None, "page": page,
                          "quote": cited, "row": "emergency top-up", "label": "emergency top-up standards",
                          "note": "for topping up when the prescribed oil is not available", **common})
    for m in OCR_CONSUMPTION.finditer(sq):
        amount, distance = float(m.group("a").replace(",", ".")), int(m.group("d").replace(",", ""))
        if distance:
            facts.append({"key": "engine_oil_consumption_max_l_per_1000km", "value": round(amount * 1000 / distance, 3), "unit": "L/1000 km",
                          "page": number, "quote": quote(m), "row": "engine oil consumption", "label": "oil consumption norm", **common})
    for m in OCR_LABEL.finditer(sq):
        notes.append({"page": number, "quote": quote(m), "fields": ["engine_oil_oem_approval", "engine_oil_capacity_l"],
                      "reason": "не публикуется производителем в руководстве: руководство ссылается на наклейку в моторном отсеке "
                                "и на сайт производителя"})
    return facts, notes


def rows_of_words(words: list[dict]) -> list[list[dict]]:
    width = max((w["x1"] for w in words), default=600.0)
    return [merge_values([render(r) for r in group_rows(col)]) for col in split_columns(width, words) if col]


def main() -> int:
    markets = json.loads((WORK / "_mcum" / "edition_markets.json").read_text(encoding="utf-8"))
    with (WORK / "_mcum" / "manifest.csv").open(encoding="utf-8", newline="") as handle:
        manifest = [r for r in csv.DictReader(handle) if r["http_status"] == "200" and r["body"]]
    by_gen = defaultdict(list)
    for row in manifest:
        by_gen[(row["make"], row["model"], row["body"], row["years"])].append(row)
    slug_to_make = {v["mcum"]: k for k, v in MAKES.items() if v.get("mcum")}
    only = set(sys.argv[1:])  # our make slugs to extract (default: every make)
    written = set()
    for (site_make, model, body, years), rows in sorted(by_gen.items()):
        if only and slug_to_make.get(site_make) not in only:
            continue
        info = markets.get(f"{site_make}/{model}/{body}/{years}", {})
        if info.get("market") != "US":
            continue
        make = slug_to_make.get(site_make)
        lines = [ln.key for ln in LINES if ln.make == make and model in ln.mcum]
        if not make or not lines:
            continue
        first, last = (int(x) for x in (years.split("-") + [years])[:2])
        folder = RAW_ROOT / "_mcum" / site_make / model / f"{body}_{years}"
        pages, sections, urls, digests = [], [], [], []
        ocr_pages = set()
        result_facts, review, notes = [], [], []
        state = PageState()
        for row in sorted(rows, key=lambda r: r["section"]):
            name = row["section"] or "_index"
            path = folder / f"{name}.html.gz"
            if not path.exists():
                path = folder / f"{name}.html"
            if not path.exists():
                continue
            raw = gzip.decompress(path.read_bytes()).decode("utf-8") if path.suffix == ".gz" else path.read_text(encoding="utf-8")
            digests.append(row["sha256"])
            parsed = pages_of(raw)
            ocr_path = folder / f"{name}.ocr.json"
            if ocr_path.exists() and sum(len(t) for _, t in parsed) < 200:
                # manual pages delivered as images: the OCR text (scripts/ocr_mcum_images.py) is the page
                for ocr_page in json.loads(ocr_path.read_text(encoding="utf-8"))["pages"]:
                    pages.append(ocr_page["text"])
                    sections.append(name)
                    urls.append(row["url"])
                    ocr_pages.add(len(pages))
                continue
            for words, text in parsed:
                pages.append(text)
                sections.append(name)
                urls.append(row["url"])
                if not PRIORITY.search(name) or not words:
                    continue
                facts, rev = extract_page(len(pages), rows_of_words(words), text, state)
                for fact in facts:
                    fact["section_url"] = row["url"]
                result_facts += facts
                review += rev
        for i, text in enumerate(pages):
            # pages of one section run on: the next page holds the rest of a paragraph
            following = pages[i + 1] if i + 1 < len(pages) and sections[i + 1] == sections[i] else ""
            extra, page_notes = (ocr_service_facts if i + 1 in ocr_pages else service_facts)(i + 1, text, following)
            for fact in extra:
                fact["section_url"] = urls[fact["page"] - 1]
            result_facts += extra
            notes += page_notes
        key = f"mcum-{model}-{body}-{years}"
        sha = hashlib.sha256("".join(digests).encode()).hexdigest()
        store = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
        with gzip.open(store, "wt", encoding="utf-8") as handle:  # page texts for quote checks
            json.dump({"sha256": sha, "file": f"_mcum/{site_make}/{model}/{body}_{years}", "pages": pages,
                       "sections": sections, "urls": urls}, handle)
        doc = {
            "key": key, "make": make, "lines": lines,
            "years": [y for y in range(first, last + 1) if 2014 <= y <= 2026],
            "doc_type": "owners_manual", "title": f"{site_make} {model} {body} {years} owner's manual (mycarusermanual.com copy)",
            "path": str(folder), "url": urls[0] if urls else "", "page_url": "", "sha256": sha,
            "retrieved_at": rows[0]["retrieved_at"], "tier": "B", "source_type": "OWNER_MANUAL_COPY",
            "publisher": "factory owner's manual, copy hosted by mycarusermanual.com",
            "authenticity": "REVIEWED_MIRROR", "generation_range": True,
        }
        # a top-up or consumption amount read by the table pass as an oil capacity ("0.5 l (0.5 qt)")
        # is not a capacity: the service pass holds it under its own field
        service_quotes = [f["quote"] for f in result_facts if f.get("source_layout") == "mcum_service"]
        result_facts = [f for f in result_facts if not (
            f["key"].startswith("engine_oil_capacity") and f.get("source_layout") != "mcum_service"
            and any(norm(f["quote"]) in norm(q) for q in service_quotes))]
        if any(f["key"].startswith("engine_oil_capacity") and f.get("source_layout") != "mcum_service"
               and isinstance(f["value"], (int, float)) and f["value"] >= 3 for f in result_facts):
            notes = [n for n in notes if "engine_oil_capacity_l" not in n["fields"]] + [
                {**n, "fields": [x for x in n["fields"] if x != "engine_oil_capacity_l"]} for n in notes if len(n["fields"]) > 1]
        out = {"doc": doc, "extractor": EXTRACTOR + "+mcum+" + SERVICE_PASS, "pages": len(pages), "edition_market": "US",
               "edition_markers": info.get("markers"), "facts": result_facts, "review": review,
               "not_in_manual": notes, "engine_codes": engine_codes(pages), "status": "ok"}
        target = WORK / make / "extracted" / f"{key}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        written.add(target.resolve())
        print(key, lines, doc["years"], len(result_facts), "facts", len(review), "review", flush=True)
    # an edition no longer classified US (re-classified on the full crawl) leaves no document behind
    for make in (only or {m for m in MAKES}):
        for stale in (WORK / make / "extracted").glob("mcum-*.json"):
            if stale.resolve() not in written:
                print("removed (edition no longer US):", stale.name, flush=True)
                stale.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
