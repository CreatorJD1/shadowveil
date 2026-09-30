import sys,numpy as np
sys.path.insert(0,'/workspace/gb'); from tracks import track
from PIL import Image,ImageDraw
# spec clip:side:a:b:step[:S]
rows=[]; per=16; C=62
for spec in sys.argv[2:]:
    p=spec.split(':'); c,s,a,b,st=p[0],p[1],int(p[2]),int(p[3]),int(p[4]); S=int(p[5]) if len(p)>5 else 50
    tr,F=track(c)
    if s.startswith('X'):
        fx,fy=[int(v) for v in s[1:].split('_')]; t={'x':[fx]*len(F),'y':[fy]*len(F)}
    else: t=tr[s]
    idx=list(range(a,b,st))
    for k0 in range(0,len(idx),per):
        r=Image.new('RGB',(40+per*(C+1),C+11),'white'); d=ImageDraw.Draw(r); d.text((1,2),c[:7],fill='black'); d.text((1,14),s,fill='black')
        for k,i in enumerate(idx[k0:k0+per]):
            x,y=t['x'][i],t['y'][i]; cr=Image.fromarray(F[i]).crop((int(x-S),int(y-S),int(x+S),int(y+S))).resize((C,C),Image.LANCZOS); r.paste(cr,(40+k*(C+1),0)); d.text((40+k*(C+1),C),str(i),fill='black')
        rows.append(r)
o=Image.new('RGB',(max(r.width for r in rows),sum(r.height for r in rows)),'white'); y=0
for r in rows: o.paste(r,(0,y)); y+=r.height
o.save(sys.argv[1])
