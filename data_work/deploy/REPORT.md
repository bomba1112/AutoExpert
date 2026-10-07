# PostgreSQL и выкладка на Hetzner — итоговый отчёт

Дата: 2026-10-06.

**Итог:** проект переведён на PostgreSQL и выложен как **закрытый staging** на сервер `ubuntu-4gb-hel1-1` (77.42.27.222).
- Сервер общий с проектом владельца **Stories**. Оба проекта работают, перезагрузку пережили.
- Staging открыт по **HTTPS**: `https://autoexpert.77-42-27-222.sslip.io/` — за паролем и с запретом индексации.

Решения владельца в ходе работы:
- вход через Caddy проекта Stories на имени sslip.io;
- SSH только по ключам;
- перезагрузка с исправлением автозапуска базы Stories.

---

## 1. Перенос на PostgreSQL

**Локальный PostgreSQL 16.14** — отдельный кластер, только localhost, порт 5433: `C:\AutoExpertData\pg16`. Ваш установленный PostgreSQL (служба `postgresql-x64-16`) не тронут.

**Что пришлось исправить, чтобы код работал и на SQLite, и на PostgreSQL:**
| Где | Что было | Как стало |
|---|---|---|
| миграция `c318d45aa731` | `WHERE is_demo = 1` (boolean нельзя сравнить с числом) | `= TRUE` |
| комнаты клуба | GROUP BY не по всем колонкам | полный GROUP BY |
| загрузчик US-базы | `json_extract` (функция SQLite) | переносимые JSON-операторы SQLAlchemy |
| кэши карточек | адрес базы из `engine.url` | общий помощник `bind_url` |
| **карточка конфигурации** | из одинаковых строк бралась «первая» в порядке, который база не гарантирует; в PostgreSQL источник пункта ТО отличался в 13 из 25 карточек | явный порядок вставки: SQLite — `rowid`, PostgreSQL — `row_order` (миграция **f095**, только PostgreSQL; при переносе заполняется из `rowid`) |
| тест удаления машины (сделан другой сессией в `99ee691`) | `pragma foreign_key_check` | проверка только на SQLite; PostgreSQL сам держит внешние ключи |

**Сверка** — `scripts/sqlite_to_postgres.py`, рабочая SQLite только на чтение и **не изменялась**:
- **78 таблиц, 683 559 строк — число строк совпало в каждой;**
- **хэши содержимого совпали** в 19 ключевых таблицах (technical_evidence, known_issues, maintenance_schedule_items, content_translations, users, все garage_* и club_*);
- 60 карточек конфигураций × 2 языка, собранные из SQLite и PostgreSQL, — 0 различий; ответы API совпадают;
- перед выкладкой сверка повторена — SQLite не менялась;
- **на сервере** карточки Camry 2020, Civic 2020 и Q5 2021 из API совпали с локальными полностью.

**Тесты:**
- backend: **658/658 на PostgreSQL** (переменная `AUTOEXPERT_TEST_DATABASE_URL`, каждый тест в откатываемой транзакции) и **658/658 на SQLite**;
- web 19/19, Flutter 46/46 — эти тесты от базы не зависят.

**Скорость и настройки:**
- PostgreSQL собирает карточки в 5,3 раза быстрее; публичный сайт — **9–10 минут вместо 102**;
- настройки под 4 ГБ в `deploy/postgres/postgresql.conf`: shared_buffers 768 МБ, work_mem 8 МБ, max_connections 40.

## 2. Что было на сервере до установки
Полный вывод — `data_work/deploy/server_inspection_before.txt`.
- **Система:** Ubuntu 26.04 LTS, ядро 7.0, работал 73 дня без перезагрузки; 3,7 ГБ памяти, swap не было; диск 38 ГБ, занято 25%.
- **Docker** 29.6.2 и Compose 5.3.1 уже были установлены.
- **Проект владельца Stories** (Telegram Mini App, `/opt/stories`, git-клон) — `stories-caddy` (держит 80/443, HTTPS для `stories.77-42-27-222.sslip.io`), `stories-backend`, `stories-postgres`. Также остановленный контейнер `story-app`.
- **Защита:**
  - вход root по паролю был разрешён;
  - firewall выключен;
  - fail2ban отсутствовал;
  - автоматические обновления работали.
- **Найдено:** у `stories-postgres` политика перезапуска `no`. После любой перезагрузки сервера база Stories не поднималась бы сама.

## 3. Что установлено и как устроено
Подробно — `deploy/README.md`.

**Изменения на сервере** (перед изменением системных настроек их архив сохранён в `/root/autoexpert-preinstall-*.tar.gz`):
- пользователь `deploy`: вход по ключу, группа docker, sudo только для служб Auto Expert и перезагрузки;
- SSH: **пароли выключены**, root — только по ключу (проверено: вход по паролю отклоняется);
- firewall ufw: входящие 22, 80, 443, плюс 8088 только с Docker-сетей на адресе 172.17.0.1;
- fail2ban для SSH; автоматические обновления безопасности; **swap 2 ГБ**;
- Docker **не перезапускался**, его общие настройки не менялись — чтобы не задеть Stories.

