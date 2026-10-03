"""Nissan and INFINITI maintenance items from the official US documents already in the raw store.

Documents (manifests data_work/_shared/manifest_official/{owners.,www.}nissanusa.com.csv,
{owners.,admin.owners.,www.}infinitiusa.com.csv; page text from the pagetext store):

  * "Service and Maintenance Guide" (model-agnostic yearly booklet, 2014-2016): one page per
    mileage point ("10,000 MILES OR 12 MONTHS") listing STANDARD MAINTENANCE and "Additional
    Maintenance Items for Severe Operating Conditions" (bullets ❑ / __). The interval of an item
    is derived from the points where it is listed (EVERY d, or FIRST f + SUBSEQUENT s); severe =
    standard points + additional severe points. The guide names models only in footnotes and
    parentheses ("CVT fluid on ... Altima, ... Rogue ..."; "(NV200 Taxi only)"): an item that
    names one of our models is a FACT for that line; an item that names only other models is not
    used; an item printed for every model is written as SECONDARY_NOTE (model not named).
  * "Owner's Manual and Maintenance Information" (2016/2017+), chapter "Maintenance and
    schedules", in one of two layouts:
      - grid tables (2016-2020): MAINTENANCE INTERVAL columns (miles x 1,000 / km / months) with
        R / I marks. The text layer loses the column of a mark, so the marks are placed from the
        glyph positions of the PDF content stream (pypdf, see Glyphs); NOTE (n) texts and text
        cells ("Replace every 105,000 miles (168,000 km)") give stated intervals; the
        "Maintenance under severe operating conditions" table gives the severe intervals;
      - point lists (2021+): "10,000 miles/(16,000 km)/12 months" (Nissan) or
        "10,000 Miles/12 Months/16,000 Km" (INFINITI) blocks with "Standard maintenance:" and
        "Severe maintenance:" bullets; footnotes with stated intervals win over the points.
  * Engine sections ("PR25DD ENGINE MODEL", "(for VR30DDTT engine)") and edition (hybrid
    manuals) go to applicability as printed; "(AWD models)" -> drive AWD.

Warranty Information Booklets were checked and carry no schedule. Every item quotes the page
text of the cited page (self-check at the end). Nothing is written for marks that do not form a
regular pattern, or for documents of the same line/year that disagree (gap / conflict entry).

Output: data_work/<make>/staging/<line>/maintenance_official.json (maintenance_common.write).

  .venv/Scripts/python.exe scripts/build_maintenance_nissan.py [nissan|infiniti ...]
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import ContentStream

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import (  # noqa: E402
    JOBS,
    gen_for,
    generations_of,
    item,
    merge_years,
    miles_to_km,
    norm,
    our_lines,
    page_text,
    pdf_source,
    write,
)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

NAME = "official"
MANIFESTS = {
    "nissan": ["owners.nissanusa.com.csv", "www.nissanusa.com.csv"],
    "infiniti": ["owners.infinitiusa.com.csv", "admin.owners.infinitiusa.com.csv", "www.infinitiusa.com.csv"],
}
REGISTRY = {"nissan": "factory-nissan-us", "infiniti": "factory-infiniti-us"}
# how each of our lines is named in the documents
MODEL_NAMES = {
    "altima": r"Altima(?! Coupe)", "sentra": r"Sentra", "rogue": r"Rogue(?! Sport)", "pathfinder": r"Pathfinder",
    "q50": r"Q50", "qx60": r"QX60|JX", "fx-qx70": r"QX70|FX",
}
OTHER_MODELS = (r"370Z|Armada|\bcube\b|Frontier|Juke|LEAF|Leaf|Maxima|Murano|NV ?200|NV ?\d{4}|\bNV\b|Quest|Titan|Versa|"
                r"Xterra|GT-R|Kicks|Altima Coupe|Q40|Q60|Q70|QX30|QX50|QX56|QX80|QX4|EX37|M37|M56|G37")

EXTRA_JOBS = [  # tried before maintenance_common.JOBS
    ("inverter_coolant", r"inverter coolant"),
    ("fluid_levels", r"all fluids|all fluid levels"),
    ("key_fob_battery", r"intelligent key"),
    ("brake_lines", r"brake (?:lines|hoses)"),
    ("brakes", r"front and rear brakes|brake pads|brake calipers"),
    ("steering_linkage", r"steering gear|tie rod ends|steering linkage"),
    ("suspension", r"suspension (?:components|parts)|axle (?:&|and) suspension"),
    ("propeller_shaft", r"propeller shaft"),
    ("drive_shaft_boots", r"drive ?shaft boots"),
    ("exhaust_system", r"exhaust system"),
    ("evap_vapor_lines", r"\bEVAP\b|vapor lines|vapor vent"),
    ("fuel_lines", r"fuel lines"),
    ("valve_clearance", r"valve clearance"),
    ("transfer_case_fluid", r"transfer (?:case )?(?:fluid|oil)"),
    ("awd_coupling_fluid", r"AWD coupling"),
    ("differential_fluid", r"differential (?:gear )?oil|differential and fluid"),
    ("transmission_fluid", r"\bCVT\b|transmission fluid"),
    ("tire_rotation", r"tire rotation|rotate tires"),
]
COMPOUND = [  # labels naming two jobs
    (r"transfer fluid (?:&|and) differential", ["transfer_case_fluid", "differential_fluid"]),
    (r"steering gear (?:&|and) linkage,? axle (?:&|and) suspension", ["steering_linkage", "suspension"]),
    (r"propeller shaft (?:&|and) drive shaft boots", ["propeller_shaft", "drive_shaft_boots"]),
    (r"engine oil (?:&|and) (?:oil )?filter", ["engine_oil_and_filter"]),
    (r"EVAP vapor lines and fuel lines", ["evap_vapor_lines", "fuel_lines"]),
]


def jobs_of(label: str) -> list[str]:
    text = re.sub(r"[*#$]|\s\d+(?:,\d+)*$", " ", label)
    for pattern, jobs in COMPOUND:
        if re.search(pattern, text, re.I):
            return jobs
    for job, pattern in EXTRA_JOBS + JOBS:
        if re.search(pattern, text, re.I):
            return [job]
    return []


def drive_of(text: str) -> str | None:
    found = re.search(r"\((?:for )?(AWD|4WD|FWD)(?: models?)?\)|\b(AWD|4WD) models?\b", text)
    return (found.group(1) or found.group(2)) if found else None


def num(text: str) -> float:
    return float(text.replace(",", ""))


def from_points(points: list[float]) -> list[tuple[str, float]] | None:
    """[(occurrence, value)]: EVERY d when the points are d, 2d, 3d ...; FIRST f + SUBSEQUENT s
    when they are f, f+s, f+2s ...; a single point is FIRST; anything else is irregular."""
    points = sorted(set(round(p, 3) for p in points))
    if not points:
        return None
    if len(points) == 1:
        return [("FIRST", points[0])]
    steps = {round(b - a, 3) for a, b in zip(points, points[1:])}
    if len(steps) != 1:
        return None
    step = steps.pop()
    if abs(points[0] - step) < 1e-6:
        return [("EVERY", step)]
    return [("FIRST", points[0]), ("SUBSEQUENT", step)]


# ---- documents -----------------------------------------------------------------------------
def documents(make: str) -> list[dict]:
    lines = our_lines(make)
    docs = []
    for name in MANIFESTS[make]:
        path = WORK / "_shared" / "manifest_official" / name
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                # (the first row of owners.nissanusa.com.csv has make "issan": the path decides)
                if row["status"] != "ok" or not row["path"].startswith(f"official/{make}/"):
                    continue
                if row["doc_type"] not in ("owners_manual", "maintenance_guide"):
                    continue
                docs.append({
                    "key": "official-" + hashlib.sha1(row["url"].encode()).hexdigest()[:12],
                    "lines": [ln for ln in row["lines"].split(";") if ln in lines],
                    "years": [int(y) for y in row["years"].split(";") if y],
                    "doc_type": row["doc_type"], "title": row["title"], "url": row["url"],
                    "path": RAW_ROOT / row["path"], "sha256": row["sha256"], "retrieved_at": row["retrieved_at"],
                    "host": name[:-4],
                })
    return docs


def edition_of(doc: dict) -> str:
    if doc["doc_type"] == "maintenance_guide":
        return "hybrid (all hybrid models)" if re.search(r"hybrid", doc["title"], re.I) else "all models"
    found = re.match(r"\d{4}\s+(?:Nissan|INFINITI)\s+(.+?)\s+Owner", doc["title"], re.I)
    return " ".join(found.group(1).lower().split()) if found else doc["title"]


# ---- glyph positions from the content stream -------------------------------------------------
def mult(a, b):
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


IDENT = [1, 0, 0, 1, 0, 0]


class Font:
    def __init__(self, obj):
        from pypdf._codecs.adobe_glyphs import adobe_glyphs
        self.cid = obj.get("/Subtype") == "/Type0"
        self.two_byte = self.cid
        if self.cid:
            enc = obj.get("/Encoding")
            enc = enc.get_object() if enc is not None else None
            if enc is not None and hasattr(enc, "get_data"):
                space = re.search(r"begincodespacerange\s*<([0-9A-Fa-f]+)>", enc.get_data().decode("latin-1"))
                self.two_byte = not (space and len(space.group(1)) == 2)
        self.widths, self.default = {}, 1000 if self.cid else 500
        self.unicode = {}
        if self.cid:
            desc = obj["/DescendantFonts"][0].get_object()
            self.default = float(desc.get("/DW", 1000))
            w = desc.get("/W")
            w = list(w.get_object()) if w is not None else []
            i = 0
            while i < len(w):
                first = int(w[i])
                nxt = w[i + 1].get_object() if hasattr(w[i + 1], "get_object") else w[i + 1]
                if isinstance(nxt, list) or hasattr(nxt, "__iter__"):
                    for k, val in enumerate(nxt):
                        self.widths[first + k] = float(val)
                    i += 2
                else:
                    for code in range(first, int(nxt) + 1):
                        self.widths[code] = float(w[i + 2])
                    i += 3
        else:
            first = int(obj.get("/FirstChar", 0))
            for k, val in enumerate(obj.get("/Widths", []) or []):
                self.widths[first + k] = float(val)
            desc = obj.get("/FontDescriptor")
            if desc is not None and "/MissingWidth" in desc.get_object():
                self.default = float(desc.get_object()["/MissingWidth"])
            enc = obj.get("/Encoding")
            enc = enc.get_object() if enc is not None else None
            if enc is not None and hasattr(enc, "get") and enc.get("/Differences") is not None:
                code = 0
                for el in enc["/Differences"]:
                    if isinstance(el, int) or str(el).lstrip("-").isdigit():
                        code = int(el)
                    else:
                        self.unicode[code] = adobe_glyphs.get(str(el), "")
                        code += 1
        tu = obj.get("/ToUnicode")
        if tu is not None:
            self.read_cmap(tu.get_object().get_data().decode("latin-1"))

    def read_cmap(self, data: str) -> None:
        def u(hexstr):
            raw = bytes.fromhex(hexstr)
            return raw.decode("utf-16-be", errors="ignore") if len(raw) % 2 == 0 else raw.decode("latin-1")
        for block in re.findall(r"beginbfchar(.*?)endbfchar", data, re.S):
            for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", block):
                self.unicode[int(src, 16)] = u(dst)
        for block in re.findall(r"beginbfrange(.*?)endbfrange", data, re.S):
            for lo, hi, rest in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(\[[^\]]*\]|<[0-9A-Fa-f]*>)", block):
                lo, hi = int(lo, 16), int(hi, 16)
                if rest.startswith("["):
                    for k, dst in enumerate(re.findall(r"<([0-9A-Fa-f]*)>", rest)):
                        self.unicode[lo + k] = u(dst)
                else:
                    base = bytes.fromhex(rest[1:-1])
                    for k in range(hi - lo + 1):
                        val = int.from_bytes(base, "big") + k
                        self.unicode[lo + k] = u(val.to_bytes(len(base), "big").hex())

    def codes(self, raw: bytes) -> list[int]:
        if self.two_byte:
            return [int.from_bytes(raw[i:i + 2], "big") for i in range(0, len(raw) - 1, 2)]
        return list(raw)

    def char(self, code: int) -> str:
        if code in self.unicode:
            return self.unicode[code]
        return chr(code) if not self.two_byte else ""


class Glyphs:
    """Positioned glyphs (x0, x1, y, size, char) of a page, in PDF user space (y up)."""

    def __init__(self, path: Path):
        self.reader = PdfReader(str(path))
        self.fonts = {}

    def font(self, ref) -> Font:
        key = id(ref.get_object()) if not hasattr(ref, "idnum") else (ref.idnum, ref.generation)
        if key not in self.fonts:
            self.fonts[key] = Font(ref.get_object())
        return self.fonts[key]

    def page(self, index: int) -> list[tuple]:
        page = self.reader.pages[index]
        out = []
        self.walk(ContentStream(page.get_contents(), self.reader).operations, page.get("/Resources") or {}, IDENT, out)
        return out

    def walk(self, ops, resources, ctm, out) -> None:
        resources = resources.get_object() if hasattr(resources, "get_object") else resources
        fonts = (resources.get("/Font") or {}) if resources else {}
        fonts = fonts.get_object() if hasattr(fonts, "get_object") else fonts
        stack, tm, tlm = [], IDENT, IDENT
        tc = tw = rise = tl = 0.0
        th, font, fs = 1.0, None, 1.0

        def show(string) -> None:
            nonlocal tm
            raw = string.get_original_bytes() if hasattr(string, "get_original_bytes") else bytes(string)
            if font is None:
                return
            if font.two_byte and raw[:2] == b"\xfe\xff" and len(raw) % 2 == 0:
                raw = raw[2:]  # pypdf hands two-byte strings back with a UTF-16 BOM in front
            for code in font.codes(raw):
                w = font.widths.get(code, font.default) / 1000.0
                trm = mult([fs * th, 0, 0, fs, 0, rise], mult(tm, ctm))
                x0, y = trm[4], trm[5]
                x1 = w * trm[0] + trm[4]
                out.append((min(x0, x1), max(x0, x1), y, abs(trm[3]) or abs(trm[1]), font.char(code)))
                adv = (w * fs + tc + (tw if (code == 32 and not font.two_byte) else 0)) * th
                tm = mult([1, 0, 0, 1, adv, 0], tm)

        for operands, op in ops:
            if op == b"q":
                stack.append(ctm)
            elif op == b"Q":
                ctm = stack.pop() if stack else ctm
            elif op == b"cm":
                ctm = mult([float(v) for v in operands], ctm)
            elif op == b"BT":
                tm = tlm = IDENT
            elif op == b"Tf":
                ref = fonts.get(operands[0]) if fonts else None
                font = self.font(ref) if ref is not None else None
                fs = float(operands[1])
            elif op == b"Tc":
                tc = float(operands[0])
            elif op == b"Tw":
                tw = float(operands[0])
            elif op == b"Tz":
                th = float(operands[0]) / 100.0
            elif op == b"TL":
                tl = float(operands[0])
            elif op == b"Ts":
                rise = float(operands[0])
            elif op in (b"Td", b"TD"):
                tx, ty = float(operands[0]), float(operands[1])
                if op == b"TD":
                    tl = -ty
                tlm = mult([1, 0, 0, 1, tx, ty], tlm)
                tm = tlm
            elif op == b"Tm":
                tlm = tm = [float(v) for v in operands]
            elif op == b"T*":
                tlm = mult([1, 0, 0, 1, 0, -tl], tlm)
                tm = tlm
            elif op == b"Tj":
                show(operands[0])
            elif op in (b"'", b'"'):
                if op == b'"':
                    tw, tc = float(operands[0]), float(operands[1])
                tlm = mult([1, 0, 0, 1, 0, -tl], tlm)
                tm = tlm
                show(operands[-1])
            elif op == b"TJ":
                for el in operands[0]:
                    if isinstance(el, (int, float)) or type(el).__name__ in ("FloatObject", "NumberObject"):
                        tm = mult([1, 0, 0, 1, -float(el) / 1000.0 * fs * th, 0], tm)
                    else:
                        show(el)
            elif op == b"Do" and resources:
                xobjs = resources.get("/XObject")
                xobj = xobjs.get_object().get(operands[0]) if xobjs is not None else None
                xobj = xobj.get_object() if xobj is not None else None
                if xobj is not None and xobj.get("/Subtype") == "/Form":
                    matrix = [float(v) for v in xobj.get("/Matrix", IDENT)]
                    self.walk(ContentStream(xobj, self.reader).operations, xobj.get("/Resources") or resources,
                              mult(matrix, ctm), out)


def tokens(glyphs: list[tuple]) -> list[dict]:
    """Words: glyphs on one baseline separated by less than a fifth of the font size."""
    rows = defaultdict(list)
    for g in glyphs:
        if not g[4] or not g[4].strip():
            continue
        rows[round(g[2] * 2) / 2].append(g)
    out = []
    for y, gs in rows.items():
        gs.sort(key=lambda g: g[0])
        cur = [gs[0]]
        for g in gs[1:]:
            if g[0] - cur[-1][1] <= 0.2 * max(g[3], 1):
                cur.append(g)
            else:
                out.append(cur)
                cur = [g]
        out.append(cur)
    return [{"x0": c[0][0], "x1": c[-1][1], "y": c[0][2], "size": c[0][3], "text": "".join(g[4] for g in c)}
            for c in out]


# ---- grid tables ------------------------------------------------------------------------------
NUMERIC = re.compile(r"^\d{1,3}(?:\.\d{1,2})?$")
KM = re.compile(r"^\(\d{1,3}\)$")
MARK = re.compile(r"^[RI]\*?$")
GRID_PAGE = re.compile(r"MAINTENANCE INTERVAL", re.I)
SECTION_ENGINE = re.compile(r"\b([A-Z0-9]{4,10}) ENGINE MODEL\b|\(([A-Z0-9]{4,10}) engine\s+model\)")


def engine_at(text: str, pos: int | None, carried: str | None) -> tuple[str | None, str | None]:
    """(engine of the section in force at text position pos, engine carried to the next page)."""
    heads = [(m.start(), m.group(1) or m.group(2)) for m in SECTION_ENGINE.finditer(text)]
    before = [e for p, e in heads if pos is None or p < pos]
    return (before[-1] if before else carried), (heads[-1][1] if heads else carried)
TABLE_TITLE = re.compile(r"(EMISSION CONTROL SYSTEM MAINTENANCE|CHASSIS (?:AND|&) BODY MAINTENANCE)(?:\s*\(for ([^)]*?)\s*engines?\))?")


def cluster_y(toks: list[dict], tol: float = 1.5) -> list[tuple[float, list[dict]]]:
    """Tokens grouped into rows of (nearly) equal baseline, top first."""
    out = []
    for t in sorted(toks, key=lambda t: -t["y"]):
        if out and abs(out[-1][0] - t["y"]) <= tol:
            out[-1][1].append(t)
        else:
            out.append((t["y"], [t]))
    return out


def grid_page(glyph_tokens: list[dict]) -> dict | None:
    """Columns (miles, km, months) and rows (label, marks per column, text cells) of one grid page."""
    rows = [(y, ts) for y, ts in cluster_y([t for t in glyph_tokens if NUMERIC.match(t["text"]) or KM.match(t["text"])])
            if len(ts) >= 4]
    rows.sort(key=lambda r: -r[0])
    plain = [(y, sorted(ts, key=lambda t: t["x0"])) for y, ts in rows if all(NUMERIC.match(t["text"]) for t in ts)]
    paren = [(y, sorted(ts, key=lambda t: t["x0"])) for y, ts in rows if all(KM.match(t["text"]) for t in ts)]
    if len(plain) < 2 or not paren:
        return None
    (y_miles, miles), (y_months, months) = plain[0], plain[1]
    y_km, kms = paren[0]
    if not (len(miles) == len(months) == len(kms)) or not (y_miles > y_km > y_months):
        return None
    vals = [num(t["text"]) for t in miles]
    if vals != sorted(vals):
        return None
    centers = [(t["x0"] + t["x1"]) / 2 for t in miles]
    step = min(b - a for a, b in zip(centers, centers[1:]))
    columns = [{"miles": num(m["text"]) * 1000, "km": int(num(k["text"][1:-1]) * 1000), "months": int(num(mo["text"]))}
               for m, k, mo in zip(miles, kms, months)]
    left = centers[0] - step / 2
    body = [t for t in glyph_tokens if t["y"] < y_months - 2]
    lines = []
    for y, ts in cluster_y([t for t in body if t["x1"] < left + 1], tol=2.0):
        text = " ".join(t["text"] for t in sorted(ts, key=lambda t: t["x0"]))
        if re.match(r"^(NOTE:|\(\d+\)|\*|Maintenance and schedules|\d+-\d+ Maintenance)", text):
            break
        lines.append({"y": y, "text": text})
    if not lines:
        return None
    bottom = lines[-1]["y"] - 6
    # wrapped labels: a line starting in lower case continues the previous one
    labels = []
    for line in lines:
        if labels and re.match(r"^[a-z(]", line["text"]) and not re.match(r"^\(\d", line["text"]):
            labels[-1]["text"] += " " + line["text"]
            labels[-1]["ys"].append(line["y"])
        else:
            labels.append({"text": line["text"], "ys": [line["y"]]})
    for lab in labels:
        lab["marks"], lab["cells"] = defaultdict(set), []
    for t in body:
        if t["x1"] < left + 1 or t["y"] < bottom:
            continue
        lab = min(labels, key=lambda lb: min(abs(t["y"] - y) for y in lb["ys"]))
        if min(abs(t["y"] - y) for y in lab["ys"]) > 8:
            continue
        center = (t["x0"] + t["x1"]) / 2
        col = min(range(len(centers)), key=lambda i: abs(centers[i] - center))
        if MARK.match(t["text"]) and abs(centers[col] - center) < step / 2:
            lab["marks"][t["text"][0]].add(col)
        else:
            lab["cells"].append((t["x0"], t["text"]))
    for lab in labels:
        lab["cell"] = " ".join(text for _, text in sorted(lab["cells"]))
    return {"columns": columns, "rows": labels}


def clean_label(text: str) -> tuple[str, list[int]]:
    notes = [int(n) for group in re.findall(r"NOTE\s*((?:\(\d+\))+)", text) for n in re.findall(r"\d+", group)]
    label = re.sub(r"(?:See\s+)?NOTE\s*(?:\(\d+\))+", " ", text)
    label = re.sub(r"[-�$]", " ", label)
    return " ".join(label.split()), notes


def page_notes(flat: str) -> dict[int, str]:
    """'(n) text' notes printed below a table (flattened page text)."""
    start = flat.find("NOTE:")
    if start < 0:
        return {}
    part = flat[start:]
    return {int(m.group(1)): m.group(2).strip()
            for m in re.finditer(r"\((\d{1,2})\)\s+(.*?)(?=\s\(\d{1,2}\)\s|\s\*:?\s*Maintenance items|$)", part)}


FIRST_THEN = re.compile(
    r"First replacement(?: interval)? is (?:at )?(?P<m1>[\d,]+) miles \((?P<k1>[\d,]+) km\)(?: or (?P<t1>\d+) months)?\. "
    r"After (?:the )?first replacement, replace every (?P<m2>[\d,]+) miles \((?P<k2>[\d,]+) km\)(?: or (?P<t2>\d+) months)?", re.I)
NOT_JUST = re.compile(
    r"(?P<cond>If [^.]*?),\s*(?:[^.]*?\.\s*And if the inspection is not performed, )?change \(not just inspect\)[^.]*?"
    r"(?:at )?every (?P<m>[\d,]+)(?: miles)? \((?P<k>[\d,]+) km\)(?: or (?P<t>\d+) months)?", re.I)
EVERY_TEXT = re.compile(r"(?P<verb>Replace|Inspect|Rotate)?[^.]*?every (?P<m>[\d,]+) miles \((?P<k>[\d,]+) km\)(?: or (?P<t>\d+) months)?", re.I)
SEVERE_ROW = re.compile(
    r"^(?P<label>.+?)\s+(?P<op>Replace|Inspect|Rotate|Change)\s+(?P<every>Every (?P<m>[\d,]+) miles \((?P<k>[\d,]+) km\)(?: or (?P<t>\d+) months)?)", re.I)


def grid_shapes(pts: dict) -> tuple[tuple | None, str | None]:
    """Interval shapes of one row's marks {miles: (km, months, page)} in miles, months and km.
    A header column whose printed km/months break an otherwise regular pattern (2020 Altima
    KR20DDET table: '82.5 (138) 138') is left out, with a note; nothing else is repaired."""
    miles = sorted(pts)
    sm = from_points(miles)
    if not sm:
        return None, None
    st = from_points([pts[k][1] for k in miles])
    sk = from_points([pts[k][0] for k in miles])
    if st and sk and [o for o, _ in sm] == [o for o, _ in st] == [o for o, _ in sk]:
        return (sm, st, sk), None
    if len(miles) < 3:
        return None, None
    ratio_t = defaultdict(list)
    ratio_k = defaultdict(list)
    for m in miles:
        ratio_t[round(pts[m][1] / m, 9)].append(m)
        ratio_k[round(pts[m][0] / m, 9)].append(m)
    rt, mt = max(ratio_t.items(), key=lambda kv: len(kv[1]))
    rk, mk = max(ratio_k.items(), key=lambda kv: len(kv[1]))
    odd = (set(miles) - set(mt)) | (set(miles) - set(mk))
    if len(odd) != 1:
        return None, None
    skip = odd.pop()
    st = [(o, round(v * rt)) for o, v in sm]
    sk = [(o, round(v * rk)) for o, v in sm]
    return (sm, st, sk), (f"the {int(skip):,}-mile column prints ({pts[skip][0] // 1000}) km x 1,000 / {pts[skip][1]} months, "
                          "inconsistent with the other columns (misprint); km and months read from the other columns")


def interval(miles, km, months) -> dict:
    miles = int(num(str(miles))) if miles is not None else None
    return {"interval_km": (int(num(str(km))) if km else miles_to_km(miles)) if miles else None,
            "interval_miles_original": miles, "interval_months": int(months) if months else None,
            "rule": "WHICHEVER_FIRST" if miles and months else None}


# ---- point lists (guides 2014-2016, manuals 2021+) ---------------------------------------------
HEAD_GUIDE = re.compile(r"^([\d,]+) MILES OR (\d+) MONTHS\s*$")
HEAD_N21 = re.compile(r"^([\d,]+) miles/\s*\(([\d,]+) km\)/\s*(\d+)\s*months\s*$", re.I)
HEAD_I21 = re.compile(r"^([\d,]+) Miles/\s*(\d+) Months/\s*([\d,]+)\s*Km\s*$", re.I)
HEAD_R23 = re.compile(r"^([\d,]+) Miles/([\d,]+)\s*Km/\s*(\d+)\s*Months\s*$", re.I)


def head_point(line: str) -> tuple | None:
    """(miles, km, months) of a point heading of the 2021+ manuals, else None."""
    m = HEAD_N21.match(line)
    if m:
        return num(m.group(1)), int(num(m.group(2))), int(m.group(3))
    m = HEAD_I21.match(line)
    if m:
        return num(m.group(1)), int(num(m.group(3))), int(m.group(2))
    m = HEAD_R23.match(line)
    if m:
        return num(m.group(1)), int(num(m.group(2))), int(m.group(3))
    return None
BULLET = re.compile(r"^\s*(?:❑|•|∙|\.\s|__)\s*")


def list_pages(texts: list[str]) -> list[int]:
    out = []
    for i, t in enumerate(texts):
        if re.search(r"Dealer Name|Dealer\s+Stamp|MAINTENANCE LOG|Premium Upgrade adds", t):
            continue
        lines = t.splitlines()
        joined = [a + (" " + b if re.match(r"^[\d,]+ (?:miles|Miles)/", a) and not head_point(a) else "")
                  for a, b in zip(lines, lines[1:] + [""])]
        if any(HEAD_GUIDE.match(x) or head_point(x) for x in joined):
            out.append(i)
    return out


def split_items(line: str) -> list[str]:
    if "__" in line:
        return [BULLET.sub("", p).strip() for p in line.split("__") if BULLET.sub("", p).strip()]
    return [BULLET.sub("", line).strip()]


def merged_lines(text: str) -> list[str]:
    """Page lines with a point heading or an engine heading split over two lines joined."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out, skip = [], False
    for a, b in zip(lines, lines[1:] + [""]):
        if skip:
            skip = False
            continue
        both = a + " " + b.strip()
        if (re.match(r"^[\d,]+ (?:miles|Miles)/", a) and not head_point(a) and head_point(both)) or (
                re.search(r"\([A-Z0-9]{4,10}(?: engine)?$", a) and re.match(r"^\s*(?:engine )?model\)", b)):
            out.append(both)
            skip = True
        else:
            out.append(a)
    return out


