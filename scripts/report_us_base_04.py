"""Read-only named technical and residual scope report for the published fourth batch."""

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
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-04"


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
                "Остаток старых 220" if m["catalog_key"] in old else "Новый seating gap"
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
            "VI",
            "2007–2011",
            "2010 4-cylinder ICE: противоречивая таблица 2.4/5-speed при заголовках 6-speed. Нужен корректный US MY2010 factory spec. 2011 HEV не подтверждён полученной брошюрой.",
        ),
        (
            "Hyundai",
            "Sonata",
            "YF",
            "2011–2013",
            "2011 2.0T отсутствует в полученной ранней брошюре; HEV и места не перенесены. MY2013 2.4 MANUAL исключена корректирующей ревизией: рекламный текст противоречит годовой таблице комплектаций. Механика подтверждена только MY2011–2012. Бак/шасси MY2012 остались неизвестными.",
        ),
        (
            "Hyundai",
            "Elantra",
            "CN7",
            "2021–2023",
            "Места закрыты только у 2021 2.0/HEV. Для NLine и MY2022–2023 нужен применимый US manual. N опубликован только MY2023; MY2022 N требует отдельной годовой заводской таблицы. NLine MT MY2023 исключён.",
        ),
        (
            "Kia",
            "K5",
            "DL3",
            "2021–2023",
            "Места/масла/жидкости подтверждены для MY2021. Нужны US manuals MY2022–2023. Бак 1.6 MY2021–2022 зависит от LX/других trim — общего значения нет. Противоречивые coolant capacities не опубликованы.",
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
    plan_rows.append(
        [
            "Tesla",
            "Model S",
            "проверка датированного US scope",
            "2016",
            "Проверить конкретную US MY2016 область",
            "Не опубликовано",
            "Нет достаточного датированного US MY2016 evidence для motor/reduction-gear/battery variants и rear-facing optional child seating",
            "Индекс/имя PDF и текущая страница другого MY не являются доказательством. Найти доступное датированное US factory document; просмотренный owner-manual mirror вернул 403, обход не выполнялся.",
        ]
    )
    (OUT / "plan-vs-actual.md").write_text(
        "# План против факта\n\nИсходные годы — область поиска, не обещание всех комплектаций. Старые 220 ключей сохранены в initial-seating-gaps.json. Не выполненные пункты не скрыты из плана.\n\n"
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
        + "\n\nДополнительный остаток: жидкость 8AT Sonata 2.0T MY2018–2019 не подтверждена однозначно общей таблицей руководства; спецификация 6AT не перенесена. BMW MY2018 минимальное AKI 89 и рекомендуемое AKI 91 различаются; RON/АИ-конвертация не выполнялась. K5 manual service-table fluid amounts не обозначены как drain/refill, если руководство этого не говорит. Публичные архивы содержат manifest/provenance, а не исходные copyrighted manuals.\n",
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
    archive = ROOT / "docs/CHECKPOINT_US_BASE_CATALOG_03.md"
    if not archive.exists():
        archive.write_bytes(checkpoint.read_bytes())
    block = (OUT / "catalog-tables.md").read_text(encoding="utf-8")
    block = START + block.split(START, 1)[1].split(END, 1)[0] + END
    intro = "# Auto Expert — U.S. base catalogue, batch04\n\nBackend 0.8.1. Пакет опубликован в существующей локальной БД. Точные связки и разрывы лет сохранены. Готовность базового каталога не равна полному dossier.\n\n"
    links = "\n\n## Источники, техническое наполнение и остаток\n\n[Delta с источниками](../deliverables/VerifiedData/us-base-catalog-04/delta-with-sources.md) · [Все модели и годы](../deliverables/VerifiedData/us-base-catalog-04/models-and-years.md) · [Технические разделы](../deliverables/VerifiedData/us-base-catalog-04/technical-coverage.md) · [Значения и provenance AZ/RU](../deliverables/VerifiedData/us-base-catalog-04/technical-fields.json) · [Поимённый остаток мест](../deliverables/VerifiedData/us-base-catalog-04/remaining-seating.md) · [План против факта](../deliverables/VerifiedData/us-base-catalog-04/plan-vs-actual.md).\n\n"
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
        + "\n```\n\nДополнительные проверки и восстановление: [BATCH04_VALIDATION.md](BATCH04_VALIDATION.md).\n",
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
