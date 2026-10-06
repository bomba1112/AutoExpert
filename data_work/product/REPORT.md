# Продуктовый этап — итоговый отчёт (этапы 0–6)

Дата: 2026-10-04. Ветка `feature/cn-catalog`. Отчёт по этапам 0–2 с решениями владельца — `STAGE2_REPORT.md`.

**Тесты на конец работы:** backend 657 ✓, web 19 ✓, Flutter 46 ✓ (Flutter в этапах 2–6 не менялся — по решению владельца экраны Flutter делаются одним проходом после этапов 3–6).

## Флаги (каждая функция — за своим; включено в preview, выключено в production)

| Флаг | Что включает | Production по умолчанию |
|---|---|---|
| `garage_v1` | Гараж | выключен |
| `ai_mechanic_v1` | ИИ-механик (выключается одним флагом) | выключен |
| `owners_club_v1` | Клуб владельцев | выключен |
| `club_ai_moderation` | ИИ-модерация клуба (дополнительно к автофильтру) | выключен всегда, пока не включат |
| `public_car_pages` | Генерация и раздача публичных страниц `/cars` | выключен |
| `subscription_v1` | Модель прав «бесплатно / подписка» | выключен (пока выключен — все права открыты, как раньше) |
| `garage_recall_job` | Суточная проверка NHTSA внутри сервера (иначе — cron со скриптом) | выключен |

Переменные окружения: `AUTOEXPERT_<ИМЯ_ФЛАГА>=true/false`.

## Этап 3 — ИИ-механик (`ai_mechanic_v1`)
- **Где:** чат в карточке машины из гаража; примеры вопросов — «какое масло», «что проверить перед зимой», «какая жидкость в коробке».
- **Из чего строится ответ:** только из данных этой конфигурации — факты, регламент ТО, известные проблемы, recalls — плюс журнал и пробег владельца. У каждого факта есть id (F1…); модель обязана ссылаться на id.
- **Проверка сервером до показа:**
  - любое число в утверждении о машине должно быть в процитированных фактах, иначе утверждение снимается (выдуманные объёмы, допуски, интервалы не пройдут);
  - общие советы показываются отдельно, «не из данных машины», и не могут содержать чисел;
  - если ничего не осталось — честный отказ: «в данных этой машины ответа нет — в руководстве и в нашей базе это не указано»;
  - HIDDEN_CONFLICT в контекст не попадает (тест).
- **Модель:** Claude через бэкенд, ключ из `AUTOEXPERT_ANTHROPIC_API_KEY` или `ANTHROPIC_API_KEY`. Модель задаётся настройкой `ai_mechanic_model`, сейчас `claude-opus-5-5`; для экономии можно поставить `claude-sonnet-5-5`.
- **Без ключа:** режим «только данные» — показываются найденные по вопросу факты машины с источниками, без генерации текста.
- **Лимит, журнал, язык:** лимит вопросов на пользователя в сутки (`ai_mechanic_daily_limit` = 20); журнал всех запросов (`ai_mechanic_requests`: вопрос, ответ, что снято проверкой, токены, время). Ответ — на языке интерфейса.
- **Тесты:** 8.
- **Ключа в этой сессии не было**, поэтому живые ответы Claude не проверялись. Обращение к API проверено тестом с подменённым транспортом: заголовки, модель, язык, снятие выдуманного числа.

## Этап 4 — Клуб владельцев (`owners_club_v1`)
**Готовность аккаунтов (проверено и доделано — до этого не было ничего из трёх пунктов):**
- **Подтверждение почты:** письмо со ссылкой; токены одноразовые, хранится только хэш.
- **Восстановление пароля:**
  - одинаковый ответ для существующей и несуществующей почты — нельзя перебрать адреса;
  - ссылка живёт 1 час;
  - после смены пароля старые сессии отзываются.