def parse_points(texts: list[str], pages: list[int], guide: bool) -> list[dict]:
    """[{point: (miles, km|None, months), condition, default_action, text, page, engine, block}]:
    every bullet of every mileage point, with the footnotes of its block (block["footnotes"])."""
    out = []
    engine, point, block = None, None, None
    condition, default_action, cur, note = "NORMAL", None, None, None
    wanted = set(pages) if guide else set(range(pages[0], min(pages[-1] + 2, len(texts))))
    for index in range(max(pages[0] - 3, 0), min(pages[-1] + 2, len(texts))):
        lines = merged_lines(texts[index])
        if index not in wanted:  # pages before the point pages: only the engine sections count
            for x in lines:
                e = SECTION_ENGINE.search(x)
                if e and not BULLET.match(x):
                    engine = e.group(1) or e.group(2)
            continue
        if guide:
            head = next((HEAD_GUIDE.match(x) for x in lines if HEAD_GUIDE.match(x)), None)
            if head is None:
                continue
            point, block = (num(head.group(1)), None, int(head.group(2))), {"footnotes": {}}
            condition, default_action, cur, note = "NORMAL", None, None, None
        else:  # a point block of the 2021+ manuals continues on the next page
            cur = note = None
        for x in lines:
            if re.match(r"^\s*(?:Additional information|NOTE FOR |MAINTENANCE LOG|MAINTENANCE UNDER)", x):
                if not guide:
                    point = None  # the schedule (or this engine's part of it) ends here
                cur = note = None
                continue
            e = SECTION_ENGINE.search(x)
            if e and not BULLET.match(x):
                engine = e.group(1) or e.group(2)
                cur = note = None
                continue
            h = head_point(x)
            if h and not guide:
                point = h
                block = {"footnotes": {}}
                condition, default_action, cur, note = "NORMAL", None, None, None
                continue
            if HEAD_GUIDE.match(x) or re.match(r"^\d+\s*MAINTENANCE SCHEDULE$|^MAINTENANCE SCHEDULE$|^Maintenance and schedules|^\d+-\d+ Maintenance", x):
                continue
            if re.match(r"^\s*(?:Standard maintenance:?|STANDARD MAINTENANCE)\s*$", x, re.I):
                condition, default_action, cur, note = "NORMAL", None, None, None
                continue
            if re.match(r"^\s*(?:Severe (?:use )?maintenance:?|Additional Maintenance Items for Severe Operating)", x, re.I):
                condition, default_action, cur, note = "SEVERE", None, None, None
                continue
            if re.match(r"^\s*Inspections?:\s*$", x):
                default_action, cur, note = "INSPECT", None, None
                continue
            if re.match(r"^\s*Essentials:\s*$", x):
                default_action, cur, note = None, None, None
                continue
            f = re.match(r"^\s*\((\d{1,2})\)\s+(.*)$", x) if not guide else re.match(r"^(\d)\s+([A-Z].*)$", x)
            if f and block is not None:
                note = int(f.group(1))
                block["footnotes"][note] = f.group(2).strip()
                cur = None
                continue
            if re.match(r"^\s*(?:\*|Equipment varies|For the ultimate|participating|Perform at number|Choose the|The following|After [\d,]+ miles)", x):
                cur = note = None
                continue
            if point is None:
                continue
            if BULLET.match(x):
                note = None
                for part in split_items(x):
                    if re.match(r"^Inspect the following:?$", part, re.I):
                        default_action, cur = "INSPECT", None
                        continue
                    if re.search(r"Multi-Point|Premium|\(Continued|continued from", part):
                        cur = None
                        continue
                    cur = {"point": point, "condition": condition, "default_action": default_action, "text": part,
                           "page": index + 1, "engine": engine, "block": block}
                    out.append(cur)
                continue
            if note is not None and x.strip():
                block["footnotes"][note] += " " + x.strip()
                continue
            if cur is not None and "__" in x:  # '... (4WD/' + 'AWD/RWD) __ Steering gear ...'
                head, *rest = x.split("__")
                if head.strip():
                    cur["text"] += " " + head.strip()
                for part in rest:
                    if part.strip():
                        cur = {**cur, "text": part.strip()}
                        out.append(cur)
                continue
            if cur is not None and x.strip() and not re.match(r"^\s*\((?:Continued|Standard)", x):
                if (re.match(r"^[a-z(&]", x.strip()) or cur["text"].endswith(("/", "-", ",", "￾", "&"))
                        or re.match(r"^\s*(?:AWD|4WD)", x)):
                    cur["text"] += " " + x.strip()
    return out


