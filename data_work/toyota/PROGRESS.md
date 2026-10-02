# Toyota (рынок США, MY2014–2026): прогресс

Обновлено: 2026-10-02. Параметры запуска: МАРКА=Toyota, ЛИНЕЙКИ=все (Camry, Corolla, RAV4, Highlander, Prius), ГОДЫ=2014–2026, ОСТАНОВКА=после первой линейки, VDB=нет.

## Сделано
- [x] Шаг 0:
  - git init и базовый коммит (`0ff74ff`);
  - бэкап БД;
  - baseline тестов: backend 531, Flutter 34, веб 3;
  - схема и счётчики «до» (`BASELINE.json`, `SCHEMA_MAP.md`).
- [x] Миграция f087 (`62024c8`): репетиция на копии, применение, тесты.
- [x] Этап марки:
  - полный обход mycarusermanual.com (Camry/Highlander: `not_on_site`; Corolla/RAV4/Prius: 574 страницы, все издания US);
  - руководства Camry 2014–2023 и Camry Hybrid 2022–2023 скачаны с carmans.net.
- [x] **Camry**: staging собран и проверен, загружен в БД, выборочная перепроверка 10%, тесты зелёные, коммит `4a6e5d5`.

## Дальше по порядку (Приложение A)
- [ ] Corolla
- [ ] RAV4
- [ ] Highlander
- [ ] Prius

## Как продолжить линейку
1. Источники:
   - `scripts/fetch_us_tech_sources.py` (vpic-canada, recalls, complaints, carmans, pages, url);
   - pressroom: `pages Toyota pressroom 10 <url>`;
   - спецификации: `url <dest> <pdf> <страница-источник>`.
2. Подготовка текста:
   - `uv run --no-project --with pypdfium2 python scripts/extract_manual_specs.py toyota`;
   - `uv run --no-project --with pypdfium2 python scripts/pdf_page_cache.py toyota`.
3. Факты вручную, с дословными цитатами: `data_work/toyota/staging/<line>/authored_gen_*.json` и `authored_issues.json`. Проверка цитат по документам: `scripts/build_us_tech_staging.py probe toyota <line> <quotes.json> "<regex ключей>"`.
4. Сборка и проверка: `.venv/Scripts/python.exe scripts/build_us_tech_staging.py toyota <line>`. Результат должен быть `errors: 0`.
5. Загрузка: сначала на копии БД, затем бэкап и рабочая БД. Команда: `.venv/Scripts/python.exe scripts/load_us_tech_facts.py toyota <line> --db <путь> --prune-stale`.
6. Тесты (backend, Flutter, веб), перепроверка 10%, коммит `data(toyota-us): <line> — ...`, обновить этот файл.

## Важно знать
- Официальные PDF Toyota (`assets.sipb.toyota.com`: руководства и Warranty & Maintenance Guide) **заблокированы для Азербайджана** на CloudFront. Обход не применялся.
- Доступны: pressroom.toyota.com (с `Crawl-delay: 10`), спецификации Product Information (с Referer страницы pressroom), support.toyota.com.
- Скрипты на Python должны использовать `verify=ssl.create_default_context()` (системные корневые сертификаты).
- Alembic запускать только с абсолютным `AUTOEXPERT_DATABASE_URL`.
