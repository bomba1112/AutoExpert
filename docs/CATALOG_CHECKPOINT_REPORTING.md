# Обязательный формат checkpoint каталога

Коррекция владельца от 2026-09-22. Каждый checkpoint начинается с двух полных таблиц:

1. **Delta from previous batch** — все добавленные/изменённые версии, включая
   повторную публикацию только с обновлённым evidence. Для них явно различать ADDED,
   CHANGED и EVIDENCE_REFRESH; нельзя считать повторную публикацию новым автомобилем.
2. **Cumulative strict-output catalog** — все версии по прежнему строгому критерию
   `US_BASE_2000` (включая подтверждённые места). Брать из `buyer.active_us_rows(buyer.records(db))`, с теми же
   source/rights, publication, market и readiness gates, что применяет приложение.
3. Начиная с batch04: **Cumulative conditional-output catalog** — базовые версии
   из `active_us_base_rows`, не вошедшие в strict. Обычная выдача использует
   `US_CONFIRMED_2000`: неизвестные места допускаются только без ограничения мест;
   неизвестное значение любого жёсткого условия не считается соответствием.
   Полные технические разделы, источники, план против факта и остаток приводятся отдельно.

Обязательные столбцы в каждой таблице:

`Make | Model | Generation | USA market | Model years | Engine | Transmission | Drivetrain | Configuration count | Status`

Дополнительные Body и Seats разделяют кузова и варианты 5/7 мест. Показывать только
фактически готовые годы и связки, а не весь паспортный диапазон поколения. Непоследовательные
годы не объединять сплошным диапазоном. AVAILABLE_SCOPED/STRICT_SCOPED действует только на
указанную строку; общего READY для частично покрытой модели недостаточно.

**Aggregate totals размещаются только после полных таблиц.** Ссылка на отдельный список
не заменяет таблицу в самом checkpoint. Полные машинные списки и catalog_key нужны
для сверки, но не заменяют читаемую таблицу.

Генератор `scripts/checkpoint_base_catalog.py` всегда пишет `catalog-tables.md` и
`catalog-tables.json` в каталог текущего batch. Для обновления главного checkpoint:

```powershell
python scripts/checkpoint_base_catalog.py --manifest data/manifests/us-base-catalog-batch-03.json --baseline deliverables/VerifiedData/us-base-03-baseline.json --previous-coverage deliverables/VerifiedData/us-base-catalog-02/coverage.json --checkpoint docs/CHECKPOINT_US_BASE_CATALOG.md
```

В следующем batch указать его manifest, снимок БД перед этим batch и предыдущий coverage.
Базовый снимок читается только для таблицы vehicle_variants; user/account/session metadata
не экспортируется. Снимок должен соответствовать предыдущей публикации, иначе delta некорректна.
Каталожные изменения не публикуются самим отчётом.

Обязательные проверки генератора: каждый batch target входит в delta ровно один раз;
каждая доступная strict запись входит в cumulative ровно один раз; суммы совпадают
с coverage. Configuration count — число опубликованных годовых записей, не объявлений.
Объединение одинаково описанных строк сохраняет все исходные catalog_key, годы и
годовые количества в JSON. Повторный рендер обновляет один блок, не дублирует таблицы.

Исторические checkpoint не считаются текущими и не должны переписываться новым составом БД.
