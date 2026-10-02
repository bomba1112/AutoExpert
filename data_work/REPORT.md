# Итоговый отчёт: база технических данных US (все марки Приложения A)

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py; отчёты по маркам — data_work/<марка>/REPORT.md.

## 1. Матрица покрытия

Обозначения: ● заполнено, ◐ частично, ○ нет, — неприменимо (электромобиль). Поля по разделу 4 промта.

Статус марок:

| Марка | Статус | Последний коммит марки |
|---|---|---|
| Hyundai | загружена | 0ec3c41 data(us): Hyundai, Kia — table cells read correctly, earlier wrong values replaced |
| Kia | загружена | 0ec3c41 data(us): Hyundai, Kia — table cells read correctly, earlier wrong values replaced |
| Toyota | загружена (Camry — принятая ранее линейка) | 2550256 data(us): Toyota — owner's manual fluids and capacities, press specifications (Cor |
| Mercedes-Benz | загружена | 788fd0d data(us): Mercedes-Benz — oil, fluids and maintenance gaps closed where sources al |
| BMW | загружена | 40e3af4 data(us): BMW — owner's manual facts, press specifications, CarComplaints (second  |
| Chevrolet | загружена | f9c8adf data(us): Chevrolet — owner's manual facts, press specifications, CarComplaints (s |
| Ford | загружена | f070be0 data(us): Ford — owner's manual facts, press specifications, CarComplaints (second |
| Lexus | загружена | db1fbdc data(us): Lexus — owner's manual facts, press specifications, CarComplaints (secon |
| Honda | загружена | ea5a550 data(us): Honda — owner's manual facts, press specifications, CarComplaints (secon |
| Nissan | загружена | 653c09b data(us): Nissan — owner's manual facts, press specifications, CarComplaints (seco |
| Land Rover | загружена | bec9c2d data(us): Land Rover — owner's manual facts, press specifications, CarComplaints ( |
| Infiniti | загружена до решения об остановке, оставлена как есть | f47df93 data(us): Infiniti — first load: base layer (EPA, vPIC, NHTSA, known issues), manu |
| Cadillac | не загружена (решение владельца) | a72994d chore(us-batch): prepared extraction and staging for Cadillac, Jeep, Mitsubishi (n |
| Jeep | не загружена (решение владельца) | 692e7a6 chore(us-batch): scripts and staging snapshot before the next load pass |
| Audi | загружена | 73fdc49 data(us): Audi — first load: base layer (EPA, vPIC, NHTSA, known issues), manual a |
| Volkswagen | загружена | e96b2ee data(us): Volkswagen — first load: base layer (EPA, vPIC, NHTSA, known issues), ma |
| Mitsubishi | не загружена (решение владельца) | 692e7a6 chore(us-batch): scripts and staging snapshot before the next load pass |
| Tesla | загружена | 0ac8e0d data(us): Tesla — first load: base layer (EPA, vPIC, NHTSA, known issues), manual  |

### Hyundai

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sonata | YF | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Sonata | LF | 2015–2019 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Sonata | DN8 | 2020–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Elantra | MD/UD | 2014–2016 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Elantra | AD | 2017–2020 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Elantra | CN7 | 2021–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ◐ | ● | ◐ | ● | ● | ● |
| Tucson | US2014-2015 | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Tucson | TL | 2016–2021 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Tucson | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ● | ● | ● |
| Santa Fe | NC | 2014–2018 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ● | ● |
| Santa Fe | US2019-2023 | 2019–2023 | ◐ | ◐ | ● | ● | ● | ● | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |
| Santa Fe | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| Santa Fe Sport | AN | 2014–2018 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Accent | RB | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Accent | US2018-2022 | 2018–2022 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Kona | OS | 2018–2023 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ◐ | ● | ● | ● | ● |
| Kona | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ● | ○ | ◐ | ◐ | ◐ | ● | ● | ● |

Итого ячеек: заполнено 132, частично 81, нет 42, неприменимо 0.

### Kia

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

### Toyota

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

### Mercedes-Benz

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C-Class | US2014-2014 | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ○ | ● | ○ | ◐ | ○ | ● | ● | ● |
| C-Class | W205 | 2015–2021 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| C-Class | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| E-Class | W212 | 2014–2016 | ◐ | ◐ | ● | ● | ○ | ● | ◐ | ◐ | ● | ○ | ◐ | ○ | ● | ● | ● |
| E-Class | US2017-2023 | 2017–2023 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| E-Class | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ○ | ● | ○ | ◐ | ○ | ● | ● | ● |
| S-Class | US2014-2020 | 2014–2020 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ○ | ● | ◐ | ● | ● | ● | ● | ● |
| S-Class | US2021+ | 2021–2026 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| GLA | US2015-2020 | 2015–2020 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| GLA | US2021+ | 2021–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| GLB | US2020+ | 2020–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ◐ | ● | ● | ● |
| GLC (+GLK) | US2014-2015 | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ○ | ● | ○ | ◐ | ○ | ● | ● | ● |
| GLC (+GLK) | X253 | 2016–2022 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| GLC (+GLK) | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ○ | ● | ○ | ◐ | ○ | ● | ● | ● |
| GLE (+ML) | 166 | 2014–2019 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| GLE (+ML) | US2020+ | 2020–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| GLS (+GL) | US2014-2019 | 2014–2019 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| GLS (+GL) | US2020+ | 2020–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| CLA | US2014-2019 | 2014–2019 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| CLA | US2020-2025 | 2020–2025 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| CLA | US2026+ | 2026–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ○ | ● | ○ | ◐ | ○ | ● | ● | ● |
| CLS | US2014-2018 | 2014–2018 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| CLS | US2019-2023 | 2019–2023 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ● | ◐ | ● | ● | ● | ● | ● |
| CLE | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ◐ | ○ | ● | ○ | ◐ | ○ | ● | ● | ● |
| AMG GT 4-Door | US2019+ | 2019–2026 | ◐ | ◐ | ● | ● | ● | ● | ◐ | ◐ | ● | ◐ | ◐ | ● | ● | ● | ● |
| EQS | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ● | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| EQB | US2022-2025 | 2022–2025 | ◐ | ◐ | ● | ● | ● | ● | — | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 223, частично 147, нет 33, неприменимо 2.

### BMW

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 Series | F30 | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| 3 Series | Seventh generation · US sedan | 2019–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| 5 Series | F10 | 2014–2016 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| 5 Series | G30 | 2017–2023 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| 5 Series | US2024+ | 2024–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| 7 Series | US2014-2015 | 2014–2015 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| 7 Series | US2016-2022 | 2016–2022 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| 7 Series | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| X5 | F15 | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| X5 | US2019+ | 2019–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| X6 | US2014-2014 | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| X6 | US2015-2019 | 2015–2019 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| X6 | US2020+ | 2020–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| X7 | US2019+ | 2019–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ○ | ○ | ◐ | ◐ | ○ | ● | ● | ● |
| M3 | US2015-2018 | 2015–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| M3 | US2021+ | 2021–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| M5 | US2014-2016 | 2014–2016 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| M5 | US2018-2023 | 2018–2023 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| M5 | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ◐ | ● | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| X5 M | US2015+ | 2015–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| X6 M | US2014-2019 | 2014–2019 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| X6 M | US2020+ | 2020–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |

Итого ячеек: заполнено 178, частично 79, нет 73, неприменимо 0.

### Chevrolet

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Malibu | VIII | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Malibu | IX | 2016–2025 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Cruze | US2014-2015 | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Cruze | II | 2016–2019 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Equinox | 2010 redesign (US) | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ◐ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Equinox | US2018-2024 | 2018–2024 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Equinox | US2025+ | 2025–2026 | ◐ | ◐ | ● | ● | ● | ◐ | ● | ◐ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| Trax | US2015-2022 | 2015–2022 | ◐ | ◐ | ● | ● | ○ | ◐ | ● | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Trax | US2024+ | 2024–2026 | ◐ | ◐ | ● | ● | ○ | ● | ● | ◐ | ○ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 53, частично 49, нет 33, неприменимо 0.

### Ford

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fusion | US2014-2020 | 2014–2020 | ◐ | ◐ | ● | ● | ○ | ● | ◐ | ● | ○ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 7, частично 4, нет 4, неприменимо 0.

### Lexus

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | VI | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| ES | US2019-2025 | 2019–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| ES | US2026+ | 2026–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| RX | III | 2014–2015 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| RX | AL20 | 2016–2022 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| RX | US2023+ | 2023–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| NX | I-US-2015 | 2015–2021 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| NX | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ◐ | ● | ● | ● |
| GX | II (2010 redesign) | 2014–2023 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| GX | US2024+ | 2024–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ● | ◐ | ● | ● | ● |

Итого ячеек: заполнено 79, частично 36, нет 35, неприменимо 0.

### Honda

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Accord | IX | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Accord | X | 2018–2022 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Accord | US2023+ | 2023–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ● | ● | ● | ● | ● |
| Civic | IX Sedan | 2014–2015 | ● | ◐ | ● | ● | ○ | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Civic | 10th | 2016–2021 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Civic | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| CR-V | IV | 2014–2016 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| CR-V | RW | 2017–2022 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| CR-V | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 85, частично 33, нет 17, неприменимо 0.

### Nissan

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Altima | L33 | 2014–2018 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Altima | US2019+ | 2019–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Sentra | B17 | 2014–2019 | ● | ◐ | ● | ● | ● | ● | ○ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Sentra | US2020-2025 | 2020–2025 | ● | ◐ | ● | ● | ● | ● | ◐ | ◐ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Sentra | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ◐ | ○ | ◐ | ◐ | ● | ● | ○ | ● |
| Rogue | T32 | 2014–2020 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Rogue | T33 | 2021–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Pathfinder | R52 | 2014–2020 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ● | ● | ● | ● | ● |
| Pathfinder | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 89, частично 34, нет 12, неприменимо 0.

### Land Rover

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Range Rover | L405 | 2014–2021 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Range Rover | US2022+ | 2022–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Range Rover Sport | L494 | 2014–2022 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Range Rover Sport | US2023+ | 2023–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Range Rover Evoque | LV | 2014–2019 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |
| Range Rover Evoque | US2020+ | 2020–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| Discovery Sport (+LR2) | US2014-2014 | 2014–2014 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Discovery Sport (+LR2) | L550 | 2015–2026 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 52, частично 31, нет 37, неприменимо 0.

### Infiniti

_Загружена до получения решения владельца остановить загрузку этой группы марок (коммит f47df93); по решению владельца оставлена как есть._

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q50 | V37 | 2014–2024 | ● | ◐ | ● | ● | ● | ● | ● | ● | ○ | ◐ | ● | ● | ● | ● | ● |
| QX60 (+JX) | L50 | 2014–2020 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ● | ◐ | ● | ● | ● |
| QX60 (+JX) | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ◐ | ● | ● | ● | ● |
| FX / QX70 | US2014-2017 | 2014–2017 | ● | ◐ | ● | ● | ● | ● | ◐ | ● | ○ | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 43, частично 13, нет 4, неприменимо 0.

### Cadillac

Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/cadillac/staging), в рабочей БД строк этого конвейера нет.

### Jeep

Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/jeep/staging), в рабочей БД строк этого конвейера нет.

### Audi

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A3 | 8V Sedan | 2015–2020 | ◐ | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ○ | ● | ● | ● |
| A3 | US2022+ | 2022–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| A4 | 8K | 2014–2016 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| A4 | 8W | 2017–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| A5 | 8T/8F | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| A5 | US2018-2024 | 2018–2024 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● |
| A5 | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| A6 | 4G | 2014–2018 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| A6 | US2019-2025 | 2019–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| A6 | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q3 | 8U | 2015–2018 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q3 | US2019-2025 | 2019–2025 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q3 | US2026+ | 2026–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q5 | 8R | 2014–2017 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q5 | FY | 2018–2024 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q5 | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |
| Q7 | 4L | 2014–2015 | ◐ | ◐ | ● | ● | ○ | ◐ | ○ | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Q7 | 4M | 2017–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ◐ | ◐ | ● | ● | ● |

Итого ячеек: заполнено 117, частично 81, нет 72, неприменимо 0.

### Volkswagen

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jetta | VI | 2014–2018 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| Jetta | VII | 2019–2026 | ● | ◐ | ● | ● | ○ | ● | ○ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| Passat | NMS | 2014–2022 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| Tiguan | 5N | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| Tiguan | II-US-LWB | 2018–2024 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| Tiguan | US2025+ | 2025–2026 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Atlas | I-US-2018 | 2018–2026 | ● | ◐ | ● | ● | ● | ◐ | ◐ | ◐ | ○ | ◐ | ◐ | ● | ● | ● | ● |
| Arteon | I | 2019–2024 | ● | ◐ | ● | ● | ● | ◐ | ○ | ◐ | ○ | ◐ | ● | ● | ● | ● | ● |
| Touareg | 7P | 2014–2017 | ● | ◐ | ● | ● | ● | ◐ | ○ | ○ | ○ | ◐ | ● | ● | ● | ● | ● |

Итого ячеек: заполнено 79, частично 39, нет 17, неприменимо 0.

### Mitsubishi

Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/mitsubishi/staging), в рабочей БД строк этого конвейера нет.

### Tesla

| Линейка | Поколение | Годы | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Model 3 | I | 2017–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model Y | I | 2020–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model S | I | 2014–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |
| Model X | I | 2016–2026 | ◐ | ◐ | ● | ● | ○ | ● | — | ○ | ○ | ○ | ◐ | ○ | ● | ● | ● |

Итого ячеек: заполнено 24, частично 12, нет 20, неприменимо 4.

## 2. Строки по таблицам: до и после

| Таблица | До f087 (бэкап 0959) | До пакета (бэкап 1308) | Сейчас |
|---|---|---|---|
| vehicle_makes | 32 | 31 | 31 |
| vehicle_models | 574 | 573 | 579 |
| vehicle_generations | 702 | 700 | 787 |
| vehicle_variants | 15592 | 15589 | 15589 |
| technical_evidence | 273086 | 274110 | 358679 |
| known_issues | 2 | 14 | 3648 |
| maintenance_schedule_items | None | 0 | 1346 |
| source_records | 24539 | 24651 | 29761 |
| raw_documents | 492 | 608 | 5752 |
| knowledge_sources | 45 | 45 | 48 |

По маркам (technical_evidence / known_issues / maintenance_schedule_items):

| Марка | До пакета | Сейчас |
|---|---|---|
| Hyundai | 0 / 0 / 0 | 7194 / 381 / 407 |
| Kia | 0 / 0 / 0 | 4585 / 265 / 639 |
| Toyota | 1031 / 14 / 0 | 6322 / 227 / 0 |
| Mercedes-Benz | 0 / 0 / 0 | 17046 / 436 / 300 |
| BMW | 0 / 0 / 0 | 11459 / 432 / 0 |
| Chevrolet | 0 / 0 / 0 | 3430 / 253 / 0 |
| Ford | 0 / 0 / 0 | 799 / 54 / 0 |
| Lexus | 0 / 0 / 0 | 4009 / 95 / 0 |
| Honda | 0 / 0 / 0 | 5896 / 212 / 0 |
| Nissan | 0 / 0 / 0 | 4154 / 211 / 0 |
| Land Rover | 0 / 0 / 0 | 3489 / 188 / 0 |
| Infiniti | 0 / 0 / 0 | 1940 / 74 / 0 |
| Cadillac | 0 / 0 / 0 | 0 / 0 / 0 |
| Jeep | 0 / 0 / 0 | 0 / 0 / 0 |
| Audi | 0 / 0 / 0 | 8143 / 384 / 0 |
| Volkswagen | 0 / 0 / 0 | 5566 / 304 / 0 |
| Mitsubishi | 0 / 0 / 0 | 0 / 0 / 0 |
| Tesla | 0 / 0 / 0 | 1568 / 132 / 0 |

## 3. Журнал пробелов

### Hyundai

