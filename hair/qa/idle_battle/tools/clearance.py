# geometry-only: min distance (px) between front hair (layer>=600, alpha>=0.25) and each eye/mouth box, head-local, every frame
import json,sys
from common import *
names=available_names()
VV={}; out={}
for n in names:
    v='apose' if n.startswith('apose') else n.rsplit('_',1)[-1] if n.startswith('keys') else n
    if v not in VV:
        s=View(v); dts={k:cv2.distanceTransform((~m).astype(np.uint8),cv2.DIST_L2,5) for k,m in s.boxm.items()}; VV[v]=(s,dts)
    s,dts=VV[v]
    if not s.boxm: out[n]={}; continue
    front=[k for k in s.by if s.layers[k]>=600]
    F=json.load(open(f'{IDLE}/frames/{n}/meta.json'))['frames']
    res={k:[] for k in s.boxm}
    for i in [None]+list(range(len(F))):
        Ms=s.hair_M(None if i is None else F[i]['hair'],rest=i is None)
        a=np.zeros((s.h,s.w),np.float32)
        for k in front: a=np.maximum(a,warp(s.pa[k],s.roi_M(Ms[k]),s.w,s.h))
        m=a>=0.25
        for k,dt in dts.items(): res[k].append(float(dt[m].min()))
    out[n]={k:dict(rest=r[0],min=min(r[1:]),min_frame=int(np.argmin(r[1:])),min_t=F[int(np.argmin(r[1:]))]['t']) for k,r in res.items()}
    print(n,{k:(round(x['rest'],1),round(x['min'],1),x['min_frame']) for k,x in out[n].items()},flush=True)
json.dump(out,open(f'{OUT}/data/clearance.json','w'),indent=1)
