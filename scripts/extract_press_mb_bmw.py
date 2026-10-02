"""Extract specification facts from the US press spec documents of Mercedes-Benz USA
(media.mbusa.com, HTML spec pages / Quick Reference Guides) and BMW Group USA
(press.bmwgroup.com, "Technical Specifications" PDFs) collected by collect_press_mb_bmw.py.

Writes one JSON per document to data_work/<make>/extracted/press-<host-short>-<line>-<year>-<sha8>.json
in the format of data_work/_shared/press/FORMAT.md. Everything is read from the stored files:
labels and values are paired from the document's own table structure (HTML table rows/cells;
PDF layout columns), every fact quotes the stored page text verbatim, rows that cannot be read
unambiguously go to `review`. Numbers are parsed, units are never converted.

Run:
  uv run --no-project --with httpx --with beautifulsoup4 --with pdfplumber --with pypdfium2 \
      python scripts/extract_press_mb_bmw.py [--host mb|bmw] [--verify]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from us_tech_common import RAW_ROOT, WORK, read_maybe_gz  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

import collect_press_mb_bmw as col  # noqa: E402

EXTRACTOR = "press-mb_bmw-1"
HOSTS = {
    "mb": {"host": col.MB_HOST, "short": "mbusa", "make": "mercedes-benz",
           "publisher": "Mercedes-Benz USA Media Newsroom (media.mbusa.com)"},
    "bmw": {"host": col.BMW_HOST, "short": "bmwgroup", "make": "bmw",
            "publisher": "BMW Group PressClub USA (press.bmwgroup.com/usa)"},
}


def norm(text: str) -> str:
    return " ".join(str(text).split())


NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
NUM_RE = re.compile(NUM)
NA_RE = re.compile(r"^(n/?a|n\.a|tba|tbd|tbc|-+|–|—|none|not available|na)\.?$", re.I)


def to_number(text: str):
    value = float(text.replace(",", ""))
    return int(value) if value.is_integer() and "." not in text else value


# --------------------------------------------------------------------------- cell segments
def split_segments(text: str) -> list[tuple[str | None, str, str]]:
    """Split a value cell into (label, value_text, kind) segments.

    "3,417 (4MATIC: 3,594)"          -> (None, "3,417", main), ("4MATIC", "3,594", label)
    "83.6” (75.6” w/o mirrors)"      -> (None, "83.6”", main), ("w/o mirrors", "75.6”", qualifier)
    "Combined system: 576 hp Engine only: 442 hp" -> ("Combined system", "576 hp", label), ...
    A parenthesis without a number ("(Cast)", "(est.)") stays part of the main text.
    """
    text = norm(text)
    out: list[tuple[str | None, str, str]] = []
    parens = []

    def keep(m):
        inner = m.group(1).strip()
        if NUM_RE.search(inner):
            parens.append(inner)
            return " "
        return m.group(0)

    main = norm(re.sub(r"\(([^()]*)\)", keep, text))
    # "Label: value" pieces; a label is not a bare number ("9: 1" is a ratio, not a label)
    labelled = list(re.finditer(r"(?:^|(?<=\s))(?![\d,.]+\s*(?::|\s|$))([A-Z0-9][A-Za-z0-9 .+/&*-]{0,40}?):\s*", main))
    qualified = QUALIFIED_LIST.fullmatch(main) if not labelled else None
    paren_qualified = PAREN_QUALIFIED_LIST.fullmatch(main) if not labelled and not qualified else None
    if labelled:
        head = main[:labelled[0].start()].strip().rstrip("/").strip()
        if head:
            out.append((None, head, "main"))  # "3,594 / 4MATIC: 3,770"
        for i, m in enumerate(labelled):
            end = labelled[i + 1].start() if i + 1 < len(labelled) else len(main)
            out.append((m.group(1).strip(), main[m.end():end].strip().rstrip("/").strip(), "label"))
    elif qualified:
        # '80" with mirrors / 76.2" without mirrors', '208 gas / 80 electric / 275 combined'
        for part in re.split(r"\s+/\s+", main):
            m = QUALIFIED_PART.fullmatch(part)
            out.append((m.group(2).strip(), m.group(1).strip(), "qualifier"))
    elif paren_qualified:
        # '58.4" (Luxury Styling) / 57.8" (Sport Styling)'
        for m in PAREN_QUALIFIED_PART.finditer(main):
            out.append((m.group(2).strip(), m.group(1).strip(), "qualifier"))
    elif main:
        out.append((None, main, "main"))
    for inner in parens:
        m = re.match(r"^(?![\d,.]+\s*(?::|\s|$))([A-Za-z0-9][^:]{0,40}):\s*(.+)$", inner)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip(), "label"))
            continue
        m = re.match(rf"^((?:{NUM})\s*{UNIT_TAIL})\s*(.*)$", inner)
        if m and m.group(2):
            out.append((m.group(2).strip(), m.group(1).strip(), "qualifier"))
        else:
            out.append((None, inner, "extra"))
    return out


UNIT_TAIL = r"(?:[”\"']|in\.?|inches|ft\.?|lbs?\.?|cu\.? ?ft\.?|gal\.?|mm|hp|lb-?ft\.?)?"
QUALIFIED_PART = re.compile(rf"((?:{NUM})\s*{UNIT_TAIL})\s+([A-Za-z][A-Za-z ./-]{{1,30}})")
QUALIFIED_LIST = re.compile(rf"(?:(?:{NUM})\s*{UNIT_TAIL}\s+[A-Za-z][A-Za-z ./-]{{1,30}}?)"
                            rf"(?:\s+/\s+(?:{NUM})\s*{UNIT_TAIL}\s+[A-Za-z][A-Za-z ./-]{{1,30}}?)+")
PAREN_QUALIFIED_PART = re.compile(rf"((?:{NUM})\s*{UNIT_TAIL})\s*\(([A-Za-z][A-Za-z ./-]{{1,30}})\)")
PAREN_QUALIFIED_LIST = re.compile(rf"(?:(?:{NUM})\s*{UNIT_TAIL}\s*\([A-Za-z][A-Za-z ./-]{{1,30}}\))"
                                  rf"(?:\s*/?\s*(?:{NUM})\s*{UNIT_TAIL}\s*\([A-Za-z][A-Za-z ./-]{{1,30}}\))+")


def numbers(text: str) -> list[str]:
    return NUM_RE.findall(text)


# --------------------------------------------------------------------------- row rules
FRONT_REAR = re.compile(r"front\s*/\s*rear|front and rear", re.I)
INTERIOR = re.compile(r"interior|cargo|trunk|load|luggage|cabin|head ?room|leg ?room|shoulder|hip", re.I)


def unit_of(label: str, unit: str, value: str) -> str:
    return f"{label} {unit} {value}".lower()


class Rule:
    def __init__(self, name, test, kind, keys, unit_ok=None, unit_bad=None):
        self.name, self.test, self.kind, self.keys = name, test, kind, keys
        self.unit_ok, self.unit_bad = unit_ok, unit_bad


def _l(pattern):
    rx = re.compile(pattern, re.I)
    return lambda label, section: bool(rx.search(label))


def _s(section_pattern, label_pattern):
    srx, lrx = re.compile(section_pattern, re.I), re.compile(label_pattern, re.I)
    return lambda label, section: bool(srx.search(section)) and bool(lrx.search(label))


IN_BAD = r"^(?!.*\binch\b)(?!.*\bin\b).*(\bmm\b|\bcm\b|\(m\)|\bmeters?\b)"
KW_ONLY = r"^(?!.*\bhp\b).*\bkw\b"  # output given in kW only
NM_ONLY = r"^(?!.*\blbs?\b)(?!.*lb-?\s?ft).*\bnm\b"  # torque given in Nm only
RULES = [
    Rule("dims3", _l(r"length\s*/\s*width\s*/\s*height"), "triple", ["length_in", "width_in", "height_in"],
         unit_bad=IN_BAD),
    Rule("doors_seats", _l(r"doors\s*/\s*seats"), "second", ["seats"]),
    Rule("track_pair", lambda l, s: bool(re.search(r"^track", l, re.I) and FRONT_REAR.search(l)), "pair",
         ["track_front_in", "track_rear_in"], unit_bad=IN_BAD),
    Rule("track_front", lambda l, s: bool(re.search(r"^(front track|track,? front)", l, re.I))
         or bool(re.search(r"^track", s, re.I) and re.match(r"^front$", l, re.I)), "num", ["track_front_in"],
         unit_bad=IN_BAD),
    Rule("track_rear", lambda l, s: bool(re.search(r"^(rear track|track,? rear)", l, re.I))
         or bool(re.search(r"^track", s, re.I) and re.match(r"^rear$", l, re.I)), "num", ["track_rear_in"],
         unit_bad=IN_BAD),
    Rule("length", lambda l, s: bool(re.match(r"^(overall |exterior |veh\.? |vehicle )?length\b", l, re.I)) and not INTERIOR.search(l + " " + s),
         "num", ["length_in"], unit_bad=IN_BAD),
    Rule("width", lambda l, s: bool(re.match(r"^(overall |exterior |veh\.? |vehicle )?width\b", l, re.I)) and not INTERIOR.search(l + " " + s),
         "num", ["width_in"], unit_bad=IN_BAD),
    Rule("height", lambda l, s: bool(re.match(r"^(overall |exterior |veh\.? |vehicle )?height\b", l, re.I)) and not INTERIOR.search(l + " " + s),
         "num", ["height_in"], unit_bad=IN_BAD),
    Rule("wheelbase", _l(r"^wheelbase"), "num", ["wheelbase_in"], unit_bad=IN_BAD),
    Rule("ground", _l(r"ground clearance"), "num", ["ground_clearance_in"], unit_bad=IN_BAD),
    Rule("curb", _l(r"curb weight|\bcurb\b"), "num", ["curb_weight_lb"], unit_bad=r"\bkg\b"),
    Rule("cargo_pair", lambda l, s: bool(re.search(r"cargo|trunk|luggage", l, re.I))
         and bool(re.search(r"/", l)) and bool(re.search(r"down|fold|max", l, re.I)), "pair",
         ["cargo_cu_ft", "cargo_max_cu_ft"], unit_bad=r"\bliters?\b|\blitres?\b|\(l\)"),
    Rule("cargo_max", lambda l, s: bool(re.search(r"cargo|trunk|luggage", l, re.I))
         and bool(re.search(r"max|folded|seats down", l, re.I)), "num", ["cargo_max_cu_ft"],
         unit_bad=r"\bliters?\b|\blitres?\b|\(l\)"),
    Rule("cargo", _l(r"^(press )?(cargo|trunk|luggage)( (volume|capacity|space|area))?\b|trunk volume|cargo (volume|capacity)"),
         "num", ["cargo_cu_ft"], unit_bad=r"\bliters?\b|\blitres?\b|\(l\)"),
    Rule("passenger_volume", _l(r"passenger volume"), "num", ["passenger_volume_cu_ft"]),
    Rule("fuel_tank", _l(r"fuel tank|fuel capacity|^(us )?tank capacity"), "num", ["fuel_tank_gal"],
         unit_bad=r"\bliters?\b|\blitres?\b|\(l\)|\bl\b"),
    Rule("seats", _l(r"^(seating capacity|seats|number of seats|no\.? of seats|seating)$"), "num", ["seats"]),
    Rule("towing", _l(r"towing"), "num", ["towing_lb"], unit_bad=r"\bkg\b"),
    Rule("turning", _l(r"turning (circle|diameter)"), "num", ["turning_circle_ft"], unit_bad=r"\(m\)|\bm\b|\bmeters?\b"),
    Rule("front_susp", lambda l, s: bool(re.search(r"front suspension|suspension,? front", l, re.I))
         or (bool(re.search(r"suspension", s, re.I)) and bool(re.match(r"^front( axle)?$", l, re.I))), "text",
         ["front_suspension"]),
    Rule("rear_susp", lambda l, s: bool(re.search(r"rear suspension|suspension,? rear", l, re.I))
         or (bool(re.search(r"suspension", s, re.I)) and bool(re.match(r"^rear( axle)?$", l, re.I))), "text",
         ["rear_suspension"]),
    Rule("front_brakes", lambda l, s: bool(re.search(r"^(front brakes?|brakes?,? front)", l, re.I))
         or (bool(re.search(r"brake", s, re.I)) and bool(re.match(r"^front$", l, re.I))), "text", ["front_brakes"]),
    Rule("rear_brakes", lambda l, s: bool(re.search(r"^(rear brakes?|brakes?,? rear)", l, re.I))
         or (bool(re.search(r"brake", s, re.I)) and bool(re.match(r"^rear$", l, re.I))), "text", ["rear_brakes"]),
    Rule("steering_type_ratio", _l(r"^steering type\s*/\s*steering ratio"), "text_first", ["steering"]),
    Rule("steering", lambda l, s: bool(re.match(r"^(steering( system| type)?|power[- ]steering)$", l, re.I))
         or (bool(re.match(r"^steering", s, re.I)) and bool(re.match(r"^(type|steering type|system)$", l, re.I))),
         "text", ["steering"]),
    Rule("tires", lambda l, s: bool(re.match(r"^(standard |front |rear )?(tires|tyres|tire size)\b", l, re.I))
         or (bool(re.search(r"tires|tyres", s, re.I)) and bool(re.match(r"^(front|rear|standard|front/rear)$", l, re.I))),
         "tires", ["tires"]),
    Rule("wheels", lambda l, s: bool(re.match(r"^(standard |front |rear )?(wheels|rims)\b", l, re.I))
         or (bool(re.search(r"wheels|rims", s, re.I)) and bool(re.match(r"^(front|rear|standard|front/rear)$", l, re.I))),
         "wheel", ["wheel_size_in"]),
    Rule("displacement", _l(r"^displacement"), "num", ["engine_displacement_cc"], unit_ok=r"\bcc\b|cm3|cm³|\(cc\)",
         unit_bad=r"liters?|litres?|\bl\b|cu\.? ?in"),
    Rule("bore_stroke", _l(r"bore\s*(x|/)\s*stroke|stroke\s*(x|/)\s*bore"), "bore_stroke", ["bore_stroke"]),
    Rule("compression", _l(r"^compression( ratio| rate)?$|^compression ratio\b"), "ratio", ["compression_ratio"]),
    Rule("engine_desc", lambda l, s: bool(re.match(r"^(engine( type)?|type of engine|engine configuration|engine description)$", l, re.I))
         or (bool(re.match(r"^engine$", s, re.I)) and bool(re.match(r"^type$", l, re.I))), "text", ["engine_description"]),
    Rule("valvetrain", lambda l, s: bool(re.search(r"valve ?train|^valves?\b|valve (gear|control|actuation)", l, re.I))
         and not re.search(r"p\.? ?cyl|per cyl", l, re.I), "text", ["valvetrain"]),
    Rule("injection", _l(r"fuel (system|injection|delivery|induction)|^injection|mixture (formation|preparation)"),
         "text", ["injection"]),
    Rule("system_power", _l(r"(system|combined|total)\s*(output|power|horsepower|hp)"), "power", ["system_power_hp"],
         unit_bad=r"\bkw\b"),
    Rule("electric_motor", _l(r"electric motor|e-?motor|e-engine|electric (drive|machine)|\bisg\b|eq boost|"
                              r"integrated starter"),
         "text", ["electric_motor"]),
    Rule("performance", _l(r"^performance$"), "perf", ["power_hp"]),
    Rule("combustion_power", _l(r"^(combustion |internal combustion )?engine (output|power|horsepower)"), "power",
         ["power_hp"], unit_bad=KW_ONLY),
    Rule("combustion_torque", _l(r"^(combustion |internal combustion )?engine torque"), "torque", ["torque_lb_ft"],
         unit_bad=NM_ONLY),
    Rule("power", lambda l, s: bool(re.match(r"^(horsepower|(max(imum)?|rated|peak|engine|net) (output|power|horsepower)|"
                                             r"output|power|net power|hp)\b", l, re.I))
         and not re.search(r"electric|e-engine|e-motor|battery|charg|system|combined|weight|steering|per\b|"
                           r"specific", l, re.I), "power", ["power_hp"],
         unit_bad=KW_ONLY),
    Rule("torque", lambda l, s: bool(re.match(r"^((max(imum)?|peak|engine|net) )?torque\b", l, re.I))
         and not re.search(r"electric|system|combined|split|distribution|vectoring|converter", l, re.I), "torque",
         ["torque_lb_ft"], unit_bad=NM_ONLY),
    Rule("transmission", lambda l, s: bool(re.match(r"^(transmission( type)?|type of transmission|gearbox)$", l, re.I))
         or (bool(re.match(r"^transmission", s, re.I)) and bool(re.match(r"^(type|transmission type)$", l, re.I))),
         "text", ["transmission_description"]),
]

POWER_RE = re.compile(rf"^(?P<v>{NUM})\s*(?:hp|horsepower|bhp)?\s*(?:@|at|/)?\s*(?P<rpm>(?:{NUM})(?:\s*[-–—]\s*(?:{NUM}))?)?\s*(?:rpm)?",
                      re.I)
TORQUE_RE = re.compile(rf"^(?P<v>{NUM})\s*(?:lb\.?-?\s?ft\.?|lb-ft|lbs?\.?-ft\.?)?\s*(?:@|at|/)?\s*"
                       rf"(?P<rpm>(?:{NUM})(?:\s*[-–—]\s*(?:{NUM}))?)?\s*(?:rpm)?", re.I)
TIRE_RE = re.compile(r"\b(?:P|LT)?\d{3}\s*/\s*\d{2}\s*(?:Z?R|-)\s*F?\s*\d{2}(?:\.\d)?(?:\s*(?:\d{2,3}(?:/\d{2,3})?\s*[A-Z]{1,2}\b|XL|RF|RSC|SSR|AS|MO|\*|\(?run-?flat\)?))*",
                     re.I)


RULES_BY_NAME = {rule.name: rule for rule in RULES}
# labels published letter-spaced ("W i dt h w / m i r r o r s ( w / o m i rr or s )") are matched
# on their compacted form
COMPACT_RULES = [("width", "width"), ("length", "length"), ("height", "height"), ("wheelbase", "wheelbase"),
                 ("curbweight", "curb"), ("groundclearance", "ground"), ("turningcircle", "turning"),
                 ("fueltank", "fuel_tank")]


def rule_for(label: str, section: str) -> Rule | None:
    for rule in RULES:
        if rule.test(label, section):
            return rule
    tokens = label.split()
    if len(tokens) >= 4 and sum(len(t) <= 2 for t in tokens) >= 0.6 * len(tokens):
        compact = re.sub(r"\s+", "", label).lower()
        for prefix, name in COMPACT_RULES:
            if compact.startswith(prefix) and not INTERIOR.search(compact):
                return RULES_BY_NAME[name]
    return None


HP_RE = re.compile(rf"({NUM})\s*hp\b(?:\s*@\s*((?:{NUM})(?:\s*[-–—]\s*(?:{NUM}))?)\s*(?:rpm)?)?", re.I)
LBFT_RE = re.compile(rf"({NUM})\s*lb\.?-?\s?ft\.?(?:\s*of torque)?(?:\s*@\s*((?:{NUM})(?:\s*[-–—]\s*(?:{NUM}))?)\s*(?:rpm)?)?",
                     re.I)


def apply_rule(rule: Rule, label: str, section: str, unit: str, cell: str) -> tuple[list[dict], list[str]]:
    """Facts (key, value, sub-label, qualifier, segment) from one value cell; or review reasons."""
    out: list[dict] = []
    reasons: list[str] = []
    context = unit_of(label, unit, cell)
    if rule.unit_bad and re.search(rule.unit_bad, f"{label} {unit}".lower()) and not (
            rule.unit_ok and re.search(rule.unit_ok, f"{label} {unit}".lower())):
        return [], []  # value given in a unit the key does not take (e.g. mm, liters): not extracted
    if rule.unit_ok and not re.search(rule.unit_ok, context):
        return [], []
    segments = split_segments(cell)
    label_paren = re.search(r"\(([^()]*[A-Za-z][^()]*)\)\s*$", label)
    for sub, text, kind in segments:
        if kind == "extra":
            # a bare number in parentheses belongs to the parenthesised part of the label:
            # "Width w/ mirrors (w/o mirrors)": "81.5” (76.9”)"
            if label_paren and rule.kind == "num" and len(numbers(text)) == 1 and not re.search(r"[A-Za-z]{3,}", text):
                out.append({"key": rule.keys[0], "value": to_number(numbers(text)[0]), "engine": None,
                            "qualifier": "value in parentheses", "segment": f"({text})"})
            continue
        if not text or NA_RE.match(text.strip()):
            continue
        sub_engine = sub if kind == "label" else None
        qualifier = sub if kind == "qualifier" else None
        if kind == "label" and re.match(r"^(standard|optional|opt\.?|std\.?|available|base)$", sub, re.I):
            sub_engine, qualifier = None, sub
        if kind == "label" and rule.kind == "perf" and re.search(r"engine|combustion", sub, re.I):
            sub_engine, qualifier = None, sub
        keys = rule.keys
        if rule.kind == "perf" and kind == "label" and re.search(r"electric|motor|isg|eq boost|e-motor", sub, re.I):
            out.append({"key": "electric_motor", "value": norm(text), "engine": None, "qualifier": sub,
                        "segment": f"{sub}: {text}"})
            continue
        if rule.kind == "perf":
            hps, tqs = HP_RE.findall(text), LBFT_RE.findall(text)
            if len(hps) > 1 or len(tqs) > 1:
                reasons.append(f"several outputs in one cell: {text!r}")
                continue
            segment = text if kind != "label" else f"{sub}: {text}"
            for (v, rpm), key, rkey in [(h, "power_hp", "power_rpm") for h in hps] + \
                                        [(t, "torque_lb_ft", "torque_rpm") for t in tqs]:
                out.append({"key": key, "value": to_number(v), "engine": sub_engine, "qualifier": qualifier,
                            "segment": segment})
                if rpm:
                    out.append({"key": rkey, "value": norm(rpm), "engine": sub_engine, "qualifier": qualifier,
                                "segment": segment})
            continue
        # sub-labels inside power/torque cells of hybrids ("Combined system: ...", "Engine only: ...")
        if sub and kind in ("label", "qualifier") and rule.kind in ("power", "torque"):
            if re.search(r"combined|system|total", sub, re.I):
                if rule.kind == "torque":
                    continue
                keys = ["system_power_hp"]
                sub_engine = None
                qualifier = sub
            elif re.search(r"electric|motor|e-motor|isg", sub, re.I):
                published = f"{sub}: {text}" if kind == "label" else f"{text} {sub}"
                out.append({"key": "electric_motor", "value": norm(text) if kind == "label" else norm(published),
                            "engine": None, "qualifier": sub, "segment": published})
                continue
            elif re.search(r"engine", sub, re.I):
                sub_engine = None
                qualifier = sub
        kind_rule = rule.kind if keys == rule.keys else "power"
        segment = text if kind != "label" else f"{sub}: {text}"
        if kind_rule == "text":
            out.append({"key": keys[0], "value": norm(text), "engine": sub_engine, "qualifier": qualifier,
                        "segment": segment})
        elif kind_rule == "text_first":
            # "Steering type / Steering ratio": "rack-and-pinion / 15.2" -> the type
            first = re.split(r"\s+/\s+", text.strip())[0]
            if first and not NUM_RE.fullmatch(first):
                out.append({"key": keys[0], "value": norm(first), "engine": sub_engine, "qualifier": qualifier,
                            "segment": segment})
        elif kind_rule == "num":
            nums = numbers(text)
            if not nums:
                continue
            if len(nums) > 1 and not re.search(r"^\s*(?:" + NUM + r")\s*(?:[”\"']|in\.?|ft\.?|lbs?\.?|cu\.? ?ft\.?|gal\.?|"
                                               r"inches|feet|pounds|gallons)?\s*$", text):
                reasons.append(f"several numbers without labels: {text!r}")
                continue
            trailing = re.match(rf"^(?:{NUM})\s*{UNIT_TAIL}\s+([A-Za-z][A-Za-z ./-]{{1,30}})$", text.strip())
            if trailing and kind == "main" and not re.match(r"^(est|estimated|approx)", trailing.group(1), re.I):
                qualifier = trailing.group(1).strip()  # '80.4” w/ mirrors'
            out.append({"key": keys[0], "value": to_number(nums[0]), "engine": sub_engine, "qualifier": qualifier,
                        "segment": segment})
        elif kind_rule in ("pair", "triple", "second"):
            text = re.sub(r"^\s*/\s*", "", text)
            parts = [p.strip() for p in re.split(r"\s*/\s*", re.sub(r"\bn/a\b", "n.a.", text, flags=re.I))]
            want = {"pair": 2, "triple": 3, "second": 2}[kind_rule]
            if kind == "qualifier" and kind_rule == "pair" and len(parts) == 1 and len(numbers(text)) == 1:
                # "62.7 front / 63.0 rear", "15.4 seats up / 50.0 seats down"
                first = re.match(r"^(front|seats? up|rear seats? up|up)\b", sub, re.I)
                second = re.match(r"^(rear|seats? down|rear seats? down|down|folded|max)", sub, re.I)
                if first or second:
                    out.append({"key": keys[0] if first else keys[1], "value": to_number(numbers(text)[0]),
                                "engine": sub_engine, "qualifier": sub, "segment": f"{text} {sub}"})
                    continue
            if len(parts) != want or not all(NUM_RE.search(p) or NA_RE.match(p) for p in parts):
                if len(parts) == 1 and kind_rule == "pair" and len(numbers(text)) == 1:
                    reasons.append(f"one value for a two-value label: {text!r}")
                else:
                    reasons.append(f"cannot split {text!r} into {want} values")
                continue
            values = [numbers(p) for p in parts]
            if any(len(v) != 1 for v in values):
                if not all(NA_RE.match(p) or len(numbers(p)) == 1 for p in parts):
                    reasons.append(f"cannot split {text!r} into {want} values")
                    continue
            if kind_rule == "second":
                out.append({"key": keys[0], "value": to_number(values[1][0]), "engine": sub_engine,
                            "qualifier": qualifier, "segment": segment})
                continue
            for key, part, v in zip(keys, parts, values):
                if v:
                    out.append({"key": key, "value": to_number(v[0]), "engine": sub_engine, "qualifier": qualifier,
                                "segment": segment})
        elif kind_rule in ("power", "torque") and not re.search(r"\d", text):
            continue
        elif kind_rule == "power":
            m = POWER_RE.match(text.strip())
            if not m:
                reasons.append(f"power value not readable: {text!r}")
                continue
            rest = text.strip()[m.end():].strip()
            if NUM_RE.search(rest) and not re.match(r"^\(?(est|estimated|prelim)", rest, re.I):
                reasons.append(f"several numbers in power cell: {text!r}")
                continue
            out.append({"key": keys[0], "value": to_number(m.group("v")), "engine": sub_engine,
                        "qualifier": qualifier, "segment": segment})
            if m.group("rpm") and keys[0] == "power_hp":
                out.append({"key": "power_rpm", "value": norm(m.group("rpm")), "engine": sub_engine,
                            "qualifier": qualifier, "segment": segment})
        elif kind_rule == "torque":
            m = TORQUE_RE.match(text.strip())
            if not m:
                reasons.append(f"torque value not readable: {text!r}")
                continue
            rest = text.strip()[m.end():].strip()
            if NUM_RE.search(rest):
                reasons.append(f"several numbers in torque cell: {text!r}")
                continue
            out.append({"key": "torque_lb_ft", "value": to_number(m.group("v")), "engine": sub_engine,
                        "qualifier": qualifier, "segment": segment})
            if m.group("rpm"):
                out.append({"key": "torque_rpm", "value": norm(m.group("rpm")), "engine": sub_engine,
                            "qualifier": qualifier, "segment": segment})
        elif kind_rule == "ratio":
            m = re.match(rf"^({NUM})\s*(:\s*1)?$", text.strip())
            if not m:
                reasons.append(f"compression ratio not readable: {text!r}")
                continue
            value = norm(text) if m.group(2) else f"{m.group(1)}:1" if re.search(r":\s*1", f"{label} {unit}") else None
            if value is None:
                reasons.append(f"compression ratio without ':1': {text!r}")
                continue
            out.append({"key": "compression_ratio", "value": value, "engine": sub_engine, "qualifier": qualifier,
                        "segment": segment})
        elif kind_rule == "tires":
            sizes = [norm(t.group(0)) for t in TIRE_RE.finditer(text)]
            if not sizes:
                continue
            for size in sizes:
                out.append({"key": "tires", "value": size, "engine": sub_engine, "qualifier": qualifier,
                            "segment": segment})
        elif kind_rule == "wheel":
            m = re.search(rf"(?:{NUM})\s*J?\s*[x×]\s*({NUM})", text) or re.search(rf"({NUM})\s*(?:-inch|”|\"|in\b)", text)
            if m:
                out.append({"key": "wheel_size_in", "value": to_number(m.group(1)), "engine": sub_engine,
                            "qualifier": qualifier, "segment": segment})
        elif kind_rule == "bore_stroke":
            parts = [p.strip() for p in re.split(r"\s*(?:/|x|×)\s*", text)]
            if len(parts) != 2 or not all(re.fullmatch(NUM, p) for p in parts):
                reasons.append(f"bore/stroke not readable: {text!r}")
                continue
            first_is_stroke = bool(re.search(r"stroke\s*(x|/)\s*bore", label, re.I))
            bore, stroke = (parts[1], parts[0]) if first_is_stroke else (parts[0], parts[1])
            unitlabel = f"{label} {unit}".lower()
            key = "bore_stroke_mm" if re.search(r"\bmm\b", unitlabel) else "bore_stroke_in" if re.search(
                r"\bin\b|inch", unitlabel) else None
            if key is None:
                reasons.append(f"bore/stroke without unit: {text!r}")
                continue
            out.append({"key": key, "value": f"{bore} x {stroke}", "engine": sub_engine, "qualifier": qualifier,
                        "segment": segment})
    return out, reasons


# --------------------------------------------------------------------------- documents
def make_fact(key, value, page, quote, original, engine_text, row):
    return {"key": key, "value": value, "page": page, "quote": quote, "original": original,
            "engine_text": engine_text, "row": row}


def combine_engine(header: str | None, sub: str | None) -> str | None:
    if header and sub:
        return f"{header} / {sub}"
    return header or sub


def row_name(label: str, section: str, qualifier: str | None) -> str:
    generic = re.match(r"^(front|rear|type|standard|front/rear|optional|ratio)$", label, re.I)
    name = f"{section}: {label}" if section and generic else label
    return f"{name} ({qualifier})" if qualifier else name


# ---- HTML tables (media.mbusa.com spec pages / QRGs; PressClub USA release texts)
def _int(value) -> int:
    try:
        return max(1, int(str(value).strip() or 1))
    except ValueError:
        return 1


def html_container(raw_html: str, host_key: str):
    """The element holding the release text: media.mbusa.com news body / PressClub div#article-text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(raw_html, "html.parser")
    if host_key == "mb":
        panel = soup.find(id="news-release-panel") or soup
        article = panel.find("article") or panel
        return article.find("div", class_="news-body-editor")
    return soup.find(id="article-text")


