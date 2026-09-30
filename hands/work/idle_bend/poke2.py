# per Ring1 frame: local pixels that poke out (outside other parts' silhouette) vs local pixels that are the only fill (useful) somewhere in the curl range
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
from qalib import *
D,view=sys.argv[1],sys.argv[2];r=Run(D)
rig=json.load(open(f'/workspace/shadowveil/views/{view}/hands/rig.json'));by={p['id']:p for p in rig['parts']}
def fidx(c,n): return max(0,min(n-1,int(np.floor(c*(n-1)+0.5))))
res={}
for S in 'LR':
    pid=f'{S}_Ring1';fr=by[pid]['frames']
    P={};U={}
    for cn in [c for c in r.C if c.startswith('curl_')]:
        c=float(cn[5:]);k=fidx(c,len(fr));fn=fr[k]['file']
        if k==0: continue
        ps=r.parts(cn,S);z=r.C[cn]['parts'];L={p:r.layer(cn,p)[...,3] for p in ps}
        other=np.zeros((1739,1365),bool);below=np.zeros((1739,1365),bool)
        for p in ps:
            if p!=pid: other|=L[p]>=128
            if p!=pid and z[p]['layer']<z[pid]['layer']: below|=L[p]>=128
        sil=nd.binary_fill_holes(nd.binary_closing(other,structure=disk(2)))
        above=np.zeros_like(other)
        for p in ps:
            if z[p]['layer']>z[pid]['layer']: above|=L[p]>=128
        mine=L[pid]>0
        bad=mine&~above&(~sil|below); useful=mine&sil&~other
        M=np.array(z[pid]['M']);inv=np.linalg.inv(np.array([[M[0],M[2],M[4]],[M[1],M[3],M[5]],[0,0,1]]))
        for nm,m,dst in (('bad',bad,P),('use',useful,U)):
            ys,xs=np.nonzero(m);q=inv@np.stack([xs,ys,np.ones_like(xs)]).astype(float)
            if nm=='bad': dst.setdefault(fn,set()).update(zip(np.round(q[0]).astype(int).tolist(),np.round(q[1]).astype(int).tolist()))
            else:
                fx,fy=np.floor(q[0]).astype(int),np.floor(q[1]).astype(int)
                for dx in (-1,0,1,2):
                    for dy in (-1,0,1,2): dst.setdefault(fn,set()).update(zip((fx+dx).tolist(),(fy+dy).tolist()))
    for fn in P:
        a=np.array(Image.open(f'/workspace/shadowveil/views/{view}/hands/{fn}'))[...,3]
        bad={(x,y) for x,y in P[fn] if a[y,x]>0};use={(x,y) for x,y in U.get(fn,set()) if a[y,x]>0}
        trim=bad-use;res[fn]={'trim':sorted(trim),'use':sorted(use)}
        print(fn,'frame px',int((a>0).sum()),'poking',len(bad),'useful elsewhere',len(bad&use),'-> trim',len(trim))
json.dump(res,open(f'trim_{view}.json','w'))
