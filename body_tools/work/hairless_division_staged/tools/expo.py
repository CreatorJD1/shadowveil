# newly exposed neck px: neck contributes visibly (no opaque piece above it) at the offset, but not at rest; split by inside/outside moved head silhouette
import sys,json,numpy as np
sys.path.insert(0,'/workspace/tmpsv/hg'); from sim import load,shift
from PIL import Image
v,pd,dx,dy=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
order,P=load(v,pd)
def visneck(dx,dy):
    i=order.index('neck'); cov=np.zeros(P['neck'].shape[:2],bool)
    for k in order[i+1:]:
        a=(shift(P[k],dx,dy) if k=='head' else P[k])[...,3]>=255; cov|=a
    return (P['neck'][...,3]>0)&~cov
r=visneck(0,0); m=visneck(dx,dy); new=m&~r
hs=shift(P['head'],dx,dy)[...,3]>0; restsil=np.zeros_like(r)
for k in order: restsil|=P[k][...,3]>0
H=np.array(Image.open(f'/workspace/shadowveil/body_tools/work/hairless_division_staged/{v}/hairless_{v}.png'))[...,3]>0
ys,xs=np.nonzero(new)
print(json.dumps({'view':v,'pieces':pd,'newly_exposed_neck_px':int(new.sum()),'of_which_outside_her_rest_silhouette':int((new&~H).sum()),'bbox':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None}))
np.save(f'/workspace/tmpsv/hg/{v}_{pd}_newneck.npy',new)
