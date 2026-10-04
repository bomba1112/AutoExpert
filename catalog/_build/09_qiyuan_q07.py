import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
b = base(176093)
for my, url, extra in [(2025, 'https://turbo.az/autos/10588616-changan-qiyuan-q07', ''),
                       (2026, 'https://turbo.az/autos/10675073-changan-qiyuan-q07', ' 2026款 Q07 в китайских таблицах нет (последние версии — 2025款, в т.ч. 激光 с 2025-10); год 2026 в объявлении — вероятно, год выпуска.')]:
    r, _ = rec([176093, 177502], 'x', model='Changan Qiyuan Q07', model_cn='长安启源Q07', my=my, trim_key='145 (21.5 kWh)',
        aliases=['Changan Nevo Q07'], status_china='2025款 145尊耀型/尊荣型 в продаже (sohu)',
        powertrain_type='PHEV_series_parallel', hybrid_system='Changan PHEV, 1 мотор + E-CVT', platform=None,
        transmission='E-CVT', listing={'battery_kwh': 21.5, 'hp': 224, 'url': url},
        fuel=miit_fuel(b), charging=chg(b),
        buyer_checks=['21.5 kWh = версия 145 (атмосферный JL469Q1); 31.7 kWh = версия 215 (у 旗舰 — турбо JL469ZQ1 110 кВт)',
                      'DC 30–80% за 0.25 ч по таблице; проверить работу DC-порта',
                      'Совместимость разъёма GB/T с местными зарядными станциями'],
        notes='Объявление совпадает с официальной версией 145: 21.5 kWh, передний мотор 165 кВт = 224 л.с. Цикл запаса хода в таблице не указан (工信部).' + extra,
        verification='verified')
    save(f'changan_qiyuan-q07_{my}_145', r)
