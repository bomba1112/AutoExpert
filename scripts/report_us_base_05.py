"""Read-only named technical and residual scope report for the published fifth batch."""

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
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-05"


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
        vehicle_ids = {v.catalog_key: v.id for v, c in live}
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
    old = set(r["catalog_key"] for r in json.loads((OUT / "initial-seating-gaps.json").read_text()))
    residual = []
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
                "Остаток старых 143" if m["catalog_key"] in old else "Новый seating gap"
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
    planned_old = defaultdict(list)
    for key in old:
        c = by_key[key]
        planned_old[(c["make"], c["model"], c["generation_code"])].append(c)
    plan_rows = []
    for identity, members in sorted(planned_old.items(), key=lambda x: sort_model(x[0])):
        closed = [c for c in members if us_catalog_ready(c)]
        remaining = [c for c in members if not us_catalog_ready(c)]
        plan_rows.append(
            [
                *identity,
                year_ranges([c["model_year"] for c in members]),
                f"Подтвердить места для {len(members)} существующих записей",
                f"Закрыто {len(closed)}: {year_ranges([c['model_year'] for c in closed]) or '—'}",
                f"Осталось {len(remaining)}: {year_ranges([c['model_year'] for c in remaining]) or '—'}",
                "Точные версии, источники и дополнительные поля — delta-with-sources.md; остаток — remaining-seating.md",
            ]
        )
    expansion = [
        (
            "Toyota",
            "Camry",
            "V sedan",
            "2002–2006",
            "18 годовых связок. 2.4:5MT/4AT до2004,5MT/5AT с2005;3.0:4AT до2003,5AT с2004;3.3SE:5AT2004–2006. Не все trim/emissions; мощность I4 и масла не агрегированы.",
        ),
        (
            "Toyota",
            "Camry",
            "VII",
            "2012–2017",
            "18 годовых связок:2.5/6AT,3.5/6AT,2.5HEV/eCVT. 2015facelift dimensions отдельно;200hp HEV не записано как мощность ДВС. Масла пока не подтверждены для этой области.",
        ),
        (
            "Honda",
            "Accord",
            "VII",
            "2003–2007",
            "Опубликованы2003 и2006–2007,11 связок.2004–2005 не интерполированы.2003V6/6MT не перенесён с coupe. Coupe/Hybrid остаются отдельной очередью.",
        ),
        (
            "Hyundai",
            "Elantra",
            "MD/UD",
            "2011–2016",
            "17 связок:1.8MPI6MT/6AT2011–2016;Sport2.0GDI6MT2014–2015 и6AT2014–2016. Места подтверждены2014/2016;масла2014обадвигателя,2016только1.8. Sport6MT2016 неоднозначен;не опубликован.",
        ),
        (
            "Nissan",
            "Rogue",
            "T32",
            "2014–2016",
            "12 конфигураций:QR25DE2.5/CVT,FWD/AWD,обычные5мест либо7местS/SVFamilyPackage. Один тип CVT, не два разных агрегата. NS-3 и масло0W20/4.6Lсфильтром толькоMY2014. SelectS35/Sport/SL7seats исключены.",
        ),
    ]
    for make, model, gen, years, remainder in expansion:
        added = [
            g
            for g in tables["delta_from_previous_batch"]
            if g["make"] == make
            and g["model"] == model
            and gen in g["generation"]
            and g["status"].startswith("ADDED")
            and not g["status"].endswith(" / EXCLUDED")
        ]
        n = sum(g["configuration_count"] for g in added)
        plan_rows.append(
            [
                make,
                model,
                gen,
                years,
                "Новые годовые технические связки",
                f"Добавлено {n}; точные E/T/drive и годы — таблица delta",
                remainder,
                "Годовые factory brochures/specifications + exact EPA tuples где нужны; US owner manuals для мест и жидкостей",
            ]
        )
    for model, year, reason in [
        (
            "Model S",
            "2016",
            "Сохранён конкретный ранее незакрытый scope ModelS2016; не hold всей марки.",
        ),
        (
            "Model 3",
            "2020",
            "Ограниченная проверка official2017–23 manual не дала приобретённого точного MY2020 motor/drive/reduction соответствия; локальный HTTP403. Места/батарея не объявлены общим препятствием.",
        ),
    ]:
        plan_rows.append(
            [
                "Tesla",
                model,
                "конкретная US область",
                year,
                "Проверить датированную техническую идентичность",
                "Не опубликовано",
                reason,
                "Датированный US factory identity source; без подстановки текущего MY",
            ]
        )
    (OUT / "plan-vs-actual.md").write_text(
        "# План против факта\n\nИсходные годы — область поиска, не обещание всех комплектаций. В этом пакете целевая работа по старым местам: E-Class, Jetta, Evoque, Cruze, ES, Q50; таблица также сохраняет остальные143старых пробела для прозрачности. Старые 143 ключей сохранены в initial-seating-gaps.json. Не выполненные пункты не скрыты из плана.\n\n"
        + grid(
            [
                "Make",
                "Model",
                "Generation",
                "Целевые US MY",
                "План",
                "Факт",
                "Невыполнено / причина",
                "Источник / следующий шаг",
            ],
            plan_rows,
        )
        + "\n\nПараллельная проверка шести существующих семейств E-Class/Jetta/Evoque/Cruze/ES/Q50 дала дополнительные размеры и применимые масла, но не явное подтверждение мест. Все 143 старых пробела сохранены, 10 новых отдельно отражены. Не использованы фото, пример расчёта пассажирской нагрузки, места универсала/кабриолета или соседний год. Годовые документы имеют сохранённые хеши. Исходные manuals остаются в частном research cache, не в публичном ZIP.\n",
        encoding="utf-8",
    )
    metrics = {
        "delta_actions": dict(actions),
        "new_available_configurations": sum(new_periods.values()),
        "new_excluded_configurations": len(excluded_keys),
        "new_configurations_by_period": {
            k: new_periods[k] for k in ("2000–2013", "2014–2020", "2021+")
        },
        "profiles_checked_az_ru": len(technical),
        "technical_fields_with_source": sum(len(i["confirmed_facts"]) for i in technical),
        "old_seating": coverage["previous_seating_gap_progress"],
        "new_variant_ids": {
            k: vehicle_ids[k]
            for k in vehicle_ids
            if any(
                g["status"].startswith("ADDED") and any(m["catalog_key"] == k for m in g["members"])
                for g in tables["delta_from_previous_batch"]
            )
        },
    }
    dump("data-reconciliation.json", metrics)
    # Preserve the preceding checkpoint verbatim before replacing the active document.
    checkpoint = ROOT / "docs/CHECKPOINT_US_BASE_CATALOG.md"
    archive = ROOT / "docs/CHECKPOINT_US_BASE_CATALOG_04.md"
    if not archive.exists():
        archive.write_bytes(checkpoint.read_bytes())
    block = (OUT / "catalog-tables.md").read_text(encoding="utf-8")
    block = START + block.split(START, 1)[1].split(END, 1)[0] + END
    intro = "# Auto Expert — U.S. base catalogue, batch05\n\nBackend 0.8.1. Пакет опубликован в существующей локальной БД. Точные связки и разрывы лет сохранены. Готовность базового каталога не равна полному dossier.\n\n"
    links = "\n\n## Источники, техническое наполнение и остаток\n\n[Delta с источниками](../deliverables/VerifiedData/us-base-catalog-05/delta-with-sources.md) · [Все модели и годы](../deliverables/VerifiedData/us-base-catalog-05/models-and-years.md) · [Технические разделы](../deliverables/VerifiedData/us-base-catalog-05/technical-coverage.md) · [Значения и provenance AZ/RU](../deliverables/VerifiedData/us-base-catalog-05/technical-fields.json) · [Поимённый остаток мест](../deliverables/VerifiedData/us-base-catalog-05/remaining-seating.md) · [План против факта](../deliverables/VerifiedData/us-base-catalog-05/plan-vs-actual.md).\n\n"
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
    details = "\n\n" + json.dumps(
        {k: v for k, v in metrics.items() if k not in {"old_seating", "new_variant_ids"}},
        ensure_ascii=False,
        indent=2,
    )
    gap = coverage["previous_seating_gap_progress"]
    strict_growth = coverage["growth"]["cumulative_us_with_seating_counts"][
        "model_year_configurations"
    ]
    gap_note = f"\n\nСтарые {gap['initial']} seating gaps: закрыто {gap['closed']}, осталось {gap['remaining']}. Новых пробелов {gap['new_batch_gaps']}; общий остаток {gap['total_remaining_gaps']}. Рост strict на {strict_growth} = {gap['closed']} закрытый старый пробел + {strict_growth - gap['closed']} новые записи с местами.\n\n"
    brands = grid(
        ["Марка", "Модели basic", "Модели strict", "Годовые basic", "Годовые strict"],
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
    checkpoint.write_text(
        intro
        + block
        + links
        + "## Сверенные итоги после поимённых списков\n\n"
        + totals
        + gap_note
        + brands
        + "\n\nСочетания считаются отдельно от годовых строк и ревизий.\n\n```json"
        + details
        + "\n```\n\nДополнительные проверки и восстановление: [BATCH05_VALIDATION.md](BATCH05_VALIDATION.md).\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {k: v for k, v in metrics.items() if k not in {"old_seating", "new_variant_ids"}},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
