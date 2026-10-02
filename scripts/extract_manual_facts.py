"""Extract fluids and capacities from owner's-manual PDFs with one generic, geometry-based parser.

For every cached manual PDF (RAW_ROOT/pagetext + the PDF itself):
  1. edition check: US markers (U.S.A./United States, miles, quarts/gallons) vs others;
  2. candidate pages: specification / capacity pages found in the cached text;
  3. visual rows rebuilt from word positions (pdfplumber), so a table label and its value
     are paired by the row they sit on, not by text order (text order pairs Toyota's
     "With filter" with the wrong number);
  4. rules per field; a value is kept only when it is unambiguous on its row:
       engine_oil_capacity_l / _without_filter_l, coolant_capacity_l,
       transmission_fluid_capacity_l, fuel_tank_l, octane_aki, octane_ron,
       engine_oil_viscosity, engine_oil_specification, engine_oil_oem_approval,
       coolant, transmission_fluid, brake_fluid;
     everything else (several engines without a label, values that do not convert,
     missing units) goes to a review list instead of the database.
Every value keeps: page, the verbatim quote (a substring of the page text), the rebuilt row,
the label and the engine text found on the row.

Output per document: data_work/<make>/extracted/<doc-key>.json (no manual text beyond the
quoted rows), plus data_work/<make>/extracted/_review.json.

  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/extract_manual_facts.py <make> [--limit N]
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY, LINES, carmans_line  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.tech_units import convert  # noqa: E402

EXTRACTOR = "manual-geometry-6"
NORMALIZE = ((chr(0xF0B4), chr(0x00D7)), (chr(0xF0B0), chr(0x00B0)), (chr(0x00A0), " "),
             (chr(0x2019), "'"), (chr(0x201C), '"'), (chr(0x201D), '"'), (chr(0x00AD), ""))


def norm(text: str) -> str:
    for old, new in NORMALIZE:
        text = text.replace(old, new)
    return " ".join(text.split())


# ---- documents -----------------------------------------------------------------------------
def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def documents(make: str) -> list[dict]:
    """Every downloaded manual-type PDF of the make with its line(s), year(s) and provenance."""
    docs = []
    for row in read_csv(WORK / "_shared" / "manifest_carmans.csv"):
        if row["kind"] != "pdf" or row["status"] != "ok" or row["make"] != make:
            continue
        docs.append({
            "key": f"carmans-{row['post']}",
            "make": make,
            "lines": [row["line"]],
            "years": [int(row["year"])],
            "doc_type": "owners_manual",
            "path": RAW_ROOT / row["path"],
            "url": row["url"],
            "page_url": row["page_url"],
            "sha256": row["sha256"],
            "retrieved_at": row["retrieved_at"],
            "tier": "B",
            "source_type": "OWNER_MANUAL_COPY",
            "publisher": "factory owner's manual, copy hosted by carmans.net",
            "authenticity": "REVIEWED_MIRROR",
        })
    for path in sorted((WORK / "_shared" / "manifest_official").glob("*.csv")):
        for row in read_csv(path):
            if row["make"] != make or row["status"] != "ok" or not row["path"].endswith(".pdf"):
                continue
            lines = [ln if "/" in ln else f"{make}/{ln}" for ln in row["lines"].split(";") if ln]
            docs.append({
                "key": "official-" + hashlib.sha1(row["url"].encode()).hexdigest()[:12],
                "make": make,
                "lines": [ln for ln in lines if ln in BY_KEY],
                "years": [int(y) for y in row["years"].split(";") if y],
                "doc_type": row["doc_type"],
                "title": row["title"],
                "path": RAW_ROOT / row["path"],
                "url": row["url"],
                "page_url": "",
                "sha256": row["sha256"],
                "retrieved_at": row["retrieved_at"],
                "tier": "A",
                "source_type": "OWNER_MANUAL_OFFICIAL" if row["doc_type"] == "owners_manual" else "MAINTENANCE_GUIDE_OFFICIAL",
                "publisher": f"{make} (manufacturer domain {path.stem})",
                "authenticity": "OFFICIAL_PUBLISHER",
            })
    return docs


def page_cache(sha: str) -> dict | None:
    path = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def edition_market(pages: list[str], official_us: bool = False) -> tuple[str, dict]:
    text = "\n".join(pages)
    marks = {
        "usa": len(re.findall(r"U\.S\.A\.|United States|\bU\.S\.", text)),
        "quarts": len(re.findall(r"\bqt\b|\bqts?\.|quarts?\b", text, re.I)),
        "gallons": len(re.findall(r"\bgal\b|\bgal\.|gallons?\b", text, re.I)),
        "mph": len(re.findall(r"\bmph\b", text, re.I)),
        "canada_only": len(re.findall(r"Canada only|Canadian owners", text, re.I)),
        "acea_only": int(bool(re.search(r"\bACEA\b", text)) and not re.search(r"\bAPI\b|ILSAC|dexos", text)),
        "middle_east": len(re.findall(r"Middle East|\bGCC\b|Gulf Cooperation", text)),
    }
    # US manuals mention other regions in passing (Ford: "if you are traveling in the Middle
    # East"); the market follows the dominant units and US references.
    us = marks["usa"] >= 3 and (marks["quarts"] + marks["gallons"]) >= 2 and marks["mph"] >= 3
    if us and not marks["acea_only"]:
        return "US", marks
    # documents from the manufacturer's US site (warranty and maintenance booklets carry no
    # units) are US editions unless they say otherwise
    if official_us and marks["usa"] >= 1 and not marks["acea_only"] and marks["middle_east"] < 10:
        return "US", marks
    if marks["middle_east"] >= 10 and marks["mph"] < 3:
        return "GCC", marks
    if marks["acea_only"]:
        return "EU", marks
    return "UNKNOWN", marks


# ---- geometry ------------------------------------------------------------------------------
VALUE_ONLY = re.compile(
    r"^[\s|()\[\],.*±~/\d-]*(?:(?:US|Imp\.?|qt\.?|qts|quarts?|gal\.?|gallons?|L|l|liters?|litres?|cc|kg|lbs?|psi|kPa|kgf/cm2|in\.?|mm)[\s|()\[\],.*±~/\d-]*)+$",
    re.I,
)


def gutter(page_width: float, words: list[dict], lo=0.30, hi=0.70) -> float | None:
    if len(words) < 30:
        return None
    left_edge = min(w["x0"] for w in words)
    right_edge = max(w["x1"] for w in words)
    span = right_edge - left_edge
    best = None
    for step in range(int(left_edge + span * lo), int(left_edge + span * hi), 2):
        if any(w["x0"] < step < w["x1"] for w in words):
            continue
        left = sum(1 for w in words if w["x1"] <= step)
        score = min(left, len(words) - left)
        if score >= 12 and (best is None or score > best[1]):
            best = (step, score)
    return best[0] if best else None


def group_rows(words) -> list[dict]:
    """Words whose top edges are within 2.5 pt form one visual row (stacked lines of a
    multi-line table cell stay apart)."""
    rows: list[dict] = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        for r in rows:
            if abs(r["top"] - w["top"]) <= 2.5:
                r["words"].append(w)
                r["bottom"] = max(r["bottom"], w["bottom"])
                break
        else:
            rows.append({"top": w["top"], "bottom": w["bottom"], "words": [w]})
    return sorted(rows, key=lambda r: r["top"])


def render(row) -> dict:
    ws = sorted(row["words"], key=lambda w: w["x0"])
    parts, prev = [], None
    for w in ws:
        if prev is not None and w["x0"] - prev["x1"] > 12:
            parts.append("|")
        parts.append(w["text"])
        prev = w
    return {"top": row["top"], "bottom": row["bottom"], "text": norm(" ".join(parts)),
            "plain": norm(" ".join(w["text"] for w in ws)), "words": row["words"]}


def value_only(row) -> bool:
    return bool(VALUE_ONLY.match(row["plain"])) and bool(re.search(r"\d", row["plain"]))


def merge_values(rows: list[dict]) -> list[dict]:
    """A row holding only a value joins the nearest label row within 9 pt above or below
    (labels and values of one table row are often printed at slightly different heights)."""
    out = [dict(r) for r in rows]
    used = set()
    for i, r in enumerate(out):
        if i in used or not value_only(r):
            continue
        candidates = []
        for j in (i - 1, i + 1):
            if 0 <= j < len(out) and j not in used and not value_only(out[j]) and not volume(out[j]["plain"]):
                gap = abs(out[j]["top"] - r["top"])
                if gap <= 9:
                    candidates.append((gap, j))
        if candidates:
            _, j = min(candidates)
            out[j] = {**out[j], "text": norm(out[j]["text"] + " | " + r["text"]),
                      "plain": norm(out[j]["plain"] + " " + r["plain"])}
            used.add(i)
    return [r for i, r in enumerate(out) if i not in used]


def split_columns(page_width: float, words: list[dict], depth: int = 0) -> list[list[dict]]:
    """Recursive gutter split (two-column pages, side-by-side tables); a value-only row of
    the right part at the same height as a label row of the left part is a table that spans
    the gutter and is joined back."""
    x = gutter(page_width, words) if depth < 2 else None
    if x is None:
        return [words]
    left = [w for w in words if w["x1"] <= x]
    right = [w for w in words if w["x0"] >= x]
    left_rows, right_rows = group_rows(left), group_rows(right)
    joined = set()
    for rr in right_rows:
        rr_view = render(rr)
        if not value_only(rr_view):
            continue
        for lr in left_rows:
            if abs(lr["top"] - rr["top"]) <= 3 and not volume(render(lr)["plain"]):
                lr["words"] = lr["words"] + rr["words"]
                joined.add(id(rr))
                break
    left_words = [w for r in left_rows for w in r["words"]]
    right_words = [w for r in right_rows if id(r) not in joined for w in r["words"]]
    return split_columns(page_width, left_words, depth + 1) + (
        split_columns(page_width, right_words, depth + 1) if right_words else []
    )


def rows_of(page) -> list[list[dict]]:
    words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False)
    columns = split_columns(float(page.width), words)
    return [merge_values([render(r) for r in group_rows(col)]) for col in columns if col]


# ---- quantities ------------------------------------------------------------------------------
NUM = r"(\d+(?:\.\d+)?|\d+-\d/\d|\d+\s\d/\d)"
QT = NUM + r"\s?(?:US\s)?(?:qt|qts|quarts?)\b\.?"
# litres need a space ("4.2 L", "(56 L)") and must not be followed by an engine word, so that
# a displacement ("1.5L L4", "2.5 L 4-cylinder") is never read as a volume
LITRE = r"(\d+(?:\.\d+)?)(?:\s(?:L|l|liters?|litres?|Liters?)\b|\s?\u2113)(?!\s?(?:L4|I4|V6|V8|4-cyl|\d-cyl|engine|Engine|DOHC|turbo|Turbo|EcoBoost|GDI|T-GDI|MPI|per\b|/))"
CC = r"(\d+(?:\.\d+)?)\s?cc\b"
GAL = r"(\d+(?:\.\d+)?)\s?(?:US\s)?(?:gal|gallons?)\b\.?"
APPROX = re.compile(r"\b(approx\w*|about|around|approximately)\b|\bca\.", re.I)


def fraction(text: str) -> Decimal:
    found = re.fullmatch(r"(\d+)[- ](\d)/(\d)", text.strip())
    if found:
        return Decimal(found.group(1)) + Decimal(found.group(2)) / Decimal(found.group(3))
    return Decimal(text)


def volume(text: str) -> dict | None:
    """Litres from a row: the stated litre figure, checked against the quart/gallon figure."""
    litre = re.search(LITRE, text)
    qt = re.search(QT, text, re.I)
    gal = re.search(GAL, text, re.I)
    if not litre and not qt and not gal:
        return None
    if len(re.findall(LITRE, text)) > 1 or len(re.findall(QT, text, re.I)) > 1 or len(re.findall(GAL, text, re.I)) > 1:
        return {"error": "several volumes on one row"}
    value = None
    try:
        if litre:
            value = Decimal(litre.group(1))
        if qt:
            from_qt = convert(fraction(qt.group(1)), "qt", "L")
            if value is None:
                value = from_qt
            elif abs(from_qt - value) > Decimal("0.15") + value * Decimal("0.03"):
                return {"error": f"quart and litre figures disagree ({qt.group(0)} vs {litre.group(0)})"}
        elif gal:
            from_gal = convert(Decimal(gal.group(1)), "gal", "L")
            if value is None:
                value = from_gal
            elif abs(from_gal - value) > Decimal("0.6") + value * Decimal("0.03"):
                return {"error": f"gallon and litre figures disagree ({gal.group(0)} vs {litre.group(0)})"}
    except (InvalidOperation, ValueError, ArithmeticError):
        return {"error": "unreadable number"}
    spans = [m for m in (qt, litre, gal) if m]
    start, end = min(m.start() for m in spans), max(m.end() for m in spans)
    if end < len(text) and text[end] == ")":
        end += 1
    if start > 0 and text[start - 1] == "(":
        start -= 1
    return {"litres": float(value.quantize(Decimal("0.1"))), "original": text[start:end],
            "approx": bool(APPROX.search(text))}


ENGINE_LABEL = re.compile(
    r"\b\d\.\d\s?L?\s?(?:T-?GDI|GDI|MPI|TFSI|TSI|EcoBoost\S*|V6|V8|L4|I4|I-4|4-cyl\w*|6-cyl\w*|Turbo\w*|turbo\w*|Hybrid|HEV|PHEV|Supercharged)\b"
    r"(?:\s?(?:T-?GDI|GDI|V6|L4|Turbo|turbo|engines?|Engines?|\([A-Z0-9]{3,6}\)))*"
    r"|\b\d\.\dL\b(?:\s?(?:engines?|Engines?|\([A-Z0-9]{3,6}\)))?"
    r"|\b\d\.\d\s?L?\s(?:engines?|Engines?)\b",
)
VOLUME_SPANS = re.compile(
    r"\(?\d+(?:\.\d+)?(?:-\d/\d)?\s?(?:US\s)?(?:qt|qts|quarts?|gal|gallons?|liters?|litres?|Imp\.?\s?(?:qt|gal)|cc)\b\.?[,)]?"
    r"|\(?\d+(?:\.\d+)?\s(?:L|l)\b[,)]?|\(?\d+(?:\.\d+)?\s?\u2113[,)]?",
    re.I,
)


def engine_text(text: str) -> str | None:
    """Engine named on a row or heading; volumes are removed first so that "4.2 L," never
    passes for a displacement."""
    found = ENGINE_LABEL.search(VOLUME_SPANS.sub(" ", text))
    return norm(found.group(0)) if found else None


# ---- rules ------------------------------------------------------------------------------------
LABELS = [  # (key, pattern) tried in order on a row; the first match names the row's item
    ("engine_oil_capacity_without_filter_l", re.compile(r"without (?:oil )?filter|excluding (?:oil )?filter|without oil filter change", re.I)),
    ("engine_oil_capacity_l", re.compile(r"(?:engine )?oil (?:capacity )?(?:\(?with|including|incl\.?) (?:oil )?filter|^\W*with (?:oil )?filter|including (?:oil )?filter|with oil filter change|oil and filter change", re.I)),
    ("engine_oil_capacity_drain_refill_l", re.compile(r"^\W*engine oil\b|^\W*oil capacity\b|^\W*motor oil\b", re.I)),
    ("coolant_capacity_l", re.compile(r"^\W*(?:engine )?coolant\b|cooling system|^\W*antifreeze", re.I)),
    ("transmission_fluid_capacity_l", re.compile(r"automatic transmission|automatic transaxle|transaxle fluid|\bCVT\b|continuously variable|transmission fluid|^\W*ATF\b", re.I)),
    ("fuel_tank_l", re.compile(r"fuel tank|fuel capacity|^\W*fuel\b", re.I)),
]
IN_ROW = {  # fluid named anywhere on a value row
    "coolant_capacity_l": re.compile(r"\bcoolant\b|antifreeze", re.I),
    "transmission_fluid_capacity_l": re.compile(r"transmission fluid|transaxle fluid|\bATF\b|\bCVT fluid", re.I),
    "fuel_tank_l": re.compile(r"fuel tank|gasoline|unleaded", re.I),
}
SKIP_ROW = re.compile(
    r"manual transmission|\bMTF\b|differential|transfer case|power steering|washer|refrigerant|brake fluid|clutch fluid"
    r"|\blow\b.{0,30}\bfull\b|\bfull\b.{0,30}\blow\b|dipstick|reserve tank|reservoir|add(?:ing)? oil|to add",
    re.I,
)
SECTION_ENGINE = re.compile(r"capacit|specification|engine oil|lubrication|^\W*\d\.\d\s?L", re.I)
STANDARDS = re.compile(
    r"API\s?(?:Service\s)?(?:S[A-Z])(?:\s?PLUS)?(?:\s?(?:/|or)\s?S[A-Z](?:\s?PLUS)?)*(?:\s?RC|\s?\"?Resource[- ]Conserving\"?)?(?:\s?or above)?"
    r"|ILSAC\s?GF-?\d[A-B]?(?:\s?or above)?|ACEA[- ]?[A-C]\d(?:/[A-C]\d)*(?:\s?or above)?|API Premium-grade"
)
OEM_APPROVALS = re.compile(
    r"dexos\s?\d\w*|MB[- ]?(?:Freigabe|Approval|Sheet)?\s?229\.\d{1,2}|BMW\s?Longlife-?\d{2}(?:\s?FE\+?)?|\bLL-\d{2}(?:\s?FE\+?)?"
    r"|VW\s?50[2-9]\s?00|VW\s?508\s?00|WSS-M2C\d{3}-[A-Z]\d|MS-\d{4,5}|Chrysler\s?MS-\d{4,5}|STJLR\.\d{2}\.\d{4}",
    re.I,
)
def std_value(text: str) -> str:
    """One spelling of an oil standard: "API SN PLUS/ SP" = "API SN PLUS/SP"."""
    return re.sub(r"\s*/\s*", "/", norm(text))


RECOMMEND = re.compile(r"\b(use|must|meets?|meeting|grade:|recommend\w*|specified|approved|required|requires)\b", re.I)
ALTERNATIVE = re.compile(r"not available|unavailable|alternative|substitute|if .{0,40} cannot be", re.I)
VISCOSITY = re.compile(r"\bSAE\s?(\d{1,2}W-?\d{2})\b|\b(\d{1,2}W-\d{2})\b")
COOLANT_TYPE = re.compile(
    r"(Toyota Super Long Life Coolant|Lexus Super Long Life Coolant|Honda Long Life Antifreeze/Coolant Type 2"
    r"|Genuine NISSAN Long Life Antifreeze/Coolant(?: \(blue\))?|Genuine INFINITI Long Life Antifreeze/Coolant(?: \(blue\))?"
    r"|DEX-COOL|Motorcraft(?: Specialty)? (?:Orange|Yellow|Green|Gold)?\s?(?:Engine )?(?:Antifreeze/)?Coolant|Mopar Antifreeze/Coolant[^.,;]{0,40}"
    r"|MB[- ]?(?:Approval )?3\d{2}\.\d|G1[23](?:\s?evo|\+\+?)?\b|Hyundai Genuine Antifreeze[^.,;]{0,30}|Kia Genuine Antifreeze[^.,;]{0,30})",
    re.I,
)
COOLANT_DESCRIPTION = re.compile(r"(ethylene[- ]glycol[^.,;•()]{0,60}|phosphate[- ]based[^.,;•()]{0,40}|silicate[- ]free[^.,;•()]{0,40})", re.I)
ATF_TYPE = re.compile(
    r"(Toyota Genuine ATF\s?WS|ATF\s?WS\b|Toyota Genuine CVT Fluid FE|CVT Fluid FE|Toyota Genuine ATF\s?FE|Honda ATF DW-1|Honda (?:Genuine )?CVT Fluid HCF-2|Honda HCF-2|Honda DCT Fluid|Genuine NISSAN (?:CVT|Matic)[^.,;]{0,25}"
    r"|NS-[23]|Matic[- ]S|DEXRON[- ]?(?:VI|HP|ULV)\w*|MERCON[- ]?(?:LV|ULV|SP)\w*|SP-?IV(?:-RR|M)?\b|ATF\+4|ZF\s?Lifeguard\s?\w+|Shell ATF[^.,;]{0,20}|SK ATF SP-IV|MOPAR[^.,;]{0,40}ATF[^.,;]{0,20})",
    re.I,
)
BRAKE_FLUID = re.compile(r"\b(DOT[\s-]?[345](?:\.1)?)\b")
OCTANE_AKI = re.compile(r"(?:octane rating|\(R\+M\)/2|AKI|anti-?knock index|pump octane(?: number)?)[^0-9]{0,40}(\d{2})\b|\b(8[5-9]|9[0-4])\s?(?:octane|AKI)\b", re.I)
OCTANE_RON = re.compile(r"Research Octane Number\s?(\d{2})|\bRON\s?(\d{2})\b", re.I)


def page_candidates(pages: list[str]) -> list[int]:
    keys = re.compile(r"capacit|specification|lubricant|engine oil|fuel tank|fluid", re.I)
    units = re.compile(r"\bqt\b|\bqts?\.|quarts?|\bgal\b|\bgal\.|gallons?|\bL\b|liters?", re.I)
    hits = [i for i, t in enumerate(pages) if keys.search(t) and units.search(t)]
    # specification chapters sit in the last third; their oil-grade and fluid-type text often
    # continues on the next page without any unit, so neighbours are included
    weighted = sorted(hits, key=lambda i: (i < len(pages) * 0.5, -i))[:40]
    near = {j for i in weighted for j in (i - 1, i, i + 1, i + 2) if 0 <= j < len(pages)}
    return sorted(near)[:80]


class PageState:
    """Carried across the rows (and pages) of one document."""

    def __init__(self):
        self.section_engine = None
        self.label = None
        self.label_ttl = 0
        self.label_approx = False


def extract_page(page_number: int, columns: list[list[dict]], text: str, state: PageState):
    facts, review = [], []
    flat = norm(text)

    def emit(key, value, unit, quote, row, label, engine=None, extra=None):
        if quote and norm(quote) not in flat:
            review.append({"page": page_number, "key": key, "row": row, "reason": "quote not in page text", "quote": quote})
            return
        facts.append({"key": key, "value": value, "unit": unit, "page": page_number, "quote": norm(quote),
                      "row": row, "label": label, "engine_text": engine, **(extra or {})})

    for rows in columns:
        state.label, state.label_ttl = None, 0  # a table does not continue into another column
        context = {"coolant": 0, "transmission": 0, "brake": 0, "oil": 0}
        triggers = {"coolant": re.compile(r"coolant|cooling system|antifreeze", re.I),
                    "transmission": re.compile(r"transmission|transaxle|\bATF\b|\bCVT\b|\bDCT\b", re.I),
                    "brake": re.compile(r"\bbrake", re.I),
                    "oil": re.compile(r"engine oil|oil grade|motor oil|oil capacity|lubrication", re.I)}
        seen = set()
        for r in rows:
            t = r["plain"]
            for name, pattern in triggers.items():
                context[name] = 6 if pattern.search(t) else max(0, context[name] - 1)
            # a heading that names an engine ("Capacities and Specifications - 2.5L")
            heading_engine = engine_text(t)
            vol = volume(t)
            if heading_engine and not vol and SECTION_ENGINE.search(t) and len(t) < 90:
                state.section_engine = heading_engine
            label_key = next((k for k, pattern in LABELS if pattern.search(t)), None)
            skip = SKIP_ROW.search(t) and not re.search(r"automatic transmission|\bCVT\b|\bATF\b", t, re.I)
            if skip:
                label_key = None
            # Toyota: "With filter" / "Without filter" rows sit under an "Oil capacity" heading
            if label_key in ("engine_oil_capacity_l", "engine_oil_capacity_without_filter_l") and not (
                context["oil"] or re.search(r"oil", t, re.I) or state.label and state.label.startswith("engine_oil")
            ):
                label_key = None
            if label_key and not vol:
                state.label, state.label_ttl = label_key, 8
                state.label_approx = bool(APPROX.search(t))
            elif state.label_ttl:
                state.label_ttl -= 1
            if vol and "error" in vol:
                if label_key or state.label_ttl:
                    review.append({"page": page_number, "key": label_key or state.label, "row": t, "reason": vol["error"]})
            elif vol and not skip:
                # words on the row itself win over a label carried from a heading row
                in_row = [k for k, pattern in IN_ROW.items() if pattern.search(t)]
                if len(in_row) > 1 and not label_key:
                    review.append({"page": page_number, "row": t, "reason": f"row names several fluids {in_row}"})
                    continue
                key = label_key or (in_row[0] if in_row else None) or (state.label if state.label_ttl else None)
                if key == "engine_oil_capacity_drain_refill_l" and re.search(r"with(?:out)? (?:oil )?filter|including", t, re.I):
                    key = "engine_oil_capacity_l" if not re.search(r"without", t, re.I) else "engine_oil_capacity_without_filter_l"
                if key:
                    engine = engine_text(t) or (state.section_engine if key != "fuel_tank_l" else None)
                    drive = re.search(r"\b(AWD|FWD|RWD|4WD|2WD|4x4|4x2|All Wheel Drive|Front Wheel Drive)\b", t)
                    # a figure the manufacturer itself calls approximate/reference is kept as
                    # stated and flagged, never rounded or invented here
                    approx = vol["approx"] or state.label_approx
                    emit(key, vol["litres"], "L", vol["original"], r["text"], key, engine,
                         {"original": vol["original"], "drive": drive.group(1) if drive else None,
                          "approx_in_source": approx})
                    if key.startswith("engine_oil"):
                        for s in STANDARDS.finditer(t):
                            emit("engine_oil_specification", std_value(s.group(0)), None, s.group(0), r["text"], "oil grade", engine)
            # fluid types on rows inside their context (tables and lists)
            found = []
            if context["coolant"]:
                found += [("coolant", c.group(0)) for c in COOLANT_TYPE.finditer(t)]
                found += [("coolant_description", c.group(0)) for c in COOLANT_DESCRIPTION.finditer(t)]
            if context["transmission"]:
                found += [("transmission_fluid", a.group(0)) for a in ATF_TYPE.finditer(t)]
            if context["brake"]:
                dots = [b.group(1) for b in BRAKE_FLUID.finditer(t)]
                if dots:
                    joined = " or ".join(dict.fromkeys(norm(d) for d in dots))
                    quote = t[t.find(dots[0]): t.rfind(dots[-1]) + len(dots[-1])]
                    found.append(("brake_fluid", quote if norm(quote) in flat else dots[0]))
            for key, value in found:
                if (key, norm(value)) in seen:
                    continue
                seen.add((key, norm(value)))
                emit(key, norm(value), None, value, r["text"], key.replace("_", " "))
            for m in OCTANE_AKI.finditer(t):
                number = m.group(1) or m.group(2)
                if number and 85 <= int(number) <= 94:
                    emit("octane_aki", int(number), None, m.group(0), r["text"], "octane")
            for m in OCTANE_RON.finditer(t):
                number = m.group(1) or m.group(2)
                if number and 89 <= int(number) <= 100:
                    emit("octane_ron", int(number), None, m.group(0), r["text"], "octane")
    # sentence rules: oil grade/approval and viscosity, with the engine the sentence names
    # sentences end at a period that is not a decimal point ("1.5L" stays inside)
    for m in re.finditer(r"(?:[^.•■]|(?<=\d)\.(?=\d))*?(?:engine oil|oil grade|motor oil|oils?\b)(?:[^.•■]|(?<=\d)\.(?=\d))*", flat, re.I):
        sentence = m.group(0)
        if not RECOMMEND.search(sentence):
            continue
        alt = "_alternative" if ALTERNATIVE.search(sentence) else ""
        engine = engine_text(sentence)
        for s in STANDARDS.finditer(sentence):
            emit("engine_oil_specification" + alt, std_value(s.group(0)), None, s.group(0), sentence[:300], "oil grade", engine)
        for s in OEM_APPROVALS.finditer(sentence):
            emit("engine_oil_oem_approval" + alt, norm(s.group(0)), None, s.group(0), sentence[:300], "oil approval", engine)
        if re.search(r"viscosity|SAE|grade", sentence, re.I):
            for v in VISCOSITY.finditer(sentence):
                visc = (v.group(1) or v.group(2)).upper()
                visc = re.sub(r"W-?", "W-", visc)
                emit("engine_oil_viscosity" + alt, "SAE " + visc, None, v.group(0), sentence[:300], "viscosity", engine)
    return facts, review


# ---- ruled capacity tables (Hyundai/Kia "Recommended lubricants and capacities") --------------
# The table has drawn cell borders; an engine name printed over two lines next to the values
# cannot be paired by text position, but the cells can. pdfplumber returns None for a cell
# covered by a merged cell above it (the value continues) and "" for an empty cell.
TABLE_SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
TABLE_LABEL_HEAD = re.compile(r"lubricant|^\W*item", re.I)
TABLE_VOLUME_HEAD = re.compile(r"volume|capacit", re.I)
TABLE_CLASS_HEAD = re.compile(r"classification|specification|recommended|type", re.I)


def cell(text) -> str:
    return norm(" ".join((text or "").split()))


def ruled_tables(page) -> list[list[list]]:
    out = []
    for table in page.extract_tables(TABLE_SETTINGS):
        if not table or len(table) < 3:
            continue
        head = [cell(c) for c in table[0]]
        if any(TABLE_LABEL_HEAD.search(h) for h in head) and any(TABLE_VOLUME_HEAD.search(h) for h in head):
            out.append(table)
    return out


def table_facts(page_number: int, table: list[list], text: str) -> tuple[list[dict], list[dict]]:
    facts, review = [], []
    flat = norm(text)
    head = [cell(c) for c in table[0]]
    vol_col = next(i for i, h in enumerate(head) if TABLE_VOLUME_HEAD.search(h))
    class_col = next((i for i, h in enumerate(head) if i > vol_col and TABLE_CLASS_HEAD.search(h)), None)
    carried = [None] * len(head)

    def emit(key, value, unit, quote, row, engine=None, extra=None):
        if quote and norm(quote) not in flat:
            review.append({"page": page_number, "key": key, "row": row, "reason": "quote not in page text", "quote": quote})
            return
        if (key, json.dumps(value), engine) in seen:
            return
        seen.add((key, json.dumps(value), engine))
        facts.append({"key": key, "value": value, "unit": unit, "page": page_number, "quote": norm(quote),
                      "row": row, "label": key.replace("_", " "), "engine_text": engine, "source_layout": "ruled_table",
                      **(extra or {})})

    seen = set()
    for raw in table[1:]:
        raw = list(raw) + [None] * (len(head) - len(raw))
        raw = raw[: len(head)]
        if not any(cell(c) for c in raw):
            continue  # spacer row: changes nothing
        if raw[0] is not None and cell(raw[0]):
            carried = [None] * len(head)  # a new item starts: nothing continues from the item above
        row = []
        for i, c in enumerate(raw):
            if c is None:  # covered by a merged cell (above, or to the left on the item's first row)
                row.append(carried[i])
            else:
                row.append(cell(c))
                carried[i] = cell(c)
        label = row[0] or ""
        middle = [c for c in row[1:vol_col] if c]
        volume_text = row[vol_col] or ""
        classification = row[class_col] if class_col is not None else ""
        if not volume_text and not classification:
            continue
        line = " | ".join(x for x in (label, *middle, volume_text, classification) if x)
        key = next((k for k, pattern in LABELS if pattern.search(label)), None)
        if SKIP_ROW.search(label) and not re.search(r"automatic transmission|\bCVT\b|\bATF\b", label, re.I):
            key = None
        brake = re.search(r"\bbrake", label, re.I)
        sub_label = [c for c in middle if not ENGINE_WORD.search(c)]
        engine = next((c for c in middle if ENGINE_WORD.search(c)), None)
        if key and volume_text:
            vol = volume(volume_text)
            if sub_label or (vol and "error" in vol) or vol is None:
                review.append({"page": page_number, "key": key, "row": line,
                               "reason": "sub-divided row (e.g. DCT gear/control oil)" if sub_label
                               else (vol or {}).get("error", "no volume")})
            else:
                emit(key, vol["litres"], "L", vol["original"], line, engine if key != "fuel_tank_l" else None,
                     {"original": vol["original"], "approx_in_source": vol["approx"]})
        if not classification:
            continue
        if key and key.startswith("engine_oil"):
            for v in VISCOSITY.finditer(classification):
                visc = re.sub(r"W-?", "W-", (v.group(1) or v.group(2)).upper())
                emit("engine_oil_viscosity", "SAE " + visc, None, v.group(0), line, engine)
            for m in STANDARDS.finditer(classification):
                emit("engine_oil_specification", std_value(m.group(0)), None, m.group(0), line, engine)
            for m in OEM_APPROVALS.finditer(classification):
                emit("engine_oil_oem_approval", norm(m.group(0)), None, m.group(0), line, engine)
        elif key == "coolant_capacity_l":
            for m in COOLANT_TYPE.finditer(classification):
                emit("coolant", norm(m.group(0)), None, m.group(0), line)
            for m in COOLANT_DESCRIPTION.finditer(classification):
                emit("coolant_description", norm(m.group(0)).strip(), None, m.group(0), line)
        elif key == "transmission_fluid_capacity_l" and not sub_label:
            for m in ATF_TYPE.finditer(classification):
                emit("transmission_fluid", norm(m.group(0)), None, m.group(0), line)
        elif brake:
            dots = list(dict.fromkeys(norm(b.group(1)) for b in BRAKE_FLUID.finditer(classification)))
            if dots:
                emit("brake_fluid", " or ".join(dots), None, dots[0] if len(dots) == 1 else classification, line)
    return facts, review


# engine names in table cells: "Smartstream G2.5 GDi", "Gamma 1.6 T-GDI", "Theta II 2.4 GDI", "2.0L MPI"
ENGINE_WORD = re.compile(r"\d\.\d|smartstream|gamma|theta|lambda|\bnu\b|kappa|\bGDi\b|\bMPi\b|T-?GDi", re.I)


def engine_codes(pages: list[str]) -> list[dict]:
    """Factory engine codes stated in the specification chapter, with the stating text."""
    found = []
    for number, text in enumerate(pages, 1):
        for m in re.finditer(r"(?:Model|Engine(?: type)?|Engine code)[^.\n]{0,40}?\(([A-Z0-9][A-Z0-9-]{3,12}(?:\s(?:and|or)\s[A-Z0-9][A-Z0-9-]{3,12})*)\)", text):
            codes = re.findall(r"[A-Z0-9][A-Z0-9-]{3,12}", m.group(1))
            if all(re.search(r"\d", c) and re.search(r"[A-Z]", c) for c in codes):
                found.append({"page": number, "codes": codes, "quote": norm(m.group(0))})
    return found


def process(doc: dict) -> dict:
    cache = page_cache(doc["sha256"])
    if cache is None:
        return {"status": "no_page_cache"}
    pages = cache["pages"]
    market, marks = edition_market(pages, official_us=doc["tier"] == "A")
    result = {
        "doc": {k: (str(v) if isinstance(v, Path) else v) for k, v in doc.items()},
        "extractor": EXTRACTOR,
        "pages": len(pages),
        "edition_market": market,
        "edition_markers": marks,
        "facts": [],
        "review": [],
        "engine_codes": engine_codes(pages),
    }
    if market != "US":
        result["status"] = "other_market"
        return result
    candidates = page_candidates(pages)
    state = PageState()
    with pdfplumber.open(doc["path"]) as pdf:
        for index in candidates:
            try:
                tables = ruled_tables(pdf.pages[index])
                columns = [] if tables else rows_of(pdf.pages[index])
            except Exception as exc:  # a damaged page must not stop the document
                result["review"].append({"page": index + 1, "reason": f"page unreadable: {type(exc).__name__}"})
                continue
            for table in tables:
                facts, review = table_facts(index + 1, table, pages[index])
                result["facts"] += facts
                result["review"] += review
            # with a ruled table the cells are authoritative; only the sentence rules still run
            facts, review = extract_page(index + 1, columns, pages[index], state)
            result["facts"] += facts
            result["review"] += review
    result["candidate_pages"] = [i + 1 for i in candidates]
    result["status"] = "ok"
    return result


def main(argv) -> int:
    make = argv[0]
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    out_dir = WORK / make / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = documents(make)
    if only:
        docs = [d for d in docs if only in d["key"] or only in str(d["path"])]
    summary = defaultdict(int)
    for doc in docs[:limit]:
        target = out_dir / f"{doc['key']}.json"
        if target.exists():
            old = json.loads(target.read_text(encoding="utf-8"))
            if old.get("extractor") == EXTRACTOR and old["doc"]["sha256"] == doc["sha256"] and "--force" not in argv:
                summary["cached"] += 1
                continue
        result = process(doc)
        summary[result["status"]] += 1
        if result["status"] == "no_page_cache":
            continue
        target.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(doc["key"], result["status"], len(result.get("facts", [])), "facts", len(result.get("review", [])), "review", flush=True)
    print(dict(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
