import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
XC = 'https://www.xchuxing.com/car/parameter?sid=610'; AH = 'https://www.autohome.com.cn/news/202502/1303971.html'
b = base(176178)
r, _ = rec([176178, 179586, 180914, 171461], 'x', model='BYD Qin Plus DM-i', model_cn='秦PLUS DM-i', my=2025,
    trim_key='DM-i 120km (智驾版, DM 5.0, 15.8 kWh)', status_china='в продаже (2025款 智驾版; 128KM进取型 с 2025-09; есть 2026款)',
    powertrain_type='PHEV_series_parallel', hybrid_system='BYD DM-i (EHS)', platform='DM 5.0', transmission='E-CVT',
    listing={'battery_kwh': 15.9, 'hp': 197, 'url': 'https://turbo.az/autos/10604255-byd-qin-plus'},
    ranges={'NEDC': None, 'WLTC': 90, 'CLTC': 120}, fuel=miit_fuel(b),
    charging=chg(b, dc=None, ac_full_h=5.55),
    battery_extra={'supplier': 'FinDreams'},
    closest={'trim': '2025款 智驾版 120KM超越型 / 128KM进取型 (sohu 176178/179586), 15.8–15.87 kWh',
             'why': 'Батарея 15.9 ≈ 15.8–15.87 kWh есть только у DM 5.0 (2025 智驾版 120/128 км, 2026 128 км); мощность у них 120 кВт = 163 л.с., не 197. 197 л.с. (145 кВт) — у 2024 荣耀版 120 км (DM-i 4.0) с батареей 18.32 kWh. По батарее ближе DM 5.0, по мощности — 荣耀版.'},
    buyer_checks=['15.9 kWh / 197 л.с. — такой версии нет: проверить код двигателя (BYD472QC = DM 5.0, 163 л.с. мотор; BYD472ZQA = DM-i 4.0, 197 л.с. мотор) и табличку батареи',
                  'DC-зарядка: по sohu есть у 120KM, по xchuxing — только у 128KM; проверить наличие DC-порта на машине',
                  'Это НЕ близнец Destroyer 05 (там DM-i 4.0, мотор 145 кВт)',
                  'Совместимость разъёма GB/T с местными зарядными станциями'],
    extra_sources={'ev_range_km': XC, 'battery_supplier': XC, 'charging': XC, 'platform': AH},
    notes='Поколение DM 5.0 подтверждено (ДВС BYD472QC 74 кВт, мотор 120 кВт). Конфликт по DC: sohu — 120KM 快充+慢充, 128KM не указано; xchuxing — 128KM DC 0.5 ч, 120KM без DC; поле dc_supported = null. AC-зарядка 120KM 5.55 ч — xchuxing. 128KM: CLTC 128 / WLTC 100 км (xchuxing), 15.87 kWh у 2026款 (sohu).',
    verification='mismatch')
save('byd_qin-plus_2025_dm5-120km', r)
