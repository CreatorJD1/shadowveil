# Read-only QA: live rest hair vs hair drawn in the A-pose turn frames at the 4 handoff frames.
# Writes only under hair/qa/turn_handoff/. Run one view at a time: python3 measure.py <view>
import json,sys,os,glob,gc
import numpy as np, cv2
from PIL import Image
R='/workspace/shadowveil'; OUT=R+'/hair/qa/turn_handoff'
v=sys.argv[1]
H=json.load(open(R+'/body_tools/work/apose_turn/angle_map.json'))['handoff'][v]
s,dx,dy,fno=H['scale'],H['dx'],H['dy'],H['frame']
W,Hh=1365,1739
def A(p): return np.asarray(Image.open(p).getchannel('A'))
# ---------- live visible hair mask (rest composite == base.png) ----------
rig=json.load(open(f'{R}/views/{v}/hair/rig.json'))['parts']
parts={}; lo=np.zeros((Hh,W),bool); hi=np.zeros((Hh,W),bool)
for p in rig:
    a=A(f'{R}/views/{v}/hair/{p["file"]}')>127
    parts[p['id']]=(a,p['layer'])
    if p['layer']<200: lo|=a
    else: hi|=a
occ=A(f'{R}/views/{v}/base_body.png')>127
for sub in ['hands','mouth']:
    for f in glob.glob(f'{R}/views/{v}/{sub}/*.png'):
        if 'chroma' in f: continue
        if sub=='mouth' and not f.endswith('/rest.png'): continue
        if sub=='hands':
            try:
                hj=json.load(open(f'{R}/views/{v}/hands/rig.json')); files={q.get('file') for q in hj['parts']}
                if os.path.basename(f) not in files: continue
            except Exception: pass
        occ|=A(f)>127
eyef=[f for f in glob.glob(f'{R}/views/{v}/eyes/*.png') if 'chroma' not in f and ('_white' in f or '_lid_0' in f or '_lash' in f)]
eyem=np.zeros((Hh,W),bool)
for f in eyef: eyem|=A(f)>127
occ|=eyem
live=hi|(lo&~occ)
vis={k:(a&(~occ if l<200 else True)) for k,(a,l) in parts.items()}
# parts drawn above a lower hair part hide it: keep it simple (bun vs hair_front ordering matters only for display)
del lo,hi
# ---------- mapped frame ----------
fr=np.asarray(Image.open(f'{R}/reference/apose_turn/frames/f{fno:03d}.png').convert('RGB'))
M=np.array([[s,0,dx],[0,s,dy]],np.float32)
fm=cv2.warpAffine(fr,M,(W,Hh),flags=cv2.INTER_LINEAR,borderValue=(0,0,255)).astype(np.float32)
del fr
r,g,b=fm[...,0],fm[...,1],fm[...,2]
spill=np.clip(b-np.maximum(r,g),0,None)          # blue excess
alpha=1-np.clip(spill/250.0,0,1)                  # key alpha
bd=np.minimum(b,np.maximum(r,g))                  # despill
fg=alpha>0.5
# un-premultiply-ish: colour of the fg over black key: rgb/alpha
mx=np.maximum(np.maximum(r,g),bd)/np.maximum(alpha,1e-3)
brown=(r-bd)/np.maximum(alpha,1e-3)
hair_c=fg&(mx<85)&(brown<28)
despilled=np.dstack([r,g,bd]).clip(0,255).astype(np.uint8)
del r,g,b,bd
# ---------- ROI / exclusions ----------
ys,xs=np.nonzero(live); x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
roi=np.zeros((Hh,W),bool); ybot=min(y1+45,Hh)
roi[max(y0-60,0):ybot,max(x0-70,0):min(x1+70,W)]=True
eyex=cv2.dilate(eyem.astype(np.uint8),np.ones((15,15),np.uint8))>0   # eyes/brows/lashes of the rig
# frame's own eyes/brows: dark but coloured/brown excluded by colour; lash black -> use rig eye zone shifted is unsafe, so also use a brow band above the rig eyes
if eyem.any():
    ey,ex=np.nonzero(eyem); band=np.zeros_like(eyex); band[max(ey.min()-28,0):ey.max()+8,ex.min()-10:ex.max()+10]=True
    eyex|=band&~cv2.dilate(live.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)  # keep live-hair pixels (fringe strands crossing)