def table_rows(container):
    """(table_no, cells, is_bold_first, colspans, own_cells) for each row of the tables in `container`.

    `cells` repeats a cell spanning several rows (rowspan) in the rows below it, so that a
    label such as "Performance" (rowspan=2) labels both rows; `own_cells` are the cells the row
    itself contains (its line in the page text)."""
    if container is None:
        return []
    out = []
    for t_no, table in enumerate(container.find_all("table")):
        if table.find_parent("table") is not None:
            continue
        pending: dict[int, list] = {}  # column -> [rows left, text]
        for tr in table.find_all("tr"):
            if tr.find_parent("table") is not table:
                continue
            tds = tr.find_all(["td", "th"], recursive=False)
            own = [col.cell_text(c) for c in tds]
            cells: list[str] = []
            spans: list[int] = []
            column = 0
            queue = list(zip(tds, own))
            while queue or any(c >= column for c in pending):
                if column in pending:
                    left, text = pending[column]
                    cells.append(text)
                    spans.append(1)
                    if left <= 1:
                        del pending[column]
                    else:
                        pending[column][0] = left - 1
                    column += 1
                    continue
                if not queue:
                    break
                td, text = queue.pop(0)
                span = _int(td.get("colspan"))
                cells.append(text)
                spans.append(span)
                rowspan = _int(td.get("rowspan"))
                if rowspan > 1:
                    pending[column] = [rowspan - 1, text]
                for _ in range(span - 1):  # a cell spanning columns: its text in the first, empty after
                    cells.append("")
                    spans.append(0)
                column += span
            strong = tds[0].find(["strong", "b"]) if tds else None
            bold = bool(strong) and norm(strong.get_text(" ")) == own[0] and bool(own[0])
            out.append((t_no, cells, bold, spans, own))
    return out


