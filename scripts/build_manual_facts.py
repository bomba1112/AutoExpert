"""Turn the per-document manual extractions into scoped facts per line (manual_facts.json).

Input: data_work/<make>/extracted/*.json (scripts/extract_manual_facts.py) and the line's
base staging (generations). Output: data_work/<make>/staging/<line>/manual_facts.json with
sources, facts, conflicts and gaps in the format build_us_batch_staging.py merges.

Rules
- A document applies to the line(s) and model year(s) it was downloaded for; only US
  editions are used.
- Engine: a factory code on the row ("(LGX)", "2ZR-FE") or the code the document's
  specification chapter states for its only engine makes the fact ENGINE level; otherwise
  the fact stays at generation level with the engine text from the row as applicability.
  An unlabeled engine-dependent value is used only when EPA lists one engine displacement
  for that line-year (or the document names its engine code); else it goes to the gaps.
- One document giving two values for the same scope (two engines on separate pages without
  labels, a with/without-package footnote) is ambiguous: nothing is written for it.
- Different documents disagreeing: an official (tier A) value wins over a copy (tier B);
  the other value is kept as HIDDEN_CONFLICT evidence. Equal tiers that disagree: both are
  hidden and the conflict is logged (prompt section 6).
- Consecutive model years with the same value inside one generation form one fact.

  .venv/Scripts/python.exe scripts/build_manual_facts.py <make>
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY, MAKES, lines_for  # noqa: E402

ENGINE_KEYS = {
    "engine_oil_capacity_l", "engine_oil_capacity_without_filter_l", "engine_oil_capacity_drain_refill_l",
    "engine_oil_viscosity", "engine_oil_specification", "engine_oil_oem_approval",
}
# Press specification pages (data_work/_shared/press/FORMAT.md): engine figures are stored
# per engine family when the page names a factory code, else with the engine as applicability.
PRESS_ENGINE_KEYS = {
    "power_hp", "power_rpm", "torque_lb_ft", "torque_rpm", "engine_description", "engine_displacement_cc",
    "bore_stroke_mm", "bore_stroke_in", "compression_ratio", "valvetrain", "injection",
}
ENGINE_KEYS = ENGINE_KEYS | PRESS_ENGINE_KEYS
ENGINE_DEPENDENT = ENGINE_KEYS | {"coolant_capacity_l", "transmission_fluid_capacity_l"}
# source unit key -> (stored key, from unit, to unit) via backend tech_units
PRESS_CONVERT = {
    "length_in": ("length_mm", "in", "mm"), "width_in": ("width_mm", "in", "mm"), "height_in": ("height_mm", "in", "mm"),
    "wheelbase_in": ("wheelbase_mm", "in", "mm"), "track_front_in": ("track_front_mm", "in", "mm"),
    "track_rear_in": ("track_rear_mm", "in", "mm"), "ground_clearance_in": ("ground_clearance", "in", "mm"),
    "curb_weight_lb": ("curb_weight_kg", "lb", "kg"), "cargo_cu_ft": ("cargo_l", "cu_ft", "L"),
    "cargo_max_cu_ft": ("cargo_max_l", "cu_ft", "L"), "passenger_volume_cu_ft": ("passenger_volume_l", "cu_ft", "L"),
    "fuel_tank_gal": ("fuel_tank_l", "gal", "L"), "turning_circle_ft": ("turning_circle_m", "ft", "m"),
    "towing_lb": ("towing_kg", "lb", "kg"),
}
UNITS = {"mm": "mm", "kg": "kg", "_l": "L", "_m": "m"}
KEY_UNIT = {"ground_clearance": "mm", "power_hp": "hp", "system_power_hp": "hp", "torque_lb_ft": "lb-ft",
            "wheel_size_in": "in", "engine_displacement_cc": "cm3"}
# values given per trim/variant on a press page (several on one page are not a conflict)
VARIANT_KEYS = {
    "curb_weight_kg", "cargo_l", "cargo_max_l", "passenger_volume_l", "ground_clearance", "height_mm", "length_mm",
    "width_mm", "track_front_mm", "track_rear_mm", "towing_kg", "turning_circle_m", "wheel_size_in", "fuel_tank_l",
    "front_brakes", "rear_brakes", "front_suspension", "rear_suspension", "steering", "transmission_description",
    "seats", "electric_motor", "system_power_hp",
}


def unit_of(key: str) -> str | None:
    if key in KEY_UNIT:
        return KEY_UNIT[key]
    for suffix, unit in UNITS.items():
        if key.endswith(suffix if suffix.startswith("_") else "_" + suffix):
            return unit
    return None


def press_value(fact: dict) -> tuple[str, object]:
    """Stored key and value of a press fact (US units converted with the fixed factors)."""
    from app.services.tech_units import convert

    key = fact["key"]
    if key in PRESS_CONVERT:
        target, source_unit, target_unit = PRESS_CONVERT[key]
        value = convert(fact["value"], source_unit, target_unit)
        return target, int(value) if target_unit in ("mm", "kg") else float(value)
    return key, fact["value"]


CYLINDERS = {"three": 3, "four": 4, "five": 5, "six": 6, "eight": 8, "ten": 10, "twelve": 12}


EDITION_NOISE = re.compile(
    r"\b(?:the|technical|specifications?|specs?|spec sheet|product information|quick reference guide|"
    r"press kit|features|and features)\b|&|\b(?:19|20)\d\d(?:\.5)?\b",
    re.I,
)


def press_edition(meta: dict, make: str) -> str:
    """The press document's edition within the line, from its published title ("2018 Elantra GT
    Specifications" -> "elantra gt", "2020 Accord Hybrid Specifications & Features" -> "accord
    hybrid"): editions of one model year (body styles, hybrids, AMG/M models) are separate
    scopes, not a conflict."""
    title = (meta.get("title") or "").split(":")[0]
    for name in {MAKES[make]["epa"], make.replace("-", " "), "Mercedes-Benz", "Mercedes-AMG", "BMW", "Land Rover"}:
        title = re.sub(re.escape(name) + r"(?!-)", " ", title, flags=re.I) if name != "Mercedes-AMG" else title
    title = EDITION_NOISE.sub(" ", title)
    return " ".join(re.sub(r"[^\w\s/+-]", " ", title).lower().split()) or "base"


def press_engine_label(text: str | None) -> str | None:
    """One spelling per engine across model years of a press site: displacement, cylinders,
    turbo/supercharged, hybrid ("2.5-liter 4-cylinder" = "2.5L I-4" = "2.5L I4")."""
    if not text:
        return None
    t = text.replace("\u2011", "-")
    disp = re.search(r"(\d\.\d)\s?-?\s?(?:L\b|liter|litre)", t, re.I)
    cyl = re.search(r"\b(?:I|V|H|W|L)-?(\d{1,2})\b|(\d{1,2})[- ]?cyl|\b(three|four|five|six|eight|ten|twelve)[- ]cylinder|\bV(\d{1,2})\b", t, re.I)
    if not disp:
        return None
    parts = [disp.group(1) + "L"]
    if cyl:
        n = next(g for g in cyl.groups() if g)
        parts.append(f"{CYLINDERS.get(n.lower(), n)}cyl")
    if re.search(r"turbo|T-?GDI|TSI|TFSI|EcoBoost|TwinPower", t, re.I):
        parts.append("Turbo")
    if re.search(r"supercharg", t, re.I):
        parts.append("Supercharged")
    if re.search(r"hybrid", t, re.I):
        parts.append("Hybrid")
    return " ".join(parts)
SKIP_KEYS = {"engine_oil_viscosity_alternative", "engine_oil_specification_alternative", "engine_oil_oem_approval_alternative"}
RANGES = {
    "engine_oil_capacity_l": (3, 12), "engine_oil_capacity_without_filter_l": (3, 12),
    "engine_oil_capacity_drain_refill_l": (3, 12), "coolant_capacity_l": (3, 25),
    "transmission_fluid_capacity_l": (0.5, 16), "fuel_tank_l": (20, 160),
    "octane_aki": (85, 94), "octane_ron": (89, 100),
    # press pages (after conversion)
    "power_hp": (60, 1100), "system_power_hp": (60, 1200), "torque_lb_ft": (60, 1300),
    "length_mm": (2500, 6500), "width_mm": (1400, 2300), "height_mm": (1000, 2300), "wheelbase_mm": (2000, 3800),
    "track_front_mm": (1200, 1900), "track_rear_mm": (1200, 1900), "ground_clearance": (80, 350),
    "curb_weight_kg": (700, 4500), "cargo_l": (100, 3500), "cargo_max_l": (200, 4000), "passenger_volume_l": (1500, 5500),
    "turning_circle_m": (8, 16), "towing_kg": (0, 6500), "wheel_size_in": (14, 24), "seats": (2, 9),
}
REGISTRY = {
    "mercedes-benz": "factory-mercedes-us", "land-rover": "factory-land-rover-us",
    "volkswagen": "factory-vw-us", "ford": "factory-ford-us",
}
RPO = re.compile(r"\(([A-Z][A-Z0-9]{2,5})\)")
TOYOTA_CODE = re.compile(r"\b(\d?[A-Z]{1,2}\d{1,2}[A-Z]?-[A-Z]{2,4})\b")


def engine_scope(text: str | None) -> tuple[str | None, str | None, str | None]:
    """(factory code, readable engine label, displacement) from a row's engine text."""
    if not text:
        return None, None, None
    code = None
    found = RPO.search(text) or TOYOTA_CODE.search(text)
    if found:
        code = found.group(1)
    label = re.sub(r"\s*\((?:[A-Z][A-Z0-9]{2,5})\)", "", text)
    label = re.sub(r"\s*\b[Ee]ngines?\b", "", label).strip(" ,-–")
    # one spelling per engine: "2.0L T-GDI" = "2.0 T-GDI", "turbo" = "Turbo"
    label = re.sub(r"(\d\.\d)\s?L\b", r"\1L", label)
    label = re.sub(r"(\d\.\d)L(?=\s?(?:T-?GDI|GDI|MPI|TFSI|TSI))", r"\1", label)
    label = re.sub(r"\bturbo\w*", "Turbo", label, flags=re.I)
    label = " ".join(label.split())
    displacement = re.search(r"(\d\.\d)\s?L?", label)
    return code, label or None, displacement.group(1) if displacement else None


