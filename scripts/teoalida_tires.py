"""Teoalida "TireSize" database: tire sizes by year, make, model and trim/package (next-stage
prompt A.4) -> field "tires", only US vehicles of our lines, MY2014–2026.

The model column carries make, designation and body ("BMW 320i xDrive Sedan", "Toyota Prius
Two"); the trim column is the package ("Base Model", "Sport Package"); the tire column lists the
sizes, ";"-separated (options and staggered front/rear). Sizes are normalised to "225/45R18"
(no "P", load index, speed rating, run-flat marks). Another nameplate of the same family
("Prius c", "Prius v", "Prius Prime", "Prius Plug-in") is not the line.

Accuracy (A.8): for each model year and designation, the official tire sizes (press
specifications) must all be among the sizes the database gives for that designation and year.

  .venv/Scripts/python.exe scripts/teoalida_tires.py [parse|check|stage|all]
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
from us_tech_lines import lines_for  # noqa: E402

SHEET, REQUIRED = "Tires by vehicle", ["Make", "Model", "Year", "Tire"]
PUBLISHER = "Teoalida - TireSize database (secondary; owner's sample)"
SIZE = re.compile(r"(\d{3})\s*/\s*(\d{2})\s*Z?R\s*-?\s*(\d{2})", re.I)


def sizes(text) -> list[str]:
    return [f"{a}/{b}R{c}" for a, b, c in SIZE.findall(str(text or ""))]


def line_for(make: str, model: str, year: int):
    """(line, designation) for a TireSize model name without the make prefix."""
    for line in lines_for(make, include_done=True):
        if not (line.years[0] <= year <= line.years[1]):
            continue
        if line.epa_exclude and re.search(line.epa_exclude, model, re.I):
            continue
        for base in (line.name, *line.epa_base):
            if model.lower().startswith(base.lower() + " ") or model.lower() == base.lower():
                rest = model[len(base):].strip()
                if re.fullmatch(r"[a-z]\b.*", rest):
                    break  # "Prius c", "Prius v": another nameplate
                return line, (rest or model)
        if line.epa_include != r".*" and re.search(line.epa_include, model):
            return line, model
    return None, None


def parse() -> dict:
    path = unique_file("tire_size")
    _, head, rows = read_table(path, SHEET, REQUIRED, valid=lambda d: isinstance(d.get("Year"), (int, float)))
    out, skipped = [], defaultdict(int)
    for r in rows:
        year = int(r["Year"])
        make = make_slug(r["Make"])
        if make is None or not (2014 <= year <= 2026):
            skipped["make not ours or year outside 2014-2026"] += 1
            continue
        model = re.sub(rf"^{re.escape(str(r['Make']))}\s+", "", str(r["Model"])).strip()
        line, designation = line_for(make, model, year)
        if line is None:
            skipped[f"{r['Make']} {model}: not one of our lines"] += 1
            continue
        found = sizes(r["Tire"])
        if not found:
            skipped["no tire size in the row"] += 1
            continue
        out.append({"row": r["_row"], "make": make, "line": line.slug, "year": year, "designation": designation,
                    "package": str(r.get("Trim") or "").strip() or None, "sizes": found, "original": str(r["Tire"])})
    data = {"source_file": path.name, "rows_read": len(rows), "records": out, "skipped": dict(skipped)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tires_us.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rows", len(rows), "ours", len(out), "skipped", dict(skipped))
    return data


def check() -> dict:
    from teoalida_accuracy import Tally, body_family, designation_fits, edition_fits, load_line, model_label, tokens, write_report

    data = json.loads((OUT / "tires_us.json").read_text(encoding="utf-8"))
    union = defaultdict(set)
    for rec in data["records"]:
        union[(rec["make"], rec["line"], rec["year"], rec["designation"])].update(rec["sizes"])
    tally = Tally("teoalida/tire_size")
    cache = {}
    for (make, line, year, designation), teo in sorted(union.items()):
        st = cache.setdefault((make, line), load_line(make, line))
        ignore = tokens(st.get("line") or "") | tokens(line.replace("-", " "))
        body = body_family(designation)
        officials = []
        for f in st["facts"]:
            if f["key"] != "tires" or f["display_level"] != "FACT" or not (f["years"][0] <= year <= f["years"][1]):
                continue
            app = f.get("applicability") or {}
            if not designation_fits(designation, model_label(app), ignore) or not edition_fits(designation, app.get("edition")):
                continue
            if body_family(" ".join(str(app.get(k) or "") for k in ("edition", "variant"))) != body:
                continue
            official = set(sizes(f["value"]))
            if official:
                officials.append((official, f["primary_source"], app.get("edition") or ""))
        where = f"{make}/{line} {year} {designation}"
        # agreement: every size the official page gives is among the database's sizes for
        # this designation and year (an agreeing official entry is reported as the same text)
        value = "; ".join(sorted(teo))
        tally.add("tires", value, [(value if o <= teo else "; ".join(sorted(o)), s, e) for o, s, e in officials], where)
    return write_report("tires", tally, {"records": len(data["records"])})


def stage() -> dict:
    from teoalida_common import clear_docs, write_doc, write_pagetext

    report = json.loads((OUT / "accuracy_tires.json").read_text(encoding="utf-8"))
    removed = clear_docs("tires")
    if not report["fields"].get("tires", {}).get("write"):
        out = {"documents": 0, "removed_previous": removed, "reason": report["fields"].get("tires", {}).get("verdict")}
        (OUT / "tires_stage.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("not staged:", out["reason"])
        return out
    data = json.loads((OUT / "tires_us.json").read_text(encoding="utf-8"))
    path = unique_file("tire_size")
    sha = write_pagetext(path, SHEET, REQUIRED)
    _, head, rows = read_table(path, SHEET, REQUIRED)
    by_row = {r["_row"]: r for r in rows}
    groups = defaultdict(list)
    for rec in data["records"]:
        groups[(rec["make"], rec["line"], rec["year"])].append(rec)
    written = 0
    for (make, line, year), recs in sorted(groups.items()):
        facts = [{"key": "tires", "value": "; ".join(rec["sizes"]), "unit": None, "page": rec["row"],
                  "quote": row_quote(by_row[rec["row"]], head, ["Model", "Year", "Trim", "Tire"]),
                  "row": f"{rec['designation']} — {rec['package']}", "label": "tires", "engine_text": None,
                  "variant": rec["designation"], "original": rec["original"],
                  **({"applicability_extra": {"package": rec["package"]}} if rec["package"] else {})}
                 for rec in recs]
        key = "teoalida-tires-" + hashlib.sha1(f"{make}|{line}|{year}".encode()).hexdigest()[:10]
        write_doc(make, "tires", key, [f"{make}/{line}"], [year], facts, path, sha,
                  f"Teoalida TireSize: {line} {year}", PUBLISHER, "2026-10-03")
        written += 1
    out = {"documents": written, "removed_previous": removed}
    (OUT / "tires_stage.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("staged documents", written)
    return out


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("parse", "all"):
        parse()
    if step in ("check", "all"):
        rep = check()
        for k, r in rep["fields"].items():
            print(f"{k}: compared {r['compared']}, agreed {r['agreed']} ({r['agreement']}), no official {r['no_official']} -> {r['verdict']}")
    if step in ("stage", "all"):
        stage()
