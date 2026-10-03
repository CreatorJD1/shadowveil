# Job 3: residual hair offset on top of the eye-fit head group. Frame segmentation = hair/qa/turn_handoff/measure.py v2 (same key,
# classifier, cleanup, ROI and eye exclusion, best-shift IoU search); the live side is the rig's own render with ?headgroup=1 at the
# eye-fit offsets (render_hg.py masks), so residual = extra hair shift needed on top of the head group. Also mean edge distance.
import json,sys,glob,numpy as np,cv2
from PIL import Image
R='/workspace/shadowveil'; D=R+'/hair/qa/turn_handoff/subofs_eyefit'; W_,Hh=1365,1739
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
    m=np.load(f'{D}/work/{v}_masks.npz'); live=m['hair']; bunm=m['bun']
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
    liveM=live&~eyex
    o=out[v]={'frame':fno,'head_group_eyefit':[hx,hy],'map':H}
    sc,tx,ty=best_shift(liveM,hf)
    o['hair_mass']=dict(dx=tx,dy=ty,iou_at0=round(iou(liveM,hf),3),iou_after=round(float(sc),3),edge_dist_at0=med(liveM,hf),edge_dist_after=med(sh(liveM,tx,ty),hf))
    if bunm.sum()>50:
        ysb,xsb=np.nonzero(bunm); w=np.zeros_like(bunm); w[max(ysb.min()-18,0):ysb.max()+18,max(xsb.min()-18,0):xsb.max()+18]=True
        sb=best_shift(liveM,hf,w)
        o['bun']=dict(dx=sb[1],dy=sb[2],iou_at0=round(iou(liveM&w,hf&w),3),iou_after=round(float(sb[0]),3),edge_dist_at0=med(liveM,hf,w),edge_dist_after=med(sh(liveM,sb[1],sb[2]),hf,sh(w,sb[1],sb[2])),bun_visible_px=int(bunm.sum()))
        # hair mass without the bun window
        nb=~w; sn=best_shift(liveM&nb,hf&nb)
        o['hair_mass_excl_bun']=dict(dx=sn[1],dy=sn[2],iou_after=round(float(sn[0]),3))
    else: o['bun']=dict(visible_px=int(bunm.sum()),note='bun not visible in this view render')
    # overlay
    yy,xx=np.nonzero(liveM|hf); cy0,cy1=max(yy.min()-30,0),min(yy.max()+30,Hh); cx0,cx1=max(xx.min()-30,0),min(xx.max()+30,W_)
    img=despilled[cy0:cy1,cx0:cx1].astype(np.float32); kb=alpha[cy0:cy1,cx0:cx1]<=0.5; img[kb]=img[kb]*0.3+235*0.7; img=img.astype(np.uint8).copy()
    fc=hf[cy0:cy1,cx0:cx1]; img[fc]=(img[fc]*0.55+np.array([255,140,0])*0.45).astype(np.uint8)
    for mm,col in ((liveM,(0,255,255)),(bunm,(255,0,255))):
        c,_=cv2.findContours(mm[cy0:cy1,cx0:cx1].astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE); cv2.drawContours(img,c,-1,col,1)
    big=cv2.resize(img,None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST)
    t=f"{v} f{fno:03d} HG {hx:+d},{hy:+d} | hair resid {tx:+d},{ty:+d} IoU {o['hair_mass']['iou_at0']:.2f}->{o['hair_mass']['iou_after']:.2f}"+(f" | bun {o['bun']['dx']:+d},{o['bun']['dy']:+d}" if 'dx' in o['bun'] else '')
    cv2.putText(big,t,(10,28),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),3); cv2.putText(big,t,(10,28),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),1)
    cv2.putText(big,'orange=frame hair  cyan=rig hair (headgroup, eye-fit)  magenta=bun',(10,54),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),1)
    Image.fromarray(big).save(f'{D}/overlay_{v}_f{fno:03d}.png')
    print(v,json.dumps(o),flush=True)
json.dump(out,open(f'{D}/subofs.json','w'),indent=1)
