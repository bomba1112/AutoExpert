# Tesla — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Model 3 | I | 2017–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model Y | I | 2020–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ◐ | ◐ | ○ | ◐ | ○ | ● | ● | ● |
| Model S | I | 2014–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ◐ | ○ | ◐ | ○ | ● | ● | ● |
| Model X | I | 2016–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ◐ | ◐ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 24, частично 17, нет 15, неприменимо 4.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 1570 |
| known_issues | 0 | 132 |
| maintenance_schedule_items | 0 | 32 |

## 3. Журнал пробелов

Записей в журнале пробелов: 127 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 60 | tesla-model-3-us-2017-ev-bev-a-a1-rwd; tesla-model-3-us-2018-ev-bev-a-a1-awd; tesla-model-3-us-2018-ev-bev-a-a1-rwd |
| maintenance:battery_coolant | no replacement interval: 'does not need to be replaced for the life of your vehicle under most circumstances' | 11 | tesla/model-y MY2020 (carmans-2020-tesla-model-y-maintenance); tesla/model-y MY2021 (carmans-2021-tesla-model-y-maintenance); tesla/model-y MY2022 (carmans-2022-tesla-model-y-maintenance) |
| tires | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| front_suspension | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| rear_suspension | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| front_brakes | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| steering | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| ground_clearance | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| cargo_l | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| engine_oil_capacity_l | no US owner's manual for these years | 2 | tesla/model-3 I; tesla/model-s I |
| engine_oil_viscosity | no US owner's manual for these years | 2 | tesla/model-3 I; tesla/model-s I |
| coolant | no US owner's manual for these years | 2 | tesla/model-3 I; tesla/model-s I |
| transmission_fluid | no US owner's manual for these years | 2 | tesla/model-3 I; tesla/model-s I |
| brake_fluid | no US owner's manual for these years | 2 | tesla/model-3 I; tesla/model-s I |
| fuel_tank_l | no US owner's manual for these years | 2 | tesla/model-3 I; tesla/model-s I |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 2 | tesla/model-y I; tesla/model-x I |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 2 | tesla/model-y I; tesla/model-x I |
| coolant | not found unambiguously in the available US owner's manuals | 2 | tesla/model-y I; tesla/model-x I |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 2 | tesla/model-y I; tesla/model-x I |
| brake_fluid | not found unambiguously in the available US owner's manuals | 2 | tesla/model-y I; tesla/model-x I |
| fuel_tank_l | not found unambiguously in the available US owner's manuals | 2 | tesla/model-y I; tesla/model-x I |
| maintenance:schedule | mycarusermanual edition market UNKNOWN, not US; not used | 1 | tesla/model-3 (tesla/model-3/4-door/2017-2023, mycarusermanual.com) |
| maintenance:schedule | no US-edition owner's manual with a Service Intervals list on disk for this line | 1 | tesla/model-3 |
| maintenance:schedule | mycarusermanual edition market GENERAL, not US; not used | 1 | tesla/model-y (tesla/model-y/suv/2023, mycarusermanual.com) |
| maintenance:schedule | not a North American (US) edition: cover 'North America': False; US 'Reporting Safety Defects' (NHTSA) text: F | 1 | tesla/model-x MY2021 (carmans-2021-tesla-model-x-maintenance) |

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
- tesla/model-3: --prune-stale, код 0, {"raw_documents_seen": 33, "te_existing": 444, "configurations": 19, "configurations_research_only": 19, "issues_existing": 42}
- tesla/model-y: --prune-stale, код 0, {"raw_documents_seen": 40, "source_records_new": 1, "te_existing": 309, "te_new_GENERATION": 1, "configurations": 12, "configurations_research_only": 12, "issues_existing": 39, "maintenance_existing": 8}
- tesla/model-s: --prune-stale, код 0, {"raw_documents_seen": 110, "te_existing": 515, "configurations": 18, "configurations_research_only": 18, "issues_existing": 40, "maintenance_existing": 10}
- tesla/model-x: --prune-stale, код 0, {"raw_documents_seen": 83, "source_records_new": 1, "te_existing": 300, "te_new_GENERATION": 1, "configurations": 11, "configurations_research_only": 11, "issues_existing": 11, "maintenance_existing": 14}
