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
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY, MAKES, lines_for  # noqa: E402

ENGINE_KEYS = {
    "engine_oil_capacity_l", "engine_oil_capacity_without_filter_l", "engine_oil_capacity_drain_refill_l",
    "engine_oil_viscosity", "engine_oil_specification", "engine_oil_oem_approval",
}
ENGINE_DEPENDENT = ENGINE_KEYS | {"coolant_capacity_l", "transmission_fluid_capacity_l"}
SKIP_KEYS = {"engine_oil_viscosity_alternative", "engine_oil_specification_alternative", "engine_oil_oem_approval_alternative"}
RANGES = {
    "engine_oil_capacity_l": (3, 12), "engine_oil_capacity_without_filter_l": (3, 12),
    "engine_oil_capacity_drain_refill_l": (3, 12), "coolant_capacity_l": (3, 25),
    "transmission_fluid_capacity_l": (0.5, 16), "fuel_tank_l": (20, 160),
    "octane_aki": (85, 94), "octane_ron": (89, 100),
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


LIST_KEYS = {"engine_oil_specification", "engine_oil_oem_approval", "coolant", "coolant_description", "transmission_fluid"}


def combine(values: list[str]) -> str:
    """List-type fields: all names one document gives, the most specific spelling kept
    ("SK ATF SP-IV" covers "SP-IV")."""
    unique = []
    values = [re.sub(r"ACEA-", "ACEA ", v) for v in values]
    for v in sorted(set(values), key=lambda x: (-len(x), x)):
        if not any(v.lower() in u.lower() for u in unique):
            unique.append(v)
    return "; ".join(sorted(unique))


def doc_powertrain(meta: dict, staging: dict, year: int) -> str | None:
    """Powertrain a document covers when it is specific (hybrid/PHEV/EV edition, or the gas
    edition of a line that also has hybrids that year)."""
    text = f"{meta['key']} {meta.get('title', '')}".lower()
    if "incl-hybrid" in text or "incl hybrid" in text:
        return None
    if re.search(r"plug-in|phev|energi|prime", text) and re.search(r"hybrid|hev", text.replace("plug-in hybrid", "")):
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
    codes = {c for e in doc.get("engine_codes", []) for c in e["codes"]}
    if not codes:
        return None
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
    for doc in extracted:
        meta = doc["doc"]
        if line_key not in meta["lines"] or doc.get("edition_market") != "US":
            continue
        tier = meta["tier"]
        doc_code = doc_engine_code(doc)
        per_doc = defaultdict(set)
        rows = []
        for fact in doc["facts"]:
            key = fact["key"]
            if key in SKIP_KEYS:
                continue
            if key in RANGES and not (RANGES[key][0] <= float(fact["value"]) <= RANGES[key][1]):
                gaps.append({"scope": f"{line_key} {meta['key']} p.{fact['page']}", "field": key,
                             "reason": f"value {fact['value']} outside the validator range; not used"})
                continue
            code, label, displacement = engine_scope(fact.get("engine_text"))
            for year in meta["years"]:
                if not (line.years[0] <= year <= line.years[1]):
                    continue
                gen = generation_for(year, gens)
                if gen is None:
                    continue
                engine_key = None
                applicability = {}
                if key in ENGINE_DEPENDENT:
                    if code:
                        engine_key = code
                    elif label:
                        applicability["engine"] = label
                    elif doc_code:
                        engine_key = doc_code
                    elif len(displacements.get(year, set())) <= 1:
                        if displacements.get(year):
                            applicability["displacement_l"] = sorted(displacements[year])[0]
                    else:
                        ambiguous.add((meta["key"], key, year, "engine not stated; EPA lists several engines"))
                        continue
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
            ranked = sorted(values.items(), key=lambda kv: (min(c["tier"] for c, _ in kv[1]), -len(kv[1])))
            best_tier = min(c["tier"] for c, _ in ranked[0][1])
            leaders = [kv for kv in ranked if min(c["tier"] for c, _ in kv[1]) == best_tier]
            if len(leaders) == 1:
                chosen[year] = (ranked[0][0], ranked[0][1], ranked[1:])
                conflicts.append({"scope": f"{line_key} {gen} MY{year}", "key": key, "applicability": applicability,
                                  "kept_value": json.loads(ranked[0][0]),
                                  "kept_from": sorted({c["source"] for c, _ in ranked[0][1]}),
                                  "other_values": [json.loads(v) for v, _ in ranked[1:]],
                                  "other_sources": sorted({c["source"] for _, cs in ranked[1:] for c, _ in cs}),
                                  "resolution": "official document kept over the copy"})
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
                    "unit": "L" if key.endswith("_l") else None,
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
    registry = REGISTRY.get(make, f"factory-{make}-us")
    out_sources = {}
    for key, used in sources.items():
        meta = used["meta"]
        extract = {"pdf_sha256": meta["sha256"], "url": meta["url"],
                   "pages": {str(p): page_text(meta["sha256"], p) for p in sorted(used["pages"])}}
        out_sources[key] = {
            "key": key, "kind": "pdf_pages", "path": "rawstore:" + Path(meta["path"]).relative_to(RAW_ROOT).as_posix(),
            "url": meta["url"], "page_url": meta.get("page_url"), "sha256": meta["sha256"], "retrieved_at": meta["retrieved_at"],
            "tier": meta["tier"], "source_type": meta["source_type"], "registry": registry,
            "title": meta.get("title") or f"{MAKES[make]['epa']} owner's manual {meta['years']} ({meta['key']})",
            "publisher": meta["publisher"], "authenticity": meta["authenticity"], "edition": "US",
            "model_year": meta["years"][0] if meta["years"] else None,
            "extract": json.dumps(extract, ensure_ascii=False),
        }
    # what no document gave, per generation
    wanted = ["engine_oil_capacity_l", "engine_oil_viscosity", "coolant", "transmission_fluid", "brake_fluid", "fuel_tank_l"]
    for gen in gens:
        have = {f["key"] for f in facts if f["generation"] == gen["code"] and f["display_level"] != "HIDDEN_CONFLICT"}
        docs_for_gen = [s for s in sources.values() if any(gen["start_year"] <= y <= gen["end_year"] for y in s["meta"]["years"])]
        for key in wanted:
            if key not in have:
                gaps.append({"scope": f"{line_key} {gen['code']}", "field": key,
                             "reason": "no US owner's manual for these years" if not docs_for_gen
                             else "not found unambiguously in the available US manuals"})
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