UNIT_CELL = re.compile(r"^(--|—|-|inches|inch|in\.?|feet|ft\.?|lbs?\.?|pounds|gallons|gal\.?|cu\.? ?ft\.?|ft³|ft3|cm³|"
                       r"cm3|cc|ccm|mm|hp|hp\s*@\s*rpm|lbs?-?\s?ft\.?|ft\.?\s?lbs?\.?|lbs?-?ft\s*@\s*rpm|mph|sec\.?|s|:1|kWh|kW|miles|mi|%|rpm|"
                       r"liters?|kg|V|Ah|in/mm|mm/in)$", re.I)
# PressClub USA tables can carry columns of models that are not registry lines (BMW i4/i5/i7/iX)
BMW_SKIP_COLUMN = re.compile(r"^(BMW\s+)?(i[3-8]|iX\d?)\b", re.I)


def parse_html_tables(rows, page_text: str, skip_column: re.Pattern | None = None
                      ) -> tuple[list[dict], list[dict]]:
    """Facts from specification tables: two-column label/value tables with section rows, or
    tables with a heading row (empty first cell) naming one column per model; an optional unit
    column after the label."""
    facts: list[dict] = []
    review: list[dict] = []
    norm_page = norm(page_text)
    section = ""
    headers: list[str] | None = None
    header_table = None
    unit_col = False
    pending_bore = None
    first_row_of_table = {}
    skipped_cols: set[str] = set()
    metric_tables = metric_only_tables(rows)
    for t_no in sorted(metric_tables):
        review.append({"page": 1, "row": "", "reason": f"table {t_no + 1} gives metric (European) data only: not used"})
    for t_no, cells, bold, spans, own in rows:
        nonempty = [c for c in cells if c]
        if not nonempty or t_no in metric_tables:
            continue
        first = first_row_of_table.setdefault(t_no, True)
        first_row_of_table[t_no] = False
        if headers is not None and t_no != header_table and len(cells) - 1 != len(headers):
            headers, unit_col = None, False
        # column heading row: empty first cell, named columns (one named column only as a table's first row)
        if not cells[0] and (len(nonempty) >= 2 or first):
            headers = cells[1:]
            header_table = t_no
            unit_col = len(headers) > 1 and not headers[0]
            if unit_col:
                headers = headers[1:]
            continue
        if len(cells) == 1 or (len(nonempty) == 1 and cells[0] and (spans[0] > 1 or bold or len(cells) == 1)):
            section = cells[0] if cells[0] else section
            continue
        label = cells[0]
        values = cells[1:]
        if headers is None:
            # no column headings: the cells of the row as published (no colspan fillers)
            values = [c for c, sp in zip(cells[1:], spans[1:]) if sp != 0]
        unit = ""
        if values and (unit_col or (len(values) >= 2 and UNIT_CELL.match(values[0]))):
            unit, values = values[0], values[1:]
            if unit in ("--", "—", "-"):
                unit = ""
        quote = norm("\t".join(own))
        if quote not in norm_page:
            review.append({"page": 1, "row": label, "reason": "row text not found in page text"})
            continue
        # Bore and Stroke on two adjacent rows ("Bore (in / mm) 3.27 / 83.0", "Stroke (in / mm) ...")
        if re.match(r"^bore\b", label, re.I) and not re.search(r"stroke", label, re.I):
            pending_bore = (label, unit, values, quote)
            continue
        if re.match(r"^stroke\b", label, re.I) and not re.search(r"bore", label, re.I) and pending_bore:
            b_label, b_unit, b_values, b_quote = pending_bore
            pending_bore = None
            if len(b_values) != len(values):
                review.append({"page": 1, "row": f"{b_label} / {label}", "reason": "bore and stroke rows differ in columns"})
                continue
            unit_names = re.search(r"\(([^)]*)\)", b_label)
            unit_text = unit_names.group(1) if unit_names else (b_unit or unit)
            units = [u.strip().lower() for u in unit_text.split("/")] if unit_text else []
            units = ["in" if u in ("inch", "inches") else u for u in units]
            for c_no, (bv, sv) in enumerate(zip(b_values, values)):
                header = headers[c_no] if headers and c_no < len(headers) else None
                if header and skip_column and skip_column.search(header):
                    continue
                bp = [p.strip() for p in bv.split("/")]
                sp = [p.strip() for p in sv.split("/")]
                if not units or len(bp) != len(units) or len(sp) != len(units):
                    if (bv or sv) and not (NA_RE.match(bv or "-") and NA_RE.match(sv or "-")):
                        review.append({"page": 1, "row": f"{b_label} / {label}",
                                       "reason": f"bore/stroke cells not readable: {bv!r} / {sv!r}"})
                    continue
                for u, b, s in zip(units, bp, sp):
                    if u not in ("in", "mm") or not re.fullmatch(NUM, b) or not re.fullmatch(NUM, s):
                        continue
                    facts.append(make_fact(f"bore_stroke_{u}", f"{b} x {s}", 1, f"{b_quote} {quote}",
                                           f"{b_label} {bv}; {label} {sv}", header, f"{b_label} / {label}"))
            continue
        rule = rule_for(label, section)
        if rule is None:
            continue
        named = [h for h in (headers or []) if h]
        filled = [(i, v) for i, v in enumerate(values) if v]
        if headers is not None and len(named) == 1 and len(filled) == 1 and len(values) != len(headers):
            # one model column whose heading cell and value cell are not aligned (spacer cells)
            values = [filled[0][1]]
            headers_row = named
        else:
            headers_row = headers
        for c_no, cell in enumerate(values):
            if not cell:
                continue
            header = headers_row[c_no] if headers_row and c_no < len(headers_row) else None
            if len(values) > 1 and header is None:
                review.append({"page": 1, "row": label, "reason": f"{len(values)} value cells without column headings"})
                break
            if header and skip_column and skip_column.search(header):
                skipped_cols.add(header)
                continue
            found, reasons = apply_rule(rule, label, section, unit, cell)
            for reason in reasons:
                review.append({"page": 1, "row": row_name(label, section, None), "reason": reason})
            for f in found:
                row = row_name(label, section, f["qualifier"])
                if unit:
                    row = row_name(f"{label} {unit}", section, f["qualifier"])
                facts.append(make_fact(f["key"], f["value"], 1, quote, cell, combine_engine(header, f["engine"]), row))
    for header in sorted(skipped_cols):
        review.append({"page": 1, "row": "", "reason": f"column {header!r} skipped: model is not a registry line"})
    return facts, review


