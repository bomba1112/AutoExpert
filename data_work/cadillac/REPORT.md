# Cadillac — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CTS | III | 2014–2019 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| SRX | 2010-REDESIGN | 2014–2016 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Escalade | US2014-2014 | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Escalade | IV | 2015–2020 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Escalade | US2021+ | 2021–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ◐ | ● | ◐ | ◐ | ◐ | ● | ● | ● |

Итого ячеек: заполнено 34, частично 29, нет 12, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 2594 |
| known_issues | 0 | 151 |
| maintenance_schedule_items | 0 | 264 |

## 3. Журнал пробелов

Записей в журнале пробелов: 269 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 87 | cadillac-cts-us-2014-2.0l-4cyl-turbo-ice-a-s6-awd; cadillac-cts-us-2014-2.0l-4cyl-turbo-ice-a-s6-rwd; cadillac-cts-us-2014-3.0l-6cyl-ice-a-s6-awd |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 22 | cadillac/cts MY2014 (carmans-2014-cadillac-cts); cadillac/cts MY2015 (carmans-2015-cadillac-cts); cadillac/cts MY2016 (carmans-2016-cadillac-cts) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 21 | cadillac/escalade MY2014 (carmans-2014-cadillac-escalade-esv); cadillac/escalade MY2015 (carmans-2015-cadillac-escalade); cadillac/escalade MY2016 (carmans-2016-cadillac-escalade) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 16 | cadillac/cts MY2014 (carmans-2014-cadillac-cts); cadillac/cts MY2015 (carmans-2015-cadillac-cts); cadillac/cts MY2016 (carmans-2016-cadillac-cts) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 13 | cadillac/cts MY2014 (carmans-2014-cadillac-cts); cadillac/cts MY2015 (carmans-2015-cadillac-cts); cadillac/cts MY2016 (carmans-2016-cadillac-cts) |
| coolant_capacity_l | value N outside the validator range; not used | 10 | cadillac/cts carmans-2018-cadillac-cts p.354; cadillac/cts carmans-2018-cadillac-cts p.354; cadillac/cts carmans-2019-cadillac-cts p.360 |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 8 | cadillac/cts MY2018 (carmans-2018-cadillac-cts); cadillac/cts MY2019 (carmans-2019-cadillac-cts); cadillac/cts MY2019 (official-52554d6eb793) |
| engine_oil_capacity_l | one document gives N values: ['N', 'N'] | 5 | cadillac/cts MY2017 (carmans-2017-cadillac-cts); cadillac/cts MY2018 (carmans-2018-cadillac-cts); cadillac/cts MY2016 (official-7001f7da5e90) |
| fuel_tank_l | value N outside the validator range; not used | 5 | cadillac/escalade carmans-2014-cadillac-escalade-esv p.339; cadillac/escalade official-2d17cb7dff62 p.438; cadillac/escalade official-2d17cb7dff62 p.438 |
| coolant | not found unambiguously in the available US owner's manuals | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade IV |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| power_hp | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| torque_lb_ft | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| tires | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| front_suspension | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| rear_suspension | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| front_brakes | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| steering | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| ground_clearance | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| cargo_l | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"'] | 4 | cadillac/srx MY2014 (carmans-2014-cadillac-srx); cadillac/srx MY2014 (official-45f6ad75f1af); cadillac/escalade MY2014 (carmans-2014-cadillac-escalade-esv) |
| maintenance:engine_air_filter | p.N: replaced when the Engine Air Filter Life System indicates; no fixed interval printed | 4 | cadillac/escalade MY2023 (cadillac-escalade-2023-owner-manual); cadillac/escalade MY2024 (cadillac-escalade-2024-owner-manual); cadillac/escalade MY2025 (cadillac-escalade-2025-owner-manual) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 3 | cadillac/cts MY2015 (official-8c19775c4259); cadillac/escalade MY2021 (carmans-2021-cadillac-escalade); cadillac/escalade MY2022 (carmans-2022-cadillac-escalade) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 3 | cadillac/cts MY2015 (official-8c19775c4259); cadillac/escalade MY2021 (carmans-2021-cadillac-escalade); cadillac/escalade MY2022 (carmans-2022-cadillac-escalade) |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"'] | 3 | cadillac/escalade MY2023 (carmans-2023-cadillac-escalade); cadillac/escalade MY2024 (carmans-2024-cadillac-escalade); cadillac/escalade MY2026 (official-860a324b5114) |
| octane_aki | one document gives N values: ['N', 'N'] | 2 | cadillac/cts MY2019 (carmans-2019-cadillac-cts); cadillac/cts MY2019 (official-52554d6eb793) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 2 | cadillac/cts III; cadillac/escalade US2014-2014 |
| cargo_max_l | value N outside the validator range; not used | 2 | cadillac/escalade press-newsgm-escalade-2025-bf4f01fd p.1; cadillac/escalade press-newsgm-escalade-2025-bf4f01fd p.1 |
| coolant_capacity_l | one document gives N values: ['N', 'N', 'N'] | 2 | cadillac/escalade MY2023 (carmans-2023-cadillac-escalade); cadillac/escalade MY2024 (carmans-2024-cadillac-escalade) |
| cargo_l | one document gives N values: ['N', 'N'] | 2 | cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd); cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd) |
| fuel_tank_l | not found unambiguously in the available US owner's manuals | 2 | cadillac/escalade US2014-2014; cadillac/escalade IV |
| maintenance:intercooler_coolant | row 'Drain, flush, and fill intercooler system.' takes different time limits from its footnotes in the normal  | 1 | cadillac/cts MY2015 (cadillac-cts-2015-cts-v-owner-manual) |
| wheel_size_in | one document gives N values: ['N', 'N'] | 1 | cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 1 | cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd) |
| front_brakes | not found unambiguously in the available US press specification pages | 1 | cadillac/escalade US2021+ |
| ground_clearance | not found unambiguously in the available US press specification pages | 1 | cadillac/escalade US2021+ |
| cargo_l | not found unambiguously in the available US press specification pages | 1 | cadillac/escalade US2021+ |
| maintenance:schedule (diesel) | p.N: the diesel schedule is printed in the Duramax diesel supplement, which is not on disk | 1 | cadillac/escalade MY2021 (cadillac-escalade-2021-owner-manual) |
| maintenance:engine_air_filter | p.N normal: replaced when the Engine Air Filter Life System indicates; no fixed interval printed | 1 | cadillac/escalade MY2022 (cadillac-escalade-2022-owner-manual) |
| maintenance:engine_air_filter | p.N severe: replaced when the Engine Air Filter Life System indicates; no fixed interval printed | 1 | cadillac/escalade MY2022 (cadillac-escalade-2022-owner-manual) |

