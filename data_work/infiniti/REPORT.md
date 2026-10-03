# Infiniti — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

**Статус:** Загружена до получения решения владельца остановить загрузку этой группы марок (коммит f47df93); по решению владельца оставлена как есть.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q50 | V37 | 2014–2024 | ● | ◐ | ● | ● | ● | ● | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |
| QX60 (+JX) | L50 | 2014–2020 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ● | ◐ | ● | ◐ | ● | ● | ● |
| QX60 (+JX) | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ● | ◐ | ◐ | ● | ● | ● | ● |
| FX / QX70 | US2014-2017 | 2014–2017 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ● | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 47, частично 13, нет 0, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 1940 |
| known_issues | 0 | 74 |
| maintenance_schedule_items | 0 | 447 |

## 3. Журнал пробелов

Записей в журнале пробелов: 223 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 81 | infiniti-q50-us-2014-3.5l-6cyl-hev-a-s7-awd; infiniti-q50-us-2014-3.5l-6cyl-hev-a-s7-rwd; infiniti-q50-us-2014-3.7l-6cyl-ice-a-s7-awd |
| octane_aki | one document gives N values: ['N', 'N'] | 23 | infiniti/q50 MY2017 (official-6c4f53e95a3b); infiniti/q50 MY2016 (official-8326bed2fcdc); infiniti/q50 MY2018 (official-859f6f6c908a) |
| fuel_tank_l | value N outside the validator range; not used | 15 | infiniti/qx60 official-0631da7f7255 p.182; infiniti/qx60 official-1d31600339bc p.115; infiniti/qx60 official-273175b7459f p.118 |
| maintenance:schedule | the owner's manual prints no maintenance schedule; it refers to the separate "Service and Maintenance Guide" | 10 | infiniti/q50 MY2014 (official-b9507bd9e1ec); infiniti/q50 MY2014 (official-a07a1fda2f02); infiniti/q50 MY2016 (official-d2af3b4d6870) |
| maintenance:suspension | 'Axle & suspension parts' (normal) listed at [N, N, N, N, N, N, N] miles: not a regular interval; not converte | 10 | infiniti/q50 MY2014 (official-da4079961577); infiniti/q50 MY2014 (official-42ba75439b84); infiniti/q50 MY2015 (official-4bcd34582bda) |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 8 | infiniti/q50 MY2020 (official-55b3819856e8); infiniti/q50 MY2024 (official-5893c25aeb89); infiniti/q50 MY2017 (official-7ca479957a94) |
| octane_ron | one document gives N values: ['N', 'N', 'N'] | 7 | infiniti/q50 MY2020 (official-55b3819856e8); infiniti/q50 MY2024 (official-5893c25aeb89); infiniti/q50 MY2018 (official-7ed9946bd145) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 7 | infiniti/q50 MY2018 (official-7ed9946bd145); infiniti/q50 MY2018 (official-859f6f6c908a); infiniti/q50 MY2019 (official-b0b04e7a95d1) |
| engine_oil_capacity_without_filter_l | engine not stated; EPA lists several engines | 7 | infiniti/q50 MY2018 (official-859f6f6c908a); infiniti/qx60 MY2016 (official-1d31600339bc); infiniti/qx60 MY2015 (official-273175b7459f) |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N'] | 7 | infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16); infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16); infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N', 'N', 'N'] | 4 | infiniti/q50 MY2024 (official-5893c25aeb89); infiniti/q50 MY2022 (official-849f6a8b0c88); infiniti/q50 MY2021 (official-dfddd4dab604) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 4 | infiniti/q50 MY2017 (official-7ca479957a94); infiniti/q50 MY2016 (official-8326bed2fcdc); infiniti/q50 MY2016 (official-d2af3b4d6870) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 4 | infiniti/q50 MY2018 (official-7ed9946bd145); infiniti/q50 MY2019 (official-b0b04e7a95d1); infiniti/qx60 MY2017 (official-31644eee83fe) |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 4 | infiniti/q50 V37; infiniti/qx60 L50; infiniti/qx60 US2022+ |
| cargo_max_l | one document gives N values: ['N', 'N'] | 4 | infiniti/qx60 MY2019 (press-infinitinews-qx60-2019-8b56f0e2); infiniti/qx60 MY2019 (press-infinitinews-qx60-2019-8b56f0e2); infiniti/qx60 MY2020 (press-infinitinews-qx60-2020-538ad510) |
| maintenance:schedule | the owner's manual prints no maintenance schedule | 3 | infiniti/q50 MY2015 (official-ae9deb07fccb); infiniti/q50 MY2015 (official-4ef2ffe34b59); infiniti/fx-qx70 MY2015 (official-5b548da2e9a6) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N'] | 2 | infiniti/qx60 MY2023 (official-8c0d2cd1db19); infiniti/qx60 MY2024 (official-b29ccef1280d) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 2 | infiniti/qx60 L50; infiniti/qx60 US2022+ |
| wheel_size_in | one document gives N values: ['N', 'N'] | 2 | infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16); infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16) |
| wheel_size_in | one document gives N values: ['N', 'N', 'N'] | 2 | infiniti/fx-qx70 MY2015 (press-infinitinews-fx-qx70-2015-f1fbd308); infiniti/fx-qx70 MY2016 (press-infinitinews-fx-qx70-2016-3dcfad77) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N', 'N'] | 1 | infiniti/q50 MY2020 (official-55b3819856e8) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 1 | infiniti/q50 MY2018 (official-859f6f6c908a) |
| octane_ron | one document gives N values: ['N', 'N'] | 1 | infiniti/q50 MY2018 (official-859f6f6c908a) |
| electric_motor | one document gives N values: ['"N lb-ft @ N,Nrpm"', '"N @ N,N \\uN N,N rpm"'] | 1 | infiniti/q50 MY2017 (press-infinitinews-q50-2017-5628af5d) |
| maintenance:brake_fluid | grid row 'Brake fluid' (p.N): R marks at [N, N, N, N, N] miles do not form a regular interval; not converted | 1 | infiniti/q50 MY2016 (official-8326bed2fcdc) |
| maintenance:steering_linkage | grid row 'Steering gear and linkage, axle and suspension parts' (p.N): I marks at [N, N, N, N, N] miles do not | 1 | infiniti/q50 MY2016 (official-8326bed2fcdc) |
| maintenance:suspension | grid row 'Steering gear and linkage, axle and suspension parts' (p.N): I marks at [N, N, N, N, N] miles do not | 1 | infiniti/q50 MY2016 (official-8326bed2fcdc) |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 1 | infiniti/qx60 MY2026 (official-49246dc11c6d) |
| fuel_tank_l | one document gives N values: ['N', 'N', 'N'] | 1 | infiniti/qx60 MY2026 (official-49246dc11c6d) |
| engine_oil_capacity_drain_refill_l | one document gives N values: ['N', 'N', 'N'] | 1 | infiniti/qx60 MY2022 (official-6e8392e278ee) |
| steering | not found unambiguously in the available US press specification pages | 1 | infiniti/qx60 L50 |
| cargo_l | not found unambiguously in the available US press specification pages | 1 | infiniti/qx60 US2022+ |
| maintenance:schedule | the owner's manual prints no maintenance schedule; it refers to the separate "Maintenance Booklet" | 1 | infiniti/qx60 MY2014 (official-0631da7f7255) |
| maintenance:cabin_air_filter | 'Replace in-cabin microfilter' (normal) listed at [N, N, N, N, N, N, N, N, N, N, N] miles: not a regular inter | 1 | infiniti/qx60 MY2025 (official-58c8a2ad173c) |
| maintenance:wiper_blades | quote of 'Using Genuine NISSAN wiper blades is recommended for proper operation of the rain-sensing auto wiper | 1 | infiniti/qx60 MY2025 (official-58c8a2ad173c) |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"'] | 1 | infiniti/fx-qx70 MY2017 (official-1c14b01d4eea) |
| valvetrain | engine not stated; EPA lists several engines | 1 | infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16) |