METRIC_UNIT = re.compile(r"^(mm|kg|l|ltr|liters?|litres?|m|kw|nm|approx\.? ltr|appr\.? l|km/h|cm³|cm3)$", re.I)
US_UNIT = re.compile(r"^(in|in\.|inch|inches|ft|ft\.|feet|lbs?\.?|pounds|gal|gal\.|gallons|hp|lb-?ft|lbs?-ft|mph|"
                     r"cu\.? ?ft\.?|ft³|ft3)$", re.I)


def metric_only_tables(rows) -> set[int]:
    """Tables whose unit cells / label units are metric only (European technical data)."""
    metric: Counter = Counter()
    us: Counter = Counter()
    for t_no, cells, _, _, _ in rows:
        if len(cells) < 2:
            continue
        units = [cells[1]] + re.findall(r"\(([^()]*)\)", cells[0])
        for u in units:
            for part in re.split(r"\s*/\s*|\s*,\s*", u.strip()):
                if METRIC_UNIT.match(part):
                    metric[t_no] += 1
                elif US_UNIT.match(part):
                    us[t_no] += 1
        if re.search(r"\b(EU|DIN|ECE)\b", cells[0]):
            metric[t_no] += 1
    return {t for t, n in metric.items() if n >= 2 and not us[t]}


