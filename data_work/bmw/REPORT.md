# BMW — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 Series | F30 | 2014–2018 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ● | ◐ | ● | ◐ | ● | ● | ● |
| 3 Series | Seventh generation · US sedan | 2019–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| 5 Series | F10 | 2014–2016 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ◐ | ● | ● | ● |
| 5 Series | G30 | 2017–2023 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| 5 Series | US2024+ | 2024–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| 7 Series | US2014-2015 | 2014–2015 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ◐ | ● | ● | ● |
| 7 Series | US2016-2022 | 2016–2022 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| 7 Series | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| X5 | F15 | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| X5 | US2019+ | 2019–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| X6 | US2014-2014 | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| X6 | US2015-2019 | 2015–2019 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ◐ | ◐ | ● | ● | ● |
| X6 | US2020+ | 2020–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| X7 | US2019+ | 2019–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ◐ | ○ | ● | ● | ● |
| M3 | US2015-2018 | 2015–2018 | ● | ◐ | ● | ● | ● | ● | ◐ | ○ | ● | ◐ | ● | ◐ | ● | ● | ● |
| M3 | US2021+ | 2021–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| M5 | US2014-2016 | 2014–2016 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ○ | ● | ◐ | ● | ◐ | ● | ● | ● |
| M5 | US2018-2023 | 2018–2023 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| M5 | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ◐ | ● | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| X5 M | US2015+ | 2015–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| X6 M | US2014-2019 | 2014–2019 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| X6 M | US2020+ | 2020–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |

Итого ячеек: заполнено 193, частично 78, нет 59, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 12256 |
| known_issues | 0 | 432 |
| maintenance_schedule_items | 0 | 36 |

## 3. Журнал пробелов