hair_f=hair_c&roi&~eyex
# clean: remove specks, fill small holes (shine)
hair_f=cv2.morphologyEx(hair_f.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(hair_f,8)
keep=np.zeros(n,bool); keep[1:]=st[1:,4]>=40; hair_f=keep[lab]
inv=(~hair_f).astype(np.uint8); n,lab,st,_=cv2.connectedComponentsWithStats(inv,4)
small=np.zeros(n,bool); small[1:]=st[1:,4]<600; hair_f|=small[lab]
del lab,inv
# same classifier on base.png (sanity ceiling for the classifier)
bp=np.asarray(Image.open(f'{R}/views/{v}/base.png')).astype(np.float32); ba=bp[...,3]/255
bmx=bp[...,:3].max(2); bbr=bp[...,0]-bp[...,2]
base_c=(ba>0.5)&(bmx<85*ba+1)&(bbr<28)&roi&~eyex
del bp
def iou(a,b): u=(a|b).sum(); return float((a&b).sum()/u) if u else float('nan')
def best_shift(L,F,win=None,rng=40):
    # L: live mask, F: frame mask; window (bool) rides with the live mask
    ys,xs=np.nonzero(L if win is None else win); pad=rng+2
    a0,a1,b0,b1=max(ys.min()-pad,0),min(ys.max()+pad,Hh),max(xs.min()-pad,0),min(xs.max()+pad,W)
    Lc=L[a0:a1,b0:b1]; Fc=F[a0:a1,b0:b1]; Wc=None if win is None else win[a0:a1,b0:b1]
    best=(-1,0,0)
    for ty in range(-rng,rng+1):
        for tx in range(-rng,rng+1):
            Ls=np.roll(np.roll(Lc,ty,0),tx,1)
            if Wc is not None:
                Ws=np.roll(np.roll(Wc,ty,0),tx,1); i=(Ls&Fc&Ws).sum(); u=((Ls|Fc)&Ws).sum()
            else: i=(Ls&Fc).sum(); u=(Ls|Fc).sum()
            sc=i/u if u else 0
            if sc>best[0]: best=(sc,tx,ty)
    return best
def centroid(m): ys,xs=np.nonzero(m); return np.array([xs.mean(),ys.mean()])
res={'view':v,'frame':fno,'map':{'scale':s,'dx':dx,'dy':dy}}
res['iou_rest']=iou(live,hair_f)
res['iou_classifier_on_base']=iou(live,base_c)
sc,tx,ty=best_shift(live,hair_f,rng=30); res['silhouette']={'dx':tx,'dy':ty,'iou_after':sc,
  'centroid_dxdy':(centroid(hair_f)-centroid(live)).round(1).tolist()}
# bun window = bun part bbox grown 18px (bun is on top: good outline)
def part_win(m,g=18):
    w=np.zeros_like(m); ys,xs=np.nonzero(m); w[max(ys.min()-g,0):ys.max()+g,max(xs.min()-g,0):xs.max()+g]=True; return w
bunm=parts['bun'][0]
sb=best_shift(live,hair_f,part_win(bunm),rng=30)
res['bun']={'dx':sb[1],'dy':sb[2],'iou_after':sb[0],'iou_at0':iou(live&part_win(bunm),hair_f&part_win(bunm)),'layer':parts['bun'][1]}
hf=vis.get('hair_front')
if hf is not None and hf.sum()>500:
    # fringe window: lower (hairline) half of hair_front's visible area, where it meets the face
    ys,xs=np.nonzero(hf); ymid=int(np.percentile(ys,45)); w=part_win(hf,14); w[:ymid]=False
    sf=best_shift(live,hair_f,w,rng=30)
    res['fringe']={'dx':sf[1],'dy':sf[2],'iou_after':sf[0],'iou_at0':iou(live&w,hair_f&w)}
else: res['fringe']=None
# whole-head check: frame key alpha vs base.png alpha inside the head band (top of hair .. live hair bottom)
hb=np.zeros((Hh,W),bool); hb[max(y0-40,0):int(y0+0.75*(y1-y0)),max(x0-70,0):min(x1+70,W)]=True
BA=np.asarray(Image.open(f'{R}/views/{v}/base.png').getchannel('A'))>127
sh=best_shift(BA&hb,fg&hb,rng=30); res['head_silhouette']={'dx':sh[1],'dy':sh[2],'iou_after':sh[0],'iou_at0':iou(BA&hb,fg&hb)}
ny=np.nonzero(fg&hb); nb=np.nonzero(BA&hb); res['head_top_dy']=int(ny[0].min()-nb[0].min())
del BA
# pose check: best scale/rotation about the head pivot on top of the silhouette shift
piv=np.array([np.mean([p['pivotX'] for p in rig if p['id']=='hair_back']),np.mean([p['pivotY'] for p in rig if p['id']=='hair_back'])])
Lsh=np.roll(np.roll(live,ty,0),tx,1).astype(np.uint8); bestp=(sc,0,1.0)
for ang in np.arange(-8,8.1,1.0):
    for k in [0.94,0.97,1.0,1.03,1.06]:
        Mr=cv2.getRotationMatrix2D((float(piv[0]+tx),float(piv[1]+ty)),float(ang),k)
        Lr=cv2.warpAffine(Lsh,Mr,(W,Hh),flags=cv2.INTER_NEAREST)>0
        q=iou(Lr,hair_f)
        if q>bestp[0]+1e-9: bestp=(q,float(ang),k)
res['pose_fit']={'iou':bestp[0],'rot_deg_ccw':bestp[1],'scale':bestp[2]}
# strands: frame-only hair / live-only hair after the silhouette shift
Ls=np.roll(np.roll(live,ty,0),tx,1); Fd=cv2.dilate(hair_f.astype(np.uint8),np.ones((9,9),np.uint8))>0
Ld=cv2.dilate(Ls.astype(np.uint8),np.ones((9,9),np.uint8))>0
def comps(m,minA=120):
    n,lab,st,cen=cv2.connectedComponentsWithStats(m.astype(np.uint8),8); out=[]
    for i in range(1,n):
        if st[i,4]>=minA: out.append({'x':int(st[i,0]),'y':int(st[i,1]),'w':int(st[i,2]),'h':int(st[i,3]),'area':int(st[i,4])})
    return sorted(out,key=lambda c:-c['area'])
res['frame_only']=comps(hair_f&~Ld)
for c in res['frame_only']: c['below_live_hair_bottom']=bool(c['y']>=y1+3-ty)  # strap tops etc., not hair
res['live_only']=comps(Ls&~Fd)
st_=[]
for k,m in vis.items():
    if not k.startswith('strand'): continue
    ms=np.roll(np.roll(m,ty,0),tx,1); nn=int(ms.sum())
    st_.append({'id':k,'px':nn,'matched_frac':float((ms&Fd).sum()/nn) if nn else None})
res['strands']=st_
json.dump(res,open(f'{OUT}/{v}.json','w'),indent=1)
# ---------- overlay ----------
ys,xs=np.nonzero(live|hair_f); cy0,cy1=max(ys.min()-30,0),min(ys.max()+30,Hh); cx0,cx1=max(xs.min()-30,0),min(xs.max()+30,W)
img=despilled[cy0:cy1,cx0:cx1].astype(np.float32)
kb=(alpha[cy0:cy1,cx0:cx1]<=0.5); img[kb]=img[kb]*0.3+np.array([235,235,235])*0.7   # key -> light grey
img=img.astype(np.uint8).copy()
fc=hair_f[cy0:cy1,cx0:cx1]
tint=img.copy(); tint[fc]=(tint[fc]*0.55+np.array([255,140,0])*0.45).astype(np.uint8); img=tint
def outline(m,col,th=1):
    c,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE); cv2.drawContours(img,c,-1,col,th)
