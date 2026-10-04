"""sohu.com (搜狐汽车) config-table helper.
  python sohu.py models <brand_id>          list models of a brand
  python sohu.py trims <model_id>           list all trims (incl. discontinued)
  python sohu.py pk <id,id,...> [full]      technical params side by side
"""
import json, re, sys, urllib.request
H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://db.auto.sohu.com/'}
BRANDS = {'byd': 239, 'changan': 242, 'qiyuan': 570, 'deepal': 539, 'zeekr': 513,
          'lynk': 424, 'toyota': 199, 'fcb': 576, 'avatr': 538}
SKIP = ('安全', '驾驶辅助', '外部', '内部', '座椅', '多媒体', '灯光', '玻璃', '空调', '智能',
        '车外', '车内', '选装', '颜色', '舒适', '防盗', '操控', '配置', '车窗')

def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40).read().decode('utf-8', 'ignore')

def models(brand):
    t = fetch(f'https://db.auto.sohu.com/brand_{brand}')
    out = []
    for m in re.finditer(r'model_(\d+)" class="brand-list-item--link">(.{0,900}?)参数', t, re.S):
        n = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m.group(2))).strip()
        if (m.group(1), n) not in out: out.append((m.group(1), n))
    return out

def trims(model):
    t = fetch(f'https://db.auto.sohu.com/model_{model}')
    ids = list(dict.fromkeys(re.findall(r'trim_(\d+)', t)))
    out = []
    for i in range(0, len(ids), 10):
        for x in pk(','.join(ids[i:i + 10])):
            ti = x['trim_info']
            out.append((ti['trim_id'], ti['year'], ti['trim_name_zh'], f"{ti['price_guide']}万", ti['date_launch']))
    return out

def pk(ids):
    return json.loads(fetch(f'https://portal.auto.sohu.com/aggr/model/trims/pk?trim_ids={ids}&city_code=110000'))

def table(d, full=False):
    rows, order = {}, []
    for t in d:
        for c in t['config']:
            if not full and any(s in c['category_name'] for s in SKIP): continue
            def walk(l, p=''):
                for x in l or []:
                    k = c['category_name'][:4] + '/' + p + x['name']
                    if k not in rows: rows[k] = [''] * len(d); order.append(k)
                    rows[k][d.index(t)] = str(x['value'])
                    walk(x.get('child_config_list'), x['name'] + '>')
            walk(c['config_list'])
    return [(k, rows[k]) for k in order if not all(v in ('', '-', 'None', '--', '---') for v in rows[k])]

if __name__ == '__main__':
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == 'models':
        for m in models(BRANDS.get(arg, arg)): print(*m)
    elif cmd == 'trims':
        for m in trims(arg): print(*m)
    elif cmd == 'pk':
        d = pk(arg)
        print(' || '.join(f"{t['trim_info']['trim_id']} {t['trim_info']['model_name_zh']} {t['trim_info']['year']} {t['trim_info']['trim_name_zh']} {t['trim_info']['price_guide']}万 {t['trim_info']['date_launch']}" for t in d))
        for k, v in table(d, len(sys.argv) > 3): print(k, '=', ' | '.join(v))
