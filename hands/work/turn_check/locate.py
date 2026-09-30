import cv2,numpy as np,json
from scipy import ndimage as ndi
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/apose-turn.mp4'
def fg(im):
    im=im.astype(int); return ~((im[...,2]>120)&(im[...,2]>im[...,0]+60)&(im[...,2]>im[...,1]+60))
def arms(m,top,H):
    y0=int(top+0.40*H); sub=m.copy(); sub[:y0]=False
    lab,n=ndi.label(sub); out=[]
    for k in range(1,n+1):
        ys,xs=np.nonzero(lab==k)
        if len(ys)<400 or ys.max()>=m.shape[0]-5 or ys.max()>top+0.95*H: continue
        # distal tip = farthest from the component's top point
        i0=np.argmin(ys); t0=np.array([xs[i0],ys[i0]]); d=np.hypot(xs-t0[0],ys-t0[1]); j=np.argmax(d); tip=np.array([xs[j],ys[j]])
        out.append(dict(k=k,area=len(ys),top=t0.tolist(),tip=tip.tolist(),mask=(lab==k)))
    return out
def wrist_cut(comp,scale):
    m=comp['mask']; t0=np.array(comp['top'],float); tip=np.array(comp['tip'],float); ys,xs=np.nonzero(m); P=np.stack([xs,ys],1).astype(float)
    # local axis from the last 110*scale px of the arm
    near=np.hypot(*(P-tip).T)<110*scale; Q=P[near]; mu=Q.mean(0); d=np.linalg.svd(Q-mu,full_matrices=False)[2][0]
    if np.dot(d,tip-mu)<0: d=-d
    pu=(P-tip)@d; pv=(P-tip)@np.array([-d[1],d[0]])
    best=None
    for s in np.arange(-110*scale,-40*scale,1.0):
        sel=np.abs(pu-s)<0.7
        if sel.sum()<2: continue
        w=np.ptp(pv[sel])
        if best is None or w<best[1]: best=(s,w)
    s,w=best; sel=np.abs(pu-s)<0.7; wr=tip+d*s+np.array([-d[1],d[0]])*np.median(pv[sel])
    hand=np.zeros_like(m); hp=P[pu>s].astype(int); hand[hp[:,1],hp[:,0]]=True
    return dict(wrist=wr.tolist(),axis=d.tolist(),wrist_width=float(w),hand=hand)
