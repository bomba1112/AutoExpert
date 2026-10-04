"""compact view of akb.py full output: python akview.py file [badlen]"""
import re, sys
t = open(sys.argv[1], encoding='utf-8').read(); L = int(sys.argv[2]) if len(sys.argv) > 2 else 260
NEG = re.compile(r'没有|没遇到|无故障|还没|未出现|不卡顿|无卡顿|减少卡顿|不会卡|暂无|从未|零故障|目前没|无异响|没出现|没啥')
for blk in t.split('\n== ')[1:]:
    lines = blk.split('\n'); h = lines[0].split(' | ')
    sid = h[0].split('view_')[1][:14] if 'view_' in h[0] else h[0]
    bad = ''; kws = []
    for l in lines[1:]:
        if l.startswith('  [最不满意]'): bad = l[10:].strip()
        elif l.startswith('  [kw]'):
            s = l[8:-3]
            if NEG.search(s) or s[60:100] in bad: continue
            kws.append(s[30:150])
    tags = sorted(set(re.findall(r'((?:车身外观|行驶过程|功能操作|电子设备|座椅|空调系统|内饰|动力系统|驾驶辅助)-[^ \-]+-[^ ]+)', blk)))
    print(f"{sid}|{h[1].strip()}|{h[3].strip()}|{h[4].strip()}: {bad[:L]}")
    for k in kws[:4]: print('   kw:', k)
    if tags: print('   tags:', '; '.join(tags))
