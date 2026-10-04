import sys; sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from yearbuild import build_model, issues_from
WIKI = 'https://en.wikipedia.org/wiki/BYD_Song_Plus'
ITH = 'https://www.ithome.com/0/783/314.htm'
def gen(k):
    y, bat, mkw, ecode, ekw, drive = k[:6]
    awd = '四驱' in (drive or '')
    if y == 2021:
        g = 'Дорестайлинг (2021款, DM-i с 03.2021); DM-i 4.0' + (' 4WD, 1.5T + 2 мотора' if awd else '')
        return {'generation': g, 'sources': {'generation': WIKI}, 'notes': 'Дорестайлинг 2020–2023 по Wikipedia.'}
    if y == 2023:
        return {'generation': 'Рестайлинг 冠军版 (Champion Edition, с 06.2023); DM-i 4.0', 'sources': {'generation': WIKI},
                'notes': 'Рестайлинг 06.2023 «Champion Edition» — Wikipedia.'}
    if y == 2024:
        return {'generation': 'Рестайлинг, 荣耀版 (Honor Edition, с 02.2024); DM-i 4.0', 'sources': {'generation': 'https://portal.auto.sohu.com/aggr/model/trims/pk?trim_ids=171589,171590,171592&city_code=110000'},
                'notes': '荣耀版 — по названию комплектаций sohu; техника как у 冠军版 (ДВС 81 кВт, мотор 145 кВт).'}
    if y == 2025:
        return {'generation': '2025款 (с 07.2024, 智驾版 с 02.2025); DM 5.0 — «первый SUV на 5-м поколении DM»', 'sources': {'generation': ITH},
                'notes': 'DM 5.0 по IT之家: ДВС 74 кВт, мотор 160 кВт.'}
def ranges(k, b):
    y, bat = k[0], k[1]
    m = b['miit_range_km'] if b else None
    if y == 2021: return {'NEDC': m, 'WLTC': None, 'CLTC': None}
    if y == 2025: return {'NEDC': None, 'WLTC': {'18.3': 91, '26.6': 128}.get(bat), 'CLTC': None, 'MIIT': m}
    return {'NEDC': None, 'WLTC': None, 'CLTC': None, 'MIIT': m}
def issues(k):
    y, drive = k[0], k[5] or ''
    if y in (2023, 2024) and '四驱' not in drive:
        return issues_from('byd_song-plus-dm-i')
    return []
def extra(k, r, b):
    if k[0] == 2021: r['sources']['ev_range_km'] = WIKI
    if k[0] == 2025 and k[1] in ('18.3', '26.6'): r['sources']['ev_range_km'] = ITH
    if k[0] in (2021, 2025) or '四驱' in (k[5] or ''):
        r['notes'] += ' known_issues не перенесены: отзывы в _issues относятся к 2023–2024 FWD (DM-i 4.0, рестайлинг).'
meta = dict(model='BYD Song PLUS DM-i', model_cn='宋PLUS DM-i', powertrain_type='PHEV_series_parallel',
            hybrid_system=lambda k: 'BYD DM-i (EHS)' + (', 2 мотора' if '四驱' in (k[5] or '') else ''),
            transmission='E-CVT')
for slug, key, r, hit in build_model(6396, 'byd_song-plus-dm-i', meta, gen, issues, ranges, extra):
    print(('MERGED ' if hit else 'new    ') + slug, '|', r['generation'], '|', len(r['trims']), 'trims |', len(r['known_issues']), 'issues |', r['verification'])
