"""Fuel shown in the app (owner rule 2026-10-04).

1. The manufacturer's octane from the US manuals (AKI scale) is shown as our AI grade by a fixed
   table (AKI_TO_AI), labelled "по требованию производителя".
2. A separate line is the Auto Expert recommendation for AZ / CIS fuel: for a direct-injection
   engine (EPA eng_dscr "SIDI", or a source naming GDI / direct injection) and for a turbo or a
   supercharger (EPA tCharger / sCharger) "не ниже АИ-95"; a manufacturer requirement above it
   (AI-95 / AI-98) raises the recommendation to it.
3. The fuel field is never empty for a gasoline car: without the manufacturer's octane only the
   recommendation is shown.
4. The recommendation is a rule of this module (a derived line), never a fact of the database,
   and it is never labelled as the manufacturer's requirement.

Rules of this module beyond the owner's text (stated so they can be changed in one place):
- an engine without direct injection and without boost, as the EPA record or the source shows it
  (a port injection named: MPI, SFI, EFI, multi-point), gets "не ниже АИ-92";
- an engine whose injection is not known gets "не ниже АИ-95" (the safe side);
- EPA "Premium" / "Midgrade" (the fuel the manufacturer states to the EPA) also raises the
  recommendation to AI-95, so the recommendation never reads lower than the fuel shown next to it;
- diesel, electric, hydrogen and natural-gas cars get no AI line; a flex-fuel car (E85) is a
  gasoline car; a record whose combustion type is unspecified but whose fuel is gasoline gets the line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# AKI (US pump octane, (R+M)/2) -> our AI grade: (ru, az, the grade a recommendation compares with)
AKI_TO_AI: dict[int, tuple[str, str, int]] = {
    87: ("АИ-92", "AI-92", 92),
    89: ("АИ-93/95", "AI-93/95", 95),
    91: ("АИ-95", "AI-95", 95),
    93: ("АИ-98", "AI-98", 98),
}
FLOOR_DIRECT_OR_BOOSTED = 95
FLOOR_PORT_NATURAL = 92
FLOOR_UNKNOWN = 95
AI_NAMES = {92: ("АИ-92", "AI-92"), 95: ("АИ-95", "AI-95"), 98: ("АИ-98", "AI-98")}

MAKER_LABEL = ("Бензин по требованию производителя", "İstehsalçının tələbi ilə benzin")
MAKER_BASIS = ("по требованию производителя", "istehsalçının tələbi ilə")
RECOMMENDATION_LABEL = ("Рекомендация Auto Expert", "Auto Expert tövsiyəsi")
RECOMMENDATION_BASIS = ("рекомендация для АЗ/СНГ", "AZ/MDB üçün tövsiyə")

DIRECT = re.compile(r"\bSIDI\b|\bT?-?GDI\b|\bGDi\b|direct[- ](?:fuel[- ])?injection|D-4S\b|\bDIG\b", re.I)
PORT = re.compile(r"\b(?:MPI|MPFI|SFI|EFI|PFI)\b|multi-?point|port (?:fuel )?injection|sequential (?:multiport )?fuel injection", re.I)
GASOLINE_POWERTRAINS = {"ICE", "HEV", "PHEV", "MHEV", "EREV", "COMBUSTION_UNSPECIFIED"}
ELECTRIC_POWERTRAINS = {"BEV", "FCEV"}


@dataclass
class Traits:
    """What the record says about the engine, with the words that show it."""

    fuel: str | None = None  # GASOLINE / DIESEL / ELECTRICITY / HYDROGEN
    powertrain: str | None = None
    direct_injection: bool | None = None  # None: not known
    direct_evidence: str | None = None
    boost: str | None = None  # TURBO / SUPERCHARGED
    port_named: bool = False
    epa_engine_known: bool = False  # an EPA record of the engine (no SIDI there = no direct injection)
    epa_grade: str | None = None  # EPA fuelType1: "Premium Gasoline", ...
    maker_aki: list[int] = field(default_factory=list)


def _value(fact) -> str:
    if isinstance(fact, dict):
        if fact.get("status") not in (None, "CONFIRMED"):
            return ""
        return str(fact.get("value") or "")
    return str(fact or "")


def _locator(fact) -> str:
    return str(fact.get("locator") or "") if isinstance(fact, dict) else ""


def traits_from_facts(facts: dict, extra_texts: list[str] = (), maker_aki: list[int] = (),
                      aspiration: str | None = None) -> Traits:
    """Traits from catalog facts ({key: {value, status, locator}}) plus texts of other sources
    (US technical evidence: injection, engine description) and the octane they state."""
    t = Traits()
    fuel = _value(facts.get("fuel")).upper()
    # a flex-fuel car (EPA "E85" next to gasoline) runs on gasoline as well
    t.fuel = "GASOLINE" if "GASOLINE" in fuel or fuel == "E85" else fuel or None
    t.powertrain = _value(facts.get("powertrain")).upper() or None
    grade = _value(facts.get("fuel_grade"))
    t.epa_grade = grade or None
    if t.fuel is None and re.search(r"gasoline|premium|regular|midgrade", grade, re.I):
        t.fuel = "GASOLINE"
    if t.fuel is None and re.search(r"diesel", grade, re.I):
        t.fuel = "DIESEL"
    description = facts.get("engine_description")
    epa_description = _value(description) if "eng_dscr" in _locator(description) else ""
    t.epa_engine_known = any("EPA vehicle" in _locator(f) for f in facts.values() if isinstance(f, dict))
    texts = [epa_description, _value(description), _value(facts.get("injection")), *extra_texts]
    for text in texts:
        if not text:
            continue
        hit = DIRECT.search(text)
        if hit:
            t.direct_injection, t.direct_evidence = True, hit.group(0)
            break
        if PORT.search(text):
            t.port_named = True
    boost = (aspiration or _value(facts.get("aspiration"))).upper()
    if "TURBO" in boost:
        t.boost = "TURBO"
    elif "SUPERCHARG" in boost:
        t.boost = "SUPERCHARGED"
    if t.direct_injection is None and (t.epa_engine_known or t.port_named):
        # EPA marks direct injection "SIDI" in eng_dscr: an EPA record without it, or a source
        # naming port injection, is an engine without direct injection
        t.direct_injection = False
    own = _value(facts.get("octane_aki"))
    t.maker_aki = sorted({int(v) for v in [*maker_aki, *([own] if own.isdigit() else [])]})
    return t


def _tr(language: str, pair) -> str:
    return pair[1] if language == "az" else pair[0]


def maker_value(aki: int, language: str) -> str:
    grade = AKI_TO_AI.get(aki)
    scale = ("по шкале США", "ABŞ şkalası ilə")
    if grade is None:
        return f"AKI {aki} ({_tr(language, scale)})"
    return f"{grade[1] if language == 'az' else grade[0]} (AKI {aki} {_tr(language, scale)})"


def recommendation(t: Traits) -> tuple[int, list[tuple[str, str]]] | None:
    """(AI grade, reasons) of the Auto Expert recommendation; None for diesel / electric cars."""
    if t.fuel not in (None, "GASOLINE") or t.powertrain in ELECTRIC_POWERTRAINS:
        return None
    if t.fuel is None and not t.maker_aki:
        return None  # nothing says the car runs on gasoline
    reasons = []
    if t.direct_injection:
        floor = FLOOR_DIRECT_OR_BOOSTED
        reasons.append((f"непосредственный впрыск ({t.direct_evidence})", f"birbaşa püskürtmə ({t.direct_evidence})"))
    if t.boost:
        floor = FLOOR_DIRECT_OR_BOOSTED
        reasons.append(("турбонаддув", "turbo") if t.boost == "TURBO" else ("механический нагнетатель", "mexaniki kompressor"))
    if not reasons:
        if t.direct_injection is False:
            floor = FLOOR_PORT_NATURAL
            reasons.append(("без непосредственного впрыска и наддува", "birbaşa püskürtmə və turbo olmadan"))
        else:
            floor = FLOOR_UNKNOWN
            reasons.append(("тип впрыска не подтверждён — с запасом", "püskürtmə növü təsdiqlənməyib — ehtiyatla"))
    maker = max((AKI_TO_AI[a][2] for a in t.maker_aki if a in AKI_TO_AI), default=None)
    if maker and maker > floor:
        floor = maker
        reasons.append(("требование производителя выше", "istehsalçının tələbi daha yüksəkdir"))
    if t.epa_grade and re.search(r"premium|midgrade", t.epa_grade, re.I) and floor < 95:
        floor = 95
        reasons.append(("EPA: Premium/Midgrade", "EPA: Premium/Midgrade"))
    return floor, reasons


def rows(t: Traits, language: str) -> list[dict]:
    """Display lines of the fuel section: the manufacturer's octane (one line per AKI value the
    record states) and the Auto Expert recommendation. kind tells them apart for the UI."""
    out = []
    for aki in t.maker_aki:
        out.append({"key": "fuel_octane_maker", "kind": "manufacturer", "label": _tr(language, MAKER_LABEL),
                    "value": maker_value(aki, language), "basis": _tr(language, MAKER_BASIS), "aki": aki})
    rec = recommendation(t)
    if rec:
        grade, reasons = rec
        name = AI_NAMES[grade][1 if language == "az" else 0]
        value = (f"ən azı {name}, {_tr(language, RECOMMENDATION_BASIS)}" if language == "az"
                 else f"не ниже {name}, {_tr(language, RECOMMENDATION_BASIS)}")
        out.append({"key": "fuel_recommendation", "kind": "recommendation", "label": _tr(language, RECOMMENDATION_LABEL),
                    "value": value, "basis": _tr(language, RECOMMENDATION_BASIS),
                    "reason": "; ".join(_tr(language, r) for r in reasons), "grade": grade})
    return out
