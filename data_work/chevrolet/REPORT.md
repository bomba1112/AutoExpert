# Chevrolet — отчёт по базе технических данных US

Сформировано 2026-10-03T18:00:06+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Malibu | VIII | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Malibu | IX | 2016–2025 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Cruze | US2014-2015 | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Cruze | II | 2016–2019 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Equinox | 2010 redesign (US) | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Equinox | US2018-2024 | 2018–2024 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Equinox | US2025+ | 2025–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ◐ | ● | ◐ | ● | ◐ | ● | ● | ● |
| Trax | US2015-2022 | 2015–2022 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Trax | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ○ | ● | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 62, частично 49, нет 24, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 3430 |
| known_issues | 0 | 253 |
| maintenance_schedule_items | 0 | 341 |

## 3. Журнал пробелов

Записей в журнале пробелов: 329 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 118 | chevrolet-malibu-us-2014-2.0l-4cyl-turbo-ice-a-s6-fwd; chevrolet-malibu-us-2014-2.4l-4cyl-hev-a-s6-fwd; chevrolet-malibu-us-2014-2.5l-4cyl-ice-a-s6-fwd |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 30 | chevrolet/malibu MY2022 (official-208c55b3d0b7); chevrolet/malibu MY2021 (official-6582638ee059); chevrolet/malibu MY2014 (official-7461695d71a7) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 21 | chevrolet/malibu MY2016 (official-f395cde9a52c); chevrolet/cruze MY2014 (official-1256553bcf46); chevrolet/cruze MY2019 (official-4d52e1c95054) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 18 | chevrolet/malibu MY2019 (official-881052775fa3); chevrolet/malibu MY2016 (official-ee9f43223777); chevrolet/malibu MY2018 (official-f212af069990) |
| maintenance:engine_air_filter | p.N: replaced when the Engine Air Filter Life System indicates; no fixed interval printed | 10 | chevrolet/malibu MY2023 (chevrolet-malibu-2023-owner-manual); chevrolet/malibu MY2024 (chevrolet-malibu-2024-owner-manual); chevrolet/malibu MY2025 (chevrolet-malibu-2025-owner-manual) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 9 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| coolant | not found unambiguously in the available US owner's manuals | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| power_hp | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| torque_lb_ft | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| tires | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| front_suspension | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| rear_suspension | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| front_brakes | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| steering | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| ground_clearance | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| cargo_l | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| fuel_tank_l | value N outside the validator range; not used | 5 | chevrolet/malibu official-fc38f1d0ac28 p.243; chevrolet/cruze official-1256553bcf46 p.381; chevrolet/cruze official-943cab632404 p.376 |
| maintenance:engine_air_filter | p.N normal: replaced when the Engine Air Filter Life System indicates; no fixed interval printed | 5 | chevrolet/malibu MY2020 (chevrolet-malibu-2020-owner-manual); chevrolet/malibu MY2021 (chevrolet-malibu-2021-owner-manual); chevrolet/malibu MY2022 (chevrolet-malibu-2022-owner-manual) |
| maintenance:engine_air_filter | p.N severe: replaced when the Engine Air Filter Life System indicates; no fixed interval printed | 5 | chevrolet/malibu MY2020 (chevrolet-malibu-2020-owner-manual); chevrolet/malibu MY2021 (chevrolet-malibu-2021-owner-manual); chevrolet/malibu MY2022 (chevrolet-malibu-2022-owner-manual) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 5 | chevrolet/trax MY2020 (official-2ea79b3a1db0); chevrolet/trax MY2016 (official-60eedef6f4f5); chevrolet/trax MY2017 (official-91f5d2c9ba4d) |
| engine_oil_capacity_drain_refill_l | value N outside the validator range; not used | 4 | chevrolet/malibu official-f395cde9a52c p.181; chevrolet/malibu official-fc38f1d0ac28 p.203; chevrolet/trax official-2ea79b3a1db0 p.223 |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"'] | 4 | chevrolet/malibu MY2016 (official-ee9f43223777); chevrolet/malibu MY2017 (official-f8c33d570c8c); chevrolet/trax MY2019 (official-9f2b2b3bcf7b) |
| transmission_fluid_capacity_l | value N outside the validator range; not used | 3 | chevrolet/cruze official-a94f00433954 p.374; chevrolet/cruze official-ecf4531dacd6 p.365; chevrolet/cruze official-ffa4b0c4604c p.340 |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 3 | chevrolet/cruze US2014-2015; chevrolet/cruze II; chevrolet/equinox 2010 redesign (US) |
| fuel_tank_l | not found unambiguously in the available US owner's manuals | 2 | chevrolet/cruze US2014-2015; chevrolet/equinox 2010 redesign (US) |
| coolant_capacity_l | value N outside the validator range; not used | 1 | chevrolet/malibu official-881052775fa3 p.343 |
| fuel_tank_l | one document gives N values: ['N', 'N', 'N'] | 1 | chevrolet/cruze MY2019 (official-4d52e1c95054) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 1 | chevrolet/cruze MY2016 (official-ffa4b0c4604c) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 1 | chevrolet/cruze MY2016 (official-ffa4b0c4604c) |
| front_brakes | not found unambiguously in the available US press specification pages | 1 | chevrolet/equinox US2025+ |
| brake_fluid | one document gives N values: ['"DOT N or DOT N"', '"DOT N"', '"DOT N"'] | 1 | chevrolet/trax MY2015 (official-5423abd06f81) |
| maintenance:schedule | no generation for MYN | 1 | chevrolet/trax MY2023 (carmans-2023-chevrolet-trax-maintenance) |

