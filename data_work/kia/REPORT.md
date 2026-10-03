# Kia — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Optima / K5 | TF/QF | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ● | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Optima / K5 | JF | 2016–2020 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Optima / K5 | DL3 | 2021–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Forte | YD | 2014–2018 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ● | ◐ | ○ | ◐ | ○ | ● | ● | ● |
| Forte | BD | 2019–2024 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Rio | US2014-2017 | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ● | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Rio | SC | 2018–2023 | ◐ | ◐ | ● | ● | ○ | ● | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Sorento | US2014-2015 | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Sorento | UM | 2016–2020 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Sorento | US2021+ | 2021–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Sportage | US2014-2016 | 2014–2016 | ◐ | ◐ | ● | ● | ○ | ● | ○ | ● | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Sportage | QL | 2017–2022 | ◐ | ◐ | ● | ● | ○ | ● | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Sportage | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 96, частично 54, нет 45, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 4592 |
| known_issues | 0 | 265 |
| maintenance_schedule_items | 0 | 639 |

## 3. Журнал пробелов

Записей в журнале пробелов: 677 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 242 | kia-optima-k5-us-2014-2.0l-4cyl-turbo-ice-a-6-spd-fwd; kia-optima-k5-us-2014-2.4l-4cyl-hev-a-am6-fwd; kia-optima-k5-us-2014-2.4l-4cyl-ice-a-6-spd-fwd |
| engine_oil_specification | engine not stated; EPA lists several engines | 28 | kia/optima-k5 MY2014 (carmans-2014-kia-optima); kia/optima-k5 MY2014 (carmans-2014-kia-optima-hybrid); kia/optima-k5 MY2015 (carmans-2015-kia-optima) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 27 | kia/optima-k5 MY2014 (carmans-2014-kia-optima-hybrid); kia/optima-k5 MY2017 (carmans-2017-kia-optima-phev); kia/optima-k5 MY2019 (carmans-2019-kia-optima-hybrid) |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N, N, N, N, N] xN,N miles | 27 | kia/optima-k5 carmans-2019-kia-optima p.451; kia/optima-k5 carmans-2019-kia-optima p.456; kia/optima-k5 carmans-2019-kia-optima-hybrid p.436 |
| maintenance transmission_fluid | interval text not understood: No check, No service required | 23 | kia/optima-k5 carmans-2019-kia-optima p.453; kia/optima-k5 carmans-2019-kia-optima p.458; kia/optima-k5 carmans-2019-kia-optima-hybrid p.437 |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 22 | kia/optima-k5 MY2014 (carmans-2014-kia-optima); kia/optima-k5 MY2014 (carmans-2014-kia-optima-hybrid); kia/optima-k5 MY2015 (carmans-2015-kia-optima) |
| maintenance engine_air_filter | irregular list points [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N] miles; not converted | 16 | kia/optima-k5 carmans-2016-kia-optima; kia/optima-k5 carmans-2018-kia-optima; kia/optima-k5 official-233e63cedbc5 |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 15 | kia/optima-k5 MY2014 (carmans-2014-kia-optima-hybrid); kia/optima-k5 MY2017 (carmans-2017-kia-optima-phev); kia/optima-k5 MY2019 (carmans-2019-kia-optima-hybrid) |
| power_hp | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| torque_lb_ft | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| tires | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| front_suspension | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| rear_suspension | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| front_brakes | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| steering | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| ground_clearance | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| cargo_l | no US press specification page for these years | 13 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| engine_oil_capacity_l | not found unambiguously in the available US owner's manuals | 12 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| coolant | not found unambiguously in the available US owner's manuals | 12 | kia/optima-k5 TF/QF; kia/optima-k5 JF; kia/optima-k5 DL3 |
| coolant_capacity_l | engine not stated; EPA lists several engines | 10 | kia/optima-k5 MY2017 (carmans-2017-kia-optima-phev); kia/optima-k5 MY2019 (carmans-2019-kia-optima-hybrid); kia/optima-k5 MY2020 (carmans-2020-kia-optima-hybrid) |
| maintenance cabin_air_filter | irregular list points [N, N, N, N] miles; not converted | 8 | kia/optima-k5 carmans-2016-kia-optima; kia/optima-k5 carmans-2018-kia-optima; kia/optima-k5 official-233e63cedbc5 |
| maintenance engine_air_filter | irregular list points [N, N] miles; not converted | 8 | kia/optima-k5 carmans-2016-kia-optima; kia/optima-k5 carmans-2018-kia-optima; kia/optima-k5 official-233e63cedbc5 |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N'] | 8 | kia/forte MY2019 (official-57b5f440c262); kia/rio MY2017 (mcum-rio-4-door-2017-2023); kia/rio MY2018 (mcum-rio-4-door-2017-2023) |
| maintenance spark_plugs | irregular list points [N, N] miles; not converted | 7 | kia/optima-k5 carmans-2016-kia-optima; kia/optima-k5 carmans-2018-kia-optima; kia/optima-k5 official-233e63cedbc5 |
| engine_oil_capacity_drain_refill_l | value N outside the validator range; not used | 6 | kia/optima-k5 carmans-2014-kia-optima p.390; kia/optima-k5 carmans-2015-kia-optima-hybrid p.390; kia/optima-k5 carmans-2015-kia-optima p.390 |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N] xN,N miles | 6 | kia/optima-k5 carmans-2023-kia-optima-incl-hybrid p.433; kia/forte carmans-2023-kia-forte p.439; kia/sorento official-c560f37de89a p.541 |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"'] | 5 | kia/optima-k5 MY2016 (carmans-2016-kia-optima); kia/optima-k5 MY2017 (official-233e63cedbc5); kia/sorento MY2016 (carmans-2016-kia-sorento) |
| coolant_capacity_l | value N outside the validator range; not used | 5 | kia/sorento official-c560f37de89a p.615; kia/sportage mcum-sportage-suv-2020 p.1080; kia/sportage mcum-sportage-suv-2020 p.1086 |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 4 | kia/optima-k5 TF/QF; kia/forte YD; kia/sorento UM |
| maintenance dct_fluid | irregular list points [N, N, N] miles; not converted | 4 | kia/optima-k5 carmans-2016-kia-optima; kia/optima-k5 carmans-2018-kia-optima; kia/optima-k5 official-233e63cedbc5 |
| maintenance cabin_air_filter | irregular list points [N, N, N, N, N] miles; not converted | 4 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15; kia/sorento carmans-2016-kia-sorento |
| maintenance spark_plugs | irregular list points [N, N, N] miles; not converted | 4 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15; kia/sorento carmans-2016-kia-sorento |
| maintenance tire_rotation | interval text not understood: Rotate every N,N km (N,N miles) | 3 | kia/forte carmans-2022-kia-forte p.419; kia/forte carmans-2022-kia-forte p.424; kia/sportage carmans-2023-kia-sportage p.455 |
| maintenance spark_plugs | interval text not understood: Replace every N,N km (N,N miles) | 3 | kia/forte carmans-2022-kia-forte p.419; kia/forte carmans-2022-kia-forte p.424; kia/sportage carmans-2023-kia-sportage p.455 |
| maintenance transmission_fluid | interval text not understood: No service required | 3 | kia/forte carmans-2022-kia-forte p.420; kia/forte carmans-2023-kia-forte p.435; kia/forte carmans-2023-kia-forte p.440 |
| fuel_tank_l | value N outside the validator range; not used | 3 | kia/sorento official-efccfd258f42 p.37; kia/sorento official-efccfd258f42 p.37; kia/sorento official-efccfd258f42 p.37 |
| maintenance engine_coolant | irregular list points [N, N, N, N] miles; not converted | 2 | kia/optima-k5 official-491f4bcda366; kia/optima-k5 official-21dfc1fbb981 |
| transmission_fluid_capacity_l | value N outside the validator range; not used | 2 | kia/forte carmans-2021-kia-forte p.668; kia/forte official-57b5f440c262 p.534 |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"'] | 2 | kia/forte MY2021 (carmans-2021-kia-forte); kia/rio MY2018 (carmans-2018-kia-rio) |
| maintenance engine_oil_and_filter | irregular list points [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N] miles; not converted | 2 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15 |
| maintenance exhaust_system | irregular list points [N, N, N, N, N] miles; not converted | 2 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15 |
| maintenance front_suspension | irregular list points [N, N, N, N, N] miles; not converted | 2 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15 |
| maintenance engine_air_filter | irregular list points [N, N, N] miles; not converted | 2 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15 |
| maintenance transmission_fluid | irregular list points [N, N, N] miles; not converted | 2 | kia/forte carmans-2017-kia-forte; kia/forte official-a69b14079d15 |
| maintenance accessory_drive_belt | interval text not understood: At first, inspect at N,N km (N,N miles) or N months, after that, inspect every N | 2 | kia/forte carmans-2022-kia-forte p.420; kia/forte carmans-2022-kia-forte p.425 |
| maintenance engine_oil_and_filter | irregular list points [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, N] miles; not converted | 2 | kia/forte official-d26795bd67b0; kia/forte official-a2412be5bad0 |
| maintenance engine_air_filter | irregular list points [N, N, N, N] miles; not converted | 2 | kia/forte official-d26795bd67b0; kia/forte official-a2412be5bad0 |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 2 | kia/sorento US2021+; kia/sportage US2023+ |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"'] | 2 | kia/sportage MY2020 (carmans-2020-kia-sportage); kia/sportage MY2021 (carmans-2021-kia-sportage) |
| maintenance brake_fluid | irregular I marks at [N, N, N, N, N, N, N, N, N, N, N, N] xN,N miles | 2 | kia/sportage carmans-2021-kia-sportage p.510; kia/sportage carmans-2021-kia-sportage p.515 |
| maintenance engine_coolant | irregular list points [N, N, N] miles; not converted | 1 | kia/optima-k5 carmans-2016-kia-optima |
| maintenance engine_coolant | interval text not understood: At first, replace at N,N km (N,N miles) or N years : after that, replace every N | 1 | kia/forte carmans-2022-kia-forte p.419 |
| maintenance engine_coolant | interval text not understood: At first, replace at N,N km (N,N miles) or N years, after that, replace every N, | 1 | kia/forte carmans-2022-kia-forte p.424 |
| engine_oil_capacity_l | no US owner's manual for these years | 1 | kia/sorento US2014-2015 |
| engine_oil_viscosity | no US owner's manual for these years | 1 | kia/sorento US2014-2015 |
| coolant | no US owner's manual for these years | 1 | kia/sorento US2014-2015 |
| transmission_fluid | no US owner's manual for these years | 1 | kia/sorento US2014-2015 |
| brake_fluid | no US owner's manual for these years | 1 | kia/sorento US2014-2015 |
| fuel_tank_l | no US owner's manual for these years | 1 | kia/sorento US2014-2015 |
| maintenance exhaust_system | irregular list points [N, N, N, N, N, N, N, N, N] miles; not converted | 1 | kia/sorento carmans-2018-kia-sorento |
| maintenance front_suspension | irregular list points [N, N, N, N, N, N, N, N, N] miles; not converted | 1 | kia/sorento carmans-2018-kia-sorento |
| maintenance transfer_case_fluid | irregular list points [N, N, N] miles; not converted | 1 | kia/sorento carmans-2018-kia-sorento |
| maintenance accessory_drive_belt | irregular list points [N, N, N, N, N] miles; not converted | 1 | kia/sorento carmans-2018-kia-sorento |
| transmission_fluid_capacity_l | one document gives N values: ['N', 'N', 'N'] | 1 | kia/sportage MY2020 (mcum-sportage-suv-2020) |
| maintenance brake_fluid | interval text not understood: Inspect every N,N km (N,N miles) or N months, Replace every N,N km (N,N miles) o | 1 | kia/sportage carmans-2023-kia-sportage p.455 |
| maintenance engine_coolant | interval text not understood: At first, replace at N,N km (N,N miles) or N months After that, replace every N, | 1 | kia/sportage carmans-2023-kia-sportage p.455 |
| maintenance differential_fluid | interval text not understood: Inspect every N,N km (N,N miles) or N months | 1 | kia/sportage carmans-2023-kia-sportage p.455 |