Записей в журнале пробелов: 1092 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 304 | hyundai-sonata-us-2014-2.0l-4cyl-turbo-ice-a-6-spd-fwd; hyundai-sonata-us-2014-2.4l-4cyl-hev-a-am6-fwd; hyundai-sonata-us-2014-2.4l-4cyl-ice-a-6-spd-fwd |
| engine_oil_specification | engine not stated; EPA lists several engines | 57 | hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2021 (official-1d7deff217ee); hyundai/sonata MY2025 (official-1ef294fc7c15) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 52 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2025 (official-1ef294fc7c15) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 47 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2025 (official-1ef294fc7c15) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 41 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2021 (official-1d7deff217ee) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 38 | hyundai/sonata MY2020 (official-05793f63ce44); hyundai/sonata MY2022 (official-134672ecd168); hyundai/sonata MY2021 (official-1d7deff217ee) |
| maintenance transmission_fluid | interval text not understood: No check, No service required | 33 | hyundai/sonata official-68438b59abf9 p.514; hyundai/sonata official-68438b59abf9 p.519; hyundai/sonata official-4d3a1b125043 p.506 |
| maintenance engine_air_filter | irregular I marks at [N, N, N, N, N, N, N, N, N] xN,N miles | 22 | hyundai/sonata official-68438b59abf9 p.508; hyundai/sonata official-68438b59abf9 p.513; hyundai/sonata official-68438b59abf9 p.518 |
| compression_ratio | engine not stated; EPA lists several engines | 19 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |
| engine_description | engine not stated; EPA lists several engines | 14 | hyundai/sonata MY2017 (press-hyundainews-sonata-2017-5a6dc3df); hyundai/sonata MY2017 (press-hyundainews-sonata-2017-7eec1965); hyundai/sonata MY2018 (press-hyundainews-sonata-2018-6111a2b9) |

### Kia

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

### Toyota

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

### Mercedes-Benz

Записей в журнале пробелов: 3052 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 464 | mercedes-benz-c-class-us-2014-1.8l-4cyl-turbo-ice-a-7-spd-rwd; mercedes-benz-c-class-us-2014-3.5l-6cyl-ice-a-7-spd-4wd; mercedes-benz-c-class-us-2014-3.5l-6cyl-ice-a-7-spd-rwd |
| width_mm | one document gives N values: ['N', 'N'] | 306 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-74c4b66b); mercedes-benz/c-class MY2018 (press-mbusa-c-class-2018-1b962891); mercedes-benz/c-class MY2018 (press-mbusa-c-class-2018-3444a6c3) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 179 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| engine_description | engine not stated; EPA lists several engines | 178 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| power_hp | engine not stated; EPA lists several engines | 178 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| valvetrain | engine not stated; EPA lists several engines | 178 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| torque_lb_ft | engine not stated; EPA lists several engines | 177 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| compression_ratio | engine not stated; EPA lists several engines | 176 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| power_rpm | engine not stated; EPA lists several engines | 174 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |
| torque_rpm | engine not stated; EPA lists several engines | 174 | mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-0f585a9d); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-16da6fb0); mercedes-benz/c-class MY2017 (press-mbusa-c-class-2017-174be5ce) |

### BMW

Записей в журнале пробелов: 850 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 401 | bmw-3-series-us-2014-2.0l-4cyl-turbo-diesel-a-s8-awd; bmw-3-series-us-2014-2.0l-4cyl-turbo-diesel-a-s8-rwd; bmw-3-series-us-2014-2.0l-4cyl-turbo-ice-a-s8-awd |
| width_mm | one document gives N values: ['N', 'N'] | 59 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-69e983f2); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-9ede91b6) |
| transmission_description | one document gives N values: ['"automatic transmission"', '"automatic"'] | 21 | bmw/3-series MY2017 (press-bmwgroup-3-series-2017-69e983f2); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-839132a4); bmw/3-series MY2017 (press-bmwgroup-3-series-2017-9ede91b6) |
| octane_aki | one document gives N values: ['N', 'N'] | 16 | bmw/5-series MY2014 (mcum-5-series-4-door-2010-2017); bmw/5-series MY2015 (mcum-5-series-4-door-2010-2017); bmw/5-series MY2016 (mcum-5-series-4-door-2010-2017) |
| transmission_description | one document gives N values: ['"NHPN"', '"automatic transmission N"'] | 15 | bmw/3-series MY2014 (press-bmwgroup-3-series-2014-e1049003); bmw/3-series MY2014 (press-bmwgroup-3-series-2014-eec89c10); bmw/3-series MY2015 (press-bmwgroup-3-series-2015-0b4f3ad4) |
| engine_oil_capacity_l | no US owner's manual for these years | 15 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| engine_oil_viscosity | no US owner's manual for these years | 15 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| coolant | no US owner's manual for these years | 15 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| transmission_fluid | no US owner's manual for these years | 15 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |
| brake_fluid | no US owner's manual for these years | 15 | bmw/3-series F30; bmw/3-series Seventh generation · US sedan; bmw/5-series F10 |

### Chevrolet

Записей в журнале пробелов: 308 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 118 | chevrolet-malibu-us-2014-2.0l-4cyl-turbo-ice-a-s6-fwd; chevrolet-malibu-us-2014-2.4l-4cyl-hev-a-s6-fwd; chevrolet-malibu-us-2014-2.5l-4cyl-ice-a-s6-fwd |
| engine_oil_oem_approval | engine not stated; EPA lists several engines | 30 | chevrolet/malibu MY2022 (official-208c55b3d0b7); chevrolet/malibu MY2021 (official-6582638ee059); chevrolet/malibu MY2014 (official-7461695d71a7) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 21 | chevrolet/malibu MY2016 (official-f395cde9a52c); chevrolet/cruze MY2014 (official-1256553bcf46); chevrolet/cruze MY2019 (official-4d52e1c95054) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 18 | chevrolet/malibu MY2019 (official-881052775fa3); chevrolet/malibu MY2016 (official-ee9f43223777); chevrolet/malibu MY2018 (official-f212af069990) |
| transmission_fluid | not found unambiguously in the available US owner's manuals | 9 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| coolant | not found unambiguously in the available US owner's manuals | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| power_hp | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| torque_lb_ft | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| tires | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |
| front_suspension | no US press specification page for these years | 8 | chevrolet/malibu VIII; chevrolet/malibu IX; chevrolet/cruze US2014-2015 |

### Ford

Записей в журнале пробелов: 135 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 46 | ford-fusion-us-2014-1.5l-4cyl-turbo-ice-a-s6-fwd; ford-fusion-us-2014-1.6l-4cyl-turbo-ice-m-6-spd-fwd; ford-fusion-us-2014-2.0l-4cyl-hev-a-variable-gear-ratios-fwd |
| fuel_tank_l | value N outside the validator range; not used | 19 | ford/fusion carmans-2014-ford-fusion-hybrid p.152; ford/fusion carmans-2014-ford-fusion-hybrid p.220; ford/fusion carmans-2014-ford-fusion-hybrid p.220 |
| engine_oil_specification | engine not stated; EPA lists several engines | 19 | ford/fusion MY2014 (carmans-2014-ford-fusion); ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid); ford/fusion MY2015 (carmans-2015-ford-fusion) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 12 | ford/fusion MY2016 (carmans-2016-ford-fusion); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion) |
| fuel_tank_l | one document gives N values: ['N', 'N'] | 7 | ford/fusion MY2014 (carmans-2014-ford-fusion-hybrid); ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid) |
| coolant_capacity_l | value N outside the validator range; not used | 6 | ford/fusion carmans-2014-ford-fusion-hybrid p.301; ford/fusion carmans-2015-ford-fusion-hybrid p.320; ford/fusion carmans-2016-ford-fusion-hybrid p.321 |
| coolant_capacity_l | engine not stated; EPA lists several engines | 6 | ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid) |
| transmission_fluid_capacity_l | engine not stated; EPA lists several engines | 4 | ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid); ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 3 | ford/fusion MY2017 (carmans-2017-ford-fusion-hybrid); ford/fusion MY2018 (carmans-2018-ford-fusion-hybrid); ford/fusion MY2019 (carmans-2019-ford-fusion-hybrid) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 2 | ford/fusion MY2015 (carmans-2015-ford-fusion-hybrid); ford/fusion MY2016 (carmans-2016-ford-fusion-hybrid) |

### Lexus

Записей в журнале пробелов: 391 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 141 | lexus-es-us-2014-2.5l-4cyl-hev-a-av-s6-fwd; lexus-es-us-2014-3.5l-6cyl-ice-a-s6-fwd; lexus-es-us-2015-2.5l-4cyl-hev-a-av-s6-fwd |
| wheel_size_in | one document gives N values: ['N', 'N'] | 54 | lexus/es MY2014 (press-lexus-es-2014-177214e2); lexus/es MY2015 (press-lexus-es-2015-b472453e); lexus/es MY2016 (press-lexus-es-2016-4597186e) |
| width_mm | one document gives N values: ['N', 'N'] | 12 | lexus/nx MY2015 (press-lexus-nx-2015-956632da); lexus/nx MY2015 (press-lexus-nx-2015-c09ddda3); lexus/nx MY2016 (press-lexus-nx-2016-260ec3e9) |
| engine_oil_capacity_l | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| engine_oil_viscosity | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| coolant | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| transmission_fluid | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| brake_fluid | no US owner's manual for these years | 10 | lexus/es VI; lexus/es US2019-2025; lexus/es US2026+ |
| height_mm | one document gives N values: ['N', 'N'] | 9 | lexus/rx MY2019 (press-lexus-rx-2019-620346fa); lexus/rx MY2019 (press-lexus-rx-2019-fddbf21b); lexus/rx MY2020 (press-lexus-rx-2020-6092356b) |
| cargo_l | one document gives N values: ['N', 'N'] | 8 | lexus/rx MY2021 (press-lexus-rx-2021-8f65d05d); lexus/rx MY2022 (press-lexus-rx-2022-ebf3602b); lexus/nx MY2019 (press-lexus-nx-2019-0d4a6ae1) |

### Honda

Записей в журнале пробелов: 891 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 184 | honda-accord-us-2014-2.0l-4cyl-hev-a-variable-gear-ratios-fwd; honda-accord-us-2014-2.0l-4cyl-phev-a-variable-gear-ratios-fwd; honda-accord-us-2014-2.4l-4cyl-ice-a-av-s7-fwd |
| injection | engine not stated; EPA lists several engines | 51 | honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa); honda/accord MY2020 (press-hondanews-accord-2020-a5a61a10); honda/accord MY2020 (press-hondanews-accord-2020-c98c463a) |
| valvetrain | engine not stated; EPA lists several engines | 48 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| engine_displacement_cc | engine not stated; EPA lists several engines | 45 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| engine_description | engine not stated; EPA lists several engines | 45 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| fuel_tank_l | value N outside the validator range; not used | 43 | honda/accord carmans-2018-honda-accord p.698; honda/accord carmans-2018-honda-accord p.700; honda/accord carmans-2019-honda-accord p.702 |
| bore_stroke_mm | engine not stated; EPA lists several engines | 42 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| compression_ratio | engine not stated; EPA lists several engines | 41 | honda/accord MY2014 (press-hondanews-accord-2014-adf9af49); honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940) |
| power_hp | engine not stated; EPA lists several engines | 33 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |
| power_rpm | engine not stated; EPA lists several engines | 33 | honda/accord MY2014 (press-hondanews-accord-2014-f4af921d); honda/accord MY2015 (press-hondanews-accord-2015-da9d6940); honda/accord MY2017 (press-hondanews-accord-2017-15b93ffa) |

### Nissan

Записей в журнале пробелов: 412 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 122 | nissan-altima-us-2014-2.5l-4cyl-ice-a-variable-gear-ratios-fwd; nissan-altima-us-2014-3.5l-6cyl-ice-a-av-s7-fwd; nissan-altima-us-2015-2.5l-4cyl-ice-a-variable-gear-ratios-fwd |
| fuel_tank_l | value N outside the validator range; not used | 72 | nissan/altima carmans-2014-nissan-altima-sedan p.92; nissan/altima carmans-2015-nissan-altima-sedan p.97; nissan/altima carmans-2018-nissan-altima-sedan p.108 |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 29 | nissan/altima MY2015 (carmans-2015-nissan-altima-sedan); nissan/altima MY2016 (carmans-2016-nissan-altima-sedan); nissan/altima MY2019 (carmans-2019-nissan-altima-sedan) |
| coolant_capacity_l | engine not stated; EPA lists several engines | 24 | nissan/altima MY2015 (carmans-2015-nissan-altima-sedan); nissan/altima MY2017 (carmans-2017-nissan-altima-sedan); nissan/altima MY2018 (carmans-2018-nissan-altima-sedan) |
| engine_oil_capacity_drain_refill_l | engine not stated; EPA lists several engines | 19 | nissan/altima MY2017 (carmans-2017-nissan-altima-sedan); nissan/altima MY2018 (carmans-2018-nissan-altima-sedan); nissan/altima MY2019 (carmans-2019-nissan-altima-sedan) |
| engine_oil_capacity_without_filter_l | engine not stated; EPA lists several engines | 17 | nissan/altima MY2016 (carmans-2016-nissan-altima-sedan); nissan/altima MY2017 (carmans-2017-nissan-altima-sedan); nissan/altima MY2016 (official-d4f834985984) |
| octane_aki | one document gives N values: ['N', 'N'] | 15 | nissan/sentra MY2017 (carmans-2017-nissan-sentra); nissan/sentra MY2018 (carmans-2018-nissan-sentra); nissan/sentra MY2019 (carmans-2019-nissan-sentra) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N'] | 12 | nissan/altima MY2026 (official-531628333f60); nissan/altima MY2025 (official-627953d373ea); nissan/sentra MY2026 (official-511ec26d6b9d) |
| engine_oil_capacity_drain_refill_l | one document gives N values: ['N', 'N'] | 11 | nissan/altima MY2023 (carmans-2023-nissan-altima); nissan/altima MY2024 (official-02f7c81d0bf6); nissan/altima MY2026 (official-531628333f60) |
| engine_oil_capacity_l | one document gives N values: ['N', 'N'] | 10 | nissan/sentra MY2016 (carmans-2016-nissan-sentra); nissan/sentra MY2015 (official-56814c430d7c); nissan/sentra MY2016 (official-b930b0e01a9b) |

### Land Rover

Записей в журнале пробелов: 256 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 108 | land-rover-range-rover-us-2014-3.0l-6cyl-turbo-ice-a-s8-4wd; land-rover-range-rover-us-2014-5.0l-8cyl-turbo-ice-a-s8-4wd; land-rover-range-rover-us-2015-3.0l-6cyl-turbo-ice-a-s8-4wd |
| power_hp | one document gives N values: ['N', 'N'] | 10 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| torque_lb_ft | one document gives N values: ['N', 'N'] | 10 | land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover-sport MY2015 (press-jlr-range-rover-sport-2015-40a4dc03) |
| engine_oil_capacity_l | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| engine_oil_viscosity | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| coolant | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| transmission_fluid | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| brake_fluid | no US owner's manual for these years | 8 | land-rover/range-rover L405; land-rover/range-rover US2022+; land-rover/range-rover-sport L494 |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 6 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6) |
| turning_circle_m | one document gives N values: ['N', 'N'] | 4 | land-rover/range-rover MY2015 (press-jlr-range-rover-2015-3154d47e); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6); land-rover/range-rover MY2020 (press-jlr-range-rover-2020-fc9b8db6) |

### Infiniti

