"""Build per-year/powertrain records for a sohu model and merge with existing catalog records.
Usage from a catalog/_build/y_*.py script:
    from yearbuild import build_model
    build_model(model_id, meta=..., generation=fn(key)->dict, issues=fn(key)->(issue_key|None), ...)
"""
import glob, json, os
from years import groups
from rec import rec, miit_fuel, chg
from build import save, hp, CAT, ORDER

def slugify(prefix, key):
    y, bat, mkw, ecode, ekw, drive, ptype, gb = key
    parts = [str(y)]
    if bat: parts.append(f"{bat}kwh")
    if mkw: parts.append(f"{mkw}kw")
    if not bat and ecode: parts.append(ecode.lower().replace(' ', ''))
    if not bat and not mkw and gb: parts.append(GB_SLUG(gb))
    if drive and '四驱' in drive: parts.append('awd')
    return f"{prefix}_{'_'.join([parts[0], '-'.join(parts[1:])])}"

def GB_SLUG(gb):
    import re
    n = re.match(r'(\d+)', gb or ''); n = n.group(1) if n else ''
    for k, v in (('双离合', 'dct'), ('手动', 'mt'), ('手自一体', 'at'), ('自动', 'at'), ('CVT', 'cvt'), ('DHT', 'dht')):
        if k in (gb or ''): return n + v
    return 'gb'

def transmission_of(gb):
    gb = gb or ''
    if 'ECVT' in gb: return 'E-CVT'
    if '单速' in gb: return 'Редуктор 1 ст.'
    if 'DHT' in gb: return gb.replace('档', '-ступ. ')
    s = GB_SLUG(gb)
    return {'dct': 'DCT', 'mt': 'MT', 'at': 'AT', 'cvt': 'CVT'}.get(s.lstrip('0123456789'), gb) if s != 'gb' else gb or None

def ptype_of(pt):
    pt = pt or ''
    for k, v in (('插电', 'PHEV_series_parallel'), ('增程', 'EREV'), ('纯电', 'BEV'), ('油电混合', 'HEV'), ('汽油', 'ICE')):
        if k in pt: return v
    return pt or None

def ranges_wa(ids):
    from sohu import pk, table
    from build import num
    d = pk(','.join(map(str, ids))); rows = dict(table(d, True))
    def rng(k):
        v = [num(x) for x in rows.get(k, []) if num(x) is not None]
        if not v: return None
        return v[0] if len(ids) == 1 else {'min': min(v), 'max': max(v)}
    return rng('车身/整备质量(kg)'), rng('车辆基本/官方0-100加速(s)')

def existing_by_trim():
    m = {}
    orig = set(open(os.path.join(os.path.dirname(__file__), 'original26.txt')).read().split())
    for p in glob.glob(os.path.join(CAT, '*.json')):
        if os.path.basename(p)[:-5] not in orig: continue
        d = json.load(open(p, encoding='utf-8'))
        tid = (d.get('sohu_trim') or {}).get('trim_id')
        if tid and not d.get('listing_copy'): m[int(tid)] = (p, d)
    return m

def years_in(txt):
    import re
    ys = set()
    for a, b in re.findall(r'(20\d\d)\s*[–-]\s*(20\d\d)', txt or ''):
        ys |= set(range(int(a), int(b) + 1))
    ys |= {int(y) for y in re.findall(r'20\d\d', txt or '')}
    return ys

def bind(issue_key, key, rules=None, default=True):
    """rules: {idx: predicate(key)}; issues without a rule use year-from-review_car match when default=True."""
    p = os.path.join(CAT, '_issues', issue_key + '.json')
    if not os.path.exists(p): return []
    out = []
    for n, i in enumerate(json.load(open(p, encoding='utf-8')).get('issues', [])):
        ok = rules[n](key) if rules and n in rules else (default and key[0] in years_in(i.get('review_car')))
        if ok:
            out.append({'text': i['text'], 'source': i['sources'][0],
                        **({'more_sources': i['sources'][1:]} if len(i['sources']) > 1 else {}),
                        **({'review_car': i['review_car']} if i.get('review_car') else {})})
    return out

def issues_from(key, filt=None):
    p = os.path.join(CAT, '_issues', key + '.json')
    if not os.path.exists(p): return []
    out = []
    for i in json.load(open(p, encoding='utf-8')).get('issues', []):
        if filt and not filt(i): continue
        out.append({'text': i['text'], 'source': i['sources'][0],
                    **({'more_sources': i['sources'][1:]} if len(i['sources']) > 1 else {}),
                    **({'review_car': i['review_car']} if i.get('review_car') else {})})
    return out

KEEP = ('listing_values', 'closest_official', 'turbo_listings', 'verification', 'aliases', 'twin_models')

