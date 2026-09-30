# Read-only helpers for Base Hair idle-battle QA. Never writes outside hair/qa/idle_battle/.
import json, os, math, subprocess
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
P='/workspace/shadowveil'; IDLE=P+'/rig/previews/idle'; OUT=P+'/hair/qa/idle_battle'
W,H=1365,1739; VW,VH=1366,1740; FPS=30
PIV=(681.5,706.0)
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1]; return (x*x+y*y<=r*r).astype(np.uint8)
def rotAt(px,py,deg):
    if not abs(deg)>=0.01: return np.array([[1,0,0],[0,1,0],[0,0,1]],float)
    t=math.radians(deg); c,s=math.cos(t),math.sin(t)
    return np.array([[c,-s,px-c*px+s*py],[s,c,py-s*px-c*py],[0,0,1]],float)
def T(dx,dy): return np.array([[1,0,dx],[0,1,dy],[0,0,1]],float)
def alpha(path):
    return np.array(Image.open(path).convert('RGBA'))[...,3]
class View:
    def __init__(s,v):
        s.v=v; d=f'{P}/views/{v}'
        rig=json.load(open(f'{d}/hair/rig.json')); s.ymax=float(rig.get('swayYMaxPx',0)); s.parts=[p for p in rig['parts'] if p.get('file')]
        s.by={p['id']:p for p in s.parts}
        full={p['id']:np.array(Image.open(f"{d}/hair/{p['file']}").convert('RGBA')) for p in s.parts}
        hu=np.zeros((H,W),bool)
        for a in full.values(): hu|=a[...,3]>0
        ys,xs=np.nonzero(hu); pad=90
        s.x0,s.y0=max(0,xs.min()-pad),max(0,ys.min()-pad); s.x1,s.y1=min(W,xs.max()+pad+1),min(H,ys.max()+pad+1)
        # make even sizes for ffmpeg crop
        if (s.x1-s.x0)%2: s.x1-=1
        if (s.y1-s.y0)%2: s.y1-=1
        s.x0,s.y0,s.x1,s.y1=map(int,(s.x0,s.y0,s.x1,s.y1)); s.w,s.h=s.x1-s.x0,s.y1-s.y0
        c=lambda a:a[s.y0:s.y1,s.x0:s.x1]
        s.pa={k:c(a[...,3]).astype(np.float32)/255 for k,a in full.items()}
        s.prgb={k:c(a[...,:3]) for k,a in full.items()}
        s.hair_union=c(hu)
        s.Mhead=cv2.dilate(s.hair_union.astype(np.uint8),disk(30))>0   # head/neck mask (hair alpha dilated 30 px)
        sway=[k for k,p in s.by.items() if (p.get('swayWeight') or 0)!=0 or (p.get('swayY') or 0)!=0]
        s.sway=sway; s.static=[k for k in s.by if k not in sway and k!='bun']
        # colour clusters of hair (dark neutral pixels of hair parts)
        px=np.concatenate([a[a[...,3]==255][:,:3] for a in full.values()]).astype(np.float32)
        dark=px[(px.max(1)<=110)&((px.max(1)-px.min(1))<=14)]
        crit=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,0.5)
        _,_,cent=cv2.kmeans(dark[::max(1,len(dark)//20000)],6,None,crit,3,cv2.KMEANS_PP_CENTERS)
        s.hair_centres=cent; s.hair_px_total=len(px); s.hair_px_dark=len(dark)
        # base.png composited on the video grey
        b=np.array(Image.open(f'{d}/base.png').convert('RGBA')).astype(np.float32)
        comp=b[...,:3]*b[...,3:]/255+128*(1-b[...,3:]/255)
        s.base_comp=c(comp).round().astype(np.uint8); s.base_a=c(b[...,3])
        # face boxes (union alpha bbox of all eye / mouth parts), converted to ROI coords
        bx=json.load(open(OUT+'/work/boxes.json'))[v]
        s.boxes={k:bx[k]['all'] for k in ('EyeR','EyeL','mouth') if k in bx}
        s.boxmask=np.zeros((s.h,s.w),bool); s.boxm={}
        for k,(a0,b0,a1,b1) in s.boxes.items():
            m=np.zeros((s.h,s.w),bool); m[b0-s.y0:b1-s.y0+1,a0-s.x0:a1-s.x0+1]=True; s.boxm[k]=m; s.boxmask|=m
        # what is behind the swaying parts at rest: static hair, body (hair cleared), face parts
        beh=c(alpha(f'{d}/base_body.png'))>0
        for k in s.static: beh|=s.pa[k]>0
        for owner in ('eyes','mouth'):
            rp=f'{d}/{owner}/rig.json'
            if os.path.exists(rp) and v!='back':
                j=json.load(open(rp)); ps=j if isinstance(j,list) else j.get('parts',[])
                for q in ps:
                    f=q.get('file')
                    if f and ('rest' in f or '_white' in f or '_lash' in f or '_lid_0' in f): beh|=c(alpha(f'{d}/{owner}/{f}'))>0
        s.behind=beh
        s.sil=nd.binary_fill_holes(cv2.morphologyEx(beh.astype(np.uint8),cv2.MORPH_CLOSE,disk(5))>0)
        s.erase=c(np.array(Image.open(f'{P}/hair/{v}_hair_erase_mask.png').convert('L')))>0
        s.layers={k:p['layer'] for k,p in s.by.items()}
        # chains / leaves / tips
        kids={}
        for k,p in s.by.items():
            if p.get('parent') in s.by: kids.setdefault(p['parent'],[]).append(k)
        s.kids=kids
        def root(k):
            while s.by[k].get('parent') in s.by and s.by[s.by[k]['parent']] and s.by[k]['parent'] not in ('hair_front','hair_back'): k=s.by[k]['parent']
            return k
        s.tips={}
        for k in s.by:
            if not k.startswith('strand') or k in kids: continue
            r=root(k); p=s.by[r]; ys_,xs_=np.nonzero(s.pa[k]>0.5)
            dd=(xs_+s.x0-p['pivotX'])**2+(ys_+s.y0-p['pivotY'])**2; i=int(dd.argmax())
            s.tips[r]=(k,float(xs_[i]),float(ys_[i]))   # ROI coords
    def roi_M(s,Mfull):
        # express a full-canvas affine in ROI coords
        return T(-s.x0,-s.y0)@Mfull@T(s.x0,s.y0)
    def hair_M(s,hair,rest=False):
        # per-part local (head-relative) transform, following rig/index.html: M = T(0,dy) * chain rotation
        rot={}
        def m(k):
            if k in rot: return rot[k]
            p=s.by[k]; par=p.get('parent'); base=m(par) if par in s.by else np.eye(3)
            d=hair.get(k,[0,0]) if hair else [0,0]
            a=0 if rest else (p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)*max(-1,min(1,d[0]))
            rot[k]=base@rotAt(p.get('pivotX',0),p.get('pivotY',0),a); return rot[k]
        out={}
        for k,p in s.by.items():
            d=hair.get(k,[0,0]) if hair else [0,0]
            dy=0 if rest else round(max(-1,min(1,d[1]))*max(0,min(1,float(p.get('swayY') or 0)))*s.ymax)
            out[k]=T(0,dy)@m(k)
        return out
    def hairlike(s,img):
        f=img.astype(np.float32); mx=f.max(-1); mn=f.min(-1)
        d=np.min(np.stack([np.linalg.norm(f-c_,axis=-1) for c_ in s.hair_centres]),0)
        return (mx<=100)&((mx-mn)<=12)&(d<=22)
def cls_white(img):
    f=img.astype(np.int16); return (f.min(-1)>=225)&((f.max(-1)-f.min(-1))<=25)
def cls_blue(img):
    f=img.astype(np.int16); return (f[...,2]>=150)&(f[...,0]<=100)&(f[...,1]<=100)&(f[...,2]-np.maximum(f[...,0],f[...,1])>=80)
def cls_grey(img):
    f=img.astype(np.int16); return (np.abs(f-128)<=6).all(-1)
def stream(path,x0,y0,w,h,scale=None):
    vf=f'crop={w}:{h}:{x0}:{y0}'
    cmd=['nice','-n','10','ffmpeg','-v','error','-threads','1','-i',path,'-vf',vf,'-f','rawvideo','-pix_fmt','rgb24','-']
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,bufsize=w*h*3)
    n=w*h*3; i=0
    try:
        while True:
            b=p.stdout.read(n)
            if len(b)<n: break
            yield i,np.frombuffer(b,np.uint8).reshape(h,w,3); i+=1
    finally:
        p.stdout.close(); p.wait()
def warp(img,M3,w,h,nearest=False):
    return cv2.warpAffine(img,M3[:2].astype(np.float64),(w,h),flags=cv2.INTER_NEAREST if nearest else cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
# Clip names: v1 renders use idle_breathe; Body renamed it idle_arm_sway for v2. Missing clips are skipped.
CLIPS=['idle_breathe','idle_arm_sway','idle_weight_shift','idle_arm_settle']
VIEWS=['apose','tpose','left','right','back']
def available_names():
    names=[]
    for n,vid in [(v,f'{IDLE}/{v}_idle.mp4') for v in VIEWS]+[('apose_hair_stiff',f'{IDLE}/apose_idle_hair_stiff.mp4'),('apose_hair_middle',f'{IDLE}/apose_idle_hair_middle.mp4')]+[(f'keys_{c}_{v}',f'{IDLE}/keys/{c}_{v}.mp4') for c in CLIPS for v in VIEWS]:
        if os.path.exists(vid) and os.path.exists(f'{IDLE}/frames/{n}/meta.json'): names.append(n)
    return names
def available_clips():
    return [c for c in CLIPS if os.path.exists(f'{IDLE}/keys/{c}_all5.mp4')]