## 4. Конфликты источников

Конфликтов: 44. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 44

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Q50 | infiniti/q50 V37 MY2020 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2023 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2024 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2023 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2024 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2017 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2023 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2024 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2023 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2024 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2017 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | length_mm | [4816.0] | [4800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2017 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2020 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2021 | track_rear_mm | [1560.0, 1565.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q50 | infiniti/q50 V37 MY2022 | track_rear_mm | [1560.0, 1570.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 L50 MY2019 | curb_weight_kg | [1141.0, 1143.0, 1165.0, 1167.0] | [2049] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 L50 MY2020 | curb_weight_kg | [1138.0, 1162.0] | [2049] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 L50 MY2019 | length_mm | [5095.0] | [4990] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 L50 MY2020 | length_mm | [5095.0] | [4990] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 US2022+ MY2022 | width_mm | [2184.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 US2022+ MY2023 | width_mm | [2184.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 US2022+ MY2024 | width_mm | [2184.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 US2022+ MY2025 | width_mm | [2184.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| QX60 (+JX) | infiniti/qx60 US2022+ MY2026 | width_mm | [2184.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 79 записей (10% каждой линейки), расхождений 0.
- fx-qx70: 16 проверено, 0 расхождений
- q50: 36 проверено, 0 расхождений
- qx60: 27 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- QX60 (+JX) US2022+ (2022–2026): consumerreports.org: "The QX60 was redesigned for the 2022 model year." (https://www.consumerreports.org/cars/infiniti/qx60/); cars.com: "2022-2027" (https://www.cars.com/research/infiniti-qx60/) [quote read once] [media: generation starts MY2022]
- QX60 (+JX): media give different first model years [2013, 2014] for one generation; MY2014 used
- QX60 (+JX): MY2026: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "Infiniti redesigned the three-row QX60 for 2026, giving it styling that is similar to that of the QX80." (https://www.consumerreports.org/cars/infiniti/qx60/) [media: weak]
- FX / QX70: MY2014: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "The basics of the FX SUV carried over to the 2014 model year, but its nomenclature was changed to QX70." (https://www.consumerreports.org/cars/infiniti/qx70/); cars.com: "Previ

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- infiniti/q50: --prune-stale, код 0, {"raw_documents_seen": 63, "source_records_new": 3, "te_existing": 969, "configurations": 40, "configurations_research_only": 28, "configurations_linked": 12, "issues_existing": 30, "maintenance_new": 169}
- infiniti/qx60: --prune-stale, код 0, {"raw_documents_seen": 75, "source_records_new": 1, "te_existing": 717, "configurations": 32, "configurations_research_only": 22, "configurations_linked": 10, "issues_existing": 38, "maintenance_new": 222}
- infiniti/fx-qx70: --prune-stale, код 0, {"raw_documents_seen": 26, "te_existing": 254, "configurations": 9, "configurations_research_only": 9, "issues_existing": 6, "maintenance_new": 56}
