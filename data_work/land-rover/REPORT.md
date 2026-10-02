# Land Rover — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Range Rover | L405 | 2014–2021 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Range Rover | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Range Rover Sport | L494 | 2014–2022 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Range Rover Sport | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Range Rover Evoque | LV | 2014–2019 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Range Rover Evoque | US2020+ | 2020–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| Discovery Sport (+LR2) | US2014-2014 | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Discovery Sport (+LR2) | L550 | 2015–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 52, частично 31, нет 37, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 3489 |
| known_issues | 0 | 188 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 256 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 108 | land-rover-range-rover-us-2014-3.0l-6cyl-turbo-ice-a-s8-4wd; land-rover-range-rover-us-2014-5.0l-8cyl-turbo-ice-a-s8-4wd; land-rover-range-rover-us-2015-3.0l-6cyl-turbo-ice-a-s8-4wd |
| power_hp | one document gives N values: ['N', 'N'] | 10 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 10 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| engine_oil_capacity_l | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| engine_oil_viscosity | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| coolant | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| transmission_fluid | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| brake_fluid | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 6 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6) |
| turning_circle_m | one document gives N values: ['N', 'N'] | 4 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6) |
| height_mm | one document gives N values: ['N', 'N'] | 4 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-evoque MY2015 (press-jlr-range-rover-evoque-2015-25328df6) |
| rear_brakes | one document gives N values: ['"N"', '"Single Piston Caliper w/ Ventilated Disc"'] | 4 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2020 (press-jlr-range-rover-sport-2020-5a639ffc) |
| torque_rpm | one document gives N values: ['"N,N-N,N"', '"N,N-N,N"'] | 4 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2020 (press-jlr-range-rover-sport-2020-5a639ffc); land-rover/range-rover-evoque MY2020 (press-jlr-range-rover-evoque-2020-03e4fdc3) |
| wheel_size_in | one document gives N values: ['N', 'N', 'N'] | 3 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| fuel_tank_l | no US owner's manual for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| power_hp | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| torque_lb_ft | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| tires | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| front_suspension | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| rear_suspension | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| front_brakes | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| steering | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| ground_clearance | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| cargo_l | no US press specification page for these years | 3 | land-rover/range-rover US2022+; land-rover/range-rover-sport US2023+; land-rover/discovery-sport US2014-2014 |
| torque_rpm | one document gives N values: ['"N,N"', '"N,N"'] | 3 | land-rover/range-rover-evoque MY2018 (press-jlr-range-rover-evoque-2018-0c127dee); land-rover/range-rover-evoque MY2019 (press-jlr-range-rover-evoque-2019-ad5b9436); land-rover/discovery-sport MY2019 (press-jlr-discovery-sport-2019-d04115a6) |
| injection | engine not stated; EPA lists several engines | 2 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| valvetrain | engine not stated; EPA lists several engines | 2 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| wheel_size_in | one document gives N values: ['N', 'N'] | 2 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover-evoque MY2015 (press-jlr-range-rover-evoque-2015-25328df6) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 2 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6) |
| cargo_max_l | one document gives N values: ['N', 'N'] | 2 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/discovery-sport MY2020 (press-jlr-discovery-sport-2020-3f520646) |
| front_brakes | one document gives N values: ['"N"', '"Twin Piston Caliper w/ Ventilated Disc"'] | 2 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2020 (press-jlr-range-rover-sport-2020-5a639ffc) |
| front_brakes | one document gives N values: ['"N"', '"Four Piston Caliper w/ Ventilated Disc"'] | 2 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2020 (press-jlr-range-rover-sport-2020-5a639ffc) |
| front_brakes | one document gives N values: ['"N"', '"Six Piston Caliper w/ Ventilated Disc"'] | 2 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2020 (press-jlr-range-rover-sport-2020-5a639ffc) |
| length_mm | one document gives N values: ['N', 'N'] | 2 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-evoque MY2015 (press-jlr-range-rover-evoque-2015-25328df6) |
| compression_ratio | one document gives N values: ['"N:N"', '"N:N"'] | 2 | land-rover/range-rover-evoque MY2020 (press-jlr-range-rover-evoque-2020-03e4fdc3); land-rover/discovery-sport MY2020 (press-jlr-discovery-sport-2020-3f520646) |
| power_hp | not found unambiguously in the available US press specification pages | 2 | land-rover/range-rover-evoque US2020+; land-rover/discovery-sport L550 |
| torque_lb_ft | not found unambiguously in the available US press specification pages | 2 | land-rover/range-rover-evoque US2020+; land-rover/discovery-sport L550 |
| tires | not found unambiguously in the available US press specification pages | 2 | land-rover/range-rover-evoque US2020+; land-rover/discovery-sport L550 |
| ground_clearance | one document gives N values: ['N', 'N'] | 1 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6) |
| front_brakes | not found unambiguously in the available US press specification pages | 1 | land-rover/range-rover-evoque US2020+ |
| cargo_l | not found unambiguously in the available US press specification pages | 1 | land-rover/range-rover-evoque US2020+ |
| cargo_l | one document gives N values: ['N', 'N'] | 1 | land-rover/discovery-sport MY2020 (press-jlr-discovery-sport-2020-3f520646) |

