"""write issue json: python wj.py <spec.json-ish python literal file>; AK(id) expands to autohome url"""
import json, sys, os, re
src = open(sys.argv[1], encoding='utf-8').read()
def AK(i): return f'https://k.autohome.com.cn/detail/view_{i}.html' if not i.startswith('http') else i
d = eval(src, {'AK': AK})
raw = ''.join(open(f, encoding='utf-8').read() for f in d.pop('_raw', []))
def full(i):
    if i.startswith('http') or len(i) >= 26: return i
    m = sorted(set(re.findall(r'view_(' + re.escape(i) + r'[0-9a-z]*)\.html', raw)))
    assert len(m) == 1, (i, m); return m[0]
for it in d['issues']:
    it['sources'] = [AK(full(s)) for s in it['sources']]
    it.setdefault('count', len(it['sources']))
out = f"C:/Users/jalil/samr/catalog/_issues/{d['key']}.json"
if os.path.exists(out) and 'force' not in sys.argv: print('EXISTS', out); sys.exit()
json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote', out, len(d['issues']))
