# Auto Expert — U.S. bulk data 08: published checkpoint

Опубликовано в существующей локальной БД. Границы: 17 утверждённых марок, рынок США,
model years с 2000 года; Skoda исключена. Таблицы ниже показывают только точные
подтверждённые версии. Исторический batch07 и исходные записи сохранены.

<!-- BEGIN VEHICLE CATALOG TABLES -->
## Delta from previous batch — us-bulk-data-08

Полный список новых, изменённых и повторно опубликованных версий batch.
`ADDED` — новая запись; `CHANGED` — изменились факты (поля указаны в Status);
`EVIDENCE_REFRESH` — обновление ревизии/provenance без изменения значений.
`ENTERED_STRICT_SCOPED` — существующая версия впервые прошла строгий gate.
`NOT_IN_STRICT_OUTPUT` — сохранена в базовом каталоге, но недоступна в текущей строгой выдаче.
`EXCLUDED` — исключена из выдачи. Область любого статуса ограничена указанными годами и связкой.

| Make | Model | Generation | USA market | Model years | Engine | Transmission | Drivetrain | Body | Seats | Configuration count | Status |
|---|---|---|---|---|---|---|---|---|---|---:|---|
| Audi | Q3 | 8U | USA | 2015–2017 | Q3 2.0T 1,984cc turbo TFSI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=200 | Six-speed Tiptronic automatic | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Audi | Q3 | 8U | USA | 2015–2017 | Q3 2.0T 1,984cc turbo TFSI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=200 | Six-speed Tiptronic automatic | FWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=Limited | 6-speed SHIFTRONIC automatic | AWD | SUV | 6 | 2 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=Limited | 6-speed SHIFTRONIC automatic | FWD | SUV | 6 | 2 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=SE | 6-speed SHIFTRONIC automatic | AWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=SE | 6-speed SHIFTRONIC automatic | FWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 6-speed manual | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in |
| Kia | Forte | BD / BDm sedan | USA | 2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 7-speed dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in |
| Kia | Forte | BD / BDm sedan | USA | 2019 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension |
| Kia | Forte | BD / BDm sedan | USA | 2020 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in |
| Kia | Forte | BD / BDm sedan | USA | 2019 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Intelligent Variable Transmission (CVT) | FWD | SEDAN | 5 | 2 (2019: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension |
| Kia | Forte | BD / BDm sedan | USA | 2020 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Intelligent Variable Transmission (CVT) | FWD | SEDAN | 5 | 2 (2020: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed automatic | FWD | SEDAN | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, rear_suspension |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed automatic | FWD | SEDAN | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, rear_suspension |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2016 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, octane_aki, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, injection, octane_aki, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2018–2019 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2016 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, octane_aki, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, injection, octane_aki, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2018–2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2020 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, octane_aki, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, height_in, injection, octane_aki, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2018–2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, rear_suspension |
| Kia | Optima | JF / JFa sedan | USA | 2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension |
| Kia | Rio | SC sedan | USA | 2019 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, injection, rear_suspension, tires, wheels |
| Kia | Rio | SC sedan | USA | 2018 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension, tires, wheels |
| Kia | Rio | SC sedan | USA | 2018 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, height_in, injection, rear_suspension, tires, wheels |
| Kia | Rio | SC sedan | USA | 2020 | Gamma II 1.6L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=120 | Intelligent Variable Transmission (CVT) | FWD | SEDAN | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, height_in, rear_suspension, tires, wheels |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | AWD | SUV | 7 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | FWD | SUV | 7 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_brakes, fuel_tank_us_gal, octane_aki, rear_brakes |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_brakes, fuel_tank_us_gal, octane_aki, rear_brakes |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_brakes, fuel_tank_us_gal, octane_aki, rear_brakes |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_brakes, fuel_tank_us_gal, octane_aki, rear_brakes |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 (2016: 2) | CHANGED / STRICT_SCOPED; changed: front_brakes, fuel_tank_us_gal, octane_aki, rear_brakes |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 (2017: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 (2018: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 1 | CHANGED / STRICT_SCOPED; changed: front_brakes, fuel_tank_us_gal, octane_aki, rear_brakes |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2021–2022 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2021–2022 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2021–2022 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2021–2022 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 | CHANGED / STRICT_SCOPED; changed: front_suspension, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 (2017: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 (2018: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 (2019: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 (2017: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, octane_aki, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 (2018: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, fuel_tank_us_gal, injection, rear_suspension |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 (2019: 2) | CHANGED / STRICT_SCOPED; changed: front_suspension, injection, rear_suspension |
| Toyota | Highlander | III | USA | 2014–2016 | Hybrid Limited 3.5L V6 Hybrid Synergy Drive; powertrain=HEV; fuel=GASOLINE; trim=Hybrid Limited | Electronically controlled CVT (ECVT) | AWD | SUV | 7 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE 2.7L DOHC VVT-i inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185; trim=LE | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE | 6-speed ECT-i automatic | AWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE Plus 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE Plus | 6-speed ECT-i automatic | AWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE Plus 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE Plus | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | Limited 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=Limited | 6-speed ECT-i automatic | AWD | SUV | 7 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | Limited 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=Limited | 6-speed ECT-i automatic | FWD | SUV | 7 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | XLE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=XLE | 6-speed ECT-i automatic | AWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | XLE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=XLE | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder Platinum 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=Platinum | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder Platinum 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=Platinum | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder S 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=S | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder S 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=S | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SL 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SL | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SL 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SL | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SV 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SV | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SV 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SV | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | ADDED / STRICT_SCOPED |

## Cumulative strict-output catalog — прежний строгий критерий с местами

Полный список из того же `active_us_rows`, который использует приложение для `US_BASE_2000`.
`AVAILABLE_SCOPED` означает доступность только указанных годов, двигателя, коробки,
привода, кузова и мест. Статус не распространяется на остальные версии модели.
Объединены только одинаково описанные версии с одинаковым статусом; перечисление лет
сохраняет разрывы. Configuration count — число опубликованных годовых записей внутри
строки, а не число машин в объявлениях. Если в одном году несколько исходных записей,
приведено распределение по годам; их точные catalog_key сохранены в catalog-tables.json.
Body и Seats добавлены, чтобы варианты кузова и 5/7 мест не смешивались.

| Make | Model | Generation | USA market | Model years | Engine | Transmission | Drivetrain | Body | Seats | Configuration count | Status |
|---|---|---|---|---|---|---|---|---|---|---:|---|
| Mercedes-Benz | A-Class | 177 Sedan | USA | 2019–2020 | A220 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=188 | 7G-DCT 7-speed dual-clutch | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Mercedes-Benz | A-Class | 177 Sedan | USA | 2019–2020 | A220 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=188 | 7G-DCT 7-speed dual-clutch | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2017 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2017 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2018 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2018 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLC-Class | X253 SUV | USA | 2018 | GLC300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLC-Class | X253 SUV | USA | 2018 | GLC300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | RWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | AMG GLE43 3.0L biturbo V6; powertrain=ICE; fuel=GASOLINE; power_hp=385 | AMG-enhanced 9G-TRONIC 9-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | AMG GLE63 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=550 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | AMG GLE63 S 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=577 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | RWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | GLE550e 3.0L biturbo V6 + plug-in hybrid motor; powertrain=PHEV; fuel=GASOLINE | 7G-TRONIC 7-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 320i 2.0L inline-4 TwinPower Turbo gasoline; engine_code=N20B20U0; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 6-speed manual | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 320i 2.0L inline-4 TwinPower Turbo gasoline; engine_code=N20B20U0; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 320i 2.0L inline-4 TwinPower Turbo gasoline; engine_code=N20B20U0; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 320i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 6-speed manual | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 320i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 320i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 328d 2.0L inline-4 TwinPower Turbo diesel; engine_code=N47D20O1; powertrain=ICE; fuel=DIESEL; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 328d 2.0L inline-4 TwinPower Turbo diesel; engine_code=N47D20O1; powertrain=ICE; fuel=DIESEL; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 328d 2.0L inline-4 TwinPower Turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 328d 2.0L inline-4 TwinPower Turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=180 | 8-speed Steptronic automatic; code=8HP45 | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016 | 328i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 6-speed manual | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016 | 328i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic; code=8HP45 | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016 | 328i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic; code=8HP45 | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 330i 2.0L inline-4 TwinPower Turbo gasoline; engine_code=B46B20O0; powertrain=ICE; fuel=GASOLINE; power_hp=248 | 6-speed manual | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 330i 2.0L inline-4 TwinPower Turbo gasoline; engine_code=B46B20O0; powertrain=ICE; fuel=GASOLINE; power_hp=248 | 8-speed Steptronic automatic; code=8HP50 | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 330i 2.0L inline-4 TwinPower Turbo gasoline; engine_code=B46B20O0; powertrain=ICE; fuel=GASOLINE; power_hp=248 | 8-speed Steptronic automatic; code=8HP50 | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2017 | 330i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=248 | 6-speed manual | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2017 | 330i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=248 | 8-speed Steptronic automatic; code=8HP50 | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2017 | 330i 2.0L inline-4 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=248 | 8-speed Steptronic automatic; code=8HP50 | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 340i 3.0L inline-6 TwinPower Turbo gasoline; engine_code=B58B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 6-speed manual | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 340i 3.0L inline-6 TwinPower Turbo gasoline; engine_code=B58B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 6-speed manual | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 340i 3.0L inline-6 TwinPower Turbo gasoline; engine_code=B58B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 8-speed Steptronic automatic; code=8HP50 | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2018 | 340i 3.0L inline-6 TwinPower Turbo gasoline; engine_code=B58B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 8-speed Steptronic automatic; code=8HP50 | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 340i 3.0L inline-6 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 6-speed manual | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 340i 3.0L inline-6 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 6-speed manual | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 340i 3.0L inline-6 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 8-speed Steptronic automatic; code=8HP50 | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 3 Series | F30 sedan LCI; FACELIFT | USA | 2016–2017 | 340i 3.0L inline-6 TwinPower Turbo gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=320 | 8-speed Steptronic automatic; code=8HP50 | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 528i 2.0L inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 528i 2.0L inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535d 3.0L inline-6 turbo; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535d 3.0L inline-6 turbo; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535i 3.0L inline-6 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 6-speed manual | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535i 3.0L inline-6 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535i 3.0L inline-6 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 550i 4.4L V8 biturbo; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 550i 4.4L V8 biturbo; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | X1 | E84 LCI | USA | 2013–2015 | sDrive28i 2.0L TwinPower Turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | RWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| BMW | X1 | E84 LCI | USA | 2013–2015 | xDrive28i 2.0L TwinPower Turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| BMW | X1 | E84 LCI | USA | 2013–2015 | xDrive35i 3.0L TwinPower Turbo inline-6; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 6-speed Steptronic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014, 2016 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; engine_code=N55B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic; code=8HP45 | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014, 2016 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; engine_code=N55B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic; code=8HP45 | RWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; engine_code=N57D30O1; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic; code=8HP70 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; engine_code=N57D30O1; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic; code=8HP75 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive40e N20 2.0L TwinPower Turbo inline-4 + electric motor; engine_code=N20B20O0; powertrain=PHEV; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic (plug-in hybrid) | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014 | xDrive50i 4.4L TwinPower Turbo V8; engine_code=N63B44O1; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic; code=8HP70 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive50i 4.4L TwinPower Turbo V8; engine_code=N63B44O1; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic; code=8HP75 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Audi | A3 | 8V Sedan | USA | 2015–2016 | 1.8 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed S tronic dual-clutch | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A3 | 8V Sedan | USA | 2015–2016 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 6-speed S tronic dual-clutch | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 6-speed manual | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 3.0 TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013–2015 | 3.0 TFSI supercharged V6; powertrain=ICE; fuel=GASOLINE; power_hp=310 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | Q3 | 8U | USA | 2015–2017 | Q3 2.0T 1,984cc turbo TFSI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=200 | Six-speed Tiptronic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Audi | Q3 | 8U | USA | 2015–2017 | Q3 2.0T 1,984cc turbo TFSI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=200 | Six-speed Tiptronic automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Audi | Q5 | 8R SUV | USA | 2014–2017 | 2.0 TFSI direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 4 | AVAILABLE_SCOPED |
| Audi | Q5 | 8R SUV | USA | 2014–2015 | 3.0 TDI direct injection; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Audi | Q5 | 8R SUV | USA | 2014–2017 | 3.0 TFSI direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=272 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 4 | AVAILABLE_SCOPED |
| Audi | Q7 | 4L | USA | 2014–2015 | 3.0 TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed Tiptronic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Audi | Q7 | 4L | USA | 2014–2015 | 3.0 TFSI supercharged V6 S line Prestige; powertrain=ICE; fuel=GASOLINE; power_hp=333 | 8-speed Tiptronic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Audi | Q7 | 4L | USA | 2014–2015 | 3.0 TFSI supercharged V6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 8-speed Tiptronic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Volkswagen | Atlas | I-US-2018 | USA | 2018–2019 | 2.0L TSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=235 | 8-speed automatic with Tiptronic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Volkswagen | Atlas | I-US-2018 | USA | 2018–2019 | 3.6L FSI narrow-angle V6; powertrain=ICE; fuel=GASOLINE; power_hp=276 | 8-speed automatic with Tiptronic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Volkswagen | Atlas | I-US-2018 | USA | 2018–2019 | 3.6L FSI narrow-angle V6; powertrain=ICE; fuel=GASOLINE; power_hp=276 | 8-speed automatic with Tiptronic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 5-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed Tiptronic automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 2.0L TDI inline-4 turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=150 | 6-speed DSG dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 2.0L TDI inline-4 turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=150 | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 3.6L FSI narrow-angle VR6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 6-speed DSG dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Tiguan | II US long-wheelbase SUV (II-US-LWB) | USA | 2018–2020 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=184 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Volkswagen | Tiguan | II US long-wheelbase SUV (II-US-LWB) | USA | 2018–2020 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=184 | 8-speed Tiptronic automatic | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Volkswagen | Tiguan | II US long-wheelbase SUV (II-US-LWB) | USA | 2018–2020 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=184 | 8-speed Tiptronic automatic | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); FACELIFT | USA | 2015 | 3.0L TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); FACELIFT | USA | 2015 | 3.0L supercharged V6 + electric motor; powertrain=HEV; fuel=GASOLINE | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); FACELIFT | USA | 2015 | 3.6L FSI narrow-angle V6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); PRE_FACELIFT | USA | 2013–2014 | 3.0L TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); PRE_FACELIFT | USA | 2013–2014 | 3.0L supercharged V6 + electric motor; powertrain=HEV; fuel=GASOLINE | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); PRE_FACELIFT | USA | 2013–2014 | 3.6L FSI narrow-angle V6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; FACELIFT | USA | 2019 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 (2019: 2) | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; FACELIFT | USA | 2019 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual (SE) | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; FACELIFT | USA | 2020 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Intelligent Variable Transmission (chain CVT) | FWD | SEDAN | 5 | 2 (2020: 2) | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2017–2018 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 4 (2017: 2, 2018: 2) | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2017–2018 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual (SE) | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2021 | 1.6L Atkinson GDI inline-4 + 32kW hybrid motor; powertrain=HEV; fuel=GASOLINE | 6-speed EcoShift dual-clutch automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2021 | Smartstream 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Smartstream Intelligent Variable Transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2014, 2016 | Nu 1.8L MPI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2014, 2016 | Nu 1.8L MPI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2014, 2016 | Sport Nu 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2014 | Sport Nu 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=Limited | 6-speed SHIFTRONIC automatic | AWD | SUV | 6 | 2 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=Limited | 6-speed SHIFTRONIC automatic | FWD | SUV | 6 | 2 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=SE | 6-speed SHIFTRONIC automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe | NC | USA | 2016–2017 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE; power_hp=290; trim=SE | 6-speed SHIFTRONIC automatic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2015 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2015 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2016 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=265 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2016 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=265 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2015, 2017–2019 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed EcoShift dual-clutch | FWD | SEDAN | 5 | 4 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2015, 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2018–2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 8-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2015, 2017–2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 4 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2016 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=175 | 7-speed EcoShift dual-clutch | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2016 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=175 | 7-speed EcoShift dual-clutch | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2019 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=161 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2019 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=161 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2016 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=164 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2016 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=164 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=181 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Tucson | TL SUV | USA | 2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=181 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 7-speed dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2019–2020 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2019–2020 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Intelligent Variable Transmission (CVT) | FWD | SEDAN | 5 | 4 (2019: 2, 2020: 2) | AVAILABLE_SCOPED |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | K5 | DL3/DL3a sedan | USA | 2021 | 1.6L turbo Gamma-II GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed torque-converter automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | K5 | DL3/DL3a sedan | USA | 2021 | 1.6L turbo Gamma-II GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed torque-converter automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | K5 | DL3/DL3a sedan | USA | 2021 | 2.5L turbo Theta-III GDI+MPI inline-4 (GT); powertrain=ICE; fuel=GASOLINE; power_hp=290 | 8-speed wet dual-clutch automatic (GT) | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Optima | JF / JFa sedan | USA | 2016–2019 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | 5 | 4 | AVAILABLE_SCOPED |
| Kia | Optima | JF / JFa sedan | USA | 2016–2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | 5 | 4 | AVAILABLE_SCOPED |
| Kia | Optima | JF / JFa sedan | USA | 2016–2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | 5 | 4 | AVAILABLE_SCOPED |
| Kia | Rio | SC sedan | USA | 2019 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Rio | SC sedan | USA | 2020 | Gamma II 1.6L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=120 | Intelligent Variable Transmission (CVT) | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 6 (2016: 2, 2017: 2, 2018: 2) | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 6 (2017: 2, 2018: 2, 2019: 2) | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 6 (2017: 2, 2018: 2, 2019: 2) | AVAILABLE_SCOPED |
| Toyota | Camry | V sedan (US 2002 redesign) | USA | 2002–2004 | 2.4L VVT-i DOHC inline-4; powertrain=ICE; fuel=GASOLINE | 4-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | V sedan (US 2002 redesign) | USA | 2005–2006 | 2.4L VVT-i DOHC inline-4; powertrain=ICE; fuel=GASOLINE | 5-speed ECT-i automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Toyota | Camry | V sedan (US 2002 redesign) | USA | 2002–2006 | 2.4L VVT-i DOHC inline-4; powertrain=ICE; fuel=GASOLINE | 5-speed manual | FWD | SEDAN | 5 | 5 | AVAILABLE_SCOPED |
| Toyota | Camry | V sedan (US 2002 redesign) | USA | 2004–2006 | 3.0L DOHC V6 gasoline VVT-i; powertrain=ICE; fuel=GASOLINE | 5-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | V sedan (US 2002 redesign) | USA | 2002–2003 | 3.0L DOHC V6 gasoline; powertrain=ICE; fuel=GASOLINE | 4-speed ECT-i automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Toyota | Camry | V sedan (US 2002 redesign) | USA | 2004–2006 | SE 3.3L VVT-i DOHC V6 gasoline; powertrain=ICE; fuel=GASOLINE | 5-speed ECT-i automatic (SE V6) | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VI sedan (2007 redesign) | USA | 2007–2010 | 2.4L Atkinson inline-4 + Hybrid Synergy Drive; powertrain=HEV; fuel=GASOLINE; power_hp=147 | Electronically controlled continuously variable transmission | FWD | SEDAN | 5 | 4 | AVAILABLE_SCOPED |
| Toyota | Camry | VI sedan (2007 redesign) | USA | 2007–2009 | 2.4L VVT-i inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | 5-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VI sedan (2007 redesign) | USA | 2007–2009 | 2.4L VVT-i inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | 5-speed manual | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VI sedan (2007 redesign) | USA | 2011 | 2.5L Dual VVT-i inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | 6-speed ECT-i automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Toyota | Camry | VI sedan (2007 redesign) | USA | 2011 | 2.5L Dual VVT-i inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Toyota | Camry | VI sedan (2007 redesign) | USA | 2007–2011 | 3.5L Dual VVT-i V6 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=268 | 6-speed ECT-i automatic | FWD | SEDAN | 5 | 5 | AVAILABLE_SCOPED |
| Toyota | Camry | VII sedan (US 2012 redesign); FACELIFT | USA | 2015–2017 | 2.5L Atkinson inline-4 + Hybrid Synergy Drive; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VII sedan (US 2012 redesign); FACELIFT | USA | 2015–2017 | 2.5L Dual VVT-i DOHC inline-4 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 6-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VII sedan (US 2012 redesign); FACELIFT | USA | 2015–2017 | 3.5L Dual VVT-i DOHC V6 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=268 | 6-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VII sedan (US 2012 redesign); PRE_FACELIFT | USA | 2012–2014 | 2.5L Atkinson inline-4 + Hybrid Synergy Drive; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VII sedan (US 2012 redesign); PRE_FACELIFT | USA | 2012–2014 | 2.5L Dual VVT-i DOHC inline-4 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 6-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VII sedan (US 2012 redesign); PRE_FACELIFT | USA | 2012–2014 | 3.5L Dual VVT-i DOHC V6 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=268 | 6-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 2.5L Atkinson inline-4 + Toyota Hybrid System; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2020 | 2.5L D-4S inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | Direct Shift 8-speed automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 2.5L D-4S inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | Direct Shift 8-speed automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 3.5L D-4S V6 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=301 | Direct Shift 8-speed automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Dual VVT-i; powertrain=ICE; fuel=GASOLINE; power_hp=132 | 4-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Dual VVT-i; powertrain=ICE; fuel=GASOLINE; power_hp=132 | 6-speed manual | FWD | SEDAN | 5 | 6 (2014: 2, 2015: 2, 2016: 2) | AVAILABLE_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Dual VVT-i; powertrain=ICE; fuel=GASOLINE; power_hp=132 | CVTi-S continuously variable transmission | FWD | SEDAN | 5 | 6 (2014: 2, 2015: 2, 2016: 2) | AVAILABLE_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Valvematic; powertrain=ICE; fuel=GASOLINE; power_hp=140 | CVTi-S continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | Hybrid Limited 3.5L V6 Hybrid Synergy Drive; powertrain=HEV; fuel=GASOLINE; trim=Hybrid Limited | Electronically controlled CVT (ECVT) | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE 2.7L DOHC VVT-i inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185; trim=LE | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE | 6-speed ECT-i automatic | AWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE Plus 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE Plus | 6-speed ECT-i automatic | AWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | LE Plus 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=LE Plus | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | Limited 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=Limited | 6-speed ECT-i automatic | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | Limited 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=Limited | 6-speed ECT-i automatic | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | XLE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=XLE | 6-speed ECT-i automatic | AWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | Highlander | III | USA | 2014–2016 | XLE 3.5L DOHC VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270; trim=XLE | 6-speed ECT-i automatic | FWD | SUV | 8 | 3 | AVAILABLE_SCOPED |
| Toyota | RAV4 | IV | USA | 2013, 2015 | 2.5L Dual VVT-i inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=176 | 6-speed ECT-i automatic | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Toyota | RAV4 | IV | USA | 2013, 2015 | 2.5L Dual VVT-i inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=176 | 6-speed ECT-i automatic | FWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 2.5L DOHC inline-4; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 3.5L DOHC V6; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder Platinum 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=Platinum | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder Platinum 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=Platinum | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder S 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=S | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder S 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=S | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SL 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SL | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SL 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SL | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SV 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SV | Xtronic continuously variable transmission | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Pathfinder | R52 | USA | 2015–2016 | Pathfinder SV 3.5L DOHC 24-valve V6; powertrain=ICE; fuel=GASOLINE; power_hp=260; trim=SV | Xtronic continuously variable transmission | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2016 | 1.8L MRA8DE inline-4 S/SV/SR/SL California SULEV; not FE+; engine_code=MRA8DE; powertrain=ICE; fuel=GASOLINE; power_hp=124 | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2017–2018 | 1.8L MRA8DE inline-4 S/SV/SR/SL; engine_code=MRA8DE; powertrain=ICE; fuel=GASOLINE; power_hp=124 | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2016 | 1.8L MRA8DE inline-4 ULEV; non-California; engine_code=MRA8DE; powertrain=ICE; fuel=GASOLINE; power_hp=130 | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2018 | NISMO 1.6L DIG turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=188 | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2018 | NISMO 1.6L DIG turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=188 | Xtronic CVT with Manual Shift Mode | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2016–2018 | S 1.8L MRA8DE inline-4; engine_code=MRA8DE; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed manual | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2017 | SR Turbo 1.6L DIG turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=188 | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Nissan | Sentra | B17 | USA | 2017–2018 | SR Turbo 1.6L DIG turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=188 | Xtronic CVT with Manual Shift Mode | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | IX sedan facelift | USA | 2016–2017 | 2.4L i-VTEC direct-injection inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | IX sedan facelift | USA | 2016–2017 | 2.4L i-VTEC direct-injection inline-4; powertrain=ICE; fuel=GASOLINE | Continuously variable transmission | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | IX sedan facelift | USA | 2016–2017 | 3.5L i-VTEC V6 with VCM; powertrain=ICE; fuel=GASOLINE; power_hp=278 | 6-speed automatic with Sport Mode | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); FACELIFT | USA | 2006–2007 | 2.4L i-VTEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=166 | 5-speed automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); FACELIFT | USA | 2006–2007 | 2.4L i-VTEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=166 | 5-speed manual | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); FACELIFT | USA | 2006–2007 | 3.0L VTEC SOHC V6; powertrain=ICE; fuel=GASOLINE; power_hp=244 | 5-speed automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); FACELIFT | USA | 2006–2007 | 3.0L VTEC SOHC V6; powertrain=ICE; fuel=GASOLINE; power_hp=244 | 6-speed manual (EX V6 sedan) | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); PRE_FACELIFT | USA | 2003 | 2.4L i-VTEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE | 5-speed automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); PRE_FACELIFT | USA | 2003 | 2.4L i-VTEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE | 5-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | VII sedan (US 2003 redesign); PRE_FACELIFT | USA | 2003 | 3.0L VTEC SOHC V6; powertrain=ICE; fuel=GASOLINE | 5-speed automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 1.5L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=192 | 6-speed manual (Sport) | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 1.5L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=192 | Continuously variable transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=252 | 10-speed automatic with Shift-By-Wire | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | CR-V | IV (US 2012 redesign) | USA | 2012–2014 | 2.4L DOHC i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 5-speed automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Honda | CR-V | IV (US 2012 redesign) | USA | 2012–2014 | 2.4L DOHC i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 5-speed automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Chevrolet | Malibu | VIII | USA | 2013–2015 | ECOTEC 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=259 | 6-speed automatic with overdrive | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Chevrolet | Malibu | VIII | USA | 2014–2015 | ECOTEC 2.5L direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=196 | 6-speed automatic with overdrive | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Chevrolet | Malibu | VIII | USA | 2013 | ECOTEC 2.5L direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=197 | 6-speed automatic with overdrive | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Chevrolet | Malibu | VIII | USA | 2013 | Eco 2.4L direct-injection inline-4 + eAssist motor-generator; powertrain=MHEV; fuel=GASOLINE; power_hp=182 | 6-speed automatic with overdrive | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 6-speed ECT-i automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 6-speed ECT-i automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 8-speed ECT-i automatic (F Sport) | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX450h 3.5L Atkinson V6 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | ECVT-i electronically controlled continuously variable transmission | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX450h 3.5L Atkinson V6 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | ECVT-i electronically controlled continuously variable transmission | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Infiniti | QX60 | L50 | USA | 2015–2016 | 2.5L supercharged inline-4 + Infiniti Direct Response Hybrid motor; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission (hybrid) | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Infiniti | QX60 | L50 | USA | 2015–2016 | 2.5L supercharged inline-4 + Infiniti Direct Response Hybrid motor; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission (hybrid) | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Infiniti | QX60 | L50 | USA | 2014–2016 | 3.5L DOHC V6; powertrain=ICE; fuel=GASOLINE; power_hp=265 | Electronically controlled continuously variable transmission | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Infiniti | QX60 | L50 | USA | 2014–2016 | 3.5L DOHC V6; powertrain=ICE; fuel=GASOLINE; power_hp=265 | Electronically controlled continuously variable transmission | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Jeep | Compass | MK | USA | 2016 | 2.0L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=158 | 5-speed manual | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Compass | MK | USA | 2016 | 2.0L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=158 | CVT2 continuously variable transaxle | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Compass | MK | USA | 2016 | 2.4L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=172 | 5-speed manual | 4WD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Compass | MK | USA | 2016 | 2.4L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=172 | 6-speed PowerTech automatic | 4WD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Compass | MK | USA | 2016 | 2.4L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=172 | 6-speed PowerTech automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Compass | MK | USA | 2016 | 2.4L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=172 | CVT2L (Freedom Drive II low-range package) | 4WD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | RWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 5.7L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 6.2L supercharged V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 6.4L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2018 | 2.4L MIVEC inline-4; engine_code=4J12; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | AWD | SUV | 7 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2018 | 2.4L MIVEC inline-4; engine_code=4J12; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | FWD | SUV | 7 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2019 | 2.4L MIVEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | AWD | SUV | 7 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2019 | 2.4L MIVEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | FWD | SUV | 7 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2018 | 3.0L MIVEC V6; engine_code=6B31; powertrain=ICE; fuel=GASOLINE; power_hp=224 | 6-speed electronic automatic | AWD | SUV | 7 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2019 | 3.0L MIVEC V6; powertrain=ICE; fuel=GASOLINE; power_hp=224 | 6-speed electronic automatic | AWD | SUV | 7 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2014 | 2.0L MIVEC DOHC inline-4; engine_code=4B11; powertrain=ICE; fuel=GASOLINE; power_hp=148 | 5-speed manual | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2014 | 2.0L MIVEC DOHC inline-4; engine_code=4B11; powertrain=ICE; fuel=GASOLINE; power_hp=148 | INVECS-III continuously variable automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2014 | 2.0L MIVEC DOHC inline-4; engine_code=4B11; powertrain=ICE; fuel=GASOLINE; power_hp=148 | INVECS-III continuously variable automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2015–2016 | 2.0L MIVEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=148 | 5-speed manual | FWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2015–2016 | 2.0L MIVEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=148 | INVECS-III continuously variable automatic | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2015–2016 | 2.0L MIVEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=148 | INVECS-III continuously variable automatic | FWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2016 | 2.4L MIVEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=168 | Continuously variable automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mitsubishi | Outlander Sport | I-US-2011 | USA | 2016 | 2.4L MIVEC DOHC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=168 | Continuously variable automatic | FWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Cadillac | SRX | 2010 redesign SUV (2010-REDESIGN) | USA | 2014–2016 | 3.6L direct-injection VVT V6; powertrain=ICE; fuel=GASOLINE; power_hp=308 | 6-speed automatic with Performance Algorithm Shifting | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Cadillac | SRX | 2010 redesign SUV (2010-REDESIGN) | USA | 2014–2016 | 3.6L direct-injection VVT V6; powertrain=ICE; fuel=GASOLINE; power_hp=308 | 6-speed automatic with Performance Algorithm Shifting | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |

