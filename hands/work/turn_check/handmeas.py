import numpy as np
from scipy import ndimage as ndi
def measure(mask,wrist,axis,thumb_hint=None):
    """mask: bool hand mask (already cut at the wrist). wrist (x,y), axis unit vector pointing into the hand."""
    u=np.asarray(axis,float); u/=np.linalg.norm(u); v=np.array([-u[1],u[0]])
    ys,xs=np.nonzero(mask); P=np.stack([xs,ys],1)-np.asarray(wrist,float); pu=P@u; pv=P@v
    L=float(pu.max())
    dt=ndi.distance_transform_edt(mask); pr=dt.max(); ro=max(3,int(round(pr*0.55)))
    yy,xx=np.mgrid[-ro:ro+1,-ro:ro+1]; disk=xx**2+yy**2<=ro*ro
    palm=ndi.binary_opening(mask,disk); fing=mask&~ndi.binary_dilation(palm,iterations=1)
    lab,n=ndi.label(fing); comps=[]
    for k in range(1,n+1):
        yk,xk=np.nonzero(lab==k)
        if len(yk)<12: continue
        Q=np.stack([xk,yk],1)-np.asarray(wrist,float); qu=Q@u; qv=Q@v
        mu=Q.mean(0); U,s,Vt=np.linalg.svd(Q-mu,full_matrices=False); ln=float(np.ptp((Q-mu)@Vt[0])); wd=float(np.ptp((Q-mu)@Vt[1]))
        if ln<1.4*wd: continue
        comps.append(dict(u0=float(qu.min()),u1=float(qu.max()),v=float(qv.mean()),len=ln,wid=wd,area=len(yk)))
    comps.sort(key=lambda c:c['v'])
    return dict(L=L,palm_r=float(pr),comps=comps,fing=fing,palm=palm)
def summarize(m):
    cs=m['comps']
    if not cs: return dict(n=0)
    # thumb = the component whose base is closest to the wrist, if it is at an end of the row
    ends=[0,len(cs)-1] if len(cs)>1 else [0]
    th=min(ends,key=lambda k:cs[k]['u0']) if len(cs)>=4 else None
    fing=[c for k,c in enumerate(cs) if k!=th]
    base=float(np.median([c['u0'] for c in fing])) if fing else None
    longest=max((c['u1']-c['u0'] for c in fing),default=None)
    return dict(n=len(cs),thumb_idx=th,thumb_v=(cs[th]['v'] if th is not None else None),palm_len=base,longest=longest,L=m['L'],order_v=[round(c['v'],1) for c in cs])
