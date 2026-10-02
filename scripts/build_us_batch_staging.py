"""Batch staging builder: the source-derived base layer for every line of a make.

Built only from cached public datasets (no model memory, no hand-authored values):
  generations     year blocks from vPIC Canadian wheelbase changes and existing DB
                  generation codes (EPA + vPIC, prompt section 3.3)
  configurations  EPA vehicles.csv (year, engine, transmission, drive, fuel economy)
  dimensions      vPIC Canadian specifications (cm -> mm, kg), SECONDARY
  recalls         NHTSA recallsByVehicle
  complaints      NHTSA complaintsByVehicle: component counts and symptom patterns
  TSBs            NHTSA Manufacturer Communications (used by issues only)
  known issues    rule-based (prompt section 7): recall, TSB, complaint pattern

Owner-manual facts (oil, fluids, capacities ...) are merged later from
data_work/<make>/staging/<line>/manual_facts.json when present.

Output per line: data_work/<make>/staging/<line>/staging.json (+ conflicts.csv, gaps.csv);
summary: data_work/<make>/staging/batch_summary.json.

  .venv/Scripts/python.exe scripts/build_us_batch_staging.py hyundai [--line sonata]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import ROOT, WORK, raw_ref  # noqa: E402
from us_tech_lines import MAKES, Line, lines_for  # noqa: E402
from us_tech_sources import (  # noqa: E402
    RAW_ROOT,
    epa_for_line,
    mfrcomms_for_line,
    nhtsa_for_line,
    read_csv,
    slug,
    vpic_ca_for_line,
)

sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402

MARKET = "US"
COMPLAINT_PATTERN_THRESHOLD = 10  # prompt section 7, kept as a constant
VPIC_LEGEND = "https://vpic.nhtsa.dot.gov/api/ (GetCanadianVehicleSpecifications: OL/OW/OH/WB/TWF/TWR in cm, CW in kg, WD front/rear %)"

# Symptom vocabulary for NHTSA complaint narratives and manufacturer-communication summaries
# (upper-cased text). Labels classify text; every issue still quotes its source text.
# key: (label, regex, component, severity)
SYMPTOMS = {
    "engine-failure": ("engine failure / knocking / seizure", r"\bENGINE (FAILURE|FAILED|SEIZ\w*|KNOCK\w*)|\bCONNECTING ROD|\bROD BEARING|\bENGINE (DIED|BLEW|BLOWN)\b", "ENGINE", "HIGH"),
    "oil-consumption": ("excessive oil consumption", r"\bOIL CONSUMPTION|\bBURN\w* (EXCESSIVE )?OIL\b|\bCONSUM\w* (EXCESSIVE )?OIL\b", "ENGINE", "HIGH"),
    "engine-fire": ("engine compartment fire", r"\b(ENGINE|VEHICLE) (COMPARTMENT )?(FIRE|CAUGHT FIRE)\b|\bCAUGHT (ON )?FIRE\b", "ENGINE", "HIGH"),
    "fuel-pump-stall": ("fuel pump / stalling", r"\bFUEL PUMP\b|\bSTALL(S|ED|ING)?\b", "FUEL SYSTEM", "HIGH"),
    "fuel-leak": ("fuel leak / fuel odor", r"\bFUEL LEAK|\bGAS(OLINE)? (LEAK|SMELL|ODOR)|\bFUEL (SMELL|ODOR)", "FUEL SYSTEM", "HIGH"),
    "loss-of-power": ("loss of power / limp mode", r"\bLOSS OF (MOTIVE )?POWER\b|\bLOST (MOTIVE )?POWER\b|\bLIMP (HOME )?MODE\b|\bREDUCED (ENGINE )?POWER\b", "POWERTRAIN", "HIGH"),
    "hesitation": ("hesitation / delayed acceleration", r"\bHESITAT\w*|\bDELAY\w* (IN )?ACCELERAT\w*", "POWERTRAIN", "MEDIUM"),
    "misfire": ("misfire / rough running", r"\bMISFIRE\w*|\bRUNS? ROUGH\b|\bROUGH IDLE\b|\bCARBON (BUILD\w*|DEPOSIT\w*)", "ENGINE", "MEDIUM"),
    "overheating": ("overheating", r"\bOVERHEAT\w*", "COOLING", "HIGH"),
    "coolant-leak": ("water pump / coolant leak", r"\bWATER PUMP\b|\bCOOLANT (LEAK\w*|LOSS|CONSUMPTION)|\bLEAKING COOLANT\b", "COOLING", "MEDIUM"),
    "turbo": ("turbocharger failure", r"\bTURBO\w* (FAIL\w*|LEAK\w*|NOISE)|\bWASTEGATE\b", "ENGINE", "HIGH"),
    "timing-drive": ("timing chain / belt", r"\bTIMING (CHAIN|BELT)\b", "ENGINE", "HIGH"),
    "harsh-shifting": ("harsh / erratic shifting", r"\b(HARSH|ROUGH|ERRATIC|JERK\w*|LURCH\w*|CLUNK\w*)\b.{0,40}\bSHIFT\w*|\bSHIFT\w*.{0,40}\b(HARSH|ROUGH|ERRATIC|JERK\w*|LURCH\w*)\b", "TRANSMISSION", "MEDIUM"),
    "transmission-failure": ("transmission failure / slipping", r"\bTRANSMISSION (FAIL\w*|SLIP\w*)|\bSLIPPING\b|\bWILL NOT SHIFT\b|\bSTUCK IN (GEAR|NEUTRAL)\b", "TRANSMISSION", "HIGH"),
    "torque-converter": ("torque converter shudder", r"\bSHUDDER\w*|\bTORQUE CONVERTER\b", "TRANSMISSION", "MEDIUM"),
    "dct-clutch": ("dual-clutch transmission", r"\bDUAL[- ]CLUTCH\b|\bDCT\b|\bCLUTCH (SLIP\w*|SHUDDER\w*|OVERHEAT\w*)", "TRANSMISSION", "MEDIUM"),
    "cvt": ("CVT problems", r"\bCVT\b|\bCONTINUOUSLY VARIABLE\b", "TRANSMISSION", "MEDIUM"),
    "brake-assist": ("brake vacuum pump / assist loss", r"\bVACUUM PUMP\b|\bBRAKE ASSIST\b|\bHARD (BRAKE )?PEDAL\b|\bBRAKE PEDAL (WAS |BECAME )?(HARD|STIFF)\b", "BRAKES", "HIGH"),
    "brake-failure": ("brake failure / ABS", r"\bABS (MODULE|PUMP|UNIT)\b|\bANTI-?LOCK.{0,20}(FAIL\w*|MALFUNCTION)|\bBRAKES? (FAIL\w*|LOSS)\b|\bLOSS OF BRAK\w*", "BRAKES", "HIGH"),
    "parking-brake": ("electronic parking brake", r"\bPARKING BRAKE (FAIL\w*|MALFUNCTION|STUCK|WILL NOT)|\bEPB\b", "BRAKES", "MEDIUM"),
    "steering-loss": ("power steering loss", r"\b(LOSS OF|LOST) (POWER )?STEERING\b|\bPOWER STEERING (FAIL\w*|WARNING|ASSIST)|\bSTEERING (BECAME|IS|WAS) (HARD|STIFF|DIFFICULT)\b", "STEERING", "HIGH"),
    "steering-noise": ("steering column / coupler noise", r"\bSTEERING (COLUMN|COUPL\w*|CLUNK\w*|NOISE)\b|\bINTERMEDIATE SHAFT\b", "STEERING", "MEDIUM"),
    "suspension": ("suspension wear (struts, arms, springs)", r"\bSTRUTS?\b|\bCONTROL ARMS?\b|\bSWAY BAR\b|\bBALL JOINTS?\b|\bCOIL SPRINGS?\b|\bSHOCK ABSORBERS?\b", "SUSPENSION", "MEDIUM"),
    "airbag": ("air bag warning / occupant classification", r"\bAIR ?BAG (LIGHT|WARNING)\b|\bPASSENGER AIR ?BAG (OFF|DISABLED)\b|\bOCCUPANT CLASSIFICATION\b", "AIR BAGS", "HIGH"),
    "false-braking": ("pre-collision false braking", r"\bPRE-?COLLISION\b|\bPHANTOM BRAK\w*|\bFALSE(LY)? BRAK\w*|\bBRAKED (BY ITSELF|ON ITS OWN)\b|\bAUTOMATIC EMERGENCY BRAK\w*", "BRAKES", "HIGH"),
    "battery-drain": ("battery drain / no start", r"\bBATTERY (DRAIN\w*|DEAD|DIED)\b|\bPARASITIC\b|\b(WILL NOT|WON'T|FAIL\w* TO) START\b|\bNO[- ]START\b", "ELECTRICAL", "MEDIUM"),
    "hybrid-system": ("hybrid / high-voltage system", r"\bHYBRID SYSTEM\b|\bINVERTER\b|\bCHECK HYBRID\b|\bHIGH[- ]VOLTAGE BATTERY\b|\bICCU\b|\bON-?BOARD CHARGER\b", "ELECTRICAL", "HIGH"),
    "infotainment": ("infotainment / display", r"\bINFOTAINMENT\b|\bHEAD UNIT\b|\bTOUCH ?SCREEN\b|\bCARPLAY\b|\bANDROID AUTO\b", "ELECTRICAL", "LOW"),
    "air-conditioning": ("air conditioning", r"\bA/?C (COMPRESSOR|CONDENSER|NOT COOL\w*|BLOW\w* (WARM|HOT))\b|\bAIR CONDITION\w* (FAIL\w*|NOT|COMPRESSOR)\b", "HVAC", "LOW"),
    "water-leak": ("water leak into cabin", r"\bWATER LEAK\w*|\bSUNROOF.{0,30}\bLEAK\w*|\bLEAK\w* (INTO|IN) (THE )?(CABIN|INTERIOR|TRUNK)\b", "BODY", "LOW"),
    "door-latch": ("door lock / latch", r"\bDOOR (LATCH|LOCK)\w* (FAIL\w*|MALFUNCTION|WILL NOT)", "BODY", "MEDIUM"),
    "seat-belt": ("seat belt", r"\bSEAT ?BELT\w* (FAIL\w*|RETRACT\w*|WILL NOT|DID NOT)", "SEAT BELTS", "MEDIUM"),
    "paint": ("paint peeling", r"\bPAINT (PEEL\w*|CHIP\w*|FLAK\w*)|\bCLEAR ?COAT\b", "BODY", "LOW"),
}
# Manufacturer communications that are not defect evidence for an issue: recall/campaign
# notices (the recall itself is evidence), best-practice or placeholder entries, and
# bulletins spanning more model years than one generation can.
TSB_EXCLUDE = re.compile(
    r"\bRECALL\b|\bCAMPAIGN\b|BEST PRACTICE|TO BE PROVIDED|INVESTIGAT\w*|PRE-?DELIVERY|\bPDI\b",
    re.I,
)
TSB_MAX_YEARS = 8


def tsb_text(summary: str) -> str:
    return re.split(r"\bKEYWORDS?\b|\*[A-Z]{2}\b|\bUPDATED\b", summary or "", maxsplit=1, flags=re.I)[0]


def tsb_relevant(row: dict) -> bool:
    years = [y for y in row["years"] if 1990 < y < 2030]
    return bool(years) and len(years) <= TSB_MAX_YEARS and not TSB_EXCLUDE.search(row["summary"] or "")


COMPONENT_HINTS = {  # NHTSA recall component prefix -> symptom keys that describe the same unit
    "ENGINE": ["engine-failure", "oil-consumption", "engine-fire", "misfire", "turbo", "timing-drive", "loss-of-power"],
    "FUEL SYSTEM": ["fuel-pump-stall", "fuel-leak"],
    "POWER TRAIN": ["harsh-shifting", "transmission-failure", "torque-converter", "dct-clutch", "cvt", "loss-of-power"],
    "SERVICE BRAKES": ["brake-assist", "brake-failure"],
    "PARKING BRAKE": ["parking-brake"],
    "STEERING": ["steering-loss", "steering-noise"],
    "SUSPENSION": ["suspension"],
    "AIR BAGS": ["airbag"],
    "FORWARD COLLISION AVOIDANCE": ["false-braking"],
    "ELECTRICAL SYSTEM": ["battery-drain", "hybrid-system"],
    "SEAT BELTS": ["seat-belt"],
    "LATCHES/LOCKS/LINKAGES": ["door-latch"],
    "ENGINE AND ENGINE COOLING": ["engine-failure", "oil-consumption", "engine-fire", "overheating", "coolant-leak"],
}
SAFETY_WORDS = re.compile(
    r"CRASH|FIRE|INJUR|DEATH|LOSS OF (MOTIVE POWER|DRIVE|STEERING|BRAK)|STALL|ROLL AWAY|ROLLAWAY",
    re.I,
)
DRIVE = {
    "Front-Wheel Drive": "FWD",
    "All-Wheel Drive": "AWD",
    "4-Wheel Drive": "4WD",
    "4-Wheel or All-Wheel Drive": "4WD",
    "Rear-Wheel Drive": "RWD",
    "Part-time 4-Wheel Drive": "4WD",
    "2-Wheel Drive": "2WD",
}
POWERTRAIN = {"": "ICE", "Hybrid": "HEV", "Plug-in Hybrid": "PHEV", "EV": "BEV", "FFV": "ICE", "Diesel": "DIESEL", "CNG": "ICE", "Bifuel (CNG)": "ICE", "FCV": "FCEV", "eFCV": "FCEV"}
BODY_RE = re.compile(r"\b(\d)\s?DR\b\s*(SEDAN|HATCH\w*|SUV|COUPE|WAGON|CONVERTIBLE|CABRIOLET|ROADSTER|VAN|LIFTBACK|CROSSOVER)?", re.I)


# ---------------------------------------------------------------------------------------
class Staging:
    def __init__(self, line: Line):
        self.line = line
        self.sources: dict[str, dict] = {}
        self.errors, self.gaps, self.conflicts, self.notes = [], [], [], []

    def add_source(self, key, **item):
        self.sources.setdefault(key, {"key": key, **item})
        return key


def manifest_row(path: Path, url: str) -> dict:
    for row in read_csv(path):
        if row.get("url") == url and row.get("status") == "ok":
            return row
    return {}


def epa_source(st: Staging) -> str:
    row = next(
        (r for r in read_csv(WORK / "_shared" / "manifest.csv") if r.get("kind") == "epa_vehicles_csv" and r["status"] == "ok"),
        {},
    )
    return st.add_source(
        "epa",
        kind="epa",
        path=row.get("path", "data_work/_shared/raw/epa/vehicles.csv.zip"),
        url=row.get("url", "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"),
        sha256=row.get("sha256"),
        retrieved_at=row.get("retrieved_at", ""),
        tier="A",
        source_type="US_FEDERAL_DATASET",
        registry="epa",
        title="EPA fueleconomy.gov vehicles.csv",
        publisher="U.S. DOE / EPA (fueleconomy.gov)",
        authenticity="OFFICIAL_PUBLISHER",
    )


# ---- generations -----------------------------------------------------------------------
def db_generations(db: sqlite3.Connection, line: Line) -> list[dict]:
    make = MAKES[line.make]["epa"]
    out = []
    for model in line.db_models:
        rows = db.execute(
            """select g.id, g.code, g.name, g.start_year, g.end_year, v.year_from
               from vehicle_generations g join vehicle_models m on m.id=g.model_id
               join vehicle_makes mk on mk.id=m.make_id
               left join vehicle_variants v on v.generation_id=g.id and v.market='US'
               where mk.name=? and m.name=? and g.is_demo=0 and g.code not like 'UNRESOLVED%'""",
            (make, model),
        ).fetchall()
        gens = {}
        for gid, code, name, start, end, year in rows:
            entry = gens.setdefault(gid, {"id": gid, "code": code, "name": name, "start_year": start,
                                          "end_year": end, "db_model": model, "years": set()})
            if year:
                entry["years"].add(year)
        out += list(gens.values())
    return out


def family(model_text: str) -> str:
    """Body family of a Canadian specification row: first word of the model + body style.

    Trim, drive and powertrain words are ignored so that hybrids and trims compare with
    the base body; different bodies (sedan vs hatchback) stay apart."""
    text = model_text.upper()
    body = BODY_RE.search(text)
    words = text.split()
    # "C-CLASS C250 ..." (2014) and "C CLASS C 300 ..." (2015+) are the same model word.
    first = re.sub(r"-CLASS$", "", words[0]) if words else ""
    return first + ("|" + body.group(0).upper().replace(" ", "") if body else "")


def detect_generations(st: Staging, epa: list[dict], ca: list[dict], dbgens: list[dict]) -> list[dict]:
    line = st.line
    years = sorted({int(r["year"]) for r in epa})
    if not years:
        return []
    fam_years = defaultdict(set)
    for r in ca:
        fam_years[family(r["model"])].add(r["year"])
    main = max(fam_years, key=lambda f: (len(fam_years[f]), f)) if fam_years else None

    def common_family(prev, year):
        """Compare like with like: the main body family if present in both years, else the
        family present in both years with the most rows; None when no family spans both."""
        both = [f for f, ys in fam_years.items() if prev in ys and year in ys]
        if main in both:
            return main
        return max(both, key=lambda f: (len(fam_years[f]), f)) if both else None

    def values(year, field, fam=None):
        return Counter(
            r[field]
            for r in ca
            if r["year"] == year and r.get(field) and (fam is None or family(r["model"]) == fam)
        )

    def starting(year, prev):
        return [f for f, ys in fam_years.items() if year in ys and prev not in ys]

    last_year = years[-1]

    def timeline(field, fam):
        out = defaultdict(set)
        for r in ca:
            if r.get(field) and (fam is None or family(r["model"]) == fam):
                out[r[field]].add(r["year"])
        return out

    def transition(prev, year, field, fam):
        """A value appears in `year` and stays (or the data ends), while a value seen before
        disappears in `prev` or `year`. Transition years with both generations on sale and
        variants listed every year (short/long wheelbase, trims) do not trigger it."""
        tl = timeline(field, fam)
        # `prev` and `year` are consecutive EPA years of the line; vPIC can list the line in
        # the years between (sold in Canada only), so a change may happen inside that gap.
        new = [
            v for v, ys in tl.items()
            if prev < min(ys) <= year and year in ys and (len(ys) >= 2 or max(ys) == last_year)
        ]
        old = [v for v, ys in tl.items() if min(ys) <= prev and prev <= max(ys) <= year]
        if not new or not old:
            return None
        numbers = all(re.fullmatch(r"\d+", v) for v in new + old)
        # Each appearing value is matched with the nearest disappearing one (short with short,
        # long with long wheelbase). Within one body family the largest of these distances
        # counts; across families (a renamed or replacing body) the smallest, so trim spread
        # does not count.
        pick = max if fam is not None else min
        step = (
            pick(min(abs(int(x) - int(y)) for x in old) for y in new) if numbers else None
        )
        return "/".join(sorted(old)), "/".join(sorted(new)), step

    def compare(prev, year, field, fam):
        """Transition within the main body family, or across all rows of the line (bodies are
        renamed at a redesign); the first that shows one wins."""
        spans = main is not None and fam == main
        for scope in [fam] if spans else ([fam] if fam is not None else []) + [None]:
            found = transition(prev, year, field, scope)
            if found:
                return found
        return None

    def db_codes(year):
        return {g["code"] for g in dbgens if year in g["years"]}

    def new_family_wheelbase(prev, year):
        """A body family that starts this year with a wheelbase no row had the year before
        (old rows can stay listed in the Canadian data for years after a redesign)."""
        before = {r["wheelbase_cm"] for r in ca if r["year"] == prev and r.get("wheelbase_cm")}
        for f in starting(year, prev):
            if len(fam_years[f]) < 2 and max(fam_years[f]) != last_year:
                continue
            wbs = {r["wheelbase_cm"] for r in ca if r["year"] == year and family(r["model"]) == f and r.get("wheelbase_cm")}
            if wbs and before and not (wbs & before):
                return f"{f} wheelbase {'/'.join(sorted(wbs))} cm"
        return None

    def epa_rename(prev, year):
        """An EPA base model that starts in `year` while another one of the line ends by `year`."""
        names = defaultdict(set)
        for r in epa:
            names[r["baseModel"]].add(int(r["year"]))
        started = [n for n, ys in names.items() if min(ys) == year]
        ended = [n for n, ys in names.items() if min(ys) < year and max(ys) in (prev, year)]
        return f"{'/'.join(ended)} -> {'/'.join(started)}" if started and ended else None

    mcum_starts = mcum_generation_starts(line)
    boundaries = {}
    for prev, year in zip(years, years[1:]):
        reasons = []
        fam = common_family(prev, year)
        gap_years = set(range(prev + 1, year))
        if gap_years and not any(r["year"] in gap_years for r in ca):
            # EPA and vPIC both lack the years in between: the line was off the US market.
            reasons.append(
                f"EPA vehicles.csv has no rows for MY{prev + 1}"
                + (f"-{year - 1}" if year - prev > 2 else "")
                + f" and vPIC has no Canadian rows for those years (the line returns in MY{year})"
            )
        changed_wb = compare(prev, year, "wheelbase_cm", fam)
        ca_, cb = db_codes(prev), db_codes(year)
        if ca_ and cb and not (ca_ & cb):
            reasons.append(f"existing DB generation codes {sorted(ca_)} (MY{prev}) -> {sorted(cb)} (MY{year})")
        changes = []
        for field, label in (("length_cm", "overall length"), ("width_cm", "overall width"),
                             ("height_cm", "overall height"), ("track_front_cm", "front track"),
                             ("track_rear_cm", "rear track")):
            pair = compare(prev, year, field, fam)
            if pair and pair[2] is not None:
                changes.append((label, pair[0], pair[1], pair[2]))
        if gap_years and any(r["year"] in gap_years for r in ca):
            if changes or changed_wb:
                reasons.append(
                    f"EPA vehicles.csv has no rows for MY{min(gap_years)}"
                    + (f"-{max(gap_years)}" if len(gap_years) > 1 else "")
                    + " and the vPIC dimensions change across that gap ("
                    + ", ".join(f"{c[0]} {c[1]} -> {c[2]} cm" for c in changes)
                    + (f"{', ' if changes else ''}wheelbase {changed_wb[0]} -> {changed_wb[1]} cm" if changed_wb else "")
                    + ")"
                )
            else:
                st.notes.append(
                    f"MY{min(gap_years)}-{max(gap_years)}: no EPA rows, no dimension change in vPIC; not a generation boundary"
                )
        if changed_wb and changed_wb[2] is not None:
            a, b, step = changed_wb
            # 1 cm is within the re-measurement noise of the Canadian data unless another body
            # dimension moved by 3 cm or more in the same year.
            body = [c for c in changes if c[3] >= 3]
            if step >= 2 or body:
                reasons.append(
                    f"vPIC Canadian specifications: wheelbase {a} cm (MY{prev}) -> {b} cm (MY{year})"
                    + ("" if step >= 2 else ", with " + ", ".join(f"{c[0]} {c[1]} -> {c[2]} cm" for c in body))
                )
        big = [
            c for c in changes
            if c[0] in ("overall length", "overall height", "overall width") and c[3] >= DIMENSION_STEP_CM
        ]
        if big:
            reasons.append(
                "vPIC Canadian specifications: "
                + ", ".join(f"{label} {x} -> {y} cm" for label, x, y, _ in big)
                + f" (MY{prev} -> MY{year}; a change of {DIMENSION_STEP_CM} cm or more)"
            )
        appeared = new_family_wheelbase(prev, year)
        renamed = epa_rename(prev, year)
        if appeared and renamed and not reasons:
            reasons.append(
                f"EPA model name changes ({renamed}) and vPIC lists a new body family "
                f"({appeared}) from MY{year}"
            )
        # The site often labels a generation by its European model year, one year before the
        # US one; the vPIC change must still fall exactly on this US model year.
        mcum_year = year if year in mcum_starts else (year - 1 if year - 1 in mcum_starts else None)
        solid = [c for c in changes if c[3] >= 2]
        if mcum_year is not None and (solid or appeared):
            reasons.append(
                f"mycarusermanual.com generation page starts at {mcum_year} ({mcum_starts[mcum_year]}), corroborated by vPIC "
                + (", ".join(f"{label} {x} -> {y} cm" for label, x, y, _ in solid) if solid else f"new body family {appeared}")
                + f" (MY{prev} -> MY{year})"
            )
        elif year in mcum_starts:
            st.notes.append(f"MY{year}: mycarusermanual.com generation page starts here, but vPIC shows no dimension change; not used")
        if not reasons and changes:
            st.notes.append(
                f"MY{year}: vPIC dimension change without a generation signal ("
                + ", ".join(f"{label} {x} -> {y}" for label, x, y, _ in changes) + "); treated as a facelift"
            )
        if reasons:
            boundaries[year] = reasons
        if fam is None and any(r["year"] == year for r in ca):
            st.notes.append(f"MY{year}: no vPIC body family spans MY{prev} and MY{year}; compared across all rows")
        if not changed_wb and len({r["wheelbase_cm"] for r in ca if r["year"] == year}) > 1:
            st.notes.append(f"MY{year}: several wheelbases in vPIC Canadian rows (mixed body/generation year)")
    apply_media_evidence(st, years, boundaries)
    # Two boundaries one model year apart: the second is the Canadian data dropping the old
    # rows a year after the new body was listed (BMW 5 Series 2024/2025); keep the first.
    for year in sorted(boundaries):
        if year - 1 in boundaries:
            st.notes.append(
                f"MY{year}: boundary signal one year after MY{year - 1} ({'; '.join(boundaries[year])}); merged into the MY{year - 1} generation"
            )
            del boundaries[year]
    blocks, start = [], years[0]
    for year in years[1:] + [None]:
        if year is None or year in boundaries:
            end = years[years.index(year) - 1] if year else years[-1]
            blocks.append({"start_year": start, "end_year": end, "boundary": boundaries.get(start, []),
                           "end_boundary": bool(year)})
            start = year
    used = set()
    gens = []
    for block in blocks:
        span = set(range(block["start_year"], block["end_year"] + 1))
        candidates = sorted(
            (g for g in dbgens if g["id"] not in used and g["years"] & span),
            key=lambda g: -len(g["years"] & span),
        )
        if not candidates and block is blocks[0] and not block["boundary"]:
            # The scope starts at 2014; an existing generation whose variants end the year
            # before, with no boundary signal at 2014, is the same generation continuing.
            candidates = [
                g for g in dbgens
                if g["id"] not in used and g["years"] and max(g["years"]) == block["start_year"] - 1
            ]
        match = candidates[0] if candidates else None
        open_ended = block["end_year"] == 2026 and block["end_year"] == line.years[1]
        bases = Counter(r["baseModel"] for r in epa if int(r["year"]) in span)
        db_model = (
            match["db_model"]
            if match
            else next((b for b, _ in bases.most_common() if b in line.db_models), line.db_models[0])
        )
        if match:
            used.add(match["id"])
            code, name = match["code"], match["name"]
            if match["years"] - span:
                st.notes.append(
                    f"generation {code}: existing DB variants also cover MY{sorted(match['years'] - span)} outside the detected block"
                )
        else:
            # New generation: the code and name state only the US scope block, never a start
            # year that no source gave (a block at the scope start may have begun earlier).
            first, last = block["start_year"], block["end_year"]
            code = f"US{first}" + ("+" if open_ended else f"-{last}")
            if not block["boundary"]:
                name = f"{line.name} (US, through {last})"
            else:
                name = f"{line.name} {first}" + ("+" if open_ended else f"-{last}") + " (US)"
        evidence = list(block["boundary"])
        if not evidence:
            evidence = [
                f"first US model year of the line in EPA vehicles.csv: {years[0]}"
                if block is blocks[0] and years[0] > 2014
                else "scope starts at MY2014; the generation may have begun earlier"
                if block is blocks[0]
                else "no boundary signal"
            ]
        gens.append(
            {
                "code": code,
                "name": name,
                "db_model": db_model,
                "existing_id": match["id"] if match else None,
                "start_year": block["start_year"],
                "end_year": block["end_year"],
                "open_ended": open_ended,
                # Only years backed by a detected boundary (or the last EPA year of a line that
                # ended before 2026) are written into empty generation year fields.
                "start_known": bool(block["boundary"]) or (block is blocks[0] and years[0] > 2014),
                "end_known": block["end_boundary"] or (not open_ended and block["end_year"] < 2026),
                "boundary_evidence": evidence,
                "evidence_tier": "B",
            }
        )
    if not ca:
        st.gaps.append({"scope": line.key, "field": "generation_boundaries",
                        "reason": "no vPIC Canadian specification rows for this line; boundaries from DB codes only"})
    return gens


DIMENSION_STEP_CM = 6  # facelifts in the data change length/height by up to 5 cm

# Preferred order when two sites give different years for one start: Consumer Reports pages
# were checked against the raw HTML; cars.com quotes through a second, decoy-tested read.
MEDIA_SITES = ["consumerreports.org", "cars.com", "caranddriver.com", "edmunds.com", "motortrend.com", "kbb.com"]
MEDIA_CHECKED = {"raw_html_exact", "webfetch_reverified"}  # quotes read only once are not used
REDESIGN = re.compile(r"redesign|all-new|all new|new generation|next[- ]generation|\b\w+-generation\b|generation\b|debut", re.I)
NOT_NEW = re.compile(r"renam|nomenclature|formerly|freshen|refresh|facelift|name change|changed the \w+ name", re.I)
_MEDIA: dict | None = None


def media_evidence(line: Line) -> dict:
    """Generation starts and refreshes that automotive media state for the line, each with a
    verbatim quote and URL (data_work/_shared/generation_evidence.json).
    - A quote counts when it was checked against the page (raw HTML match, or a second
      decoy-tested read); a quote read only once may only confirm another site.
    - A start is strong when a checked quote for that year speaks of a redesign / new
      generation, or both sites list it; one site whose own entry is marked disputed is weak.
    - A start whose texts call it a rename or refresh (and no checked quote says redesign)
      is rejected; such years, and weak ones, never veto a boundary the data show.
    Starts one year apart are one start: the year more sites give, else the preferred site's."""
    global _MEDIA
    if _MEDIA is None:
        path = WORK / "_shared" / "generation_evidence.json"
        _MEDIA = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"lines": {}}
    entry = _MEDIA.get("lines", {}).get(line.key) or {}

    def site_rank(item):
        site = (item.get("site") or "").removeprefix("www.")
        return MEDIA_SITES.index(site) if site in MEDIA_SITES else len(MEDIA_SITES)

    def checked(item):
        return item.get("quote_check", "raw_html_exact") in MEDIA_CHECKED

    raw = [g for g in entry.get("generations", [])
           if isinstance(g.get("first_us_model_year"), int) and g.get("quote") and g.get("url")]
    refreshes = defaultdict(list)
    for item in entry.get("refreshes", []):
        if isinstance(item.get("model_year"), int) and item.get("quote") and item.get("url") and checked(item):
            refreshes[item["model_year"]].append(item)
    clusters = []
    for item in sorted(raw, key=lambda g: g["first_us_model_year"]):
        if clusters and item["first_us_model_year"] - clusters[-1][-1]["first_us_model_year"] <= 1:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    starts, weak, disagreements, rejected = {}, {}, [], []
    for cluster in clusters:
        cluster = [i for i in cluster if checked(i)] + [i for i in cluster if not checked(i)]
        by_year = defaultdict(list)
        for item in cluster:
            by_year[item["first_us_model_year"]].append(item)
        candidates = [y for y in by_year if any(checked(i) for i in by_year[y])]
        if not candidates:
            continue  # only quotes read once: not evidence on their own
        year = max(candidates, key=lambda y: (len(by_year[y]), -min(site_rank(i) for i in by_year[y]), y))
        items = sorted(by_year[year], key=lambda i: (not checked(i), site_rank(i)))
        if len(by_year) > 1:
            disagreements.append((year, sorted(by_year)))
        checked_quotes = " ".join(i["quote"] for i in items if checked(i))
        texts = " ".join(f"{i['quote']} {i.get('listing_quote') or ''} {i.get('note') or ''}" for i in items)
        texts += " " + " ".join(r["quote"] for r in refreshes.get(year, []))
        sites = {i.get("site") for i in items}
        explicit = re.search(r"redesign|all-new|all new|new generation|next[- ]generation|third generation|fourth generation|fifth generation", checked_quotes, re.I)
        if NOT_NEW.search(texts) and not explicit:
            rejected.append((year, items))
        elif len(sites) >= 2 or (REDESIGN.search(checked_quotes) and not all(i.get("agreement") == "disputed" for i in items)):
            starts[year] = items
        else:
            weak[year] = items
    ends = {}
    for item in raw:
        last = item.get("last_us_model_year")
        if isinstance(last, int) and checked(item) and (starts or weak):
            pool = {**weak, **starts}
            first = min(pool, key=lambda y: abs(y - item["first_us_model_year"]))
            ends[first] = max(ends.get(first, last), last)
    return {"starts": starts, "weak": weak, "ends": ends, "refreshes": dict(refreshes),
            "disagreements": disagreements, "rejected": rejected}


