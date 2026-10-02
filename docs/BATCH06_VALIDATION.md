# Batch06: опубликованные данные и проверка

`us-base-catalog-06` опубликован в существующей локальной БД, backend 0.8.1.
[Checkpoint](CHECKPOINT_US_BASE_CATALOG.md) сначала содержит полную поимённую delta,
накопительные strict/conditional таблицы с точными engine/transmission/drive/year,
затем счётчики. [Checkpoint05](CHECKPOINT_US_BASE_CATALOG_05.md) сохранён.

## Области пакета

| Make | Model / generation | US MY | Опубликованные варианты |
|---|---|---|---|
| Mercedes-Benz | GLE SUV166 | 2016–2018 | 300d/7AT/AWD2016; 350/7AT/RWD,AWD2016–2018; 400/7AT/AWD2016 и9AT/AWD2017; 550e/7AT/AWD2016–2018; AMG43/9AT/AWD2017–2018; AMG63/63S/7AT/AWD2016–2018 |
| BMW | X5 F15 | 2014–2016 | 35i/8AT/RWD,AWD;35d/8AT/AWD;50i/8AT/AWD;40e/8AT/AWD только2016 |
| Audi | A6 4G sedan | 2012–2015 | 2.0T/CVT/FWD2012–2015;2.0T/8AT/AWD2013–2015;3.0supercharged/8AT/AWD2012–2015;3.0TDI/8AT/AWD2014–2015 |
| Volkswagen | Touareg7P | 2013–2015 | 3.6FSI,3.0TDI,3.0superchargedHybrid; все8AT/AWD |
| Hyundai | Santa Fe Sport AN | 2013–2016 | 2.4GDI и2.0T GDI;6AT;FWD/AWD; короткий кузов |
| Toyota | Corolla XI | 2014–2016 | L1.8DualVVTi/6MT,4AT;SPlus1.8/6MT;LE1.8/CVT;S1.8/CVT;LEEco1.8Valvematic/CVT;всеFWD |
| Honda | CR-V IV | 2012–2014 | 2.4i-VTEC/5AT/FWD,AWD |
| Lexus | RX III | 2013–2015 | RX350/6AT/FWD,AWD;RX350FSport/8AT/AWD;RX450h/eCVT/FWD,AWD |
| Infiniti | Q50 V37 | 2017 | Дополнены2.0t,3.0t300hp,RedSport400hp;7AT;RWD/AWD |
| Chevrolet | Cruze II sedan | 2018 | Дополнены1.4LE2/6MT,6AT и1.6LH7diesel/6MT,9AT;FWD |

Точная поштучная применимость и ссылки — [delta-with-sources.md](../deliverables/VerifiedData/us-base-catalog-06/delta-with-sources.md).
24 существующие записи имеют только evidence refresh: Q50 ICE2016/2018 и Hybrid2016–2018,
Cruze2017/2019. Это не новые технические значения и не рост каталога.

## Реально добавленные технические поля

- Все восемь новых семейств: подтверждённые поколение/рынок/годы, двигатели,
  коробки, привод и кузов; доступные мощность, момент, впрыск/наддув и заводские размеры.
- В годовых таблицах добавлены применимые подвеска, тормоза, вместимость и оснащение.
  Полнота всех11подкатегорий не заявлена: ноль полей не считается заполненным разделом.
- Q50 MY2017: объём масла **с фильтром**, отдельно двигатель и привод:
  2.0T RWD6.3L/AWD6.6L;3.0T300/400hp RWD4.8L/AWD5.4L.
  Существующие вязкость и допуск сохранены. Добавлены MaticS ATF, DOT3,
  AKI91 minimum и рекомендация AKI93 для VR30. Hybrid и соседние MY исключены.
- Cruze MY2018: LE2 масло4.0L с фильтром, dexos1Gen2 full synthetic, SAE0W20;
  LH7 масло5.0L с фильтром, dexos2, SAE5W30 (0W40 ниже−29°C по руководству).
  DEXRON-VI для AT; заводской US part19259104 для MT; DEX-COOL50:50 и DOT3.
  Объём жидкости коробки в использованной таблице не указан, поэтому не придуман.
- Исправлен бак Cruze2018gasAT: LS12.0USgal, остальные13.7USgal. В прошлой
  ревизии13.7 было слишком широким. История сохранена. Для MY2019 требуется своя проверка.
- X5 MY2016: заводские коды двигателей/коробок, AKI minimum/recommended для бензина,
  табличные объёмы масла. Вид заправки таблица не уточняет; это явно подписано.
- A6: табличные объёмы масла в исходных USqt; не выданы за drain/refill в литрах.
  Вязкость/допуск не выведены из соседних двигателей или годов.
- RX: исходные87/91 из брошюры сохранены с оговоркой об отсутствии названия шкалы;
  поле AKI/RON не заполнено предположением.

