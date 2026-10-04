"""Year/powertrain expansion for all catalog models (except Song Plus — see y_byd_song-plus.py).
python y_all.py [model_tag ...]   (no args = all)
"""
import json, os, re, sys
sys.path.insert(0, r'C:/Users/jalil/samr/tools')
from yearbuild import build_model, bind, CAT

AH_QIN = 'https://www.autohome.com.cn/news/202502/1303971.html'   # Qin PLUS 2025 = DM 5.0
ITH_SONG = 'https://www.ithome.com/0/783/314.htm'                  # DM 5.0: engine 74 kW
XC_QIN = 'https://www.xchuxing.com/car/parameter?sid=610'
TAGS = r'(第[一二三四五]代|智慧冠军版|冠军版|荣耀版|荣耀百万版|真香版|智驾版|蓝鲸版|畅享版|PRO|智慧新蓝鲸|蓝鲸智电iDD|经典版|改款|超长续航|华为乾崑|500Bar|新蓝鲸|天枢|五周年)'
TRIMS = {}  # filled lazily by gen()

def tags_of(trims):
    found = []
    for t in trims:
        for m in re.findall(TAGS, t):
            if m not in found: found.append(m)
    return found

def e(k): return (k[3] or '')
def bat(k): return k[1]
def yr(k): return k[0]

def dm_gen(k):
    return 'DM 5.0' if e(k).startswith('BYD472QC') else 'DM-i 4.0'

def dm_sources(k):
    return {'generation': AH_QIN if dm_gen(k) == 'DM 5.0' else None}

def make_gen(label_fn, src_fn=None, note_fn=None):
    def gen(k):
        g = {'generation': label_fn(k)}
        src = src_fn(k) if src_fn else {}
        g['sources'] = {kk: v for kk, v in (src or {}).items() if v}
        if note_fn: g['notes'] = note_fn(k)
        return g
    return gen

def run(model_id, prefix, meta, label_fn, issues=None, src_fn=None, note_fn=None, extra=None, ranges=None):
    gen = make_gen(label_fn, src_fn, note_fn)
    out = build_model(model_id, prefix, meta, gen, issues, ranges, extra)
    for slug, key, r, hit in out:
        print(('MERGED ' if hit else 'new    ') + slug, '|', r['generation'], '|', len(r['trims']), 'tr |', len(r['known_issues']), 'iss |', r['verification'])
    return out

# ---------------- model configs ----------------
def qin_plus():
    lab = {2021: 'Дорестайлинг 2021款', 2023: '冠军版 (2023款)', 2024: '荣耀版 (2024款)', 2025: '智驾版 (2025款, с 02.2025)', 2026: '2026款'}
    def ranges(k, b):
        m = b['miit_range_km'] if b else None
        if k[0] == 2025 and k[1] == '7.68': return {'NEDC': None, 'WLTC': 43, 'CLTC': 55}
        if k[0] == 2025 and k[1] == '15.8': return {'NEDC': None, 'WLTC': 90, 'CLTC': 120}
        return {'NEDC': None, 'WLTC': None, 'CLTC': None, 'MIIT': m}
    def extra(k, r, b):
        if k[0] == 2025: r['sources']['ev_range_km'] = XC_QIN
        if dm_gen(k) == 'DM 5.0' and k[0] == 2026:
            r['notes'] += ' DM 5.0 — по ДВС BYD472QC 74 кВт и мотору 120 кВт (как у 2025 智驾版, autohome).'
        if k[0] == 2025 and k[1] == '15.8':
            r['notes'] += ' В группу входят 120KM и 128KM (одна силовая установка); у 128KM CLTC 128 / WLTC 100 км (xchuxing).'
        if dm_gen(k) != 'DM 5.0':
            r['notes'] += ' known_issues не перенесены: отзывы в _issues относятся к DM 5.0 (2025–2026).'
    run(6397, 'byd_qin-plus-dm-i', dict(model='BYD Qin Plus DM-i', model_cn='秦PLUS DM-i', hybrid_system='BYD DM-i (EHS)'),
        lambda k: f"{lab.get(k[0], str(k[0]) + '款')}; {dm_gen(k)}",
        issues=lambda k: bind('byd_qin-plus-dm5', k) if dm_gen(k) == 'DM 5.0' else [],
        src_fn=dm_sources, ranges=ranges, extra=extra)