def media_reason(items: list[dict], what: str) -> str:
    return "; ".join(
        f'{i.get("site")}: "{i["quote"]}" ({i["url"]})'
        + ("" if i.get("quote_check", "raw_html_exact") in MEDIA_CHECKED else " [quote read once]")
        for i in items[:2]
    ) + f" [{what}]"


def apply_media_evidence(st: Staging, years: list[int], boundaries: dict[int, list[str]]) -> None:
    """Media-stated generation starts become boundaries (or move an adjacent detected one to
    the stated US model year); a detected boundary that falls inside a generation the media
    bound on both sides, or in a year they call a refresh, is dropped. Boundaries backed by
    existing DB generation codes are never moved or dropped by media evidence."""
    media = media_evidence(st.line)
    if not media["starts"] and not media["refreshes"] and not media["weak"]:
        return
    for year, sites in media["disagreements"]:
        st.notes.append(f"media give different first model years {sites} for one generation; MY{year} used")
    for year, items in media["rejected"]:
        st.notes.append(f"MY{year}: media list a new block, but their own text calls it a rename/refresh; not a generation start ({media_reason(items, 'media: not a start')})")
    for year, items in sorted(media["weak"].items()):
        # a weak start (one site, listing or badge only) only confirms a boundary the data shows
        near = [y for y in (year, year - 1, year + 1) if y in boundaries]
        if near:
            media["starts"][year] = items
        else:
            st.notes.append(f"MY{year}: one site lists a new generation without redesign wording and the data show no boundary; not used ({media_reason(items, 'media: weak')})")

    def db_backed(year):
        return any("existing DB generation codes" in r for r in boundaries.get(year, []))

    for start, items in sorted(media["starts"].items()):
        reason = media_reason(items, f"media: generation starts MY{start}")
        if start <= years[0]:
            continue
        # the first EPA model year from the stated start on (the line can skip a year)
        year = next((y for y in years if y >= start), None)
        if year is None:
            continue
        if year in boundaries:
            boundaries[year].append(reason)
            continue
        near = [y for y in (year - 1, year + 1) if y in boundaries]
        movable = [y for y in near if not db_backed(y)]
        if near and not movable:
            st.notes.append(f"MY{year}: media state a generation start, but the DB generation codes place it at MY{near[0]}; DB kept ({reason})")
            continue
        if movable:
            src = movable[0]
            boundaries[year] = boundaries.pop(src) + [reason]
            st.notes.append(f"boundary moved from MY{src} to the media-stated MY{year}")
        else:
            boundaries[year] = [reason]
    starts = sorted(media["starts"])
    contested = {y for y, _ in media["rejected"]} | (set(media["weak"]) - set(media["starts"]))
    for year in sorted(boundaries):
        if db_backed(year) or any("[media:" in r for r in boundaries[year]):
            continue
        if year in contested:
            st.notes.append(f"MY{year}: media disagree whether a generation starts here; the data boundary is kept")
            continue
        inside = [
            s for s in starts
            if s < year and (any(n > year for n in starts) or media["ends"].get(s, 0) >= year)
        ]
        refresh = media["refreshes"].get(year)
        if refresh or inside:
            why = (
                media_reason(refresh, f"media: refresh MY{year}") if refresh
                else media_reason(media["starts"][inside[-1]], f"media: generation started MY{inside[-1]}")
                + (f", next starts MY{min(n for n in starts if n > year)}" if any(n > year for n in starts) else "")
            )
            st.notes.append(f"MY{year}: detected boundary ({'; '.join(boundaries[year])}) dropped; {why}")
            del boundaries[year]


