# Документы с американским графиком ТО: что найдено и что нужно от владельца

Дата: 2026-10-04. Основание: `data_work/product/maintenance_gaps_input.json` (модели без графика ТО, рынок США). Работа только исследовательская: в `autoexpert.db` и в код backend ничего не записано.

## Итог коротко

- **Toyota (Camry, Corolla, RAV4, Highlander, 2014-2026):** ничего не найдено. Американские руководства владельца Toyota графика ТО не содержат (проверены все 49 PDF на диске: Camry/Camry Hybrid 2014-2023, Corolla 2017-2023 и 2026, RAV4/Hybrid/Prime 2014-2023 и 2026 Plug-in Hybrid, Highlander/Hybrid 2015-2023 — ни в одном нет таблицы интервалов) — они отсылают к отдельной книжке «Scheduled Maintenance Guide» / «Warranty and Maintenance Guide». На carmans.net и mycarusermanual.com этих книжек нет. Официальные PDF (assets.sipb.toyota.com) из Азербайджана заблокированы, обход не применялся. Нужно 52 гида (4 модели × 13 лет).
- **Hyundai Sonata 2024-2026, Tucson 2025-2026, Santa Fe 2024-2026:** документы **уже есть на диске** (официальные US-руководства с ownersmanual.hyundai.com), график ТО внутри есть (обычный и для тяжёлых условий). Пробел в БД — не из-за документов, а потому что сборщик ТО не выпустил по ним пунктов. Владельцу ничего доставать не нужно.
- **Hyundai Sonata 2014-2019, Elantra 2014-2020, Tucson 2014-2021, Santa Fe 2014-2018:** не найдено ни на диске, ни на копи-сайтах (Hyundai на carmans.net нет вообще; на mycarusermanual.com нет Sonata/Elantra, Tucson — не US-издания или год не подтверждён, Santa Fe — только 2023). Нужно 26 руководств.
- С копи-сайтов **ничего не скачано**: подходящих файлов нет. Манифест `C:\AutoExpertData\raw\manuals\copysites_maintenance_manifest.csv` создан, строк нет.

## А) Найдено

Все — официальные PDF Hyundai, скачанные раньше (`C:\AutoExpertData\raw\official\hyundai\ownersmanual.hyundai.com`). Страницы — номера страниц PDF (не печатные номера). Год модели в самих PDF не напечатан (только copyright); год — из названия документа в официальном каталоге ownersmanual.hyundai.com (страна U.S.A, язык en_US).