## Cumulative conditional-output catalog — места не подтверждены

Доступны в обычном поиске `US_CONFIRMED_2000`, если число мест не ограничено и все другие жёсткие условия подтверждены. UNKNOWN не проходит требование мест, бюджета или другого неизвестного поля: только отдельная группа «Требует уточнения», без первого предложения. Это доступность, а не новая верификация.

| Make | Model | Generation | USA market | Model years | Engine | Transmission | Drivetrain | Body | Seats | Configuration count | Status |
|---|---|---|---|---|---|---|---|---|---|---:|---|
| Mercedes-Benz | C-Class | W205 sedan | USA | 2015–2016 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | AWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2015–2016 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | RWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2014 | E250 BlueTEC 2.1L inline-4 twin-turbo diesel; engine_code=OM651; powertrain=ICE; fuel=DIESEL; power_hp=195 | 7-speed automatic | AWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2014 | E250 BlueTEC 2.1L inline-4 twin-turbo diesel; engine_code=OM651; powertrain=ICE; fuel=DIESEL; power_hp=195 | 7-speed automatic | RWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2015–2016 | E250 BlueTEC 2.1L inline-4 twin-turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=195 | 7-speed automatic | AWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2015–2016 | E250 BlueTEC 2.1L inline-4 twin-turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=195 | 7-speed automatic | RWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2014 | E350 3.5L V6 direct injection; engine_code=M276; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7-speed automatic | AWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2014 | E350 3.5L V6 direct injection; engine_code=M276; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7-speed automatic | RWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2015–2016 | E350 3.5L V6 direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7-speed automatic | AWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2015–2016 | E350 3.5L V6 direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7-speed automatic | RWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2015–2016 | E400 3.0L V6 biturbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=329 | 7-speed automatic | AWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | E-Class | W212 sedan | USA | 2015–2016 | E400 3.0L V6 biturbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=329 | 7-speed automatic | RWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLC-Class | X253 SUV | USA | 2017, 2019 | GLC300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLC-Class | X253 SUV | USA | 2017, 2019 | GLC300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | RWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2017 | AMG GLE43 3.0L biturbo V6; powertrain=ICE; fuel=GASOLINE; power_hp=362 | AMG-enhanced 9G-TRONIC 9-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | AMG GLE63 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=550 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | AMG GLE63 S 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=577 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016 | GLE300d BlueTEC 2.1L twin-turbo diesel inline-4; powertrain=ICE; fuel=DIESEL; power_hp=201 | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | RWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016 | GLE400 3.0L biturbo direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=329 | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2017 | GLE400 3.0L biturbo direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=329 | 9G-TRONIC 9-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | GLE550e 3.0L biturbo V6 + plug-in hybrid motor; powertrain=PHEV; fuel=GASOLINE | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X3 | F25 | USA | 2015 | sDrive28i 2.0L TwinPower Turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | RWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X3 | F25 | USA | 2015 | xDrive28d 2.0L TwinPower Turbo diesel inline-4; powertrain=ICE; fuel=DIESEL; power_hp=180 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X3 | F25 | USA | 2014–2015 | xDrive28i 2.0L TwinPower Turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X3 | F25 | USA | 2014–2015 | xDrive35i 3.0L TwinPower Turbo inline-6; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X5 | F15 | USA | 2015 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X5 | F15 | USA | 2015 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | RWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X5 | F15 | USA | 2015 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| BMW | X5 | F15 | USA | 2015 | xDrive50i 4.4L TwinPower Turbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2012 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | multitronic continuously variable transmission | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2012 | 3.0 TFSI supercharged V6; powertrain=ICE; fuel=GASOLINE; power_hp=310 | 8-speed Tiptronic automatic | AWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Jetta | VI sedan | USA | 2017–2018 | 1.4 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=150 | 5-speed manual | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Jetta | VI sedan | USA | 2017–2018 | 1.4 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=150 | 6-speed Tiptronic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Jetta | VI sedan | USA | 2017–2018 | 1.8 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed Tiptronic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Jetta | VI sedan | USA | 2017–2018 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=210 | 6-speed DSG dual-clutch | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Jetta | VI sedan | USA | 2017 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=210 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Passat | NMS North American sedan; FACELIFT | USA | 2016–2017 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed Tiptronic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Passat | NMS North American sedan; FACELIFT | USA | 2018–2019 | 2.0L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=174 | 6-speed Tiptronic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Volkswagen | Passat | NMS North American sedan; FACELIFT | USA | 2016–2018 | 3.6L FSI narrow-angle VR6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 6-speed DSG dual-clutch | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Accent | RB | USA | 2016–2017 | SE 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=137 | 6-speed SHIFTRONIC automatic | FWD | HATCHBACK | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Accent | RB | USA | 2016–2017 | SE 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=137 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Accent | RB | USA | 2016–2017 | SE 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=137 | 6-speed manual | FWD | HATCHBACK | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Accent | RB | USA | 2016–2017 | SE 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=137 | 6-speed manual | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2022–2023 | 1.6L Atkinson GDI inline-4 + 32kW hybrid motor; powertrain=HEV; fuel=GASOLINE | 6-speed EcoShift dual-clutch automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2023 | N 2.0L turbo GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=276 | 6-speed manual with rev matching (N) | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2023 | N 2.0L turbo GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=276 | 8-speed wet dual-clutch automatic (N) | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2021–2022 | N Line 1.6L turbo GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 6-speed manual (N Line) | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2021–2023 | N Line 1.6L turbo GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 7-speed dual-clutch automatic (N Line) | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | CN7/CN7A sedan | USA | 2022–2023 | Smartstream 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Smartstream Intelligent Variable Transmission | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2015 | Nu 1.8L MPI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2015 | Nu 1.8L MPI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2015 | Sport Nu 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | MD/UD sedan; FACELIFT | USA | 2015 | Sport Nu 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | MD/UD sedan; PRE_FACELIFT | USA | 2011–2013 | Nu 1.8L MPI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Elantra | MD/UD sedan; PRE_FACELIFT | USA | 2011–2013 | Nu 1.8L MPI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Sonata | LF / LFa sedan | USA | 2016 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed EcoShift dual-clutch | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Sonata | LF / LFa sedan | USA | 2016 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Sonata | LF / LFa sedan | USA | 2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Sonata | YF sedan | USA | 2012–2013 | 2.0L twin-scroll turbo GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=274 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Sonata | YF sedan | USA | 2011–2013 | 2.4L GDI inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Sonata | YF sedan | USA | 2011–2012 | 2.4L GDI inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | 6-speed manual (GLS) | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2017–2018 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=175 | 7-speed EcoShift dual-clutch | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2017–2018 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=175 | 7-speed EcoShift dual-clutch | FWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2020 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=161 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2020 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=161 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2017–2018 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=164 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2017–2018 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=164 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=181 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Hyundai | Tucson | TL SUV | USA | 2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=181 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | K5 | DL3/DL3a sedan | USA | 2022–2023 | 1.6L turbo Gamma-II GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed torque-converter automatic | AWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | K5 | DL3/DL3a sedan | USA | 2022–2023 | 1.6L turbo Gamma-II GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=180 | 8-speed torque-converter automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | K5 | DL3/DL3a sedan | USA | 2022–2023 | 2.5L turbo Theta-III GDI+MPI inline-4 (GT); powertrain=ICE; fuel=GASOLINE; power_hp=290 | 8-speed wet dual-clutch automatic (GT) | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Optima | JF / JFa sedan | USA | 2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Optima | JF / JFa sedan | USA | 2020 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Optima | JF / JFa sedan | USA | 2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Optima | TF/QF | USA | 2012–2013 | 2.0L turbo GDI inline-4 (SX); powertrain=ICE; fuel=GASOLINE; power_hp=274 | 6-speed Sportmatic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Optima | TF/QF | USA | 2012–2013 | 2.4L GDI inline-4 SULEV (LX/EX); powertrain=ICE; fuel=GASOLINE; power_hp=192 | 6-speed Sportmatic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Optima | TF/QF | USA | 2012–2013 | 2.4L GDI inline-4 ULEV (LX/EX); powertrain=ICE; fuel=GASOLINE; power_hp=200 | 6-speed Sportmatic automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Rio | SC sedan | USA | 2018 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Rio | SC sedan | USA | 2018 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Honda | Civic | IX Sedan | USA | 2013 | LX 1.8L i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=140 | 5-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Honda | Civic | IX Sedan | USA | 2013 | LX 1.8L i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=140 | 5-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Honda | Civic | IX Sedan | USA | 2013 | Si 2.4L DOHC i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=201 | 6-speed close-ratio manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Honda | Civic | IX Sedan | USA | 2015 | Si 2.4L DOHC i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=205 | 6-speed close-ratio manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Land Rover | Range Rover | L405 | USA | 2014–2016 | 3.0L supercharged V6 340hp; powertrain=ICE; fuel=GASOLINE; power_hp=340 | 8-speed automatic | 4WD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Land Rover | Range Rover | L405 | USA | 2016 | 3.0L supercharged V6 380hp; powertrain=ICE; fuel=GASOLINE; power_hp=380 | 8-speed automatic | 4WD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Land Rover | Range Rover | L405 | USA | 2014–2016 | 5.0L supercharged V8 510hp; powertrain=ICE; fuel=GASOLINE; power_hp=510 | 8-speed automatic | 4WD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Land Rover | Range Rover Evoque | LV five-door SUV | USA | 2017 | 2.0L turbo inline-4 (240 hp); powertrain=ICE; fuel=GASOLINE; power_hp=240 | 9-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Land Rover | Range Rover Evoque | LV five-door SUV | USA | 2018 | Ingenium Si4 2.0L turbo inline-4 (237 hp); powertrain=ICE; fuel=GASOLINE; power_hp=237 | 9-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Land Rover | Range Rover Evoque | LV five-door SUV | USA | 2018 | Ingenium Si4 2.0L turbo inline-4 (286 hp); powertrain=ICE; fuel=GASOLINE; power_hp=286 | 9-speed automatic | AWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.4L turbo gasoline inline-4; engine_code=LE2; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.4L turbo gasoline inline-4; engine_code=LE2; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017, 2019 | 1.4L turbo gasoline inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017 | 1.4L turbo gasoline inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.6L turbo diesel inline-4; engine_code=LH7; powertrain=ICE; fuel=DIESEL | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.6L turbo diesel inline-4; engine_code=LH7; powertrain=ICE; fuel=DIESEL | 9-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017 | 1.6L turbo diesel inline-4; powertrain=ICE; fuel=DIESEL | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017, 2019 | 1.6L turbo diesel inline-4; powertrain=ICE; fuel=DIESEL | 9-speed automatic | FWD | SEDAN | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Lexus | ES | VI sedan | USA | 2016–2018 | ES300h 2.5L Atkinson inline-4 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Lexus | ES | VI sedan | USA | 2016–2018 | ES350 3.5L V6; powertrain=ICE; fuel=GASOLINE; power_hp=268 | 6-speed electronically controlled automatic | FWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Lexus | NX | I-US-2015 | USA | 2015–2017 | NX200t / NX Turbo 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=235 | 6-speed automatic | AWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Lexus | NX | I-US-2015 | USA | 2015–2017 | NX200t / NX Turbo 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=235 | 6-speed automatic | FWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Lexus | NX | I-US-2015 | USA | 2015–2017 | NX300h 2.5L Atkinson inline-4 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | AWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Lexus | NX | I-US-2015 | USA | 2015–2016 | NX300h 2.5L Atkinson inline-4 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Compass | MK | USA | 2014–2015 | 2.0L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=158 | 5-speed manual | FWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Compass | MK | USA | 2015 | 2.0L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=158 | CVT2 continuously variable transaxle | FWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Compass | MK | USA | 2014–2015 | 2.4L DOHC Dual VVT inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=172 | 5-speed manual | 4WD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | RWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 5.7L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 6.2L supercharged V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 6.4L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Cadillac | Escalade | IV | USA | 2015 | 6.2L SIDI V8; powertrain=ICE; fuel=GASOLINE; power_hp=420 | Hydra-Matic 6-speed automatic; code=6L80 | 4WD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Cadillac | Escalade | IV | USA | 2015 | 6.2L SIDI V8; powertrain=ICE; fuel=GASOLINE; power_hp=420 | Hydra-Matic 6-speed automatic; code=6L80 | RWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Cadillac | Escalade | IV | USA | 2016 | 6.2L SIDI V8; powertrain=ICE; fuel=GASOLINE; power_hp=420 | Hydra-Matic 8-speed automatic | 4WD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Cadillac | Escalade | IV | USA | 2016 | 6.2L SIDI V8; powertrain=ICE; fuel=GASOLINE; power_hp=420 | Hydra-Matic 8-speed automatic | RWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Cadillac | Escalade | IV | USA | 2015 | 6.2L SIDI V8; powertrain=ICE; fuel=GASOLINE; power_hp=420 | Hydra-Matic 8-speed automatic; code=8L90 | 4WD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Cadillac | Escalade | IV | USA | 2015 | 6.2L SIDI V8; powertrain=ICE; fuel=GASOLINE; power_hp=420 | Hydra-Matic 8-speed automatic; code=8L90 | RWD | SUV | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |

