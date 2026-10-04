import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
b = base(171590)
r, _ = rec([171590, 171591, 173929], 'x', model='BYD Song PLUS DM-i', model_cn='宋PLUS DM-i', my=2024,
    trim_key='荣耀版 DM-i 110km (18.3 kWh, DM-i 4.0)', status_china='2024款 荣耀版 снят; с 2024-07 продаётся 2025款 (DM 5.0, ДВС 74 кВт, мотор 160 кВт)',
    powertrain_type='PHEV_series_parallel', hybrid_system='BYD DM-i (EHS)', platform='DM-i 4.0', transmission='E-CVT',
    listing={'battery_kwh': 18.3, 'hp': 331, 'url': 'https://turbo.az/autos/10652522-byd-song-plus-dm-i'},
    fuel=None, charging=chg(b),
    closest={'trim': '2024款 荣耀版 DM-i 110km 旗舰型/旗舰PLUS (sohu 171590/171591)',
             'why': 'Год 2024 и батарея 18.3 kWh совпадают; привод передний, 1 мотор 145 кВт = 197 л.с. 331 л.с. нет ни у одной версии Song PLUS DM-i: даже сумма ДВС+мотор = 110+197 = 307 л.с. (2024) или 101+218 = 319 л.с. (2025款 112KM, тоже 18.3 kWh). Цифру 331 продавца, вероятно, не стоит использовать.'},
    buyer_checks=['331 л.с. в объявлении не соответствует ни одной версии — проверить код двигателя: BYD472QA = DM-i 4.0 (2024 荣耀版, мотор 145 кВт); BYD472QC = DM 5.0 (2025款, мотор 160 кВт)',
                  '18.3 kWh = версия 110 км (2024) или 112 км (2025款)',
                  'DC-зарядка указана (快充+慢充), время для 2024 荣耀版 в таблице не указано',
                  'Совместимость разъёма GB/T с местными зарядными станциями'],
    notes='Поколение DM-i 4.0 для 2024 荣耀版 — по ДВС BYD472QA 81 кВт и мотору 145 кВт (как у Destroyer 05). Альтернатива по батарее — 2025款 DM-i 112KM (DM 5.0: BYD472QC 74 кВт, мотор 160 кВт/260 Н·м, DC 30–80% за 0.38 ч). Цикл запаса хода в таблице не указан (工信部). Расход 工信部 у 2024 荣耀版 не указан.',
    verification='mismatch')
save('byd_song-plus-dm-i_2024_110km', r)
