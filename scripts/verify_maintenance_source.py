"""Full source check of the US maintenance schedule items: every item of every
data_work/<make>/staging/<line>/maintenance*.json is re-read from the document it cites and gets
a verdict CONFIRMED or UNCONFIRMED with reason codes.

The check is independent of the builders: it does not call their parsing or interval functions;
it re-derives the interval from the document (page-text store RAW_ROOT/pagetext/<sha>.json.gz,
the PDF itself through pdfplumber chars and ruling lines, or the stored JSON of a json_file
source). Only low-level shared helpers are used (page text loading, norm, RAW_ROOT / WORK).

An item is CONFIRMED only when all of these hold for every source document it cites:
  a. quote on page   every cite's quote is found on its cited page(s) (normalised: whitespace,
                     hyphenation, U+FFFE, ligatures, quotes / dashes); a grid quote (row label +
                     marks) may be checked as label on the page + marks from the geometry;
  b. interval stated the item's interval is stated by the clause / row it comes from:
                     text   the clause carrying the item (quote located on the page; a linked
                            heading or footnote where the layout puts the interval there) prints the
                            distance (miles as printed, else km), the km when it prints km, and the
                            months (or years x 12); FIRST from the first part ("at first", "first",
                            "initial", "at X miles"), SUBSEQUENT from the after part ("after that",
                            "thereafter", "then every", "after every"), EVERY needs "every"/"each"/
                            interval wording;
                     grid   the marks of the item's row are read from the page geometry (chars with
                            coordinates, rotated tables turned back) and mapped to the column
                            headers (miles / km / months); marks at d, 2d, 3d ... -> EVERY d; first f
                            then a constant step s -> FIRST f + SUBSEQUENT s; one mark -> FIRST;
                            irregular -> not confirmable;
                     list   (schedules printed as one block per interval point) the points whose
                            blocks list the item, turned into a shape the same way;
                     json   the item's values are the points / text of its entry in the stored file;
                     monitor items without distance and months (oil life monitor, Maintenance
                            Minder, CBS): the quote states the job and the action, the page states the
                            on-board system; a max_interval is stated (quote or its footnote);
  c. action          REPLACE / INSPECT / ROTATE / ADJUST / CLEAN matches the clause verb or the
                     mark letter of the grid legend;
  d. condition       a SEVERE item comes from a severe section / table / wording; a NORMAL item
                     does not (when the page tells); when the severe-use condition is attached to one
                     verb only ('Inspect the front and rear axle fluid, change if using your vehicle for
                     police, taxi, ... or frequent trailer towing'), the SEVERE item must carry that
                     verb's action (REPLACE) and a NORMAL item the other one (INSPECT);
  e. job             the quote (row label, bullet, clause) names the job, and not only as a part of
                     another component's name: 'ATF' in 'Rear Sport Differential - Change ATF ...',
                     'coolant' in 'Coolant (Inverter)' / 'Front axle drive - drain coolant', 'toothed
                     belt' in 'Coolant Pump Toothed Belt', 'oil' in 'AWD Clutch - Change oil'
                     (JOB_OTHER_COMPONENT; a card row 'Subject - operation' whose subject names another
                     job must name the item's own component in its operation);
  f. scope / extent  a row or bullet that carries a footnote mark whose footnote gives one engine its
                     own interval for the job ('*6 : Engine oil (2.0 TGDI) Replace every 6,500 miles
                     ...') states its interval for the other engines only: the item must be scoped
                     (Hyundai / Kia); an engine-footnote item must carry the engine printed in front of
                     its interval; an EVERY quote followed on the page by 'then every ...' /
                     'thereafter ...' stops short of its cell; a quote inside an owner's-manual
                     supplement that revises only some interval blocks ('This supplement revises or adds
                     to the "15,000 miles/(24,000 km)/18 months", "90,000 miles/..." sections') is not
                     the whole schedule;
  g. applicability   a restriction printed with the item's own label ('Drive shaft boots (4WD/AWD)',
                     'Rear differential oil (AWD)', '(AWD models)', 'if equipped with 4WD', '(Diesel
                     Engine)', '(Gas Engine)', 'Replace CVT Fluid (... (HEV))', '(CVT only)', 'Except 1.4L
                     Engine:', '(Except 6.2L V8 Engine)') must be carried by the item's applicability (drive /
                     engine / transmission / edition / models / variant / plan values; a negative one by an
                     *_except value or a narrower value of the same kind); the opposite scope contradicts it;
                     a model exclusion ('(except ... Outlander Sport)') must not name the item's own line,
                     and one of an edition of the line ('Except CTS-V:'), an equipment exclusion ('(except
                     vehicles with timing chain)', ', without limited slip differential') and a cited scope
                     note ('For diesel engine vehicles, see ... supplement') must be carried.
                     Only the sentences of the label that name the item's job count, and only their part
                     before the first interval statement. Mopar schedule data: the item's engine scope must be
                     named by the service text, the plan title or the document title, and not negated there
                     ('Non SRT Engines' does not state SRT). A negated mention ('for non-DSG') does not name
                     a job.
Units: km must be the printed km when the source prints km; a conversion never confirms a
distance by itself (the printed miles, or the printed km of a km-only text, must be there).
Time limit: when the item's own clause prints a time limit ('every 47,500 miles (75,000 km) or 3
years') the item must carry it (months_printed_not_in_item); for grids / lists, where a note can make
a line mileage-only ('(1) Performed based on the number of miles only'), a missing time limit is
only reported as the warning time_printed_not_in_item.
Clause extent: a quote that stops short of its printed cell / note is read with the rest of that
cell or note on the page (the whole text cell of a grid row, the whole footnote '*N: ...', a
NOTE whose opening condition 'If towing a trailer ...' governs all of its sentences, the note '(N)'
a list bullet refers to when it prints a first interval and the one after it).
Layout families (re-derived from the document, independent of the builders):
  GM charts (Chevrolet, Cadillac)  columns = vertical heading cells '12 000 km/7,500 mi', marks = the
                                   check-mark glyph ('@' in the symbol font), time limit from the row's
                                   footnote (n) of the chart's Normal / Severe footnote block;
  Jeep 2014-16 owner's manuals     header rows 'Mileage or time passed' / 'Or Years:' / 'Or
                                   Kilometers:' (turned numbers), X marks;
  Mitsubishi booklets              header rows 'miles x 1,000' / 'km x 1,000' / 'months', X marks, text
                                   cells across the columns, footnotes *N; older booklets: list blocks
                                   '● 30,000 Miles (48,000 km) or at 24 months';
  Nissan / Infiniti                stacked heading cells 'miles / (km) / months', R / I marks (grids over
                                   two pages), service-guide and owner's-manual lists, severe tables;
  Hyundai / Kia                    tables turned by 90 degrees read in a logical frame, headings
                                   Months / Miles x1,000 / Km x1,000, R / I marks, engine sub-rows,
                                   text cells, the severe-usage table, list-format schedules;
  text families                    Audi / VW cards, Ford tables, Honda Maintenance Minder, Tesla,
                                   Mercedes Service A / B, BMW CBS; Mopar schedule data (json).
Misprinted column heading: a single grid column whose km / months heading breaks the proportion that
every other column keeps with its miles heading (2020 Altima '82.5 / (138) / 138' beside '86.25 / (138)
/ 138') is left out of the km / months shapes when at least three other marked columns, the first one
among them, state the interval (warning header_misprint_column:<miles>); the miles still come from
every marked column.
Mopar schedule data: the years printed at the plan's points give the time limit (an item without it:
warning time_printed_not_in_item; a different one: months_mismatch).
Reason codes (UNCONFIRMED): quote_not_on_page, distance_not_stated / distance_mismatch,
km_not_as_printed / km_unitless_not_as_printed ('(90K)') / km_printed_implausible ('(300 km)') /
km_not_printed_nor_converted, months_not_stated / months_mismatch / months_printed_not_in_item,
every_not_stated / first_not_stated / subsequent_not_stated / occurrence_mismatch, marks_irregular /
header_points_inconsistent (a misprinted column heading) / marks_not_found / row_label_not_found /
sub_row_ambiguous, list_points_not_found, action_mismatch / action_not_stated, severe_not_stated /
normal_item_from_severe_text / action_not_stated_for_condition, job_not_named / footnote_names_other_job /
job_names_other_component, footnote_engine_scope_missing / footnote_engine_not_stated,
drive_scope_not_carried / powertrain_scope_not_carried / transmission_scope_not_carried /
engine_scope_not_carried, *_scope_contradicted, scope_excludes_line, engine_scope_not_stated (Mopar plan),
clause_continues_after_quote, schedule_supplement_partial, schedule_other_powertrain /
schedule_canada (a card schedule that is not the US combustion one), max_interval_not_stated,
schedule_system_not_stated, interval_not_stated (a monitor item that carries an interval), plus
layout codes (*_not_found, pdf_page_missing, verifier_error).

Output: data_work/_shared/maintenance_verification/<make>.json (one record per item) and
summary.json (counts per make by verdict, method and reason).

  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/verify_maintenance_source.py [make ...]
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from maintenance_common import page_text  # noqa: E402  (low-level: page-text store)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

OUT_DIR = WORK / "_shared" / "maintenance_verification"
KM_PER_MI = 1.609344

# ============================================================================ text normalisation

_TRANS = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "″": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-",
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ", " ": " ", "　": " ",
    "×": "x", "￾": "", "­": "", "​": "", "﻿": "", "‎": "", "‏": "",
})


def canon(text: str) -> str:
    """Comparable form of a text: NFKC (ligatures, full-width), quotes and dashes unified, U+FFFE /
    soft hyphen dropped, whitespace collapsed."""
    t = unicodedata.normalize("NFKC", str(text)).translate(_TRANS)
    t = " ".join(t.split())
    t = re.sub(r"(?<=[a-z])(?=(?:After|Thereafter|Every|EVERY)\b)", " ", t)  # glued words: "120 monthsAfter that"
    return re.sub(r"(?<=[a-z])- (?=[a-z])", "", t)  # a word broken at a line end: "pro- cedures"


def compact(text: str) -> str:
    """canon() without whitespace and hyphens, lower case: hyphenation and line breaks vanish."""
    return "".join(ch for ch in canon(text).lower() if not ch.isspace() and ch != "-")


class CText:
    """A canon text with its compact form and the map compact index -> canon index."""

    def __init__(self, raw: str):
        self.text = canon(raw)
        chars, pos = [], []
        for i, ch in enumerate(self.text.lower()):
            if ch.isspace() or ch == "-":
                continue
            chars.append(ch)
            pos.append(i)
        self.compact = "".join(chars)
        self.pos = pos

    def spans(self, needle: str) -> list[tuple[int, int]]:
        c = compact(needle)
        if not c:
            return []
        out, start = [], 0
        while True:
            i = self.compact.find(c, start)
            if i < 0:
                return out
            out.append((self.pos[i], self.pos[i + len(c) - 1] + 1))
            start = i + 1

    def has(self, needle: str) -> bool:
        c = compact(needle)
        return bool(c) and c in self.compact


# ============================================================================ vocabulary

JOB_NAMES = {
    "ac_desiccant": r"desiccant",
    "accessory_drive_belt": r"drive belts?|ribbed (?:v-?)?belt|v-belt|serpentine|accessory (?:drive )?belt|belts? condition|belt drive",
    "awd_coupling_fluid": r"awd clutch|awd coupling|haldex|torque splitter|all[- ]wheel[- ]drive (?:coupling|clutch)",
    "battery": r"batter(?:y|ies)",
    "battery_12v": r"batter(?:y|ies)",
    "brake_fluid": r"brake fluid|brake/clutch fluid|brake and clutch system|brake fluid",
    "brake_lines": r"brake (?:lines|hoses)|brake hoses",
    "brakes": (r"brakes\b|brake (?:pads?|linings?|discs?|rotors?|system|calipers?|shoes|pad thickness|components?)"
               r"|disc brakes?|drum brakes?|front and rear brakes|brake disc"),
    "cabin_air_filter": (r"cabin (?:air )?filter|dust and pollen filter|pollen|passenger compartment air filter"
                         r"|climate control air filter|air conditioning(?:/cabin)? filter|a/c (?:cabin )?filter|in-cabin"
                         r"|microfilter|cabin dust|combination filter|air purifier|hepa|cabin and|cabin air"),
    "clutch_fluid": r"clutch fluid",
    "cooling_system": r"cooling system",
    "cooling_system_hoses": r"coolant hoses|radiator hose",
    "cv_joints": r"cv joints?|cv/universal",
    "dct_fluid": r"dual clutch|\bdct\b",
    "differential_fluid": (r"differential|axle (?:fluid|oil|drive)|final drive|rear axle|front axle|\bptu\b|power transfer unit"
                           r"|rear drive|\brda\b|transfer fluid & differential"),
    "drive_shaft_boots": r"drive ?shafts?|half-shaft|cv boots",
    "driveshaft_boots": r"drive ?shafts?",
    "dual_clutch_fluid": r"\bdsg\b|dual[- ]clutch",
    "engine_air_filter": r"air (?:cleaner|filter)|engine air|air cleaner element",
    "engine_coolant": r"coolant|cooling system",
    "engine_oil": r"engine oil|motor oil|\boil\b",
    "engine_oil_and_filter": r"engine oil|motor oil|oil (?:and|&) (?:oil )?filter|oil change|change (?:the )?(?:engine )?oil|\boil\b",
    "evap_system": r"evaporative|\bevap\b",
    "evap_vapor_lines": r"vapor|\bevap\b",
    "exhaust_system": r"exhaust(?!\s+fluid)|muffler",  # 'Diesel Exhaust Fluid' is not the exhaust system
    "fluid_levels": r"fluid levels?|all fluids|fluids inspected",
    "front_suspension": r"suspension|tie rod|ball joints?",
    "fuel_filter": r"fuel filters?|water separator|fuel filter",
    "fuel_lines": r"fuel (?:lines|hoses|line)",
    "fuel_system": r"fuel system",
    "gas_struts": r"gas struts?|lift supports?",
    "high_voltage_wiring": r"high voltage wire",
    "idle_speed": r"idle speed",
    "intercooler_coolant": r"intercooler",
    "inverter_coolant": r"inverter",
    "key_fob_battery": r"intelligent key|key battery|keyless|transmitter battery|remote (?:control|key)",
    "manual_transmission_fluid": r"manual trans(?:mission|axle)",
    "motor_coolant": r"motor coolant",
    "motor_cooling_oil": r"motor cooling oil",
    "parking_brake": r"parking brake|park brake",
    "pcv_valve": r"\bpcv\b",
    "propeller_shaft": r"propeller shaft",
    "spark_plugs": r"spark plugs?(?! wires| boots)",
    "steering_linkage": r"steering",
    "supercharger_drive_belt": r"supercharger drive belt",
    "suspension": r"suspension",
    "timing_belt": r"timing belt|toothed belt|camshaft drive",
    "tire_rotation": r"rotat",
    "transfer_case_fluid": r"transfer (?:case|oil|fluid|box)",
    "transmission_fluid": r"transmission|transaxle|\bcvt\b|\batf\b|multitronic|tiptronic",
    "valve_clearance": r"valve clearance",
    "wiper_blades": r"wiper blades?|wiper",
    "diesel_exhaust_fluid": r"diesel exhaust fluid|\bdef\b|adblue",
}

ACTION_VERBS = {
    "REPLACE": r"replac\w*|chang\w*|renew\w*|flush\w*|drain\w*|refill\w*|fill completely|fill\b",
    "INSPECT": r"inspect\w*|lnspect|check\w*|examin\w*|test\b|visually|health check|read out|measure\w*",
    "ROTATE": r"rotat\w*",
    "ADJUST": r"adjust\w*",
    "CLEAN": r"clean\w*|lubricat\w*",
}

SEVERE_WORDS = re.compile(
    r"\bsevere|\bdusty\b|\bsandy\b|\bunpaved\b|off-?road|\btowing\b|\btow\b|\btrailer|\bcamper|car-top|\bpolice\b"
    r"|\btaxi\b|\bfleet\b|commercial use|\bmountain|short (?:trips|distances)|\bidling\b|low[- ]speed driving|stop-and-go"
    r"|\brough\b|\bmuddy\b|\bsalted\b|\bsalt\b|heavy traffic|\bsoot\b|very cold|extensive idling|frequent(?:ly)? (?:trailer|towing)",
    re.I)


NEGATED_NAME = re.compile(r"\bnon[- ]?(?=[A-Za-z])[A-Za-z0-9]+", re.I)  # 'for non-DSG': names what the row is NOT for


def job_named(job: str, text: str) -> bool:
    """The text names the job; a negated mention ('Transmission, Automatic - Change Fluid ... for non-DSG')
    does not name it."""
    pattern = JOB_NAMES.get(job)
    return bool(pattern and re.search(pattern, NEGATED_NAME.sub(" ", canon(text)), re.I))


# A job's name can be part of another component's name: 'ATF' in 'Rear Sport Differential - Change ATF
# ...', 'coolant' in 'Coolant (Inverter)', 'toothed belt' in 'Coolant Pump Toothed Belt', 'oil' in
# 'Differential oil'. job -> (another component named, the job's own component named): a label that
# names the other component and not the job's own one does not state the job.
JOB_OTHER_COMPONENT = {
    "engine_coolant": (r"inverter|motor coolant|(?:hv|high[- ]voltage|traction|hybrid) battery|battery coolant|intercooler"
                       r"|power electronics|charge air|axle|differential|final drive",
                       r"engine|radiator"),
    "transmission_fluid": (r"differential|final drive|axle|transfer (?:case|box|fluid|oil)|power transfer unit|\bptu\b"
                           r"|rear drive (?:unit|module)|manual (?:trans|gear)|coupling|haldex",
                           r"(?<!manual )(?<!manual\s)(?:transmission|transaxle)|gearbox|tiptronic|multitronic|s ?tronic|\bdsg\b"
                           r"|\bcvt\b|\bivt\b|dual[- ]clutch|\bdct\b|automatic|intelligent variable"),
    "timing_belt": (r"coolant pump|water pump|balance shaft|ribbed|accessory|serpentine|v-belt|drive belts?\b",
                    r"timing|camshaft|cam belt"),
    "engine_oil": (r"differential|gear oil|transfer|axle|transmission|transaxle|coupling|clutch|motor cooling|reduction gear"
                   r"|power steering|shock|haldex",
                   r"engine|motor oil|oil filter"),
    "engine_oil_and_filter": (r"differential|gear oil|transfer|axle|transmission|transaxle|coupling|clutch|motor cooling|reduction gear"
                              r"|power steering|shock|haldex",
                              r"engine|motor oil|oil filter|oil (?:and|&) (?:oil )?filter"),
    "engine_air_filter": (r"cabin|climate control|pollen|in-cabin|microfilter|passenger compartment|air conditioning|a/c\b|hepa"
                          r"|fuel tank air|dust filter",
                          r"engine|air cleaner|intake"),
    "accessory_drive_belt": (r"timing belt|camshaft|toothed belt|coolant pump", r"drive belt|ribbed|v-belt|serpentine|accessory|poly"),
}


def job_reasons(job: str, text: str) -> list[str]:
    """The job against the label / clause that carries the item: named, and not as a part of another
    component's name (JOB_OTHER_COMPONENT); a card row 'Subject - operation' whose subject names another
    job states the item only when its operation names the item's own component ('Brake System - Check
    ... brake fluid level' states brake fluid; 'Rear Sport Differential - Change ATF ...' and 'AWD Clutch
    - Change oil' do not state the transmission fluid / the engine oil)."""
    t = canon(text)
    if not job_named(job, t):
        return ["job_not_named"]
    other = JOB_OTHER_COMPONENT.get(job)
    if other and re.search(other[0], t, re.I) and not re.search(other[1], t, re.I):
        return ["job_names_other_component"]
    m = re.match(r"\s*([A-Z][^-]{2,80}?)\s+-\s+(?=[A-Za-z])", t)
    if m:
        subject, operation = m.group(1), t[m.end():]
        named = {j for j in JOB_NAMES if job_named(j, subject)}
        same = {job} | JOB_ALIASES.get(job, set())
        strong = other[1] if other else JOB_NAMES.get(job)
        if named and not (named & same) and not (strong and re.search(strong, operation, re.I)):
            return ["job_names_other_component"]
    return []


# jobs whose names overlap (one label names both): a subject that names one of them states the other
JOB_ALIASES = {
    "engine_oil": {"engine_oil_and_filter"}, "engine_oil_and_filter": {"engine_oil"},
    "battery": {"battery_12v"}, "battery_12v": {"battery"},
    "drive_shaft_boots": {"driveshaft_boots", "cv_joints"}, "driveshaft_boots": {"drive_shaft_boots", "cv_joints"},
    "cv_joints": {"drive_shaft_boots", "driveshaft_boots"},
    "dct_fluid": {"dual_clutch_fluid", "transmission_fluid"}, "dual_clutch_fluid": {"dct_fluid", "transmission_fluid"},
    "front_suspension": {"suspension", "steering_linkage"}, "suspension": {"front_suspension", "steering_linkage"},
    "steering_linkage": {"front_suspension", "suspension"},
    "cooling_system": {"engine_coolant"}, "engine_coolant": {"cooling_system"},
    "evap_system": {"evap_vapor_lines"}, "evap_vapor_lines": {"evap_system"},
    "fuel_lines": {"fuel_system"}, "fuel_system": {"fuel_lines"},
}


CONDITIONAL_VERB = re.compile(r"\b(?:replac\w*|chang\w*|adjust\w*|clean\w*|renew\w*)\b(?=[^.;:]{0,40}?\b(?:if|as) (?:necessary|needed|required)\b)",
                              re.I)


NEGATED_VERB = re.compile(r"\(?\s*not (?:just|only|merely) (?:inspect|check)\w*\s*\)?", re.I)  # 'change (not just inspect) oil'


def verbs_in(text: str) -> set[str]:
    """Actions named by the verbs of a text; a conditional one ('check ... and replace if necessary')
    or a negated one ('change (not just inspect) oil') is not the item's action."""
    t = CONDITIONAL_VERB.sub(" ", NEGATED_VERB.sub(" ", canon(text)))
    return {action for action, pattern in ACTION_VERBS.items() if re.search(rf"\b(?:{pattern})", t, re.I)}


# ============================================================================ numbers and clauses

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
           "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20}
_NUMW = "|".join(WORDNUM)
_N = r"\d{1,3}(?:,\d{3})+|\d{1,3}(?: \d{3})+(?=\s*(?:km|mi|k\s?m))|\d+(?:\.\d+)?"
DIST_RE = re.compile(
    rf"(?<![\d.,])(?P<n1>{_N})\s*(?P<k1>[Kk](?![a-zA-Z]))?(?:\s*-\s*(?P<n2>{_N})\s*(?P<k2>[Kk](?![a-zA-Z]))?)?"
    r"\s*(?P<u>miles?\b|mi\b\.?|kilomet(?:er|re)s?\b|k\s?m\b)", re.I)
