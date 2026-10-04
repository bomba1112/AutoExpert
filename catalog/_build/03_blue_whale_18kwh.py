import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
CNC = 'https://carnewschina.com/2023/10/21/changan-qiyuan-a05-plug-in-hybrid-sedan-launched-price-starts-at-12300-usd'
HS = 'Changan Blue Whale (蓝鲸) hybrid, 1 мотор + E-CVT'
common_checks = ['18.4 kWh LFP + мотор 158 кВт (215 л.с.) + ДВС JL469Q1 72 кВт — одна и та же силовая установка Changan у A05 145 / Eado PHEV 145 / UNI-Z PHEV',
                 'DC-зарядка есть (30–80% по таблице sohu); проверить работу DC-порта',
                 'Совместимость разъёма GB/T с местными зарядными станциями']

# 1) Eado PHEV
b = base(177015)
r, _ = rec([177015, 177016], 'x', model='Changan Eado PHEV', model_cn='长安逸动PHEV', my=2025,
    trim_key='智慧新蓝鲸 145KM (18.4 kWh)', status_china='в продаже (2025款 с 2025-03, sohu)',
    powertrain_type='PHEV_series_parallel', hybrid_system=HS, platform=None, transmission='E-CVT',
    listing={'battery_kwh': 18.4, 'hp': 215, 'url': 'https://turbo.az/autos/10743833-changan-eado'},
    fuel=miit_fuel(b), charging=chg(b), buyer_checks=common_checks,
    notes='Объявление совпадает с официальной версией 145KM: 18.4 kWh, мотор 158 кВт = 215 л.с. Силовая установка идентична Qiyuan A05 145 (sohu: тот же ДВС JL469Q1, мотор 158 кВт/330 Н·м, 18.4 kWh). Цикл запаса хода 145 км в таблице не указан (工信部).',
    verification='verified')
save('changan_eado-phev_2025_145km', r)

# 2) UNI-Z PHEV
b = base(176124)
r, _ = rec([176124, 177916, 171994], 'x', model='Changan UNI-Z PHEV', model_cn='长安UNI-Z PHEV', my=2025,
    trim_key='智慧新蓝鲸 125km (18.4 kWh)', status_china='в продаже (2025款 战舰+/超能型; 战舰版 снят, sohu); есть 2026款 130km',
    powertrain_type='PHEV_series_parallel', hybrid_system=HS, platform=None, transmission='E-CVT',
    listing={'battery_kwh': 18.4, 'hp': 215, 'url': 'https://turbo.az/autos/10738355-changan-uni-z'},
    fuel=miit_fuel(b), charging=chg(b), buyer_checks=common_checks,
    notes='Объявление совпадает с официальной версией 125km: 18.4 kWh, мотор 158 кВт = 215 л.с. 2024 蓝鲸智电iDD 125km технически такой же (sohu). Время AC-зарядки в таблице не указано. Цикл запаса хода в таблице не указан (工信部).',
    verification='verified')
save('changan_uni-z-phev_2025_125km', r)

# 3) Nevo A05 (= Qiyuan A05 145)
b = base(174994)
r, _ = rec([174994, 174995, 174996], 'x', model='Changan Nevo A05', model_cn='长安启源A05', my=2025,
    trim_key='145 (真香版, 18.4 kWh)', aliases=['Changan Qiyuan A05'], twins=['Changan Qiyuan A05 145 (то же авто, экспортное имя Nevo)'],
    status_china='2025款 真香版 145 снят с продажи (sohu)',
    powertrain_type='PHEV_series_parallel', hybrid_system=HS, platform=None, transmission='E-CVT',
    listing={'battery_kwh': 18.4, 'hp': 215, 'url': 'https://turbo.az/autos/10736390-changan-nevo-a05'},
    ranges={'NEDC': None, 'WLTC': None, 'CLTC': 145}, fuel=miit_fuel(b), charging=chg(b),
    buyer_checks=common_checks + ['Рынок в объявлении «Другое» — уточнить происхождение (Китай/экспорт); экспортная версия может отличаться комплектацией'],
    extra_sources={'ev_range_km': CNC, 'hybrid_system': CNC},
    notes='В ТЗ указано как известное расхождение, но по таблице sohu объявление СОВПАДАЕТ с Qiyuan A05 145: 18.4 kWh, мотор 158 кВт = 215 л.с. (сравнивать надо с версией 145, а не 70). Nevo A05 — экспортное имя Qiyuan A05. CLTC 145 км — carnewschina. Конфликт: carnewschina (запуск 2023) — 18.99 kWh и ДВС 81 кВт; sohu — 18.4 kWh и 72 кВт; взято sohu.',
    verification='verified')
save('changan_nevo-a05_2025_145', r)
