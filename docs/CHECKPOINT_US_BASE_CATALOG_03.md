# Auto Expert — U.S. base catalogue, batch03

Отчёт приведён к формату владельца **2026-09-22**. Состав сверён с существующей
локальной БД и scope `US_BASE_2000`; новые автомобильные данные этим исправлением не публиковались.

<!-- BEGIN VEHICLE CATALOG TABLES -->
## Delta from previous batch — us-base-catalog-03

Полный список новых, изменённых и повторно опубликованных версий batch.
`ADDED` — новая запись; `CHANGED` — изменились факты (поля указаны в Status);
`EVIDENCE_REFRESH` — обновление ревизии/provenance без изменения значений.
`ENTERED_STRICT_SCOPED` — существующая версия впервые прошла строгий gate.
`NOT_IN_STRICT_OUTPUT` — сохранена в базовом каталоге, но недоступна в текущей строгой выдаче.
`EXCLUDED` — исключена из выдачи. Область любого статуса ограничена указанными годами и связкой.

| Make | Model | Generation | USA market | Model years | Engine | Transmission | Drivetrain | Body | Seats | Configuration count | Status |
|---|---|---|---|---|---|---|---|---|---|---:|---|
| Mercedes-Benz | C-Class | W205 sedan | USA | 2017 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | AWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2015–2016 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | AWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2017 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | RWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2015–2016 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | RWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2018 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | AWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2018 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | RWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Volkswagen | Passat | NMS North American sedan; FACELIFT | USA | 2016–2017 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed Tiptronic automatic | FWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Volkswagen | Passat | NMS North American sedan; FACELIFT | USA | 2018–2019 | 2.0L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=174 | 6-speed Tiptronic automatic | FWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Volkswagen | Passat | NMS North American sedan; FACELIFT | USA | 2016–2018 | 3.6L FSI narrow-angle VR6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 6-speed DSG dual-clutch | FWD | SEDAN | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 5-speed manual | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed Tiptronic automatic | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 2.0L TDI inline-4 turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=150 | 6-speed DSG dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 2.0L TDI inline-4 turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=150 | 6-speed manual | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 3.6L FSI narrow-angle VR6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 6-speed DSG dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Hyundai | Elantra | AD / ADa sedan; FACELIFT | USA | 2019 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 2 (2019: 2) | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Elantra | AD / ADa sedan; FACELIFT | USA | 2019 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual (SE) | FWD | SEDAN | UNKNOWN | 1 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Elantra | AD / ADa sedan; FACELIFT | USA | 2020 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Intelligent Variable Transmission (chain CVT) | FWD | SEDAN | UNKNOWN | 2 (2020: 2) | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2017 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 (2017: 2) | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2018 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 2 (2018: 2) | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2017 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual (SE) | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2018 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual (SE) | FWD | SEDAN | UNKNOWN | 1 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Sonata | LF / LFa sedan | USA | 2017 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed EcoShift dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Hyundai | Sonata | LF / LFa sedan | USA | 2015–2016, 2018–2019 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed EcoShift dual-clutch | FWD | SEDAN | UNKNOWN | 4 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Sonata | LF / LFa sedan | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Hyundai | Sonata | LF / LFa sedan | USA | 2015–2016 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Sonata | LF / LFa sedan | USA | 2018–2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 8-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Hyundai | Sonata | LF / LFa sedan | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Hyundai | Sonata | LF / LFa sedan | USA | 2015–2016, 2018–2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | UNKNOWN | 4 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Optima | JF / JFa sedan | USA | 2016, 2018–2020 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | UNKNOWN | 4 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Optima | JF / JFa sedan | USA | 2016, 2018–2020 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 4 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Optima | JF / JFa sedan | USA | 2016, 2018–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 4 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 2 | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | AWD | SUV | 7 | 2 | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | FWD | SUV | 7 | 2 | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 3 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 3 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 6 (2016: 2, 2017: 2, 2018: 2) | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 3 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; FACELIFT | USA | 2020–2022 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 1 | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 1 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 1 | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 1 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 (2018: 2) | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 (2017: 2) | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 2 (2019: 2) | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 (2018: 2) | CHANGED / ENTERED_STRICT_SCOPED; changed: seats |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 (2017: 2) | EVIDENCE_REFRESH / STRICT_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2019 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 2 (2019: 2) | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 2.5L Atkinson inline-4 + Toyota Hybrid System; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2020 | 2.5L D-4S inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | Direct Shift 8-speed automatic | AWD | SEDAN | 5 | 1 | ADDED / STRICT_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 2.5L D-4S inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | Direct Shift 8-speed automatic | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 3.5L D-4S V6 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=301 | Direct Shift 8-speed automatic | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 2.5L DOHC inline-4; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 3.5L DOHC V6; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Honda | Accord | IX sedan facelift | USA | 2016–2017 | 2.4L i-VTEC direct-injection inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed manual | FWD | SEDAN | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Honda | Accord | IX sedan facelift | USA | 2016–2017 | 2.4L i-VTEC direct-injection inline-4; powertrain=ICE; fuel=GASOLINE | Continuously variable transmission | FWD | SEDAN | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Honda | Accord | IX sedan facelift | USA | 2016–2017 | 3.5L i-VTEC V6 with VCM; powertrain=ICE; fuel=GASOLINE; power_hp=278 | 6-speed automatic with Sport Mode | FWD | SEDAN | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Honda | Accord | X sedan | USA | 2018 | 1.5L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=192 | 6-speed manual (Sport) | FWD | SEDAN | 5 | 1 | ADDED / STRICT_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 1.5L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=192 | Continuously variable transmission | FWD | SEDAN | 5 | 1 | ADDED / STRICT_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=252 | 10-speed automatic with Shift-By-Wire | FWD | SEDAN | 5 | 1 | ADDED / STRICT_SCOPED |
| Land Rover | Range Rover Evoque | LV five-door SUV | USA | 2017 | 2.0L turbo inline-4 (240 hp); powertrain=ICE; fuel=GASOLINE; power_hp=240 | 9-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Land Rover | Range Rover Evoque | LV five-door SUV | USA | 2018 | Ingenium Si4 2.0L turbo inline-4 (237 hp); powertrain=ICE; fuel=GASOLINE; power_hp=237 | 9-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Land Rover | Range Rover Evoque | LV five-door SUV | USA | 2018 | Ingenium Si4 2.0L turbo inline-4 (286 hp); powertrain=ICE; fuel=GASOLINE; power_hp=286 | 9-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017–2019 | 1.4L turbo gasoline inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017–2018 | 1.4L turbo gasoline inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed manual | FWD | SEDAN | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017–2018 | 1.6L turbo diesel inline-4; powertrain=ICE; fuel=DIESEL | 6-speed manual | FWD | SEDAN | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017–2019 | 1.6L turbo diesel inline-4; powertrain=ICE; fuel=DIESEL | 9-speed automatic | FWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Lexus | ES | VI sedan | USA | 2016–2018 | ES300h 2.5L Atkinson inline-4 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Lexus | ES | VI sedan | USA | 2016–2018 | ES350 3.5L V6; powertrain=ICE; fuel=GASOLINE; power_hp=268 | 6-speed electronically controlled automatic | FWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | ADDED / NOT_IN_STRICT_OUTPUT |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | RWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | RWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 5.7L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 5.7L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 6.2L supercharged V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 6.2L supercharged V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2020 | 6.4L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 6.4L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mitsubishi | Outlander | III SUV | USA | 2018 | 2.4L MIVEC inline-4; engine_code=4J12; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | AWD | SUV | 7 | 1 | ADDED / STRICT_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2018 | 2.4L MIVEC inline-4; engine_code=4J12; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | FWD | SUV | 7 | 1 | ADDED / STRICT_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2019 | 2.4L MIVEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | AWD | SUV | 7 | 1 | ADDED / STRICT_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2019 | 2.4L MIVEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=166 | Continuously variable transmission | FWD | SUV | 7 | 1 | ADDED / STRICT_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2018 | 3.0L MIVEC V6; engine_code=6B31; powertrain=ICE; fuel=GASOLINE; power_hp=224 | 6-speed electronic automatic | AWD | SUV | 7 | 1 | ADDED / STRICT_SCOPED |
| Mitsubishi | Outlander | III SUV | USA | 2019 | 3.0L MIVEC V6; powertrain=ICE; fuel=GASOLINE; power_hp=224 | 6-speed electronic automatic | AWD | SUV | 7 | 1 | ADDED / STRICT_SCOPED |
| Cadillac | SRX | 2010 redesign SUV (2010-REDESIGN) | USA | 2014–2016 | 3.6L direct-injection VVT V6; powertrain=ICE; fuel=GASOLINE; power_hp=308 | 6-speed automatic with Performance Algorithm Shifting | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Cadillac | SRX | 2010 redesign SUV (2010-REDESIGN) | USA | 2014–2016 | 3.6L direct-injection VVT V6; powertrain=ICE; fuel=GASOLINE; power_hp=308 | 6-speed automatic with Performance Algorithm Shifting | FWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |

