"""Full catalog rebuild, in order:
  1. year/powertrain records from sohu  (catalog/_build/y_byd_song-plus.py, catalog/_build/y_all.py)
  2. sync listing copies (records with "copy_of")
  3. components.py write  -> 4. migrate_issues.py  -> 5. resolve_issues.py
  6. index.csv + auto blocks in REPORT.md
  7. regression check vs. previous run: records / components / issues must not decrease.
  8. translations (tools/i18n.py build): catalog/i18n/{az,en}.json from catalog/i18n/phrases;
     a changed Russian text keeps its old translation as "stale" and is listed as missing
     until the phrases cover it (reported, does not stop the rebuild).
Usage: python tools/rebuild_all.py
"""
import collections, glob, json, os, re, subprocess, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(TOOLS, '..', 'catalog'))
BUILD = os.path.join(ROOT, '_build')
SNAP = os.path.join(BUILD, 'last_rebuild.json')
sys.path.insert(0, TOOLS)
L = lambda p: json.load(open(p, encoding='utf-8'))
def W(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def run(script, *args):
    print(f'\n=== {os.path.relpath(script, os.path.dirname(ROOT))} {" ".join(args)}', flush=True)
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    r = subprocess.run([sys.executable, script, *args], cwd=os.path.dirname(script), env=env, capture_output=True, text=True, encoding='utf-8')
    lines = [l for l in r.stdout.splitlines() if not l.startswith('saved ')]
    print('\n'.join(lines[-15:]))
    if r.returncode != 0:
        print(r.stderr[-3000:]); raise SystemExit(f'step failed: {script}')

def snapshot():
    recs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, '*.json')))
    comps = sorted(os.path.relpath(p, ROOT).replace('\\', '/') for p in glob.glob(os.path.join(ROOT, 'components', '*', '*.json')))
    issues = set(); resolved = 0
    for s in recs:
        d = L(os.path.join(ROOT, s + '.json'))
        issues |= {i['source'] + ' || ' + i['text'] for i in d.get('known_issues') or []}
        resolved += len(d.get('known_issues_resolved') or [])
    for c in comps:
        issues |= {i['source'] + ' || ' + i['text'] for i in L(os.path.join(ROOT, c)).get('known_issues') or []}
    return {'records': recs, 'components': comps, 'issues': sorted(issues), 'resolved_total': resolved}

def sync_copies():
    n = 0
    for p in glob.glob(os.path.join(ROOT, '*.json')):
        d = L(p)
        if not d.get('copy_of'): continue
        b = L(os.path.join(ROOT, d['copy_of'] + '.json'))
        for k in ('generation', 'trims', 'curb_weight_kg', 'accel_0_100_s'):
            d[k] = b.get(k)
        have = {(i['source'], i['text']) for i in d.get('known_issues') or []}
        d['known_issues'] = (d.get('known_issues') or []) + [i for i in b.get('known_issues') or [] if (i['source'], i['text']) not in have]
        W(p, d); n += 1
    print(f'\n=== sync listing copies: {n}')

FAM = [('byd_qin-plus', 'BYD Qin Plus DM-i'), ('byd_qin-plus-dm-i', 'BYD Qin Plus DM-i'), ('byd_destroyer-05', 'BYD Destroyer 05'),
       ('byd_song-plus-dm-i', 'BYD Song Plus DM-i'), ('byd_leopard-7', 'BYD Leopard 7 PHEV'),
       ('changan_qiyuan-a05', 'Changan Qiyuan A05 / Nevo A05'), ('changan_nevo-a05', 'Changan Qiyuan A05 / Nevo A05'),
       ('changan_qiyuan-a06', 'Changan Qiyuan A06 EREV'), ('changan_eado-phev', 'Changan Eado PHEV'),
       ('changan_cs75', 'Changan CS75 / CS75 PRO'), ('changan_cs75-pro', 'Changan CS75 / CS75 PRO'), ('changan_cs75-plus', 'Changan CS75 PLUS'),
       ('changan_uni-z-phev', 'Changan UNI-Z PHEV'), ('changan_cs55-plus', 'Changan CS55 PLUS'), ('changan_uni-v', 'Changan UNI-V'),
       ('changan_deepal-s07', 'Deepal S07 EREV'), ('changan_qiyuan-q07', 'Changan Qiyuan Q07'), ('changan_nevo-q06', 'Changan Nevo Q06 EREV'),
       ('zeekr_x', 'Zeekr X'), ('changan_deepal-s09', 'Deepal S09 EREV'), ('lynk-co_900', 'Lynk & Co 900'), ('zeekr_001', 'Zeekr 001'),
       ('zeekr_8x', 'Zeekr 8X'), ('toyota_corolla-cross-cn', 'Toyota Corolla Cross Hybrid (Китай, 锐放双擎)')]

