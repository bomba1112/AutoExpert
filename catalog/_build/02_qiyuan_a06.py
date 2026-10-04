import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
b = base(180201)
r, _ = rec([180201, 180202, 181396, 169540, 169347], 'x',
    model='Changan Qiyuan A06 EREV', model_cn='长安启源A06 增程版', my=2026, trim_key='增程 240 (28.39 kWh)',
    status_china='в продаже с 2025-11 (2026款); 增程-версии A06 до 2025-11 не было',
    powertrain_type='EREV', hybrid_system='Changan 增程 (range extender), ДВС только генератор', platform=None,
    transmission='Редуктор 1 ст.',
    listing={'battery_kwh': 28.39, 'hp': 163, 'url': 'https://turbo.az/autos/10730684-changan-qiyuan-a06', 'year': 2023, 'drive': 'передний'},
    ranges={'NEDC': None, 'WLTC': None, 'CLTC': None, 'MIIT': 240},
    fuel=miit_fuel(b), charging=chg(b),
    closest={'trim': 'Qiyuan A06 增程版 2026款 240Max/240激光Ultra (sohu 180201/180202/181396)',
        'why': 'Батарея 28.39 kWh и мотор 120 кВт = 163 л.с. совпадают точно. Не совпадают год (в объявлении 2023, а 增程 A06 вышел в 2025-11) и привод (в объявлении передний, официально задний). Альтернатива по году — Deepal SL03 / Qiyuan A07 增程 2023 (28.39–28.4 kWh), но у них мотор 160 кВт = 218 л.с.'},
    buyer_checks=['Год в объявлении (2023) невозможен для A06 增程 — проверить VIN/дату выпуска; возможно, это Deepal SL03 или A07 增程 2023 (218 л.с.)',
                  'Привод задний (официально), не передний как в объявлении',
                  'EREV: двигатель только заряжает батарею; при разряженной батарее динамика ограничена',
                  'Есть только DC-зарядка по данным sohu (充电方式: 快充); наличие AC-порта проверить на машине',
                  'Совместимость разъёма GB/T с местными зарядными станциями'],
    notes='Тип EREV — из таблицы sohu (动力类型: 增程式), turbo.az пишет «Plug-in Hibrid». Цикл запаса хода 240 км в таблице не указан (工信部). Разгон 0–100 в таблице не указан. Объявление не совпадает по году и приводу — см. closest_official.',
    verification='mismatch')
save('changan_qiyuan-a06_2026_erev-240', r)
