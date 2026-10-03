# Mitsubishi — отчёт по базе технических данных US

Сформировано 2026-10-03T20:46:07+00:00 скриптом scripts/build_us_report.py.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль).

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Outlander | III | 2014–2021 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| Outlander | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ● | ○ | ◐ | ◐ | ● | ● | ● |
| Outlander Sport | I-US-2011 | 2014–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 27, частично 10, нет 8, неприменимо 0.

## 2. Строки до и после

| Таблица | До пакета | После |
|---|---|---|
| technical_evidence | 0 | 1805 |
| known_issues | 0 | 64 |
| maintenance_schedule_items | 0 | 584 |

## 3. Журнал пробелов

Записей в журнале пробелов: 178 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 91 | mitsubishi-outlander-us-2014-2.4l-4cyl-ice-a-av-s6-4wd; mitsubishi-outlander-us-2014-2.4l-4cyl-ice-a-av-s6-fwd; mitsubishi-outlander-us-2014-3.0l-6cyl-ice-a-s6-4wd |
| compression_ratio | engine not stated; EPA lists several engines | 9 | mitsubishi/outlander MY2014 (press-mitsubishicars-outlander-2014-9977ec18); mitsubishi/outlander MY2015 (press-mitsubishicars-outlander-2015-63bc5400); mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 4 | mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 4 | mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| power_hp | engine not stated; EPA lists several engines | 4 | mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| power_rpm | engine not stated; EPA lists several engines | 4 | mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| torque_lb_ft | engine not stated; EPA lists several engines | 4 | mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| torque_rpm | engine not stated; EPA lists several engines | 4 | mitsubishi/outlander MY2016 (press-mitsubishicars-outlander-2016-f78b1cd9); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| cargo_l | one document gives N values: ['N', 'N'] | 4 | mitsubishi/outlander MY2019 (press-mitsubishicars-outlander-2019-13f3de32); mitsubishi/outlander MY2019 (press-mitsubishicars-outlander-2019-13f3de32); mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97) |
| maintenance:fuel_filter | p.N schedule N: 'Check fuel filter*N': footnote: Periodic maintenance is not required. | 4 | mitsubishi/outlander MY2022 (mitsubishi-wm-2022-2022-mitsubishi-warranty-outlander); mitsubishi/outlander MY2022 (mitsubishi-wm-2022-2022-mitsubishi-warranty-outlander); mitsubishi/outlander MY2023 (mitsubishi-wm-2023-2023-outlander) |
| maintenance:valve_clearance | p.N schedule N: 'Inspect intake & exhaust valve clearance*N,*N': footnote: Periodic maintenance is not require | 4 | mitsubishi/outlander MY2022 (mitsubishi-wm-2022-2022-mitsubishi-warranty-outlander); mitsubishi/outlander MY2022 (mitsubishi-wm-2022-2022-mitsubishi-warranty-outlander); mitsubishi/outlander MY2023 (mitsubishi-wm-2023-2023-outlander) |
| maintenance:schedule (Outlander (gasoline)) | no US booklet on disk (salesforce copies disallowed by robots.txt) | 4 | mitsubishi/outlander MY2017; mitsubishi/outlander MY2018; mitsubishi/outlander MY2024 |
| maintenance:schedule (Outlander Sport) | no US booklet on disk (salesforce copies disallowed by robots.txt) | 4 | mitsubishi/outlander-sport MY2017; mitsubishi/outlander-sport MY2018; mitsubishi/outlander-sport MY2024 |
| electric_motor | one document gives N values: ['"N Nm"', '"N Nm"', '"NkW"', '"YN"'] | 3 | mitsubishi/outlander MY2018 (press-mitsubishicars-outlander-2018-60aa5cd7); mitsubishi/outlander MY2019 (press-mitsubishicars-outlander-2019-e8987408); mitsubishi/outlander MY2020 (press-mitsubishicars-outlander-2020-edf3c303) |
| engine_oil_capacity_l | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| engine_oil_viscosity | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| coolant | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| transmission_fluid | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| brake_fluid | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| maintenance:schedule (Outlander PHEV) | no US booklet on disk (salesforce copies disallowed by robots.txt) | 3 | mitsubishi/outlander MY2019; mitsubishi/outlander MY2024; mitsubishi/outlander MY2025 |
| engine_description | engine not stated; EPA lists several engines | 2 | mitsubishi/outlander MY2025 (press-mitsubishicars-outlander-2025-d0103e97); mitsubishi/outlander MY2026 (press-mitsubishicars-outlander-2026-7dbda758) |
| maintenance:schedule (Outlander (gasoline)) | no US booklet on disk (none listed in the manifests) | 2 | mitsubishi/outlander MY2021; mitsubishi/outlander MY2026 |
| electric_motor | one document gives N values: ['"N Nm"', '"N Nm"', '"NkW"', '"NkW"', '"YN"'] | 1 | mitsubishi/outlander MY2021 (press-mitsubishicars-outlander-2021-72c5fabb) |
| power_hp | not found unambiguously in the available US press specification pages | 1 | mitsubishi/outlander US2022+ |
| torque_lb_ft | not found unambiguously in the available US press specification pages | 1 | mitsubishi/outlander US2022+ |
| tires | not found unambiguously in the available US press specification pages | 1 | mitsubishi/outlander US2022+ |
| front_brakes | not found unambiguously in the available US press specification pages | 1 | mitsubishi/outlander US2022+ |
| steering | not found unambiguously in the available US press specification pages | 1 | mitsubishi/outlander US2022+ |
| cargo_l | not found unambiguously in the available US press specification pages | 1 | mitsubishi/outlander US2022+ |
| generation_boundaries | no vPIC Canadian specification rows for this line; boundaries from DB codes only | 1 | mitsubishi/outlander-sport |
| maintenance:schedule (Outlander Sport) | no US booklet on disk (none listed in the manifests) | 1 | mitsubishi/outlander-sport MY2026 |

