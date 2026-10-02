# Auto Expert — US base catalogue / approved UX flow

Checkpoint: **2026-09-21**, backend **0.8.1**, существующий проект и локальная БД.
**Batch `us-base-catalog-02` опубликован. Общий этап — PARTIAL.**

Текущий scope: 17 приоритетных марок, только US, MY2000+. Range Rover — линейка
Land Rover. Skoda исключена. Исторические данные других рынков сохранены.
Ни Turbo.az crawler, ни фиктивная выгрузка не создавались; точные числа объявлений
неизвестны. Приоритет моделей редакционный, не измеренная популярность.

## Публикация

Добавлены **103 конфигурации восьми новых моделей**: E-Class, GLC-Class, 5 Series,
Q5, Sonata, Tucson, Jetta, Tiguan. **73 существующие конфигурации Kia** дополнены
документальными фактами. Всего batch содержит **176 целевых записей**.

| Показатель, накопительно | Базовая техника, прежний контракт | Текущий US-слой с подтверждёнными местами |
|---|---:|---:|
| Марки | 6 из 17 | 5 из 17 |
| Модели | 18 | 8 |
| Поколения | 19 | 9 |
| Поколение × рынок | 19 | 9 |
| Варианты двигателей | 47 | 17 |
| Варианты коробок | 42 | 15 |
| Сочетания двигатель / коробка | 67 | 22 |
| Сочетания с учётом привода | 93 | 32 |
| Конфигурации по модельным годам | 271 | 71 |
| Модели с пригодной для filter/resolver областью | 18 | 8 |

**По новому Definition of Done готовы только 71 конфигурация восьми моделей.**
У 200 базовых конфигураций пока недостаточно documentary evidence для числа мест.
Они сохранены, но не выдаются как готовые в `US_BASE_2000`. Отличие от предыдущего
checkpoint связано с новым обязательным seating, а не удалением данных.
BMW330i MY2025 сохранён отдельно как pipeline proof и в эти базовые счётчики не включён.

Счётчики относятся к подтверждённым подмножествам, не всем комплектациям и годам
жизни поколений. Двигатели и коробки дедуплицированы; реальные сочетания сохраняются
целиком, списки не перемножаются. Market variant здесь — поколение × рынок.

## Coverage 17 марок

| Марка | Модели, база | Поколения | Двигатели | Коробки | Сочетания | Годовые конфигурации | Готовы с местами: модели / конфигурации |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mercedes-Benz | 3 | 3 | 5 | 4 | 6 | 30 | 1 / 2 |
| BMW | 2 | 2 | 9 | 4 | 14 | 54 | 1 / 18 |
| Audi | 2 | 2 | 4 | 4 | 6 | 19 | 2 / 19 |
| Volkswagen | 3 | 3 | 8 | 9 | 12 | 30 | 1 / 9 |
| Hyundai | 3 | 3 | 7 | 8 | 10 | 46 | 0 / 0 |
| Kia | 5 | 6 | 14 | 13 | 19 | 92 | 3 / 23 |
| Toyota | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Nissan | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Honda | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Land Rover | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Chevrolet | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Lexus | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Infiniti | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Jeep | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Mitsubishi | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Cadillac | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| Tesla | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |

Ноль означает отсутствие подтверждённого базового покрытия, а не отсутствие марки
на рынке или исследовательских строк в БД. Полное покрытие 17 марок не заявляется.

## Подтверждённая область batch02

| Модель | Поколение | MY | Целевые конфигурации | Из них с местами |
|---|---|---|---:|---:|
| Mercedes-Benz E-Class | W212 sedan | 2014–2016 | 16 | 0 |
| Mercedes-Benz GLC-Class | X253 | 2017–2019 | 6 | 2 |
| BMW 5 Series | F10 sedan | 2014–2015 | 18 | 18 |
| Audi Q5 | 8R | 2014–2017 | 10 | 10 |
| Hyundai Sonata | LF | 2015–2019 | 15 | 0 |
| Hyundai Tucson | TL | 2016–2020 | 20 | 0 |
| Volkswagen Jetta | VI | 2017–2018 | 9 | 0 |
| Volkswagen Tiguan | II-US-LWB | 2018–2020 | 9 | 9 |
| Kia Sportage | QL | 2017–2022 | 30 | 6 |
| Kia Sorento | UM | 2016–2020 | 29 | 8 |
| Kia Forte | YD | 2017–2018 | 6 | 6 |
| Kia Forte | BD | 2019–2020 | 8 | 3 |

