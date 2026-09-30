# line-art metric: outline width (2x distance transform on the skeleton), breaks (inner skeleton endpoints), kinks (turn > 60 deg over 5 px)
import numpy as np
from scipy import ndimage as nd
from skimage.morphology import skeletonize
def line_mask(rgba):
    a=rgba[...,3].astype(np.int32);rgb=rgba[...,:3].astype(np.int32)
    lum=(rgb[...,0]*299+rgb[...,1]*587+rgb[...,2]*114)//1000
    m=(a>128)&(lum<75)
    thick=nd.binary_dilation(nd.binary_opening(m,iterations=3),iterations=4)  # dark fills (bikini, hair mass) are not line art
    return m&~thick
NB=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
def roi_stats(rgba,cx,cy,r=48):
    h,w=rgba.shape[:2];x0,x1=max(0,int(cx-r)),min(w,int(cx+r));y0,y1=max(0,int(cy-r)),min(h,int(cy+r))
    if x1-x0<8 or y1-y0<8: return None
    m=line_mask(rgba[y0:y1,x0:x1]);m=nd.binary_opening(m,iterations=0) if False else m
    if m.sum()<10: return dict(px=int(m.sum()),wmed=0,wp90=0,ends=0,kinks=0,comps=comps(rgba[y0:y1,x0:x1]))
    dt=nd.distance_transform_edt(m);sk=skeletonize(m);ys,xs=np.nonzero(sk)
    wd=2*dt[sk]-1;wmed=float(np.median(wd));wp90=float(np.percentile(wd,90))
    S=set(zip(ys.tolist(),xs.tolist()));deg={p:sum((p[0]+a,p[1]+b) in S for a,b in NB) for p in S}
    H,Wd=m.shape;inner=lambda p:3<p[0]<H-4 and 3<p[1]<Wd-4
    ends=sum(1 for p,d in deg.items() if d==1 and inner(p))
    def walk(p,prev,n):
        cur=p
        for _ in range(n):
            nx=[(cur[0]+a,cur[1]+b) for a,b in NB if (cur[0]+a,cur[1]+b) in S and (cur[0]+a,cur[1]+b)!=prev]
            if len(nx)!=1: return None
            prev,cur=cur,nx[0]
        return cur
    kinks=0
    for p,d in deg.items():
        if d!=2 or not inner(p): continue
        nb=[(p[0]+a,p[1]+b) for a,b in NB if (p[0]+a,p[1]+b) in S]
        e1=walk(nb[0],p,4);e2=walk(nb[1],p,4)
        if e1 is None or e2 is None: continue
        v1=np.array(e1)-p;v2=np.array(e2)-p;c=np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v2)+1e-9)
        if c>-0.5: kinks+=1   # angle between arms < 120 deg -> turn > 60 deg
    return dict(px=int(m.sum()),wmed=round(wmed,2),wp90=round(wp90,2),ends=ends,kinks=kinks,comps=comps(rgba[y0:y1,x0:x1]))
def comps(c):
    # breaks: connected line pieces (lum<100, 1 px closing, pieces >= 8 px); a real break splits one line into two (+1)
    a=c[...,3].astype(np.int32);rgb=c[...,:3].astype(np.int32);lum=(rgb[...,0]*299+rgb[...,1]*587+rgb[...,2]*114)//1000
    m=(a>128)&(lum<100);m=m&~nd.binary_dilation(nd.binary_opening(m,iterations=3),iterations=4);m=nd.binary_closing(m,iterations=1)
    lab,nc=nd.label(m,structure=np.ones((3,3)))
    if not nc: return 0
    sz=nd.sum(m,lab,range(1,nc+1));return int((np.array(sz)>=8).sum())