## 4. Конфликты источников

Конфликтов: 18. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 18

| Линейка | Область | Поле | Оставлено | Другие значения | Решение |
|---|---|---|---|---|---|
| Outlander | mitsubishi/outlander III MY2015 | width_mm | [1811.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2015 | width_mm | [1811.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2020 | curb_weight_kg | [1915.0] | [1545] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2021 | curb_weight_kg | [1916.0] | [1545] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2018 | height_mm | [1709.0] | [1680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2016 | length_mm | [4694.0] | [4660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2016 | length_mm | [4694.0] | [4660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2015 | width_mm | [1811.0] | [1800] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2020 | curb_weight_kg | [1915.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2021 | curb_weight_kg | [1916.0] | [1610] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2018 | height_mm | [1709.0] | [1680] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander III MY2016 | length_mm | [4694.0] | [4660] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander US2022+ MY2025 | width_mm | [1897.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander US2022+ MY2026 | width_mm | [1897.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander US2022+ MY2025 | curb_weight_kg | [1725.0] | [2090] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander US2022+ MY2026 | curb_weight_kg | [1710.0] | [2090] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander US2022+ MY2025 | width_mm | [1897.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |
| Outlander | mitsubishi/outlander US2022+ MY2026 | width_mm | [1897.0] | [1860] | official value is the main value; the vPIC Canadian value stays a SECONDARY note (section 5.2) |

## 5. Выборочная перепроверка

Проверено 132 записей (10% каждой линейки), расхождений 0.
- outlander: 84 проверено, 0 расхождений
- outlander-sport: 48 проверено, 0 расхождений

## Поколения: свидетельства прессы и решения детектора

- Outlander US2022+ (2022–2026): consumerreports.org: "The seven-passenger Outlander is fully redesigned for 2022." (https://www.consumerreports.org/cars/mitsubishi/outlander/); cars.com: "An all-new platform transforms the 2022 Mitsubishi Outlander from a quirky, dated entry in the compact crossover field to a sophisticated, techn
- Outlander: MY2016: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "2016 Model Redesign Year" (https://www.consumerreports.org/cars/mitsubishi/outlander/) [media: weak])
- Outlander Sport: MY2015: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "This aging small SUV is a shortened version of the previous-generation Outlander" (https://www.consumerreports.org/cars/mitsubishi/outlander-sport/) [media: weak])

## Изменения ранее записанных строк (последняя загрузка)

- нет

## Загрузка

Режим: live, quick_check: ok, нарушений FK: 0, полностью перезагружены: []
- mitsubishi/outlander: --prune-stale, код 0, {"raw_documents_seen": 78, "source_records_new": 73, "te_new_GENERATION": 473, "te_new_ENGINE": 18, "te_new_CONFIGURATION": 440, "configurations": 40, "configurations_research_only": 38, "configurations_linked": 2, "issues_new": 40, "maintenance_new": 411}
- mitsubishi/outlander-sport: --prune-stale, код 0, {"raw_documents_seen": 48, "source_records_new": 39, "te_new_ENGINE": 8, "te_new_GENERATION": 305, "te_new_CONFIGURATION": 561, "configurations": 51, "configurations_research_only": 50, "configurations_linked": 1, "issues_new": 24, "maintenance_new": 173}
