# Карта хранения: техническая база США (Toyota, MY2014–2026)

Дата: 2026-10-02. Статус: **ПРОЕКТ, ждёт подтверждения владельца**. В БД ничего не записано.
Основание: чтение кода (`backend/app/models/*`, `services/knowledge_import.py`, `services/commercial_fact_overlay.py`, `services/catalog_buyer.py`, `schemas/knowledge.py`, `schemas/catalog_verification.py`) и read-only запросы к `autoexpert.db` (Alembic `f086_listing_intake`).

## 1. Как устроена схема сейчас

### Конфигурации
- **Одна строка на модельный год.** У строки `vehicle_variants` `year_from` равен `year_to`.
- **Карточка конфигурации** лежит в `vehicle_variants.specifications["catalog"]`, а факты — в её словаре `facts`. Каждый факт — скаляр с полями `value`, `unit`, `status`, `locator` и `documentary_source`.
- **Каждому факту соответствует строка** в `technical_evidence` с `conditions.fact`.

### Путь записи
Запись идёт только через импорт: `ImportJob` → staging `CatalogRevision` → review → `publish_job` → `apply_revision` (`knowledge_import.py:606`).

`apply_revision` при повторной публикации **заменяет весь словарь `facts`**. Поэтому старые факты переносятся в новую ревизию дословно, иначе они пропадут.

### Что видит приложение
Профиль (`catalog_buyer.vehicle_profile`, строки 1054–1384) читает только `catalog.facts`. Ключи для масел, жидкостей, шин, тормозов, подвески, момента, бака и массы в UI уже предусмотрены.

Production-показ определяется двумя правилами из `commercial_fact_overlay.py`:
- **Права.** Показывается только факт с `COMMERCIAL_OK`, а его `fact_name` должен входить в `CLAIM_FIELDS`. Масла, жидкости, шины, тормоза, подвеска, момент и бак в этот список **не входят**.
- **Источник.** Для `factory-toyota-us` с официального домена `toyota.com` уже есть правило `FACTUAL_EXTRACTION` / `OFFICIAL_PUBLISHER`.

### Чего в схеме нет
- **Уровня поколения и семейства двигателя.** `technical_evidence` и `known_issues` всегда привязаны к одной конфигурации года: колонка `vehicle_variant_id` обязательна (NOT NULL).
- **Структурированного ТО** (отдельная запись на каждую работу, интервал в км/мес).
- **Таблицы recalls.** Recall сейчас хранится как строка `technical_evidence` с `conditions.campaign_number`.

### Что безопасно
Все существующие читатели `technical_evidence` и `known_issues` фильтруют по `vehicle_variant_id` (`providers/database.py:24`, `api/routes/vin.py:760`, `research_pipeline.py:673`). Строки без привязки к конфигурации им не видны, поэтому старый код их не затронет.

### Тесты
Тесты работают на БД в памяти (`conftest.py:35`). Живую БД не читает ни один тест. Файлы из `data/manifests` читает только `test_catalog_active_scope.py`. Новые данные существующие тесты не сломают.

## 2. Карта: 15 полей промта → куда пишутся

Обозначения:
- **TE** — `technical_evidence` с новыми колонками области применения (миграция f087, раздел 3).
- **Каталог** — `vehicle_variants.specifications.catalog.facts`, т.е. то, что читает UI.