## Cumulative strict-output catalog — весь доступный каталог

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
| Mercedes-Benz | C-Class | W205 sedan | USA | 2017 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2017 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 7G-TRONIC 7-speed automatic | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2018 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | C-Class | W205 sedan | USA | 2018 | C300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | RWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLC-Class | X253 SUV | USA | 2018 | GLC300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Mercedes-Benz | GLC-Class | X253 SUV | USA | 2018 | GLC300 2.0L inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=241 | 9G-TRONIC 9-speed automatic | RWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 528i 2.0L inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 528i 2.0L inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535d 3.0L inline-6 turbo; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535d 3.0L inline-6 turbo; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535i 3.0L inline-6 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 6-speed manual | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535i 3.0L inline-6 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 535i 3.0L inline-6 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 550i 4.4L V8 biturbo; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| BMW | 5 Series | F10 sedan | USA | 2014–2015 | 550i 4.4L V8 biturbo; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic | RWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 6-speed manual | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | Q5 | 8R SUV | USA | 2014–2017 | 2.0 TFSI direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 4 | AVAILABLE_SCOPED |
| Audi | Q5 | 8R SUV | USA | 2014–2015 | 3.0 TDI direct injection; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Audi | Q5 | 8R SUV | USA | 2014–2017 | 3.0 TFSI direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=272 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 4 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 5-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 1.8L TSI inline-4 turbo; powertrain=ICE; fuel=GASOLINE; power_hp=170 | 6-speed Tiptronic automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 2.0L TDI inline-4 turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=150 | 6-speed DSG dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 2.0L TDI inline-4 turbo diesel; powertrain=ICE; fuel=DIESEL; power_hp=150 | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Passat | NMS North American sedan; PRE_FACELIFT | USA | 2015 | 3.6L FSI narrow-angle VR6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 6-speed DSG dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Volkswagen | Tiguan | II US long-wheelbase SUV (II-US-LWB) | USA | 2018–2020 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=184 | 8-speed Tiptronic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Volkswagen | Tiguan | II US long-wheelbase SUV (II-US-LWB) | USA | 2018–2020 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=184 | 8-speed Tiptronic automatic | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Volkswagen | Tiguan | II US long-wheelbase SUV (II-US-LWB) | USA | 2018–2020 | 2.0 TSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=184 | 8-speed Tiptronic automatic | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2017 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 2 (2017: 2) | AVAILABLE_SCOPED |
| Hyundai | Elantra | AD / ADa sedan; PRE_FACELIFT | USA | 2017 | Nu 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual (SE) | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2017 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed EcoShift dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Hyundai | Sonata | LF / LFa sedan | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed SHIFTRONIC automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2019 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Forte | BD / BDm sedan | USA | 2019 | 2.0L MPI Atkinson inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | Intelligent Variable Transmission (CVT) | FWD | SEDAN | 5 | 2 (2019: 2) | AVAILABLE_SCOPED |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed automatic | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Forte | YD / YDm sedan | USA | 2017–2018 | 2.0L MPI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=147 | 6-speed manual | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 1.6L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=178 | 7-speed dry dual-clutch | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=245 | 6-speed automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Optima | JF / JFa sedan | USA | 2017 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 6-speed automatic | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | AWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; FACELIFT | USA | 2019–2020 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 8-speed Sportmatic automatic | FWD | SUV | 7 | 2 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 7 | 6 (2016: 2, 2017: 2, 2018: 2) | AVAILABLE_SCOPED |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 3.3L GDI V6; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2018 | 2.0L T-GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | 5 | 4 (2017: 2, 2018: 2) | AVAILABLE_SCOPED |
| Kia | Sportage | QL crossover; PRE_FACELIFT | USA | 2017–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | 5 | 4 (2017: 2, 2018: 2) | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 2.5L Atkinson inline-4 + Toyota Hybrid System; powertrain=HEV; fuel=GASOLINE | Electronically controlled continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2020 | 2.5L D-4S inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | Direct Shift 8-speed automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 2.5L D-4S inline-4 gasoline; powertrain=ICE; fuel=GASOLINE | Direct Shift 8-speed automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Toyota | Camry | VIII sedan (2018 redesign) | USA | 2018–2020 | 3.5L D-4S V6 gasoline; powertrain=ICE; fuel=GASOLINE; power_hp=301 | Direct Shift 8-speed automatic | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 2.5L DOHC inline-4; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 3.5L DOHC V6; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 1.5L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=192 | 6-speed manual (Sport) | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 1.5L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=192 | Continuously variable transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Honda | Accord | X sedan | USA | 2018 | 2.0L turbo direct-injection inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=252 | 10-speed automatic with Shift-By-Wire | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
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
| Cadillac | SRX | 2010 redesign SUV (2010-REDESIGN) | USA | 2014–2016 | 3.6L direct-injection VVT V6; powertrain=ICE; fuel=GASOLINE; power_hp=308 | 6-speed automatic with Performance Algorithm Shifting | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Cadillac | SRX | 2010 redesign SUV (2010-REDESIGN) | USA | 2014–2016 | 3.6L direct-injection VVT V6; powertrain=ICE; fuel=GASOLINE; power_hp=308 | 6-speed automatic with Performance Algorithm Shifting | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
<!-- END VEHICLE CATALOG TABLES -->

