"""Accuracy of a Teoalida dataset against the values already written from official sources
(next-stage prompt A.8): per source and field — compared / agreed (within rounding and unit
tolerance) / differ, with examples. A field whose agreement is below 90% is not written from
that source; a field with fewer than MIN_COMPARED comparisons has no measured accuracy and is not
written either (reported as "not measurable on this file").

Official values: the facts of the line's staging shown as FACT (manufacturer documents: owner's
manuals, press specifications) and the EPA data of the configurations (cylinders, displacement,
drive, EPA mpg). Teoalida values are compared only with official values whose applicability fits
the same model year and model designation (variant), engine and powertrain.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from us_tech_common import WORK  # noqa: E402

THRESHOLD = 0.90
MIN_COMPARED = 5
BODY_WORDS = {"sedan", "sports", "wagon", "touring", "coupe", "convertible", "gran", "turismo", "gt", "cabrio",
              "cabriolet", "hatchback", "suv", "4-door", "2-door"}
# key -> (absolute tolerance, relative tolerance): rounding of inch/lb/gal/cu-ft conversions
TOLERANCE = {
    "length_mm": (6, 0), "width_mm": (6, 0), "height_mm": (6, 0), "wheelbase_mm": (6, 0),
    "track_front_mm": (6, 0), "track_rear_mm": (6, 0), "ground_clearance": (6, 0),
    "turning_circle_m": (0.15, 0), "curb_weight_kg": (5, 0.01), "cargo_l": (6, 0.02), "cargo_max_l": (6, 0.02),
    "fuel_tank_l": (0.6, 0), "power_hp": (1, 0), "torque_lb_ft": (1, 0), "power_rpm": (0, 0), "torque_rpm": (0, 0),
    "engine_displacement_l": (0.05, 0), "engine_displacement_cc": (6, 0), "cylinders": (0, 0),
    "engine_oil_capacity_l": (0.1, 0), "coolant_capacity_l": (0.1, 0), "transmission_fluid_capacity_l": (0.1, 0),
    "epa_combined_mpg": (0, 0), "epa_city_mpg": (0, 0), "epa_highway_mpg": (0, 0),
    "towing_kg": (5, 0.01), "passenger_volume_l": (30, 0.01), "seats": (0, 0),
}


def tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[\s/,()]+", (text or "").lower()) if t}


def designation_fits(designation: str | None, variant: str | None) -> bool:
    """Same model designation, ignoring body words ("330i xDrive" fits "330i xDrive Sports Wagon")."""
    if not designation or not variant:
        return True
    a, b = tokens(designation) - BODY_WORDS, tokens(variant) - BODY_WORDS
    return bool(a) and bool(b) and (a <= b or b <= a)


MODEL_TOKEN = re.compile(r"^(?:m?\d{3}[a-z]{0,2}|m\d{1,3}[a-z]?|x\d|z\d|i\d|[a-z]{1,3}\d{2,3}[a-z]?)$")


def edition_fits(designation: str | None, edition: str | None) -> bool:
    """A press edition that names model designations ("330e sedan", "m340i and m340i xdrive
    sedans") fits only those; an edition naming none ("3 series sedan") fits every designation."""
    if not designation or not edition:
        return True
    named = {t for t in tokens(edition) if MODEL_TOKEN.match(t)}
    return not named or bool(named & tokens(designation))


def model_label(app: dict) -> str | None:
    """The model designation an applicability names: its variant, or a press engine label that
    is a designation ("330i", "M340i xDrive") rather than an engine ("2.5L")."""
    if app.get("variant"):
        return app["variant"]
    label = app.get("engine")
    if label and any(MODEL_TOKEN.match(t) for t in tokens(label)) and not re.search(r"\d\.\d", label):
        return label
    return None


def number(value):
    if isinstance(value, (int, float)):
        return float(value)
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*$", str(value))
    return float(m.group(1)) if m else None


def agree(key: str, a, b) -> bool:
    x, y = number(a), number(b)
    if x is not None and y is not None:
        abs_tol, rel_tol = TOLERANCE.get(key, (0, 0.01))
        return abs(x - y) <= max(abs_tol, rel_tol * max(abs(x), abs(y))) + 1e-9
    return " ".join(str(a).lower().split()) == " ".join(str(b).lower().split())


def load_line(make: str, line: str) -> dict | None:
    path = WORK / make / "staging" / line / "staging.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def official_values(staging: dict, key: str, year: int, designation: str | None, config: dict | None) -> list:
    """Official values for one field, model year and designation (with their source)."""
    out = []
    for f in staging["facts"]:
        if f["key"] != key or f["display_level"] != "FACT" or not (f["years"][0] <= year <= f["years"][1]):
            continue
        app = f.get("applicability") or {}
        if not designation_fits(designation, model_label(app)) or not edition_fits(designation, app.get("edition")):
            continue
        if config and app.get("powertrain") and config.get("powertrain") and app["powertrain"] != config["powertrain"]:
            continue
        if config and app.get("displacement_l") and config.get("displacement_l") and str(app["displacement_l"]) != str(config["displacement_l"]):
            continue
        out.append((f["value"], f["primary_source"], app.get("variant") or app.get("edition") or ""))
    if config:
        epa = {"cylinders": config.get("cylinders"), "engine_displacement_l": config.get("displacement_l"),
               "drivetrain": config.get("drivetrain")}
        if key in epa and epa[key] not in (None, ""):
            out.append((epa[key], "epa", config["configuration_key"]))
        for v in config.get("epa_vehicles", []):
            if key in ("epa_city_mpg", "epa_highway_mpg", "epa_combined_mpg") and designation_fits(designation, v.get("epa_model")):
                out.append((v.get(key.replace("epa_", "")), "epa", v.get("epa_model")))
    return out


class Tally:
    def __init__(self, source: str):
        self.source = source
        self.rows = defaultdict(lambda: {"compared": 0, "agreed": 0, "differ": 0, "no_official": 0,
                                         "examples_agree": [], "examples_differ": []})

    def add(self, key: str, value, officials: list, where: str) -> str:
        r = self.rows[key]
        if not officials:
            r["no_official"] += 1
            return "no_official"
        r["compared"] += 1
        hit = next((o for o in officials if agree(key, value, o[0])), None)
        if hit:
            r["agreed"] += 1
            if len(r["examples_agree"]) < 3:
                r["examples_agree"].append({"where": where, "teoalida": value, "official": hit[0], "source": hit[1]})
            return "agreed"
        r["differ"] += 1
        if len(r["examples_differ"]) < 8:
            r["examples_differ"].append({"where": where, "teoalida": value,
                                         "official": sorted({json.dumps(o[0]) for o in officials})[:4],
                                         "sources": sorted({o[1] for o in officials})[:3]})
        return "differ"

    def verdicts(self) -> dict:
        out = {}
        for key, r in sorted(self.rows.items()):
            rate = r["agreed"] / r["compared"] if r["compared"] else None
            if r["compared"] < MIN_COMPARED:
                verdict = "not measurable (too few comparisons) - not written"
            elif rate < THRESHOLD:
                verdict = "below 90% - not written"
            else:
                verdict = "written (SECONDARY_NOTE)"
            out[key] = {**{k: v for k, v in r.items()}, "agreement": round(rate, 3) if rate is not None else None,
                        "verdict": verdict, "write": verdict.startswith("written")}
        return out


def write_report(name: str, tally: Tally, extra: dict | None = None) -> dict:
    out = {"source": tally.source, "threshold": THRESHOLD, "min_compared": MIN_COMPARED,
           "fields": tally.verdicts(), **(extra or {})}
    path = WORK / "_shared" / "teoalida" / f"accuracy_{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