<!-- END VEHICLE CATALOG TABLES -->

## Проверенный результат после поимённого списка

Добавлены 4 модели и поколения: Audi Q3 8U MY2015–2017, Hyundai Santa Fe NC
MY2016–2017, Toyota Highlander III MY2014–2016, Nissan Pathfinder R52
MY2015–2016. Это **60 новых конфигураций** с точной применимостью двигателя,
коробки, привода, кузова, года и мест. Параллельно обогащены **92 существующие
конфигурации Kia** на основе годовых таблиц Kia Media; подробные версии и поля
перечислены в Delta выше. Никакие исследовательские строки EPA не выдаются за
проверенный автомобиль.

| Метрика | Дельта batch08 | Накопительно, базовый каталог | Накопительно, строгая выдача с местами |
|---|---:|---:|---:|
| Марки | 0 новых | 16 | 15 |
| Модели | +4 | 59 | 47 |
| Поколения | +4 | 69 | 55 |
| Рынок × поколение | +4 | 69 | 55 |
| Двигательные варианты | +12 | 177 | 137 |
| Варианты коробок | +5 | 143 | 111 |
| Подтверждённые двигатель × коробка | +12 | 226 | 174 |
| Годовые конфигурации | +60 | 790 | 560 |

Без подтверждённого числа мест остаются **230 старых конфигураций**
(из 230 на входе; новых таких пробелов 0). Они не проходят фильтр по числу мест,
но доступны по прежним правилам при отсутствии этого ограничения. Это отдельный
остаток и не замедлял расширение четырёх семейств. Tesla остаётся 17-й маркой без
подтверждённой базовой конфигурации; Land Rover присутствует в базовом каталоге,
но не в строгом выходе с местами.

