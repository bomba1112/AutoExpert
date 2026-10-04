"""Tag every known_issue with scope; move clear engine/transmission/hybrid_system issues into component files.
Scopes come from catalog/_build/issue_scopes.json (manual classification, keyed by source+text). Idempotent."""
import glob, json, os
import components as C
ROOT = C.ROOT
SC = {(u['source'], u['text']): u for u in json.load(open(os.path.join(ROOT, '_build', 'issue_scopes.json'), encoding='utf-8'))}
SUB = {'engine': 'engines', 'transmission': 'transmissions', 'hybrid_system': 'hybrid_systems'}

def main():
    C.write()                     # components field + component files (used_in rebuilt, existing issues kept)
    bucket = {}                   # (kind, cid) -> {(source,text): issue}
    stats = {'moved': 0, 'kept_no_component': 0, 'kept_doubt': 0, 'tagged': 0}
    for p in sorted(glob.glob(os.path.join(ROOT, '*.json'))):
        d = C.L(p); comp = d.get('components') or {}; keep = []
        for i in d.get('known_issues') or []:
            u = SC.get((i['source'], i['text']))
            if not u:
                raise SystemExit(f'no scope for issue in {p}: {i["text"][:60]}')
            i['scope'] = u['scope']; stats['tagged'] += 1
            if u['move'] and comp.get(u['scope']):
                b = bucket.setdefault((u['scope'], comp[u['scope']]), {})
                e = b.setdefault((i['source'], i['text']), {'text': i['text'], 'source': i['source'], 'more_sources': [],
                                                           'scope': u['scope'], 'review_car': i.get('review_car'), 'reported_in': []})
                for s in i.get('more_sources', []):
                    if s not in e['more_sources'] and s != e['source']: e['more_sources'].append(s)
                if d['model'] not in e['reported_in']: e['reported_in'].append(d['model'])
                if u.get('why'): e['scope_note'] = u['why']
                stats['moved'] += 1
                continue
            if u['scope'] in SUB:
                if u['move']:
                    i['scope_note'] = 'агрегатная проблема, но компонент для этой записи не определён — оставлено в модели'; stats['kept_no_component'] += 1
                else:
                    i['scope_note'] = 'оставлено в модели: ' + (u.get('why') or 'сомнение'); stats['kept_doubt'] += 1
            keep.append(i)
        d['known_issues'] = keep
        C.W(p, d)
    for (kind, cid), issues in bucket.items():
        p = os.path.join(C.COMP, SUB[kind], cid + '.json'); c = C.L(p)
        have = {(x['source'], x['text']): x for x in c.get('known_issues') or []}
        for k, e in issues.items():
            if k in have:
                h = have[k]
                for s in e['more_sources']:
                    if s not in h.setdefault('more_sources', []): h['more_sources'].append(s)
                for m in e['reported_in']:
                    if m not in h.setdefault('reported_in', []): h['reported_in'].append(m)
            else:
                have[k] = e
        for x in have.values():
            if not x.get('more_sources'): x.pop('more_sources', None)
        c['known_issues'] = list(have.values())
        C.W(p, c)
    print(stats, {f'{k}:{c}': len(v) for (k, c), v in bucket.items()})

if __name__ == '__main__':
    main()
