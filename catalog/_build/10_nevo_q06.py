import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, miit_fuel, chg; from build import save, base
b = base(183942)
r, _ = rec([183942], 'x', model='Changan Nevo Q06 EREV', model_cn='长安启源Q06 增程版', my=2026, trim_key='增程 1600 双电机 (28.39 kWh)',
    aliases=['Changan Qiyuan Q06', 'Q06 R'], status_china='новинка: старт продаж 2026-09-23 (2027款)',
    powertrain_type='EREV', hybrid_system='Changan 增程 (range extender), ДВС только генератор', platform=None,
    transmission='Редуктор 1 ст.', listing={'battery_kwh': 28.4, 'hp': 367, 'url': 'https://turbo.az/autos/10727942-changan-nevo-q06'},
    fuel=None, charging=chg(b),
    buyer_checks=['Модель вышла в Китае 2026-09-23 — машина почти новая; уточнить у официального дилера гарантию и наличие запчастей',
                  'Привод: sohu — «双电机后驱» (задний), в прессе — 2 мотора по 135 кВт спереди и сзади; проверить, полный ли привод',
                  'EREV: ДВС только заряжает батарею',
                  'DC 30–80% за 0.25 ч по таблице; AC-зарядка в таблице не указана — проверить',
                  'Совместимость разъёма GB/T с местными зарядными станциями'],

    notes='Объявление совпадает с официальной версией: 28.39 kWh, суммарно 270 кВт = 367 л.с. (sohu, 2027款 1600 双电机智享型). Год 2026 в объявлении — год выпуска. Конфликт по приводу: sohu пишет «双电机后驱», но указывает только задний мотор 270 кВт и «1 мотор»; пресса — 2 мотора по 135 кВт (передний + задний). Поле motor.count/axle по sohu, drive — не подтверждён. Цикл запаса хода 200 км в таблице не указан (工信部).',
    verification='partial')
r['drive'] = None
r['motor']['count'] = None; r['motor']['axle'] = None
save('changan_nevo-q06_2026_erev', r)
