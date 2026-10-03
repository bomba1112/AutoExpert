# Honda — отчёт по базе технических данных US

Сформировано 2026-10-03T18:00:06+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Accord | IX | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ◐ | ◐ | ● | ● | ● |
| Accord | X | 2018–2022 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ● | ◐ | ◐ | ◐ | ● | ● | ● |
| Accord | US2023+ | 2023–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Civic | IX Sedan | 2014–2015 | ● | ◐ | ● | ● | ○ | ◐ | ○ | ◐ | ● | ◐ | ◐ | ◐ | ● | ● | ● |
| Civic | 10th | 2016–2021 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ● | ◐ | ◐ | ◐ | ● | ● | ● |
| Civic | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ● | ◐ | ● | ◐ | ● | ● | ● |
| CR-V | IV | 2014–2016 | ● | ◐ | ● | ● | ● | ● | ● | ● | ● | ◐ | ● | ◐ | ● | ● | ● |
| CR-V | RW | 2017–2022 | ● | ◐ | ● | ● | ● | ● | ● | ● | ● | ◐ | ● | ◐ | ● | ● | ● |
| CR-V | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ● | ● | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 94, частично 33, нет 8, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 5896 |
| known_issues | 0 | 212 |
| maintenance_schedule_items | 0 | 588 |

## 3. Журнал пробелов