def destroyer():
    tmpl = json.load(open(os.path.join(CAT, 'byd_destroyer-05_2025_dm-i-120km.json'), encoding='utf-8'))['known_issues']
    def iss(k):
        return [dict(i, review_car='Destroyer 05, DM-i 18.3 kWh / 145 кВт (из эталонной записи)') for i in tmpl] if (k[1] == '18.3' and k[2] == '145') else []
    def extra(k, r, b):
        if not (k[1] == '18.3' and k[2] == '145'):
            r['notes'] += ' known_issues не перенесены: эталонные отзывы — по версии 18.3 kWh / мотор 145 кВт.'
    run(6675, 'byd_destroyer-05', dict(model='BYD Destroyer 05', model_cn='驱逐舰05', hybrid_system='BYD DM-i (EHS)',
                                       aliases=['Chazor', 'King', 'Seal 5 DM-i']),
        lambda k: f"{k[0]}款; {dm_gen(k)} (ДВС {e(k)} 81 кВт)", issues=iss, extra=extra)

def leopard7():
    run(7682, 'byd_leopard-7', dict(model='BYD Leopard 7 PHEV', model_cn='方程豹 钛7 PHEV', aliases=['Fangchengbao Tai 7', 'Leopard Ti7'],
                                    hybrid_system=lambda k: 'BYD PHEV, 1.5T BYD472ZQB' + (' + 2 мотора' if '四驱' in (k[5] or '') else ' + 1 мотор')),
        lambda k: {2025: '2025款 (с 09.2025)', 2026: '2026款 (с 08.2026)'}[k[0]] + '; 1.5T BYD472ZQB 115 кВт',
        issues=lambda k: bind('byd_leopard-7', k) if (k[0] == 2025 and k[1] == '35.6') else [],
        extra=lambda k, r, b: None if (k[0] == 2025 and k[1] == '35.6') else r.__setitem__('notes', r['notes'] + ' known_issues не перенесены: отзывы — по версиям 2025 с 35.6 kWh.'))

def qiyuan_a05():
    def lab(k):
        return ('2024款 (запуск 10.2023; 真香版 с 04.2024); ДВС JL473Q5 81 кВт' if k[0] == 2024
                else '2025款 真香版 (с 10.2024); ДВС JL469Q1 72 кВт')
    def note(k):
        return ('Версия 2024 с ДВС 81 кВт и батареей 18.99 kWh — это и есть данные carnewschina (запуск 2023), которые расходились с sohu 2025.'
                if k[0] == 2024 else '')
    run(7228, 'changan_qiyuan-a05', dict(model='Changan Qiyuan A05', model_cn='长安启源A05', aliases=['Changan Nevo A05'],
                                         hybrid_system='Changan Blue Whale (蓝鲸) hybrid, 1 мотор + E-CVT'),
        lab, issues=lambda k: bind('changan_qiyuan-a05', k), note_fn=note)

def qiyuan_a06():
    run(7686, 'changan_qiyuan-a06', dict(model='Changan Qiyuan A06 EREV', model_cn='长安启源A06 增程版', aliases=['Changan Nevo A06'],
                                         hybrid_system='Changan 增程 (range extender), ДВС только генератор'),
        lambda k: '2026款 增程 (запуск 11.2025)', issues=lambda k: bind('changan_qiyuan-a06-erev', k))

def eado():
    run(5444, 'changan_eado-phev', dict(model='Changan Eado PHEV', model_cn='长安逸动PHEV', hybrid_system='Changan Blue Whale (蓝鲸) hybrid, 1 мотор + E-CVT'),
        lambda k: '2025款 智慧新蓝鲸 (с 03.2025); силовая установка как у Qiyuan A05 2025',
        note_fn=lambda k: 'known_issues: отзывов по Eado PHEV с конкретикой не найдено (_issues/changan_eado-phev.json).')

def cs75():
    def lab(k):
        t = tags_of(TRIMS.get(k, []))
        return f"{k[0]}款{(' ' + '/'.join(t)) if t else ''}; ДВС {e(k)} {k[4]} кВт"
    run(4095, 'changan_cs75', dict(model='Changan CS75 / CS75 PRO', model_cn='长安CS75'), lab,
        note_fn=lambda k: 'known_issues: отзывов именно по CS75/CS75 PRO не найдено (агент нашёл только CS75 PLUS — другая модель).')

def uni_z():
    run(7339, 'changan_uni-z-phev', dict(model='Changan UNI-Z PHEV', model_cn='长安UNI-Z PHEV', hybrid_system='Changan Blue Whale (蓝鲸) hybrid, 1 мотор + E-CVT'),
        lambda k: {2024: '2024款 蓝鲸智电iDD (с 03.2024)', 2025: '2025款 智慧新蓝鲸 (с 02.2025)', 2026: '2026款 智慧新蓝鲸 130km (мотор 160 кВт)'}[k[0]],
        issues=lambda k: bind('changan_uni-z-phev', k) if k[2] == '158' else [])