def parse_mb(raw_html: str, page_text: str) -> tuple[list[dict], list[dict], list[str]]:
    facts, review = parse_html_tables(table_rows(html_container(raw_html, "mb")), page_text)
    return facts, review, []


def parse_bmw_html(raw_html: str, page_text: str) -> tuple[list[dict], list[dict], list[str]]:
    rows = table_rows(html_container(raw_html, "bmw"))
    facts, review = parse_html_tables(rows, page_text, skip_column=BMW_SKIP_COLUMN)
    codes = []
    for _, cells, _, _, _ in rows:
        if cells and re.match(r"^engine (type|code|designation)$", cells[0], re.I):
            for cell in cells[1:]:
                if ENGINE_CODE.match(cell.strip()) and cell.strip() not in codes:
                    codes.append(cell.strip())
    return facts, review, codes


# ---- BMW PDF (word positions of the stored PDF; quotes from the stored layout text)
UNIT_ATOM = (r"(?:mm|inch(?:\s?³)?|in\.?|inches|m³|m²|m|ft³|ft²|ft\.?\s?lbs?\.?(?:\s*\(Nm\))?|ft\.?|ft3|cu\.? ?ft\.?|"
             r"kg|lbs?-?\s?ft|lbs?\.?|liters?|litres?|l|gal\.?|gallons|cm³|cm3|ccm|cc|hp|HP|bhp|rpm|RPM|lb-?\s?ft|Nm|kW|kWh|"
             r"Km/h|km/h|mph|mpg|miles|s|sec|%|:1|--|—|Ah|V|A|W|F/R|% front|% rear|cd x A)")
UNIT_EXPR = rf"{UNIT_ATOM}(?:\s*(?:/|@|//)\s*{UNIT_ATOM})*"
UNIT_FULL = re.compile(rf"^{UNIT_EXPR}$", re.I)
LABEL_SPLIT = re.compile(rf"^(?P<label>.+?)\s+(?P<unit>{UNIT_EXPR})$", re.I)
NOISE_RE = re.compile(r"^-\s*\d+\s*-$|^-\s*more\s*-|^a subsidiary|^of bmw ag|press information|^bmw group|"
                      r"corporate communications|^company\b|^postal address|^telephone|^internet|page \d+ of \d+|"
                      r"^\S+\.xls\b|^firm\b", re.I)
NUMERIC_LABELS = re.compile(r"wheelbase|length|width|height|track|curb weight|displacement|output|torque|power|"
                            r"fuel tank|tank capacity|turning circle|ground clearance|doors|seats|compression|stroke|bore",
                            re.I)
ENGINE_CODE = re.compile(r"^[A-Z]\d{2}[A-Z]\d{2}[A-Z]\d[A-Z0-9]*$")
# words of a column heading naming a model variant
MODEL_WORD = re.compile(r"\b\d{3}[a-zA-Z]{1,2}\b|xDrive|sDrive|xDr\b|sDr\b|\bM\d|\bX\d|Sedan|Coup[eé]|Wagon|"
                        r"Gran Turismo|\bGT\b|ALPINA|iPerformance|Competition|Touring|Convertible|Cabrio|\bSAV\b|"
                        r"\bSAC\b|\bB7\b|XB7")
