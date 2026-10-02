# Auto Expert — U.S. base catalogue, batch06

Backend0.8.1. Опубликовано в существующей локальной БД после batch05. Правила publication/search и утверждённый UI неизменны. Все статусы относятся к точным связкам, не ко всей модели.

<!-- BEGIN VEHICLE CATALOG TABLES -->
## Delta from previous batch — us-base-catalog-06

Полный список новых, изменённых и повторно опубликованных версий batch.
`ADDED` — новая запись; `CHANGED` — изменились факты (поля указаны в Status);
`EVIDENCE_REFRESH` — обновление ревизии/provenance без изменения значений.
`ENTERED_STRICT_SCOPED` — существующая версия впервые прошла строгий gate.
`NOT_IN_STRICT_OUTPUT` — сохранена в базовом каталоге, но недоступна в текущей строгой выдаче.
`EXCLUDED` — исключена из выдачи. Область любого статуса ограничена указанными годами и связкой.

| Make | Model | Generation | USA market | Model years | Engine | Transmission | Drivetrain | Body | Seats | Configuration count | Status |
|---|---|---|---|---|---|---|---|---|---|---:|---|
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2017 | AMG GLE43 3.0L biturbo V6; powertrain=ICE; fuel=GASOLINE; power_hp=362 | AMG-enhanced 9G-TRONIC 9-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | AMG GLE43 3.0L biturbo V6; powertrain=ICE; fuel=GASOLINE; power_hp=385 | AMG-enhanced 9G-TRONIC 9-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | AMG GLE63 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=550 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | AMG GLE63 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=550 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | AMG GLE63 S 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=577 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | AMG GLE63 S 5.5L biturbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=577 | AMG SPEEDSHIFT PLUS 7-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016 | GLE300d BlueTEC 2.1L twin-turbo diesel inline-4; powertrain=ICE; fuel=DIESEL; power_hp=201 | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | RWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | GLE350 3.5L direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=302 | 7G-TRONIC 7-speed automatic | RWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016 | GLE400 3.0L biturbo direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=329 | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2017 | GLE400 3.0L biturbo direct-injection V6; powertrain=ICE; fuel=GASOLINE; power_hp=329 | 9G-TRONIC 9-speed automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2018 | GLE550e 3.0L biturbo V6 + plug-in hybrid motor; powertrain=PHEV; fuel=GASOLINE | 7G-TRONIC 7-speed automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Mercedes-Benz | GLE-Class | 166 SUV (GLE facelift) | USA | 2016–2017 | GLE550e 3.0L biturbo V6 + plug-in hybrid motor; powertrain=PHEV; fuel=GASOLINE | 7G-TRONIC 7-speed automatic | AWD | SUV | UNKNOWN | 2 | ADDED / NOT_IN_STRICT_OUTPUT |
| BMW | X5 | F15 | USA | 2014, 2016 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; engine_code=N55B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic; code=8HP45 | AWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2014, 2016 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; engine_code=N55B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic; code=8HP45 | RWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2015 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| BMW | X5 | F15 | USA | 2015 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic | RWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| BMW | X5 | F15 | USA | 2014 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; engine_code=N57D30O1; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic; code=8HP70 | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; engine_code=N57D30O1; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic; code=8HP75 | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2015 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| BMW | X5 | F15 | USA | 2016 | xDrive40e N20 2.0L TwinPower Turbo inline-4 + electric motor; engine_code=N20B20O0; powertrain=PHEV; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic (plug-in hybrid) | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2014 | xDrive50i 4.4L TwinPower Turbo V8; engine_code=N63B44O1; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic; code=8HP70 | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive50i 4.4L TwinPower Turbo V8; engine_code=N63B44O1; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic; code=8HP75 | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| BMW | X5 | F15 | USA | 2015 | xDrive50i 4.4L TwinPower Turbo V8; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 1 | ADDED / STRICT_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 1 | ADDED / STRICT_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2012 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | multitronic continuously variable transmission | FWD | SEDAN | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 2 | ADDED / STRICT_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 2 | ADDED / STRICT_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 3.0 TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 2 | ADDED / STRICT_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013–2015 | 3.0 TFSI supercharged V6; powertrain=ICE; fuel=GASOLINE; power_hp=310 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2012 | 3.0 TFSI supercharged V6; powertrain=ICE; fuel=GASOLINE; power_hp=310 | 8-speed Tiptronic automatic | AWD | SEDAN | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Volkswagen | Touareg | 7P (second US generation); FACELIFT | USA | 2015 | 3.0L TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); FACELIFT | USA | 2015 | 3.0L supercharged V6 + electric motor; powertrain=HEV; fuel=GASOLINE | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); FACELIFT | USA | 2015 | 3.6L FSI narrow-angle V6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); PRE_FACELIFT | USA | 2013–2014 | 3.0L TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); PRE_FACELIFT | USA | 2013–2014 | 3.0L supercharged V6 + electric motor; powertrain=HEV; fuel=GASOLINE | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| Volkswagen | Touareg | 7P (second US generation); PRE_FACELIFT | USA | 2013–2014 | 3.6L FSI narrow-angle V6; powertrain=ICE; fuel=GASOLINE; power_hp=280 | 8-speed automatic (4MOTION) | AWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2015 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2015 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 2 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=264 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2016 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=265 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2016 | 2.0L GDI inline-4 twin-scroll turbo; powertrain=ICE; fuel=GASOLINE; power_hp=265 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 1 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | AWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2014–2016 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | FWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Hyundai | Santa Fe Sport | AN short-body Sport | USA | 2013 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=190 | 6-speed SHIFTRONIC automatic | FWD | SUV | UNKNOWN | 1 | ADDED / NOT_IN_STRICT_OUTPUT |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Dual VVT-i; powertrain=ICE; fuel=GASOLINE; power_hp=132 | 4-speed ECT-i automatic | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Dual VVT-i; powertrain=ICE; fuel=GASOLINE; power_hp=132 | 6-speed manual | FWD | SEDAN | 5 | 6 (2014: 2, 2015: 2, 2016: 2) | ADDED / STRICT_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Dual VVT-i; powertrain=ICE; fuel=GASOLINE; power_hp=132 | CVTi-S continuously variable transmission | FWD | SEDAN | 5 | 6 (2014: 2, 2015: 2, 2016: 2) | ADDED / STRICT_SCOPED |
| Toyota | Corolla | XI sedan (US 2014 redesign) | USA | 2014–2016 | 1.8L DOHC inline-4 Valvematic; powertrain=ICE; fuel=GASOLINE; power_hp=140 | CVTi-S continuously variable transmission | FWD | SEDAN | 5 | 3 | ADDED / STRICT_SCOPED |
| Honda | CR-V | IV (US 2012 redesign) | USA | 2012–2014 | 2.4L DOHC i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 5-speed automatic | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Honda | CR-V | IV (US 2012 redesign) | USA | 2012–2014 | 2.4L DOHC i-VTEC inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=185 | 5-speed automatic | FWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.4L turbo gasoline inline-4; engine_code=LE2; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, coolant, engine_code, engine_oil_capacity_l, engine_oil_specification, engine_oil_viscosity, fuel_tank_us_gal, transmission_fluid |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.4L turbo gasoline inline-4; engine_code=LE2; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, coolant, engine_code, engine_oil_capacity_l, engine_oil_specification, engine_oil_viscosity, transmission_fluid |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017, 2019 | 1.4L turbo gasoline inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017 | 1.4L turbo gasoline inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=153 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.6L turbo diesel inline-4; engine_code=LH7; powertrain=ICE; fuel=DIESEL | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, coolant, engine_code, engine_oil_capacity_l, engine_oil_specification, engine_oil_viscosity, transmission_fluid |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2018 | 1.6L turbo diesel inline-4; engine_code=LH7; powertrain=ICE; fuel=DIESEL | 9-speed automatic | FWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, coolant, engine_code, engine_oil_capacity_l, engine_oil_specification, engine_oil_viscosity, transmission_fluid |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017 | 1.6L turbo diesel inline-4; powertrain=ICE; fuel=DIESEL | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Chevrolet | Cruze | II sedan (VIN B generation) | USA | 2017, 2019 | 1.6L turbo diesel inline-4; powertrain=ICE; fuel=DIESEL | 9-speed automatic | FWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 6-speed ECT-i automatic | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 6-speed ECT-i automatic | FWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 8-speed ECT-i automatic (F Sport) | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX450h 3.5L Atkinson V6 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | ECVT-i electronically controlled continuously variable transmission | AWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX450h 3.5L Atkinson V6 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | ECVT-i electronically controlled continuously variable transmission | FWD | SUV | 5 | 3 | ADDED / STRICT_SCOPED |
| Infiniti | Q50 | V37 sedan | USA | 2017 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, engine_oil_capacity_l, fuel_grade, octane_aki, transmission_fluid |
| Infiniti | Q50 | V37 sedan | USA | 2016, 2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2017 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, engine_oil_capacity_l, fuel_grade, octane_aki, transmission_fluid |
| Infiniti | Q50 | V37 sedan | USA | 2016, 2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2017 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, engine_oil_capacity_l, fuel_grade, octane_aki, transmission_fluid |
| Infiniti | Q50 | V37 sedan | USA | 2016, 2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2017 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, engine_oil_capacity_l, fuel_grade, octane_aki, transmission_fluid |
| Infiniti | Q50 | V37 sedan | USA | 2016, 2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2017 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, engine_oil_capacity_l, fuel_grade, octane_aki, transmission_fluid |
| Infiniti | Q50 | V37 sedan | USA | 2016, 2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |
| Infiniti | Q50 | V37 sedan | USA | 2017 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 1 | CHANGED / NOT_IN_STRICT_OUTPUT; changed: brake_fluid, engine_oil_capacity_l, fuel_grade, octane_aki, transmission_fluid |
| Infiniti | Q50 | V37 sedan | USA | 2016, 2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 2 | EVIDENCE_REFRESH / NOT_IN_STRICT_OUTPUT |

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
| BMW | X5 | F15 | USA | 2014, 2016 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; engine_code=N55B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic; code=8HP45 | AWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014, 2016 | sDrive35i / xDrive35i 3.0L TwinPower Turbo inline-6; engine_code=N55B30M0; powertrain=ICE; fuel=GASOLINE; power_hp=300 | 8-speed Steptronic automatic; code=8HP45 | RWD | SUV | 5 | 2 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; engine_code=N57D30O1; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic; code=8HP70 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive35d 3.0L TwinPower Turbo diesel inline-6; engine_code=N57D30O1; powertrain=ICE; fuel=DIESEL; power_hp=255 | 8-speed Steptronic automatic; code=8HP75 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive40e N20 2.0L TwinPower Turbo inline-4 + electric motor; engine_code=N20B20O0; powertrain=PHEV; fuel=GASOLINE; power_hp=240 | 8-speed Steptronic automatic (plug-in hybrid) | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2014 | xDrive50i 4.4L TwinPower Turbo V8; engine_code=N63B44O1; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic; code=8HP70 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| BMW | X5 | F15 | USA | 2016 | xDrive50i 4.4L TwinPower Turbo V8; engine_code=N63B44O1; powertrain=ICE; fuel=GASOLINE; power_hp=445 | 8-speed Steptronic automatic; code=8HP75 | AWD | SUV | 5 | 1 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 6-speed manual | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A4 | B8 / 8K sedan | USA | 2014–2016 | 2.0 TFSI inline-4 turbo direct injection; powertrain=ICE; fuel=GASOLINE; power_hp=220 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=211 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 1 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 2.0 TFSI turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=220 | multitronic continuously variable transmission | FWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2014–2015 | 3.0 TDI turbo diesel V6; powertrain=ICE; fuel=DIESEL; power_hp=240 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 2 | AVAILABLE_SCOPED |
| Audi | A6 | 4G sedan (US 2012 redesign) | USA | 2013–2015 | 3.0 TFSI supercharged V6; powertrain=ICE; fuel=GASOLINE; power_hp=310 | 8-speed Tiptronic automatic | AWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
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
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 2.5L DOHC inline-4; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Altima | L33 sedan | USA | 2016–2018 | 3.5L DOHC V6; powertrain=ICE; fuel=GASOLINE | Xtronic continuously variable transmission | FWD | SEDAN | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | AWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Nissan | Rogue | T32 | USA | 2014–2016 | QR25DE 2.5L DOHC inline-4; engine_code=QR25DE; powertrain=ICE; fuel=GASOLINE; power_hp=170 | Xtronic CVT | FWD | SUV | 7 | 3 | AVAILABLE_SCOPED |
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
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 6-speed ECT-i automatic | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 6-speed ECT-i automatic | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX350 3.5L Dual VVT-i V6; powertrain=ICE; fuel=GASOLINE; power_hp=270 | 8-speed ECT-i automatic (F Sport) | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX450h 3.5L Atkinson V6 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | ECVT-i electronically controlled continuously variable transmission | AWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
| Lexus | RX | III (US 2010 redesign) | USA | 2013–2015 | RX450h 3.5L Atkinson V6 + Lexus Hybrid Drive; powertrain=HEV; fuel=GASOLINE | ECVT-i electronically controlled continuously variable transmission | FWD | SUV | 5 | 3 | AVAILABLE_SCOPED |
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
| Kia | Rio | SC sedan | USA | 2018 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed automatic | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Rio | SC sedan | USA | 2018 | Gamma 1.6L GDI inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=130 | 6-speed manual | FWD | SEDAN | UNKNOWN | 1 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | AWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Kia | Sorento | UM / UMa crossover; PRE_FACELIFT | USA | 2016–2018 | 2.4L GDI inline-4; powertrain=ICE; fuel=GASOLINE | 6-speed Sportmatic automatic | FWD | SUV | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
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
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 2.0t turbo inline-4; powertrain=ICE; fuel=GASOLINE; power_hp=208 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.0t twin-turbo V6 (300 hp); powertrain=ICE; fuel=GASOLINE; power_hp=300 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | 3.5L V6 + Direct Response Hybrid; powertrain=HEV; fuel=GASOLINE | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | AWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Infiniti | Q50 | V37 sedan | USA | 2016–2018 | Red Sport twin-turbo V6 (400 hp); powertrain=ICE; fuel=GASOLINE; power_hp=400 | 7-speed electronically controlled automatic | RWD | SEDAN | UNKNOWN | 3 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 3.6L Pentastar V6; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | RWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 5.7L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 6.2L supercharged V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |
| Jeep | Grand Cherokee | WK (2011 redesign) SUV (WK-2011) | USA | 2018–2019 | 6.4L HEMI V8; powertrain=ICE; fuel=GASOLINE | 8-speed automatic | AWD | SUV | UNKNOWN | 2 | AVAILABLE_WITHOUT_SEAT_CONSTRAINT / SEATS_UNKNOWN |

