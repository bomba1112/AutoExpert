# Этап E — когда появится домен (подготовлено, НЕ включено)

Пусть домен — `DOMAIN` (например `autoexpert.app`), staging — `staging.DOMAIN`.

## 1. DNS у регистратора
| Тип | Имя | Значение | TTL |
|---|---|---|---|
| A | `staging` (или `@` для корня) | `77.42.27.222` | 300 |
| AAAA | то же | IPv6 сервера из консоли Hetzner (если используется) | 300 |

Проверка: `nslookup staging.DOMAIN` отдаёт `77.42.27.222`.

## 2. HTTPS (Caddy сам получит сертификат Let's Encrypt)
В `/srv/autoexpert/shared/.env`:
```
SITE_ADDRESS='staging.DOMAIN'
AUTOEXPERT_CORS_ORIGINS='["https://staging.DOMAIN"]'
AUTOEXPERT_PUBLIC_APP_URL='https://staging.DOMAIN/preview/'
AUTOEXPERT_PUBLIC_SITE_BASE_URL='https://staging.DOMAIN'
```
затем `docker compose --env-file /srv/autoexpert/shared/.env up -d caddy backend`. Порт 80 остаётся открытым
(перенаправление на HTTPS и выдача сертификата). Basic Auth остаётся, пока staging закрыт.

## 3. Публичный сайт с адресами домена (на ноутбуке)
```
python scripts/build_public_pages.py --out C:/AutoExpertData/public_site_staging --base https://staging.DOMAIN --app https://staging.DOMAIN/preview/
deploy/release.sh
```
(на PostgreSQL ~10 минут). При публичном запуске — убрать `Disallow` из robots.txt и заголовок noindex.

## 4. Ссылки в письмах
Берутся из `AUTOEXPERT_PUBLIC_APP_URL` (п. 2) — после подключения почтового провайдера.

## 5. Flutter
Flutter web собран с относительным адресом API (`/api/v1`) — пересборка не нужна. Мобильные сборки:
`flutter build apk --dart-define=API_BASE_URL=https://staging.DOMAIN/api/v1`.

## 6. Регистрация реальных людей
Только после HTTPS (п. 2) и решения о публичном запуске.