**Изменения в проекте Stories** (по решению владельца):
1. В `/opt/stories/deploy/production/Caddyfile` добавлен блок `autoexpert.77-42-27-222.sslip.io → 172.17.0.1:8088`. Caddy перезагружен без простоя, Stories отвечал 200 до и после.
   - Копия прежнего файла: `Caddyfile.bak-autoexpert-20261006T091126Z` рядом с ним.
   - Откат: `bash /root/autoexpert-server/stories_caddy_link.sh --undo`.
   - В git Stories эти два файла видны как изменённый и новый.
2. `docker update --restart unless-stopped stories-postgres-1` — настройка только самого контейнера. **При следующей выкладке Stories её compose-файл вернёт `restart: no`.** Чтобы исправить навсегда, в `docker-compose.production.yml` Stories у сервиса postgres нужен `restart: unless-stopped`.

**Auto Expert** (`/srv/autoexpert`, Docker Compose, проект `autoexpert`):
- **Сервисы:**
  - `postgres` 16 — порт наружу не открыт;
  - `migrate` — `alembic upgrade head`;
  - `backend` — FastAPI, 2 процесса, контейнер только для чтения, без root-прав;
  - `web` — веб-приложение `/preview`, Flutter web `/app`;
  - `site` — 1 581 публичная страница `/cars`;
  - `caddy` — пароль, `noindex`, CSP; слушает только `172.17.0.1:8088`.
- **Режим staging:**
  - backend в режиме `production`: обязательный секретный ключ, без инструментов разработчика, без демо-сессий, демо-засев выключен;
  - флаги включены явно: `show_us_tech_facts`, `garage_v1`, `ai_mechanic_v1`, `owners_club_v1`, `public_car_pages`, `subscription_v1`;
  - оплата — заглушка: покупка отвечает «магазин не подключён», пробный период работает;
  - `robots.txt: Disallow /` и заголовок `X-Robots-Tag: noindex`.
- **Тяжёлое собрано на ноутбуке:** публичный сайт (из PostgreSQL, с адресом staging), Flutter web, база vPIC (144 МБ). На сервере собирается только образ backend из зависимостей с хэшами.
- **Выпуск:** код из закоммиченного HEAD архивом через scp (`gh` на ноутбуке не установлен). Хранятся 5 выпусков, откат — переключение ссылки.
  - Подключить GitHub позже: `winget install GitHub.cli` → `gh auth login` → создать приватный репозиторий → `git push`.
- **Данные на сервере:** перенесены дампом с ноутбука; **строки совпали во всех 79 таблицах** (683 560 вместе с `alembic_version`).
- **Расписание (systemd):**
  - `autoexpert-health` — каждые 5 минут;
  - `autoexpert-backup` — 03:30 UTC;
  - `autoexpert-recalls` — 06:00 UTC, проверка новых кампаний NHTSA по машинам в гаражах; пробный запуск прошёл.
- **Перезагрузка проверена:** через минуту после старта поднялись все 8 контейнеров обоих проектов, таймеры, swap, firewall и fail2ban. Stories 200, Auto Expert 401 (просит пароль).
- **Память после запуска:** занято 1,8 ГБ (Auto Expert около 1 ГБ, из них PostgreSQL 720 МБ; Stories около 120 МБ); доступно 2 ГБ плюс swap. Диск занят на 38%.

