# Cadillac — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

**Статус:** Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/cadillac/staging), в рабочей БД строк этого конвейера нет.

## Подготовлено, но не записано в БД

- линеек: 3
- поколений: 5
- конфигураций: 87
- фактов: 390
- отзывов: 47
- проблем: 151
- пунктов ТО: 0

## Журнал пробелов подготовленных данных

Записей в журнале пробелов: 261 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 87 | cadillac-cts-us-2014-2.0l-4cyl-turbo-ice-a-s6-awd; cadillac-cts-us-2014-2.0l-4cyl-turbo-ice-a-s6-rwd; cadillac-cts-us-2014-3.0l-6cyl-ice-a-s6-awd |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 22 | cadillac/cts MY2014 (carmans-2014-cadillac-cts); cadillac/cts MY2015 (carmans-2015-cadillac-cts); cadillac/cts MY2016 (carmans-2016-cadillac-cts) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 21 | cadillac/escalade MY2014 (carmans-2014-cadillac-escalade-esv); cadillac/escalade MY2015 (carmans-2015-cadillac-escalade); cadillac/escalade MY2016 (carmans-2016-cadillac-escalade) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 16 | cadillac/cts MY2014 (carmans-2014-cadillac-cts); cadillac/cts MY2015 (carmans-2015-cadillac-cts); cadillac/cts MY2016 (carmans-2016-cadillac-cts) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 13 | cadillac/cts MY2014 (carmans-2014-cadillac-cts); cadillac/cts MY2015 (carmans-2015-cadillac-cts); cadillac/cts MY2016 (carmans-2016-cadillac-cts) |
| coolant_capacity_l | value N outside the validator range; not used | 10 | cadillac/cts carmans-2018-cadillac-cts p.354; cadillac/cts carmans-2018-cadillac-cts p.354; cadillac/cts carmans-2019-cadillac-cts p.360 |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 8 | cadillac/cts MY2018 (carmans-2018-cadillac-cts); cadillac/cts MY2019 (carmans-2019-cadillac-cts); cadillac/cts MY2019 (official-52554d6eb793) |
| engine_oil_capacity_l | one document gives N values: ['N', 'N'] | 5 | cadillac/cts MY2017 (carmans-2017-cadillac-cts); cadillac/cts MY2018 (carmans-2018-cadillac-cts); cadillac/cts MY2016 (official-7001f7da5e90) |
| fuel_tank_l | value N outside the validator range; not used | 5 | cadillac/escalade carmans-2014-cadillac-escalade-esv p.339; cadillac/escalade official-2d17cb7dff62 p.438; cadillac/escalade official-2d17cb7dff62 p.438 |
| coolant | not found unambiguously in the available US owner's manuals | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade IV |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| power_hp | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| torque_lb_ft | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| tires | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| front_suspension | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| rear_suspension | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| front_brakes | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| steering | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| ground_clearance | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| cargo_l | no US press specification page for these years | 4 | cadillac/cts III; cadillac/srx 2010-REDESIGN; cadillac/escalade US2014-2014 |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"', '"SAE NW-N"'] | 4 | cadillac/srx MY2014 (carmans-2014-cadillac-srx); cadillac/srx MY2014 (official-45f6ad75f1af); cadillac/escalade MY2014 (carmans-2014-cadillac-escalade-esv) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 3 | cadillac/cts MY2015 (official-8c19775c4259); cadillac/escalade MY2021 (carmans-2021-cadillac-escalade); cadillac/escalade MY2022 (carmans-2022-cadillac-escalade) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 3 | cadillac/cts MY2015 (official-8c19775c4259); cadillac/escalade MY2021 (carmans-2021-cadillac-escalade); cadillac/escalade MY2022 (carmans-2022-cadillac-escalade) |
| engine_oil_viscosity | one document gives N values: ['"SAE NW-N"', '"SAE NW-N"'] | 3 | cadillac/escalade MY2023 (carmans-2023-cadillac-escalade); cadillac/escalade MY2024 (carmans-2024-cadillac-escalade); cadillac/escalade MY2026 (official-860a324b5114) |
| octane_aki | one document gives N values: ['N', 'N'] | 2 | cadillac/cts MY2019 (carmans-2019-cadillac-cts); cadillac/cts MY2019 (official-52554d6eb793) |
| engine_oil_viscosity | not found unambiguously in the available US owner's manuals | 2 | cadillac/cts III; cadillac/escalade US2014-2014 |
| cargo_max_l | value N outside the validator range; not used | 2 | cadillac/escalade press-newsgm-escalade-2025-bf4f01fd p.1; cadillac/escalade press-newsgm-escalade-2025-bf4f01fd p.1 |
| coolant_capacity_l | one document gives N values: ['N', 'N', 'N'] | 2 | cadillac/escalade MY2023 (carmans-2023-cadillac-escalade); cadillac/escalade MY2024 (carmans-2024-cadillac-escalade) |
| cargo_l | one document gives N values: ['N', 'N'] | 2 | cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd); cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd) |
| fuel_tank_l | not found unambiguously in the available US owner's manuals | 2 | cadillac/escalade US2014-2014; cadillac/escalade IV |
| wheel_size_in | one document gives N values: ['N', 'N'] | 1 | cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 1 | cadillac/escalade MY2025 (press-newsgm-escalade-2025-bf4f01fd) |
| front_brakes | not found unambiguously in the available US press specification pages | 1 | cadillac/escalade US2021+ |
| ground_clearance | not found unambiguously in the available US press specification pages | 1 | cadillac/escalade US2021+ |
| cargo_l | not found unambiguously in the available US press specification pages | 1 | cadillac/escalade US2021+ |
