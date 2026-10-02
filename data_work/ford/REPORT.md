# Ford — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fusion | US2014-2020 | 2014–2020 | ◐ | ◐ | ● | ● | ○ | ● | ◐ | ● | ○ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 7, частично 4, нет 4, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 799 |
| known_issues | 0 | 54 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 135 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 46 | ford-fusion-us-2014-1.5l-4cyl-turbo-ice-a-s6-fwd; ford-fusion-us-2014-1.6l-4cyl-turbo-ice-m-6-spd-fwd; ford-fusion-us-2014-2.0l-4cyl-hev-a-variable-gear-ratios-fwd |
| fuel_tank_l | value N outside the validator range; not used | 19 | ford/fusion carmans-2014-ford-fusion-hybrid p.152; ford/fusion carmans-2014-ford-fusion-hybrid p.220; ford/fusion carmans-2014-ford-fusion-hybrid p.220 |
| engine_oil_specification | engine not stated; EPA lists several engines | 19 | ford/fusion MY2014 (carmans-2014-ford-fusion); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid); ford/fusion MY2015 (carmans-2015-ford-fusion) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 12 | ford/fusion MY2016 (carmans-2016-ford-fusion); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 7 | ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid); ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid) |
| coolant_capacity_l | value N outside the validator range; not used | 6 | ford/fusion carmans-2014-ford-fusion-hybrid p.301; ford/fusion carmans-2015-ford-fusion-hybrid p.320; ford/fusion carmans-2016-ford-fusion-hybrid p.321 |
| coolant_capacity_l | engine not stated; EPA lists several engines | 6 | ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 4 | ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 3 | ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid); ford/fusion MY2019 (carmans-2019-ford-fusion-hybrid) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 2 | ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid) |
| transmission_fluid_capacity_l | value N outside the validator range; not used | 1 | ford/fusion carmans-2014-ford-fusion p.294 |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 1 | ford/fusion US2014-2020 |
| power_hp | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| torque_lb_ft | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| tires | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| front_suspension | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| rear_suspension | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| front_brakes | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| steering | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| ground_clearance | no US press specification page for these years | 1 | ford/fusion US2014-2020 |
| cargo_l | no US press specification page for these years | 1 | ford/fusion US2014-2020 |

## 4. Конфликты источников

Конфликтов: 4. По решениям:

- model-year manual kept over the whole-generation page (Appendix E.6): 4

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Fusion | ford/fusion US2014-2020 MY2017 | transmission_fluid_capacity_l | 8.5 | [1.0] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Fusion | ford/fusion US2014-2020 MY2018 | transmission_fluid_capacity_l | 8.5 | [1.0] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Fusion | ford/fusion US2014-2020 MY2019 | transmission_fluid_capacity_l | 8.5 | [1.0] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Fusion | ford/fusion US2014-2020 MY2020 | transmission_fluid_capacity_l | 8.5 | [1.0] | model-year manual kept over the whole-generation page (Appendix E.6) |

## 5. Выборочная перепроверка

Проверено 18 записей (10% каждой линейки), расхождений 0.
- fusion: 18 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- нет

## Изменения ранее записанных строк (последняя загрузка)

- Fusion: проблема fusion-US2014-2020-tsb-hesitation обновлена {"evidence_ids": [2, 3], "note": [null, "CarComplaints.com \"Stalling, Hesitating\" (owner reports): MY2016: #1, average cost to fix $6,000, average mileage 23,
- Fusion: проблема fusion-US2014-2020-tsb-misfire обновлена {"evidence_ids": [22, 23], "note": [null, "CarComplaints.com \"Misfire On Spark Plug #2\" (owner reports): MY2018: #3, average cost to fix $7,900, average milea
- Fusion: проблема fusion-US2014-2020-complaints-steering-loss обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 2], "note": [null, "CarComplaints.com \"Power Steering Failed\" (owner reports): MY2014: #1, avera
- Fusion: проблема fusion-US2014-2020-complaints-transmission-failure обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 3], "note": [null, "CarComplaints.com \"Transmission Failure\" (owner reports): MY2019: #3, averag

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- ford/fusion: --prune-stale, код 0, {"raw_documents_seen": 74, "source_records_new": 20, "te_existing": 750, "te_new_GENERATION": 49, "configurations": 46, "configurations_research_only": 46, "issues_existing": 54, "issues_updated": 4}