Публикация batch: **2026-09-21**, backend **0.8.1**, существующий проект и локальная БД.
**`us-base-catalog-03` опубликован; проверки PASS. Общий этап PARTIAL.**

Добавлены **95 новых годовых конфигураций десяти новых моделей / десяти марок**.
Обновлены **120 существующих записей** без замены их идентификаторов; среди прежних
200 seating gaps закрыты **39**, остаются **161**. Обновление записи само по себе
не считается закрытием пробела. Всего batch обработал 215 записей через существующий pipeline.

## Какие 6 марок были покрыты и какие 11 ещё не были

На входе, после batch02, **6 из 17** имели подтверждённую базовую технику:
**Mercedes-Benz, BMW, Audi, Volkswagen, Hyundai, Kia**.

На входе **11 из 17** такого покрытия не имели:
**Toyota, Nissan, Honda, Land Rover, Chevrolet, Lexus, Infiniti, Jeep, Mitsubishi, Cadillac, Tesla**.

Batch03 добавил первые десять марок из этой группы. Сейчас базовая техника есть у
**16 из 17**, без подтверждённой базовой области остаётся **Tesla**.
По текущему строгому контракту, включающему места, пригодная область есть у **12 из 17**.
Строгой области пока нет у **Land Rover, Chevrolet, Lexus, Infiniti, Tesla**.
Ноль — отсутствие подтверждённого покрытия, а не отсутствие марки в Азербайджане.

