# Auto Expert — закрытый staging на сервере (Hetzner CX23)

Полный отчёт: `data_work/deploy/REPORT.md`. Здесь — как устроено и команды.

## Устройство

Сервер общий с проектом **Stories** (Telegram Mini App, `/opt/stories`): его Caddy держит 80/443, выдаёт HTTPS
и пересылает `autoexpert.77-42-27-222.sslip.io` на край Auto Expert (`172.17.0.1:8088`, снаружи недоступен).
Блок добавлен скриптом `deploy/server/stories_caddy_link.sh` (откат: `--undo`). Docker на сервере не
перезапускать: это перезапустит и Stories.

```
Интернет :443 ──> stories-caddy (HTTPS) ──> 172.17.0.1:8088 ──> caddy Auto Expert (Basic Auth, noindex)
                       ├─ /api/*     ──> backend  (FastAPI, 2 процесса, read-only контейнер)
                       ├─ /preview/* ──> web      (nginx: веб-приложение apps/web_preview)
                       ├─ /app/*     ──> web      (nginx: Flutter web)
                       ├─ /cars/*    ──> site     (nginx: публичные страницы, собраны на ноутбуке)
                       └─ /          ──> 302 /preview/
backend ──> postgres (PostgreSQL 16, порт наружу не открыт; deploy/postgres/postgresql.conf под 4 ГБ)
migrate — разовый контейнер: alembic upgrade head перед стартом backend
```

Папки на сервере:

| Путь | Что |
|---|---|
| `/srv/autoexpert/releases/<время>-<коммит>/` | выпуски (код, deploy/, web/, site/); хранятся 5 последних |
| `/srv/autoexpert/current` | ссылка на работающий выпуск |
| `/srv/autoexpert/shared/.env` | секреты (chmod 600, не в git) |
| `/srv/autoexpert/vpic/vpic_lite.sqlite` | локальная база NHTSA vPIC (только чтение) |
| `/srv/autoexpert/media/` | фото клуба и данные знаний |
| `/srv/autoexpert/backups/` | ежесуточные дампы (7 последних) |
| `/srv/autoexpert/logs/` | health.log, backup.log, recalls.log (ротация еженедельно) |

Задачи по расписанию (systemd timers): `autoexpert-backup` 03:30 UTC, `autoexpert-health` каждые 5 минут,
`autoexpert-recalls` 06:00 UTC (новые кампании NHTSA по машинам в гаражах).

## Порядок первой установки
1. С ноутбука: `ssh root@77.42.27.222 'bash -s' < deploy/server/inspect.sh` — осмотр (ничего не меняет).
   (Выполнено 2026-10-06, результат — `data_work/deploy/server_inspection_before.txt`.)
2. Если чужих проектов нет: `scp -r deploy/server root@77.42.27.222:/root/autoexpert-server` и
   `ssh root@77.42.27.222 bash /root/autoexpert-server/bootstrap.sh`. Проверить вход `ssh deploy@77.42.27.222`
   в новом окне, не закрывая старое.
3. Секреты: `uv run --no-project --with bcrypt python deploy/make_secrets.py` (на ноутбуке, вне git) →
   `scp C:/AutoExpertData/secrets/staging.env deploy@77.42.27.222:/srv/autoexpert/shared/.env` → `chmod 600`.
4. vPIC: `scp C:/AutoExpertData/vpic/vpic_lite.sqlite deploy@77.42.27.222:/srv/autoexpert/vpic/`.
5. Выпуск: `deploy/release.sh` (код из закоммиченного HEAD, web, Flutter web, сайт из
   `C:/AutoExpertData/public_site_staging`).
6. База: `deploy/push_database.sh` (дамп локального PostgreSQL → восстановление → сверка строк).
7. `ssh root@77.42.27.222 bash /root/autoexpert-server/stories_caddy_link.sh` — HTTPS через Caddy Stories.
8. `sudo systemctl start autoexpert-backup.timer autoexpert-health.timer autoexpert-recalls.timer`.
9. Перезагрузка сервера и проверка, что всё поднялось само (выполнено: оба проекта поднялись).

## Команды «на всякий случай» (на сервере, пользователь deploy)

```bash
cd /srv/autoexpert/current/deploy
C="docker compose --env-file /srv/autoexpert/shared/.env"
$C ps                                  # состояние
$C logs -f --tail 200 backend          # логи (то же для caddy, postgres, web, site)
$C restart backend                     # перезапуск одного сервиса
$C up -d                               # поднять всё
sudo systemctl start autoexpert-backup # ручной бэкап сейчас
$C exec backend python scripts/manage_users.py list              # аккаунты
$C exec backend python scripts/manage_users.py verify EMAIL      # подтвердить почту (пока нет почтового провайдера)
$C exec backend python scripts/manage_users.py admin EMAIL       # права модератора
```

Откат на прошлый выпуск:
```bash
ls -1t /srv/autoexpert/releases                     # выпуски, новые сверху
ln -sfn /srv/autoexpert/releases/<прошлый> /srv/autoexpert/current
cd /srv/autoexpert/current/deploy && RELEASE=<прошлый> docker compose --env-file /srv/autoexpert/shared/.env up -d
```
Миграции базы вперёд необратимы без бэкапа: перед выпуском с новой миграцией — ручной бэкап.

Восстановление базы из дампа:
```bash
$C stop backend caddy
$C exec -T postgres pg_restore -U autoexpert -d autoexpert --clean --if-exists --no-owner < /srv/autoexpert/backups/<файл>.dump
$C up -d
```

С ноутбука: `deploy/pull_backup.sh` — скачать последний дамп и проверить, что он восстанавливается.
