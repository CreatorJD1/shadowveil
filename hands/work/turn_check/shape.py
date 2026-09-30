import numpy as np,cv2
def shape_metrics(hand,wrist,axis):
    u=np.asarray(axis,float); u/=np.linalg.norm(u); v=np.array([-u[1],u[0]])
    ys,xs=np.nonzero(hand); P=np.stack([xs,ys],1)-np.asarray(wrist,float); pu=P@u; pv=P@v; L=float(pu.max())
    W=float(np.ptp(pv))
    # thumb-side bulge: extent either side of the hand's own midline over 15..55% of L
    mid=np.median(pv[(pu>0.6*L)]) if (pu>0.6*L).any() else 0.0
    band=(pu>0.15*L)&(pu<0.55*L); ext_pos=float(pv[band].max()-mid) if band.any() else 0; ext_neg=float(mid-pv[band].min()) if band.any() else 0
    # fingertips = prominent peaks of distance-from-wrist along the outer contour, beyond 0.5 L
    cs,_=cv2.findContours(hand.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cs,key=len)[:,0,:].astype(float); d=(c-np.asarray(wrist,float))@u; n=len(d); tips=[]
    win=max(6,n//40)
    for i in range(n):
        seg=d[[(i+k)%n for k in range(-win,win+1)]]
        if d[i]==seg.max() and d[i]>0.5*L:
            # prominence: drop on both sides within 3*win
            l=min(d[[(i-k)%n for k in range(1,3*win)]]); r=min(d[[(i+k)%n for k in range(1,3*win)]])
            if d[i]-max(l,r)>0.06*L: tips.append((float(d[i]),c[i].tolist()))
    # merge tips closer than 4 px
    mt=[]
    for t in sorted(tips,key=lambda t:-t[0]):
        if all(np.hypot(t[1][0]-q[1][0],t[1][1]-q[1][1])>0.06*L for q in mt): mt.append(t)
    return dict(L=L,W=W,thumb_bulge_pos=ext_pos,thumb_bulge_neg=ext_neg,thumb_side=('+v' if ext_pos>ext_neg else '-v'),bulge_diff=ext_pos-ext_neg,tips=len(mt),tip_pts=[t[1] for t in mt])
