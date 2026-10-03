### Точность Teoalida

| Источник | Поле | Сравнено | Совпало | Расходится | Нет официального | Совпадение | Решение |
|---|---|---:|---:|---:|---:|---:|---|
| Ravenol (масла и жидкости) | engine_code (family, first 3 characters) | 5 | 5 | 0 | 115 | 100% | записано (SECONDARY_NOTE) |
| Ravenol (масла и жидкости) | transmission_code (gear count vs EPA transmission) | 103 | 103 | 0 | 0 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | cargo_l | 50 | 39 | 11 | 138 | 78% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | cargo_max_l | 15 | 10 | 5 | 19 | 67% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | curb_weight_kg | 80 | 77 | 3 | 114 | 96% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | cylinders | 164 | 162 | 2 | 31 | 99% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | drivetrain | 164 | 164 | 0 | 31 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | engine_displacement_l | 164 | 164 | 0 | 31 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | epa_combined_mpg | 164 | 142 | 22 | 31 | 87% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | fuel_tank_l | 68 | 58 | 10 | 127 | 85% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | fuel_type (class vs EPA) | 164 | 164 | 0 | 31 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | ground_clearance | 49 | 49 | 0 | 133 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | height_mm | 50 | 49 | 1 | 145 | 98% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | length_mm | 89 | 86 | 3 | 106 | 97% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | platform_code | 71 | 60 | 11 | 124 | 84% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | power_hp | 12 | 11 | 1 | 84 | 92% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | power_rpm | 9 | 9 | 0 | 87 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | seats | 84 | 84 | 0 | 111 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | system_power_hp | 53 | 53 | 0 | 46 | 100% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | torque_lb_ft | 18 | 15 | 3 | 96 | 83% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | torque_rpm | 14 | 13 | 1 | 91 | 93% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | track_front_mm | 1 | 1 | 0 | 18 | 100% | не измеримо (меньше 5 сравнений) — не записано |
| Year-Make-Model-Trim-Specs (US) | track_rear_mm | 1 | 1 | 0 | 18 | 100% | не измеримо (меньше 5 сравнений) — не записано |
| Year-Make-Model-Trim-Specs (US) | transmission (gear count vs EPA) | 92 | 87 | 5 | 17 | 95% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | turning_circle_m | 34 | 27 | 7 | 158 | 79% | ниже 90% — не записано |
| Year-Make-Model-Trim-Specs (US) | wheelbase_mm | 103 | 99 | 4 | 92 | 96% | записано (SECONDARY_NOTE) |
| Year-Make-Model-Trim-Specs (US) | width_mm | 79 | 78 | 1 | 116 | 99% | записано (SECONDARY_NOTE) |
| TireSize | tires | 19 | 15 | 4 | 34 | 79% | ниже 90% — не записано |
| Year-Make-Model (коды платформ) | platform_code | 20 | 20 | 0 | 0 | 100% | записано (SECONDARY_NOTE) |
| Car Models List (коды платформ) | platform_code | 31 | 31 | 0 | 0 | 100% | записано (SECONDARY_NOTE) |
| Tuning (только сравнение) | power_hp (EU tuning 'standard' vs our official) | 3 | 0 | 3 | 0 | 0% | не измеримо (меньше 5 сравнений) — не записано |

### Поля без пересечения с официальными данными

- Ravenol (масла и жидкости): coolant_capacity_l, engine_oil_capacity_l, front_differential_fluid_capacity_l, interval automatic_transmission_fluid replace, interval brake_fluid replace, interval coolant inspect, interval engine_oil_and_filter replace, interval rear_differential_fluid replace, manual_transmission_fluid_capacity_l, rear_differential_fluid_capacity_l, transfer_case_fluid_capacity_l, transmission_fluid_capacity_l
- Year-Make-Model-Trim-Specs (US): acceleration_0_60_mph_s, cam_type, charge_time_240v_h, drag_coefficient, engine_type, epa_combined_mpge, epa_electric_range_km, epa_kwh_per_100mi, fast_charge_port, front_head_room_mm, front_hip_room_mm, front_leg_room_mm, front_shoulder_room_mm, gross_weight_kg, interior_volume_l, nhtsa_overall_rating, payload_kg, rear_head_room_mm, rear_hip_room_mm, rear_leg_room_mm, rear_shoulder_room_mm, safety_features, suspension_features, tires_wheels_features, valve_timing, valves

### Записано из Teoalida

| Файл Teoalida (ключ источника) | Поле | Строк technical_evidence с цитатой |
|---|---|---:|
| platforms | platform_code | 109 |
| ravenol | transmission_code | 48 |
| ravenol | engine_code | 32 |
| ymmt | length_mm | 195 |
| ymmt | width_mm | 195 |
| ymmt | height_mm | 195 |
| ymmt | wheelbase_mm | 195 |
| ymmt | seats | 195 |
| ymmt | cylinders | 195 |
| ymmt | engine_displacement_l | 195 |
| ymmt | drivetrain | 195 |
| ymmt | transmission_description | 195 |
| ymmt | fuel_type | 195 |
| ymmt | curb_weight_kg | 194 |
| ymmt | ground_clearance | 182 |
| ymmt | system_power_hp | 99 |
| ymmt | torque_rpm | 15 |
| ymmt | power_hp | 10 |
| ymmt | power_rpm | 10 |

### ТО по маркам

| Марка | До | После | Система / уровень показа |
|---|---:|---:|---|
| Toyota | 0 | 0 | — |
| Lexus | 0 | 0 | — |
| BMW | 0 | 36 | CBS/SECONDARY_NOTE 36 |
| Chevrolet | 0 | 341 | FIXED_INTERVAL/FACT 328, OIL_LIFE_MONITOR/FACT 13 |
| Ford | 0 | 96 | FIXED_INTERVAL/SECONDARY_NOTE 70, OIL_LIFE_MONITOR/SECONDARY_NOTE 26 |
| Honda | 0 | 588 | FIXED_INTERVAL/FACT 96, MAINTENANCE_MINDER/FACT 492 |
| Nissan | 0 | 748 | FIXED_INTERVAL/FACT 636, FIXED_INTERVAL/SECONDARY_NOTE 112 |
| Land Rover | 0 | 0 | — |
| Infiniti | 0 | 447 | FIXED_INTERVAL/FACT 310, FIXED_INTERVAL/SECONDARY_NOTE 137 |
| Audi | 0 | 690 | FIXED_INTERVAL/FACT 690 |
| Volkswagen | 0 | 274 | FIXED_INTERVAL/FACT 274 |
| Tesla | 0 | 32 | FIXED_INTERVAL/SECONDARY_NOTE 32 |
| Hyundai | 407 | 407 | FIXED_INTERVAL/FACT 407 |
| Kia | 639 | 639 | FIXED_INTERVAL/FACT 285, FIXED_INTERVAL/SECONDARY_NOTE 354 |
| Mercedes-Benz | 300 | 300 | SERVICE_A_B/SECONDARY_NOTE 300 |
| **Всего** | **1346** | **4598** | |

### Итоги базы

| Таблица | Строк (live) |
|---|---:|
| technical_evidence | 359 922 |
| known_issues | 3 648 |
| maintenance_schedule_items | 4 598 |
| source_records | 30 096 |
| raw_documents | 6 109 |

