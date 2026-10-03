"""Teoalida "Year-Make-Model" and "Car Models List": platform codes / generation numbers
(next-stage prompt A.5).

- A platform code is a secondary fact at generation level (fills generations we only label
  "US2014-2015"; confirms F30, G30, JF …).
- Years (YMM per model year; the models list's "Model Years (US/Canada)") are used only to check
  our generation boundaries: a code change inside one of our generations, or the same codes on
  both sides of one of our boundaries, is logged; our boundaries are never changed.
- Accuracy (A.8): where our generation code is a chassis code (F30, G30, JF, TF/QF, 5N …), the
  database must give it for the same model year. A code is written for a generation only when the
  source passes and gives the same codes for every year of the generation it covers.
- "Car Nameplates" holds descriptions only (no code, no structured years): inventory only.

  .venv/Scripts/python.exe scripts/teoalida_platforms.py [parse|check|stage|all]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from teoalida_common import OUT, read_table, row_quote, unique_file  # noqa: E402
from teoalida_ymmt import make_slug  # noqa: E402
from us_tech_common import WORK  # noqa: E402
from us_tech_lines import lines_for  # noqa: E402

SOURCES = {
    "ymm": {"sheet": "DATABASE", "required": ["Year", "Make", "Model"], "code": "Platform code / generation",
            "quote": ["Year", "Make", "Model", "Platform code / generation"],
            "publisher": "Teoalida - Year-Make-Model database (secondary; owner's sample)"},
    "car_models_list": {"sheet": "Car models list WORLDWIDE", "required": ["Make", "Model"],
                        "code": "Platform / generation number",
                        "quote": ["Model", "Platform / generation number", "European / World classification", "Production years",
                                  "American classification", "Model Years (US/Canada)"],
                        "publisher": "Teoalida - Car Models List (secondary; owner's sample)"},
}
ROMAN = re.compile(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)(?:-.*)?$")


def norm_name(text: str) -> str:
    return " ".join(str(text).lower().replace("-", " ").split())


def lines_of(make: str, model: str) -> list:
    """Our lines a model cell names ("3-Series, M3" -> 3 Series and M3)."""
    # codes listed for several nameplates at once ("3-Series, M3": F30, F31, F80 / G20, G21)
    # cannot be told apart per nameplate: they are taken for the first one only (the M3's own
    # G80 is not in that cell)
    first = norm_name(str(model).split(",")[0])
    out = []
    for line in lines_for(make, include_done=True):
        # the line's own name ("X5 M" is not "X5"); "Optima / K5" names both
        if first in {norm_name(n) for n in (line.name, *line.name.split("/")) if n.strip()}:
            out.append(line)
    return out


def codes_of(text) -> list[str]:
    """"F30, F31, F80" / "4th gen YB/SC/FB/UC" -> codes (the generation ordinal is dropped)."""
    out = []
    for part in re.split(r"[,/]", str(text or "")):
        part = re.sub(r"^\s*\d+(?:st|nd|rd|th)\s+gen(?:eration)?\s*", "", part.strip(), flags=re.I).strip()
        if part and not re.fullmatch(r"[-?_ ]+", part):
            out.append(part)
    return out


def years_of(source: str, row: dict) -> list[int]:
    if source == "ymm":
        return [int(row["Year"])]
    m = re.search(r"MY\s*(\d{4})\s*-\s*(\d{4}|_+)", str(row.get("Model Years (US/Canada)") or ""))
    if not m or "?" in str(row.get("Model Years (US/Canada)")):
        return []
    end = int(m.group(2)) if m.group(2).isdigit() else 2026
    return list(range(int(m.group(1)), min(end, 2026) + 1))


def parse() -> dict:
    out = {}
    for source, cfg in SOURCES.items():
        path = unique_file(source)
        _, head, rows = read_table(path, cfg["sheet"], cfg["required"],
                                   valid=lambda d: str(d.get("Make")) not in ("Make", "") and isinstance(d.get("Model"), (str, int)))
        claims = []
        for r in rows:
            make = make_slug(r["Make"])
            if make is None:
                continue
            codes = codes_of(r.get(cfg["code"]))
            years = [y for y in years_of(source, r) if 2014 <= y <= 2026]
            if not codes or not years:
                continue
            for line in lines_of(make, r["Model"]):
                ys = [y for y in years if line.years[0] <= y <= line.years[1]]
                if ys:
                    claims.append({"row": r["_row"], "make": make, "line": line.slug, "years": ys, "codes": codes,
                                   "model": str(r["Model"])})
        out[source] = {"file": path.name, "claims": claims}
    (OUT / "platforms_us.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print({s: len(v["claims"]) for s, v in out.items()})
    return out


def by_year(claims: list) -> dict:
    """(make, line) -> year -> set of codes (two rows of one year, e.g. F30 and G20 in 2019,
    are both kept)."""
    out = defaultdict(lambda: defaultdict(set))
    for c in claims:
        for y in c["years"]:
            out[(c["make"], c["line"])][y].update(c["codes"])
    return out


def our_generations(make: str, line: str) -> list:
    path = WORK / make / "staging" / line / "staging.json"
    return json.loads(path.read_text(encoding="utf-8"))["generations"] if path.exists() else []


def chassis_parts(code: str) -> list[str]:
    """Our generation code as chassis codes, or [] when it is a label ("US2014-2015", "VII")."""
    if code.startswith("US") or ROMAN.match(code) or " " in code:
        return []
    return [p for p in code.split("/") if re.fullmatch(r"[A-Z0-9]{1,5}", p)]


def check() -> dict:
    from teoalida_accuracy import Tally, write_report

    data = json.loads((OUT / "platforms_us.json").read_text(encoding="utf-8"))
    reports, boundary = {}, []
    for source, block in data.items():
        tally = Tally(f"teoalida/{source}")
        for (make, line), years in sorted(by_year(block["claims"]).items()):
            gens = our_generations(make, line)
            for g in gens:
                parts = chassis_parts(g["code"])
                gyears = [y for y in range(g["start_year"], g["end_year"] + 1) if y in years]
                for y in gyears:
                    if parts:
                        hit = next((p for p in parts if p in years[y]), None)
                        tally.add("platform_code", hit or ", ".join(sorted(years[y])), [(hit or g["code"], "generation", g["code"])],
                                  f"{make}/{line} {y}")
                # boundary check: the database's codes inside one of our generations
                sets = [frozenset(years[y]) for y in gyears]
                common = frozenset.intersection(*sets) if sets else frozenset()
                if sets and not common:
                    boundary.append({"source": source, "line": f"{make}/{line}", "generation": g["code"],
                                     "years": {y: sorted(years[y]) for y in gyears},
                                     "finding": "the database changes platform code inside this generation"})
            for a, b in zip(gens, gens[1:]):
                ya, yb = a["end_year"], b["start_year"]
                if ya in years and yb in years and years[ya] == years[yb]:
                    boundary.append({"source": source, "line": f"{make}/{line}", "generation": f"{a['code']} | {b['code']}",
                                     "years": {ya: sorted(years[ya]), yb: sorted(years[yb])},
                                     "finding": "same platform codes on both sides of our generation boundary"})
        reports[source] = write_report(f"platforms_{source}", tally, {"records": len(block["claims"])})
    (OUT / "platforms_boundaries.json").write_text(json.dumps(boundary, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"reports": reports, "boundary_findings": len(boundary)}


def stage() -> dict:
    from teoalida_common import clear_docs, write_doc, write_pagetext

    data = json.loads((OUT / "platforms_us.json").read_text(encoding="utf-8"))
    removed = clear_docs("platforms")
    written, skipped = 0, []
    for source, block in data.items():
        report = json.loads((OUT / f"accuracy_platforms_{source}.json").read_text(encoding="utf-8"))
        if not report["fields"].get("platform_code", {}).get("write"):
            skipped.append({"source": source, "reason": report["fields"].get("platform_code", {}).get("verdict", "no comparison")})
            continue
        cfg = SOURCES[source]
        path = unique_file(source)
        sha = write_pagetext(path, cfg["sheet"], cfg["required"])
        _, head, rows = read_table(path, cfg["sheet"], cfg["required"])
        raw = {r["_row"]: r for r in rows}
        years_codes = by_year(block["claims"])
        for (make, line), years in sorted(years_codes.items()):
            for g in our_generations(make, line):
                gyears = [y for y in range(g["start_year"], g["end_year"] + 1) if y in years]
                if not gyears:
                    continue
                common = frozenset.intersection(*[frozenset(years[y]) for y in gyears])
                if not common:
                    skipped.append({"source": source, "line": f"{make}/{line}", "generation": g["code"],
                                    "reason": "the database gives different codes inside this generation"})
                    continue
                order = [c for cl in block["claims"] for c in cl["codes"]]
                value = ", ".join(sorted(common, key=order.index))
                rows_used = sorted({cl["row"] for cl in block["claims"] if cl["make"] == make and cl["line"] == line
                                    and set(cl["years"]) & set(gyears) and common & set(cl["codes"])})
                facts = [{"key": "platform_code", "value": value, "unit": None, "page": n,
                          "quote": row_quote(raw[n], head, cfg["quote"]), "row": f"{source} row {n}",
                          "label": "platform code", "engine_text": None} for n in rows_used]
                key = "teoalida-platforms-" + hashlib.sha1(f"{source}|{make}|{line}|{g['code']}".encode()).hexdigest()[:10]
                write_doc(make, "platforms", key, [f"{make}/{line}"], gyears, facts, path, sha,
                          f"Teoalida {source}: {line} {g['code']} platform code", cfg["publisher"], "2026-10-03")
                written += 1
    out = {"documents": written, "removed_previous": removed, "skipped": skipped}
    (OUT / "platforms_stage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("staged documents", written, "skipped", len(skipped))
    return out


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("parse", "all"):
        parse()
    if step in ("check", "all"):
        res = check()
        for source, rep in res["reports"].items():
            for k, r in rep["fields"].items():
                print(f"{source} {k}: compared {r['compared']}, agreed {r['agreed']} ({r['agreement']}) -> {r['verdict']}")
        print("boundary findings", res["boundary_findings"])
    if step in ("stage", "all"):
        stage()