LIST_KEYS = {"engine_oil_specification", "engine_oil_oem_approval", "coolant", "coolant_description", "transmission_fluid", "tires"}


def combine(values: list[str]) -> str:
    """List-type fields: all names one document gives, the most specific spelling kept
    ("SK ATF SP-IV" covers "SP-IV")."""
    unique = []
    values = [re.sub(r"\bACEA-", "ACEA ", v) for v in values]
    for v in sorted(set(values), key=lambda x: (-len(x), x)):
        if not any(v.lower() in u.lower() for u in unique):
            unique.append(v)
    return "; ".join(sorted(unique))


_CONFIRMED: dict[str, bool] = {}


def edition_confirmed(meta: dict) -> bool:
    """Does the document's text itself speak of a hybrid / plug-in / electric powertrain?"""
    if meta.get("doc_type") == "press_specifications":
        return True  # the manufacturer's own spec sheet for that edition
    title = f"{meta['key']} {meta.get('title', '')}".lower()
    claim = (r"plug-in|\bPHEV\b" if re.search(r"plug-in|phev|energi|prime", title)
             else r"hybrid" if re.search(r"hybrid|\bhev\b", title)
             else r"\bEV\b|electric vehicle|high[- ]voltage battery")
    sha = meta.get("sha256") or ""
    key = f"{sha}|{claim}"
    if key not in _CONFIRMED:
        try:
            with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
                text = " ".join(json.load(handle)["pages"])
            _CONFIRMED[key] = len(re.findall(claim, text, re.I)) >= 3
        except (FileNotFoundError, OSError, ValueError):
            _CONFIRMED[key] = True  # no page text to check: the title is kept
    return _CONFIRMED[key]


