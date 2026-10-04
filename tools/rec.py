"""Assemble a record from base() + manual fields."""
from build import base, api, hp, save
def rec(trim_ids, slug, *, model, model_cn, my, trim_key, status_china, powertrain_type, hybrid_system, platform,
        transmission, listing, ranges=None, fuel=None, charging=None, aliases=(), twins=(), notes='', verification='verified',
        closest=None, fingerprint=None, buyer_checks=(), extra_sources=None, battery_extra=None, engine_extra=None,
        system_power_hp=None, overrides=None, model_url=None):
    ids = ','.join(map(str, trim_ids)) if isinstance(trim_ids, (list, tuple)) else str(trim_ids)
    b = base(ids.split(',')[0]); A = api(ids)
    page = f"https://db.auto.sohu.com/trim_{b['_sohu']['trim_id']}/"
    eng = b['engine']
    if eng and engine_extra: eng.update(engine_extra)
    mot = b['motor']
    bat = b['battery']
    if bat and battery_extra: bat.update(battery_extra)
    r = dict(model=model, model_cn=model_cn, aliases=list(aliases), twin_models=list(twins), my=my, trim_key=trim_key,
             status_china=status_china, powertrain_type=powertrain_type, hybrid_system=hybrid_system, platform=platform,
             engine=eng, motor=mot, system_power_hp=system_power_hp if system_power_hp is not None else b['system_power_hp'],
             transmission=transmission, drive=b['drive'], battery=bat,
             ev_range_km=ranges or ({'NEDC': None, 'WLTC': None, 'CLTC': None, 'MIIT': b['miit_range_km']} if bat else None),
             consumption_kwh_100km=b['consumption_kwh_100km'], fuel_l_100km=fuel,
             charging=charging, accel_0_100_s=b['accel_0_100_s'], top_speed_kmh=b['top_speed_kmh'],
             curb_weight_kg=b['curb_weight_kg'], dimensions_mm=b['dimensions_mm'], known_issues=[],
             buyer_checks=list(buyer_checks),
             match_fingerprint=fingerprint or {'battery_kwh': bat['kwh'] if bat else None,
                                               'hp': hp(mot['power_kw']) if (mot and bat) else (eng['power_hp'] if eng else None)},
             listing_values=listing, turbo_listings=[listing['url']] + listing.get('more', []),
             sources={'config_table': A, 'trim_page': page}, notes=notes, verification=verification)
    r['listing_values'] = {k: v for k, v in listing.items() if k != 'more'}
    if closest: r['closest_official'] = closest
    if extra_sources: r['sources'].update(extra_sources)
    r['sources'].update({k: A for k in ('engine', 'motor', 'battery', 'performance', 'weight', 'dimensions') if k not in r['sources']})
    if overrides:
        for k, v in overrides.items(): r[k] = v
    r['sohu_trim'] = b['_sohu']
    return r, b

def miit_fuel(b):
    v = b.get('fuel_miit')
    if not v: return None
    last = v.split('/')[-1]
    from build import num
    n = num(last)
    return {'value': n, 'cycle': '工信部综合 (с учётом электро)'} if n is not None else None

def chg(b, connector='GB/T', dc=None, dc_kw=None, ac_kw=None, dc_to_80_h=None, ac_full_h=None):
    mode = b.get('charge_mode') or ''
    if dc is None:
        dc = True if (b.get('dc_h') or '快充' in mode) else (False if mode == '慢充' else None)
    return {'connector': connector, 'dc_supported': dc, 'dc_kw': dc_kw or b.get('dc_kw'),
            'dc_to_80_h': dc_to_80_h if dc_to_80_h is not None else b.get('dc_h'),
            'dc_window_pct': b.get('dc_pct'),
            'ac_kw': ac_kw or b.get('ac_kw'), 'ac_full_h': ac_full_h if ac_full_h is not None else b.get('ac_h')}