## 4. Как открыть staging
- **Адрес:** `https://autoexpert.77-42-27-222.sslip.io/`. sslip.io — бесплатное имя, которое указывает на IP сервера; с ним работает HTTPS (сертификат Let's Encrypt до января 2027). Так же устроен адрес Stories.
- **Логин и пароль Basic Auth** — только в файле `C:\AutoExpertData\secrets\STAGING_ACCESS.txt` на ноутбуке, вне git. В отчёте и чате их нет.
- **Внутри:**
  - `/preview/` — веб-приложение;
  - `/app/` — Flutter web;
  - `/cars/en/` — публичные страницы.
- **После входа:**
  - зарегистрироваться в приложении;
  - подтвердить почту и выдать права модератора на сервере (почтового провайдера пока нет): `$C exec backend python scripts/manage_users.py verify ВАШ_EMAIL` и `... admin ВАШ_EMAIL` (см. раздел 6).
- **HTTPS уже есть**, пароли идут зашифрованными. Но это закрытый staging: регистрацию посторонних людей не открывать до решения о публичном запуске.
- Если на ноутбуке браузер ругается на сертификат, это Avast проверяет HTTPS-трафик и подставляет свой сертификат. На сервере сертификат настоящий (Let's Encrypt).

## 5. Бэкапы
- **Ежесуточно в 03:30 UTC:**
  - `pg_dump` в сжатом формате, без остановки сервиса;
  - архив фото клуба;
  - контрольные суммы и число строк по таблицам;
  - хранятся 7 последних в `/srv/autoexpert/backups`;
  - первый бэкап сделан: 166 МБ.
- **Проверка восстановления выполнена:**
  - серверный дамп скачан на ноутбук (`deploy/pull_backup.sh`);
  - контрольные суммы сошлись;
  - восстановлен в отдельную базу;
  - **строки совпали во всех 79 таблицах.**
- **Копия вне сервера:** пока хранилища нет, это ноутбук — `C:\AutoExpertData\server_backups`, хранится 14 копий; скачивать `deploy/pull_backup.sh` вручную или по расписанию Windows. Как только появится Hetzner Storage Box или S3, в `/srv/autoexpert/shared/.env` задаётся `BACKUP_OFFSITE=storagebox|s3` с параметрами, и копия уходит автоматически после каждого бэкапа.
- **Наблюдение:**
  - каждые 5 минут проверяются прокси, здоровье backend, состояние 5 контейнеров и диск (больше 80% — предупреждение);
  - проблемы пишутся в `/srv/autoexpert/logs/health.log` и в журнал (`journalctl -t autoexpert`);
  - логи ротируются: контейнеры — 10 МБ × 5, файлы — еженедельно.
  - Уведомлений вам на телефон пока нет — нужен канал (почта или Telegram).
- **Рекомендую** включить в консоли Hetzner **Backups** (автоматические снимки сервера, +20% к цене) — страховка для обоих проектов.

## 6. Команды «на всякий случай»
На сервере от пользователя `deploy`: `ssh deploy@77.42.27.222`, затем `cd /srv/autoexpert/current/deploy; C="docker compose --env-file /srv/autoexpert/shared/.env"`.

| Что | Команда |
|---|---|
| состояние | `$C ps` |
| логи | `$C logs -f --tail 200 backend` (или caddy, postgres, web, site) |
| перезапуск | `$C restart backend` / всё: `$C up -d` |
| ручной бэкап | `sudo systemctl start autoexpert-backup.service` |
| скачать и проверить бэкап (ноутбук) | `deploy/pull_backup.sh` |
| новый выпуск (ноутбук) | `deploy/release.sh` |
| откат | `ln -sfn /srv/autoexpert/releases/<прошлый> /srv/autoexpert/current && cd /srv/autoexpert/current/deploy && RELEASE=<прошлый> $C up -d --force-recreate` |
| восстановление из дампа | `$C stop backend caddy && $C exec -T postgres pg_restore -U autoexpert -d autoexpert --clean --if-exists --no-owner < /srv/autoexpert/backups/<файл>.dump && $C up -d` |
| подтвердить почту / модератор | `$C exec backend python scripts/manage_users.py verify EMAIL` / `admin EMAIL` |
| убрать связь с Caddy Stories | `ssh root@77.42.27.222 bash /root/autoexpert-server/stories_caddy_link.sh --undo` |

**Не перезапускать Docker целиком** (`systemctl restart docker`): это перезапустит и Stories.

## 7. Что нужно от владельца
1. **Stories:** добавить `restart: unless-stopped` сервису postgres в `/opt/stories/docker-compose.production.yml`; сейчас исправлено только у работающего контейнера. Учесть, что при `git reset` или новой выкладке Stories блок Auto Expert в его Caddyfile может пропасть — тогда снова запустить `stories_caddy_link.sh`.
2. **Хранилище для бэкапов вне сервера:** Hetzner Storage Box BX11 (1 ТБ, около €4/мес, рядом с сервером) или S3-совместимое (Hetzner Object Storage, Backblaze B2). Нужны пользователь и хост Storage Box (ключ я создам) или ключи S3 — в `.env` на сервере, не в чат.
3. **Домен** — для публичного запуска (`deploy/DOMAIN.md`). Для staging сейчас достаточно sslip.io.
4. **Ключи:** Claude API, почтовый провайдер (подтверждение почты, восстановление пароля), push, магазины. Переменные — в `deploy/.env.example`; без ключей функции работают в безключевом режиме.
5. **Канал уведомлений** о проблемах сервера (почта или Telegram).
6. Включить **Hetzner Backups** (снимки сервера).
7. Пароль staging из `STAGING_ACCESS.txt` передать нужным людям защищённым способом.

## Коммиты
- `5c64ccb` feat(db): PostgreSQL support and SQLite→PostgreSQL transfer
- `28b7a5b`, `458b9c7` — набор для выкладки, CSP
- `3e97120` — общий сервер со Stories
- `549bd47`, `cd73de8` — правки шаблона доступа, таймеров и скриптов
- плюс исправление сравнения строк (CRLF) и этот отчёт