<!-- END VEHICLE CATALOG TABLES -->

[Delta с источниками](../deliverables/VerifiedData/us-base-catalog-06/delta-with-sources.md) · [Все модели и годы](../deliverables/VerifiedData/us-base-catalog-06/models-and-years.md) · [Фактически заполненные разделы](../deliverables/VerifiedData/us-base-catalog-06/technical-coverage.md) · [Значения / AZ/RU / provenance](../deliverables/VerifiedData/us-base-catalog-06/technical-fields.json) · [Остаток мест](../deliverables/VerifiedData/us-base-catalog-06/remaining-seating.md) · [План и факт](../deliverables/VerifiedData/us-base-catalog-06/plan-vs-actual.md) · [Оставшийся master-list](../deliverables/VerifiedData/us-base-catalog-06/remaining-master-queue.md).

## Краткий накопительный перечень

| Make | Model | Generation | Строгий критерий: US MY | Дополнительно без ограничения мест: US MY |
|---|---|---|---|---|
| Mercedes-Benz | C-Class | W205 | 2017–2018 | 2015–2016 |
| Mercedes-Benz | E-Class | W212 | — | 2014–2016 |
| Mercedes-Benz | GLC-Class | X253 | 2018 | 2017, 2019 |
| Mercedes-Benz | GLE-Class | 166 | 2018 | 2016–2017 |
| BMW | 3 Series | F30 | 2016–2018 | — |
| BMW | 5 Series | F10 | 2014–2015 | — |
| BMW | X5 | F15 | 2014, 2016 | 2015 |
| Audi | A4 | 8K | 2014–2016 | — |
| Audi | A6 | 4G | 2013–2015 | 2012 |
| Audi | Q5 | 8R | 2014–2017 | — |
| Volkswagen | Jetta | VI | — | 2017–2018 |
| Volkswagen | Passat | NMS | 2015 | 2016–2019 |
| Volkswagen | Tiguan | II-US-LWB | 2018–2020 | — |
| Volkswagen | Touareg | 7P | 2013–2015 | — |
| Hyundai | Elantra | AD | 2017–2020 | — |
| Hyundai | Elantra | CN7 | 2021 | 2021–2023 |
| Hyundai | Elantra | MD/UD | 2014, 2016 | 2011–2013, 2015 |
| Hyundai | Santa Fe Sport | AN | 2014–2016 | 2013 |
| Hyundai | Sonata | LF | 2015, 2017–2019 | 2016 |
| Hyundai | Sonata | YF | — | 2011–2013 |
| Hyundai | Tucson | TL | 2016, 2019 | 2017–2018, 2020 |
| Kia | Forte | BD | 2019–2020 | — |
| Kia | Forte | YD | 2017–2018 | — |
| Kia | K5 | DL3 | 2021 | 2022–2023 |
| Kia | Optima | JF | 2016–2019 | 2020 |
| Kia | Rio | SC | 2019–2020 | 2018 |
| Kia | Sorento | UM | 2016–2020 | 2016–2018 |
| Kia | Sportage | QL | 2017–2022 | — |
| Toyota | Camry | V | 2002–2006 | — |
| Toyota | Camry | VI | 2007–2011 | — |
| Toyota | Camry | VII | 2012–2017 | — |
| Toyota | Camry | VIII | 2018–2020 | — |
| Toyota | Corolla | XI | 2014–2016 | — |
| Nissan | Altima | L33 | 2016–2018 | — |
| Nissan | Rogue | T32 | 2014–2016 | — |
| Honda | Accord | IX | 2016–2017 | — |
| Honda | Accord | VII | 2003, 2006–2007 | — |
| Honda | Accord | X | 2018 | — |
| Honda | CR-V | IV | 2012–2014 | — |
| Land Rover | Range Rover Evoque | LV | — | 2017–2018 |
| Chevrolet | Cruze | II | — | 2017–2019 |
| Lexus | ES | VI | — | 2016–2018 |
| Lexus | RX | III | 2013–2015 | — |
| Infiniti | Q50 | V37 | — | 2016–2018 |
| Jeep | Grand Cherokee | WK-2011 | 2020 | 2018–2019 |
| Mitsubishi | Outlander | III | 2018–2019 | — |
| Cadillac | SRX | 2010-REDESIGN | 2014–2016 | — |

