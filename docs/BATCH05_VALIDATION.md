# Batch05: проверка данных и существующего интерфейса

`us-base-catalog-05` опубликован локально поверх исправленного batch04, backend 0.8.1.
[Полный checkpoint](CHECKPOINT_US_BASE_CATALOG.md) содержит сначала поимённую delta,
накопительные строгий и условный каталоги с точными engine/transmission/drive/year,
затем агрегаты. [Checkpoint04](CHECKPOINT_US_BASE_CATALOG_04.md) сохранён.

## Область и фактический результат

Новые области: Camry V MY2002–2006, Camry VII MY2012–2017, Accord VII MY2003 и
MY2006–2007, Elantra MD/UD MY2011–2016, Rogue T32 MY2014–2016. Только перечисленные
в manifest версии; годы между областями Accord не интерполированы. Из моделей
впервые добавлен Rogue, остальные получили поколения/годы.

76 новых конфигураций; 54 существующие получили изменённые технические поля,
14 — только обновлённые ссылки/ревизии evidence. Последние не считаются новыми данными.
Из них Lexus ES MY2016–2018 — 6 записей только с обновлением evidence; у Q50
MY2018 — ещё 8 таких записей. Изменённые технические поля Q50 относятся к MY2016–2017.
Итого 30 доступных моделей / 488 конфигураций, из них 24 модели / 335 конфигураций
с подтверждёнными местами. 143 старых seating gaps не закрыты; добавлено 10 новых.
Рост строгой готовности на 66 относится к новым записям с явным подтверждением мест.

По E-Class W212, Jetta VI, Evoque LV, Cruze II, ES VI и Q50 V37 проверены уже
использованные годовые материалы и дополнительные руководства/заводские страницы.
Размеры и применимые сведения о жидкостях добавлены. Надёжного явного подтверждения
мест для этих агрегированных областей не найдено. Примеры расчёта нагрузки,
места универсала/кабриолета и соседние годы не перенесены. Эти модели сохраняют
обычную доступность, когда пользователь не требует неизвестное поле.

Существующие `US_CONFIRMED_2000`, `US_BASE_2000`, resolver и buyer-фильтры не изменены.
Рост произошёл за счёт опубликованных фактов. Исходный SHA-256 `us_catalog_ready`
совпадает. 18 UI-файлов совпадают с baseline; прикладной код и дизайн не менялись.

## Доказательства и неоднозначности

- Годовые manufacturer-authored brochures из архивов описаны как зеркала заводских
  документов, не как официальные домены. Использованные 54 raw documents сверены
  по SHA-256, registry, URL, рынку и годам.
- Camry V: 2.4/4AT только MY2002–2004; 2.4/5AT MY2005–2006;
  3.0/4AT MY2002–2003; 3.0/5AT MY2004–2006; 3.3SE/5AT MY2004–2006.
  2.4/5MT подтверждён MY2002–2006. V6/manual не добавлен.
- Camry VII: 2.5/6AT, 3.5/6AT, 2.5HEV/eCVT MY2012–2017. Длина меняется с
  facelift MY2015; мощность гибридной системы не записана как мощность одного ДВС.
- Accord: 2003 V6/6MT относится к coupe и не подтверждает sedan. Седан V6/6MT
  добавлен только MY2006–2007. MY2004–2005 оставлены в очереди.
- Elantra MD/UD: Touring/GT/Coupe не смешаны с sedan. Sport6MT MY2016 упомянут
  в таблице расхода, но неоднозначен в retail equipment — не опубликован.
  Места подтверждены руководствами MY2014 и MY2016, без переноса на другие годы.
  Размеры MY2016 взяты из годовой брошюры; противоречивая таблица руководства исключена.
- Rogue: 5 мест либо 7 только S/SV Family Package. Это один QR25DE/CVT с разными
  вариантами оснащения, а не две коробки. Rogue Select S35 и Rogue Sport не добавлены.
  Запрос минимум 7 мест возвращает шесть годовых FWD/AWD конфигураций Family Package.
- E-Class MY2014: масло 6.5 L при замене с фильтром относится к E250 BlueTEC/E350;
  объём DEF не перепутан с моторным маслом. AMG-допуски не перенесены.
- Q50 MY2017: допуски и вязкость раздельно для 2.0T и VR30 3.0T. Объём масла
  зависит также от привода и не сведён в одно агрегированное число; Hybrid исключён.
- Tesla: сохранён конкретный Model S MY2016 и ограниченно проверен Model 3 MY2020.
  Датированная идентичность второй области пока недостаточна; ни одна не опубликована.
  Это не утверждение об отсутствии источников по всей марке.

