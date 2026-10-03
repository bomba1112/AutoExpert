# Jeep — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Grand Cherokee | WK-2011 | 2014–2021 | ◐ | ◐ | ● | ● | ○ | ● | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Grand Cherokee | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ○ | ● | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Cherokee | KL | 2014–2023 | ◐ | ◐ | ● | ● | ○ | ● | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |
| Cherokee | US2026+ | 2026–2026 | ◐ | ◐ | ● | ● | ○ | ● | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Compass | MK | 2014–2016 | ◐ | ◐ | ● | ● | ○ | ● | ● | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| Compass | MP | 2017–2026 | ◐ | ◐ | ● | ● | ○ | ● | ● | ● | ● | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 51, частично 21, нет 18, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 3887 |
| known_issues | 0 | 244 |
| maintenance_schedule_items | 0 | 451 |

## 3. Журнал пробелов

Записей в журнале пробелов: 410 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 179 | jeep-grand-cherokee-us-2014-3.0l-6cyl-turbo-diesel-a-8-spd-4wd; jeep-grand-cherokee-us-2014-3.0l-6cyl-turbo-diesel-a-8-spd-rwd; jeep-grand-cherokee-us-2014-3.6l-6cyl-ice-a-8-spd-4wd |
| coolant_capacity_l | one document gives N values: ['N', 'N'] | 28 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2021 (official-279827ad7254) |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 22 | jeep/grand-cherokee MY2017 (official-0c5d0982e5de); jeep/grand-cherokee MY2018 (official-285834fb39dc); jeep/grand-cherokee MY2016 (official-4a36beb37f33) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 21 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2024 (official-2ddeb9fed3d8); jeep/grand-cherokee MY2023 (official-3e8401906661) |
| octane_aki | one document gives N values: ['N', 'N'] | 15 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2017 (official-0c5d0982e5de); jeep/grand-cherokee MY2021 (official-279827ad7254) |
| fuel_tank_l | value N outside the validator range; not used | 12 | jeep/grand-cherokee official-e9e755a7eaad p.531; jeep/cherokee official-0198a6663aac p.341; jeep/cherokee official-0198a6663aac p.341 |
| engine_oil_specification | engine not stated; EPA lists several engines | 12 | jeep/grand-cherokee MY2022 (official-0a8be9d59112); jeep/grand-cherokee MY2024 (official-2ddeb9fed3d8); jeep/grand-cherokee MY2023 (official-3e8401906661) |
| brake_fluid | one document gives N values: ['"DOT N"', '"DOT N"'] | 12 | jeep/grand-cherokee MY2018 (official-285834fb39dc); jeep/grand-cherokee MY2016 (official-4a36beb37f33); jeep/grand-cherokee MY2016 (official-aab479b0d08e) |
| maintenance transfer_case_fluid | irregular points [N, N, N, N] in the official schedule; not converted | 9 | jeep/grand-cherokee MY2017; jeep/grand-cherokee MY2017; jeep/grand-cherokee MY2018 |
| maintenance:tire_rotation | rotate the tires at every oil change indicated by the oil change indicator system; no fixed interval printed | 9 | jeep/grand-cherokee MY2014 (jeep-grand-cherokee-2014-owner-manual); jeep/grand-cherokee MY2015 (jeep-grand-cherokee-2015-owner-manual); jeep/grand-cherokee MY2016 (jeep-grand-cherokee-2016-owner-manual) |
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
| coolant_capacity_l | value N outside the validator range; not used | 4 | jeep/compass official-5175e72ae08e p.416; jeep/compass official-7c0929791243 p.76; jeep/compass official-aa9675841b2a p.274 |
| coolant_capacity_l | engine not stated; EPA lists several engines | 3 | jeep/grand-cherokee MY2016 (official-4a36beb37f33); jeep/grand-cherokee MY2016 (official-aab479b0d08e); jeep/grand-cherokee MY2014 (official-b0b53935c6be) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 3 | jeep/grand-cherokee MY2016 (official-4a36beb37f33); jeep/grand-cherokee MY2016 (official-aab479b0d08e); jeep/grand-cherokee MY2014 (official-b0b53935c6be) |
| maintenance:transfer_case_fluid | p.N 'Inspect transfer case fluid.': marks at [N, N, N, N] miles do not form a regular interval; not converted | 3 | jeep/grand-cherokee MY2014 (jeep-grand-cherokee-2014-owner-manual); jeep/grand-cherokee MY2015 (jeep-grand-cherokee-2015-owner-manual); jeep/grand-cherokee MY2016 (jeep-grand-cherokee-2016-owner-manual) |
| engine_oil_capacity_l | value N outside the validator range; not used | 3 | jeep/compass official-5175e72ae08e p.416; jeep/compass official-aa9675841b2a p.274; jeep/compass official-c7dd3a917dfe p.450 |
| coolant_capacity_l | one document gives N values: ['N', 'N', 'N'] | 2 | jeep/grand-cherokee MY2017 (official-0c5d0982e5de); jeep/cherokee MY2019 (official-6ba1a11cd3f1) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 2 | jeep/grand-cherokee MY2024 (official-2ddeb9fed3d8); jeep/grand-cherokee MY2026 (official-e9d6ee5e937d) |
| coolant | not found unambiguously in the available US owner's manuals | 2 | jeep/grand-cherokee US2022+; jeep/cherokee US2026+ |
| brake_fluid | one document gives N values: ['"DOT N or DOT N"', '"DOT N"'] | 1 | jeep/grand-cherokee MY2017 (official-5662e979cd35) |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 1 | jeep/grand-cherokee MY2015 (official-e9e755a7eaad) |
| maintenance:schedule | 'N Jeep Grand Cherokee SRT - SRT Owner Manual' listed in the manifest but not on disk (status error) | 1 | jeep/grand-cherokee MY2015 |
| engine_oil_capacity_l | one document gives N values: ['N', 'N', 'N'] | 1 | jeep/cherokee MY2019 (official-6ba1a11cd3f1) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 1 | jeep/cherokee US2026+ |
| maintenance accessory_drive_belt | irregular points [] in the official schedule; not converted | 1 | jeep/cherokee MY2019 |
| maintenance spark_plugs NORMAL EVERY | schedules of the same edition give different intervals (N mi / None mo in N Jeep Cherokee - Maintenance Schedu | 1 | jeep/cherokee MY2019 |
| brake_fluid | not found unambiguously in the available US owner's manuals | 1 | jeep/compass MK |

## 4. Конфликты источников

Конфликтов: 8. По решениям:

- sources of the same rank disagree; field not shown: 8

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Grand Cherokee | jeep/grand-cherokee US2022+ MY2022 | fuel_tank_l | None | [87.0, 93.1] | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee US2022+ MY2022 | engine_oil_capacity_l | None | [4.7, 5.6] | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee US2022+ MY2022 | transmission_fluid | None | ['Mopar® ATF+4 Automatic Transmi', 'Mopar® ATF+4 Automatic Transmi; Mopar® ZF 8  | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee WK-2011 MY2021 | fuel_tank_l | None | [93.1, 87.0] | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee WK-2011 MY2021 | engine_oil_capacity_l | None | [5.6, 4.7] | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee WK-2011 MY2017 | coolant | None | ['Mopar Antifreeze/Coolant 10', 'Mopar Antifreeze/Coolant 10 Year/150'] | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee WK-2011 MY2016 | coolant | None | ['MOPAR Antifreeze/Coolant 10 Year/150', 'MOPAR Antifreeze/Coolant 10 Year/'] | sources of the same rank disagree; field not shown |
| Grand Cherokee | jeep/grand-cherokee WK-2011 MY2019 | coolant | None | ['Mopar Antifreeze/Coolant', 'Mopar Antifreeze/Coolant 10'] | sources of the same rank disagree; field not shown |

## 5. Выборочная перепроверка

Проверено 133 записей (10% каждой линейки), расхождений 0.
- cherokee: 25 проверено, 0 расхождений
- compass: 25 проверено, 0 расхождений
- grand-cherokee: 83 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Grand Cherokee US2022+ (2022–2026): consumerreports.org: "The 2022 redesigned Grand Cherokee is slightly larger than the previous version." (https://www.consumerreports.org/cars/jeep/grand-cherokee/) [media: generation starts MY2022]
- Grand Cherokee: media give different first model years [2021, 2022] for one generation; MY2022 used
- Cherokee US2026+ (2026–2026): consumerreports.org: "The Cherokee returns after a brief hiatus, now packaged exclusively as a hybrid." (https://www.consumerreports.org/cars/jeep/cherokee/); cars.com: "an all-new generation debuted for 2026 on a notably larger platform" (https://www.cars.com/research/jeep-cherokee/) [media: genera
- Compass MP (2017–2026): consumerreports.org: "2017 Model Redesign Year" (https://www.consumerreports.org/cars/jeep/compass/); cars.com: "All-new five-passenger compact SUV" (https://www.cars.com/research/jeep-compass/) [media: generation starts MY2017]
- Compass: boundary moved from MY2018 to the media-stated MY2017
- Compass: MY2015: detected boundary (vPIC Canadian specifications: wheelbase 264 cm (MY2014) -> 263 cm (MY2015), with overall length 441 -> 445 cm) dropped; consumerreports.org: "2007 Model Redesign Year" (https://www.consumerreports.org/cars/jeep/compass/) [media: generation started MY2007], next starts MY20

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- jeep/grand-cherokee: --prune-stale, код 0, {"raw_documents_seen": 138, "source_records_new": 133, "te_new_GENERATION": 915, "te_new_CONFIGURATION": 820, "configurations": 68, "configurations_research_only": 53, "configurations_linked": 15, "issues_new": 115, "maintenance_new": 356}
- jeep/cherokee: --prune-stale, код 0, {"raw_documents_seen": 67, "source_records_new": 51, "te_new_GENERATION": 394, "te_new_CONFIGURATION": 761, "configurations": 59, "configurations_research_only": 59, "issues_new": 71, "maintenance_new": 42}
- jeep/compass: --prune-stale, код 0, {"raw_documents_seen": 71, "source_records_new": 53, "te_new_GENERATION": 421, "te_new_CONFIGURATION": 576, "configurations": 52, "configurations_linked": 11, "configurations_research_only": 41, "issues_new": 58, "maintenance_new": 53}
