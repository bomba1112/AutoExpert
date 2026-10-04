import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
common = dict(model='Deepal S07 EREV', model_cn='深蓝S07 增程版', aliases=['Changan Deepal S07', 'Deepal S7'],
    powertrain_type='EREV', hybrid_system='Changan 增程 (range extender), ДВС только генератор', platform=None,
    transmission='Редуктор 1 ст.')
checks = ['EREV: ДВС не связан с колёсами; при пустой батарее — режим генератора, динамика и шум хуже',
          '2025款: генератор JL469Q1 72 кВт; 2024款: JL473QJ 70 кВт — сверить код двигателя с годом',
          'DC 30–80% за 0.25 ч по таблице; проверить работу DC-порта',
          'Совместимость разъёма GB/T с местными зарядными станциями']
for tid, ids, slug, key, lv, note in [
    (176108, [177908, 176108, 176110, 173922], 'changan_deepal-s07_2025_erev-215', '增程 215 (31.73 kWh)',
     {'battery_kwh': 31.73, 'hp': 238, 'url': 'https://turbo.az/autos/10747015-changan-deepal-s07'},
     'Объявление совпадает с официальной версией 215: 31.73 kWh, задний мотор 175 кВт = 238 л.с.'),
    (176109, [176109, 176111, 173909], 'changan_deepal-s07_2025_erev-285', '增程 285 (39.05 kWh)',
     {'battery_kwh': 39.05, 'hp': 258, 'url': 'https://turbo.az/autos/10076984-changan-deepal-s07'},
     'Объявление совпадает с официальной версией 285: 39.05 kWh, задний мотор 190 кВт = 258 л.с.')]:
    b = base(tid)
    r, _ = rec(ids, 'x', my=2025, trim_key=key, status_china='2025款 в продаже частично (sohu); с 2025-09 — 2026款 230/300 (乾崑 ADS SE)',
        listing=lv, fuel=miit_fuel(b), charging=chg(b), buyer_checks=checks,
        notes=note + ' Тип EREV — из таблицы sohu (增程式); turbo.az пишет «Plug-in Hibrid». Цикл запаса хода в таблице не указан (工信部). Момент ДВС 2025款 в таблице не указан. Время AC-зарядки не указано.',
        verification='verified', **common)
    save(slug, r)