def mcum_generation_starts(line: Line) -> dict[int, str]:
    """First model year of each generation page the mycarusermanual.com crawl found for the line."""
    make = MAKES[line.make]["mcum"]
    starts = {}
    for row in read_csv(WORK / "_mcum" / "manifest.csv"):
        if row["make"] != make or row["model"] not in line.mcum or row["section"] != "_index":
            continue
        if row["http_status"] != "200":
            continue
        first = int(row["years"].split("-")[0])
        starts[first] = f"{row['model']}/{row['body']}/{row['years']}"
    return starts


def generation_for(year, gens):
    for g in gens:
        if g["start_year"] <= year <= g["end_year"]:
            return g["code"]
    return None


# ---- configurations (EPA) ----------------------------------------------------------------
def build_configurations(st: Staging, epa: list[dict], gens: list[dict]) -> list[dict]:
    line = st.line
    groups = defaultdict(list)
    for r in epa:
        powertrain = POWERTRAIN.get(r["atvType"], r["atvType"] or "ICE")
        drive = DRIVE.get(r["drive"], r["drive"] or None)
        turbo = bool(r["tCharger"].strip() or r["sCharger"].strip())
        key = (int(r["year"]), r["displ"], r["cylinders"], powertrain, r["trany"], drive, turbo)
        groups[key].append(r)
    configs = []
    for (year, displ, cylinders, powertrain, trany, drive, turbo), members in sorted(groups.items(), key=str):
        gen = generation_for(year, gens)
        engine_part = f"{displ}l-{cylinders}cyl" if displ else "ev"
        trans_part = slug((trany or "na").replace("Automatic", "a").replace("Manual", "m"))
        config_key = (
            f"{line.make}-{line.slug}-us-{year}-{engine_part}{'-turbo' if turbo else ''}-"
            f"{powertrain.lower()}-{trans_part}-{(drive or 'na').lower()}"
        )
        missing = [n for n, v in (("engine", displ or powertrain == "BEV"), ("transmission", trany), ("drive", drive)) if not v]
        for name in missing:
            st.gaps.append({"scope": config_key, "field": name, "reason": "EPA row has no value"})
        if gen is None:
            st.errors.append({"where": config_key, "error": "NO_GENERATION_FOR_YEAR"})
        aspiration = None
        if displ:
            if any(m["tCharger"].strip() for m in members):
                aspiration = "TURBOCHARGED"
            elif any(m["sCharger"].strip() for m in members):
                aspiration = "SUPERCHARGED"
            else:
                aspiration = "NATURALLY_ASPIRATED"
        configs.append(
            {
                "configuration_key": config_key,
                "year": year,
                "generation": gen,
                "engine_family_key": None,
                "transmission_key": None,
                "powertrain": powertrain,
                "drivetrain": drive,
                "epa_trany": trany,
                "displacement_l": displ or None,
                "cylinders": int(cylinders) if cylinders else None,
                "aspiration": aspiration,
                "epa_vehicles": [
                    {
                        "epa_id": m["id"],
                        "epa_model": m["model"],
                        "city_mpg": int(m["city08"]),
                        "highway_mpg": int(m["highway08"]),
                        "combined_mpg": int(m["comb08"]),
                        "combined_l_100km": str(convert(m["comb08"], "mpg", "L/100km")) if int(m["comb08"]) else None,
                        "fuel_type": m["fuelType1"],
                        "eng_dscr": m["eng_dscr"],
                        "ev_motor": m["evMotor"],
                        "range_mi": m["range"],
                    }
                    for m in sorted(members, key=lambda m: m["id"])
                ],
                "engine_rule_cites": [],
            }
        )
        st.gaps.append({"scope": config_key, "field": "engine_family_key",
                        "reason": "factory engine code not in EPA; filled only from a source that names it"})
    return configs