Все фактические значения, языки, источники и локаторы —
[technical-fields.json](../deliverables/VerifiedData/us-base-catalog-06/technical-fields.json).
[Технические подкатегории](../deliverables/VerifiedData/us-base-catalog-06/technical-coverage.md)
перечислены по точным версиям, включая незаполненные поля.

## Ограничения доказательств

Manufacturer-authored brochures на auto-brochures/dealereprocess обозначены зеркалами,
а не официальными доменами. Factory PDF и официальные BMW/NHTSA документы имеют raw hashes.
42 использованных документальных ссылки сверены с registry, URL, SHA-256, make/model/market/year.
NHTSA TSB для кодов поколений не превращены в KnownIssue/recall применимости.

BMW2015: архивный файл повторяет copyright2014; annual identity опирается на официальный
датированный MY2015 orderguide, не имя файла. Спорные X5 длина192.4/193.2in и
объём35i2979/3004cc исключены; номинальные3.0L и подтверждённые связки сохранены.
Corolla2014:140hpLEEco из технической матрицы; противоречивое132hp из общего рекламного
абзаца не перенесено. История discrepancy сохранена в manifest.

Коды: GLE166, A6 4G, Touareg7P; SantaFeSport — подтверждённый US AN, не long-bodyNC.
Официальные Toyota/Honda web releases отдельно подтверждают порядковые поколения.
Локальный HTTP этих страниц дал403 при доступности web-инструменту; raw response
не фальсифицирован, ограничение записано в generation_corroboration.

Rogue7places остаётся только S/SV FamilyPackage; Accord MT не переносится между
кузовами/комплектациями. RXF-Sport8AT не переносится на обычный RX350. X540e не7мест.

## Места: три раздельные когорты

| Когорта | Было | Закрыто | Осталось |
|---|---:|---:|---:|
| Старые143 |143|0|143|
| Добавленные в batch05 |10|0|10|
| Новые batch06 |24|0|24|

Новые24: GLE2016–2017(14),X52015(4),A62012(2),SantaFeSport2013(4).
Другие86новых записей имеют явное подтверждение мест. Старые документы проверены
пакетно в точных областях; расчёт нагрузки, фото и вместимость соседнего кузова/MY
не использованы как доказательство. Расширение каталога на эти пробелы не ожидало.
[Поимённый остаток](../deliverables/VerifiedData/us-base-catalog-06/remaining-seating.md)
и [раздельные когорты](../deliverables/VerifiedData/us-base-catalog-06/seating-cohorts-after.json).

## Проверки

- 342 regression tests PASS,72.12s;2 предупреждения deprecated test-client API.
- `ruff check backend scripts` PASS.
- 144 batch targets проверены resolver,42 source documents, все10областей фильтра в AZ/RU.
- Накопленная матрица resolver:598конфигураций;18отрицательных сочетаний.
  Rogue min7seats в AZ/RU возвращает только6годовых FamilyPackageконфигураций.
- Live HTTP:47PASS,17марок×AZ/RU, facets/search/profile/compare.
-598профилей сверены по ключам и source URLs в AZ/RU.
- Повтор всех baseline/reviewed jobs: без новых revisions/jobs/raw docs и без изменения
  хеша каталога. [Idempotency](../deliverables/VerifiedData/us-base-catalog-06/idempotency.json).
- [Preservation](../deliverables/VerifiedData/us-base-catalog-06/preservation.json):
  никаких удалений/неожиданных изменений; SQLite integrity/FK PASS.
- SHA-25618UI-файлов и трёх файлов правил publication/search/schema совпадают с baseline.
  Рост strict вызван новыми доказательствами, правила выдачи неизменны.

## Реальные снимки и перенос

[PNG из живого preview](../deliverables/VerifiedData/us-base-catalog-06/screenshots/README.md):
Corolla2016SPlus6MT и Q5020173.0TAWD, жидкости на RU/AZ. Снимки viewport без склейки
и редактирования. Ссылки на источники и отображение неизвестных полей проверены.
Новый UI не создан; телефон, APK и Hetzner не проверялись/не развёртывались.

До публикации: `.backups/before-us-base-06-20260922T075458Z.sqlite3`.
[Baseline hashes](../deliverables/VerifiedData/us-base-06-baseline.json) и isolated
in-memory restore integrity/FK PASS. Работающая БД не откатывалась.
Для rollback остановить writer-процессы, сохранить текущее состояние отдельно,
восстановить проверенную копию через SQLite backup API, не копировать поверх WAL.

Обновлённый source/deployment ZIP содержит source/manifests/docs; **без живой БД,
private raw manuals и секретов**. Не выдавать старые portable exports за текущий verified restore.
Новой среде нужны permitted acquisition, локальные RawDocument/revision IDs,
финальные manifests с historical corrections и обычный review/publish/audit.
Prepared IDs напрямую между БД не переносятся. Повтор batch06 проверен на текущей БД.

Платные provider/LLM/image calls0. Phone/Hetzner/costs/deep dossiers/commercial features
остались отложенными; существующие модули и данные сохранены.