Записей в журнале пробелов: 896 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 184 | honda-accord-us-2014-2.0l-4cyl-hev-a-variable-gear-ratios-fwd; honda-accord-us-2014-2.0l-4cyl-phev-a-variable-gear-ratios-fwd; honda-accord-us-2014-2.4l-4cyl-ice-a-av-s7-fwd |
| injection | engine not stated; EPA lists several engines | 51 | honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa); honda/accord MY2020 (press-hondanews-accord-2020-a5a61a10); honda/accord MY2020 (press-hondanews-accord-2020-c98c463a) |
| valvetrain | engine not stated; EPA lists several engines | 48 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 45 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| engine_description | engine not stated; EPA lists several engines | 45 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| fuel_tank_l | value N outside the validator range; not used | 43 | honda/accord carmans-2018-honda-accord p.698; honda/accord carmans-2018-honda-accord p.700; honda/accord carmans-2019-honda-accord p.702 |
| bore_stroke_mm | engine not stated; EPA lists several engines | 42 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| compression_ratio | engine not stated; EPA lists several engines | 41 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| power_hp | engine not stated; EPA lists several engines | 33 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| power_rpm | engine not stated; EPA lists several engines | 33 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| torque_lb_ft | engine not stated; EPA lists several engines | 33 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| torque_rpm | engine not stated; EPA lists several engines | 33 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 26 | honda/civic MY2023 (press-hondanews-civic-2023-03c22e4e); honda/civic MY2023 (press-hondanews-civic-2023-03c22e4e); honda/civic MY2024 (press-hondanews-civic-2024-2c58a962) |
| coolant_capacity_l | value N outside the validator range; not used | 19 | honda/civic carmans-2024-honda-civic p.749; honda/cr-v carmans-2018-honda-cr-v p.655; honda/cr-v carmans-2018-honda-crv p.655 |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 16 | honda/cr-v MY2014 (carmans-2014-honda-cr-v); honda/cr-v MY2015 (carmans-2015-honda-cr-v); honda/cr-v MY2016 (carmans-2016-honda-cr-v) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 14 | honda/accord MY2018 (carmans-2018-honda-accord); honda/accord MY2019 (carmans-2019-honda-accord); honda/accord MY2020 (carmans-2020-honda-accord) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 14 | honda/accord MY2018 (carmans-2018-honda-accord); honda/accord MY2019 (carmans-2019-honda-accord); honda/accord MY2020 (carmans-2020-honda-accord) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 14 | honda/accord MY2018 (carmans-2018-honda-accord); honda/accord MY2019 (carmans-2019-honda-accord); honda/accord MY2020 (carmans-2020-honda-accord) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 13 | honda/accord MY2018 (carmans-2018-honda-accord); honda/accord MY2019 (carmans-2019-honda-accord); honda/accord MY2020 (carmans-2020-honda-accord) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 13 | honda/accord MY2018 (carmans-2018-honda-accord); honda/accord MY2019 (carmans-2019-honda-accord); honda/accord MY2020 (carmans-2020-honda-accord) |
| electric_motor | one document gives N values: ['"N @ N,N-N,N"', '"N @ N-N,N"'] | 13 | honda/accord MY2023 (press-hondanews-accord-2023-301eb0a8); honda/accord MY2024 (press-hondanews-accord-2024-e16008de); honda/accord MY2025 (press-hondanews-accord-2025-47d13a0f) |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N'] | 13 | honda/cr-v MY2015 (carmans-2015-honda-crv); honda/cr-v MY2018 (carmans-2018-honda-cr-v); honda/cr-v MY2018 (carmans-2018-honda-crv) |
| engine_oil_specification | engine not stated; EPA lists several engines | 12 | honda/accord MY2018 (carmans-2018-honda-accord); honda/accord MY2019 (carmans-2019-honda-accord); honda/accord MY2020 (carmans-2020-honda-accord) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 7 | honda/accord MY2014 (press-hondanews-accord-2014-abb7a88a); honda/civic MY2014 (press-hondanews-civic-2014-397b3427); honda/civic MY2015 (press-hondanews-civic-2015-a6fbfada) |
| engine_oil_capacity_drain_refill_l | one document gives N values: ['N', 'N'] | 7 | honda/cr-v MY2019 (carmans-2019-honda-cr-v); honda/cr-v MY2020 (carmans-2020-honda-cr-v-hybrid); honda/cr-v MY2021 (carmans-2021-honda-cr-v-hybrid) |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N', 'N', 'N'] | 6 | honda/cr-v MY2014 (carmans-2014-honda-cr-v); honda/cr-v MY2015 (carmans-2015-honda-cr-v); honda/cr-v MY2016 (carmans-2016-honda-cr-v) |
| front_brakes | not found unambiguously in the available US press specification pages | 5 | honda/accord IX; honda/accord X; honda/civic IX Sedan |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 5 | honda/accord X; honda/accord US2023+; honda/civic IX Sedan |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 5 | honda/accord X; honda/accord US2023+; honda/civic IX Sedan |
| maintenance:transmission_fluid | REPLACE SEVERE {"edition": "civic sedan"}: the manuals give different values ['[[N, null], null]', '[[N, null] | 5 | honda/civic MY2022; honda/civic MY2023; honda/civic MY2024 |
| engine_oil_capacity_l | one document gives N values: ['N', 'N'] | 5 | honda/cr-v MY2017 (carmans-2017-honda-cr-v); honda/cr-v MY2017 (carmans-2017-honda-crv); honda/cr-v MY2018 (carmans-2018-honda-cr-v) |
| ground_clearance | not found unambiguously in the available US press specification pages | 4 | honda/accord IX; honda/accord X; honda/civic IX Sedan |
| steering | not found unambiguously in the available US press specification pages | 4 | honda/accord X; honda/civic 10th; honda/civic US2022+ |
| track_front_mm | one document gives N values: ['N', 'N'] | 4 | honda/cr-v MY2017 (press-hondanews-cr-v-2017-b3de1e82); honda/cr-v MY2018 (press-hondanews-cr-v-2018-4466fe82); honda/cr-v MY2019 (press-hondanews-cr-v-2019-5d6e0e86) |
| track_rear_mm | one document gives N values: ['N', 'N'] | 4 | honda/cr-v MY2017 (press-hondanews-cr-v-2017-b3de1e82); honda/cr-v MY2018 (press-hondanews-cr-v-2018-4466fe82); honda/cr-v MY2019 (press-hondanews-cr-v-2019-5d6e0e86) |
| electric_motor | one document gives N values: ['"N @ N,N-N,N"', '"N lb.-ft. @ N-N,N"'] | 3 | honda/accord MY2018 (press-hondanews-accord-2018-1b614d66); honda/accord MY2019 (press-hondanews-accord-2019-7d563077); honda/accord MY2020 (press-hondanews-accord-2020-c98c463a) |
| electric_motor | one document gives N values: ['"N @ N - N rpm"', '"N"', '"N lb-ft @ N - N rpm"'] | 3 | honda/cr-v MY2021 (press-hondanews-cr-v-2021-67d914ad); honda/cr-v MY2022 (press-hondanews-cr-v-2022-667ff7bc); honda/cr-v MY2022 (press-hondanews-cr-v-2022-87d6d66a) |
| electric_motor | one document gives N values: ['"N / N @ N-N"', '"N @ N-N"'] | 2 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| electric_motor | one document gives N values: ['"N"', '"N @ N - N rpm"', '"N lb-ft @ N - N"'] | 2 | honda/accord MY2021 (press-hondanews-accord-2021-f9134b8a); honda/accord MY2022 (press-hondanews-accord-2022-75c5510c) |
| octane_aki | one document gives N values: ['N', 'N'] | 2 | honda/civic MY2015 (carmans-2015-honda-civic); honda/civic MY2024 (carmans-2024-honda-civic) |
| electric_motor | one document gives N values: ['"N @ N"', '"N @ N-N"', '"N @ N-N"', '"N @ N-N"'] | 2 | honda/civic MY2014 (press-hondanews-civic-2014-3db9065c); honda/civic MY2015 (press-hondanews-civic-2015-b3a2aeeb) |
| power_hp | one document gives N values: ['N', 'N'] | 2 | honda/civic MY2017 (press-hondanews-civic-2017-82d8834b); honda/civic MY2018 (press-hondanews-civic-2018-df017c1e) |
| transmission_description | one document gives N values: ['"N-Speed Manual Transmission (NMT)"', '"Continuously Variable Transmission (M-C | 2 | honda/civic MY2019 (press-hondanews-civic-2019-5b7b31ed); honda/civic MY2020 (press-hondanews-civic-2020-48958387) |
| engine | EPA row has no value | 2 | honda-cr-v-us-2025-ev-fcev-a-a1-fwd; honda-cr-v-us-2026-ev-fcev-a-a1-fwd |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N', 'N'] | 2 | honda/cr-v MY2019 (carmans-2019-honda-cr-v); honda/cr-v MY2023 (mcum-cr-v-suv-2023) |
| transmission_description | one document gives N values: ['"N-Speed Manual Transmission"', '"Continously Variable Transmission - CVT (avai | 1 | honda/accord MY2014 (press-hondanews-accord-2014-abb7a88a) |
| electric_motor | one document gives N values: ['"N @ N-N rpm"', '"N lb-ft @ N-N rpm"'] | 1 | honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| engine_oil_capacity_l | no US owner's manual for these years | 1 | honda/accord IX |
| engine_oil_viscosity | no US owner's manual for these years | 1 | honda/accord IX |
| coolant | no US owner's manual for these years | 1 | honda/accord IX |
| transmission_fluid | no US owner's manual for these years | 1 | honda/accord IX |
| brake_fluid | no US owner's manual for these years | 1 | honda/accord IX |
| brake_fluid | one document gives N values: ['"DOT N or DOT N"', '"DOT N"', '"DOT N"'] | 1 | honda/civic MY2017 (carmans-2017-honda-civic) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 1 | honda/civic IX Sedan |
| power_hp | not found unambiguously in the available US press specification pages | 1 | honda/civic IX Sedan |
| torque_lb_ft | not found unambiguously in the available US press specification pages | 1 | honda/civic IX Sedan |
| transmission_description | one document gives N values: ['"Continuously Variable Transmission (CVT) (NWD; City/Highway/Combined)"', '"Con | 1 | honda/cr-v MY2016 (press-hondanews-cr-v-2016-06b32229) |
| electric_motor | one document gives N values: ['"N @ N - N rpm"', '"N lb-ft @ N - N rpm"'] | 1 | honda/cr-v MY2020 (press-hondanews-cr-v-2020-6a419618) |
| electric_motor | one document gives N values: ['"N @N,N-N,N"', '"N"'] | 1 | honda/cr-v MY2023 (press-hondanews-cr-v-2023-81f41c33) |
| electric_motor | one document gives N values: ['"N"', '"N"'] | 1 | honda/cr-v MY2026 (press-hondanews-cr-v-2026-fee9e11f) |

## 4. Конфликты источников

Конфликтов: 96. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 89
- sources of the same rank disagree; field not shown: 7

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Accord | honda/accord IX MY2014 | wheelbase_mm | [2776.0] | [2720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord IX MY2014 | wheelbase_mm | [2776.0] | [2720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord IX MY2017 | length_mm | [4813.0, 4890.0, 4930.0] | [4950] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2023 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2024 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2025 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2026 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2023 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2024 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2025 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2026 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2023 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2024 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2025 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2026 | track_front_mm | [1590.0, 1600.0] | [1620] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2023 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2024 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2025 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord US2023+ MY2026 | track_rear_mm | [1613.0, 1621.0] | [1590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | curb_weight_kg | [1420.0, 1431.0, 1451.0, 1455.0, 1459.0, 1494.0, 1496.0, 1516.0, 1525.0, 1532.0, 1542.0, 1555.0] | [1603] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | length_mm | [4882.0] | [4830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | track_rear_mm | [1603.0, 1610.0] | [1580] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | wheelbase_mm | [2830.0] | [2720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1850] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | length_mm | [4882.0] | [4830] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | track_rear_mm | [1603.0, 1610.0] | [1580] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | wheelbase_mm | [2830.0] | [2720] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1850] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2019 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2020 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2019 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2020 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2019 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2020 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2019 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2020 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2019 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2020 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | length_mm | [4902.0] | [4880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2018 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2019 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2020 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2021 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Accord | honda/accord X MY2022 | width_mm | [1862.0] | [1910] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2016 | width_mm | [1798.0] | [1880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2016 | width_mm | [1798.0] | [1880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2016 | width_mm | [1798.0] | [1880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2021 | height_mm | [1415.0, 1430.0, 1435.0] | [1390] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2019 | length_mm | [4503.0, 4506.0, 4519.0, 4557.0, 4641.0, 4643.0] | [4490] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2020 | length_mm | [4503.0, 4519.0, 4557.0, 4641.0, 4643.0] | [4490] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2021 | length_mm | [4519.0, 4557.0, 4641.0] | [4490] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2016 | width_mm | [1798.0] | [1880] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2021 | height_mm | [1415.0, 1430.0, 1435.0] | [1390] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2019 | length_mm | [4503.0, 4506.0, 4519.0, 4557.0, 4641.0, 4643.0] | [4490] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2020 | length_mm | [4503.0, 4519.0, 4557.0, 4641.0, 4643.0] | [4490] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic 10th MY2021 | length_mm | [4519.0, 4557.0, 4641.0] | [4490] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic IX Sedan MY2014 | curb_weight_kg | [1303.0, 1306.0, 1330.0, 1332.0, 1362.0] | [1230] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Civic | honda/civic IX Sedan MY2014 | length_mm | [4519.0, 4542.0, 4557.0] | [4500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2023 | compression_ratio | None | ['13,9', '13.9'] | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v US2023+ MY2023 | turning_circle_m | None | [11.3, 11.4] | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v US2023+ MY2023 | tires | None | ['235 / 55R19 101H; 235 / 60R18 103H', '235 / 55R19 101H; 235 / 60R18 103H; 235  | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v US2023+ MY2023 | length_mm | None | [4674, 4694] | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v US2023+ MY2023 | width_mm | None | [1854, 1867] | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v US2023+ MY2023 | height_mm | None | [1676, 1689] | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v US2023+ MY2023 | wheelbase_mm | None | [2692, 2700] | sources of the same rank disagree; field not shown |
| CR-V | honda/cr-v RW MY2020 | length_mm | [4625.0] | [4590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v RW MY2021 | length_mm | [4625.0] | [4590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v RW MY2022 | length_mm | [4625.0] | [4590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v RW MY2020 | length_mm | [4625.0] | [4590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v RW MY2021 | length_mm | [4625.0] | [4590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v RW MY2022 | length_mm | [4625.0] | [4590] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2023 | curb_weight_kg | [1781.0] | [1649] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2024 | curb_weight_kg | [1781.0] | [1649] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2025 | curb_weight_kg | [1781.0, 2023.0] | [1649] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2026 | curb_weight_kg | [1769.0, 1781.0, 2023.0] | [1649] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2023 | curb_weight_kg | [1781.0] | [1599] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2024 | curb_weight_kg | [1781.0] | [1599] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2025 | curb_weight_kg | [1781.0, 2023.0] | [1599] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| CR-V | honda/cr-v US2023+ MY2026 | curb_weight_kg | [1769.0, 1781.0, 2023.0] | [1599] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 296 записей (10% каждой линейки), расхождений 0.
- accord: 109 проверено, 0 расхождений
- civic: 116 проверено, 0 расхождений
- cr-v: 71 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Accord X (2018–2022): consumerreports.org: "This generation of Accord has a coupelike silhouette and a lower stance." (https://www.consumerreports.org/cars/honda/accord/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/honda-accord/) [media: generation starts MY2018]
- Accord US2023+ (2023–2026): consumerreports.org: "The 2023 Accord is treated to an evolutionary redesign" (https://www.consumerreports.org/cars/honda/accord/); cars.com: "The Honda Accord's 2023 redesign wasn't particularly dramatic" (https://www.cars.com/research/honda-accord/) [media: generation starts MY2023]
- Civic 10th (2016–2021): consumerreports.org: "Honda pulled out all of the stops, building a clean-sheet design." (https://www.consumerreports.org/cars/honda/civic/); cars.com: "The 10th-generation Civic marked a return to the compact car's roots: a renewed focus on fun-to-drive performance thanks to an all-new platform for
- Civic US2022+ (2022–2026): consumerreports.org: "Honda's 11th-generation Civic remains fuel efficient and brings a simpler infotainment system." (https://www.consumerreports.org/cars/honda/civic/); cars.com: "The Honda Civic underwent a complete redesign for 2022, kicking off the 11th generation" (https://www.cars.com/researc
- CR-V RW (2017–2022): consumerreports.org: "The redesigned CR-V gains features, space, and refinement." (https://www.consumerreports.org/cars/honda/cr-v/); cars.com: "Fully redesigned for 2017" (https://www.cars.com/research/honda-cr_v/) [media: generation starts MY2017]
- CR-V US2023+ (2023–2026): consumerreports.org: "The redesigned CR-V gained size and weight, but didn't stray far from its proven formula of practicality and functionality." (https://www.consumerreports.org/cars/honda/cr-v/); cars.com: "The CR-V was redesigned for 2023 with several notable improvements over the previous gener

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- honda/accord: --prune-stale, код 0, {"raw_documents_seen": 132, "source_records_new": 22, "te_existing": 2027, "configurations": 62, "configurations_research_only": 54, "configurations_linked": 8, "issues_existing": 69, "maintenance_new": 183}
- honda/civic: --prune-stale, код 0, {"raw_documents_seen": 211, "source_records_new": 38, "te_existing": 2456, "configurations": 77, "configurations_research_only": 76, "configurations_linked": 1, "issues_existing": 62, "maintenance_new": 282}
- honda/cr-v: --prune-stale, код 0, {"raw_documents_seen": 121, "source_records_new": 20, "te_existing": 1413, "configurations": 45, "configurations_linked": 8, "configurations_research_only": 37, "issues_existing": 81, "maintenance_new": 123}
