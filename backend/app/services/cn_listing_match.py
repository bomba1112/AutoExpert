"""Match a turbo.az listing to a configuration of the Chinese catalogue (market CN).

Owner rules (2026-10-04):
  - the traction battery (kWh) is the main fingerprint: a seller value fits an official one
    within max(0.15 kWh, 1 %) (rounding 18.32 -> 18.3, 15.87 -> 15.9);
  - power: the listing's horsepower is metric (a.g. = PS); kW = hp / 1.36 must be within 3 % of
    one official power of the configuration — traction motors, engine, system or engine +
    motors (the catalogue fingerprint is one of these). When the battery fits but the power
    does not, the configuration stays (sellers write 331 or 925 a.g.); the difference is
    reported as a conflict, not as a reason to reject;
  - model year ±1: turbo.az's year is the production / registration year, a 年款 is the model
    year; the configurations of the listed year rank first;
  - without a battery (ICE, or a seller who omits it) power, displacement and powertrain decide.
Seller values are never written to the catalogue; the result only names configurations.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.services import cn_catalog

HP_PER_KW = Decimal("1.36")
POWER_TOLERANCE = Decimal("0.03")
BATTERY_ABS = Decimal("0.15")
BATTERY_REL = Decimal("0.01")
DISPLACEMENT_TOLERANCE = Decimal("0.06")
YEAR_WINDOW = 1
MODEL_MAP = Path(__file__).resolve().parents[3] / "data_work" / "cn" / "model_map.json"
# a seller's powertrain word -> catalogue powertrains it may stand for
POWERTRAIN_FITS = {
    "PHEV": {"PHEV", "EREV"},  # turbo.az lists range extenders as "Plug-in Hibrid"
    "HEV": {"HEV", "PHEV"},
    "BEV": {"BEV"},
    "ICE": {"ICE", "HEV"},
}
DRIVE_FITS = {"FWD": {"FWD"}, "RWD": {"RWD"}, "AWD_OR_4WD": {"AWD", "4WD"}}
CN_MARKET_WORDS = ("çin", "cin", "китай", "china", "chinese")
QUESTIONS = {
    "year": (
        "Какой модельный год (年款) указан в документах автомобиля?",
        "Avtomobilin sənədlərində hansı model ili (年款) göstərilib?",
        "Which model year (年款) is in the car's documents?",
    ),
    "battery": (
        "Какая ёмкость тяговой батареи указана (кВт·ч)?",
        "Dartı batareyasının tutumu nə qədər göstərilib (kVt·saat)?",
        "What traction battery capacity is stated (kWh)?",
    ),
    "power": (
        "Какая мощность указана в документах автомобиля?",
        "Avtomobilin sənədlərində hansı güc göstərilib?",
        "Which power is in the car's documents?",
    ),
    "drivetrain": ("Какой привод указан?", "Hansı ötürücü göstərilib?", "Which drive is stated?"),
}


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.cn_listing_match is not None:
        return bool(settings.cn_listing_match)
    return settings.environment != "production"


def compact(value) -> str:
    text = str(value or "").replace("İ", "I").replace("ı", "i")
    text = unicodedata.normalize("NFKD", text).casefold()
    return "".join(c for c in text if c.isalnum() and not unicodedata.combining(c))


def _number(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(",", "."))
    except Exception:  # noqa: BLE001
        return None


# ---- seller claims --------------------------------------------------------------------


@dataclass
class ListingFacts:
    make: str | None = None
    model: str | None = None
    year: int | None = None
    battery_kwh: Decimal | None = None
    power_hp: Decimal | None = None
    displacement_l: Decimal | None = None
    powertrain: str | None = None
    drivetrain: str | None = None
    market_cn: bool = False
    raw: dict = field(default_factory=dict)


def powertrain_word(text: str) -> str | None:
    t = str(text or "").casefold()
    if "plug" in t or "phev" in t or "erev" in t:
        return "PHEV"
    if "hibrid" in t or "гибрид" in t or "hybrid" in t:
        return "HEV"
    if "elektr" in t or "электр" in t or "electric" in t:
        return "BEV"
    if "benzin" in t or "бензин" in t or "gasoline" in t or "petrol" in t:
        return "ICE"
    return None


def parse_engine(text: str) -> dict:
    """turbo.az engine line: "1.5 L / 7.68 kWh / 197 a.g. / Plug-in Hibrid"."""
    text = str(text or "")
    out = {}
    if m := re.search(r"(\d{1,2}[.,]\d)\s*(?:L|л|litr)\b", text, re.IGNORECASE):
        out["displacement_l"] = _number(m[1])
    if m := re.search(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:kWh|kW·h|kVt·saat|кВт·ч|кВтч)", text, re.I):
        out["battery_kwh"] = _number(m[1])
    if m := re.search(r"(\d{2,4})\s*(?:a\.\s?g\.|а\.г\.|л\.\s?с\.|hp\b|PS\b|at gücü)", text, re.I):
        out["power_hp"] = _number(m[1])
    word = powertrain_word(text.rsplit("/", 1)[-1]) if "/" in text else None
    if word:
        out["powertrain"] = word
    return out


def facts_from_claims(claims: dict) -> ListingFacts:
    """claims: field -> ClaimDraft (or any object with raw_value / normalized_value)."""

    def raw(name):
        claim = claims.get(name)
        return claim.raw_value if claim is not None else None

    def normalized(name):
        claim = claims.get(name)
        return claim.normalized_value if claim is not None else None

    facts = ListingFacts(make=raw("make"), model=raw("model"))
    year = normalized("year")
    facts.year = year if isinstance(year, int) else None
    engine = parse_engine(raw("engine") or "")
    facts.battery_kwh = engine.get("battery_kwh")
    facts.power_hp = engine.get("power_hp")
    facts.displacement_l = engine.get("displacement_l")
    facts.powertrain = powertrain_word(raw("fuel") or "") or engine.get("powertrain")
    drive = normalized("drivetrain")
    facts.drivetrain = drive if drive in DRIVE_FITS else None
    market = compact(raw("market") or "")
    facts.market_cn = any(compact(word) in market for word in CN_MARKET_WORDS) if market else False
    facts.raw = {"engine": raw("engine"), "fuel": raw("fuel")}
    return facts


# ---- catalogue candidates -------------------------------------------------------------


@dataclass
class Candidate:
    variant: VehicleVariant
    key: str
    make: str
    model: str
    names: set[str]
    year: int
    powertrain: str | None
    batteries: list[Decimal]
    powers: dict[str, Decimal]
    displacement_l: Decimal | None
    drivetrain: str | None


def _model_map() -> dict:
    return json.loads(MODEL_MAP.read_text(encoding="utf-8"))


def candidates(db) -> list[Candidate]:
    out = []
    variants = db.scalars(
        select(VehicleVariant).where(
            VehicleVariant.market == cn_catalog.MARKET,
            VehicleVariant.catalog_key.like("cn:%"),
            VehicleVariant.is_demo.is_(False),
        )
    ).all()
    for variant in variants:
        cn = (variant.specifications or {}).get("cn") or {}
        model = variant.generation.model
        batteries = {
            Decimal(str(fp["battery_kwh"]))
            for fp in cn.get("fingerprints") or []
            if fp.get("battery_kwh") is not None
        }
        if variant.battery_kwh is not None:
            batteries.add(Decimal(str(variant.battery_kwh)))
        out.append(
            Candidate(
                variant=variant,
                key=variant.catalog_key,
                make=model.make.name,
                model=model.name,
                names={compact(model.name), *(compact(a) for a in cn.get("aliases") or [])},
                year=variant.year_from,
                powertrain=variant.powertrain_type,
                batteries=sorted(batteries),
                powers={k: Decimal(str(v)) for k, v in (cn.get("power_options_kw") or {}).items()},
                displacement_l=variant.displacement_l,
                drivetrain=variant.drivetrain,
            )
        )
    return out


def catalogue_make(name: str | None, rows: list[Candidate]) -> str | None:
    if not name:
        return None
    aliases = {compact(k): v for k, v in _model_map().get("make_aliases", {}).items()}
    key = compact(name)
    target = aliases.get(key)
    for row in rows:
        if compact(row.make) in (key, compact(target or "")):
            return row.make
    return None


def battery_fits(claimed: Decimal, official: Decimal) -> bool:
    return abs(claimed - official) <= max(BATTERY_ABS, official * BATTERY_REL)


def power_fit(claimed_hp: Decimal, powers: dict[str, Decimal]) -> str | None:
    kw = claimed_hp / HP_PER_KW
    best = None
    for name, value in powers.items():
        gap = abs(kw - value) / value
        if gap <= POWER_TOLERANCE and (best is None or gap < best[0]):
            best = (gap, name)
    return best[1] if best else None


# ---- matching ---------------------------------------------------------------------------


def _ps(kw: Decimal) -> str:
    return f"{(kw * HP_PER_KW).quantize(Decimal('1'))}"


def _candidate_view(c: Candidate, language: str, primary: bool) -> dict:
    v = c.variant
    return {
        "variant_id": v.id,
        "make": c.make,
        "model": c.model,
        "year": c.year,
        "configuration": cn_catalog.summary(v, language),
        "engine": v.engine,
        "transmission": v.transmission,
        "drivetrain": v.drivetrain,
        "body": None,
        "fuel": v.fuel,
        "market": cn_catalog.MARKET,
        "configuration_key": c.key,
        "powertrain_type": c.powertrain,
        "battery_kwh": float(v.battery_kwh) if v.battery_kwh is not None else None,
        "power_kw": float(v.power_kw) if v.power_kw is not None else None,
        "primary": primary,
    }


def _question(rows: list[Candidate], language: str) -> str | None:
    def differ(attr):
        return len({repr(getattr(c, attr)) for c in rows}) > 1

    for name, attr in (
        ("battery", "batteries"),
        ("power", "powers"),
        ("drivetrain", "drivetrain"),
        ("year", "year"),
    ):
        if differ(attr):
            return cn_catalog.tr(language, QUESTIONS[name])
    return cn_catalog.tr(language, QUESTIONS["year"])


def _year_conflict(facts: ListingFacts, named: list[Candidate], language: str) -> dict:
    """No configuration within ±1 of the listed year. When the battery (else the power) still
    points at configurations of the model, they are named with a year conflict instead of a
    silent "no match" (a seller's year can be wrong: Qiyuan A06 EREV listed as 2023)."""
    pool = named
    if facts.battery_kwh is not None:
        pool = [c for c in pool if any(battery_fits(facts.battery_kwh, b) for b in c.batteries)]
    elif facts.power_hp is not None:
        pool = [c for c in pool if power_fit(facts.power_hp, c.powers)]
    else:
        pool = []
    if not pool:
        return {"status": "NO_MATCH", "candidates": [], "question": None, "conflicts": []}
    ranked = sorted(pool, key=lambda c: (abs(c.year - facts.year), c.key))
    return {
        "status": "CLAIM_CONFLICT",
        "candidates": [_candidate_view(c, language, False) for c in ranked[:8]],
        "question": None,
        "conflicts": [
            {
                "field_name": "year",
                "claimed": str(facts.year),
                "catalog_values": sorted({str(c.year) for c in pool})[:8],
            }
        ],
    }


def match(facts: ListingFacts, rows: list[Candidate], language: str = "ru") -> dict:
    empty = {"status": "NO_MATCH", "candidates": [], "question": None, "conflicts": []}
    make = catalogue_make(facts.make, rows)
    if make is None or not facts.model:
        return {**empty, "status": "OUT_OF_PRODUCT_SCOPE"}
    model_key = compact(facts.model)
    named = [c for c in rows if c.make == make and model_key in c.names]
    if not named:
        # "Deepal S07" may come as make Deepal + model S07: the alias table covers it
        return {**empty, "status": "OUT_OF_PRODUCT_SCOPE"}
    pool = named
    if facts.year:
        pool = [c for c in pool if abs(c.year - facts.year) <= YEAR_WINDOW]
        if not pool:
            return _year_conflict(facts, named, language)
    conflicts = []

    def narrow(rows_, keep, field_name, claimed, catalog_values):
        kept = [c for c in rows_ if keep(c)]
        if kept:
            return kept, None
        return rows_, {
            "field_name": field_name,
            "claimed": claimed,
            "catalog_values": sorted(set(catalog_values))[:8],
        }

    if facts.powertrain:
        fits = POWERTRAIN_FITS[facts.powertrain]
        pool, conflict = narrow(
            pool,
            lambda c: c.powertrain in fits,
            "fuel",
            facts.raw.get("fuel") or facts.powertrain,
            [c.powertrain or "?" for c in pool],
        )
        if conflict:
            return {
                **empty,
                "status": "CLAIM_CONFLICT",
                "candidates": [_candidate_view(c, language, False) for c in pool[:8]],
                "conflicts": [conflict],
            }
    battery_decided = False
    if facts.battery_kwh is not None:
        kept = [c for c in pool if any(battery_fits(facts.battery_kwh, b) for b in c.batteries)]
        if not kept:
            values = [f"{b.normalize():f} kWh" for c in pool for b in c.batteries]
            return {
                **empty,
                "status": "CLAIM_CONFLICT",
                "candidates": [_candidate_view(c, language, False) for c in pool[:8]],
                "conflicts": [
                    {
                        "field_name": "battery_kwh",
                        "claimed": f"{facts.battery_kwh.normalize():f} kWh",
                        "catalog_values": sorted(set(values))[:8] or ["—"],
                    }
                ],
            }
        pool, battery_decided = kept, True
    if facts.power_hp is not None:
        kept = [c for c in pool if power_fit(facts.power_hp, c.powers)]
        if kept:
            pool = kept
        else:
            values = [
                f"{_ps(c.variant.power_kw)} a.g. ({c.variant.power_kw.normalize():f} kW)"
                for c in pool
                if c.variant.power_kw is not None
            ]
            conflict = {
                "field_name": "power",
                "claimed": f"{facts.power_hp.normalize():f} a.g.",
                "catalog_values": sorted(set(values))[:8],
            }
            if not battery_decided:
                return {
                    **empty,
                    "status": "CLAIM_CONFLICT",
                    "candidates": [_candidate_view(c, language, False) for c in pool[:8]],
                    "conflicts": [conflict],
                }
            conflicts.append(conflict)  # the battery decides; the seller's figure is reported
    if facts.displacement_l is not None:
        pool, _ = narrow(
            pool,
            lambda c: (
                c.displacement_l is None
                or abs(Decimal(str(c.displacement_l)) - facts.displacement_l)
                <= DISPLACEMENT_TOLERANCE
            ),
            "engine",
            "",
            [],
        )
    if facts.drivetrain:
        pool, _ = narrow(
            pool,
            lambda c: c.drivetrain is None or c.drivetrain in DRIVE_FITS[facts.drivetrain],
            "drivetrain",
            "",
            [],
        )

    def rank(c: Candidate) -> tuple:
        # the model named exactly as in the listing before a model reached through an alias
        # ("CS 75 Pro" before "CS 75"), then the listed year before its neighbours
        return (compact(c.model) != model_key, abs(c.year - facts.year) if facts.year else 0)

    ranked = sorted(pool, key=lambda c: (*rank(c), c.key))
    if len(ranked) == 1:
        return {
            "status": "EXACT_MATCH",
            "candidates": [_candidate_view(ranked[0], language, True)],
            "question": None,
            "conflicts": conflicts,
        }
    best = [c for c in ranked if rank(c) == rank(ranked[0])]
    primary = best[0] if len(best) == 1 else None
    return {
        "status": "MULTIPLE_CANDIDATES",
        "candidates": [_candidate_view(c, language, c is primary) for c in ranked[:8]],
        "question": _question(best if primary is None else ranked, language),
        "conflicts": conflicts,
    }


def applies(facts: ListingFacts, rows: list[Candidate]) -> bool:
    """CN path for makes only in the CN catalogue or a listing that names the Chinese market."""
    return catalogue_make(facts.make, rows) is not None


def try_match(db, claims: dict, language: str, *, us_result: dict | None = None) -> dict | None:
    """None: not a CN listing (the US matcher's answer stands). A make the US catalogue also has
    (Toyota) goes to the CN catalogue only when the US matcher found nothing."""
    if not enabled():
        return None
    facts = facts_from_claims(claims)
    known = _model_map()
    names = {compact(m) for m in known["makes"]} | {compact(a) for a in known["make_aliases"]}
    if compact(facts.make) not in names:
        return None  # a US/CA make: nothing to load
    rows = candidates(db)
    if not rows:
        return None
    if not applies(facts, rows):
        return None
    us_status = us_result["status"] if us_result is not None else "OUT_OF_PRODUCT_SCOPE"
    if us_status in ("EXACT_MATCH", "MULTIPLE_CANDIDATES") and not facts.market_cn:
        return None
    result = match(facts, rows, language)
    if us_status != "OUT_OF_PRODUCT_SCOPE" and result["status"] in (
        "OUT_OF_PRODUCT_SCOPE",
        "NO_MATCH",
    ):
        return None  # a make the US catalogue knows: nothing better than the US answer
    return result


def derived_claims(claims: dict) -> list[tuple[str, str, object, str, str, float]]:
    """Battery and power stated inside the turbo.az engine line, as separate seller claims:
    (field, raw, normalized, unit, locator, confidence)."""
    engine = claims.get("engine")
    if engine is None:
        return []
    parsed = parse_engine(engine.raw_value)
    out = []
    if parsed.get("battery_kwh") is not None:
        value = parsed["battery_kwh"]
        out.append(
            (
                "battery_kwh",
                f"{value.normalize():f} kWh",
                float(value),
                "kWh",
                engine.source_locator,
                engine.confidence,
            )
        )
    if parsed.get("power_hp") is not None:
        value = parsed["power_hp"]
        out.append(
            (
                "power_hp",
                f"{value.normalize():f} a.g.",
                float(value),
                "PS",
                engine.source_locator,
                engine.confidence,
            )
        )
    return out


# ---- regression against the catalogue's own listing links -------------------------------


def regression(db, turbo_specs: Path, staging: Path) -> dict:
    """The turbo.az listings the catalogue was built from: each must land on the record that
    lists it (turbo_listings or listing_values.url)."""
    from app.services.listing_intake import _claim

    listings = json.loads(Path(turbo_specs).read_text(encoding="utf-8"))
    expected: dict[str, set[str]] = {}
    alternatives: dict[str, set[str]] = {}
    records = {
        "cn:" + path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((Path(staging) / "catalog").glob("*.json"))
    }
    by_trim = {}
    for key, record in records.items():
        for trim in record.get("trims") or []:
            for trim_id in re.findall(r"sohu (\d+)", trim):
                by_trim.setdefault(trim_id, set()).add(key)
    for key, record in records.items():
        urls = set(record.get("turbo_listings") or [])
        if (record.get("listing_values") or {}).get("url"):
            urls.add(record["listing_values"]["url"])
        # a mismatch record names its closest official versions by sohu trim id
        named = (record.get("closest_official") or {}).get("trim") or ""
        others = {k for t in re.findall(r"\d{6}", named) for k in by_trim.get(t, ())} - {key}
        for url in urls:
            expected.setdefault(url, set()).add(key)
            alternatives.setdefault(url, set()).update(others)
    rows = candidates(db)
    results = []
    for item in listings:
        claims = {}
        for name, value in (
            ("make", item.get("make")),
            ("model", item.get("model")),
            ("year", item.get("year")),
            ("engine", item.get("engine_raw")),
            ("fuel", item.get("fuel")),
            ("transmission", item.get("gearbox")),
            ("drivetrain", item.get("drive")),
            ("market", item.get("market")),
        ):
            if value is not None:
                claim = _claim(name, value, f"turbo_specs:{name}", 0.9)
                if claim:
                    claims[claim.field_name] = claim
        result = match(facts_from_claims(claims), rows, "ru")
        keys = [c["configuration_key"] for c in result["candidates"]]
        primary = next((c["configuration_key"] for c in result["candidates"] if c["primary"]), None)
        want = expected.get(item["url"], set())
        alternative = alternatives.get(item["url"], set())
        matched = result["status"] in ("EXACT_MATCH", "MULTIPLE_CANDIDATES")
        if matched and (primary in want or (len(keys) == 1 and keys[0] in want)):
            outcome = "primary"
        elif want & set(keys):
            outcome = "candidate"
        elif alternative & set(keys):
            outcome = "closest_official_alternative"
        else:
            outcome = "miss"
        results.append(
            {
                "url": item["url"],
                "listing": f"{item['make']} {item['model']} {item['year']} "
                f"| {item.get('engine_raw')}",
                "expected": sorted(want),
                "catalogue_alternatives": sorted(alternative),
                "status": result["status"],
                "primary": primary,
                "candidates": keys,
                "conflicts": result["conflicts"],
                "outcome": outcome,
            }
        )
    summary = {}
    for r in results:
        summary[r["outcome"]] = summary.get(r["outcome"], 0) + 1
    return {"listings": len(results), "summary": summary, "results": results}
