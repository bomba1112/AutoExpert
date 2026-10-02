# Nissan — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Altima | L33 | 2014–2018 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Altima | US2019+ | 2019–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Sentra | B17 | 2014–2019 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Sentra | US2020-2025 | 2020–2025 | ● | ◐ | ● | ● | ● | ● | ◐ | ◐ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Sentra | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ◐ | ○ | ◐ | ◐ | ● | ● | ○ | ● |
| Rogue | T32 | 2014–2020 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Rogue | T33 | 2021–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Pathfinder | R52 | 2014–2020 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ● | ● | ● | ● | ● |
| Pathfinder | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 89, частично 34, нет 12, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 4154 |
| known_issues | 0 | 211 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 412 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 122 | nissan-altima-us-2014-2.5l-4cyl-ice-a-variable-gear-ratios-fwd; nissan-altima-us-2014-3.5l-6cyl-ice-a-av-s7-fwd; nissan-altima-us-2015-2.5l-4cyl-ice-a-variable-gear-ratios-fwd |
| fuel_tank_l | value N outside the validator range; not used | 72 | nissan/altima carmans-2014-nissan-altima-sedan p.92; nissan/altima carmans-2015-nissan-altima-sedan p.97; nissan/altima carmans-2018-nissan-altima-sedan p.108 |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 29 | nissan/altima MY2015 (carmans-2015-nissan-altima-sedan); nissan/altima MY2016 (carmans-2016-nissan-altima-sedan); nissan/altima MY2019 (carmans-2019-nissan-altima-sedan) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 24 | nissan/altima MY2015 (carmans-2015-nissan-altima-sedan); nissan/altima MY2017 (carmans-2017-nissan-altima-sedan); nissan/altima MY2018 (carmans-2018-nissan-altima-sedan) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 19 | nissan/altima MY2017 (carmans-2017-nissan-altima-sedan); nissan/altima MY2018 (carmans-2018-nissan-altima-sedan); nissan/altima MY2019 (carmans-2019-nissan-altima-sedan) |
| engine_oil_capacity_without_filter_l | engine not stated; EPA lists several engines | 17 | nissan/altima MY2016 (carmans-2016-nissan-altima-sedan); nissan/altima MY2017 (carmans-2017-nissan-altima-sedan); nissan/altima MY2016 (official-d4f834985984) |
| octane_aki | one document gives N values: ['N', 'N'] | 15 | nissan/sentra MY2017 (carmans-2017-nissan-sentra); nissan/sentra MY2018 (carmans-2018-nissan-sentra); nissan/sentra MY2019 (carmans-2019-nissan-sentra) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N'] | 12 | nissan/altima MY2026 (official-531628333f60); nissan/altima MY2025 (official-627953d373ea); nissan/sentra MY2026 (official-511ec26d6b9d) |
| engine_oil_capacity_drain_refill_l | one document gives N values: ['N', 'N'] | 11 | nissan/altima MY2023 (carmans-2023-nissan-altima); nissan/altima MY2024 (official-02f7c81d0bf6); nissan/altima MY2026 (official-531628333f60) |
| engine_oil_capacity_l | one document gives N values: ['N', 'N'] | 10 | nissan/sentra MY2016 (carmans-2016-nissan-sentra); nissan/sentra MY2015 (official-56814c430d7c); nissan/sentra MY2016 (official-b930b0e01a9b) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 9 | nissan/altima L33; nissan/altima US2019+; nissan/sentra B17 |
| cargo_l | not found unambiguously in the available US press specification pages | 7 | nissan/altima L33; nissan/altima US2019+; nissan/sentra B17 |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 5 | nissan/altima L33; nissan/sentra B17; nissan/sentra US2026+ |
| coolant_capacity_l | value N outside the validator range; not used | 5 | nissan/sentra official-511ec26d6b9d p.456; nissan/sentra official-511ec26d6b9d p.456; nissan/rogue carmans-2026-nissan-rogue p.581 |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 4 | nissan/altima MY2026 (official-531628333f60); nissan/altima MY2025 (official-627953d373ea); nissan/pathfinder MY2025 (official-788622dcf159) |
| height_mm | one document gives N values: ['N', 'N'] | 4 | nissan/altima MY2025 (press-nissannews-altima-2025-8a7b3b89); nissan/altima MY2025 (press-nissannews-altima-2025-8a7b3b89); nissan/altima MY2026 (press-nissannews-altima-2026-2b0f5d63) |
| fuel_tank_l | one document gives N values: ['N', 'N', 'N'] | 4 | nissan/rogue MY2026 (carmans-2026-nissan-rogue); nissan/rogue MY2026 (official-1c14f723f96f); nissan/rogue MY2024 (official-9296d77ee8d0) |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N'] | 3 | nissan/altima MY2026 (official-531628333f60); nissan/altima MY2025 (official-627953d373ea); nissan/sentra MY2026 (official-511ec26d6b9d) |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 3 | nissan/altima MY2019 (press-nissannews-altima-2019-f7adfd3b); nissan/altima MY2023 (press-nissannews-altima-2023-2669e149); nissan/altima MY2024 (press-nissannews-altima-2024-8534174d) |
| ground_clearance | not found unambiguously in the available US press specification pages | 3 | nissan/altima L33; nissan/altima US2019+; nissan/sentra B17 |
| rear_suspension | one document gives N values: ['"NISMO-tuned front and rear suspension"', '"Torsion Beam"'] | 3 | nissan/sentra MY2017 (press-nissannews-sentra-2017-f618c18b); nissan/sentra MY2018 (press-nissannews-sentra-2018-cd6a6173); nissan/sentra MY2019 (press-nissannews-sentra-2019-51fcc602) |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 3 | nissan/rogue MY2026 (carmans-2026-nissan-rogue); nissan/rogue MY2026 (official-1c14f723f96f); nissan/rogue MY2025 (official-9b62fef6fa22) |
| electric_motor | one document gives N values: ['"N"', '"N"', '"Advanced electric motor \\uN N kW"'] | 3 | nissan/rogue MY2017 (press-nissannews-rogue-2017-b7db407e); nissan/rogue MY2018 (press-nissannews-rogue-2018-f5d0224d); nissan/rogue MY2019 (press-nissannews-rogue-2019-3617e98e) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 2 | nissan/altima MY2016 (carmans-2016-nissan-altima-sedan); nissan/altima MY2016 (official-d4f834985984) |
| injection | engine not stated; EPA lists several engines | 2 | nissan/altima MY2014 (press-nissannews-altima-2014-2bfe45da); nissan/altima MY2015 (press-nissannews-altima-2015-42367868) |
| power_hp | one document gives N values: ['N', 'N'] | 2 | nissan/altima MY2019 (press-nissannews-altima-2019-f7adfd3b); nissan/altima MY2023 (press-nissannews-altima-2023-2669e149) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 2 | nissan/sentra MY2024 (official-29218ece51cf); nissan/sentra MY2025 (official-8cbc63d25c88) |
| coolant | not found unambiguously in the available US owner's manuals | 2 | nissan/sentra US2020-2025; nissan/sentra US2026+ |
| engine_oil_capacity_l | one document gives N values: ['N', 'N', 'N'] | 2 | nissan/rogue MY2015 (official-0533ab860a7e); nissan/pathfinder MY2025 (official-788622dcf159) |
| octane_ron | one document gives N values: ['N', 'N'] | 2 | nissan/pathfinder MY2025 (official-788622dcf159); nissan/pathfinder MY2026 (official-f833693eb154) |
| passenger_volume_l | one document gives N values: ['N', 'N'] | 2 | nissan/pathfinder MY2025 (press-nissannews-pathfinder-2025-df0eeb32); nissan/pathfinder MY2026 (press-nissannews-pathfinder-2026-042c77d3) |
| valvetrain | engine not stated; EPA lists several engines | 1 | nissan/altima MY2014 (press-nissannews-altima-2014-2bfe45da) |
| transmission_fluid_capacity_l | value N outside the validator range; not used | 1 | nissan/sentra official-511ec26d6b9d p.456 |
| electric_motor | one document gives N values: ['"N"', '"N"', '"N"', '"N"'] | 1 | nissan/rogue MY2026 (press-nissannews-rogue-2026-deaa1bf3) |
| transmission_description | one document gives N values: ['"Single speed reduction gearbox"', '"Single speed, drive mode-switchable reduct | 1 | nissan/rogue MY2026 (press-nissannews-rogue-2026-deaa1bf3) |
| coolant_capacity_l | one document gives N values: ['N', 'N', 'N'] | 1 | nissan/pathfinder MY2026 (official-f833693eb154) |
| engine_oil_capacity_l | one document gives N values: ['N', 'N', 'N', 'N', 'N'] | 1 | nissan/pathfinder MY2026 (official-f833693eb154) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N', 'N', 'N'] | 1 | nissan/pathfinder MY2026 (official-f833693eb154) |
| electric_motor | one document gives N values: ['"N"', '"N"', '"Advanced electric motor - N kW"'] | 1 | nissan/pathfinder MY2014 (press-nissannews-pathfinder-2014-402ac222) |
| system_power_hp | one document gives N values: ['N', 'N'] | 1 | nissan/pathfinder MY2014 (press-nissannews-pathfinder-2014-402ac222) |

## 4. Конфликты источников

Конфликтов: 36. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 28
- official document kept over the copy: 7
- sources of the same rank disagree; field not shown: 1

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Altima | nissan/altima US2019+ MY2020 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 (or | ['Genuine NISSAN CVT Fluid NS-3'] | official document kept over the copy |
| Altima | nissan/altima US2019+ MY2021 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 (or | ['Genuine NISSAN CVT Fluid NS-3'] | official document kept over the copy |
| Altima | nissan/altima US2019+ MY2022 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 (or | ['Genuine NISSAN CVT Fluid NS-3'] | official document kept over the copy |
| Altima | nissan/altima L33 MY2014 | track_front_mm | [1575.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Altima | nissan/altima L33 MY2015 | track_front_mm | [1575.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sentra | nissan/sentra B17 MY2016 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 | ['Genuine NISSAN CVT Fluid NS-3 may'] | official document kept over the copy |
| Sentra | nissan/sentra US2020-2025 MY2021 | track_rear_mm | [1570.0, 1580.0, 1585.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sentra | nissan/sentra US2020-2025 MY2022 | track_rear_mm | [1570.0, 1580.0, 1585.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sentra | nissan/sentra US2020-2025 MY2023 | track_rear_mm | [1570.0, 1580.0, 1585.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sentra | nissan/sentra US2020-2025 MY2024 | track_rear_mm | [1570.0, 1580.0, 1585.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sentra | nissan/sentra US2020-2025 MY2025 | track_rear_mm | [1570.0, 1580.0, 1585.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Rogue | nissan/rogue T32 MY2015 | transmission_fluid | None | ['Genuine NISSAN CVT Fluid NS-3 may damage th', 'Genuine NISSAN CVT Fluid NS-3;  | sources of the same rank disagree; field not shown |
| Rogue | nissan/rogue T32 MY2016 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 (or; Genuine NISSAN CVT NS-3 may damage the | ['Genuine NISSAN CVT Fluid NS-3 ONLY in; Genuine NISSAN CVT NS-3 may damage the  | official document kept over the copy |
| Rogue | nissan/rogue T33 MY2024 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 | ['NS-3'] | official document kept over the copy |
| Rogue | nissan/rogue T32 MY2017 | length_mm | [4686.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Rogue | nissan/rogue T32 MY2018 | length_mm | [4686.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Rogue | nissan/rogue T32 MY2017 | length_mm | [4686.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Rogue | nissan/rogue T32 MY2018 | length_mm | [4686.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder R52 MY2016 | transmission_fluid | Genuine NISSAN CVT Fluid NS-3 (or; Genuine NISSAN CVT Fluid NS-3 may | ['Genuine NISSAN CVT Fluid NS-3 ONLY in; Genuine NISSAN CVT Fluid NS-3 may damag | official document kept over the copy |
| Pathfinder | nissan/pathfinder R52 MY2017 | height_mm | [1768.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder R52 MY2017 | height_mm | [1768.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder R52 MY2017 | height_mm | [1768.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2022 | length_mm | [5022.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2023 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2024 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2025 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2026 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2023 | track_front_mm | [1694.0, 1699.0] | [1660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2023 | track_rear_mm | [1694.0, 1699.0] | [1660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2022 | length_mm | [5022.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2023 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2024 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2025 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2026 | length_mm | [5022.0, 5050.0] | [5010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2023 | track_front_mm | [1694.0, 1699.0] | [1660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Pathfinder | nissan/pathfinder US2022+ MY2023 | track_rear_mm | [1694.0, 1699.0] | [1660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 187 записей (10% каждой линейки), расхождений 0.
- altima: 64 проверено, 0 расхождений
- pathfinder: 36 проверено, 0 расхождений
- rogue: 42 проверено, 0 расхождений
- sentra: 45 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Altima US2019+ (2019–2026): consumerreports.org: "The sixth-generation Altima offers all-wheel drive and a turbo engine." (https://www.consumerreports.org/cars/nissan/altima/); cars.com: "Nissan debuted the new-for-2019 Altima at the 2018 New York International Auto Show." (https://www.cars.com/research/nissan-altima/) [media:
- Sentra US2020-2025 (2020–2025): consumerreports.org: "The redesigned 2020 Sentra is a complete transformation." (https://www.consumerreports.org/cars/nissan/sentra/); cars.com: "The Sentra was redesigned for the 2020 model year, marking the start of its eighth generation" (https://www.cars.com/research/nissan-sentra/) [media: gene
- Sentra US2026+ (2026–2026): consumerreports.org: "Nissan gave the 2026 Sentra a thorough refresh inside and out, with new styling, updated controls, and more advanced driver aids." (https://www.consumerreports.org/cars/nissan/sentra/); cars.com: "A redesigned, ninth-generation Sentra debuted for the 2026 model year" (https://w
- Rogue T33 (2021–2026): consumerreports.org: "The third generation Rogue debuted in 2021, and was a major upgrade over its predecessor." (https://www.consumerreports.org/cars/nissan/rogue/); cars.com: "Redesigned for 2021" (https://www.cars.com/research/nissan-rogue/) [quote read once] [media: generation starts MY2021]
- Rogue: MY2019: detected boundary (vPIC Canadian specifications: overall length 463 -> 469 cm (MY2018 -> MY2019; a change of 6 cm or more)) dropped; consumerreports.org: "The 2014 redesign made the Rogue bigger, better, quieter and more refined overall." (https://www.consumerreports.org/cars/nissan/rogue/);
- Pathfinder US2022+ (2022–2026): consumerreports.org: "The three-row Pathfinder was redesigned for 2022 with a squared-off exterior" (https://www.consumerreports.org/cars/nissan/pathfinder/); cars.com: "This new fifth-generation model is a complete departure that incorporates some styling cues from the original Pathfinder" (https:/

## Изменения ранее записанных строк (последняя загрузка)

- Altima: проблема altima-L33-tsb-cvt обновлена {"evidence_ids": [76, 77], "note": [null, "CarComplaints.com \"Cvt Failure\" (owner reports): MY2018: #2, average cost to fix $6,500, average mileage 98,000 mi"
- Altima: проблема altima-L33-tsb-hesitation обновлена {"evidence_ids": [12, 15], "note": [null, "CarComplaints.com \"Hesitates/Sputters\" (owner reports): MY2015: #1, average cost to fix $3,000, average mileage 50,
- Altima: проблема altima-L33-tsb-torque-converter обновлена {"evidence_ids": [11, 12], "note": [null, "CarComplaints.com \"Shudders And Jerks\" (owner reports): MY2014: #2, average cost to fix $3,300, average mileage 40,
- Altima: проблема altima-US2019+-tsb-cvt обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [9, 10], "note": [null, "CarComplaints.com \"Cvt Malfunction\" (owner reports): MY2019: #3, average co
- Altima: проблема altima-US2019+-tsb-false-braking обновлена {"evidence_ids": [6, 7], "note": [null, "CarComplaints.com \"Automatic Emergency Brake Malfunction\" (owner reports): MY2020: #2, average cost to fix N/A, avera
- Altima: проблема altima-L33-complaints-transmission-failure обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 2], "note": [null, "CarComplaints.com \"Transmission Failure\" (owner reports): MY2014: #1, averag
- Pathfinder: проблема pathfinder-R52-tsb-infotainment обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [14, 15], "note": [null, "CarComplaints.com \"Infotainment System Failing\" (owner reports): MY2019: #
- Pathfinder: проблема pathfinder-R52-tsb-steering-noise обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [3, 4], "note": [null, "CarComplaints.com \"Power Steering Noise\" (owner reports): MY2015: #3, averag
- Pathfinder: проблема pathfinder-R52-tsb-torque-converter обновлена {"evidence_ids": [9, 11], "note": [null, "CarComplaints.com \"Shudder, Jerking\" (owner reports): MY2015: #1, average cost to fix $2,800, average mileage 31,000
- Pathfinder: проблема pathfinder-US2022+-tsb-suspension обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [2, 3], "note": [null, "CarComplaints.com \"Struts Failure\" (owner reports): MY2022: #1, average cost
- Pathfinder: проблема pathfinder-R52-complaints-hesitation обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 3], "note": [null, "CarComplaints.com \"Transmission Slips And Hesitates\" (owner reports): MY2014
- Pathfinder: проблема pathfinder-R52-complaints-timing-drive обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 3], "note": [null, "CarComplaints.com \"Timing Chain Failing\" (owner reports): MY2018: #1, averag
- Pathfinder: проблема pathfinder-R52-complaints-transmission-failure обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 3], "note": [null, "CarComplaints.com \"Transmission Slips And Hesitates\" (owner reports): MY2014
- Pathfinder: проблема pathfinder-US2022+-complaints-water-leak обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [1, 2], "note": [null, "CarComplaints.com \"Sunroof Leaks Horribly\" (owner reports): MY2022: #3, aver

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: ['rogue', 'sentra']
- nissan/altima: --prune-stale, код 0, {"raw_documents_seen": 86, "source_records_new": 42, "te_existing": 712, "te_new_GENERATION": 529, "te_new_ENGINE": 13, "configurations": 35, "configurations_research_only": 26, "configurations_linked": 9, "issues_existing": 50, "issues_updated": 6}
- nissan/sentra: --replace-own, код 0, {"replaced_own_te": 592, "replaced_own_issues": 44, "raw_documents_seen": 92, "source_records_new": 40, "te_new_GENERATION": 591, "te_new_ENGINE": 33, "te_new_CONFIGURATION": 343, "configurations": 25, "configurations_research_only": 25, "issues_new": 44}
- nissan/rogue: --replace-own, код 0, {"replaced_own_te": 777, "replaced_own_issues": 71, "raw_documents_seen": 107, "source_records_new": 57, "te_new_GENERATION": 511, "te_new_ENGINE": 72, "te_new_CONFIGURATION": 462, "configurations": 34, "configurations_research_only": 34, "issues_new": 68}
- nissan/pathfinder: --prune-stale, код 0, {"raw_documents_seen": 84, "source_records_new": 41, "te_existing": 643, "te_new_GENERATION": 195, "te_new_ENGINE": 50, "configurations": 28, "configurations_research_only": 28, "issues_existing": 49, "issues_updated": 8}