## Сверенные итоги после поимённых списков

| Метрика | Было basic | Стало basic | Было strict | Стало strict |
|---|---|---|---|---|
| makes | 16 | 16 | 12 | 13 |
| models | 30 | 38 | 24 | 32 |
| generations | 39 | 47 | 32 | 40 |
| market_variants | 39 | 47 | 32 | 40 |
| engine_variants | 98 | 122 | 76 | 98 |
| transmission_variants | 89 | 106 | 70 | 86 |
| engine_transmission_combinations | 133 | 162 | 103 | 129 |
| drivetrain_combinations | 169 | 205 | 132 | 165 |
| model_year_configurations | 488 | 598 | 335 | 421 |

| Марка | Моделей basic | Моделей strict | Годовых basic | Годовых strict |
|---|---|---|---|---|
| Mercedes-Benz | 4 | 3 | 50 | 12 |
| BMW | 3 | 3 | 67 | 63 |
| Audi | 3 | 3 | 32 | 30 |
| Volkswagen | 4 | 3 | 39 | 23 |
| Hyundai | 4 | 4 | 99 | 52 |
| Kia | 6 | 6 | 101 | 84 |
| Toyota | 2 | 2 | 81 | 81 |
| Nissan | 2 | 2 | 18 | 18 |
| Honda | 2 | 2 | 26 | 26 |
| Land Rover | 1 | 0 | 3 | 0 |
| Chevrolet | 1 | 0 | 10 | 0 |
| Lexus | 2 | 1 | 21 | 15 |
| Infiniti | 1 | 0 | 24 | 0 |
| Jeep | 1 | 1 | 15 | 5 |
| Mitsubishi | 1 | 1 | 6 | 6 |
| Cadillac | 1 | 1 | 6 | 6 |
| Tesla | 0 | 0 | 0 | 0 |

```json
{
  "delta_actions": {
    "ADDED": 110,
    "CHANGED": 10,
    "EVIDENCE_REFRESH": 24
  },
  "new_available_configurations": 110,
  "new_excluded_configurations": 0,
  "new_configurations_by_period": {
    "2014–2020": 89,
    "2000–2013": 21
  },
  "profiles_checked_az_ru": 598,
  "technical_fields_with_source": 11633,
  "seating_cohorts": {
    "old_143": {
      "initial": 143,
      "closed": 0,
      "remaining": 143
    },
    "introduced_in_batch05_10": {
      "initial": 10,
      "closed": 0,
      "remaining": 10
    },
    "introduced_in_batch06": {
      "count": 24
    }
  }
}
```

Проверки, ограничения и перенос: [BATCH06_VALIDATION.md](BATCH06_VALIDATION.md). Старый checkpoint05 сохранён отдельно.