def label_refs(text: str, guide: bool) -> tuple[str, list[int]]:
    """'Replace engine oil & filter (1)' -> label, [1]; guide 'CVT fluid4' / 'fluid3,4' -> refs."""
    refs = [int(n) for n in re.findall(r"\((\d{1,2})\)", text)]
    label = re.sub(r"\(\d{1,2}\)", " ", text)
    if guide:
        m = re.search(r"(?<=[A-Za-z)])(\d(?:,\d)*)$", label.strip())
        if m:
            refs += [int(n) for n in m.group(1).split(",")]
            label = label.strip()[: m.start()]
    return " ".join(label.replace("*", " ").split()), refs


def action_for(label: str, default: str | None) -> str | None:
    t = label.lower()
    if re.match(r"(?:perform )?(?:tire rotation|rotate)", t):
        return "ROTATE"
    if re.match(r"(replace|change)", t):
        return "REPLACE"
    if re.match(r"(inspect|check)", t):
        return "INSPECT"
    if re.match(r"lubricate", t):
        return None
    if re.match(r"engine coolant", t):
        return "REPLACE"
    return default


def model_scope(line_slug: str, texts: list[str]) -> str:
    """'named' (our model is named), 'other' (only other models named), 'generic' (printed for every
    model; exceptions name other models only). texts = the item label and its footnotes."""
    ours = MODEL_NAMES[line_slug]
    others = "|".join([OTHER_MODELS] + [v for k, v in MODEL_NAMES.items() if k != line_slug])
    named = other = False
    for text in texts:
        if not text:
            continue
        if re.search(r"except[^.;)]*\b(?:" + ours + r")\b", text):
            return "other"
        if re.search(r"\b(?:" + ours + r")\b", text):
            named = True
        elif re.search(r"\b(?:" + others + r")", text) and not re.search(r"\bexcept\b", text, re.I):
            other = True
    return "named" if named else "other" if other else "generic"


