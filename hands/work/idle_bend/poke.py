# which Ring/Pinky frame pixels stick out of the silhouette of the other hand parts (posed), mapped back to frame-local pixels
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
from qalib import *
D,view=sys.argv[1],sys.argv[2];r=Run(D)
rig=json.load(open(f'/workspace/shadowveil/views/{view}/hands/rig.json'));by={p['id']:p for p in rig['parts']}
def fidx(c,n): return max(0,min(n-1,int(np.floor(c*(n-1)+0.5))))
out={}
for S in 'LR':
  for F in ['Ring','Pinky']:
    for seg in '123':
        pid=f'{S}_{F}{seg}';fr=by[pid].get('frames')
        if not fr: continue
        acc={}
        for cn in [c for c in r.C if c.startswith('curl_')]:
            c=float(cn[5:]);k=fidx(c,len(fr));fn=fr[k]['file'] if isinstance(fr[k],dict) else fr[k]
            if k==0: continue
            ps=r.parts(cn,S);z=r.C[cn]['parts'];L={p:r.layer(cn,p)[...,3] for p in ps}
            other=np.zeros((1739,1365),bool)
            for p in ps:
                if F not in p: other|=L[p]>=128
            sil=nd.binary_fill_holes(nd.binary_closing(other,structure=disk(2)))
            above=np.zeros_like(other)
            for p in ps:
                if z[p]['layer']>z[pid]['layer']: above|=L[p]>=128
            bad=(L[pid]>0)&~sil&~above
            if not bad.any(): continue
            M=np.array(z[pid]['M']);A=np.array([[M[0],M[2],M[4]],[M[1],M[3],M[5]],[0,0,1]]);inv=np.linalg.inv(A)
            ys,xs=np.nonzero(bad);q=inv@np.stack([xs,ys,np.ones_like(xs)]).astype(float)
            loc=set(zip(np.round(q[0]).astype(int).tolist(),np.round(q[1]).astype(int).tolist()))
            acc.setdefault(fn,set()).update(loc);print(view,pid,cn,fn,'poking px',int(bad.sum()),'world e.g.',list(zip(xs[:3].tolist(),ys[:3].tolist())))
        for fn,s in acc.items(): out[fn]=sorted(s)
json.dump(out,open(f'poke_{view}.json','w'));print({k:len(v) for k,v in out.items()})
