# Job 3: residual hair offset on top of the eye-fit head group. Frame segmentation = hair/qa/turn_handoff/measure.py v2 (same key,
# classifier, cleanup, ROI and eye exclusion, best-shift IoU search); the live side is the rig's own render with ?headgroup=1 at the
# eye-fit offsets (render_hg.py masks), so residual = extra hair shift needed on top of the head group. Also mean edge distance.
import json,sys,glob,numpy as np,cv2
from PIL import Image
R='/workspace/shadowveil'; D=R+'/rig/work/hgsubhair'; W_,Hh=1365,1739
HG={'apose':(0,-9),'left':(0,11),'back':(2,11),'right':(3,5)}
def A(p): return np.asarray(Image.open(p).getchannel('A'))
def iou(a,b): u=(a|b).sum(); return float((a&b).sum()/u) if u else float('nan')
def best_shift(L,F,win=None,rng=20):
    ys,xs=np.nonzero(L if win is None else win); pad=rng+2
    a0,a1,b0,b1=max(ys.min()-pad,0),min(ys.max()+pad,Hh),max(xs.min()-pad,0),min(xs.max()+pad,W_)
    Lc=L[a0:a1,b0:b1]; Fc=F[a0:a1,b0:b1]; Wc=None if win is None else win[a0:a1,b0:b1]; best=(-1,0,0)
    for ty in range(-rng,rng+1):
        for tx in range(-rng,rng+1):
            Ls=np.roll(np.roll(Lc,ty,0),tx,1)
            if Wc is not None: Ws=np.roll(np.roll(Wc,ty,0),tx,1); i=(Ls&Fc&Ws).sum(); u=((Ls|Fc)&Ws).sum()
            else: i=(Ls&Fc).sum(); u=(Ls|Fc).sum()
            sc=i/u if u else 0
            if sc>best[0]: best=(sc,tx,ty)
    return best
def edge(m): return (m.astype(np.uint8)-cv2.erode(m.astype(np.uint8),np.ones((3,3),np.uint8)))>0
def med(a,b,win=None):
    if win is not None: a=a&win; b=b&win
    ea,eb=edge(a),edge(b)
    if not ea.any() or not eb.any(): return None
    da=cv2.distanceTransform((~eb).astype(np.uint8),cv2.DIST_L2,3); db=cv2.distanceTransform((~ea).astype(np.uint8),cv2.DIST_L2,3)
    return round(float((da[ea].mean()+db[eb].mean())/2),2)
