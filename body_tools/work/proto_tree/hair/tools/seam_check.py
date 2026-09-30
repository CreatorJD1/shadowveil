# Joint seam check: for every chained strand joint (child whose parent is a swaying strand segment), draw the strand's
# segments alone (bilinear, drawImage semantics, world matrices from render.matrices) and look near the joint for pixels
# that are interior to the strand under BOTH the parent's and the child's transform (ideal coverage 1) but whose
# composite alpha is < 0.98 (AA seam / hairline showing what's underneath). Sweep: 41 HairSwayX x HairSwayY {-1,0,1}.
import sys, json, numpy as np
from render import *
def alpha_of(path): return np.array(Image.open(path))[...,3].astype(float)
def warpA(A,M,box):
    x0,y0,x1,y1=box; a,b,c,d,e,f=M
    if np.allclose(M,I): return A[y0:y1,x0:x1]/255
    det=a*d-b*c; oy,ox=np.mgrid[y0:y1,x0:x1].astype(float); X=ox+.5-e; Y=oy+.5-f
    sx=(d*X-c*Y)/det-.5; sy=(-b*X+a*Y)/det-.5
    return ndi.map_coordinates(A,[sy,sx],order=1,mode='constant',cval=0)/255
RELDY=(-1,0,1)
def check(v,verbose=False,S=None,nocap=False):
    parts,ymax=load_rig(v); by={p['id']:p for p in parts}; hd=f'{R}/views/{v}/hair'
    S=S if S is not None else np.round(np.linspace(-1,1,41),3)
    res={}
    for p in parts:
        q=by.get(p.get('parent'))
        if not q or not q['id'].startswith('strand') : continue
        root=p['id'].split('_')[0]+'_'+p['id'].split('_')[1]
        segs=[x for x in parts if x['id']==root or x['id'].startswith(root+'_')]
        As={x['id']:alpha_of(f"{hd}/{x['file']}") for x in segs}
        # whole strand without caps (caps are the child's copies of parent pixels) = max over segments
        Wm=np.max(list(As.values()),0)
        if nocap:
            for x in segs:
                pp=by.get(x.get('parent'))
                if pp is not None and pp['id'] in As: As[x['id']]=np.where(As[pp['id']]>0,0,As[x['id']])
        px,py=p['pivotX'],p['pivotY']; box=(int(px)-14,int(py)-14,int(px)+15,int(py)+15)
        worst=0; bad=0; interior=0; soft=0; sworst=0; spos=None
        for sx in S:
            for rel in RELDY:   # v1.3: per-part vertical drives are independent -> relative dy between child and parent
                Ms=dict(matrices(parts,ymax,sx,0)); Ms[p['id']]=mul(T(0,rel),Ms[p['id']])
                for x in segs:   # descendants of the child move with it
                    if x['layer']<p['layer']: Ms[x['id']]=mul(T(0,rel),Ms[x['id']])
                Mc,Mp=Ms[p['id']],Ms[q['id']]
                jx=Mc[0]*px+Mc[2]*py+Mc[4]; jy=Mc[1]*px+Mc[3]*py+Mc[5]
                b2=(int(jx)-10,int(jy)-10,int(jx)+11,int(jy)+11)
                ideal=np.minimum(warpA(Wm,Mp,b2),warpA(Wm,Mc,b2))
                comp=np.zeros_like(ideal)
                for x in sorted(segs,key=lambda t:t['layer']):
                    a=warpA(As[x['id']],Ms[x['id']],b2); comp=a+comp*(1-a)
                oy,ox=np.mgrid[b2[1]:b2[3],b2[0]:b2[2]]; near=np.hypot(ox+.5-jx,oy+.5-jy)<=7
                m=near&(ideal>=0.999)&(comp<0.98)
                sm=near&(ideal>0.2)&(ideal-comp>0.08); soft+=int(sm.sum())
                if sm.any():
                    dd=float((ideal-comp)[sm].max())
                    if dd>sworst: sworst=dd; spos=(float(sx),rel)
                interior+=int((near&(ideal>=0.999)).sum()); bad+=int(m.sum()); worst=max(worst,float((ideal-comp)[near&(ideal>=0.999)].max(initial=0)))
        res[p['id']]=dict(interior_px_checked=interior,seam_px=bad,soft_drop_px=soft,soft_worst=round(sworst,3),soft_worst_at=spos,worst_alpha_drop=round(worst,3))
    return res
if __name__=='__main__':
    nc='--nocap' in sys.argv
    if '--dy2' in sys.argv: RELDY=(-2,-1,0,1,2)
    if '--dy3' in sys.argv: RELDY=(-3,-2,-1,0,1,2,3)
    vs=[a for a in sys.argv[1:] if not a.startswith('--')]
    out={v:check(v,nocap=nc) for v in (vs or ['apose','tpose','left','right','back'])}
    print(json.dumps(out,indent=1))
