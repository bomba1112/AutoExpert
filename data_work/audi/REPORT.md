# Audi — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A3 | 8V Sedan | 2015–2020 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ○ | ● | ● | ● |
| A3 | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| A4 | 8K | 2014–2016 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| A4 | 8W | 2017–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| A5 | 8T/8F | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| A5 | US2018-2024 | 2018–2024 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| A5 | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| A6 | 4G | 2014–2018 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| A6 | US2019-2025 | 2019–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| A6 | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q3 | 8U | 2015–2018 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q3 | US2019-2025 | 2019–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q3 | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q5 | 8R | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q5 | FY | 2018–2024 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q5 | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q7 | 4L | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q7 | 4M | 2017–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |

Итого ячеек: заполнено 117, частично 81, нет 72, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 8143 |
| known_issues | 0 | 384 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 646 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 260 | audi-a3-us-2015-1.8l-4cyl-turbo-ice-a-am-s6-fwd; audi-a3-us-2015-2.0l-4cyl-turbo-diesel-a-am-s6-fwd; audi-a3-us-2015-2.0l-4cyl-turbo-ice-a-am-s6-awd |
| wheel_size_in | one document gives N values: ['N', 'N'] | 22 | audi/a3 MY2025 (press-audiusa-a3-2025-f4ef9cce); audi/a3 MY2025 (press-audiusa-a3-2025-f4ef9cce); audi/a3 MY2026 (press-audiusa-a3-2026-2a9484c7) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 18 | audi/a3 MY2015 (press-audiusa-a3-2015-cacf8499); audi/a3 MY2022 (press-audiusa-a3-2022-ae51d2b9); audi/a3 MY2025 (press-audiusa-a3-2025-f4ef9cce) |
| engine_oil_capacity_l | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| engine_oil_viscosity | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| coolant | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| transmission_fluid | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| brake_fluid | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| ground_clearance | not found unambiguously in the available US press specification pages | 13 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| front_brakes | not found unambiguously in the available US press specification pages | 10 | audi/a3 8V Sedan; audi/a4 8K; audi/a4 8W |
| wheel_size_in | one document gives N values: ['N', 'N', 'N'] | 10 | audi/a4 MY2017 (press-audiusa-a4-2017-267ca685); audi/a6 MY2026 (press-audiusa-a6-2026-2db7b32a); audi/a6 MY2026 (press-audiusa-a6-2026-9e289d44) |
| fuel_tank_l | no US owner's manual for these years | 9 | audi/a3 8V Sedan; audi/a4 8K; audi/a4 8W |
| front_suspension | not found unambiguously in the available US press specification pages | 8 | audi/a3 8V Sedan; audi/a4 8K; audi/a4 8W |
| rear_suspension | not found unambiguously in the available US press specification pages | 8 | audi/a3 8V Sedan; audi/a4 8K; audi/a4 8W |
| power_hp | engine not stated; EPA lists several engines | 8 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2015 (press-audiusa-a5-2015-b8d49195) |
| power_rpm | engine not stated; EPA lists several engines | 8 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2015 (press-audiusa-a5-2015-b8d49195) |
| front_brakes | one document gives N values: ['"Floating caliper"', '"Single Piston N\\" (Nmm) Ventilated steel discs"'] | 8 | audi/a5 MY2025 (press-audiusa-a5-2025-08a27239); audi/a5 MY2025 (press-audiusa-a5-2025-08a27239); audi/a5 MY2025 (press-audiusa-a5-2025-43477f23) |
| front_brakes | one document gives N values: ['"Floating caliper /"', '"Single-piston floating caliper N\\" (Nmm) ventilated s | 8 | audi/a5 MY2026 (press-audiusa-a5-2026-f3ffdbb6); audi/a5 MY2026 (press-audiusa-a5-2026-f3ffdbb6); audi/a5 MY2026 (press-audiusa-a5-2026-fbe660da) |
| rear_brakes | one document gives N values: ['"Floating caliper with integrated electric parking brake"', '"Single-piston flo | 8 | audi/a5 MY2026 (press-audiusa-a5-2026-f3ffdbb6); audi/a5 MY2026 (press-audiusa-a5-2026-f3ffdbb6); audi/a5 MY2026 (press-audiusa-a5-2026-fbe660da) |
| valvetrain | engine not stated; EPA lists several engines | 7 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2015 (press-audiusa-a5-2015-b8d49195) |
| torque_lb_ft | engine not stated; EPA lists several engines | 7 | audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2015 (press-audiusa-a5-2015-b8d49195); audi/a5 MY2017 (press-audiusa-a5-2017-0ab79ada) |
| torque_rpm | engine not stated; EPA lists several engines | 7 | audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2015 (press-audiusa-a5-2015-b8d49195); audi/a5 MY2017 (press-audiusa-a5-2017-0ab79ada) |
| engine_description | engine not stated; EPA lists several engines | 6 | audi/a3 MY2016 (press-audiusa-a3-2016-5177c854); audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 6 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2018 (press-audiusa-a5-2018-923eb4f3) |
| compression_ratio | engine not stated; EPA lists several engines | 6 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2018 (press-audiusa-a5-2018-923eb4f3) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 6 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2018 (press-audiusa-a5-2018-923eb4f3) |
| rear_brakes | one document gives N values: ['"Floating caliper with integrated parking brake"', '"Single Piston N\\" (Nmm) v | 6 | audi/a5 MY2025 (press-audiusa-a5-2025-08a27239); audi/a5 MY2025 (press-audiusa-a5-2025-08a27239); audi/a5 MY2025 (press-audiusa-a5-2025-43477f23) |
| power_rpm | one document gives N values: ['"N,N-N,N"', '"N-N"'] | 5 | audi/a4 MY2017 (press-audiusa-a4-2017-e2a0350f); audi/a5 MY2018 (press-audiusa-a5-2018-120891b5); audi/a5 MY2018 (press-audiusa-a5-2018-120891b5) |
| torque_rpm | one document gives N values: ['"N,N-N,N"', '"N-N"'] | 5 | audi/a4 MY2017 (press-audiusa-a4-2017-e2a0350f); audi/a5 MY2018 (press-audiusa-a5-2018-120891b5); audi/a5 MY2018 (press-audiusa-a5-2018-120891b5) |
| power_hp | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| torque_lb_ft | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| tires | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| front_suspension | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| rear_suspension | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| front_brakes | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| steering | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| ground_clearance | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| cargo_l | no US press specification page for these years | 5 | audi/a6 4G; audi/q3 8U; audi/q5 8R |
| wheelbase_mm | one document gives N values: ['N', 'N', 'N'] | 4 | audi/a6 MY2020 (press-audiusa-a6-2020-5e62f4f5); audi/a6 MY2021 (press-audiusa-a6-2021-aa3bc5cb); audi/a6 MY2025 (press-audiusa-a6-2025-6ae7417a) |
| rear_brakes | one document gives N values: ['"Floating caliper with integrated parking brake"', '"single-piston N\\" (Nmm) v | 4 | audi/a6 MY2026 (press-audiusa-a6-2026-77b198eb); audi/a6 MY2026 (press-audiusa-a6-2026-77b198eb); audi/q7 MY2026 (press-audiusa-q7-2026-5d8fcdf9) |
| bore_stroke_in | engine not stated; EPA lists several engines | 3 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2018 (press-audiusa-a5-2018-923eb4f3) |
| injection | engine not stated; EPA lists several engines | 3 | audi/a4 MY2014 (press-audiusa-a4-2014-e67acc62); audi/a4 MY2015 (press-audiusa-a4-2015-3933e851); audi/a5 MY2018 (press-audiusa-a5-2018-923eb4f3) |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 3 | audi/a4 MY2017 (press-audiusa-a4-2017-267ca685); audi/a5 MY2018 (press-audiusa-a5-2018-74063df5); audi/q7 MY2020 (press-audiusa-q7-2020-bad8d113) |
| tires | not found unambiguously in the available US press specification pages | 3 | audi/a4 8K; audi/a5 8T/8F; audi/a5 US2018-2024 |
| cargo_l | not found unambiguously in the available US press specification pages | 3 | audi/a6 US2019-2025; audi/q3 US2019-2025; audi/q3 US2026+ |
| cargo_l | one document gives N values: ['N', 'N'] | 2 | audi/a3 MY2015 (press-audiusa-a3-2015-cacf8499); audi/a3 MY2015 (press-audiusa-a3-2015-cacf8499) |
| steering | not found unambiguously in the available US press specification pages | 2 | audi/a3 8V Sedan; audi/q3 US2026+ |
| engine_oil_capacity_drain_refill_l | value N outside the validator range; not used | 2 | audi/a5 mcum-a5-4-door-2025-2026 p.20; audi/a5 mcum-a5-4-door-2025-2026 p.20 |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 2 | audi/a5 MY2025 (mcum-a5-4-door-2025-2026); audi/a5 MY2026 (mcum-a5-4-door-2025-2026) |
| octane_ron | one document gives N values: ['N', 'N', 'N'] | 2 | audi/a5 MY2025 (mcum-a5-4-door-2025-2026); audi/a5 MY2026 (mcum-a5-4-door-2025-2026) |
| engine_description | one document gives N values: ['"N TFSI\\uNae, N CYL"', '"N TFSI\\uNae,N CYL"'] | 2 | audi/a6 MY2020 (press-audiusa-a6-2020-5e62f4f5); audi/a6 MY2020 (press-audiusa-a6-2020-5e62f4f5) |
| front_brakes | one document gives N values: ['"Floating caliper /"', '"Single-piston floating caliper / N\\" (Nmm) ventilated | 2 | audi/a6 MY2026 (press-audiusa-a6-2026-2db7b32a); audi/a6 MY2026 (press-audiusa-a6-2026-ebd3f192) |
| front_brakes | one document gives N values: ['"Aluminum fixed caliper /"', '"dual-piston N\\" (Nmm) Ventilated steel discs"'] | 2 | audi/q7 MY2026 (press-audiusa-q7-2026-5d8fcdf9); audi/q7 MY2026 (press-audiusa-q7-2026-5d8fcdf9) |
| engine_description | one document gives N values: ['"N TFSI"', '"Four-cylinder"'] | 1 | audi/a4 MY2016 (press-audiusa-a4-2016-5bd562a3) |
| engine_description | one document gives N values: ['"N TFSI quattro\\uNae"', '"Six-cylinder"'] | 1 | audi/a4 MY2016 (press-audiusa-a4-2016-5bd562a3) |
| engine_description | one document gives N values: ['"N TFSI"', '"Inline four-cylinder"'] | 1 | audi/a4 MY2017 (press-audiusa-a4-2017-267ca685) |
| power_rpm | one document gives N values: ['"N,N-N,N"', '"N,N-N,N"'] | 1 | audi/a4 MY2017 (press-audiusa-a4-2017-267ca685) |
| engine_description | one document gives N values: ['"Four-cylinder"', '"Inline four-cylinder"'] | 1 | audi/a4 MY2017 (press-audiusa-a4-2017-e2a0350f) |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N'] | 1 | audi/a5 MY2018 (press-audiusa-a5-2018-74063df5) |
| wheelbase_mm | one document gives N values: ['N', 'N', 'N', 'N'] | 1 | audi/a5 MY2021 (press-audiusa-a5-2021-7325382b) |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 1 | audi/a5 US2025+ |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 1 | audi/a5 US2025+ |
| coolant | not found unambiguously in the available US owner's manuals | 1 | audi/a5 US2025+ |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 1 | audi/a5 US2025+ |
| front_brakes | one document gives N values: ['"N-piston N\\" (Nmm) ventilated steel discs"', '"Fixed caliper"'] | 1 | audi/a6 MY2026 (press-audiusa-a6-2026-77b198eb) |
| front_brakes | one document gives N values: ['"N-piston N\\" (Nmm) ventilated steel discs"', '"Floating caliper"'] | 1 | audi/a6 MY2026 (press-audiusa-a6-2026-77b198eb) |
| front_brakes | one document gives N values: ['"Floating caliper /"', '"Single-piston caliper / N\\" (Nmm) ventilated steel di | 1 | audi/a6 MY2026 (press-audiusa-a6-2026-9e289d44) |
| rear_brakes | one document gives N values: ['"Floating caliper with integrated parking brake"', '"Single-piston caliper / N\ | 1 | audi/a6 MY2026 (press-audiusa-a6-2026-9e289d44) |
| power_hp | one document gives N values: ['N', 'N'] | 1 | audi/q7 MY2020 (press-audiusa-q7-2020-bad8d113) |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 1 | audi/q7 MY2020 (press-audiusa-q7-2020-bad8d113) |
| front_brakes | one document gives N values: ['"N-piston N\\" (Nmm) Ventilated steel discs"', '"Aluminum fixed caliper /"'] | 1 | audi/q7 MY2026 (press-audiusa-q7-2026-5d8fcdf9) |

## 4. Конфликты источников

Конфликтов: 132. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 130
- sources of the same rank disagree; field not shown: 2

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| A3 | audi/a3 8V Sedan MY2015 | height_mm | [1392.0, 1415.0] | [1360] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | length_mm | [4455.0, 4468.0] | [4440] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | track_front_mm | [1552.0, 1554.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | track_rear_mm | [1527.0] | [1510] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | width_mm | [1961.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | width_mm | [1961.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | width_mm | [1961.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 8V Sedan MY2015 | width_mm | [1961.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 US2022+ MY2022 | curb_weight_kg | [1510.0, 1585.0, 1605.0, 1655.0] | [1300] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 US2022+ MY2025 | curb_weight_kg | [1570.0, 1610.0, 1645.0] | [1300] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A3 | audi/a3 US2022+ MY2026 | curb_weight_kg | [1570.0, 1610.0, 1645.0] | [1300] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | curb_weight_kg | [1765.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | curb_weight_kg | [1765.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | height_mm | [1473.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | height_mm | [1473.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | length_mm | [4722.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | length_mm | [4722.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | track_front_mm | [1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | track_front_mm | [1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | track_rear_mm | [1575.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | track_rear_mm | [1575.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | width_mm | [1842.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | width_mm | [1842.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | curb_weight_kg | [1765.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | curb_weight_kg | [1765.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | height_mm | [1473.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | height_mm | [1473.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | length_mm | [4722.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | length_mm | [4722.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | track_front_mm | [1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | track_front_mm | [1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | track_rear_mm | [1575.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | track_rear_mm | [1575.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | width_mm | [1842.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | width_mm | [1842.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2016 | height_mm | [1407.0, 1427.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2016 | track_front_mm | [1552.0, 1565.0] | [1580] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2016 | track_rear_mm | [1539.0, 1552.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2016 | width_mm | [1826.0] | [1840] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | height_mm | [1473.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | height_mm | [1473.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | length_mm | [4722.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | length_mm | [4722.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | track_front_mm | [1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | track_front_mm | [1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | track_rear_mm | [1575.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | track_rear_mm | [1575.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2014 | width_mm | [1842.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8K MY2015 | width_mm | [1842.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8W MY2017 | curb_weight_kg | [1735.0] | [1645] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8W MY2017 | height_mm | [1427.0, 1494.0] | [1400] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8W MY2017 | width_mm | [1842.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A4 | audi/a4 8W MY2020 | height_mm | [1427.0, 1494.0] | [1400] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_front_mm | [1585.0, 1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_front_mm | [1585.0, 1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2017 | track_front_mm | [1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_front_mm | [1585.0, 1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_rear_mm | [1575.0, 1577.0, 1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_front_mm | [1585.0, 1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_rear_mm | [1575.0, 1577.0, 1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_front_mm | [1585.0, 1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2017 | track_front_mm | [1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_rear_mm | [1575.0, 1577.0, 1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2017 | track_rear_mm | [1575.0, 1577.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_front_mm | [1585.0, 1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2017 | track_front_mm | [1588.0, 1590.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2015 | track_rear_mm | [1575.0, 1577.0, 1582.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 8T/8F MY2017 | track_rear_mm | [1575.0, 1577.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2018-2024 MY2018 | length_mm | [4724.0, 4732.0, 4752.0] | [4670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2018-2024 MY2018 | length_mm | [4724.0, 4732.0, 4752.0] | [4670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2018-2024 MY2021 | height_mm | [1372.0, 1384.0, 1387.0, 1400.0] | [1360] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2018-2024 MY2018 | curb_weight_kg | [1680.0, 1780.0, 1810.0] | [1920] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2018-2024 MY2018 | length_mm | [4724.0, 4732.0, 4752.0] | [4690] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2018-2024 MY2018 | length_mm | [4724.0, 4732.0, 4752.0] | [4690] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | height_mm | [1387.0, 1397.0, 1400.0, 1435.0, 1448.0] | [1370] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | length_mm | [4755.0, 4757.0, 4765.0, 4778.0, 4829.0, 4834.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | height_mm | [1387.0, 1397.0, 1400.0, 1435.0, 1448.0] | [1370] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | length_mm | [4755.0, 4757.0, 4765.0, 4778.0, 4829.0, 4834.0] | [4700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2026 | curb_weight_kg | [1855.0, 1945.0] | [1770] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | track_front_mm | [1588.0, 1598.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | track_rear_mm | [1567.0, 1588.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | height_mm | [1387.0, 1397.0, 1400.0, 1435.0, 1448.0] | [1360] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | length_mm | [4755.0, 4757.0, 4765.0, 4778.0, 4829.0, 4834.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | height_mm | [1387.0, 1397.0, 1400.0, 1435.0, 1448.0] | [1370] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | length_mm | [4755.0, 4757.0, 4765.0, 4778.0, 4829.0, 4834.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | height_mm | [1387.0, 1397.0, 1400.0, 1435.0, 1448.0] | [1370] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | length_mm | [4755.0, 4757.0, 4765.0, 4778.0, 4829.0, 4834.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | curb_weight_kg | [1690.0, 1710.0, 1780.0, 1850.0, 1855.0, 1945.0] | [2025] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2026 | curb_weight_kg | [1855.0, 1945.0] | [2025] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | track_front_mm | [1588.0, 1598.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A5 | audi/a5 US2025+ MY2025 | track_rear_mm | [1567.0, 1588.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2019-2025 MY2025 | engine_displacement_cc | None | [2894, 2900] | sources of the same rank disagree; field not shown |
| A6 | audi/a6 US2019-2025 MY2025 | torque_lb_ft | None | [442, 443] | sources of the same rank disagree; field not shown |
| A6 | audi/a6 US2019-2025 MY2020 | curb_weight_kg | [1860.0, 1935.0, 2035.0] | [2150] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2019-2025 MY2020 | length_mm | [4938.0, 4950.0, 4953.0] | [5000] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2019-2025 MY2020 | track_front_mm | [1621.0, 1631.0, 1633.0, 1646.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2019-2025 MY2020 | track_rear_mm | [1603.0, 1610.0, 1618.0] | [1650] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2019-2025 MY2021 | track_front_mm | [1631.0, 1633.0, 1646.0, 1669.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2019-2025 MY2025 | track_front_mm | [1631.0, 1633.0, 1646.0, 1669.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2026+ MY2026 | curb_weight_kg | [1955.0, 2035.0, 2260.0] | [2360] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2026+ MY2026 | length_mm | [4950.0, 4996.0, 4999.0] | [4930] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2026+ MY2026 | wheelbase_mm | [2924.0] | [2950] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2026+ MY2026 | curb_weight_kg | [1955.0, 2035.0, 2260.0] | [2400] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2026+ MY2026 | length_mm | [4950.0, 4996.0, 4999.0] | [4930] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| A6 | audi/a6 US2026+ MY2026 | wheelbase_mm | [2924.0] | [2950] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2019-2025 MY2021 | curb_weight_kg | [1770.0, 1776.0] | [1535] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2019-2025 MY2025 | curb_weight_kg | [1775.0] | [1535] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2019-2025 MY2021 | height_mm | [1598.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2019-2025 MY2025 | height_mm | [1598.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2019-2025 MY2021 | width_mm | [1849.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2019-2025 MY2025 | width_mm | [1849.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q3 | audi/q3 US2026+ MY2026 | height_mm | [1628.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | curb_weight_kg | [1925.0, 1955.0, 2025.0, 2050.0] | [1835] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2026 | height_mm | [1664.0, 1669.0, 1671.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | length_mm | [4717.0] | [4680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | height_mm | [1664.0, 1669.0, 1671.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | curb_weight_kg | [1925.0, 1955.0, 2025.0, 2050.0] | [1775] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2026 | height_mm | [1664.0, 1669.0, 1671.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | length_mm | [4717.0] | [4690] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | height_mm | [1664.0, 1669.0, 1671.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | curb_weight_kg | [1925.0, 1955.0, 2025.0, 2050.0] | [2129] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | length_mm | [4717.0] | [4680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2026 | curb_weight_kg | [1910.0, 1940.0, 2010.0, 2040.0] | [2115] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2026 | height_mm | [1664.0, 1669.0, 1671.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | length_mm | [4717.0] | [4680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | curb_weight_kg | [1925.0, 1955.0, 2025.0, 2050.0] | [2115] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | height_mm | [1664.0, 1669.0, 1671.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2026 | curb_weight_kg | [1910.0, 1940.0, 2010.0, 2040.0] | [2115] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2026 | height_mm | [1664.0, 1669.0, 1671.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | length_mm | [4717.0] | [4690] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | curb_weight_kg | [1925.0, 1955.0, 2025.0, 2050.0] | [2115] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Q5 | audi/q5 US2025+ MY2025 | height_mm | [1664.0, 1669.0, 1671.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 294 записей (10% каждой линейки), расхождений 0.
- a3: 48 проверено, 0 расхождений
- a4: 32 проверено, 0 расхождений
- a5: 74 проверено, 0 расхождений
- a6: 56 проверено, 0 расхождений
- q3: 17 проверено, 0 расхождений
- q5: 39 проверено, 0 расхождений
- q7: 28 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- A3 US2022+ (2022–2026): consumerreports.org: "Audi improves upon its capable entry-level sedan with an all-new 2022 model" (https://www.consumerreports.org/cars/audi/a3/); cars.com: "Redesigned for 2022" (https://www.cars.com/research/audi-a3/) [quote read once] [media: generation starts MY2022]
- A3: MY2017: detected boundary (vPIC Canadian specifications: wheelbase 264 cm (MY2016) -> 263 cm (MY2017), with overall height 142 -> 139 cm) dropped; consumerreports.org: "This wholly redesigned Audi A3 is part of a wave of compact luxury-branded models" (https://www.consumerreports.org/cars/audi/a3/);
- A4 8W (2017–2025): consumerreports.org: "2025 is the final model year for the A4, replaced by the A5." (https://www.consumerreports.org/cars/audi/a4/); cars.com: "Redesigned for 2017" (https://www.cars.com/research/audi-a4/) [quote read once] [media: generation starts MY2017]
- A5 US2018-2024 (2018–2024): consumerreports.org: "The 2018 A5 and S5 coupe and convertible have been redesigned." (https://www.consumerreports.org/cars/audi/a5/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/audi-a5/) [media: generation starts MY2018]
- A5 US2025+ (2025–2026): consumerreports.org: "The A4 is replaced by a redesigned version of what is now called the A5 Sportback" (https://www.consumerreports.org/cars/audi/a5/); cars.com: "Consolidates prior A4, A5 into one model" (https://www.cars.com/research/audi-a5/) [media: generation starts MY2025]
- A6 US2019-2025 (2019–2025): consumerreports.org: "The redesigned Audi A6 features lots of new technology, including a new infotainment system." (https://www.consumerreports.org/cars/audi/a6/); cars.com: "The redesigned 2019 Audi A6 shares an updated look and technology with the redone 2019 A7 hatchback" (https://www.cars.com/a
- A6 US2026+ (2026–2026): consumerreports.org: "Redesigned for 2026, the A6 delivers a high-level driving experience" (https://www.consumerreports.org/cars/audi/a6/); cars.com: "Redesigned for 2026" (https://www.cars.com/research/audi-a6/) [quote read once] [media: generation starts MY2026]
- A6: boundary moved from MY2020 to the media-stated MY2019
- A6: boundary moved from MY2025 to the media-stated MY2026
- Q3 US2019-2025 (2019–2025): consumerreports.org: "The redesigned Q3 is a pleasant SUV that packs luxury and practicality into a small package." (https://www.consumerreports.org/cars/audi/q3/); cars.com: "the second-generation Audi Q3 subcompact SUV, which gets a needed full redesign for 2019" (https://www.cars.com/articles/201
- Q3 US2026+ (2026–2026): consumerreports.org: "The redesigned Q3 has one powertrain choice" (https://www.consumerreports.org/cars/audi/q3/); cars.com: "Redesigned for 2026" (https://www.cars.com/research/audi-q3/) [quote read once] [media: generation starts MY2026]
- Q5 FY (2018–2024): consumerreports.org: "2018 Model Redesign Year" (https://www.consumerreports.org/cars/audi/q5/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/audi-q5/) [quote read once] [media: generation starts MY2018]
- Q5 US2025+ (2025–2026): consumerreports.org: "The redesigned Q5 gets new styling, increased performance promise, and a growing list of advanced safety features." (https://www.consumerreports.org/cars/audi/q5/); cars.com: "Redesigned five-seat luxury compact SUV" (https://www.cars.com/research/audi-q5/) [quote read once] [m
- Q5: MY2009: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "The Q5 hits its target as a compact, luxurious and sporty SUV spot on." (https://www.consumerreports.org/cars/audi/q5/) [media: weak])
- Q5: MY2021: detected boundary (mycarusermanual.com generation page starts at 2020 (q5/suv/2020), corroborated by vPIC overall length 467 -> 468/469 cm (MY2020 -> MY2021)) dropped; consumerreports.org: "For 2021, the Q5 got a freshening with a modest power boost." (https://www.consumerreports.org/cars/au
- Q7 4M (2017–2026): consumerreports.org: "The redesigned Q7 employs a supercharged 3.0-liter V6 that is mated to a very smooth eight-speed automatic." (https://www.consumerreports.org/cars/audi/q7/); cars.com: "Redesigned for 2017 after skipping 2016" (https://www.cars.com/research/audi-q7/) [quote read once] [media: g

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- audi/a3: --prune-stale, код 0, {"raw_documents_seen": 79, "source_records_new": 74, "te_new_GENERATION": 728, "te_new_CONFIGURATION": 483, "configurations": 37, "configurations_linked": 4, "configurations_research_only": 33, "issues_new": 39}
- audi/a4: --prune-stale, код 0, {"raw_documents_seen": 76, "source_records_new": 61, "te_new_GENERATION": 577, "te_new_CONFIGURATION": 490, "configurations": 38, "configurations_research_only": 35, "configurations_linked": 3, "issues_new": 45}
- audi/a5: --prune-stale, код 0, {"raw_documents_seen": 112, "source_records_new": 94, "te_new_GENERATION": 1052, "te_new_CONFIGURATION": 709, "configurations": 47, "configurations_research_only": 47, "issues_new": 61}
- audi/a6: --prune-stale, код 0, {"raw_documents_seen": 90, "source_records_new": 72, "te_new_GENERATION": 836, "te_new_CONFIGURATION": 585, "configurations": 51, "configurations_linked": 4, "configurations_research_only": 47, "issues_new": 65}
- audi/q3: --prune-stale, код 0, {"raw_documents_seen": 46, "source_records_new": 29, "te_new_GENERATION": 328, "te_new_CONFIGURATION": 196, "configurations": 16, "configurations_linked": 6, "configurations_research_only": 10, "issues_new": 39}
- audi/q5: --prune-stale, код 0, {"raw_documents_seen": 92, "source_records_new": 74, "te_new_GENERATION": 768, "te_new_CONFIGURATION": 524, "configurations": 40, "configurations_research_only": 32, "configurations_linked": 8, "issues_new": 79}
- audi/q7: --prune-stale, код 0, {"raw_documents_seen": 54, "source_records_new": 37, "te_new_GENERATION": 526, "te_new_CONFIGURATION": 341, "configurations": 31, "configurations_research_only": 26, "configurations_linked": 5, "issues_new": 56}
