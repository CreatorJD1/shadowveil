import numpy as np,cv2
def handgeo(hand,wrist,axis):
    """Same measurement for video hands and our composites. Axis = wrist->distal direction.
    L = wrist to farthest pixel along axis. Tips = contour peaks beyond 0.5L with prominence >0.06L.
    Valleys = min-distance contour point between consecutive tips. palm_len = median of valley depths
    excluding the shallowest-from-wrist (thumb crotch) when >=3 valleys; palm_w = max width across the axis
    between 0.3 and 0.9 palm_len; finger_len = L - palm_len."""
    u=np.asarray(axis,float); u/=np.linalg.norm(u); v=np.array([-u[1],u[0]]); w0=np.asarray(wrist,float)
    ys,xs=np.nonzero(hand); P=np.stack([xs,ys],1)-w0; pu=P@u; pv=P@v; L=float(pu.max())
    cs,_=cv2.findContours(hand.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=len)[:,0,:].astype(float); d=(c-w0)@u; cvv=(c-w0)@v; n=len(d); win=max(4,n//50)
    pk=[]
    for i in range(n):
        seg=d[[(i+k)%n for k in range(-win,win+1)]]
        if d[i]==seg.max() and d[i]>0.5*L:
            l=min(d[[(i-k)%n for k in range(1,3*win)]]); r=min(d[[(i+k)%n for k in range(1,3*win)]])
            if d[i]-max(l,r)>0.06*L: pk.append(i)
    # merge peaks closer than 0.06L
    keep=[]
    for i in sorted(pk,key=lambda i:-d[i]):
        if all(np.hypot(*(c[i]-c[j]))>0.06*L for j in keep): keep.append(i)
    keep=sorted(keep)
    valleys=[]
    for a,b in zip(keep,keep[1:]):
        seg=range(a,b+1); j=min(seg,key=lambda k:d[k]); valleys.append(float(d[j]))
    vs=sorted(valleys)
    if len(vs)>=3: palm=float(np.median(vs[1:]))
    elif len(vs)>=1: palm=float(max(vs))
    else: palm=None
    pw=None
    if palm:
        ws=[]
        for s_ in np.arange(0.75*palm,0.98*palm,1.0):
            q=np.sort(pv[np.abs(pu-s_)<0.6])
            if len(q)<2: continue
            br=np.nonzero(np.diff(q)>2.0)[0]; seg=np.split(q,br+1); ws.append(max(float(g[-1]-g[0]) for g in seg))
        pw=float(np.median(ws)) if ws else None
    return dict(L=L,W=float(np.ptp(pv)),tips=len(keep),tip_pts=[c[i].tolist() for i in keep],valleys=valleys,palm_len=palm,palm_w=pw,finger_len=(L-palm) if palm else None,tip_v=[float(cvv[i]) for i in keep])