JOINERS = {"/", "–", "-", "—", "@", "//"}


def _median(values: list[float]) -> float:
    values = sorted(values)
    n = len(values)
    return values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2


def pdf_lines(pdf_path: Path) -> list[list[list[dict]]]:
    """Per page: lines (words clustered by their top position) of tokens {text, x0, x1}.
    A stand-alone "/", "–" or "@" between two close words and a "(450)" right after a value are
    joined into one token ("5080 / 200", "600@5700 – 6600", "330 (450) / 1400-4500")."""
    import pdfplumber

    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
            lines: list[dict] = []
            for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
                if lines and abs(w["top"] - lines[-1]["top"]) <= 3:
                    lines[-1]["words"].append(w)
                else:
                    lines.append({"top": w["top"], "words": [w]})
            out = []
            for line in lines:
                ws = sorted(line["words"], key=lambda w: w["x0"])
                toks: list[dict] = []
                i = 0
                while i < len(ws):
                    w = ws[i]
                    tok = {"text": w["text"], "x0": w["x0"], "x1": w["x1"]}
                    if (w["text"] in JOINERS and toks and i + 1 < len(ws)
                            and w["x0"] - toks[-1]["x1"] < 8 and ws[i + 1]["x0"] - w["x1"] < 8):
                        nxt = ws[i + 1]
                        toks[-1]["text"] += f" {w['text']} {nxt['text']}"
                        toks[-1]["x1"] = nxt["x1"]
                        i += 2
                        continue
                    if toks and re.fullmatch(r"\([\d.,]+\)", w["text"]) and w["x0"] - toks[-1]["x1"] < 8:
                        toks[-1]["text"] += f" {w['text']}"
                        toks[-1]["x1"] = w["x1"]
                        i += 1
                        continue
                    toks.append(tok)
                    i += 1
                out.append(toks)
            pages.append(out)
    return pages


def _numeric(text: str) -> bool:
    return bool(re.search(r"\d", text)) and not re.search(r"[A-Za-z]", text) and not text.startswith(":")


def split_label_text(text: str) -> tuple[str, str]:
    """(label, unit) of the label part of a row ("Veh. length mm / inch", "Engine power hp@rpm")."""
    text = norm(text)
    m = LABEL_SPLIT.match(text)
    if m and not re.search(r"\d", m.group("unit")):
        return m.group("label").strip(), m.group("unit").strip()
    m = re.match(r"^(?P<label>.+?\b(?:diameter|ratio))\s*/?\s*(?P<unit>inch|in|mm|:1)$", text, re.I)
    if m:
        return m.group("label").strip(), m.group("unit").strip()
    return text, ""


class PageLayout:
    """Label column and model-variant columns of one PDF page."""

    def __init__(self, left: float, n_cols: int, centers: list[float]):
        self.left, self.n_cols, self.centers = left, n_cols, centers
        self.headers = [""] * n_cols
        if n_cols > 1:
            gaps = [centers[i + 1] - centers[i] for i in range(n_cols - 1)]
            self.bounds = ([centers[0] - gaps[0] / 2] + [(centers[i] + centers[i + 1]) / 2 for i in range(n_cols - 1)]
                           + [centers[-1] + gaps[-1] / 2])
        else:
            self.bounds = []

    def is_left(self, toks) -> bool:
        return bool(toks) and abs(toks[0]["x0"] - self.left) <= 3 and not NOISE_RE.search(
            " ".join(t["text"] for t in toks[:3]))

    def col_of(self, tok) -> int | None:
        if self.n_cols == 1:
            return 0
        mid = (tok["x0"] + tok["x1"]) / 2
        if mid < self.bounds[0]:
            return None
        for i in range(self.n_cols):
            if mid < self.bounds[i + 1]:
                return i
        return self.n_cols - 1

    def spans(self, tok) -> bool:
        return self.n_cols > 1 and sum(1 for c in self.centers if tok["x0"] - 2 <= c <= tok["x1"] + 2) > 1

    def split_row(self, toks):
        """(label, unit, {column: [token texts]}, spanning) of a left-aligned line."""
        if self.n_cols > 1:
            label_toks = [t for t in toks if self.col_of(t) is None]
            value_toks = [t for t in toks if self.col_of(t) is not None]
        else:
            # single column: the label is the run of words up to the first wide gap or number
            label_toks, value_toks = [toks[0]], []
            for prev, t in zip(toks, toks[1:]):
                if value_toks or t["x0"] - prev["x1"] > 12 or _numeric(t["text"]):
                    value_toks.append(t)
                else:
                    label_toks.append(t)
        label, unit = split_label_text(" ".join(t["text"] for t in label_toks))

        def unit_tok(i: int) -> bool:
            t = value_toks[i]
            if not UNIT_FULL.match(t["text"]) or t["text"] == "M" or i + 1 >= len(value_toks):
                return False
            if value_toks[i + 1]["x0"] - t["x1"] <= 8:
                return False
            if self.n_cols > 1:
                return (t["x0"] + t["x1"]) / 2 < self.centers[0] - (self.centers[1] - self.centers[0]) * 0.25
            return True

        while value_toks and unit_tok(0):
            unit = f"{unit} {value_toks[0]['text']}".strip()
            value_toks = value_toks[1:]
        cells: dict[int, list[str]] = {}
        spanning = False
        for t in value_toks:
            if self.spans(t):
                spanning = True
            cells.setdefault(self.col_of(t), []).append(t["text"])
        return label, unit, cells, spanning


def bmw_value_centers(page, left: float) -> list[float]:
    """Centers of the numeric values of the numeric rows of a page."""
    out = []
    for toks in page:
        if not toks or abs(toks[0]["x0"] - left) > 3:
            continue
        run = []
        for t in reversed(toks[1:]):
            if not _numeric(t["text"]):
                break
            run.append(t)
        label_text = " ".join(t["text"] for t in toks[:len(toks) - len(run)])
        if run and NUMERIC_LABELS.search(label_text):
            out.extend((t["x0"] + t["x1"]) / 2 for t in run)
    return out


def bmw_calibrate(page, left: float) -> tuple[int, list[float]] | None:
    """(columns, centers) from the numeric rows of one page: trailing run of numeric values."""
    runs: dict[int, list[list[float]]] = {}
    for toks in page:
        if not toks or abs(toks[0]["x0"] - left) > 3:
            continue
        run = []
        for t in reversed(toks[1:]):
            if not _numeric(t["text"]):
                break
            run.append(t)
        run.reverse()
        label_text = " ".join(t["text"] for t in toks[:len(toks) - len(run)])
        if run and NUMERIC_LABELS.search(label_text):
            runs.setdefault(len(run), []).append([(t["x0"] + t["x1"]) / 2 for t in run])
    if not runs:
        return None
    n_cols = max(runs, key=lambda k: (len(runs[k]), k))
    return n_cols, [_median([r[i] for r in runs[n_cols]]) for i in range(n_cols)]


def bmw_headings(page, lay: PageLayout) -> list[str] | None:
    """Column headings: the block of lines standing in the value columns and naming models,
    above the first numeric row of the page."""
    first_row = None
    for idx, toks in enumerate(page):
        if lay.is_left(toks):
            label, unit, cells, _ = lay.split_row(toks)
            if NUMERIC_LABELS.search(label) and any(_numeric(" ".join(v)) for v in cells.values()):
                first_row = idx
                break
    if first_row is None:
        return None
    block = []
    started = False
    for toks in reversed(page[:first_row]):
        if not toks or NOISE_RE.search(" ".join(t["text"] for t in toks)):
            continue
        in_area = all(lay.col_of(t) is not None and not lay.spans(t) for t in toks)
        in_area = in_area and bool(MODEL_WORD.search(" ".join(t["text"] for t in toks)))
        if lay.is_left(toks) or not in_area:
            if started:
                break
            continue
        started = True
        block.insert(0, toks)
    if not block:
        return None
    headers = [""] * lay.n_cols
    for toks in block:
        for t in toks:
            c = lay.col_of(t)
            headers[c] = norm(f"{headers[c]} {t['text']}")
    return headers


