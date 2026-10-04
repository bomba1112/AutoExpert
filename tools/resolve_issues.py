"""known_issues_resolved = model issues + issues of its components (inherited ones carry "origin")."""
import glob, json, os
import components as C
SUB = {'engine': 'engines', 'transmission': 'transmissions', 'hybrid_system': 'hybrid_systems'}
KIND_RU = {'engine': 'двигатель', 'transmission': 'коробка', 'hybrid_system': 'гибридная система'}

def comp_label(kind, c):
    if kind == 'engine': return (c.get('codes') or [c['id']])[0]
    return c.get('marketing_name') or c.get('name') or c['id']

def main():
    cache = {}; report = []
    for p in sorted(glob.glob(os.path.join(C.ROOT, '*.json'))):
        d = C.L(p); slug = os.path.basename(p)[:-5]
        res = [dict(i, origin='модель') for i in d.get('known_issues') or []]
        seen = {(i['source'], i['text']) for i in res}; inh = 0
        for kind, cid in (d.get('components') or {}).items():
            if not cid: continue
            key = (kind, cid)
            if key not in cache: cache[key] = C.L(os.path.join(C.COMP, SUB[kind], cid + '.json'))
            c = cache[key]
            for i in c.get('known_issues') or []:
                k = (i['source'], i['text'])
                if k in seen: continue
                seen.add(k)
                own = d['model'] in (i.get('reported_in') or [])
                src_models = ', '.join(i.get('reported_in') or []) or 'неизвестно'
                res.append({'text': i['text'], 'source': i['source'], **({'more_sources': i['more_sources']} if i.get('more_sources') else {}),
                            'scope': i.get('scope', kind), 'component': cid,
                            'origin': f"{KIND_RU[kind]} {comp_label(kind, c)}, отзыв по {src_models}" + (' (эта модель)' if own else '')})
                if not own: inh += 1
        d['known_issues_resolved'] = res
        C.W(p, d)
        report.append((slug, len(d.get('known_issues') or []), len(res), inh))
    return report

if __name__ == '__main__':
    for slug, own, tot, inh in main():
        if inh: print(f'{slug}: своих {own}, всего {tot}, унаследовано от других моделей {inh}')