def cs55():
    def g(k):
        y, code = k[0], e(k)
        if y == 2020: return '1-е поколение, ДВС JL476ZQCD'
        if code == 'JL473ZQ2': return '1-е поколение, 蓝鲸版 (1.5T JL473ZQ2)'
        if y in (2022, 2023): return '第二代 (2-е поколение)'
        if y in (2024, 2025): return '第三代 (3-е поколение)'
        return '第四代 (4-е поколение, 新蓝鲸)'
    gen2 = lambda k: k[0] in (2022, 2023) and e(k) == 'JL473ZQ7'
    rules = {0: lambda k: gen2(k) or k[0] == 2026, 1: lambda k: gen2(k) or k[0] == 2026,
             2: lambda k: (k[0] == 2024 or k[0] == 2026) and '双离合' in (k[7] or ''),
             3: lambda k: gen2(k) or k[0] == 2024, 5: lambda k: gen2(k)}
    run(6091, 'changan_cs55-plus', dict(model='Changan CS55 PLUS', model_cn='长安CS55 PLUS'), lambda k: f"{k[0]}款; {g(k)}; ДВС {e(k)} {k[4]} кВт",
        issues=lambda k: bind('changan_cs55-plus', k, rules))

def cs75_plus():
    def g(k):
        t = tags_of(TRIMS.get(k, []))
        return f"{k[0]}款{(' ' + '/'.join(t)) if t else ' (1-е поколение)'}; ДВС {e(k)} {k[4]} кВт"
    is15 = lambda k: e(k).startswith('JL473') or e(k).startswith('NE15')
    gen4_15 = lambda k: k[0] in (2025, 2026) and e(k) == 'JL473ZQD'
    rules = {0: lambda k: k[0] == 2025 and e(k) == 'JL473ZQD', 1: lambda k: k[0] in (2025, 2026) and is15(k),
             2: lambda k: k[0] == 2025 and e(k) == 'JL473ZQD', 3: lambda k: k[0] == 2025 and e(k) in ('JL473ZQD', 'JL486ZQ5') and k[7] == '8档自动',
             4: lambda k: k[0] == 2025 and e(k) == 'JL473ZQD', 5: lambda k: k[0] in (2025, 2026) and is15(k)}
    run(5823, 'changan_cs75-plus', dict(model='Changan CS75 PLUS', model_cn='长安CS75 PLUS'), g,
        issues=lambda k: bind('changan_cs75-plus', k, rules))

def uni_v():
    is15 = lambda k: e(k).startswith('JL473')
    rules = {0: lambda k: k[0] in (2024, 2025) and is15(k), 1: lambda k: k[0] in (2024, 2025) and is15(k),
             2: lambda k: k[0] == 2024 and is15(k), 3: lambda k: k[0] in (2024, 2025) and is15(k)}
    run(6570, 'changan_uni-v', dict(model='Changan UNI-V', model_cn='长安UNI-V'),
        lambda k: f"{k[0]}款{(' ' + '/'.join(tags_of(TRIMS.get(k, [])))) if tags_of(TRIMS.get(k, [])) else ''}; ДВС {e(k)} {k[4]} кВт",
        issues=lambda k: bind('changan_uni-v', k, rules))

def deepal_s07():
    b215 = lambda k: k[1] == '31.73'; b285 = lambda k: k[1] in ('39.05', '39.06')
    rules = {0: lambda k: k[0] in (2024, 2025) and (b215(k) or b285(k)), 2: lambda k: k[0] == 2024 and b215(k),
             5: lambda k: k[0] == 2024 and (b215(k) or b285(k))}
    run(6970, 'changan_deepal-s07', dict(model='Deepal S07 EREV', model_cn='深蓝S07 增程版', aliases=['Changan Deepal S07', 'Deepal S7'],
                                        hybrid_system='Changan 增程 (range extender), ДВС только генератор'),
        lambda k: f"{k[0]}款; генератор {e(k)} {k[4]} кВт" + ('; 华为乾崑 ADS' if k[0] == 2026 else ''),
        issues=lambda k: bind('changan_deepal-s07-erev', k, rules))

def q07():
    b215 = lambda k: k[1] == '31.7'
    run(7596, 'changan_qiyuan-q07', dict(model='Changan Qiyuan Q07', model_cn='长安启源Q07', aliases=['Changan Nevo Q07'], hybrid_system='Changan PHEV, 1 мотор + E-CVT'),
        lambda k: f"2025款 (с 04.2025); ДВС {e(k)} {k[4]} кВт" + (' (турбо, 旗舰)' if e(k) == 'JL469ZQ1' else ''),
        issues=lambda k: bind('changan_qiyuan-q07', k, {1: b215, 5: b215}),
        note_fn=lambda k: 'Тип: autohome называет Q07 增程, sohu — 插电式混合动力 (E-CVT); взято sohu.')