## Действительно новые технические данные

Сравнение с закрытой резервной копией до batch08 дало
**1278** новых подтверждённых
ячеек «конфигурация × поле» в 60 новых автомобилях и
**356** в 92 прежних
автомобилях Kia: всего **1634**.
Это число полей с точной годовой/вариантной применимостью, не число независимых
заводских документов или уникальных механических фактов. Сверка обнаружила
0 конфликтов
с прежними подтверждёнными значениями. Повторные публикации и 7 302 строки
EPA research-кандидатов в эти числа не включены.

Заполнены/расширены подкатегории: двигатель (объём, цилиндры, мощность и впрыск),
тип коробки, привод, число мест, длина/ширина/высота/колёсная база, бак,
передняя/задняя подвеска, тормоза и колёса/шины там, где заводская таблица
подтвердила применимость. Объём моторного масла добавлен к 6 Audi Q3,
но вязкость/допуск масла в этом пакете не подтверждены. Подтверждённый исходный
октановый показатель AKI добавлен к 26 Kia;
автоматического перевода AKI в RON нет. Тип коробки подтверждён для всех 60
новых конфигураций; жидкость и применимый объём коробки не заполнены без
однозначного заводского источника. Опции по комплектации и общие строки с
неоднозначным `optional` не распространялись на другие версии.