def build_model(model_id, prefix, meta, gen, issues=None, ranges=None, extra=None, ymin=2020, ymax=2027, dry=False):
    """meta: dict(model, model_cn, powertrain_type|fn, hybrid_system|fn, transmission|fn)
       gen(key)->{'generation': str, 'platform': str|None, 'sources': {...}, 'notes': str}
       issues(key)->list of issue dicts; ranges(key, b)->dict; extra(key, r, b)->None (mutate)"""
    ex = existing_by_trim(); made = []; used = set()
    for key, trims in groups(model_id, ymin, ymax).items():
        ids = [t['trim_id'] for t in trims]
        g = gen(key)
        f = lambda v: v(key) if callable(v) else v
        r, b = rec(ids, 'x', model=meta['model'], model_cn=meta['model_cn'], my=key[0],
                   trim_key=g.get('trim_key') or f"{key[0]}款 {trims[0]['trim_name_zh'].strip()}",
                   status_china=('в продаже' if any(t.get('flag_status_product') == 1 for t in trims) else 'снята с продажи') + ' (sohu)',
                   powertrain_type=f(meta['powertrain_type']) if meta.get('powertrain_type') else ptype_of(key[6]),
                   hybrid_system=f(meta.get('hybrid_system')),
                   platform=g.get('platform'), transmission=f(meta['transmission']) if meta.get('transmission') else transmission_of(key[7]),
                   listing={'url': None}, ranges=(ranges(key, None) if ranges else None), fuel=None, charging=None,
                   aliases=meta.get('aliases', ()), notes='', verification='verified')
        r['fuel_l_100km'] = miit_fuel(b) if b.get('battery') else r['fuel_l_100km']
        if b.get('battery'): r['charging'] = chg(b)
        if ranges: r['ev_range_km'] = ranges(key, b)
        r['generation'] = g['generation']
        r['trims'] = [f"{t['trim_name_zh'].strip()} (sohu {t['trim_id']}, {t['date_launch']}, {t['price_guide']}万)" for t in trims]
        r['sources'].update(g.get('sources', {}))
        r['curb_weight_kg'], r['accel_0_100_s'] = ranges_wa(ids)
        r['notes'] = (g.get('notes', '') + (' Масса и разгон — диапазон по комплектациям группы; прочие поля — по sohu ' + str(ids[0]) + '.' if len(ids) > 1 else '')).strip()
        r['listing_values'] = None; r['turbo_listings'] = []
        r['known_issues'] = issues(key) if issues else []
        core = [r['curb_weight_kg'], (r['engine'] or {}).get('power_kw') if r['powertrain_type'] != 'BEV' else 1]
        if r['battery']: core += [r['battery']['kwh'], (r['motor'] or {}).get('power_kw')]
        r['verification'] = 'verified' if all(c is not None for c in core) else 'partial'
        if extra: extra(key, r, b)
        # merge with existing record (matched by sohu trim id)
        hit = next((ex[i] for i in ids if i in ex), None)
        if hit:
            p, old = hit; slug = os.path.basename(p)[:-5]
            for k in KEEP:
                if old.get(k) is not None: r[k] = old[k]
            r['notes'] = r['notes']
            if old.get('known_issues') and not r['known_issues']: r['known_issues'] = old['known_issues']
            elif old.get('known_issues'):
                seen = {i['source'] + i['text'] for i in r['known_issues']}
                r['known_issues'] = [i for i in old['known_issues'] if i['source'] + i['text'] not in seen] + r['known_issues']
            r['buyer_checks'] = old.get('buyer_checks', []) or r['buyer_checks']
            on = old.get('notes', '').split(' | ')[0]
            r['notes'] = on + (' | ' + r['notes'] if r['notes'] else '')
            r['sources'] = {**r['sources'], **old.get('sources', {})}
            for k in ('trim_key', 'hybrid_system', 'platform', 'transmission', 'ev_range_km', 'charging', 'fuel_l_100km',
                      'status_china', 'engine', 'motor', 'battery', 'match_fingerprint', 'model', 'model_cn'):
                if old.get(k) is not None: r[k] = old[k]
            r['sohu_trim'] = old.get('sohu_trim', r['sohu_trim'])
            if old.get('my') != r['my'] and r.get('listing_values') is not None and 'year' not in r['listing_values']:
                r['listing_values'] = {**r['listing_values'], 'year': old.get('my')}
                r['notes'] += ' Год в объявлении %s, официальный 年款 — %s.' % (old.get('my'), r['my'])
        else:
            slug = slugify(prefix, key)
            if slug in used and key[3]:
                slug += '-' + key[3].lower().replace(' ', '')
        used.add(slug)
        made.append((slug, key, r, bool(hit)))
        if not dry:
            save(slug, r, force=True)
    return made