| Модель | Год(ы) | Документ | US подтверждён | Источник | Локальный файл | Обычный график, стр. | Тяжёлые условия, стр. | Примечание |
|---|---|---|---|---|---|---|---|---|
| Hyundai Sonata | 2024 | 2024 Sonata Owner's Manual (DN8, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/DN8/2024/en_US | `DN8_2024_ICE_SONATA.pdf` | 427-430 | 431-432 | вводная 425-426, пояснения с 433 |
| Hyundai Sonata | 2024 | 2024 Sonata Hybrid Owner's Manual (DN8HEV, HEV, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/DN8HEV/2024/en_US | `DN8HEV_2024_HEV_SONATA-HYBRID.pdf` | 473-475 | 476-477 | гибрид; вводная 472 |
| Hyundai Sonata | 2025 | 2025 Sonata Owner's Manual (DN8, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/DN8/2025/en_US | `DN8_2025_ICE_SONATA.pdf` | 483-486 | 487-488 | вводная 481-482 |
| Hyundai Sonata | 2025 | 2025 Sonata Hybrid Owner's Manual (DN8HEV, HEV, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/DN8HEV/2025/en_US | `DN8HEV_2025_HEV_SONATA-HYBRID.pdf` | 473-475 | 476-477 | гибрид |
| Hyundai Sonata | 2026 | 2026 Sonata Owner's Manual (DN8, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/DN8/2026/en_US | `DN8_2026_ICE_SONATA.pdf` | 479-482 | 483-484 | вводная 477-478 |
| Hyundai Sonata | 2026 | 2026 Sonata Hybrid Owner's Manual (DN8HEV, HEV, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/DN8HEV/2026/en_US | `DN8HEV_2026_HEV_SONATA-HYBRID.pdf` | 473-475 | 476-477 | гибрид |
| Hyundai Tucson | 2025 | 2025 Tucson Owner's Manual (NX4, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/NX4/2025/en_US | `NX4_2025_ICE_TUCSON.pdf` | 525-529 | 530-531 | вводная 523-524 |
| Hyundai Tucson | 2025 | 2025 Tucson Owner's Manual (NX4a, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/NX4a/2025/en_US | `NX4a_2025_ICE_TUCSON.pdf` | 523-527 | 528-529 | вводная 521-522 |
| Hyundai Tucson | 2026 | 2026 Tucson Owner's Manual (NX4, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/NX4/2026/en_US | `NX4_2026_ICE_TUCSON.pdf` | 668-672 | 672-673 | вводная 666-667; сетка без заголовка 'Normal maintenance schedule' (заголовок 'MAINTENANCE INTERVALS') |
| Hyundai Tucson | 2026 | 2026 Tucson Owner's Manual (NX4a, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/NX4a/2026/en_US | `NX4a_2026_ICE_TUCSON.pdf` | нет | нет | сокращённое (abridged) руководство: графика ТО НЕТ; для 2026 использовать NX4_2026 |
| Hyundai Santa Fe | 2024 | 2024 Santa Fe Owner's Manual (MX5a, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/MX5a/2024/en_US | `MX5a_2024_ICE_SANTA-FE.pdf` | 580-584 | 585-586 | вводная 578-579; штамп на страницах 'MX5a-2024-en_US' |
| Hyundai Santa Fe | 2025 | 2025 Santa Fe Owner's Manual (MX5a, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/MX5a/2025/en_US | `MX5a_2025_ICE_SANTA-FE.pdf` | 580-584 | 585-586 | штамп на страницах 'MX5a-2025-en_US' |
| Hyundai Santa Fe | 2025 | 2025 Santa Fe Hybrid Owner's Manual (MX5aHEV, HEV, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/MX5aHEV/2025/en_US | `MX5aHEV_2025_HEV_SANTA-FE-HYBRID.pdf` | 655-657 | 658-659 | гибрид; вводная 653-654 |
| Hyundai Santa Fe | 2026 | 2026 Santa Fe Owner's Manual (MX5a, ICE, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/MX5a/2026/en_US | `MX5a_2026_ICE_SANTA-FE.pdf` | 722-726 | 726-728 | вводная 720-721; заголовок сетки 'MAINTENANCE INTERVALS' |
| Hyundai Santa Fe | 2026 | 2026 Santa Fe Hybrid Owner's Manual (MX5aHEV, HEV, U.S.A en_US) | да: каталог U.S.A/en_US, «HYUNDAI Motor America», мили | https://ownersmanual.hyundai.com/full_pdf/MX5aHEV/2026/en_US | `MX5aHEV_2026_HEV_SANTA-FE-HYBRID.pdf` | 728-730 | 731-732 | гибрид; вводная 726-727 |

По всем этим файлам в `data_work/hyundai/staging/<модель>/maintenance.json` пунктов ТО нет (Sonata — до 2023, Tucson — до 2024, Santa Fe — до 2023). Значит, нужно прогнать/доработать сборщик ТО Hyundai (`scripts/build_maintenance_hmc.py`) по этим документам; это отдельная задача, здесь не делалось. Для 2026 Tucson брать `NX4_2026`, а не `NX4a_2026` (сокращённое руководство без графика). Santa Fe Hybrid 2024 в каталоге нет.

## Б) Нужно от владельца

### Toyota — Warranty & Maintenance Guide (US), по одной книжке на модель и год

Где официально: toyota.com/owners → Manuals & Warranties → модель и год → «Warranty & Maintenance Guide» (PDF лежит на assets.sipb.toyota.com, из Азербайджана закрыт — скачать из США или через знакомого/дилера). Если гид называется «Scheduled Maintenance Guide» или график есть в «Owner's Manual Supplement» — подходит тоже. Если одна книжка прямо называет на обложке несколько лет или моделей — достаточно одной, мы запишем ровно те годы, что в ней названы. Гибриды (Camry Hybrid, RAV4 Hybrid/Prime, Highlander Hybrid, Corolla Hybrid) — если у Toyota на них отдельная книжка, она тоже нужна.

