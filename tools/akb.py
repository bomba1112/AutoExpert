"""autohome koubei dump: python akb.py <seriesId> [maxpages] [specfilter-substring] [full]
prints owner reviews (skips 探店 dealer-visit type). With 'full' fetches each detail page and
prints the 最不满意 section + fault-keyword snippets from the whole body."""
import json, sys, urllib.request, re, html, os
from concurrent.futures import ThreadPoolExecutor
sid = sys.argv[1]; maxp = int(sys.argv[2]) if len(sys.argv) > 2 else 10
flt = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-' else ''
full = 'full' in sys.argv[4:]
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120', 'Referer': f'https://k.autohome.com.cn/{sid}'}
def get(u):
    import time
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode('utf-8', 'ignore')
        except Exception:
            if k == 3: raise
            time.sleep(3 * (k + 1))
def page(i):
    return json.loads(get(f'https://koubeiipv6.app.autohome.com.cn/pc/series/list?pm=3&seriesId={sid}&pageIndex={i}&pageSize=20&yearid={os.environ.get("YEARID","0")}&ge=0&seriesSummaryKey=0&order=0'))['result']
KW = r'故障|坏了|异响|死机|黑屏|重启|漏水|漏油|渗|维修|返厂|更换|换了|召回|报警|抖动|顿挫|异味|生锈|开裂|脱落|失灵|断电|趴窝|亏电|熄火|无法启动|进水|起雾|卡顿|闪退'
def detail(u):
    try:
        t = get(u)
    except Exception as e:
        return f'ERR {e}', []
    x = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S))))
    end = x.find('上述内容的版权'); x = x[:end] if end > 0 else x
    i = x.find('最不满意'); bad = ''
    if i >= 0:
        m = re.search(r' 空间 \d | 驾驶感受 \d ', x[i:]); bad = x[i + 4:i + (m.start() if m else 1200)][:1200]
    st = x.find('最满意'); body = x[st:] if st >= 0 else x
    sn = [body[max(0, m.start() - 70):m.end() + 70] for m in re.finditer(KW, body)]
    return bad.strip(), sn[:8]
def spage(spec, i):
    return json.loads(get(f'https://koubeiipv6.app.autohome.com.cn/pc/spec/list?pm=3&specId={spec}&pageIndex={i}&pageSize=20&ge=0&seriesSummaryKey=0&order=0'))['result']
def allpages():
    if os.environ.get('SPECIDS'):
        for spec in os.environ['SPECIDS'].split(','):
            r = spage(spec, 1); print('# spec', spec, r.get('rowcount'), 'pages', r.get('pagecount'))
            for i in range(1, min(maxp, r['pagecount']) + 1):
                if i > 1: r = spage(spec, i)
                yield from r['list']
        return
    r = page(1); print('#', r['seriesname'], r['rowcountString'], 'pages', r['pagecount'])
    for i in range(1, min(maxp, r['pagecount']) + 1):
        if i > 1: r = page(i)
        yield from r['list']
items = []
if True:
    for e in allpages():
        if any(x.get('name') == '探店时间' for x in e.get('exinfolist') or []): continue
        if flt and flt not in e['specname']: continue
        items.append(e)
def show(e):
    u = f"https://k.autohome.com.cn/detail/view_{e['showId']}.html"
    out = [f"== {u} | {e['specname']} | post {e['posttime']} | own {e.get('carOwnershipPeriod')} | {e.get('distance')}"]
    if full:
        bad, sn = detail(u); out.append(f'  [最不满意] {bad}')
        for s in sn: out.append(f'  [kw] ...{s}...')
    else:
        for c in e.get('contents', []):
            if c.get('structuredname') not in ('好评', '最满意', '满意'): out.append(f"  [{c['structuredname']}] {c['content'][:300]}")
    return '\n'.join(out)
with ThreadPoolExecutor(6) as ex:
    for s in ex.map(show, items): print(s)
print('# shown', len(items))
