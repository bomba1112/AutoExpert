import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec; from build import save
CNC = 'https://carnewschina.com/2023/10/21/changan-qiyuan-a05-plug-in-hybrid-sedan-launched-price-starts-at-12300-usd'
r, b = rec([174993, 175007, 172326, 170126], 'changan_qiyuan-a05_2025_70',
    model='Changan Qiyuan A05', model_cn='长安启源A05', my=2025, trim_key='70 (真香版, 9.07 kWh)',
    aliases=['Changan Nevo A05'], status_china='в продаже (2025款 真香版 с 2024-10)',
    powertrain_type='PHEV_series_parallel', hybrid_system='Changan Blue Whale iDD', platform='Changan EPA0 / iDD',
    transmission='E-CVT (DHT)',
    listing={'battery_kwh': 9.07, 'hp': 190, 'url': 'https://turbo.az/autos/10724400-changan-qiyuan-a05'},
    ranges={'NEDC': None, 'WLTC': None, 'CLTC': 70},
    fuel=None,
    charging={'connector': 'GB/T', 'dc_supported': None, 'dc_kw': None, 'dc_to_80_h': None, 'ac_kw': None, 'ac_full_h': 3},
    buyer_checks=['9.07 kWh = версия 70 км (NCM, 140 кВт); 18.4 kWh = версия 145 км (LFP, 158 кВт, с DC)',
                  'Наличие DC-разъёма: у 2024 70 — только AC; у 2025 70 sohu пишет «快充+慢充» без времени — проверить порт на машине',
                  'Совместимость разъёма GB/T с местными зарядными станциями'],
    extra_sources={'ev_range_km': CNC, 'charging': 'https://portal.auto.sohu.com/aggr/model/trims/pk?trim_ids=174993,172326&city_code=110000'},
    notes='Объявление совпадает с официальной версией 70: 9.07 kWh, мотор 140 кВт = 190 л.с. Батарея у версии 70 — NCM (三元锂), у 145 — LFP. Цикл CLTC для 70 км — по carnewschina. Тип гибрида и платформа (iDD/EPA0) — по описанию Changan; отдельно в таблице sohu не указаны. 2024 70 и 2025 70 технически одинаковы (sohu), отличие — у 2025 указан DC в способах зарядки без данных о мощности.',
    verification='partial')
r['platform'] = None  # not in config table
r['notes'] = r['notes'].replace(' Тип гибрида и платформа (iDD/EPA0) — по описанию Changan; отдельно в таблице sohu не указаны.', ' Платформа в таблице sohu не указана.')
r['sources']['hybrid_system'] = CNC
save('changan_qiyuan-a05_2025_70', r)
