# Tesla — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Model 3 | I | 2017–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model Y | I | 2020–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model S | I | 2014–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model X | I | 2016–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 24, частично 12, нет 20, неприменимо 4.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 1568 |
| known_issues | 0 | 132 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 112 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 60 | tesla-model-3-us-2017-ev-bev-a-a1-rwd; tesla-model-3-us-2018-ev-bev-a-a1-awd; tesla-model-3-us-2018-ev-bev-a-a1-rwd |
| engine_oil_capacity_l | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| engine_oil_viscosity | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| coolant | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| transmission_fluid | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| brake_fluid | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| fuel_tank_l | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| tires | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| front_suspension | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| rear_suspension | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| front_brakes | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| steering | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| ground_clearance | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| cargo_l | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |

## 4. Конфликты источников

Конфликтов: 0. По решениям:


## 5. Выборочная перепроверка

Проверено 34 записей (10% каждой линейки), расхождений 0.
- model-3: 10 проверено, 0 расхождений
- model-s: 15 проверено, 0 расхождений
- model-x: 3 проверено, 0 расхождений
- model-y: 6 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Model Y: MY2025: detected boundary (vPIC Canadian specifications: overall width 192 -> 198 cm (MY2024 -> MY2025; a change of 6 cm or more)) dropped; consumerreports.org: "the Model Y received an extensive update for 2025, with a freshened appearance with more Cybertruck-like horizontal lighting, front and re

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- tesla/model-3: --prune-stale, код 0, {"raw_documents_seen": 33, "source_records_new": 29, "te_new_GENERATION": 200, "te_new_CONFIGURATION": 244, "configurations": 19, "configurations_research_only": 19, "issues_new": 42}
- tesla/model-y: --prune-stale, код 0, {"raw_documents_seen": 35, "source_records_new": 26, "te_new_GENERATION": 153, "te_new_CONFIGURATION": 156, "configurations": 12, "configurations_research_only": 12, "issues_new": 39}
- tesla/model-s: --prune-stale, код 0, {"raw_documents_seen": 106, "source_records_new": 92, "te_new_GENERATION": 183, "te_new_CONFIGURATION": 332, "configurations": 18, "configurations_research_only": 18, "issues_new": 40}
- tesla/model-x: --prune-stale, код 0, {"raw_documents_seen": 79, "source_records_new": 64, "te_new_GENERATION": 92, "te_new_CONFIGURATION": 208, "configurations": 11, "configurations_research_only": 11, "issues_new": 11}
