# mean luminance of the white exposed at X=-1/+1 (Y=0): live vs staged, and her drawn white (base.png) in the same rows
import json,numpy as np
from PIL import Image
R='/workspace/shadowveil'; S=f'{R}/eyes/staged/white_tone'
VIEWS={'apose':['EyeR','EyeL'],'tpose':['EyeR','EyeL'],'left':['EyeL'],'right':['EyeR']}
L=lambda p: np.array(Image.open(p).convert('RGBA')).astype(int)
out={}
for v,es in VIEWS.items():
    rig=json.load(open(f'{R}/views/{v}/eyes/rig.json')); lim=rig['irisLimitsPx']; base=L(f'{R}/views/{v}/base.png')
    for e in es:
        w=L(f'{R}/views/{v}/eyes/{e}_white.png'); n=L(f'{S}/{v}/{e}_white.png'); i=L(f'{R}/views/{v}/eyes/{e}_iris.png')
        im=i[...,3]>0; wm=w[...,3]>0; drawn=wm&~im
        for X,dx in ((-1,lim['dxAtXminus1']),(1,lim['dxAtXplus1'])):
            if dx==0: continue
            s=np.roll(im,dx,1); ex=im&~s
            rows=np.nonzero(ex.any(1))[0]
            her=drawn.copy(); her[[y for y in range(her.shape[0]) if y not in set(rows)]]=False
            lum=lambda a,m: round(float(a[m][:,:3].mean()),1)
            out[f'{v}/{e} X={X:+d}']=dict(exposedPx=int(ex.sum()),liveLum=lum(w,ex),stagedLum=lum(n,ex),herDrawnWhiteSameRowsLum=lum(base,her&(base[...,:3].mean(-1)>=120)),changedPx=int((ex&(w!=n).any(-1)).sum()))
json.dump(out,open(f'{S}/measure.json','w'),indent=1)
for k,x in out.items(): print(k,x)
