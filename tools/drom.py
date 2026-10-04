import re,html,sys,urllib.request
def get(u):
    b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120'}),timeout=30).read()
    t=b.decode('cp1251','ignore') if b'windows-1251' in b[:5000].lower() else b.decode('utf-8','ignore')
    return t
def text(t):
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',t)))
if __name__=='__main__':
    base='/'+sys.argv[1].strip('/')+'/'
    t=get('https://www.drom.ru'+base)
    ids=sorted(set(re.findall(re.escape(base)+r'(\d+)/',t)))
    for i in ids:
        u=f'https://www.drom.ru{base}{i}/'
        x=text(get(u))
        a=x.find('Характеристики'); b=x.find('Мнения')
        h=re.search(r'(BYD|Changan|Toyota|ZEEKR|Lynk|Чанган)[^|]{0,120}?(20\d\d)',x)
        m=re.search(r'Недостатки(.{0,1200}?)(Поломки|Оценка|Комментари|Достоинства)',x)
        p=re.search(r'Поломки(.{0,600}?)(Оценка|Комментари)',x)
        print('==',u); print('SPEC:',x[a:a+300] if a>=0 else '')
        print('MINUS:',m.group(1).strip() if m else None); print('BREAK:',p.group(1).strip() if p else None)
