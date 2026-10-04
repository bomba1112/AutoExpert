"""categorize akb full output: python akcat.py file [extra_regex_name=regex ...]
prints per-category review counts and short snippets (+-45 chars) with review short ids."""
import re, sys
from collections import defaultdict
t = open(sys.argv[1], encoding='utf-8').read()
CAT = {
 'head_unit': r'死机|黑屏|白屏|自动重启|重启|卡顿|卡死|闪退|花屏',
 'rattle': r'异响|咯吱|嘎吱|吱吱|咔咔|哒哒',
 'brake': r'刹车.{0,8}(异响|偏软|太软|发软|偏硬|点头|不线性|不跟脚|前段|行程|异常|抖)',
 'noise_road': r'胎噪|风噪|路噪|隔音',
 'engine_noise': r'发动机.{0,8}(噪音|声音|吵|轰|嗡|震动|抖)|增程器.{0,6}(噪音|声音|吵|震)',
 'suspension': r'底盘.{0,6}(硬|软|松散|颠|异响|调校)|悬挂.{0,4}(硬|软)|减震.{0,4}(硬|软|差)|避震.{0,4}(硬|软|差)',
 'jerk': r'顿挫|前窜|往前窜|窜一下|一冲一冲|耸',
 'range_fuel': r'续航.{0,6}(虚|打折|缩水|掉|达成率)|亏电.{0,4}油耗.{0,6}(高|偏高)|油耗.{0,3}(高|偏高|大)',
 'paint_body': r'车漆|漆面|漆薄|生锈|锈',
 'adas': r'智驾|辅助驾驶|AEB|误刹|幽灵刹车|自动泊车|车道保持|NOA|领航',
 'lights': r'大灯|车灯|远光|近光',
 'leak': r'漏水|进水|渗水|漏油|起雾',
 'charge': r'充电.{0,8}(故障|失败|慢|跳枪|中断|中止|充不进)|充不进',
 'climate': r'空调.{0,8}(异味|不制冷|故障|噪音|吵)|热泵',
 'app_key': r'APP|App|app|蓝牙钥匙|手机钥匙|NFC',
 'door_handle': r'门把手',
 'smell': r'异味|味道大|气味',
 'tire': r'轮胎|胎压|爆胎|鼓包',
 'steering': r'方向盘.{0,6}(抖|异响|跑偏|虚位)|跑偏',
 'battery12v': r'亏电(?!.{0,4}油耗)|小电瓶|电瓶',
}
for a in sys.argv[2:]:
    k, v = a.split('=', 1); CAT[k] = v
NEG = re.compile(r'没有|没遇到|无故障|还没|未出现|不卡顿|无卡顿|减少卡顿|不会卡|暂无|从未|零故障|目前没|无异响|没出现|没啥|几乎感觉不到|无顿挫|没有顿挫|毫无顿挫|感受不到')
hits = defaultdict(list)
for blk in t.split('\n== ')[1:]:
    lines = blk.split('\n'); h = lines[0].split(' | ')
    sid = h[0].split('view_')[1][:14] if 'view_' in h[0] else h[0]
    txt = ' '.join(l.split('] ', 1)[-1] for l in lines[1:] if l.startswith('  ['))
    meta = h[1].strip()[:22] + '/' + h[3].replace('own ', '').strip()
    for k, rx in CAT.items():
        sn = []
        for m in re.finditer(rx, txt):
            s = txt[max(0, m.start() - 45):m.end() + 45]
            if NEG.search(s): continue
            if any(s[20:60] in x for x in sn): continue
            sn.append(s)
        if sn: hits[k].append((sid, meta, sn[:2]))
for k, v in sorted(hits.items(), key=lambda x: -len(x[1])):
    print(f'#### {k}: {len(v)} reviews')
    for sid, meta, sn in v[:int(__import__("os").environ.get("NMAX", "14"))]:
        print(f'  {sid} {meta}: ' + ' || '.join(s.replace(chr(10), ' ') for s in sn))
