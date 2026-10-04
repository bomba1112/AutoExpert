import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec; from build import save, base, num
def fuel(b):
    v = b.get('fuel_miit'); n = num(v.split('/')[-1]) if v else None
    return {'value': n, 'cycle': '工信部综合'} if n is not None else None
ICE = dict(powertrain_type='ICE', hybrid_system=None, platform=None, ranges=None, charging=None)
ENG = 'Changan Blue Whale (蓝鲸) 1.5T'

# CS75 PRO
b = base(179884)
r, _ = rec([179884, 179885, 178204], 'x', model='Changan CS75 PRO', model_cn='长安CS75 PRO', my=2025, trim_key='1.5T DCT (JL473ZQD, 192 л.с.)',
    status_china='в продаже (2026款 PRO 1.5T DCT с 2025-10)', transmission='7DCT (сухое/мокрое сцепление — не указано)',
    listing={'battery_kwh': None, 'hp': 192, 'url': 'https://turbo.az/autos/10612950-changan-cs-75-pro'}, fuel=fuel(b),
    buyer_checks=['192 л.с. — двигатель JL473ZQD (2026款, с 2025-10); у 2025款 PRO — JL473ZQ7 188 л.с. Проверить код двигателя и дату выпуска',
                  '7-ступенчатый «робот» DCT: проверить рывки на малой скорости и при трогании'],
    notes='Объявление (192 л.с., робот = 7DCT) совпадает с 2026款 PRO 1.5T DCT (выпуск с 2025-10), в объявлении год 2025 — вероятно, год выпуска. 2025款 PRO (2025-06) — 188 л.с./300 Н·м. Тип сцепления DCT в таблице sohu не указан.',
    verification='verified', **ICE)
r['hybrid_system'] = None
save('changan_cs75-pro_2025_1.5t-dct', r)

# CS55 PLUS
b = base(179572)
r, _ = rec([179587, 179571, 179572, 179588], 'x', model='Changan CS55 PLUS', model_cn='长安CS55 PLUS', my=2026, trim_key='第四代 新蓝鲸 1.5T DCT',
    status_china='в продаже (2026款 第四代 с 2025-09)', transmission='7DCT',
    listing={'battery_kwh': None, 'hp': 192, 'url': 'https://turbo.az/autos/10650770-changan-cs-55-plus', 'more': ['https://turbo.az/autos/10603959-changan-cs-55-plus']}, fuel=fuel(b),
    buyer_checks=['Двигатель JL473ZQD 141 кВт/310 Н·м', '7DCT: проверить рывки на малой скорости и при трогании'],
    notes='Объявление (192 л.с., робот) совпадает с 2026款 第四代 1.5T DCT. Расход 工信部 — у версии 天枢豪华型 (у 精英型 не указан). Два объявления — одна конфигурация.',
    verification='verified', **ICE)
save('changan_cs55-plus_2026_1.5t-dct', r)

# CS75 PLUS 2026 1.5T. The two "185 hp" listings (turbo.az 10536975, 10667087) belong to 2025款
# 第三代 冠军版 JL473ZQ7 (138 kW / 188 PS, record changan_cs75-plus_2025_jl473zq7-8at) — owner
# decision 2026-10-04: 2026款 1.5T is JL473ZQD 141 kW / 192 PS only (sohu 180009/180010/182719/182720).
b = base(180009)
r, _ = rec([180009, 180010, 178449, 178450], 'x', model='Changan CS75 PLUS', model_cn='长安CS75 PLUS', my=2026, trim_key='智慧冠军版 1.5T 8AT',
    status_china='в продаже (2026款 智慧冠军版 с 2025-10)', transmission='8AT',
    listing={'url': None}, fuel=fuel(b),
    fingerprint={'battery_kwh': None, 'hp': 192},
    buyer_checks=['8-ступенчатый автомат: проверить толчки при переключениях'],
    notes='Данные записи — 2026款 1.5T JL473ZQD (141 кВт, 192 л.с.); все 1.5T комплектации 2026款 (sohu 180009/180010/182719/182720) — 141 кВт. Объявления «185 л.с.» перепривязаны к 2025款 第三代 冠军版 (JL473ZQ7, 138 кВт) по решению владельца 2026-10-04.',
    verification='verified', **ICE)
save('changan_cs75-plus_2026_1.5t-8at', r)

# UNI-V
b = base(178813)
r, _ = rec([178813, 178814, 177246], 'x', model='Changan UNI-V', model_cn='长安UNI-V', my=2026, trim_key='第三代 1.5T DCT (192 л.с.)',
    status_china='в продаже (2025款 第三代 с 2025-08; 2026款 на sohu нет)', transmission='7DCT',
    listing={'battery_kwh': None, 'hp': 192, 'url': 'https://turbo.az/autos/10744031-changan-uni-v'}, fuel=None,
    buyer_checks=['Двигатель JL473ZQD 141 кВт/310 Н·м (у 2024 — 188 л.с.)', '7DCT: проверить рывки на малой скорости'],
    notes='Объявление (192 л.с., робот) совпадает с 2025款 第三代 1.5T DCT; 2026款 в китайских таблицах нет — год в объявлении, вероятно, год выпуска. Расход 工信部 у 第三代 не указан; у 2025 500Bar 尊享型 — 6.37 л/100 км.',
    verification='verified', **ICE)
r['fuel_l_100km'] = {'value': 6.37, 'cycle': '工信部综合 (2025款 1.5T 500Bar, sohu 177246)'}
save('changan_uni-v_2026_1.5t-dct', r)
