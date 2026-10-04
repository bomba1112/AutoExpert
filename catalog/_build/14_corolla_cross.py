import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from build import save
AD = 'https://www.auto-data.net/en/toyota-corolla-cross-2.0-197hp-hybrid-e-cvt-45157'
AT = 'https://autotijd.be/en/specs/toyota/corolla-cross/20l-197-hp-3371'
r = dict(model='Toyota Corolla Cross Hybrid', model_cn=None, aliases=[], twin_models=[], my=2026, trim_key='2.0 Hybrid FWD (5-е поколение THS, 197 л.с.)',
    status_china='не китайская машина (официальный дилер); в Китае — 卡罗拉锐放双擎/锋兰达混动 с другим двигателем 1.8',
    powertrain_type='HEV', hybrid_system='Toyota Hybrid System (5-е поколение)', platform='TNGA-C (GA-C)',
    engine={'code': 'M20A-FXS', 'displacement_cc': 1987, 'aspiration': 'NA', 'compression': 14, 'power_hp': 152, 'power_kw': 112, 'torque_nm': 190},
    motor={'type': None, 'count': 1, 'power_hp': 113, 'power_kw': 83, 'torque_nm': 206, 'axle': 'front'},
    system_power_hp=197, transmission='E-CVT', drive='FWD',
    battery={'kwh': None, 'chemistry': 'Li-ion', 'brand': None, 'supplier': None, 'cooling': None, 'voltage_v': 222},
    ev_range_km=None, consumption_kwh_100km=None, fuel_l_100km={'value': 5.1, 'cycle': 'WLTP'}, charging=None,
    accel_0_100_s=7.7, top_speed_kmh=180, curb_weight_kg=1440,
    dimensions_mm={'length': 4460, 'width': 1825, 'height': 1620, 'wheelbase': 2640},
    known_issues=[],
    buyer_checks=['Обычный гибрид без зарядки от розетки', 'Уточнить у дилера страну выпуска и рынок (Европа/Ближний Восток/Япония) — комплектации отличаются',
                  'Данные auto-data — для выпуска 12.2021–08.2025; для 2026 модельного года проверить, не изменились ли цифры'],
    match_fingerprint={'battery_kwh': None, 'hp': 197},
    listing_values={'battery_kwh': None, 'hp': 197, 'url': 'https://turbo.az/autos/10482266-toyota-corolla-cross', 'market': 'официальный дилер'},
    turbo_listings=['https://turbo.az/autos/10482266-toyota-corolla-cross'],
    sources={'engine': AD, 'motor': AD, 'battery': AD, 'performance': AD, 'fuel': AD, 'weight': AD, 'dimensions': AD, 'system_power': AT, 'hybrid_system': 'https://carguide.ph/2021/12/2022-toyota-corolla-cross-now-boasts-of.html'},
    notes='Китайские таблицы не применимы: машина от официального дилера, версия 2.0 Hybrid 197 л.с. продаётся вне Китая. Источник — auto-data.net (Европа, выпуск 12.2021–08.2025) и autotijd.be. Ёмкость батареи в источниках не указана (Li-ion 222 В). Масса — нижняя граница диапазона 1440–1505 кг. Платформа TNGA-C — общеизвестна, но в источниках этой записи не подтверждена.',
    verification='partial')
r['platform'] = None
r['notes'] = r['notes'].replace(' Платформа TNGA-C — общеизвестна, но в источниках этой записи не подтверждена.', '')
save('toyota_corolla-cross_2026_2.0-hev', r)
