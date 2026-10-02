# Batch04: проверки, ограничения и восстановление

Публикация `us-base-catalog-04` выполнена локально поверх batch03, backend 0.8.1.
Поимённые результаты и цифры находятся в [checkpoint](CHECKPOINT_US_BASE_CATALOG.md).
Исходный [checkpoint03](CHECKPOINT_US_BASE_CATALOG_03.md) сохранён отдельно.

## Допуск к поиску и новые данные

`US_BASE_2000` и функция `us_catalog_ready` сохранены. Совпадение исходного SHA-256
функции проверено до и после публикации. Исходные 146 strict-записей не превратились
в 366 от изменения допуска. До импорта все семь старых HTTP-запросов дали прежний
результат побайтно по сохранённому разрешённому набору каталожных полей.

В обычном интерфейсе используется `US_CONFIRMED_2000`: технически подтверждённая
карточка допускается без неизвестного необязательного поля. При требовании мест,
бюджета, клиренса и других жёстких условий UNKNOWN попадает только в отдельную группу
уточнения и не получает первое предложение. «Не знаю» и «Неважно» сохранены.
Исследовательские, исключённые, не-US версии и Skoda не получили автоматический допуск.

| Контрольный запрос | Batch03 strict | Только коррекция допуска, strict | Только коррекция допуска, ordinary | Batch04 strict | Batch04 ordinary |
|---|---:|---:|---:|---:|---:|
| C300 MY2015 без мест | 0 | 0 | 2 | 0 | 2 |
| C300 MY2015 минимум 7 мест | 0 | 0 | 0 | 0 | 0 |
| Без марки: sedan, gasoline, AT | 38 | 38 | 126 | 86 | 146 |
| Бюджет 20 000 AZN, цены неизвестны | 0 | 0 | 0 | 0 | 0 |
| Минимум 7 мест | 29 | 29 | 29 | 29 | 29 |
| Рынок CA | 0 | 0 | 0 | 0 | 0 |
| Skoda | 0 | 0 | 0 | 0 | 0 |

Числа в таблице — `matched_versions`, не размер текущей страницы. Сохранённые
`match_ids`/`uncertain_ids` ограничены размером страницы 100 и не используются как
полное количество каталога. JSON до, после коррекции допуска и после данных:
[before](../deliverables/VerifiedData/us-base-catalog-04/search-before.json),
[admission-only](../deliverables/VerifiedData/us-base-catalog-04/search-admission-only.json),
[after](../deliverables/VerifiedData/us-base-catalog-04/search-after.json).

## Выполненные проверки

- `pytest backend/tests -q`: **342 PASS**, 104.20 s первоначально и **342 PASS**, 47.70 s
  после корректирующей публикации; два предупреждения о deprecated
  API FastAPI/Starlette test client. Это запуск batch04, не перенесённые 340 из batch03.
- `ruff check backend scripts`: PASS; `node --check` двух изменённых JS-модулей: PASS.
- [Live HTTP](../deliverables/VerifiedData/us-base-catalog-04/live-http.json): **47 PASS**,
  AZ/RU, facets, поиск без марки, семь мест, сравнение, профили и все 17 приоритетных марок.
- [Матрица batch](../deliverables/VerifiedData/us-base-catalog-04/resolver-matrix.json):
  191 доступная цель resolver и 1 документированное исключение; по каждой из 13 семейных областей фильтры AZ/RU,
  строгая выдача и отрицательный запрос несуществующего двигателя.
- [Обычный resolver](../deliverables/VerifiedData/us-base-catalog-04/ordinary-resolver-matrix.json):
  весь накопительный базовый US-каталог; отдельно запрещённые сочетания K5 2.5 AWD MY2023,
  Elantra 1.6 MANUAL MY2023, Camry 2.4 AT MY2010, Sonata 2.0 AT MY2011
  и Sonata 2.4 MANUAL MY2013.
  Отрицательный результат означает отсутствие подтверждённой связи в текущем каталоге,
  а не универсальное утверждение о существовании автомобиля вне этой области evidence.
- Профили всех 412 базовых записей проверены на одинаковые ключи фактов и source URLs
  в AZ/RU. Полные значения и provenance: [technical-fields.json](../deliverables/VerifiedData/us-base-catalog-04/technical-fields.json).
- **88 использованных raw documents** сверены по SHA-256, source registry, URL, рынку,
  марке/модели и покрытию подтверждённых модельных лет. Manufacturer-authored brochures
  из архивов не выдаются за официальные домены. Raw manuals/PDF не включаются в source ZIP.
- [Повторная публикация](../deliverables/VerifiedData/us-base-catalog-04/idempotency.json):
  одинаковые SHA-256 каталога, число variants, generations, revisions, jobs и документов;
  новые записи/ревизии при повторе не создаются.
- [Сохранность](../deliverables/VerifiedData/us-base-catalog-04/preservation.json): PASS.
  Старые данные и история сохранены; нет удалений или изменений вне разрешённых областей.

## Визуальная проверка