Kia pipeline повторно использовал 25
закэшированных годовых документов и обработал 2033
строки; 69 неоднозначных строк
помещены в карантин. Из 182
извлечённых исходных фактов к текущим вариантам безопасно применены
95 уникальных исходных фактов.
Исходная шкала единиц и применимость сохранены. Отдельно 244
AZ/RU-подписей — представление уже существующих значений, не дополнительные
технические факты.

## Источники, доступ и измеренное время

10 годовых US брошюр производителя Audi/Hyundai/Toyota/Nissan получены через
опубликованные индексы; 239 PDF-страниц просмотрены программным индексатором,
44 страницы отобраны как технические. Документы и SHA/локаторы проверены в
[`documents.json`](../deliverables/VerifiedData/us-bulk-data-08/documents.json).
Дополнительные идентификаторы поколения подтверждены документами производителя
на NHTSA. Свежий официальный EPA ZIP использован как
[candidate index](../deliverables/VerifiedData/us-bulk-data-08/epa-summary.md):
7 302 строк для 74 моделей master-list, **0** заводских конфигураций опубликовано
из EPA без отдельного matching. Lemon Manuals проверен ограниченными прямыми
запросами; `robots.txt` и целевая страница завершились connect timeout, так что
данных из Lemon в этом batch **0**. Подробный
[receipt](../deliverables/VerifiedData/us-bulk-data-08/lemon-access.md).

