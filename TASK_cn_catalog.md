# ЗАДАЧА: Технический каталог китайских авто для Auto Expert

## Контекст
Auto Expert — приложение для покупателей авто в Азербайджане (Баку).
Пользователь должен понять **техническую часть** машины: тип силовой установки,
гибридная система, батарея, двигатель, мотор, коробка, зарядка, слабые места.
Данные turbo.az вводит продавец — они **не являются технической правдой**,
это только список того, что исследовать, и "отпечаток" для сопоставления.

## Вход
- `turbo_specs.json` (в этой папке) — объявления с turbo.az:
  make, model, year, price_azn, under_budget, fuel, engine_l, battery_kwh, hp, gearbox, drive, market, url.

## Выход
1. `catalog/<slug>.json` — одна запись на уникальную конфигурацию
   (slug пример: `byd_destroyer-05_2025_dm-i-120km`).
2. `catalog/index.csv` — сводка: slug, модель, год, тип, батарея, л.с., статус проверки.
3. `catalog/REPORT.md` — что найдено, что не удалось подтвердить, расхождения с объявлениями.

## Порядок работы
1. Сгруппируй объявления в **уникальные конфигурации** по ключу:
   `make + model + year + battery_kwh + hp`. Дубли объявлений = одна запись.
2. Порядок обработки: сначала `under_budget = true` (до 44 000 AZN), по возрастанию цены. Потом остальные.
3. **Первую конфигурацию сделай, покажи мне результат и жди моего "ок".**
   После "ок" — обрабатывай все остальные подряд без остановок.
4. Сохраняй каждый JSON сразу после готовности (чтобы можно было продолжить после обрыва).
   Если файл уже есть в `catalog/` — пропускай.
5. Близнецы (rebadge) — одна техническая база, но отдельная запись со ссылкой
   в `twin_models` (например Destroyer 05 = Qin Plus DM-i 4.0 / Qin Pro).

## Источники (по приоритету)
Технические данные:
1. Китайские официальные таблицы конфигураций: autohome.com.cn (参数配置), dongchedi.com, yilu.cn, bitauto.com
2. data.carnewschina.com (структурированно, на английском, по году/комплектации)
3. auto-data.net, en.wikipedia.org (таблицы силовых установок)
4. Официальные сайты BYD / Changan / Geely

Слабые места (только реальные отзывы владельцев):
- drom.ru, drive2.ru, kolesa.kz, club.autohome.com.cn

## ЖЁСТКИЕ ПРАВИЛА
1. **Не выдумывать.** Нет подтверждения → `null`. Лучше пустое поле, чем неверное.
2. **Каждое числовое поле — с источником** в объекте `sources` (поле → URL).
3. **Конфликт источников:** приоритет у китайских официальных таблиц конфигураций.
   Расхождение записать в `notes` (пример: Wikipedia DC 25 kW vs autohome 17 kW → берём 17).
4. **PHEV vs EREV — проверять обязательно.** turbo.az подписывает EREV как "Plug-in Hibrid".
   Признаки EREV: редуктор (Reduktor), большая батарея (обычно >25 kWh), двигатель не связан
   с колёсами механически (增程 / range extender). Тип брать из официальной таблицы, не из turbo.az.
   Значения `powertrain_type`: `ICE`, `HEV`, `PHEV_series_parallel`, `PHEV_parallel`, `EREV`, `BEV`.
5. **Мощность из turbo.az** часто = мощность электромотора или системы, а не ДВС. Разделяй:
   `engine.power_hp`, `motor.power_hp`, `system_power_hp`.
6. **Поколение гибридной системы указывать точно** (BYD DM-i 4.0 vs DM 5.0 отличаются мотором).
   Пример: Qin Plus 2025 с 15.9 kWh — это DM 5.0, НЕ близнец Destroyer 05.
7. **Разъём зарядки:** машина китайского рынка → GB/T (если источник не говорит иное).
   Отдельно указать, есть ли DC вообще (у базовых версий часто нет).
8. **known_issues** — только из отзывов владельцев, у каждого пункта источник.
   Общие слова ("китайская электрика плохая") — не писать.
9. **Расхождение с объявлением** (цифры продавца не совпадают ни с одной официальной
   комплектацией) → не подгонять, записать в REPORT.md как "проверить у продавца".
   Известные случаи: Changan Nevo A05 (18.4 kWh/215 hp не совпадает с Qiyuan A05),
   Changan Qiyuan A06R (непонятное название версии), Lynk & Co 900 цена 99999 = заглушка.