def parse_bmw(pdf_path: Path, pages: list[str]) -> tuple[list[dict], list[dict], list[str]]:
    """BMW US technical-data / technical-specification PDFs, one column per model variant.

    Layouts: MY2014-16 "Technical Data" (dual units "mm / inch"), MY2017-18 Excel sheets (unit
    column, "--" for none, several pages with different model columns) and MY2018+ "Technical
    Specifications." press layout. Words and their x positions come from the stored PDF: the label
    column is the dominant left edge of the lines; per page, the value columns are the medians of
    the value positions of numeric rows and the column headings are the block of lines standing in
    those columns above the first numeric row (a page without them continues the previous page's
    columns). Each value is assigned to the column it stands under; a value spanning several
    columns, or values in columns without a heading, go to review. Quotes are the row's words,
    checked against the stored layout text."""
    facts: list[dict] = []
    review: list[dict] = []
    codes: list[str] = []
    page_tokens = pdf_lines(pdf_path)
    norm_pages = [norm(p) for p in pages]
    firsts = Counter(round(toks[0]["x0"]) for page in page_tokens for toks in page
                     if len(toks) >= 2 and not NOISE_RE.search(toks[0]["text"]))
    if not firsts:
        return facts, [{"page": 1, "row": "", "reason": "no text lines"}], codes
    left = max(firsts.items(), key=lambda kv: (kv[1], -kv[0]))[0]

    def quote_for(p_no: int, line_toks: list[list[dict]]) -> str | None:
        text = norm(" ".join(t["text"] for toks in line_toks for t in toks))
        return text if text in norm_pages[p_no - 1] else None

    seen = set()
    skipped_cols: set[str] = set()
    lay: PageLayout | None = None
    for p_no, page in enumerate(page_tokens, 1):
        cal = bmw_calibrate(page, left)
        points = bmw_value_centers(page, left)
        if cal is not None and lay is not None and lay.n_cols > 1 and points and all(
                min(abs(x - c) for c in lay.centers) < 15 for x in points):
            cal = None  # the values stand in the previous page's columns: same layout continues
        if cal is not None and not (lay is not None and lay.n_cols > 1 and cal[0] == 1):
            new = PageLayout(left, cal[0], cal[1])
            heads = bmw_headings(page, new) if new.n_cols > 1 else None
            if heads is not None:
                new.headers = heads
            elif lay is not None and lay.n_cols > 1:
                # columns found again among the previous page's columns keep their headings
                mapped = []
                for c in new.centers:
                    i = min(range(lay.n_cols), key=lambda k: abs(lay.centers[k] - c))
                    mapped.append(lay.headers[i] if abs(lay.centers[i] - c) < 15 else "")
                new.headers = mapped
            lay = new
            if lay.n_cols > 1 and not all(lay.headers):
                review.append({"page": p_no, "row": "",
                               "reason": f"{lay.n_cols} value columns but no column headings found"})
        elif lay is None:
            lay = PageLayout(left, 1, [])
        section = ""
        rows: list[dict] = []
        for toks in page:
            if not toks or NOISE_RE.search(" ".join(t["text"] for t in toks)):
                continue
            if lay.is_left(toks):
                label, unit, cells, spanning = lay.split_row(toks)
                if not cells and not unit and not re.search(r"\d", label):
                    section = label
                    rows.append({"label": None})
                    continue
                rows.append({"section": section, "label": label, "unit": unit, "cells": [cells],
                             "spanning": spanning, "lines": [toks]})
            elif rows and rows[-1].get("label") and toks[0]["x0"] > left + 3:
                if lay.n_cols > 1 and all(lay.col_of(t) is not None for t in toks) and all(
                        norm(t["text"]) in lay.headers[lay.col_of(t)] for t in toks):
                    rows.append({"label": None})  # a repeated heading line
                    continue
                cells = {}
                for t in toks:
                    if lay.spans(t):
                        rows[-1]["spanning"] = True
                    cells.setdefault(lay.col_of(t) if lay.n_cols > 1 else 0, []).append(t["text"])
                rows[-1]["cells"].append(cells)
                rows[-1]["lines"].append(toks)
            else:
                rows.append({"label": None})
        headers = lay.headers
        n_cols = lay.n_cols

        def header_of(c):
            if n_cols == 1:
                return None
            return headers[c] if c is not None and c < len(headers) and headers[c] else ""

        # bore and stroke on two rows ("Stroke mm 94.6", "Bore mm 82")
        named = {}
        for i, row in enumerate(rows):
            if row.get("label") and re.match(r"^(bore|stroke)$", row["label"], re.I) and len(row["cells"]) == 1:
                named[row["label"].lower()] = i
        if set(named) == {"bore", "stroke"} and abs(named["bore"] - named["stroke"]) == 1:
            b, s = rows[named["bore"]], rows[named["stroke"]]
            first, second = (s, b) if named["stroke"] < named["bore"] else (b, s)
            quote = quote_for(p_no, first["lines"] + second["lines"])
            units = [u.strip().lower() for u in re.split(r"\s*/\s*", b["unit"])] if b["unit"] == s["unit"] else []
            for c in range(n_cols):
                bv, sv = " ".join(b["cells"][0].get(c, [])), " ".join(s["cells"][0].get(c, []))
                header = header_of(c)
                if not quote or not bv or not sv or header == "" or (header and BMW_SKIP_COLUMN.search(header)):
                    continue
                bp = [p.strip() for p in bv.split("/")]
                sp = [p.strip() for p in sv.split("/")]
                if len(bp) != len(units) or len(sp) != len(units):
                    review.append({"page": p_no, "row": "Bore / Stroke", "reason": f"not readable: {bv!r} / {sv!r}"})
                    continue
                for unit, bb, ss in zip(units, bp, sp):
                    key = {"mm": "bore_stroke_mm", "inch": "bore_stroke_in", "in": "bore_stroke_in"}.get(unit)
                    if key and re.fullmatch(NUM, bb) and re.fullmatch(NUM, ss):
                        fact = make_fact(key, f"{bb} x {ss}", p_no, quote,
                                         f"Bore {b['unit']} {bv}; Stroke {s['unit']} {sv}", header, "Bore / Stroke")
                        sig = (fact["key"], fact["value"], fact["engine_text"])
                        if sig not in seen:
                            seen.add(sig)
                            facts.append(fact)
        for row in rows:
            if not row.get("label"):
                continue
            label, unit, section = row["label"], row["unit"], row["section"]
            if re.match(r"^engine (type|code|designation)$", label, re.I):
                values = [v for c in row["cells"][0].values() for v in " ".join(c).split()]
                found_codes = [v for v in values if ENGINE_CODE.match(v)]
                for code in found_codes:
                    if code not in codes:
                        codes.append(code)
                if found_codes:
                    continue
            rule = rule_for(label, section)
            if rule is None or re.match(r"^(bore|stroke)$", label, re.I):
                continue
            quote = quote_for(p_no, row["lines"])
            if quote is None:
                review.append({"page": p_no, "row": label, "reason": "row text not found in page text"})
                continue
            if rule.kind in ("power", "torque", "perf") and re.search(r"e-engine|e-motor|electric", quote, re.I):
                continue  # electric machine rows: not the combustion engine's output
            if row["spanning"]:
                review.append({"page": p_no, "row": label, "reason": "a value spans several model columns"})
                continue
            per_col: dict[int, list[str]] = {}
            for cells in row["cells"]:
                for c, parts in cells.items():
                    per_col.setdefault(c, []).append(" ".join(parts))
            for c, parts in sorted(per_col.items(), key=lambda kv: -1 if kv[0] is None else kv[0]):
                header = header_of(c)
                if header == "":
                    review.append({"page": p_no, "row": label, "reason": "value in a column without heading"})
                    continue
                if header and BMW_SKIP_COLUMN.search(header):
                    skipped_cols.add(header)
                    continue
                if len(parts) == 2 and FRONT_REAR.search(label) and rule.kind in ("tires", "wheel", "text"):
                    cell_values = [(parts[0], "front"), (parts[1], "rear")]
                elif len(parts) > 1 and rule.kind not in ("text",):
                    review.append({"page": p_no, "row": label, "reason": f"several lines of values: {parts!r}"})
                    continue
                else:
                    cell_values = [(" ".join(parts), None)]
                for cell, axle in cell_values:
                    cell = norm(cell)
                    lead = re.match(rf"^({UNIT_EXPR})\s+(?=[\d(])", cell, re.I) if rule.kind in ("power", "torque") else None
                    cell_unit = unit
                    if lead:  # "ft lbs (Nm) @ rpm 553 / 2200-5000": the unit printed in the value area
                        cell_unit = f"{unit} {lead.group(1)}".strip()
                        cell = cell[lead.end():]
                    cell = bmw_pick_unit(rule, cell_unit, cell)
                    if cell is None:
                        continue
                    found, reasons = apply_rule(rule, label, section, bmw_unit_for(rule, cell_unit), cell)
                    for reason in reasons:
                        review.append({"page": p_no, "row": label, "reason": reason})
                    for f in found:
                        qualifier = f["qualifier"] or axle
                        fact = make_fact(f["key"], f["value"], p_no, quote, cell, combine_engine(header, f["engine"]),
                                         f"{label}{(' ' + unit) if unit else ''}" + (f" ({qualifier})" if qualifier else ""))
                        sig = (fact["key"], str(fact["value"]), fact["engine_text"], fact["row"])
                        if sig in seen:
                            continue  # headings and their first rows repeat on every page
                        seen.add(sig)
                        facts.append(fact)
    for header in sorted(skipped_cols):
        review.append({"page": 1, "row": "", "reason": f"column {header!r} skipped: model is not a registry line"})
    return facts, review, codes