| Операция | Тип | Фактическое wall time |
|---|---|---:|
| Найти точные ссылки в индексах брошюр, успешный проход | Программно | 0.358 s |
| Скачать 10 PDF | Программно / сеть | 22.751 s |
| Извлечь PDF, cold / warm cache | Программно | 2.051 s / 0.380 s |
| Разобрать 25 Kia HTML из локального cache | Программно | 1.105 s |
| EPA candidate index, cold / warm cache | Программно | 0.932 s / 0.020 s |
| Подготовить reviewed manifest | Программно | 4.229 s |
| Опубликовать новый catalogue manifest после устранения name conflict | Программно | 5.708 s |
| Опубликовать Kia enrichment | Программно | 18.452 s |
| Полная backend regression (последний записанный прогон) | Программно | 49.780 s |
| Разбор неоднозначной применимости таблиц/моделей | Агент, отдельная проверка | Индивидуальное время не инструментировано; не включено в программные замеры |
| Deployment package | Программно | В отдельном packaging receipt после сборки |

Быстрый content-hash cache устранил повторное извлечение одного и того же PDF/EPA
содержимого: PDF cold/warm и EPA cold/warm показаны выше. Это сравнение одного
входа при разных состояниях cache, не доказательство ускорения относительно
старого importer на идентичной нагрузке. Длительность сетевого чтения и
ручного разбора не замаскирована под время парсера.