# ---- build -------------------------------------------------------------------------------------
class Builder:
    def __init__(self, make: str):
        self.make = make
        self.lines = our_lines(make)
        self.sources: dict = {}
        self.pages_used = defaultdict(set)
        self.per_line = defaultdict(list)  # line -> raw entries
        self.gaps = defaultdict(list)
        self.checked_docs = []

    def scope(self, line, doc, years) -> str:
        return f"{self.make}/{line} MY{years[0]}" + (f"-{years[-1]}" if len(years) > 1 else "") + f" ({doc['key']})"

    def add(self, doc, job, action, *, condition="NORMAL", occurrence="EVERY", iv=None, applicability=None,
            note=None, quote, page, locator, display="FACT", lines=None):
        texts = self.texts[doc["key"]]
        if norm(quote) not in norm(texts[page - 1]):
            raise SystemExit(f"quote not on page: {doc['key']} p.{page}: {quote[:100]}")
        if iv and iv.get("interval_km") is not None and not (1000 <= iv["interval_km"] <= 400000):
            return
        self.pages_used[doc["key"]].add(page)
        for line in (lines if lines is not None else doc["lines"]):
            self.per_line[line].append({"doc": doc, "job": job, "action": action, "condition": condition,
                                        "occurrence": occurrence, "iv": iv or {}, "applicability": applicability or {},
                                        "note": note, "quote": quote, "page": page, "locator": locator,
                                        "display": display})

    def gap(self, doc, field, reason, lines=None):
        for line in (lines if lines is not None else doc["lines"]):
            years = self.years_of(doc, line)
            if years:
                self.gaps[line].append({"scope": self.scope(line, doc, years), "field": f"maintenance:{field}", "reason": reason})

    def years_of(self, doc, line) -> list[int]:
        lo, hi = self.lines[line].years
        return [y for y in doc["years"] if lo <= y <= hi]

    def quote_line(self, texts, page, label) -> str:
        """The page-text line of a grid row (label start)."""
        words = label.split()[:3]
        pattern = re.compile(r"^\s*" + r"\s+".join(re.escape(w) for w in words), re.I)
        for ln in texts[page - 1].splitlines():
            if pattern.match(ln):
                return ln.strip()
        return " ".join(words)

    # -- grid manuals
    def grid(self, doc, texts, pages):
        glyphs = Glyphs(doc["path"])
        app_base = {"edition": edition_of(doc)}
        rows = {}  # (engine, table, label) -> {"marks": {mark: {col}}, "pages": [], "cells": [], "notes": [], "columns": {}}
        carried, table, table_engine = None, None, None
        first_grid = pages[0]
        for index in range(max(first_grid - 3, 0), pages[-1] + 1):
            text = texts[index]
            at = re.search(r"MAINTENANCE INTERVAL", text)
            section_engine, carried = engine_at(text, at.start() if (at and index in pages) else None, carried)
            if index not in pages:
                continue
            title = TABLE_TITLE.search(" ".join(text.split()))
            if title:
                table = "emission" if title.group(1).startswith("EMISSION") else "chassis"
                table_engine = title.group(2)
            parsed = grid_page(tokens(glyphs.page(index)))
            if parsed is None:
                self.gap(doc, "schedule", f"grid table on page {index + 1} not read (columns not found)")
                continue
            notes = page_notes(norm(text))
            engine = table_engine or section_engine
            for row in parsed["rows"]:
                label, refs = clean_label(row["text"])
                if not label:
                    continue
                # the two pages of one table may spell a row differently ('Brake lines & cables' / 'and')
                key = (engine, table, re.sub(r"[^a-z0-9]", "", label.lower().replace("&", "and")))
                r = rows.setdefault(key, {"label": label, "marks": defaultdict(dict), "pages": [], "cells": [], "refs": set(),
                                          "notes": {}, "engine": engine})
                r["pages"].append(index + 1)
                r["refs"] |= set(refs)
                for mark, cols in row["marks"].items():
                    for c in cols:
                        col = parsed["columns"][c]
                        r["marks"][mark][col["miles"]] = (col["km"], col["months"], index + 1)
                if row["cell"]:
                    r["cells"].append((index + 1, row["cell"]))
            for key, r in rows.items():
                if index + 1 in r["pages"]:
                    for n, t in notes.items():
                        r["notes"].setdefault(n, (index + 1, t))
            # notes printed on the page after the first half of a two-page table
            for key, r in rows.items():
                if r["pages"] and r["pages"][-1] == index and notes:
                    for n, t in notes.items():
                        r["notes"].setdefault(n, (index + 1, t))
        for key, r in rows.items():
            jobs = jobs_of(r["label"])
            if not jobs:
                continue
            app = dict(app_base)
            if r["engine"]:
                app["engine"] = r["engine"]
            drive = drive_of(r["label"])
            if drive:
                app["drive"] = drive
            first_page = r["pages"][0]
            quote = self.quote_line(texts, first_page, r["label"])
            stated = False
            # text cell: "Replace every 105,000 miles (168,000 km)"
            for page, cell in r["cells"]:
                m = EVERY_TEXT.search(cell)
                if m:
                    flat = norm(texts[page - 1])
                    q = norm(cell) if norm(cell) in flat else norm(m.group(0))
                    if q not in flat:
                        continue
                    action = {"replace": "REPLACE", "inspect": "INSPECT", "rotate": "ROTATE"}.get((m.group("verb") or "").lower(), "REPLACE")
                    for job in jobs:
                        self.add(doc, job, action, iv=interval(m.group("m"), m.group("k"), m.group("t")), applicability=app,
                                 quote=q, page=page, locator=f"p.{page} grid row '{r['label']}': {cell}")
                    stated = True
                    break
            # notes of the row
            for n in sorted(r["refs"]):
                if n not in r["notes"]:
                    continue
                page, text = r["notes"][n]
                flat = norm(texts[page - 1])
                f = FIRST_THEN.search(text)
                if f:
                    for job in jobs:
                        for occ, mi, k, t in (("FIRST", f.group("m1"), f.group("k1"), f.group("t1")),
                                              ("SUBSEQUENT", f.group("m2"), f.group("k2"), f.group("t2"))):
                            self.add(doc, job, "REPLACE", occurrence=occ, iv=interval(mi, k, t), applicability=app,
                                     quote=norm(f.group(0)), page=page, locator=f"p.{page} NOTE ({n}) of grid row '{r['label']}'")
                    stated = True
                s = NOT_JUST.search(text)
                if s and norm(s.group(0)) in flat:
                    for job in jobs:
                        self.add(doc, job, "REPLACE", condition="SEVERE", iv=interval(s.group("m"), s.group("k"), s.group("t")),
                                 applicability=app, note=f"severe condition as printed: {s.group('cond')}",
                                 quote=norm(s.group(0)), page=page, locator=f"p.{page} NOTE ({n}) of grid row '{r['label']}'")
            # marks
            for mark, action in (("R", "REPLACE"), ("I", "INSPECT")):
                pts = r["marks"].get(mark) or {}
                if not pts:
                    continue
                if stated and action == "REPLACE":
                    continue
                miles = sorted(pts)
                shapes, header_note = grid_shapes(pts)
                if shapes is None:
                    for job in jobs:
                        self.gap(doc, job, f"grid row '{r['label']}' (p.{first_page}): {mark} marks at "
                                 f"{[int(mi) for mi in miles]} miles do not form a regular interval; not converted")
                    continue
                shape_m, shape_t, shape_k = shapes
                for (occ, mi), (_, mo), (_, k) in zip(shape_m, shape_t, shape_k):
                    if occ == "FIRST" and len(shape_m) == 1 and len(miles) == 1:
                        note = "single mark in the printed schedule"
                    else:
                        note = header_note
                    for job in jobs:
                        self.add(doc, job, action, occurrence=occ, iv=interval(mi, k, mo), applicability=app, note=note,
                                 quote=quote, page=first_page,
                                 locator=f"p.{'/'.join(map(str, sorted(set(r['pages']))))} grid row '{r['label']}': {mark} at "
                                         f"{', '.join(f'{int(x):,}' for x in miles)} miles")

    # -- severe table and explanation texts of a manual
    def manual_texts(self, doc, texts, first, last):
        app_base = {"edition": edition_of(doc)}
        carried = None
        for index in range(max(first - 3, 0), min(last + 3, len(texts))):
            text = texts[index]
            at = re.search(r"Maintenance item\s+Maintenance operation\s+Maintenance interval", text, re.I)
            engine, carried = engine_at(text, at.start() if at else None, carried)
            if not at or index < first:
                continue
            lines = text.splitlines()
            start = next(i for i, ln in enumerate(lines) if re.search(r"Maintenance item\s+Maintenance operation", ln, re.I))
            buf = ""
            for ln in lines[start + 1:]:
                cand = (buf + " " + ln).strip() if buf else ln.strip()
                m = SEVERE_ROW.match(cand)
                if not m:
                    buf = cand if len(cand) < 120 and not re.match(r"^(MAINTENANCE UNDER|\d+-\d+|Maintenance and)", ln) else ""
                    continue
                buf = ""
                label = re.sub(r"[-$*]", " ", m.group("label"))
                jobs = jobs_of(label)
                if not jobs:
                    continue
                app = dict(app_base)
                if engine:
                    app["engine"] = engine
                if drive_of(label):
                    app["drive"] = drive_of(label)
                op = m.group("op").lower()
                action = {"replace": "REPLACE", "change": "REPLACE", "inspect": "INSPECT", "rotate": "ROTATE"}[op]
                for job in jobs:
                    self.add(doc, job, action, condition="SEVERE", iv=interval(m.group("m"), m.group("k"), m.group("t")),
                             applicability=app, quote=norm(cand), page=index + 1,
                             locator=f"p.{index + 1} Maintenance under severe operating conditions: {norm(label)}")
        # tire rotation stated in the maintenance explanations ("Tires should be rotated every 5,000 miles (8,000 km)")
        for index in range(max(first - 8, 0), first + 1):
            flat = norm(texts[index])
            for m in re.finditer(r"(?:(?P<eng>[A-Z0-9]{4,10}) Engine [Mm]odel; )?Tires should be rotated every (?P<m>[\d,]+) miles \((?P<k>[\d,]+) km\)", flat):
                app = dict(app_base)
                if m.group("eng"):
                    app["engine"] = m.group("eng")
                self.add(doc, "tire_rotation", "ROTATE", iv=interval(m.group("m"), m.group("k"), None), applicability=app,
                         quote=m.group(0), page=index + 1, locator=f"p.{index + 1} explanation of maintenance items: tire rotation")
            break_on = None
        return None

    # -- point lists
    def points(self, doc, texts, pages, guide: bool):
        entries = parse_points(texts, pages, guide)
        if not entries:
            return
        app_base = {"edition": edition_of(doc)}
        explicit = set()
        groups = defaultdict(lambda: {"NORMAL": {}, "SEVERE": {}, "in_severe": False})
        for e in entries:
            label, refs = label_refs(e["text"], guide)
            action = action_for(label, e["default_action"] or ("INSPECT" if guide and e.get("default_action") else None))
            if action is None and guide:
                action = "INSPECT" if not re.match(r"(Replace|Rotate|Change|Lubricate)", label) else None
            if action is None:
                action = "INSPECT" if e["default_action"] == "INSPECT" else None
            if action is None:
                continue
            jobs = jobs_of(label)
            if not jobs:
                continue
            notes_text = " ".join(e["block"]["footnotes"].get(n, "") for n in refs)
            for line in doc["lines"]:
                scope = model_scope(line, [label] + [e["block"]["footnotes"].get(n, "") for n in refs]) if guide else "named"
                if scope == "other":
                    continue
                # stated intervals in the item's footnotes win over the points
                f = FIRST_THEN.search(norm(notes_text))
                flat = norm(texts[e["page"] - 1])
                app = dict(app_base)
                if e["engine"]:
                    app["engine"] = e["engine"]
                d = drive_of(label) or (re.search(r"\b(?:" + MODEL_NAMES[line] + r") (AWD|4WD)\b", notes_text) or [None, None])[1]
                if d:
                    app["drive"] = d
                if guide and re.search(r"\b(?:" + MODEL_NAMES[line] + r")\s+Hybrid", label + " " + notes_text):
                    app["variant"] = "hybrid (as printed)"
                if f and norm(f.group(0)) in flat:
                    for job in jobs:
                        key = (line, job, app.get("engine"))
                        if key in explicit:
                            continue
                        explicit.add(key)
                        for occ, mi, k, t in (("FIRST", f.group("m1"), f.group("k1"), f.group("t1")),
                                              ("SUBSEQUENT", f.group("m2"), f.group("k2"), f.group("t2"))):
                            self.add(doc, job, "REPLACE", occurrence=occ, iv=interval(mi, k, t), applicability=app,
                                     quote=norm(f.group(0)), page=e["page"], lines=[line],
                                     locator=f"p.{e['page']} footnote of '{label}'")
                    continue
                mileage_only = bool(re.search(r"Performed based on the number of miles|Mileage only", notes_text, re.I))
                for job in jobs:
                    g = groups[(line, job, action, json.dumps(app, sort_keys=True), scope)]
                    g["NORMAL" if e["condition"] == "NORMAL" else "SEVERE"].setdefault(e["point"][0], (e, label))
                    if e["condition"] == "SEVERE":
                        g["in_severe"] = True
                    g["mileage_only"] = g.get("mileage_only", False) or mileage_only
        if not guide:
            explicit |= self.additional_notes(doc, texts, pages)
        for (line, job, action, app_json, scope), g in groups.items():
            app = json.loads(app_json)
            if (line, job, app.get("engine")) in explicit or (None, job, app.get("engine")) in explicit:
                continue
            for condition in ("NORMAL", "SEVERE"):
                if condition == "SEVERE" and not g["in_severe"]:
                    continue
                pts = dict(g["NORMAL"])
                if condition == "SEVERE":
                    for k, v in g["SEVERE"].items():
                        pts.setdefault(k, v)
                if not pts:
                    continue
                miles = sorted(pts)
                shape_m = from_points(miles)
                shape_t = from_points([pts[m][0]["point"][2] for m in miles])
                kms = [pts[m][0]["point"][1] for m in miles]
                shape_k = from_points(kms) if all(kms) else None
                if not shape_m or not shape_t or [o for o, _ in shape_m] != [o for o, _ in shape_t]:
                    self.gap(doc, job, f"'{pts[miles[0]][1]}' ({condition.lower()}) listed at {[int(m) for m in miles]} miles: "
                             "not a regular interval; not converted", lines=[line])
                    continue
                first_e, first_label = pts[miles[0]]
                step_mi = shape_m[-1][1]
                step_e, step_label = pts.get(step_mi, pts[miles[0]]) if step_mi in pts else pts[miles[0]]
                flat = norm(texts[step_e["page"] - 1])
                q = norm(step_e["text"]) if norm(step_e["text"]) in flat else norm(step_label)
                if q not in flat:
                    self.gap(doc, job, f"quote of '{step_label}' not found on p.{step_e['page']}; not used", lines=[line])
                    continue
                display, note = "FACT", None
                if guide and scope == "generic":
                    display = "SECONDARY_NOTE"
                    note = ("model-agnostic Service and Maintenance Guide: the item is printed for all models "
                            "('Equipment varies by model'); this model is not named for it")
                elif guide:
                    note = "model-agnostic Service and Maintenance Guide; the item names this model"
                cond_note = None
                if condition == "SEVERE":
                    cond_note = "severe operating conditions: standard points plus the additional severe items"
                for n, ((occ, mi), (_, mo)) in enumerate(zip(shape_m, shape_t)):
                    k = int(shape_k[n][1]) if shape_k else None
                    months = None if g.get("mileage_only") else mo
                    extra = "single point in the printed schedule" if len(miles) == 1 else None
                    self.add(doc, job, action, condition=condition, occurrence=occ, iv=interval(mi, k, months),
                             applicability=app, note="; ".join(x for x in (note, cond_note, extra) if x) or None,
                             quote=q, page=step_e["page"], lines=[line], display=display,
                             locator=f"p.{step_e['page']} '{step_label}' ({condition.lower()}) listed at "
                                     f"{', '.join(f'{int(m):,}' for m in miles)} miles")

    def additional_notes(self, doc, texts, pages) -> set:
        """'Additional information' after a point list: NOTE FOR ENGINE COOLANT (first/then) and
        NOTE FOR SPARK PLUGS ('Replace every 105,000 miles (168,000 km)'), for the engine section in force."""
        found = set()
        carried = None
        for index in range(max(pages[0] - 3, 0), min(pages[-1] + 3, len(texts))):
            text = texts[index]
            at = re.search(r"NOTE FOR (?:ENGINE COOLANT|SPARK PLUGS)", text)
            engine, carried = engine_at(text, at.start() if at else None, carried)
            if not at or index < pages[0]:
                continue
            flat = norm(text)
            app = {"edition": edition_of(doc), **({"engine": engine} if engine else {})}
            c = re.search(r"NOTE FOR ENGINE COOLANT\s*\*?:?\s*\(1\)\s*", flat)
            f = FIRST_THEN.search(flat, c.end()) if c else None
            if f:
                for occ, mi, k, t in (("FIRST", f.group("m1"), f.group("k1"), f.group("t1")),
                                      ("SUBSEQUENT", f.group("m2"), f.group("k2"), f.group("t2"))):
                    self.add(doc, "engine_coolant", "REPLACE", occurrence=occ, iv=interval(mi, k, t), applicability=app,
                             quote=f.group(0), page=index + 1, locator=f"p.{index + 1} Additional information: NOTE FOR ENGINE COOLANT")
                found.add((None, "engine_coolant", engine))
            sp = re.search(r"NOTE FOR SPARK PLUGS:?\s*\(1\)\s*(Replace every (?P<m>[\d,]+) miles \((?P<k>[\d,]+) km\))", flat)
            if sp:
                self.add(doc, "spark_plugs", "REPLACE", iv=interval(sp.group("m"), sp.group("k"), None), applicability=app,
                         quote=sp.group(1), page=index + 1, locator=f"p.{index + 1} Additional information: NOTE FOR SPARK PLUGS")
                found.add((None, "spark_plugs", engine))
        return found

    def guide_explanations(self, doc, texts):
        """Engine coolant first/subsequent and severe fluid intervals stated in a guide's
        'Explanation of scheduled maintenance items'."""
        app = {"edition": edition_of(doc)}
        for index, text in enumerate(texts[:20]):
            flat = norm(text)
            m = re.search(r"Engine Coolant\*? Replace coolant at the specified in ?terval\..*?"
                          r"(?P<q>The recommended ser ?vice interval of the factory-fill coolant is (?P<m1>[\d,]+) miles \((?P<k1>[\d,]+) km\) or "
                          r"(?P<y1>\d+) years, whichever comes first\. Subsequent replacement of Genuine (?:Nissan|Infiniti|INFINITI) Long Life "
                          r"Antifreeze/Coolant \(Blue\) should occur every (?P<m2>[\d,]+) miles \((?P<k2>[\d,]+) km\) or (?P<y2>\d+) years,? whichever comes first)",
                          flat.replace("￾", ""), re.I)
            if m and norm(m.group("q")) in flat:
                for occ, mi, k, y in (("FIRST", m.group("m1"), m.group("k1"), m.group("y1")),
                                      ("SUBSEQUENT", m.group("m2"), m.group("k2"), m.group("y2"))):
                    for line in doc["lines"]:
                        self.add(doc, "engine_coolant", "REPLACE", occurrence=occ, iv=interval(mi, k, int(y) * 12),
                                 applicability=app, quote=m.group("q"), page=index + 1, lines=[line], display="SECONDARY_NOTE",
                                 note="model-agnostic Service and Maintenance Guide: stated for the engine coolant of all models; "
                                      "this model is not named",
                                 locator=f"p.{index + 1} Explanation of scheduled maintenance items: Engine Coolant")
                return True
        return False

    def run(self):
        for doc in documents(self.make):
            if not doc["lines"]:
                continue
            try:
                texts = page_text(doc["sha256"])
            except FileNotFoundError:
                self.gap(doc, "schedule", "page text of the document not in the pagetext store")
                continue
            self.texts = getattr(self, "texts", {})
            self.texts[doc["key"]] = texts
            self.docs = getattr(self, "docs", {})
            self.docs[doc["key"]] = doc
            grid_pages = [i for i, t in enumerate(texts) if GRID_PAGE.search(t) and re.search(r"(?:miles|Miles)\s*\S\s*1,000", t)]
            lpages = list_pages(texts)
            guide = doc["doc_type"] == "maintenance_guide"
            if guide:
                if lpages:
                    self.points(doc, texts, lpages, guide=True)
                    self.guide_explanations(doc, texts)
                else:
                    self.gap(doc, "schedule", "guide without mileage-point pages")
                continue
            if grid_pages:
                self.grid(doc, texts, grid_pages)
                self.manual_texts(doc, texts, grid_pages[0], grid_pages[-1])
            elif lpages:
                self.points(doc, texts, lpages, guide=False)
                self.manual_texts(doc, texts, lpages[0], lpages[-1])
            else:
                ref = re.search(r"(Service and Maintenance Guide|Service & Maintenance Guide|Warranty and Maintenance Booklet|Maintenance Booklet)",
                                " ".join(texts))
                reason = ("the owner's manual prints no maintenance schedule"
                          + (f"; it refers to the separate \"{ref.group(1)}\"" if ref else ""))
                self.gap(doc, "schedule", reason)
        return self.finish()

    def finish(self) -> int:
        total = 0
        for slug, line in sorted(self.lines.items()):
            gens = generations_of(self.make, slug)
            raw = []
            conflicts = []
            for e in self.per_line.get(slug, []):
                doc = e["doc"]
                for year in self.years_of(doc, slug):
                    gen = gen_for(gens, year)
                    if gen is None:
                        continue
                    raw.append((year, gen, e))
            # one interval per scope and year: documents (or rows) that disagree -> not written
            by_scope = defaultdict(list)
            for year, gen, e in raw:
                key = (year, gen, e["job"], e["action"], e["condition"], e["occurrence"], json.dumps(e["applicability"], sort_keys=True))
                by_scope[key].append(e)
            items = []
            for key, es in by_scope.items():
                year, gen = key[0], key[1]
                variants = {(e["iv"].get("interval_km"), e["iv"].get("interval_months")) for e in es}
                if len(variants) > 1:
                    # a stated interval from a severe table / note wins over a derived one only within one document
                    self.gaps[slug].append({
                        "scope": f"{self.make}/{slug} MY{year} ({', '.join(sorted({e['doc']['key'] for e in es}))})",
                        "field": f"maintenance:{key[2]}",
                        "reason": f"{key[3]} {key[4]} {key[5]} {key[6]}: the documents/rows give different intervals "
                                  f"{sorted(variants, key=str)}; not written"})
                    continue
                # one item per scope and year: a FACT statement wins over a SECONDARY_NOTE one; the other
                # documents/rows that state the same interval are kept as further citations
                es = sorted(es, key=lambda e: (e["display"] != "FACT", e["doc"]["key"], e["page"]))
                e0 = es[0]
                it = item(slug, gen, year, e0["job"], e0["action"], condition=e0["condition"], occurrence=e0["occurrence"],
                          system="FIXED_INTERVAL", interval=e0["iv"], applicability=e0["applicability"], note=e0["note"],
                          source=e0["doc"]["key"], quote=e0["quote"], page=e0["page"], locator=e0["locator"][:480],
                          display_level=e0["display"], confidence="HIGH" if e0["display"] == "FACT" else "MEDIUM")
                for e in es[1:]:
                    if e["display"] != e0["display"]:
                        continue
                    cite = {"source": e["doc"]["key"], "quote": norm(e["quote"]), "pages": [e["page"]], "locator": e["locator"][:480]}
                    if cite not in it["cites"] and len(it["cites"]) < 4:
                        it["cites"].append(cite)
                items.append(it)
            # merge identical items of consecutive years (different quotes of one document collapse too)
            for it in items:
                pass
            merged = merge_years(items)
            used = {c["source"] for it in merged for c in it["cites"]}
            sources = {}
            for key in used:
                doc = self.docs[key]
                pages = {c_page for it in merged for c in it["cites"] if c["source"] == key for c_page in c["pages"]}
                stype = "OWNER_MANUAL_OFFICIAL" if doc["doc_type"] == "owners_manual" else "MAINTENANCE_SCHEDULE_OFFICIAL"
                sources[key] = pdf_source(key, doc["path"], doc["sha256"], doc["url"], doc["title"],
                                          f"{self.make} (manufacturer domain {doc['host']})", REGISTRY[self.make],
                                          doc["years"], pages, doc["retrieved_at"], source_type=stype)
            gaps = []
            seen_gaps = set()
            for g in self.gaps.get(slug, []):
                k = json.dumps(g, sort_keys=True)
                if k not in seen_gaps:
                    seen_gaps.add(k)
                    gaps.append(g)
            if not merged:
                gaps.append({"scope": f"{self.make}/{slug}", "field": "maintenance:schedule",
                             "reason": "no maintenance item could be built from the official documents on disk"})
            out = write(self.make, slug, NAME, sources, merged, gaps)
            years = sorted({y for it in merged for y in range(it["years"][0], it["years"][1] + 1)})
            print(f"{self.make}/{slug}: items {len(merged)}, years {years[0] if years else '-'}-{years[-1] if years else '-'} "
                  f"({len(years)}), sources {len(sources)}, gaps {len(gaps)} -> {out.relative_to(WORK.parent)}", flush=True)
            total += len(merged)
        return total


