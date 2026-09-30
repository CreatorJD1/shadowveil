import json,sys,numpy as np
from defs import D
ROOT='/workspace/shadowveil'
for V in sys.argv[1:]:
    s=json.load(open(f'{ROOT}/views/{V}/body/skin.json')); bn=[b['name'] for b in s['bones']]
    Vx=np.array(s['vertices'],float)
    for side in D[V]:
        (x0,y0),(x1,y1)=D[V][side]['wrist']; A=np.array([x0,y0],float); t=np.array([x1-x0,y1-y0],float); Lw=np.linalg.norm(t); t/=Lw; n=np.array([-t[1],t[0]])
        if (np.array(D[V][side]['inside'])-A)@n>0: n=-n
        rel=Vx-A; u=rel@t; sd=rel@n
        sel=np.nonzero((u>-3)&(u<Lw+3)&(sd>-4)&(sd<=12))[0]
        fb=f'forearm_{side}'; bad=[]
        for i in sel:
            w=dict((bn[b],x) for b,x in s['weights'][i]); fw=w.get(fb,0)
            if fw<0.999: bad.append((round(sd[i],1),round(u[i],1),{k:round(x,3) for k,x in w.items()}))
        print(V,side,'verts in band -4..12 px:',len(sel),'not 100% forearm:',len(bad))
        for b in sorted(bad)[:12]: print('   sd',b[0],'u',b[1],b[2])
        if 'underlay' in s and s['underlay'].get('vertices'):
            U=np.array(s['underlay']['vertices'],float); rel=U-A; u=rel@t; sd=rel@n; sel=np.nonzero((u>-3)&(u<Lw+3)&(sd>-4)&(sd<=12))[0]
            nb=sum(1 for i in sel if dict((bn[b],x) for b,x in s['underlay']['weights'][i]).get(fb,0)<0.999); print('   underlay verts in band',len(sel),'not 100% forearm',nb)