K_ONLY_RE = re.compile(r"\(\s*(?P<n>\d+)\s*K\s*\)")
TIME_RE = re.compile(rf"(?<![\d.,])(?P<n>\d+|{_NUMW})\s*-?\s*(?P<u>years?|yrs?\b|months?|mos?\b)", re.I)
YEARLY_RE = re.compile(r"\b(?:every|each|once a|a|per)\s+year\b|\bannual(?:ly)?\b|\byearly\b(?!\s+intervals?\s+do(?:es)?\s+not)", re.I)
MASK_RE = re.compile(r"which\s*ever\s+(?:comes|occurs|is)\s+first|first sign|first visit to|(?:first|1st) (?:registration|delivery)", re.I)
FIRST_RE = re.compile(r"\b(?:at first|first|initial(?:ly)?|only once)\b", re.I)
AT_NUM_RE = re.compile(r"\bat\s+(?:approximately\s+)?(?=\d)", re.I)
AFTER_RE = re.compile(r"\bafter that\b|\bthereafter\b|\bafter every\b|\bafter (?:the )?(?:first|initial) (?:replacement|change|inspection|service)\b"
                      r"|\bthen\b|\bsubsequent(?:ly)?\b", re.I)
EVERY_RE = re.compile(r"\bevery\b|\beach\b|\bintervals? of\b|\bannual(?:ly)?\b|\byearly\b|\bonce a year\b|\bper year\b|\bregardless of mileage\b", re.I)


def _num(s: str) -> float:
    return float(s.replace(",", "").replace(" ", ""))


def _ival(v: float) -> int | float:
    return int(v) if float(v).is_integer() else v


def scan_numbers(text: str) -> dict:
    """Distances, km and times printed in a text. {'miles': [..], 'km': [..], 'pairs': {miles: km|None},
    'months': [..]} (ranges '10,000-12,000 miles' give a tuple)."""
    t = text
    toks = []
    for m in DIST_RE.finditer(t):
        unit = "km" if re.match(r"k", m.group("u"), re.I) else "mi"
        v1 = _num(m.group("n1")) * (1000 if m.group("k1") else 1)
        v = v1
        if m.group("n2"):
            v2 = _num(m.group("n2")) * (1000 if (m.group("k2") or m.group("k1")) else 1)
            v = (_ival(v1), _ival(v2))
        else:
            v = _ival(v1)
        toks.append({"kind": unit, "v": v, "s": m.start(), "e": m.end()})
    for m in K_ONLY_RE.finditer(t):
        if not any(tk["s"] <= m.start() < tk["e"] for tk in toks):
            toks.append({"kind": "km", "v": int(m.group("n")) * 1000, "s": m.start(), "e": m.end(), "konly": True})
    toks.sort(key=lambda x: x["s"])
    pairs, used_km, konly = {}, set(), set()
    for i, tk in enumerate(toks):
        if tk["kind"] != "mi":
            continue
        km = None
        if i + 1 < len(toks) and toks[i + 1]["kind"] == "km" and re.fullmatch(r"\s*\(?\s*", t[tk["e"]:toks[i + 1]["s"]]):
            km = toks[i + 1]["v"]
            used_km.add(i + 1)
            if toks[i + 1].get("konly"):
                konly.add(tk["v"])
        elif i > 0 and toks[i - 1]["kind"] == "km" and re.fullmatch(r"\s*\(\s*", t[toks[i - 1]["e"]:tk["s"]]):
            km = toks[i - 1]["v"]
            used_km.add(i - 1)
        pairs.setdefault(tk["v"], km)
    months = []
    for m in TIME_RE.finditer(t):
        n = m.group("n").lower()
        n = int(n) if n.isdigit() else WORDNUM[n]
        months.append(n * 12 if m.group("u").lower().startswith("y") else n)
    for m in YEARLY_RE.finditer(t):
        months.append(12)
    return {"miles": [tk["v"] for tk in toks if tk["kind"] == "mi"], "km": [tk["v"] for tk in toks if tk["kind"] == "km"],
            "pairs": pairs, "months": months, "konly": konly}


def has_interval(text: str) -> bool:
    n = scan_numbers(text)
    return bool(n["miles"] or n["km"] or n["months"])


def masked(text: str) -> str:
    return MASK_RE.sub(lambda m: "#" * len(m.group(0)), text)


def structure(text: str) -> dict:
    """Split an interval clause into its parts: {'first': str|None, 'after': str|None, 'every': str|None}.
    FIRST part: from a first marker ('at first', 'first', 'initial', 'at <number>') up to an after
    marker; AFTER part: from the after marker ('after that', 'thereafter', 'then', 'after every') on,
    when it carries an interval; otherwise the clause is one EVERY part."""
    mt = masked(text)
    f = FIRST_RE.search(mt)
    at = AT_NUM_RE.search(mt)
    if at and (f is None or at.start() < f.start()):
        # 'at 100000 miles' / 'at 10 years or ...': a first point, unless the text says 'every' before it
        if not EVERY_RE.search(mt[:at.start()]):
            f = at
    a = None
    for m in AFTER_RE.finditer(mt):
        if (f is None or m.start() > f.start()) and has_interval(text[m.start():]):
            a = m
            break
    if f is not None and a is not None:
        return {"first": text[f.start():a.start()], "after": text[a.start():], "every": None, "first_marker": True}
    if a is not None and has_interval(text[:a.start()]):
        return {"first": text[:a.start()], "after": text[a.start():], "every": None, "first_marker": False}
    if f is not None:
        return {"first": text[f.start():], "after": None, "every": None, "first_marker": True}
    # 'After 40,000 miles (64,000 km) or 48 months, inspect every 10,000 miles ...': the point after which
    # the interval runs, then the recurring part
    m = re.search(r"\bafter\s+(?=\d)", mt, re.I)
    if m:
        e = next((x for x in EVERY_RE.finditer(mt, m.end()) if has_interval(text[x.start():])), None)
        if e is not None and has_interval(text[m.start():e.start()]):
            return {"first": text[m.start():e.start()], "after": text[e.start():], "every": None, "first_marker": True}
    return {"first": None, "after": None, "every": text, "first_marker": False}


def segments(text: str) -> list[str]:
    """Interval statements of a text: sentences (a sentence carrying an after marker stays with the
    one before it), alternatives 'or, if ...', and new statements 'At <n>' / 'Every <n>' printed one
    after another (one per model in a maintenance card cell)."""
    t = canon(text)
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z(*])|,?\s+or,?\s+(?=if\b)", t)
    merged: list[str] = []
    for p in parts:
        if merged and AFTER_RE.search(masked(p)) and has_interval(p) and has_interval(merged[-1]) \
                and not re.match(r"\s*(?:\(?\d+\)|\*\d)", p):
            merged[-1] = f"{merged[-1]} {p}"
        elif merged and re.match(r"\(?\s*or\b", p, re.I) and has_interval(p):
            # 'Every 161 000 km (100,000 mi) Replace ... struts. Or every 10 years, whichever comes
            # first.': the time limit of the statement before
            merged[-1] = f"{merged[-1]} {p}"
        else:
            merged.append(p)
    out = []
    for p in merged:
        cuts = [0]
        # a new statement: 'Every <n>' / 'At <n>' printed one after another, or a second verb with its
        # own interval in the same sentence ('Inspect every 8,000 miles ... or 12 months, and replace
        # every 48,000 miles ...')
        starts = [m.start() for m in re.finditer(r"(?<![A-Za-z])(?:At|Every|EVERY|First|FIRST)\s+(?=[\d,]+)", p)]
        starts += [m.start(1) for m in re.finditer(
            r"[,;]\s*(?:and\s+)?((?:inspect|replace|change|check|rotate|clean|adjust)\w*\s+(?:every|at)\s+(?=[\d,]))", p, re.I)
            if not AFTER_RE.search(masked(p[max(0, m.start() - 30):m.start(1)]))]  # '..., after that, replace every'
        for pos in sorted(set(starts)):
            if pos > cuts[-1] and has_interval(p[cuts[-1]:pos]):
                cuts.append(pos)
        cuts.append(len(p))
        out += [p[a:b].strip() for a, b in zip(cuts, cuts[1:]) if p[a:b].strip()]
    return out or [t]


def close(a: float, b: float, rel: float = 0.02) -> bool:
    return abs(a - b) <= rel * max(abs(a), abs(b), 1)


def check_values(it: dict, part: str, warnings: list) -> list[str]:
    """The item's distance / km / months against the numbers printed in one part of a clause."""
    nums = scan_numbers(part)
    reasons = []
    mi, km, mo = it.get("interval_miles_original"), it.get("interval_km"), it.get("interval_months")
    if mi:
        cands = [v for v in nums["pairs"] if (v == mi if not isinstance(v, tuple) else mi in v)]
        if not cands:
            reasons.append("distance_not_stated")
        else:
            printed_km = nums["pairs"][cands[0]]
            if isinstance(printed_km, tuple):
                printed_km = printed_km[list(cands[0]).index(mi)] if isinstance(cands[0], tuple) else None
            if printed_km is not None:
                if km != printed_km:
                    # '(90K)' printed without a unit after the miles: the card's metric value;
                    # '180,000 miles (300 km)': a misprint, the item's km is then not printed anywhere
                    if not 1.3 <= printed_km / mi <= 1.9:
                        reasons.append("km_printed_implausible")
                    else:
                        reasons.append("km_unitless_not_as_printed" if cands[0] in nums["konly"] else "km_not_as_printed")
            elif km and not close(km, mi * KM_PER_MI):
                reasons.append("km_not_printed_nor_converted")
    elif km:
        if km not in nums["km"]:
            reasons.append("distance_not_stated")
    elif nums["miles"] or nums["km"]:
        warnings.append("distance_printed_not_in_item")
    if mo:
        if mo not in nums["months"]:
            reasons.append("months_not_stated")
    elif nums["months"] and (mi or km):
        # 'every 47,500 miles (75,000 km) or 3 years' printed in the item's own clause: an item without
        # the time limit is not the stated interval
        reasons.append("months_printed_not_in_item")
    return reasons


def check_clause(it: dict, clause: str, warnings: list) -> tuple[list[str], str]:
    """Occurrence and values of the item against one interval statement. Returns (reasons, part used)."""
    st = structure(clause)
    occ = it["occurrence"]
    if occ == "EVERY":
        if st["every"] is not None:
            if not EVERY_RE.search(masked(st["every"])):
                return ["every_not_stated"] + check_values(it, st["every"], []), st["every"]
            return check_values(it, st["every"], warnings), st["every"]
        if st["first"] is not None and st["after"] is not None:
            # 'first X, thereafter every X': the same values in both parts state an EVERY interval
            r1, r2 = check_values(it, st["first"], []), check_values(it, st["after"], [])
            if not r1 and not r2:
                return [], clause
            return ["occurrence_mismatch"] + (r2 or r1), clause
        return ["every_not_stated"] + check_values(it, st["first"], []), st["first"]
    if occ == "FIRST":
        if st["first"] is None:
            return ["first_not_stated"] + check_values(it, clause, []), clause
        return check_values(it, st["first"], warnings), st["first"]
    if occ == "SUBSEQUENT":
        if st["after"] is None:
            return ["subsequent_not_stated"] + check_values(it, clause, []), clause
        return check_values(it, st["after"], warnings), st["after"]
    return ["occurrence_unknown"], clause


def check_action(it: dict, part: str, label: str = "", extra: set | None = None) -> list[str]:
    """The item's action against the verb of its part (else of its label / context)."""
    action = it["action"]
    if it["job"] == "tire_rotation":
        # 'Rotate tires, inspect tire wear and measure tread depth': the job is the rotation
        return [] if action == "ROTATE" and re.search(r"\brotat", canon(part + " " + label), re.I) else ["action_mismatch"]
    # the verb that introduces the interval ('At first, replace at ...'), not a remark after it
    # ('only if required according to Standard Inspection')
    nums = [m.start() for m in DIST_RE.finditer(part)] + [m.start() for m in TIME_RE.finditer(part)]
    first_num = min(nums) if nums else None
    own = verbs_in(part[:first_num] if first_num is not None else part)
    if own:
        return [] if action in own else ["action_mismatch"]
    ctx = verbs_in(label) | (extra or set())
    if not ctx:
        return ["action_not_stated"]
    return [] if action in ctx else ["action_mismatch"]


def lead_severe(text: str) -> str | None:
    """SEVERE when a note opens with a severe-usage condition ('(1) If towing a trailer, ...,
    inspect ... And if the inspection is not performed, change ...'): the opening condition governs
    every sentence of the note."""
    first = re.split(r"(?<=[.;])\s+(?=[A-Z])", canon(text).strip(), maxsplit=1)[0]
    return "SEVERE" if SEVERE_WORDS.search(first) else None


SEVERE_IF = re.compile(r"\b(?:if|when|whenever)\b", re.I)


def severe_split(text: str) -> tuple[set, set] | None:
    """A text whose severe-use condition governs one verb only: 'Inspect the front and rear axle fluid,
    change if using your vehicle for police, taxi, ... or frequent trailer towing' -> ({INSPECT},
    {REPLACE}); 'if the vehicle is used for towing, replace ...' -> (set(), {REPLACE}). Returns (the
    actions stated without the condition, the actions under the condition), None when no severe
    condition is attached to a verb."""
    t = canon(text)
    t = CONDITIONAL_VERB.sub(lambda m: " " * len(m.group(0)), t)
    t = NEGATED_VERB.sub(lambda m: " " * len(m.group(0)), t)
    verbs = []
    for action, vp in ACTION_VERBS.items():
        verbs += [(m.start(), m.end(), action) for m in re.finditer(rf"\b(?:{vp})", t, re.I)]
    verbs.sort()
    severe_spans, severe_actions = [], set()
    for m in SEVERE_IF.finditer(t):
        sent_end = re.search(r"[.;](?:\s|$)|$", t[m.end():])
        cond_end = m.end() + sent_end.start()
        if not SEVERE_WORDS.search(t[m.end():cond_end]):
            continue
        clause_start = max([t.rfind(ch, 0, m.start()) for ch in ",;."] + [-1]) + 1
        before = [v for v in verbs if clause_start <= v[0] < m.start()]
        if before:
            # 'change if using ...': the verb of the clause the condition closes
            severe_actions.add(before[-1][2])
            severe_spans.append((before[-1][0], cond_end))
            continue
        # 'if the vehicle is used for towing, replace ...': the verb after the condition's comma
        comma = t.find(",", m.end(), cond_end)
        after = [v for v in verbs if comma >= 0 and comma < v[0] < cond_end]
        if after:
            severe_actions.add(after[0][2])
            severe_spans.append((m.start(), cond_end))
    if not severe_actions:
        return None
    normal = {a for s, e, a in verbs if not any(a0 <= s < b0 for a0, b0 in severe_spans)}
    return normal, severe_actions


def check_condition(it: dict, text: str, context: str | None) -> list[str]:
    """context: SEVERE / NORMAL of the section the item comes from, None when the page does not tell.
    A severe-use condition attached to one verb of the text ('Inspect ..., change if using your vehicle
    for police, taxi, ...') makes that verb the severe-use action and the others the normal-use ones:
    the item's action must be the one of its condition."""
    severe = bool(SEVERE_WORDS.search(canon(text))) or context == "SEVERE"
    split = severe_split(text) if context != "SEVERE" else None
    if split is not None:
        normal, under = split
        if it["condition"] == "SEVERE":
            return [] if it["action"] in under else ["action_not_stated_for_condition"]
        if it["action"] in normal:
            return []
        return ["normal_item_from_severe_text"]
    if it["condition"] == "SEVERE" and not severe:
        return ["severe_not_stated"]
    if it["condition"] == "NORMAL" and severe:
        return ["normal_item_from_severe_text"]
    return []


def best_text_check(it: dict, texts: list[str], label: str, context: str | None, extra_verbs: set | None = None,
                    job_text: str | None = None) -> tuple[list[str], str, list[str]]:
    """Run the text checks on every interval statement of the texts; the best statement wins.
    Returns (reasons, evidence, warnings)."""
    best = None
    for text in texts:
        for seg in segments(text):
            if not has_interval(seg):
                continue
            warnings: list[str] = []
            reasons, part = check_clause(it, seg, warnings)
            reasons += check_action(it, part if verbs_in(part) else seg, label, extra_verbs)
            reasons += check_condition(it, seg + " " + label, context)
            reasons += job_reasons(it["job"], (job_text if job_text is not None else label) + " " + seg)
            cand = (len(reasons), reasons, seg, warnings)
            if best is None or cand[0] < best[0]:
                best = cand
    if best is None:
        return ["interval_not_stated"], (texts[0][:160] if texts else ""), []
    return best[1], best[2][:240], best[3]


# ============================================================================ shapes

def shape(points: list[float]) -> list[tuple[str, float]] | None:
    """Points of a schedule -> [(EVERY, d)] | [(FIRST, f), (SUBSEQUENT, s)] | [(FIRST, p)] | None."""
    pts = sorted(set(round(p, 3) for p in points))
    if not pts:
        return None
    if len(pts) == 1:
        return [("FIRST", pts[0])]
    steps = {round(b - a, 3) for a, b in zip(pts, pts[1:])}
    if len(steps) != 1:
        return None
    step = steps.pop()
    if abs(pts[0] - step) < 1e-6:
        return [("EVERY", step)]
    return [("FIRST", pts[0]), ("SUBSEQUENT", step)]


def shape_one_gap(points: list[float]) -> list[tuple[str, float]] | None:
    """shape() of points from which one interior point was left out (a misprinted column heading):
    one step of twice the others is allowed."""
    pts = sorted(set(round(p, 3) for p in points))
    if len(pts) < 3:
        return None
    steps = [round(b - a, 3) for a, b in zip(pts, pts[1:])]
    step = min(steps)
    if step <= 0 or any(s not in (step, round(2 * step, 3)) for s in steps) or steps.count(round(2 * step, 3)) != 1:
        return shape(points)
    if abs(pts[0] - step) < 1e-6:
        return [("EVERY", step)]
    return [("FIRST", pts[0]), ("SUBSEQUENT", step)]


def header_misprints(cols: list[dict]) -> list[int]:
    """Columns of a grid whose km / months heading breaks the proportion that every other column keeps
    with its miles heading ('82.5 / (138) / 138' among '78.75 / (126) / 126', '86.25 / (138) / 138'):
    the indexes of the misprinted columns (empty when the headings are consistent or unclear)."""
    bad = set()
    for kind in ("km", "months"):
        ratios = [(i, round(c[kind] / c["miles"], 5)) for i, c in enumerate(cols) if c.get(kind) and c.get("miles")]
        if len(ratios) < 6:
            continue
        common = Counter(r for _, r in ratios).most_common(1)[0]
        odd = [i for i, r in ratios if r != common[0]]
        if len(odd) == 1:
            bad.add(odd[0])
        elif odd:
            return []
    return sorted(bad)


def compare_cols(it: dict, all_cols: list[dict], marked: list[dict], warnings: list) -> list[str]:
    """compare_shape() over the column headings of the marked columns; a single misprinted km / months
    heading (header_misprints) is left out of the km / months shapes when the item's other marked
    columns (at least three, the first one among them) state the interval."""
    def series(cs):
        miles = [c["miles"] for c in cs if c.get("miles") is not None]
        km = [c["km"] for c in cs if c.get("km") is not None]
        months = [c["months"] for c in cs if c.get("months") is not None]
        return (miles if len(miles) == len(cs) else [], km if len(km) == len(cs) else [], months if len(months) == len(cs) else [])

    miles, km, months = series(marked)
    reasons = compare_shape(it, miles, km, months, warnings)
    if "header_points_inconsistent" not in reasons:
        return reasons
    bad = [all_cols[i] for i in header_misprints(all_cols)]
    marked_sorted = sorted(marked, key=lambda c: c.get("miles") or 0)
    if len(bad) != 1 or not any(c is bad[0] for c in marked_sorted[1:]) or len(marked_sorted) < 4:
        return reasons
    rest = [c for c in marked_sorted if c is not bad[0]]
    _, km2, months2 = series(rest)
    w2: list[str] = []
    r2 = compare_shape(it, miles, km2, months2, w2, gap_ok=True)
    if r2:
        return reasons
    warnings += w2 + [f"header_misprint_column:{bad[0]['miles']}"]
    return []


def compare_shape(it: dict, miles: list | None, km: list | None, months: list | None, warnings: list,
                  km_printed: bool = True, gap_ok: bool = False) -> list[str]:
    """The item against the shapes of the points (miles, km, months) where its row / bullet is due.
    gap_ok: the km / months points miss one misprinted column (shape_one_gap)."""
    reasons = []
    shapes = {}
    for name, pts in (("miles", miles), ("km", km), ("months", months)):
        if pts:
            s = shape_one_gap(pts) if gap_ok and name != "miles" else shape(pts)
            if s is None:
                # regular miles but an irregular km / months row: the column headings misprint a point
                return ["header_points_inconsistent" if name != "miles" and miles and shape(miles) else "marks_irregular"]
            shapes[name] = s
    if not shapes:
        return ["no_points"]
    occs = {tuple(o for o, _ in s) for s in shapes.values()}
    if len(occs) != 1:
        return ["points_disagree"]
    occ_list = next(iter(occs))
    if it["occurrence"] not in occ_list:
        return ["occurrence_mismatch"]
    idx = occ_list.index(it["occurrence"])
    if "miles" in shapes:
        if it.get("interval_miles_original") != _ival(shapes["miles"][idx][1]):
            reasons.append("distance_mismatch")
    if "km" in shapes and km_printed:
        if it.get("interval_km") != _ival(shapes["km"][idx][1]):
            reasons.append("km_not_as_printed")
    elif it.get("interval_km") and it.get("interval_miles_original") and not close(it["interval_km"], it["interval_miles_original"] * KM_PER_MI):
        reasons.append("km_not_printed_nor_converted")
    if "months" in shapes:
        if it.get("interval_months") is None:
            warnings.append("time_printed_not_in_item")  # the item leaves out the printed time limit
        elif it.get("interval_months") != _ival(shapes["months"][idx][1]):
            reasons.append("months_mismatch")
    elif it.get("interval_months"):
        reasons.append("months_not_stated")
    if "miles" not in shapes and it.get("interval_miles_original"):
        reasons.append("distance_not_stated")
    return reasons


# ============================================================================ documents

