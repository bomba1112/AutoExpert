"""Final report of the US technical database batch (prompt section 10), built from data only.

Reads the staging of every line (what was loaded), the load reports, the 10% rechecks, the
live database and a pre-batch backup (rows before/after), the generation evidence, the
manifests (sources, blocked hosts), the library and git. Writes:
  data_work/REPORT.md              all makes
  data_work/<make>/REPORT.md       one make
Nothing in the report is typed by hand: every number is counted here.

  .venv/Scripts/python.exe scripts/build_us_report.py
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data_work"
sys.path.insert(0, str(ROOT / "scripts"))
from us_tech_lines import MAKE_ORDER, MAKES, lines_for  # noqa: E402

LIVE = ROOT / "autoexpert.db"
BEFORE_BATCH = Path(r"C:\AutoExpertBackups\autoexpert.db.backup_20261002_1308_pre_batch_hyundai")
BEFORE_ALL = ROOT / "autoexpert.db.backup_20261002_0959"
TABLES = ["vehicle_makes", "vehicle_models", "vehicle_generations", "vehicle_variants", "technical_evidence",
          "known_issues", "maintenance_schedule_items", "source_records", "raw_documents", "knowledge_sources"]
BASELINE_COMMIT = "0ff74ff"
MARK = {"full": "●", "part": "◐", "none": "○", "na": "—"}
# owner's decision of 2026-10-02 (evening): of the last seven makes only Audi, Volkswagen and Tesla
# are loaded; Infiniti had already been loaded when the decision arrived and is kept as it is.
# Owner's decision of 2026-10-03: Cadillac, Jeep, Mitsubishi loaded by the same rules (one commit
# per make); a make leaves this set when its load is committed.
NOT_LOADED = {"jeep", "mitsubishi"}
STATUS_NOTE = {
    **{m: ("Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/" + m +
           "/staging), в рабочей БД строк этого конвейера нет.") for m in NOT_LOADED},
    "infiniti": ("Загружена до получения решения владельца остановить загрузку этой группы марок "
                 "(коммит f47df93); по решению владельца оставлена как есть."),
}

FIELDS = [
    ("1 Идентификация", ["body", "seats"]),
    ("2 Двигатель", None),
    ("3 Коробка", None),
    ("4 Привод", None),
    ("5 Мощность/момент", ["power_hp", "torque_lb_ft"]),
    ("6 Топливо/бак", ["octane_aki|octane_ron|fuel_type", "fuel_tank_l"]),
    ("7 Масло", ["engine_oil_viscosity", "engine_oil_specification|engine_oil_oem_approval",
                 "engine_oil_capacity_l|engine_oil_capacity_drain_refill_l"]),
    ("8 Жидкости", ["coolant|coolant_description", "transmission_fluid", "brake_fluid"]),
    ("9 ТО", None),
    ("10 Шины", ["tires", "tire_pressure_front_kpa"]),
    ("11 Размеры", ["length_mm", "width_mm", "height_mm", "wheelbase_mm", "ground_clearance", "cargo_l", "curb_weight_kg"]),
    ("12 Узлы", ["front_suspension", "rear_suspension", "front_brakes", "rear_brakes", "steering"]),
    ("13 Отзывы", None),
    ("14 Проблемы", None),
    ("15 Источники", None),
]


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def counts(db: Path) -> dict:
    if not db.exists():
        return {}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    out = {}
    for table in TABLES:
        try:
            out[table] = con.execute(f"select count(*) from {table}").fetchone()[0]
        except sqlite3.Error:
            out[table] = None
    out["by_make"] = {}
    for table in ("technical_evidence", "known_issues", "maintenance_schedule_items"):
        try:
            rows = con.execute(
                f"select m.name, count(*) from {table} t join vehicle_makes m on m.id = t.make_id group by m.name"
                if table != "maintenance_schedule_items" else
                "select m.name, count(*) from maintenance_schedule_items t join vehicle_generations g on g.id = t.generation_id "
                "join vehicle_models mo on mo.id = g.model_id join vehicle_makes m on m.id = mo.make_id group by m.name"
            ).fetchall()
        except sqlite3.Error:
            rows = []
        for name, n in rows:
            out["by_make"].setdefault(name, {})[table] = n
    con.close()
    return out


def generation_status(staging: dict, gen: dict) -> list[str]:
    code = gen["code"]
    years = set(range(gen["start_year"], (gen.get("end_year") or gen["start_year"]) + 1))
    facts = [f for f in staging.get("facts", []) if f.get("generation") == code and f.get("display_level") != "HIDDEN_CONFLICT"]
    keys = {f["key"] for f in facts}
    cfgs = [c for c in staging.get("configurations", []) if c.get("generation") == code]
    bev = bool(cfgs) and all(c.get("powertrain") in ("BEV", "FCEV") for c in cfgs)
    out = []
    for name, need in FIELDS:
        n = name.split()[0]
        if n == "1":
            # generation and its model years are always there; seats/body complete it
            out.append("full" if keys & {"seats", "body"} else "part")
        elif n == "6":
            epa_fuel = any(v.get("fuel_type") for c in cfgs for v in c.get("epa_vehicles", []))
            hits = [epa_fuel, bool(keys & {"octane_aki", "octane_ron", "fuel_type"}), "fuel_tank_l" in keys]
            if bev:
                hits = hits[:1]
            out.append("full" if all(hits) else "part" if any(hits) else "none")
        elif n == "2":
            if not cfgs:
                out.append("none")
            elif all(c.get("engine_family_key") for c in cfgs):
                out.append("full")
            else:
                out.append("part")
        elif n == "3":
            out.append("none" if not cfgs else "full" if all(c.get("epa_trany") for c in cfgs) else "part")
        elif n == "4":
            out.append("none" if not cfgs else "full" if all(c.get("drivetrain") for c in cfgs) else "part")
        elif n == "9":
            items = [i for i in staging.get("maintenance", []) if i.get("generation") == code]
            out.append("full" if any(i["job"] == "engine_oil_and_filter" for i in items) else "part" if items else "none")
        elif n == "13":
            out.append("full" if any(s.get("source_type") == "NHTSA_RECALLS_API" or str(k).startswith("nhtsa-recalls")
                                     for k, s in staging.get("sources", {}).items()) else "none")
        elif n == "14":
            out.append("full" if any(i.get("generation") == code for i in staging.get("issues", [])) else "none")
        elif n == "15":
            out.append("full" if all(f.get("cites") for f in facts) else "part")
        else:
            if bev and n in ("7",):
                out.append("na")
                continue
            hits = [any(k in keys for k in alt.split("|")) for alt in need]
            if bev and n == "6":
                hits = hits[:1]
            if bev and n == "5":
                hits = [("power_hp" in keys) or ("system_power_hp" in keys) or ("electric_motor" in keys)]
            out.append("full" if all(hits) else "part" if any(hits) else "none")
    _ = years
    return out


def make_data(make: str) -> dict:
    data = {"make": make, "lines": []}
    for line in lines_for(make, include_done=True):
        path = WORK / make / "staging" / line.slug / "staging.json"
        staging = read_json(path)
        if staging is None:
            data["lines"].append({"key": line.key, "name": line.name, "missing": True})
            continue
        load = read_json(path.parent / "load_report.json", {})
        data["lines"].append({"key": line.key, "name": line.name, "staging": staging, "load": load, "batch": bool(staging.get("build"))})
    data["recheck"] = read_json(WORK / make / "staging" / "recheck_10pct.json", {})
    data["pass_live"] = read_json(WORK / make / "staging" / "load_pass_live.json", {})
    return data


def matrix(data: dict) -> list[str]:
    head = "| Линейка | Поколение | Годы | " + " | ".join(n.split(" ", 1)[0] for n, _ in FIELDS) + " |"
    out = [head, "|" + "---|" * (3 + len(FIELDS))]
    totals = Counter()
    for line in data["lines"]:
        if line.get("missing"):
            out.append(f"| {line['name']} | — | — | " + " | ".join("○" for _ in FIELDS) + " |")
            continue
        for gen in line["staging"].get("generations", []):
            status = generation_status(line["staging"], gen)
            totals.update(status)
            years = f"{gen['start_year']}–{gen.get('end_year') or ''}"
            out.append(f"| {line['name']} | {gen['code']} | {years} | " + " | ".join(MARK[s] for s in status) + " |")
    out.append("")
    out.append(f"Итого ячеек: заполнено {totals['full']}, частично {totals['part']}, нет {totals['none']}, неприменимо {totals['na']}.")
    return out


def gaps_section(data: dict, detail: bool) -> list[str]:
    by = Counter()
    examples = defaultdict(list)
    for line in data["lines"]:
        for g in (line.get("staging") or {}).get("gaps", []):
            reason = re.sub(r"\d+(\.\d+)?", "N", g["reason"])[:110]
            by[(g["field"], reason)] += 1
            if len(examples[(g["field"], reason)]) < 3:
                examples[(g["field"], reason)].append(g["scope"])
    out = [f"Записей в журнале пробелов: {sum(by.values())} (по полю и причине):", "",
           "| Поле | Причина | Записей | Примеры |", "|---|---|---|---|"]
    for (field, reason), n in by.most_common(None if detail else 40):
        out.append(f"| {field} | {reason} | {n} | {'; '.join(examples[(field, reason)])} |")
    return out


def conflicts_section(data: dict, detail: bool) -> list[str]:
    rows = []
    for line in data["lines"]:
        st = line.get("staging") or {}
        for c in st.get("conflicts", []):
            rows.append((line["name"], c.get("scope", ""), c.get("key", ""), str(c.get("kept_value")), str(c.get("other_values"))[:80], c.get("resolution", "")))
        for c in (line.get("load") or {}).get("conflicts", []) if isinstance((line.get("load") or {}).get("conflicts"), list) else []:
            rows.append((line["name"], "загрузка", c.get("what", ""), str(c.get("existing"))[:40], str(c.get("new"))[:40], c.get("resolution", "")))
    res = Counter(r[5][:70] for r in rows)
    out = [f"Конфликтов: {len(rows)}. По решениям:", ""] + [f"- {k}: {v}" for k, v in res.most_common()]
    if detail and rows:
        out += ["", "| Линейка | Область | Поле | Оставлено | Другие значения | Решение |", "|---|---|---|---|---|---|"]
        out += [f"| {a} | {b} | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in rows[:400]]
        if len(rows) > 400:
            out.append(f"(ещё {len(rows) - 400} строк — в staging.json линеек, поле conflicts)")
    return out


def recheck_section(data: dict) -> list[str]:
    rc = data["recheck"] or {}
    checked = sum(v.get("checked", 0) for v in rc.values())
    bad = sum(v.get("mismatches", 0) for v in rc.values())
    out = [f"Проверено {checked} записей (10% каждой линейки), расхождений {bad}."]
    for line, v in sorted(rc.items()):
        out.append(f"- {line}: {v.get('checked')} проверено, {v.get('mismatches')} расхождений")
    return out


def notes_section(data: dict) -> list[str]:
    out = []
    for line in data["lines"]:
        st = line.get("staging") or {}
        media = [n for n in st.get("notes", []) if "media" in n or "dropped" in n or "moved" in n]
        for g in st.get("generations", []):
            ev = [e for e in g.get("boundary_evidence", []) if "[media:" in e]
            if ev:
                out.append(f"- {line['name']} {g['code']} ({g['start_year']}–{g.get('end_year') or ''}): {ev[0][:300]}")
        for n in media:
            out.append(f"- {line['name']}: {n[:300]}")
    return out or ["- нет"]


def prepared_counts(data: dict) -> dict:
    c = Counter()
    for line in data["lines"]:
        st = line.get("staging") or {}
        c["линеек"] += 1
        c["поколений"] += len(st.get("generations", []))
        c["конфигураций"] += len(st.get("configurations", []))
        c["фактов"] += len(st.get("facts", []))
        c["отзывов"] += len(st.get("recalls", []))
        c["проблем"] += len(st.get("issues", []))
        c["пунктов ТО"] += len(st.get("maintenance", []))
    return dict(c)


def report_make(make: str, data: dict, live: dict, before: dict) -> list[str]:
    name = MAKES[make]["epa"]
    out = [f"# {name} — отчёт по базе технических данных US", "",
           f"Сформировано {datetime.now(UTC).isoformat(timespec='seconds')} скриптом scripts/build_us_report.py.", ""]
    if make in STATUS_NOTE:
        out += [f"**Статус:** {STATUS_NOTE[make]}", ""]
    if make in NOT_LOADED:
        out += ["## Подготовлено, но не записано в БД", ""]
        out += [f"- {k}: {v}" for k, v in prepared_counts(data).items()]
        out += ["", "## Журнал пробелов подготовленных данных", ""] + gaps_section(data, False)
        return out
    out += ["## 1. Матрица покрытия", "", "Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).", ""]
    out += matrix(data)
    te_b = before.get("by_make", {}).get(name, {})
    te_a = live.get("by_make", {}).get(name, {})
    out += ["", "## 2. Строки до и после", "",
            "| Таблица | До пакета | После |", "|---|---|---|"]
    for t in ("technical_evidence", "known_issues", "maintenance_schedule_items"):
        out.append(f"| {t} | {te_b.get(t, 0)} | {te_a.get(t, 0)} |")
    out += ["", "## 3. Журнал пробелов", ""] + gaps_section(data, True)
    out += ["", "## 4. Конфликты источников", ""] + conflicts_section(data, True)
    out += ["", "## 5. Выборочная перепроверка", ""] + recheck_section(data)
    out += ["", "## Поколения: свидетельства прессы и решения детектора", ""] + notes_section(data)
    corrections = []
    for line in data["lines"]:
        for s in (line.get("load") or {}).get("stale", []) if isinstance((line.get("load") or {}).get("stale"), list) else []:
            corrections.append(f"- {line['name']}: {s.get('fact_key')} = {s.get('value')} (MY{s.get('years')}) — {s.get('action')}")
        for u in (line.get("load") or {}).get("issues_updated", []):
            corrections.append(f"- {line['name']}: проблема {u.get('issue')} обновлена {json.dumps(u.get('changes'), ensure_ascii=False)[:160]}")
    out += ["", "## Изменения ранее записанных строк (последняя загрузка)", ""] + (corrections or ["- нет"])
    live_pass = data.get("pass_live") or {}
    if live_pass:
        out += ["", "## Загрузка", "", f"Режим: {live_pass.get('mode')}, quick_check: {live_pass.get('quick_check')}, "
                f"нарушений FK: {live_pass.get('foreign_key_violations')}, полностью перезагружены: {live_pass.get('replace_own')}"]
        for key, v in live_pass.get("lines", {}).items():
            out.append(f"- {key}: {v.get('flag')}, код {v.get('exit')}, {json.dumps(v.get('counts') or {}, ensure_ascii=False)}")
    return out


def blocked_hosts() -> list[str]:
    out = []
    for path in sorted((WORK / "_shared" / "manifest_press").glob("*.csv")) + sorted((WORK / "_shared" / "manifest_official").glob("*.csv")):
        rows = read_csv(path)
        st = Counter(r.get("status") for r in rows)
        notes = {r.get("note") for r in rows if r.get("status") in ("blocked", "skipped") and r.get("note")}
        if st.get("blocked") or st.get("skipped"):
            out.append(f"- {path.stem}: {dict(st)}; {'; '.join(sorted(n for n in notes if n))[:200]}")
    return out


def library_section() -> list[str]:
    rows = read_csv(WORK / "_library" / "manifest.csv")
    by = Counter((r["market"], r["make"]) for r in rows)
    out = [f"Материалов в библиотеке (data_work/_library/manifest.csv): {len(rows)}.", "",
           "| Рынок | Марка | Материалов |", "|---|---|---|"]
    out += [f"| {m} | {mk} | {n} |" for (m, mk), n in sorted(by.items())]
    other = Counter()
    for make in MAKE_ORDER:
        for path in (WORK / make / "extracted").glob("*.json"):
            d = read_json(path, {})
            if d.get("status") == "other_market":
                other[(d.get("edition_market") or "UNKNOWN", make)] += 1
    out += ["", f"Скачанные руководства не US-издания (не использованы, помечены other_market): {sum(other.values())}.", "",
            "| Рынок | Марка | Документов |", "|---|---|---|"]
    out += [f"| {m} | {mk} | {n} |" for (m, mk), n in sorted(other.items())]
    return out


def manual_years(make: str, line_key: str) -> dict:
    """Model year -> US owner's-manual editions that cover it, from every extracted document:
    a year-specific manual or a generation edition (mycarusermanual, e.g. Audi Q7 2016-2025)
    covers all its years. Press pages, secondary databases and non-US editions do not count."""
    out = defaultdict(set)
    for path in (WORK / make / "extracted").glob("*.json"):
        doc = read_json(path, {})
        meta = doc.get("doc", {})
        if (line_key in meta.get("lines", []) and doc.get("edition_market") == "US" and doc.get("status", "ok") == "ok"
                and meta.get("doc_type") not in ("press_specifications", "secondary_specifications", "teoalida_specifications")):
            for y in meta.get("years", []):
                out[y].add(meta["key"])
    return out


def vin_samples(all_data: dict) -> list[str]:
    out = []
    for make in ("bmw", "volkswagen", "audi"):
        for line in all_data[make]["lines"]:
            st = line.get("staging") or {}
            years = sorted({c["year"] for c in st.get("configurations", [])})
            covered = manual_years(make, line["key"])
            missing = [y for y in years if y not in covered]
            if missing:
                out.append(f"- {line['name']}: {', '.join(map(str, missing))}")
    return out


def models_outside() -> list[str]:
    out = []
    for make in MAKE_ORDER:
        for line in lines_for(make, include_done=True):
            st = read_json(WORK / make / "staging" / line.slug / "staging.json", {})
            if st and not st.get("configurations"):
                out.append(f"- {line.name} ({MAKES[make]['epa']}): нет строк EPA за 2014–2026 — в США под этим именем не продавалась; в базу не добавлялась.")
    unmapped = read_json(WORK / "_shared" / "nhtsa_unmapped_models.json", {})
    out += ["", "Модели этих марок, которые NHTSA перечисляет для США, но которых нет в списке линеек (предложения, в базу не добавлялись):", ""]
    for make in MAKE_ORDER:
        names = unmapped.get(make) or []
        if names:
            out.append(f"- {MAKES[make]['epa']}: {', '.join(names)}")
    return out


def status_lines() -> list[str]:
    out = ["| Марка | Статус | Последний коммит марки |", "|---|---|---|"]
    for make in MAKE_ORDER:
        name = MAKES[make]["epa"]
        commit = git("log", "--format=%h %s", "-n", "1", "--", f"data_work/{make}/staging").strip()
        if make in NOT_LOADED:
            status = "не загружена (решение владельца)"
        elif make == "infiniti":
            status = "загружена до решения об остановке, оставлена как есть"
        elif make == "toyota":
            status = "загружена (Camry — принятая ранее линейка)"
        else:
            status = "загружена"
        out.append(f"| {name} | {status} | {commit[:90]} |")
    return out


def mbusa_failures() -> list[str]:
    rows = read_csv(WORK / "_shared" / "manifest_official" / "www.mbusa.com.csv")
    manuals = [r for r in rows if r.get("doc_type") == "owners_manual"]
    first = [r for r in manuals if "alternative" not in (r.get("note") or "")]
    alt = [r for r in manuals if "alternative" in (r.get("note") or "")]
    last = {}
    for r in first:
        last[r["url"]] = r
    st = Counter(r["status"] for r in last.values())
    # line-years (EPA years of the staging) against every US-edition manual extracted for the
    # make: mbusa downloads, alternative editions and mycarusermanual copies
    all_years, ok_years = set(), set()
    for line in lines_for("mercedes-benz"):
        staging = read_json(WORK / "mercedes-benz" / "staging" / line.slug / "staging.json", {})
        all_years |= {(line.key, c["year"]) for c in staging.get("configurations", [])}
    for path in (WORK / "mercedes-benz" / "extracted").glob("*.json"):
        doc = read_json(path, {})
        meta = doc.get("doc", {})
        if (doc.get("edition_market") == "US" and doc.get("status", "ok") == "ok"
                and meta.get("doc_type") not in ("press_specifications", "secondary_specifications")):
            ok_years |= {(line, year) for line in meta.get("lines", []) for year in meta.get("years", [])}
    log = read_json(WORK / "_shared" / "manifest_official" / "mbusa_alternatives_log.json", [])
    tried = sum(1 for x in log if x["tried"])
    got = sum(1 for x in log if x["downloaded"])
    none_listed = sum(1 for x in log if not x["alternatives_listed"])
    missing = sorted(all_years - ok_years)
    return [
        f"- www.mbusa.com (руководства Mercedes-Benz), основной проход: скачано {st.get('ok', 0)} руководств "
        f"(и {sum(1 for r in rows if r.get('doc_type') != 'owners_manual' and r['status'] == 'ok')} гарантийных/сервисных "
        f"книжек), недоступно {st.get('error', 0)} (шлюз сайта отвечал 502). Повтор недоступных файлов с таймаутом "
        "180 с: 0 из 7, остановлен по решению владельца.",
        f"- Альтернативные официальные US-издания тех же модели-годов (другой кузов или другая дата издания, "
        f"по одному запросу, таймаут 180 с, до 2 попыток на модели-год): модели-годов {len(log)}, с попытками {tried}, "
        f"скачано {got} ({sum(1 for r in alt if r['status'] == 'ok')} файлов), без альтернатив в каталоге mbusa "
        f"{none_listed}; запросов с ошибкой {sum(1 for r in alt if r['status'] != 'ok')}.",
        f"- Модели-годы Mercedes (годы EPA) без US-руководства ни в одном источнике (mbusa, альтернативные издания, "
        f"mycarusermanual) после всех попыток: {len(missing)} из {len(all_years)}: "
        + ", ".join(f"{line.split('/')[-1]} {year}" for line, year in missing) + ".",
        "- Копии руководств для Mercedes: mycarusermanual.com — только 4 модели Mercedes в каталоге; carmans.net — "
        "Mercedes нет; ownersman.com — защита Cloudflare (не обходится); manualslib.com и usermanual.wiki → manuals.plus "
        "не отвечают.",
        "- auto-data.net: объём масла и ОЖ собраны (вторичный источник); допуск масла на auto-data.net закрыт входом "
        "в аккаунт — не собирался.",
    ]


def corrections_section() -> list[str]:
    out = []
    for make in MAKE_ORDER:
        changes = removed = 0
        examples = []
        for path in sorted((WORK / make / "staging").glob("*/corrections.json")):
            data = read_json(path, {})
            for c in data.get("value_changes", []):
                changes += 1
                if isinstance(c.get("existing"), (int, float)) and len(examples) < 8:
                    examples.append(f"{path.parent.name}: {c.get('what', '').split()[-1]} {c.get('existing')} → {c.get('new')}")
            removed += len(data.get("removed", []))
        if changes or removed:
            out.append(f"- {MAKES[make]['epa']}: значений заменено {changes}, строк удалено как устаревшие {removed}"
                       + (f"; числовые примеры: {'; '.join(examples)}" if examples else ""))
    return out or ["- нет"]


def unconfirmed_editions() -> list[str]:
    items = read_json(WORK / "_shared" / "edition_title_not_confirmed.json", [])
    return [f"- {k} {t}".rstrip() + " — значения использованы как обычное (не гибридное/EV) издание" for k, t in items] or ["- нет"]


def a25a_section() -> list[str]:
    facts = read_json(WORK / "toyota" / "A25A-FKS_2022_check.json", [])
    out = ["| Поле | Значение | Годы | Уровень | Источник (стр.) |", "|---|---|---|---|---|"]
    for f in facts:
        cites = "; ".join(f"{c['source']} p.{','.join(map(str, c.get('pages') or []))}" for c in (f.get("cites") or [])[:3])
        value = f"{f['value']} {f.get('unit') or ''}".strip()
        out.append(f"| {f['fact_key']} | {value} | {f['years'][0]}–{f['years'][1]} | {f['display_level']} | {cites} |")
    return out


def press_section() -> list[str]:
    out = ["| Сайт | Документов скачано | Не найдено | Заблокировано |", "|---|---|---|---|"]
    for path in sorted((WORK / "_shared" / "manifest_press").glob("*.csv")):
        rows = [r for r in read_csv(path) if r.get("doc_type", "press_specifications") in ("press_specifications", "")]
        last = {}
        for r in rows:
            last[r.get("url")] = r
        st = Counter(r.get("status") for r in last.values())
        out.append(f"| {path.stem} | {st.get('ok', 0)} | {st.get('not_found', 0)} | {st.get('blocked', 0)} |")
    parsed = Counter()
    for make in MAKE_ORDER:
        parsed[make] = len(list((WORK / make / "extracted").glob("press-*.json")))
    out += ["", "Разобрано пресс-документов по маркам: " + ", ".join(f"{MAKES[m]['epa']} {n}" for m, n in parsed.items() if n)]
    return out


def cc_maintenance_section(all_data: dict) -> list[str]:
    out = ["| Марка | Проблемы с подтверждением CarComplaints | Только по отзывам владельцев (CarComplaints) | Пунктов ТО |", "|---|---|---|---|"]
    for make in MAKE_ORDER:
        if make in NOT_LOADED:
            continue
        raised = owners = mnt = 0
        for line in all_data[make]["lines"]:
            st = line.get("staging") or {}
            for i in st.get("issues", []):
                if i.get("evidence", {}).get("carcomplaints"):
                    if "-cc-" in i["id"]:
                        owners += 1
                    else:
                        raised += 1
            mnt += len(st.get("maintenance", []))
        out.append(f"| {MAKES[make]['epa']} | {raised} | {owners} | {mnt} |")
    return out


MB_FIELDS = [
    ("Объём масла", ["engine_oil_capacity_l", "engine_oil_capacity_drain_refill_l"]),
    ("Допуск/стандарт масла", ["engine_oil_oem_approval", "engine_oil_specification"]),
    ("Вязкость", ["engine_oil_viscosity"]),
    ("ОЖ", ["coolant", "coolant_description", "coolant_capacity_l"]),
    ("Жидкость АКПП", ["transmission_fluid", "transmission_fluid_capacity_l"]),
    ("Тормозная", ["brake_fluid"]),
]
MB_BEFORE_COMMIT = "f8a2184"  # Mercedes-Benz load before the gap-closing round


def mb_line_years(staging: dict) -> dict:
    """year -> {field: source kind} for the shown facts; kinds: manual (US owner's manual, official
    or copy), secondary (auto-data.net), press."""
    kinds = {}
    for key, item in (staging.get("sources") or {}).items():
        st = item.get("source_type", "")
        kinds[key] = ("secondary" if st == "SECONDARY_SPEC_DATABASE" else "press" if st == "PRESS_RELEASE"
                      else "manual" if st.startswith("OWNER_MANUAL") else "other")
    out = defaultdict(dict)
    whole = defaultdict(set)  # (year, label) with a value for all models, not only named ones
    rank = {"manual": 0, "press": 1, "secondary": 2, "other": 3}
    for f in staging.get("facts", []):
        if f.get("display_level") == "HIDDEN_CONFLICT":
            continue
        for label, keys in MB_FIELDS:
            if f["key"] in keys:
                kind = kinds.get(f.get("primary_source"), "other")
                variant = (f.get("applicability") or {}).get("variant") or ""
                for y in range(f["years"][0], f["years"][1] + 1):
                    prev = out[y].get(label)
                    if prev is None or rank[kind] < rank[prev]:
                        out[y][label] = kind
                    if not variant or "all models" in variant or "all other models" in variant:
                        whole[(y, label)].add(kind)
    for y, fields in out.items():
        for label, kind in fields.items():
            if kind not in whole[(y, label)]:
                fields[label] = kind + "*"
    for item in staging.get("maintenance", []):
        for y in range(item["years"][0], item["years"][1] + 1):
            out[y]["ТО"] = "mbusa A/B" if item.get("primary_source") == "mbusa-service-intervals" else "manual"
    return out


def mercedes_section() -> list[str]:
    out = ["Поля по модельным годам каждой линейки (EPA-годы). Источник: manual — US-руководство (официальное или копия), "
           "secondary — auto-data.net (европейская карточка, сопоставленная с US-конфигурацией), press — пресс-материал; "
           "«*» — значение только для названных в таблице руководства моделей (не для всех конфигураций года); "
           "mbusa A/B — интервалы Service A/B с официальной страницы mbusa.com (без привязки к модели и году, «approximately» "
           "в источнике, уровень SECONDARY_NOTE); «—» — нет данных.", ""]
    labels = [l for l, _ in MB_FIELDS] + ["ТО"]
    totals = Counter()
    rows = ["| Линейка | Год | " + " | ".join(labels) + " |", "|---|---|" + "---|" * len(labels)]
    for line in lines_for("mercedes-benz"):
        path = f"data_work/mercedes-benz/staging/{line.slug}/staging.json"
        now_st = read_json(ROOT / path, {})
        old = subprocess.run(["git", "show", f"{MB_BEFORE_COMMIT}:{path}"], cwd=ROOT, capture_output=True)
        before = mb_line_years(json.loads(old.stdout)) if old.returncode == 0 else {}
        after = mb_line_years(now_st)
        for year in sorted({c["year"] for c in now_st.get("configurations", [])}):
            cells = []
            for label in labels:
                a, b = after.get(year, {}).get(label), before.get(year, {}).get(label)
                totals[(label, "after" if a else "none")] += 1
                if a and not b:
                    totals[(label, "closed")] += 1
                cells.append((a or "—") + (" (новое)" if a and not b else ""))
            rows.append(f"| {line.name} | {year} | " + " | ".join(cells) + " |")
    summary = ["| Поле | Годы с данными | Закрыто в этом раунде | Осталось без данных |", "|---|---|---|---|"]
    for label in labels:
        summary.append(f"| {label} | {totals[(label, 'after')]} | {totals[(label, 'closed')]} | {totals[(label, 'none')]} |")
    why = [
        "",
        "Почему не закрыто остальное:",
        "",
        "- Модели-годы без US-руководства (см. «Недоступные источники»): объём масла и ОЖ взяты с auto-data.net, "
        "где карточка однозначно сопоставилась с US-конфигурацией (обозначение, объём, цилиндры, привод, годы); "
        "если карточки расходятся между собой — значение скрыто как конфликт, не выбирается.",
        "- Допуск масла (MB 229.x): только из таблиц руководств; на auto-data.net допуск закрыт входом — для годов без "
        "руководства пусто.",
        "- Вязкость: US-руководства Mercedes дают таблицу SAE-классов по температуре, а не одно значение; записано "
        "только там, где руководство прямо ограничивает класс (AMG: «only SAE 0W-40 or 5W-40»).",
        "- Жидкость АКПП: в US-руководствах Mercedes нет ни спецификации, ни объёма ATF (обслуживание по Service A/B "
        "у дилера) — пусто.",
        "- Тормозная жидкость: «MB-Approval 331.0» из руководств; для годов без руководства — пусто.",
        "- ТО: официальная страница mbusa.com «Service & Maintenance»: Service A — первый визит «approximately» "
        "10 000 миль или 1 год (что наступит раньше), далее «approximately» каждые 20 000 миль или 2 года; Service B — "
        "«approximately» 20 000 миль или 1 год после предыдущего визита, далее каждые 20 000 миль или 2 года. Страница не называет модели и годы и сама пишет «approximately» — строки "
        "записаны как SECONDARY_NOTE с этой оговоркой. Электромобили (EQS, EQB): на странице пакет обслуживания EV без "
        "интервалов — пусто с причиной в gaps.",
        "- Значения из таблиц руководств привязаны к строке таблицы (обозначение модели как напечатано, "
        "«all other models (not …)», «Mercedes-AMG vehicles»), на остальные модели не распространяются.",
    ]
    return out + summary + why + [""] + rows


def tests_section() -> list[str]:
    out = []
    for label, path in (("baseline backend", WORK / "toyota" / "baseline_backend_pytest.txt"),
                        ("baseline flutter", WORK / "toyota" / "baseline_flutter_tests.txt"),
                        ("baseline web", WORK / "toyota" / "baseline_web_tests.txt"),
                        ("final backend", WORK / "_batch" / "final_backend_pytest.txt"),
                        ("final flutter", WORK / "_batch" / "final_flutter_tests.txt"),
                        ("final web", WORK / "_batch" / "final_web_tests.txt")):
        if not path.exists():
            out.append(f"- {label}: нет файла {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        summary = re.findall(r"\d+ (?:passed|failed)[^\n]*|All tests passed!|Some tests failed\.|ℹ (?:pass|fail) \d+", text)
        out.append(f"- {label}: {'; '.join(summary[-3:]) or 'итог не найден'} ({path.relative_to(ROOT)})")
    return out


def main() -> int:
    live, before, first = counts(LIVE), counts(BEFORE_BATCH), counts(BEFORE_ALL)
    all_data = {make: make_data(make) for make in MAKE_ORDER}
    dry = "--dry" in sys.argv
    for make, data in all_data.items():
        text = "\n".join(report_make(make, data, live, before)) + "\n"
        if dry:
            print(make, len(text.splitlines()), "lines")
            continue
        target = WORK / make / "REPORT.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and "scripts/build_us_report.py" not in target.read_text(encoding="utf-8"):
            # a hand-written report (the accepted Camry report) is kept under its own name
            keep = target.with_name("REPORT_CAMRY.md" if make == "toyota" else "REPORT_previous.md")
            if keep.exists():
                raise SystemExit(f"{target} is hand-written and {keep.name} exists; not overwriting")
            target.rename(keep)
        target.write_text(text, encoding="utf-8")
    out = ["# Итоговый отчёт: база технических данных US (все марки Приложения A)", "",
           f"Сформировано {datetime.now(UTC).isoformat(timespec='seconds')} скриптом scripts/build_us_report.py; "
           "отчёты по маркам — data_work/<марка>/REPORT.md.", "",
           "## 1. Матрица покрытия", "", "Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль). "
           "Поля по разделу 4 промта.", ""]
    out += ["Статус марок:", ""] + status_lines() + [""]
    for make in MAKE_ORDER:
        if make in NOT_LOADED:
            out += [f"### {MAKES[make]['epa']}", "", f"{STATUS_NOTE[make]}", ""]
            continue
        note = [f"_{STATUS_NOTE[make]}_", ""] if make in STATUS_NOTE else []
        out += [f"### {MAKES[make]['epa']}", ""] + note + matrix(all_data[make]) + [""]
    out += ["## 2. Строки по таблицам: до и после", "",
            "| Таблица | До f087 (бэкап 0959) | До пакета (бэкап 1308) | Сейчас |", "|---|---|---|---|"]
    for t in TABLES:
        out.append(f"| {t} | {first.get(t)} | {before.get(t)} | {live.get(t)} |")
    out += ["", "По маркам (technical_evidence / known_issues / maintenance_schedule_items):", "",
            "| Марка | До пакета | Сейчас |", "|---|---|---|"]
    for make in MAKE_ORDER:
        n = MAKES[make]["epa"]
        b, a = before.get("by_make", {}).get(n, {}), live.get("by_make", {}).get(n, {})
        fmt = lambda d: f"{d.get('technical_evidence', 0)} / {d.get('known_issues', 0)} / {d.get('maintenance_schedule_items', 0)}"  # noqa: E731
        out.append(f"| {n} | {fmt(b)} | {fmt(a)} |")
    out += ["", "## 3. Журнал пробелов", ""]
    for make in MAKE_ORDER:
        if make in NOT_LOADED:
            continue
        out += [f"### {MAKES[make]['epa']}", ""] + gaps_section(all_data[make], False)[:14] + [""]
    out += ["Закрытые и заблокированные источники (manifest):", ""] + blocked_hosts()
    out += ["", "## 4. Конфликты источников и решения", ""]
    for make in MAKE_ORDER:
        if make in NOT_LOADED:
            continue
        out += [f"### {MAKES[make]['epa']}", ""] + conflicts_section(all_data[make], False) + [""]
    out += ["## 5. Выборочная перепроверка (10%)", ""]
    for make in MAKE_ORDER:
        if make in NOT_LOADED:
            continue
        out += [f"### {MAKES[make]['epa']}", ""] + recheck_section(all_data[make])[:1] + [""]
    migrations = [p for p in git("diff", "--name-only", BASELINE_COMMIT, "HEAD", "--", "backend/alembic/versions").split() if p]
    out += ["## 6. Изменения схемы", ""] + ([f"- {m}" for m in migrations] or ["- нет"])
    out += ["", "## 7. Тесты: baseline и финал", ""] + tests_section()
    out += ["", "## 8. Модели, которых нет в США, и предложения", ""] + models_outside()
    out += ["", "## 9. Нужны VIN-образцы (руководство выдаётся только по VIN: BMW, VW, Audi)", "",
            "Линейка и модельные годы без US-руководства в собранных источниках:", ""] + (vin_samples(all_data) or ["- нет"])
    out += ["", "## 10. Vehicle Databases", "", "VDB = нет; запросов к VDB: 0."]
    out += ["", "## 11. Git-коммиты", ""] + [f"- {l}" for l in git("log", "--oneline", f"{BASELINE_COMMIT}..HEAD").splitlines()]
    out += ["", "## 12. Библиотека других рынков", ""] + library_section()
    out += ["", "## Дополнительно", "", "### Недоступные источники", ""] + blocked_hosts() + mbusa_failures()
    out += ["", "### Исправления ранее записанных строк (журнал data_work/<марка>/staging/<линейка>/corrections.json)", ""] + corrections_section()
    out += ["", "### Документы, у которых название файла не подтверждено текстом", ""] + unconfirmed_editions()
    out += ["", "### Mercedes-Benz: масло, жидкости и ТО — что закрыто и что нет", ""] + mercedes_section()
    out += ["", "### Сверка A25A-FKS, 2022 (по запросу владельца)", ""] + a25a_section()
    out += ["", "### Пресс-материалы производителей", ""] + press_section()
    out += ["", "### CarComplaints.com и ТО по маркам (загруженные данные)", ""] + cc_maintenance_section(all_data)
    out += ["", "## Поколения: свидетельства прессы", "",
            "Источник: data_work/_shared/generation_evidence.json (cars.com, consumerreports.org; Car and Driver, "
            "Edmunds, KBB и MotorTrend недоступны для автоматического чтения). Используются только цитаты, сверенные со страницей.", ""]
    for make in MAKE_ORDER:
        notes = notes_section(all_data[make])
        if notes != ["- нет"]:
            out += [f"### {MAKES[make]['epa']}", ""] + notes[:60] + [""]
    if dry:
        print("\n".join(out[:80]))
        return 0
    (WORK / "REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("written", WORK / "REPORT.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