# ---- vPIC Canadian dimensions ----------------------------------------------------------
DIM_KEYS = {
    "length_cm": ("length_mm", "cm", "mm"),
    "width_cm": ("width_mm", "cm", "mm"),
    "height_cm": ("height_mm", "cm", "mm"),
    "wheelbase_cm": ("wheelbase_mm", "cm", "mm"),
    "track_front_cm": ("track_front_mm", "cm", "mm"),
    "track_rear_cm": ("track_rear_mm", "cm", "mm"),
    "curb_weight_kg": ("curb_weight_kg", "kg", "kg"),
}
VPIC_CODE = {"length_cm": "OL", "width_cm": "OW", "height_cm": "OH", "wheelbase_cm": "WB",
             "track_front_cm": "TWF", "track_rear_cm": "TWR", "curb_weight_kg": "CW", "weight_distribution": "WD"}


def vpic_source(st: Staging, year: int) -> str:
    key = f"vpic-ca-{st.line.make}-{year}"
    if key in st.sources:
        return key
    row = next(
        (r for r in read_csv(WORK / "_shared" / "manifest_vpic.csv")
         if r["kind"] == "vpic_canada_specs" and r["make"] == st.line.make and r["year"] == str(year) and r["status"] == "ok"),
        None,
    )
    return st.add_source(
        key,
        kind="json_gz",
        path="rawstore:" + row["path"],
        url=row["url"],
        sha256=row["sha256"],
        retrieved_at=row["retrieved_at"],
        tier="B",
        source_type="VPIC_CANADIAN_SPECIFICATIONS",
        registry="nhtsa-vpic-vehicle-api",
        title=f"vPIC GetCanadianVehicleSpecifications {MAKES[st.line.make]['vpic']} {year} (metric)",
        publisher="NHTSA vPIC (Transport Canada data)",
        authenticity="OFFICIAL_PUBLISHER",
        model_year=year,
    )