def self_check(make: str) -> tuple[int, int]:
    checked = problems = 0
    for path in sorted((WORK / make / "staging").glob(f"*/maintenance_{NAME}.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cache = {}
        for it in data["items"]:
            for c in it["cites"]:
                src = data["sources"][c["source"]]
                if src["sha256"] not in cache:
                    cache[src["sha256"]] = page_text(src["sha256"])
                for p in c["pages"]:
                    checked += 1
                    if norm(c["quote"]) not in norm(cache[src["sha256"]][p - 1]):
                        problems += 1
                        print("PROBLEM", path.parent.name, it["id"], c["source"], p, c["quote"][:80])
            if it["schedule_system"] == "FIXED_INTERVAL" and not (it["interval_km"] or it["interval_months"]):
                problems += 1
                print("PROBLEM no interval", it["id"])
            if it["interval_km"] is not None and not (1000 <= it["interval_km"] <= 400000):
                problems += 1
                print("PROBLEM interval_km", it["id"], it["interval_km"])
    return checked, problems


def main(argv: list[str]) -> int:
    makes = argv or ["nissan", "infiniti"]
    checked = problems = 0
    for make in makes:
        Builder(make).run()
        c, p = self_check(make)
        checked, problems = checked + c, problems + p
    print(f"checked {checked}, problems {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