def q06():
    run(8014, 'changan_nevo-q06', dict(model='Changan Nevo Q06 EREV', model_cn='长安启源Q06 增程版', aliases=['Changan Qiyuan Q06', 'Q06 R'],
                                       hybrid_system='Changan 增程 (range extender), ДВС только генератор'),
        lambda k: '2027款 (старт продаж 2026-09-23)', note_fn=lambda k: 'known_issues: отзывов с конкретикой ещё нет (около месяца эксплуатации).')

def zeekr_x():
    run(7010, 'zeekr_x', dict(model='Zeekr X', model_cn='极氪X'),
        lambda k: (f"{k[0]}款 дорестайлинг" if k[0] < 2026 else '2026款 рестайлинг (с 11.2025)') + '; SEA2',
        issues=lambda k: bind('zeekr_x', k), src_fn=lambda k: {'generation': 'https://en.wikipedia.org/wiki/Zeekr_X'})

def s09():
    run(7599, 'changan_deepal-s09', dict(model='Deepal S09 EREV', model_cn='深蓝S09', aliases=['Changan Deepal S09'],
                                        hybrid_system='Changan 增程 (range extender, 1.5T)'),
        lambda k: f"{k[0]}款; генератор JL469ZQ1 1.5T 110 кВт" + ('; 超长续航' if k[1] == '53.49' else ''),
        issues=lambda k: bind('changan_deepal-s09', k, {2: lambda k: k[0] == 2025 and k[1] == '40.18'}))

def lynk900():
    run(7586, 'lynk-co_900', dict(model='Lynk & Co 900', model_cn='领克900', hybrid_system=lambda k: f"Lynk PHEV, {'1.5T' if '15' in e(k) else '2.0T'} + 2 мотора, 3-ступ. DHT"),
        lambda k: f"{k[0]}款; ДВС {e(k)} {k[4]} кВт", issues=lambda k: bind('lynk_900', k))

def zeekr001():
    run(6463, 'zeekr_001', dict(model='Zeekr 001', model_cn='极氪001'),
        lambda k: f"{k[0]}款" + {2021: ' (запуск)', 2023: '', 2024: ' (рестайлинг 2024)', 2025: '', 2026: ' (2026款, 103/95 kWh)'}.get(k[0], ''),
        issues=lambda k: bind('zeekr_001', k, {5: lambda k: k[0] == 2025 and '四驱' in (k[5] or '')}),
        note_fn=lambda k: 'Поколение/рестайлинг указаны по годам sohu; границы рестайлинга источником не подтверждены.')

def zeekr8x():
    run(7803, 'zeekr_8x', dict(model='Zeekr 8X', model_cn='极氪8X', hybrid_system='Zeekr PHEV, 2.0T + моторы, 1-ступ. DHT'),
        lambda k: '2026款 (запуск 04.2026); ДВС DHE20-PFZ 2.0T 205 кВт', issues=lambda k: bind('zeekr_8x', k))

def corolla_cn():
    run(7038, 'toyota_corolla-cross-cn', dict(model='Toyota Corolla Cross Hybrid (Китай, 卡罗拉锐放双擎)', model_cn='卡罗拉锐放双擎',
                                              hybrid_system='Toyota hybrid 2.0, 1 мотор + E-CVT', aliases=['Toyota Frontlander (锋兰达, близнец GAC Toyota)']),
        lambda k: f"{k[0]}款; 2.0 M20G {k[4]} кВт + мотор 83 кВт",
        issues=lambda k: bind('toyota_corolla-cross-hev', k))

MODELS = dict(qin=qin_plus, destroyer=destroyer, leopard=leopard7, a05=qiyuan_a05, a06=qiyuan_a06, eado=eado, cs75=cs75,
              uniz=uni_z, cs55=cs55, cs75plus=cs75_plus, univ=uni_v, s07=deepal_s07, q07=q07, q06=q06, zeekrx=zeekr_x,
              s09=s09, lynk=lynk900, z001=zeekr001, z8x=zeekr8x, corolla=corolla_cn)

# trims per key for tag-based labels: patch groups() to remember trim names
import years as _y
_orig = _y.groups
def _groups(model, ymin=2020, ymax=2027):
    g = _orig(model, ymin, ymax)
    for k, v in g.items(): TRIMS[k] = [x['trim_name_zh'] for x in v]
    return g
import yearbuild as _yb
_yb.groups = _groups

if __name__ == '__main__':
    for name in (sys.argv[1:] or MODELS):
        print('####', name); MODELS[name]()
