"""Build catalog records from sohu config tables.
from build import base, save   -> base(trim_id) returns dict pre-filled from sohu; save(slug, rec) writes catalog/<slug>.json (skips if exists)
"""
import json, os, re
from sohu import pk, table
CAT = os.path.join(os.path.dirname(__file__), '..', 'catalog')
KW2HP = 1.35962  # metric hp (PS), as turbo.az and Chinese tables use

def num(v):
    if v is None: return None
    m = re.search(r'-?\d+(\.\d+)?', str(v).replace(',', ''))
    if not m: return None
    x = float(m.group()); return int(x) if x.is_integer() else x

def hp(kw):
    return round(kw * KW2HP) if kw else None

def raw(trim_id):
    d = pk(str(trim_id))
    return d[0]['trim_info'], {k: v[0] for k, v in table(d, True)}

def g(r, *names):
    for n in names:
        for k, v in r.items():
            if k.split('/', 1)[1] == n and v not in ('', '-', '--', '---', '待查'): return v
    return None

def api(ids): return f'https://portal.auto.sohu.com/aggr/model/trims/pk?trim_ids={ids}&city_code=110000'

def base(trim_id):
    ti, r = raw(trim_id)
    eng_kw = num(g(r, '发动机/最大功率(kW/rpm)', '最大功率(kW/rpm)'))
    fk, rk = num(g(r, '前电动机最大功率(kW)')), num(g(r, '后电动机最大功率(kW)'))
    tk = num(g(r, '电动机总功率(kW)'))
    ft, rt = num(g(r, '前电动机最大扭矩(N·m)')), num(g(r, '后电动机最大扭矩(N·m)'))
    tt = num(g(r, '电动机总扭矩(N·m)'))
    cnt = num(g(r, '电机数'))
    size = g(r, '长x宽x高(mm)')
    L = W = Hh = None
    if size and 'x' in size: L, W, Hh = [num(x) for x in size.split('x')[:3]]
    chem = g(r, '电池种类') or ''
    drive = g(r, '驱动方式') or ''
    out = {
        '_sohu': {'trim_id': ti['trim_id'], 'name': f"{ti['model_name_zh']} {ti['year']}款 {ti['trim_name_zh']}",
                  'price_wan': ti['price_guide'], 'launch': ti['date_launch'], 'status': ti.get('flag_status_product')},
        'engine': None if not eng_kw else {
            'code': g(r, '发动机型号'), 'displacement_cc': num(g(r, '汽缸容积(cc)')),
            'aspiration': {'自然吸气': 'NA', '涡轮增压': 'turbo'}.get(g(r, '进气形式'), g(r, '进气形式')),
            'compression': num(g(r, '压缩比')), 'power_hp': hp(eng_kw), 'power_kw': eng_kw,
            'torque_nm': num(g(r, '发动机/最大扭矩(N·m/rpm)', '最大扭矩(N·m/rpm)'))},
        'motor': None if not tk else {
            'type': 'PMSM' if '永磁' in (g(r, '电机类型') or '') else g(r, '电机类型'),
            'count': cnt, 'power_hp': hp(tk), 'power_kw': tk, 'torque_nm': tt,
            'axle': 'front+rear' if (fk and rk) else ('rear' if rk else 'front'),
            'front_kw': fk, 'rear_kw': rk, 'front_nm': ft, 'rear_nm': rt},
        'system_power_hp': hp(num(g(r, '系统综合功率(kW)'))) if g(r, '系统综合功率(kW)') else None,
        'system_power_kw': num(g(r, '系统综合功率(kW)')),
        'gearbox_cn': g(r, '变速箱类型', '变速箱'),
        'drive': 'AWD' if ('四驱' in drive) else ('RWD' if '后驱' in drive else ('FWD' if '前驱' in drive else drive or None)),
        'battery': {'kwh': num(g(r, '电池容量(kWh)')),
                    'chemistry': 'LFP' if '磷酸铁锂' in chem else ('NCM' if '三元' in chem else (chem or None)),
                    'brand': g(r, '电芯品牌', '电池品牌'), 'supplier': None, 'cooling': g(r, '电池冷却方式')} if g(r, '电池容量(kWh)') else None,
        'miit_range_km': num(g(r, '工信部纯电续航里程(km)', 'CLTC纯电续航里程(km)', '纯电续航里程(km)')),
        'consumption_kwh_100km': num(g(r, '百公里耗电量(kWh/100km)')),
        'fuel_miit': g(r, '工信部油耗(L/100km)(城市/市郊/综合)', 'WLTC综合油耗(L/100km)'),
        'charge_mode': g(r, '充电方式'), 'dc_h': num(g(r, '快充时间(小时)')), 'dc_pct': g(r, '快充电量(%)'),
        'ac_h': num(g(r, '慢充时间(小时)')), 'dc_kw': num(g(r, '最大快充功率(kW)', '快充功率(kW)')),
        'ac_kw': num(g(r, '最大慢充功率(kW)', '慢充功率(kW)')),
        'accel_0_100_s': num(g(r, '官方0-100加速(s)')), 'top_speed_kmh': num(g(r, '官方最高车速(km/h)')),
        'curb_weight_kg': num(g(r, '整备质量(kg)')),
        'dimensions_mm': {'length': L, 'width': W, 'height': Hh, 'wheelbase': num(g(r, '轴距(mm)'))},
        'tank_l': num(g(r, '油箱容积(L)')),
        'gearbox_raw': g(r, '变速箱'), 'power_type': g(r, '动力类型'),
        '_raw': r,
    }
    return out

ORDER = ['model', 'model_cn', 'aliases', 'twin_models', 'my', 'trim_key', 'generation', 'trims', 'status_china', 'powertrain_type',
         'hybrid_system', 'platform', 'engine', 'motor', 'system_power_hp', 'transmission', 'drive', 'battery',
         'ev_range_km', 'consumption_kwh_100km', 'fuel_l_100km', 'charging', 'accel_0_100_s', 'top_speed_kmh',
         'curb_weight_kg', 'dimensions_mm', 'known_issues', 'buyer_checks', 'match_fingerprint', 'listing_values',
         'closest_official', 'turbo_listings', 'sources', 'notes', 'verification']

def save(slug, rec, force=False):
    p = os.path.join(CAT, slug + '.json')
    if os.path.exists(p) and not force:
        print('skip (exists)', slug); return
    out = {k: rec[k] for k in ORDER if k in rec}
    out.update({k: v for k, v in rec.items() if k not in out})
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('saved', slug)

if __name__ == '__main__':
    import sys
    b = base(sys.argv[1]); b.pop('_raw')
    print(json.dumps(b, ensure_ascii=False, indent=1))