| № | Поле | Уровень | Куда пишется | Колонки / ключи | Чего не хватает |
|---|---|---|---|---|---|
| 1 | Идентификация: поколение, годы, кузов, места | поколение / конфигурация | `vehicle_generations` (`name`, `code`, `start_year`, `end_year`); `vehicle_variants` (`market`, `body`); Каталог `body`, `seats` | Есть | У Camry VII/VIII пусто `start_year`/`end_year` — заполнить. Нет поколения 2025+ — добавить «IX». Код кузова (XV50/70/80) хранить как факт TE `chassis_code`, только если он есть в источнике |
| 2 | Двигатель: код, объём, цилиндры, наддув, впрыск | семейство двигателя + конфигурация | TE `scope_level=ENGINE` (`engine_code`): `engine_displacement`, `cylinders`, `aspiration`, `injection`, `compression_ratio`. `vehicle_variants.engine_code`, `engine`. Каталог `engine_code`, `engine_description`, `injection` | Колонки в `vehicle_variants` есть | Уровень ENGINE в TE — миграция |
| 3 | Коробка: тип, передачи, обозначение | конфигурация | `vehicle_variants.transmission`, `transmission_code`; Каталог `transmission_description`, `transmission_family`, `gears`, `transmission_code` | Есть | — |
| 4 | Привод | конфигурация | `vehicle_variants.drivetrain`; Каталог `drivetrain` | Есть | — |
| 5 | Мощность и момент (по годам) | конфигурация | `vehicle_variants.power_kw`; Каталог `power_hp`, `power_kw`, `torque_nm`, `torque_lb_ft` | Есть | В production — только после расширения `CLAIM_FIELDS` (код) |
| 6 | Топливо, октановое число, расход, бак | конфигурация / поколение | Каталог `fuel`, `fuel_grade`, `octane_aki`, `octane_ron`, `fuel_combined` (L/100km), `epa_*_mpg`, `fuel_tank_l`; `vehicle_variants.official_fuel_*` | Есть | Бак на уровне поколения — TE GENERATION |
| 7 | Масло двигателя: вязкость, стандарт, допуск, объём с фильтром | семейство двигателя | TE ENGINE: `engine_oil_viscosity`, `engine_oil_specification`, `engine_oil_oem_approval` (у Toyota обычно NULL), `engine_oil_capacity_l` | Ключи в UI есть | Уровень ENGINE — миграция. Подпись для `engine_oil_oem_approval` в UI — код |
| 8 | Прочие жидкости и ёмкости | поколение / коробка | TE GENERATION/TRANSMISSION: `coolant`, `coolant_capacity_l`, `brake_fluid`, `transmission_fluid`, `transmission_fluid_capacity_l`, `transfer_fluid`, `front_differential_fluid`, `rear_differential_fluid`, `hybrid_*` | Типы жидкостей в UI есть | Подписи UI для ёмкостей (`*_capacity_l`) — код. Если в руководстве «обратитесь к дилеру» — NULL с причиной |
| 9 | ТО: каждая работа — отдельная запись | поколение (+ двигатель, + условия) | **Новая таблица `maintenance_schedule_items`** | — | Миграция (раздел 3) |
| 10 | Шины, давление | пакет колёс / конфигурация | TE GENERATION с `applicability.trim`: `tires`, `wheels`, `tire_pressure_front_kpa`, `tire_pressure_rear_kpa`; Каталог `tires`, `wheels` | Ключи шин в UI есть | Подпись давления в UI — код |
| 11 | Размеры: длина, база, клиренс, багажник, масса | поколение | TE GENERATION: `length_mm`, `width_mm`, `height_mm`, `wheelbase_mm`, `track_front_mm`, `track_rear_mm`, `ground_clearance` (мм), `cargo_l`, `curb_weight_kg`; `vehicle_variants.ground_clearance_mm` | Ключи в UI есть, кроме `curb_weight_kg` | Подпись UI для `curb_weight_kg` — код |
| 12 | Подвеска, тормоза, рулевое | поколение | TE GENERATION: `front_suspension`, `rear_suspension`, `front_brakes`, `rear_brakes`, `steering` | Есть, кроме `steering` | Подпись UI для `steering` — код |
| 13 | Recalls NHTSA | поколение + годы + применимость | TE `category=SAFETY`, `fact_key=nhtsa_recall`, `conditions`: `campaign_number`, `component`, `summary`, `consequence`, `remedy`, `report_received_date` — существующий шаблон `dossier_synthesis`/`paid_report` | Есть | Уровень GENERATION — миграция. Показ в профиле требует RU/AZ `documentary_sections` — отдельный шаг |
| 14 | Известные проблемы | двигатель / коробка / поколение + годы | `known_issues`: `component`, `description`, `symptoms`, `consequences`, `severity` (LOW/MEDIUM/HIGH), `confidence`, `inspection_recommendation`, `evidence_ids` (ссылки на TE recall/TSB/паттерны жалоб), `source_count`, `status` | Есть | Новые колонки: область применения, `cause`, `typical_fix`, `probability`, `display_level`. `vehicle_variant_id` → nullable |
| 15 | Источник у каждого факта | у факта | `source_records` (`title`, `publisher`, `url`, `source_type`, `source_tier`, `market`, `retrieved_at`, `confidence`) + `raw_documents` (sha256 скачанного файла) + `knowledge_sources` (реестр). TE.`source_id` → `source_records` | Есть | В TE нужны `raw_document_id`, `locator` (страница) — миграция |

### Уровни достоверности промта → существующие словари
| Промт | `source_records.source_tier` | `confidence` | `status` (EvidenceStatus) | новое поле `display_level` |
|---|---|---|---|---|
| OFFICIAL_SOURCE (домен toyota.com, NHTSA, EPA) или два независимых источника совпали | A (или B + B) | HIGH | CONFIRMED | `FACT` |
| один вторичный источник | B | MEDIUM | CONFIRMED | `SECONDARY_NOTE` («по данным справочников») |
| только отзывы владельцев | C | LOW | ESTIMATE | `OWNER_REPORTS` («владельцы сообщают…») |
| источники противоречат друг другу | значения хранятся отдельными строками | — | — | `HIDDEN_CONFLICT` + запись в журнал конфликтов |

## 3. План миграции `f087_us_tech_scoped_facts`

Все новые колонки nullable. Существующие 273 086 строк TE и 2 строки `known_issues` не меняются. Downgrade — удаление добавленного.

