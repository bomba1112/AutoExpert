# Volkswagen — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jetta | VI | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| Jetta | VII | 2019–2026 | ● | ◐ | ● | ● | ○ | ● | ○ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| Passat | NMS | 2014–2022 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| Tiguan | 5N | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| Tiguan | II-US-LWB | 2018–2024 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| Tiguan | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| Atlas | I-US-2018 | 2018–2026 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| Arteon | I | 2019–2024 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| Touareg | 7P | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 88, частично 39, нет 8, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 5592 |
| known_issues | 0 | 304 |
| maintenance_schedule_items | 0 | 274 |

## 3. Журнал пробелов

Записей в журнале пробелов: 756 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 163 | volkswagen-jetta-us-2014-1.4l-4cyl-turbo-hev-a-am-s7-fwd; volkswagen-jetta-us-2014-1.8l-4cyl-turbo-ice-a-s6-fwd; volkswagen-jetta-us-2014-1.8l-4cyl-turbo-ice-m-5-spd-fwd |
| engine_oil_capacity_drain_refill_l | value N outside the validator range; not used | 44 | volkswagen/jetta carmans-2019-volkswagen-jetta p.249; volkswagen/jetta carmans-2019-volkswagen-jetta p.250; volkswagen/jetta carmans-2019-volkswagen-jetta p.252 |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 42 | volkswagen/jetta MY2014 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2015 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2016 (mcum-jetta-4-door-2011-2018) |
| fuel_tank_l | value N outside the validator range; not used | 36 | volkswagen/jetta carmans-2022-volkswagen-jetta p.342; volkswagen/jetta carmans-2023-volkswagen-jetta-2 p.342; volkswagen/jetta mcum-jetta-4-door-2011-2018 p.151 |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 31 | volkswagen/jetta MY2014 (press-vw-jetta-2014-0fb78ecb); volkswagen/jetta MY2014 (press-vw-jetta-2014-0fb78ecb); volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f) |
| wheel_size_in | one document gives N values: ['N', 'N'] | 27 | volkswagen/jetta MY2014 (press-vw-jetta-2014-0fb78ecb); volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac) |
| bore_stroke_in | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| compression_ratio | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| engine_description | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| power_hp | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| power_rpm | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| torque_lb_ft | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| torque_rpm | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| valvetrain | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| cargo_l | one document gives N values: ['N', 'N'] | 20 | volkswagen/tiguan MY2018 (press-vw-tiguan-2018-3e326d7e); volkswagen/tiguan MY2019 (press-vw-tiguan-2019-43f8aae5); volkswagen/tiguan MY2020 (press-vw-tiguan-2020-0938826a) |
| wheel_size_in | one document gives N values: ['N', 'N', 'N'] | 19 | volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2025 (press-vw-jetta-2025-16cdd190); volkswagen/jetta MY2026 (press-vw-jetta-2026-67422415) |
| engine_oil_oem_approval | не публикуется производителем в руководстве: руководство ссылается на наклейку в моторном отсеке — «There is a | 18 | volkswagen/jetta MY2019-2025 (mcum-jetta-4-door-2019-2025 p.143); volkswagen/jetta MY2019-2025 (mcum-jetta-4-door-2019-2025 p.183); volkswagen/passat MY2014-2022 (mcum-passat-suv-2014-2023 p.13) |
| engine_oil_capacity_l | не публикуется производителем в руководстве: руководство ссылается на наклейку в моторном отсеке — «There is a | 18 | volkswagen/jetta MY2019-2025 (mcum-jetta-4-door-2019-2025 p.143); volkswagen/jetta MY2019-2025 (mcum-jetta-4-door-2019-2025 p.183); volkswagen/passat MY2014-2022 (mcum-passat-suv-2014-2023 p.13) |
| octane_ron | one document gives N values: ['N', 'N'] | 12 | volkswagen/jetta MY2019 (mcum-jetta-4-door-2019-2025); volkswagen/jetta MY2020 (mcum-jetta-4-door-2019-2025); volkswagen/jetta MY2021 (mcum-jetta-4-door-2019-2025) |
| wheel_size_in | one document gives N values: ['N', 'N', 'N', 'N'] | 12 | volkswagen/passat MY2017 (press-vw-passat-2017-95389f0e); volkswagen/tiguan MY2014 (press-vw-tiguan-2014-8171e3bb); volkswagen/tiguan MY2015 (press-vw-tiguan-2015-e2e7198e) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 10 | volkswagen/jetta MY2019 (carmans-2019-volkswagen-jetta); volkswagen/jetta MY2020 (carmans-2020-volkswagen-jetta); volkswagen/jetta MY2021 (carmans-2021-volkswagen-jetta) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 8 | volkswagen/jetta VI; volkswagen/jetta VII; volkswagen/passat NMS |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 8 | volkswagen/jetta VI; volkswagen/jetta VII; volkswagen/passat NMS |
| engine_oil_specification | engine not stated; EPA lists several engines | 7 | volkswagen/jetta MY2014 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2015 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2016 (mcum-jetta-4-door-2011-2018) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 7 | volkswagen/jetta MY2014 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2015 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2016 (mcum-jetta-4-door-2011-2018) |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 6 | volkswagen/jetta MY2014 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2015 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2016 (mcum-jetta-4-door-2011-2018) |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 6 | volkswagen/jetta VI; volkswagen/jetta VII; volkswagen/tiguan II-US-LWB |
| coolant | not found unambiguously in the available US owner's manuals | 4 | volkswagen/jetta VI; volkswagen/passat NMS; volkswagen/tiguan 5N |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 3 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1); volkswagen/touareg MY2015 (press-vw-touareg-2015-fd3a4d82) |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"'] | 3 | volkswagen/tiguan MY2014 (mcum-tiguan-4-door-2007-2016); volkswagen/tiguan MY2015 (mcum-tiguan-4-door-2007-2016); volkswagen/tiguan MY2016 (mcum-tiguan-4-door-2007-2016) |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N'] | 3 | volkswagen/atlas MY2025 (press-vw-atlas-2025-fd879fc0); volkswagen/atlas MY2026 (press-vw-atlas-2026-67e07c32); volkswagen/atlas MY2026 (press-vw-atlas-2026-90959a4c) |
| bore_stroke_in | one document gives N values: ['"N x N"', '"N x N"'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| bore_stroke_mm | one document gives N values: ['"N x N"', '"N x N"'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| compression_ratio | one document gives N values: ['"N:N"', '"N:N"'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| engine_description | one document gives N values: ['"NL, inline four cylinder, NV, turbocharged and intercooled, DI"', '"NL, inline | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| engine_displacement_cc | one document gives N values: ['N', 'N'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| power_hp | one document gives N values: ['N', 'N'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| power_rpm | one document gives N values: ['"N"', '"N"'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| torque_rpm | one document gives N values: ['"N"', '"N"'] | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| valvetrain | one document gives N values: ['"Double overhead camshaft, spur belt driven, four valves per cylinder, maintena | 2 | volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac); volkswagen/jetta MY2015 (press-vw-jetta-2015-96b3fce1) |
| cargo_l | not found unambiguously in the available US press specification pages | 2 | volkswagen/tiguan US2025+; volkswagen/atlas I-US-2018 |
| power_hp | not found unambiguously in the available US press specification pages | 1 | volkswagen/jetta VII |
| torque_lb_ft | not found unambiguously in the available US press specification pages | 1 | volkswagen/jetta VII |
| maintenance:transmission_fluid | row text not found again on one page: Transmission, Automatic - Change Fluid & filter (if applicable) | 1 | volkswagen/jetta MY2024 (volkswagen-maintenance-card-2024 p.4) |
| power_hp | value N outside the validator range; not used | 1 | volkswagen/touareg press-vw-touareg-2015-fd3a4d82 p.1 |
| engine_oil_capacity_l | no US owner's manual for these years | 1 | volkswagen/touareg 7P |
| engine_oil_viscosity | no US owner's manual for these years | 1 | volkswagen/touareg 7P |
| coolant | no US owner's manual for these years | 1 | volkswagen/touareg 7P |
| transmission_fluid | no US owner's manual for these years | 1 | volkswagen/touareg 7P |
| brake_fluid | no US owner's manual for these years | 1 | volkswagen/touareg 7P |

## 4. Конфликты источников

Конфликтов: 185. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 156
- sources of the same rank disagree; field not shown: 28
- model-year manual kept over the whole-generation page (Appendix E.6): 1

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Jetta | volkswagen/jetta VI MY2014 | curb_weight_kg | [1502.0] | [1393] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2014 | curb_weight_kg | [1502.0] | [1456] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2014 | curb_weight_kg | [1502.0] | [1307] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2015 | curb_weight_kg | [1547.0] | [1364] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2016 | curb_weight_kg | [1529.0] | [1364] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2017 | curb_weight_kg | [1441.0] | [1364] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2015 | curb_weight_kg | [1547.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2016 | curb_weight_kg | [1529.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2015 | curb_weight_kg | [1547.0] | [1272] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2016 | curb_weight_kg | [1529.0] | [1272] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2017 | curb_weight_kg | [1441.0] | [1272] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2017 | curb_weight_kg | [1441.0] | [1502] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2017 | track_rear_mm | [1532.0, 1534.0] | [1550] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2015 | curb_weight_kg | [1547.0] | [1417] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VI MY2016 | curb_weight_kg | [1529.0] | [1417] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2019 | length_mm | [4702.0, 4704.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2020 | length_mm | [4702.0, 4704.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2021 | length_mm | [4702.0, 4704.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2022 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2023 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2024 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2025 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2026 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2019 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2020 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2021 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2022 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2023 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2024 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2025 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2026 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2020 | length_mm | [4702.0, 4704.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2021 | length_mm | [4702.0, 4704.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2022 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2023 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2024 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2025 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2026 | length_mm | [4737.0, 4747.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2020 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2021 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2022 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2023 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2024 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2025 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Jetta | volkswagen/jetta VII MY2026 | width_mm | [1798.0] | [1810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | curb_weight_kg | [1579.0] | [1439] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | height_mm | [1486.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2017 | height_mm | [1486.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | track_front_mm | [1577.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2017 | track_front_mm | [1577.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | track_rear_mm | [1549.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2017 | track_rear_mm | [1549.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | height_mm | [1486.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | track_front_mm | [1577.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | track_rear_mm | [1549.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2022 | height_mm | [1491.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2022 | track_front_mm | [1567.0] | [1580] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | height_mm | [1486.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | track_front_mm | [1577.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2015 | track_rear_mm | [1549.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2017 | height_mm | [1486.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2017 | track_front_mm | [1577.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Passat | volkswagen/passat NMS MY2017 | track_rear_mm | [1549.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan 5N MY2014 | height_mm | [1704.0] | [1680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan 5N MY2014 | curb_weight_kg | [1629.0] | [1539] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan 5N MY2014 | height_mm | [1704.0] | [1680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan II-US-LWB MY2019 | curb_weight_kg | [1688.0] | [1749] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan II-US-LWB MY2021 | curb_weight_kg | [1694.0] | [1749] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan II-US-LWB MY2018 | length_mm | [4702.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tiguan | volkswagen/tiguan II-US-LWB MY2018 | length_mm | [4702.0] | [4720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | fuel_tank_l | 70.4 | [70.0] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | compression_ratio | None | ['12.0:1', '11.4:1'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | compression_ratio | None | ['12.0:1', '11.4:1'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | torque_rpm | None | ['2750', '3500'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | torque_rpm | None | ['2750', '3500'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | fuel_tank_l | None | [70.4, 73.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | fuel_tank_l | None | [70.4, 73.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | passenger_volume_l | None | [4352.3, 4360.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | passenger_volume_l | None | [4352.3, 4360.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | rear_brakes | None | ['12.2 x 0.9-in solid rear discs', '12.2 x 0.9-in vented rear discs'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | rear_brakes | None | ['12.2 x 0.9-in solid rear discs', '12.2 x 0.9-in vented rear discs'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | height_mm | None | [1781, 1788] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | height_mm | None | [1781, 1788] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | curb_weight_kg | None | [2007, 2008] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | curb_weight_kg | None | [2092, 2093] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | power_rpm | None | ['4500', '5000'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | power_rpm | None | ['4500', '5000'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | fuel_tank_l | None | [70.4, 73.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | fuel_tank_l | None | [70.4, 73.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | passenger_volume_l | None | [4352.3, 4360.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | passenger_volume_l | None | [4352.3, 4360.8] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | front_suspension | None | ['Strut-type with lower control arms, coil springs, telescopic dampers, anti-rol | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | front_suspension | None | ['Strut-type with lower control arms, coil springs, telescopic dampers, anti-rol | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | rear_suspension | None | ['Multilink with coil springs, telescopic dampers, anti-roll bar', 'roll bar Mul | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | rear_suspension | None | ['Multilink with coil springs, telescopic dampers, anti-roll bar', 'roll bar Mul | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | rear_brakes | None | ['12.2 x 0.9-in solid rear discs', '12.2 x 0.9-in vented rear discs'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | rear_brakes | None | ['12.2 x 0.9-in solid rear discs', '12.2 x 0.9-in vented rear discs'] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | curb_weight_kg | None | [1927, 1929] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | curb_weight_kg | None | [2012, 2014] | sources of the same rank disagree; field not shown |
| Atlas | volkswagen/atlas I-US-2018 MY2018 | height_mm | [1778.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2019 | height_mm | [1778.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2018 | track_front_mm | [1707.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2019 | track_front_mm | [1707.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | height_mm | [1778.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | height_mm | [1781.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | height_mm | [1781.0, 1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | height_mm | [1781.0, 1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | height_mm | [1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | height_mm | [1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | height_mm | [1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | track_front_mm | [1707.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | width_mm | [1991.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | curb_weight_kg | [1970.0] | [2084] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | curb_weight_kg | [1958.0] | [2084] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | curb_weight_kg | [1958.0] | [2084] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | height_mm | [1778.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | height_mm | [1781.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | height_mm | [1781.0, 1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | height_mm | [1781.0, 1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | height_mm | [1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | height_mm | [1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | height_mm | [1788.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | track_front_mm | [1707.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | track_front_mm | [1702.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | width_mm | [1991.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2018 | height_mm | [1778.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2019 | height_mm | [1778.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2018 | track_front_mm | [1707.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2019 | track_front_mm | [1707.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | height_mm | [1778.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | height_mm | [1781.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | height_mm | [1781.0, 1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | height_mm | [1781.0, 1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | height_mm | [1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | height_mm | [1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | height_mm | [1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | length_mm | [5037.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | curb_weight_kg | [1970.0] | [2084] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | curb_weight_kg | [1958.0] | [2084] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | curb_weight_kg | [1958.0] | [2084] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | height_mm | [1778.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | height_mm | [1781.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | height_mm | [1781.0, 1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | height_mm | [1781.0, 1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | height_mm | [1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | height_mm | [1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | height_mm | [1788.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2020 | length_mm | [5037.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2021 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2022 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2023 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2024 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2025 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Atlas | volkswagen/atlas I-US-2018 MY2026 | length_mm | [5098.0] | [4970] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Arteon | volkswagen/arteon I MY2021 | track_rear_mm | [1577.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Arteon | volkswagen/arteon I MY2023 | track_rear_mm | [1577.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2014 | track_rear_mm | [1659.0, 1669.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2016 | track_front_mm | [1656.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2016 | track_rear_mm | [1676.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2015 | track_front_mm | [1651.0, 1656.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2015 | track_rear_mm | [1669.0, 1676.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2014 | track_rear_mm | [1659.0, 1669.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2015 | track_front_mm | [1651.0, 1656.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2015 | track_rear_mm | [1669.0, 1676.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2016 | track_front_mm | [1656.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2017 | track_front_mm | [1656.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2016 | track_rear_mm | [1676.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Touareg | volkswagen/touareg 7P MY2017 | track_rear_mm | [1676.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 231 записей (10% каждой линейки), расхождений 0.
- arteon: 15 проверено, 0 расхождений
- atlas: 46 проверено, 0 расхождений
- jetta: 66 проверено, 0 расхождений
- passat: 24 проверено, 0 расхождений
- tiguan: 61 проверено, 0 расхождений
- touareg: 19 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Jetta VII (2019–2026): consumerreports.org: "The seventh generation Jetta has easy-to-use controls, great fuel economy, good cabin room" (https://www.consumerreports.org/cars/volkswagen/jetta/); cars.com: "Fully redesigned for 2019" (https://www.cars.com/research/volkswagen-jetta/) [media: generation starts MY2019]
- Passat: MY2020: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "2022 is the final year for the Passat." (https://www.consumerreports.org/cars/volkswagen/passat/); cars.com: "2020-2022 Passat" (https://www.cars.com/research/volkswagen-passat
- Tiguan II-US-LWB (2018–2024): consumerreports.org: "The second-generation Tiguan is one of the largest models in the small-SUV segment." (https://www.consumerreports.org/cars/volkswagen/tiguan/); cars.com: "It's been a long time coming, but a redesigned 2018 Volkswagen Tiguan has landed in the U.S." (https://www.cars.com/researc
- Tiguan US2025+ (2025–2026): consumerreports.org: "The Volkswagen Tiguan has been redesigned for 2025, with an all-new exterior and a longer wheelbase." (https://www.consumerreports.org/cars/volkswagen/tiguan/); cars.com: "Redesigned for 2025" (https://www.cars.com/research/volkswagen-tiguan/) [quote read once] [media: generati
- Atlas: MY2020: detected boundary (vPIC Canadian specifications: overall length 504 -> 497 cm (MY2019 -> MY2020; a change of 6 cm or more)) dropped; consumerreports.org: "2018 Model Redesign Year" (https://www.consumerreports.org/cars/volkswagen/atlas/); cars.com: "Brand-new model for 2018" (https://www.car
- Atlas: MY2021: detected boundary (vPIC Canadian specifications: overall length 504 -> 510 cm (MY2020 -> MY2021; a change of 6 cm or more)) dropped; consumerreports.org: "2018 Model Redesign Year" (https://www.consumerreports.org/cars/volkswagen/atlas/); cars.com: "Brand-new model for 2018" (https://www.car

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- volkswagen/jetta: --prune-stale, код 0, {"raw_documents_seen": 126, "source_records_new": 13, "te_existing": 1848, "configurations": 66, "configurations_research_only": 63, "configurations_linked": 3, "issues_existing": 80, "maintenance_new": 72}
- volkswagen/passat: --prune-stale, код 0, {"raw_documents_seen": 50, "te_existing": 698, "configurations": 21, "configurations_research_only": 21, "issues_existing": 47, "maintenance_new": 34}
- volkswagen/tiguan: --prune-stale, код 0, {"raw_documents_seen": 84, "te_existing": 1336, "configurations": 29, "configurations_research_only": 25, "configurations_linked": 4, "issues_existing": 80, "maintenance_new": 84}
- volkswagen/atlas: --prune-stale, код 0, {"raw_documents_seen": 56, "te_existing": 1011, "configurations": 27, "configurations_linked": 6, "configurations_research_only": 21, "issues_existing": 66, "maintenance_new": 27}
- volkswagen/arteon: --prune-stale, код 0, {"raw_documents_seen": 42, "te_existing": 328, "configurations": 11, "configurations_research_only": 11, "issues_existing": 12, "maintenance_new": 25}
- volkswagen/touareg: --prune-stale, код 0, {"raw_documents_seen": 28, "te_existing": 371, "configurations": 9, "configurations_research_only": 5, "configurations_linked": 4, "issues_existing": 19, "maintenance_new": 32}