class Docs:
    """Page texts (canon), PDFs (pdfplumber) and JSON sources, opened once."""

    def __init__(self):
        self._pages: dict[str, list[CText] | None] = {}
        self._pdf: dict[str, object] = {}
        self._geo: dict[tuple, object] = {}
        self._json: dict[str, object] = {}

    def pages(self, src: dict) -> list[CText] | None:
        sha = src["sha256"]
        if sha not in self._pages:
            try:
                self._pages[sha] = [CText(p) for p in page_text(sha)]
            except FileNotFoundError:
                self._pages[sha] = None
        return self._pages[sha]

    def raw_path(self, src: dict) -> Path:
        return RAW_ROOT / src["path"][len("rawstore:"):]

    def pdf(self, src: dict):
        key = src["sha256"]
        if key not in self._pdf:
            path = self.raw_path(src)
            try:
                self._pdf[key] = pdfplumber.open(path) if path.suffix.lower() == ".pdf" and path.exists() else None
            except Exception:  # noqa: BLE001 - a damaged PDF must not stop the run
                self._pdf[key] = None
        return self._pdf[key]

    def geo(self, src: dict, page_no: int):
        key = (src["sha256"], page_no)
        if key not in self._geo:
            pdf = self.pdf(src)
            self._geo[key] = PageGeo(pdf.pages[page_no - 1]) if pdf is not None and 0 < page_no <= len(pdf.pages) else None
        return self._geo[key]

    def json(self, src: dict):
        key = src["sha256"]
        if key not in self._json:
            path = self.raw_path(src)
            self._json[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        return self._json[key]

    def close(self):
        for pdf in self._pdf.values():
            if pdf is not None:
                pdf.close()
        self._pdf.clear()
        self._geo.clear()


# ============================================================================ page geometry

class PageGeo:
    """Characters and ruling lines of a PDF page, in a logical frame.

    frame(rotated): rotated=True turns a table printed turned by 90 degrees back into reading
    position (lines read bottom to top for a counter-clockwise turn, top to bottom for a
    clockwise one). Words are built from characters by position; characters that run across the
    frame (rotated column headings) are grouped into vertical words."""

    def __init__(self, page):
        self.page = page
        self.width, self.height = float(page.width), float(page.height)
        self.chars = [c for c in page.chars if c.get("text") is not None]
        try:
            self.edges = page.edges
        except Exception:  # noqa: BLE001
            self.edges = []
        self._frames = {}

    def rotation(self) -> str:
        """'none', 'ccw' (text reads bottom to top) or 'cw', by the majority of the glyphs."""
        glyphs = [c for c in self.chars if c["text"].strip()]
        rot = [c for c in glyphs if not c.get("upright", True)]
        if len(rot) <= len(glyphs) / 2:
            return "none"
        up = sum(1 for c in rot if c["matrix"][1] > 0)
        return "ccw" if up >= len(rot) / 2 else "cw"

    def _tf(self, box: tuple, rot: str) -> tuple:
        x0, top, x1, bottom = box
        if rot == "ccw":
            return (self.height - bottom, x0, self.height - top, x1)
        if rot == "cw":
            return (top, self.width - x1, bottom, self.width - x0)
        return box

    def frame(self, rot: str | None = None) -> dict:
        rot = rot or self.rotation()
        if rot in self._frames:
            return self._frames[rot]
        chars = []
        for c in self.chars:
            x0, top, x1, bottom = self._tf((c["x0"], c["top"], c["x1"], c["bottom"]), rot)
            a, b = c["matrix"][0], c["matrix"][1]
            # direction of the glyph in the logical frame
            if rot == "none":
                aligned = c.get("upright", True)
            elif rot == "ccw":
                aligned = (not c.get("upright", True)) and b > 0
            else:
                aligned = (not c.get("upright", True)) and b < 0
            chars.append({"t": c["text"], "x0": x0, "x1": x1, "y0": top, "y1": bottom, "aligned": aligned,
                          "size": max(bottom - top, 1.0) if aligned else max(x1 - x0, 1.0),
                          "up": b > 0 if not c.get("upright", True) else None,
                          "font": c.get("fontname", "")})
        hr, vr = [], []
        for e in self.edges:
            x0, top, x1, bottom = self._tf((e["x0"], e["top"], e["x1"], e["bottom"]), rot)
            if abs(bottom - top) < 2 and x1 - x0 > 4:
                hr.append((x0, x1, (top + bottom) / 2))
            elif abs(x1 - x0) < 2 and bottom - top > 4:
                vr.append((top, bottom, (x0 + x1) / 2))
        words = _words([c for c in chars if c["aligned"]])
        vwords = _vwords([c for c in chars if not c["aligned"]], rot)
        fr = {"rot": rot, "chars": chars, "words": words, "vwords": vwords, "hr": hr, "vr": vr,
              "lines": _lines(words), "rows": _rows(words)}
        self._frames[rot] = fr
        return fr


def _words(chars: list[dict]) -> list[dict]:
    """Horizontal words: characters of one line, split at spaces and gaps wider than a fifth of the
    glyph height."""
    chars = sorted(chars, key=lambda c: ((c["y0"] + c["y1"]) / 2, c["x0"]))
    lines: list[list[dict]] = []
    for c in chars:
        cy = (c["y0"] + c["y1"]) / 2
        for ln in reversed(lines[-6:]):
            ly = ln[0]["_cy"]
            if abs(cy - ly) <= 0.45 * max(c["size"], ln[0]["size"]):
                c["_cy"] = ly
                ln.append(c)
                break
        else:
            c["_cy"] = cy
            lines.append([c])
    out = []
    for ln in lines:
        ln.sort(key=lambda c: c["x0"])
        cur = None
        for c in ln:
            if not c["t"].strip():
                cur = None
                continue
            if cur is not None and c["x0"] - cur["x1"] <= 0.2 * max(c["size"], 1.0):
                cur["t"] += c["t"]
                cur["x1"] = max(cur["x1"], c["x1"])
                cur["y0"] = min(cur["y0"], c["y0"])
                cur["y1"] = max(cur["y1"], c["y1"])
                cur["chars"].append(c)
            else:
                cur = {"t": c["t"], "x0": c["x0"], "x1": c["x1"], "y0": c["y0"], "y1": c["y1"], "size": c["size"], "chars": [c]}
                out.append(cur)
    for w in out:
        w["cx"], w["cy"] = (w["x0"] + w["x1"]) / 2, (w["y0"] + w["y1"]) / 2
    return out


def _vwords(chars: list[dict], rot: str) -> list[dict]:
    """Words of characters that run across the frame (rotated headings): grouped by their x, read
    along y in the direction of the glyphs."""
    chars = sorted(chars, key=lambda c: ((c["x0"] + c["x1"]) / 2))
    cols: list[list[dict]] = []
    for c in chars:
        cx = (c["x0"] + c["x1"]) / 2
        if cols and abs(cx - cols[-1][0]["_cx"]) <= 0.45 * max(c["size"], 1.0):
            c["_cx"] = cols[-1][0]["_cx"]
            cols[-1].append(c)
        else:
            c["_cx"] = cx
            cols.append([c])
    out = []
    for col in cols:
        ups = [c["up"] for c in col if c["up"] is not None]
        reads_up = sum(1 for u in ups if u) >= len(ups) / 2 if ups else True
        if rot == "ccw":
            reads_up = not reads_up
        col.sort(key=lambda c: -c["y1"] if reads_up else c["y0"])
        cur, space = None, False
        for c in col:
            if not c["t"].strip():
                space = True
                continue
            size = max(c["x1"] - c["x0"], 1.0)
            gap = None if cur is None else ((cur["y0"] - c["y1"]) if reads_up else (c["y0"] - cur["y1"]))
            if cur is not None and gap <= 1.2 * size:
                # one vertical line of text: a space where the text has one or a gap is wide
                cur["t"] += (" " if space or gap > 0.3 * size + 0.5 else "") + c["t"]
                cur["y0"], cur["y1"] = min(cur["y0"], c["y0"]), max(cur["y1"], c["y1"])
                cur["x0"], cur["x1"] = min(cur["x0"], c["x0"]), max(cur["x1"], c["x1"])
            else:
                cur = {"t": c["t"], "x0": c["x0"], "x1": c["x1"], "y0": c["y0"], "y1": c["y1"]}
                out.append(cur)
            space = False
    for w in out:
        w["cx"], w["cy"] = (w["x0"] + w["x1"]) / 2, (w["y0"] + w["y1"]) / 2
    return out


def _lines(words: list[dict]) -> list[dict]:
    """Words grouped into visual lines (same y), each line split where the gap is wider than two
    glyph heights (table cells side by side)."""
    words = sorted(words, key=lambda w: (w["cy"], w["x0"]))
    rows: list[list[dict]] = []
    for w in words:
        if rows and abs(w["cy"] - rows[-1][0]["cy"]) <= 0.45 * max(w["size"], rows[-1][0]["size"]):
            rows[-1].append(w)
        else:
            rows.append([w])
    out = []
    for r in rows:
        r.sort(key=lambda w: w["x0"])
        cur = None
        for w in r:
            if cur is not None and w["x0"] - cur["x1"] <= 2.0 * w["size"]:
                cur["words"].append(w)
                cur["x1"] = w["x1"]
                cur["y0"], cur["y1"] = min(cur["y0"], w["y0"]), max(cur["y1"], w["y1"])
            else:
                cur = {"words": [w], "x0": w["x0"], "x1": w["x1"], "y0": w["y0"], "y1": w["y1"], "size": w["size"]}
                out.append(cur)
    for ln in out:
        ln["t"] = " ".join(w["t"] for w in ln["words"])
        ln["cy"] = (ln["y0"] + ln["y1"]) / 2
    return out


def _rows(words: list[dict]) -> list[list[dict]]:
    """Words grouped by their baseline only (one visual row across the page), left to right."""
    rows: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w["cy"], w["x0"])):
        if rows and abs(w["cy"] - rows[-1][0]["cy"]) <= 0.45 * max(w["size"], rows[-1][0]["size"]):
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w["x0"]) for r in rows]


def rules_at(fr: dict, x: float, lo: float = -1e9, hi: float = 1e9) -> list[float]:
    """y of the horizontal rules crossing x (sorted, merged within 1.5 pt)."""
    ys = sorted(y for x0, x1, y in fr["hr"] if x0 - 1 <= x <= x1 + 1 and lo <= y <= hi)
    out = []
    for y in ys:
        if not out or y - out[-1] > 1.5:
            out.append(y)
    return out


# ============================================================================ grids

NUM_WORD = re.compile(r"\(?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\)?\*?")
HEAD_KINDS = [
    ("months", re.compile(r"(?:or\s+)?months?\s*:?", re.I)),
    ("years", re.compile(r"(?:or\s+)?years?\s*:?", re.I)),
    ("miles", re.compile(r"(?:or\s+)?miles?\s*:?(?:\s*[x×6]\s*1,?000)?"
                         r"|mileage(?: or time passed)?(?:\s*\(whichever comes first\))?\s*:?", re.I)),
    ("km", re.compile(r"\(?(?:or\s+)?(?:km|kilomet(?:er|re)s)\s*:?(?:\s*[x×6]\s*1,?000)?\)?", re.I)),
]
GM_HEAD = re.compile(r"(\d{1,3}(?:\s?\d{3})+)\s*km\s*/\s*(\d{1,3}(?:,\d{3})*)\s*mi")


