"""Hair motion measurement on Clean-room reference videos (read-only analysis).
Per frame: face (skin) centroid + head tilt, hair mask (dark non-blue near head), core vs loose strands,
bun centroid, Farneback flow of hair minus face. Then lag (xcorr), period (autocorr/zero-crossings),
settle, overshoots, sway angle, and a driven damped-spring fit (f, zeta) hair_abs ~ spring(head)."""
import cv2, numpy as np, json, sys, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/workspace/shadowveil/hair/qa/grok_ref'
def frames(p):
    cap=cv2.VideoCapture(p); fps=cap.get(cv2.CAP_PROP_FPS); F=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        F.append(f)
    return fps,F
def measure(f,prev_gray=None,prev_masks=None):
    b,g,r=[f[...,i].astype(int) for i in range(3)]
    blue=(b-np.maximum(r,g)>40)
    hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV); H,S,V=[hsv[...,i].astype(int) for i in range(3)]
    fg=~blue; ys,xs=np.where(fg); top=ys.min()
    skin=(H>=4)&(H<=25)&(S>70)&(V>90)
    dark=(V<95)&~blue
    y0,y1=top,top+185
    sk=skin.copy(); sk[:y0]=0; sk[y1:]=0
    # restrict to the column band of the hair near top (head)
    hr=dark[top:top+60]; hx=np.where(hr.any(0))[0]; cx0=np.median(np.where(hr)[1]) if hr.any() else f.shape[1]/2
    band=np.zeros_like(sk); band[:,int(cx0-95):int(cx0+95)]=1; sk&=band.astype(bool)
    # keep largest skin component (face)
    n,lab,st,cen=cv2.connectedComponentsWithStats(sk.astype(np.uint8))
    if n<2: return None
    k=1+np.argmax(st[1:,4]); face=lab==k
    fyv,fxv=np.where(face); 
    # face: only upper part above chin estimate: rows where width is > 40% of max (drop neck)
    rows=np.bincount(fyv-top,minlength=200); mx=rows.max()
    chin=top+np.where(rows>0.35*mx)[0].max()
    face&=(np.arange(f.shape[0])[:,None]<=chin)
    fyv,fxv=np.where(face); fx,fy=fxv.mean(),fyv.mean()
    hm=dark.copy(); hm[:top]=0; hm[chin+45:]=0; hmb=np.zeros_like(hm); hmb[:,int(fx-120):int(fx+120)]=1; hm&=hmb.astype(bool)
    # remove eyes/brows/mouth dark pixels inside the face hull
    fh=cv2.convexHull(np.stack([fxv,fyv],1).astype(np.int32)); fhm=np.zeros(hm.shape,np.uint8); cv2.fillConvexPoly(fhm,fh,1)
    fhm=cv2.dilate(fhm,np.ones((7,7),np.uint8)); hm&=~fhm.astype(bool)
    yy,xx=np.mgrid[0:hm.shape[0],0:hm.shape[1]]; hm&=~((yy>chin-10)&(np.abs(xx-fx)<36))  # drop jaw/neck line art
    hyv,hxv=np.where(hm)
    if len(hyv)<200: return None
    core=cv2.morphologyEx(hm.astype(np.uint8),cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11))).astype(bool)
    loose=hm&~cv2.dilate(core.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    htop=hyv.min(); hh=chin-htop
    bun=hm&(np.arange(f.shape[0])[:,None]<htop+0.22*hh)
    byv,bxv=np.where(bun)
    # head tilt: orientation of (face + hair core) blob
    head=(face|core).astype(np.uint8); m=cv2.moments(head,True)
    tilt=0.5*np.degrees(np.arctan2(2*m['mu11'],m['mu20']-m['mu02']))  # ~ +-90 for vertical blob
    tilt=(tilt-90) if tilt>0 else (tilt+90)
    ly,lx=np.where(loose&(np.arange(f.shape[0])[:,None]>fy-10))  # loose strands below eye line (hanging tendrils)
    L=lx<fx; Rr=lx>=fx
    def ang(xx,yy):  # angle of strand mass about temple pivot, 0 = straight down, + = toward screen-right
        if len(xx)<15: return np.nan
        return np.degrees(np.arctan2(xx.mean()-px,yy.mean()-py))
    px,py=fx,fy-35
    res=dict(top=top,fx=fx,fy=fy,chin=chin,tilt=tilt,hx=hxv.mean(),hy=hyv.mean(),bx=bxv.mean() if len(bxv) else np.nan,by=byv.mean() if len(byv) else np.nan,
             nloose=int(loose.sum()),lx=lx.mean() if len(lx) else np.nan,ly=ly.mean() if len(ly) else np.nan,
             angL=ang(lx[L],ly[L]),angR=ang(lx[Rr],ly[Rr]),
             tipL=float(ly[L].max()-fy) if L.sum()>15 else np.nan, tipR=float(ly[Rr].max()-fy) if Rr.sum()>15 else np.nan)
    gray=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
    if prev_gray is not None:
        Y0=max(0,top-30);Y1=min(f.shape[0],top+300);X0=max(0,int(fx)-180);X1=min(f.shape[1],int(fx)+180)
        fl=np.zeros(f.shape[:2]+(2,),np.float32)
        fl[Y0:Y1,X0:X1]=cv2.calcOpticalFlowFarneback(prev_gray[Y0:Y1,X0:X1],gray[Y0:Y1,X0:X1],None,0.5,3,15,3,5,1.2,0)
        pf,ph,pl=prev_masks
        res['flow_face_x']=float(fl[...,0][pf].mean()); res['flow_hair_x']=float(fl[...,0][ph].mean())
        res['flow_loose_x']=float(fl[...,0][pl].mean()) if pl.sum()>20 else np.nan
        res['flow_face_y']=float(fl[...,1][pf].mean()); res['flow_hair_y']=float(fl[...,1][ph].mean())
    return res,gray,(face,hm,loose),(face,hm,loose,core,bun)
def stream(path,maxrows=460):
    cap=cv2.VideoCapture(path)
    while True:
        ok,f=cap.read()
        if not ok: break
        yield np.ascontiguousarray(f[:maxrows])  # head/hair region only; frames streamed, never all in RAM
def run(path,tag):
    cap=cv2.VideoCapture(path); fps=cap.get(cv2.CAP_PROP_FPS); nfr=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
    rows=[]; pg=None; pm=None; dbg=None
    for i,f in enumerate(stream(path)):
        o=measure(f,pg,pm)
        if o is None: rows.append(None); pg=None; continue
        r,pg,pm,ms=o; rows.append(r)
        if i==nfr//2: dbg=(f.copy(),ms)
    keys=sorted({k for r in rows if r for k in r})
    D={k:np.array([ (r.get(k,np.nan) if r else np.nan) for r in rows],float) for k in keys}
    D['fps']=fps; D['n']=len(rows)
    if dbg:
        f,(face,hm,loose,core,bun)=dbg; v=f.copy(); v[core]=(0,255,255); v[loose]=(0,0,255); v[bun]=(0,255,0); v[face]=(v[face]*0.5+np.array([255,0,255])*0.5).astype(np.uint8)
        t=int(np.nanmin(D['top'])); cv2.imwrite(f'{OUT}/mask_debug_{tag}.png',v[max(0,t-10):t+260,:])
    return D
if __name__=='__main__':
    src=sys.argv[1]; tag=sys.argv[2]
    D=run(src,tag); np.savez(f'/tmp/gr/sig_{tag}.npz',**{k:np.asarray(v) for k,v in D.items()})
    print(tag,'fps',D['fps'],'n',D['n'],'valid',int(np.isfinite(D['fx']).sum()))