## Накопительный результат и прирост к batch02

| Показатель | Базовая техника (прирост) | Strict-output с подтверждёнными местами (прирост) |
|---|---:|---:|
| Марки | 16 (+10) | 12 (+7) |
| Модели | 28 (+10) | 19 (+11) |
| Поколения | 30 (+11) | 20 (+11) |
| Поколение × рынок | 30 (+11) | 20 (+11) |
| Варианты двигателей | 74 (+27) | 43 (+26) |
| Варианты коробок | 62 (+20) | 37 (+22) |
| Допустимые двигатель / коробка | 98 (+31) | 54 (+32) |
| Сочетания с учётом привода | 132 (+39) | 72 (+40) |
| Годовые конфигурации | 366 (+95) | 146 (+75) |
| Модели с пригодной для filter/resolver областью | 28 (+10) | 19 (+11) |

**Готовность текущего этапа: 146 конфигураций 19 моделей.**
Остальные базовые записи не выдаются как готовые в `US_BASE_2000`. Basic coverage
отражает подтверждённую технику без seating gate и не подменяет strict readiness.
Новые 95 конфигураций дали 36 strict-output записей; ещё 39 получены закрытием старых пробелов.

Счётчики относятся к конкретным подтверждённым подмножествам годов, кузовов и сочетаний,
а не всему модельному ряду. Honda Accord IX/X — одна модель и два поколения.
Market variant = поколение × рынок; текущий рынок только US. Двигатели и коробки
дедуплицированы в рамках поколения и рынка; их списки не перемножаются.
BMW 330i MY2025 остаётся отдельным pipeline proof, в этих базовых счётчиках не участвует.

