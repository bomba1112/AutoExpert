import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from rec import rec, chg; from build import save, base
W = 'https://en.wikipedia.org/wiki/Zeekr_X'
b = base(175218)
r, _ = rec([175218, 175217, 180125], 'x', model='Zeekr X', model_cn='极氪X', my=2026, trim_key='RWD Long Range (200 кВт, NCM 66/69 kWh)',
    status_china='2025款 长续航版 заменена 2026款 (с 2025-11: RWD 250 кВт, 61.47 kWh LFP)',
    powertrain_type='BEV', hybrid_system=None, platform='SEA2 (Sustainable Experience Architecture)', transmission='Редуктор 1 ст.',
    listing={'battery_kwh': 69.0, 'hp': 272, 'url': 'https://turbo.az/autos/10330527-zeekr-x', 'market': 'официальный дилер'},
    ranges={'NEDC': None, 'WLTC': None, 'CLTC': 560}, fuel=None,
    charging=chg(b, connector=None, dc=True, dc_kw=150, ac_kw=22),
    battery_extra={'supplier': 'CATL'},
    engine_extra=None,
    fingerprint=[{'battery_kwh': 66, 'hp': 272}, {'battery_kwh': 69, 'hp': 272}],
    buyer_checks=['Машина от официального дилера — экспортная версия: разъём (CCS2 или GB/T) уточнить у дилера и на машине',
                  '69 kWh (экспортное обозначение, CATL NCM) ≈ китайская 66 kWh; 2026款 в Китае — уже 250 кВт/61.47 kWh LFP: проверить, какая версия на самом деле',
                  'Китайская SAMR-кампания S2026M0102V: аварийная механическая ручка двери плохо заметна (выпуск 2023-03 — 2026-05) — уточнить у дилера, выполнено ли'],
    extra_sources={'battery_export': W, 'platform': W, 'charging': W, 'battery_supplier': W, 'recall': 'https://www.samr.gov.cn/zlfzj/qxcpzh/zhdt/art/2026/art_42805c6f5d224bf18faf750fd07ce620.html'},
    notes='Мотор 200 кВт = 272 л.с., задний привод — совпадает с китайской 2025款 五座长续航版 (sohu: 66 kWh NCM, 560 км). Wikipedia указывает для дорестайла 69 kWh CATL NCM при тех же 200 кВт — это и есть цифра объявления (экспортная). DC 150 кВт и AC 22 кВт — Wikipedia (в таблице sohu не указано). Разъём экспортной версии не подтверждён — null. CLTC 560 км — Wikipedia (диапазон 512–560) и sohu 工信部 560.',
    verification='partial')
r['engine'] = None
save('zeekr_x_2026_rwd-200kw', r)
