"""Tables for data_work/NEXT_STAGE_REPORT.md, computed from the files and the live database
(read only): Teoalida accuracy per source and field, Teoalida rows written per field, maintenance
items per make before / after stage B, database totals.

  .venv/Scripts/python.exe scripts/next_stage_report_tables.py > data_work/_next_stage/report_tables.md
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEO = ROOT / "data_work" / "_shared" / "teoalida"
SOURCES = {
    "accuracy_ravenol.json": "Ravenol (масла и жидкости)",
    "accuracy_ymmt.json": "Year-Make-Model-Trim-Specs (US)",
    "accuracy_tires.json": "TireSize",
    "accuracy_platforms_ymm.json": "Year-Make-Model (коды платформ)",
    "accuracy_platforms_car_models_list.json": "Car Models List (коды платформ)",
    "accuracy_tuning.json": "Tuning (только сравнение)",
}
VERDICT = {"written (SECONDARY_NOTE)": "записано (SECONDARY_NOTE)", "below 90% - not written": "ниже 90% — не записано",
           "not measurable (too few comparisons) - not written": "не измеримо (меньше 5 сравнений) — не записано"}


def pct(x) -> str:
    return "—" if x is None else f"{x * 100:.0f}%"


def accuracy() -> list[str]:
    out = ["| Источник | Поле | Сравнено | Совпало | Расходится | Нет официального | Совпадение | Решение |",
           "|---|---|---:|---:|---:|---:|---:|---|"]
    for name, title in SOURCES.items():
        data = json.loads((TEO / name).read_text(encoding="utf-8"))
        for field, v in (data.get("fields") or {}).items():
            if not v.get("compared") and not v.get("write") and field not in ("tires",):
                continue  # fields with nothing to compare are listed separately
            out.append(f"| {title} | {field} | {v['compared']} | {v['agreed']} | {v['differ']} | {v.get('no_official', 0)} | "
                       f"{pct(v.get('agreement'))} | {VERDICT.get(v['verdict'], v['verdict'])} |")
    return out


def unmeasurable() -> list[str]:
    out = []
    for name, title in SOURCES.items():
        data = json.loads((TEO / name).read_text(encoding="utf-8"))
        fields = [f for f, v in (data.get("fields") or {}).items() if not v.get("compared")]
        if fields:
            out.append(f"- {title}: {', '.join(fields)}")
    return out


def written(db) -> list[str]:
    counts = defaultdict(Counter)
    for fact_key, conditions in db.execute(
            "select fact_key, conditions from technical_evidence where scope_level is not null and conditions like '%teoalida%'"):
        cond = json.loads(conditions or "{}")
        sources = {c.get("source", "") for c in cond.get("cites", [])}
        for s in sources:
            if s.startswith("teoalida"):
                counts[s.split("-")[1] if "-" in s else s][fact_key] += 1
    out = ["| Файл Teoalida (ключ источника) | Поле | Строк technical_evidence с цитатой |", "|---|---|---:|"]
    for src, c in sorted(counts.items()):
        for k, n in c.most_common():
            out.append(f"| {src} | {k} | {n} |")
    return out


def maintenance(db) -> list[str]:
    before = json.loads((ROOT / "data_work" / "_shared" / "maintenance_counts_before.json").read_text(encoding="utf-8"))["counts"]
    after = dict(db.execute("select m.name, count(*) from maintenance_schedule_items i join vehicle_makes m on m.id=i.make_id group by 1"))
    systems = defaultdict(Counter)
    for make, system, display in db.execute(
            "select m.name, i.schedule_system, i.display_level from maintenance_schedule_items i join vehicle_makes m on m.id=i.make_id"):
        systems[make][f"{system}/{display}"] += 1
    makes = ["Toyota", "Lexus", "BMW", "Chevrolet", "Ford", "Honda", "Nissan", "Land Rover", "Infiniti", "Audi", "Volkswagen",
             "Tesla", "Hyundai", "Kia", "Mercedes-Benz"]
    out = ["| Марка | До | После | Система / уровень показа |", "|---|---:|---:|---|"]
    for make in makes:
        detail = ", ".join(f"{k} {n}" for k, n in sorted(systems[make].items()))
        out.append(f"| {make} | {before.get(make, 0)} | {after.get(make, 0)} | {detail or '—'} |")
    out.append(f"| **Всего** | **{sum(before.values())}** | **{sum(after.values())}** | |")
    return out


def totals(db) -> list[str]:
    rows = []
    for table in ("technical_evidence", "known_issues", "maintenance_schedule_items", "source_records", "raw_documents"):
        rows.append(f"| {table} | {db.execute(f'select count(*) from {table}').fetchone()[0]:,} |".replace(",", " "))
    return ["| Таблица | Строк (live) |", "|---|---:|", *rows]


def main() -> int:
    db = sqlite3.connect((ROOT / "autoexpert.db").resolve().as_uri() + "?mode=ro", uri=True)
    sections = [("Точность Teoalida", accuracy()), ("Поля без пересечения с официальными данными", unmeasurable()),
                ("Записано из Teoalida", written(db)), ("ТО по маркам", maintenance(db)), ("Итоги базы", totals(db))]
    for title, lines in sections:
        print(f"### {title}\n")
        print("\n".join(lines))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