## 4. Конфликты источников

Конфликтов: 3. По решениям:

- official document kept over the copy: 2
- official value is the main value; the vPIC Canadian value stays a SECO: 1

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Equinox | chevrolet/equinox US2018-2024 MY2021 | engine_oil_oem_approval | dexos1 | ['dexos1; dexos2'] | official document kept over the copy |
| Equinox | chevrolet/equinox US2018-2024 MY2021 | engine_oil_viscosity | SAE 0W-20 | ['SAE 5W-30'] | official document kept over the copy |
| Equinox | chevrolet/equinox US2025+ MY2025 | curb_weight_kg | [1555.0] | [1625] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 65 записей (10% каждой линейки), расхождений 0.
- cruze: 13 проверено, 0 расхождений
- equinox: 27 проверено, 0 расхождений
- malibu: 15 проверено, 0 расхождений
- trax: 10 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Malibu IX (2016–2025): consumerreports.org: "Completely redesigned for 2016, the Malibu is much sleeker than the boxy sedan it replaced." (https://www.consumerreports.org/cars/chevrolet/malibu/); cars.com: "A stylish redesign for 2016 made the Malibu one of the better-looking entries in the mid-size sedan category" (https
- Cruze II (2016–2019): consumerreports.org: "A redesigned Cruze was introduced for 2016." (https://www.consumerreports.org/cars/chevrolet/cruze/); cars.com: "The Cruze was redesigned for 2016, gaining sleeker styling and lots of new tech features" (https://www.cars.com/research/chevrolet-cruze/) [media: generation starts 
- Equinox US2018-2024 (2018–2024): consumerreports.org: "The new Equinox has tidier dimensions" (https://www.consumerreports.org/cars/chevrolet/equinox/); cars.com: "With SUV sales on the rise, Chevy released a redesigned Equinox for 2018." (https://www.cars.com/research/chevrolet-equinox/) [media: generation starts MY2018]
- Equinox US2025+ (2025–2026): consumerreports.org: "Redesigned for 2025, the Chevrolet Equinox is similar in size and mechanical details to the SUV it supplants." (https://www.consumerreports.org/cars/chevrolet/equinox/); cars.com: "The Chevrolet Equinox entered a new generation for 2025 with a bold, truck-inspired redesign." (h
- Trax US2024+ (2024–2026): consumerreports.org: "The redesigned Trax is almost a foot longer than its predecessor." (https://www.consumerreports.org/cars/chevrolet/trax/); cars.com: "Redesigned on larger, FWD-only platform for 2024" (https://www.cars.com/research/chevrolet-trax/) [media: generation starts MY2024]

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- chevrolet/malibu: --prune-stale, код 0, {"raw_documents_seen": 84, "source_records_new": 13, "te_existing": 824, "configurations": 27, "configurations_linked": 5, "configurations_research_only": 22, "issues_existing": 70, "maintenance_new": 86}
- chevrolet/cruze: --prune-stale, код 0, {"raw_documents_seen": 42, "source_records_new": 7, "te_existing": 860, "configurations": 28, "configurations_research_only": 26, "configurations_linked": 2, "issues_existing": 63, "maintenance_new": 100}
- chevrolet/equinox: --prune-stale, код 0, {"raw_documents_seen": 90, "source_records_new": 13, "te_existing": 1205, "configurations": 44, "configurations_research_only": 44, "issues_existing": 75, "maintenance_new": 87}
- chevrolet/trax: --prune-stale, код 0, {"raw_documents_seen": 66, "source_records_new": 11, "te_existing": 541, "configurations": 19, "configurations_research_only": 19, "issues_existing": 45, "maintenance_new": 68}