1. **`technical_evidence`** — новые колонки:
   - `scope_level` (CONFIGURATION / GENERATION / ENGINE / TRANSMISSION);
   - `make_id` FK → `vehicle_makes`, `generation_id` FK → `vehicle_generations`;
   - `engine_code`, `transmission_code`;
   - `year_from`, `year_to`;
   - `fact_key`, `value` (JSON-скаляр), `unit`;
   - `raw_document_id` FK → `raw_documents`, `locator`;
   - `display_level`.

   Колонка `vehicle_variant_id` становится nullable. Исходные значение и единица, а также применимость (кузов, комплектация, HEV) кладутся в существующую колонку `conditions`. Индексы: (`scope_level`, `generation_id`), (`make_id`, `engine_code`), `fact_key`.
2. **`known_issues`** — новые колонки: `scope_level`, `make_id`, `generation_id`, `engine_code`, `transmission_code`, `year_from`, `year_to`, `market`, `title`, `cause`, `typical_fix`, `probability` (COMMON / OCCASIONAL / RARE), `display_level`. Колонка `vehicle_variant_id` становится nullable.
3. **Новая таблица `maintenance_schedule_items`**: `id`, временные метки, `market`, `make_id`, `generation_id`, `engine_code`, `transmission_code`, `year_from`, `year_to`, `applicability` (JSON), `schedule_system` (FIXED_INTERVAL / OIL_LIFE_MONITOR / MAINTENANCE_MINDER / CBS / SERVICE_A_B), `job`, `action` (REPLACE / INSPECT / ROTATE), `condition` (NORMAL / SEVERE), `occurrence` (EVERY / FIRST / SUBSEQUENT), `interval_km`, `interval_months`, `interval_miles_original`, `rule` (WHICHEVER_FIRST), `max_interval_km`, `max_interval_months`, `source_id` FK, `raw_document_id` FK, `locator`, `confidence`, `status`, `display_level`, `notes`.

   **Альтернатива без новой таблицы:** строки TE с `category=MAINTENANCE` и интервалами в JSON. Минус: интервалы без типов, их неудобно использовать для напоминаний в «Гараже».
4. ORM-модели обновляются под новые колонки. Читающий код не меняется.

**Риск миграции:** на SQLite изменение nullable требует пересборки `technical_evidence` (273 тыс. строк). Перед миграцией делается свежий бэкап, миграция сначала прогоняется на копии.

## 4. Что уже есть по Toyota (read-only, `BASELINE.json`)

### Общие цифры
- **Марка Toyota:** 37 моделей, 49 поколений, 1 501 конфигурация.
- **Документы:** 50 файлов в `raw_documents` от `factory-toyota-us` (брошюры).
- **Видимо в приложении:** Camry 28, Corolla 29, RAV4 13, Highlander 38, Prius 3 — всего 111 из 644. Только годы ≤2021.

### По линейкам
| Линейка | Конфигураций US 2014–2026 | Поколения в БД | Есть | Нет |
|---|---|---|---|---|
| Camry | 72 | VII (2012–17, заводские строки), VIII (2018–20), UNRESOLVED (84 EPA + 15 CA), DEMO XV70 | ядро: двигатель / коробка / привод; у части — размеры в дюймах, подвеска, тормоза, бак; 6 recalls (2019); 819 COMMERCIAL_OK | масла, жидкости, ТО, шины, клиренс, мощность/момент у большинства; заводских строк 2021–2026 нет; known_issues только DEMO |
| Corolla | 113 | XI (2014–19), XII (2020–21), UNRESOLVED | ядро, мощность/момент у 57, 9 recalls | то же, заводских строк 2022+ нет |
| RAV4 | 96 | IV (2013–15), V (2019–21), UNRESOLVED | ядро, мощность/момент у 31 | 2016–2018 и 2022+ без заводских строк, recalls 0 |
| Highlander | 127 | III (2014–16), IV (2020–21), UNRESOLVED | ядро, размеры у 30 | 2017–2019 и 2022+ без заводских строк, recalls 0 |
| Prius | 39 | ZVW30 (2013–15), UNRESOLVED | ядро; у 9 строк — подвеска, тормоза, шины, клиренс, масса | XW50 / XW60 без заводских строк |

Связанные модели есть в БД отдельно: Prius Prime, Prius c, Prius v, RAV4 Prime, Corolla Cross, Grand Highlander. Корректности ради: это отдельные модели, список линеек не расширяется.

## 5. Решения владельца перед записью
1. Утвердить миграцию f087 (раздел 3), включая новую таблицу ТО.
2. Новые заводские конфигурации Toyota на 2021–2026 (для 2014–2020 они уже есть): только исследовательский слой, или ещё и COMMERCIAL_OK claims по существующему правилу для официальных документов toyota.com? Второе увеличит число видимых в приложении конфигураций выше 644.
3. Показ новых полей (масла, жидкости, ТО, размеры) в приложении — отдельная задача в коде (`CLAIM_FIELDS` и подписи в UI). В эту фазу не входит.
4. Поколения: оставить существующие коды VII/VIII, заполнить у них годы, добавить IX (2025+). Коды XV50/XV70/XV80 — только как факт с источником.
