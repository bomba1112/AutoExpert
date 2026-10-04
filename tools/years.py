"""Group all sohu trims of a model by (year, powertrain key).
  python years.py <model_id> [ymin ymax]
"""
import json, sys
from sohu import fetch, pk, table
import re

def all_trims(model):
    t = fetch(f'https://db.auto.sohu.com/model_{model}')
    ids = list(dict.fromkeys(re.findall(r'trim_(\d+)', t)))
    out = []
    for i in range(0, len(ids), 10):
        out += pk(','.join(ids[i:i + 10]))
    return out

def val(tbl, *names):
    for n in names:
        for k, v in tbl:
            if k.split('/', 1)[1] == n and v[0].strip() not in ('', '-', '--', '---', '待查'): return v[0].strip()
    return None

def key_of(t):
    tbl = table([t], True)
    return (t['trim_info']['year'],
            val(tbl, '电池容量(kWh)'), val(tbl, '电动机总功率(kW)'), val(tbl, '发动机型号'),
            val(tbl, '最大功率(kW/rpm)'), val(tbl, '驱动方式'), val(tbl, '动力类型'), val(tbl, '变速箱'))

def groups(model, ymin=2020, ymax=2027):
    g = {}
    for t in all_trims(model):
        y = t['trim_info']['year']
        if not (ymin <= y <= ymax): continue
        g.setdefault(key_of(t), []).append(t['trim_info'])
    return dict(sorted(g.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), str(kv[0][2]))))

if __name__ == '__main__':
    m = sys.argv[1]; a = sys.argv[2:]
    for k, v in groups(m, *(map(int, a) if a else ())).items():
        print(k, '|', '; '.join(f"{x['trim_id']} {x['trim_name_zh'].strip()} ({x['date_launch']})" for x in v))