def doc_powertrain(meta: dict, staging: dict, year: int) -> str | None:
    """Powertrain a document covers when it is specific (hybrid/PHEV/EV edition, or the gas
    edition of a line that also has hybrids that year)."""
    text = f"{meta['key']} {meta.get('title', '')}".lower()
    if "incl-hybrid" in text or "incl hybrid" in text:
        return None
    if re.search(r"hybrid|\bhev\b|plug-in|phev|energi|prime|electric|\bev\b|e-tron", text) and not edition_confirmed(meta):
        # the file name says hybrid/EV but the manual's own text never does (carmans.net
        # "2015-kia-optima-hybrid.pdf" is the regular Optima manual): treated as the regular edition
        text = re.sub(r"hybrid|\bhev\b|plug-in|phev|energi|prime|electric|\bev\b|e-tron", " ", text)
    if re.search(r"plug-in|phev|energi|prime", text) and re.search(r"hybrid|\bhev\b", text.replace("plug-in hybrid", "")):
        return "HEV/PHEV"
    if re.search(r"plug-in|phev|energi|prime", text):
        return "PHEV"
    if re.search(r"hybrid|\bhev\b", text):
        return "HEV"
    if re.search(r"electric|\bev\b|e-tron", text):
        return "BEV"
    powertrains = {c["powertrain"] for c in staging["configurations"] if c["year"] == year}
    if powertrains - {"ICE"} and "ICE" in powertrains:
        return "ICE"
    return None