def _median(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0.0


def header_rows(fr: dict) -> list[dict]:
    """Header rows of interval grids: a label cell (Months / Miles x 1,000 / (km x 1,000) / Or Years:
    ...) followed on its baseline by numbers (or by numbers printed turned, one per column)."""
    out = []
    for row in fr["rows"]:
        i = 0
        while i < len(row):
            phrase, prev, hit = "", None, None
            for k in range(i, min(i + 8, len(row))):
                v = row[k]
                if prev is not None and v["x0"] - prev["x1"] > 1.2 * v["size"]:
                    break
                # 'INTERVALSMonths': a diagonal heading glued to the label cell
                piece = re.sub(r"^[A-Z]{3,}(?=(?:Months?|Miles|Km|MONTHS)\b)", "", v["t"]) if k == i else v["t"]
                phrase = (phrase + " " + piece).strip()
                prev = v
                for kind, rx in HEAD_KINDS:
                    if rx.fullmatch(phrase):
                        hit = (kind, phrase, k)
            if hit is None or (i > 0 and row[i]["x0"] - row[i - 1]["x1"] < 1.5 * row[i]["size"]
                               and re.fullmatch(r"[\d,.()]+", row[i - 1]["t"])):
                # 'Inspect every 8,000 miles (13,000 km)': a unit after a number is not a header label
                i += 1
                continue
            kind, phrase, k = hit
            last = row[k]
            vals = [(w["cx"], float(NUM_WORD.fullmatch(w["t"]).group(1).replace(",", "")), w)
                    for w in row[k + 1:] if NUM_WORD.fullmatch(w["t"])]
            y0, y1 = min(w["y0"] for w in row[i:k + 1]), max(w["y1"] for w in row[i:k + 1])
            cy = (y0 + y1) / 2
            for vw in fr["vwords"]:
                if vw["x0"] > last["x1"] and vw["y0"] - 2 <= cy <= vw["y1"] + 2 and NUM_WORD.fullmatch(vw["t"].replace(" ", "")):
                    vals.append((vw["cx"], float(NUM_WORD.fullmatch(vw["t"].replace(" ", "")).group(1).replace(",", "")), vw))
            vals.sort(key=lambda t: t[0])
            if len(vals) >= 3 and all(b[1] > a[1] for a, b in zip(vals, vals[1:])):
                out.append({"kind": kind, "phrase": phrase, "thousand": bool(re.search(r"1,?000", phrase)), "x1": last["x1"],
                            "y0": y0, "y1": y1, "cy": cy, "vals": [(cx, v) for cx, v, _ in vals],
                            "bottom": max([y1] + [w["y1"] for _, _, w in vals])})
            i = k + 1
    return out


def grid_columns(fr: dict, label_y: float, family: str = "rows") -> dict | None:
    """The interval columns of the grid above a row label: [{cx, miles, km, months}] with the
    pitch, the left edge of the data area and the bottom of the heading."""
    if family == "gm":
        heads = []
        for vw in fr["vwords"]:
            m = GM_HEAD.search(vw["t"])
            if m and vw["cy"] < label_y:
                heads.append({"cx": vw["cx"], "km": int(re.sub(r"\s", "", m.group(1))), "miles": int(m.group(2).replace(",", "")),
                              "months": None, "y1": vw["y1"], "cy": vw["cy"]})
        if len(heads) < 5:
            return None
        # the heading block nearest above the row (a page can print two charts)
        top = max(h["cy"] for h in heads)
        heads = [h for h in heads if abs(h["cy"] - top) < 60]
        heads.sort(key=lambda h: h["cx"])
        pitch = _median([b["cx"] - a["cx"] for a, b in zip(heads, heads[1:])])
        return {"cols": heads, "pitch": pitch, "data_x0": heads[0]["cx"] - 0.6 * pitch,
                "head_bottom": max(h["y1"] for h in heads), "problem": None}
    if family == "stacked":
        return stacked_columns(fr, label_y)
    heads = [h for h in header_rows(fr) if h["cy"] < label_y]
    if not heads:
        return None
    base_pick = max(heads, key=lambda h: h["cy"])  # the heading block nearest above the row
    block = [h for h in heads if abs(h["cy"] - base_pick["cy"]) < 80]
    by_kind = {}
    for h in sorted(block, key=lambda h: h["cy"]):
        by_kind[h["kind"]] = h
    base = by_kind.get("miles") or by_kind.get("km") or by_kind.get("months") or by_kind.get("years")
    vals = sorted(base["vals"])
    pitch = _median([b[0] - a[0] for a, b in zip(vals, vals[1:])])
    cols = [{"cx": cx, "miles": None, "km": None, "months": None} for cx, _ in vals]
    problem = None

    def put(kind, h, mult):
        for cx, v in h["vals"]:
            k = min(range(len(cols)), key=lambda i: abs(cols[i]["cx"] - cx))
            if abs(cols[k]["cx"] - cx) <= 0.5 * pitch:
                cols[k][kind] = _ival(round(v * mult, 3))

    mi, km = by_kind.get("miles"), by_kind.get("km")
    mi_mult = 1000 if mi and (mi["thousand"] or max(v for _, v in mi["vals"]) < 1000) else 1
    km_mult = 1000 if km and (km["thousand"] or max(v for _, v in km["vals"]) < 1000) else 1
    if mi and not mi["thousand"] and mi_mult == 1000:
        # 'Miles 7.5 15 ...' without 'x 1,000': thousands only when the km row agrees (km / miles ~1.6)
        ok = km is not None and all(
            1.5 <= (kv / mv) <= 1.7 for (_, mv), (_, kv) in zip(sorted(mi["vals"]), sorted(km["vals"])) if mv)
        if not ok:
            problem = "header_units_unclear"
    if mi:
        put("miles", mi, mi_mult)
    if km:
        put("km", km, km_mult)
    if by_kind.get("months"):
        put("months", by_kind["months"], 1)
    elif by_kind.get("years"):
        put("months", by_kind["years"], 12)
    bottom = max(h["bottom"] for h in by_kind.values())
    return {"cols": cols, "pitch": pitch, "data_x0": cols[0]["cx"] - 0.6 * pitch, "head_bottom": bottom, "problem": problem,
            "kinds": sorted(by_kind)}


def stacked_columns(fr: dict, label_y: float) -> dict | None:
    """Nissan / Infiniti grids: each column heading cell stacks miles x 1,000, (km x 1,000) and
    months ('7.5 / (12) / 6'); the label cell 'Miles x 1,000 (km x 1,000) Months' wraps on its own
    lines. The km row (numbers in parentheses) anchors each column; the miles number is the one
    just above it, the months number the one just below."""
    page_t = " ".join(w["t"] for w in fr["words"])
    if not (re.search(r"\bMiles\b", page_t, re.I) and re.search(r"\b1,000\)?", page_t)):  # 'Miles x / 1,000' wraps
        return None
    nums = [w for w in fr["words"] if w["cy"] < label_y and re.fullmatch(r"\(?\d+(?:\.\d+)?\)?", w["t"])]
    kms = [w for w in nums if w["t"].startswith("(") and w["t"].endswith(")")]
    rows = _rows(kms)
    rows = [r for r in rows if len(r) >= 4]
    if not rows:
        return None
    row = max(rows, key=lambda r: r[0]["cy"])
    pitch = _median([b["cx"] - a["cx"] for a, b in zip(row, row[1:])])
    cols, bottom = [], row[0]["y1"]
    for k in row:
        size = k["size"]
        above = [w for w in nums if w is not k and abs(w["cx"] - k["cx"]) < 0.4 * pitch and 0 < k["cy"] - w["cy"] < 2.2 * size
                 and not w["t"].startswith("(")]
        below = [w for w in nums if w is not k and abs(w["cx"] - k["cx"]) < 0.4 * pitch and 0 < w["cy"] - k["cy"] < 2.2 * size
                 and not w["t"].startswith("(")]
        mi = max(above, key=lambda w: w["cy"]) if above else None
        mo = min(below, key=lambda w: w["cy"]) if below else None
        cols.append({"cx": k["cx"], "miles": _ival(round(float(mi["t"]) * 1000, 3)) if mi else None,
                     "km": _ival(round(float(k["t"].strip("()")) * 1000, 3)), "months": int(float(mo["t"])) if mo else None})
        if mo:
            bottom = max(bottom, mo["y1"])
    problem = None if all(c["miles"] for c in cols) else "header_units_unclear"
    return {"cols": cols, "pitch": pitch, "data_x0": cols[0]["cx"] - 0.6 * pitch, "head_bottom": bottom, "problem": problem,
            "kinds": ["miles", "km", "months"]}


def lkey(text: str) -> str:
    """Row-label key: compact, '&' and 'and' alike (one page prints 'Brake lines and cables', the
    continuation page 'Brake lines & cables')."""
    return compact(text).replace("and", "&")


def label_places(fr: dict, grid: dict, label: str) -> list[dict]:
    """Places of a row label in the label area left of the grid (consecutive lines whose text holds
    the label): [{y0, y1, x0}]."""
    target = lkey(label)
    if len(target) < 3:
        return []
    if grid["data_x0"] < 1e8:
        # a ruled label cell holding the label (a merged item cell beside engine sub-cells)
        cells = [c for c in page_cells(fr) if c["box"][2] <= grid["data_x0"] + 3 and c["box"][1] >= grid["head_bottom"] - 3
                 and target in lkey(c["t"])]
        if cells:
            out = []
            for c in sorted(cells, key=lambda c: len(c["t"])):
                ws = c["words"]
                out.append({"y0": min(w["y0"] for w in ws), "y1": max(w["y1"] for w in ws), "x0": min(w["x0"] for w in ws),
                            "size": _median([w["size"] for w in ws])})
            return out
    words = [w for w in fr["words"] if w["x1"] <= grid["data_x0"] + 2 and w["cy"] > grid["head_bottom"]
             and not re.fullmatch(r"[RIX@✓]\*?\d*|\(cid:\d+\)", w["t"])]  # marks on the label's baseline
    rows = _rows(words)
    # first pass: whole lines of the label area; second pass: only the first cell of each line (a
    # wrapped label 'Spark plugs (Iridium/Platinum - tipped / type)' beside a 'See NOTE (6)' cell)
    for lines in (rows, [_first_cell(r) for r in rows]):
        texts = [lkey(" ".join(w["t"] for w in ln)) for ln in lines]
        out = []
        for i in range(len(lines)):
            acc = ""
            for j in range(i, min(i + 10, len(lines))):
                acc += texts[j]
                if target in acc:
                    if not (j > i and target in "".join(texts[i + 1:j + 1])):
                        ws = [w for ln in lines[i:j + 1] for w in ln]
                        out.append({"y0": min(w["y0"] for w in ws), "y1": max(w["y1"] for w in ws), "x0": min(w["x0"] for w in ws),
                                    "size": _median([w["size"] for w in ws])})
                    break
                if len(acc) > len(target) + 300:
                    break
        if out:
            return out
    return []


def _first_cell(row: list[dict]) -> list[dict]:
    """The words of a visual row up to the first gap wider than one and a half glyph heights."""
    out = row[:1]
    for w in row[1:]:
        if w["x0"] - out[-1]["x1"] > 1.5 * w["size"]:
            break
        out.append(w)
    return out


def data_rules(fr: dict, grid: dict) -> list[float]:
    """y of the horizontal rules that run across the interval columns (at least half of them)."""
    xs = [c["cx"] for c in grid["cols"]]
    buckets: dict[float, set] = {}
    for x0, x1, y in fr["hr"]:
        crossed = {i for i, x in enumerate(xs) if x0 - 1 <= x <= x1 + 1}
        if not crossed:
            continue
        key = next((k for k in buckets if abs(k - y) <= 1.5), y)
        buckets.setdefault(key, set()).update(crossed)
    return sorted(y for y, s in buckets.items() if len(s) >= max(1, len(xs) // 2))


def row_bands(fr: dict, grid: dict, place: dict) -> tuple[tuple[float, float], list[tuple[float, float]]]:
    """The label's band (between the rules crossing the label column) and the data bands (between
    the rules across the columns) that belong to it: one band, the merged band that holds the
    label band, or the sub-rows inside it."""
    ys = rules_at(fr, place["x0"] + 1.5)
    slack = max(1.0, 0.4 * place["size"])  # glyph boxes can reach over a cell's ruling
    above = [y for y in ys if y <= place["y0"] + slack]
    below = [y for y in ys if y >= place["y1"] - slack]
    pad = 0.6 * place["size"]
    lab = (above[-1] if above else place["y0"] - pad, below[0] if below else place["y1"] + pad)
    dys = data_rules(fr, grid)
    bands = [(a, b) for a, b in zip(dys, dys[1:]) if b - a > 2]
    inside = [b for b in bands if b[0] >= lab[0] - 1.5 and b[1] <= lab[1] + 1.5]
    if inside:
        return lab, inside
    holder = [b for b in bands if b[0] <= lab[0] + 1.5 and b[1] >= lab[1] - 1.5]
    if holder:
        return lab, holder[:1]
    return lab, [lab]


def band_marks(fr: dict, grid: dict, band: tuple[float, float], mark_re) -> tuple[list[tuple[int, str]], str]:
    """Marks of a data band mapped to the nearest column (within half a pitch), and the band's other
    text (an interval written across the columns)."""
    marks, text_words = [], []
    y0, y1 = band
    for w in fr["words"]:
        if not (y0 <= w["cy"] <= y1) or w["cx"] < grid["data_x0"] or w["cx"] > grid["cols"][-1]["cx"] + 0.6 * grid["pitch"]:
            continue
        if mark_re.fullmatch(w["t"]):
            k = min(range(len(grid["cols"])), key=lambda i: abs(grid["cols"][i]["cx"] - w["cx"]))
            if abs(grid["cols"][k]["cx"] - w["cx"]) <= 0.5 * grid["pitch"]:
                marks.append((k, w["t"]))
                continue
        text_words.append(w)
    text = " ".join(" ".join(x["t"] for x in r) for r in _rows(text_words))
    return sorted(marks), text


def sub_label(fr: dict, grid: dict, place: dict, band: tuple[float, float]) -> str:
    """Text of the label area inside a data band, right of the main label column (an engine cell)."""
    ws = [w for w in fr["words"] if band[0] <= w["cy"] <= band[1] and w["x1"] <= grid["data_x0"] + 2
          and w["x0"] > place["x0"] + 8]
    return " ".join(" ".join(x["t"] for x in r) for r in _rows(ws))


def engine_key(it: dict) -> tuple[str | None, bool]:
    app = it.get("applicability") or {}
    if app.get("engine_except"):
        return str(app["engine_except"]), True
    if app.get("engine"):
        return str(app["engine"]), False
    return None, False


def pick_band(fr, grid, place, bands, it, quote_label: str) -> tuple[tuple[float, float] | None, str]:
    """The data band of the item among sub-rows: the one whose engine cell names the item's engine
    (or is named in the quote); one band -> that band."""
    if len(bands) == 1:
        return bands[0], sub_label(fr, grid, place, bands[0])
    eng, exc = engine_key(it)
    subs = [(b, sub_label(fr, grid, place, b)) for b in bands]
    if eng:
        for b, s in subs:
            cs = compact(s)
            if compact(eng) in cs and (("except" in cs) == exc):
                return b, s
    for b, s in subs:
        if s and compact(s) in compact(quote_label):
            return b, s
    return None, " | ".join(s for _, s in subs)


def grid_row(ctx, src, page_no: int, label: str, it: dict, mark_re, family: str = "rows",
             quote_label: str | None = None) -> dict:
    """Read the item's row of a grid page: {'ok', 'reasons', 'marks': [(col, mark)], 'grid', 'text',
    'sub', 'rot'}."""
    geo = ctx.docs.geo(src, page_no)
    if geo is None:
        return {"reasons": ["pdf_page_missing"]}
    rots = [geo.rotation()] + [r for r in ("none", "ccw", "cw") if r != geo.rotation()]
    last = {"reasons": ["grid_header_not_found"]}
    for rot in rots:
        fr = geo.frame(rot)
        probe = label_places(fr, {"data_x0": 1e9, "head_bottom": -1e9}, label)
        for place0 in probe or [{"y0": 1e9}]:
            grid = grid_columns(fr, place0["y0"], family)
            if grid is None:
                continue
            places = [p for p in label_places(fr, grid, label)
                      if not probe or (p["y0"] <= place0["y1"] + 1 and p["y1"] >= place0["y0"] - 1)]
            if not places:
                last = {"reasons": ["row_label_not_found"], "grid": grid}
                continue
            place = places[0]
            lab, bands = row_bands(fr, grid, place)
            band, sub = pick_band(fr, grid, place, bands, it, quote_label or label)
            if band is None:
                return {"reasons": ["sub_row_ambiguous"], "grid": grid, "text": sub, "rot": rot}
            marks, text = band_marks(fr, grid, band, mark_re)
            return {"reasons": [grid["problem"]] if grid.get("problem") else [], "marks": marks, "grid": grid,
                    "text": text, "sub": sub, "rot": rot, "band": band}
    return last


def points_of(grid: dict, cols: list[int]) -> tuple[list, list, list]:
    c = grid["cols"]
    miles = [c[k]["miles"] for k in cols if c[k]["miles"] is not None]
    km = [c[k]["km"] for k in cols if c[k]["km"] is not None]
    months = [c[k]["months"] for k in cols if c[k]["months"] is not None]
    if len(miles) != len(cols):
        miles = []
    if len(km) != len(cols):
        km = []
    if len(months) != len(cols):
        months = []
    return miles, km, months


def cell_at(fr: dict, x: float, y: float) -> tuple[float, float, float, float] | None:
    """The ruled cell (x0, y0, x1, y1) of a table that contains the point: the nearest vertical rules
    crossing y left and right of x, the nearest horizontal rules crossing x above and below y."""
    ys = rules_at(fr, x)
    above = [r for r in ys if r <= y]
    below = [r for r in ys if r > y]
    xs = sorted(xv for y0, y1, xv in fr["vr"] if y0 - 1 <= y <= y1 + 1)
    left = [v for v in xs if v <= x]
    right = [v for v in xs if v > x]
    if not above or not below:
        return None
    return (left[-1] if left else -1e9, above[-1], right[0] if right else 1e9, below[0])


def page_cells(fr: dict) -> list[dict]:
    """Ruled cells of the page holding text: [{box: (x0, y0, x1, y1), t}] (words grouped by the cell
    that contains their centre)."""
    if "cells" in fr:
        return fr["cells"]
    groups: dict[tuple, list] = {}
    for w in fr["words"]:
        box = cell_at(fr, w["cx"], w["cy"])
        if box is None:
            continue
        key = tuple(round(v, 1) for v in box)
        groups.setdefault(key, []).append(w)
    cells = []
    for box, ws in groups.items():
        cells.append({"box": box, "t": " ".join(" ".join(x["t"] for x in r) for r in _rows(ws)), "words": ws})
    fr["cells"] = cells
    return cells


def sibling_cells(fr: dict, cell: dict) -> list[dict]:
    """Cells of the same table row: beside the cell, spanning its centre line."""
    x0, y0, x1, y1 = cell["box"]
    cy = (y0 + y1) / 2
    out = []
    for c in page_cells(fr):
        a0, b0, a1, b1 = c["box"]
        if c is cell or not (b0 - 1 <= cy <= b1 + 1):
            continue
        if a1 <= x0 + 1 or a0 >= x1 - 1:
            out.append(c)
    return sorted(out, key=lambda c: abs((c["box"][0] + c["box"][2]) / 2 - (x0 + x1) / 2))


def head_text(grid: dict, k: int) -> str:
    c = grid["cols"][k]
    return "/".join(str(c[x]) for x in ("miles", "km", "months") if c.get(x) is not None)


# ============================================================================ results

def res(ok: bool, reasons: list[str], method: str, evidence: str, warnings: list[str] | None = None) -> dict:
    return {"ok": ok and not reasons, "reasons": list(dict.fromkeys(reasons)), "method": method,
            "evidence": canon(evidence)[:300], "warnings": list(dict.fromkeys(warnings or []))}


def fail(reason: str, method: str, evidence: str = "") -> dict:
    return res(False, [reason], method, evidence)


MARK_TAIL = re.compile(r"(?:\s*(?:\b[RIX]+(?:\*\d*)?\b|[RIX]\*\d*|[@✓]+|[-–]|\*\d+))+\s*$")


def strip_marks(quote: str) -> str:
    t = canon(quote)
    s = MARK_TAIL.sub("", t).strip()
    return s if len(s) >= 3 else t


BULLETS = "❑□☐●•■◆▪\u0086"  # U+0086: the check box of the Mitsubishi booklets (symbol font)


def is_bullet(ch: str) -> bool:
    return ch in BULLETS or 0xE000 <= ord(ch) <= 0xF8FF


class Ctx:
    def __init__(self, docs: Docs, make: str):
        self.docs, self.make = docs, make
        self.line = ""  # the staging line of the item being checked (scope_excludes_line)
        self._lines = None

    def lines(self) -> set[str]:
        """The make's staging lines (compact names): a model a schedule excludes that is a line of its own is
        not an edition of the item's line."""
        if self._lines is None:
            root = WORK / self.make / "staging"
            self._lines = {compact(p.name.replace("-", " ")) for p in root.iterdir() if p.is_dir()} if root.exists() else set()
        return self._lines

    def located(self, src: dict, cite: dict) -> list[tuple[int, tuple[int, int]]]:
        """(page index, span) of every place of the cite's quote on its cited pages."""
        pages = self.docs.pages(src)
        out = []
        if pages is None:
            return out
        for p in cite.get("pages") or []:
            if 0 < p <= len(pages):
                out += [(p - 1, s) for s in pages[p - 1].spans(cite["quote"])]
        return out


def quote_status(ctx: Ctx, src: dict, cite: dict) -> str | None:
    """'full': the quote is on a cited page; 'label': only its row label (marks stripped) is;
    'split': the quote runs over two consecutive cited pages; None: not found."""
    pages = ctx.docs.pages(src)
    if pages is None:
        return None
    pgs = [p for p in (cite.get("pages") or []) if 0 < p <= len(pages)]
    if any(pages[p - 1].has(cite["quote"]) for p in pgs):
        return "full"
    if len(pgs) > 1 and CText(" ".join(pages[p - 1].text for p in pgs)).has(cite["quote"]):
        return "split"
    label = strip_marks(cite["quote"])
    if label != canon(cite["quote"]) and any(pages[p - 1].has(label) for p in pgs):
        return "label"
    return None


def governing_verbs(text: str, job: str) -> set[str]:
    """Actions of the verbs that govern the job's name in a list-like text ('checking brake fluid
    and, if necessary, changing the engine oil'): the nearest verb before each mention."""
    t = canon(text)
    t = CONDITIONAL_VERB.sub(lambda m: " " * len(m.group(0)), t)  # 'inspect and replace ... if necessary'
    t = NEGATED_VERB.sub(lambda m: " " * len(m.group(0)), t)
    pattern = JOB_NAMES.get(job)
    out = set()
    if not pattern:
        return out
    verbs = []
    for action, vp in ACTION_VERBS.items():
        verbs += [(m.start(), action) for m in re.finditer(rf"\b(?:{vp})", t, re.I)]
    verbs.sort()
    for m in re.finditer(pattern, t, re.I):
        before = [(pos, a) for pos, a in verbs if pos < m.start()]
        if before:
            out.add(before[-1][1])
            # 'Inspect and replace the PCV valve', 'Inspect/replace ...': every verb of the chain
            k = len(before) - 1
            while k > 0:
                gap = t[before[k - 1][0]:before[k][0]]
                if not re.fullmatch(r"\w+\s*(?:,|/|and|or|and/or)\s*", gap, re.I):
                    break
                out.add(before[k - 1][1])
                k -= 1
        after = [a for pos, a in verbs if m.end() <= pos <= m.end() + 25]
        if not before and after:
            out.add(after[0])
    return out


# ============================================================================ families: text

def fam_text_quotes(ctx: Ctx, it: dict, src: dict, cites: list[dict], context: str | None = None,
                    label_of=None, extra_verbs: set | None = None) -> dict:
    """Generic text family: each quote is (or contains) the clause carrying the item."""
    texts = []
    labels = []
    for c in cites:
        texts.append(canon(c["quote"]))
        if label_of:
            labels.append(label_of(c))
    label = " ".join(x for x in labels if x)
    reasons, ev, warn = best_text_check(it, texts, label, context, extra_verbs)
    return res(not reasons, reasons, "text", ev, warn)


def fam_tesla(ctx, it, src, cites):
    return fam_text_quotes(ctx, it, src, cites)


def fam_mercedes(ctx, it, src, cites):
    """mbusa.com 'What is Service A/B?': the visit interval, then 'Service X includes:' the jobs."""
    out = []
    for c in cites:
        q = canon(c["quote"])
        m = re.search(r"includes:", q, re.I)
        if not m:
            out.append(fail("includes_list_not_found", "text", q[:120]))
            continue
        clause, listing = q[:m.start()], q[m.end():]
        entries = [e for e in re.split(r"\s(?=[A-Z])", listing) if e.strip()]
        named = [e for e in entries if job_named(it["job"], e)]
        service = (it.get("applicability") or {}).get("service")
        reasons = []
        if service and not re.search(rf"\b{re.escape(service)}\b", clause, re.I):
            reasons.append("service_not_stated")
        if not named:
            reasons.append("job_not_named")
        verbs = set()
        for e in named:
            verbs |= verbs_in(e) | ({"REPLACE"} if re.search(r"exchange", e, re.I) else set())
        if named and it["action"] not in verbs:
            reasons.append("action_mismatch")
        warn = []
        r2, part = check_clause(it, clause, warn)
        reasons += r2
        reasons += check_condition(it, "", "NORMAL")  # Service A / B: the regular schedule
        out.append(res(not reasons, reasons, "text", f"{part.strip()} | {'; '.join(named)}", warn))
    return combine_groups(out)


def fam_bmw(ctx, it, src, cites):
    """Condition Based Service: the quote names the job and its verb; the page names CBS."""
    out = []
    pages = ctx.docs.pages(src)
    for c in cites:
        q = canon(c["quote"])
        reasons = job_reasons(it["job"], q)
        if "job_not_named" not in reasons and it["action"] not in governing_verbs(q, it["job"]):
            reasons.append("action_mismatch")
        page = " ".join(pages[p - 1].text for p in c.get("pages") or [] if pages and 0 < p <= len(pages))
        if it["schedule_system"] != "CBS" or not re.search(r"Condition Based Service|\bCBS\b", page):
            reasons.append("schedule_system_not_stated")
        if it.get("interval_km") or it.get("interval_months") or it.get("max_interval_km") or it.get("max_interval_months"):
            reasons.append("interval_not_stated")
        reasons += check_condition(it, "", "NORMAL")  # Condition Based Service is not a severe section
        out.append(res(not reasons, reasons, "monitor", q))
    return combine_groups(out)


# ---------------------------------------------------------------- maintenance cards (Audi, VW)

CARD_SCHEDULE = re.compile(r"(?<![\d.])(\d)\.(\d)\s+((?:MY \d{4} )?(?:Audi |VW )?Maintenance Schedule(?:\s*\([^)]*\))?"
                           r"(?:\s*-\s*(?:United States|Canada|USA))?)")
CARD_SECTION = re.compile(r"(?<![\d.])(\d)\.(\d)\.(\d)\s+(?:(Minor|Standard|Extended|Major) Maintenance|(Additional) Maintenance Items)")
CARD_NOTE = re.compile(r"(?<![\w)])(\d)\)\s+((?:First\s+)?(minor|standard|extended|major)\s+maintenance\s+services?\b.*?)"
                       r"(?=\s\d\)\s+(?:First|Minor|Standard|Extended|Major)\b|[-]|\s+all completed items|\s+\d\.\d|\s+Labor Item|$)",
                       re.I)


def card_stream(pages: list[CText]) -> tuple[str, list[int]]:
    text, offsets = "", []
    for p in pages:
        offsets.append(len(text))
        text += p.text + " "
    return text, offsets


def card_layout(stream: str) -> dict:
    """Schedules (number -> (title, start)) and sections ([(pos, schedule number, section)]) of a
    maintenance card, and its interval footnotes ([(pos, section, text)])."""
    schedules = {}
    for m in CARD_SCHEDULE.finditer(stream):
        schedules.setdefault(f"{m.group(1)}.{m.group(2)}", (m.group(3), m.start()))
    sections = [(m.start(), f"{m.group(1)}.{m.group(2)}", (m.group(4) or m.group(5)).lower()) for m in CARD_SECTION.finditer(stream)]
    notes = [(m.start(), m.group(3).lower(), m.group(2)) for m in CARD_NOTE.finditer(stream)]
    return {"schedules": schedules, "sections": sections, "notes": notes}


def card_scope(schedule_title: str | None) -> list[str]:
    """A schedule of the card that is not the US schedule of a combustion / hybrid vehicle."""
    t = schedule_title or ""
    out = []
    if re.search(r"Canada", t):
        out.append("schedule_canada")
    if re.search(r"Electric Vehicles|Routan Only", t):
        out.append("schedule_other_powertrain")
    return out


def fam_card(ctx, it, src, cites):
    """Audi / VW maintenance cards: Minor / Standard / Extended service lists take the interval of
    the section's footnote; Additional Maintenance Items print their own interval."""
    pages = ctx.docs.pages(src)
    if pages is None:
        return fail("page_text_missing", "text")
    stream, offsets = card_stream(pages)
    lay = card_layout(stream)
    foot_cites = [canon(re.sub(r"^\s*\d\)\s*", "", c["quote"])) for c in cites if (c.get("locator") or "").endswith("interval footnote")]
    per_cite = []
    for c in cites:
        loc = c.get("locator") or ""
        if loc.endswith("interval footnote"):
            continue
        hits = ctx.located(src, c)
        wanted = loc.split()[0].lower() if loc else None
        cands = [card_place(it, lay, stream, offsets[pi] + s, canon(c["quote"]), foot_cites, wanted) for pi, (s, e) in hits]
        cands = [x for x in cands if x is not None]
        if not cands:
            per_cite.append(fail("quote_not_on_page" if not hits else "section_not_found", "text", c["quote"]))
            continue
        # the same text printed in several places: the place that states the item (else the first)
        per_cite.append(min(cands, key=lambda r: (not r["ok"], len(r["reasons"]))))
    if not per_cite:
        return fail("no_usable_cite", "text")
    good = [r for r in per_cite if r["ok"]]
    if good:
        # one confirming row of the document is enough; the other rows cited are reported
        extra = [f"other_cite:{x}" for r in per_cite if not r["ok"] for x in r["reasons"]]
        return res(True, [], "text", good[0]["evidence"], good[0]["warnings"] + extra)
    return min(per_cite, key=lambda r: len(r["reasons"]))


def card_place(it: dict, lay: dict, stream: str, pos: int, label: str, foot_cites: list[str],
               wanted: str | None = None) -> dict | None:
    """The item checked at one place of the card stream (section list row or additional item)."""
    before = [x for x in lay["sections"] if x[0] <= pos]
    if not before:
        return None
    _, sched, section = before[-1]
    title = lay["schedules"].get(sched, (None, None))[0]
    scope = card_scope(title)
    inherited = ""
    if section == "minor" and wanted in ("standard", "extended"):
        # 'Standard Maintenance: Perform Minor Maintenance': a minor row is part of the standard service
        heads = [x for x in lay["sections"] if x[1] == sched and x[2] == wanted]
        if heads:
            h = heads[0][0]
            nxt = min([x[0] for x in lay["sections"] if x[0] > h] + [len(stream)])
            if re.search(r"Perform (?:Minor|Standard) Maintenance", stream[h:nxt]):
                section, inherited = wanted, f" (via 'Perform Minor Maintenance' of the {wanted} list)"
    if section != "additional":
        reasons, warn = list(scope), []
        reasons += job_reasons(it["job"], label)
        reasons += check_action(it, label, label)
        # the footnote of this section inside the same schedule (between its heading and the next)
        first_sec = min(p for p, sn, _ in lay["sections"] if sn == sched)
        bounds = [p for _, p in lay["schedules"].values()] + [p for p, sn, _ in lay["sections"] if sn != sched]
        start = lay["schedules"][sched][1] if sched in lay["schedules"] else max([p for p in bounds if p < first_sec], default=0)
        end = min([p for p in bounds if p > start and p > first_sec] + [len(stream)])
        own = [n for n in lay["notes"] if n[1] == section and start <= n[0] < end]
        if not own:
            return res(False, reasons + ["interval_footnote_not_found"], "text", f"[{section}] {label[:80]}")
        note = min(own, key=lambda n: abs(n[0] - pos))[2]
        if not any(compact(q) in compact(note) for q in foot_cites):
            reasons.append("footnote_not_the_section_one")
        r2, part = check_clause(it, note, warn)
        reasons += r2
        reasons += check_condition(it, note, "NORMAL")
        return res(not reasons, reasons, "text", f"[{section} {sched} {title or ''}]{inherited} {label[:60]} <- {part[:140]}", warn)
    # Additional Maintenance Items: the row label is the quote's own head; a quote that is only an
    # interval (a further interval line of the row) takes the label of its bullet
    split = re.compile(r"(?<![A-Za-z])(?:Every|EVERY|First|At|Only once|\d+ years)\s*[\d,]*")
    head = split.split(label)[0]
    if len(head.strip()) < 4:
        start = max((i for i in range(max(0, pos - 2500), pos + 1) if is_bullet(stream[i])), default=pos)
        head = split.split(canon(stream[start:pos] + " " + label))[0]
    reasons, ev, warn = best_text_check(it, [label], head, "NORMAL", job_text=head + " " + label)
    return res(not reasons and not scope, scope + reasons, "text", f"{head[:60]} | {ev}", warn)


# ---------------------------------------------------------------- Honda (Maintenance Minder)

def footnote_text(page: str, marker: str) -> str | None:
    """Text of the footnote '*N:' printed on the page."""
    m = re.search(rf"(?<![\w])\*\s?{re.escape(marker)}\s*:\s*(.+?)(?=\s\*\s?\d\s*:|\s#\s*:|\sCODE\b|\s\d\s*[●•]|$)", page)
    return m.group(1) if m else None


def footnote_around(page: str, s: int) -> str:
    """The whole footnote ('*N: ...') that contains position s of the page (the conditions are
    often stated in the sentences before the interval sentence)."""
    heads = [m for m in re.finditer(r"(?<![\w])\*\s?\d\s*:", page[:s + 1])]
    if not heads:
        return ""
    start = heads[-1].start()
    m = re.search(r"\s\*\s?\d\s*:|\s#\s*:|\sCODE\b", page[s:])
    return page[start:s + (m.start() if m else len(page) - s)]


MINDER_CODE = re.compile(r"(?<![\w*#/.,:(])([AB0-9])(?:\s+|\s*[●•]\s*)(?=[A-Z])")


def fam_honda(ctx, it, src, cites):
    pages = ctx.docs.pages(src)
    if pages is None:
        return fail("page_text_missing", "text")
    out = []
    for c in cites:
        loc = c.get("locator") or ""
        hits = ctx.located(src, c)
        if not hits:
            out.append(fail("quote_not_on_page", "text", c["quote"]))
            continue
        pi, (s, e) = hits[0]
        page = pages[pi].text
        q = canon(c["quote"])
        if it["schedule_system"] == "MAINTENANCE_MINDER":
            reasons = []
            if not re.search(r"Maintenance Minder", page, re.I):
                reasons.append("schedule_system_not_stated")
            reasons += job_reasons(it["job"], q)
            # an item listed under '● Inspect these items:' takes the verb of that list head; a row
            # that runs into the next one ('Replace engine oil and oil filter ● Inspect front and
            # rear brakes') takes the verb governing the job's name
            if verbs_in(q):
                gov = governing_verbs(q, it["job"])
                if it["action"] not in (gov or verbs_in(q)):
                    reasons.append("action_mismatch")
            else:
                heads = list(re.finditer(r"\b(Inspect|Check|Replace|Rotate)\b[^:●]{0,40}:", page[max(0, s - 800):s]))
                reasons += check_action(it, q, heads[-1].group(0) if heads else "")
            code = (it.get("applicability") or {}).get("minder_code")
            if code:
                codes = list(MINDER_CODE.finditer(page[:s + 1]))
                found = codes[-1].group(1) if codes else None
                if found != str(code):
                    reasons.append("minder_code_not_stated")
            if it.get("max_interval_months") or it.get("max_interval_km"):
                marks = re.findall(r"\*\s?(\d)", q)
                ok_max = False
                for mk in marks:
                    ft = footnote_text(page, mk)
                    if ft and (not it.get("max_interval_months") or it["max_interval_months"] in scan_numbers(ft)["months"]) \
                            and job_named(it["job"], ft):
                        ok_max = True
                if not ok_max:
                    reasons.append("max_interval_not_stated")
            if it.get("interval_km") or it.get("interval_months"):
                reasons.append("interval_not_stated")
            reasons += check_condition(it, "", "NORMAL")  # the Maintenance Minder table is not a severe section
            out.append(res(not reasons, reasons, "monitor", f"code {code}: {q}"))
            continue
        # fixed interval: a footnote of a minder row or a side note, a clause of its own
        label = q
        note = footnote_around(page, s)
        if not job_named(it["job"], q):
            # 'If you drive in dusty conditions, replace every 15,000 miles': the job is in the row
            # that carries the footnote marker
            mk = re.match(r"\*\s?(\d)", note)
            if mk:
                rows = [m for m in re.finditer(rf"([A-Za-z][^●•*]{{2,80}}?)\s*\*\s?{mk.group(1)}(?!\d)(?!\s*:)", page)]
                label = " ".join(m.group(1) for m in rows) + " " + q
        context = "SEVERE" if note and SEVERE_WORDS.search(note) else None
        reasons, ev, warn = best_text_check(it, [q], label, context, job_text=label)
        out.append(res(not reasons, reasons, "text", ev, warn))
    return combine_groups(out)


# ---------------------------------------------------------------- Mopar schedule data (JSON)

def fam_mopar(ctx, it, src, cites):
    data = ctx.docs.json(src)
    if data is None:
        return fail("json_source_missing", "json")
    plans = data if isinstance(data, list) else [data]
    plan_title = canon((it.get("applicability") or {}).get("plan") or "")
    out = []
    for c in cites:
        q = canon(c["quote"])
        cands = [p for p in plans if canon(p.get("title", "")) == plan_title] or plans
        if it["schedule_system"] == "OIL_LIFE_MONITOR":
            hit = None
            for p in cands:
                for anc in p.get("ancillary", []):
                    for s in anc.get("services", []):
                        if compact(f"{anc.get('title', '')} {s}") == compact(q):
                            hit = (anc.get("title", ""), s, p)
            if hit is None:
                out.append(fail("json_entry_not_found", "json", q))
                continue
            reasons = plan_engine_reasons(it, src, [hit[1], hit[2].get("title", ""), src.get("title", "")])
            if not re.search(r"oil change indicator|oil change interval", hit[0], re.I):
                reasons.append("schedule_system_not_stated")
            reasons += job_reasons(it["job"], hit[1])
            reasons += check_action(it, hit[1], hit[1])
            if it.get("interval_km") or it.get("interval_months"):
                reasons.append("interval_not_stated")
            reasons += check_condition(it, hit[1], "NORMAL")
            out.append(res(not reasons, reasons, "json", f"{hit[0]} {hit[1]}"))
            continue
        found = []
        for p in cands:
            mnt = p.get("maintenance", {})
            table = mnt.get("intervals", [])
            for s in mnt.get("services", []):
                if compact(s.get("description", "")) == compact(q):
                    found.append((p, table, s))
        if not found:
            out.append(fail("json_entry_not_found", "json", q))
            continue
        best = None
        for p, table, s in found:
            text = canon(s.get("description", ""))
            # the engine scope from the plan title / the document title ('Non SRT Engines' is not SRT)
            reasons, warn = plan_engine_reasons(it, src, [text, canon(p.get("title", "")), canon(src.get("title", ""))]), []
            pts, years = [], []
            for i in s.get("intervals") or []:
                if i >= len(table):
                    warn.append("json_point_index_out_of_range")  # a column the plan does not print
                    continue
                raw = str(table[i].get("distance") or "").replace(",", "").strip()
                pts.append(int(raw) if raw.isdigit() else None)
                yr = str(table[i].get("years") or "").strip()
                years.append(int(yr) if yr.isdigit() else None)
            if any(x is None for x in pts) or not pts:
                reasons.append("points_not_mileage")
            elif has_interval(text):
                r2, ev, warn = best_text_check(it, [text], text, None)
                reasons += r2
            else:
                reasons += compare_shape(it, pts, None, None, warn, km_printed=False)
                # the plan's points also print years ('30,000' / '3'): the time limit of the points
                ys = shape([y * 12 for y in years]) if years and all(y for y in years) else None
                if ys is not None:
                    if it.get("interval_months") is None:
                        warn.append("time_printed_not_in_item")
                    else:
                        occ = [o for o, _ in ys]
                        if it["occurrence"] not in occ or _ival(ys[occ.index(it["occurrence"])][1]) != it["interval_months"]:
                            reasons.append("months_mismatch")
                reasons += job_reasons(it["job"], text)
                reasons += check_action(it, text, text)
                reasons += check_condition(it, text, None)
            ev = f"{p.get('title', '')}: {text[:120]} @ {pts} mi"
            cand = (len(reasons), reasons, ev, warn)
            if best is None or cand[0] < best[0]:
                best = cand
        out.append(res(not best[1], best[1], "json", best[2], best[3]))
    return combine_groups(out)


# ---------------------------------------------------------------- GM (Chevrolet, Cadillac)

GM_MARK = re.compile(r"@")
GM_CHART = re.compile(r"Maintenance\s+Schedule\s+Additional\s+Required\s+Services\s*-\s*(Normal|Severe)", re.I)
GM_FOOT = re.compile(r"Footnotes\s*-+\s*Maintenance\s+Schedule\s+Additional\s+Required\s+Services\s*-\s*(Normal|Severe)", re.I)


def jobs_named(text: str) -> set[str]:
    return {j for j in JOB_NAMES if job_named(j, text)}


def gm_chart_condition(page: str) -> str | None:
    for m in GM_CHART.finditer(page):
        before = page[max(0, m.start() - 15):m.start()]
        if "Footnotes" in before:
            continue
        return m.group(1).upper()
    return None


def gm_footnote(pages: list[CText], grid_page: int, condition: str, n: int) -> tuple[str, int] | None:
    """Footnote (n) of the chart's footnote block (Normal / Severe), on the grid page or the next ones."""
    for p in range(grid_page - 1, min(grid_page + 3, len(pages))):
        t = pages[p].text
        heads = [m for m in GM_FOOT.finditer(t) if m.group(1).upper() == condition]
        start = heads[0].end() if heads else (0 if p > grid_page - 1 else None)
        if start is None:
            continue
        m = re.search(rf"\({n}\)\s+(.+?)(?=\s\(\d{{1,2}}\)\s|\s*Special Application Services|\s*Additional Maintenance and Care|$)", t[start:])
        if m:
            return m.group(1), p + 1
    return None


def fam_gm(ctx, it, src, cites):
    pages = ctx.docs.pages(src)
    out = []
    rows = [c for c in cites if "marks at" in (c.get("locator") or "")]
    nomark = [c for c in cites if "(no mileage mark)" in (c.get("locator") or "")]
    oil = [c for c in cites if "Oil Life System" in (c.get("locator") or "") or "Engine Oil Change (continued)" in (c.get("locator") or "")]
    heads_b = [c for c in cites if (c.get("locator") or "").endswith("interval heading")]
    bullets_b = [c for c in cites if re.search(r"(Normal Service|Severe Service|Owner Checks and Services), Every", c.get("locator") or "")]
    tire_b = [c for c in cites if (c.get("locator") or "") == "Maintenance Schedule: Tire Rotation and Required Services"]
    if it["schedule_system"] == "OIL_LIFE_MONITOR":
        text = " ".join(canon(c["quote"]) for c in oil)
        page = " ".join(pages[p - 1].text for c in oil for p in c.get("pages") or [])
        reasons = []
        reasons += job_reasons(it["job"], text)
        reasons += check_action(it, text, text)
        if not re.search(r"oil life|CHANGE ENGINE OIL SOON", page, re.I):
            reasons.append("schedule_system_not_stated")
        if it.get("max_interval_months") and it["max_interval_months"] not in scan_numbers(text)["months"]:
            reasons.append("max_interval_not_stated")
        if it.get("interval_km") or it.get("interval_months"):
            reasons.append("interval_not_stated")
        reasons += check_condition(it, "", "NORMAL")  # the Oil Life System paragraph is not a severe section
        return res(not reasons, reasons, "monitor", text)
    for c in rows:
        pg = (c.get("pages") or [None])[0]
        label = strip_marks(c["quote"])
        page = pages[pg - 1].text
        cond = gm_chart_condition(page)
        g = grid_row(ctx, src, pg, label, it, GM_MARK, "gm")
        reasons = list(g.get("reasons", []))
        if "marks" not in g:
            out.append(res(False, reasons, "grid", f"p.{pg} {label[:80]}"))
            continue
        cols = sorted({k for k, _ in g["marks"]})
        if not cols:
            reasons.append("marks_not_found")
        miles, km, _ = points_of(g["grid"], cols)
        warn = []
        if cols:
            # the chart gives the distance; a footnote referenced by the row may give the time limit
            it_dist = dict(it, interval_months=None)
            reasons += compare_shape(it_dist, miles, km, None, warn)
        refs = [int(x) for x in re.findall(r"\((\d{1,2})\)", label)]
        months, foot_ev, foot_other = None, "", False
        for n in refs:
            f = gm_footnote(pages, pg, cond or "NORMAL", n)
            if f is None:
                continue
            first = f[0].split(".")[0]
            # a time limit: '(2) Or every two years, whichever comes first', '(3) Or as indicated by
            # the DIC or two years whichever comes first', '(6) Replace brake fluid every five years'
            if not (re.match(r"Or\b", first) or EVERY_RE.search(first)):
                continue
            ms = scan_numbers(first)["months"]
            if not ms:
                continue
            named = jobs_named(first)
            if named and it["job"] not in named:
                foot_other = True
            months = ms[0] if len(ms) == 1 else (it.get("interval_months") if it.get("interval_months") in ms else ms[0])
            foot_ev = f"({n}) {first}"
        if it.get("interval_months"):
            if it["interval_months"] != months:
                reasons.append("months_not_stated")
            elif foot_other:
                reasons.append("footnote_names_other_job")
        elif months and not foot_other:
            warn.append("time_printed_not_in_item")
        reasons += job_reasons(it["job"], label)
        if it["job"] == "tire_rotation":
            if not re.search(r"\brotat", label, re.I) or it["action"] != "ROTATE":
                reasons.append("action_mismatch")
        else:
            gov = governing_verbs(label, it["job"]) or verbs_in(label)
            if it["action"] not in gov:
                reasons.append("action_mismatch" if gov else "action_not_stated")
        reasons += check_condition(it, "", cond)
        ev = f"p.{pg} [{cond}] {label[:70]}: @ at {', '.join(head_text(g['grid'], k) for k in cols)}" + (f"; {foot_ev}" if foot_ev else "")
        out.append(res(not reasons, reasons, "grid", ev, warn))
    for c in nomark:
        # 'Replace brake/clutch fluid. (7)' printed without marks: the footnote states the interval
        pg = (c.get("pages") or [None])[0]
        label = canon(c["quote"])
        cond = gm_chart_condition(pages[pg - 1].text)
        refs = [int(x) for x in re.findall(r"\((\d{1,2})\)", label)]
        texts = []
        for n in refs:
            f = gm_footnote(pages, pg, cond or "NORMAL", n)
            if f:
                texts.append(f[0])
        if not texts:
            out.append(fail("footnote_not_found", "text", label))
            continue
        app = it.get("applicability") or {}
        if app.get("brake_fluid_type"):
            # 'every five years for DOT 3 fluid or every three years for DOT 4 fluid'
            dot = re.escape(app["brake_fluid_type"])
            texts = [m.group(0) for t in texts for m in re.finditer(rf"(?:replace \w+ fluid )?every \w+ years? for {dot} fluid", t, re.I)] or texts
        reasons, ev, warn = best_text_check(it, texts, label, cond, job_text=label + " " + " ".join(texts))
        out.append(res(not reasons, reasons, "text", f"p.{pg} [{cond}] {label[:60]} <- {ev}", warn))
    for c in bullets_b + tire_b:
        # layout B: a bullet under its 'Every 36 000 km (22,500 mi)' heading of the Normal / Severe section
        hits = ctx.located(src, c)
        if not hits:
            out.append(fail("quote_not_on_page", "text", c["quote"]))
            continue
        stream, offsets = card_stream(pages)
        text = canon(c["quote"])
        if c in tire_b:
            reasons, ev, warn = best_text_check(it, [text], text, "NORMAL")
            out.append(res(not reasons, reasons, "text", ev, warn))
            continue
        cited_heads = [canon(h["quote"]) for h in heads_b]
        cands = []
        for pi, (s, e) in hits:
            before = stream[:offsets[pi] + s]
            heads = list(re.finditer(r"Every \d{1,3}(?: \d{3})+ km \(\d{1,3}(?:,\d{3})* mi\)"
                                     r"|Every (?:One|Two|Three|Four|Five|Six|Seven|Eight|Ten|\d{1,2}) Years", before))
            secs = list(re.finditer(r"Additional Required Services\s*-+\s*(Normal|Severe) Service|Owner Checks and Services"
                                    r"|Severe Conditions Requiring", before))
            if not heads or not secs:
                cands.append(fail("interval_heading_not_found", "text", text))
                continue
            head, sec = heads[-1], secs[-1]
            reasons, warn = [], []
            if sec.start() > head.start():
                reasons.append("interval_heading_not_found")
            if not any(compact(h) == compact(head.group(0)) for h in cited_heads):
                reasons.append("heading_not_the_cited_one")
            cond = "SEVERE" if (sec.group(1) or "").lower() == "severe" else "NORMAL"
            r2, ev, warn = best_text_check(it, [f"{head.group(0)} {text}"], text, cond, job_text=text)
            reasons += r2
            cands.append(res(not reasons, reasons, "text", f"[{cond}] {ev}", warn))
        # the bullet printed under several headings: the place under the cited heading
        out.append(min(cands, key=lambda r: (not r["ok"], len(r["reasons"]))))
    if not out:
        return fail("no_usable_cite", "text")
    return combine_groups(out)


# ---------------------------------------------------------------- Jeep owner's manuals 2014-2016

X_MARK = re.compile(r"X(?:\*\d+)?")


def fam_jeep_om(ctx, it, src, cites):
    pages = ctx.docs.pages(src)
    out = []
    if it["schedule_system"] == "OIL_LIFE_MONITOR":
        text = " ".join(canon(c["quote"]) for c in cites)
        reasons = []
        if not re.search(r"Oil Change Indicator|oil change interval", text, re.I):
            reasons.append("schedule_system_not_stated")
        reasons += job_reasons(it["job"], text)
        if it["action"] not in governing_verbs(text, it["job"]):
            reasons.append("action_mismatch")
        nums = scan_numbers(text)
        if it.get("max_interval_months") and it["max_interval_months"] not in nums["months"]:
            reasons.append("max_interval_not_stated")
        if it.get("max_interval_km") and it["max_interval_km"] not in nums["km"]:
            reasons.append("max_interval_not_stated")
        reasons += check_condition(it, "", "NORMAL")  # the Oil Change Indicator paragraph is not a severe section
        return res(not reasons, reasons, "monitor", text)
    for c in cites:
        loc = c.get("locator") or ""
        if "column headings" in loc or "footnote" in loc:
            continue  # supporting quotes (checked on their page)
        pg = (c.get("pages") or [None])[0]
        if "row '" not in loc:
            # 'Severe Duty All Models: Change Engine Oil at 4000 miles (6,500 km) if ... dusty ...'
            page = pages[pg - 1].text
            context = "SEVERE" if re.search(r"Severe Duty", page) else None
            reasons, ev, warn = best_text_check(it, [canon(c["quote"])], "", context)
            out.append(res(not reasons, reasons, "text", ev, warn))
            continue
        label = strip_marks(c["quote"])
        if has_interval(label):
            # the row prints its own interval ('Flush and replace the engine coolant at 120 months if not
            # done at 150,000 miles (240,000 km).'): the row text is the statement, the marks only note it
            reasons, ev, warn = best_text_check(it, [label], label, None)
            out.append(res(not reasons, reasons, "text", f"p.{pg} row states: {ev}", warn))
            continue
        g = grid_row(ctx, src, pg, label, it, X_MARK, "rows")
        reasons = list(g.get("reasons", []))
        if "marks" not in g:
            out.append(res(False, reasons, "grid", f"p.{pg} {label[:80]}"))
            continue
        cols = sorted({k for k, _ in g["marks"]})
        warn = []
        if not cols:
            reasons.append("marks_not_found")
        else:
            miles, km, months = points_of(g["grid"], cols)
            page_all = " ".join(pages[p].text for p in range(pg - 1, min(pg + 3, len(pages))))
            if re.search(r"\*\*", label + " " + g.get("sub", "")) and re.search(r"\*\*\s*The spark plug change interval is mileage[- ]based only", page_all):
                months = None  # '** ... mileage based only, yearly intervals do not apply'
            reasons += compare_shape(it, miles, km, months, warn)
        reasons += job_reasons(it["job"], label)
        gov = governing_verbs(label, it["job"]) or verbs_in(label)
        if it["action"] not in gov:
            reasons.append("action_mismatch" if gov else "action_not_stated")
        reasons += check_condition(it, label, None)
        ev = f"p.{pg} {label[:70]}: X at {', '.join(head_text(g['grid'], k) for k in cols)}"
        out.append(res(not reasons, reasons, "grid", ev, warn))
    if not out:
        return fail("no_usable_cite", "text")
    return combine_groups(out)


fam_jeep_om.grid_ok = True


# ---------------------------------------------------------------- Ford owner's manuals (tables)

FORD_TITLE = re.compile(r"(?:Normal scheduled maintenance|Other maintenance items|At every oil change interval|Towing a trailer"
                        r"|Extensive idling|Operating in dusty or sandy|Brake Fluid Maintenance|Exceeding|Special Operating Conditions"
                        r"|Normal Maintenance Intervals)(?!\s+chart)", re.I)
FORD_SEVERE = re.compile(r"Towing a trailer|Extensive idling|Operating in dusty or sandy|Special Operating Conditions", re.I)
INTERVAL_PIECE = re.compile(r"(?:Every|At)\s+[\d,]+\s*(?:miles|mi)\b\s*(?:\(\s*[\d,]+\s*(?:km|kilometers)?\s*\)?)?|Every\s+\d+\s+months\s+or(?:\s+[\d,]+)?", re.I)


def ford_condition(pages: list[CText], pi: int, s: int) -> str | None:
    """NORMAL / SEVERE of the table the text at (page index, offset) belongs to: the last table title
    printed before it (this page, else the page before)."""
    before = pages[pi].text[:s]
    titles = list(FORD_TITLE.finditer(before))
    if not titles and pi > 0:
        titles = list(FORD_TITLE.finditer(pages[pi - 1].text))
    if not titles:
        return None
    return "SEVERE" if FORD_SEVERE.search(titles[-1].group(0)) else "NORMAL"


def fam_ford(ctx, it, src, cites):
    pages = ctx.docs.pages(src)
    texts = [canon(c["quote"]) for c in cites]
    if it["schedule_system"] == "OIL_LIFE_MONITOR":
        item_texts = [t for t in texts if not re.search(r"\bexceed\b", t, re.I)]
        max_texts = [t for t in texts if re.search(r"\bexceed\b", t, re.I)]
        page = " ".join(pages[p - 1].text for c in cites for p in c.get("pages") or [])
        prev = " ".join(pages[p - 2].text for c in cites for p in c.get("pages") or [] if p > 1)
        reasons = []
        if not re.search(r"oil change interval|Oil-Life Monitor|oil monitoring system|oil life", page + " " + prev, re.I):
            reasons.append("schedule_system_not_stated")
        if not any(job_named(it["job"], t) for t in item_texts or texts):
            reasons.append("job_not_named")
        gov = set()
        for t in item_texts or texts:
            gov |= governing_verbs(t, it["job"]) or verbs_in(t)
        if it["action"] not in gov:
            reasons.append("action_mismatch" if gov else "action_not_stated")
        nums = scan_numbers(" ".join(max_texts))
        if it.get("max_interval_km") and it["max_interval_km"] not in nums["km"]:
            reasons.append("max_interval_not_stated")
        if it.get("max_interval_months") and it["max_interval_months"] not in nums["months"]:
            reasons.append("max_interval_not_stated")
        if it.get("interval_km") or it.get("interval_months"):
            reasons.append("interval_not_stated")
        reasons += check_condition(it, "", "NORMAL")  # an on-board / indicator paragraph is not a severe section
        return res(not reasons, reasons, "monitor", " | ".join(texts)[:240])
    notes = [c for c in cites if (c.get("locator") or "").endswith("footnote")]
    out = []
    for c in cites:
        if c in notes:
            continue
        q = canon(c["quote"])
        item_text = INTERVAL_PIECE.sub(" ", q).strip(" .")
        if len(compact(item_text)) < 6 or not job_named(it["job"], item_text):
            continue  # the interval cell of the row (checked with the row's item cell)
        hits = ctx.located(src, c)
        if not hits:
            out.append(fail("quote_not_on_page", "text", q))
            continue
        pi, (s, e) = hits[0]
        cond = ford_condition(pages, pi, s)
        if has_interval(item_text) or (has_interval(q) and not INTERVAL_PIECE.search(q)):
            # a sentence with its own interval ('Fusion full hybrid: Change engine oil and filter every 12 months ...')
            reasons, ev, warn = best_text_check(it, [q], q, cond)
            out.append(res(not reasons, reasons, "text", ev, warn))
            continue
        geo = ctx.docs.geo(src, pi + 1)
        fr = geo.frame("none") if geo else None
        cell = None
        if fr is not None:
            target = compact(re.sub(r"\s*\d+$", "", item_text))
            cands = [cl for cl in page_cells(fr) if target and target in compact(cl["t"])]
            cell = min(cands, key=lambda cl: len(cl["t"])) if cands else None
        if cell is None:
            out.append(fail("table_cell_not_found", "text", item_text))
            continue
        sib = [cl for cl in sibling_cells(fr, cell) if has_interval(cl["t"])]
        if not sib:
            out.append(fail("interval_cell_not_found", "text", cell["t"]))
            continue
        clause_texts = [canon(sib[0]["t"])]
        # a footnote marked on the item cell ('Change engine coolant.2' / '**' -> '2 Initial replacement at ...')
        marks = re.findall(r"(?:^|\s|[.)])(\d|\*{1,3})(?=\s|$)", cell["t"])
        page_t = pages[pi].text + " " + (pages[pi + 1].text if pi + 1 < len(pages) else "")
        for n in notes:
            nq = canon(n["quote"])
            if any(re.search(rf"(?<![\d,*]){re.escape(m)}\s*{re.escape(nq[:25])}", page_t) for m in marks):
                clause_texts.append(nq)
        check_it = it
        if it["occurrence"] == "FIRST" and any(re.search(r"\bafter (?:the )?initial (?:inspection|replacement)\b", t, re.I)
                                               for t in clause_texts[1:]):
            # 'Every 100000 miles' + footnote 'After initial inspection, inspect every other oil change':
            # the cell's distance is the initial point
            check_it = dict(it, occurrence="EVERY")
        reasons, ev, warn = best_text_check(check_it, clause_texts, cell["t"], cond, job_text=cell["t"])
        out.append(res(not reasons, reasons, "text", f"[{cond}] {cell['t'][:60]} | {ev}", warn))
    if not out:
        return fail("no_usable_cite", "text")
    return combine_groups(out)


fam_ford.grid_ok = True


# ---------------------------------------------------------------- Hyundai / Kia owner's manuals

LOC_ROW = re.compile(r"row '(.+?)'(?: / '(.+?)')?: ")
RI_MARK = re.compile(r"[RI]")
HMC_POINT = re.compile(r"^(?P<mi>\d{1,3}(?:,\d{3})+|\d+(?:\.\d)?)\s*miles\s*\((?P<km>\d{1,3}(?:,\d{3})*)\s*km\)\s*or\s*(?P<mo>\d+)\s*months$", re.I)
HMC_OWN_POINT = re.compile(r"\((?P<mi>\d{1,3}(?:,\d{3})+)\s*miles\s*\((?P<km>\d{1,3}(?:,\d{3})*)\s*km\)\s*or\s*(?P<mo>\d+)\s*months\)", re.I)


def in_text(needle: str, hay: str, share: float = 1.0) -> bool:
    """The needle (or its first share of characters, for a cell cut at its ruling) in the hay."""
    n, h = compact(needle), compact(hay)
    if not n:
        return False
    if n in h:
        return True
    k = max(12, int(len(n) * share))
    return share < 1.0 and n[:k] in h


def hmc_grid(ctx, it, src, c, label, sub):
    pg = c["pages"][0]
    quote = canon(c["quote"])
    g = grid_row(ctx, src, pg, label, it, RI_MARK, "rows", quote_label=f"{label} {sub or ''} {quote}")
    reasons = list(g.get("reasons", []))
    if "marks" not in g:
        return res(False, reasons, "grid", f"p.{pg} {label}")
    row_label = f"{label} {sub or ''}".strip()
    reasons += job_reasons(it["job"], row_label)
    if (c.get("locator") or "").endswith("text cell"):
        # an interval written across the columns of the row
        if not in_text(quote, g["text"], 0.7):
            reasons.append("clause_not_in_row")
        cells = [quote] + ([g["text"]] if g.get("text") and in_text(quote, g["text"], 0.7) else [])  # the whole printed cell
        r2, ev, warn = best_text_check(it, cells, row_label, hmc_page_condition(ctx.docs.pages(src), pg) or "NORMAL", job_text=row_label)
        return res(not (reasons + r2), reasons + r2, "text", f"p.{pg} row '{row_label}': {ev}", warn)
    letter = {"REPLACE": "R", "INSPECT": "I"}.get(it["action"])
    if letter is None:
        reasons.append("action_mismatch")
        return res(False, reasons, "grid", f"p.{pg} {row_label}")
    cols = sorted({k for k, m in g["marks"] if m == letter})
    warn = []
    if not cols:
        reasons.append("marks_not_found")
    else:
        reasons += compare_cols(it, g["grid"]["cols"], [g["grid"]["cols"][k] for k in cols], warn)
    reasons += check_condition(it, "", hmc_page_condition(ctx.docs.pages(src), pg))
    ev = f"p.{pg} row '{row_label}': {letter} at {', '.join(head_text(g['grid'], k) for k in cols)}"
    return res(not reasons, reasons, "grid", ev, warn)


def hmc_page_condition(pages: list[CText], pg: int) -> str | None:
    """The schedule a grid / list page belongs to, by its heading: 'Normal Maintenance Schedule' or
    a severe-usage heading (this page, else the page before)."""
    for p in (pg, pg - 1):
        if 0 < p <= len(pages):
            t = pages[p - 1].text
            if re.search(r"Maintenance Under Severe Usage|Severe Maintenance Schedule|Severe Driving Conditions", t, re.I):
                return "SEVERE" if not re.search(r"Normal Maintenance Schedule", t, re.I) else None
            if re.search(r"Normal Maintenance Schedule", t, re.I):
                return "NORMAL"
    return None


def hmc_severe(ctx, it, src, c, label, sub):
    """'Maintenance Under Severe Usage Conditions': item | (engine) | operation R/I | interval | conditions."""
    pg = c["pages"][0]
    geo = ctx.docs.geo(src, pg)
    if geo is None:
        return fail("pdf_page_missing", "text")
    quote = canon(c["quote"])
    best = None
    for rot in [geo.rotation()] + [r for r in ("none", "ccw") if r != geo.rotation()]:
        fr = geo.frame(rot)
        cells = page_cells(fr)
        anchors = [cl for cl in cells if sub and in_text(sub, cl["t"]) and len(compact(cl["t"])) <= len(compact(sub)) + 20]
        anchors = anchors or [cl for cl in cells if in_text(label, cl["t"])]
        for a in anchors:
            row = sibling_cells(fr, a)
            ivl = [cl for cl in row if in_text(quote, cl["t"], 0.7)]
            if not ivl:
                continue
            ops = [cl["t"].strip() for cl in row if re.fullmatch(r"[RI]", cl["t"].strip())]
            lab = [cl for cl in [a] + row if in_text(label, cl["t"])]
            reasons = []
            if not lab:
                reasons.append("row_label_not_found")
            letter = {"REPLACE": "R", "INSPECT": "I"}.get(it["action"])
            if not ops:
                reasons.append("action_not_stated")
            elif letter not in ops:
                reasons.append("action_mismatch")
            page = " ".join(cl["t"] for cl in cells)
            severe = re.search(r"severe|driving\s+condition", page + " " + ctx.docs.pages(src)[pg - 1].text, re.I)
            r2, ev, warn = best_text_check(dict(it, action=it["action"]), [quote], f"{label} {sub or ''}", "SEVERE" if severe else None,
                                           extra_verbs={"REPLACE" if "R" in ops else "INSPECT"} if ops else None,
                                           job_text=f"{label} {sub or ''}")
            r2 = [x for x in r2 if x not in ("action_not_stated", "action_mismatch")] if ops else r2
            reasons += r2
            cand = res(not reasons, reasons, "text", f"p.{pg} severe row '{label}' {ops}: {ev}", warn)
            if best is None or len(cand["reasons"]) < len(best["reasons"]):
                best = cand
        if best is not None and best["ok"]:
            break
    return best or fail("severe_row_not_found", "text", f"p.{pg} {label}")


def hmc_list_bullet(ctx, it, src, c, label):
    """A list-format bullet that prints its own interval: '❑ Rotate tire position (Every 7,500 miles ...)'."""
    pages = ctx.docs.pages(src)
    pg = c["pages"][0]
    t = pages[pg - 1].text
    quote = canon(c["quote"])
    segs = re.split(r"❑|□", t)
    bare = re.sub(r"\s*\*\s?\d+", "", label)  # footnote marks print after the bullet's own interval
    hit = [s for s in segs if in_text(bare, s) and in_text(quote, s)]
    if not hit:
        return fail("bullet_not_found", "text", f"p.{pg} {label}")
    seg = hit[0]
    severe = re.search(r"severe", t, re.I) and not re.search(r"Normal Maintenance Schedule", t, re.I)
    reasons, ev, warn = best_text_check(it, [quote], label, "SEVERE" if severe else "NORMAL", job_text=label + " " + seg)
    return res(not reasons, reasons, "text", f"p.{pg} bullet '{label}': {ev}", warn)


def hmc_list_lines(geo) -> list[str]:
    """Lines of a two-column list page in reading order (left column, then right column)."""
    fr = geo.frame("none")
    mid = geo.width / 2
    out = []
    for right in (False, True):
        ws = [w for w in fr["words"] if (w["cx"] >= mid) == right]
        for r in _rows(ws):
            out.append(" ".join(w["t"] for w in r))
    return out


def hmc_list_schedule(ctx, it, src, c, label):
    """List-format schedule (older Kia): blocks '7,500 miles (12,000 km) or 6 months' each followed by
    bullets; the item's points are the blocks that list it (or the bullet's own point)."""
    pages = ctx.docs.pages(src)
    pg = c["pages"][0]
    # the bullet's label: the quote without the bullet's own point ('(7,500 miles (12,000 km) or 12 months)')
    quote = canon(HMC_OWN_POINT.sub(" ", canon(c["quote"]))).strip()

    def is_list(p):
        return 0 < p <= len(pages) and "❑" in pages[p - 1].text and re.search(r"miles\s*\([\d,]+\s*km\)\s*or\s*\d+\s*months", pages[p - 1].text)

    lo = pg
    while is_list(lo - 1) and lo > pg - 12:
        lo -= 1
    hi = pg
    while is_list(hi + 1) and hi < pg + 14:
        hi += 1
    lines = []
    for p in range(lo, hi + 1):
        geo = ctx.docs.geo(src, p)
        if geo is not None:
            lines += [(p, ln) for ln in hmc_list_lines(geo)]
    bullets, block = [], None
    for p, ln in lines:
        t = canon(ln).strip()
        m = HMC_POINT.match(t)
        if m:
            block = (float(m.group("mi").replace(",", "")), int(m.group("km").replace(",", "")), int(m.group("mo")), p)
            continue
        if re.search(r"no check,?\s*no service required", t, re.I):
            block = None
            continue
        if t.startswith("❑"):
            bullets.append({"block": block, "t": t[1:].strip(), "p": p})
        elif bullets and block is not None and bullets[-1]["block"] is block and not re.match(r"\(Continued\)|\*\d|❈", t) \
                and len(bullets[-1]["t"]) < 400:
            bullets[-1]["t"] += " " + t
    pts = []
    for b in bullets:
        if not in_text(quote, b["t"]):
            continue
        own = HMC_OWN_POINT.search(b["t"])
        if own and compact(b["t"]).find(compact(quote)) < compact(b["t"]).find(compact(own.group(0))):
            pts.append((float(own.group("mi").replace(",", "")), int(own.group("km").replace(",", "")), int(own.group("mo")), b["p"]))
        elif b["block"] is not None:
            pts.append(b["block"])
    if not pts:
        return fail("list_points_not_found", "list", f"p.{pg} {quote}")
    pts = sorted(set(pts))
    warn = []
    reasons = compare_shape(it, [int(x[0]) for x in pts], [x[1] for x in pts], [x[2] for x in pts], warn)
    reasons += job_reasons(it["job"], quote)
    reasons += check_action(it, quote, quote)
    reasons += check_condition(it, "", hmc_page_condition(pages, pg))
    ev = f"'{quote[:60]}' listed at " + ", ".join(f"{int(x[0]):,} mi/{x[2]} mo (p.{x[3]})" for x in pts)
    return res(not reasons, reasons, "list", ev, warn)


def hmc_engine_footnote(page: str, n: str) -> tuple[str, str] | None:
    """The footnote '*N : Engine oil (2.0 TGDI) Replace every 6,500 miles ...' printed on the page:
    (engine, text) when it gives one engine its own interval."""
    for m in re.finditer(rf"(?<![\w(])\*\s?{n}\s*:?\s+(?=[A-Z])(.{{3,200}}?)(?=\s\*\s?\d+\s*:?\s+[A-Z]|❑|❈|\s\d{{1,3}},\d{{3}} miles \(|$)", page):
        body = m.group(1)
        eng = re.match(r"[A-Za-z][A-Za-z ,/&]{2,40}?\s*\(\s*([^()]*?(?:\d\.\d|T-?GDI|GDI|MPI)[^()]*?)\s*\)\s*(?=(?:Replace|Inspect|Change|At first)\b)",
                       body, re.I)
        if eng and has_interval(body):
            return eng.group(1), body
    return None


def hmc_footnote_scope(ctx, it, src, c, label: str) -> list[str]:
    """A row / bullet that carries a footnote mark '*N' whose footnote gives one engine its own interval
    for the same job ('Replace engine oil and filter *6 (Every 7,500 miles ...)' + '*6 : Engine oil (2.0
    TGDI) Replace every 6,500 miles ...'): the row's interval is for the other engines, so the item must
    be scoped (engine_except, or another engine of its own)."""
    pages = ctx.docs.pages(src)
    out = []
    for n in re.findall(r"\*\s?(\d+)", label):
        for pg in c.get("pages") or []:
            if not 0 < pg <= len(pages):
                continue
            f = hmc_engine_footnote(pages[pg - 1].text, n)
            if f is None or not job_named(it["job"], f[1]):
                continue
            app = it.get("applicability") or {}
            eng = compact(f[0])
            if app.get("engine_except") and eng in compact(app["engine_except"]):
                continue
            if app.get("engine") and eng not in compact(app["engine"]):
                continue  # the row names its own engine ('(2.4 GDI) *3')
            out.append("footnote_engine_scope_missing")
    return out


def fam_hmc(ctx, it, src, cites):
    out = []
    for c in cites:
        loc = c.get("locator") or ""
        lab_all = re.search(r"(?:row|bullet|schedule:) '(.+?)'", loc)
        scope = hmc_footnote_scope(ctx, it, src, c, lab_all.group(1)) if lab_all and "footnote" not in loc else []
        if scope:
            out.append(res(False, scope, "text", f"{loc[:80]}"))
            continue
        m = LOC_ROW.search(loc)
        if "list schedule" in loc:
            lab = re.search(r"list schedule: '(.+?)' listed under", loc)
            out.append(hmc_list_schedule(ctx, it, src, c, lab.group(1) if lab else c["quote"]))
        elif "list bullet" in loc:
            lab = re.search(r"list bullet '(.+?)':", loc)
            out.append(hmc_list_bullet(ctx, it, src, c, lab.group(1) if lab else ""))
        elif "severe table" in loc and m:
            out.append(hmc_severe(ctx, it, src, c, m.group(1), m.group(2)))
        elif "grid" in loc and m:
            out.append(hmc_grid(ctx, it, src, c, m.group(1), m.group(2)))
        elif "footnote" in loc:
            reasons, ev, warn = best_text_check(it, [canon(c["quote"])], loc, "NORMAL", job_text=loc + " " + c["quote"])
            # '*6 : Engine oil (2.0 TGDI) Replace every ...': the engine of the item is the one the footnote
            # prints in front of its interval
            hits = ctx.located(src, c)
            eng = (it.get("applicability") or {}).get("engine")
            stated = None
            if hits:
                pi, (s, e) = hits[0]
                before = ctx.docs.pages(src)[pi].text[max(0, s - 90):s]
                stated = re.search(r"\*\s?\d+\s*:?\s*([A-Za-z][A-Za-z ,/&]{2,40}?)\s*\(([^()]+)\)\s*$", before)
            if stated is None or not eng or compact(stated.group(2)) != compact(eng):
                reasons.append("footnote_engine_not_stated")
            elif not job_named(it["job"], stated.group(1)):
                reasons.append("job_not_named")
            out.append(res(not reasons, reasons, "text", ev, warn))
        else:
            out.append(fail("no_verifier_for_layout", "text", loc))
    if not out:
        return fail("no_usable_cite", "text")
    return combine_groups(out)


fam_hmc.grid_ok = True


# ---------------------------------------------------------------- Nissan / Infiniti

NIS_GUIDE_POINT = re.compile(r"\b(\d{1,3}(?:,\d{3})+) MILES OR (\d+) MONTHS\b")
# '5,000 miles/(8,000 km)/6 months', '11,250 Miles/18,000 Km/18 Months', '5,000 Miles/6 Months/8,000 Km'
_NIS_P = (r"(?P<mi>\d{1,3}(?:,\d{3})+)\s*miles\s*/\s*(?:\(?\s*(?P<km1>\d{1,3}(?:,\d{3})+)\s*km\s*\)?\s*/\s*(?P<mo1>\d+)\s*months"
          r"|(?P<mo2>\d+)\s*months\s*/\s*(?P<km2>\d{1,3}(?:,\d{3})+)\s*km)")
NIS_OM_POINT = re.compile(_NIS_P, re.I)
NIS_SEVERE_BOX = re.compile(r"Additional Maintenance Items for Severe Operating Conditions", re.I)
NIS_TOKEN = re.compile(
    rf"(?P<point>{_NIS_P})"
    r"|(?P<section>(?:Standard|Severe(?: use)?) maintenance\s*:)"
    r"|(?P<engine>\(\s*[A-Z0-9]{4,}\s+engine model\s*\))"
    r"|(?P<sub>(?:Inspections?|Essentials?|Replacements?|Inspect)\s*:)"
    r"|(?P<bullet>(?<!\S)[•.](?=\s))", re.I)


def nis_point(text: str) -> tuple[int, int, int] | None:
    m = NIS_OM_POINT.search(text)
    if not m:
        return None
    km = m.group("km1") or m.group("km2")
    mo = m.group("mo1") or m.group("mo2")
    return int(m.group("mi").replace(",", "")), int(km.replace(",", "")), int(mo)
NIS_CUT = re.compile(r"\s+\(\d\)\s+[A-Z]|\s+[\d-]{1,6}\s+Maintenance and schedules|\s*\[\s*Edit:|\s+Maintenance and schedules|\s+\(Continued"
                     r"|\s+Equipment varies|\s+\d\s+[A-Z][a-z]+ (?:and|on|except|require)|\s+For the ultimate|\s+Perform at number"
                     r"|\s+NOTE:|\s+After \d{1,3},\d{3} miles|\s+\*\s+[A-Z]|\s+<>\s*:|\s+Refer to [Pp]age")
GRID_RI = re.compile(r"[RI]\*?")


def nis_key(text: str) -> str:
    """Comparable form of a list item: footnote marks and superscript numbers dropped."""
    t = NIS_CUT.split(canon(text))[0]
    t = re.sub(r"(?<=[A-Za-z)])(?:\s*[\d,]+)+$", "", t.strip())  # superscripts 'fluid 2 ,3'
    t = re.sub(r"[*★#]+|\(\d+\)", "", t)
    t = re.sub(r"^(Replace|Inspect|Rotate|Change)d\b", r"\1", t.strip())  # 'Replaced air cleaner filter' (a misprint)
    t = canon(t).lower()
    t = re.sub(r"\(\s*if (?:applicable|equipped)\s*\)", "", t)  # 'Manual transmission oil (if applicable)'
    # 'Inspect axle and suspension parts' (one block) = 'Axle & suspension part' under 'Inspections:' (another)
    t = re.sub(r"^inspect(?:ion)?s?\s+(?:the\s+)?", "", t)
    t = re.sub(r"\band\b", "&", t)
    t = re.sub(r"(?<=[a-z])s\b", "", t)
    return compact(t)


def nis_same(bullet: str, key: str) -> bool:
    """A list bullet is the item's line: the same key, or one is the first conjunct of the other
    ('Engine drive belts' in one block, 'Engine drive belts and hose inspections' in the next)."""
    if not bullet or not key:
        return False
    if bullet == key:
        return True
    short, long_ = sorted((bullet, key), key=len)
    return len(short) >= 10 and long_.startswith(short + "&")


def span_pages(pages: list[CText], pg: int, rx, limit: int, gap: int = 3) -> tuple[int, int]:
    """The run of pages around pg that print schedule points (rx), allowing a few pages between
    them without points (an advertisement or a notes page inside a maintenance guide)."""
    def has(p):
        return 0 < p <= len(pages) and rx.search(pages[p - 1].text)
    lo = hi = pg
    while lo > pg - limit and any(has(lo - k) for k in range(1, gap + 1)):
        lo = next(lo - k for k in range(1, gap + 1) if has(lo - k))
    while hi < pg + limit and any(has(hi + k) for k in range(1, gap + 1)):
        hi = next(hi + k for k in range(1, gap + 1) if has(hi + k))
    return lo, hi


def nissan_points(ctx, src, pg: int, label: str, engine_hint: str | None = None) -> tuple[list, list, str]:
    """Points (miles, km|None, months, page, section) where a list schedule prints the label: Service and
    Maintenance Guide pages (one '5,000 MILES OR 6 MONTHS' page each, standard box + 'Additional
    Maintenance Items for Severe Operating Conditions' box) or owner's-manual lists ('5,000
    miles/(8,000 km)/6 months', 'Standard maintenance:' / 'Severe maintenance:' bullets)."""
    pages = ctx.docs.pages(src)
    key = nis_key(label)
    std, sev = [], []
    if NIS_GUIDE_POINT.search(pages[pg - 1].text):
        lo, hi = span_pages(pages, pg, NIS_GUIDE_POINT, 40)
        for p in range(lo, hi + 1):
            t = pages[p - 1].text
            pts = NIS_GUIDE_POINT.findall(t)
            if not pts or re.search(r"Premium Upgrade adds", t):
                continue  # the optional premium upgrade pages are not the schedule
            mi, mo = pts[-1]  # the page's title is printed last in its text
            point = (int(mi.replace(",", "")), None, int(mo), p)
            box = NIS_SEVERE_BOX.search(t)
            parts = [(t[:box.start()] if box else t, std), (t[box.end():] if box else "", sev)]
            for part, bucket in parts:
                items = re.split(r"❑|__", part)
                for x in items:
                    x = re.sub(r"^\s*Inspect the following:\s*", "", x)
                    if nis_same(nis_key(x), key):
                        verb = "INSPECT" if re.search(r"Inspect the following", part[:part.find(x)] if x in part else "") else None
                        bucket.append(point + (verb,))
                        break
        return std, sev, "guide"
    # owner's manual: the token stream of the schedule's pages (columns are in reading order)
    lo, hi = span_pages(pages, pg, NIS_OM_POINT, 24)
    schedules, cur = [], None
    point, section, sub, last_mi, engine = None, None, None, None, None
    for p in range(lo, min(hi + 1, len(pages)) + 1):
        t = pages[p - 1].text
        if p == hi + 1:
            # the last block's list runs onto the next page, which prints no point heading of its own
            # ('120,000 miles ...' at the foot of p.505, its 'Severe use maintenance' list on p.506);
            # that page is read up to the block's notes
            if "•" not in t[:200]:
                break
            cut = re.search(r"\s\(\d\)\s+[A-Z]|\s\*\s+[A-Z]", t)
            t = t[:cut.start()] if cut else t
        toks = list(NIS_TOKEN.finditer(t))
        for n, m in enumerate(toks):
            end = toks[n + 1].start() if n + 1 < len(toks) else len(t)
            if m.group("engine") or cur is None:
                if m.group("engine"):
                    engine = re.sub(r"[()\s]|engine model", "", m.group("engine"), flags=re.I)
                    if cur is not None and cur["engine"] == engine and not (cur["std"] or cur["sev"] or cur["pages"]):
                        continue  # the same heading printed twice
                cur = {"std": [], "sev": [], "pages": set(), "engine": engine}
                schedules.append(cur)
                last_mi = None
                if m.group("engine"):
                    continue
            if m.group("point"):
                mi, km_, mo_ = nis_point(m.group("point"))
                if last_mi is not None and mi <= last_mi:
                    cur = {"std": [], "sev": [], "pages": set(), "engine": engine}
                    schedules.append(cur)
                last_mi = mi
                point = (mi, km_, mo_, p)
                section, sub = None, None
            elif m.group("section"):
                section = "sev" if re.match(r"severe", m.group("section"), re.I) else "std"
            elif m.group("sub"):
                sub = m.group("sub")
            elif m.group("bullet") and point and section:
                cur["pages"].add(p)
                if nis_same(nis_key(t[m.end():end]), key):
                    verb = "INSPECT" if sub and re.match(r"Inspect", sub, re.I) else None
                    cur[section].append(point + (verb,))
    # schedules without an engine heading in the body: the manual's contents list the engine models
    # ('PR25DD engine model ... KR15DDT engine model') in the order of the schedules
    full = [s for s in schedules if s["pages"]]
    if full and not any(s["engine"] for s in full):
        names = []
        for p in pages:
            for nm in re.findall(r"\b([A-Z]{2}\d{2}[A-Z]{2,5})\s+engine model", p.text):
                if nm not in names:
                    names.append(nm)
        if len(names) == len(full) > 1:
            for s, nm in zip(full, names):
                s["engine"] = nm
    # the schedule of the item's engine ('2.0L 4 CYLINDER (KR20DDET engine model)'), else the one
    # whose pages hold the cited page
    if engine_hint:
        mine = [s for s in schedules if s["engine"] and compact(s["engine"]) in compact(engine_hint) and s["pages"]]
        if mine:
            s = next((s for s in mine if pg in s["pages"] and (s["std"] or s["sev"])),
                     next((s for s in mine if s["std"] or s["sev"]), mine[0]))
            return s["std"], s["sev"], f"om {s['engine']}"
    for s in schedules:
        if pg in s["pages"] and (s["std"] or s["sev"]):
            return s["std"], s["sev"], f"om {s['engine'] or ''}".strip()
    best = max(schedules, key=lambda s: len(s["std"]) + len(s["sev"]), default={"std": [], "sev": [], "engine": None})
    return best["std"], best["sev"], f"om {best.get('engine') or ''}".strip()


def nissan_list(ctx, it, src, c, label):
    pg = c["pages"][0]
    std, sev, kind = nissan_points(ctx, src, pg, label, (it.get("applicability") or {}).get("engine"))
    pts = std + (sev if it["condition"] == "SEVERE" else [])
    if not pts:
        return fail("list_points_not_found", "list", f"p.{pg} {label}")
    uniq = sorted({x[:3] for x in pts})
    warn = []
    note = nissan_bullet_note(ctx, src, c, label)
    if note:
        # 'Engine coolant * (3)' + '(3) First replacement interval is 105,000 miles (168,000 km) or 84
        # months. After first replacement, replace every 75,000 miles ...': the note states the item's
        # own interval (the block headings only show where the first point falls)
        reasons, n_ev, warn = best_text_check(it, [note], label, None, job_text=label + " " + note)
    else:
        km = [x[1] for x in uniq] if all(x[1] is not None for x in uniq) else None
        reasons = compare_shape(it, [x[0] for x in uniq], km, [x[2] for x in uniq], warn, km_printed=km is not None)
    if it["condition"] == "NORMAL" and not std:
        reasons.append("normal_item_from_severe_text")
    if it["condition"] == "SEVERE" and not sev:
        reasons.append("severe_not_stated")
    reasons += job_reasons(it["job"], label)
    verbs = verbs_in(label) | {x[4] for x in pts if x[4]}
    if note:
        pass  # the action is the note's verb (checked with the note)
    elif not verbs:
        reasons.append("action_not_stated")
    elif it["action"] not in verbs:
        reasons.append("action_mismatch")
    ev = f"'{label[:50]}' ({kind}) {'standard' if it['condition'] == 'NORMAL' else 'standard+severe'} points: " + \
         ", ".join(f"{x[0]:,}" for x in uniq) + " mi" + (f"; note: {n_ev}" if note else "")
    return res(not reasons, reasons, "list", ev, warn)


def nissan_bullet_note(ctx, src, c, label: str) -> str | None:
    """The note '(N) ...' that a list bullet refers to ('Engine coolant * (3)'), when it states a first
    interval and the one after it: the first note (N) printed after the bullet on its page."""
    marks = re.findall(r"\((\d)\)", label)
    hits = ctx.located(src, c)
    if not marks or not hits:
        return None
    pi, (s, e) = hits[0]
    pages = ctx.docs.pages(src)
    # the block's notes follow its lists, on the bullet's page or at the top of the next one
    t = pages[pi].text[e:] + (" " + pages[pi + 1].text if pi + 1 < len(pages) else "")
    nxt = re.search(r"\d{1,3},\d{3}\s*miles\s*/", t, re.I)  # the next block's heading ends this block
    t = t[:nxt.start()] if nxt else t
    for n in marks:
        m = re.search(rf"(?<![\w•])\({n}\)\s+([A-Z].*?)(?=\s\(\d\)\s+[A-Z]|\s\*\s+[A-Z]|\s\d{{1,3}},\d{{3}} miles\s*/|$)", t)
        if not m:
            continue
        st = structure(m.group(1))
        if st["first"] is not None and st["after"] is not None:
            return m.group(1)
    return None


def nissan_grid(ctx, it, src, c, label, pages_spec: list[int]):
    quote = canon(c["quote"])
    letter = {"REPLACE": "R", "INSPECT": "I"}.get(it["action"])
    reasons, warn, all_pts, texts, grid_cols = [], [], [], [], []
    found_any = False
    for pg in pages_spec:
        g = grid_row(ctx, src, pg, label, it, GRID_RI, "stacked", quote_label=quote)
        if "marks" not in g:
            # a grid continued on the next page: every page of it must be read
            reasons += g.get("reasons", []) or ["row_label_not_found"]
            continue
        found_any = True
        reasons += g.get("reasons", [])
        texts.append(g["text"])
        cols = sorted({k for k, m in g["marks"] if m.rstrip("*") == letter})
        all_pts += [g["grid"]["cols"][k] for k in cols]
        grid_cols += g["grid"]["cols"]
    if not found_any:
        return res(False, reasons or ["row_label_not_found"], "grid", f"{label}")
    reasons += job_reasons(it["job"], label)
    if any(in_text(quote, t, 0.8) for t in texts) and has_interval(quote):
        cells = [quote] + [t for t in texts if in_text(quote, t, 0.8)]  # the whole printed cell of the row
        r2, ev, warn = best_text_check(it, cells, label, "NORMAL", job_text=label)
        return res(not (reasons + r2), reasons + r2, "text", f"row '{label}': {ev}", warn)
    if letter is None:
        reasons.append("action_mismatch")
    # the grid is the standard schedule (severe ones are the 'Maintenance under severe operating
    # conditions' tables and the NOTEs)
    reasons += check_condition(it, "", "NORMAL")
    if not all_pts:
        reasons.append("marks_not_found")
    else:
        # one column per point (a point printed on both pages of a split grid counts once)
        uniq = list({(p["miles"], p["km"], p["months"]): p for p in all_pts}.values())
        reasons += compare_cols(it, grid_cols, uniq, warn)
    ev = f"row '{label}': {letter} at " + ", ".join(f"{p['miles']:,}" for p in sorted(all_pts, key=lambda p: p["miles"] or 0) if p["miles"])
    return res(not reasons, reasons, "grid", ev, warn)


def nissan_severe_row(ctx, it, src, c, label):
    """'Maintenance under severe operating conditions' table: item | operation | interval | conditions."""
    pg = c["pages"][0]
    pages = ctx.docs.pages(src)
    page = pages[pg - 1].text + " " + (pages[pg - 2].text if pg > 1 else "")
    context = "SEVERE" if re.search(r"severe (?:operating|driving) conditions", page, re.I) else None
    quote = canon(c["quote"])
    texts, row_label, ops = [quote], label, set()
    geo = ctx.docs.geo(src, pg)
    if geo is not None:
        fr = geo.frame(geo.rotation())
        cells = [cl for cl in page_cells(fr) if in_text(label, cl["t"]) and len(compact(cl["t"])) < len(compact(label)) + 40]
        for cl in cells:
            row = sibling_cells(fr, cl)
            ivl = [r["t"] for r in row if has_interval(r["t"])]
            if ivl:
                texts = [canon(ivl[0])]
                ops = {a for r in row for a in verbs_in(r["t"]) if len(r["t"]) < 20}
                break
    reasons, ev, warn = best_text_check(it, texts, row_label, context, extra_verbs=ops or None, job_text=row_label)
    return res(not reasons, reasons, "text", f"severe table '{label[:50]}': {ev}", warn)


def fam_nissan(ctx, it, src, cites):
    out = []
    for c in cites:
        loc = c.get("locator") or ""
        q = canon(c["quote"])
        m = re.match(r"p\.(\d+)(?:/(\d+))? grid row '(.+?)': ", loc)
        if m:
            spec = [int(m.group(1))] + ([int(m.group(2))] if m.group(2) else [])
            out.append(nissan_grid(ctx, it, src, c, m.group(3), spec))
            continue
        m = re.match(r"p\.\d+ '(.+?)' \((normal|severe)\) listed at", loc)
        if m:
            out.append(nissan_list(ctx, it, src, c, q))
            continue
        m = re.search(r"Maintenance under severe operating conditions: (?:months )?(.+)$", loc)
        if m:
            out.append(nissan_severe_row(ctx, it, src, c, m.group(1)))
            continue
        # NOTE / footnote / explanation / additional information: the clause, the row or heading it belongs to
        lab = re.search(r"(?:NOTE \(\d+\) of grid row|footnote of) '(.+?)'", loc)
        head = re.search(r"(?:explanation of (?:scheduled )?maintenance items|Additional information): (.+)$", loc, re.I)
        label = lab.group(1) if lab else head.group(1) if head else ""
        hits = ctx.located(src, c)
        if lab and hits:
            # the NOTE / footnote number in front of the quote must be the one the row refers to
            pi, (s, e) = hits[0]
            t = ctx.docs.pages(src)[pi].text
            pages_t = t + " " + (ctx.docs.pages(src)[pi - 1].text if pi > 0 else "")
            if not re.search(re.escape(compact(label)[:12]), compact(pages_t)):
                out.append(fail("row_label_not_found", "text", label))
                continue
        reasons, ev, warn = best_text_check(it, [q], label, lead_severe(q) if lab else None, job_text=label + " " + q)
        out.append(res(not reasons, reasons, "text", f"{loc[:60]}: {ev}", warn))
    if not out:
        return fail("no_usable_cite", "text")
    return combine_groups(out)


fam_nissan.grid_ok = True


# ---------------------------------------------------------------- Mitsubishi warranty / maintenance booklets

MIT_POINT = re.compile(r"●\s*(?:(?P<mi>\d{1,3}(?:,\d{3})+)\s*Miles\s*\(\s*(?P<km>\d{1,3}(?:,\d{3})+)\s*km\s*\)"
                       r"(?:\s*or\s*at\s*(?P<mo>\d+)\s*months)?|(?P<mo2>\d+)\s*Months)", re.I)


def mit_schedule_condition(pages: list[CText], n: str) -> str | None:
    """'Use Schedule 1 if you primarily operate your vehicle under any of these conditions; dusty ...':
    Schedule 1 is the severe one, Schedule 2 the normal one (when the booklet says so)."""
    if any(re.search(r"Use Schedule 1 if you primarily operate", p.text) for p in pages):
        return "SEVERE" if n == "1" else "NORMAL"
    return None


def mit_booklet(ctx, it, src, c, kind: str, notes: list[dict]):
    """Older booklets: 'Regular / Severe Maintenance Schedule' pages, blocks '● 30,000 Miles (48,000 km)
    or at 24 months' followed by the items due."""
    pages = ctx.docs.pages(src)
    title = "Severe Maintenance Schedule" if kind == "severe" else "Regular Maintenance Schedule"
    sched_pages = [i for i, p in enumerate(pages) if p.text.startswith(title) or p.text[:60].find(title) >= 0]
    quote = canon(c["quote"])

    def bare(s: str) -> str:  # footnote marks ('condition. *1') print in several ways
        return re.sub(r"\*\d*", "", compact(s))

    key = bare(quote)
    pts = []
    point = None
    for i in sched_pages:
        t = pages[i].text
        toks = [(m.start(), "p", m) for m in MIT_POINT.finditer(t)] + \
               [(k, "b", None) for k, ch in enumerate(t) if is_bullet(ch) and ch not in "●•"]
        toks.sort(key=lambda x: x[0])
        for n, (pos, typ, m) in enumerate(toks):
            end = toks[n + 1][0] if n + 1 < len(toks) else len(t)
            if typ == "p":
                mo = m.group("mo") or m.group("mo2")
                point = (int(m.group("mi").replace(",", "")) if m.group("mi") else None,
                         int(m.group("km").replace(",", "")) if m.group("km") else None, int(mo) if mo else None, i + 1)
                continue
            body = bare(t[pos + 1:end])
            # the same line, not a longer qualified one ('Rotate tires (Lancer 2.4L with 18" wheels)')
            if point and len(key) >= 8 and body.startswith(key) and body[len(key):len(key) + 1] not in ("(", "["):
                pts.append(point)
    if not pts:
        return fail("list_points_not_found", "list", quote)
    pts = sorted(set(pts), key=lambda x: (x[0] or 0, x[2] or 0))
    warn, reasons = [], []
    texts = [canon(n["quote"]) for n in notes]
    if texts and has_interval(" ".join(texts)):
        # '* Change at first 120,000 Miles (192,000 km) or at 96 months, thereafter every ...': the item's
        # own interval in the footnote of its line
        r2, ev, warn = best_text_check(it, texts, quote, "SEVERE" if kind == "severe" else "NORMAL", job_text=quote)
        page_t = " ".join(pages[p[3] - 1].text for p in pts)
        if not re.search(re.escape(compact(quote)[:20]) + r".{0,6}\*", compact(page_t)):
            r2.append("footnote_not_linked")
        return res(not r2, r2, "text", f"{quote[:50]} * {ev}", warn)
    miles = [p[0] for p in pts if p[0]]
    km = [p[1] for p in pts if p[1]]
    months = [p[2] for p in pts if p[2]]
    if len(miles) != len(pts):
        miles = []
    if len(km) != len(pts):
        km = []
    if len(months) != len(pts):
        months = []
    reasons += compare_shape(it, miles, km, months, warn)
    reasons += job_reasons(it["job"], quote)
    reasons += check_action(it, quote, quote)
    reasons += check_condition(it, "", "SEVERE" if kind == "severe" else "NORMAL")
    ev = f"{kind}: '{quote[:50]}' at " + ", ".join(f"{p[0]:,}/{p[2]}" if p[0] else f"{p[2]} mo" for p in pts)
    return res(not reasons, reasons, "list", ev, warn)


def mit_full_note(ctx, src, c) -> str:
    """The whole footnote '*N: ...' on the page that holds the cite's quote (the quote can stop after
    its first sentence: '... then change ... if necessary.' + 'And if the inspection is not performed,
    change (not just inspect) ... every 30,000 miles (48,000 km).')."""
    hits = ctx.located(src, c)
    if not hits:
        return canon(c["quote"])
    pi, (s, e) = hits[0]
    t = ctx.docs.pages(src)[pi].text
    heads = list(re.finditer(r"\*\s?\d+\s*:", t[:s + 4]))
    start = heads[-1].start() if heads else s
    m = re.search(r"\*\s?\d+\s*:", t[max(e, start + 4):])
    end = max(e, start + 4) + m.start() if m else len(t)
    return t[start:max(end, e)]


def fam_mitsubishi(ctx, it, src, cites):
    pages = ctx.docs.pages(src)
    out = []
    parents = [canon(c["quote"]) for c in cites if (c.get("locator") or "").endswith("parent row")]
    notes = [c for c in cites if re.search(r"footnote", c.get("locator") or "")]
    for c in cites:
        loc = c.get("locator") or ""
        m = re.match(r"Schedule (\d) p\.(\d+), row '(.+)'$", loc)
        if m:
            n, pg, row = m.group(1), int(m.group(2)), m.group(3)
            quote = canon(c["quote"])
            cond = mit_schedule_condition(pages, n)
            if not re.search(rf"\bSchedule {n}\b", pages[pg - 1].text):
                out.append(fail("schedule_not_on_page", "grid", loc))
                continue
            text_cell = has_interval(quote)
            head_q = re.split(r"(?<![A-Za-z])(?:Every|First|Replace every|Inspect for)\s", quote)[0].strip()
            labels = [canon(row), head_q] if text_cell else [strip_marks(quote)]
            for label in labels:
                g = grid_row(ctx, src, pg, label, it, X_MARK, "rows", quote_label=quote)
                if "marks" in g:
                    break
            reasons = list(g.get("reasons", []))
            if "marks" not in g:
                out.append(res(False, reasons, "grid", f"p.{pg} {label[:60]}"))
                continue
            row_label = " ".join(parents + [canon(row)])
            reasons += job_reasons(it["job"], row_label)
            # a footnote of the row ('Check transfer fluid & differential gear oil*10' -> '*10: If towing ...
            # change (not just inspect) oil at every 20,000 miles ...') can carry the item's own interval
            foot = [mit_full_note(ctx, src, x) for x in notes if re.search(r"\*(\d+)", x.get("locator") or "")
                    and re.search(rf"\*\s?{re.search(r'[*](\d+)', x['locator']).group(1)}(?!\d)", canon(row))]
            if foot:
                # the footnote's opening condition ('*2: If towing a trailer ...') governs all its sentences
                f_ctx = "SEVERE" if any(lead_severe(re.sub(r"^\*\s?\d+\s*:\s*", "", f)) for f in foot) else None
                r_f, ev_f, w_f = best_text_check(it, foot, row_label, f_ctx, job_text=row_label + " " + " ".join(foot))
                if not r_f:
                    out.append(res(True, [], "text", f"p.{pg} S{n} row '{row[:50]}' footnote: {ev_f}", w_f))
                    continue
            if text_cell:
                head = canon(row)
                cell = quote[len(head):].strip() if quote.startswith(head[:20]) else quote[len(head_q):].strip() or quote
                if not in_text(cell, g["text"], 0.7):
                    reasons.append("clause_not_in_row")
                # the quote can stop short of the cell's end ('Every 3,750 miles (6,000 km)' of a cell that
                # prints '... or every 3 months'): the whole printed cell of the row is the clause
                cells = [cell] + ([g["text"]] if g.get("text") and in_text(cell, g["text"], 0.7) else [])
                r2, ev, warn = best_text_check(it, cells, row_label, cond, job_text=row_label)
                out.append(res(not (reasons + r2), reasons + r2, "text", f"p.{pg} S{n} row '{row[:50]}': {ev}", warn))
                continue
            cols = sorted({k for k, _ in g["marks"]})
            warn = []
            if not cols:
                reasons.append("marks_not_found")
            else:
                reasons += compare_cols(it, g["grid"]["cols"], [g["grid"]["cols"][k] for k in cols], warn)
            gov = governing_verbs(row_label, it["job"]) or verbs_in(row_label)
            if it["action"] not in gov:
                reasons.append("action_mismatch" if gov else "action_not_stated")
            reasons += check_condition(it, "", cond)
            ev = f"p.{pg} S{n} row '{row[:50]}': X at {', '.join(head_text(g['grid'], k) for k in cols)}"
            out.append(res(not reasons, reasons, "grid", ev, warn))
            continue
        m = re.match(r"(Regular|Severe) maintenance schedule, first listed at", loc)
        if m:
            out.append(mit_booklet(ctx, it, src, c, m.group(1).lower(), [x for x in notes if "maintenance schedule footnote" in (x.get("locator") or "")]))
            continue
        m = re.match(r"Schedule (\d) footnote \*(\d+)", loc)
        if m and not any(re.match(r"Schedule \d p\.", x.get("locator") or "") for x in cites):
            # a footnote that carries the item's interval: '*2: After 60,000 miles ... inspect every ...'
            cond = mit_schedule_condition(pages, m.group(1))
            q = canon(c["quote"])
            pg = c["pages"][0]
            rows = [r.group(1) for r in re.finditer(rf"([A-Za-z][^*]{{3,80}}?)\s*\*\s?{m.group(2)}(?!\d)(?!\s*:)", pages[pg - 1].text)]
            label = " ".join(rows)
            reasons, ev, warn = best_text_check(it, [q], label, cond, job_text=label + " " + q)
            out.append(res(not reasons, reasons, "text", f"footnote *{m.group(2)}: {ev}", warn))
    if not out:
        return fail("no_usable_cite", "text")
    return combine_groups(out)


fam_mitsubishi.grid_ok = True


def combine_groups(results: list[dict]) -> dict:
    """All parts must pass; the evidence of the first failing part (else the first part)."""
    if not results:
        return fail("no_usable_cite", "text")
    bad = [r for r in results if not r["ok"]]
    pick = bad[0] if bad else results[0]
    reasons = [x for r in results for x in r["reasons"]]
    warnings = [x for r in results for x in r["warnings"]]
    return res(not bad, reasons, pick["method"], pick["evidence"], warnings)


# ============================================================================ driver

FAMILIES = {
    "tesla": fam_tesla,
    "mercedes-benz": fam_mercedes,
    "bmw": fam_bmw,
    "audi": fam_card,
    "volkswagen": fam_card,
    "honda": fam_honda,
    "chevrolet": fam_gm,
    "cadillac": fam_gm,
    "jeep": fam_jeep_om,
    "ford": fam_ford,
    "hyundai": fam_hmc,
    "kia": fam_hmc,
    "nissan": fam_nissan,
    "infiniti": fam_nissan,
    "mitsubishi": fam_mitsubishi,
}
fam_gm.grid_ok = True


def family_for(make: str, src: dict, cites: list[dict]):
    if src.get("kind") == "json_file":
        return fam_mopar
    return FAMILIES.get(make)


SUPPLEMENT = re.compile(r"supplement\s+revises(?:\s+or\s+adds\s+to)?(?P<what>.{0,500}?)(?:Read carefully|Printing:|$)", re.I)
POINT_SECTION = re.compile(r"\d{1,3},\d{3}\s*miles\s*/")
CONTINUATION = re.compile(r"^\s*[,;]?\s*(?:and\s+)?(?:then|thereafter|after that|afterwards|subsequently)\b[\s,]*(?:\w+\s+){0,4}?(?:every|each|at|in)?\s*\d",
                          re.I)


def supplement_partial(pages: list[CText], pg: int) -> str | None:
    """A cited page inside an owner's-manual supplement that revises only some interval blocks of the
    schedule ('This supplement revises or adds to the "15,000 miles/(24,000 km)/18 months", "90,000
    miles/(144,000 km)/108 months" ... sections'): its blocks are not the whole schedule."""
    for p in range(pg - 1, max(0, pg - 6), -1):
        m = SUPPLEMENT.search(pages[p - 1].text)
        if m:
            return f"p.{p}: {m.group(0)[:160]}" if POINT_SECTION.search(m.group("what")) else None
    return None


def extent_reasons(ctx: Ctx, it: dict, src: dict, cites: list[dict]) -> list[str]:
    """Checks of the place of the quotes in the document, for every family: the quote's clause goes on
    after it with a following interval ('Every 150,000 miles (240K km)' + ' then every 20K'), so an EVERY
    reading stops short of the printed cell; the quote sits in a supplement that revises only some
    interval blocks."""
    pages = ctx.docs.pages(src)
    out = []
    for c in cites:
        for pg in c.get("pages") or []:
            if not 0 < pg <= len(pages):
                continue
            if it["occurrence"] == "EVERY":
                for s, e in pages[pg - 1].spans(c["quote"]):
                    if CONTINUATION.match(pages[pg - 1].text[e:e + 80]):
                        out.append("clause_continues_after_quote")
            if pg <= 40 and supplement_partial(pages, pg):
                out.append("schedule_supplement_partial")
    return out


# ============================================================================ scope (applicability)
#
# A restriction printed with the item's own line ('Drive shaft boots (4WD/AWD)', 'Rear differential oil
# (AWD)', 'Propeller shaft (AWD models)', 'Change ... transfer case fluid, if equipped with 4WD', 'Toothed
# Belt ... (Diesel Engine)', 'Replace CVT Fluid (... (HEV))', '... (CVT only)', 'Except 1.4L Engine:',
# '(Except 6.2L V8 Engine)') limits the vehicles the interval is for. The item states that interval
# only when its applicability carries the restriction: a positive one in a scope value (drive, engine,
# transmission, edition / models / variant / plan ...), a negative one in an *_except value or by a
# narrower positive value of the same kind. An item that carries the opposite scope contradicts the
# source. A negative model scope ('(except Q60 IPL)', '(except ... Outlander Sport)') must not name the
# item's own line; one that names an edition of the line ('Except CTS-V:' on the CTS line) must be carried.
# An equipment exclusion ('(except vehicles with timing chain)', ', without limited slip differential.')
# must be carried by an *_except value (or a narrower equipment value). A cited note that names no job
# ('For diesel engine vehicles, see ... the Duramax diesel supplement.') must have its scope named by the
# item (as its own or as an exception). Only the sentences of the quote / row label that name the item's job count ('Rotate
# tires and perform Required Services. ... Drain the diesel fuel filter of water. (Diesel Only)': the
# restriction is the fuel filter's), and only their label part before the first interval statement
# ('... Jetta (163), Jetta (hybrid) Every 180,000 miles' lists models, it does not restrict the row).

_SEP = r"(?:\s*(?:/|,|&|\band\b|\bor\b)\s*)"
SCOPE_TOKENS = {
    "drive": [(r"\b(?:4WD|4x4|e-?4WD)\b|four[- ]wheel[- ]drive", "4WD"), (r"\b(?:AWD|e-?AWD)\b|all[- ]wheel[- ]drive", "AWD"),
              (r"\b2WD\b", "2WD"), (r"\bFWD\b|front[- ]wheel[- ]drive", "FWD"), (r"\bRWD\b|rear[- ]wheel[- ]drive", "RWD")],
    "powertrain": [(r"\bplug-?in hybrid\b|\bPHEV\b", "phev"), (r"\bhybrid\b|\bHEV\b", "hybrid"), (r"\bdiesel\b|\bTDI\b|\bduramax\b", "diesel"),
                   (r"\bgas(?:oline)?\b|\bpetrol\b", "gas"), (r"\belectric\b|\bEV\b", "electric")],
    "transmission": [(r"\bCVT\b|continuously variable", "cvt"), (r"\bsix-?\s?speed\b", "six-speed"), (r"\b(?:\d+|eight)[- ]?speed\b", "n-speed"),
                     (r"\bmanual(?:\s+(?:transmission|transaxle|gearbox))?\b|\bM/T\b", "manual"),
                     (r"\bautomatic(?:\s+(?:transmission|transaxle))?\b|\bA/T\b", "automatic"), (r"\bDSG\b|\bDCT\b|dual[- ]clutch", "dsg")],
    # engine codes are matched with their printed case ('LF3', 'KR20DDET', '4B1'), the other words without
    "engine": [(r"\b\d\.\d\s?L?\b", None), (r"(?-i:\b[A-Z]{2}\d{2}[A-Z]{2,5}\b)", None), (r"(?-i:\b\d[A-Z]\d{1,2}\b)", None),
               (r"(?-i:\bL[A-Z][A-Z0-9]\b)", None),
               (r"\bT-?GDI\b|\bGDI\b|\bMPI\b|\bTFSI\b|\bTSI\b|\bSRT\b|\bV[68]\b|\bI4\b|\bturbo\b|\beAssist\b", None)],
}
ENGINE_GENERIC = {"TGDI", "GDI", "MPI", "TFSI", "TSI", "V6", "V8", "I4", "TURBO", "EASSIST"}
TRANSMISSION_JOBS = {"dsg": ("dual_clutch_fluid", "dct_fluid"), "manual": ("manual_transmission_fluid", "clutch_fluid")}
SCOPE_FILLER = re.compile(r"\b(?:engines?|models?|vehicles?|only|with|equipped|if|all|the|an?|transmissions?|transaxles?|type|"
                          r"electronic|vehicle|cylinder|series)\b|[/,&.()\-:«»]|\band\b|\bor\b", re.I)
SCOPE_NEG = re.compile(r"^\s*(?:except(?:\s+with)?|excluding|without|not for|non)\b[- ]?\s*", re.I)
SCOPE_PAREN = re.compile(r"\(([^()]{1,80})\)")
SCOPE_PHRASE = re.compile(r"\b(?:if equipped with|equipped with|for)\s+(?:an?\s+)?(?P<c>[^.,;()»«]{1,60}?)(?=\s*(?:[.,;()»«]|$|\s-\s|\s(?:Every|At|First)\b))", re.I)
SCOPE_LEAD_EXCEPT = re.compile(r"^\s*(?P<c>Except\s+[^:]{1,60}):", re.I)
SCOPE_EXCEPT = re.compile(r"\b(?P<c>(?:except|excluding)\s+[^.,;:()»«*]{1,40}?)(?=\s*(?:[.,;:()»«*]|$|\s(?:Every|At|First)\b))", re.I)
SCOPE_NON = re.compile(r"\bnon[- ]?(?P<c>[A-Za-z0-9.]+)", re.I)
SCOPE_WITHOUT = re.compile(r"(?:^|,)\s*(?P<c>without\s+[^.,;:()»«*]{3,60}?)(?=\s*(?:[.,;:()»«*]|$))", re.I)  # ', without limited slip differential.'
INTERVAL_START = re.compile(r"(?<![A-Za-z])(?:Every|EVERY|At first|At\s+(?=\d)|First\s+(?=\d))")
SCOPE_SKIP_KEYS = {"service", "minder_code", "approx_in_source", "scope", "operating_condition", "schedule_table", "oil_monitor",
                   "brake_fluid_type", "side", "component", "filter", "operation", "axle"}


def scope_tokens(content: str) -> dict[str, set]:
    """Scope words of a restriction's content by kind ({} when the content is not only scope words:
    '(for Audi Connected Services)', '(including tensioner)', '(Engine)' are not restrictions)."""
    found: dict[str, set] = {}
    rest = content
    for kind, pats in SCOPE_TOKENS.items():
        for pat, norm_tok in pats:
            for m in re.finditer(pat, rest, re.I):
                found.setdefault(kind, set()).add(norm_tok or m.group(0).upper().replace(" ", "").replace("-", ""))
            rest = re.sub(pat, " ", rest, flags=re.I)
    rest = SCOPE_FILLER.sub(" ", rest)
    if re.search(r"[A-Za-z]{2,}", rest):
        return {}
    return found


def scope_restrictions(text: str) -> list[tuple[str, str, dict]]:
    """Restrictions printed in a label part: [(polarity +/-, content, {kind: tokens}) ...]; a negative
    one whose content is not scope words is a model exclusion (kind 'model')."""
    out = []
    # a parenthesis is one restriction or none ('(including visible HV components of PHEV vehicles)' is
    # not one); the phrases are read outside the parentheses
    outside = SCOPE_PAREN.sub(" ", text)
    contents = [m.group(1) for m in SCOPE_PAREN.finditer(text)] + [m.group("c") for m in SCOPE_PHRASE.finditer(outside)]
    contents += [m.group("c") for m in SCOPE_LEAD_EXCEPT.finditer(outside)]
    contents += [m.group("c") for m in SCOPE_EXCEPT.finditer(outside)]  # 'Spark plugs *5 EXCEPT TGDI' (row + engine cell)
    contents += [f"non {m.group('c')}" for m in SCOPE_NON.finditer(outside)]
    contents += [m.group("c") for m in SCOPE_WITHOUT.finditer(outside)]
    # 'AWD models', 'Diesel Only', 'TDI Vehicles' outside parentheses
    for m in re.finditer(r"\b((?:4WD|AWD|2WD|FWD|RWD|4x4|diesel|hybrid|HEV|PHEV|CVT|TDI)(?:" + _SEP + r"(?:4WD|AWD|2WD|FWD|RWD|4x4))*)\s+(?:models?|vehicles?|only)\b", outside, re.I):
        contents.append(m.group(1))
    seen = set()
    for c in contents:
        c = c.strip()
        if not c or c.lower() in seen:
            continue
        seen.add(c.lower())
        neg = SCOPE_NEG.match(c)
        body = c[neg.end():] if neg else c
        toks = scope_tokens(body)
        equip = re.match(r"\s*vehicles?\s+(?:with|equipped with)\s+(.+)", body, re.I)
        if toks:
            out.append(("-" if neg else "+", c, toks))
        elif neg and (equip or re.match(r"\s*without\b", neg.group(0), re.I)) and re.search(r"[A-Za-z]{3,}", body):
            # '(except vehicles with timing chain)', 'without electronic limited slip differential'
            out.append(("-", c, {"equipment": {(equip.group(1) if equip else body).strip()}}))
        elif neg and re.search(r"[A-Za-z]{2,}", body):
            out.append(("-", c, {"model": {body}}))
    return out


def scope_units(text: str) -> list[str]:
    """Sentences of a label / clause; a sentence that only states a restriction ('If equipped with manual
    transmission.', '(Diesel Only)', '(Except 1.8L Hybrid.)') belongs to the sentence before it."""
    # a sentence ends at '.' / ';' and at a parenthesis that closes one ('(Except 1.8L Hybrid.) Inspect ...')
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z(])|(?<=\.\))\s+(?=[A-Z(])", canon(text))
    out: list[str] = []
    for p in parts:
        bare = p
        for _, c, _ in scope_restrictions(p):
            bare = bare.replace(c, " ")
        bare = re.sub(r"\bif equipped with\b|\bfor\b|[@✓*]|\b[RIX]\b|\(\d+\)|\d", " ", bare, flags=re.I)
        if out and not re.search(r"[A-Za-z]{3,}", bare):
            out[-1] = f"{out[-1]} {p}"
        else:
            out.append(p)
    return out


def _label_part(unit: str) -> str:
    """The label part of a unit: before the first interval statement."""
    cut = [m.start() for m in DIST_RE.finditer(unit)] + [m.start() for m in TIME_RE.finditer(unit)] + \
          [m.start() for m in INTERVAL_START.finditer(unit) if m.start() > 0]
    return unit[:min(cut)] if cut else unit


def _value_kind_hits(kind: str, value: str) -> set:
    """Scope tokens of one kind named positively in an applicability value ('Non Turbo Model' does not
    name turbo; 'hybrid (all hybrid models)' names hybrid)."""
    v = re.sub(r"\b(?:non|except|excluding|without)\b[- ]?\s*[\w.]+", " ", str(value), flags=re.I)
    hits = set()
    for pat, norm_tok in SCOPE_TOKENS.get(kind, []):
        for m in re.finditer(pat, v, re.I):
            hits.add(norm_tok or m.group(0).upper().replace(" ", "").replace("-", ""))
    return hits


def _engine_meet(want: set, have: set) -> bool:
    """Engine tokens: the most specific kind both sides print decides: an engine code ('LF3' is not
    'LFX'), else the displacement ('2.0L' = '2.0'), else a generic word ('TGDI', 'turbo')."""
    def disp(s):
        return {re.sub(r"L$", "", x) for x in s if re.fullmatch(r"\d\.\dL?", x)}
    codes_w, codes_h = want - ENGINE_GENERIC - {x for x in want if re.fullmatch(r"\d\.\dL?", x)}, \
        have - ENGINE_GENERIC - {x for x in have if re.fullmatch(r"\d\.\dL?", x)}
    if codes_w and codes_h:
        return bool(codes_w & codes_h)
    if disp(want) and disp(have):
        return bool(disp(want) & disp(have))
    return bool(want & have)


def _tokens_meet(kind: str, want: set, have: set) -> bool:
    if kind == "engine":
        return _engine_meet(want, have)
    return bool(want & have)


def scope_reasons(ctx: Ctx, it: dict, src: dict, cites: list[dict]) -> list[str]:
    appl = it.get("applicability") or {}
    pos_vals = [str(v) for k, v in appl.items() if not k.endswith("_except") and k != "except" and k not in SCOPE_SKIP_KEYS]
    neg_vals = [str(v) for k, v in appl.items() if k.endswith("_except") or k == "except"]
    if it.get("engine"):
        pos_vals.append(str(it["engine"]))
    out = []
    line = compact(ctx.line.replace("-", " "))
    line_names = {compact(x) for x in [ctx.line.replace("-", " ")] + [str(appl.get(k) or "") for k in ("edition", "models")] if x}
    other_lines = ctx.lines() - {line}
    for c in cites:
        # the quote, and the row label the locator prints (with its engine / sub-row cell: 'Spark plugs *5' / 'EXCEPT TGDI')
        labels = re.findall(r"'([^']{3,240})'", c.get("locator") or "")
        texts = [c["quote"]] + ([" ".join(labels)] if labels else [])
        units = [u for t in texts for u in scope_units(t)]
        for u in units:
            for pol, content, toks in scope_restrictions(_label_part(u)):
                if "model" in toks and pol == "-":
                    names = [compact(x) for x in re.split(r",|\band\b|\bor\b", re.sub(r"^\s*all\s+", "", next(iter(toks["model"])), flags=re.I))]
                    if any(n and n in line_names for n in names):
                        out.append("scope_excludes_line")
                    # an edition of the item's own line ('Except CTS-V:' on the CTS line; not 'Outlander Sport',
                    # which is a line of its own): carried by an *_except value or a narrower edition / models value
                    for n in names:
                        if not n or n == line or not line or not n.startswith(line) or n in other_lines:
                            continue
                        if any(n in compact(v) for v in neg_vals):
                            continue
                        eds = [compact(str(appl.get(k))) for k in ("edition", "models") if appl.get(k)]
                        if any(n in e for e in eds):
                            out.append("edition_scope_contradicted")
                        elif not eds:
                            out.append("edition_scope_not_carried")
        own = [u for u in units if job_named(it["job"], u)]
        if not own:
            # a cited scope note that names no job ('For diesel engine vehicles, see "Maintenance Schedule" in
            # the Duramax diesel supplement.'): the item must name that scope, as its own or as an exception
            for u in [u for u in units if not jobs_named(u)]:
                for pol, content, toks in scope_restrictions(_label_part(u)):
                    for kind, want in toks.items():
                        if kind in ("model", "equipment"):
                            continue
                        named = set().union(*[_value_kind_hits(kind, v) for v in pos_vals + neg_vals]) if pos_vals + neg_vals else set()
                        if not _tokens_meet(kind, want, named):
                            out.append(f"{kind}_scope_not_carried")
        for u in own:
            for pol, content, toks in scope_restrictions(_label_part(u)):
                for kind, want in toks.items():
                    if kind == "model":
                        continue
                    if kind == "equipment":
                        x = compact(next(iter(want)))
                        if any(compact(v) and (x in compact(v) or compact(v) in x) for v in neg_vals):
                            continue
                        if any(x in compact(v) for v in pos_vals):
                            out.append("equipment_scope_contradicted")
                        elif not appl.get("equipment"):
                            out.append("equipment_scope_not_carried")
                        continue
                    have_pos = set().union(*[_value_kind_hits(kind, v) for v in pos_vals]) if pos_vals else set()
                    have_neg = set().union(*[_value_kind_hits(kind, v) for v in neg_vals]) if neg_vals else set()
                    if kind == "drive" and appl.get("drive"):
                        have_pos |= _value_kind_hits("drive", appl["drive"])
                    if pol == "+":
                        if _tokens_meet(kind, want, have_pos):
                            continue
                        if kind == "transmission" and any(it["job"] in TRANSMISSION_JOBS.get(w, ()) for w in want):
                            continue  # 'Dual clutch transmission (DCT) fluid': the job is that transmission's own
                        if kind == "powertrain" and want == {"gas"} and appl.get("engine") and not _value_kind_hits("powertrain", appl["engine"]) - {"gas"}:
                            continue  # '(Gasoline engine) 2.0 MPI': a named gasoline engine
                        if kind in ("powertrain", "engine") and ({"powertrain", "engine"} - {kind}) & set(toks) and \
                                _tokens_meet("engine", toks.get("engine", set()), set().union(*[_value_kind_hits("engine", v) for v in pos_vals]) if pos_vals else set()):
                            continue  # '(1.8L Hybrid only.)' carried by the engine '1.8L Hybrid'
                        out.append(f"{kind}_scope_contradicted" if _tokens_meet(kind, want, have_neg) else f"{kind}_scope_not_carried")
                    else:
                        if _tokens_meet(kind, want, have_neg) or any(compact(content) in compact(v) for v in pos_vals):
                            continue  # an *_except value, or the same negated scope ('Non Turbo Model')
                        if _tokens_meet(kind, want, have_pos):
                            out.append(f"{kind}_scope_contradicted")
                        elif kind == "transmission" and want <= {"dsg"} and it["job"] not in ("dual_clutch_fluid", "dct_fluid"):
                            continue  # 'Transmission, Automatic ... for non-DSG': the automatic transmission's own job
                        elif have_pos:
                            continue  # a narrower scope of the same kind ('Except 1.4L' -> engine '1.8L')
                        else:
                            out.append(f"{kind}_scope_not_carried")
    return sorted(set(out), key=out.index)


def plan_engine_reasons(it: dict, src: dict, texts: list[str]) -> list[str]:
    """Mopar schedule data: the item's engine scope ('3.6L/5.7L', 'SRT') must be named by the service
    text, the plan title or the document title, and not negated there ('Non SRT Engines' does not
    state SRT)."""
    eng = (it.get("applicability") or {}).get("engine")
    if not eng:
        return []
    out = []
    for tok in [t.strip() for t in str(eng).split("/") if t.strip()]:
        disp = re.fullmatch(r"(\d\.\d)L?", tok)
        pat = rf"\b{re.escape(disp.group(1))}\s?L?\b" if disp else rf"\b{re.escape(tok)}\b"
        pos = neg = False
        for t in texts:
            for m in re.finditer(pat, t, re.I):
                if re.search(r"\b(?:non|except|excluding|without)[- ]?\s*$", t[max(0, m.start() - 12):m.start()], re.I):
                    neg = True
                else:
                    pos = True
        if not pos:
            out.append("engine_scope_contradicted" if neg else "engine_scope_not_stated")
    return sorted(set(out))


def verify_item(ctx: Ctx, it: dict, sources: dict) -> dict:
    groups: "OrderedDict[str, list]" = OrderedDict()
    for c in it["cites"]:
        groups.setdefault(c["source"], []).append(c)
    results, quote_reasons, scope = [], [], []
    for key, cites in groups.items():
        src = sources.get(key)
        if src is None:
            results.append(fail("source_missing", "text", key))
            continue
        fam = family_for(ctx.make, src, cites)
        if fam is None:
            results.append(fail("no_verifier_for_layout", "text", key))
            continue
        scope += [x for x in scope_reasons(ctx, it, src, cites) if x not in scope]
        if src.get("kind") != "json_file":
            if ctx.docs.pages(src) is None:
                results.append(fail("page_text_missing", "text", key))
                continue
            for c in cites:
                st = quote_status(ctx, src, c)
                if st is None:
                    quote_reasons.append("quote_not_on_page")
                elif st == "label" and not getattr(fam, "grid_ok", False):
                    quote_reasons.append("quote_not_on_page")
            quote_reasons += extent_reasons(ctx, it, src, cites)
        try:
            r = fam(ctx, it, src, cites)
        except Exception as exc:  # noqa: BLE001 - one odd page must not stop the run; reported
            r = fail("verifier_error", "text", f"{type(exc).__name__}: {exc}")
        r["source"] = key
        results.append(r)
    out = combine_groups(results)
    quote_reasons += scope
    if quote_reasons:
        out = res(False, quote_reasons + out["reasons"], out["method"], out["evidence"], out["warnings"])
    return out


def run_make(make: str) -> list[dict]:
    docs = Docs()
    ctx = Ctx(docs, make)
    records = []
    for path in sorted((WORK / make / "staging").glob("*/maintenance*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ctx.line = path.parent.name
        for it in data.get("items", []):
            r = verify_item(ctx, it, data.get("sources", {}))
            records.append({
                "make": make, "line": path.parent.name, "file": path.relative_to(ROOT).as_posix(), "item_id": it["id"],
                "job": it["job"], "action": it["action"], "condition": it["condition"], "occurrence": it["occurrence"],
                "years": it["years"], "generation": it.get("generation"), "engine": it.get("engine"),
                "applicability": it.get("applicability"), "interval_km": it.get("interval_km"),
                "interval_miles_original": it.get("interval_miles_original"), "interval_months": it.get("interval_months"),
                # method: text | grid | json | monitor; a schedule printed as one list block per interval
                # point is read like a grid (the points where the line is listed) -> method grid, layout list
                "verdict": "CONFIRMED" if r["ok"] else "UNCONFIRMED", "reasons": r["reasons"],
                "method": "grid" if r["method"] == "list" else r["method"], "layout": r["method"],
                "evidence": r["evidence"], "warnings": r["warnings"],
            })
    docs.close()
    return records


def all_makes() -> list[str]:
    """Every make with a maintenance staging file (a make whose files hold no item gets an empty list)."""
    return sorted({p.parts[-4] for p in WORK.glob("*/staging/*/maintenance*.json")})


def summarize(records: list[dict]) -> dict:
    out = {"items": len(records), "verdict": Counter(), "method": Counter(), "reasons": Counter(),
           "method_verdict": Counter(), "layout": Counter(), "warnings": Counter()}
    for r in records:
        out["verdict"][r["verdict"]] += 1
        out["method"][r["method"]] += 1
        out["method_verdict"][f"{r['method']}:{r['verdict']}"] += 1
        out["layout"][r.get("layout", r["method"])] += 1
        for x in r["reasons"]:
            out["reasons"][x] += 1
        for x in r["warnings"]:
            out["warnings"][x] += 1
    return {k: (dict(v.most_common()) if isinstance(v, Counter) else v) for k, v in out.items()}


def debug_item(make: str, item_id: str) -> int:
    """--item <id>: the per-source results of one item (calibration aid)."""
    docs = Docs()
    ctx = Ctx(docs, make)
    for path in sorted((WORK / make / "staging").glob("*/maintenance*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        ctx.line = path.parent.name
        for it in data.get("items", []):
            if it["id"] != item_id:
                continue
            print("scope", [scope_reasons(ctx, it, data["sources"][k], [c for c in it["cites"] if c["source"] == k])
                            for k in dict.fromkeys(c["source"] for c in it["cites"]) if k in data["sources"]])
            groups: "OrderedDict[str, list]" = OrderedDict()
            for c in it["cites"]:
                groups.setdefault(c["source"], []).append(c)
            for key, cites in groups.items():
                src = data["sources"][key]
                fam = family_for(make, src, cites)
                print(key, [quote_status(ctx, src, c) for c in cites] if src.get("kind") != "json_file" else "json")
                print("   ", fam(ctx, it, src, cites) if fam else "no family")
    docs.close()
    return 0


def main(argv: list[str]) -> int:
    if "--item" in argv:
        i = argv.index("--item")
        return debug_item(argv[0], argv[i + 1])
    makes = [a for a in argv if not a.startswith("--")] or all_makes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = OUT_DIR / "summary.json"
    # a run over some makes updates their entries; a full run rewrites the summary
    partial = any(not a.startswith("--") for a in argv)
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if partial and summary_path.exists() else {}
    for make in makes:
        records = run_make(make)
        # the round-3 audit rules (scripts/maintenance_audit_rules.py) apply after the checks above
        from maintenance_audit_rules import apply as audit_rules

        records = audit_rules(make, records, ROOT / "data_work")
        (OUT_DIR / f"{make}.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
        summary[make] = summarize(records)
        s = summary[make]
        print(f"{make}: items {s['items']}, {s['verdict']}, methods {s['method']}", flush=True)
        for reason, n in list(s["reasons"].items())[:8]:
            print(f"   {n:5d} {reason}")
    summary_path.write_text(json.dumps(dict(sorted(summary.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
