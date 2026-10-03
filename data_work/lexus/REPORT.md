# Lexus — отчёт по базе технических данных US

Сформировано 2026-10-03T18:00:06+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | VI | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| ES | US2019-2025 | 2019–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| ES | US2026+ | 2026–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| RX | III | 2014–2015 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| RX | AL20 | 2016–2022 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| RX | US2023+ | 2023–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| NX | I-US-2015 | 2015–2021 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| NX | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| GX | II (2010 redesign) | 2014–2023 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| GX | US2024+ | 2024–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ● | ◐ | ● | ● | ● |

Итого ячеек: заполнено 79, частично 36, нет 35, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 4009 |
| known_issues | 0 | 95 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 391 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 141 | lexus-es-us-2014-2.5l-4cyl-hev-a-av-s6-fwd; lexus-es-us-2014-3.5l-6cyl-ice-a-s6-fwd; lexus-es-us-2015-2.5l-4cyl-hev-a-av-s6-fwd |
| wheel_size_in | one document gives N values: ['N', 'N'] | 54 | lexus/es MY2014 (press-lexus-es-2014-177214e2); lexus/es MY2015 (press-lexus-es-2015-b472453e); lexus/es MY2016 (press-lexus-es-2016-4597186e) |
| width_mm | one document gives N values: ['N', 'N'] | 12 | lexus/nx MY2015 (press-lexus-nx-2015-956632da); lexus/nx MY2015 (press-lexus-nx-2015-c09ddda3); lexus/nx MY2016 (press-lexus-nx-2016-260ec3e9) |
| engine_oil_capacity_l | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| engine_oil_viscosity | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| coolant | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| transmission_fluid | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| brake_fluid | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| height_mm | one document gives N values: ['N', 'N'] | 9 | lexus/rx MY2019 (press-lexus-rx-2019-620346fa); lexus/rx MY2019 (press-lexus-rx-2019-fddbf21b); lexus/rx MY2020 (press-lexus-rx-2020-6092356b) |
| cargo_l | one document gives N values: ['N', 'N'] | 8 | lexus/rx MY2021 (press-lexus-rx-2021-8f65d05d); lexus/rx MY2022 (press-lexus-rx-2022-ebf3602b); lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1) |
| electric_motor | one document gives N values: ['"N hp (N kW)"', '"AC NV N hp (NkW)"', '"AC NV"', '"Drives front wheels, regener | 8 | lexus/nx MY2015 (press-lexus-nx-2015-956632da); lexus/nx MY2016 (press-lexus-nx-2016-260ec3e9); lexus/nx MY2017 (press-lexus-nx-2017-3fdeafe7) |
| wheel_size_in | one document gives N values: ['N', 'N', 'N'] | 7 | lexus/es MY2019 (press-lexus-es-2019-cb5f82d0); lexus/es MY2020 (press-lexus-es-2020-15579eb6); lexus/es MY2021 (press-lexus-es-2021-01bc7c9d) |
| turning_circle_m | value N outside the validator range; not used | 6 | lexus/rx press-lexus-rx-2021-341ddde1 p.3; lexus/rx press-lexus-rx-2022-07d119c0 p.3; lexus/nx press-lexus-nx-2016-9100f406 p.3 |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N'] | 6 | lexus/rx MY2018 (press-lexus-rx-2018-2c4a1afe); lexus/rx MY2018 (press-lexus-rx-2018-8bdddf04); lexus/rx MY2019 (press-lexus-rx-2019-38a6fb49) |
| electric_motor | one document gives N values: ['"Function Drives front wheels, regenerative braking Type Permanent magnet synch | 6 | lexus/rx MY2018 (press-lexus-rx-2018-d5962412); lexus/rx MY2018 (press-lexus-rx-2018-f11ff3f0); lexus/rx MY2019 (press-lexus-rx-2019-86cc6501) |
| electric_motor | one document gives N values: ['"N hp (N kW)"', '"N hp (N kW)"', '"AC NV"', '"Drives front wheels, regenerative | 5 | lexus/rx MY2014 (press-lexus-rx-2014-31315e67); lexus/rx MY2015 (press-lexus-rx-2015-45a8ce15); lexus/rx MY2016 (press-lexus-rx-2016-79cda6bb) |
| passenger_volume_l | one document gives N values: ['N', 'N'] | 4 | lexus/es MY2020 (press-lexus-es-2020-15579eb6); lexus/es MY2021 (press-lexus-es-2021-01bc7c9d); lexus/es MY2022 (press-lexus-es-2022-56a1722e) |
| cargo_l | value N outside the validator range; not used | 4 | lexus/rx press-lexus-rx-2018-2c4a1afe p.1; lexus/rx press-lexus-rx-2018-8bdddf04 p.1; lexus/rx press-lexus-rx-2018-d5962412 p.1 |
| cargo_l | one document gives N values: ['N', 'N', 'N', 'N', 'N', 'N'] | 4 | lexus/rx MY2018 (press-lexus-rx-2018-2c4a1afe); lexus/rx MY2018 (press-lexus-rx-2018-8bdddf04); lexus/rx MY2018 (press-lexus-rx-2018-d5962412) |
| ground_clearance | not found unambiguously in the available US press specification pages | 3 | lexus/es VI; lexus/es US2019-2025; lexus/rx US2023+ |
| electric_motor | one document gives N values: ['"AC NV"', '"Drives front wheels, regeneration during braking"', '"Drives rear w | 3 | lexus/nx MY2022 (press-lexus-nx-2022-677d29eb); lexus/nx MY2023 (press-lexus-nx-2023-11eb8793); lexus/nx MY2024 (press-lexus-nx-2024-c04f30b9) |
| electric_motor | one document gives N values: ['"Drives front wheels, regeneration during braking"', '"Drives rear wheels, rege | 3 | lexus/nx MY2022 (press-lexus-nx-2022-dd6ab453); lexus/nx MY2023 (press-lexus-nx-2023-e3f193f6); lexus/nx MY2024 (press-lexus-nx-2024-b350314f) |
| height_mm | one document gives N values: ['N', 'N', 'N'] | 3 | lexus/gx MY2020 (press-lexus-gx-2020-5473b1b9); lexus/gx MY2021 (press-lexus-gx-2021-38081976); lexus/gx MY2022 (press-lexus-gx-2022-94c61d0c) |
| electric_motor | one document gives N values: ['"AC NV"', '"Drives front wheels, regenerative braking"', '"Drives rear wheels,  | 2 | lexus/rx MY2021 (press-lexus-rx-2021-3530be72); lexus/rx MY2022 (press-lexus-rx-2022-234e8336) |
| cargo_l | one document gives N values: ['N', 'N', 'N'] | 2 | lexus/rx MY2021 (press-lexus-rx-2021-eed478db); lexus/rx MY2022 (press-lexus-rx-2022-47071e83) |
| tires | not found unambiguously in the available US press specification pages | 2 | lexus/rx US2023+; lexus/gx US2024+ |
| steering | not found unambiguously in the available US press specification pages | 2 | lexus/rx US2023+; lexus/gx US2024+ |
| bore_stroke_in | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| cargo_max_l | one document gives N values: ['N', 'N'] | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| compression_ratio | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| ground_clearance | one document gives N values: ['N', 'N'] | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| injection | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| power_hp | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| power_rpm | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| rear_suspension | one document gives N values: ['"Trailing arm double wishbone type, coil springs"', '"Trailing arm type double  | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| torque_lb_ft | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| torque_rpm | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| towing_kg | one document gives N values: ['N', 'N'] | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| track_front_mm | one document gives N values: ['N', 'N'] | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| track_rear_mm | one document gives N values: ['N', 'N'] | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| transmission_description | one document gives N values: ['"N-speed Multi-Mode Automatic Transmission, Electronically Controlled Transmiss | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| valvetrain | engine not stated; EPA lists several engines | 2 | lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1); lexus/nx MY2020 (press-lexus-nx-2020-7a52690f) |
| fuel_tank_l | no US owner's manual for these years | 1 | lexus/es US2026+ |
| power_hp | no US press specification page for these years | 1 | lexus/es US2026+ |
| torque_lb_ft | no US press specification page for these years | 1 | lexus/es US2026+ |
| tires | no US press specification page for these years | 1 | lexus/es US2026+ |
| front_suspension | no US press specification page for these years | 1 | lexus/es US2026+ |
| rear_suspension | no US press specification page for these years | 1 | lexus/es US2026+ |
| front_brakes | no US press specification page for these years | 1 | lexus/es US2026+ |
| steering | no US press specification page for these years | 1 | lexus/es US2026+ |
| ground_clearance | no US press specification page for these years | 1 | lexus/es US2026+ |
| cargo_l | no US press specification page for these years | 1 | lexus/es US2026+ |
| electric_motor | one document gives N values: ['"N hp (N kW)"', '"AC NV"', '"Drives front wheels, regenerative braking Type Per | 1 | lexus/rx MY2019 (press-lexus-rx-2019-fddbf21b) |
| front_brakes | not found unambiguously in the available US press specification pages | 1 | lexus/nx US2022+ |
| cargo_l | not found unambiguously in the available US press specification pages | 1 | lexus/gx II (2010 redesign) |

## 4. Конфликты источников

Конфликтов: 55. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 55

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| ES | lexus/es US2019-2025 MY2021 | track_front_mm | [1598.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2022 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2023 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2019 | track_front_mm | [1598.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2020 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2021 | track_front_mm | [1598.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2022 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2023 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2019 | track_front_mm | [1598.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2020 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2021 | track_front_mm | [1598.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2022 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| ES | lexus/es US2019-2025 MY2023 | track_front_mm | [1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx III MY2014 | height_mm | [1684.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx III MY2015 | height_mm | [1684.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx III MY2014 | height_mm | [1684.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx III MY2015 | height_mm | [1684.0] | [1720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx US2023+ MY2023 | curb_weight_kg | [1845.0] | [1945] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx US2023+ MY2024 | curb_weight_kg | [1845.0] | [1945] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx US2023+ MY2023 | curb_weight_kg | [1845.0] | [2010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx US2023+ MY2024 | curb_weight_kg | [1845.0] | [2010] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx US2023+ MY2024 | curb_weight_kg | [1845.0] | [2155] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RX | lexus/rx US2023+ MY2023 | curb_weight_kg | [1845.0] | [2155] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx I-US-2015 MY2018 | curb_weight_kg | [1896.0] | [1755] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx I-US-2015 MY2018 | curb_weight_kg | [1896.0] | [1835] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_front_mm | [1605.0] | [1670] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2022 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2023 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| NX | lexus/nx US2022+ MY2024 | track_rear_mm | [1626.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| GX | lexus/gx US2024+ MY2024 | height_mm | [1915.0, 1920.0, 1935.0] | [1880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| GX | lexus/gx US2024+ MY2024 | length_mm | [5005.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| GX | lexus/gx US2024+ MY2024 | track_front_mm | [1667.0, 1687.0] | [1580] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| GX | lexus/gx US2024+ MY2024 | track_rear_mm | [1668.0, 1688.0] | [1580] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| GX | lexus/gx US2024+ MY2024 | wheelbase_mm | [2850.0] | [2790] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| GX | lexus/gx US2024+ MY2024 | width_mm | [1980.0, 2000.0] | [1880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 194 записей (10% каждой линейки), расхождений 0.
- es: 52 проверено, 0 расхождений
- gx: 19 проверено, 0 расхождений
- nx: 39 проверено, 0 расхождений
- rx: 84 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- ES US2019-2025 (2019–2025): consumerreports.org: "The seventh generation Lexus ES retains its comfortable, quiet demeanor" (https://www.consumerreports.org/cars/lexus/es/); cars.com: "The redesigned 2019 ES kicked off the model's seventh generation on an all-new platform." (https://www.cars.com/research/lexus-es_350/) [media: 
- ES US2026+ (2026–2026): consumerreports.org: "2026 Model Redesign Year" (https://www.consumerreports.org/cars/lexus/es/); cars.com: "The all-new 2026 ES will be available either as a hybrid or a pure electric vehicle." (https://www.cars.com/articles/all-new-2026-lexus-es-offers-stepped-electrification-with-phev-and-ev-powe
- RX AL20 (2016–2022): consumerreports.org: "The RX got a 2016 makeover, with avant-garde exterior styling and advanced safety features." (https://www.consumerreports.org/cars/lexus/rx/); cars.com: "One of the best-selling luxury vehicles on the market is redesigned for 2016." (https://www.cars.com/articles/2016-lexus-rx-
- RX US2023+ (2023–2026): consumerreports.org: "The redesigned 2023 RX is powered by a 2.4-liter turbocharged four-cylinder engine" (https://www.consumerreports.org/cars/lexus/rx/); cars.com: "Redesigned for 2023" (https://www.cars.com/research/lexus-rx_350/) [quote read once] [media: generation starts MY2023]
- NX US2022+ (2022–2026): consumerreports.org: "The redesigned 2022 Lexus NX looks much like the outgoing model, but beneath that familiar design is a raft of improvements." (https://www.consumerreports.org/cars/lexus/nx/); cars.com: "The NX was redesigned for the 2022 model year, and its model lineup was revamped (and expan
- GX US2024+ (2024–2026): consumerreports.org: "The redesigned Lexus GX promises more luxury and power than the long-running model it replaces." (https://www.consumerreports.org/cars/lexus/gx/); cars.com: "Redesigned for 2024 with more overt off-road attitude" (https://www.cars.com/research/lexus-gx_550/) [quote read once] [

## Изменения ранее записанных строк (последняя загрузка)

- ES: проблема es-VI-tsb-infotainment обновлена {"probability": ["OCCASIONAL", "COMMON"], "evidence_ids": [8, 9], "note": [null, "CarComplaints.com \"Infotainment Software Bugs\" (owner reports): MY2016: #2, 
- RX: проблема rx-AL20-recall-20V012000 обновлена {"evidence_ids": [5, 6], "note": [null, "CarComplaints.com \"Stalling\" (owner reports): MY2019: #1, average cost to fix N/A, average mileage 7,000 mi"]}
- RX: проблема rx-AL20-recall-20V682000 обновлена {"evidence_ids": [5, 6], "note": [null, "CarComplaints.com \"Stalling\" (owner reports): MY2019: #1, average cost to fix N/A, average mileage 7,000 mi"]}

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- lexus/es: --prune-stale, код 0, {"raw_documents_seen": 108, "source_records_new": 26, "te_existing": 625, "te_new_GENERATION": 336, "te_new_ENGINE": 84, "configurations": 33, "configurations_research_only": 27, "configurations_linked": 6, "issues_existing": 27, "issues_updated": 1, "issues_new": 1}
- lexus/rx: --prune-stale, код 0, {"raw_documents_seen": 124, "source_records_new": 32, "te_existing": 860, "te_new_GENERATION": 537, "te_new_ENGINE": 140, "configurations": 49, "configurations_linked": 7, "configurations_research_only": 42, "issues_existing": 30, "issues_updated": 2}
- lexus/nx: --prune-stale, код 0, {"raw_documents_seen": 104, "source_records_new": 24, "te_existing": 766, "te_new_GENERATION": 182, "te_new_ENGINE": 84, "configurations": 46, "configurations_linked": 11, "configurations_research_only": 35, "issues_existing": 20}
- lexus/gx: --prune-stale, код 0, {"raw_documents_seen": 57, "source_records_new": 11, "te_existing": 245, "te_new_GENERATION": 121, "te_new_ENGINE": 29, "configurations": 13, "configurations_research_only": 13, "issues_existing": 17}