Точные ежегодные двигатели, коробки, кузова, привод и локаторы находятся в
[неизменяемом manifest](../data/manifests/us-base-catalog-batch-02.json).
73 строки Kia — обновления, не новые автомобили.

- E-Class: E250 BlueTEC, E350, E400 в применимых годах; wagon/coupe/AMG не добавлены по аналогии.
- GLC300: 9AT RWD/AWD; места подтверждены только MY2018. «ATHLETIC FIVE» в MY2019
  означает предложения линейки, а не число мест.
- BMW F10: применимые 528i/535i/535d/550i; 535i 6MT только RWD. Остальное по годовым таблицам.
- Q5: 2.0T/3.0T; TDI только MY2014–2015. MY2016 TDI не перенесён через stop-sale.
- Sonata: 2.4 GDI 6AT, Eco 1.6T 7DCT, 2.0T 6AT до MY2017 / 8AT с MY2018.
- Tucson: 2.0 GDI 6AT; 1.6T 7DCT MY2016–2018; 2.4 GDI 6AT MY2019–2020.
  Ранняя брошюра MY2018 не подтверждает поздний Sport 2.4; этот вариант исключён.
- Jetta: 1.4TSI/1.8TSI/GLI с применимыми коробками. Неоднозначные колонки MY2016
  исключены. GLI 6MT подтверждён только MY2017.
- Tiguan: US LWB, 2.0TSI 8AT; FWD 7 мест, AWD 5/7 мест — отдельные конфигурации.
  `II-US-LWB` — внутреннее обозначение поколения, не заводской chassis code.
  Годовые размеры сохранены раздельно; MY2020 не подменяет MY2018/2019.

## Доказательства

Проверены **52 уникальных документа**: RawDocument, SHA-256, URL, locator, годы.
Заводские брошюры на публичном зеркале имеют отдельно издателя и адрес размещения;
зеркало не объявлено официальным сайтом производителя.

