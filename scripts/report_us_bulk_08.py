"""Assemble the named US bulk checkpoint from read-only audited artifacts."""

# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path

from catalog_checkpoint_report import END, START

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def timing(name, entries):
    rows = [row for row in entries if row["operation"] == name and row["exit_code"] == 0]
    return f"{rows[-1]['wall_seconds']:.3f} s" if rows else "not measured"


def remaining_queue(new_models):
    source = (
        ROOT / "deliverables/VerifiedData/us-base-catalog-07/remaining-master-queue.md"
    ).read_text(encoding="utf-8")
    lines = [line for line in source.splitlines() if line.startswith("|")]
    result = []
    for line in lines[2:]:
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) == 3 and (parts[0], parts[1]) not in new_models:
            result.append(line)
    return "\n".join([lines[0], lines[1], *result]), len(result)


def main():
    tables = (OUT / "catalog-tables.md").read_text(encoding="utf-8")
    block = START + tables.split(START, 1)[1].split(END, 1)[0] + END
    coverage = load("coverage.json")
    table_data = load("catalog-tables.json")
    fact_delta = load("fact-delta.json")
    factory = load("factory-prepared.json")
    epa = load("epa-benchmark.json")
    timings = load("operation-timings.json")
    assert coverage["status"] == "PASS"
    assert table_data["reconciliation"]["status"] == "PASS"
    assert table_data["reconciliation"]["strict_output_configuration_count"] == 560
    assert table_data["reconciliation"]["delta_configuration_count"] == 152
    assert fact_delta["batch_new_configurations"] == 60
    new_models = {
        (row["make"], row["model"])
        for row in table_data["delta_from_previous_batch"]
        if row["status"].startswith("ADDED")
    }
    assert new_models == {
        ("Audi", "Q3"),
        ("Hyundai", "Santa Fe"),
        ("Toyota", "Highlander"),
        ("Nissan", "Pathfinder"),
    }
    queue, queue_count = remaining_queue(new_models)
    base = coverage["cumulative_basic_counts"]
    strict = coverage["cumulative_us_with_seating_counts"]
    gaps = coverage["previous_seating_gap_progress"]
    assert gaps["initial"] == gaps["remaining"] == 230
    fields = fact_delta["existing_configuration_newly_confirmed_fields"]
    oil = fact_delta["batch_new_configuration_fact_fields"].get("engine_oil_capacity_us_qt", 0)
    body = f"""# Auto Expert — U.S. bulk data 08: published checkpoint

Опубликовано в существующей локальной БД. Границы: 17 утверждённых марок, рынок США,
model years с 2000 года; Skoda исключена. Таблицы ниже показывают только точные
подтверждённые версии. Исторический batch07 и исходные записи сохранены.

{block}

## Проверенный результат после поимённого списка

Добавлены 4 модели и поколения: Audi Q3 8U MY2015–2017, Hyundai Santa Fe NC
MY2016–2017, Toyota Highlander III MY2014–2016, Nissan Pathfinder R52
MY2015–2016. Это **60 новых конфигураций** с точной применимостью двигателя,
коробки, привода, кузова, года и мест. Параллельно обогащены **92 существующие
конфигурации Kia** на основе годовых таблиц Kia Media; подробные версии и поля
перечислены в Delta выше. Никакие исследовательские строки EPA не выдаются за
проверенный автомобиль.

| Метрика | Дельта batch08 | Накопительно, базовый каталог | Накопительно, строгая выдача с местами |
|---|---:|---:|---:|
| Марки | 0 новых | {base["makes"]} | {strict["makes"]} |
| Модели | +4 | {base["models"]} | {strict["models"]} |
| Поколения | +4 | {base["generations"]} | {strict["generations"]} |
| Рынок × поколение | +4 | {base["market_variants"]} | {strict["market_variants"]} |
| Двигательные варианты | +12 | {base["engine_variants"]} | {strict["engine_variants"]} |
| Варианты коробок | +5 | {base["transmission_variants"]} | {strict["transmission_variants"]} |
| Подтверждённые двигатель × коробка | +12 | {base["engine_transmission_combinations"]} | {strict["engine_transmission_combinations"]} |
| Годовые конфигурации | +60 | {base["model_year_configurations"]} | {strict["model_year_configurations"]} |

Без подтверждённого числа мест остаются **{gaps["remaining"]} старых конфигураций**
(из 230 на входе; новых таких пробелов 0). Они не проходят фильтр по числу мест,
но доступны по прежним правилам при отсутствии этого ограничения. Это отдельный
остаток и не замедлял расширение четырёх семейств. Tesla остаётся 17-й маркой без
подтверждённой базовой конфигурации; Land Rover присутствует в базовом каталоге,
но не в строгом выходе с местами.

## Действительно новые технические данные

Сравнение с закрытой резервной копией до batch08 дало
**{fact_delta["batch_new_configuration_confirmed_fact_cells"]}** новых подтверждённых
ячеек «конфигурация × поле» в 60 новых автомобилях и
**{fact_delta["existing_configuration_newly_confirmed_fact_cells"]}** в 92 прежних
автомобилях Kia: всего **{fact_delta["newly_confirmed_fact_cells_total"]}**.
Это число полей с точной годовой/вариантной применимостью, не число независимых
заводских документов или уникальных механических фактов. Сверка обнаружила
{len(fact_delta["existing_configuration_confirmed_value_conflicts"])} конфликтов
с прежними подтверждёнными значениями. Повторные публикации и 7 302 строки
EPA research-кандидатов в эти числа не включены.

Заполнены/расширены подкатегории: двигатель (объём, цилиндры, мощность и впрыск),
тип коробки, привод, число мест, длина/ширина/высота/колёсная база, бак,
передняя/задняя подвеска, тормоза и колёса/шины там, где заводская таблица
подтвердила применимость. Объём моторного масла добавлен к {oil} Audi Q3,
но вязкость/допуск масла в этом пакете не подтверждены. Подтверждённый исходный
октановый показатель AKI добавлен к {fields.get("octane_aki", 0)} Kia;
автоматического перевода AKI в RON нет. Тип коробки подтверждён для всех 60
новых конфигураций; жидкость и применимый объём коробки не заполнены без
однозначного заводского источника. Опции по комплектации и общие строки с
неоднозначным `optional` не распространялись на другие версии.

Kia pipeline повторно использовал {factory["counts"]["documents_selected"]}
закэшированных годовых документов и обработал {factory["counts"]["rows_processed"]}
строки; {factory["counts"]["source_rows_quarantined"]} неоднозначных строк
помещены в карантин. Из {factory["counts"]["source_facts_extracted"]}
извлечённых исходных фактов к текущим вариантам безопасно применены
{factory["counts"]["unique_source_facts_applied"]} уникальных исходных фактов.
Исходная шкала единиц и применимость сохранены. Отдельно {load("factory-localization-prepared.json")["counts"]["localized_values"]}
AZ/RU-подписей — представление уже существующих значений, не дополнительные
технические факты.

## Источники, доступ и измеренное время

10 годовых US брошюр производителя Audi/Hyundai/Toyota/Nissan получены через
опубликованные индексы; 239 PDF-страниц просмотрены программным индексатором,
44 страницы отобраны как технические. Документы и SHA/локаторы проверены в
[`documents.json`](../deliverables/VerifiedData/us-bulk-data-08/documents.json).
Дополнительные идентификаторы поколения подтверждены документами производителя
на NHTSA. Свежий официальный EPA ZIP использован как
[candidate index](../deliverables/VerifiedData/us-bulk-data-08/epa-summary.md):
7 302 строк для 74 моделей master-list, **0** заводских конфигураций опубликовано
из EPA без отдельного matching. Lemon Manuals проверен ограниченными прямыми
запросами; `robots.txt` и целевая страница завершились connect timeout, так что
данных из Lemon в этом batch **0**. Подробный
[receipt](../deliverables/VerifiedData/us-bulk-data-08/lemon-access.md).

| Операция | Тип | Фактическое wall time |
|---|---|---:|
| Найти точные ссылки в индексах брошюр, успешный проход | Программно | {timing("factory_index_discovery", timings)} |
| Скачать 10 PDF | Программно / сеть | {timing("factory_pdf_acquisition", timings)} |
| Извлечь PDF, cold / warm cache | Программно | {timing("factory_pdf_cold_extraction", timings)} / {timing("factory_pdf_warm_extraction", timings)} |
| Разобрать 25 Kia HTML из локального cache | Программно | {factory["duration_seconds"]:.3f} s |
| EPA candidate index, cold / warm cache | Программно | {epa["cold"]["wall_seconds"]:.3f} s / {epa["warm"]["wall_seconds"]:.3f} s |
| Подготовить reviewed manifest | Программно | {timing("batch08-prepare", timings)} |
| Опубликовать новый catalogue manifest после устранения name conflict | Программно | {timing("batch08-publish-after-name-repair", timings)} |
| Опубликовать Kia enrichment | Программно | {load("factory-publication.json")["seconds"]:.3f} s |
| Полная backend regression (последний записанный прогон) | Программно | {timing("full-backend-regression-final", timings)} |
| Разбор неоднозначной применимости таблиц/моделей | Агент, отдельная проверка | Индивидуальное время не инструментировано; не включено в программные замеры |
| Deployment package | Программно | В отдельном packaging receipt после сборки |

Быстрый content-hash cache устранил повторное извлечение одного и того же PDF/EPA
содержимого: PDF cold/warm и EPA cold/warm показаны выше. Это сравнение одного
входа при разных состояниях cache, не доказательство ускорения относительно
старого importer на идентичной нагрузке. Длительность сетевого чтения и
ручного разбора не замаскирована под время парсера.

## Оставшаяся очередь owner master-list

{queue}

Осталось {queue_count} названных, пока не покрытых модельных позиций из
предыдущей очереди. Внутри уже опубликованных моделей также остаются другие
годы, кузова, двигатели и рынки; готовность в таблицах выше не распространяется
на них. Следующий batch должен брать эти записи по локальной релевантности,
приоритету марки и году, затем по качеству доступных источников. Телефон,
Hetzner, ownership-cost, глубокие досье, изображения и коммерция отложены.
"""
    for path in (OUT / "checkpoint.md", ROOT / "docs/CHECKPOINT_US_BASE_CATALOG.md"):
        path.write_text(body, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "delta_records": table_data["reconciliation"]["delta_configuration_count"],
                "strict_records": strict["model_year_configurations"],
                "remaining_models": queue_count,
                "new_fact_cells": fact_delta["newly_confirmed_fact_cells_total"],
            }
        )
    )


if __name__ == "__main__":
    main()
