# Hyundai — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sonata | YF | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Sonata | LF | 2015–2019 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Sonata | DN8 | 2020–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Elantra | MD/UD | 2014–2016 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Elantra | AD | 2017–2020 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Elantra | CN7 | 2021–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ◐ | ● | ◐ | ● | ● | ● |
| Tucson | US2014-2015 | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Tucson | TL | 2016–2021 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Tucson | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ● | ● | ● |
| Santa Fe | NC | 2014–2018 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ● | ● |
| Santa Fe | US2019-2023 | 2019–2023 | ◐ | ◐ | ● | ● | ● | ● | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Santa Fe | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| Santa Fe Sport | AN | 2014–2018 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Accent | RB | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Accent | US2018-2022 | 2018–2022 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Kona | OS | 2018–2023 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ● | ● |
| Kona | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ● | ○ | ◐ | ◐ | ◐ | ● | ● | ● |

Итого ячеек: заполнено 132, частично 81, нет 42, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 7194 |
| known_issues | 0 | 381 |
| maintenance_schedule_items | 0 | 407 |

## 3. Журнал пробелов

Записей в журнале пробелов: 1092 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 304 | hyundai-sonata-us-2014-2.0l-4cyl-turbo-ice-a-6-spd-fwd; hyundai-sonata-us-2014-2.4l-4cyl-hev-a-am6-fwd; hyundai-sonata-us-2014-2.4l-4cyl-ice-a-6-spd-fwd |
| engine_oil_specification | engine not stated; EPA lists several engines | 57 | hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2021 (official-1d7deff217ee); hyundai/sonata MY2025 (official-1ef294fc7c15) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 52 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2025 (official-1ef294fc7c15) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 47 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2025 (official-1ef294fc7c15) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 41 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2021 (official-1d7deff217ee) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 38 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2021 (official-1d7deff217ee) |
| maintenance transmission_fluid | interval text not understood: No check, No service required | 33 | hyundai/sonata official-68438b59abf9 p.514; hyundai/sonata official-68438b59abf9 p.519; hyundai/sonata official-4d3a1b125043 p.506 |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N, N] xN,N miles | 22 | hyundai/sonata official-68438b59abf9 p.508; hyundai/sonata official-68438b59abf9 p.513; hyundai/sonata official-68438b59abf9 p.518 |
| compression_ratio | engine not stated; EPA lists several engines | 19 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| engine_description | engine not stated; EPA lists several engines | 14 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N, N, N, N, N] xN,N miles | 13 | hyundai/sonata official-05793f63ce44 p.457; hyundai/santa-fe official-c34991e79f3d p.451; hyundai/santa-fe official-c34991e79f3d p.456 |
| fuel_tank_l | value N outside the validator range; not used | 12 | hyundai/sonata official-1ef294fc7c15 p.104; hyundai/sonata official-46f8dcfb5ec4 p.128; hyundai/sonata official-5196d2ee9d3a p.104 |
| bore_stroke_mm | engine not stated; EPA lists several engines | 11 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 11 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| power_hp | engine not stated; EPA lists several engines | 11 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| power_rpm | engine not stated; EPA lists several engines | 11 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| torque_lb_ft | engine not stated; EPA lists several engines | 11 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| torque_rpm | engine not stated; EPA lists several engines | 11 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| coolant_capacity_l | value N outside the validator range; not used | 10 | hyundai/sonata official-1ef294fc7c15 p.33; hyundai/sonata official-1ef294fc7c15 p.33; hyundai/sonata official-46f8dcfb5ec4 p.56 |
| maintenance transfer_case_fluid | interval text not understood: No check, No service required | 10 | hyundai/tucson official-98ff8677bbe7 p.488; hyundai/tucson official-48cecf9698b2 p.490; hyundai/tucson official-b29d49aeeb56 p.472 |
| track_front_mm | one document gives N values: ['N', 'N'] | 9 | hyundai/sonata MY2023 (press-hyundainews-sonata-2023-eec7fe62); hyundai/tucson MY2018 (press-hyundainews-tucson-2018-032c5328); hyundai/tucson MY2019 (press-hyundainews-tucson-2019-0b4655b6) |
| track_rear_mm | one document gives N values: ['N', 'N'] | 9 | hyundai/sonata MY2023 (press-hyundainews-sonata-2023-eec7fe62); hyundai/tucson MY2018 (press-hyundainews-tucson-2018-032c5328); hyundai/tucson MY2019 (press-hyundainews-tucson-2019-0b4655b6) |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 9 | hyundai/sonata DN8; hyundai/elantra CN7; hyundai/tucson TL |
| coolant | not found unambiguously in the available US owner's manuals | 9 | hyundai/sonata DN8; hyundai/elantra CN7; hyundai/tucson TL |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 9 | hyundai/elantra MY2022 (press-hyundainews-elantra-2022-0be89770); hyundai/elantra MY2023 (press-hyundainews-elantra-2023-9b130658); hyundai/elantra MY2025 (press-hyundainews-elantra-2025-827ecd7f) |
| rear_brakes | one document gives N values: ['"N\\uNd"', '"Solid disc"'] | 8 | hyundai/sonata MY2019 (press-hyundainews-sonata-2019-7514ab5e); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-2cad8e16); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-37c95b5c) |
| engine_oil_capacity_l | no US owner's manual for these years | 8 | hyundai/sonata YF; hyundai/sonata LF; hyundai/elantra MD/UD |
| engine_oil_viscosity | no US owner's manual for these years | 8 | hyundai/sonata YF; hyundai/sonata LF; hyundai/elantra MD/UD |
| coolant | no US owner's manual for these years | 8 | hyundai/sonata YF; hyundai/sonata LF; hyundai/elantra MD/UD |
| transmission_fluid | no US owner's manual for these years | 8 | hyundai/sonata YF; hyundai/sonata LF; hyundai/elantra MD/UD |
| brake_fluid | no US owner's manual for these years | 8 | hyundai/sonata YF; hyundai/sonata LF; hyundai/elantra MD/UD |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N, N, N] xN,N miles | 8 | hyundai/sonata official-5f5310b5ac33 p.483; hyundai/sonata official-134672ecd168 p.481; hyundai/sonata official-48d85e5c31f1 p.467 |
| front_brakes | one document gives N values: ['"N\\uNd"', '"Ventilated disc"'] | 7 | hyundai/sonata MY2020 (press-hyundainews-sonata-2020-2cad8e16); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-37c95b5c); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-80be13df) |
| steering | one document gives N values: ['"Column-mounted"', '"Rack-and-Pinion"'] | 7 | hyundai/sonata MY2020 (press-hyundainews-sonata-2020-2cad8e16); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-37c95b5c); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-80be13df) |
| maintenance engine_oil_and_filter | interval text not understood: Replace N,N miles (N,N km) or N months | 7 | hyundai/elantra official-19e9040c6d24 p.425; hyundai/elantra official-1436a2844f22 p.427; hyundai/elantra official-1907558b86fc p.420 |
| front_brakes | one document gives N values: ['"N x N"', '"Ventilated Disc"'] | 7 | hyundai/santa-fe MY2020 (press-hyundainews-santa-fe-2020-69eaeb06); hyundai/kona MY2020 (press-hyundainews-kona-2020-0f38ceb7); hyundai/kona MY2021 (press-hyundainews-kona-2021-43b3983d) |
| injection | engine not stated; EPA lists several engines | 7 | hyundai/santa-fe MY2020 (press-hyundainews-santa-fe-2020-69eaeb06); hyundai/santa-fe MY2021 (press-hyundainews-santa-fe-2021-7e0b0088); hyundai/santa-fe MY2022 (press-hyundainews-santa-fe-2022-3cd3dcee) |
| rear_brakes | one document gives N values: ['"N x N"', '"Solid Disc"'] | 7 | hyundai/santa-fe MY2020 (press-hyundainews-santa-fe-2020-69eaeb06); hyundai/kona MY2020 (press-hyundainews-kona-2020-0f38ceb7); hyundai/kona MY2021 (press-hyundainews-kona-2021-43b3983d) |
| electric_motor | one document gives N values: ['"N lb-ft"', '"N kW (N HP)"', '"Interior-permanent magnet synchronous motor"'] | 6 | hyundai/elantra MY2021 (press-hyundainews-elantra-2021-09352ce6); hyundai/elantra MY2022 (press-hyundainews-elantra-2022-0be89770); hyundai/elantra MY2023 (press-hyundainews-elantra-2023-9b130658) |
| cargo_l | not found unambiguously in the available US press specification pages | 6 | hyundai/tucson US2022+; hyundai/santa-fe NC; hyundai/santa-fe US2024+ |
| maintenance differential_fluid | quote not found in the page text; not used | 6 | hyundai/tucson official-98ff8677bbe7 p.488; hyundai/tucson official-98ff8677bbe7 p.488; hyundai/tucson official-b29d49aeeb56 p.472 |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 6 | hyundai/kona MY2023 (mcum-kona-suv-2023-2026); hyundai/kona MY2024 (mcum-kona-suv-2023-2026); hyundai/kona MY2025 (mcum-kona-suv-2023-2026) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N-N,N rpm"', '"N kW (N HP) @ N,N\\uN,N rpm"', '"Permanent magnet s | 5 | hyundai/sonata MY2020 (press-hyundainews-sonata-2020-2cad8e16); hyundai/sonata MY2020 (press-hyundainews-sonata-2020-80be13df); hyundai/sonata MY2021 (press-hyundainews-sonata-2021-1e69088c) |
| steering | one document gives N values: ['"Column-mounted Motor Driven Power Steering (C-MDPS)"', '"Rack and pinion type  | 5 | hyundai/elantra MY2022 (press-hyundainews-elantra-2022-0be89770); hyundai/elantra MY2023 (press-hyundainews-elantra-2023-9b130658); hyundai/elantra MY2024 (press-hyundainews-elantra-2024-92affea3) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 5 | hyundai/elantra CN7; hyundai/tucson TL; hyundai/tucson US2022+ |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N] xN,N miles | 5 | hyundai/elantra official-19e9040c6d24 p.425; hyundai/elantra official-1436a2844f22 p.427; hyundai/elantra official-1907558b86fc p.420 |
| maintenance accessory_drive_belt | interval text not understood: At first, Inspect at N,N mile (N,N km) or N months After that, Inspect every N,N | 5 | hyundai/elantra official-19e9040c6d24 p.425; hyundai/elantra official-1436a2844f22 p.427; hyundai/elantra official-1907558b86fc p.420 |
| maintenance transmission_fluid | interval text not understood: No Check, No Service required | 5 | hyundai/elantra official-19e9040c6d24 p.426; hyundai/elantra official-1436a2844f22 p.428; hyundai/elantra official-1907558b86fc p.421 |
| cargo_l | one document gives N values: ['N', 'N'] | 5 | hyundai/santa-fe MY2018 (press-hyundainews-santa-fe-2018-2a32ff91); hyundai/santa-fe MY2019 (press-hyundainews-santa-fe-2019-b6c87b62); hyundai/santa-fe MY2024 (press-hyundainews-santa-fe-2024-1326b88b) |
| front_brakes | one document gives N values: ['"N\\uNd (N\\uNd)"', '"Ventilated Disc"'] | 5 | hyundai/santa-fe MY2021 (press-hyundainews-santa-fe-2021-7e0b0088); hyundai/santa-fe MY2022 (press-hyundainews-santa-fe-2022-3cd3dcee); hyundai/santa-fe MY2023 (press-hyundainews-santa-fe-2023-52582e7a) |
| fuel_tank_l | no US owner's manual for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| power_hp | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| torque_lb_ft | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| tires | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| front_suspension | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| rear_suspension | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| front_brakes | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| steering | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| ground_clearance | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| cargo_l | no US press specification page for these years | 4 | hyundai/sonata YF; hyundai/elantra MD/UD; hyundai/tucson US2014-2015 |
| rear_brakes | one document gives N values: ['"N\\uNd"', '"Solid Disc"'] | 4 | hyundai/santa-fe MY2021 (press-hyundainews-santa-fe-2021-7e0b0088); hyundai/santa-fe MY2022 (press-hyundainews-santa-fe-2022-3cd3dcee); hyundai/santa-fe MY2023 (press-hyundainews-santa-fe-2023-52582e7a) |
| electric_motor | one document gives N values: ['"N kW (NHP) @ N,N rpm"', '"N lb-ft."', '"Permanent-Magnet Synchronous Motor (PM | 4 | hyundai/kona MY2020 (press-hyundainews-kona-2020-0f38ceb7); hyundai/kona MY2021 (press-hyundainews-kona-2021-43b3983d); hyundai/kona MY2022 (press-hyundainews-kona-2022-6331aa5b) |
| steering | one document gives N values: ['"Motor Driven Power Steering (MDPS) - Power assisted, column-mounted"', '"Rack  | 4 | hyundai/kona MY2020 (press-hyundainews-kona-2020-0f38ceb7); hyundai/kona MY2021 (press-hyundainews-kona-2021-43b3983d); hyundai/kona MY2022 (press-hyundainews-kona-2022-6331aa5b) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N-N,N rpm"', '"N kW (N HP) @ N,N \\uN N,N rpm"', '"Permanent magne | 3 | hyundai/sonata MY2023 (press-hyundainews-sonata-2023-eec7fe62); hyundai/sonata MY2025 (press-hyundainews-sonata-2025-d44a4ab6); hyundai/sonata MY2026 (press-hyundainews-sonata-2026-1411d1a4) |
| track_front_mm | one document gives N values: ['N', 'N', 'N'] | 3 | hyundai/sonata MY2024 (press-hyundainews-sonata-2024-ff741624); hyundai/sonata MY2025 (press-hyundainews-sonata-2025-d44a4ab6); hyundai/sonata MY2026 (press-hyundainews-sonata-2026-1411d1a4) |
| track_rear_mm | one document gives N values: ['N', 'N', 'N'] | 3 | hyundai/sonata MY2024 (press-hyundainews-sonata-2024-ff741624); hyundai/sonata MY2025 (press-hyundainews-sonata-2025-d44a4ab6); hyundai/sonata MY2026 (press-hyundainews-sonata-2026-1411d1a4) |
| maintenance dct_fluid | interval text not understood: No check, no service requied | 3 | hyundai/elantra official-6c25b18ce96a p.468; hyundai/elantra official-094ea46bd28b p.468; hyundai/elantra official-fada0b7e92ea p.481 |
| maintenance exhaust_system | irregular I marks at [N, N, N, N, N, N, N, N] xN,N miles | 3 | hyundai/elantra official-6c25b18ce96a p.469; hyundai/elantra official-094ea46bd28b p.469; hyundai/elantra official-fada0b7e92ea p.482 |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N] xN,N miles | 3 | hyundai/elantra official-4ec688485579 p.477; hyundai/elantra official-f6d5734746c3 p.477; hyundai/elantra official-03489bd80c5e p.477 |
| maintenance cooling_system | interval text not understood: Inspect “Coolant level adjustment and leak” every day | 3 | hyundai/elantra official-4ec688485579 p.479; hyundai/elantra official-f6d5734746c3 p.479; hyundai/elantra official-03489bd80c5e p.479 |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N,Nrpm"', '"N kW (N hp) @ N,N-N,N rpm"'] | 3 | hyundai/tucson MY2024 (press-hyundainews-tucson-2024-f0e86ba3); hyundai/tucson MY2025 (press-hyundainews-tucson-2025-c3c2f1c3); hyundai/tucson MY2026 (press-hyundainews-tucson-2026-d444524b) |
| electric_motor | one document gives N values: ['"N lb. ft."', '"N kW (est. N HP) N-N rpm"', '"Permanent magnet synchronous moto | 3 | hyundai/santa-fe MY2024 (press-hyundainews-santa-fe-2024-1326b88b); hyundai/santa-fe MY2025 (press-hyundainews-santa-fe-2025-e70595ed); hyundai/santa-fe MY2026 (press-hyundainews-santa-fe-2026-b1e68ce1) |
| brake_fluid | one document gives N values: ['"DOT N or DOT N"', '"DOT N"'] | 3 | hyundai/kona MY2021 (official-191f61e02257); hyundai/kona MY2019 (official-5796b4131a33); hyundai/kona MY2020 (official-a804c9b38cc6) |
| rear_brakes | one document gives N values: ['"N\\uNd"', '"Ventilated"'] | 3 | hyundai/kona MY2022 (press-hyundainews-kona-2022-0b159db6); hyundai/kona MY2022 (press-hyundainews-kona-2022-4f40582a); hyundai/kona MY2023 (press-hyundainews-kona-2023-66d6a036) |
| rear_brakes | one document gives N values: ['"N\\uNd"', '"Solid"'] | 3 | hyundai/kona MY2024 (press-hyundainews-kona-2024-894fc7c7); hyundai/kona MY2025 (press-hyundainews-kona-2025-efa3e0e1); hyundai/kona MY2026 (press-hyundainews-kona-2026-9e855460) |
| turning_circle_m | value N outside the validator range; not used | 2 | hyundai/sonata press-hyundainews-sonata-2021-1e69088c p.4; hyundai/sonata press-hyundainews-sonata-2022-28a25bc2 p.4 |
| steering | one document gives N values: ['"Motor Driven Power Steering (MDPS) - Power assisted"', '"Rack and pinion type  | 2 | hyundai/elantra MY2020 (press-hyundainews-elantra-2020-a56afa8f); hyundai/elantra MY2021 (press-hyundainews-elantra-2021-09352ce6) |
| maintenance fuel_filter | interval text not understood: The fuel filter is considered to be maintenance free but periodic inspection is  | 2 | hyundai/elantra official-4b1b5d326596 p.491; hyundai/elantra official-eb4a1903331a p.491 |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N,Nrpm"', '"NkW (NHP) @ N,N-N,N rpm"'] | 2 | hyundai/tucson MY2022 (press-hyundainews-tucson-2022-f193794f); hyundai/tucson MY2023 (press-hyundainews-tucson-2023-3086dc50) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N,N rpm"', '"N kW (N hp) @ N,N \\uN N,N rpm"'] | 2 | hyundai/tucson MY2025 (press-hyundainews-tucson-2025-c3c2f1c3); hyundai/tucson MY2026 (press-hyundainews-tucson-2026-d444524b) |
| tires | not found unambiguously in the available US press specification pages | 2 | hyundai/tucson US2022+; hyundai/santa-fe US2024+ |
| front_brakes | not found unambiguously in the available US press specification pages | 2 | hyundai/tucson US2022+; hyundai/santa-fe US2024+ |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 2 | hyundai/santa-fe MY2018 (official-8d55d8b56d6d); hyundai/santa-fe MY2019 (official-c34991e79f3d) |
| electric_motor | one document gives N values: ['"N lb. ft."', '"N kW (est. N HP) N-Nrpm"'] | 2 | hyundai/santa-fe MY2022 (press-hyundainews-santa-fe-2022-3cd3dcee); hyundai/santa-fe MY2023 (press-hyundainews-santa-fe-2023-52582e7a) |
| electric_motor | one document gives N values: ['"N lb. ft."', '"NkW (est. N HP) N-Nprm"'] | 2 | hyundai/santa-fe MY2022 (press-hyundainews-santa-fe-2022-3cd3dcee); hyundai/santa-fe MY2023 (press-hyundainews-santa-fe-2023-52582e7a) |
| rear_brakes | one document gives N values: ['"N\\uNd"', '"N\\uNd"', '"Solid Disc"'] | 2 | hyundai/santa-fe MY2024 (press-hyundainews-santa-fe-2024-1326b88b); hyundai/santa-fe MY2025 (press-hyundainews-santa-fe-2025-e70595ed) |
| front_brakes | one document gives N values: ['"N\\uNd"', '"Ventilated Disc"'] | 2 | hyundai/santa-fe MY2026 (press-hyundainews-santa-fe-2026-b1e68ce1); hyundai/accent MY2020 (press-hyundainews-accent-2020-949142b8) |
| ground_clearance | not found unambiguously in the available US press specification pages | 2 | hyundai/santa-fe NC; hyundai/santa-fe-sport AN |
| front_brakes | one document gives N values: ['"N"', '"Ventilated Disc"'] | 2 | hyundai/accent MY2021 (press-hyundainews-accent-2021-ced9fab2); hyundai/accent MY2022 (press-hyundainews-accent-2022-7cc70400) |
| steering | one document gives N values: ['"Motor Driven Power Steering (MDPS)"', '"Rack-and-Pinion"'] | 2 | hyundai/accent MY2021 (press-hyundainews-accent-2021-ced9fab2); hyundai/accent MY2022 (press-hyundainews-accent-2022-7cc70400) |
| electric_motor | one document gives N values: ['"N kW"', '"N kW (NHP)"'] | 2 | hyundai/kona MY2024 (press-hyundainews-kona-2024-37017f11); hyundai/kona MY2025 (press-hyundainews-kona-2025-fb7fa03e) |
| electric_motor | one document gives N values: ['"N lb-ft."', '"Permanent-Magnet Synchronous Motor (PMSM)"'] | 2 | hyundai/kona MY2024 (press-hyundainews-kona-2024-37017f11); hyundai/kona MY2025 (press-hyundainews-kona-2025-fb7fa03e) |
| steering | one document gives N values: ['"Motor Driven Power Steering (C-MDPS) - Power assisted, column-mounted"', '"Rac | 2 | hyundai/kona MY2024 (press-hyundainews-kona-2024-37017f11); hyundai/kona MY2025 (press-hyundainews-kona-2025-fb7fa03e) |
| power_hp | value N outside the validator range; not used | 1 | hyundai/sonata press-hyundainews-sonata-2017-7eec1965 p.1 |
| track_front_mm | one document gives N values: ['N', 'N', 'N', 'N'] | 1 | hyundai/sonata MY2022 (press-hyundainews-sonata-2022-543cd1cf) |
| track_rear_mm | one document gives N values: ['N', 'N', 'N', 'N'] | 1 | hyundai/sonata MY2022 (press-hyundainews-sonata-2022-543cd1cf) |
| maintenance engine_oil_and_filter | irregular R marks at [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N] xN,N miles | 1 | hyundai/sonata official-05793f63ce44 p.457 |
| maintenance battery | irregular I marks at [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N] xN,N miles | 1 | hyundai/sonata official-05793f63ce44 p.458 |
| maintenance front_suspension | irregular I marks at [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N] xN,N miles | 1 | hyundai/sonata official-05793f63ce44 p.458 |
| transmission_description | one document gives N values: ['"N-SPEED ELECTRONIC AUTOMATIC WITH OVERDRIVE LOCK-UP TORQUE CONVERTER, GATE TYP | 1 | hyundai/elantra MY2018 (press-hyundainews-elantra-2018-2ff66e9d) |
| transmission_description | one document gives N values: ['"N-SPEED ELECTRIC AUTOMATIC WITH OVERDRIVE LOCK-UP TORQUE CONVERTER, GATE TYPE, | 1 | hyundai/elantra MY2018 (press-hyundainews-elantra-2018-4b941dc6) |
| transmission_description | one document gives N values: ['"N-SPEED MANUAL, DRY SINGLE PLATE WITH DIAPHRAGM SPRING TYPE"', '"N-SPEED DCT,  | 1 | hyundai/elantra MY2018 (press-hyundainews-elantra-2018-a1d97475) |
| rear_suspension | not found unambiguously in the available US press specification pages | 1 | hyundai/elantra CN7 |
| steering | not found unambiguously in the available US press specification pages | 1 | hyundai/elantra CN7 |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N'] | 1 | hyundai/tucson MY2026 (official-9968375ae98a) |
| transmission_description | one document gives N values: ['"N-SPEED AUTOMATIC WITH OD LOCK-UP TORQUE CONVERTER, GATE TYPE, ELECTRONIC SHIF | 1 | hyundai/tucson MY2017 (press-hyundainews-tucson-2017-83e102cf) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N-N,N rpm"', '"N kW (N HP) @ N,N\\uN,N rpm"'] | 1 | hyundai/tucson MY2022 (press-hyundainews-tucson-2022-f193794f) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N-N,N rpm"', '"N kW (N HP) @ N,N \\uN N,N rpm"'] | 1 | hyundai/tucson MY2023 (press-hyundainews-tucson-2023-3086dc50) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N-N,N rpm"', '"N kW (N hp) @ N,N\\uN,N rpm"'] | 1 | hyundai/tucson MY2024 (press-hyundainews-tucson-2024-f0e86ba3) |
| electric_motor | one document gives N values: ['"N lb.-ft. @ N-N,N rpm"', '"N kW (est. N HP) @ N,N\\uN,N rpm"', '"Permanent mag | 1 | hyundai/santa-fe MY2021 (press-hyundainews-santa-fe-2021-7e0b0088) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 1 | hyundai/santa-fe US2024+ |
| front_brakes | one document gives N values: ['"N\\uNd x N\\uNd"', '"Ventilated Disc"'] | 1 | hyundai/accent MY2019 (press-hyundainews-accent-2019-0eea4335) |
| front_brakes | one document gives N values: ['"N mm (FWD)"', '"Nmm (AWD)"'] | 1 | hyundai/kona MY2019 (press-hyundainews-kona-2019-22ed18b5) |
| rear_brakes | one document gives N values: ['"Nmm (FWD)"', '"Nmm (AWD)"'] | 1 | hyundai/kona MY2019 (press-hyundainews-kona-2019-22ed18b5) |
| electric_motor | one document gives N values: ['"N kW (NHP)"', '"N. lb-ft."', '"Permanent Magnet Synchronous Motor (PMSM)"'] | 1 | hyundai/kona MY2019 (press-hyundainews-kona-2019-aed6cfa8) |
| electric_motor | one document gives N values: ['"N kW (NHP)"', '"N kW"'] | 1 | hyundai/kona MY2024 (press-hyundainews-kona-2024-37017f11) |

## 4. Конфликты источников

Конфликтов: 78. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 74
- official document kept over the copy: 4

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Sonata | hyundai/sonata DN8 MY2024 | curb_weight_kg | [1560.0, 1603.0, 1672.0] | [1499] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sonata | hyundai/sonata LF MY2017 | curb_weight_kg | [1586.0, 1615.0, 1718.0, 1728.0] | [1475] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sonata | hyundai/sonata LF MY2018 | curb_weight_kg | [1586.0, 1615.0] | [1475] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sonata | hyundai/sonata LF MY2018 | curb_weight_kg | [1586.0, 1615.0] | [1727] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Sonata | hyundai/sonata LF MY2019 | curb_weight_kg | [1473.0, 1498.0, 1522.0, 1526.0, 1586.0, 1600.0, 1615.0] | [1730] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra AD MY2018 | height_mm | [1435.0, 1466.0] | [1400] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra AD MY2018 | width_mm | [1796.0, 1801.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra AD MY2018 | width_mm | [1796.0, 1801.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra AD MY2019 | curb_weight_kg | [1296.0] | [1335] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra AD MY2019 | width_mm | [1796.0, 1801.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra AD MY2020 | width_mm | [1796.0, 1801.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra CN7 MY2021 | curb_weight_kg | [1345.0, 1392.0] | [1236] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra CN7 MY2022 | curb_weight_kg | [1345.0, 1392.0] | [1236] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra CN7 MY2023 | curb_weight_kg | [1345.0, 1392.0] | [1236] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra CN7 MY2024 | curb_weight_kg | [1345.0, 1392.0] | [1236] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra CN7 MY2025 | curb_weight_kg | [1345.0, 1392.0] | [1236] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Elantra | hyundai/elantra CN7 MY2026 | curb_weight_kg | [1345.0, 1392.0] | [1236] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tucson | hyundai/tucson US2022+ MY2026 | length_mm | [4641.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tucson | hyundai/tucson US2022+ MY2026 | length_mm | [4641.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tucson | hyundai/tucson US2022+ MY2026 | length_mm | [4641.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Tucson | hyundai/tucson US2022+ MY2026 | length_mm | [4641.0] | [4630] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Santa Fe | hyundai/santa-fe US2019-2023 MY2023 | coolant_description | Phosphate-based Ethylene glycol coolant for aluminum ra | ['Phosphate-based; ethylene glycol coolant to prevent'] | official document kept over the copy |
| Santa Fe | hyundai/santa-fe US2019-2023 MY2019 | height_mm | [1689.0, 1699.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Santa Fe | hyundai/santa-fe US2019-2023 MY2021 | curb_weight_kg | [1907.0] | [1729] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Santa Fe | hyundai/santa-fe US2019-2023 MY2019 | height_mm | [1689.0, 1699.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Santa Fe | hyundai/santa-fe US2019-2023 MY2021 | curb_weight_kg | [1907.0] | [1661] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Santa Fe | hyundai/santa-fe US2019-2023 MY2019 | height_mm | [1689.0, 1699.0] | [1710] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | track_rear_mm | [1511.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | track_rear_mm | [1511.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | height_mm | [1450.0] | [1430] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | length_mm | [4384.0] | [4190] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | length_mm | [4384.0] | [4190] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | length_mm | [4384.0] | [4190] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | track_rear_mm | [1511.0] | [1530] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2018 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2019 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accent | hyundai/accent US2018-2022 MY2020 | width_mm | [1730.0] | [1700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | transmission_fluid | SK ATF SP-IV | ['SP-IV'] | official document kept over the copy |
| Kona | hyundai/kona OS MY2020 | coolant_description | phosphate based coolant to | ['Phosphate-based Ethylene glycol coolant for alu-'] | official document kept over the copy |
| Kona | hyundai/kona OS MY2023 | coolant_description | Ethylene-glycol with phosphate based coolant for aluminum radiator | ['Ethylene glycol'] | official document kept over the copy |
| Kona | hyundai/kona OS MY2020 | curb_weight_kg | [1685.0, 1710.0, 1740.0] | [1399] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | curb_weight_kg | [1685.0, 1710.0, 1740.0] | [1399] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2019 | height_mm | [1554.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | height_mm | [1554.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | height_mm | [1554.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | track_rear_mm | [1575.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | track_rear_mm | [1575.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | curb_weight_kg | [1685.0, 1710.0, 1740.0] | [1311] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | curb_weight_kg | [1685.0, 1710.0, 1740.0] | [1311] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2019 | height_mm | [1554.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | height_mm | [1554.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | height_mm | [1554.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | track_rear_mm | [1575.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | track_rear_mm | [1575.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2022 | curb_weight_kg | [1515.0, 1685.0, 1740.0] | [1390] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2022 | curb_weight_kg | [1515.0, 1685.0, 1740.0] | [1315] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2019 | height_mm | [1554.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | height_mm | [1554.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | height_mm | [1554.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2020 | track_rear_mm | [1575.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona OS MY2021 | track_rear_mm | [1575.0] | [1560] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona US2024+ MY2025 | curb_weight_kg | [1620.0, 1705.0, 1765.0] | [1453] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona US2024+ MY2025 | curb_weight_kg | [1620.0, 1705.0, 1765.0] | [1363] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Kona | hyundai/kona US2024+ MY2024 | length_mm | [4356.0] | [4390] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 322 записей (10% каждой линейки), расхождений 0.
- accent: 21 проверено, 0 расхождений
- elantra: 60 проверено, 0 расхождений
- kona: 52 проверено, 0 расхождений
- santa-fe: 58 проверено, 0 расхождений
- santa-fe-sport: 11 проверено, 0 расхождений
- sonata: 77 проверено, 0 расхождений
- tucson: 43 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Sonata LF (2015–2019): consumerreports.org: "The 2015 Sonata models may be less stylish than the previous generation" (https://www.consumerreports.org/cars/hyundai/sonata/); cars.com: "The Sonata's exterior took on a tamer look with its 2015 redesign" (https://www.cars.com/research/hyundai-sonata/) [media: generation star
- Sonata DN8 (2020–2026): consumerreports.org: "Redesigned for 2020, the Sonata has a sleek, coupe-like silhouette." (https://www.consumerreports.org/cars/hyundai/sonata/); cars.com: "the redesigned 2020 Sonata's exterior design was dramatic" (https://www.cars.com/research/hyundai-sonata/) [media: generation starts MY2020]
- Elantra AD (2017–2020): consumerreports.org: "The redesigned Elantra is relatively roomy, sparing with fuel, and features intuitive controls." (https://www.consumerreports.org/cars/hyundai/elantra/); cars.com: "All-new for 2017" (https://www.cars.com/research/hyundai-elantra/) [media: generation starts MY2017]
- Elantra CN7 (2021–2026): consumerreports.org: "The redesigned for 2021 Elantra got a slightly roomier interior and a more sophisticated infotainment system." (https://www.consumerreports.org/cars/hyundai/elantra/); cars.com: "Redesigned for 2021" (https://www.cars.com/research/hyundai-elantra/) [media: generation starts MY2
- Tucson TL (2016–2021): consumerreports.org: "The redesigned-for-2016 Tucson shares only its name with the previous generation." (https://www.consumerreports.org/cars/hyundai/tucson/); cars.com: "Heavily revised five-seat compact SUV" (https://www.cars.com/research/hyundai-tucson/) [media: generation starts MY2016]
- Tucson US2022+ (2022–2026): consumerreports.org: "The redesigned fourth-generation Tucson compact SUV is much more substantial than the mediocre model it replaces." (https://www.consumerreports.org/cars/hyundai/tucson/); cars.com: "Redesigned for 2022" (https://www.cars.com/research/hyundai-tucson/) [media: generation starts M
- Santa Fe US2019-2023 (2019–2023): consumerreports.org: "The redesigned five-passenger Santa Fe is a compelling choice priced close to some top-trim compact SUVs." (https://www.consumerreports.org/cars/hyundai/santa-fe/); cars.com: "Redesigned for 2019, replacing Santa Fe Sport" (https://www.cars.com/research/hyundai-santa_fe/) [medi
- Santa Fe US2024+ (2024–2026): consumerreports.org: "The midsized Hyundai Santa Fe SUV is redesigned for the 2024 model year, giving it a boxy look and a striking interior." (https://www.consumerreports.org/cars/hyundai/santa-fe/); cars.com: "Redesigned for 2024" (https://www.cars.com/research/hyundai-santa_fe/) [media: generatio
- Santa Fe Sport: media give different first model years [2013, 2014] for one generation; MY2013 used
- Santa Fe Sport: MY2013: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "2013 Model Redesign Year" (https://www.consumerreports.org/cars/hyundai/santa-fe-sport/) [media: weak])
- Accent US2018-2022 (2018–2022): consumerreports.org: "This generation of Accent comes only as a sedan." (https://www.consumerreports.org/cars/hyundai/accent/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/hyundai-accent/) [media: generation starts MY2018]
- Kona US2024+ (2024–2026): consumerreports.org: "The redesigned Kona feels more mature and substantial than the original model." (https://www.consumerreports.org/cars/hyundai/kona/); cars.com: "Redesigned for 2024" (https://www.cars.com/research/hyundai-kona/) [media: generation starts MY2024]

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: ['accent', 'elantra', 'kona', 'santa-fe', 'santa-fe-sport', 'sonata', 'tucson']
- hyundai/sonata: --replace-own, код 0, {"replaced_own_maintenance": 87, "replaced_own_te": 1531, "replaced_own_issues": 84, "raw_documents_seen": 117, "te_new_GENERATION": 824, "te_new_ENGINE": 8, "te_new_CONFIGURATION": 694, "configurations": 54, "configurations_research_only": 39, "configurations_linked": 15, "issues_new": 84, "maintenance_new": 87}
- hyundai/elantra: --replace-own, код 0, {"replaced_own_maintenance": 67, "replaced_own_te": 1499, "replaced_own_issues": 73, "raw_documents_seen": 112, "te_new_GENERATION": 648, "te_new_CONFIGURATION": 852, "configurations": 64, "configurations_research_only": 54, "configurations_linked": 10, "issues_new": 73, "maintenance_new": 67}
- hyundai/tucson: --replace-own, код 0, {"replaced_own_maintenance": 48, "replaced_own_te": 1129, "replaced_own_issues": 62, "raw_documents_seen": 90, "te_new_GENERATION": 502, "te_new_CONFIGURATION": 630, "configurations": 54, "configurations_research_only": 34, "configurations_linked": 20, "issues_new": 62, "maintenance_new": 48}
- hyundai/santa-fe: --replace-own, код 0, {"replaced_own_maintenance": 122, "replaced_own_te": 1195, "replaced_own_issues": 79, "raw_documents_seen": 91, "source_records_new": 1, "te_new_GENERATION": 594, "te_new_CONFIGURATION": 618, "configurations": 50, "configurations_research_only": 50, "issues_new": 79, "maintenance_new": 122}
- hyundai/santa-fe-sport: --replace-own, код 0, {"replaced_own_te": 402, "replaced_own_issues": 26, "raw_documents_seen": 25, "te_new_GENERATION": 158, "te_new_CONFIGURATION": 244, "configurations": 20, "configurations_research_only": 10, "configurations_linked": 10, "issues_new": 26}
- hyundai/accent: --replace-own, код 0, {"replaced_own_te": 425, "replaced_own_issues": 25, "raw_documents_seen": 43, "te_new_GENERATION": 238, "te_new_CONFIGURATION": 187, "configurations": 17, "configurations_research_only": 17, "issues_new": 25}
- hyundai/kona: --replace-own, код 0, {"replaced_own_maintenance": 83, "replaced_own_te": 977, "replaced_own_issues": 32, "raw_documents_seen": 86, "source_records_new": 4, "te_new_GENERATION": 487, "te_new_CONFIGURATION": 510, "configurations": 45, "configurations_research_only": 45, "issues_new": 32, "maintenance_new": 83}