## Покрытие каждой из 17 марок

| Марка | Модели, база | Поколения | Двигатели | Коробки | E/T сочетания | Годовые конфигурации | Strict: модели / конфигурации |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mercedes-Benz | 3 | 3 | 5 | 4 | 6 | 30 | 2 / 6 |
| BMW | 2 | 2 | 9 | 4 | 14 | 54 | 1 / 18 |
| Audi | 2 | 2 | 4 | 4 | 6 | 19 | 2 / 19 |
| Volkswagen | 3 | 3 | 8 | 9 | 12 | 30 | 2 / 14 |
| Hyundai | 3 | 3 | 7 | 8 | 10 | 46 | 2 / 6 |
| Kia | 5 | 6 | 14 | 13 | 19 | 92 | 4 / 47 |
| Toyota | 1 | 1 | 3 | 2 | 3 | 10 | 1 / 10 |
| Nissan | 1 | 1 | 2 | 1 | 2 | 6 | 1 / 6 |
| Honda | 1 | 2 | 4 | 6 | 6 | 9 | 1 / 3 |
| Land Rover | 1 | 1 | 3 | 1 | 3 | 3 | 0 / 0 |
| Chevrolet | 1 | 1 | 2 | 3 | 4 | 10 | 0 / 0 |
| Lexus | 1 | 1 | 2 | 2 | 2 | 6 | 0 / 0 |
| Infiniti | 1 | 1 | 4 | 1 | 4 | 24 | 0 / 0 |
| Jeep | 1 | 1 | 4 | 1 | 4 | 15 | 1 / 5 |
| Mitsubishi | 1 | 1 | 2 | 2 | 2 | 6 | 1 / 6 |
| Cadillac | 1 | 1 | 1 | 1 | 1 | 6 | 1 / 6 |
| Tesla | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |

## Новые подтверждённые области

| Модель | Поколение | US model years | Базовых конфигураций | Strict с местами |
|---|---|---|---:|---:|
| Toyota Camry | VIII | 2018–2020 | 10 | 10 |
| Nissan Altima | L33 | 2016–2018 | 6 | 6 |
| Honda Accord | IX | 2016–2017 | 6 | 0 |
| Honda Accord | X | 2018–2018 | 3 | 3 |
| Land Rover Range Rover Evoque | LV | 2017–2018 | 3 | 0 |
| Chevrolet Cruze | II | 2017–2019 | 10 | 0 |
| Lexus ES | VI | 2016–2018 | 6 | 0 |
| Infiniti Q50 | V37 | 2016–2018 | 24 | 0 |
| Jeep Grand Cherokee | WK-2011 | 2018–2020 | 15 | 5 |
| Mitsubishi Outlander | III | 2018–2019 | 6 | 6 |
| Cadillac SRX | 2010-REDESIGN | 2014–2016 | 6 | 6 |

[Подробные связки двигатель / коробка / привод и годовые источники](../deliverables/VerifiedData/us-base-catalog-03/scopes.md).
[Неизменяемый manifest](../data/manifests/us-base-catalog-batch-03.json) содержит
годовую применимость, кузова, исключения и documentary locators для каждой группы.
`2010-REDESIGN` для SRX — внутренний идентификатор, не выдуманный chassis code.
`WK-2011` отделяет новое поколение Grand Cherokee от предшественника с похожим кодом.

## Закрытие мест среди прежних 200 конфигураций