Официальные web-страницы Toyota/Honda подтверждают порядковые поколения. Некоторые
из них доступны web-инструменту, но локальный HTTP дал 403; фиктивных raw responses нет.
`generation_corroboration` в manifest отдельно фиксирует это ограничение. В проверяемой
цепочке остаются годовые заводские таблицы и применимые документы NHTSA.

## Сохранённая корректирующая публикация

Первоначальная попытка Toyota остановилась на `IDENTITY_RANGE_EVIDENCE_GAP`:
в generation references были только крайние годы, хотя годовые PDF уже получены.
Транзакция Toyota не прошла. Её job/revisions сохранены как `SUPERSEDED`, не удалены.

`data/manifests/us-base-catalog-05-correction-01.json` завершает 102 оставшиеся цели:
для Camry VII и Accord VII используется существующий fallback к **каждому годовому
документу своего сочетания**, вместо ссылок только на крайние годы. Исходный manifest05
и prepared-файл неизменны. Verification gate не менялся. 42 цели первых успешно
опубликованных source jobs сохранены; остальные прошли исправление. Parent publication
содержит `PARENT_PUBLISHED_JOBS_PLUS_CORRECTION` и перечень реальных завершённых jobs.

## Проверки

- 342 regression tests PASS, 43.74 s; 2 предупреждения deprecated test-client API.
- `ruff check backend scripts` PASS. Изменён только read-only report generator,
  data manifests, policy active batch и документация; UI/продуктовая логика неизменны.
- [Live HTTP](../deliverables/VerifiedData/us-base-catalog-05/live-http.json): 47 PASS,
  AZ/RU, все 17 марок, поиск, facets, профиль, сравнение и строгие семь мест.
- [Batch resolver](../deliverables/VerifiedData/us-base-catalog-05/resolver-matrix.json):
  144 цели; фильтры всех 11 семейных областей в AZ/RU, strict и отрицательные проверки.
- [Весь обычный каталог](../deliverables/VerifiedData/us-base-catalog-05/ordinary-resolver-matrix.json):
  488 конфигураций, 10 отрицательных сочетаний и отдельный Rogue Family Package в AZ/RU.
  Отсутствие подтверждённого сочетания не объявляет автомобиль невозможным вне базы evidence.
- [Профили](../deliverables/VerifiedData/us-base-catalog-05/technical-fields.json):
  все 488 сравниваются по ключам и URL источников AZ/RU. Пустые подкатегории остаются
  пустыми и не считаются полным dossier.
- [Idempotency](../deliverables/VerifiedData/us-base-catalog-05/idempotency.json):
  повтор всех успешных parent jobs и correction не меняет хеш каталога, количество
  variants/generations/revisions/jobs/raw documents. Superseded job не повторяется.
- [Preservation](../deliverables/VerifiedData/us-base-catalog-05/preservation.json):
  старые записи, история и пользовательские данные сохранены, удалений нет.

## Снимки существующей реализации

[Browser QA](../deliverables/VerifiedData/us-base-catalog-05/browser-qa/README.md).
Снимки сняты из работающего preview; реальные значения показаны, не нарисованы.
Четыре цветные категории, синяя рекомендация и альтернативы сохранены. Placeholder
изображений остаётся прежним; фотографии из эталонного макета не подставлялись.
Выдача снята двумя последовательными viewport-снимками, чтобы не использовать
некорректно склеенный full-page capture. Итоговые PNG проверены визуально.
Телефон и APK в этом пакете не проверялись и не пересобирались.

## Резервная копия и перенос

До импорта SQLite backup API создал
`.backups/before-us-base-05-20260921T232537Z.sqlite3`.
SHA-256 и UI hashes: [baseline](../deliverables/VerifiedData/us-base-05-baseline.json).
Восстановление в отдельную in-memory БД проверило integrity/foreign keys.
Рабочая БД не откатывалась. Для реального rollback сначала остановить writer-процессы,
сохранить текущую БД отдельно и восстановить проверенную копию SQLite backup API;
не копировать файл поверх работающего WAL.

Source/deployment ZIP включает source/manifests/docs, **не живую БД**, `.env`, ключи
или private raw manuals. Исторические `published-data` exports не выдаются за свежий
verified restore. Финальные факты и provenance текущего состояния находятся в
`technical-fields.json`, final correction и остальных каталожных manifests.

Для новой среды нужны разрешённое получение документов, новые локальные RawDocument
и revision IDs, составление финального manifest с применёнными corrections, обычный
review/publish и resolver-аудит. Не переносить prepared IDs напрямую и не повторять
superseded parent Toyota job. На текущей БД повтор успешных jobs проверен отдельно.
Крупный manual импортирован с process-only limit 64 MiB; `.env` и API limit не менялись.

Платные provider/LLM/image calls: 0. Costs, СТО, deep dossiers, images, ads, телефон
и Hetzner остались отложенными. Никакого нового этапа или редизайна не создано.
