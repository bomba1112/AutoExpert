"""python specs.py <seriesId> <regex>  -> prints comma list of specids matching regex (with counts to stderr)"""
import json,urllib.request,sys,re
sid,rx=sys.argv[1],sys.argv[2]
H={'User-Agent':'Mozilla/5.0','Referer':f'https://k.autohome.com.cn/{sid}'}
r=json.loads(urllib.request.urlopen(urllib.request.Request(f'https://koubeiipv6.app.autohome.com.cn/pc/series/list?pm=3&seriesId={sid}&pageIndex=1&pageSize=20&yearid=0&ge=0&seriesSummaryKey=0&order=0',headers=H),timeout=30).read())['result']
sp=[(s['specid'],s['specname'],s['koubeicount']) for g in r['specgroup'] for s in g['speclist'] if re.search(rx,s['specname']) and s['koubeicount']>0]
for x in sp: print(x, file=sys.stderr)
print('total', sum(x[2] for x in sp), file=sys.stderr)
print(','.join(str(x[0]) for x in sp))
