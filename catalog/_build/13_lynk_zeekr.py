import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
DEALER = 'Машина от официального дилера — возможно экспортная версия: разъём зарядки (CCS2 или GB/T) уточнить у дилера и на машине'
REC_LYNK = 'https://www.samr.gov.cn/zlfzj/qxcpzh/zhdt/art/2026/art_4b10150a9a1f45bfa04fe70e55cbc94d.html'

b = base(182326)
r, _ = rec([182326, 182325, 183377], 'x', model='Lynk & Co 900', model_cn='领克900', my=2026, trim_key='1.5T PHEV (44.85 kWh)',
    status_china='в продаже (2026款 1.5T с 2026-04)', powertrain_type='PHEV_series_parallel',
    hybrid_system='Lynk PHEV, 1.5T + 2 мотора, 3-ступ. DHT', platform=None, transmission='3-ступ. DHT',
    listing={'battery_kwh': None, 'hp': 721, 'url': 'https://turbo.az/autos/10323535-lynk-co-900', 'price_azn': 99999, 'market': 'официальный дилер'},
    fuel=miit_fuel(b), charging=chg(b, connector=None),
    fingerprint={'battery_kwh': 44.85, 'hp': 721},
    buyer_checks=['Цена 99 999 AZN в объявлении — заглушка, реальную цену уточнить',
                  '721 л.с. = ДВС 190 + моторы 530 (160+230 кВт) — арифметическая сумма; версия 2.0T дала бы 254 + 480 = 734 л.с. и 52.38 kWh',
                  'SAMR S2026M0112V: замена лидара у 领克900 выпуска 2025-01-08 — 2025-12-10; проверить дату выпуска и выполнение',
                  DEALER],
    extra_sources={'recall': REC_LYNK},
    notes='Батарея в объявлении не указана. 721 л.с. совпадает с суммой ДВС JLM-4G15TD 140 кВт + моторов 390 кВт = 530 кВт (720.6 л.с.) у версии 1.5T; официальная «系统综合功率» в таблице sohu не указана, поэтому system_power_hp = null. Цикл запаса хода 220 км не указан (工信部). Разъём экспортной версии не подтверждён.',
    verification='verified')
save('lynk-co_900_2026_1.5t-phev', r)

b = base(179788)
r, _ = rec([179788, 179789], 'x', model='Zeekr 001', model_cn='极氪001', my=2026, trim_key='103 kWh 四驱 (680 кВт)',
    status_china='в продаже (2026款 с 2025-10)', powertrain_type='BEV', hybrid_system=None, platform=None, transmission='Редуктор 1 ст.',
    listing={'battery_kwh': 103.0, 'hp': 925, 'url': 'https://turbo.az/autos/10440730-zeekr-001', 'market': 'официальный дилер'},
    fuel=None, charging=chg(b, connector=None),
    buyer_checks=['103 kWh NCM + 925 л.с. = 2026款 103度四驱 Ultra/Ultra+', 'DC 10–80% за 0.17 ч по таблице (нужна мощная станция)', DEALER],
    notes='Объявление совпадает с официальной версией 2026款 103度四驱: 103 kWh NCM, моторы 310+370 = 680 кВт = 925 л.с. Цикл запаса хода 762 км не указан (工信部). Разъём экспортной версии не подтверждён.',
    verification='verified')
r['engine'] = None
save('zeekr_001_2026_103kwh-awd', r)

b = base(181548)
r, _ = rec([181548, 181578, 181579], 'x', model='Zeekr 8X', model_cn='极氪8X', my=2026, trim_key='55 kWh (2.0T + 660 кВт)',
    status_china='в продаже (2026款 с 2026-04)', powertrain_type='PHEV_series_parallel',
    hybrid_system='Zeekr PHEV, 2.0T + 2 мотора, 1-ступ. DHT', platform=None, transmission='1-ступ. DHT',
    listing={'battery_kwh': 55.0, 'hp': 898, 'url': 'https://turbo.az/autos/10547402-zeekr-8x', 'market': 'официальный дилер'},
    fuel=None, charging=chg(b, connector=None),
    buyer_checks=['55 kWh = Max/Ultra/Ultra+ 55kWh; 70 kWh — отдельные версии', 'turbo.az: «Reduktor» — по таблице это 1-ступенчатый DHT (ДВС может работать на колёса), это PHEV, не EREV', DEALER],
    notes='Объявление совпадает с официальной версией 55kWh: моторы 290+370 = 660 кВт = 897 л.с. (в объявлении 898 — округление). ДВС DHE20-PFZ 2.0T 205 кВт. Тип PHEV — sohu (插电式混合动力, 1档DHT). Цикл запаса хода 320 км не указан (工信部).',
    verification='verified')
save('zeekr_8x_2026_55kwh', r)
