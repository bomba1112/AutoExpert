"""Component catalog: engines / transmissions / hybrid_systems.
  python components.py plan      -> print assignment table (no writes)
  python components.py write     -> write component files (used_in rebuilt) + "components" field in every record
Engines are identified strictly by factory code. Transmissions / hybrid systems by type+supplier+generation,
only where a source confirms it; otherwise null (reason kept in COMPONENT_NULL_REASON of the record).
"""
import collections, glob, json, os, re, sys

ROOT = os.path.join(os.path.dirname(__file__), '..', 'catalog')
COMP = os.path.join(ROOT, 'components')
L = lambda p: json.load(open(p, encoding='utf-8'))
def W(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# ---------------- sources ----------------
S = dict(
    AH_QIN_DM5='https://www.autohome.com.cn/news/202502/1303971.html',
    ITH_SONG_DM5='https://www.ithome.com/0/783/314.htm',
    WIKI_SONG='https://en.wikipedia.org/wiki/BYD_Song_Plus',
    IFANR_TAI7='https://www.ifanr.com/1637177',
    IFANR_LYNK900='https://www.ifanr.com/1664258',
    XINHUA_8X='https://www.news.cn/auto/20260320/bec3e49f307b4479988b9ac22010bb5e/c.html',
    IFANR_8X='https://www.ifanr.com/1658285',
    IFANR_CS75P_GEN2='https://www.ifanr.com/digest/1475311',
    AH_CS75P_GEN4='https://www.autohome.com.cn/news/202408/1299965.html',
    ITH_CS75P_ULTRA='https://www.ithome.com/0/819/893.htm',
    AH_CS55P_7DCT='https://www.autohome.com.cn/news/202109/1213277.html',
    AH_CS55P_7DCT_ASK='https://www.autohome.com.cn/ask/25061429.html',
    IFANR_UNIV_GEN3='https://www.ifanr.com/1633591',
    CARGUIDE_CC='https://carguide.ph/2021/12/2022-toyota-corolla-cross-now-boasts-of.html',
    AH_RUIFANG_THS='https://www.autohome.com.cn/ask/24459447.html',
    AH_RUIFANG_M20G='https://www.autohome.com.cn/news/202510/1309994.html',
)

# ---------------- hybrid systems & transmissions (manual, sourced) ----------------
HYB = {
    'byd_dmi_4.0': dict(name='BYD DM-i (4-е поколение DM, «DM-i 4.0»)', codes=['EHS (DM-i)'], supplier='BYD', generation='DM-i 4.0',
                        specs={'type': 'PHEV, последовательно-параллельный (EHS)', 'engine_kw': 81}, sources={'generation_switch': S['ITH_SONG_DM5'], 'song_plus': S['WIKI_SONG']}),
    'byd_dm_5.0': dict(name='BYD DM 5.0 (5-е поколение DM)', codes=['EHS (DM 5.0)'], supplier='BYD', generation='DM 5.0',
                       specs={'type': 'PHEV, последовательно-параллельный (EHS)'}, sources={'qin_plus_2025': S['AH_QIN_DM5'], 'song_plus_2025': S['ITH_SONG_DM5'], 'leopard_7': S['IFANR_TAI7']}),
    'lynk_em-p': dict(name='Lynk & Co EM-P (智能电混)', codes=['EM-P'], supplier='Lynk & Co / Geely', generation='EM-P (Lynk 900, 2025+)',
                      specs={'type': 'PHEV, 3-ступенчатый DHT'}, sources={'lynk_900': S['IFANR_LYNK900']}),
    'zeekr_sep': dict(name='Zeekr SEP 浩瀚超级电混', codes=['SEP'], supplier='Zeekr', generation='SEP (浩瀚-S, 900 В, 2026)',
                      specs={'type': 'PHEV, 1-ступенчатый DHT, P1+P3 спереди, P4 сзади'}, sources={'zeekr_8x': S['XINHUA_8X'], 'layout': S['IFANR_8X']}),
    'toyota_ths_5': dict(name='Toyota Hybrid System, 5-е поколение', codes=['THS (5th gen)'], supplier='Toyota', generation='5-е поколение',
                         specs={'type': 'HEV, e-CVT (power-split)'}, sources={'corolla_cross_2.0': S['CARGUIDE_CC'], 'ruifang_cn': S['AH_RUIFANG_THS']}),
}
TRN = {
    'byd_ehs_ecvt_dmi4': dict(name='BYD EHS E-CVT (DM-i 4.0)', codes=['EHS'], supplier='BYD', generation='DM-i 4.0', specs={'type': 'E-CVT, 1 ступень, в составе EHS'},
                              sources={'generation': S['ITH_SONG_DM5']}),
    'byd_ehs_ecvt_dm5': dict(name='BYD EHS E-CVT (DM 5.0)', codes=['EHS'], supplier='BYD', generation='DM 5.0', specs={'type': 'E-CVT, 1 ступень, в составе EHS'},
                             sources={'qin_plus_2025': S['AH_QIN_DM5'], 'song_plus_2025': S['ITH_SONG_DM5'], 'leopard_7': S['IFANR_TAI7']}),
    'lynk_em-p_3dht': dict(name='Lynk EM-P 3DHT', codes=['3DHT'], supplier='Lynk & Co / Geely', generation='EM-P', specs={'type': 'DHT, 3 ступени'},
                           sources={'lynk_900': S['IFANR_LYNK900']}),
    'zeekr_sep_1dht': dict(name='Zeekr SEP 1DHT', codes=['1DHT'], supplier='Zeekr', generation='SEP', specs={'type': 'DHT, 1 ступень'}, sources={'zeekr_8x': S['IFANR_8X']}),
    'toyota_ths5_ecvt': dict(name='Toyota e-CVT (THS 5-го поколения)', codes=['e-CVT'], supplier='Toyota', generation='THS 5', specs={'type': 'e-CVT (power-split)'},
                             sources={'corolla_cross_2.0': S['CARGUIDE_CC'], 'ruifang_cn': S['AH_RUIFANG_THS']}),
    'aisin_8at': dict(name='Aisin 8AT (CS75 PLUS)', codes=['8AT'], supplier='Aisin', generation='8-ступенчатый гидроавтомат', specs={'type': 'AT, 8 ступеней'},
                      sources={'cs75plus_gen2': S['IFANR_CS75P_GEN2'], 'cs75plus_gen4_1.5t': S['AH_CS75P_GEN4'], 'cs75plus_gen4_ultra_2.0t': S['ITH_CS75P_ULTRA']}),
    'changan_bluewhale_7dct_wet': dict(name='Changan 蓝鲸 7DCT (мокрое сцепление)', codes=['7DCT'], supplier='Changan (蓝鲸)', generation='蓝鲸 7DCT, мокрый',
                                       specs={'type': 'DCT, 7 ступеней, мокрые сцепления'},
                                       sources={'cs55plus_2022': S['AH_CS55P_7DCT'], 'cs55plus': S['AH_CS55P_7DCT_ASK'], 'univ_gen3': S['IFANR_UNIV_GEN3']}),
}

def family(slug):
    a = slug.split('_'); return a[0] + '_' + a[1]

def assign(slug, d):
    """returns (components dict, reasons dict)"""
    fam = family(slug); eng = (d.get('engine') or {}); code = (eng.get('code') or '').strip() or None
    gen = (d.get('generation') or ''); gb = d.get('transmission') or ''; ptype = d.get('powertrain_type')
    c = {'engine': None, 'transmission': None, 'hybrid_system': None}; why = {}
    # engine: by exact code
    if code: c['engine'] = engine_id(code, d)
    else: why['engine'] = 'нет ДВС (BEV)' if ptype == 'BEV' else 'код двигателя неизвестен'
    # BYD
    if fam.startswith('byd_'):
        g5 = code == 'BYD472QC' or fam == 'byd_leopard-7'
        c['hybrid_system'] = 'byd_dm_5.0' if g5 else 'byd_dmi_4.0'
        c['transmission'] = 'byd_ehs_ecvt_dm5' if g5 else 'byd_ehs_ecvt_dmi4'
    elif fam == 'lynk-co_900':
        c['hybrid_system'], c['transmission'] = 'lynk_em-p', 'lynk_em-p_3dht'
    elif fam == 'zeekr_8x':
        c['hybrid_system'], c['transmission'] = 'zeekr_sep', 'zeekr_sep_1dht'
    elif fam.startswith('toyota_'):
        c['hybrid_system'], c['transmission'] = 'toyota_ths_5', 'toyota_ths5_ecvt'
    elif fam == 'changan_cs75-plus':
        if 'AT' in gb and ((d['my'] in (2022, 2023) and '第二代' in gen and '第三代' not in gen)
                           or (d['my'] == 2025 and '第四代' in gen and '冠军版' not in gen)):
            c['transmission'] = 'aisin_8at'
        elif 'AT' in gb:
            why['transmission'] = 'Aisin 8AT подтверждён только для 第二代 и 第四代 (2025); здесь другое/смешанное поколение или 6AT'
        else:
            why['transmission'] = 'механика: тип/поставщик не подтверждены'
    elif fam == 'changan_cs55-plus' and 'DCT' in gb and code and code.startswith('JL473'):
        c['transmission'] = 'changan_bluewhale_7dct_wet'
    elif fam == 'changan_uni-v' and 'DCT' in gb and d['my'] == 2025:
        c['transmission'] = 'changan_bluewhale_7dct_wet'
    # reasons for remaining nulls
    if c['transmission'] is None and 'transmission' not in why:
        if 'Редуктор' in gb: why['transmission'] = 'редуктор EV/EREV — тип/поставщик не указаны'
        elif fam in ('changan_uni-v', 'changan_cs75', 'changan_cs55-plus') and 'DCT' in gb:
            why['transmission'] = '7DCT: мокрое сцепление/поставщик для этого года источником не подтверждены'
        elif 'E-CVT' in gb: why['transmission'] = 'E-CVT Changan: поколение гибридной трансмиссии не подтверждено'
        elif gb: why['transmission'] = f'{gb}: поставщик/поколение не подтверждены'
        elif ptype == 'BEV': why['transmission'] = 'BEV: редуктор, тип/поставщик не указаны'
        else: why['transmission'] = 'нет данных о трансмиссии'
    if c['hybrid_system'] is None and ptype in ('ICE', 'BEV'):
        why['hybrid_system'] = 'не гибрид (ICE/BEV)'
    if c['hybrid_system'] is None and ptype not in ('ICE', 'BEV'):
        fp = fingerprint(d, code)
        if fp: c['hybrid_system'] = fp
        else: why['hybrid_system'] = 'гибрид без подтверждённого названия и без полного технического отпечатка'
    return c, why

FP_META = {}
def fingerprint(d, code):
    """Technical fingerprint for hybrids without a confirmed marketing name: engine code + motor kW + gearbox type + PHEV/EREV."""
    m = d.get('motor') or {}; ptype = d.get('powertrain_type'); gb = d.get('transmission') or ''
    kws = [k for k in (m.get('front_kw'), m.get('rear_kw')) if k]
    if not kws and m.get('power_kw'): kws = [m['power_kw']]
    gbt = 'ecvt' if 'E-CVT' in gb else ('reducer' if 'Редуктор' in gb else None)
    if not (code and kws and gbt and ptype in ('PHEV_series_parallel', 'EREV')): return None
    pt = 'erev' if ptype == 'EREV' else 'phev'
    brand = family_brand(d)
    fid = f"{brand}_{pt}_{code.lower()}_m{'-'.join(str(int(k)) for k in kws)}"
    meta = FP_META.setdefault(fid, {'engine_code': code, 'motor_kw': kws, 'gearbox': gbt, 'type': pt.upper(), 'batteries': set(),
                                    'axle': m.get('axle')})
    if (d.get('battery') or {}).get('kwh') is not None: meta['batteries'].add((d.get('battery') or {})['kwh'])
    return fid

ENG_META = {}
def engine_id(code, d):
    brand = family_brand(d)
    cc = code.lower().replace(' ', '')
    if cc.startswith('byd'): cc = cc[3:]
    disp = eng_disp(code, d)
    eid = f"{brand}_{cc}" + (f"_{disp}" if '?' not in disp else '')
    ENG_META.setdefault(eid, {'code': code, 'brand': brand})
    return eid

def family_brand(d):
    m = (d.get('model') or '').lower()
    for k in ('byd', 'changan', 'deepal', 'lynk', 'zeekr', 'toyota'):
        if k in m: return 'changan' if k == 'deepal' else k
    return 'other'

def eng_disp(code, d):
    e = d.get('engine') or {}
    cc = e.get('displacement_cc')
    lit = f"{round(cc / 1000, 1)}" if cc else None
    if not lit:
        m = re.search(r'(\d)(\d)(\d)', code)  # JL473 -> 1.5? not reliable; fall back by power family
        lit = '1.5' if any(x in code for x in ('472', '473', '469', '15')) else ('2.0' if any(x in code for x in ('486', '484', '20')) else '?')
    t = 't' if (e.get('aspiration') == 'turbo') else ''
    return f"{lit}{t}"

def scan():
    recs = {}
    for p in sorted(glob.glob(os.path.join(ROOT, '*.json'))):
        recs[os.path.basename(p)[:-5]] = L(p)
    return recs

def plan():
    recs = scan(); use = collections.defaultdict(list); nulls = collections.defaultdict(list)
    for s, d in recs.items():
        c, why = assign(s, d)
        for k, v in c.items():
            if v: use[(k, v)].append(s)
            else: nulls[(k, why.get(k, ''))].append(s)
    return recs, use, nulls

def write():
    recs, use, nulls = plan()
    eng_specs = collections.defaultdict(lambda: {'power_kw': set(), 'torque_nm': set(), 'displacement_cc': set(), 'aspiration': set(), 'models': set()})
    for s, d in recs.items():
        c, why = assign(s, d)
        old = d.get('components') or {}
        d['components'] = c
        d['components_null_reason'] = {k: v for k, v in why.items() if c.get(k) is None} or None
        W(os.path.join(ROOT, s + '.json'), d)
        if c['engine']:
            e = d['engine']; es = eng_specs[c['engine']]
            for k in ('power_kw', 'torque_nm', 'displacement_cc', 'aspiration'):
                if e.get(k) is not None: es[k].add(e[k])
            es['models'].add(d['model'])
    # engines
    for (kind, cid), slugs in use.items():
        sub = {'engine': 'engines', 'transmission': 'transmissions', 'hybrid_system': 'hybrid_systems'}[kind]
        p = os.path.join(COMP, sub, cid + '.json')
        old = L(p) if os.path.exists(p) else {}
        if kind == 'engine':
            m = ENG_META[cid]; es = eng_specs[cid]
            base = dict(id=cid, name=f"{m['brand'].upper()} {m['code']}", codes=[m['code']],
                        supplier={'byd': 'BYD', 'changan': 'Changan', 'lynk': 'Geely (Lynk & Co)', 'zeekr': 'Zeekr / Geely', 'toyota': 'Toyota'}.get(m['brand']),
                        generation=None,
                        specs={'displacement_cc': sorted(es['displacement_cc']) or None, 'aspiration': sorted(es['aspiration']) or None,
                               'power_kw': sorted(es['power_kw']) or None, 'torque_nm': sorted(es['torque_nm']) or None},
                        sources={'specs': 'таблицы sohu в записях used_in (поле sources.engine)'})
        elif cid in FP_META:
            m = FP_META[cid]
            base = dict(id=cid, name=f"{m['type']} Changan: ДВС {m['engine_code']} + мотор(ы) {'+'.join(map(str, m['motor_kw']))} кВт, {'E-CVT' if m['gearbox'] == 'ecvt' else 'редуктор'}",
                        marketing_name=None, codes=[m['engine_code']], supplier='Changan', generation=None,
                        specs={'fingerprint': {'engine_code': m['engine_code'], 'motor_kw': m['motor_kw'], 'gearbox': m['gearbox'], 'type': m['type']},
                               'batteries_kwh': sorted(m['batteries']), 'motor_axle': m['axle']},
                        sources={'specs': 'таблицы sohu в записях used_in'},
                        note='Компонент по техническому отпечатку (маркетинговое название первоисточником не подтверждено). Объединены записи с полным совпадением ключа; батарея может отличаться.')
        else:
            meta = (HYB if kind == 'hybrid_system' else TRN)[cid]
            base = dict(id=cid, **meta)
        comp = {**base, 'known_issues': old.get('known_issues', []), 'used_in': sorted(slugs)}
        comp['sources'] = {**base.get('sources', {}), **{k: v for k, v in (old.get('sources') or {}).items() if k not in base.get('sources', {})}}
        order = ['id', 'name', 'marketing_name', 'codes', 'supplier', 'generation', 'specs', 'note', 'known_issues', 'used_in', 'sources']
        W(p, {k: comp.get(k) for k in order if k in comp})
    return recs, use, nulls

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    recs, use, nulls = (write() if cmd == 'write' else plan())
    for (k, cid), slugs in sorted(use.items()):
        fams = sorted({family(s) for s in slugs})
        print(f"{k:13} {cid:34} {len(slugs):3}  {', '.join(fams)}")
    print('\nNULL:')
    for (k, why), slugs in sorted(nulls.items()):
        print(f"{k:13} {len(slugs):3}  {why}  | {', '.join(sorted({family(s) for s in slugs}))}")