def bmw_unit_for(rule, unit: str) -> str:
    """Unit passed to the unit checks: the part of a dual unit the key takes."""
    parts = [p.strip() for p in re.split(r"\s*/\s*", unit)] if unit else []
    if len(parts) < 2:
        return unit
    wanted = bmw_wanted_units(rule)
    for p in parts:
        if p.lower() in wanted:
            return p
    return unit


def bmw_wanted_units(rule) -> tuple[str, ...]:
    key = rule.keys[0]
    if key.endswith("_in") or key == "wheel_size_in":
        return ("inch", "in", "in.")
    if key.endswith("_ft") and "cu" not in key:
        return ("ft", "ft.")
    if key.endswith("_cu_ft"):
        return ("ft³", "ft3", "cu ft", "cu. ft")
    if key.endswith("_lb"):
        return ("lbs", "lb", "lbs.")
    if key.endswith("_gal"):
        return ("gal", "gal.")
    if key.endswith("_cc"):
        return ("cm³", "cm3", "cc", "ccm")
    return ()


def bmw_pick_unit(rule, unit: str, cell: str) -> str | None:
    """With a dual unit ("mm / inch", "Kg / lbs"), keep the part of the value in the key's unit."""
    parts = [p.strip() for p in re.split(r"\s*/\s*", unit)] if unit else []
    if len(parts) != 2 or rule.kind not in ("num",):
        return cell
    wanted = bmw_wanted_units(rule)
    idx = [i for i, p in enumerate(parts) if p.lower() in wanted]
    values = [v.strip() for v in re.split(r"\s*/\s*", cell)]
    if len(idx) != 1 or len(values) != 2:
        return None if len(idx) == 1 else cell
    return values[idx[0]]


# --------------------------------------------------------------------------- driver
def load_pagetext(digest: str) -> dict | None:
    path = RAW_ROOT / "pagetext" / f"{digest}.json.gz"
    if not path.exists():
        return None
    return json.loads(read_maybe_gz(path).decode("utf-8"))


def verify_quotes(facts: list[dict], pages: list[str]) -> list[dict]:
    bad = []
    normed = [norm(p) for p in pages]
    for f in facts:
        p = f["page"] - 1
        if not (0 <= p < len(normed)) or norm(f["quote"]) not in normed[p]:
            bad.append(f)
    return bad


def slug_of(line_key: str) -> str:
    return line_key.split("/", 1)[1]


def own_outputs(out_dir: Path, short: str) -> list[Path]:
    """Files this extractor wrote earlier for a host (re-written on every run)."""
    found = []
    for path in out_dir.glob(f"press-{short}-*.json"):
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("extractor") == EXTRACTOR:
                found.append(path)
        except (OSError, ValueError):
            continue
    return found


def run(host_keys: list[str]) -> dict:
    stats = {}
    for hk in host_keys:
        cfg = HOSTS[hk]
        manifest = col.MANIFEST_DIR / f"{cfg['host']}.csv"
        if not manifest.exists():
            print(f"{cfg['host']}: no manifest")
            continue
        rows = {}
        with manifest.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows[row["url"]] = row
        out_dir = WORK / cfg["make"] / "extracted"
        out_dir.mkdir(parents=True, exist_ok=True)
        for path in own_outputs(out_dir, cfg["short"]):
            path.unlink()
        counts = Counter()
        docs = 0
        n_review = 0
        skipped = []
        done_sha: dict[str, str] = {}
        for row in sorted(rows.values(), key=lambda r: r["url"]):
            if row["status"] != "ok" or row["doc_type"] != "press_specifications":
                continue
            lines = [k for k in row["line"].split(";") if k in BY_KEY]
            if not lines or not row["year"]:
                skipped.append((row["title"], "no registry line or no model year"))
                continue
            if row["sha256"] in done_sha:
                skipped.append((row["title"], f"same file as {done_sha[row['sha256']]}"))
                continue
            done_sha[row["sha256"]] = row["url"]
            year = int(row["year"])
            years = [year]
            both = re.search(r"\b(20[12]\d)\s*/\s*(20[12]\d)\b", row["title"])  # "2017/2018 E-Class Wagon ..."
            if both:
                years = sorted({int(both.group(1)), int(both.group(2))})
                years = [y for y in years if any(col.in_years(k, y) for k in lines)] or [year]
            raw_path = RAW_ROOT / row["path"]
            pt = load_pagetext(row["sha256"])
            if pt is None or not raw_path.exists():
                skipped.append((row["title"], "raw file or page text missing"))
                continue
            pages = pt["pages"]
            if hk == "mb":
                facts, review, codes = parse_mb(read_maybe_gz(raw_path).decode("utf-8"), pages[0])
            elif raw_path.suffix == ".gz":
                facts, review, codes = parse_bmw_html(read_maybe_gz(raw_path).decode("utf-8"), pages[0])
            else:
                facts, review, codes = parse_bmw(raw_path, pages)
            bad = verify_quotes(facts, pages)
            for f in bad:
                facts.remove(f)
                review.append({"page": f["page"], "row": f["row"], "reason": "quote not found in page text"})
            key = f"press-{cfg['short']}-{slug_of(lines[0])}-{year}-{row['sha256'][:8]}"
            doc = {
                "doc": {"key": key, "make": cfg["make"], "lines": lines, "years": years,
                        "doc_type": "press_specifications", "title": row["title"], "path": str(raw_path),
                        "url": row["url"], "page_url": "", "sha256": row["sha256"],
                        "retrieved_at": row["retrieved_at"], "tier": "A", "source_type": "PRESS_RELEASE",
                        "publisher": cfg["publisher"], "authenticity": "OFFICIAL_PUBLISHER"},
                "extractor": EXTRACTOR,
                "pages": len(pages),
                "edition_market": "US",
                "status": "ok" if facts else "no_facts",
                "engine_codes": codes,
                "review": review,
                "facts": facts,
            }
            (out_dir / f"{key}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
            docs += 1
            n_review += len(review)
            for f in facts:
                counts[f["key"]] += 1
        stats[cfg["host"]] = {"documents": docs, "facts": dict(sorted(counts.items())), "skipped": skipped}
        print(f"{cfg['host']}: {docs} documents, {sum(counts.values())} facts, {n_review} review rows, "
              f"{len(skipped)} skipped")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")
        for title, why in skipped:
            print(f"  skipped: {title} ({why})")
    return stats


def verify(host_keys: list[str], sample: int, seed: int) -> int:
    """Re-check every written quote against the stored page text; print a random sample of facts."""
    import random

    problems = 0
    all_facts = []
    for hk in host_keys:
        cfg = HOSTS[hk]
        out_dir = WORK / cfg["make"] / "extracted"
        files = own_outputs(out_dir, cfg["short"])
        n_facts = 0
        for path in files:
            doc = json.loads(path.read_text(encoding="utf-8"))
            pt = load_pagetext(doc["doc"]["sha256"])
            pages = [norm(p) for p in pt["pages"]] if pt else []
            for f in doc["facts"]:
                n_facts += 1
                ok = 0 < f["page"] <= len(pages) and norm(f["quote"]) in pages[f["page"] - 1]
                if not ok:
                    problems += 1
                    print(f"QUOTE NOT FOUND: {path.name} {f['key']} {f['quote'][:80]!r}")
                all_facts.append((path.name, doc["doc"]["sha256"], f))
        print(f"{cfg['host']}: {len(files)} files, {n_facts} facts checked")
    rng = random.Random(seed)
    for name, digest, f in rng.sample(all_facts, min(sample, len(all_facts))):
        print(f"\nSAMPLE {name} page {f['page']}\n  key={f['key']} value={f['value']!r} engine_text={f['engine_text']!r}"
              f"\n  row={f['row']!r}\n  original={f['original']!r}\n  quote={f['quote'][:300]!r}"
              f"\n  pagetext=RAW_ROOT/pagetext/{digest}.json.gz")
    print(f"\nquote problems: {problems}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", choices=["mb", "bmw", "all"], default="all")
    parser.add_argument("--verify", action="store_true", help="only re-check quotes of the written files")
    parser.add_argument("--sample", type=int, default=5, help="random facts to print with --verify")
    parser.add_argument("--seed", type=int, default=20261002)
    args = parser.parse_args()
    hosts = ["mb", "bmw"] if args.host == "all" else [args.host]
    if args.verify:
        sys.exit(1 if verify(hosts, args.sample, args.seed) else 0)
    run(hosts)


if __name__ == "__main__":
    main()
