import sys
from drom import get,text
for u in sys.argv[1:]:
    x=text(get(u)); a=x.find('Год выпуска'); b=x.find('Мнения владельцев',a)
    c=x.find('Комментарии',a)
    end=min([i for i in (b,c) if i>a] or [a+4000])
    print('==',u); print(x[a:min(end,a+3500)]); print()