def coverage():
    names = list(dict.fromkeys(n for _, n in FAM)); cov = {n: collections.Counter() for n in names}; unk = []
    for p in glob.glob(os.path.join(ROOT, '*.json')):
        s = os.path.basename(p)[:-5]; d = L(p)
        if d.get('listing_copy') or s.startswith('toyota_corolla-cross_'): continue
        pre = '_'.join(s.split('_')[:2]); fam = [n for k, n in FAM if k == pre]
        if not fam: unk.append(s); continue
        cov[fam[0]][d['my']] += 1
    years = sorted({y for c in cov.values() for y in c} | set(range(2020, 2027)))
    out = ['| Модель | ' + ' | '.join(map(str, years)) + ' | Записей |', '|---|' + '---|' * len(years) + '---|']
    for n, c in cov.items():
        out.append(f'| {n} | ' + ' | '.join(str(c[y]) if c[y] else '—' for y in years) + f' | {sum(c.values())} |')
    if unk: out.append(f'\nНе отнесены к модели: {", ".join(unk)}')
    return '\n'.join(out)

def totals(rows, snap):
    ver = collections.Counter(r['verification'] for r in rows)
    sohu = sum(1 for r in rows if not r['slug'].startswith('toyota_corolla-cross_')) - sum(
        1 for p in glob.glob(os.path.join(ROOT, '*.json')) if L(p).get('listing_copy'))
    nl = sum(1 for r in rows if r['listing'] == 'да')
    return (f"**Итого {len(rows)} записей** (index.csv): {sohu} из таблиц sohu + копии по объявлениям + Corolla Cross от дилера. "
            f"verified {ver['verified']} · partial {ver['partial']} · mismatch {ver['mismatch']}. "
            f"Привязку к объявлению сохраняют {nl} записей. Компонентов: {len(snap['components'])}. "
            f"Уникальных болячек: {len(snap['issues'])}, в known_issues_resolved всего {snap['resolved_total']}.")

def set_block(text, name, body):
    pat = re.compile(rf'(<!-- AUTO:{name} -->\n).*?(<!-- /AUTO:{name} -->)', re.S)
    if not pat.search(text): raise SystemExit(f'REPORT.md: marker AUTO:{name} not found')
    return pat.sub(lambda m: m.group(1) + body + '\n' + m.group(2), text)

def main():
    before = L(SNAP) if os.path.exists(SNAP) else snapshot()
    run(os.path.join(ROOT, '_build', 'y_byd_song-plus.py'))
    run(os.path.join(ROOT, '_build', 'y_all.py'))
    sync_copies()
    run(os.path.join(TOOLS, 'components.py'), 'write')
    run(os.path.join(TOOLS, 'migrate_issues.py'))
    run(os.path.join(TOOLS, 'resolve_issues.py'))
    import finalize
    rows = finalize.index()
    after = snapshot()
    rp = os.path.join(ROOT, 'REPORT.md'); t = open(rp, encoding='utf-8').read()
    t = set_block(t, 'coverage', coverage()); t = set_block(t, 'totals', totals(rows, after))
    open(rp, 'w', encoding='utf-8').write(t)
    # regression check
    lost = {k: sorted(set(before[k]) - set(after[k])) for k in ('records', 'components', 'issues')}
    print('\n=== check')
    for k in ('records', 'components', 'issues'):
        print(f'{k:11} before {len(before[k]):4}  after {len(after[k]):4}  lost {len(lost[k])}')
    print(f"resolved    before {before['resolved_total']:4}  after {after['resolved_total']:4}")
    bad = any(lost.values()) or after['resolved_total'] < before['resolved_total']
    if bad:
        for k, v in lost.items():
            for x in v: print(f'  LOST {k}: {x}')
        raise SystemExit('REGRESSION: something disappeared — snapshot NOT updated')
    W(SNAP, after)
    print('OK — snapshot updated')
    print('\n=== translations')
    import i18n
    report, errors = i18n.build()
    if errors:
        print(f'TRANSLATIONS: {errors} missing or failing checks — add them to catalog/i18n/phrases')

if __name__ == '__main__':
    main()