| Модель | Годы | Поколение | Какой документ | Папка | Имя файла |
|---|---|---|---|---|---|
| Toyota Camry | 2014-2017 | XV50 | «<год> Toyota Camry Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\camry\` | `<год>_toyota_camry_warranty_maintenance_guide_US.pdf` |
| Toyota Camry | 2018-2024 | XV70 | «<год> Toyota Camry Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\camry\` | `<год>_toyota_camry_warranty_maintenance_guide_US.pdf` |
| Toyota Camry | 2025-2026 | XV80 | «<год> Toyota Camry Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\camry\` | `<год>_toyota_camry_warranty_maintenance_guide_US.pdf` |
| Toyota Corolla | 2014-2019 | E170 (седан) | «<год> Toyota Corolla Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\corolla\` | `<год>_toyota_corolla_warranty_maintenance_guide_US.pdf` |
| Toyota Corolla | 2020-2026 | E210 | «<год> Toyota Corolla Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\corolla\` | `<год>_toyota_corolla_warranty_maintenance_guide_US.pdf` |
| Toyota RAV4 | 2014-2018 | XA40 | «<год> Toyota RAV4 Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\rav4\` | `<год>_toyota_rav4_warranty_maintenance_guide_US.pdf` |
| Toyota RAV4 | 2019-2025 | XA50 | «<год> Toyota RAV4 Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\rav4\` | `<год>_toyota_rav4_warranty_maintenance_guide_US.pdf` |
| Toyota RAV4 | 2026 | XA60 | «<год> Toyota RAV4 Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\rav4\` | `<год>_toyota_rav4_warranty_maintenance_guide_US.pdf` |
| Toyota Highlander | 2014-2019 | XU50 | «<год> Toyota Highlander Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\highlander\` | `<год>_toyota_highlander_warranty_maintenance_guide_US.pdf` |
| Toyota Highlander | 2020-2026 | XU70 | «<год> Toyota Highlander Warranty & Maintenance Guide (US)» — по одному на каждый год | `C:\AutoExpertData\raw\owner_supplied\toyota\highlander\` | `<год>_toyota_highlander_warranty_maintenance_guide_US.pdf` |

### Hyundai — руководство владельца (US), в нём раздел Maintenance → Scheduled Maintenance Services

Где официально: MyHyundai — hyundaiusa.com/us/en/owners → Manuals & Warranties (PDF на owners.hyundaiusa.com/content/…, robots.txt запрещает скачивать скриптом — скачать вручную в браузере). В официальном каталоге ownersmanual.hyundai.com (U.S.A) этих лет нет. «Owner's Handbook & Warranty Information» Hyundai USA не подходит: графика ТО в нём нет (проверены издания 2019-2026). Нужен американский вариант (мили, «Hyundai Motor America»), не общий/европейский.

| Модель | Годы | Поколение | Какой документ | Папка | Имя файла | Примечание |
|---|---|---|---|---|---|---|
| Hyundai Sonata | 2014 | YF | «2014 Hyundai Sonata Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\sonata\` | `2014_hyundai_sonata_owners_manual_US.pdf` | также 2014 Sonata Hybrid, если нужен гибрид |
| Hyundai Sonata | 2015-2019 | LF | «<год> Hyundai Sonata Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\sonata\` | `<год>_hyundai_sonata_owners_manual_US.pdf` | по одному на год; Sonata Hybrid / Plug-in Hybrid (2016-2019) — отдельные руководства |
| Hyundai Elantra | 2014-2016 | MD/UD | «<год> Hyundai Elantra Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\elantra\` | `<год>_hyundai_elantra_owners_manual_US.pdf` | седан; Elantra GT/Coupe — отдельные руководства |
| Hyundai Elantra | 2017-2020 | AD | «<год> Hyundai Elantra Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\elantra\` | `<год>_hyundai_elantra_owners_manual_US.pdf` | седан; Elantra GT (PD) — отдельное руководство |
| Hyundai Tucson | 2014-2015 | LM | «<год> Hyundai Tucson Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\tucson\` | `<год>_hyundai_tucson_owners_manual_US.pdf` | на mycarusermanual.com есть Tucson 2010-2015, но это не американское издание (бензин+дизель, км) |
| Hyundai Tucson | 2016-2021 | TL | «<год> Hyundai Tucson Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\tucson\` | `<год>_hyundai_tucson_owners_manual_US.pdf` | на mycarusermanual.com Tucson 2016-2019 — европейское/общее издание (дизель, Europe), не US; страница 'Tucson 2020' — US, но год в документе не указан, а сайт подписывает её одновременно '2020' и '2020-2026', график — картинками |
| Hyundai Santa Fe | 2014-2018 | DM (Santa Fe Sport / Santa Fe) | «<год> Hyundai Santa Fe Sport и <год> Hyundai Santa Fe Owner's Manual (US)» — по одному на год | `C:\AutoExpertData\raw\owner_supplied\hyundai\santa-fe\` | `<год>_hyundai_santa_fe_owners_manual_US.pdf` | в эти годы в США два варианта (Sport 5 мест и Santa Fe 7 мест); если руководство общее — одного файла на год достаточно |

Итого нужно: Toyota — 52 гида (Camry 13, Corolla 13, RAV4 13, Highlander 13); Hyundai — 26 руководств (Sonata 6, Elantra 7, Tucson 8, Santa Fe 5). Поштучный список с именами файлов — в `data_work/product/maintenance_documents_needed.json` (`needed_from_owner`).

## Что проверено на копи-сайтах

- **carmans.net:** sitemap (2046 постов) проверен 2026-10-04: Hyundai нет ни одного поста; постов 'maintenance'/'warranty'/'guide' нет; на страницах постов Toyota ровно один PDF — руководство владельца. Руководства Toyota US (Camry 2014-2023, Corolla 2017-2023, RAV4 2014-2023, Highlander 2015-2023) уже лежат локально и графика ТО не содержат (только чек-лист общего ТО и ссылка на 'Scheduled Maintenance Guide'/'Warranty and Maintenance Guide').
- **mycarusermanual.com:** проверен 2026-10-04: Hyundai — bayon, i10, i20, i30, ioniq, ix35, kona, santa-fe (только 2023), tucson (2004-2009, 2010-2015, 2016-2019, 2020); Sonata и Elantra нет. Toyota: camry и highlander без поколений, corolla 2000-2017 и 2023, rav4 2001-2012 и 2020; гидов Warranty & Maintenance нет; в уже скачанных HTML-руководствах Toyota таблиц интервалов нет.
- Не использовались: turbo.az, LEMON, charm.li, VDB. Логинов, капчи, платных разделов и обхода геоблокировки не было.

## Попутные находки

- C:\AutoExpertData\raw\official\hyundai\ownersmanual.hyundai.com\TMa_2018_ICE_SANTA-FE.pdf: каталог Hyundai называет его '2018 Santa Fe', но по содержанию это новое поколение TM (Rear Occupant Alert и т.п.), т.е. фактически 2019MY. В data_work/hyundai/staging/santa-fe/maintenance.json из него 40 пунктов с годами [2018, 2018] и поколением 'NC' (official-8d55d8b56d6d) — график поколения TM привязан к старому поколению; в БД для 2018 его использовать нельзя. Настоящий 2018 Santa Fe (DM) остаётся без документа.
- C:\AutoExpertData\raw\official\hyundai\ownersmanual.hyundai.com\NX4a_2021_ICE_TUCSON.pdf: каталог называет '2021 Tucson', но это 4-е поколение NX4 (вёрстка 2021-12-06), т.е. фактически 2022MY. Для 2021 Tucson (TL) нужен свой документ.
- C:\AutoExpertData\raw\manuals\toyota\carmans\2021-toyota-rav4.pdf и 2022-toyota-rav4.pdf: на первых страницах 'Plug-in hybrid system' — это руководства RAV4 Prime, а не обычного RAV4.
- C:\AutoExpertData\raw\manuals\toyota\carmans\2026-toyota-corolla.pdf: канадское издание (Toyota Canada, уведомление для Квебека), не US.