outline(live[cy0:cy1,cx0:cx1],(0,255,255),1)                 # live hair outline at rest (as mapped)
outline(bunm[cy0:cy1,cx0:cx1],(255,0,255),1)
if hf is not None and hf.sum()>500: outline(hf[cy0:cy1,cx0:cx1],(0,255,0),1)
Z=3; big=cv2.resize(img,None,fx=Z,fy=Z,interpolation=cv2.INTER_NEAREST)
txt=[f'{v} f{fno:03d}  IoU {res["iou_rest"]:.3f}  sil {tx:+d},{ty:+d}  bun {sb[1]:+d},{sb[2]:+d}'+(f'  fringe {res["fringe"]["dx"]:+d},{res["fringe"]["dy"]:+d}' if res['fringe'] else ''),
     'orange=frame hair (segmented)  cyan=live hair outline  magenta=bun part  green=hair_front']
for i,t in enumerate(txt): cv2.putText(big,t,(10,28+26*i),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),3); cv2.putText(big,t,(10,28+26*i),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),1)
Image.fromarray(big).save(f'{OUT}/overlay_{v}_f{fno:03d}.png')
# plain side-by-side too: mapped frame | base.png (head crop)
bimg=Image.open(f'{R}/views/{v}/base.png').crop((cx0,cy0,cx1,cy1)); bg=Image.new('RGBA',bimg.size,(235,235,235,255)); bg.alpha_composite(bimg)
fimg=Image.fromarray(despilled[cy0:cy1,cx0:cx1]); sbs=Image.new('RGB',(bimg.size[0]*2,bimg.size[1])); sbs.paste(fimg,(0,0)); sbs.paste(bg.convert('RGB'),(bimg.size[0],0))
sbs.save(f'{OUT}/sidebyside_{v}_f{fno:03d}.png')
print(json.dumps({k:res[k] for k in ['iou_rest','iou_classifier_on_base','silhouette','bun','fringe','pose_fit','head_silhouette','head_top_dy']}))
print('frame_only',res['frame_only'][:6]); print('live_only',res['live_only'][:6]); print('strands',res['strands'])
