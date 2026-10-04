import sys, json; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from build import save
base = json.load(open(r'C:/Users/jalil/samr/catalog/changan_qiyuan-a06_2026_erev-240.json', encoding='utf-8'))
r = dict(base)
r.update(model='Changan Qiyuan A06R (название из объявления)', my=2025,
    listing_values={'battery_kwh': 28.39, 'hp': 325, 'url': 'https://turbo.az/autos/10315170-changan-qiyuan-a06r', 'drive': 'задний'},
    turbo_listings=['https://turbo.az/autos/10315170-changan-qiyuan-a06r'],
    closest_official={'trim': 'Qiyuan A06 增程版 2026款 240 (sohu 180201/180202/181396)',
        'why': 'Модели «A06R» нет ни в sohu, ни в Wikipedia. Батарея 28.39 kWh, задний привод и редуктор совпадают только с A06 增程 (EREV), но у него мотор 120 кВт = 163 л.с., а не 325. У A06 BEV максимум 210 кВт = 286 л.с. (Wikipedia) и батарея другая. 325 л.с. нет ни у одной версии A06.'},
    buyer_checks=['Название «A06R» не официальное; 325 л.с. не соответствует ни одной версии A06 — проверить VIN, шильдик и табличку батареи',
                  'Если батарея 28.39 kWh — это A06 增程 (EREV, 163 л.с.), выпуск с 2025-11'] + base['buyer_checks'][2:],
    notes='Запись — техническая база A06 增程 240 (копия), т.к. только она совпадает по батарее. Название версии и мощность из объявления не подтверждены. ' + base['notes'],
    verification='mismatch')
save('changan_qiyuan-a06r_2025_erev-240', r)