## 4. Конфликты источников

Конфликтов: 30. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 30

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Range Rover | land-rover/range-rover L405 MY2020 | height_mm | [1869.0] | [1840] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | length_mm | [5001.0] | [5200] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2015 | length_mm | [4999.0] | [5200] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2015 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | height_mm | [1869.0] | [1840] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | height_mm | [1869.0] | [1840] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | height_mm | [1869.0] | [1840] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | height_mm | [1869.0] | [1840] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2020 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover | land-rover/range-rover L405 MY2015 | width_mm | [1984.0] | [2070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Sport | land-rover/range-rover-sport L494 MY2020 | height_mm | [1803.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Sport | land-rover/range-rover-sport L494 MY2020 | height_mm | [1803.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Sport | land-rover/range-rover-sport L494 MY2020 | height_mm | [1803.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Sport | land-rover/range-rover-sport L494 MY2020 | height_mm | [1803.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Sport | land-rover/range-rover-sport L494 MY2015 | curb_weight_kg | [2144.0] | [2489] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Sport | land-rover/range-rover-sport L494 MY2015 | curb_weight_kg | [2144.0] | [2590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque LV MY2018 | width_mm | [1900.0] | [1970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque LV MY2019 | width_mm | [1900.0] | [1970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque LV MY2015 | curb_weight_kg | [1640.0, 1669.0] | [1770] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque LV MY2018 | width_mm | [1900.0] | [1970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque US2020+ MY2020 | width_mm | [1905.0] | [2000] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque US2020+ MY2020 | length_mm | [4371.0] | [4360] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque US2020+ MY2020 | wheelbase_mm | [2682.0] | [2660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Range Rover Evoque | land-rover/range-rover-evoque US2020+ MY2020 | width_mm | [1905.0] | [1970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Discovery Sport (+LR2) | land-rover/discovery-sport L550 MY2020 | width_mm | [1905.0] | [1890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Discovery Sport (+LR2) | land-rover/discovery-sport L550 MY2020 | width_mm | [1905.0] | [1890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 98 записей (10% каждой линейки), расхождений 0.
- discovery-sport: 17 проверено, 0 расхождений
- range-rover: 29 проверено, 0 расхождений
- range-rover-evoque: 26 проверено, 0 расхождений
- range-rover-sport: 26 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Range Rover US2022+ (2022–2026): consumerreports.org: "The redesigned Range Rover continues its legacy of pushing boundaries, with new tech and an elegant design." (https://www.consumerreports.org/cars/land-rover/range-rover/); cars.com: "A completely redesigned Range Rover debuted for the 2022 model year and, curiously, was sold a
- Range Rover Sport US2023+ (2023–2026): consumerreports.org: "this redesigned Range Rover Sport narrows the gap compared to the Range Rover in terms of luxury and refinement." (https://www.consumerreports.org/cars/land-rover/range-rover-sport/); cars.com: "Redesigned for 2023" (https://www.cars.com/research/land_rover-range_rover_sport/) 
- Range Rover Evoque US2020+ (2020–2026): consumerreports.org: "2020 Model Redesign Year" (https://www.consumerreports.org/cars/land-rover/range-rover-evoque/); cars.com: "Redesigned for 2020" (https://www.cars.com/research/land_rover-range_rover_evoque/) [quote read once] [media: generation starts MY2020]
- Discovery Sport (+LR2) L550 (2015–2026): consumerreports.org: "The compact Discovery Sport is based on the Evoque, with seating for five or, with its tiny optional third-row, seven." (https://www.consumerreports.org/cars/land-rover/discovery-sport/); cars.com: "2015-2026 Discovery Sport" (https://www.cars.com/research/land_rover-discovery_

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: ['discovery-sport', 'range-rover', 'range-rover-evoque', 'range-rover-sport']
- land-rover/range-rover: --replace-own, код 0, {"replaced_own_te": 1111, "replaced_own_issues": 53, "raw_documents_seen": 70, "source_records_new": 4, "te_new_GENERATION": 600, "te_new_ENGINE": 11, "te_new_CONFIGURATION": 622, "configurations": 38, "configurations_linked": 5, "configurations_research_only": 33, "issues_new": 53}
- land-rover/range-rover-sport: --replace-own, код 0, {"replaced_own_te": 943, "replaced_own_issues": 59, "raw_documents_seen": 60, "source_records_new": 4, "te_new_GENERATION": 568, "te_new_ENGINE": 11, "te_new_CONFIGURATION": 500, "configurations": 40, "configurations_research_only": 40, "issues_new": 59}
- land-rover/range-rover-evoque: --replace-own, код 0, {"replaced_own_te": 534, "replaced_own_issues": 39, "raw_documents_seen": 58, "source_records_new": 6, "te_new_GENERATION": 493, "te_new_CONFIGURATION": 200, "configurations": 16, "configurations_research_only": 16, "issues_new": 39}
- land-rover/discovery-sport: --replace-own, код 0, {"replaced_own_te": 412, "replaced_own_issues": 37, "raw_documents_seen": 56, "source_records_new": 4, "te_new_GENERATION": 318, "te_new_CONFIGURATION": 166, "configurations": 14, "configurations_research_only": 14, "issues_new": 37}