| Модель | Подтверждённые MY | Закрыто старых конфигураций |
|---|---|---:|
| Hyundai Elantra | 2017 | 3 |
| Hyundai Sonata | 2017 | 3 |
| Kia Optima | 2017 | 3 |
| Kia Sorento | 2016, 2017, 2018 | 15 |
| Kia Sportage | 2018 | 6 |
| Mercedes-Benz C-Class | 2017, 2018 | 4 |
| Volkswagen Passat | 2015 | 5 |

**Старый cohort: 200 → 39 закрыто → 161 осталось.** Новые семейства добавили
ещё **59 seating gaps**; всего теперь **220** базовых конфигураций без достаточного
подтверждения мест. Рост общего числа gaps связан с расширением техники, не с потерей фактов.
В [coverage.json](../deliverables/VerifiedData/us-base-catalog-03/coverage.json) сохранены
точные `catalog_key` закрытых и оставшихся записей; прогресс не считается по числу перезаписей.

Sorento MY2016–2018: V6 — 7 мест, 2.0T — 5, по таблицам Kia; для 2.4 сочетание
5/опционально7 не сведено к одному числу. Для новых моделей места подтверждены
в Camry/Altima/Outlander/SRX по annual factory tables, Accord2018 по руководству
с отдельными таблицами 1.5L/2.0L, Grand Cherokee только MY2020 (front2/rear3).
Число мест не перенесено автоматически на соседние годы.

## Доказательства, ограничения и конфликты

Проверены **87 уникальных RawDocument**: URL, источник, SHA-256, локатор и
полная годовая применимость. Заводские брошюры на публичных зеркалах имеют отдельно
издателя и адрес размещения. Зеркала не объявлены официальными сайтами производителя.
Основные технические таблицы — ежегодные US factory brochures; NHTSA-hosted manufacturer
communications используются здесь для обозначения поколений, а не для known issues.
Generation-only материалы из других стран не поставляют US комплектации или агрегаты.

Привод Honda/Cruze/Grand Cherokee дополнительно привязан к точным годовым EPA tuples:
make/model/displacement/transmission description/year. В provenance привода сохранены
EPA row IDs, собственный RawDocument и hash. Устройство коробки подтверждает заводской
документ, а не количество виртуальных передач EPA. Повторного EPA download не было.

- Evoque2018: конфликт единиц torque между таблицами; крутящий момент не импортирован.
- Cruze2018 diesel: строка мощности повторяет бензиновые значения; diesel power исключена.
- Cruze2019: EPA row40470 с variable ratios противоречит заводским 6AT/9AT; CVT не добавлен.
- Grand Cherokee2018: ошибочное «nine gears» в прозе против явных 8AT и точных EPA tuples;
  используется подтверждённая 8AT. Общая мощность SRT на диапазон лет не назначена.
- Accord IX: V6 manual coupe не перенесён на sedan. Accord X 2.0T manual оставлен за
  пределами пакета до однозначной проверки наследования оснащения в trim table.
- Outlander2020 пока вне области: найденная брошюра не подтверждает устройство коробки.
- Tesla Model S: приобретённые открытые factory brochures не устанавливают внутри
  документа нужную MY applicability и gearbox specification. Имя файла не является
  достаточным evidence; записей ready не создано. Исследование Tesla не задержало остальные марки.

[Реестр доказательств](../deliverables/VerifiedData/us-base-catalog-03/documents.json) ·
[Acquisition receipts](../deliverables/VerifiedData/base-catalog-acquisition.json) ·
[Основные acquisition URLs](../data/manifests/us-base-03-acquisition.json).
Supplemental, supplemental-2 и seating acquisition manifests лежат рядом.
Неуспешные HTTP/TLS запросы сохранены как неуспешные; содержимое для них не выдумано.
Платных provider calls **0**. Raw PDF/HTML хранится локально, не в публичных архивах.

## Проверка и сохранность

- [Сверка нового формата отчёта](../deliverables/VerifiedData/us-base-catalog-03/reporting-format-validation.json):
  полный delta, полный cumulative, точное совпадение конфигураций с пользовательским API.
  [Правила следующих checkpoint](CATALOG_CHECKPOINT_REPORTING.md) закреплены в policy и генераторе.
