# Ford — отчёт по базе технических данных US

Сформировано 2026-10-03T18:00:06+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fusion | US2014-2020 | 2014–2020 | ◐ | ◐ | ● | ● | ○ | ● | ◐ | ● | ● | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 8, частично 4, нет 3, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 799 |
| known_issues | 0 | 54 |
| maintenance_schedule_items | 0 | 96 |

## 3. Журнал пробелов

Записей в журнале пробелов: 192 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 46 | ford-fusion-us-2014-1.5l-4cyl-turbo-ice-a-s6-fwd; ford-fusion-us-2014-1.6l-4cyl-turbo-ice-m-6-spd-fwd; ford-fusion-us-2014-2.0l-4cyl-hev-a-variable-gear-ratios-fwd |
| fuel_tank_l | value N outside the validator range; not used | 19 | ford/fusion carmans-2014-ford-fusion-hybrid p.152; ford/fusion carmans-2014-ford-fusion-hybrid p.220; ford/fusion carmans-2014-ford-fusion-hybrid p.220 |
| engine_oil_specification | engine not stated; EPA lists several engines | 19 | ford/fusion MY2014 (carmans-2014-ford-fusion); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid); ford/fusion MY2015 (carmans-2015-ford-fusion) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 12 | ford/fusion MY2016 (carmans-2016-ford-fusion); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion) |
| maintenance:cabin_air_filter | p.N 'Operating in dusty or sandy conditions (such as unpaved or dusty roads)': 'Replace cabin air filter.' has | 8 | ford/fusion MY2014 (carmans-2014-ford-fusion-maintenance); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid-maintenance); ford/fusion MY2015 (carmans-2015-ford-fusion-maintenance) |
| maintenance:engine_air_filter | p.N 'Operating in dusty or sandy conditions (such as unpaved or dusty roads)': 'Replace engine air filter.' ha | 8 | ford/fusion MY2014 (carmans-2014-ford-fusion-maintenance); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid-maintenance); ford/fusion MY2015 (carmans-2015-ford-fusion-maintenance) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 7 | ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid); ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid) |
| maintenance:cabin_air_filter | p.N 'Extensive idling or low-speed driving for long distances, as in heavy commercial use (such as delivery, t | 7 | ford/fusion MY2014 (carmans-2014-ford-fusion-maintenance); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid-maintenance); ford/fusion MY2015 (carmans-2015-ford-fusion-maintenance) |
| maintenance:engine_air_filter | p.N 'Extensive idling or low-speed driving for long distances, as in heavy commercial use (such as delivery, t | 7 | ford/fusion MY2014 (carmans-2014-ford-fusion-maintenance); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid-maintenance); ford/fusion MY2015 (carmans-2015-ford-fusion-maintenance) |
| coolant_capacity_l | value N outside the validator range; not used | 6 | ford/fusion carmans-2014-ford-fusion-hybrid p.301; ford/fusion carmans-2015-ford-fusion-hybrid p.320; ford/fusion carmans-2016-ford-fusion-hybrid p.321 |
| coolant_capacity_l | engine not stated; EPA lists several engines | 6 | ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid) |
| maintenance:cabin_air_filter | p.N 'Extensive Idling or Low-speed Driving for Long Distances, as in Heavy Commercial Use (Such as Delivery, T | 6 | ford/fusion MY2018 (carmans-2018-ford-fusion-maintenance); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid-maintenance); ford/fusion MY2019 (carmans-2019-ford-fusion-maintenance) |
| maintenance:engine_air_filter | p.N 'Extensive Idling or Low-speed Driving for Long Distances, as in Heavy Commercial Use (Such as Delivery, T | 6 | ford/fusion MY2018 (carmans-2018-ford-fusion-maintenance); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid-maintenance); ford/fusion MY2019 (carmans-2019-ford-fusion-maintenance) |
| maintenance:cabin_air_filter | p.N 'Operating in Dusty or Sandy Conditions (Such as Unpaved or Dusty Roads)': 'Replace cabin air filter.' has | 6 | ford/fusion MY2018 (carmans-2018-ford-fusion-maintenance); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid-maintenance); ford/fusion MY2019 (carmans-2019-ford-fusion-maintenance) |
| maintenance:engine_air_filter | p.N 'Operating in Dusty or Sandy Conditions (Such as Unpaved or Dusty Roads)': 'Replace engine air filter.' ha | 6 | ford/fusion MY2018 (carmans-2018-ford-fusion-maintenance); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid-maintenance); ford/fusion MY2019 (carmans-2019-ford-fusion-maintenance) |
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
| maintenance:cabin_air_filter | p.N 'Extensive idling or low-speed driving for long distances': 'Replace cabin air filter.' has no fixed inter | 1 | ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid-maintenance) |
| maintenance:engine_air_filter | p.N 'Extensive idling or low-speed driving for long distances': 'Replace engine air filter.' has no fixed inte | 1 | ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid-maintenance) |
| maintenance:engine_coolant | p.N: subsequent interval printed as N mi (N km) after a first one of N mi; looks like a misprint, subsequent i | 1 | ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid-maintenance) |

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

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- ford/fusion: --prune-stale, код 0, {"raw_documents_seen": 88, "source_records_new": 14, "te_existing": 799, "configurations": 46, "configurations_research_only": 46, "issues_existing": 54, "maintenance_new": 96}
