"""Merge _issues into records (only if record has no known_issues) and build index.csv."""
import csv, glob, json, os
CAT = os.path.join(os.path.dirname(__file__), '..', 'catalog')
ISSUE_MAP = {
    'changan_qiyuan-a05_2025_70': 'changan_qiyuan-a05', 'changan_nevo-a05_2025_145': 'changan_qiyuan-a05',
    'changan_qiyuan-a06_2026_erev-240': 'changan_qiyuan-a06-erev', 'changan_qiyuan-a06r_2025_erev-240': 'changan_qiyuan-a06-erev',
    'changan_eado-phev_2025_145km': 'changan_eado-phev',  # cs75-pro: issues are CS75 PLUS data, not merged
    'changan_uni-z-phev_2025_125km': 'changan_uni-z-phev', 'changan_cs55-plus_2026_1.5t-dct': 'changan_cs55-plus',
    'changan_cs75-plus_2026_1.5t-8at': 'changan_cs75-plus', 'changan_uni-v_2026_1.5t-dct': 'changan_uni-v',
    'byd_qin-plus_2025_dm5-120km': 'byd_qin-plus-dm5', 'byd_song-plus-dm-i_2024_110km': 'byd_song-plus-dm-i',
    'changan_deepal-s07_2025_erev-215': 'changan_deepal-s07-erev', 'changan_deepal-s07_2025_erev-285': 'changan_deepal-s07-erev',
    'changan_qiyuan-q07_2025_145': 'changan_qiyuan-q07', 'changan_qiyuan-q07_2026_145': 'changan_qiyuan-q07',
    # toyota: issues are Chinese 1.8 HEV, not merged
    'changan_nevo-q06_2026_erev': 'changan_nevo-q06',
    'zeekr_x_2026_rwd-200kw': 'zeekr_x', 'byd_leopard-7_2025_phev-4wd-190km': 'byd_leopard-7',
    'changan_deepal-s09_2025_erev-4wd': 'changan_deepal-s09', 'lynk-co_900_2026_1.5t-phev': 'lynk_900',
    'zeekr_001_2026_103kwh-awd': 'zeekr_001', 'zeekr_8x_2026_55kwh': 'zeekr_8x',
}
TYPE_RU = {'ICE': 'ДВС', 'HEV': 'HEV', 'PHEV_series_parallel': 'PHEV', 'PHEV_parallel': 'PHEV', 'EREV': 'EREV', 'BEV': 'BEV'}

def merge():
    for slug, key in ISSUE_MAP.items():
        p, ip = os.path.join(CAT, slug + '.json'), os.path.join(CAT, '_issues', key + '.json')
        if not (os.path.exists(p) and os.path.exists(ip)): continue
        d = json.load(open(p, encoding='utf-8'))
        if d.get('known_issues'): continue
        iss = json.load(open(ip, encoding='utf-8')).get('issues', [])
        d['known_issues'] = [{'text': i['text'], 'source': i['sources'][0], **({'more_sources': i['sources'][1:]} if len(i['sources']) > 1 else {}),
                              **({'review_car': i['review_car']} if i.get('review_car') else {})} for i in iss]
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def index():
    rows = []
    for p in sorted(glob.glob(os.path.join(CAT, '*.json'))):
        d = json.load(open(p, encoding='utf-8')); slug = os.path.basename(p)[:-5]
        lv = d.get('listing_values') or {}
        fp = d.get('match_fingerprint')
        hp_off = '/'.join(dict.fromkeys(str(x.get('hp')) for x in fp)) if isinstance(fp, list) else (
            '/'.join(map(str, fp['hp'])) if isinstance(fp.get('hp'), list) else fp.get('hp'))
        bat = (d.get('battery') or {}).get('kwh')
        w, a = d.get('curb_weight_kg'), d.get('accel_0_100_s')
        fmt = lambda v: (f"{v['min']}-{v['max']}" if v['min'] != v['max'] else v['min']) if isinstance(v, dict) else ('' if v is None else v)
        rows.append({'slug': slug, 'model': d['model'], 'year': d['my'], 'trim': d.get('trim_key'), 'generation': d.get('generation') or '',
                     'trims_n': len(d.get('trims') or []),
                     'type': TYPE_RU.get(d['powertrain_type'], d['powertrain_type']), 'battery_kwh': bat if bat is not None else '',
                     'hp_official': hp_off, 'hp_listing': lv.get('hp', ''), 'battery_listing': lv.get('battery_kwh') if lv.get('battery_kwh') is not None else '',
                     'weight_kg': fmt(w), 'accel_0_100_s': fmt(a), 'listing': 'да' if lv.get('url') else '',
                     'known_issues': len(d.get('known_issues') or []),
                     'issues_resolved': len(d.get('known_issues_resolved') or []),
                     'engine_comp': (d.get('components') or {}).get('engine') or '',
                     'transmission_comp': (d.get('components') or {}).get('transmission') or '',
                     'hybrid_comp': (d.get('components') or {}).get('hybrid_system') or '',
                     'verification': d['verification']})
    with open(os.path.join(CAT, 'index.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows

if __name__ == '__main__':
    import sys
    if 'merge' in sys.argv: merge()
    for r in index(): print(r['slug'], r['type'], r['battery_kwh'], r['hp_official'], r['hp_listing'], r['known_issues'], r['verification'])
