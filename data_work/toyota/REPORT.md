# Toyota — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Camry | IX | 2025–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ○ | ○ | ◐ | ● | ● | ● | ○ | ● |
| Camry | VII | 2012–2017 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ● | ● | ● | ● | ● | ● |
| Camry | VIII | 2018–2024 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ● | ● | ● | ● | ● | ● |
| Corolla | XI | 2014–2019 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ● | ● | ● | ● |
| Corolla | XII | 2020–2026 | ● | ◐ | ● | ● | ○ | ● | ○ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| RAV4 | IV | 2014–2018 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| RAV4 | V (2019 redesign, TNGA) | 2019–2025 | ● | ◐ | ● | ● | ● | ● | ● | ◐ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| RAV4 | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ◐ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| Highlander | III | 2014–2019 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Highlander | IV | 2020–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Prius | ZVW30 | 2014–2015 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| Prius | US2016-2022 | 2016–2022 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| Prius | US2023+ | 2023–2026 | ● | ◐ | ● | ● | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ● | ● |

Итого ячеек: заполнено 137, частично 38, нет 20, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 1031 | 6717 |
| known_issues | 14 | 227 |
| maintenance_schedule_items | 0 | 0 |

## 3. Журнал пробелов

Записей в журнале пробелов: 1133 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 167 | toyota-corolla-us-2014-1.8l-4cyl-ice-a-av-s7-fwd; toyota-corolla-us-2014-1.8l-4cyl-ice-a-variable-gear-ratios-fwd; toyota-corolla-us-2014-1.8l-4cyl-ice-a-4-spd-fwd |
| engine_oil_capacity_drain_refill_l | value N outside the validator range; not used | 76 | toyota/corolla carmans-2021-toyota-corolla p.558; toyota/corolla carmans-2022-toyota-corolla p.558; toyota/corolla carmans-2023-toyota-corolla p.305 |
| rear_brakes | one document gives N values: ['"N in."', '"Solid Disc"'] | 39 | toyota/corolla MY2018 (press-toyota-corolla-2018-850f6e9e); toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52) |
| valvetrain | engine not stated; EPA lists several engines | 39 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| front_brakes | one document gives N values: ['"N in."', '"Power-assisted Ventilated disc"'] | 38 | toyota/corolla MY2018 (press-toyota-corolla-2018-850f6e9e); toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52) |
| compression_ratio | engine not stated; EPA lists several engines | 37 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 35 | toyota/corolla MY2020 (carmans-2020-toyota-corolla); toyota/corolla MY2021 (carmans-2021-toyota-corolla); toyota/corolla MY2022 (carmans-2022-toyota-corolla) |
| engine_description | engine not stated; EPA lists several engines | 35 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| power_hp | engine not stated; EPA lists several engines | 32 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| power_rpm | engine not stated; EPA lists several engines | 32 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 30 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| torque_lb_ft | engine not stated; EPA lists several engines | 30 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| torque_rpm | engine not stated; EPA lists several engines | 30 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| injection | engine not stated; EPA lists several engines | 29 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2021 (press-toyota-corolla-2021-471ed88b) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 28 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| coolant_capacity_l | value N outside the validator range; not used | 24 | toyota/rav4 carmans-2017-toyota-rav4-hybrid p.610; toyota/rav4 carmans-2018-toyota-rav4-hybrid p.614; toyota/rav4 carmans-2020-toyota-rav4-hybrid p.679 |
| fuel_tank_l | value N outside the validator range; not used | 23 | toyota/corolla carmans-2020-toyota-corolla p.526; toyota/rav4 carmans-2017-toyota-rav4-hybrid p.610; toyota/rav4 carmans-2018-toyota-rav4-hybrid p.614 |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 19 | toyota/corolla MY2019 (carmans-2019-toyota-corolla); toyota/corolla MY2020 (carmans-2020-toyota-corolla); toyota/corolla MY2021 (carmans-2021-toyota-corolla) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 19 | toyota/corolla MY2019 (carmans-2019-toyota-corolla); toyota/corolla MY2020 (carmans-2020-toyota-corolla); toyota/corolla MY2021 (carmans-2021-toyota-corolla) |
| engine_oil_specification | engine not stated; EPA lists several engines | 18 | toyota/corolla MY2019 (carmans-2019-toyota-corolla); toyota/corolla MY2020 (carmans-2020-toyota-corolla); toyota/corolla MY2021 (carmans-2021-toyota-corolla) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 18 | toyota/corolla MY2019 (carmans-2019-toyota-corolla); toyota/corolla MY2020 (carmans-2020-toyota-corolla); toyota/corolla MY2021 (carmans-2021-toyota-corolla) |
| height_mm | one document gives N values: ['N', 'N'] | 18 | toyota/rav4 MY2017 (press-toyota-rav4-2017-a5793392); toyota/rav4 MY2017 (press-toyota-rav4-2017-a5793392); toyota/rav4 MY2017 (press-toyota-rav4-2017-e27992ec) |
| cargo_l | one document gives N values: ['N', 'N'] | 18 | toyota/highlander MY2014 (press-toyota-highlander-2014-895a1697); toyota/highlander MY2014 (press-toyota-highlander-2014-895a1697); toyota/highlander MY2014 (press-toyota-highlander-2014-a90b58ce) |
| turning_circle_m | one document gives N values: ['N', 'N'] | 17 | toyota/rav4 MY2014 (press-toyota-rav4-2014-50664163); toyota/rav4 MY2015 (press-toyota-rav4-2015-43cfad53); toyota/rav4 MY2016 (press-toyota-rav4-2016-0941e6a0) |
| passenger_volume_l | one document gives N values: ['N', 'N'] | 16 | toyota/corolla MY2014 (press-toyota-corolla-2014-6638e1d9); toyota/corolla MY2015 (press-toyota-corolla-2015-4122f5a5); toyota/corolla MY2016 (press-toyota-corolla-2016-04eac171) |
| track_front_mm | one document gives N values: ['N', 'N'] | 14 | toyota/rav4 MY2014 (press-toyota-rav4-2014-50664163); toyota/rav4 MY2015 (press-toyota-rav4-2015-43cfad53); toyota/rav4 MY2016 (press-toyota-rav4-2016-0941e6a0) |
| track_rear_mm | one document gives N values: ['N', 'N'] | 14 | toyota/rav4 MY2014 (press-toyota-rav4-2014-50664163); toyota/rav4 MY2015 (press-toyota-rav4-2015-43cfad53); toyota/rav4 MY2016 (press-toyota-rav4-2016-0941e6a0) |
| cargo_l | one document gives N values: ['N', 'N', 'N'] | 14 | toyota/rav4 MY2019 (press-toyota-rav4-2019-8c79d3a0); toyota/rav4 MY2019 (press-toyota-rav4-2019-f9c3638a); toyota/highlander MY2020 (press-toyota-highlander-2020-05341a46) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 13 | toyota/corolla MY2019 (carmans-2019-toyota-corolla); toyota/corolla MY2023 (carmans-2023-toyota-corolla); toyota/corolla MY2026 (carmans-2026-toyota-corolla) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 12 | toyota/corolla MY2020 (carmans-2020-toyota-corolla); toyota/corolla MY2021 (carmans-2021-toyota-corolla); toyota/corolla MY2022 (carmans-2022-toyota-corolla) |
| seats | one document gives N values: ['N', 'N'] | 12 | toyota/highlander MY2020 (press-toyota-highlander-2020-05341a46); toyota/highlander MY2021 (press-toyota-highlander-2021-8afcfd62); toyota/highlander MY2022 (press-toyota-highlander-2022-215ea4c4) |
| passenger_volume_l | one document gives N values: ['N', 'N', 'N'] | 10 | toyota/highlander MY2020 (press-toyota-highlander-2020-05341a46); toyota/highlander MY2021 (press-toyota-highlander-2021-8afcfd62); toyota/highlander MY2022 (press-toyota-highlander-2022-215ea4c4) |
| bore_stroke_in | engine not stated; EPA lists several engines | 8 | toyota/corolla MY2019 (press-toyota-corolla-2019-69ccaa30); toyota/corolla MY2020 (press-toyota-corolla-2020-36f86d52); toyota/corolla MY2021 (press-toyota-corolla-2021-471ed88b) |
| front_brakes | one document gives N values: ['"N in."', '"Ventilated disc"'] | 8 | toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54); toyota/corolla MY2021 (press-toyota-corolla-2021-5332800a); toyota/corolla MY2022 (press-toyota-corolla-2022-50c13e7a) |
| rear_brakes | one document gives N values: ['"N in."', '"Solid disc"'] | 8 | toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54); toyota/corolla MY2021 (press-toyota-corolla-2021-5332800a); toyota/corolla MY2022 (press-toyota-corolla-2022-50c13e7a) |
| front_brakes | not found unambiguously in the available US press specification pages | 7 | toyota/rav4 IV; toyota/rav4 V (2019 redesign, TNGA); toyota/rav4 US2026+ |
| engine_oil_capacity_without_filter_l | engine not stated; EPA lists several engines | 6 | toyota/corolla MY2019 (carmans-2019-toyota-corolla); toyota/highlander MY2015 (carmans-2015-toyota-highlander); toyota/highlander MY2016 (carmans-2016-toyota-highlander) |
| electric_motor | one document gives N values: ['"N/N lb.-ft."', '"Permanent Magnet Synchronous"'] | 6 | toyota/rav4 MY2020 (press-toyota-rav4-2020-bc5c7673); toyota/rav4 MY2021 (press-toyota-rav4-2021-b30eb77b); toyota/rav4 MY2022 (press-toyota-rav4-2022-96200f26) |
| front_brakes | one document gives N values: ['"N in."', '"Power-assisted ventilated disc"'] | 6 | toyota/highlander MY2024 (press-toyota-highlander-2024-a4e144a9); toyota/highlander MY2024 (press-toyota-highlander-2024-a7175686); toyota/highlander MY2025 (press-toyota-highlander-2025-72f6700f) |
| rear_brakes | one document gives N values: ['"N in. rotor"', '"Solid disc (hydraulic with power assist) with standard Anti-l | 6 | toyota/prius MY2014 (press-toyota-prius-2014-e1f9c967); toyota/prius MY2015 (press-toyota-prius-2015-030b2330); toyota/prius MY2016 (press-toyota-prius-2016-54265b0e) |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 5 | toyota/rav4 MY2018 (carmans-2018-toyota-rav4); toyota/rav4 MY2019 (carmans-2019-toyota-rav4); toyota/rav4 MY2020 (carmans-2020-toyota-rav4) |
| electric_motor | one document gives N values: ['"N lb-ft"', '"N hp/N kW"', '"DCNV"', '"Permanent Magnet AC Synchronous Motor"'] | 5 | toyota/prius MY2018 (press-toyota-prius-2018-46f3e2fd); toyota/prius MY2019 (press-toyota-prius-2019-fb186b39); toyota/prius MY2020 (press-toyota-prius-2020-13f8ad0d) |
| wheel_size_in | one document gives N values: ['N', 'N'] | 5 | toyota/prius MY2021 (press-toyota-prius-2021-bb27b648); toyota/prius MY2023 (press-toyota-prius-2023-999c3af7); toyota/prius MY2024 (press-toyota-prius-2024-714877a0) |
| engine_family_key | hybrid engine code not found in opened sources | 4 | toyota-camry-us-2014-2.5l-4cyl-hev-a-variable-gear-ratios-fwd; toyota-camry-us-2015-2.5l-4cyl-hev-a-variable-gear-ratios-fwd; toyota-camry-us-2016-2.5l-4cyl-hev-a-variable-gear-ratios-fwd |
| engine_family_key | Engine code of the ninth-generation Camry Hybrid not stated in opened sources (no MYN-N owner's manual copy; N | 4 | toyota-camry-us-2025-2.5l-4cyl-hev-a-av-s6-awd; toyota-camry-us-2025-2.5l-4cyl-hev-a-av-s6-fwd; toyota-camry-us-2026-2.5l-4cyl-hev-a-av-s6-awd |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N'] | 4 | toyota/corolla MY2014 (mcum-corolla-4-door-2013-2017); toyota/corolla MY2015 (mcum-corolla-4-door-2013-2017); toyota/corolla MY2016 (mcum-corolla-4-door-2013-2017) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 4 | toyota/corolla XII; toyota/rav4 US2026+; toyota/highlander III |
| brake_fluid | not found unambiguously in the available US owner's manuals | 4 | toyota/corolla XII; toyota/rav4 V (2019 redesign, TNGA); toyota/rav4 US2026+ |
| electric_motor | one document gives N values: ['"N lb.-ft."', '"AC NV"', '"Drives front wheels, regeneration during braking"',  | 4 | toyota/highlander MY2014 (press-toyota-highlander-2014-a90b58ce); toyota/highlander MY2015 (press-toyota-highlander-2015-c240413d); toyota/highlander MY2016 (press-toyota-highlander-2016-91d6700e) |
| electric_motor | one document gives N values: ['"N lb.-ft."', '"N hp/N kW"', '"DCNV"', '"Permanent Magnet Synchronous Motor"'] | 4 | toyota/prius MY2014 (press-toyota-prius-2014-e1f9c967); toyota/prius MY2015 (press-toyota-prius-2015-030b2330); toyota/prius MY2016 (press-toyota-prius-2016-54265b0e) |
| front_brakes | one document gives N values: ['"N in. rotor"', '"Ventilated disc (hydraulic with power assist) with standard A | 4 | toyota/prius MY2014 (press-toyota-prius-2014-e1f9c967); toyota/prius MY2015 (press-toyota-prius-2015-030b2330); toyota/prius MY2016 (press-toyota-prius-2016-54265b0e) |
| electric_motor | one document gives N values: ['"N hp/N kW"', '"N lb.-ft."', '"DCNV"', '"Permanent Magnet AC Synchronous Motor" | 4 | toyota/prius MY2023 (press-toyota-prius-2023-999c3af7); toyota/prius MY2024 (press-toyota-prius-2024-714877a0); toyota/prius MY2025 (press-toyota-prius-2025-cf77a74a) |
| front_brakes | one document gives N values: ['"N in. (FWD models); N in. (AWD)"', '"Ventilated disc"'] | 4 | toyota/prius MY2023 (press-toyota-prius-2023-999c3af7); toyota/prius MY2024 (press-toyota-prius-2024-714877a0); toyota/prius MY2025 (press-toyota-prius-2025-cf77a74a) |
| rear_brakes | one document gives N values: ['"N in. FWD; N in (AWD)"', '"Solid disc"'] | 4 | toyota/prius MY2023 (press-toyota-prius-2023-999c3af7); toyota/prius MY2024 (press-toyota-prius-2024-714877a0); toyota/prius MY2025 (press-toyota-prius-2025-cf77a74a) |
| bore_stroke_mm | one document gives N values: ['"N x N"', '"N x N"'] | 3 | toyota/corolla MY2020 (press-toyota-corolla-2020-b39c38c3); toyota/corolla MY2021 (press-toyota-corolla-2021-7688188f); toyota/corolla MY2022 (press-toyota-corolla-2022-9c115d68) |
| engine_displacement_cc | one document gives N values: ['N', 'N'] | 3 | toyota/corolla MY2020 (press-toyota-corolla-2020-b39c38c3); toyota/corolla MY2021 (press-toyota-corolla-2021-7688188f); toyota/corolla MY2022 (press-toyota-corolla-2022-9c115d68) |
| power_hp | one document gives N values: ['N', 'N'] | 3 | toyota/corolla MY2020 (press-toyota-corolla-2020-b39c38c3); toyota/corolla MY2021 (press-toyota-corolla-2021-7688188f); toyota/corolla MY2022 (press-toyota-corolla-2022-9c115d68) |
| power_rpm | one document gives N values: ['"N,N"', '"N,N"'] | 3 | toyota/corolla MY2020 (press-toyota-corolla-2020-b39c38c3); toyota/corolla MY2021 (press-toyota-corolla-2021-7688188f); toyota/corolla MY2022 (press-toyota-corolla-2022-9c115d68) |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 3 | toyota/corolla MY2020 (press-toyota-corolla-2020-b39c38c3); toyota/corolla MY2021 (press-toyota-corolla-2021-7688188f); toyota/corolla MY2022 (press-toyota-corolla-2022-9c115d68) |
| torque_rpm | one document gives N values: ['"N,N"', '"N,N"'] | 3 | toyota/corolla MY2020 (press-toyota-corolla-2020-b39c38c3); toyota/corolla MY2021 (press-toyota-corolla-2021-7688188f); toyota/corolla MY2022 (press-toyota-corolla-2022-9c115d68) |
| electric_motor | one document gives N values: ['"N kW (N hp)"', '"N kW (N hp)"', '"Permanent Synchronous Magnet Motor"'] | 3 | toyota/corolla MY2023 (press-toyota-corolla-2023-91062a12); toyota/corolla MY2025 (press-toyota-corolla-2025-c7c8995e); toyota/corolla MY2026 (press-toyota-corolla-2026-cc9e8e8b) |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 3 | toyota/corolla XII; toyota/highlander III; toyota/highlander IV |
| front_brakes | one document gives N values: ['"N in. (LE), N in. (XLE/LTD) N sq. in."', '"Power-assisted Ventilated disc"'] | 3 | toyota/rav4 MY2014 (press-toyota-rav4-2014-50664163); toyota/rav4 MY2015 (press-toyota-rav4-2015-43cfad53); toyota/rav4 MY2016 (press-toyota-rav4-2016-0941e6a0) |
| electric_motor | one document gives N values: ['"N hp (N kW)"', '"AC NV N hp (NkW)"', '"AC NV"', '"Drives front wheels, regener | 3 | toyota/rav4 MY2016 (press-toyota-rav4-2016-66dcfc66); toyota/rav4 MY2017 (press-toyota-rav4-2017-e27992ec); toyota/rav4 MY2018 (press-toyota-rav4-2018-051b09d7) |
| rear_brakes | one document gives N values: ['"N in."', '"Solid Disc with Electronically Controlled Braking (ECB) system and  | 3 | toyota/highlander MY2024 (press-toyota-highlander-2024-a4e144a9); toyota/highlander MY2025 (press-toyota-highlander-2025-df825d09); toyota/highlander MY2026 (press-toyota-highlander-2026-136805d4) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 2 | toyota/corolla MY2023 (carmans-2023-toyota-corolla); toyota/corolla MY2026 (carmans-2026-toyota-corolla) |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 2 | toyota/corolla MY2014 (press-toyota-corolla-2014-6638e1d9); toyota/highlander MY2025 (press-toyota-highlander-2025-72f6700f) |
| electric_motor | one document gives N values: ['"N kW (N hp)"', '"Permanent Synchronous Magnet Motor"'] | 2 | toyota/corolla MY2021 (press-toyota-corolla-2021-5332800a); toyota/corolla MY2022 (press-toyota-corolla-2022-50c13e7a) |
| front_brakes | one document gives N values: ['"N in. N sq. in."', '"Power-assisted Ventilated disc"'] | 2 | toyota/rav4 MY2016 (press-toyota-rav4-2016-66dcfc66); toyota/rav4 MY2017 (press-toyota-rav4-2017-e27992ec) |
| cargo_l | not found unambiguously in the available US press specification pages | 2 | toyota/highlander III; toyota/highlander IV |
| front_brakes | one document gives N values: ['"N in. rotor"', '"Power-assisted ventilated front disc brakes; solid rear disc  | 2 | toyota/prius MY2018 (press-toyota-prius-2018-46f3e2fd); toyota/prius MY2019 (press-toyota-prius-2019-fb186b39) |
| engine_family_key | No source opened in this session names the MYN Camry VN engine code (no N owner's manual copy; NHTSA communica | 1 | toyota-camry-us-2024-3.5l-6cyl-ice-a-s8-fwd |
| electric_motor | one document gives N values: ['"N Nm (N lb.-ft.)"', '"N kW (N hp)"', '"Permanent Synchronous Magnet Motor"'] | 1 | toyota/corolla MY2020 (press-toyota-corolla-2020-cb716d54) |
| front_brakes | one document gives N values: ['"N-in. x N-in."', '"Ventilated disc N piston caliper"'] | 1 | toyota/corolla MY2023 (press-toyota-corolla-2023-4b866652) |
| rear_brakes | one document gives N values: ['"N-in. x N-in."', '"Ventilated disc N piston caliper"'] | 1 | toyota/corolla MY2023 (press-toyota-corolla-2023-4b866652) |
| power_hp | not found unambiguously in the available US press specification pages | 1 | toyota/corolla XII |
| torque_lb_ft | not found unambiguously in the available US press specification pages | 1 | toyota/corolla XII |
| transmission_fluid_capacity_l | value N outside the validator range; not used | 1 | toyota/rav4 carmans-2019-toyota-rav4 p.663 |
| system_power_hp | one document gives N values: ['N', 'N'] | 1 | toyota/rav4 MY2018 (press-toyota-rav4-2018-051b09d7) |
| front_brakes | one document gives N values: ['"N in. (LE) N in. (XLE, Adventure, SE, Limited, and Platinum)"', '"Power-assist | 1 | toyota/rav4 MY2018 (press-toyota-rav4-2018-c526d0c1) |
| electric_motor | one document gives N values: ['"N/N hp (N/N kW)"', '"N/N lb.-ft."', '"Permanent Magnet Synchronous"'] | 1 | toyota/rav4 MY2019 (press-toyota-rav4-2019-8c79d3a0) |
| electric_motor | one document gives N values: ['"N HP"', '"N lb.-ft."', '"N lb.-ft."', '"DC NV"', '"Permanent Magnet Synchronou | 1 | toyota/rav4 MY2026 (press-toyota-rav4-2026-236e0e1d) |
| electric_motor | one document gives N values: ['"N lb-ft"', '"AC NV"', '"Drives front wheels, regeneration during braking"', '" | 1 | toyota/highlander MY2018 (press-toyota-highlander-2018-46ad3956) |
| front_brakes | one document gives N values: ['"Power-assisted ventilated front disc brakes; solid rear disc with integrated r | 1 | toyota/prius MY2020 (press-toyota-prius-2020-13f8ad0d) |
| rear_brakes | one document gives N values: ['"N in. rotor Solid disc (hydraulic with power assist)"', '"with standard Anti-l | 1 | toyota/prius MY2020 (press-toyota-prius-2020-13f8ad0d) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 1 | toyota/prius US2023+ |
| tires | not found unambiguously in the available US press specification pages | 1 | toyota/prius US2023+ |
| front_suspension | not found unambiguously in the available US press specification pages | 1 | toyota/prius US2023+ |
| steering | not found unambiguously in the available US press specification pages | 1 | toyota/prius US2023+ |

## 4. Конфликты источников

Конфликтов: 174. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 164
- model-year manual kept over the whole-generation page (Appendix E.6): 5
- Product Information 2017 gives Tread Width (Front/Rear) 62.0/61.6 in. : 2
- Product Information sheets 2014-2017 state 'With filter L4 : 4.7qt' (4: 1
- Product Information 2021-2024 gives 15.8 gal. for front-wheel-drive gr: 1
- Hybrid Product Information 2022-2023 gives 13.2 gal.; the hybrid owner: 1

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Camry |  | track_front_mm | 1585 | None | Product Information 2017 gives Tread Width (Front/Rear) 62.0/61.6 in. for V6 XSE/XLE, the owner's manual gives 62.4/62.0 in. (1585/1575 mm) for P215/55R17 and P225/45R18 tires. Manual kept (primary for dimensions). |
| Camry |  | track_rear_mm | 1575 | None | Product Information 2017 gives Tread Width (Front/Rear) 62.0/61.6 in. for V6 XSE/XLE, the owner's manual gives 62.4/62.0 in. (1585/1575 mm) for P215/55R17 and P225/45R18 tires. Manual kept (primary for dimensions). |
| Camry |  | engine_oil_capacity_l | 4.4 | None | Product Information sheets 2014-2017 state 'With filter L4 : 4.7qt' (4.4 L by the fixed factor is 4.65 qt; the sheets round up to 4.7 qt). Manual value kept per prompt rule (manual is the primary oil source). |
| Camry |  | fuel_tank_l | 60.6 | None | Product Information 2021-2024 gives 15.8 gal. for front-wheel-drive grades; the 2021-2023 owner's manuals give 16.0 gal. (60.6 L) for 2WD models. Manual kept. |
| Camry |  | fuel_tank_l | 49.3 | None | Hybrid Product Information 2022-2023 gives 13.2 gal.; the hybrid owner's manuals give 13 gal. (49.3 L). Manual kept. |
| Corolla | toyota/corolla XII MY2023 | coolant_description | ethylene glycol based non-silicate; ethylene glycol-based | ['ethylene glycol-based'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Corolla | toyota/corolla XI MY2019 | curb_weight_kg | [1388.0] | [1265] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | length_mm | [4315.0] | [4640] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | track_rear_mm | [1544.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | wheelbase_mm | [2639.0] | [2700] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | length_mm | [4315.0] | [4380] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | track_rear_mm | [1544.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2019 | width_mm | [1775.0] | [1790] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2017 | height_mm | [1455.0, 1476.0] | [1410] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XI MY2018 | track_rear_mm | [1521.0] | [1500] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | height_mm | [1435.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_rear_mm | [1534.0, 1544.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_rear_mm | [1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | width_mm | [1775.0, 1781.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | width_mm | [1781.0, 1791.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | width_mm | [1781.0, 1791.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | width_mm | [1781.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | height_mm | [1435.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_rear_mm | [1534.0, 1544.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_rear_mm | [1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | width_mm | [1775.0, 1781.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | width_mm | [1781.0, 1791.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | width_mm | [1781.0, 1791.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | width_mm | [1781.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | height_mm | [1435.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_rear_mm | [1534.0, 1544.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_rear_mm | [1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | width_mm | [1775.0, 1781.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | width_mm | [1781.0, 1791.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | width_mm | [1781.0, 1791.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | width_mm | [1781.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | length_mm | [4409.0, 4630.0] | [4380] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2020 | track_rear_mm | [1534.0, 1544.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2021 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2022 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_rear_mm | [1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | curb_weight_kg | [1293.0, 1340.0, 1411.0, 1429.0] | [1485] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | curb_weight_kg | [1293.0, 1340.0, 1411.0, 1429.0] | [1485] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1420] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1520] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | width_mm | [1781.0, 1791.0, 1849.0] | [1760] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | curb_weight_kg | [1293.0, 1429.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | curb_weight_kg | [1340.0, 1411.0, 1429.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | curb_weight_kg | [1293.0, 1340.0, 1411.0, 1429.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | curb_weight_kg | [1293.0, 1340.0, 1411.0, 1429.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | height_mm | [1435.0, 1450.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | height_mm | [1435.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | height_mm | [1435.0, 1450.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | height_mm | [1435.0, 1450.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_front_mm | [1532.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2023 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2024 | track_rear_mm | [1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2025 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Corolla | toyota/corolla XII MY2026 | track_rear_mm | [1534.0, 1544.0, 1549.0] | [1600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 IV MY2017 | length_mm | [4661.0] | [4600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 IV MY2017 | length_mm | [4661.0] | [4600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 IV MY2016 | curb_weight_kg | [1567.0, 1581.0, 1597.0, 1619.0, 1635.0, 1647.0] | [1765] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 IV MY2017 | length_mm | [4661.0] | [4600] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 US2026+ MY2026 | height_mm | [1694.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 US2026+ MY2026 | length_mm | [4597.0, 4623.0] | [4650] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| RAV4 | toyota/rav4 US2026+ MY2026 | height_mm | [1694.0] | [1780] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Highlander | toyota/highlander III MY2019 | curb_weight_kg | [1875.0, 1925.0, 1955.0, 1971.0, 2057.0, 2082.0, 2111.0] | [2220] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Highlander | toyota/highlander III MY2014 | curb_weight_kg | [1875.0, 1925.0, 1955.0, 1975.0, 1995.0, 2025.0, 2045.0] | [2205] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius US2016-2022 MY2018 | octane_aki | 86 | [87] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Prius | toyota/prius US2016-2022 MY2020 | octane_aki | 85 | [87] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Prius | toyota/prius US2023+ MY2026 | engine_oil_capacity_l | 4.2 | [3.9] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Prius | toyota/prius US2023+ MY2026 | engine_oil_capacity_without_filter_l | 3.9 | [3.5] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Prius | toyota/prius US2016-2022 MY2021 | length_mm | [4572.0] | [4540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius US2016-2022 MY2022 | length_mm | [4572.0] | [4540] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius US2023+ MY2024 | curb_weight_kg | [1405.0, 1435.0, 1460.0, 1465.0, 1490.0, 1515.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius US2023+ MY2025 | curb_weight_kg | [1405.0, 1435.0, 1460.0, 1465.0, 1490.0, 1515.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius US2023+ MY2026 | curb_weight_kg | [1405.0, 1435.0, 1460.0, 1465.0, 1490.0, 1515.0] | [1570] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius ZVW30 MY2014 | height_mm | [1491.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius ZVW30 MY2015 | height_mm | [1491.0] | [1480] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius ZVW30 MY2014 | length_mm | [4481.0] | [4460] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Prius | toyota/prius ZVW30 MY2015 | length_mm | [4481.0] | [4460] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 263 записей (10% каждой линейки), расхождений 0.
- corolla: 60 проверено, 0 расхождений
- highlander: 71 проверено, 0 расхождений
- prius: 71 проверено, 0 расхождений
- rav4: 61 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Corolla XII (2020–2026): consumerreports.org: "The redesigned Corolla sedan is fuel efficient, but the new styling has compromised the rear seat room" (https://www.consumerreports.org/cars/toyota/corolla/); cars.com: "The 2020 redesign puts the Corolla on a new platform shared with the compact sedan's hatchback sibling." (h
- RAV4 V (2019 redesign, TNGA) (2019–2025): consumerreports.org: "The popular RAV4 was redesigned for 2019, with new proportions and a more-rugged appearance." (https://www.consumerreports.org/cars/toyota/rav4/); cars.com: "The redesigned 2019 RAV4 got a makeover that gave this compact SUV a rugged, chunkier look" (https://www.cars.com/resear
- RAV4 US2026+ (2026–2026): consumerreports.org: "The redesigned-for-2026 RAV4 smartly evolves the industry's bestselling compact SUV" (https://www.consumerreports.org/cars/toyota/rav4/); cars.com: "The redesigned 2026 RAV4 wasn't significantly changed in dimensions or exterior styling" (https://www.cars.com/research/toyota-ra
- Highlander IV (2020–2026): consumerreports.org: "the fourth-generation Highlander retains its qualities of comfortable ride and a smooth powertrain." (https://www.consumerreports.org/cars/toyota/highlander/); cars.com: "The fourth-generation Highlander debuted as a 2020 model" (https://www.cars.com/research/toyota-highlander/
- Prius US2016-2022 (2016–2022): consumerreports.org: "the fourth-generation Prius was a revolution." (https://www.consumerreports.org/cars/toyota/prius/); cars.com: "Along with updated styling, the Prius grew for 2016, increasing cargo space." (https://www.cars.com/research/toyota-prius/) [media: generation starts MY2016]
- Prius US2023+ (2023–2026): consumerreports.org: "complete redesign of the Prius gave it a sleeker look, more power, and incremental improvements in fuel economy." (https://www.consumerreports.org/cars/toyota/prius/); cars.com: "Toyota took a radical approach with the car's 2023 redesign" (https://www.cars.com/research/toyota-

## Изменения ранее записанных строк (последняя загрузка)

- Camry: torque_lb_ft = 182 (MY[2021, 2021]) — deleted (superseded by the current staging scope)
- Camry: torque_lb_ft = 185 (MY[2021, 2021]) — deleted (superseded by the current staging scope)

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- toyota/corolla: --prune-stale, код 0, {"raw_documents_seen": 107, "te_existing": 1601, "configurations": 59, "configurations_research_only": 57, "configurations_linked": 2, "issues_existing": 44}
- toyota/rav4: --prune-stale, код 0, {"raw_documents_seen": 113, "te_existing": 1395, "configurations": 38, "configurations_research_only": 36, "configurations_linked": 2, "issues_existing": 66}
- toyota/highlander: --prune-stale, код 0, {"raw_documents_seen": 99, "te_existing": 1526, "configurations": 49, "configurations_linked": 6, "configurations_research_only": 43, "issues_existing": 64}
- toyota/prius: --prune-stale, код 0, {"raw_documents_seen": 81, "source_records_new": 13, "te_existing": 769, "te_new_GENERATION": 395, "configurations": 21, "configurations_research_only": 21, "issues_existing": 39}