- [Документы и локаторы](../deliverables/VerifiedData/us-base-catalog-02/documents.json).
- [Годовые брошюры: acquisition manifest](../data/manifests/az-base-02-acquisition.json).
- [Дополнительные factory документы](../data/manifests/us-base-02-supplemental-acquisition.json).
- [Mercedes-Benz: W212/X253](https://www.mbusa.com/content/mb-nafta/en_us/winter-wheel-and-tire-assemblies.html).
- [Audi: manufacturer applicability](https://static.nhtsa.gov/odi/tsbs/2024/MC-10253261-0001.pdf).
- [Hyundai: applicability](https://static.nhtsa.gov/odi/tsbs/2024/MC-11000314-0001.pdf).
- [BMW: F10 applicability](https://static.nhtsa.gov/odi/tsbs/2021/MC-10198894-9999.pdf).
- [Volkswagen: Jetta VI](https://www.volkswagen-newsroom.com/en/international-driving-presentation-of-the-new-jetta-2292/the-new-jetta-body-styling-and-function-2302).
- [Volkswagen: Tiguan generations](https://www.volkswagen-newsroom.com/en/tiguan-global-bestseller-breaks-the-six-million-mark-and-has-been-the-best-selling-volkswagen-in-2019-5964).

Бюллетень для определения поколения не становится автоматически known issue.
EPA row не считается доказательством точной комплектации. Новых платных calls: **0**.
Это локальная исследовательская публикация; коммерческие права на распространение
всех документов не заявлены. Production rights gate сохранён.

## UI/UX и подбор

Сохранены white/blue оформление и три направления главной. «Начать подбор» ведёт
прямо к фильтрам, затем результатам и профилю. В текущем слое только US MY2000+,
марка необязательна. Top recommendation имеет причины, ниже конкуренты разных моделей.

Ranking учитывает условия и выбранные измеримые предпочтения, только при сопоставимых
данных всей группы. Неизвестные надёжность, цены и расходы не получают выдуманный балл.
Равенство раскрывается: более новый модельный год, затем название. При неизвестном
бюджете нет ложного подтверждения доступности по цене — требуется уточнение.

Профиль: сводка сверху без «Обзора», четыре цветные категории и 11 технических подгрупп.
Factory facts имеют ссылки. Отсутствующие данные не выданы за полный dossier.
0–60 mph не пересчитан в 0–100 km/h; Regular/Premium не превращён в AI-92/AI-95.
Existing ownership-система сохранена в сравнении, работа над ней не велась.
Имеющийся placeholder изображения не блокирует каталог.

## Проверка

- Все 176 целей проверены resolver; строгий scope учитывает места. AZ/RU фильтры
  проверены по семействам; противоречивый двигатель отвергается.
- Live HTTP: 13 PASS — подбор без марки, Tiguan AWD 5/7 мест, исключение CA/Skoda,
  неизвестный бюджет, профили и сравнение.
- Браузер: 4 экрана × AZ/RU × 360/390/430 = 24 проверки, без горизонтального overflow.
  Пройден основной flow; сравнение Kia Forte/Audi A4 работает. Проверены категории,
  11 подгрупп и клавиатурное переключение вкладок.
- Регрессия: **336 PASS**, две прежние dependency deprecation warnings.
- DB preservation PASS: нет удалений и неожиданных изменений. Старые ревизии и отчёты
  сохранены. UI изменён только в catalog-views.js, catalog-copy.js, styles.css.
- Телефон и Hetzner: **DEFERRED_BY_USER**. Real-device PASS не заявляется.
- APK этим batch не пересобирался: существующий APK0.8.1 — предыдущая сборка.

[Coverage](../deliverables/VerifiedData/us-base-catalog-02/coverage.json) ·
[Resolver matrix](../deliverables/VerifiedData/us-base-catalog-02/resolver-matrix.json) ·
[Live HTTP](../deliverables/VerifiedData/us-base-catalog-02/live-http.json) ·
[Responsive UI](../deliverables/VerifiedData/us-base-catalog-02/responsive-ui.json) ·
[Preservation](../deliverables/VerifiedData/us-base-catalog-02/preservation.json).

## Запуск и перенос

Локальная версия: http://127.0.0.1:8000/preview/.
На этом компьютере .venv/python.exe отклонён Windows App Control. Защита не менялась.
Поддержан явный `Start-Local.ps1 -PythonExecutable <absolute-python-path>`: используются
уже установленный bundled Codex Python3.12 и зависимости проекта через PYTHONPATH.
На обычной разрешённой среде штатный запуск по-прежнему использует .venv.

Проверки с зависимостями проекта:

```powershell
python scripts/checkpoint_base_catalog.py --baseline deliverables/VerifiedData/us-base-02-baseline.json
python scripts/smoke_us_catalog.py
python -m pytest -q
```

Активный manifest выбирается из policy. `run_base_catalog_batch.py` подготавливает
его; `--publish-reviewed` публикует проверенный batch. В существующей локальной БД
с теми же prepared.json и документами повтор идемпотентен. Опубликованные batch01/02
не редактировать: изменения оформлять следующим batch и новыми ревизиями.

[Source/deployment archive](../deliverables/VerifiedData/AutoExpert_0.8.1_VerifiedData_Source_Deployment.zip)
и [QA archive](../deliverables/VerifiedData/AutoExpert_0.8.1_VerifiedData_QA.zip) не содержат
живую БД, .env, секреты, частный PDF-кеш, user/account/session metadata.
SHA256SUMS и inventory приложены отдельно.

**Архив не переносит готовую БД одной распаковкой.** На новой БД требуются повторный
source acquisition, сопоставление RawDocument IDs и baseline revisions и review.
Локальные IDs из prepared manifest нельзя применять к чужой БД. Прежний portable fact
bundle остаётся research baseline. [Deployment runbook](../deploy/README.md) подготовлен;
развёртывание не выполнялось.

## Следующий batch

Оставшиеся 11 марок брать пакетно из `first_wave_model_order` существующей
[policy](../data/manifests/az-market-priority-policy.json): Toyota, Nissan, Honda, Land Rover,
Chevrolet, Lexus, Infiniti, Jeep, Mitsubishi, Cadillac, Tesla. Поколения, годы и реальные
сочетания подтверждать документами. Редакционные имена кандидатов не считать готовыми.
Отдельная очередь — seating evidence для 200 существующих конфигураций.
Новые ready-записи должны сразу иметь подтверждённые места. Другие рынки, ownership,
изображения, глубокие dossiers, телефон и сервер не являются gate следующего batch.