Записей в журнале пробелов: 919 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 401 | bmw-3-series-us-2014-2.0l-4cyl-turbo-diesel-a-s8-awd; bmw-3-series-us-2014-2.0l-4cyl-turbo-diesel-a-s8-rwd; bmw-3-series-us-2014-2.0l-4cyl-turbo-ice-a-s8-awd |
| width_mm | one document gives N values: ['N', 'N'] | 59 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-69e983f2); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-9ede91b6) |
| octane_aki | one document gives N values: ['N', 'N'] | 34 | bmw/3-series MY2014 (mcum-3-series-4-door-2013-2019); bmw/3-series MY2015 (mcum-3-series-4-door-2013-2019); bmw/3-series MY2016 (mcum-3-series-4-door-2013-2019) |
| transmission_description | one document gives N values: ['"automatic transmission"', '"automatic"'] | 21 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-69e983f2); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-9ede91b6) |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 16 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 16 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| coolant | not found unambiguously in the available US owner's manuals | 16 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 16 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| brake_fluid | not found unambiguously in the available US owner's manuals | 16 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| transmission_description | one document gives N values: ['"NHPN"', '"automatic transmission N"'] | 15 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-e1049003); bmw/3-series MY2014 (press-bmwgroup-3-series-2014-eec89c10); bmw/3-series MY2015 (press-bmwgroup-3-series-2015-0b4f3ad4) |
| power_hp | engine not stated; EPA lists several engines | 15 | bmw/3-series MY2026 (press-bmwgroup-3-series-2026-ed050784); bmw/3-series MY2015 (teoalida-ymmt-3e62c6fabe); bmw/3-series MY2017 (teoalida-ymmt-478df663bf) |
| power_rpm | engine not stated; EPA lists several engines | 15 | bmw/3-series MY2026 (press-bmwgroup-3-series-2026-ed050784); bmw/3-series MY2015 (teoalida-ymmt-3e62c6fabe); bmw/3-series MY2017 (teoalida-ymmt-478df663bf) |
| torque_rpm | engine not stated; EPA lists several engines | 15 | bmw/3-series MY2026 (press-bmwgroup-3-series-2026-ed050784); bmw/3-series MY2015 (teoalida-ymmt-3e62c6fabe); bmw/3-series MY2017 (teoalida-ymmt-478df663bf) |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 15 | bmw/x6 MY2020 (mcum-x6-4-door-2020-2025); bmw/x6 MY2021 (mcum-x6-4-door-2020-2025); bmw/x6 MY2022 (mcum-x6-4-door-2020-2025) |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 12 | bmw/3-series MY2014 (mcum-3-series-4-door-2013-2019); bmw/3-series MY2015 (mcum-3-series-4-door-2013-2019); bmw/3-series MY2016 (mcum-3-series-4-door-2013-2019) |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 12 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4) |
| front_suspension | not found unambiguously in the available US press specification pages | 9 | bmw/3-series F30; bmw/5-series F10; bmw/7-series US2014-2015 |
| rear_suspension | not found unambiguously in the available US press specification pages | 9 | bmw/3-series F30; bmw/5-series F10; bmw/7-series US2014-2015 |
| wheel_size_in | value N outside the validator range; not used | 7 | bmw/3-series press-bmwgroup-3-series-2026-ed050784 p.1; bmw/m5 press-bmwgroup-m5-2021-9fa55a65 p.1; bmw/m5 press-bmwgroup-m5-2021-9fa55a65 p.1 |
| cargo_l | not found unambiguously in the available US press specification pages | 7 | bmw/x5 F15; bmw/x6 US2015-2019; bmw/x6 US2020+ |
| wheel_size_in | one document gives N values: ['N', 'N', 'N'] | 6 | bmw/3-series MY2019 (press-bmwgroup-3-series-2019-d96bbe05); bmw/x5 MY2020 (press-bmwgroup-x5-2020-f241f74b); bmw/x5 MY2021 (press-bmwgroup-x5-2021-6942a683) |
| coolant_capacity_l | value N outside the validator range; not used | 6 | bmw/5-series mcum-5-series-4-door-2024-2025 p.664; bmw/x5 carmans-2023-bmw-x5 p.390; bmw/x6 carmans-2023-bmw-x6 p.378 |
| maintenance | the manual copy does not describe the CBS jobs (or the page is missing) | 6 | bmw/5-series MY2024-2025 (mcum-5-series-4-door-2024-2025); bmw/7-series MY2014-2014 (mcum-7-series-4-door-2008-2014); bmw/7-series MY2022-2025 (mcum-7-series-4-door-2022-2025) |
| engine_oil_capacity_l | no US owner's manual for these years | 6 | bmw/x5 F15; bmw/x5 US2019+; bmw/x6 US2014-2014 |
| engine_oil_viscosity | no US owner's manual for these years | 6 | bmw/x5 F15; bmw/x5 US2019+; bmw/x6 US2014-2014 |
| coolant | no US owner's manual for these years | 6 | bmw/x5 F15; bmw/x5 US2019+; bmw/x6 US2014-2014 |
| transmission_fluid | no US owner's manual for these years | 6 | bmw/x5 F15; bmw/x5 US2019+; bmw/x6 US2014-2014 |
| brake_fluid | no US owner's manual for these years | 6 | bmw/x5 F15; bmw/x5 US2019+; bmw/x6 US2014-2014 |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 5 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985); bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa); bmw/5-series MY2021 (press-bmwgroup-5-series-2021-dfae6ab7) |
| wheel_size_in | one document gives N values: ['N', 'N'] | 5 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985); bmw/5-series MY2024 (press-bmwgroup-5-series-2024-8292b63c); bmw/x5 MY2020 (press-bmwgroup-x5-2020-f241f74b) |
| power_hp | one document gives N values: ['N', 'N'] | 4 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985); bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa); bmw/5-series MY2018 (press-bmwgroup-5-series-2018-098c0c80) |
| engine_oil_specification | engine not stated; EPA lists several engines | 4 | bmw/5-series MY2014 (mcum-5-series-4-door-2010-2017); bmw/5-series MY2015 (mcum-5-series-4-door-2010-2017); bmw/5-series MY2016 (mcum-5-series-4-door-2010-2017) |
| transmission_description | one document gives N values: ['"NHPN"', '"Automatic"'] | 4 | bmw/7-series MY2020 (press-bmwgroup-7-series-2020-4df94d77); bmw/7-series MY2020 (press-bmwgroup-7-series-2020-4df94d77); bmw/7-series MY2020 (press-bmwgroup-7-series-2020-4df94d77) |
| curb_weight_kg | value N outside the validator range; not used | 4 | bmw/x5 press-bmwgroup-x5-2024-1d92d5e0 p.1; bmw/x6 press-bmwgroup-x5-2024-1d92d5e0 p.1; bmw/x5-m press-bmwgroup-x5-m-2020-c9fdb92e p.1 |
| transmission_description | one document gives N values: ['"GANXNDZ"', '"automatic"'] | 4 | bmw/x5 MY2020 (press-bmwgroup-x5-2020-f241f74b); bmw/x6 MY2020 (press-bmwgroup-x6-2020-887ba676); bmw/x7 MY2020 (press-bmwgroup-x5-2020-f241f74b) |
| electric_motor | one document gives N values: ['"N"', '"GCNPNA"'] | 3 | bmw/7-series MY2017 (press-bmwgroup-7-series-2017-580eaf18); bmw/7-series MY2017 (press-bmwgroup-7-series-2017-8b766732); bmw/7-series MY2018 (press-bmwgroup-7-series-2018-7b84e832) |
| front_brakes | not found unambiguously in the available US press specification pages | 3 | bmw/x7 US2019+; bmw/m3 US2015-2018; bmw/x6-m US2014-2019 |
| electric_motor | one document gives N values: ['"N"', '"GCNPNA"', '"Permanent activated synchronous maschine"'] | 2 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2018 (press-bmwgroup-3-series-2018-2f36bf41) |
| transmission_description | one document gives N values: ['"automatic transmission"', '"automatic"', '"manual transmission"'] | 2 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2018 (press-bmwgroup-3-series-2018-2f36bf41) |
| transmission_description | one document gives N values: ['"NHP"', '"automatic"'] | 2 | bmw/3-series MY2019 (press-bmwgroup-3-series-2019-d96bbe05); bmw/x5 MY2019 (press-bmwgroup-x5-2019-fca9ffa5) |
| wheel_size_in | one document gives N values: ['N', 'N', 'N', 'N'] | 2 | bmw/3-series MY2019 (press-bmwgroup-3-series-2019-d96bbe05); bmw/x5 MY2019 (press-bmwgroup-x5-2019-fca9ffa5) |
| transmission_description | one document gives N values: ['"GANPNHZ"', '"automatic"'] | 2 | bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa); bmw/x5 MY2021 (press-bmwgroup-x5-2021-6942a683) |
| torque_lb_ft | engine not stated; EPA lists several engines | 2 | bmw/3-series MY2026 (press-bmwgroup-3-series-2026-ed050784); bmw/7-series MY2017 (press-bmwgroup-7-series-2017-c6eb54ce) |
| power_hp | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| torque_lb_ft | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| tires | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| front_suspension | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| rear_suspension | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| front_brakes | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| steering | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| ground_clearance | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| cargo_l | no US press specification page for these years | 2 | bmw/7-series US2023+; bmw/x6 US2014-2014 |
| transmission_description | one document gives N values: ['"NHPN"', '"automatic transmission"'] | 2 | bmw/x5 MY2016 (press-bmwgroup-x5-2016-4d15d8af); bmw/x5 MY2016 (press-bmwgroup-x5-2016-4d15d8af) |
| transmission_description | one document gives N values: ['"NPNXPH"', '"automatic transmission"'] | 2 | bmw/x5 MY2016 (press-bmwgroup-x5-2016-4d15d8af); bmw/x5 MY2016 (press-bmwgroup-x5-2016-62d90d13) |
| electric_motor | one document gives N values: ['"N"', '"GCNPNMN"', '"drive"'] | 2 | bmw/x5 MY2017 (press-bmwgroup-x5-2017-cccb7b1f); bmw/x5 MY2018 (press-bmwgroup-x5-2018-b624bc8a) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 2 | bmw/x5 MY2020 (press-bmwgroup-x5-2020-f241f74b); bmw/x7 MY2020 (press-bmwgroup-x5-2020-f241f74b) |
| transmission_description | one document gives N values: ['"NHPN"', '"automatic"'] | 2 | bmw/x7 MY2019 (press-bmwgroup-x7-2019-26130d98); bmw/x7 MY2019 (press-bmwgroup-x7-2019-26130d98) |
| steering | not found unambiguously in the available US press specification pages | 2 | bmw/x7 US2019+; bmw/m5 US2014-2016 |
| transmission_description | one document gives N values: ['"MNHPN"', '"automatic transmission"'] | 2 | bmw/m5 MY2019 (press-bmwgroup-m5-2019-6f6cd412); bmw/m5 MY2020 (press-bmwgroup-m5-2020-318dbe98) |
| front_brakes | one document gives N values: ['"N mm / N in / Ventilated, cross drilled, compound rotor"', '"N piston fixed ca | 2 | bmw/x5-m MY2015 (press-bmwgroup-x5-m-2015-843f1b04); bmw/x6-m MY2015 (press-bmwgroup-x6-m-2015-0346e97e) |
| rear_brakes | one document gives N values: ['"N mm / N in / Ventilated, cross drilled, compound rotor"', '"Single piston flo | 2 | bmw/x5-m MY2015 (press-bmwgroup-x5-m-2015-843f1b04); bmw/x6-m MY2015 (press-bmwgroup-x6-m-2015-0346e97e) |
| transmission_description | one document gives N values: ['"M NHPN"', '"automatic transmission N"'] | 2 | bmw/x5-m MY2015 (press-bmwgroup-x5-m-2015-843f1b04); bmw/x6-m MY2015 (press-bmwgroup-x6-m-2015-0346e97e) |
| transmission_description | one document gives N values: ['"N-speed automatic"', '"MNHPN"'] | 2 | bmw/x5-m MY2020 (press-bmwgroup-x5-m-2020-c9fdb92e); bmw/x6-m MY2020 (press-bmwgroup-x5-m-2020-c9fdb92e) |
| bore_stroke_mm | one document gives N values: ['"N x N"', '"N x N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| bore_stroke_mm | one document gives N values: ['"N x N"', '"N x N"', '"N x N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N', 'N', 'N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| engine_displacement_cc | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| engine_displacement_cc | one document gives N values: ['N', 'N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| front_brakes | one document gives N values: ['"disc ventilated / N"', '"disc ventilated // N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| ground_clearance | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| height_mm | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| injection | one document gives N values: ['"Commom rail direct injection / CRN"', '"High precision direct injection"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| power_hp | one document gives N values: ['N', 'N', 'N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| power_rpm | one document gives N values: ['"N-N"', '"N-N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| power_rpm | one document gives N values: ['"N"', '"N-N"', '"N-N"', '"N-N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| rear_brakes | one document gives N values: ['"disc ventilated / N"', '"disc ventilated // N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| rear_brakes | one document gives N values: ['"disc ventilated / N"', '"disc ventilated // N"', '"disc ventilated //N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| torque_lb_ft | one document gives N values: ['N', 'N', 'N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| torque_rpm | one document gives N values: ['"N-N"', '"N-N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| torque_rpm | one document gives N values: ['"N-N"', '"N-N"', '"N-N"', '"N-N"'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| track_front_mm | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| track_rear_mm | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| track_rear_mm | one document gives N values: ['N', 'N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| transmission_description | one document gives N values: ['"NHPN"', '"I plus"', '"K"', '"automatic transmission N"', '"manual transmission | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| transmission_description | one document gives N values: ['"NHPN"', '"NPNH"', '"Hybridgetriebe GenN N"', '"I plus"', '"automatic transmiss | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| turning_circle_m | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-75739985) |
| engine_description | one document gives N values: ['"-- GCNPNA"', '"N"'] | 1 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-69e983f2) |
| transmission_description | one document gives N values: ['"NHP Sport"', '"automatic"'] | 1 | bmw/3-series MY2020 (press-bmwgroup-3-series-2020-e14a30eb) |
| power_rpm | one document gives N values: ['"N,N"', '"N,N \\uN N,N"'] | 1 | bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa) |
| system_power_hp | one document gives N values: ['N', 'N'] | 1 | bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa) |
| torque_rpm | one document gives N values: ['"N - N,N"', '"N,N \\uN N,N"'] | 1 | bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa) |
| torque_rpm | one document gives N values: ['"N \\uN N,N"', '"N,N \\uN N,N"'] | 1 | bmw/3-series MY2021 (press-bmwgroup-3-series-2021-c00ec7aa) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 1 | bmw/3-series MY2026 (press-bmwgroup-3-series-2026-ed050784) |
| compression_ratio | engine not stated; EPA lists several engines | 1 | bmw/3-series MY2026 (press-bmwgroup-3-series-2026-ed050784) |
| transmission_description | one document gives N values: ['"NHPNH"', '"automatic transmission N"'] | 1 | bmw/5-series MY2015 (press-bmwgroup-5-series-2015-f1e0e421) |
| power_rpm | one document gives N values: ['"N,N-N,N"', '"N,N"'] | 1 | bmw/5-series MY2021 (press-bmwgroup-5-series-2021-dfae6ab7) |
| power_rpm | one document gives N values: ['"N,N-N,N"', '"N"'] | 1 | bmw/5-series MY2021 (press-bmwgroup-5-series-2021-dfae6ab7) |
| torque_rpm | one document gives N values: ['"N,N \\uN N,N"', '"N \\uN N,N"'] | 1 | bmw/5-series MY2021 (press-bmwgroup-5-series-2021-dfae6ab7) |
| cargo_l | value N outside the validator range; not used | 1 | bmw/7-series press-bmwgroup-7-series-2017-c6eb54ce p.1 |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 1 | bmw/7-series MY2014 (mcum-7-series-4-door-2008-2014) |
| steering | one document gives N values: ['"EPS"', '"rack-and-pinion"'] | 1 | bmw/7-series MY2016 (press-bmwgroup-7-series-2016-4a36a889) |
| engine_description | engine not stated; EPA lists several engines | 1 | bmw/7-series MY2017 (press-bmwgroup-7-series-2017-c6eb54ce) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 1 | bmw/7-series MY2017 (press-bmwgroup-7-series-2017-c6eb54ce) |
| injection | engine not stated; EPA lists several engines | 1 | bmw/7-series MY2017 (press-bmwgroup-7-series-2017-c6eb54ce) |
| engine_description | one document gives N values: ['"-- -"', '"N"'] | 1 | bmw/7-series MY2018 (press-bmwgroup-7-series-2018-2276a2a3) |
| transmission_description | one document gives N values: ['"NPNH"', '"Automatic"'] | 1 | bmw/7-series MY2020 (press-bmwgroup-7-series-2020-4df94d77) |
| fuel_tank_l | not found unambiguously in the available US owner's manuals | 1 | bmw/7-series US2023+ |
| engine_description | one document gives N values: ['"BNBNMN"', '"Inline-N"'] | 1 | bmw/x6 MY2020 (press-bmwgroup-x6-2020-887ba676) |
| engine_description | one document gives N values: ['"NNBNTN"', '"VN"'] | 1 | bmw/x6 MY2020 (press-bmwgroup-x6-2020-887ba676) |
| transmission_description | one document gives N values: ['"GANLNCZ"', '"automatic"'] | 1 | bmw/x6 MY2020 (press-bmwgroup-x6-2020-887ba676) |
| transmission_description | one document gives N values: ['"GANXNCZ"', '"automatic"'] | 1 | bmw/x6 MY2020 (press-bmwgroup-x6-2020-887ba676) |
| fuel_tank_l | no US owner's manual for these years | 1 | bmw/x6 US2014-2014 |
| front_brakes | one document gives N values: ['"disc ventilated / N"', '"disc ventilated / N"'] | 1 | bmw/m3 MY2015 (press-bmwgroup-m3-2015-59b0fac6) |
| rear_brakes | one document gives N values: ['"disc ventilated / N"', '"disc ventilated / N"'] | 1 | bmw/m3 MY2015 (press-bmwgroup-m3-2015-59b0fac6) |
| transmission_description | one document gives N values: ['"DKG N"', '"manual transmission N"'] | 1 | bmw/m3 MY2015 (press-bmwgroup-m3-2015-59b0fac6) |
| cargo_l | one document gives N values: ['N', 'N'] | 1 | bmw/m3 MY2018 (press-bmwgroup-m3-2018-e0576169) |
| transmission_description | one document gives N values: ['"DKG N"', '"G"', '"M-DKG N"', '"manual transmission N"'] | 1 | bmw/m5 MY2015 (press-bmwgroup-m5-2015-0725d70b) |
| torque_lb_ft | not found unambiguously in the available US press specification pages | 1 | bmw/m5 US2025+ |