- Resolver: все **215** целевых конфигураций; оба языка фильтров для всех 18 областей.
  Проверены строгие seating scopes, неправильные сочетания и отрицательные запросы.
- Регрессия **340 PASS**; две прежние dependency deprecation warnings. Ruff PASS для
  изменённых Python-файлов. Новые проверки исключают borrowing drive evidence из
  другого модельного года, CVT или неподходящего привода.
- Live HTTP: **47 PASS**, результаты в [live-http.json](../deliverables/VerifiedData/us-base-catalog-03/live-http.json);
  проверяется фактическая выдача каждой из 17 марок в AZ/RU, подбор без марки,
  профиль/сравнение, Tiguan AWD5/7, неизвестный бюджет, исключение CA/Skoda.
- [DB preservation PASS](../deliverables/VerifiedData/us-base-catalog-03/preservation.json):
  integrity/FK PASS, нет удалений и неожиданных изменений; прежние ревизии/отчёты сохранены.
- [Повтор публикации PASS](../deliverables/VerifiedData/us-base-catalog-03/idempotency.json):
  215 записей / 22 существующих jobs, логический digest всей БД не изменился.
- **UI_UNCHANGED: PASS**, SHA-256 всех 18 файлов совпадает с baseline.
  Новый UI не создавался. Браузерный визуальный прогон batch02 сохранён как исторический;
  в этом batch он не заявляется новым real-device тестом.
- Телефон и Hetzner **DEFERRED_BY_USER**. APK не пересобирался. Ownership-cost,
  глубокие dossiers, изображения и реклама в этом пакете не разрабатывались.

## Воспроизводимость и deployment package

Локальный backend: http://127.0.0.1:8000/preview/. Активный manifest выбирается из policy.
Подготовленные batch01/02/03 неизменяемы; изменения выпускаются следующим batch.
Повтор публикации на этой же БД использует сохранённые prepared revisions и source IDs.

```powershell
python scripts/checkpoint_base_catalog.py --baseline deliverables/VerifiedData/us-base-03-baseline.json --previous-coverage deliverables/VerifiedData/us-base-catalog-02/coverage.json
python scripts/smoke_us_catalog.py
python -m pytest -q
```

При подготовке batch03 полный Honda manual превысил штатные32MiB. Использован существующий
процессный параметр `AUTOEXPERT_KNOWLEDGE_IMPORT_MAX_BYTES=67108864` (64MiB) только для
локального import command; конфигурация API, .env и дефолт32MiB не изменялись.
На этой машине App Control блокирует project .venv/python.exe; использован уже имеющийся
bundled Python3.12 с установленными зависимостями проекта через PYTHONPATH.
Защита Windows/TLS не менялась. `Start-Local.ps1 -PythonExecutable <absolute-path>` поддержан.

[Source/deployment archive](../deliverables/VerifiedData/AutoExpert_0.8.1_VerifiedData_Source_Deployment.zip)
и [QA archive](../deliverables/VerifiedData/AutoExpert_0.8.1_VerifiedData_QA.zip) обновлены.
Они исключают .env/секреты, живую БД, private raw cache, account/session metadata.
**Распаковка не переносит готовую БД.** В новой среде нужны acquisition, mapping
RawDocument/revision IDs и review; локальные prepared IDs нельзя применять к другой БД.
Предыдущий portable fact bundle остаётся research baseline. Runbook подготовлен,
развёртывание не выполнялось; коммерческие права на все документы не заявлены.

## Продолжение очереди

Приоритеты 17 марок сохранены в [policy](../data/manifests/az-market-priority-policy.json).
Далее пакетно расширять её модельные семейства и проверенные диапазоны USMY2000+;
отдельно закрывать 161 старых и 59 новых seating gaps. Для Tesla продолжить
по датированным US homologation/manual источникам, без угадывания по названию PDF.
Turbo.az остаётся ручным внешним ориентиром, не ingestion source; точных counts нет.
Приоритет владельца достаточен для работы. Ни crawler, ни фиктивная выгрузка не создавались.
Другие рынки и Skoda вне текущего пакета. Ownership, изображения, глубокие dossiers,
телефон и сервер не становятся gate.

[Предыдущий checkpoint batch02](CHECKPOINT_US_BASE_CATALOG_02.md).