def build_dimension_facts(st: Staging, ca: list[dict], gens: list[dict]) -> list[dict]:
    facts = []
    runs = defaultdict(list)  # (gen, model, fact key, value) -> [rows]
    for r in ca:
        gen = generation_for(r["year"], gens)
        if gen is None:
            continue
        for field, (fact_key, _, _) in DIM_KEYS.items():
            value = (r.get(field) or "").strip()
            if re.fullmatch(r"\d+(\.\d+)?", value):
                runs[(gen, r["model"], fact_key, field, value)].append(r)
        wd = (r.get("weight_distribution") or "").strip()
        if re.fullmatch(r"\d{2}/\d{2}", wd):
            runs[(gen, r["model"], "weight_distribution_front_rear_pct", "weight_distribution", wd)].append(r)
    for (gen, model, fact_key, field, value), rows in sorted(runs.items()):
        years = sorted({r["year"] for r in rows})
        # contiguous year runs only
        chunks, chunk = [], [years[0]]
        for y in years[1:]:
            if y == chunk[-1] + 1:
                chunk.append(y)
            else:
                chunks.append(chunk)
                chunk = [y]
        chunks.append(chunk)
        for chunk in chunks:
            if field in DIM_KEYS:
                _, unit_from, unit_to = DIM_KEYS[field]
                number = convert(value, unit_from, unit_to) if unit_from != unit_to else Decimal(value)
                shown = int(number) if number == number.to_integral_value() else float(number)
                unit = unit_to
            else:
                shown, unit = value, "%"
            cites = [
                {
                    "source": vpic_source(st, y),
                    "pages": None,
                    "quote": model,
                    "field": VPIC_CODE[field],
                    "raw_value": value,
                    "tier": "B",
                    "publisher": "NHTSA vPIC (Transport Canada data)",
                }
                for y in chunk
            ]
            facts.append(
                {
                    "id": f"{st.line.slug}-{gen}-vpic-{slug(model)}-{fact_key}-{chunk[0]}",
                    "generation": gen,
                    "key": fact_key,
                    "level": "GENERATION",
                    "engine": None,
                    "gen_bound": True,
                    "years": [chunk[0], chunk[-1]],
                    "value": shown,
                    "unit": unit,
                    "original": f"{VPIC_CODE[field]} = {value} ({'cm' if field.endswith('_cm') else 'kg' if field.endswith('_kg') else 'front/rear %'}, Canadian specification row '{model}')",
                    "applicability": {"vpic_ca_model": model, "market_of_data": "CA"},
                    "note": "Transport Canada dimensions via NHTSA vPIC; US version may differ (SECONDARY). Legend: " + VPIC_LEGEND,
                    "cites": cites,
                    "display_level": "SECONDARY_NOTE",
                    "confidence": "MEDIUM",
                    "primary_source": cites[0]["source"],
                }
            )
    return facts


# ---- NHTSA recalls and complaints -------------------------------------------------------
def nhtsa_source(st: Staging, item: dict, kind: str) -> str:
    row = item["row"]
    return st.add_source(
        item["source"],
        kind="json_gz",
        path="rawstore:" + row["path"],
        url=row["url"],
        sha256=row["sha256"],
        retrieved_at=row["retrieved_at"],
        tier="A",
        source_type="NHTSA_RECALLS_API" if kind == "recalls" else "NHTSA_COMPLAINTS_API",
        registry="nhtsa-safety-batch",
        title=f"NHTSA {kind} {row['model']} {row['year']}",
        publisher="NHTSA",
        authenticity="OFFICIAL_PUBLISHER",
        model_year=int(row["year"]),
    )


