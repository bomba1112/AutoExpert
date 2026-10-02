# Mitsubishi — отчёт по базе технических данных US

Сформировано 2026-10-02T20:13:36+00:00 скриптом scripts/build_us_report.py.

**Статус:** Не загружена по решению владельца (2026-10-02, вечер). Данные подготовлены (data_work/mitsubishi/staging), в рабочей БД строк этого конвейера нет.

## Подготовлено, но не записано в БД

- линеек: 2
- поколений: 3
- конфигураций: 91
- фактов: 90
- отзывов: 37
- проблем: 64
- пунктов ТО: 0

## Журнал пробелов подготовленных данных

Записей в журнале пробелов: 137 (по полю и причине):

| Поле | Причина | Записей | Примеры |
|---|---|---|---|
| engine_family_key | factory engine code not in EPA; filled only from a source that names it | 91 | mitsubishi-outlander-us-2014-2.4l-4cyl-ice-a-av-s6-4wd; mitsubishi-outlander-us-2014-2.4l-4cyl-ice-a-av-s6-fwd; mitsubishi-outlander-us-2014-3.0l-6cyl-ice-a-s6-4wd |
| engine_oil_capacity_l | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| engine_oil_viscosity | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| coolant | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| transmission_fluid | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| brake_fluid | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| fuel_tank_l | no US owner's manual for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| power_hp | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| torque_lb_ft | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| tires | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| front_suspension | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| rear_suspension | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| front_brakes | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| steering | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| ground_clearance | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| cargo_l | no US press specification page for these years | 3 | mitsubishi/outlander III; mitsubishi/outlander US2022+; mitsubishi/outlander-sport I-US-2011 |
| generation_boundaries | no vPIC Canadian specification rows for this line; boundaries from DB codes only | 1 | mitsubishi/outlander-sport |
