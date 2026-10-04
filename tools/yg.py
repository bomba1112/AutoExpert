import json,urllib.request,sys
sid=sys.argv[1]
H={'User-Agent':'Mozilla/5.0','Referer':f'https://k.autohome.com.cn/{sid}'}
r=json.loads(urllib.request.urlopen(urllib.request.Request(f'https://koubeiipv6.app.autohome.com.cn/pc/series/list?pm=3&seriesId={sid}&pageIndex=1&pageSize=20&yearid=0&ge=0&seriesSummaryKey=0&order=0',headers=H)).read())['result']
print(r['seriesname'],r['rowcountString'])
for g in r['specgroup']: print(' ',g['groupname'], g.get('yearId'), sum(s['koubeicount'] for s in g['speclist']), [(s['specname'],s['koubeicount']) for s in g['speclist']][:8])
