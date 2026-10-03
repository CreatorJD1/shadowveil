import json, numpy as np, sys
sys.path.insert(0,'.')
from fitlib import *
B=base()[...,:3].astype(np.int32); Lm=lum(B)
out={}
for E in ['EyeR','EyeL']:
    O=alpha(f'{E}_white.png'); ir=alpha(f'{E}_iris.png'); l0=alpha(f'{E}_lid_0.png'); la=alpha(f'{E}_lash.png')
    pl,pr=corners(O)
    outer,inner=(pl,pr) if E=='EyeR' else (pr,pl)
    cols={}
    xs=np.unique(np.nonzero(O)[1])
    for x in xs:
        r=np.nonzero(O[:,x])[0]; yt,yb=int(r.min()),int(r.max())
        y=yt-1; band=[]
        while Lm[y,x]<100: band.append(y); y-=1
        # coverage width incl. AA (stop at skin)
        y=yt-1; cov=0.0; rows=[]
        while Lm[y,x]<128 and yt-y<9: cov+=np.clip((140-Lm[y,x])/(140-10),0,1); rows.append(y); y-=1
        y=yb+1; low=[]; lcov=0.0
        while Lm[y,x]<128 and y-yb<5: low.append(y); lcov+=np.clip((140-Lm[y,x])/(140-10),0,1); y+=1
        cols[int(x)]=dict(yt=yt,yb=yb,band=[min(band),max(band)] if band else None,band_ink=len(band),band_cov=round(cov,2),band_rows=[min(rows),max(rows)] if rows else None,low=[min(low),max(low)] if low else None,low_cov=round(lcov,2))
    out[E]=dict(outer=outer.tolist(),inner=inner.tolist(),cols=cols)
    print(E,'outer',outer,'inner',inner)
    for x in xs: c=cols[int(x)]; print(x,c['yt'],c['yb'],'band',c['band'],c['band_ink'],c['band_cov'],c['band_rows'],'low',c['low'],c['low_cov'])
json.dump(out,open('her_raw.json','w'),indent=1)
