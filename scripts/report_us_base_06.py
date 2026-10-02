"""Read-only named technical and residual scope report for the published sixth batch."""

# ruff: noqa: E402, E501
import json
from collections import Counter, defaultdict
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.services import catalog_buyer as buyer
from app.services.catalog_verification import us_catalog_ready
from app.services.market_priority import policy
from catalog_checkpoint_report import END, START, cell, year_ranges
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-06"


def dump(name, value):
    (OUT / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def grid(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    )


def main():
    coverage = json.loads((OUT / "coverage.json").read_text(encoding="utf-8"))
    tables = json.loads((OUT / "catalog-tables.json").read_text(encoding="utf-8"))
    with SessionLocal() as db:
        live = buyer.active_us_base_rows(buyer.records(db))
        by_key = {v.catalog_key: c for v, c in live}
        excluded_keys = {
            m["catalog_key"]
            for g in tables["delta_from_previous_batch"]
            if g["status"].endswith(" / EXCLUDED")
            for m in g["members"]
        }
        for v in db.scalars(
            select(VehicleVariant).where(VehicleVariant.catalog_key.in_(excluded_keys))
        ):
            by_key[v.catalog_key] = v.specifications["catalog"]
        technical = []
        models = defaultdict(lambda: {"strict": [], "conditional": []})
        tech_groups = {}
        for v, c in live:
            category = "strict" if us_catalog_ready(c) else "conditional"
            models[(c["make"], c["model"], c.get("generation_code"))][category].append(
                c["model_year"]
            )
            profiles = {lang: buyer.vehicle_profile(c, lang) for lang in ("ru", "az")}
            # Same field keys and source URLs in both languages; translated display is intentional.
            for ru, az in zip(
                profiles["ru"]["technical"], profiles["az"]["technical"], strict=True
            ):
                assert [(r["key"], r["source_url"]) for r in ru["rows"]] == [
                    (r["key"], r["source_url"]) for r in az["rows"]
                ]
            populated = {
                g["title"]: [r["key"] for r in g["rows"]]
                for g in profiles["ru"]["technical"]
                if g["rows"]
            }
            empty = [g["title"] for g in profiles["ru"]["technical"] if not g["rows"]]
            extra_keys = [
                "seats",
                "engine_code",
                "transmission_code",
                "octane_aki",
                "engine_oil_viscosity",
                "engine_oil_specification",
                "engine_oil_capacity_l",
                "transmission_fluid",
                "front_suspension",
                "front_brakes",
                "wheels",
            ]
            aliases = {
                "front_suspension": ["front_suspension", "suspension_front", "suspension"],
                "front_brakes": ["front_brakes", "brakes"],
            }
            missing = [
                key
                for key in extra_keys
                if not any(
                    c["facts"].get(alias, {}).get("status") == "CONFIRMED"
                    for alias in aliases.get(key, [key])
                )
            ]
            item = {
                "catalog_key": v.catalog_key,
                "variant_id": v.id,
                "make": c["make"],
                "model": c["model"],
                "generation": c.get("generation_code"),
                "year": c["model_year"],
                "configuration": c["configuration"],
                "status": category,
                "profiles": profiles,
                "confirmed_facts": {
                    k: f for k, f in c["facts"].items() if f.get("status") == "CONFIRMED"
                },
                "missing_selected_fields": missing,
            }
            technical.append(item)
            grouping = {
                "make": c["make"],
                "model": c["model"],
                "generation": c.get("generation_code"),
                "configuration": c["configuration"],
                "populated": populated,
                "empty": empty,
                "missing": missing,
            }
            sig = json.dumps(grouping, sort_keys=True, ensure_ascii=False)
            group = tech_groups.setdefault(sig, {**grouping, "years": []})
            group["years"].append(c["model_year"])
    order = policy()["primary_makes"]

    def sort_model(x):
        return (order.index(x[0]), x[1], str(x[2]))

    model_rows = [
        [*key, year_ranges(value["strict"]) or "—", year_ranges(value["conditional"]) or "—"]
        for key, value in sorted(models.items(), key=lambda x: sort_model(x[0]))
    ]
    model_md = grid(
        [
            "Make",
            "Model",
            "Generation",
            "Строгий критерий: US MY",
            "Дополнительно без ограничения мест: US MY",
        ],
        model_rows,
    )
    dump("models-and-years.json", model_rows)
    (OUT / "models-and-years.md").write_text(model_md + "\n", encoding="utf-8")
    dump("technical-fields.json", technical)
    tech_rows = []
    for g in sorted(
        tech_groups.values(),
        key=lambda x: (
            *sort_model((x["make"], x["model"], x["generation"])),
            x["configuration"],
            x["years"],
        ),
    ):
        filled = "; ".join(f"{title}: {', '.join(keys)}" for title, keys in g["populated"].items())
        missing = "; ".join(g["empty"]) + "; поля: " + ", ".join(g["missing"])
        tech_rows.append(
            [
                g["make"],
                g["model"],
                g["generation"],
                year_ranges(g["years"]),
                g["configuration"],
                filled,
                missing,
                "US manual/spec table для указанного MY и агрегата; точный локатор по незаполненным полям. Полнота раздела не заявлена.",
            ]
        )
    (OUT / "technical-coverage.md").write_text(
        "# Техническая часть: фактическое наполнение\n\nНазвание раздела не считается данными. Ниже перечислены именно опубликованные поля; значения, AZ/RU, источники и локаторы каждой конфигурации — в technical-fields.json. Перечень отсутствующих полей выборочный, не заявление о полном заводском профиле.\n\n"
        + grid(
            [
                "Make",
                "Model",
                "Generation",
                "US MY",
                "Версия",
                "Заполненные подкатегории и поля",
                "Остаток",
                "Следующий шаг",
            ],
            tech_rows,
        )
        + "\n",
        encoding="utf-8",
    )
    delta = []
    actions = Counter()
    new_periods = Counter()
    residual = []
    cohorts = json.loads((OUT / "seating-cohorts-before.json").read_text(encoding="utf-8"))
    oldest = {r["catalog_key"] for r in cohorts["old_143"]}
    fifth = {r["catalog_key"] for r in cohorts["introduced_in_batch05_10"]}
    for g in tables["delta_from_previous_batch"]:
        actions[g["status"].split(" / ")[0]] += g["configuration_count"]
        sources = set()
        for member in g["members"]:
            c = by_key[member["catalog_key"]]
            if g["status"].startswith("ADDED") and not g["status"].endswith(" / EXCLUDED"):
                y = c["model_year"]
                new_periods[
                    "2000–2013" if y <= 2013 else "2014–2020" if y <= 2020 else "2021+"
                ] += 1
            for key, f in c["facts"].items():
                if not g["changed_fields"] or key in g["changed_fields"]:
                    url = (f.get("documentary_source") or {}).get("url")
                    if url:
                        sources.add(url)
            if not sources:
                sources.add(c["source_url"])
        delta.append(
            [
                g["make"],
                g["model"],
                g["generation"],
                year_ranges(g["model_years"]),
                g["engine"],
                g["transmission"],
                g["drivetrain"],
                g["seats"],
                g["configuration_count"],
                g["status"],
                ", ".join(g["changed_fields"])
                or (
                    "Исключена: конфликт применимости, история сохранена"
                    if g["status"].endswith(" / EXCLUDED")
                    else (
                        "Новая техническая связка"
                        if g["status"].startswith("ADDED")
                        else "Только revision/provenance"
                    )
                ),
                "<br>".join(f"[Документ]({url})" for url in sorted(sources)),
            ]
        )
    (OUT / "delta-with-sources.md").write_text(
        "# Delta с источниками\n\nСтатусы относятся только к перечисленной связке и годам. NOT_IN_STRICT_OUTPUT доступен в обычном поиске без ограничения неизвестных мест; другие жёсткие ограничения сохраняются. Факт имеет точную область в technical-fields.json и manifest.\n\n"
        + grid(
            [
                "Make",
                "Model",
                "Generation",
                "US MY",
                "Engine",
                "Transmission",
                "Drivetrain",
                "Seats",
                "Count",
                "Статус / доступность",
                "Изменение",
                "Источники",
            ],
            delta,
        )
        + "\n",
        encoding="utf-8",
    )
    for g in tables["cumulative_conditional_output_catalog"]:
        buckets = defaultdict(list)
        for m in g["members"]:
            buckets[
                "Старые 143"
                if m["catalog_key"] in oldest
                else "Добавленные в batch05: 10"
                if m["catalog_key"] in fifth
                else "Добавленные в batch06"
            ].append(m["model_year"])
        for kind, years in buckets.items():
            special = (
                "Отдельно проверить стандартные/опциональные 5/7 мест и комплектацию"
                if g["model"] == "Sorento"
                else "Нужна явная вместимость для этого US MY/кузова и применимость к этой версии"
            )
            residual.append(
                [
                    g["make"],
                    g["model"],
                    g["generation"],
                    year_ranges(years),
                    g["engine"],
                    g["transmission"],
                    g["drivetrain"],
                    len(years),
                    kind,
                    "seats",
                    "Проверенные документы не закрыли точную применимость мест; вывод по фото/соседнему MY не использован",
                    special + "; US owner manual либо manufacturer specification table",
                ]
            )
    (OUT / "remaining-seating.md").write_text(
        "# Поимённый остаток мест\n\n"
        + grid(
            [
                "Make",
                "Model",
                "Generation",
                "US MY",
                "Engine",
                "Transmission",
                "Drive",
                "Count",
                "Очередь",
                "Поле",
                "Причина",
                "Следующий источник/шаг",
            ],
            residual,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = json.loads(
        (ROOT / "data/manifests/us-base-catalog-batch-06.json").read_text(encoding="utf-8")
    )
    cohort_report = {}
    for name, entries in cohorts.items():
        closed = [r for r in entries if us_catalog_ready(by_key[r["catalog_key"]])]
        remaining = [r for r in entries if not us_catalog_ready(by_key[r["catalog_key"]])]
        cohort_report[name] = dict(
            initial=len(entries),
            closed=len(closed),
            remaining=len(remaining),
            closed_records=closed,
            remaining_records=remaining,
        )
    new_gaps = [r for r in coverage["seating_gaps"] if r["catalog_key"] not in oldest | fifth]
    cohort_report["introduced_in_batch06"] = dict(count=len(new_gaps), records=new_gaps)
    dump("seating-cohorts-after.json", cohort_report)
    plan_rows = []
    for p in manifest["planned_queue"]:
        groups = [
            g
            for g in tables["delta_from_previous_batch"]
            if g["make"] == p["make"]
            and g["model"] == p["model"]
            and g["status"].startswith("ADDED")
        ]
        strict = sorted(
            {
                m["model_year"]
                for g in groups
                if g["status"].endswith(" / STRICT_SCOPED")
                for m in g["members"]
            }
        )
        conditional = sorted(
            {
                m["model_year"]
                for g in groups
                if "NOT_IN_STRICT_OUTPUT" in g["status"]
                for m in g["members"]
            }
        )
        plan_rows.append(
            [
                p["make"],
                p["model"],
                p["generation"],
                f"{p['years'][0]}–{p['years'][-1]}",
                year_ranges(strict) or "—",
                year_ranges(conditional) or "—",
                sum(g["configuration_count"] for g in groups),
                "Только подтверждённые версии из delta; другие комплектации не заявлены",
            ]
        )
    (OUT / "plan-vs-actual.md").write_text(
        "# План и факт batch06\n\nЦелевые диапазоны не означают все комплектации. Santa Fe Sport хранится с подтверждённым американским кодом AN; NC с длинным кузовом не добавлен.\n\n"
        + grid(
            [
                "Make",
                "Model",
                "Generation",
                "Целевые US MY",
                "MY с подтверждёнными местами",
                "MY с неизвестными местами",
                "Новых связок",
                "Граница",
            ],
            plan_rows,
        )
        + "\n\nСтарые143 и новые10 batch05 проверялись по уже приобретённым документам. Дополнительного достаточного подтверждения мест не найдено; ни одна карточка не скрыта из обычного поиска из-за необязательного неизвестного поля. Точные версии каждой когорты сохранены отдельно.\n",
        encoding="utf-8",
    )
    present = {(r[0], r[1]) for r in model_rows}
    remaining_queue = []
    for make in order:
        for model in policy()["first_wave_model_order"][make]:
            if (make, model) not in present:
                note = "Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch"
                if model == "Santa Fe":
                    note = "AN Sport уже покрыт; длинный NC 3.3 остаётся отдельной областью"
                if make == "Tesla":
                    note = "Нужна датированная US technical identity; сохранены конкретные holds Model S2016 / Model3 2020; не запрет всей марки"
                remaining_queue.append(dict(make=make, model=model, reason=note))
    dump("remaining-master-queue.json", remaining_queue)
    (OUT / "remaining-master-queue.md").write_text(
        "# Оставшиеся модели master-list\n\nОчередь следует заданному владельцем порядку марок/моделей, не удобству источников. Внутри уже добавленных моделей другие годы, кузова и версии также остаются не подтверждёнными до отдельного evidence.\n\n"
        + grid(
            ["Make", "Model", "Область / причина"],
            [[r["make"], r["model"], r["reason"]] for r in remaining_queue],
        )
        + "\n\nОтдельные точные пробелы: AccordVII MY2004–2005 и coupe/Hybrid; Elantra Sport6MT2016; Camry2000–2001; seating — remaining-seating.md. У Cruze2019 требуется самостоятельная проверка применимости объёма бака LS/AT; исправление MY2018 на него не перенесено.\n",
        encoding="utf-8",
    )
    metrics = dict(
        delta_actions=dict(actions),
        new_available_configurations=sum(new_periods.values()),
        new_excluded_configurations=len(excluded_keys),
        new_configurations_by_period=dict(new_periods),
        profiles_checked_az_ru=len(technical),
        technical_fields_with_source=sum(len(i["confirmed_facts"]) for i in technical),
        seating_cohorts={
            k: {f: v for f, v in x.items() if not isinstance(v, list)}
            for k, x in cohort_report.items()
        },
    )
    dump("data-reconciliation.json", metrics)
    checkpoint = ROOT / "docs/CHECKPOINT_US_BASE_CATALOG.md"
    block = (OUT / "catalog-tables.md").read_text(encoding="utf-8")
    block = START + block.split(START, 1)[1].split(END, 1)[0] + END
    totals = grid(
        ["Метрика", "Было basic", "Стало basic", "Было strict", "Стало strict"],
        [
            [
                key,
                coverage["cumulative_basic_counts"][key]
                - coverage["growth"]["cumulative_basic_counts"][key],
                coverage["cumulative_basic_counts"][key],
                coverage["cumulative_us_with_seating_counts"][key]
                - coverage["growth"]["cumulative_us_with_seating_counts"][key],
                coverage["cumulative_us_with_seating_counts"][key],
            ]
            for key in (
                "makes",
                "models",
                "generations",
                "market_variants",
                "engine_variants",
                "transmission_variants",
                "engine_transmission_combinations",
                "drivetrain_combinations",
                "model_year_configurations",
            )
        ],
    )
    brands = grid(
        ["Марка", "Моделей basic", "Моделей strict", "Годовых basic", "Годовых strict"],
        [
            [
                r["make"],
                r["basic"]["models"],
                r["us_with_seating"]["models"],
                r["basic"]["model_year_configurations"],
                r["us_with_seating"]["model_year_configurations"],
            ]
            for r in coverage["priority_make_coverage"]
        ],
    )
    links = "\n\n[Delta с источниками](../deliverables/VerifiedData/us-base-catalog-06/delta-with-sources.md) · [Все модели и годы](../deliverables/VerifiedData/us-base-catalog-06/models-and-years.md) · [Фактически заполненные разделы](../deliverables/VerifiedData/us-base-catalog-06/technical-coverage.md) · [Значения / AZ/RU / provenance](../deliverables/VerifiedData/us-base-catalog-06/technical-fields.json) · [Остаток мест](../deliverables/VerifiedData/us-base-catalog-06/remaining-seating.md) · [План и факт](../deliverables/VerifiedData/us-base-catalog-06/plan-vs-actual.md) · [Оставшийся master-list](../deliverables/VerifiedData/us-base-catalog-06/remaining-master-queue.md).\n\n"
    checkpoint.write_text(
        "# Auto Expert — U.S. base catalogue, batch06\n\nBackend0.8.1. Опубликовано в существующей локальной БД после batch05. Правила publication/search и утверждённый UI неизменны. Все статусы относятся к точным связкам, не ко всей модели.\n\n"
        + block
        + links
        + "## Краткий накопительный перечень\n\n"
        + model_md
        + "\n\n## Сверенные итоги после поимённых списков\n\n"
        + totals
        + "\n\n"
        + brands
        + "\n\n```json\n"
        + json.dumps(metrics, ensure_ascii=False, indent=2)
        + "\n```\n\nПроверки, ограничения и перенос: [BATCH06_VALIDATION.md](BATCH06_VALIDATION.md). Старый checkpoint05 сохранён отдельно.\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
