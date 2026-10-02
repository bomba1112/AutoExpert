"""Build and validate the staging set for one make/line of the US tech database.

Inputs (all produced earlier in this pipeline, nothing from model memory):
  data_work/<make>/staging/<line>/authored_gen_*.json   hand-authored facts, each with
                                                        verbatim quotes from opened sources
  data_work/<make>/raw/...                              cached sources (git-ignored)
  data_work/<make>/manifest.csv, raw/manuals/manifest.csv, data_work/_shared/manifest.csv

Every authored quote must be found in the cached text of its source; the page is
resolved automatically. Values derived by unit conversion are recomputed with the
fixed factors of app.services.tech_units. EPA configurations, NHTSA recalls and NHTSA
complaint patterns are derived by code from the cached raw files.

Output: data_work/<make>/staging/<line>/staging.json (+ conflicts.csv, gaps.csv)
Exit code 1 when any validation error remains; nothing is written to the database here.

  .venv/Scripts/python.exe scripts/build_us_tech_staging.py toyota camry
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402

COMPLAINT_PATTERN_THRESHOLD = 10  # prompt section 7: starting threshold, kept as a constant
# Symptom keyword patterns applied to NHTSA complaint narratives (upper-cased). A complaint
# can match several symptoms. Counts are per generation and model year; NHTSA complaints
# carry no engine field, so patterns are never attributed to one engine.
SYMPTOM_PATTERNS = {
    "fuel pump / stall": r"FUEL PUMP|STALL",
    "brake vacuum pump / assist loss": r"VACUUM PUMP|BRAKE ASSIST|HARD (BRAKE )?PEDAL|BRAKE PEDAL (WAS |BECAME )?(HARD|STIFF)",
    "hesitation / delayed acceleration": r"HESITAT|DELAY(ED)? (IN )?ACCELERAT|LAG",
    "harsh / erratic shifting": r"(HARSH|ROUGH|ERRATIC|JERK|LURCH|CLUNK)\w*.{0,40}SHIFT|SHIFT\w*.{0,40}(HARSH|ROUGH|ERRATIC|JERK|LURCH)",
    "torque converter shudder": r"SHUDDER|TORQUE CONVERTER",
    "water pump / coolant leak": r"WATER PUMP|COOLANT LEAK|LEAKING COOLANT",
    "transmission whine / grind": r"WHINE|GRIND",
    "power steering loss / steering": r"(LOSS OF|LOST) (POWER )?STEERING|POWER STEERING (FAIL|WARNING)|STEERING (BECAME|IS|WAS) (HARD|STIFF|DIFFICULT)|EPS",
    "excessive oil consumption": r"OIL CONSUMPTION|BURN\w* OIL|CONSUM\w* OIL",
    "air bag light / OCS": r"AIR ?BAG (LIGHT|WARNING)|PASSENGER AIR ?BAG (OFF|DISABLED)|OCCUPANT CLASSIFICATION",
    "pre-collision false braking": r"PRE-?COLLISION|PHANTOM BRAK|FALSE(LY)? BRAK|BRAKED (BY ITSELF|ON ITS OWN)",
}
MARKET = "US"
LINE_NAMES = {"camry": ("Camry", ["CAMRY", "CAMRY HYBRID"])}

# Plausibility ranges (validator, prompt section 6). Values outside are rejected.
RANGES = {
    "engine_oil_capacity_l": (3, 12),
    "engine_oil_capacity_without_filter_l": (3, 12),
    "coolant_capacity_l": (3, 20),
    "transmission_fluid_capacity_l": (1, 15),
    "fuel_tank_l": (20, 150),
    "length_mm": (3000, 6000),
    "width_mm": (1400, 2200),
    "height_mm": (1100, 2200),
    "wheelbase_mm": (2000, 3800),
    "track_front_mm": (1200, 1900),
    "track_rear_mm": (1200, 1900),
    "ground_clearance": (90, 350),
    "cargo_l": (100, 3000),
    "curb_weight_kg": (700, 4000),
    "engine_displacement_cc": (600, 8000),
    "power_hp": (40, 900),
    "system_power_hp": (40, 1200),
    "torque_lb_ft": (40, 1000),
    "tire_pressure_front_kpa": (150, 450),
    "tire_pressure_rear_kpa": (150, 450),
    "wheel_nut_torque_nm": (50, 250),
    "octane_aki": (85, 95),
    "octane_ron": (89, 100),
    "seats": (2, 9),
}


# Symbol-font private-use glyphs used by the manuals (U+F0B4 is the multiplication sign),
# BOM-like and soft-hyphen artifacts, and typographic quotes; code points keep the source ASCII.
NORMALIZE = (
    (chr(0xF0B4), chr(0x00D7)),
    (chr(0xF0B0), chr(0x00B0)),
    (chr(0xFFFE), ""),
    (chr(0x00AD), ""),
    (chr(0x00A0), " "),
    (chr(0x201C), '"'),
    (chr(0x201D), '"'),
    (chr(0x2019), "'"),
)


def norm(text: str) -> str:
    for old, new in NORMALIZE:
        text = text.replace(old, new)
    return " ".join(text.split())


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Sources:
    """Registry of every source document, keyed by short ids used in authored files."""

    def __init__(self, make: str, line: str):
        self.make, self.line = make, line
        self.base = ROOT / "data_work" / make
        self.items: dict[str, dict] = {}
        self._text_cache: dict[str, object] = {}
        editions = {}
        path = self.base / "manual_editions.json"
        if path.exists():
            editions = json.loads(path.read_text(encoding="utf-8"))
        for row in read_csv(self.base / "raw" / "manuals" / "manifest.csv"):
            if row["status"] != "ok":
                continue
            hybrid = row["model"].endswith("-hybrid")
            key = f"om-{row['year']}" + ("-hv" if hybrid else "")
            name = Path(row["path"]).name
            self.items[key] = {
                "key": key,
                "kind": "pdf",
                "path": row["path"],
                "url": row["url"],
                "page_url": row["page_url"],
                "sha256": row["sha256"],
                "retrieved_at": row["retrieved_at"],
                "tier": "B",
                "source_type": "OWNER_MANUAL_COPY",
                "title": f"{row['year']} Toyota Camry{' Hybrid' if hybrid else ''} Owner's Manual (US edition, copy)",
                "publisher": "Toyota (factory owner's manual), copy hosted by carmans.net",
                "authenticity": "REVIEWED_MIRROR",
                "edition": editions.get(name, {}).get("edition_market"),
                "model_year": int(row["year"]),
            }
        for row in read_csv(ROOT / "data_work" / "_shared" / "manifest.csv"):
            if row["status"] != "ok":
                continue
            path = row["path"]
            if "/product_info/" in path and "amry" in path:
                name = Path(path).name
                year = int(re.search(r"(20\d\d)", name).group(1))
                hybrid = "Hybrid" in name
                key = f"pi-{year}" + ("-hv" if hybrid else "")
                if key in self.items:
                    continue
                self.items[key] = {
                    "key": key,
                    "kind": "pdf",
                    "path": path,
                    "url": row["url"],
                    "page_url": row["page_url"],
                    "sha256": row["sha256"],
                    "retrieved_at": row["retrieved_at"],
                    "tier": "A",
                    "source_type": "PRODUCT_INFORMATION",
                    "title": f"{year} Toyota Camry{' Hybrid' if hybrid else ''} Product Information",
                    "publisher": "Toyota Motor North America (file linked from pressroom.toyota.com)",
                    "authenticity": "OFFICIAL_PUBLISHER",
                    "model_year": year,
                }
            elif row["kind"] == "epa_vehicles_csv":
                self.items["epa"] = {
                    "key": "epa",
                    "kind": "epa",
                    "path": path,
                    "url": row["url"],
                    "sha256": row["sha256"],
                    "retrieved_at": row["retrieved_at"],
                    "tier": "A",
                    "source_type": "US_FEDERAL_DATASET",
                    "title": "EPA fueleconomy.gov vehicles.csv",
                    "publisher": "U.S. DOE / EPA (fueleconomy.gov)",
                    "authenticity": "OFFICIAL_PUBLISHER",
                }
            elif "nhtsa_mfrcomms/MFR_COMMS" in path:
                self.items.setdefault(
                    "nhtsa-mfrcomms",
                    {
                        "key": "nhtsa-mfrcomms",
                        "kind": "mfrcomms",
                        "paths": [],
                        "url": "https://static.nhtsa.gov/odi/ffdd/tsbs/",
                        "sha256": "",
                        "retrieved_at": row["retrieved_at"],
                        "tier": "A",
                        "source_type": "US_FEDERAL_DATASET",
                        "title": "NHTSA Manufacturer Communications flat files",
                        "publisher": "NHTSA",
                        "authenticity": "OFFICIAL_PUBLISHER",
                    },
                )["paths"].append(path)
        for row in read_csv(self.base / "manifest.csv"):
            if row["status"] != "ok":
                continue
            kind, year = row["kind"], row["year"]
            if kind == "pressroom":
                key = "pressroom-" + slug(row["page_url"].split("pressroom.toyota.com/")[-1])
                self.items[key] = {
                    "key": key,
                    "kind": "html",
                    "path": row["path"],
                    "url": row["page_url"],
                    "sha256": row["sha256"],
                    "retrieved_at": row["retrieved_at"],
                    "tier": "A",
                    "source_type": "PRESS_RELEASE",
                    "title": row["page_url"],
                    "publisher": "Toyota Motor North America (pressroom.toyota.com)",
                    "authenticity": "OFFICIAL_PUBLISHER",
                }
            elif kind in ("vpic_canada_specs", "nhtsa_recalls", "nhtsa_complaints"):
                prefix = {
                    "vpic_canada_specs": "vpic-ca",
                    "nhtsa_recalls": "nhtsa-recalls",
                    "nhtsa_complaints": "nhtsa-complaints",
                }[kind]
                self.items[f"{prefix}-{year}"] = {
                    "key": f"{prefix}-{year}",
                    "kind": "json",
                    "path": row["path"],
                    "url": row["url"],
                    "sha256": row["sha256"],
                    "retrieved_at": row["retrieved_at"],
                    "tier": "B" if kind == "vpic_canada_specs" else "A",
                    "source_type": {
                        "vpic_canada_specs": "VPIC_CANADIAN_SPECIFICATIONS",
                        "nhtsa_recalls": "NHTSA_RECALLS_API",
                        "nhtsa_complaints": "NHTSA_COMPLAINTS_API",
                    }[kind],
                    "title": f"{kind} {row['model']} {year}",
                    "publisher": "NHTSA"
                    + (" vPIC (Transport Canada data)" if kind == "vpic_canada_specs" else ""),
                    "authenticity": "OFFICIAL_PUBLISHER",
                    "model_year": int(year),
                }
        support = self.base / "raw" / "support_toyota" / "timing-belt-or-chain-7690.txt"
        if support.exists():
            self.items["support-timing"] = {
                "key": "support-timing",
                "kind": "txt",
                "path": support.relative_to(ROOT).as_posix(),
                "url": "https://support.toyota.com/s/article/Does-my-vehicle-have-7690?language=en_US",
                "sha256": hashlib.sha256(support.read_bytes()).hexdigest(),
                "retrieved_at": "2026-10-02",
                "tier": "A",
                "source_type": "MANUFACTURER_SUPPORT_ARTICLE",
                "title": "Does my vehicle have a timing belt or timing chain?",
                "publisher": "Toyota Motor North America (support.toyota.com)",
                "authenticity": "OFFICIAL_PUBLISHER",
            }

    def powertrain_scope(self, key: str):
        """ICE/HEV when a document covers only one powertrain, None when it covers both.

        Gasoline owner's manuals and Product Information sheets document gasoline models only;
        hybrid documents (and the hybrid-only MY2025+ Camry sheets) document hybrids only.
        """
        item = self.items.get(key) or {}
        if item.get("source_type") not in {"OWNER_MANUAL_COPY", "PRODUCT_INFORMATION"}:
            return None
        if key.endswith("-hv"):
            return "HEV"
        first_page = self.pages(key)[0] if item.get("kind") == "pdf" else ""
        return "HEV" if "HYBRID POWER SYSTEM" in first_page.upper() else "ICE"

    def pages(self, key: str) -> list[str]:
        """Normalized text units of a source: PDF pages, or one unit for other kinds."""
        if key in self._text_cache:
            return self._text_cache[key]
        item = self.items[key]
        if item["kind"] == "pdf":
            cache = self.base / "raw" / "pagetext" / f"{Path(item['path']).stem}.json"
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data["sha256"] != item["sha256"]:
                raise ValueError(f"PAGE_CACHE_STALE:{key}")
            units = [norm(t) for t in data["pages"]]
        elif item["kind"] == "html":
            soup = BeautifulSoup((ROOT / item["path"]).read_text(encoding="utf-8"), "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            units = [norm(title + " " + soup.get_text(" ", strip=True))]
        elif item["kind"] == "mfrcomms":
            rows = mfrcomms_rows(self)
            units = [norm(r["summary"]) for r in rows]
        elif item["kind"] == "json":
            data = json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
            units = [norm(json.dumps(data, ensure_ascii=False))]
        else:
            units = [norm((ROOT / item["path"]).read_text(encoding="utf-8"))]
        self._text_cache[key] = units
        return units

    def locate(self, key: str, quote: str):
        if key not in self.items:
            return None, "UNKNOWN_SOURCE"
        wanted = norm(quote)
        hits = [i + 1 for i, text in enumerate(self.pages(key)) if wanted in text]
        if not hits:
            return None, "QUOTE_NOT_FOUND"
        return hits, None


_MFR_ROWS = None


def mfrcomms_rows(sources: Sources):
    global _MFR_ROWS
    if _MFR_ROWS is not None:
        return _MFR_ROWS
    names = LINE_NAMES[sources.line][1]
    rows = []
    for path in sources.items["nhtsa-mfrcomms"]["paths"]:
        archive = zipfile.ZipFile(ROOT / path)
        member = [i.filename for i in archive.infolist() if i.filename.endswith(".csv")][0]
        with archive.open(member) as handle:
            for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8", errors="replace")):
                if (
                    row["Make"].strip().upper() != "TOYOTA"
                    or row["Model"].strip().upper() not in names
                ):
                    continue
                years = sorted(
                    {int(y) for y in re.findall(r"\d{4}", row["Model Year"]) if y != "9999"}
                )
                if not any(2014 <= y <= 2026 for y in years):
                    continue
                rows.append(
                    {
                        "id": row["TSB/Document ID"].strip(),
                        "model": row["Model"].strip().upper(),
                        "years": years,
                        "summary": row["Concise Summary"].strip(),
                        "file": Path(path).name,
                    }
                )
    _MFR_ROWS = rows
    return rows


def generation_for(year: int, generations: list[dict]):
    for gen in generations:
        if gen["start_year"] <= year <= gen["end_year"]:
            return gen["code"]
    return None


def build(make: str, line: str) -> int:
    staging_dir = ROOT / "data_work" / make / "staging" / line
    sources = Sources(make, line)
    authored = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(staging_dir.glob("authored_gen_*.json"))
    ]
    errors, conflicts, gaps, facts = [], [], [], []
    generations = []

    def resolve(cites, where):
        resolved = []
        for cite in cites:
            key, quote = cite[0], cite[1]
            pages, problem = sources.locate(key, quote)
            if problem:
                errors.append({"where": where, "source": key, "quote": quote, "error": problem})
                continue
            item = sources.items[key]
            resolved.append(
                {
                    "source": key,
                    "pages": pages if item["kind"] == "pdf" else None,
                    "quote": quote,
                    "tier": item["tier"],
                    "publisher": item["publisher"],
                }
            )
        return resolved

    for doc in authored:
        row = doc["generation_row"]
        generations.append(
            {
                "code": row["code"],
                "start_year": row["start_year"],
                "end_year": row["end_year"],
                "evidence": resolve(row.get("cites", []), f"generation {row['code']}"),
                "boundary_evidence": row.get("boundary_evidence", []),
                "open_ended": bool(row.get("open_ended")),
                "name": row.get("name"),
            }
        )
    for doc in authored:
        gen = doc["generation"]
        for index, fact in enumerate(doc["facts"]):
            where = f"{gen}#{index} {fact['key']}"
            cites = resolve(fact["cites"], where)
            if not cites:
                continue
            value = fact["value"]
            if "convert" in fact:
                number, unit_from, unit_to = fact["convert"]
                expected = convert(number, unit_from, unit_to)
                shown = re.search(r"[\d.]+", str(value)).group(0)
                if Decimal(shown) != expected:
                    errors.append(
                        {"where": where, "error": f"CONVERSION_MISMATCH {value} != {expected}"}
                    )
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                text = " ".join(c["quote"] for c in cites) + " " + str(fact.get("orig", ""))
                plain = re.sub(r"(?<=\d),(?=\d{3})", "", text)
                if str(value).rstrip("0").rstrip(".") not in plain and str(value) not in plain:
                    errors.append({"where": where, "error": f"VALUE_NOT_IN_QUOTES {value}"})
            if fact["key"] in RANGES and isinstance(value, (int, float)):
                low, high = RANGES[fact["key"]]
                if not low <= value <= high:
                    errors.append(
                        {"where": where, "error": f"OUT_OF_RANGE {value} not in {low}-{high}"}
                    )
            years = fact["years"]
            if not (2014 <= years[0] <= years[1] <= 2026):
                errors.append({"where": where, "error": f"YEARS_OUTSIDE_SCOPE {years}"})
            gen_row = next(g for g in generations if g["code"] == gen)
            if not (gen_row["start_year"] <= years[0] and years[1] <= gen_row["end_year"]):
                errors.append({"where": where, "error": f"YEARS_OUTSIDE_GENERATION {years}"})
            applicability = dict(fact.get("app", {}))
            if fact["level"] == "GENERATION" and "powertrain" not in applicability:
                scopes = {sources.powertrain_scope(c["source"]) for c in cites}
                if None not in scopes and len(scopes) == 1:
                    applicability["powertrain"] = scopes.pop()
            tiers = {c["tier"] for c in cites}
            publishers = {c["publisher"] for c in cites}
            if "A" in tiers or len(publishers) >= 2:
                display, confidence = "FACT", "HIGH"
            elif tiers == {"C"}:
                display, confidence = "OWNER_REPORTS", "LOW"
            else:
                display, confidence = "SECONDARY_NOTE", "MEDIUM"
            record = {
                "id": f"{line}-{gen}-{index}",
                "generation": gen,
                "key": fact["key"],
                "level": fact["level"],
                "engine": fact.get("engine"),
                "gen_bound": fact.get("gen_bound", fact["level"] != "ENGINE"),
                "years": years,
                "value": value,
                "unit": fact.get("unit"),
                "original": fact.get("orig"),
                "applicability": applicability,
                "note": fact.get("note"),
                "cites": cites,
                "display_level": display,
                "confidence": confidence,
                "primary_source": sorted(cites, key=lambda c: (c["tier"], c["source"]))[0][
                    "source"
                ],
            }
            facts.append(record)
            if fact.get("conflict_with"):
                conflict_cites = resolve(fact.get("conflict_cites", []), where + " conflict")
                conflicts.append(
                    {
                        "fact_id": record["id"],
                        "key": fact["key"],
                        "generation": gen,
                        "years": years,
                        "kept_value": value,
                        "kept_from": record["primary_source"],
                        "other_value": fact.get("conflict_value"),
                        "other_sources": [c["source"] for c in conflict_cites],
                        "resolution": fact["conflict_with"],
                    }
                )
                if conflict_cites and fact.get("conflict_value") is not None:
                    facts.append(
                        {
                            **record,
                            "id": record["id"] + "-conflict",
                            "value": fact["conflict_value"],
                            "cites": conflict_cites,
                            "display_level": "HIDDEN_CONFLICT",
                            "confidence": "LOW",
                            "primary_source": conflict_cites[0]["source"],
                            "note": "Conflicting value kept as evidence only: "
                            + fact["conflict_with"],
                        }
                    )

    scopes = Counter(
        json.dumps(
            [
                f["generation"],
                f["level"],
                f.get("engine"),
                f["key"],
                f["years"],
                f.get("applicability") or {},
                f["display_level"] == "HIDDEN_CONFLICT",
            ],
            sort_keys=True,
        )
        for f in facts
    )
    for scope, count in scopes.items():
        if count > 1:
            errors.append({"where": scope, "error": f"DUPLICATE_FACT_SCOPE x{count}"})
    for doc in authored:
        for rule in doc.get("engine_rules", []):
            if rule.get("engine"):
                resolve(rule.get("cites", []), f"engine_rule {doc['generation']} {rule['engine']}")
    configurations = build_configurations(sources, authored, generations, errors, gaps)
    recalls = build_recalls(sources, generations, line)
    patterns = build_complaint_patterns(sources, generations)
    symptom_patterns = build_symptom_patterns(sources, generations)
    issues, tsbs = build_issues(staging_dir, sources, recalls, symptom_patterns, errors)
    output = {
        "make": make.title(),
        "line": LINE_NAMES[line][0],
        "market": MARKET,
        "sources": sources.items,
        "generations": generations,
        "configurations": configurations,
        "facts": facts,
        "recalls": recalls,
        "complaint_patterns": patterns,
        "symptom_patterns": symptom_patterns,
        "issues": issues,
        "tsbs": tsbs,
        "conflicts": conflicts,
        "gaps": gaps,
        "errors": errors,
        "counts": {
            "facts": len(facts),
            "configurations": len(configurations),
            "recalls": len(recalls),
            "complaint_patterns": len(patterns),
            "symptom_patterns": len(symptom_patterns),
            "issues": len(issues),
            "tsbs": len(tsbs),
            "conflicts": len(conflicts),
            "errors": len(errors),
            "display_levels": dict(Counter(f["display_level"] for f in facts)),
        },
    }
    (staging_dir / "staging.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    write_csv(staging_dir / "conflicts.csv", conflicts)
    write_csv(staging_dir / "gaps.csv", gaps)
    print(json.dumps(output["counts"], ensure_ascii=False))
    for error in errors[:60]:
        print("ERROR", json.dumps(error, ensure_ascii=False))
    return 1 if errors else 0


def write_csv(path: Path, rows: list[dict]):
    keys = sorted({k for r in rows for k in r}) or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                    for k, v in row.items()
                }
            )


def build_configurations(sources, authored, generations, errors, gaps):
    """US configurations from the EPA dataset; engine family keys only from authored rules."""
    item = sources.items["epa"]
    archive = zipfile.ZipFile(ROOT / item["path"])
    with archive.open(archive.namelist()[0]) as handle:
        rows = [
            r
            for r in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8"))
            if r["make"] == "Toyota"
            and r["model"].startswith(LINE_NAMES[sources.line][0])
            and 2014 <= int(r["year"]) <= 2026
        ]
    rules = [
        rule | {"generation": doc["generation"]}
        for doc in authored
        for rule in doc.get("engine_rules", [])
    ]
    trans_rules = [
        rule | {"generation": doc["generation"]}
        for doc in authored
        for rule in doc.get("transmission_rules", [])
    ]
    groups = defaultdict(list)
    for r in rows:
        hybrid = r["atvType"] == "Hybrid"
        drive = {"Front-Wheel Drive": "FWD", "All-Wheel Drive": "AWD"}.get(r["drive"], r["drive"])
        key = (int(r["year"]), r["displ"], int(r["cylinders"]), hybrid, r["trany"], drive)
        groups[key].append(r)
    configs = []
    for (year, displ, cylinders, hybrid, trany, drive), members in sorted(groups.items()):
        gen = generation_for(year, generations)
        rule = next(
            (
                x
                for x in rules
                if x["generation"] == gen
                and x["years"][0] <= year <= x["years"][1]
                and Decimal(str(x["displ"])) == Decimal(displ)
                and x["cylinders"] == cylinders
                and x["hybrid"] == hybrid
            ),
            None,
        )
        trule = next(
            (
                x
                for x in trans_rules
                if x["generation"] == gen
                and x["years"][0] <= year <= x["years"][1]
                and x["epa_trany"] == trany
                and x.get("drive") in (None, drive)
                and x["hybrid"] == hybrid
            ),
            None,
        )
        powertrain = "HEV" if hybrid else "ICE"
        trans_slug = slug(trany.replace("Automatic", "a"))
        config_key = f"toyota-{slug(LINE_NAMES[sources.line][0])}-us-{year}-{displ}l-{cylinders}cyl-{powertrain.lower()}-{trans_slug}-{drive.lower()}"
        if gen is None:
            errors.append({"where": config_key, "error": "NO_GENERATION_FOR_YEAR"})
        if rule is None:
            gaps.append(
                {
                    "scope": config_key,
                    "field": "engine_family_key",
                    "reason": "no authored engine rule for this generation/displacement",
                }
            )
        elif rule.get("engine") is None:
            gaps.append(
                {
                    "scope": config_key,
                    "field": "engine_family_key",
                    "reason": rule.get("note", "engine code not found in opened sources"),
                }
            )
        aspiration = (
            "NATURALLY_ASPIRATED"
            if not any(m["tCharger"].strip() or m["sCharger"].strip() for m in members)
            else None
        )
        configs.append(
            {
                "configuration_key": config_key,
                "year": year,
                "generation": gen,
                "engine_family_key": rule.get("engine") if rule else None,
                "transmission_key": trule.get("transmission") if trule else None,
                "powertrain": powertrain,
                "drivetrain": drive,
                "epa_trany": trany,
                "displacement_l": displ,
                "cylinders": cylinders,
                "aspiration": aspiration,
                "epa_vehicles": [
                    {
                        "epa_id": m["id"],
                        "epa_model": m["model"],
                        "city_mpg": int(m["city08"]),
                        "highway_mpg": int(m["highway08"]),
                        "combined_mpg": int(m["comb08"]),
                        "combined_l_100km": str(convert(m["comb08"], "mpg", "L/100km")),
                        "fuel_type": m["fuelType1"],
                        "eng_dscr": m["eng_dscr"],
                    }
                    for m in sorted(members, key=lambda m: m["id"])
                ],
                "engine_rule_cites": rule.get("cites", []) if rule else [],
            }
        )
    return configs


def build_recalls(sources, generations, line):
    campaigns = {}
    for key, item in sorted(sources.items.items()):
        if not key.startswith("nhtsa-recalls-"):
            continue
        data = json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
        for r in data.get("results", []):
            number = r["NHTSACampaignNumber"]
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
                    "model_years": [],
                    "sources": [],
                },
            )
            entry["model_years"].append(int(r["ModelYear"]))
            entry["sources"].append(key)
    recalls = []
    for entry in campaigns.values():
        years = sorted(set(entry["model_years"]))
        by_gen = defaultdict(list)
        for year in years:
            by_gen[generation_for(year, generations)].append(year)
        for gen, gen_years in by_gen.items():
            recalls.append(
                {
                    **entry,
                    "generation": gen,
                    "model_years": gen_years,
                    "years": [min(gen_years), max(gen_years)],
                }
            )
    return sorted(recalls, key=lambda r: (r["years"][0], r["campaign_number"]))


def build_symptom_patterns(sources, generations):
    counts = defaultdict(lambda: {"by_year": Counter(), "odi": []})
    for key, item in sorted(sources.items.items()):
        if not key.startswith("nhtsa-complaints-"):
            continue
        year = item["model_year"]
        gen = generation_for(year, generations)
        data = json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
        for r in data.get("results", []):
            text = (r.get("summary") or "").upper()
            for name, pattern in SYMPTOM_PATTERNS.items():
                if re.search(pattern, text):
                    bucket = counts[f"{gen}|{name}"]
                    bucket["by_year"][year] += 1
                    if len(bucket["odi"]) < 25:
                        bucket["odi"].append(r.get("odiNumber"))
    return {
        key: {
            "key": key,
            "count": sum(v["by_year"].values()),
            "by_year": dict(sorted(v["by_year"].items())),
            "sample_odi": v["odi"],
            "above_threshold": sum(v["by_year"].values()) >= COMPLAINT_PATTERN_THRESHOLD,
            "engine_specific": False,
        }
        for key, v in counts.items()
    }


def build_issues(staging_dir, sources, recalls, symptom_patterns, errors):
    path = staging_dir / "authored_issues.json"
    if not path.exists():
        return [], []
    issues = json.loads(path.read_text(encoding="utf-8"))["issues"]
    recall_numbers = {r["campaign_number"] for r in recalls}
    tsb_rows = {r["id"]: r for r in mfrcomms_rows(sources)}
    used_tsbs = {}
    for issue in issues:
        ev = issue["evidence"]
        for number in ev.get("recalls", []):
            if number not in recall_numbers:
                errors.append({"where": issue["id"], "error": f"UNKNOWN_RECALL {number}"})
        for tsb in ev.get("tsbs", []):
            if tsb not in tsb_rows:
                errors.append({"where": issue["id"], "error": f"UNKNOWN_TSB {tsb}"})
            else:
                used_tsbs[tsb] = tsb_rows[tsb]
        for key in ev.get("complaint_patterns", []):
            if key not in symptom_patterns:
                errors.append({"where": issue["id"], "error": f"UNKNOWN_COMPLAINT_PATTERN {key}"})
        # The complaint threshold is evaluated inside the issue's own model years.
        low, high = issue["years"]
        in_years = [
            sum(
                n
                for year, n in symptom_patterns.get(k, {}).get("by_year", {}).items()
                if low <= int(year) <= high
            )
            for k in ev.get("complaint_patterns", [])
        ]
        issue["complaints_in_years"] = in_years
        pattern = any(n >= COMPLAINT_PATTERN_THRESHOLD for n in in_years)
        tsb = bool(ev.get("tsbs"))
        expected = "COMMON" if pattern and tsb else "OCCASIONAL" if pattern or tsb else "RARE"
        if issue["probability"] != expected:
            errors.append(
                {
                    "where": issue["id"],
                    "error": f"PROBABILITY_RULE {issue['probability']} != {expected}",
                }
            )
        if issue["severity"] not in {"LOW", "MEDIUM", "HIGH"}:
            errors.append({"where": issue["id"], "error": "SEVERITY_VOCAB"})
        if issue["probability"] == "RARE" and not ev.get("recalls"):
            errors.append({"where": issue["id"], "error": "RARE_REQUIRES_RECALL"})
    return issues, list(used_tsbs.values())


def build_complaint_patterns(sources, generations):
    """Count NHTSA complaints per generation and NHTSA component (one complaint, several components)."""
    counts = defaultdict(lambda: {"count": 0, "odi": [], "years": Counter()})
    for key, item in sorted(sources.items.items()):
        if not key.startswith("nhtsa-complaints-"):
            continue
        data = json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
        year = item["model_year"]
        gen = generation_for(year, generations)
        for r in data.get("results", []):
            for component in {
                c.strip() for c in (r.get("components") or "").split(",") if c.strip()
            }:
                bucket = counts[(gen, component)]
                bucket["count"] += 1
                bucket["years"][year] += 1
                if len(bucket["odi"]) < 25:
                    bucket["odi"].append(r.get("odiNumber"))
    patterns = []
    for (gen, component), bucket in sorted(
        counts.items(), key=lambda kv: (-kv[1]["count"], kv[0][1])
    ):
        patterns.append(
            {
                "generation": gen,
                "component": component,
                "count": bucket["count"],
                "by_year": dict(sorted(bucket["years"].items())),
                "sample_odi": bucket["odi"],
                "above_threshold": bucket["count"] >= COMPLAINT_PATTERN_THRESHOLD,
            }
        )
    return patterns


def probe(make: str, line: str, quotes_file: str, pattern: str) -> int:
    """Report which sources (keys matching `pattern`) contain each quote of a JSON list."""
    sources = Sources(make, line)
    keys = sorted(k for k in sources.items if re.search(pattern, k))
    for quote in json.loads(Path(quotes_file).read_text(encoding="utf-8")):
        found = []
        for key in keys:
            pages, problem = sources.locate(key, quote)
            if not problem:
                found.append(f"{key}:{','.join(map(str, pages or []))}")
        print(f"{quote!r} -> {' '.join(found) if found else 'NOT FOUND'}")
    return 0


if __name__ == "__main__":
    if sys.argv[1] == "probe":
        sys.exit(probe(*sys.argv[2:6]))
    sys.exit(build(sys.argv[1], sys.argv[2]))