- **Защита от подбора:** 5 неудачных входов на адрес или 30 с одного IP за 15 минут → 15 минут блокировки.
- **Письма** уходят в очередь `outbox_messages`; почтового и SMS-провайдера пока нет. Подтверждение телефона требует SMS-провайдера: канал SMS в очереди уже предусмотрен.
- **Писать в клубе можно с подтверждённой почтой.** Demo-сессии preview — исключение.

**Клуб:**
- **Комнаты:** по марке (18) и по популярным поколениям — у поколения есть конфигурации и не меньше 3 известных проблем; таких 182. По комплектациям комнат нет, пустых комнат нет. Из машины в гараже ведёт кнопка «Клуб владельцев».
- **Стартовые темы:** из известных проблем поколения в нашей базе, до 20 на комнату. Показываются на языке читателя: SECONDARY_NOTE — «по данным справочников», OWNER_REPORTS — «владельцы сообщают», HIDDEN_CONFLICT — никогда.
- **Посты, комментарии, фото:** до 4 на пост; фото перекодируются — метаданные камеры и координаты удаляются. Есть отметка «у меня то же самое».
- **Модерация:**
  - кнопка «пожаловаться»; 3 жалобы скрывают текст до решения модератора;
  - автофильтр мата (RU/AZ/EN) и спама (ссылки, повторы, частота) — такие тексты уходят модератору;
  - по флагу — ИИ-модерация;
  - блокировка автора; журнал всех действий модерации; экран модератора — только для `is_admin`.
- **Связь с базой:** когда «у меня то же самое» отмечают `club_review_threshold` владельцев (5), тема попадает в очередь проверки. Только после одобрения модератора она записывается в базу как известная проблема поколения — OWNER_REPORTS «владельцы сообщают», уверенность LOW, число владельцев. Автоматически ничего не пишется.
- **Личные данные:**
  - почта и телефоны в текстах заменяются на «[скрыто]»;
  - авторы видны по имени в клубе или «Владелец #XXXX», почты в ответах нет (проверено тестом).
- **Тесты:** 6 (аккаунты) и 11 (клуб).
- **Данные в живой базе:** при открытии клуба в preview там созданы комнаты и стартовые темы. Это рабочие данные клуба, не тестовые.

## Этап 5 — Публичные страницы (`public_car_pages`)
- **Генератор:** `scripts/build_public_pages.py` строит статический сайт — страница на **линейку → поколение → двигатель**, языки EN (главный), RU, AZ.
  - Пример адреса: `/cars/en/toyota/camry/viii-2018-2024/2-5l-a25a-fks/`.
  - Разделы: известные проблемы, масло и жидкости, регламент ТО, отзывные кампании, FAQ.
  - Где значения различаются по годам, приводу или коробке — указано, к чему относятся («2018–2022 · FWD; 2020–2022 · AWD»).
- **Правила данных:**
  - как в карточке: вторичное — с пометкой, скрытые конфликты — никогда;
  - без цитат из руководств — только значения и название источника;
  - страница без данных не создаётся.
- **SEO:**
  - понятные адреса, `title` и `description`, canonical;
  - hreflang для en/ru/az и x-default;
  - schema.org `Vehicle` и `FAQPage`;
  - `sitemap.xml` с альтернативами языков и `robots.txt`;
  - один общий CSS, без JavaScript.
- На каждой странице блок «Добавьте свою машину в гараж» со ссылкой на приложение.
- **Сборка:** полная сборка 2026-10-05: 527 страниц на язык (1 581 страница, вместе с индексами 1 917 HTML), 41 МБ, sitemap на 2 583 адреса, 102 минуты в 8 процессах. Результат лежит в `C:\AutoExpertData\public_site` — это папка для выкладки на сервер, в git её нет. В preview страницы открываются по адресу `/cars/...`.
- Тесты: 6.

## Этап 6 — Модель подписки (`subscription_v1`, без реальных платежей)

