# Jeep — отчёт по базе технических данных US

Сформировано 2026-10-03T18:00:06+00:00 скриптом scripts/build_us_report.py.

**Статус:** Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/jeep/staging), в рабочей БД строк этого конвейера нет.

## Подготовлено, но не записано в БД

- линеек: 3
- поколений: 6
- конфигураций: 179
- фактов: 554
- отзывов: 137
- проблем: 244
- пунктов ТО: 316

## Журнал пробелов подготовленных данных

Записей в журнале пробелов: 394 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 179 | jeep-grand-cherokee-us-2014-3.0l-6cyl-turbo-diesel-a-8-spd-4wd; jeep-grand-cherokee-us-2014-3.0l-6cyl-turbo-diesel-a-8-spd-rwd; jeep-grand-cherokee-us-2014-3.6l-6cyl-ice-a-8-spd-4wd |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 28 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2021 (official-279827ad7254) |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 22 | jeep/grand-cherokee MY2017 (official-0c5d0982e5de); jeep/grand-cherokee MY2018 (official-285834fb39dc); jeep/grand-cherokee MY2016 (official-4a36beb37f33) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 21 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2024 (official-2ddeb9fed3d8); jeep/grand-cherokee MY2023 (official-3e8401906661) |
| fuel_tank_l | value N outside the validator range; not used | 16 | jeep/grand-cherokee official-e9e755a7eaad p.531; jeep/cherokee official-0198a6663aac p.341; jeep/cherokee official-0198a6663aac p.341 |
| octane_aki | one document gives N values: ['N', 'N'] | 15 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2017 (official-0c5d0982e5de); jeep/grand-cherokee MY2021 (official-279827ad7254) |
| engine_oil_specification | engine not stated; EPA lists several engines | 12 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2024 (official-2ddeb9fed3d8); jeep/grand-cherokee MY2023 (official-3e8401906661) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 9 | jeep/grand-cherokee MY2018 (official-285834fb39dc); jeep/grand-cherokee MY2016 (official-4a36beb37f33); jeep/grand-cherokee MY2016 (official-aab479b0d08e) |
| maintenance transfer_case_fluid | irregular points [N, N, N, N] in the official schedule; not converted | 9 | jeep/grand-cherokee MY2017; jeep/grand-cherokee MY2017; jeep/grand-cherokee MY2018 |
| engine_oil_capacity_l | one document gives N values: ['N', 'N'] | 7 | jeep/grand-cherokee MY2018 (official-285834fb39dc); jeep/grand-cherokee MY2019 (official-c0affd9b4982); jeep/cherokee MY2014 (official-0198a6663aac) |
| power_hp | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| torque_lb_ft | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| tires | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| front_suspension | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| rear_suspension | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| front_brakes | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| steering | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| ground_clearance | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| cargo_l | no US press specification page for these years | 6 | jeep/grand-cherokee WK-2011; jeep/grand-cherokee US2022+; jeep/cherokee KL |
| coolant_capacity_l | engine not stated; EPA lists several engines | 3 | jeep/grand-cherokee MY2016 (official-4a36beb37f33); jeep/grand-cherokee MY2016 (official-aab479b0d08e); jeep/grand-cherokee MY2014 (official-b0b53935c6be) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 3 | jeep/grand-cherokee MY2016 (official-4a36beb37f33); jeep/grand-cherokee MY2016 (official-aab479b0d08e); jeep/grand-cherokee MY2014 (official-b0b53935c6be) |
| coolant_capacity_l | one document gives N values: ['N', 'N', 'N'] | 2 | jeep/grand-cherokee MY2017 (official-0c5d0982e5de); jeep/cherokee MY2019 (official-6ba1a11cd3f1) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 2 | jeep/grand-cherokee MY2024 (official-2ddeb9fed3d8); jeep/grand-cherokee MY2026 (official-e9d6ee5e937d) |
| coolant | not found unambiguously in the available US owner's manuals | 2 | jeep/grand-cherokee US2022+; jeep/cherokee US2026+ |
| brake_fluid | one document gives N values: ['"DOT N. If DOT N"', '"DOT N"'] | 2 | jeep/compass MY2018 (official-5175e72ae08e); jeep/compass MY2017 (official-aa9675841b2a) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N, SAE JN brake fluid is not available, then DOT N"'] | 1 | jeep/grand-cherokee MY2017 (official-5662e979cd35) |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 1 | jeep/grand-cherokee MY2015 (official-e9e755a7eaad) |
| brake_fluid | one document gives N values: ['"DOT N Brake Fluid, SAE JN should be used. If DOT N"', '"DOT N"'] | 1 | jeep/cherokee MY2020 (official-4a59cbf55e4f) |
| engine_oil_capacity_l | one document gives N values: ['N', 'N', 'N'] | 1 | jeep/cherokee MY2019 (official-6ba1a11cd3f1) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 1 | jeep/cherokee US2026+ |
| maintenance accessory_drive_belt | irregular points [] in the official schedule; not converted | 1 | jeep/cherokee MY2019 |
| coolant_capacity_l | value N outside the validator range; not used | 1 | jeep/compass official-7c0929791243 p.76 |
| brake_fluid | not found unambiguously in the available US owner's manuals | 1 | jeep/compass MK |