def build_recalls(st: Staging, sets: list[dict], gens: list[dict]) -> list[dict]:
    campaigns = {}
    for item in sets:
        source = nhtsa_source(st, item, "recalls")
        for r in item["results"]:
            number = r.get("NHTSACampaignNumber")
            if not number:
                continue
            entry = campaigns.setdefault(
                number,
                {
                    "campaign_number": number,
                    "component": r.get("Component"),
                    "summary": r.get("Summary"),
                    "consequence": r.get("Consequence"),
                    "remedy": r.get("Remedy"),
                    "report_received_date": r.get("ReportReceivedDate"),
                    "manufacturer": r.get("Manufacturer"),
                    "nhtsa_models": set(),
                    "model_years": set(),
                    "sources": set(),
                },
            )
            entry["model_years"].add(int(r.get("ModelYear") or item["year"]))
            entry["nhtsa_models"].add(item["model"])
            entry["sources"].add(source)
    recalls = []
    for entry in campaigns.values():
        by_gen = defaultdict(list)
        for year in sorted(entry["model_years"]):
            by_gen[generation_for(year, gens)].append(year)
        for gen, years in by_gen.items():
            if gen is None:
                continue
            recalls.append(
                {
                    **{k: v for k, v in entry.items() if k not in ("nhtsa_models", "model_years", "sources")},
                    "generation": gen,
                    "model_years": years,
                    "years": [min(years), max(years)],
                    "nhtsa_models": sorted(entry["nhtsa_models"]),
                    "source": sorted(entry["sources"])[0],
                    "sources": sorted(entry["sources"]),
                }
            )
    return sorted(recalls, key=lambda r: (r["years"][0], r["campaign_number"]))