Записей в журнале пробелов: 194 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 81 | infiniti-q50-us-2014-3.5l-6cyl-hev-a-s7-awd; infiniti-q50-us-2014-3.5l-6cyl-hev-a-s7-rwd; infiniti-q50-us-2014-3.7l-6cyl-ice-a-s7-awd |
| octane_aki | one document gives N values: ['N', 'N'] | 23 | infiniti/q50 MY2017 (official-6c4f53e95a3b); infiniti/q50 MY2016 (official-8326bed2fcdc); infiniti/q50 MY2018 (official-859f6f6c908a) |
| fuel_tank_l | value N outside the validator range; not used | 15 | infiniti/qx60 official-0631da7f7255 p.182; infiniti/qx60 official-1d31600339bc p.115; infiniti/qx60 official-273175b7459f p.118 |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 8 | infiniti/q50 MY2020 (official-55b3819856e8); infiniti/q50 MY2024 (official-5893c25aeb89); infiniti/q50 MY2017 (official-7ca479957a94) |
| octane_ron | one document gives N values: ['N', 'N', 'N'] | 7 | infiniti/q50 MY2020 (official-55b3819856e8); infiniti/q50 MY2024 (official-5893c25aeb89); infiniti/q50 MY2018 (official-7ed9946bd145) |
| engine_oil_capacity_l | engine not stated; EPA lists several engines | 7 | infiniti/q50 MY2018 (official-7ed9946bd145); infiniti/q50 MY2018 (official-859f6f6c908a); infiniti/q50 MY2019 (official-b0b04e7a95d1) |
| engine_oil_capacity_without_filter_l | engine not stated; EPA lists several engines | 7 | infiniti/q50 MY2018 (official-859f6f6c908a); infiniti/qx60 MY2016 (official-1d31600339bc); infiniti/qx60 MY2015 (official-273175b7459f) |
| curb_weight_kg | one document gives N values: ['N', 'N', 'N'] | 7 | infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16); infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16); infiniti/fx-qx70 MY2014 (press-infinitinews-fx-qx70-2014-bf283b16) |
| engine_oil_capacity_without_filter_l | one document gives N values: ['N', 'N', 'N', 'N'] | 4 | infiniti/q50 MY2024 (official-5893c25aeb89); infiniti/q50 MY2022 (official-849f6a8b0c88); infiniti/q50 MY2021 (official-dfddd4dab604) |
| engine_oil_viscosity | engine not stated; EPA lists several engines | 4 | infiniti/q50 MY2017 (official-7ca479957a94); infiniti/q50 MY2016 (official-8326bed2fcdc); infiniti/q50 MY2016 (official-d2af3b4d6870) |

### Audi

Записей в журнале пробелов: 646 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 260 | audi-a3-us-2015-1.8l-4cyl-turbo-ice-a-am-s6-fwd; audi-a3-us-2015-2.0l-4cyl-turbo-diesel-a-am-s6-fwd; audi-a3-us-2015-2.0l-4cyl-turbo-ice-a-am-s6-awd |
| wheel_size_in | one document gives N values: ['N', 'N'] | 22 | audi/a3 MY2025 (press-audiusa-a3-2025-f4ef9cce); audi/a3 MY2025 (press-audiusa-a3-2025-f4ef9cce); audi/a3 MY2026 (press-audiusa-a3-2026-2a9484c7) |
| wheelbase_mm | one document gives N values: ['N', 'N'] | 18 | audi/a3 MY2015 (press-audiusa-a3-2015-cacf8499); audi/a3 MY2022 (press-audiusa-a3-2022-ae51d2b9); audi/a3 MY2025 (press-audiusa-a3-2025-f4ef9cce) |
| engine_oil_capacity_l | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| engine_oil_viscosity | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| coolant | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| transmission_fluid | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| brake_fluid | no US owner's manual for these years | 17 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| ground_clearance | not found unambiguously in the available US press specification pages | 13 | audi/a3 8V Sedan; audi/a3 US2022+; audi/a4 8K |
| front_brakes | not found unambiguously in the available US press specification pages | 10 | audi/a3 8V Sedan; audi/a4 8K; audi/a4 8W |

### Volkswagen

Записей в журнале пробелов: 730 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 163 | volkswagen-jetta-us-2014-1.4l-4cyl-turbo-hev-a-am-s7-fwd; volkswagen-jetta-us-2014-1.8l-4cyl-turbo-ice-a-s6-fwd; volkswagen-jetta-us-2014-1.8l-4cyl-turbo-ice-m-5-spd-fwd |
| engine_oil_capacity_drain_refill_l | value N outside the validator range; not used | 55 | volkswagen/jetta carmans-2019-volkswagen-jetta p.249; volkswagen/jetta carmans-2019-volkswagen-jetta p.250; volkswagen/jetta carmans-2019-volkswagen-jetta p.252 |
| octane_aki | one document gives N values: ['N', 'N', 'N'] | 42 | volkswagen/jetta MY2014 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2015 (mcum-jetta-4-door-2011-2018); volkswagen/jetta MY2016 (mcum-jetta-4-door-2011-2018) |
| fuel_tank_l | value N outside the validator range; not used | 36 | volkswagen/jetta carmans-2022-volkswagen-jetta p.342; volkswagen/jetta carmans-2023-volkswagen-jetta-2 p.342; volkswagen/jetta mcum-jetta-4-door-2011-2018 p.151 |
| curb_weight_kg | one document gives N values: ['N', 'N'] | 31 | volkswagen/jetta MY2014 (press-vw-jetta-2014-0fb78ecb); volkswagen/jetta MY2014 (press-vw-jetta-2014-0fb78ecb); volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f) |
| wheel_size_in | one document gives N values: ['N', 'N'] | 27 | volkswagen/jetta MY2014 (press-vw-jetta-2014-0fb78ecb); volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-ecdd49ac) |
| bore_stroke_in | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| bore_stroke_mm | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| compression_ratio | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |
| engine_description | engine not stated; EPA lists several engines | 22 | volkswagen/jetta MY2014 (press-vw-jetta-2014-2842b69f); volkswagen/jetta MY2014 (press-vw-jetta-2014-60013743); volkswagen/jetta MY2015 (press-vw-jetta-2015-b0f357a9) |

### Tesla

Записей в журнале пробелов: 112 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 60 | tesla-model-3-us-2017-ev-bev-a-a1-rwd; tesla-model-3-us-2018-ev-bev-a-a1-awd; tesla-model-3-us-2018-ev-bev-a-a1-rwd |
| engine_oil_capacity_l | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| engine_oil_viscosity | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| coolant | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| transmission_fluid | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| brake_fluid | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| fuel_tank_l | no US owner's manual for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| tires | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| front_suspension | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |
| rear_suspension | no US press specification page for these years | 4 | tesla/model-3 I; tesla/model-y I; tesla/model-s I |

Закрытые и заблокированные источники (manifest):

- media.cadillac.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- media.chevrolet.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- media.ford.com: {'blocked': 2}; robots.txt answered 403 on https://media.ford.com/robots.txt; scripted access refused, host stopped
- media.gm.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- media.stellantisnorthamerica.com: {'blocked': 41}; robots.txt disallows / for ClaudeBot, Claude-Web, anthropic-ai (Anthropic AI agents); host not crawled
- news.gm.com: {'ok': 24, 'blocked': 1}; stopped after 403 on POST https://news.gm.com/content/public/us/en/gm-news/home/search/jcr:content/par/channelbox_1738069849/par/multicollectionsolrs.search.solr
- pressroom.chevrolet.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- www.kiamedia.com: {'blocked': 5}; robots.txt disallows / for ClaudeBot, Claude-Web, anthropic-ai (Anthropic AI agents); host not crawled
- assets.sia.toyota.com: {'skipped': 28}; AccessDenied from this network (geo-restricted)
- mmna-ssb.my.salesforce.com: {'skipped': 18}; robots.txt disallows
- owners.hyundaiusa.com: {'skipped': 78}; robots.txt disallows /content/
- www.bmwusa.com: {'skipped': 116}; refuses scripted clients (bot protection); browser-only
- www.fordservicecontent.com: {'skipped': 100}; refuses scripted clients (bot protection); browser-only
- www.tesla.com: {'skipped': 16}; Akamai refuses scripted clients

## 4. Конфликты источников и решения

### Hyundai

Конфликтов: 78. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 74
- official document kept over the copy: 4

### Kia

Конфликтов: 11. По решениям:

- model-year manual kept over the whole-generation page (Appendix E.6): 10
- official document kept over the copy: 1

### Toyota