## Оставшаяся очередь owner master-list

| Make | Model | Область / причина |
|---|---|---|
| BMW | 4 Series | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Audi | A5 | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Volkswagen | Arteon | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Hyundai | Kona | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Toyota | Prius | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Land Rover | Range Rover Sport | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Land Rover | Discovery Sport | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Chevrolet | Equinox | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Lexus | GX | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Infiniti | FX | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Jeep | Cherokee | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Cadillac | CTS | Следующее непокрытое семейство master-list; годы и варианты будут выбраны по локальной релевантности до следующего batch |
| Tesla | Model 3 | Нужна датированная US technical identity; сохранены конкретные holds Model S2016 / Model3 2020; не запрет всей марки |
| Tesla | Model Y | Нужна датированная US technical identity; сохранены конкретные holds Model S2016 / Model3 2020; не запрет всей марки |
| Tesla | Model S | Нужна датированная US technical identity; сохранены конкретные holds Model S2016 / Model3 2020; не запрет всей марки |
| Tesla | Model X | Нужна датированная US technical identity; сохранены конкретные holds Model S2016 / Model3 2020; не запрет всей марки |

Осталось 16 названных, пока не покрытых модельных позиций из
предыдущей очереди. Внутри уже опубликованных моделей также остаются другие
годы, кузова, двигатели и рынки; готовность в таблицах выше не распространяется
на них. Следующий batch должен брать эти записи по локальной релевантности,
приоритету марки и году, затем по качеству доступных источников. Телефон,
Hetzner, ownership-cost, глубокие досье, изображения и коммерция отложены.
