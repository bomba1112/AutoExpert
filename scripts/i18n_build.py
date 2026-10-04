"""Assemble and check the Russian / Azerbaijani translations of buyer-facing texts.

Inputs (data_work/_shared/i18n/):
  sources.json        texts to translate (scripts/i18n_collect.py)
  glossary.json       the single glossary of technical terms (version, terms per kind)
  llm/*.json          free-text translations from translation agents: [{kind, hash, ru, az}]
and scripts/i18n_templates.py (hand translations and sentence templates).

Order per text: hand translation -> sentence template -> title template (part from the
glossary) -> glossary entry of the kind -> topic composed from glossary parts -> agent
translation. Every result is checked:
  - every number, campaign / bulletin number, code and URL of the English text is present;
  - Russian: no Latin word left that is not a name, an abbreviation or a code of the source;
  - Azerbaijani: no English function word, and few English content words copied over;
  - glossary terms found in the English text appear in the translation (stem check, warning).
Output: translations.json (passed), missing.json (no translation yet), failed.json (checks).

  .venv/Scripts/python.exe scripts/i18n_build.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "data_work" / "_shared" / "i18n"
sys.path.insert(0, str(ROOT / "scripts"))
from i18n_templates import MANUAL, TEMPLATES, TITLE_TEMPLATES  # noqa: E402

TOKEN = re.compile(r"[A-Za-z][A-Za-z'&.-]*")
KEEP = re.compile(r"\b(?:\d{2}V\d{3}\w{3}|[A-Z0-9]*\d[A-Z0-9/.-]*|https?://\S+|[a-z]+\.(?:gov|com|org)\S*)\b")
URL = re.compile(r"https?://\S+|\b[a-z0-9-]+\.(?:gov|com|org)(?:/\S*)?", re.I)
# abbreviations the glossary adds next to a translated name ("антиблокировочная система (ABS)")
GLOSSARY_ABBREVIATIONS = {"ABS", "ESC", "TPMS", "ADAS", "SRS", "FMVSS", "VIN", "LED", "HVAC", "EVAP", "ECM", "PCM", "TCM", "OCS",
                          "ECU", "TECM", "BCM", "BMS", "BECM", "HPCU", "EGR", "PRNDL", "CVT", "DCT", "DC", "DOT", "HEPA", "ISOFIX",
                          "LATCH", "NHTSA", "TSB", "EPS", "OEM", "USB", "GPS", "OTA", "SUV", "EV", "HV", "PHEV", "HEV", "AWD", "FWD",
                          "RWD", "A/C", "ACC", "AEB", "FCW", "LDW", "BSM", "RCTA", "API", "SAE", "ILSAC", "ACEA", "CAN", "LIN", "AT", "MT"}
EN_FUNCTION = {"the", "and", "with", "when", "may", "will", "which", "that", "this", "these", "from", "into", "while",
               "vehicle", "vehicles", "certain", "could", "should", "would", "might", "recalling", "dealers", "owners"}


def lower_first(text: str) -> str:
    """Lower-case start after a colon ("Подушки безопасности: датчики"), abbreviations kept."""
    first = text.split(" ")[0] if text else ""
    if not text or first[:2].isupper():
        return text
    # Azerbaijani dotted / dotless i: "İşçi" -> "işçi", "Ilıq" -> "ılıq" (str.lower gives "i̇")
    head = {"İ": "i", "I": "ı"}.get(text[0], text[0].lower())
    return head + text[1:]


def words(text: str) -> list[str]:
    return TOKEN.findall(text)


def kept_tokens(text: str) -> set[str]:
    return {m.group(0).rstrip(".,;:)") for m in KEEP.finditer(text)}


def check(source: str, ru: str, az: str, glossary_general: dict) -> list[str]:
    problems = []
    for token in kept_tokens(source):
        for lang, out in (("ru", ru), ("az", az)):
            # a code is carried over as printed; a value with a unit ("12V", "48V") may take the
            # translated unit ("12 В"), so its digits are what must survive
            # numbers with a unit, range or slash ("12V", "25-50", "16/17-", "6-") may be written
            # with the translated unit or an en dash; campaign numbers and part codes stay exact
            digits_only = re.fullmatch(r"(?:\d+(?:[.,]\d+)?[A-Za-z]{0,3}[/\-–]?)+|\d+-[A-Za-z]+", token) is not None  # "4-WHEEL"
            if token not in out and not (digits_only and all(d in out for d in re.findall(r"\d+", token))):
                problems.append(f"{lang}: '{token}' of the source is missing")
    source_words = set(words(URL.sub(" ", source)))
    # "non-SRT" is one token of the source: its parts may stand alone in a translation ("кроме SRT")
    source_words |= {part for w in list(source_words) if "-" in w for part in w.split("-") if part}
    # Russian: a Latin word must be a name / abbreviation / code carried over from the source
    for w in words(URL.sub(" ", ru)):
        if w not in source_words and w.upper() not in GLOSSARY_ABBREVIATIONS and w.rstrip(".") not in GLOSSARY_ABBREVIATIONS:
            problems.append(f"ru: Latin word '{w}' not in the source")
        elif w.islower() and len(w) > 2 and w not in ("nhtsa.gov", "recalls"):
            problems.append(f"ru: untranslated '{w}'")
    lower_az = {w.lower() for w in words(URL.sub(" ", az))}
    # "may" is also the Azerbaijani name of May: "15 may 2016-cı il", "may 2016"
    az_dates = URL.sub(" ", az)
    if re.search(r"\b\d{1,2}\s+may\b|\bmay\s+\d{4}\b", az_dates, re.I) and not re.search(r"\bmay\s+(?!\d)[a-z]", re.sub(r"\b\d{1,2}\s+may\b|\bmay\s+\d{4}\b", "", az_dates, flags=re.I), re.I):
        lower_az.discard("may")
    leftovers = sorted(lower_az & EN_FUNCTION)
    if leftovers:
        problems.append(f"az: English words {leftovers}")
    content = {w.lower() for w in words(URL.sub(" ", source)) if w.islower() and len(w) >= 5}
    copied = content & lower_az
    if content and len(copied) / len(content) > 0.2:
        problems.append(f"az: English content words copied {sorted(copied)[:6]}")
    for lang, out in (("ru", ru), ("az", az)):
        if "̇" in out:
            problems.append(f"{lang}: combining dot above (a Turkish-style lower-cased İ)")
        if not out.strip():
            problems.append(f"{lang}: empty")
        elif len(out) < 0.4 * len(source) or len(out) > 3.0 * len(source) + 20:
            problems.append(f"{lang}: length {len(out)} against {len(source)}")
    return problems


def glossary_warnings(source: str, ru: str, az: str, general: dict) -> list[str]:
    out = []
    low = source.lower()
    for term, tr in general.items():
        if re.search(rf"\b{re.escape(term.lower())}\b", low):
            for lang, text in (("ru", ru), ("az", az)):
                stem = tr[lang].lower().split()[0][: max(4, int(len(tr[lang].split()[0]) * 0.6))]
                if stem not in text.lower():
                    out.append(f"{lang}: glossary term '{term}' -> '{tr[lang]}' not used")
    return out


def main() -> int:
    sources = json.loads((I18N / "sources.json").read_text(encoding="utf-8"))
    glossary = json.loads((I18N / "glossary.json").read_text(encoding="utf-8"))
    version = glossary["version"]
    terms = glossary["terms"]
    llm = {}
    for path in sorted((I18N / "llm").glob("*.json")):
        for entry in json.loads(path.read_text(encoding="utf-8")):
            llm[(entry["kind"], entry["hash"])] = entry

    def term(kind: str, text: str):
        entry = terms.get(kind, {}).get(text) or terms.get(kind, {}).get(text.upper())
        return (entry["ru"], entry["az"]) if entry else None

    def component(text: str):
        parts = [term("nhtsa_component_segment", seg.strip()) for seg in text.split(":") if seg.strip()]
        if not parts or None in parts:
            return None

        join = lambda i: ": ".join(p[i] if n == 0 else lower_first(p[i]) for n, p in enumerate(parts))  # noqa: E731
        return join(0), join(1)

    def topic(text: str):
        whole = term("issue_topic", text)
        if whole:
            return whole
        parts = [term("issue_topic_part", p.strip()) for p in text.split(" / ")]
        if None in parts:
            return None
        return " / ".join(p[0] for p in parts), " / ".join(p[1] for p in parts)

    def translate(kind: str, text: str):
        if text in MANUAL:
            return MANUAL[text][0], MANUAL[text][1], "manual"
        for pattern, ru, az in TEMPLATES:
            m = pattern.match(text)
            if m:
                return ru.format(**m.groupdict()), az.format(**m.groupdict()), "template"
        if kind == "issue_title":
            for pattern, part_kind, ru, az in TITLE_TEMPLATES:
                m = pattern.match(text)
                if not m:
                    continue
                part = m.group("part")
                tr = {"nhtsa_component": component, "issue_topic": topic,
                      "carcomplaints_problem": lambda p: term("carcomplaints_problem", p)}[part_kind](part)
                if tr:
                    values = {k: v for k, v in m.groupdict().items() if k != "part"}
                    return ru.format(part=lower_first(tr[0]), **values), az.format(part=lower_first(tr[1]), **values), "template"
                break
        if kind in ("issue_component", "recall_component"):
            tr = component(text)
            if tr:
                return tr[0], tr[1], "glossary"
        if kind == "issue_symptom":
            tr = topic(text)
            if tr:
                return tr[0], tr[1], "glossary"
        if kind.startswith("maintenance_"):
            tr = term(kind, text)
            if tr:
                return tr[0], tr[1], "glossary"
        entry = llm.get((kind, sources_hash[(kind, text)]))
        if entry:
            return entry["ru"], entry["az"], "llm"
        return None

    sources_hash = {(e["kind"], e["text"]): e["hash"] for e in sources}
    general = terms.get("general", {})
    passed, missing, failed = [], [], []
    warnings = Counter()
    for e in sources:
        result = translate(e["kind"], e["text"])
        if result is None:
            missing.append(e)
            continue
        ru, az, method = result
        problems = check(e["text"], ru, az, general)
        warn = glossary_warnings(e["text"], ru, az, general) if method == "llm" else []
        for w in warn:
            warnings[w.split("'")[1]] += 1
        record = {"kind": e["kind"], "hash": e["hash"], "text": e["text"], "ru": ru, "az": az, "method": method,
                  "glossary_version": version, "rows": e["rows"]}
        if problems:
            failed.append({**record, "problems": problems})
        else:
            passed.append({**record, "warnings": warn} if warn else record)
    (I18N / "translations.json").write_text(json.dumps(passed, ensure_ascii=False, indent=1), encoding="utf-8")
    (I18N / "missing.json").write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding="utf-8")
    (I18N / "failed.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1), encoding="utf-8")
    by = Counter((r["kind"], r["method"]) for r in passed)
    print("passed", len(passed), "missing", len(missing), "failed", len(failed))
    for (kind, method), n in sorted(by.items()):
        print(f"  {kind:24} {method:9} {n}")
    print("missing by kind", dict(Counter(e["kind"] for e in missing)))
    print("failed by kind", dict(Counter(e["kind"] for e in failed)))
    if warnings:
        print("glossary warnings (term: count)", warnings.most_common(10))
    return 0


if __name__ == "__main__":
    sys.exit(main())