## 4. Конфликты источников

Конфликтов: 13. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 9
- sources of the same rank disagree; field not shown: 2
- official document kept over the copy: 2

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| CTS | cadillac/cts III MY2014 | fuel_tank_l | None | [72.0, 68.1] | sources of the same rank disagree; field not shown |
| CTS | cadillac/cts III MY2015 | fuel_tank_l | None | [72.0, 68.1] | sources of the same rank disagree; field not shown |
| CTS | cadillac/cts III MY2016 | coolant_capacity_l | 10.2 | [10.0] | official document kept over the copy |
| Escalade | cadillac/escalade IV MY2015 | engine_oil_capacity_l | 7.6 | [8.0] | official document kept over the copy |
| Escalade | cadillac/escalade US2021+ MY2025 | width_mm | [2159.0] | [2060] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | width_mm | [2159.0] | [2060] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | width_mm | [2159.0] | [2060] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | height_mm | [1933.0, 1938.0] | [1950] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | width_mm | [2159.0] | [2060] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | height_mm | [1933.0, 1938.0] | [1950] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | width_mm | [2159.0] | [2060] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | height_mm | [1933.0, 1938.0] | [1950] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Escalade | cadillac/escalade US2021+ MY2025 | width_mm | [2159.0] | [2060] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 79 записей (10% каждой линейки), расхождений 0.
- cts: 34 проверено, 0 расхождений
- escalade: 36 проверено, 0 расхождений
- srx: 9 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Escalade IV (2015–2020): consumerreports.org: "Few vehicles arrive with the Escalade's imposing look." (https://www.consumerreports.org/cars/cadillac/escalade/); cars.com: "The redesigned Escalade has a bold new face punctuated by distinctive headlights" (https://www.cars.com/articles/2015-cadillac-escalade-first-look-14206
- Escalade US2021+ (2021–2026): consumerreports.org: "The Cadillac Escalade and Escalade ESV have been redesigned for 2021, growing in size and features." (https://www.consumerreports.org/cars/cadillac/escalade/); cars.com: "The brand has unveiled the completely redesigned 2021 model" (https://www.cars.com/articles/2021-cadillac-e

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- cadillac/cts: --prune-stale, код 0, {"raw_documents_seen": 59, "source_records_new": 54, "te_new_GENERATION": 493, "te_new_ENGINE": 7, "te_new_CONFIGURATION": 479, "configurations": 41, "configurations_research_only": 41, "issues_new": 37, "maintenance_new": 123}
- cadillac/srx: --prune-stale, код 0, {"raw_documents_seen": 25, "source_records_new": 17, "te_new_GENERATION": 172, "te_new_CONFIGURATION": 66, "configurations": 6, "configurations_linked": 6, "issues_new": 20, "maintenance_new": 29}
- cadillac/escalade: --prune-stale, код 0, {"raw_documents_seen": 109, "source_records_new": 98, "te_new_GENERATION": 897, "te_new_CONFIGURATION": 480, "configurations": 40, "configurations_research_only": 38, "configurations_linked": 2, "issues_new": 94, "maintenance_new": 112}