Перед финальным checkpoint выпущена корректирующая ревизия
`us-base-catalog-04-correction-01`: 2013 Sonata 2.4 MANUAL исключена из подтверждённой
выдачи, а диапазон механики у MY2011–2012 сужен до этих двух лет. У заводской US-брошюры
MY2013 есть внутреннее противоречие: общее рекламное описание PDF p11 упоминает manual,
но список GLS/SE/Limited на p16 и таблица расхода p18 перечисляют automatic.
Существование строки сертификации EPA не сняло конфликт розничной применимости.
[Первичный документ производителя](https://www.auto-brochures.com/makes/Hyundai/Sonata/Hyundai_US%20Sonata_2013.pdf).
Исходный manifest04 и ревизии не переписаны. Policy перечисляет применённое исправление;
checkpoint читает обе публикации и показывает исключённую строку в delta.
Для этого существующий publisher получил поддержку `catalog_key` при исключении
factory-записи: прежде механизм исключений принимал только EPA ID.
Это исправление данных, не ослабление или ужесточение правил пользовательского допуска.


Реальные изображения браузера и параметры viewport: [browser-qa](../deliverables/VerifiedData/us-base-catalog-04/browser-qa/README.md).
Проверены главная, фильтры, выдача без марки, профиль K5 MY2023, открытая техническая
подкатегория и карточка с неизвестными местами: AZ/RU, 360/390/430 px, обычный и увеличенный текст.

Сопоставление с `C:/Users/jalil/OneDrive/Desktop/approved_ui_reference.png`: сохранены
сине-белая композиция, три направления главной, пошаговый подбор, крупные карточки,
основная навигация. Четыре существующие цветные категории профиля сохранены.
Фотографии не подставлены из макета; текущие placeholders и иллюстрация главной
остаются отличием реализации от фотореференса. Полного пиксельного совпадения не заявляем.
Локальная панель тестирования существовала до batch04.

Обнаружены и исправлены два дефекта адаптации: у fact tiles оставалась фиксированная
двухколоночная раскладка старого `dl`; на крупном тексте категории профиля выходили
за пределы узкого экрана. В карточках label теперь над значением; крупные категории
на мобильной ширине идут одной колонкой. Размеры/цвета обычной композиции не переделаны.
В технических строках увеличенного режима теперь действительно увеличен текст.
Проверка относится к browser preview. APK не пересобирался; телефон не подключался.

## Локальная резервная копия и перенос

Копия до изменения данных:
`C:/Users/jalil/OneDrive/Desktop/AUTO_EXPERT/STAGE6_1/.backups/before-us-base-04-20260921T211842Z.sqlite3`.
Создана SQLite backup API, не копированием незакрытого файла.
SHA-256: `1581f2a905874c4c483315bdfa07be3e064631331c6868fc637bcb68adcb98af`.
Восстановление в отдельную SQLite in-memory БД проверяет integrity/foreign keys,
не откатывая рабочий каталог. NTFS ACL копии ограничен текущим Windows-пользователем,
SYSTEM и Administrators; наследование отключено. Копия **не зашифрована**;
параметры синхронизации OneDrive этим заданием не менялись и не проверялись.

При реальном восстановлении сначала остановить backend/worker, сохранить отдельную
копию текущей БД, проверить путь SQLite из существующей локальной конфигурации,
затем восстановить указанную копию через SQLite backup API в отключённую целевую БД.
Проверить integrity/foreign keys перед запуском. Не заменять работающую БД простым
копированием поверх WAL-файлов. Такой rollback в этом пакете не выполнялся.

Source/deployment ZIP — исходники, manifest и документация, **не резервная копия БД**.
Он исключает `.env`, ключи, private raw cache, живую БД, account/session metadata.
В новой среде нужно повторить разрешённое acquisition, сопоставить RawDocument IDs,
создать собственные review/revision IDs и опубликовать данные существующим pipeline.
Локальные prepared IDs нельзя переносить в чужую БД без mapping. Исходные документы
потребуют локального получения; доступность всех внешних URL в будущем не гарантируется.
Для крупных разрешённых manuals использован существующий процессный import limit 64 MiB;
конфигурация API/.env не менялась.

При воспроизведении публикаций соблюдать порядок: исходный manifest batch04, затем
`data/manifests/us-base-catalog-04-correction-01.json`. Этот correction входит в batch04,
не является новым этапом или расширением каталога. Не восстанавливать промежуточное
состояние с Sonata MY2013 MANUAL как подтверждённой конфигурацией.

Команды локального повторного аудита (настроенное окружение проекта):

```powershell
python scripts/checkpoint_base_catalog.py --manifest data/manifests/us-base-catalog-batch-04.json --baseline deliverables/VerifiedData/us-base-04-baseline.json --previous-coverage deliverables/VerifiedData/us-base-catalog-03/coverage.json
python scripts/report_us_base_04.py
python scripts/smoke_us_catalog.py
python -m pytest backend/tests -q
python scripts/package_verified_data.py
```

Платных API/LLM/image-generation вызовов: **0**. Hetzner, телефон, ownership-cost,
изображения и глубокие dossier остаются отложенными. Архитектура и стек сохранены.