sh=lambda m,tx,ty:np.roll(np.roll(m,ty,0),tx,1)
out={}
for v,(hx,hy) in HG.items():
    H=json.load(open(R+'/body_tools/work/apose_turn/angle_map.json'))['handoff'][v]; s,dx,dy,fno=H['scale'],H['dx'],H['dy'],H['frame']
    M2={md:np.load(f'{D}/m/{v}_{md}_masks.npz') for md in ('off','on')}; live=M2['off']['hair']|M2['on']['hair']; bunm=M2['off']['bun']
    fr=np.asarray(Image.open(f'{R}/reference/apose_turn/frames/f{fno:03d}.png').convert('RGB'))
    fm=cv2.warpAffine(fr,np.array([[s,0,dx],[0,s,dy]],np.float32),(W_,Hh),flags=cv2.INTER_LINEAR,borderValue=(0,0,255)).astype(np.float32)
    r,g,b=fm[...,0],fm[...,1],fm[...,2]; spill=np.clip(b-np.maximum(r,g),0,None); alpha=1-np.clip(spill/250.0,0,1); bd=np.minimum(b,np.maximum(r,g))
    fg=alpha>0.5; mx=np.maximum(np.maximum(r,g),bd)/np.maximum(alpha,1e-3); brown=(r-bd)/np.maximum(alpha,1e-3); hair_c=fg&(mx<85)&(brown<28)
    despilled=np.dstack([r,g,bd]).clip(0,255).astype(np.uint8)
    ys,xs=np.nonzero(live); x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
    roi=np.zeros((Hh,W_),bool); roi[max(y0-60,0):min(y1+45,Hh),max(x0-70,0):min(x1+70,W_)]=True
    eyem=np.zeros((Hh,W_),bool)
    for f in glob.glob(f'{R}/views/{v}/eyes/*.png'):
        if 'chroma' in f or not ('_white' in f or '_lid_0' in f or '_lash' in f): continue
        eyem|=A(f)>127
    eyem=sh(eyem,hx,hy)                                   # eyes ride with the head group
    eyex=cv2.dilate(eyem.astype(np.uint8),np.ones((15,15),np.uint8))>0
    if eyem.any():
        ey,ex=np.nonzero(eyem); band=np.zeros_like(eyex); band[max(ey.min()-28,0):ey.max()+8,ex.min()-10:ex.max()+10]=True
        eyex|=band&~cv2.dilate(live.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    hf=hair_c&roi&~eyex
    hf=cv2.morphologyEx(hf.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(hf,8); keep=np.zeros(n,bool); keep[1:]=st[1:,4]>=40; hf=keep[lab]
    inv=(~hf).astype(np.uint8); n,lab,st,_=cv2.connectedComponentsWithStats(inv,4); small=np.zeros(n,bool); small[1:]=st[1:,4]<600; hf|=small[lab]
    bun_u=M2['off']['bun']|M2['on']['bun']
    if bun_u.sum()>50:
        ysb,xsb=np.nonzero(bun_u); w=np.zeros_like(bun_u); w[max(ysb.min()-18,0):ysb.max()+18,max(xsb.min()-18,0):xsb.max()+18]=True
    else: w=np.zeros_like(bun_u)
    nb=~w; o=out[v]={'frame':fno,'head_group':[hx,hy]}
    for md in ('off','on'):
        L=M2[md]['hair']&~eyex
        r=dict(mass_edge=med(L,hf),mass_iou=round(iou(L,hf),3),exbun_edge=med(L&nb,hf&nb),exbun_iou=round(iou(L&nb,hf&nb),3))
        if w.any(): r.update(bun_edge=med(L,hf,w),bun_iou=round(iou(L&w,hf&w),3))
        o[md]=r
    # see-through holes (enclosed transparent px) and face visibility, off vs on
    from scipy import ndimage as nd
    def holes(a):
        lab,n=nd.label(~a);bd=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]));return np.isin(lab,[k for k in range(1,n+1) if k not in bd])
    Fo=np.asarray(Image.open(f'{D}/m/{v}_off_full.png')).astype(int);Fn=np.asarray(Image.open(f'{D}/m/{v}_on_full.png')).astype(int)
    ho,hn=holes(Fo[...,3]>=128),holes(Fn[...,3]>=128); o['new_hole_px']=int((hn&~ho).sum()); o['holes_off_on']=[int(ho.sum()),int(hn.sum())]
    Go=np.asarray(Image.open(f'{D}/m/{v}_off_face.png')).astype(int);Gn=np.asarray(Image.open(f'{D}/m/{v}_on_face.png')).astype(int)
    o['face_solo_px_diff']=int((np.abs(Go-Gn).max(-1)>0).sum())
    vo=(Go[...,3]>0)&(np.abs(Fo[...,:3]-Go[...,:3]).max(-1)<=8);vn=(Gn[...,3]>0)&(np.abs(Fn[...,:3]-Gn[...,:3]).max(-1)<=8)
    o['face_visible_px_off_on']=[int(vo.sum()),int(vn.sum())]; o['face_px_newly_covered']=int((vo&~vn).sum()); o['face_px_newly_shown']=int((vn&~vo).sum())
    fa=(Go[...,3]>0)|(Gn[...,3]>0); o['full_frame_px_changed_in_face']=int(((np.abs(Fo-Fn).max(-1)>0)&fa).sum())
    print(v,json.dumps(o),flush=True)
json.dump(out,open(f'{D}/hairsub_measure.json','w'),indent=1)