## 4. Конфликты источников

Конфликтов: 11. По решениям:

- model-year manual kept over the whole-generation page (Appendix E.6): 10
- official document kept over the copy: 1

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Rio | kia/rio US2014-2017 MY2015 | coolant_description | Ethylene glycol base coolant for aluminum radiator | ['Ethylene glycol base coolant for aluminum radiator; ethylene-glycol-based'] | official document kept over the copy |
| Rio | kia/rio US2014-2017 MY2017 | coolant_description | Ethylene glycol base coolant for aluminum radiator; ethylene-glycol-based | ['Ethylene-glycol with phosphate'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio US2014-2017 MY2017 | transmission_fluid | SP-IV | ['SP-CVT1'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio US2014-2017 MY2017 | fuel_tank_l | 43.0 | [45.0] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio SC MY2018 | transmission_fluid | SK ATF SP-IV | ['SP-CVT1'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio SC MY2019 | transmission_fluid | SP-IV | ['SP-CVT1'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio SC MY2019 | coolant_description | Ethylene-glycol with phosphate based coolant for cooling device | ['Ethylene-glycol with phosphate'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio SC MY2020 | coolant_description | Ethylene-glycol with phosphate based coolant for cooling device | ['Ethylene-glycol with phosphate'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Rio | kia/rio SC MY2021 | coolant_description | Ethylene-glycol with phosphate based coolant for cooling device | ['Ethylene-glycol with phosphate'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Sportage | kia/sportage US2014-2016 MY2016 | coolant_description | Ethylene glycol base coolant for aluminum radiator; phosphate based coolant to | ['Ethylene glycol base coolant for aluminum radiator'] | model-year manual kept over the whole-generation page (Appendix E.6) |
| Sportage | kia/sportage QL MY2020 | transmission_fluid | SK ATF SP-IV | ['SP-IV'] | model-year manual kept over the whole-generation page (Appendix E.6) |

## 5. Выборочная перепроверка

Проверено 181 записей (10% каждой линейки), расхождений 0.
- forte: 39 проверено, 0 расхождений
- optima-k5: 47 проверено, 0 расхождений
- rio: 19 проверено, 0 расхождений
- sorento: 35 проверено, 0 расхождений
- sportage: 41 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Optima / K5 JF (2016–2020): consumerreports.org: "Riding on an all-new chassis shared with the Hyundai Sonata, the redesigned 2016 Optima midsized sedan packs a lot of substance and value." (https://www.consumerreports.org/cars/kia/optima/); cars.com: "The 2016 redesign brought slightly updated styling, and the car was wider, 
- Optima / K5 DL3 (2021–2026): consumerreports.org: "The K5 replaces the Optima." (https://www.consumerreports.org/cars/kia/k5/); cars.com: "Kia retired the Optima name after the 2020 model year; the redesigned Kia mid-size sedan that debuted for 2021 was named the K5." (https://www.cars.com/research/kia-optima/) [media: generati
- Forte BD (2019–2024): consumerreports.org: "The Forte was discontinued and replaced by the new K4 for 2025." (https://www.consumerreports.org/cars/kia/forte/); cars.com: "2019-2024" (https://www.cars.com/research/kia-forte/) [quote read once] [media: generation starts MY2019]
- Rio SC (2018–2023): consumerreports.org: "With its all-new platform, the fourth-generation Rio sedan and hatchback sit lower, wider, and slightly longer than before." (https://www.consumerreports.org/cars/kia/rio/); cars.com: "Redesigned for 2018 on new platform" (https://www.cars.com/research/kia-rio/) [media: generat
- Sorento UM (2016–2020): consumerreports.org: "Redesigned for 2016, the Sorento is slightly larger than before but still remains right-sized" (https://www.consumerreports.org/cars/kia/sorento/); cars.com: "The Sorento received a full redesign for the 2016 model year" (https://www.cars.com/research/kia-sorento/) [media: gene
- Sorento US2021+ (2021–2026): consumerreports.org: "Kia redesigned its Sorento SUV for 2021, with new engines and an available hybrid version." (https://www.consumerreports.org/cars/kia/sorento/); cars.com: "The Sorento got a clean-sheet redesign for 2021" (https://www.cars.com/research/kia-sorento/) [media: generation starts MY
- Sportage QL (2017–2022): consumerreports.org: "The redesigned Sportage is a stylish and mildly sporty choice among small SUVs." (https://www.consumerreports.org/cars/kia/sportage/); cars.com: "Completely redesigned for 2017" (https://www.cars.com/research/kia-sportage/) [media: generation starts MY2017]
- Sportage US2023+ (2023–2026): consumerreports.org: "The redesigned 2023 Sportage is larger and better equipped than the previous model." (https://www.consumerreports.org/cars/kia/sportage/); cars.com: "Redesigned for 2023" (https://www.cars.com/research/kia-sportage/) [media: generation starts MY2023]

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- kia/optima-k5: --prune-stale, код 0, {"raw_documents_seen": 91, "te_existing": 1032, "configurations": 48, "configurations_research_only": 48, "issues_existing": 71, "maintenance_existing": 216}
- kia/forte: --prune-stale, код 0, {"raw_documents_seen": 62, "te_existing": 949, "configurations": 45, "configurations_research_only": 45, "issues_existing": 45, "maintenance_existing": 135}
- kia/rio: --prune-stale, код 0, {"raw_documents_seen": 49, "source_records_new": 2, "te_existing": 373, "te_new_GENERATION": 2, "configurations": 16, "configurations_research_only": 13, "configurations_linked": 3, "issues_existing": 17, "maintenance_existing": 36}
- kia/sorento: --prune-stale, код 0, {"raw_documents_seen": 84, "source_records_new": 3, "te_existing": 1259, "te_new_GENERATION": 3, "configurations": 75, "configurations_research_only": 75, "issues_existing": 85, "maintenance_existing": 69}
- kia/sportage: --prune-stale, код 0, {"raw_documents_seen": 80, "source_records_new": 2, "te_existing": 972, "te_new_GENERATION": 2, "configurations": 58, "configurations_research_only": 58, "issues_existing": 47, "maintenance_existing": 183}