10. `notes`, `known_issues`, `buyer_checks` — на русском языке.

## Схема записи (ЭТАЛОН — так должна выглядеть каждая запись)
```json
{
  "model": "BYD Destroyer 05",
  "model_cn": "驱逐舰05",
  "aliases": ["Chazor", "King", "Seal 5 DM-i"],
  "twin_models": ["BYD Qin Plus DM-i (DM-i 4.0)", "BYD Qin Pro"],
  "my": 2025,
  "trim_key": "DM-i 120km",
  "status_china": "снята с продажи, преемник Seal 05 DM-i",
  "powertrain_type": "PHEV_series_parallel",
  "hybrid_system": "BYD DM-i (EHS)",
  "platform": "DM-i 4.0",
  "engine": {"code": "BYD472QA", "displacement_cc": 1498, "aspiration": "NA",
             "compression": 15.5, "power_hp": 110, "power_kw": 81, "torque_nm": 135},
  "motor": {"type": "PMSM", "count": 1, "power_hp": 197, "power_kw": 145,
            "torque_nm": 325, "axle": "front"},
  "system_power_hp": 197,
  "transmission": "E-CVT",
  "drive": "FWD",
  "battery": {"kwh": 18.3, "chemistry": "LFP", "brand": "BYD Blade",
              "supplier": "FinDreams", "cooling": "liquid"},
  "ev_range_km": {"NEDC": 120, "WLTC": 101, "CLTC": null},
  "consumption_kwh_100km": 14.5,
  "fuel_l_100km": {"value": 3.8, "cycle": "NEDC"},
  "charging": {"connector": "GB/T", "dc_supported": true, "dc_kw": 17,
               "dc_to_80_h": 1.1, "ac_kw": 3.3, "ac_full_h": 5.5},
  "accel_0_100_s": 7.3,
  "top_speed_kmh": 185,
  "curb_weight_kg": 1620,
  "dimensions_mm": {"length": 4780, "width": 1837, "height": 1495, "wheelbase": 2718},
  "known_issues": [
    {"text": "Стойки стабилизатора изнашиваются рано (дважды за 70 тыс. км)", "source": "https://m.kolesa.kz/reviews/?reviewId=689ea3dffe1390c6f4105a33&mark-id=byd&model-id=destroyer-05"},
    {"text": "Слабая шумоизоляция, слышно двигатель и дорогу", "source": "https://www.drom.ru/reviews/byd/destroyer_05/5kopeek/"},
    {"text": "Дешёвые материалы салона, вялый руль", "source": "https://www.drom.ru/reviews/byd/destroyer_05/5kopeek/"},
    {"text": "Мало регулировки сиденья для роста >185 см (кузов Qin Plus)", "source": "https://www.drive2.ru/l/666551712500155200/"}
  ],
  "buyer_checks": [
    "18.3 kWh = версия 120 км с DC; 8.3 kWh = версия 55 км без DC",
    "Стук спереди — стойки стабилизатора",
    "Совместимость разъёма GB/T с местными зарядными станциями"
  ],
  "match_fingerprint": {"battery_kwh": 18.3, "hp": 197},
  "turbo_listings": ["https://turbo.az/autos/10017220-byd-destroyer-05"],
  "sources": {
    "engine": "https://www.yilu.cn/params/97652/",
    "motor": "https://www.yilu.cn/params/97652/",
    "battery": "https://www.yilu.cn/params/97652/",
    "charging": "https://www.yilu.cn/params/97652/",
    "ev_range_km": "https://www.yilu.cn/params/97652/",
    "performance": "https://data.carnewschina.com/database/byd/byd-destroyer-05/2025",
    "platform": "https://en.wikipedia.org/wiki/BYD_Destroyer_05"
  },
  "notes": "Wikipedia указывает DC 25 kW, китайская таблица конфигурации — 17 kW; взято 17. Поколение DM-i 4.0 подтверждено (мотор 145 kW; у DM 5.0 — 160 kW).",
  "verification": "verified"
}
```
`verification`: `verified` (все ключевые поля из официальных таблиц), `partial` (часть полей null),
`mismatch` (объявление не совпадает с официальными комплектациями).

## Запись Destroyer 05 уже готова
Сохрани эталон выше как `catalog/byd_destroyer-05_2025_dm-i-120km.json` и начни со следующей конфигурации.

## Работа со мной
- Одна конфигурация за раз до моего "ок" на первой, потом — подряд.
- Коротко. Без длинных объяснений.
- В конце: выведи `catalog/index.csv` в терминал и путь к REPORT.md.