def doc_engine_code(doc: dict) -> str | None:
    """The engine family a document's specification chapter states, when it states one."""
    codes = {c for e in doc.get("engine_codes", []) for c in ([e] if isinstance(e, str) else e["codes"])}
    if not codes:
        return None
    if doc["doc"].get("doc_type") == "press_specifications" and len(codes) != 1:
        return None  # a press page with several engines: each fact carries its own engine text
    return "/".join(sorted(codes))


def generation_for(year, gens):
    for g in gens:
        if g["start_year"] <= year <= g["end_year"]:
            return g["code"]
    return None


def epa_displacements(staging: dict) -> dict[int, set]:
    out = defaultdict(set)
    for cfg in staging["configurations"]:
        if cfg.get("displacement_l"):
            out[cfg["year"]].add(str(cfg["displacement_l"]))
    return out


def page_text(sha: str, page: int) -> str:
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"][page - 1]


def build_line(make: str, line_key: str, extracted: list[dict]) -> dict:
    line = BY_KEY[line_key]
    staging_path = WORK / make / "staging" / line.slug / "staging.json"
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    gens = staging["generations"]
    displacements = epa_displacements(staging)
    sources, gaps, conflicts = {}, [], []
    # observations: scope -> year -> list of (value, cite)
    observed = defaultdict(lambda: defaultdict(list))
    ambiguous = set()
    # years a US owner's manual covers per field: a secondary database (auto-data.net) only
    # fills a field for model years no US manual gives it for
    manual_years = defaultdict(set)
    for doc in extracted:
        meta = doc["doc"]
        if (line_key in meta["lines"] and doc.get("edition_market") == "US"
                and meta.get("doc_type") not in ("press_specifications", "teoalida_specifications")):
            for fact in doc["facts"]:
                manual_years[fact["key"]].update(meta["years"])
    for doc in extracted:
        meta = doc["doc"]
        secondary = meta.get("doc_type") == "secondary_specifications"
        if line_key not in meta["lines"]:
            continue
        if doc.get("edition_market") != "US" and not (secondary and doc.get("edition_market") == "EU_MATCHED_TO_US"):
            continue
        tier = meta["tier"]
        doc_code = doc_engine_code(doc)
        per_doc = defaultdict(set)
        rows = []
        press = meta.get("doc_type") == "press_specifications"
        for fact in doc["facts"]:
            if press:
                try:
                    key, value = press_value(fact)
                except (ArithmeticError, ValueError):
                    gaps.append({"scope": f"{line_key} {meta['key']} p.{fact['page']}", "field": fact["key"],
                                 "reason": f"value {fact['value']!r} is not a number; not used"})
                    continue
                fact = {**fact, "key": key, "value": value}
            key = fact["key"]
            if key in SKIP_KEYS:
                continue
            if make == "mercedes-benz" and key == "coolant" and re.search(r"\b331\.\d", str(fact["value"])):
                # MB sheet 331.x is the brake fluid approval; a row pass can read it under the
                # coolant heading of the same page (operator's manuals and their copies)
                gaps.append({"scope": f"{line_key} {meta['key']} p.{fact['page']}", "field": key,
                             "reason": f"value {fact['value']!r} is the MB brake fluid approval, not a coolant; not used"})
                continue
            if key in RANGES and not (RANGES[key][0] <= float(fact["value"]) <= RANGES[key][1]):
                gaps.append({"scope": f"{line_key} {meta['key']} p.{fact['page']}", "field": key,
                             "reason": f"value {fact['value']} outside the validator range; not used"})
                continue
            code, label, displacement = engine_scope(fact.get("engine_text"))
            if press:
                label = press_engine_label(fact.get("engine_text")) or label
            for year in meta["years"]:
                if secondary and year in manual_years.get(key, set()):
                    continue
                if not (line.years[0] <= year <= line.years[1]):
                    continue
                gen = generation_for(year, gens)
                if gen is None:
                    continue
                engine_key = None
                applicability = {"edition": press_edition(meta, make)} if press else {}
                if key in ENGINE_DEPENDENT:
                    if code:
                        engine_key = code
                    elif label:
                        applicability["engine"] = label
                    elif doc_code:
                        engine_key = doc_code
                    elif fact.get("source_layout") == "mb_model_table" and (fact.get("variant") or fact.get("all_models")):
                        pass  # Mercedes "Model | Capacity" row: the row names its models (variant) or says "All models"
                    elif len(displacements.get(year, set())) <= 1:
                        if displacements.get(year):
                            applicability["displacement_l"] = sorted(displacements[year])[0]
                    else:
                        ambiguous.add((meta["key"], key, year, "engine not stated; EPA lists several engines"))
                        continue
                elif press and key in VARIANT_KEYS and fact.get("engine_text"):
                    applicability["variant"] = " ".join(fact["engine_text"].split())
                if fact.get("variant"):
                    applicability["variant"] = " ".join(fact["variant"].split())
                if fact.get("applicability_extra"):  # database rows (Teoalida): transmission type, part condition
                    applicability.update(fact["applicability_extra"])
                if fact.get("drive"):
                    applicability["drive"] = fact["drive"]
                powertrain = doc_powertrain(meta, staging, year)
                if powertrain and key not in ("brake_fluid", "octane_aki", "octane_ron"):
                    applicability["powertrain"] = powertrain
                level = "ENGINE" if engine_key and key in ENGINE_KEYS else "GENERATION"
                if engine_key and level == "GENERATION":
                    applicability["engine_code"] = engine_key
                    engine_key = None
                scope = (gen, level, engine_key, key, json.dumps(applicability, sort_keys=True))
                cite = {
                    "source": meta["key"], "pages": [fact["page"]], "quote": fact["quote"], "row": fact.get("row"),
                    "tier": tier, "publisher": meta["publisher"], "year": year,
                    "range": bool(meta.get("generation_range")),
                    "approx_in_source": bool(fact.get("approx_in_source")),
                }
                per_doc[(scope, year)].add(json.dumps(fact["value"]))
                rows.append((scope, year, fact["value"], cite, fact))
        combined = {}
        for (scope, year), values in per_doc.items():
            if scope[3] in LIST_KEYS and len(values) > 1:
                combined[(scope, year)] = json.dumps(combine([json.loads(v) for v in values]))
            elif len(values) > 1:
                ambiguous.add((meta["key"], scope[3], year, f"one document gives {len(values)} values: {sorted(values)}"))
        done = set()
        for scope, year, value, cite, fact in rows:
            if (scope, year) in combined:
                if (scope, year) in done:
                    observed[scope][year][-1][1]["quote_more"] = observed[scope][year][-1][1].get("quote_more", []) + [cite["quote"]]
                    continue
                done.add((scope, year))
                value = json.loads(combined[(scope, year)])
            elif len(per_doc[(scope, year)]) > 1:
                continue
            observed[scope][year].append((value, cite, fact))
            used = sources.setdefault(meta["key"], {"meta": meta, "pages": set()})
            used["pages"].add(fact["page"])
    for doc_key, key, year, reason in sorted(ambiguous):
        gaps.append({"scope": f"{line_key} MY{year} ({doc_key})", "field": key, "reason": reason})
    # what a US manual says it does not print (VW/Audi: oil standard and quantity on a label in
    # the engine compartment): a gap with the manual's own words, never a value
    for doc in extracted:
        meta = doc["doc"]
        if line_key not in meta["lines"] or doc.get("edition_market") != "US":
            continue
        for note in doc.get("not_in_manual", []):
            years = [y for y in meta["years"] if line.years[0] <= y <= line.years[1]]
            for field in note["fields"]:
                if years:
                    gaps.append({"scope": f"{line_key} MY{years[0]}-{years[-1]} ({meta['key']} p.{note['page']})", "field": field,
                                 "reason": f"{note['reason']} — «{note['quote']}»"})
    facts = []
    for scope, by_year in observed.items():
        gen, level, engine_key, key, applicability_json = scope
        applicability = json.loads(applicability_json)
        chosen = {}  # year -> (value, cites, hidden list)
        for year, items in by_year.items():
            values = defaultdict(list)
            for value, cite, fact in items:
                values[json.dumps(value)].append((cite, fact))
            if len(values) == 1:
                value_json, cites = next(iter(values.items()))
                chosen[year] = (value_json, cites, [])
                continue
            # rank: official before copy; a manual of that model year before a whole-generation
            # page (mycarusermanual, Appendix E.6); then the value more documents give
            def rank(kv):
                cites = [c for c, _ in kv[1]]
                return (min(c["tier"] for c in cites), all(c["range"] for c in cites), -len(cites))

            ranked = sorted(values.items(), key=rank)
            best = rank(ranked[0])[:2]
            leaders = [kv for kv in ranked if rank(kv)[:2] == best]
            if len(leaders) == 1:
                chosen[year] = (ranked[0][0], ranked[0][1], ranked[1:])
                conflicts.append({"scope": f"{line_key} {gen} MY{year}", "key": key, "applicability": applicability,
                                  "kept_value": json.loads(ranked[0][0]),
                                  "kept_from": sorted({c["source"] for c, _ in ranked[0][1]}),
                                  "other_values": [json.loads(v) for v, _ in ranked[1:]],
                                  "other_sources": sorted({c["source"] for _, cs in ranked[1:] for c, _ in cs}),
                                  "resolution": "official document kept over the copy" if rank(ranked[0])[0] != rank(ranked[1])[0]
                                  else "model-year manual kept over the whole-generation page (Appendix E.6)"})
            else:
                chosen[year] = (None, [], ranked)
                conflicts.append({"scope": f"{line_key} {gen} MY{year}", "key": key, "applicability": applicability,
                                  "kept_value": None, "other_values": [json.loads(v) for v, _ in ranked],
                                  "other_sources": sorted({c["source"] for _, cs in ranked for c, _ in cs}),
                                  "resolution": "sources of the same rank disagree; field not shown"})
        # contiguous runs of the same value
        for hidden in (False, True):
            runs = []
            for year in sorted(chosen):
                value_json, cites, others = chosen[year]
                entries = [(value_json, cites)] if not hidden else [(v, cs) for v, cs in others]
                for v, cs in entries:
                    if v is None:
                        continue
                    if runs and runs[-1]["value"] == v and runs[-1]["years"][-1] == year - 1:
                        runs[-1]["years"].append(year)
                        runs[-1]["cites"] += cs
                    else:
                        runs.append({"value": v, "years": [year], "cites": list(cs)})
            for run in runs:
                value = json.loads(run["value"])
                cites = [c for c, _ in run["cites"]]
                first_fact = run["cites"][0][1]
                tiers = {c["tier"] for c in cites}
                approx = any(c["approx_in_source"] for c in cites)
                display = "HIDDEN_CONFLICT" if hidden else ("FACT" if "A" in tiers else "SECONDARY_NOTE")
                digest = hashlib.sha1(json.dumps([applicability, run["value"], hidden], sort_keys=True).encode()).hexdigest()[:8]
                facts.append({
                    "id": f"{line.slug}-{gen}-man-{key}-{digest}-{run['years'][0]}",
                    "generation": gen,
                    "key": key,
                    "level": level,
                    "engine": engine_key,
                    "gen_bound": True,
                    "years": [run["years"][0], run["years"][-1]],
                    "value": value,
                    "unit": unit_of(key),
                    "original": first_fact.get("original") or first_fact["quote"],
                    "applicability": {**applicability, **({"approx_in_source": True} if approx else {})},
                    "note": "manufacturer states the figure as approximate/reference" if approx else None,
                    "cites": [
                        {**{k: c[k] for k in ("source", "pages", "quote", "tier", "publisher", "row", "year")},
                         **({"quote_more": c["quote_more"]} if c.get("quote_more") else {})}
                        for c in cites
                    ],
                    "display_level": display,
                    "confidence": "HIGH" if display == "FACT" else "LOW" if hidden else "MEDIUM",
                    "primary_source": sorted(cites, key=lambda c: (c["tier"], c["source"]))[0]["source"],
                })
    factory_registry = REGISTRY.get(make, f"factory-{make}-us")
    out_sources = {}
    for key, used in sources.items():
        meta = used["meta"]
        extract = {"pdf_sha256": meta["sha256"], "url": meta["url"],
                   "pages": {str(p): page_text(meta["sha256"], p) for p in sorted(used["pages"])}}
        out_sources[key] = {
            "key": key, "kind": "pdf_pages", "path": "rawstore:" + Path(meta["path"]).relative_to(RAW_ROOT).as_posix(),
            "url": meta["url"], "page_url": meta.get("page_url"), "sha256": meta["sha256"], "retrieved_at": meta["retrieved_at"],
            "tier": meta["tier"], "source_type": meta["source_type"],
            "registry": meta.get("registry") or ("auto-data" if meta.get("doc_type") == "secondary_specifications" else factory_registry),
            "title": meta.get("title") or f"{MAKES[make]['epa']} owner's manual {meta['years']} ({meta['key']})",
            "publisher": meta["publisher"], "authenticity": meta["authenticity"],
            "edition": meta.get("edition") or ("EU listing matched to the US configuration" if meta.get("doc_type") == "secondary_specifications" else "US"),
            "model_year": meta["years"][0] if meta["years"] else None,
            "extract": json.dumps(extract, ensure_ascii=False),
        }
    # what no document gave, per generation
    wanted = {
        "manual": (["engine_oil_capacity_l", "engine_oil_viscosity", "coolant", "transmission_fluid", "brake_fluid", "fuel_tank_l"],
                   "US owner's manual"),
        "press": (["power_hp", "torque_lb_ft", "tires", "front_suspension", "rear_suspension", "front_brakes", "steering",
                   "ground_clearance", "cargo_l"], "US press specification page"),
    }
    for gen in gens:
        have = {f["key"] for f in facts if f["generation"] == gen["code"] and f["display_level"] != "HIDDEN_CONFLICT"}
        for kind, (keys, what) in wanted.items():
            docs_for_gen = [
                s for s in sources.values()
                if any(gen["start_year"] <= y <= gen["end_year"] for y in s["meta"]["years"])
                and (s["meta"].get("doc_type") == "press_specifications") == (kind == "press")
                and s["meta"].get("doc_type") != "teoalida_specifications"
            ]
            for key in keys:
                if key in ("power_hp", "torque_lb_ft") and all(
                    c["powertrain"] == "BEV" for c in staging["configurations"]
                    if gen["start_year"] <= c["year"] <= gen["end_year"]
                ):
                    continue
                if key not in have:
                    gaps.append({"scope": f"{line_key} {gen['code']}", "field": key,
                                 "reason": f"no {what} for these years" if not docs_for_gen
                                 else f"not found unambiguously in the available {what}s"})
    return {"sources": out_sources, "facts": facts, "conflicts": conflicts, "gaps": gaps}


def main(argv) -> int:
    make = argv[0]
    extracted = []
    for path in sorted((WORK / make / "extracted").glob("*.json")):
        if path.name.startswith("_"):
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("status") == "ok":
            extracted.append(doc)
    for line in lines_for(make):
        if not (WORK / make / "staging" / line.slug / "staging.json").exists():
            continue
        result = build_line(make, line.key, extracted)
        out = WORK / make / "staging" / line.slug / "manual_facts.json"
        out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        shown = sum(1 for f in result["facts"] if f["display_level"] != "HIDDEN_CONFLICT")
        print(line.key, "sources", len(result["sources"]), "facts", shown, "hidden", len(result["facts"]) - shown,
              "conflicts", len(result["conflicts"]), "gaps", len(result["gaps"]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
