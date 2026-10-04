import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
GBT = 'Совместимость разъёма GB/T с местными зарядными станциями'
b = base(179318)
r, _ = rec([179318, 179319], 'x', model='BYD Leopard 7 PHEV', model_cn='方程豹 钛7 PHEV', my=2025, trim_key='190KM 四驱 (35.6 kWh, 360 кВт)',
    aliases=['Fangchengbao Tai 7', 'Leopard Ti7'], status_china='2025款 в продаже (с 2025-09); с 2026-08 — 2026款 300KM (50 kWh)',
    powertrain_type='PHEV_series_parallel', hybrid_system='BYD PHEV, 1.5T + 2 мотора (перед 160 кВт / зад 200 кВт), E-CVT', platform=None,
    transmission='E-CVT', listing={'battery_kwh': 35.6, 'hp': 490, 'url': 'https://turbo.az/autos/10741004-byd-leopard-7'},
    fuel=None, charging=chg(b),
    buyer_checks=['35.6 kWh + 490 л.с. = 4WD 190KM; 2WD 200KM — 1 мотор 200 кВт (272 л.с.)',
                  'Снаряжённая масса 2925 кг (sohu) — проверить износ тормозов и шин', 'DC 30–80% за 0.29 ч по таблице', GBT],
    notes='Объявление совпадает с официальной версией 2025款 190KM 四驱: 35.6 kWh, моторы 160+200 = 360 кВт = 490 л.с. ДВС BYD472ZQB 1.5T 115 кВт. Название гибридной системы (DMO и т.п.) в таблице sohu не указано. Цикл запаса хода в таблице не указан (工信部). Расход 工信部 не указан.',
    verification='verified')
save('byd_leopard-7_2025_phev-4wd-190km', r)

b = base(177497)
r, _ = rec([177497, 177498], 'x', model='Deepal S09 EREV', model_cn='深蓝S09', my=2025, trim_key='四驱Ultra (40.18 kWh, 362 кВт)',
    aliases=['Changan Deepal S09'], status_china='2025款 в продаже (с 2025-05)',
    powertrain_type='EREV', hybrid_system='Changan 增程 (range extender, 1.5T), 2 мотора', platform=None, transmission='Редуктор 1 ст.',
    listing={'battery_kwh': 40.18, 'hp': 492, 'url': 'https://turbo.az/autos/9741620-changan-deepal-s09'},
    fuel=miit_fuel(b), charging=chg(b),
    buyer_checks=['40.18 kWh + 492 л.с. = 四驱Ultra/Ultra+; 后驱 — 231 кВт (314 л.с.); 超长续航 — 53.49 kWh',
                  'EREV: ДВС JL469ZQ1 1.5T только генератор', 'Масса 2668 кг — проверить тормоза и подвеску', GBT],
    notes='Объявление совпадает с официальной версией 2025款 四驱Ultra: 40.18 kWh, моторы 131+231 = 362 кВт = 492 л.с. Цикл запаса хода 210 км в таблице не указан (工信部).',
    verification='verified')
save('changan_deepal-s09_2025_erev-4wd', r)