| Бесплатно | Подписка | Разово |
|---|---|---|
| Гараж: 1 машина; базовый регламент ТО и напоминания; чтение клуба; публичные страницы | Несколько машин; персональные подсказки (известные проблемы вашей машины) и уведомления о recalls; ИИ-механик; писать в клубе; экспорт журнала (PDF); без рекламы | VIN-отчёт (как было) |

- **Цены по регионам** в конфиге `subscription_prices`: US $3.99, CA C$4.99, AZ 1.00 AZN в месяц. Пробный период `subscription_trial_days` = 7 дней, один раз на пользователя.
- **Оплата:** App Store и Google Play — заглушка. Вне production «покупка» включает месяц без списания; в production ответ `501 STORE_NOT_CONNECTED`. Отмена оставляет права до конца оплаченного периода.
- **Платная функция без прав** возвращает `402 SUBSCRIPTION_REQUIRED` с названием функции. Приложение открывает экран подписки; в карточке машины вместо проблем — блок «по подписке».
- Оплату VIN-истории и реальные платежи не трогал.
- Тесты: 7.

## Скриншоты
- Этап 2 — `data_work/product/screens/stage2/`.
- Этапы 3–6 — `data_work/product/screens/stages3-6/` (EN, RU, AZ):
  - `free_car_locked_*` — бесплатный план: подсказки закрыты;
  - `subscription_free_*`, `subscription_trial_*`;
  - `mechanic_*` — ответ в режиме «только данные» и честный отказ;
  - `club_home_*`, `club_room_*`, `club_post_*`, `club_starter_topic_*`;
  - `public_camry_*` — страница целиком; `public_camry_top_*` — первый экран.
- Данные для скриншотов — тестовые вводы под demo-сессиями. Машины и посты после съёмки удалены.