Конфликтов: 174. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 164
- model-year manual kept over the whole-generation page (Appendix E.6): 5
- Product Information 2017 gives Tread Width (Front/Rear) 62.0/61.6 in. : 2
- Product Information sheets 2014-2017 state 'With filter L4 : 4.7qt' (4: 1
- Product Information 2021-2024 gives 15.8 gal. for front-wheel-drive gr: 1
- Hybrid Product Information 2022-2023 gives 13.2 gal.; the hybrid owner: 1

### Mercedes-Benz

Конфликтов: 340. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 322
- sources of the same rank disagree; field not shown: 18

### BMW

Конфликтов: 227. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 226
- sources of the same rank disagree; field not shown: 1

### Chevrolet

Конфликтов: 3. По решениям:

- official document kept over the copy: 2
- official value is the main value; the vPIC Canadian value stays a SECO: 1

### Ford

Конфликтов: 4. По решениям:

- model-year manual kept over the whole-generation page (Appendix E.6): 4

### Lexus

Конфликтов: 55. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 55

### Honda

Конфликтов: 96. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 89
- sources of the same rank disagree; field not shown: 7

### Nissan

Конфликтов: 36. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 28
- official document kept over the copy: 7
- sources of the same rank disagree; field not shown: 1

### Land Rover

Конфликтов: 30. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 30

### Infiniti

Конфликтов: 44. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 44

### Audi

Конфликтов: 132. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 130
- sources of the same rank disagree; field not shown: 2

### Volkswagen

Конфликтов: 185. По решениям:

- official value is the main value; the vPIC Canadian value stays a SECO: 156
- sources of the same rank disagree; field not shown: 28
- model-year manual kept over the whole-generation page (Appendix E.6): 1

### Tesla

Конфликтов: 0. По решениям:


## 5. Выборочная перепроверка (10%)

### Hyundai

Проверено 322 записей (10% каждой линейки), расхождений 0.

### Kia

Проверено 182 записей (10% каждой линейки), расхождений 0.

### Toyota

Проверено 224 записей (10% каждой линейки), расхождений 0.

### Mercedes-Benz

Проверено 936 записей (10% каждой линейки), расхождений 0.

### BMW

Проверено 559 записей (10% каждой линейки), расхождений 0.

### Chevrolet

Проверено 65 записей (10% каждой линейки), расхождений 0.

### Ford

Проверено 18 записей (10% каждой линейки), расхождений 0.

### Lexus

Проверено 194 записей (10% каждой линейки), расхождений 0.

### Honda

Проверено 296 записей (10% каждой линейки), расхождений 0.

### Nissan

Проверено 187 записей (10% каждой линейки), расхождений 0.

### Land Rover

Проверено 98 записей (10% каждой линейки), расхождений 0.

### Infiniti

Проверено 79 записей (10% каждой линейки), расхождений 0.

### Audi

Проверено 294 записей (10% каждой линейки), расхождений 0.

### Volkswagen

Проверено 228 записей (10% каждой линейки), расхождений 0.

### Tesla

Проверено 34 записей (10% каждой линейки), расхождений 0.

## 6. Изменения схемы

- backend/alembic/versions/f087_us_tech_scoped_facts.py

## 7. Тесты: baseline и финал

- baseline backend: 531 passed, 2 warnings in 235.12s (0:03:55) (data_work\toyota\baseline_backend_pytest.txt)
- baseline flutter: All tests passed! (data_work\toyota\baseline_flutter_tests.txt)
- baseline web: ℹ pass 3; ℹ fail 0 (data_work\toyota\baseline_web_tests.txt)
- final backend: 545 passed, 2 warnings in 81.02s (0:01:21) (data_work\_batch\final_backend_pytest.txt)
- final flutter: All tests passed! (data_work\_batch\final_flutter_tests.txt)
- final web: ℹ pass 3; ℹ fail 0 (data_work\_batch\final_web_tests.txt)

## 8. Модели, которых нет в США, и предложения

- V-Class (Mercedes-Benz): нет строк EPA за 2014–2026 — в США под этим именем не продавалась; в базу не добавлялась.

Модели этих марок, которые NHTSA перечисляет для США, но которых нет в списке линеек (предложения, в базу не добавлялись):

- Hyundai: AZERA, EQUUS, GENESIS, GENESIS COUPE, IONIQ, IONIQ 5, IONIQ 5 BEV, IONIQ 5 N, IONIQ 6, IONIQ 9 BEV, IONIQ ELECTRIC, IONIQ EV, IONIQ HEV, IONIQ HYBRID, IONIQ PLUG-IN, IONIQ PLUG-IN HYBRID, NEXO, PALISADE, PALISADE HYBRID HEV, PALISADE ICE, SANTA CRUZ, SANTA CRUZ ICE, TUCSON FUEL CELL, VELOSTER, VELOSTER N, VENUE, VENUE ICE
- Kia: CADENZA, CARNIVAL, CARNIVAL HEV, CARNIVAL HYBRID HEV, CARNIVAL ICE, EV6, EV9, EV9 BEV, K4, K4 5DR ICE, K4 ICE, K900, NIRO, NIRO ELECTRIC, NIRO EV, NIRO HEV, NIRO HYBRID, NIRO PHEV, NIRO PLUG-IN HYBRID, SEDONA, SELTOS, SELTOS ICE, SOUL, SOUL EV, STINGER, TELLURIDE
- Toyota: 4RUNNER, 4RUNNER HYBRID, 86, AVALON, AVALON HYBRID, BZ4X, C-HR, COROLLA CROSS, COROLLA CROSS HYBRID, CROWN HYBRID, CROWN SIGNIA HYBRID, FJ CRUISER, FR-S, GR86, GRAND HIGHLANDER, GRAND HIGHLANDER HYBRID, GRAND HIGHLANDER LATER RELEASE, LAND CRUISER, LAND CRUISER HYBRID, LANDCRUISER, MIRAI, PRIUS C, PRIUS PLUG-IN HYBRID, PRIUS PRIME, PRIUS V, RAV4 PLUG-IN HYBRID, RAV4 PRIME, SCION FR-S, SCION IA, SCION IQ, SCION TC, SCION XB, SCION XD, SEQUOIA, SEQUOIA HYBRID, SIENNA, SIENNA HYBRID, SUPRA, TACOMA, TUNDRA, TUNDRA HYBRID, UNKNOWN, VENZA, VENZA HYBRID, YARIS, YARIS HATCHBACK, YARIS IA, YARIS LIFTBACK, redundant CAMRY, redundant SEQUOIA, redundant SIENNA, redundant VENZA
- Mercedes-Benz: A 220 4MATIC, A-CLASS, AMG A35, AMG G63, AMG GT, AMG GT S, AMG GT-CLASS, AMG GT-CLASS ROADSTER, AMG GT43, AMG GT55, AMG GT63, B 250E, B-CLASS E-CELL, EQE, EQE 320+, EQE 350 4MATIC, EQE 350+, EQE SUV, EQS SUV, EQS SUV 580 4MATIC, G 580 EV, G-CLASS, GT CLASS, GT CLASS CABRIOLET, GT COUPE, GT-CLASS, MERCEDES-BENZ ESPRINTER (HO), MERCEDES-BENZ ESPRINTER (SO), METRIS, METRIS CARGO, METRIS CARGO VAN, METRIS PASSENGER, METRIS PASSENGER VAN, SL-CLASS, SLC-CLASS, SLK-CLASS, SLS AMG, SPRINTER (VS30), SPRINTER 1500, SPRINTER 1500 12 PASSENGER, SPRINTER 1500 CARGO, SPRINTER 1500 CARGO VAN, SPRINTER 1500 PASSENGER, SPRINTER 1500 PASSENGER VAN, SPRINTER 2500, SPRINTER 2500  MIXTO, SPRINTER 2500 12 PASSENGER, SPRINTER 2500 12 PASSENGER VAN, SPRINTER 2500 15 PASSENGER, SPRINTER 2500 15 PASSENGER VAN, SPRINTER 2500 CARGO, SPRINTER 2500 CARGO DIESEL, SPRINTER 2500 CARGO VAN, SPRINTER 2500 CARGO VAN (LWB), SPRINTER 2500 CARGO VAN (SWB), SPRINTER 2500 CREW, SPRINTER 2500 CREW DIESEL, SPRINTER 2500 CREW VAN, SPRINTER 2500 CREW VAN (LWB), SPRINTER 2500 CREW VAN (SWB), SPRINTER 2500 MIXTO, SPRINTER 2500 PASSENGER VAN, SPRINTER 2500 PASSENGER VAN (12-PASSENGER), SPRINTER 2500 PASSENGER VAN (15-PASSENGER), SPRINTER 3500, SPRINTER 3500 CAB CHASSIS, SPRINTER 3500 CARGO VAN, SPRINTER 3500 CREW VAN, SPRINTER 3500XD CARGO VAN, SPRINTER 3500XD CREW VAN, SPRINTER 4500
- BMW: 2 SERIES, 2 SERIES COUPE, 2 SERIES COUPE ICE, 2 SERIES GRAN, 2 SERIES GRAN COUPE, 228I, 228I XDRIVE, 4 SERIES, 4 SERIES CONVERTIBLE, 4 SERIES COUPE, 4 SERIES COUPE ICE, 4 SERIES GRAN, 4 SERIES GRAN COUPE, 428I, 428I XDRIVE, 428XI, 430I, 430I XDRIVE, 435I, 435I XDRIVE, 435XI, 6 SERIES, 640I, 640I XDRIVE, 650I, 650I XDRIVE, 650XI, 8 SERIES, 8 SERIES CONVERTIBLE, 8 SERIES COUPE, 8 SERIES GRAN, 8 SERIES GRAN COUPE, ACTIVE HYBRID 535I, C 400 X, C600 SPORT MAXI-SCOOTER, C650 GT MAXI-SCOOTER, CE 04, F 750 GS, F 850 GS, F700 GS, F800 GS, F800 GT, F850GS, G 310 R, G 650 GS, G310 GS, G310R, G650GS, G650GS SERTAO, I3, I3 BEV, I3 PHEV, I3 REX, I4, I4 EDRIVE40, I4 GRAN COUPE, I4 GRAN COUPE BEV, I4 XDRIVE40, I5, I7, I7 SEDAN, I7 SEDAN BEV, I8, I8 ROADSTER, IX, IX BEV, IX XDRIVE60, K 1600 B, K 1600 GT, K 1600 GTL, K1300 S, K1600B, M 1000 XR, M2, M2 COMPETITION, M2 COUPE, M235I, M240I, M4, M4 CONVERTIBLE, M4 COUPE, M440I, M6, M8, M8 CONVERTIBLE, M8 GRAN, M850I, R 1200 GS, R 1200 GS ADVENTURE, R 1200 RT, R 1250 GS, R 1250 GS ADVENTURE, R 1250 R, R 1250 RS, R 1250 RT, R 1300 GS, R 1300 GS ADVENTURE, R 1300 R, R 1300 RT, R 18, R 18 CLASSIC, R NINE T, R1200 GS, R1200 GS ADVENTURE, R1200 R, R1200 RS, R1200 RT, R1250 GS ADVENTURE, S 1000 R, S 1000 RR, S 1000 XR, S1000 R, S1000 RR, S1000 XR, X1, X1 ICE, X1 SAV, X1 SDRIVE28I, X1 XDRIVE28I, X1 XDRIVE35I, X2, X2 ICE, X3, X3 30E XDRIVE, X3 ICE, X3 M, X3 SDRIVE28I, X3 XDRIVE28D, X3 XDRIVE28I, X3 XDRIVE35I, X4, X4 M, X4 XDRIVE28I, X4 XDRIVE35I, XM, Z4, Z4 M40I, Z4 SDRIVE28I, Z4 SDRIVE35I, Z4 SDRIVE35IS
- Chevrolet: 3500HD, 4500, 4500HD, 5500HD, 6500, 6500HD, BLAZER, BLAZER EV, BLAZER ICE, BOLT, BOLT EUV, BOLT EV, CAMARO, CAMARO LT1, CAMARO LT1 WITH RECARO, CAMARO LT1 WITHOUT RECARO, CAMARO SS, CAMARO SS WITH RECARO, CAMARO SS WITHOUT RECARO, CAMARO WITH RECARO, CAMARO WITHOUT RECARO, CAMARO ZL1, CAMARO ZL1 WITH RECARO, CAPRICE PPV, CAPTIVA, CITY EXPRESS, COBALT, COLORADO, COLORADO - ZR2 BISON ICE, COLORADO ICE, COLORADO ZR2 BISON, CORVETTE, CORVETTE E-RAY HEV, CORVETTE ICE, CORVETTE STINGRAY, CORVETTE STRINGRAY, CORVETTE Z06, CORVETTE ZR1, CORVETTE ZR1 ICE, EQUINOX EV, EQUINOX EV BEV, EXPRESS, EXPRESS 3500, EXPRESS 4500, EXPRESS CARGO 2500, EXPRESS CARGO 3500, EXPRESS CARGO G23405, EXPRESS CARGO G23705, EXPRESS CARGO G2500, EXPRESS CARGO G33405, EXPRESS CARGO G33705, EXPRESS CARGO G3500, EXPRESS CUTAWAY VAN, EXPRESS PASSENGER 1500, EXPRESS PASSENGER 2500, EXPRESS PASSENGER 3500 - 12 PASSENGER, EXPRESS PASSENGER 3500 - 15 PASSENGER, EXPRESS PASSENGER 3500 12 PASS, EXPRESS PASSENGER 3500 15 PASS, EXPRESS PASSENGER 3500- 12 PASSENGER, EXPRESS PASSENGER 3500- 15 PASSENGER, EXPRESS PASSENGER G2500, EXPRESS PASSENGER G3500 12 PASS, EXPRESS PASSENGER G3500 15 PASS, G4500, IMPALA, IMPALA ECO EASSIST, IMPALA LIMITED, LOW CAB FORWARD 3500, LOW CAB FORWARD 4500, N300, ONIX, ORLANDO, S10, SILVERADO 1500, SILVERADO 1500 ICE, SILVERADO 1500 LTD, SILVERADO 2500, SILVERADO 2500 ICE, SILVERADO 3500, SILVERADO 4500, SILVERADO 5500, SILVERADO 6500, SILVERADO EV, SILVERADO EV BEV, SILVERADO HD, SILVERADO LD 1500, SILVERADO LT, SONIC, SPARK, SPARK EV, SS, SUBURBAN, SUBURBAN 1500, SUBURBAN ICE, TAHOE, TAHOE ICE, TRAILBLAZER, TRAILBLAZER ICE, TRAVERSE, TRAVERSE ICE, TRAVERSE LIMITED, VOLT, duplicate SILVERADO 5500
- Ford: BRONCO, BRONCO 2DR, BRONCO 2DR ICE, BRONCO 4DR, BRONCO 4DR ICE, BRONCO SPORT, BRONCO SPORT EARLY RELEASE, BRONCO SPORT ICE, BRONCO SPORT LATER RELEASE, C-MAX, CMAX ENERGI, CMAX HEV, E-150, E-250, E-350, E-350 P12, E-350 P15, E-450, ECONOLINE, ECOSPORT, EDGE, ESCAPE, ESCAPE GAS, ESCAPE GAS ICE, ESCAPE HEV, ESCAPE HYBRID, ESCAPE PHEV, ESCAPE PHEV PHEV, EXPEDITION, EXPEDITION EL, EXPEDITION ICE, EXPEDITION MAX, EXPEDITION MAX ICE, EXPLORER, EXPLORER GAS ICE, EXPLORER HEV, EXPLORER POLICE INTERCEPT, F-150, F-150  REGULAR CAB, F-150  SUPER CAB, F-150 (REGULAR CAB) GAS, F-150 (REGULAR CAB) GAS ICE, F-150 (SUPER CAB) GAS, F-150 (SUPER CAB) GAS ICE, F-150 (SUPER CREW) GAS, F-150 (SUPER CREW) GAS ICE, F-150 (SUPER CREW) HEV, F-150 (SUPER CREW) HEV HEV, F-150 (SUPER CREW) LIGHTNING BEV, F-150 (Super Crew) Lightning BEV, F-150 CREW CAB, F-150 REGULAR CAB, F-150 SUPER CAB, F-150 SUPER CAB DIESEL, F-150 SUPER CREW, F-150 SUPER CREW DIESEL, F-150 SUPER CREW DiESEL, F-150 SUPER CREW HEV, F-150 SUPERCAB, F-150 SUPERCAB DIESEL, F-250 (CREW CAB), F-250 (CREW CAB) ICE, F-250 (REGULAR CAB), F-250 (REGULAR CAB) ICE, F-250 (SUPER CAB), F-250 (SUPER CAB) ICE, F-250 CREW CAB, F-250 REGULAR CAB, F-250 SD, F-250 SUPER CAB, F-250 SUPER CREW, F-250 SUPERCAB, F-250 TREMOR, F-250 TREMOR (CREW CAB), F-250 TREMOR CREW CAB, F-350 (CREW CAB), F-350 (REGULAR CAB), F-350 (SUPER CAB), F-350 CREW, F-350 CREW CAB, F-350 REGULAR CAB, F-350 SD, F-350 SUPER CAB, F-350 SUPER CREW, F-350 SUPERCAB, F-450, F-450 SD, F-53, F-550, F-550 SD, F-59, F-600 SD, F-650, F-650 ROUSH PROPANE, F-650 SD, F-750, F-750 SD, F53, FIESTA, FLEX, FOCUS, FOCUS BEV, FOCUS RS, MAVERICK, MAVERICK EARLY RELEASE, MAVERICK HEV, MAVERICK HEV EARLY RELEASE, MAVERICK HEV HEV, MAVERICK HEV LATER RELEASE, MAVERICK ICE, MAVERICK LATER RELEASE, MUSTANG, MUSTANG CONVERTIBLE, MUSTANG COUPE, MUSTANG GT 500, MUSTANG GT350R, MUSTANG GT500, MUSTANG ICE, MUSTANG MACH-E, MUSTANG MACH-E BEV, MUSTANG MACH-E BEV BEV, MUSTANG NO REAR SEAT ICE, POLICE INTERCEPTOR SEDAN, POLICE INTERCEPTOR UTILIT, RANGER, RANGER (SUPER CAB), RANGER (SUPER CREW), RANGER (SUPER CREW) ICE, RANGER SUPER CAB, RANGER SUPER CREW, STRIPPED CHASSIS, TAURUS, TRANSIT, TRANSIT  MEDIUM ROOF (8,10,12) PASS, TRANSIT CONNECT, TRANSIT CONNECT VAN, TRANSIT CONNECT WAGON, TRANSIT HIGH ROOF, TRANSIT HIGH ROOF (8,10,12) PASS, TRANSIT HIGH ROOF 12 PASS, TRANSIT HIGH ROOF 15 PASS, TRANSIT HIGH ROOF(8,10,12) PASS, TRANSIT LOW ROOF (8,10,12) PASS, TRANSIT LOW ROOF 12 PASS, TRANSIT LOW ROOF 15 PASS, TRANSIT LOW ROOF(8,10,12) PASS, TRANSIT MEDIUM ROOF (8,10,12) PASS, TRANSIT MEDIUM ROOF 12 PASS, TRANSIT MEDIUM ROOF 15 PASS, TRANSIT MEDIUM ROOF(8,10,12) PASS, TRANSIT T-350 HD, TRANSIT VAN, TRANSIT VAN - GAS, TRANSIT VAN BATTERY ELECTRIC, TRANSIT VAN BEV, TRANSIT VAN GAS ICE, TRANSIT WAGON - HIGH ROOF 12 PASS ICE, TRANSIT WAGON - HIGH ROOF 15 PASS ICE, TRANSIT WAGON - LOW ROOF 12 PASS ICE, TRANSIT WAGON - LOW ROOF 15 PASS ICE, TRANSIT WAGON - MED ROOF 12 PASS ICE, TRANSIT WAGON - MED ROOF 15 PASS ICE, redundant C-MAX HYBRID
- Lexus: CT200H, GS, GS200T, GS300, GS350, GS450H, IS, IS 250, IS 300, IS 350, IS 350 ICE, IS 500, IS F, IS200T, IS250, IS250C, IS300, IS350, IS350C, LC, LC 500, LC 500 CONVERTIBLE, LS, LS 500, LS 500H, LS460, LS460L, LS500, LS600HL, LX 570, LX 600, LX 600 ICE, LX570, RC, RC 200T, RC 300, RC 350, RC F, RC200T, RC200t, RC300, RC350, RZ 300E, RZ 350E BEV, RZ 450E, RZ 450E BEV, RZ 550E BEV, TX 350, TX 350 ICE, TX 350 LATER RELEASE, TX 500H, TX 550H+, TX HYBRID, UX, UX 200, UX 250H, UX 300H
- Honda: ADV150, ADV160, CB1000SP, CB1100, CB300, CB300F, CB300R, CB500, CB500F, CB500X, CBF300, CBR1000RR, CBR1000RS, CBR300R, CBR600RR, CBR650, CBR650R, CLARITY ELECTRIC, CLARITY FUEL CELL, CLARITY PLUG-IN HYBRID, CMX1100, CMX300, CMX500, CR-Z, CRF1000, CRF1000A, CRF1000D, CRF1000LD, CRF1100, CRF1100 AFRICA TWIN, CRF1100A, CRF1100D4, CRF250L, CRF300L, CRF450, CRF450L, CRF50, CROSSTOUR, CT125, CTX1300, CTX700, FIT, GL1800, GL1800A, GL1800B, GL1800BD, GL1800C, GROM125, HR-V, HR-V ICE, INSIGHT, MONKEY125, NAVI, NC700JD, NC700X, NC750X, NPS50, NSS300, NVA110B, NX500, ODYSSEY, ODYSSEY ICE, PASSPORT, PASSPORT ICE, PILOT, PILOT ICE, PROLOGUE BEV, PROLOGUE EV, REBEL 1100, RIDGELINE, RIDGELINE ICE, ST1300PA, SXS1000, SXS700, TRAIL 125, VFR1200X, VT1300, VT1300CX, VT750, VT750C, XL750, XR150L, Z125M
- Nissan: 370Z, 370Z ROADSTER, ARIYA, ARMADA, ARMADA ICE, CUBE, FRONTIER, FRONTIER CREW CAB, FRONTIER CREW CAB ICE, FRONTIER KING CAB, FRONTIER KING CAB ICE, GTR, JUKE, KICKS, KICKS ICE, KICKS PLAY, LEAF, LEAF (40 KWH BATTERY), LEAF (40 kWH BATTERY), LEAF (53 KWH BATTERY) BEV, LEAF BEV, LEAF PLUS, LEAF PLUS (60 KWH BATTERY), LEAF PLUS (60 kWH BATTERY), LEAF PLUS (62 KWH BATTERY), LEAF PLUS (75 KWH BATTERY) BEV, MAXIMA, MURANO, MURANO CROSSCABRIOLET, MURANO HYBRID, MURANO ICE, NV1500, NV1500, NV2500, NV3500, NV200, NV200 CARGO, NV2500, NV3500, NV3500 Cargo, NV3500 PASSGENGER VAN, NV3500 Passenger Van, QUEST, ROGUE SPORT, TITAN, TITAN CREW CAB, TITAN KING CAB, TITAN XD, TITAN XD CREW CAB, VERSA, VERSA NOTE, VERSA NOTE SR, XTERRA, Z, redundant ARIYA
- Land Rover: DEFENDER, DEFENDER 110, DEFENDER 110 MHEV, DEFENDER 130, DEFENDER 130 MHEV, DEFENDER 90, DEFENDER 90 MHEV, DEFENDER L663 110, DEFENDER L663 90, DISCOVERY, DISCOVERY MHEV, LAND ROVER DEFENDER 110, LAND ROVER DEFENDER 130, LAND ROVER DEFENDER 90, LR4 (5 SEAT), LR4 (7 SEAT), RANGE ROVER VELAR, RANGE ROVER VELAR MHEV
- Infiniti: G37, Q40, Q60, Q70, Q70 HYBRID, Q70L, QX30, QX50, QX55, QX80, QX80 ICE
- Cadillac: ATS, ATS V-SERIES, ATS-V, CT4, CT4 ICE, CT4-V, CT4-V BLACKWING, CT4-V BLACKWING ICE, CT5, CT5 ICE, CT5 WITH V6, CT5 WITH V6 ICE, CT5-V, CT5-V BLACKWING, CT5-V BLACKWING ICE, CT6, CT6 HYBRID, CT6 PHEV, CT6-V, ELR, ESCALADE IQ, ESCALADE IQL, LYRIQ, LYRIQ BEV, LYRIQ-V BEV, OPTIQ, OPTIQ BEV, OPTIQ-V BEV, VISTIQ BEV, XT4, XT5, XT5 ICE, XT6, XTS
- Jeep: GLADIATOR, GLADIATOR DIESEL, GLADIATOR ICE, GRAND WAGONEER, GRAND WAGONEER ICE, GRAND WAGONEER L, GRAND WAGONEER L ICE, PATRIOT, RENEGADE, WAGONEER, WAGONEER L, WAGONEER S, WRANGLER, WRANGLER 2-DOOR, WRANGLER 2-DOOR ICE, WRANGLER 4-DOOR, WRANGLER 4-DOOR 392, WRANGLER 4-DOOR 392 ICE, WRANGLER 4-DOOR 4XE, WRANGLER 4-DOOR ICE, WRANGLER 4-DOOR RHD, WRANGLER 4-DOOR RHD ICE, WRANGLER UNLIMITED, WRANGLER UNLIMITED 392, WRANGLER UNLIMITED DIESEL, WRANGLER UNLIMITED PHEV, WRANGLER UNLIMITED RHD
- Audi: A7, A7 (WITH REAR SEAT SABS), A7 PHEV, A8, A8 LWB, A8 NWB, A8L, A8L PHEV, ALL-NEW Q5, ALL-NEW SQ5, AUDI A3, AUDI A4, AUDI A4 ALLROAD, AUDI A5, AUDI A5 COUPE, AUDI A5 SPORTBACK, AUDI A6, AUDI A6 ALLROAD, AUDI E-TRON, AUDI E-TRON GT, AUDI E-TRON S, AUDI E-TRON S SPORTBACK, AUDI E-TRON SPORTBACK, AUDI Q3, AUDI Q4 E-TRON, AUDI Q4 SPORTBACK E-TRON, AUDI Q5, AUDI Q5 PHEV, AUDI Q5 SPORTBACK, AUDI Q7, AUDI Q8, AUDI RS 6 AVANT, AUDI RS E-TRON GT, AUDI RS Q8, AUDI S3, AUDI S4, AUDI S5, AUDI S5 COUPE, AUDI S6, AUDI SQ5, AUDI SQ7, AUDI SQ8, E-TRON, E-TRON SPORTBACK, Q4 E-TRON, Q4 SPORTBACK E-TRON, Q6 E-TRON, Q6 SPORTBACK E-TRON, Q8, R8, R8 SPYDER, RS 7, RS E-TRON GT, RS Q8, RS7, S E-TRON GT BEV, S7, S8, SQ6 E-TRON, SQ8, TT, TTRS
- Volkswagen: ALLTRACK, ATLAS CROSS SPORT, BEETLE, CC, E-GOLF, EGOLF, EOS, GOLF, GOLF GTI, GOLF R, GOLF R ICE, GOLF SPORTWAGEN, GTI, ID.4, ID.BUZZ, ROUTAN, TAOS, TAOS ICE, eGOLF
- Mitsubishi: ECLIPSE CROSS, IMIEV, LANCER, LANCER EVOLUTION, LANCER SPORTBACK, MIRAGE, MIRAGE G4
- Tesla: CYBERTRUCK, CYBERTRUCK (ALL VARIANTS), CYBERTRUCK BEV, SEMI

## 9. Нужны VIN-образцы (руководство выдаётся только по VIN: BMW, VW, Audi)

Линейка и модельные годы без US-руководства в собранных источниках:

- 3 Series: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- 5 Series: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2025, 2026
- 7 Series: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2023, 2024, 2025, 2026
- X5: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- X6: 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026
- X7: 2020, 2021, 2022, 2023, 2024, 2025, 2026
- M3: 2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024, 2025, 2026
- M5: 2014, 2015, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2025, 2026
- X5 M: 2015, 2016, 2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- X6 M: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- Jetta: 2015, 2016, 2017, 2018, 2024, 2025, 2026
- Passat: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022
- Tiguan: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2025, 2026
- Atlas: 2019, 2020, 2022, 2023, 2025, 2026
- Arteon: 2019, 2020, 2021, 2022, 2023, 2024
- Touareg: 2014, 2015, 2016, 2017
- A3: 2015, 2016, 2017, 2018, 2019, 2020, 2022, 2023, 2024, 2025, 2026
- A4: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
- A5: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2026
- A6: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- Q3: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- Q5: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- Q7: 2014, 2015, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

## 10. Vehicle Databases

VDB = нет; запросов к VDB: 0.

## 11. Git-коммиты

- a72994d chore(us-batch): prepared extraction and staging for Cadillac, Jeep, Mitsubishi (not loaded); mycarusermanual crawl report
- 788fd0d data(us): Mercedes-Benz — oil, fluids and maintenance gaps closed where sources allow
- 0ac8e0d data(us): Tesla — first load: base layer (EPA, vPIC, NHTSA, known issues), manual and press facts, CarComplaints
- e96b2ee data(us): Volkswagen — first load: base layer (EPA, vPIC, NHTSA, known issues), manual and press facts, CarComplaints
- 73fdc49 data(us): Audi — first load: base layer (EPA, vPIC, NHTSA, known issues), manual and press facts, CarComplaints
- f47df93 data(us): Infiniti — first load: base layer (EPA, vPIC, NHTSA, known issues), manual and press facts, CarComplaints
- bec9c2d data(us): Land Rover — owner's manual facts, press specifications, CarComplaints (second pass)
- 653c09b data(us): Nissan — owner's manual facts, press specifications, CarComplaints (second pass)
- ea5a550 data(us): Honda — owner's manual facts, press specifications, CarComplaints (second pass)
- db1fbdc data(us): Lexus — owner's manual facts, press specifications, CarComplaints (second pass)
- f070be0 data(us): Ford — owner's manual facts, press specifications, CarComplaints (second pass)
- f9c8adf data(us): Chevrolet — owner's manual facts, press specifications, CarComplaints (second pass)
- 40e3af4 data(us): BMW — owner's manual facts, press specifications, CarComplaints (second pass)
- f8a2184 data(us): Mercedes-Benz — operator's manual fluids, press specifications, CarComplaints
- 2550256 data(us): Toyota — owner's manual fluids and capacities, press specifications (Corolla, RAV4, Highlander, Prius)
- 0ec3c41 data(us): Hyundai, Kia — table cells read correctly, earlier wrong values replaced
- 1448794 data(us): Hyundai — manual capacities per engine, maintenance schedules, press specs, CarComplaints
- 692e7a6 chore(us-batch): scripts and staging snapshot before the next load pass
- f5af985 data(us): Kia — owner's manual facts (oil, fluids, capacities) from one generic parser
- 7225946 data(us): Land Rover — base layer for Range Rover, Sport, Evoque, Discovery Sport (+LR2)
- d9af217 data(us): Nissan — base layer for Altima, Sentra, Rogue, Pathfinder
- 7f4fb2f data(us): Honda — base layer for Accord, Civic, CR-V
- 237b6eb data(us): Lexus — base layer for ES, RX, NX, GX
- d5e90a1 fix(us-batch): generation boundary rules; reload BMW 5 Series (G60 from MY2024)
- 1591dbb data(us): BMW, Chevrolet, Ford — base layer (EPA, vPIC, NHTSA, known issues)
- 401b0e5 data(us): Mercedes-Benz — base layer for 14 lines (EPA, vPIC, NHTSA, known issues)
- 17fc8ef data(us): Toyota — base layer for Corolla, RAV4, Highlander, Prius
- 6736836 data(us): Kia — base layer for 5 lines (EPA, vPIC, NHTSA, known issues)
- 31ee4a8 fix(us-batch): prune only rows tagged with the same line; finer generation rules
- 1ce0539 data(us): Hyundai — base layer for 7 lines (EPA, vPIC, NHTSA, known issues)
- 249b05f chore(db): remove demo data (cleanup plan groups A and B) and make demo seeding opt-in
- ebba0bc docs(toyota-us): record the Camry commit in report and progress
- 4a6e5d5 data(toyota-us): Camry — US MY2014-2026 tech facts, recalls, known issues
- 0b65774 chore(data-toyota-us): step 0 baseline, schema map and test logs
- 62024c8 feat(db): f087 scoped technical facts and maintenance schedule

## 12. Библиотека других рынков

Материалов в библиотеке (data_work/_library/manifest.csv): 10.

| Рынок | Марка | Материалов |
|---|---|---|
| CA | kia | 1 |
| EU | audi | 2 |
| EU | mercedes | 2 |
| EU | mitsubishi | 1 |
| EU | vw | 2 |
| GENERAL | honda | 1 |
| GENERAL | hyundai | 1 |

Скачанные руководства не US-издания (не использованы, помечены other_market): 54.

| Рынок | Марка | Документов |
|---|---|---|
| EU | mercedes-benz | 1 |
| EU | volkswagen | 9 |
| UNKNOWN | chevrolet | 1 |
| UNKNOWN | hyundai | 2 |
| UNKNOWN | jeep | 1 |
| UNKNOWN | kia | 16 |
| UNKNOWN | mercedes-benz | 2 |
| UNKNOWN | tesla | 12 |
| UNKNOWN | toyota | 1 |
| UNKNOWN | volkswagen | 9 |

## Дополнительно

### Недоступные источники

- media.cadillac.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- media.chevrolet.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- media.ford.com: {'blocked': 2}; robots.txt answered 403 on https://media.ford.com/robots.txt; scripted access refused, host stopped
- media.gm.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- media.stellantisnorthamerica.com: {'blocked': 41}; robots.txt disallows / for ClaudeBot, Claude-Web, anthropic-ai (Anthropic AI agents); host not crawled
- news.gm.com: {'ok': 24, 'blocked': 1}; stopped after 403 on POST https://news.gm.com/content/public/us/en/gm-news/home/search/jcr:content/par/channelbox_1738069849/par/multicollectionsolrs.search.solr
- pressroom.chevrolet.com: {'blocked': 2}; robots.txt: the group that applies to this client (User-agent: *) has 'Disallow: /'; no page of the host requested
- www.kiamedia.com: {'blocked': 5}; robots.txt disallows / for ClaudeBot, Claude-Web, anthropic-ai (Anthropic AI agents); host not crawled
- assets.sia.toyota.com: {'skipped': 28}; AccessDenied from this network (geo-restricted)
- mmna-ssb.my.salesforce.com: {'skipped': 18}; robots.txt disallows
- owners.hyundaiusa.com: {'skipped': 78}; robots.txt disallows /content/
- www.bmwusa.com: {'skipped': 116}; refuses scripted clients (bot protection); browser-only
- www.fordservicecontent.com: {'skipped': 100}; refuses scripted clients (bot protection); browser-only
- www.tesla.com: {'skipped': 16}; Akamai refuses scripted clients
- www.mbusa.com (руководства Mercedes-Benz), основной проход: скачано 35 руководств (и 9 гарантийных/сервисных книжек), недоступно 91 (шлюз сайта отвечал 502). Повтор недоступных файлов с таймаутом 180 с: 0 из 7, остановлен по решению владельца.
- Альтернативные официальные US-издания тех же модели-годов (другой кузов или другая дата издания, по одному запросу, таймаут 180 с, до 2 попыток на модели-год): модели-годов 96, с попытками 77, скачано 25 (25 файлов), без альтернатив в каталоге mbusa 19; запросов с ошибкой 89.
- Модели-годы Mercedes (годы EPA) без US-руководства ни в одном источнике (mbusa, альтернативные издания, mycarusermanual) после всех попыток: 34 из 139: amg-gt-4-door 2019, c-class 2014, c-class 2015, c-class 2016, c-class 2020, cla 2016, cla 2018, cla 2019, cla 2020, cls 2015, cls 2016, e-class 2017, e-class 2019, gla 2015, gla 2016, gla 2019, gla 2020, glb 2020, glc 2014, gle 2015, gle 2016, gle 2017, gls 2014, gls 2015, gls 2016, gls 2017, gls 2019, s-class 2014, s-class 2015, s-class 2016, s-class 2017, s-class 2018, s-class 2019, s-class 2020.
- Копии руководств для Mercedes: mycarusermanual.com — только 4 модели Mercedes в каталоге; carmans.net — Mercedes нет; ownersman.com — защита Cloudflare (не обходится); manualslib.com и usermanual.wiki → manuals.plus не отвечают.
- auto-data.net: объём масла и ОЖ собраны (вторичный источник); допуск масла на auto-data.net закрыт входом в аккаунт — не собирался.

### Исправления ранее записанных строк (журнал data_work/<марка>/staging/<линейка>/corrections.json)

- Hyundai: значений заменено 3, строк удалено как устаревшие 327
- Kia: значений заменено 26, строк удалено как устаревшие 58; числовые примеры: optima-k5: engine_oil_capacity_drain_refill_l 7.8 → 4.8; optima-k5: transmission_fluid_capacity_l 6.6 → 7.8; optima-k5: engine_oil_capacity_drain_refill_l 7.8 → 4.8; optima-k5: transmission_fluid_capacity_l 6.6 → 7.8
- Mercedes-Benz: значений заменено 1, строк удалено как устаревшие 22
- Land Rover: значений заменено 7, строк удалено как устаревшие 0; числовые примеры: discovery-sport: nhtsa_complaint_pattern 6 → 7; range-rover: nhtsa_complaint_pattern 6 → 7; range-rover: nhtsa_complaint_pattern 2 → 3; range-rover: nhtsa_complaint_pattern 2 → 3; range-rover-sport: nhtsa_complaint_pattern 1 → 2; range-rover-sport: nhtsa_complaint_pattern 2 → 4; range-rover-sport: nhtsa_complaint_pattern 1 → 2

### Документы, у которых название файла не подтверждено текстом

- carmans-2015-kia-optima-hybrid — значения использованы как обычное (не гибридное/EV) издание
- carmans-2023-kia-optima-incl-hybrid — значения использованы как обычное (не гибридное/EV) издание
- official-1c2856f63b05 2017 Warranty and Consumer Information Manual (Optima Plug-i — значения использованы как обычное (не гибридное/EV) издание
- carmans-2026-toyota-rav4-plug-in-hybrid — значения использованы как обычное (не гибридное/EV) издание

### Mercedes-Benz: масло, жидкости и ТО — что закрыто и что нет

Поля по модельным годам каждой линейки (EPA-годы). Источник: manual — US-руководство (официальное или копия), secondary — auto-data.net (европейская карточка, сопоставленная с US-конфигурацией), press — пресс-материал; «*» — значение только для названных в таблице руководства моделей (не для всех конфигураций года); mbusa A/B — интервалы Service A/B с официальной страницы mbusa.com (без привязки к модели и году, «approximately» в источнике, уровень SECONDARY_NOTE); «—» — нет данных.

| Поле | Годы с данными | Закрыто в этом раунде | Осталось без данных |
|---|---|---|---|
| Объём масла | 108 | 100 | 31 |
| Допуск/стандарт масла | 43 | 43 | 96 |
| Вязкость | 2 | 1 | 137 |
| ОЖ | 90 | 72 | 49 |
| Жидкость АКПП | 0 | 0 | 139 |
| Тормозная | 40 | 40 | 99 |
| ТО | 131 | 131 | 8 |

Почему не закрыто остальное:

- Модели-годы без US-руководства (см. «Недоступные источники»): объём масла и ОЖ взяты с auto-data.net, где карточка однозначно сопоставилась с US-конфигурацией (обозначение, объём, цилиндры, привод, годы); если карточки расходятся между собой — значение скрыто как конфликт, не выбирается.
- Допуск масла (MB 229.x): только из таблиц руководств; на auto-data.net допуск закрыт входом — для годов без руководства пусто.
- Вязкость: US-руководства Mercedes дают таблицу SAE-классов по температуре, а не одно значение; записано только там, где руководство прямо ограничивает класс (AMG: «only SAE 0W-40 or 5W-40»).
- Жидкость АКПП: в US-руководствах Mercedes нет ни спецификации, ни объёма ATF (обслуживание по Service A/B у дилера) — пусто.
- Тормозная жидкость: «MB-Approval 331.0» из руководств; для годов без руководства — пусто.
- ТО: официальная страница mbusa.com «Service & Maintenance»: Service A — первый визит «approximately» 10 000 миль или 1 год (что наступит раньше), далее «approximately» каждые 20 000 миль или 2 года; Service B — «approximately» 20 000 миль или 1 год после предыдущего визита, далее каждые 20 000 миль или 2 года. Страница не называет модели и годы и сама пишет «approximately» — строки записаны как SECONDARY_NOTE с этой оговоркой. Электромобили (EQS, EQB): на странице пакет обслуживания EV без интервалов — пусто с причиной в gaps.
- Значения из таблиц руководств привязаны к строке таблицы (обозначение модели как напечатано, «all other models (not …)», «Mercedes-AMG vehicles»), на остальные модели не распространяются.

| Линейка | Год | Объём масла | Допуск/стандарт масла | Вязкость | ОЖ | Жидкость АКПП | Тормозная | ТО |
|---|---|---|---|---|---|---|---|---|
| C-Class | 2014 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2015 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2016 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2017 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| C-Class | 2018 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| C-Class | 2019 | secondary (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| C-Class | 2020 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2021 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2022 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| C-Class | 2023 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2024 | manual (новое) | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| C-Class | 2025 | manual | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| C-Class | 2026 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| E-Class | 2014 | manual (новое) | — | — | manual | — | — | mbusa A/B (новое) |
| E-Class | 2015 | manual (новое) | — | — | manual (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2016 | manual (новое) | — | — | manual (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2017 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2018 | manual* (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| E-Class | 2019 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2020 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| E-Class | 2021 | secondary (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| E-Class | 2022 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2023 | manual* (новое) | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2024 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2025 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| E-Class | 2026 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2014 | — | — | — | — | — | — | mbusa A/B (новое) |
| S-Class | 2015 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| S-Class | 2016 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| S-Class | 2017 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| S-Class | 2018 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2019 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2020 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2021 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| S-Class | 2022 | secondary (новое) | — | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| S-Class | 2023 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2024 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2025 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| S-Class | 2026 | manual* (новое) | manual* (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLA | 2015 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2016 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2017 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLA | 2018 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLA | 2019 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2020 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2021 | manual | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLA | 2022 | manual (новое) | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| GLA | 2023 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2024 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2025 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLA | 2026 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLB | 2020 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLB | 2021 | manual | — | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLB | 2022 | manual | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLB | 2023 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLB | 2024 | manual | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| GLB | 2025 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLB | 2026 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLC (+GLK) | 2014 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLC (+GLK) | 2015 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLC (+GLK) | 2016 | secondary (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2017 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2018 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2019 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2020 | secondary (новое) | — | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2021 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2022 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLC (+GLK) | 2023 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLC (+GLK) | 2024 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLC (+GLK) | 2025 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLC (+GLK) | 2026 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2014 | manual* (новое) | — | — | manual (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2015 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2016 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2017 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2018 | manual (новое) | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2019 | manual (новое) | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2020 | manual (новое) | — | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLE (+ML) | 2021 | manual* (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLE (+ML) | 2022 | secondary (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLE (+ML) | 2023 | secondary (новое) | — | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLE (+ML) | 2024 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2025 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLE (+ML) | 2026 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2014 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2015 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2016 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2017 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2018 | manual (новое) | manual (новое) | — | manual (новое) | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2019 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2020 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2021 | manual* (новое) | manual* (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLS (+GL) | 2022 | manual* (новое) | manual* (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| GLS (+GL) | 2023 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2024 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2025 | — | — | — | — | — | — | mbusa A/B (новое) |
| GLS (+GL) | 2026 | — | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2014 | manual* (новое) | — | manual (новое) | manual (новое) | — | — | mbusa A/B (новое) |
| CLA | 2015 | manual | — | manual | manual | — | — | mbusa A/B (новое) |
| CLA | 2016 | — | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2017 | manual (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| CLA | 2018 | — | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2019 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2020 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2021 | manual* (новое) | manual* (новое) | — | manual* (новое) | — | — | mbusa A/B (новое) |
| CLA | 2022 | manual | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| CLA | 2023 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2024 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| CLA | 2025 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| CLA | 2026 | secondary (новое) | — | — | — | — | — | mbusa A/B (новое) |
| CLS | 2014 | secondary (новое) | — | — | manual (новое) | — | — | mbusa A/B (новое) |
| CLS | 2015 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| CLS | 2016 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| CLS | 2017 | manual* (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| CLS | 2018 | manual* (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| CLS | 2019 | manual* (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| CLS | 2020 | manual* (новое) | — | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| CLS | 2021 | manual* (новое) | manual (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| CLS | 2022 | manual* (новое) | manual* (новое) | — | manual* (новое) | — | — | mbusa A/B (новое) |
| CLS | 2023 | manual* | manual* (новое) | — | manual | — | manual (новое) | mbusa A/B (новое) |
| CLE | 2024 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| CLE | 2025 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| CLE | 2026 | secondary (новое) | — | — | secondary (новое) | — | — | mbusa A/B (новое) |
| AMG GT 4-Door | 2019 | — | — | — | — | — | — | mbusa A/B (новое) |
| AMG GT 4-Door | 2020 | manual (новое) | — | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| AMG GT 4-Door | 2021 | manual (новое) | manual (новое) | — | manual (новое) | — | manual (новое) | mbusa A/B (новое) |
| AMG GT 4-Door | 2022 | manual (новое) | manual* (новое) | — | manual* (новое) | — | — | mbusa A/B (новое) |
| AMG GT 4-Door | 2023 | — | — | — | — | — | — | mbusa A/B (новое) |
| AMG GT 4-Door | 2024 | — | — | — | — | — | — | mbusa A/B (новое) |
| AMG GT 4-Door | 2025 | — | — | — | — | — | — | mbusa A/B (новое) |
| AMG GT 4-Door | 2026 | — | — | — | — | — | — | mbusa A/B (новое) |
| EQS | 2022 | — | — | — | — | — | — | — |
| EQS | 2023 | — | — | — | — | — | — | — |
| EQS | 2024 | — | — | — | — | — | — | — |
| EQS | 2025 | — | — | — | — | — | — | — |
| EQS | 2026 | — | — | — | — | — | — | — |
| EQB | 2022 | — | — | — | manual (новое) | — | — | — |
| EQB | 2024 | — | — | — | manual (новое) | — | — | — |
| EQB | 2025 | — | — | — | — | — | — | — |

### Сверка A25A-FKS, 2022 (по запросу владельца)

| Поле | Значение | Годы | Уровень | Источник (стр.) |
|---|---|---|---|---|
| coolant | Toyota Super Long Life Coolant or similar high-quality ethylene glycol-based coolant per the manual | 2018–2023 | SECONDARY_NOTE | om-2018 p.428,437,545; om-2019 p.428,437,545; om-2020 p.428,437,543 |
| engine_oil_viscosity | SAE 0W-16 | 2018–2023 | SECONDARY_NOTE | om-2018 p.543; om-2019 p.543; om-2020 p.541 |
| engine_oil_alternatives | SAE 0W-20 if 0W-16 is not available; replace with 0W-16 at the next oil change | 2018–2023 | SECONDARY_NOTE | om-2018 p.543; om-2021 p.588; om-2023 p.578 |
| engine_oil_specification | API SN/RC | 2018–2022 | SECONDARY_NOTE | om-2018 p.543; om-2019 p.543; om-2020 p.541 |
| engine_oil_capacity_l | 4.5 L | 2018–2023 | FACT | om-2018 p.543; om-2019 p.543; om-2020 p.541 |
| engine_oil_capacity_without_filter_l | 4.2 L | 2018–2023 | SECONDARY_NOTE | om-2018 p.543; om-2021 p.588; om-2023 p.578 |
| coolant_capacity_l | 6.9 L | 2018–2023 | SECONDARY_NOTE | om-2018 p.545; om-2019 p.545; om-2020 p.543 |
| transmission_fluid | Toyota Genuine ATF WS | 2018–2023 | SECONDARY_NOTE | om-2018 p.546; om-2019 p.546; om-2020 p.544 |
| transmission_fluid_capacity_l | 7.3 L | 2018–2023 | SECONDARY_NOTE | om-2018 p.546; om-2019 p.546; om-2020 p.544 |

### Пресс-материалы производителей

| Сайт | Документов скачано | Не найдено | Заблокировано |
|---|---|---|---|
| hondanews.com | 95 | 0 | 0 |
| media.audiusa.com | 67 | 39 | 0 |
| media.cadillac.com | 0 | 0 | 0 |
| media.chevrolet.com | 0 | 0 | 0 |
| media.ford.com | 0 | 0 | 0 |
| media.gm.com | 0 | 0 | 0 |
| media.jlr.com | 15 | 39 | 0 |
| media.mbusa.com | 345 | 0 | 0 |
| media.mitsubishicars.com | 22 | 0 | 0 |
| media.stellantisnorthamerica.com | 0 | 0 | 39 |
| media.vw.com | 63 | 10 | 0 |
| news.gm.com | 2 | 0 | 0 |
| press.bmwgroup.com | 83 | 0 | 0 |
| pressroom.chevrolet.com | 0 | 0 | 0 |
| pressroom.lexus.com | 103 | 0 | 0 |
| pressroom.toyota.com | 123 | 0 | 0 |
| usa.infinitinews.com | 17 | 0 | 0 |
| usa.nissannews.com | 56 | 0 | 0 |
| www.hyundainews.com | 81 | 22 | 0 |
| www.kiamedia.com | 0 | 0 | 0 |

Разобрано пресс-документов по маркам: Hyundai 78, Toyota 116, Mercedes-Benz 344, BMW 83, Chevrolet 1, Lexus 97, Honda 95, Nissan 56, Land Rover 15, Infiniti 17, Cadillac 1, Audi 67, Volkswagen 62, Mitsubishi 22

### CarComplaints.com и ТО по маркам (загруженные данные)

| Марка | Проблемы с подтверждением CarComplaints | Только по отзывам владельцев (CarComplaints) | Пунктов ТО |
|---|---|---|---|
| Hyundai | 30 | 2 | 407 |
| Kia | 18 | 0 | 639 |
| Toyota | 9 | 1 | 0 |
| Mercedes-Benz | 0 | 0 | 300 |
| BMW | 2 | 0 | 0 |
| Chevrolet | 19 | 2 | 0 |
| Ford | 4 | 0 | 0 |
| Lexus | 3 | 1 | 0 |
| Honda | 10 | 2 | 0 |
| Nissan | 21 | 0 | 0 |
| Land Rover | 0 | 0 | 0 |
| Infiniti | 2 | 0 | 0 |
| Audi | 24 | 1 | 0 |
| Volkswagen | 18 | 0 | 0 |
| Tesla | 0 | 0 | 0 |

## Поколения: свидетельства прессы

Источник: data_work/_shared/generation_evidence.json (cars.com, consumerreports.org; Car and Driver, Edmunds, KBB и MotorTrend недоступны для автоматического чтения). Используются только цитаты, сверенные со страницей.

### Hyundai

- Sonata LF (2015–2019): consumerreports.org: "The 2015 Sonata models may be less stylish than the previous generation" (https://www.consumerreports.org/cars/hyundai/sonata/); cars.com: "The Sonata's exterior took on a tamer look with its 2015 redesign" (https://www.cars.com/research/hyundai-sonata/) [media: generation star
- Sonata DN8 (2020–2026): consumerreports.org: "Redesigned for 2020, the Sonata has a sleek, coupe-like silhouette." (https://www.consumerreports.org/cars/hyundai/sonata/); cars.com: "the redesigned 2020 Sonata's exterior design was dramatic" (https://www.cars.com/research/hyundai-sonata/) [media: generation starts MY2020]
- Elantra AD (2017–2020): consumerreports.org: "The redesigned Elantra is relatively roomy, sparing with fuel, and features intuitive controls." (https://www.consumerreports.org/cars/hyundai/elantra/); cars.com: "All-new for 2017" (https://www.cars.com/research/hyundai-elantra/) [media: generation starts MY2017]
- Elantra CN7 (2021–2026): consumerreports.org: "The redesigned for 2021 Elantra got a slightly roomier interior and a more sophisticated infotainment system." (https://www.consumerreports.org/cars/hyundai/elantra/); cars.com: "Redesigned for 2021" (https://www.cars.com/research/hyundai-elantra/) [media: generation starts MY2
- Tucson TL (2016–2021): consumerreports.org: "The redesigned-for-2016 Tucson shares only its name with the previous generation." (https://www.consumerreports.org/cars/hyundai/tucson/); cars.com: "Heavily revised five-seat compact SUV" (https://www.cars.com/research/hyundai-tucson/) [media: generation starts MY2016]
- Tucson US2022+ (2022–2026): consumerreports.org: "The redesigned fourth-generation Tucson compact SUV is much more substantial than the mediocre model it replaces." (https://www.consumerreports.org/cars/hyundai/tucson/); cars.com: "Redesigned for 2022" (https://www.cars.com/research/hyundai-tucson/) [media: generation starts M
- Santa Fe US2019-2023 (2019–2023): consumerreports.org: "The redesigned five-passenger Santa Fe is a compelling choice priced close to some top-trim compact SUVs." (https://www.consumerreports.org/cars/hyundai/santa-fe/); cars.com: "Redesigned for 2019, replacing Santa Fe Sport" (https://www.cars.com/research/hyundai-santa_fe/) [medi
- Santa Fe US2024+ (2024–2026): consumerreports.org: "The midsized Hyundai Santa Fe SUV is redesigned for the 2024 model year, giving it a boxy look and a striking interior." (https://www.consumerreports.org/cars/hyundai/santa-fe/); cars.com: "Redesigned for 2024" (https://www.cars.com/research/hyundai-santa_fe/) [media: generatio
- Santa Fe Sport: media give different first model years [2013, 2014] for one generation; MY2013 used
- Santa Fe Sport: MY2013: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "2013 Model Redesign Year" (https://www.consumerreports.org/cars/hyundai/santa-fe-sport/) [media: weak])
- Accent US2018-2022 (2018–2022): consumerreports.org: "This generation of Accent comes only as a sedan." (https://www.consumerreports.org/cars/hyundai/accent/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/hyundai-accent/) [media: generation starts MY2018]
- Kona US2024+ (2024–2026): consumerreports.org: "The redesigned Kona feels more mature and substantial than the original model." (https://www.consumerreports.org/cars/hyundai/kona/); cars.com: "Redesigned for 2024" (https://www.cars.com/research/hyundai-kona/) [media: generation starts MY2024]

### Kia

- Optima / K5 JF (2016–2020): consumerreports.org: "Riding on an all-new chassis shared with the Hyundai Sonata, the redesigned 2016 Optima midsized sedan packs a lot of substance and value." (https://www.consumerreports.org/cars/kia/optima/); cars.com: "The 2016 redesign brought slightly updated styling, and the car was wider, 
- Optima / K5 DL3 (2021–2026): consumerreports.org: "The K5 replaces the Optima." (https://www.consumerreports.org/cars/kia/k5/); cars.com: "Kia retired the Optima name after the 2020 model year; the redesigned Kia mid-size sedan that debuted for 2021 was named the K5." (https://www.cars.com/research/kia-optima/) [media: generati
- Forte BD (2019–2024): consumerreports.org: "The Forte was discontinued and replaced by the new K4 for 2025." (https://www.consumerreports.org/cars/kia/forte/); cars.com: "2019-2024" (https://www.cars.com/research/kia-forte/) [quote read once] [media: generation starts MY2019]
- Rio SC (2018–2023): consumerreports.org: "With its all-new platform, the fourth-generation Rio sedan and hatchback sit lower, wider, and slightly longer than before." (https://www.consumerreports.org/cars/kia/rio/); cars.com: "Redesigned for 2018 on new platform" (https://www.cars.com/research/kia-rio/) [media: generat
- Sorento UM (2016–2020): consumerreports.org: "Redesigned for 2016, the Sorento is slightly larger than before but still remains right-sized" (https://www.consumerreports.org/cars/kia/sorento/); cars.com: "The Sorento received a full redesign for the 2016 model year" (https://www.cars.com/research/kia-sorento/) [media: gene
- Sorento US2021+ (2021–2026): consumerreports.org: "Kia redesigned its Sorento SUV for 2021, with new engines and an available hybrid version." (https://www.consumerreports.org/cars/kia/sorento/); cars.com: "The Sorento got a clean-sheet redesign for 2021" (https://www.cars.com/research/kia-sorento/) [media: generation starts MY
- Sportage QL (2017–2022): consumerreports.org: "The redesigned Sportage is a stylish and mildly sporty choice among small SUVs." (https://www.consumerreports.org/cars/kia/sportage/); cars.com: "Completely redesigned for 2017" (https://www.cars.com/research/kia-sportage/) [media: generation starts MY2017]
- Sportage US2023+ (2023–2026): consumerreports.org: "The redesigned 2023 Sportage is larger and better equipped than the previous model." (https://www.consumerreports.org/cars/kia/sportage/); cars.com: "Redesigned for 2023" (https://www.cars.com/research/kia-sportage/) [media: generation starts MY2023]

### Toyota

- Corolla XII (2020–2026): consumerreports.org: "The redesigned Corolla sedan is fuel efficient, but the new styling has compromised the rear seat room" (https://www.consumerreports.org/cars/toyota/corolla/); cars.com: "The 2020 redesign puts the Corolla on a new platform shared with the compact sedan's hatchback sibling." (h
- RAV4 V (2019 redesign, TNGA) (2019–2025): consumerreports.org: "The popular RAV4 was redesigned for 2019, with new proportions and a more-rugged appearance." (https://www.consumerreports.org/cars/toyota/rav4/); cars.com: "The redesigned 2019 RAV4 got a makeover that gave this compact SUV a rugged, chunkier look" (https://www.cars.com/resear
- RAV4 US2026+ (2026–2026): consumerreports.org: "The redesigned-for-2026 RAV4 smartly evolves the industry's bestselling compact SUV" (https://www.consumerreports.org/cars/toyota/rav4/); cars.com: "The redesigned 2026 RAV4 wasn't significantly changed in dimensions or exterior styling" (https://www.cars.com/research/toyota-ra
- Highlander IV (2020–2026): consumerreports.org: "the fourth-generation Highlander retains its qualities of comfortable ride and a smooth powertrain." (https://www.consumerreports.org/cars/toyota/highlander/); cars.com: "The fourth-generation Highlander debuted as a 2020 model" (https://www.cars.com/research/toyota-highlander/
- Prius US2016-2022 (2016–2022): consumerreports.org: "the fourth-generation Prius was a revolution." (https://www.consumerreports.org/cars/toyota/prius/); cars.com: "Along with updated styling, the Prius grew for 2016, increasing cargo space." (https://www.cars.com/research/toyota-prius/) [media: generation starts MY2016]
- Prius US2023+ (2023–2026): consumerreports.org: "complete redesign of the Prius gave it a sleeker look, more power, and incremental improvements in fuel economy." (https://www.consumerreports.org/cars/toyota/prius/); cars.com: "Toyota took a radical approach with the car's 2023 redesign" (https://www.cars.com/research/toyota-

### Mercedes-Benz

- C-Class W205 (2015–2021): consumerreports.org: "This version of the Mercedes C-Class scored near the top of the compact sport sedan segment." (https://www.consumerreports.org/cars/mercedes-benz/c-class/); cars.com: "2015-2021 C-Class" (https://www.cars.com/research/mercedes_benz-c_class/) [media: generation starts MY2015]
- C-Class US2022+ (2022–2026): consumerreports.org: "The redesigned C-Class builds on the sportiness of the previous version" (https://www.consumerreports.org/cars/mercedes-benz/c-class/); cars.com: "Sedan redesigned for 2022" (https://www.cars.com/research/mercedes_benz-c_class/) [media: generation starts MY2022]
- E-Class US2017-2023 (2017–2023): consumerreports.org: "The redesigned E-Class delivers nimbler handling and better fuel economy than the previous generation." (https://www.consumerreports.org/cars/mercedes-benz/e-class/); cars.com: "Redesigned for 2017" (https://www.cars.com/research/mercedes_benz-e_class/) [media: generation start
- E-Class US2024+ (2024–2026): consumerreports.org: "The redesigned E-Class midsized luxury sedan coddles occupants with a comfortable ride and quiet cabin" (https://www.consumerreports.org/cars/mercedes-benz/e-class/); cars.com: "Redesigned for 2024" (https://www.cars.com/research/mercedes_benz-e_class/) [media: generation start
- S-Class US2021+ (2021–2026): consumerreports.org: "This redesigned flagship sedan continues to deliver a very comfortable ride but the low profile tires mar it." (https://www.consumerreports.org/cars/mercedes-benz/s-class/); cars.com: "Redesigned for 2021" (https://www.cars.com/research/mercedes_benz-s_class/) [media: generatio
- GLA US2021+ (2021–2026): consumerreports.org: "The GLA is redesigned for 2021 and is the fourth model on Mercedes front-drive architecture" (https://www.consumerreports.org/cars/mercedes-benz/gla/); cars.com: "The redesign sports styling changes and an overhauled interior that align the GLA with its new or redesigned platfo
- GLA: MY2017: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2017-2020 GLA 250" (https://www.cars.com/research/mercedes_benz-gla_250/) [media: weak])
- GLC (+GLK) X253 (2016–2022): consumerreports.org: "Based on the current C-Class, the rounded GLC replaces the GLK." (https://www.consumerreports.org/cars/mercedes-benz/glc/); cars.com: "Replacement for GLK" (https://www.cars.com/research/mercedes_benz-glc_class/) [media: generation starts MY2016]
- GLC (+GLK) US2023+ (2023–2026): consumerreports.org: "The redesigned GLC mirrors the C-Class redesign with the same cockpit." (https://www.consumerreports.org/cars/mercedes-benz/glc/); cars.com: "2023-2027 GLC 300" (https://www.cars.com/research/mercedes_benz-glc_300/) [media: generation starts MY2023]
- GLE (+ML) US2020+ (2020–2026): consumerreports.org: "2020 Model Redesign Year" (https://www.consumerreports.org/cars/mercedes-benz/gle/); cars.com: "Redesigned GLE-Class slated to arrive as a 2020 model" (https://www.cars.com/research/mercedes_benz-gle_350/) [media: generation starts MY2020]
- GLE (+ML): MY2016: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "The 2016 models got a nomenclature change to GLE." (https://www.consumerreports.org/cars/mercedes-benz/m-class/); cars.com: "Formerly M-Class, renamed for 2016" (https://www.ca
- GLS (+GL) US2020+ (2020–2026): consumerreports.org: "The new for 2020 GLS is a very functional three-row SUV that exudes luxury with its gorgeous interior." (https://www.consumerreports.org/cars/mercedes-benz/gls/); cars.com: "The redesigned 2020 Mercedes-Benz GLS-Class debuted at the 2019 New York International Auto Show" (https
- GLS (+GL): MY2017: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "Mercedes' seven-passenger SUV is freshened for the 2017 model year, with revised interior and exterior styling, a nine-speed automatic, an upgraded air suspension" (https://www
- CLA US2020-2025 (2020–2025): consumerreports.org: "2020 Model Redesign Year" (https://www.consumerreports.org/cars/mercedes-benz/cla/); cars.com: "the CLA sticking around for 2020 and getting a redesign to boot" (https://www.cars.com/articles/2020-mercedes-benz-cla-class-still-small-but-bigger-on-tech-safety-1420756952173/) [qu
- CLA US2026+ (2026–2026): consumerreports.org: "A fully redesigned 2026 CLA compact sedan will be offered in both electric and hybrid versions." (https://www.consumerreports.org/cars/mercedes-benz/cla/); cars.com: "Mercedes-Benz is launching the third generation of its smallest car for 2026" (https://www.cars.com/articles/ho
- CLS US2019-2023 (2019–2023): consumerreports.org: "the redesigned third-generation CLS continues to rely on the same recipe" (https://www.consumerreports.org/cars/mercedes-benz/cls/); cars.com: "Redesigned for 2019" (https://www.cars.com/research/mercedes_benz-cls_450/) [quote read once] [media: generation starts MY2019]
- CLS: MY2012: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "The CLS has been extensively freshened and now has a 4.6-liter twin-turbo V8." (https://www.consumerreports.org/cars/mercedes-benz/cls/); cars.com: "Redesigned for 2012" (https
- AMG GT 4-Door: MY2019: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "New model for 2019" (https://www.cars.com/research/mercedes_benz-amg_gt_53/) [media: weak])

### BMW

- 3 Series Seventh generation · US sedan (2019–2026): consumerreports.org: "The redesigned 3 Series sedan brings new infotainment tech, standard advanced safety features, improved handling, and better fuel economy." (https://www.consumerreports.org/cars/bmw/3-series/); cars.com: "Redesigned for 2019" (https://www.cars.com/research/bmw-330/) [media: gen
- 5 Series G30 (2017–2023): consumerreports.org: "BMW focused on adding technology and on sharpening the handling of the 2017 5 Series redesign." (https://www.consumerreports.org/cars/bmw/5-series/); cars.com: "Redesigned for 2017" (https://www.cars.com/research/bmw-530/) [media: generation starts MY2017]
- 5 Series US2024+ (2024–2026): consumerreports.org: "The redesigned 5 Series is larger than its predecessor, and has lightly smoothed-out styling." (https://www.consumerreports.org/cars/bmw/5-series/); cars.com: "For 2024, the eighth generation of the 5 Series sees other changes, including revised styling, updated gas powertrains
- 7 Series US2016-2022 (2016–2022): consumerreports.org: "2016 Model Redesign Year" (https://www.consumerreports.org/cars/bmw/7-series/); cars.com: "Redesigned for 2016" (https://www.cars.com/research/bmw-750/) [media: generation starts MY2016]
- 7 Series US2023+ (2023–2026): consumerreports.org: "In redesigning the 7 Series for 2023, BMW also introduced an EV version called the i7." (https://www.consumerreports.org/cars/bmw/7-series/); cars.com: "BMW has revealed a redesigned version of its lower-riding stablemate — the 2023 7 Series sedan." (https://www.cars.com/articl
- X5 US2019+ (2019–2026): consumerreports.org: "The redesigned 2019 X5 is one of the best vehicles we've ever tested." (https://www.consumerreports.org/cars/bmw/x5/); cars.com: "BMW redesigned its mid-size X5 SUV for the 2019 model year, and the fourth generation of the X5 has a little bit more of everything" (https://www.ca
- X6 US2020+ (2020–2026): consumerreports.org: "The 2020 X6 is a coupelike, sporty SUV that's based on the redesigned X5." (https://www.consumerreports.org/cars/bmw/x6/); cars.com: "Redesigned for 2020" (https://www.cars.com/research/bmw-x6/) [quote read once] [media: generation starts MY2020]
- X6: MY2015: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "Styling was refreshed for 2015 and the V8 engine got more power." (https://www.consumerreports.org/cars/bmw/x6/); cars.com: "2015-2019" (https://www.cars.com/research/bmw-x6/) 
- X6: MY2015: media disagree whether a generation starts here; the data boundary is kept
- M5 US2018-2023 (2018–2023): cars.com: "New all-wheel drive with selectable rear-wheel drive" (https://www.cars.com/research/bmw-m5/) [media: generation starts MY2018]
- M5 US2025+ (2025–2026): cars.com: "Redesigned for 2025" (https://www.cars.com/research/bmw-m5/) [media: generation starts MY2025]
- M5: MY2013: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2013-2016 M5" (https://www.cars.com/research/bmw-m5/) [media: weak])
- X5 M: MY2015: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2015-2018 X5 M" (https://www.cars.com/research/bmw-x5_m/) [media: weak])
- X5 M: MY2020: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2020-2026 X5 M" (https://www.cars.com/research/bmw-x5_m/) [media: weak])
- X6 M US2020+ (2020–2026): cars.com: "2020-2027 X6 M" (https://www.cars.com/research/bmw-x6_m/) [media: generation starts MY2020]
- X6 M: MY2010: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2010-2014" (https://www.cars.com/research/bmw-x6_m/) [media: weak])
- X6 M: MY2015: one site lists a new generation without redesign wording and the data show no boundary; not used (cars.com: "2015-2019 X6 M" (https://www.cars.com/research/bmw-x6_m/) [media: weak])

### Chevrolet

- Malibu IX (2016–2025): consumerreports.org: "Completely redesigned for 2016, the Malibu is much sleeker than the boxy sedan it replaced." (https://www.consumerreports.org/cars/chevrolet/malibu/); cars.com: "A stylish redesign for 2016 made the Malibu one of the better-looking entries in the mid-size sedan category" (https
- Cruze II (2016–2019): consumerreports.org: "A redesigned Cruze was introduced for 2016." (https://www.consumerreports.org/cars/chevrolet/cruze/); cars.com: "The Cruze was redesigned for 2016, gaining sleeker styling and lots of new tech features" (https://www.cars.com/research/chevrolet-cruze/) [media: generation starts 
- Equinox US2018-2024 (2018–2024): consumerreports.org: "The new Equinox has tidier dimensions" (https://www.consumerreports.org/cars/chevrolet/equinox/); cars.com: "With SUV sales on the rise, Chevy released a redesigned Equinox for 2018." (https://www.cars.com/research/chevrolet-equinox/) [media: generation starts MY2018]
- Equinox US2025+ (2025–2026): consumerreports.org: "Redesigned for 2025, the Chevrolet Equinox is similar in size and mechanical details to the SUV it supplants." (https://www.consumerreports.org/cars/chevrolet/equinox/); cars.com: "The Chevrolet Equinox entered a new generation for 2025 with a bold, truck-inspired redesign." (h
- Trax US2024+ (2024–2026): consumerreports.org: "The redesigned Trax is almost a foot longer than its predecessor." (https://www.consumerreports.org/cars/chevrolet/trax/); cars.com: "Redesigned on larger, FWD-only platform for 2024" (https://www.cars.com/research/chevrolet-trax/) [media: generation starts MY2024]

### Lexus

- ES US2019-2025 (2019–2025): consumerreports.org: "The seventh generation Lexus ES retains its comfortable, quiet demeanor" (https://www.consumerreports.org/cars/lexus/es/); cars.com: "The redesigned 2019 ES kicked off the model's seventh generation on an all-new platform." (https://www.cars.com/research/lexus-es_350/) [media: 
- ES US2026+ (2026–2026): consumerreports.org: "2026 Model Redesign Year" (https://www.consumerreports.org/cars/lexus/es/); cars.com: "The all-new 2026 ES will be available either as a hybrid or a pure electric vehicle." (https://www.cars.com/articles/all-new-2026-lexus-es-offers-stepped-electrification-with-phev-and-ev-powe
- RX AL20 (2016–2022): consumerreports.org: "The RX got a 2016 makeover, with avant-garde exterior styling and advanced safety features." (https://www.consumerreports.org/cars/lexus/rx/); cars.com: "One of the best-selling luxury vehicles on the market is redesigned for 2016." (https://www.cars.com/articles/2016-lexus-rx-
- RX US2023+ (2023–2026): consumerreports.org: "The redesigned 2023 RX is powered by a 2.4-liter turbocharged four-cylinder engine" (https://www.consumerreports.org/cars/lexus/rx/); cars.com: "Redesigned for 2023" (https://www.cars.com/research/lexus-rx_350/) [quote read once] [media: generation starts MY2023]
- NX US2022+ (2022–2026): consumerreports.org: "The redesigned 2022 Lexus NX looks much like the outgoing model, but beneath that familiar design is a raft of improvements." (https://www.consumerreports.org/cars/lexus/nx/); cars.com: "The NX was redesigned for the 2022 model year, and its model lineup was revamped (and expan
- GX US2024+ (2024–2026): consumerreports.org: "The redesigned Lexus GX promises more luxury and power than the long-running model it replaces." (https://www.consumerreports.org/cars/lexus/gx/); cars.com: "Redesigned for 2024 with more overt off-road attitude" (https://www.cars.com/research/lexus-gx_550/) [quote read once] [

### Honda

- Accord X (2018–2022): consumerreports.org: "This generation of Accord has a coupelike silhouette and a lower stance." (https://www.consumerreports.org/cars/honda/accord/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/honda-accord/) [media: generation starts MY2018]
- Accord US2023+ (2023–2026): consumerreports.org: "The 2023 Accord is treated to an evolutionary redesign" (https://www.consumerreports.org/cars/honda/accord/); cars.com: "The Honda Accord's 2023 redesign wasn't particularly dramatic" (https://www.cars.com/research/honda-accord/) [media: generation starts MY2023]
- Civic 10th (2016–2021): consumerreports.org: "Honda pulled out all of the stops, building a clean-sheet design." (https://www.consumerreports.org/cars/honda/civic/); cars.com: "The 10th-generation Civic marked a return to the compact car's roots: a renewed focus on fun-to-drive performance thanks to an all-new platform for
- Civic US2022+ (2022–2026): consumerreports.org: "Honda's 11th-generation Civic remains fuel efficient and brings a simpler infotainment system." (https://www.consumerreports.org/cars/honda/civic/); cars.com: "The Honda Civic underwent a complete redesign for 2022, kicking off the 11th generation" (https://www.cars.com/researc
- CR-V RW (2017–2022): consumerreports.org: "The redesigned CR-V gains features, space, and refinement." (https://www.consumerreports.org/cars/honda/cr-v/); cars.com: "Fully redesigned for 2017" (https://www.cars.com/research/honda-cr_v/) [media: generation starts MY2017]
- CR-V US2023+ (2023–2026): consumerreports.org: "The redesigned CR-V gained size and weight, but didn't stray far from its proven formula of practicality and functionality." (https://www.consumerreports.org/cars/honda/cr-v/); cars.com: "The CR-V was redesigned for 2023 with several notable improvements over the previous gener

### Nissan

- Altima US2019+ (2019–2026): consumerreports.org: "The sixth-generation Altima offers all-wheel drive and a turbo engine." (https://www.consumerreports.org/cars/nissan/altima/); cars.com: "Nissan debuted the new-for-2019 Altima at the 2018 New York International Auto Show." (https://www.cars.com/research/nissan-altima/) [media:
- Sentra US2020-2025 (2020–2025): consumerreports.org: "The redesigned 2020 Sentra is a complete transformation." (https://www.consumerreports.org/cars/nissan/sentra/); cars.com: "The Sentra was redesigned for the 2020 model year, marking the start of its eighth generation" (https://www.cars.com/research/nissan-sentra/) [media: gene
- Sentra US2026+ (2026–2026): consumerreports.org: "Nissan gave the 2026 Sentra a thorough refresh inside and out, with new styling, updated controls, and more advanced driver aids." (https://www.consumerreports.org/cars/nissan/sentra/); cars.com: "A redesigned, ninth-generation Sentra debuted for the 2026 model year" (https://w
- Rogue T33 (2021–2026): consumerreports.org: "The third generation Rogue debuted in 2021, and was a major upgrade over its predecessor." (https://www.consumerreports.org/cars/nissan/rogue/); cars.com: "Redesigned for 2021" (https://www.cars.com/research/nissan-rogue/) [quote read once] [media: generation starts MY2021]
- Rogue: MY2019: detected boundary (vPIC Canadian specifications: overall length 463 -> 469 cm (MY2018 -> MY2019; a change of 6 cm or more)) dropped; consumerreports.org: "The 2014 redesign made the Rogue bigger, better, quieter and more refined overall." (https://www.consumerreports.org/cars/nissan/rogue/);
- Pathfinder US2022+ (2022–2026): consumerreports.org: "The three-row Pathfinder was redesigned for 2022 with a squared-off exterior" (https://www.consumerreports.org/cars/nissan/pathfinder/); cars.com: "This new fifth-generation model is a complete departure that incorporates some styling cues from the original Pathfinder" (https:/

### Land Rover

- Range Rover US2022+ (2022–2026): consumerreports.org: "The redesigned Range Rover continues its legacy of pushing boundaries, with new tech and an elegant design." (https://www.consumerreports.org/cars/land-rover/range-rover/); cars.com: "A completely redesigned Range Rover debuted for the 2022 model year and, curiously, was sold a
- Range Rover Sport US2023+ (2023–2026): consumerreports.org: "this redesigned Range Rover Sport narrows the gap compared to the Range Rover in terms of luxury and refinement." (https://www.consumerreports.org/cars/land-rover/range-rover-sport/); cars.com: "Redesigned for 2023" (https://www.cars.com/research/land_rover-range_rover_sport/) 
- Range Rover Evoque US2020+ (2020–2026): consumerreports.org: "2020 Model Redesign Year" (https://www.consumerreports.org/cars/land-rover/range-rover-evoque/); cars.com: "Redesigned for 2020" (https://www.cars.com/research/land_rover-range_rover_evoque/) [quote read once] [media: generation starts MY2020]
- Discovery Sport (+LR2) L550 (2015–2026): consumerreports.org: "The compact Discovery Sport is based on the Evoque, with seating for five or, with its tiny optional third-row, seven." (https://www.consumerreports.org/cars/land-rover/discovery-sport/); cars.com: "2015-2026 Discovery Sport" (https://www.cars.com/research/land_rover-discovery_

### Infiniti

- QX60 (+JX) US2022+ (2022–2026): consumerreports.org: "The QX60 was redesigned for the 2022 model year." (https://www.consumerreports.org/cars/infiniti/qx60/); cars.com: "2022-2027" (https://www.cars.com/research/infiniti-qx60/) [quote read once] [media: generation starts MY2022]
- QX60 (+JX): media give different first model years [2013, 2014] for one generation; MY2014 used
- QX60 (+JX): MY2026: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "Infiniti redesigned the three-row QX60 for 2026, giving it styling that is similar to that of the QX80." (https://www.consumerreports.org/cars/infiniti/qx60/) [media: weak]
- FX / QX70: MY2014: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "The basics of the FX SUV carried over to the 2014 model year, but its nomenclature was changed to QX70." (https://www.consumerreports.org/cars/infiniti/qx70/); cars.com: "Previ

### Cadillac

- Escalade IV (2015–2020): consumerreports.org: "Few vehicles arrive with the Escalade's imposing look." (https://www.consumerreports.org/cars/cadillac/escalade/); cars.com: "The redesigned Escalade has a bold new face punctuated by distinctive headlights" (https://www.cars.com/articles/2015-cadillac-escalade-first-look-14206
- Escalade US2021+ (2021–2026): consumerreports.org: "The Cadillac Escalade and Escalade ESV have been redesigned for 2021, growing in size and features." (https://www.consumerreports.org/cars/cadillac/escalade/); cars.com: "The brand has unveiled the completely redesigned 2021 model" (https://www.cars.com/articles/2021-cadillac-e

### Jeep

- Grand Cherokee US2022+ (2022–2026): consumerreports.org: "The 2022 redesigned Grand Cherokee is slightly larger than the previous version." (https://www.consumerreports.org/cars/jeep/grand-cherokee/) [media: generation starts MY2022]
- Grand Cherokee: media give different first model years [2021, 2022] for one generation; MY2022 used
- Cherokee US2026+ (2026–2026): consumerreports.org: "The Cherokee returns after a brief hiatus, now packaged exclusively as a hybrid." (https://www.consumerreports.org/cars/jeep/cherokee/); cars.com: "an all-new generation debuted for 2026 on a notably larger platform" (https://www.cars.com/research/jeep-cherokee/) [media: genera
- Compass MP (2017–2026): consumerreports.org: "2017 Model Redesign Year" (https://www.consumerreports.org/cars/jeep/compass/); cars.com: "All-new five-passenger compact SUV" (https://www.cars.com/research/jeep-compass/) [media: generation starts MY2017]
- Compass: boundary moved from MY2018 to the media-stated MY2017
- Compass: MY2015: detected boundary (vPIC Canadian specifications: wheelbase 264 cm (MY2014) -> 263 cm (MY2015), with overall length 441 -> 445 cm) dropped; consumerreports.org: "2007 Model Redesign Year" (https://www.consumerreports.org/cars/jeep/compass/) [media: generation started MY2007], next starts MY20

### Audi

- A3 US2022+ (2022–2026): consumerreports.org: "Audi improves upon its capable entry-level sedan with an all-new 2022 model" (https://www.consumerreports.org/cars/audi/a3/); cars.com: "Redesigned for 2022" (https://www.cars.com/research/audi-a3/) [quote read once] [media: generation starts MY2022]
- A3: MY2017: detected boundary (vPIC Canadian specifications: wheelbase 264 cm (MY2016) -> 263 cm (MY2017), with overall height 142 -> 139 cm) dropped; consumerreports.org: "This wholly redesigned Audi A3 is part of a wave of compact luxury-branded models" (https://www.consumerreports.org/cars/audi/a3/);
- A4 8W (2017–2025): consumerreports.org: "2025 is the final model year for the A4, replaced by the A5." (https://www.consumerreports.org/cars/audi/a4/); cars.com: "Redesigned for 2017" (https://www.cars.com/research/audi-a4/) [quote read once] [media: generation starts MY2017]
- A5 US2018-2024 (2018–2024): consumerreports.org: "The 2018 A5 and S5 coupe and convertible have been redesigned." (https://www.consumerreports.org/cars/audi/a5/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/audi-a5/) [media: generation starts MY2018]
- A5 US2025+ (2025–2026): consumerreports.org: "The A4 is replaced by a redesigned version of what is now called the A5 Sportback" (https://www.consumerreports.org/cars/audi/a5/); cars.com: "Consolidates prior A4, A5 into one model" (https://www.cars.com/research/audi-a5/) [media: generation starts MY2025]
- A6 US2019-2025 (2019–2025): consumerreports.org: "The redesigned Audi A6 features lots of new technology, including a new infotainment system." (https://www.consumerreports.org/cars/audi/a6/); cars.com: "The redesigned 2019 Audi A6 shares an updated look and technology with the redone 2019 A7 hatchback" (https://www.cars.com/a
- A6 US2026+ (2026–2026): consumerreports.org: "Redesigned for 2026, the A6 delivers a high-level driving experience" (https://www.consumerreports.org/cars/audi/a6/); cars.com: "Redesigned for 2026" (https://www.cars.com/research/audi-a6/) [quote read once] [media: generation starts MY2026]
- A6: boundary moved from MY2020 to the media-stated MY2019
- A6: boundary moved from MY2025 to the media-stated MY2026
- Q3 US2019-2025 (2019–2025): consumerreports.org: "The redesigned Q3 is a pleasant SUV that packs luxury and practicality into a small package." (https://www.consumerreports.org/cars/audi/q3/); cars.com: "the second-generation Audi Q3 subcompact SUV, which gets a needed full redesign for 2019" (https://www.cars.com/articles/201
- Q3 US2026+ (2026–2026): consumerreports.org: "The redesigned Q3 has one powertrain choice" (https://www.consumerreports.org/cars/audi/q3/); cars.com: "Redesigned for 2026" (https://www.cars.com/research/audi-q3/) [quote read once] [media: generation starts MY2026]
- Q5 FY (2018–2024): consumerreports.org: "2018 Model Redesign Year" (https://www.consumerreports.org/cars/audi/q5/); cars.com: "Redesigned for 2018" (https://www.cars.com/research/audi-q5/) [quote read once] [media: generation starts MY2018]
- Q5 US2025+ (2025–2026): consumerreports.org: "The redesigned Q5 gets new styling, increased performance promise, and a growing list of advanced safety features." (https://www.consumerreports.org/cars/audi/q5/); cars.com: "Redesigned five-seat luxury compact SUV" (https://www.cars.com/research/audi-q5/) [quote read once] [m
- Q5: MY2009: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "The Q5 hits its target as a compact, luxurious and sporty SUV spot on." (https://www.consumerreports.org/cars/audi/q5/) [media: weak])
- Q5: MY2021: detected boundary (mycarusermanual.com generation page starts at 2020 (q5/suv/2020), corroborated by vPIC overall length 467 -> 468/469 cm (MY2020 -> MY2021)) dropped; consumerreports.org: "For 2021, the Q5 got a freshening with a modest power boost." (https://www.consumerreports.org/cars/au
- Q7 4M (2017–2026): consumerreports.org: "The redesigned Q7 employs a supercharged 3.0-liter V6 that is mated to a very smooth eight-speed automatic." (https://www.consumerreports.org/cars/audi/q7/); cars.com: "Redesigned for 2017 after skipping 2016" (https://www.cars.com/research/audi-q7/) [quote read once] [media: g

### Volkswagen

- Jetta VII (2019–2026): consumerreports.org: "The seventh generation Jetta has easy-to-use controls, great fuel economy, good cabin room" (https://www.consumerreports.org/cars/volkswagen/jetta/); cars.com: "Fully redesigned for 2019" (https://www.cars.com/research/volkswagen-jetta/) [media: generation starts MY2019]
- Passat: MY2020: media list a new block, but their own text calls it a rename/refresh; not a generation start (consumerreports.org: "2022 is the final year for the Passat." (https://www.consumerreports.org/cars/volkswagen/passat/); cars.com: "2020-2022 Passat" (https://www.cars.com/research/volkswagen-passat
- Tiguan II-US-LWB (2018–2024): consumerreports.org: "The second-generation Tiguan is one of the largest models in the small-SUV segment." (https://www.consumerreports.org/cars/volkswagen/tiguan/); cars.com: "It's been a long time coming, but a redesigned 2018 Volkswagen Tiguan has landed in the U.S." (https://www.cars.com/researc
- Tiguan US2025+ (2025–2026): consumerreports.org: "The Volkswagen Tiguan has been redesigned for 2025, with an all-new exterior and a longer wheelbase." (https://www.consumerreports.org/cars/volkswagen/tiguan/); cars.com: "Redesigned for 2025" (https://www.cars.com/research/volkswagen-tiguan/) [quote read once] [media: generati
- Atlas: MY2020: detected boundary (vPIC Canadian specifications: overall length 504 -> 497 cm (MY2019 -> MY2020; a change of 6 cm or more)) dropped; consumerreports.org: "2018 Model Redesign Year" (https://www.consumerreports.org/cars/volkswagen/atlas/); cars.com: "Brand-new model for 2018" (https://www.car
- Atlas: MY2021: detected boundary (vPIC Canadian specifications: overall length 504 -> 510 cm (MY2020 -> MY2021; a change of 6 cm or more)) dropped; consumerreports.org: "2018 Model Redesign Year" (https://www.consumerreports.org/cars/volkswagen/atlas/); cars.com: "Brand-new model for 2018" (https://www.car

### Mitsubishi

- Outlander US2022+ (2022–2026): consumerreports.org: "The seven-passenger Outlander is fully redesigned for 2022." (https://www.consumerreports.org/cars/mitsubishi/outlander/); cars.com: "An all-new platform transforms the 2022 Mitsubishi Outlander from a quirky, dated entry in the compact crossover field to a sophisticated, techn
- Outlander: MY2016: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "2016 Model Redesign Year" (https://www.consumerreports.org/cars/mitsubishi/outlander/) [media: weak])
- Outlander Sport: MY2015: one site lists a new generation without redesign wording and the data show no boundary; not used (consumerreports.org: "This aging small SUV is a shortened version of the previous-generation Outlander" (https://www.consumerreports.org/cars/mitsubishi/outlander-sport/) [media: weak])

### Tesla

- Model Y: MY2025: detected boundary (vPIC Canadian specifications: overall width 192 -> 198 cm (MY2024 -> MY2025; a change of 6 cm or more)) dropped; consumerreports.org: "the Model Y received an extensive update for 2025, with a freshened appearance with more Cybertruck-like horizontal lighting, front and re

