# Reference measurement only: reads the Grok clean-room mp4s, never writes outside reference_timing/.
import subprocess, numpy as np, json, sys, os
from scipy import ndimage as ndi
from PIL import Image
VID='/workspace/shadowveil/reference/grok_build/public/clean-room/videos'
OUT='/workspace/shadowveil/mouth/work/reference_timing'
CX0,CY0,CW,CH=230,40,310,320          # crop of the head region (video px)
UP=4                                   # analysis upscale (bicubic) around the mouth
def frames(clip):
    p=subprocess.Popen(['ffmpeg','-v','error','-i',f'{VID}/{clip}.mp4','-vf',f'crop={CW}:{CH}:{CX0}:{CY0}',
                        '-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    n=CW*CH*3
    while True:
        b=p.stdout.read(n)
        if len(b)<n: break
        yield np.frombuffer(b,np.uint8).reshape(CH,CW,3)
    p.wait()
def lumf(a): return a[...,:3].astype(float)@[0.299,0.587,0.114]
def classify(a, skin_l):
    """a: RGB float crop. Returns mouth mask (lips+opening), opening mask (cavity/teeth/tongue)."""
    r,g,b=a[...,0],a[...,1],a[...,2]; l=lumf(a)
    blue=(b>r+30)
    dark=(l<skin_l-28)&~blue                       # lips, outline, cavity
    teeth=(l>skin_l+45)&(np.abs(r-b)<45)&~blue    # whites brighter than skin, low chroma
    tongue=(r-g>55)&(l<skin_l-10)&~blue
    cav=(l<25)&~blue                               # her cavity is near-black; her lips are 45-90
    return dark,teeth,tongue,cav
def measure(a, prev, skin_l, win=(40,26)):
    """a: RGB crop (video px). prev: (x,y) mouth centre in crop coords."""
    px,py=prev; wx,wy=win
    x0,y0=int(px-wx),int(py-wy); sub=a[y0:y0+2*wy,x0:x0+2*wx].astype(float)
    big=np.array(Image.fromarray(sub.astype(np.uint8)).resize((2*wx*UP,2*wy*UP),Image.BICUBIC)).astype(float)
    dark,teeth,tongue,cav=classify(big,skin_l)
    lab,n=ndi.label(ndi.binary_closing(dark|teeth|tongue,iterations=UP))
    if n==0: return None
    cy_,cx_=wy*UP,wx*UP
    # component with most pixels within 12 px (video) of the previous centre
    yy,xx=np.mgrid[:big.shape[0],:big.shape[1]]
    near=(np.hypot(yy-cy_,xx-cx_)<12*UP)
    counts=ndi.sum(near,lab,range(1,n+1)); k=int(np.argmax(counts))+1
    if counts[k-1]<4*UP*UP: return None
    m=ndi.binary_fill_holes(lab==k)
    ys,xs=np.nonzero(m)
    W=(xs.max()-xs.min()+1)/UP; Ht=(ys.max()-ys.min()+1)/UP
    # opening = cavity/teeth/tongue strictly inside the mouth (eroded 1 video px so the outline doesn't count)
    inner=ndi.binary_erosion(m,iterations=UP)
    op=(cav|teeth|tongue)&inner
    op=ndi.binary_opening(op,iterations=1)           # drop 1-subpixel specks
    lo,ho=ndi.label(op)                                # keep only opening blobs that contain real cavity or teeth
    if ho:                                             # (reddish closed lips can pass the tongue colour test)
        seed=ndi.sum((cav|teeth)&op,lo,range(1,ho+1)); keep=[k+1 for k in range(ho) if seed[k]>=UP*UP]
        op=np.isin(lo,keep)
    oys,oxs=np.nonzero(op)
    if len(oys):
        c0,c1=xs.min(),xs.max(); spans=[]
        for c in range(int(c0+0.3*(c1-c0)),int(c0+0.7*(c1-c0))+1):
            r=np.nonzero(op[:,c])[0]; spans.append((r.max()-r.min()+1) if len(r) else 0)
        OH=max(spans)/UP; OW=(oxs.max()-oxs.min()+1)/UP
    else: OH=OW=0.0
    teeth_px=(teeth&inner).sum()/UP**2; tongue_px=(tongue&inner).sum()/UP**2
    # corners: mean y of the 2 leftmost / rightmost columns; centre: mid-row of the mouth mask at the centre column
    def coly(c): r=np.nonzero(m[:,c])[0]; return (r.min()+r.max())/2
    lx,rx=xs.min(),xs.max(); cxm=(lx+rx)//2
    yL=np.mean([coly(c) for c in range(lx,lx+UP)]); yR=np.mean([coly(c) for c in range(rx-UP+1,rx+1)]); ycor=(yL+yR)/2
    # seam / opening centre line at the centre column
    col=op[:,cxm-UP:cxm+UP+1].any(1); r=np.nonzero(col)[0]
    if len(r): yc=(r.min()+r.max())/2
    else:      # closed: darkest row near the centre column inside the mouth
        l=lumf(big[:,cxm-UP:cxm+UP+1]).mean(1); l[~m[:,cxm]]=999; yc=float(np.argmin(l))
    # mouth centre in crop coordinates for tracking
    ncx=x0+(lx+rx)/2/UP; ncy=y0+(ys.min()+ys.max())/2/UP
    # face width (skin run through the mouth centre column, 12 video px above the mouth centre = nose/cheek level)
    fy=int(round(ncy))-12; row=a[fy].astype(float); rl=lumf(row); sk=(np.abs(rl-skin_l)<25)&(row[:,2]<row[:,0])
    c=int(round(ncx)); L_=c
    while L_>0 and sk[L_-1:L_+1].any() if False else (L_>0 and sk[L_-1]): L_-=1
    R_=c
    while R_<len(sk)-1 and sk[R_+1]: R_+=1
    faceW=float(R_-L_+1)
    return dict(faceW=faceW,W=W,Hmouth=Ht,openH=OH,openW=OW,teeth=float(teeth_px),tongue=float(tongue_px),
                cornerLift=(yc-ycor)/UP, cornerDy=(yL-yR)/UP, cx=ncx+CX0, cy=ncy+CY0, _new=(ncx,ncy), _big=big, _m=m, _op=op)
def eye_dist(a,prev):
    """distance between her orange (screen-left) and green (screen-right) iris centroids, video px"""
    px,py=int(prev[0]),int(prev[1]); y0=max(py-95,0); sub=a[y0:py-15,max(px-70,0):px+70].astype(int)
    r,g,b=sub[...,0],sub[...,1],sub[...,2]
    green=(g>r+8)&(g>b+25)&(g>70)
    orange=(r>g+30)&(g>b+50)&(r>140)
    cs=[]
    for m in (orange,green):
        lab,n=ndi.label(m)
        if n==0: return None
        sz=ndi.sum(m,lab,range(1,n+1)); k=int(np.argmax(sz))+1
        if sz[k-1]<5: return None
        cs.append(ndi.center_of_mass(lab==k))
    d=float(np.hypot(cs[0][0]-cs[1][0],cs[0][1]-cs[1][1]))
    ang=float(np.degrees(np.arctan2(cs[1][0]-cs[0][0],cs[1][1]-cs[0][1])))
    return (d,ang) if d>20 else None
def skin_level(a,prev):
    px,py=int(prev[0]),int(prev[1])
    s=a[py-30:py-18,px-14:px+14].astype(float)       # cheeks/upper lip skin above the mouth
    l=lumf(s); return float(np.median(l))
if __name__=='__main__':
    clips=sys.argv[1:]
    start=json.load(open(f'{OUT}/start.json')) if os.path.exists(f'{OUT}/start.json') else {}
    for clip in clips:
        prev=tuple(start.get(clip,(383-CX0,182-CY0))); rows=[]; last=None; crops=[]
        for i,a in enumerate(frames(clip)):
            skin=skin_level(a,prev)
            r=measure(a,prev,skin)
            if i==0: fixp=(int(prev[0]),int(prev[1]))
            px_,py_=fixp; mc=a[py_-14:py_+14,px_-22:px_+22].astype(np.int16)   # fixed window: raw pixel change, no tracking shift
            dup=0.0 if last is None or last.shape!=mc.shape else float(np.abs(mc-last).mean()); last=mc
            if r is None: rows.append(dict(clip=clip,frame=i,t_ms=round(i*1000/24,1),ok=0,frameDiff=round(dup,2))); continue
            if abs(r['_new'][0]-prev[0])<8 and abs(r['_new'][1]-prev[1])<8: prev=r['_new']
            ed=eye_dist(a,prev)
            rows.append(dict(clip=clip,frame=i,t_ms=round(i*1000/24,1),ok=1,frameDiff=round(dup,2),skinL=round(skin,1),eyeD=(round(ed[0],2) if ed else None),roll=(round(ed[1],1) if ed else None),
                **{k:(round(v,2) if isinstance(v,float) else v) for k,v in r.items() if not k.startswith('_')}))
            if i%3==0 or True:
                v=r['_big'].astype(np.uint8).copy(); e=r['_m']^ndi.binary_erosion(r['_m']); v[e]=(0,255,0); v[r['_op']&~ndi.binary_erosion(r['_op'])]=(255,0,255)
                crops.append(np.concatenate([r['_big'].astype(np.uint8),v],1))
        json.dump(rows,open(f'{OUT}/tmp/{clip}.json','w'))
        np.save(f'{OUT}/tmp/{clip}_crops.npy',np.stack(crops)) if crops else None
        ok=[x for x in rows if x['ok']]
        print(clip,len(rows),'ok',len(ok),'W med %.1f'%np.median([x['W'] for x in ok]) if ok else '', 'openH max %.1f'%max([x['openH'] for x in ok]) if ok else '',flush=True)