## 4. Конфликты источников

Конфликтов: 265. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 226
- sources of the same rank disagree; field not shown: 39

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| 3 Series | bmw/3-series F30 MY2015 | curb_weight_kg | [1715.0, 1735.0, 1785.0, 1819.0] | [1474] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2014 | curb_weight_kg | [1715.0, 1719.0, 1776.0, 1819.0] | [1495] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2014 | curb_weight_kg | [1715.0, 1719.0, 1776.0, 1819.0] | [1565] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2015 | curb_weight_kg | [1715.0, 1735.0, 1785.0, 1819.0] | [1565] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2014 | curb_weight_kg | [1715.0, 1719.0, 1776.0, 1819.0] | [1642] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2015 | curb_weight_kg | [1715.0, 1735.0, 1785.0, 1819.0] | [1642] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2015 | curb_weight_kg | [1715.0, 1735.0, 1785.0, 1819.0] | [1524] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2014 | curb_weight_kg | [1715.0, 1719.0, 1776.0, 1819.0] | [1545] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2014 | curb_weight_kg | [1715.0, 1719.0, 1776.0, 1819.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2015 | curb_weight_kg | [1715.0, 1735.0, 1785.0, 1819.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2015 | curb_weight_kg | [1715.0, 1735.0, 1785.0, 1819.0] | [1608] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2014 | curb_weight_kg | [1715.0, 1719.0, 1776.0, 1819.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2017 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series F30 MY2018 | length_mm | [4643.0, 4826.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | curb_weight_kg | [1625.0, 1707.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | height_mm | [1443.0, 1448.0] | [1510] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | length_mm | [4717.0] | [4830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | track_front_mm | [1582.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | wheelbase_mm | [2850.0] | [2920] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | curb_weight_kg | [1625.0, 1707.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | height_mm | [1443.0, 1448.0] | [1510] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | length_mm | [4717.0] | [4830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | track_front_mm | [1582.0] | [1540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | wheelbase_mm | [2850.0] | [2920] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | height_mm | [1443.0, 1448.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | length_mm | [4717.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | track_front_mm | [1582.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | wheelbase_mm | [2850.0] | [2810] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2019 | curb_weight_kg | [1625.0, 1707.0] | [1770] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2021 | curb_weight_kg | [1832.0, 1877.0] | [1770] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | length_mm | [4722.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | track_rear_mm | [1567.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2020 | curb_weight_kg | [1746.0, 1800.0] | [1585] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2021 | curb_weight_kg | [1832.0, 1877.0] | [1585] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | curb_weight_kg | [1653.0, 1702.0, 1767.0, 1818.0] | [1585] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2026 | curb_weight_kg | [1818.0] | [1585] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | length_mm | [4722.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2026 | length_mm | [4722.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | track_rear_mm | [1567.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2026 | track_rear_mm | [1567.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2021 | curb_weight_kg | [1832.0, 1877.0] | [1735] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2026 | curb_weight_kg | [1818.0] | [1735] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | length_mm | [4722.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2026 | length_mm | [4722.0] | [4710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2025 | track_rear_mm | [1567.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 3 Series | bmw/3-series Seventh generation · US sedan MY2026 | track_rear_mm | [1567.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2017 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series G30 MY2018 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series G30 MY2019 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series G30 MY2020 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series G30 MY2021 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series G30 MY2022 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series G30 MY2023 | platform_code | None | ['G30, G31', 'G30, G31, G38'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series US2024+ MY2024 | platform_code | None | ['G60, G61', 'G60, G61, G68'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series US2024+ MY2025 | platform_code | None | ['G60, G61', 'G60, G61, G68'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series US2024+ MY2026 | platform_code | None | ['G60, G61', 'G60, G61, G68'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series F10 MY2014 | platform_code | None | ['F10, F11', 'F10, F11, F18'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series F10 MY2015 | platform_code | None | ['F10, F11', 'F10, F11, F18'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series F10 MY2016 | platform_code | None | ['F10, F11', 'F10, F11, F18'] | sources of the same rank disagree; field not shown |
| 5 Series | bmw/5-series F10 MY2015 | length_mm | [4912.0, 5006.0] | [4900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series F10 MY2015 | length_mm | [4912.0, 5006.0] | [4900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series F10 MY2015 | length_mm | [4912.0, 5006.0] | [4900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series F10 MY2015 | length_mm | [4912.0, 5006.0] | [4900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series F10 MY2015 | length_mm | [4912.0, 5006.0] | [4900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series F10 MY2015 | length_mm | [4912.0, 5006.0] | [4900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2017 | curb_weight_kg | [1699.0, 1745.0, 1759.0, 1823.0, 2037.0, 2100.0, 2241.0] | [1615] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2018 | curb_weight_kg | [1699.0, 1745.0, 1759.0, 1823.0, 1935.0, 1983.0, 1989.0] | [2064] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2021 | length_mm | [4973.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2017 | curb_weight_kg | [1699.0, 1745.0, 1759.0, 1823.0, 2037.0, 2100.0, 2241.0] | [1615] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2021 | length_mm | [4973.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2021 | length_mm | [4973.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2018 | curb_weight_kg | [1699.0, 1745.0, 1759.0, 1823.0, 1935.0, 1983.0, 1989.0] | [2058] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series G30 MY2021 | length_mm | [4973.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | height_mm | [1514.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | length_mm | [5060.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_front_mm | [1623.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_rear_mm | [1656.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | wheelbase_mm | [2995.0] | [2980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | width_mm | [1900.0] | [1870] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | curb_weight_kg | [1833.0, 1886.0] | [1680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | height_mm | [1514.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | length_mm | [5060.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_front_mm | [1623.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_rear_mm | [1656.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | wheelbase_mm | [2995.0] | [2980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | width_mm | [1900.0] | [1870] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | curb_weight_kg | [1833.0, 1886.0] | [1745] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | height_mm | [1514.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | length_mm | [5060.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_front_mm | [1623.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_rear_mm | [1656.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | wheelbase_mm | [2995.0] | [2980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | width_mm | [1900.0] | [1870] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | height_mm | [1514.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | length_mm | [5060.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_front_mm | [1623.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_rear_mm | [1656.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | wheelbase_mm | [2995.0] | [2980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | width_mm | [1900.0] | [1870] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | height_mm | [1514.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | curb_weight_kg | [1833.0, 1886.0] | [2230] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | height_mm | [1514.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | curb_weight_kg | [1833.0, 1886.0] | [2380] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_front_mm | [1623.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_rear_mm | [1656.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | curb_weight_kg | [1833.0, 1886.0] | [2280] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_front_mm | [1623.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 5 Series | bmw/5-series US2024+ MY2024 | track_rear_mm | [1656.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2016 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2016-2022 MY2017 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2016-2022 MY2018 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2016-2022 MY2019 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2016-2022 MY2020 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2016-2022 MY2021 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2016-2022 MY2022 | platform_code | None | ['G11, G12', 'G10, G11'] | sources of the same rank disagree; field not shown |
| 7 Series | bmw/7-series US2014-2015 MY2015 | track_rear_mm | [1651.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2014-2015 MY2015 | track_rear_mm | [1651.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2014-2015 MY2015 | track_rear_mm | [1651.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2014-2015 MY2015 | track_rear_mm | [1651.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2014-2015 MY2015 | track_rear_mm | [1651.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2016 | length_mm | [5248.0] | [5100] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2017 | length_mm | [5248.0] | [5100] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2018 | length_mm | [5248.0, 5250.0] | [5100] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2020 | length_mm | [5268.0] | [5120] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2016 | wheelbase_mm | [3211.0] | [3070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2017 | wheelbase_mm | [3211.0] | [3070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2018 | wheelbase_mm | [3211.0] | [3070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| 7 Series | bmw/7-series US2016-2022 MY2020 | wheelbase_mm | [3211.0] | [3070] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2014 | platform_code | None | ['F15', 'F15, F85'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 F15 MY2015 | platform_code | None | ['F15', 'F15, F85'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 F15 MY2016 | platform_code | None | ['F15', 'F15, F85'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 F15 MY2017 | platform_code | None | ['F15', 'F15, F85'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 F15 MY2018 | platform_code | None | ['F15', 'F15, F85'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2019 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2020 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2024 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2025 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2026 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2021 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2022 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 US2019+ MY2023 | platform_code | None | ['G05', 'G05, G18, F95'] | sources of the same rank disagree; field not shown |
| X5 | bmw/x5 F15 MY2014 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2015 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2016 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2014 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2015 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2016 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2014 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2015 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2016 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2017 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 F15 MY2018 | length_mm | [4907.0] | [4890] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 US2019+ MY2021 | curb_weight_kg | [2573.0] | [2420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 US2019+ MY2020 | curb_weight_kg | [2386.0, 2568.0] | [2258] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 US2019+ MY2021 | curb_weight_kg | [2573.0] | [2258] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 US2019+ MY2021 | curb_weight_kg | [2573.0] | [2339] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 | bmw/x5 US2019+ MY2021 | curb_weight_kg | [2573.0] | [2435] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2015 | platform_code | None | ['F16', 'F16, F86'] | sources of the same rank disagree; field not shown |
| X6 | bmw/x6 US2015-2019 MY2016 | platform_code | None | ['F16', 'F16, F86'] | sources of the same rank disagree; field not shown |
| X6 | bmw/x6 US2015-2019 MY2017 | platform_code | None | ['F16', 'F16, F86'] | sources of the same rank disagree; field not shown |
| X6 | bmw/x6 US2015-2019 MY2018 | platform_code | None | ['F16', 'F16, F86'] | sources of the same rank disagree; field not shown |
| X6 | bmw/x6 US2015-2019 MY2019 | platform_code | None | ['F16', 'F16, F86'] | sources of the same rank disagree; field not shown |
| X6 | bmw/x6 US2015-2019 MY2015 | height_mm | [1689.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2015 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2017 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2018 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2015 | curb_weight_kg | [2100.0] | [2345] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2015 | height_mm | [1689.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2015 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2017 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2015-2019 MY2018 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2020+ MY2020 | track_front_mm | [1679.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2020+ MY2024 | track_front_mm | [1676.0, 1679.0, 1684.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2020+ MY2024 | curb_weight_kg | [2267.0, 2269.0, 2404.0, 2429.0, 2528.0] | [2175] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2020+ MY2020 | track_front_mm | [1679.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 | bmw/x6 US2020+ MY2024 | track_front_mm | [1676.0, 1679.0, 1684.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X7 | bmw/x7 US2019+ MY2023 | height_mm | [1796.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X7 | bmw/x7 US2019+ MY2021 | curb_weight_kg | [2568.0, 2658.0] | [2440] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X7 | bmw/x7 US2019+ MY2023 | curb_weight_kg | [2715.0] | [2457] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X7 | bmw/x7 US2019+ MY2023 | height_mm | [1796.0] | [1830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2015-2018 MY2018 | length_mm | [4686.0] | [4670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2015-2018 MY2015 | length_mm | [4686.0] | [4670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2015-2018 MY2017 | length_mm | [4686.0] | [4670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2022 | curb_weight_kg | [1805.0, 1810.0] | [1705] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2024 | curb_weight_kg | [1776.0] | [1705] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2021 | length_mm | [4803.0] | [4790] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2022 | length_mm | [4803.0] | [4790] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2025 | length_mm | [4803.0] | [4790] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2024 | width_mm | [1918.0] | [1900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M3 | bmw/m3 US2021+ MY2025 | width_mm | [1887.0] | [1900] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2018 | tires | None | ['275/40 ZR 19 102Y 285/40 ZR', '275/40 ZR 19 102Y; 285/40 ZR 19 104Y'] | sources of the same rank disagree; field not shown |
| M5 | bmw/m5 US2014-2016 MY2015 | height_mm | [1448.0] | [1460] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2014-2016 MY2015 | track_front_mm | [1628.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2014-2016 MY2015 | track_rear_mm | [1582.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2014-2016 MY2015 | width_mm | [1890.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2021 | length_mm | [4989.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2018 | track_front_mm | [1626.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2019 | track_front_mm | [1626.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2020 | track_front_mm | [1626.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2021 | track_front_mm | [1626.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2018 | track_rear_mm | [1595.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2019 | track_rear_mm | [1595.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2020 | track_rear_mm | [1595.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2018-2023 MY2018 | width_mm | [1902.0] | [1870] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | curb_weight_kg | [2445.0, 2508.0] | [1982] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | height_mm | [1509.0, 1516.0] | [1470] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | length_mm | [5095.0] | [4960] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | track_front_mm | [1684.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | track_rear_mm | [1661.0] | [1630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | wheelbase_mm | [3005.0] | [2980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| M5 | bmw/m5 US2025+ MY2025 | width_mm | [1971.0] | [1870] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2020 | curb_weight_kg | [2438.0, 2461.0] | [2350] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2024 | curb_weight_kg | [2474.0, 2494.0] | [2350] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2017 | height_mm | [1717.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2018 | height_mm | [1717.0] | [1750] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2017 | length_mm | [4895.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2018 | length_mm | [4895.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2024 | length_mm | [4948.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2020 | track_front_mm | [1699.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2024 | track_front_mm | [1699.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2024 | track_rear_mm | [1689.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2020 | wheelbase_mm | [2972.0] | [2930] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2024 | wheelbase_mm | [2972.0] | [2930] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X5 M | bmw/x5-m US2015+ MY2024 | width_mm | [2014.0, 2019.0] | [1980] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2015 | height_mm | [1689.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2017 | height_mm | [1689.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2018 | height_mm | [1689.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2015 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2017 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2018 | length_mm | [4923.0] | [4910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2015 | track_front_mm | [1666.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2017 | track_front_mm | [1666.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2018 | track_front_mm | [1666.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2015 | track_rear_mm | [1666.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2017 | track_rear_mm | [1666.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2014-2019 MY2018 | track_rear_mm | [1666.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2020+ MY2020 | track_front_mm | [1699.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2020+ MY2024 | track_front_mm | [1699.0] | [1640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2020+ MY2024 | track_rear_mm | [1689.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| X6 M | bmw/x6-m US2020+ MY2024 | width_mm | [2014.0, 2019.0] | [2000] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 638 записей (10% каждой линейки), расхождений 0.
- 3-series: 174 проверено, 0 расхождений
- 5-series: 121 проверено, 0 расхождений
- 7-series: 93 проверено, 0 расхождений
- m3: 53 проверено, 0 расхождений
- m5: 25 проверено, 0 расхождений
- x5: 84 проверено, 0 расхождений
- x5-m: 16 проверено, 0 расхождений
- x6: 35 проверено, 0 расхождений
- x6-m: 17 проверено, 0 расхождений
- x7: 20 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- 3 Series Seventh generation · US sedan (2019–2026): consumerreports.org: "The redesigned 3 Series sedan brings new infotainment tech, standard advanced safety features, improved handling, and better fuel economy." (https://www.consumerreports.org/cars/bmw/3-series/); cars.com: "Redesigned for 2019" (https://www.cars.com/research/bmw-330/) [media: gen
- 5 Series G30 (2017–2023): consumerreports.org: "BMW focused on adding technology and on sharpening the handling of the 2017 5 Series redesign." (https://www.consumerreports.org/cars/bmw/5-series/); cars.com: "Redesigned for 2017" (https://www.cars.com/research/bmw-530/) [media: generation starts MY2017]
- 5 Series US2024+ (2024–2026): consumerreports.org: "The redesigned 5 Series is larger than its predecessor, and has lightly smoothed-out styling." (https://www.consumerreports.org/cars/bmw/5-series/); cars.com: "For 2024, the eighth generation of the 5 Series sees other changes, including revised styling, updated gas powertrains
- 7 Series US2016-2022 (2016–2022): consumerreports.org: "2016 Model Redesign Year" (https://www.consumerreports.org/cars/bmw/7-series/); cars.com: "Redesigned for 2016" (https://www.cars.com/research/bmw-750/) [media: generation starts MY2016]
- 7 Series US2023+ (2023–2026): consumerreports.org: "In redesigning the 7 Series for 2023, BMW also introduced an EV version called the i7." (https://www.consumerreports.org/cars/bmw/7-series/); cars.com: "BMW has revealed a redesigned version of its lower-riding stablemate — the 2023 7 Series sedan." (https://www.cars.com/articl
- X5 US2019+ (2019–2026): consumerreports.org: "The redesigned 2019 X5 is one of the best vehicles we've ever tested." (https://www.consumerreports.org/cars/bmw/x5/); cars.com: "BMW redesigned its mid-size X5 SUV for the 2019 model year, and the fourth generation of the X5 has a little bit more of everything" (https://www.ca
- X6 US2020+ (2020–2026): consumerreports.org: "The 2020 X6 is a coupelike, sporty SUV that's based on the redesigned X5." (https://www.consumerreports.org/cars/bmw/x6/); cars.com: "Redesigned for 2020" (https://www.cars.com/research/bmw-x6/) [quote read once] [media: generation starts MY2020]
- X6: MY2015: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "Styling was refreshed for 2015 and the V8 engine got more power." (https://www.consumerreports.org/cars/bmw/x6/); cars.com: "2015-2019" (https://www.cars.com/research/bmw-x6/) 
- X6: MY2015: media disagree whether a generation starts here; the data boundary is kept
- M5 US2018-2023 (2018–2023): cars.com: "New all-wheel drive with selectable rear-wheel drive" (https://www.cars.com/research/bmw-m5/) [media: generation starts MY2018]
- M5 US2025+ (2025–2026): cars.com: "Redesigned for 2025" (https://www.cars.com/research/bmw-m5/) [media: generation starts MY2025]
- M5: MY2013: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2013-2016 M5" (https://www.cars.com/research/bmw-m5/) [media: weak])
- X5 M: MY2015: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2015-2018 X5 M" (https://www.cars.com/research/bmw-x5_m/) [media: weak])
- X5 M: MY2020: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2020-2026 X5 M" (https://www.cars.com/research/bmw-x5_m/) [media: weak])
- X6 M US2020+ (2020–2026): cars.com: "2020-2027 X6 M" (https://www.cars.com/research/bmw-x6_m/) [media: generation starts MY2020]
- X6 M: MY2010: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2010-2014" (https://www.cars.com/research/bmw-x6_m/) [media: weak])
- X6 M: MY2015: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2015-2019 X6 M" (https://www.cars.com/research/bmw-x6_m/) [media: weak])

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- bmw/3-series: --prune-stale, код 0, {"raw_documents_seen": 212, "te_existing": 3017, "configurations": 89, "configurations_research_only": 89, "issues_existing": 61, "maintenance_new": 6}
- bmw/5-series: --prune-stale, код 0, {"raw_documents_seen": 125, "te_existing": 2410, "configurations": 87, "configurations_linked": 19, "configurations_research_only": 68, "issues_existing": 66, "maintenance_new": 9}
- bmw/7-series: --prune-stale, код 0, {"raw_documents_seen": 104, "te_existing": 1861, "configurations": 62, "configurations_research_only": 62, "issues_existing": 52, "maintenance_new": 6}
- bmw/x5: --prune-stale, код 0, {"raw_documents_seen": 79, "te_existing": 1580, "configurations": 51, "configurations_research_only": 44, "configurations_linked": 7, "issues_existing": 76}
- bmw/x6: --prune-stale, код 0, {"raw_documents_seen": 58, "te_existing": 844, "configurations": 33, "configurations_research_only": 33, "issues_existing": 62, "maintenance_new": 3}
- bmw/x7: --prune-stale, код 0, {"raw_documents_seen": 36, "te_existing": 499, "configurations": 16, "configurations_research_only": 16, "issues_existing": 42}
- bmw/m3: --prune-stale, код 0, {"raw_documents_seen": 58, "te_existing": 828, "configurations": 25, "configurations_research_only": 25, "issues_existing": 19, "maintenance_new": 6}
- bmw/m5: --prune-stale, код 0, {"raw_documents_seen": 48, "te_existing": 538, "configurations": 14, "configurations_research_only": 14, "issues_existing": 37, "maintenance_new": 6}
- bmw/x5-m: --prune-stale, код 0, {"raw_documents_seen": 32, "te_existing": 321, "configurations": 11, "configurations_research_only": 11, "issues_existing": 9}
- bmw/x6-m: --prune-stale, код 0, {"raw_documents_seen": 28, "te_existing": 358, "configurations": 13, "configurations_research_only": 13, "issues_existing": 8}
