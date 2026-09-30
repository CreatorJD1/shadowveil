import numpy as np
from scipy import ndimage as ndi
def arms2(m,top,H,fr=0.30):
    sub=m.copy(); sub[:int(top+fr*H)]=False; lab,n=ndi.label(sub); out=[]
    for k in range(1,n+1):
        mk=lab==k; ys,xs=np.nonzero(mk)
        if len(ys)<400 or len(ys)>40000 or ys.max()>=m.shape[0]-5 or ys.max()>top+0.95*H: continue
        i0=np.argmin(ys); t0=np.array([xs[i0],ys[i0]]); d=np.hypot(xs-t0[0],ys-t0[1]); j=np.argmax(d)
        out.append(dict(area=len(ys),top=t0.tolist(),tip=[int(xs[j]),int(ys[j])],mask=mk))
    return out
def profile(comp):
    m=comp['mask']; ys,xs=np.nonzero(m); P=np.stack([xs,ys],1).astype(float); tip=np.array(comp['tip'],float)
    r=np.hypot(*(P-tip).T); Q=P[(r>90)&(r<200)]
    if len(Q)<50: Q=P[r>60]
    mu=Q.mean(0); d=np.linalg.svd(Q-mu,full_matrices=False)[2][0]
    if d@(tip-mu)<0: d=-d
    pu=(P-tip)@d; nv=np.array([-d[1],d[0]]); pv=(P-tip)@nv
    prof={}
    for s in range(int(pu.min())+2,0):
        sel=np.abs(pu-s)<0.7
        if sel.sum()>1: prof[s]=(float(pv[sel].min()),float(pv[sel].max()))
    return P,pu,pv,d,nv,tip,prof
def wrist2(comp,H):
    P,pu,pv,d,nv,tip,prof=profile(comp); ss=sorted(prof); w={s:prof[s][1]-prof[s][0] for s in ss}
    # forearm width = median width 100..140 px behind tip (scaled); wrist = most proximal s (scanning from tip back) where width first returns to <= forearm width+2 behind the palm max
    k=H/1056
    far=[w[s] for s in ss if -150*k<s<-100*k]
    fw=np.median(far) if far else min(w.values())
    cand=[s for s in ss if -110*k<s<-30*k]
    smax=max(cand,key=lambda s:w[s]) if cand else -60
    wr_s=None
    for s in range(smax,int(-150*k),-1):
        if s in w and w[s]<=fw+2: wr_s=s; break
    if wr_s is None: wr_s=min(cand,key=lambda s:w[s])
    a,b=prof[wr_s]; wr=tip+d*wr_s+nv*(a+b)/2
    hand=np.zeros_like(comp['mask']); hp=P[pu>wr_s].astype(int); hand[hp[:,1],hp[:,0]]=True
    return dict(wrist=wr.tolist(),axis=d.tolist(),wrist_width=float(w[wr_s]),hand=hand,fw=float(fw),palm_max=float(w[smax]),L_axis=float(-wr_s))
from collections import deque
def geoball(m,tip,R):
    x0,y0=max(0,tip[0]-R-2),max(0,tip[1]-R-2); x1,y1=min(m.shape[1],tip[0]+R+3),min(m.shape[0],tip[1]+R+3)
    sub=m[y0:y1,x0:x1]; h,w=sub.shape; D=np.full((h,w),1e9); t=(tip[1]-y0,tip[0]-x0)
    if not sub[t]: return None
    D[t]=0; q=deque([t]); st=[(0,1,1),(1,0,1),(0,-1,1),(-1,0,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]
    while q:
        y,x=q.popleft(); dv=D[y,x]
        for dy,dx,c in st:
            yy,xx=y+dy,x+dx
            if 0<=yy<h and 0<=xx<w and sub[yy,xx] and D[yy,xx]>dv+c+1e-6 and dv+c<=R:
                D[yy,xx]=dv+c; q.append((yy,xx))
    out=np.zeros_like(m); out[y0:y1,x0:x1]=D<=R; return out