def build_complaints(st: Staging, sets: list[dict], gens: list[dict]):
    seen = set()
    components = defaultdict(lambda: {"count": 0, "odi": [], "years": Counter()})
    symptoms = defaultdict(lambda: {"by_year": Counter(), "odi": [], "sources": set()})
    for item in sets:
        source = nhtsa_source(st, item, "complaints")
        gen = generation_for(item["year"], gens)
        if gen is None:
            continue
        for r in item["results"]:
            odi = r.get("odiNumber")
            if odi in seen:
                continue
            seen.add(odi)
            for component in {c.strip() for c in (r.get("components") or "").split(",") if c.strip()}:
                bucket = components[(gen, component)]
                bucket["count"] += 1
                bucket["years"][item["year"]] += 1
                if len(bucket["odi"]) < 25:
                    bucket["odi"].append(odi)
            text = (r.get("summary") or "").upper()
            for key, (_, pattern, _, _) in SYMPTOMS.items():
                if re.search(pattern, text):
                    bucket = symptoms[f"{gen}|{key}"]
                    bucket["by_year"][item["year"]] += 1
                    bucket["sources"].add(source)
                    if len(bucket["odi"]) < 25:
                        bucket["odi"].append(odi)
    patterns = [
        {
            "generation": gen,
            "component": component,
            "count": b["count"],
            "by_year": dict(sorted(b["years"].items())),
            "sample_odi": b["odi"],
            "above_threshold": b["count"] >= COMPLAINT_PATTERN_THRESHOLD,
        }
        for (gen, component), b in sorted(components.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    ]
    symptom_patterns = {
        key: {
            "key": key,
            "label": SYMPTOMS[key.split("|", 1)[1]][0],
            "count": sum(b["by_year"].values()),
            "by_year": {str(y): n for y, n in sorted(b["by_year"].items())},
            "sample_odi": b["odi"],
            "above_threshold": sum(b["by_year"].values()) >= COMPLAINT_PATTERN_THRESHOLD,
            "engine_specific": False,
            "source": sorted(b["sources"])[0],
        }
        for key, b in symptoms.items()
    }
    return patterns, symptom_patterns


# ---- manufacturer communications and known issues ------------------------------------------
def symptom_keys(text: str) -> list[str]:
    text = (text or "").upper()
    return [k for k, (_, pattern, _, _) in SYMPTOMS.items() if re.search(pattern, text)]


def complaints_in(symptom_patterns, gen, key, years):
    pattern = symptom_patterns.get(f"{gen}|{key}")
    if not pattern:
        return 0
    return sum(n for y, n in pattern["by_year"].items() if years[0] <= int(y) <= years[1])


def probability(pattern_hit: bool, tsb: bool) -> str:
    return "COMMON" if pattern_hit and tsb else "OCCASIONAL" if pattern_hit or tsb else "RARE"


def build_issues(st: Staging, recalls, symptom_patterns, tsb_rows, gens):
    issues, used_tsbs = [], {}
    tsbs_by_gen_symptom = defaultdict(list)
    for t in tsb_rows:
        for gen in gens:
            years = [y for y in t["years"] if gen["start_year"] <= y <= gen["end_year"]]
            if not years:
                continue
            if not tsb_relevant(t):
                continue
            for key in symptom_keys(tsb_text(t["summary"])):
                tsbs_by_gen_symptom[(gen["code"], key)].append({**t, "gen_years": years})
    covered = set()
    for r in recalls:
        gen, years = r["generation"], r["years"]
        text = f"{r['component']} {r['summary']}"
        hint = []
        for prefix, keys in COMPONENT_HINTS.items():
            if (r["component"] or "").upper().startswith(prefix):
                hint += keys
        keys = [k for k in symptom_keys(text) if not hint or k in hint] or [k for k in hint if k in symptom_keys(r["summary"] or "")]
        pattern_keys = [f"{gen}|{k}" for k in keys if f"{gen}|{k}" in symptom_patterns]
        counts = [complaints_in(symptom_patterns, gen, k, years) for k in keys]
        tsbs = sorted({t["id"] for k in keys for t in tsbs_by_gen_symptom.get((gen, k), [])
                       if any(years[0] <= y <= years[1] for y in t["gen_years"])})
        for k in keys:
            for t in tsbs_by_gen_symptom.get((gen, k), []):
                if t["id"] in tsbs:
                    used_tsbs[t["id"]] = t
            covered.add((gen, k))
        consequence = (r["consequence"] or "").upper()
        label_only = re.search(r"LABEL|OWNER'?S MANUAL|CERTIFICATION", (r["summary"] or "").upper()) and not SAFETY_WORDS.search(consequence)
        severity = "LOW" if label_only else "HIGH" if SAFETY_WORDS.search(consequence) else "MEDIUM"
        pattern_hit = any(n >= COMPLAINT_PATTERN_THRESHOLD for n in counts)
        issues.append(
            {
                "id": f"{st.line.slug}-{gen}-recall-{r['campaign_number']}",
                "generation": gen,
                "years": years,
                "scope_level": "GENERATION",
                "component": r["component"] or "UNKNOWN",
                "title": f"NHTSA recall {r['campaign_number']}: {r['component']}",
                "symptoms": [SYMPTOMS[k][0] for k in keys],
                "cause": r["summary"] or "",
                "consequences": r["consequence"] or "",
                "inspection": f"Check that NHTSA recall {r['campaign_number']} was completed for this VIN (nhtsa.gov/recalls or a dealer).",
                "typical_fix": r["remedy"] or "",
                "severity": severity,
                "probability": probability(pattern_hit, bool(tsbs)),
                "complaints_in_years": counts,
                "evidence": {"recalls": [r["campaign_number"]], "tsbs": tsbs, "complaint_patterns": pattern_keys},
                "rule": "recall" + (" + TSB" if tsbs else "") + (" + complaint pattern" if pattern_hit else ""),
            }
        )
    for (gen, key), rows in sorted(tsbs_by_gen_symptom.items()):
        if (gen, key) in covered:
            continue
        years = [min(y for t in rows for y in t["gen_years"]), max(y for t in rows for y in t["gen_years"])]
        count = complaints_in(symptom_patterns, gen, key, years)
        label, _, component, severity = SYMPTOMS[key]
        for t in rows:
            used_tsbs[t["id"]] = t
        summaries = []
        for t in rows:
            text = tsb_text(t["summary"]).strip()
            if text and text not in summaries:
                summaries.append(text)
        issues.append(
            {
                "id": f"{st.line.slug}-{gen}-tsb-{key}",
                "generation": gen,
                "years": years,
                "scope_level": "GENERATION",
                "component": component,
                "title": f"Manufacturer communication: {label}",
                "symptoms": [label],
                "cause": " | ".join(summaries[:3])[:2000],
                "consequences": "",
                "inspection": f"Ask a dealer whether manufacturer communications {', '.join(sorted({t['id'] for t in rows})[:5])} apply to this VIN and were performed.",
                "typical_fix": "per manufacturer communication " + ", ".join(sorted({t["id"] for t in rows})[:5]),
                "severity": severity,
                "probability": probability(count >= COMPLAINT_PATTERN_THRESHOLD, True),
                "complaints_in_years": [count],
                "evidence": {"recalls": [], "tsbs": sorted({t["id"] for t in rows}),
                             "complaint_patterns": [f"{gen}|{key}"] if f"{gen}|{key}" in symptom_patterns else []},
                "rule": "TSB" + (" + complaint pattern" if count >= COMPLAINT_PATTERN_THRESHOLD else ""),
            }
        )
        covered.add((gen, key))
    for key, p in sorted(symptom_patterns.items()):
        gen, symptom = key.split("|", 1)
        if (gen, symptom) in covered or not p["above_threshold"]:
            continue
        label, _, component, severity = SYMPTOMS[symptom]
        years = [int(min(p["by_year"])), int(max(p["by_year"]))]
        issues.append(
            {
                "id": f"{st.line.slug}-{gen}-complaints-{symptom}",
                "generation": gen,
                "years": years,
                "scope_level": "GENERATION",
                "component": component,
                "title": f"Owners report: {label}",
                "symptoms": [label],
                "cause": f"{p['count']} NHTSA owner complaints mention this symptom (keyword pattern); no recall or manufacturer communication found.",
                "consequences": "",
                "inspection": "Ask for service records and test for the reported symptom during inspection.",
                "typical_fix": "",
                "severity": severity,
                "probability": "OCCASIONAL",
                "complaints_in_years": [p["count"]],
                "evidence": {"recalls": [], "tsbs": [], "complaint_patterns": [key]},
                "rule": "complaint pattern only (owner reports)",
            }
        )
    return issues, list(used_tsbs.values())


# ---- vPIC (Canadian, SECONDARY) against official values (prompt section 5.2) --------------------
VPIC_TOLERANCE = {"length_mm": 10, "width_mm": 10, "height_mm": 10, "wheelbase_mm": 10,
                  "track_front_mm": 10, "track_rear_mm": 10, "curb_weight_kg": 0.03}


def cross_check_vpic(st: Staging, facts: list[dict]) -> None:
    """A vPIC dimension that falls inside the range of the official (tier A) values for the same
    generation and model year (plus rounding tolerance) is recorded as corroborated; one outside
    it is a conflict: the official value is the main one, the Canadian value stays a note."""
    official = defaultdict(list)
    for f in facts:
        if f["key"] in VPIC_TOLERANCE and f["display_level"] == "FACT" and not str(f["primary_source"]).startswith("vpic-"):
            for year in range(f["years"][0], f["years"][1] + 1):
                official[(f["key"], f["generation"], year)].append(f)
    for f in facts:
        if f["key"] not in VPIC_TOLERANCE or not str(f["primary_source"]).startswith("vpic-"):
            continue
        for year in range(f["years"][0], f["years"][1] + 1):
            others = official.get((f["key"], f["generation"], year))
            if not others:
                continue
            values = [float(o["value"]) for o in others]
            tol = VPIC_TOLERANCE[f["key"]]
            tol = tol * max(values) if tol < 1 else tol
            if min(values) - tol <= float(f["value"]) <= max(values) + tol:
                f.setdefault("corroborated_by", [])
                f["corroborated_by"] = sorted(set(f["corroborated_by"]) | {o["id"] for o in others})
            else:
                st.conflicts.append({
                    "scope": f"{st.line.key} {f['generation']} MY{year}", "key": f["key"],
                    "applicability": f.get("applicability"), "kept_value": sorted(set(values)),
                    "kept_from": sorted({o["primary_source"] for o in others}),
                    "other_values": [f["value"]], "other_sources": [f["primary_source"]],
                    "resolution": "official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2)",
                })


# ---- CarComplaints (owner reports, prompt sections 5 and 7) -----------------------------------
CC_RECURRING_YEARS = 2  # a CarComplaints-only problem must be in the "worst" list of 2+ model years
STEP_UP = {"RARE": "OCCASIONAL", "OCCASIONAL": "COMMON", "COMMON": "COMMON"}
CC_COMPONENT = {
    "engine": "ENGINE", "transmission": "TRANSMISSION", "brakes": "BRAKES", "steering": "STEERING",
    "suspension": "SUSPENSION", "electrical": "ELECTRICAL", "fuel_system": "FUEL SYSTEM",
    "cooling_system": "COOLING", "ac_heater": "HVAC", "body_paint": "BODY", "windows_windshield": "BODY",
    "interior_accessories": "BODY", "exterior_accessories": "BODY", "lights": "ELECTRICAL",
    "seat_belts_air_bags": "AIR BAGS", "wheels_hubs": "SUSPENSION", "exhaust_system": "EXHAUST",
    "drivetrain": "POWERTRAIN", "accessories_interior": "BODY", "accessories_exterior": "BODY",
}
_CC: dict[str, dict] = {}


def carcomplaints_for_line(line: Line) -> dict:
    """Parsed CarComplaints model-year pages of the line (scripts/collect_carcomplaints.py)."""
    if line.make not in _CC:
        path = WORK / "_shared" / "carcomplaints" / f"{line.make}.json"
        _CC[line.make] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return _CC[line.make].get(line.key) or {}


def build_cc_problems(st: Staging, gens: list[dict]) -> dict:
    """Problems from the "Worst <year> <model> Problems" lists, grouped per generation and
    problem page (the site's own problem slug), with the site's average repair cost and
    mileage per model year."""
    data = carcomplaints_for_line(st.line)
    if data.get("status") != "ok":
        if data:
            st.notes.append(f"CarComplaints: {data.get('status')}")
        return {}
    problems = {}
    for site_model, by_year in data["models"].items():
        for year_text, page in by_year.items():
            year = int(year_text)
            gen = generation_for(year, gens)
            if gen is None:
                continue
            for item in page["worst"]:
                slug = (item.get("problem_url") or "").rstrip("/").rsplit("/", 1)[-1].removesuffix(".shtml")
                slug = slug or re.sub(r"[^a-z0-9]+", "_", item["problem"].lower()).strip("_")
                key = f"{gen}|{slug}"
                entry = problems.setdefault(key, {
                    "key": key, "generation": gen, "problem": item["problem"], "category": item.get("category", "").replace("-", "_"),
                    "symptoms": symptom_keys(item["problem"]), "by_year": {}, "site_model": site_model,
                })
                entry["by_year"][str(year)] = {
                    "rank": item["rank"], "avg_cost": item["avg_cost"], "avg_mileage": item["avg_mileage"],
                    "quote": item["quote"], "url": page["url"], "problem_url": item.get("problem_url"),
                }
    for entry in problems.values():
        years = sorted(int(y) for y in entry["by_year"])
        entry["years"] = [years[0], years[-1]]
        entry["recurring"] = len(years) >= CC_RECURRING_YEARS
    return problems


_CC_MANIFEST: dict[str, dict] = {}


def cc_source(st: Staging, url: str) -> str | None:
    if not _CC_MANIFEST:
        _CC_MANIFEST.update({r["url"]: r for r in read_csv(WORK / "_shared" / "manifest_carcomplaints.csv") if r["status"] == "ok"})
    row = _CC_MANIFEST.get(url)
    if row is None:
        return None
    return st.add_source(
        f"carcomplaints-{row['line'].split('/')[-1]}-{row['year']}-{hashlib.sha1(url.encode()).hexdigest()[:6]}",
        kind="html_gz",
        path="rawstore:" + row["path"],
        url=url,
        sha256=row["sha256"],
        retrieved_at=row["retrieved_at"],
        tier="C",
        source_type="OWNER_COMPLAINTS_SITE",
        registry="carcomplaints",
        title=f"CarComplaints.com {row['line']} {row['year']} problems page",
        publisher="CarComplaints.com (owner reports)",
        authenticity="OWNER_REPORTS",
        model_year=int(row["year"]),
    )


def cc_summary(entry: dict) -> str:
    parts = [f"MY{y}: #{v['rank']}, average cost to fix {v['avg_cost']}, average mileage {v['avg_mileage']}"
             for y, v in sorted(entry["by_year"].items())]
    return f"CarComplaints.com \"{entry['problem']}\" (owner reports): " + "; ".join(parts)


def apply_carcomplaints(st: Staging, issues: list[dict], problems: dict) -> list[dict]:
    """Section 7: a CarComplaints problem on the same component/symptom and years as an issue
    raises its probability one step and adds the site's cost and mileage (marked as owner
    reports); a recurring problem found only there becomes an owner-report issue, severity at
    most MEDIUM. A one-year CarComplaints-only entry is not written."""
    used = set()
    for issue in issues:
        symptom_keys_of_issue = {k for k, (label, _, _, _) in SYMPTOMS.items() if label in issue["symptoms"]}
        matched = [
            e for e in problems.values()
            if e["generation"] == issue["generation"] and set(e["symptoms"]) & symptom_keys_of_issue
            and e["years"][0] <= issue["years"][1] and issue["years"][0] <= e["years"][1]
        ]
        if not matched:
            continue
        issue["probability_before_carcomplaints"] = issue["probability"]
        issue["probability"] = STEP_UP[issue["probability"]]
        issue["evidence"]["carcomplaints"] = sorted(e["key"] for e in matched)
        issue["rule"] += " + CarComplaints (probability +1)"
        issue["note"] = " | ".join(cc_summary(e) for e in matched)
        used.update(e["key"] for e in matched)
    for key, entry in sorted(problems.items()):
        if key in used or not entry["recurring"]:
            continue
        label = SYMPTOMS[entry["symptoms"][0]][0] if entry["symptoms"] else entry["problem"]
        severity = SYMPTOMS[entry["symptoms"][0]][3] if entry["symptoms"] else "MEDIUM"
        component = SYMPTOMS[entry["symptoms"][0]][2] if entry["symptoms"] else CC_COMPONENT.get(entry["category"], entry["category"].upper() or "UNKNOWN")
        issues.append({
            "id": f"{st.line.slug}-{entry['generation']}-cc-{key.split('|', 1)[1][:60]}",
            "generation": entry["generation"],
            "years": entry["years"],
            "scope_level": "GENERATION",
            "component": component,
            "title": f"Owners report (CarComplaints.com): {entry['problem']}",
            "symptoms": [label],
            "cause": cc_summary(entry),
            "consequences": "",
            "inspection": "Ask for service records and test for the reported problem during inspection.",
            "typical_fix": "",
            "severity": "MEDIUM" if severity == "HIGH" else severity,
            "probability": "OCCASIONAL",
            "complaints_in_years": [],
            "evidence": {"recalls": [], "tsbs": [], "complaint_patterns": [], "carcomplaints": [key]},
            "rule": "CarComplaints only, recurring (owner reports; SECONDARY)",
            "note": "по отзывам владельцев (CarComplaints.com)",
        })
        used.add(key)
    for key in sorted(used):
        entry = problems[key]
        entry["sources"] = sorted({s for v in entry["by_year"].values() if (s := cc_source(st, v["url"]))})
    return [problems[k] for k in sorted(used)]


# ---- build ------------------------------------------------------------------------------------
def build_line(db, line: Line) -> dict:
    st = Staging(line)
    epa = epa_for_line(line)
    ca = vpic_ca_for_line(line)
    dbgens = db_generations(db, line)
    if not epa:
        st.gaps.append({"scope": line.key, "field": "all", "reason": "no EPA rows: model not sold in the US in 2014-2026 under this name"})
    epa_source(st)
    gens = detect_generations(st, epa, ca, dbgens)
    configurations = build_configurations(st, epa, gens) if gens else []
    facts = build_dimension_facts(st, ca, gens) if gens else []
    recall_sets = nhtsa_for_line(line, "recalls")
    complaint_sets = nhtsa_for_line(line, "complaints")
    recalls = build_recalls(st, recall_sets, gens) if gens else []
    patterns, symptom_patterns = build_complaints(st, complaint_sets, gens) if gens else ([], {})
    tsb_rows = mfrcomms_for_line(line)
    if tsb_rows:
        st.add_source(
            "nhtsa-mfrcomms",
            kind="mfrcomms",
            paths=sorted({t["file"] for t in tsb_rows}),
            url="https://static.nhtsa.gov/odi/ffdd/tsbs/",
            sha256="",
            retrieved_at="2026-10-02",
            tier="A",
            source_type="US_FEDERAL_DATASET",
            registry="nhtsa-safety-batch",
            title="NHTSA Manufacturer Communications flat files",
            publisher="NHTSA",
            authenticity="OFFICIAL_PUBLISHER",
        )
    issues, tsbs = build_issues(st, recalls, symptom_patterns, tsb_rows, gens) if gens else ([], [])
    cc_problems = apply_carcomplaints(st, issues, build_cc_problems(st, gens)) if gens else []
    manual = WORK / line.make / "staging" / line.slug / "manual_facts.json"
    if manual.exists():
        extra = json.loads(manual.read_text(encoding="utf-8"))
        facts += extra.get("facts", [])
        for key, item in extra.get("sources", {}).items():
            st.sources.setdefault(key, item)
        st.gaps += extra.get("gaps", [])
        st.conflicts += extra.get("conflicts", [])
    cross_check_vpic(st, facts)
    maintenance = []
    path = WORK / line.make / "staging" / line.slug / "maintenance.json"
    if path.exists():
        extra = json.loads(path.read_text(encoding="utf-8"))
        maintenance = [i for i in extra.get("items", []) if i["generation"] in {g["code"] for g in gens}]
        for key, item in extra.get("sources", {}).items():
            st.sources.setdefault(key, item)
        st.gaps += extra.get("gaps", [])
    validate(st, gens, facts, issues)
    return {
        "make": MAKES[line.make]["epa"],
        "line": line.name,
        "line_key": line.key,
        "db_models": list(line.db_models),
        "market": MARKET,
        "build": "us-batch-1",
        "sources": st.sources,
        "generations": gens,
        "configurations": configurations,
        "facts": facts,
        "recalls": recalls,
        "complaint_patterns": patterns,
        "symptom_patterns": symptom_patterns,
        "issues": issues,
        "cc_problems": cc_problems,
        "tsbs": tsbs,
        "maintenance": maintenance,
        "conflicts": st.conflicts,
        "gaps": st.gaps,
        "notes": st.notes,
        "errors": st.errors,
        "counts": {
            "generations": len(gens),
            "configurations": len(configurations),
            "facts": len(facts),
            "recalls": len(recalls),
            "symptom_patterns": len(symptom_patterns),
            "issues": len(issues),
            "issues_by_probability": dict(Counter(i["probability"] for i in issues)),
            "cc_problems": len(cc_problems),
            "tsbs": len(tsbs),
            "maintenance": len(maintenance),
            "errors": len(st.errors),
            "display_levels": dict(Counter(f["display_level"] for f in facts)),
        },
    }


RANGES = {
    "length_mm": (2500, 6500), "width_mm": (1400, 2300), "height_mm": (1000, 2300),
    "wheelbase_mm": (2000, 3800), "track_front_mm": (1200, 1900), "track_rear_mm": (1200, 1900),
    "curb_weight_kg": (700, 4500), "engine_oil_capacity_l": (3, 12), "coolant_capacity_l": (3, 25),
    "transmission_fluid_capacity_l": (0.5, 16), "fuel_tank_l": (20, 160),
}


def validate(st: Staging, gens, facts, issues):
    codes = {g["code"] for g in gens}
    for g in gens:
        if not (2014 <= g["start_year"] <= g["end_year"] <= 2026):
            st.errors.append({"where": g["code"], "error": "GENERATION_YEARS_OUTSIDE_SCOPE"})
    for f in facts:
        where = f["id"]
        if not f.get("cites"):
            st.errors.append({"where": where, "error": "NO_EVIDENCE"})
        if f["generation"] not in codes and f["level"] != "ENGINE":
            st.errors.append({"where": where, "error": "UNKNOWN_GENERATION"})
        gen = next((g for g in gens if g["code"] == f["generation"]), None)
        if gen and not (gen["start_year"] <= f["years"][0] <= f["years"][1] <= gen["end_year"]):
            st.errors.append({"where": where, "error": f"YEARS_OUTSIDE_GENERATION {f['years']}"})
        if f["key"] in RANGES and isinstance(f["value"], (int, float)):
            low, high = RANGES[f["key"]]
            if not low <= f["value"] <= high:
                st.errors.append({"where": where, "error": f"OUT_OF_RANGE {f['value']} not in {low}-{high}"})
    scopes = Counter(
        json.dumps([f["generation"], f["level"], f.get("engine"), f["key"], f["years"], f.get("applicability") or {},
                    f["display_level"] == "HIDDEN_CONFLICT",
                    f["value"] if f["display_level"] == "HIDDEN_CONFLICT" else None], sort_keys=True)
        for f in facts
    )
    for scope, count in scopes.items():
        if count > 1:
            st.errors.append({"where": scope, "error": f"DUPLICATE_FACT_SCOPE x{count}"})
    for issue in issues:
        if issue["generation"] not in codes:
            st.errors.append({"where": issue["id"], "error": "UNKNOWN_GENERATION"})
        if issue["probability"] == "RARE" and not issue["evidence"]["recalls"]:
            st.errors.append({"where": issue["id"], "error": "RARE_REQUIRES_RECALL"})


def write_csv(path: Path, rows: list[dict]):
    keys = sorted({k for r in rows for k in r}) or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("make")
    parser.add_argument("--line")
    parser.add_argument("--db", default=str(ROOT / "autoexpert.db"))
    args = parser.parse_args(argv)
    db = sqlite3.connect(f"file:{Path(args.db).as_posix()}?mode=ro", uri=True)
    summary, failed = {}, 0
    for line in lines_for(args.make):
        if args.line and line.slug != args.line:
            continue
        staging = build_line(db, line)
        out = WORK / line.make / "staging" / line.slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "staging.json").write_text(json.dumps(staging, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
        write_csv(out / "gaps.csv", staging["gaps"])
        write_csv(out / "conflicts.csv", staging["conflicts"])
        summary[line.key] = {
            **staging["counts"],
            "generation_blocks": [
                f"{g['code']} {g['start_year']}-{'' if g['open_ended'] else g['end_year']}" for g in staging["generations"]
            ],
        }
        failed += bool(staging["errors"])
        print(line.key, json.dumps(summary[line.key], ensure_ascii=False), flush=True)
        for error in staging["errors"][:10]:
            print("  ERROR", json.dumps(error, ensure_ascii=False))
    path = WORK / args.make / "staging" / "batch_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