## Регламенты ТО (решение владельца по этапу 2)
- Список нужных документов: `data_work/product/maintenance_documents_needed.md`.
  - Копий на carmans и mycarusermanual нет.
  - Toyota: нужны 52 книжки Warranty & Maintenance Guide — Camry, Corolla, RAV4, Highlander за 2014–2026.
  - Hyundai: нужны 26 руководств за старые годы.
  - Куда класть: `C:\AutoExpertData\raw\owner_supplied\<марка>\<модель>\`, имена файлов предложены в списке.
- Hyundai 2024–2026 скачивать не нужно: график уже есть в официальных руководствах на диске. Пробел — в сборщике ТО (`build_maintenance_hmc.py`); это вынесено в отдельную задачу.

## Миграции и бэкапы
- f090 (Гараж), f091 (ИИ-механик), f092 (аккаунты), f093 (клуб), f094 (подписки).
- Перед каждой — бэкап в `C:\AutoExpertBackups\autoexpert.db.backup_20261005_pre_f09x`, затем копия-репетиция, потом живая база.
- Все пять применены к живой базе (последняя — f094, после сборки сайта, которая читала живую базу).

## Коммиты
- `7e83bde` fix(i18n): nine maintenance jobs without a label (PCV valve, CV joints, motor coolant…) get RU / AZ / EN labels
- `011acff` chore(screens): screenshot scripts for stages 3–6; the garage script starts the trial first (several cars are a subscription right)
- `bac3dd4` feat(subscription): subscription model behind subscription_v1 — free (1 car, basic schedule, reading the club, public pages) vs subscription (several cars, personal hints and recall alerts, AI mechanic, writing in the club, PDF log, no ads), prices per region in the config, trial once, App Store / Google Play stub outside production only, 402 with the feature, subscription screen (product phase, stage 6)
- `961c517` feat(public-pages): static public car pages behind public_car_pages — one page per generation and engine in EN/RU/AZ (known issues, oil & fluids, maintenance schedule, recalls), display rules, no quotations, hreflang, schema.org Vehicle + FAQPage, sitemap, garage link; generator script, preview serves /cars (product phase, stage 5)
- `f53a78e` feat(club): owners club screens in the web preview behind owners_club_v1 — rooms of my cars and makes, room with starter topics, post with photos, comments, 'me too', report; link from the garage car (product phase, stage 4c)
- `b08230b` feat(club): owners club behind owners_club_v1 — make and generation rooms with starter topics from known issues, posts, comments, photos without metadata, 'me too', reports, autofilter and optional AI moderation, bans, moderation log, review queue into OWNER_REPORTS only after a moderator, personal data masked (product phase, stage 4b)
- `90fcb12` docs(product): missing US maintenance schedules of 14 popular models — copy sites checked (nothing usable), Hyundai 2024–2026 already on disk, list of documents for the owner
- `c63cb4c` feat(accounts): account readiness for the owners club — email confirmation, password reset without address enumeration, single-use expiring tokens, older sessions revoked after a reset, login lock after repeated failures, message outbox (product phase, stage 4a)
- `105339d` feat(ai-mechanic): AI mechanic for a Garage car behind ai_mechanic_v1 — answers only from the car's data, every number checked against the cited facts, general advice apart, honest refusal, Claude via the backend (key from env), data-only mode without a key, daily limit, request log (product phase, stage 3)
- `2326f77` fix(garage): 'не знаю' answers about jobs outside the car's schedule are not saved
- `e38158f` docs(product): stage 2 report — Garage, data gaps of the showcase cars, decisions for the owner; sample service log PDF
- `fafa89f` feat(garage): Garage screens in the web preview behind garage_v1 — list, add by VIN or catalog with history questions, car card, oil interval, service log, PDF, 'My car' feed; stage 2 screenshots EN/RU/AZ
- `d30342c` feat(garage): Garage backend behind garage_v1 — local vPIC VIN decoding, next-service calculation, service log, feed, daily NHTSA recall check, push interface, service log PDF (product phase, stage 2)
- `088ae15` feat(i18n): Flutter English — terms, US tech panel, device language default (product phase, stage 1)
- `ba1dbe9` feat(i18n): English as the third language — server texts, web, data texts, US units (product phase, stage 1)
- (этот отчёт и скриншоты этапов 3–6 — следующим коммитом)

## Что нужно от владельца перед выкладкой
1. **Ключ Claude API** — для ИИ-механика (и ИИ-модерации клуба, если её включать). Плюс решение по модели: opus-5-5 или sonnet-5-5 ради цены.
2. **Домен** для публичных страниц и ссылок в письмах: настройки `public_site_base_url` и `public_app_url`. Затем перегенерировать сайт.
3. **Аккаунты магазинов** App Store Connect и Google Play Console: подписочные продукты, цены, проверка чеков на сервере.
4. **Push-сервис** (APNs / FCM) — интерфейс отправки готов (`garage_push.PushSender`).
5. **Почтовый провайдер** (и SMS, если нужен телефон) — для подтверждения почты и восстановления пароля. Сейчас письма копятся в `outbox_messages`.
6. **Подтверждение цен** по регионам и длины пробного периода.
7. **Модераторы клуба:** назначить пользователей с правами `is_admin`.
8. **Перенос на PostgreSQL и сервер Hetzner** — отдельным промтом. Там же cron для `garage_recall_job.py` и для генератора сайта.
9. **Документы ТО** из списка выше — в `raw/owner_supplied`.

## Известные ограничения
- **Экраны Flutter** для этапов 2–6 не сделаны — по решению владельца, следующим проходом. Сервер и API для них готовы.
- **Типичный пробег проблем** (CarComplaints) в базе пока пустой; гараж и сайт покажут его, когда он появится.
- **Витринные машины этапа 2:** у Camry 2020 и Sonata 2018 нет регламента ТО — ждут документов из списка.
- **Подписи работ на публичных страницах:** сайт собран до добавления подписей к 9 работам ТО (PCV, ШРУС, охлаждение электромотора и др.). При следующей генерации эти подписи появятся на трёх языках.
