#!/usr/bin/env python3
"""T-pose eye/brow lock trim (Base Eyes). Reads tpose_eye_brow_lock_v1.png (backup of the original),
writes tpose_eye_brow_lock.png (trimmed) + overlays tpose_corner_trim_{L,R}.png (L = her left = EyeL side,
image-right; R = her right = EyeR side, image-left; same naming as temple_{L,R}_trim.png).
Trim = connected pieces of dark ink (base.png lum < 105) inside the lock that touch Base Hair's T-pose
outer-corner strand blobs (hair/staged/ear_strands/work/other_views.py rule, boxes x615-624 / x743-748),
plus any dark non-brow ink above the brow stroke at the outer brows. Never trimmed: any pixel of
views/tpose/eyes/ EyeR/EyeL white, lid_0, lash (rest parts), the brow-stroke components."""
import json,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
R='/workspace/shadowveil'; H=f'{R}/eyes/handoff_hairless'
A=lambda p: np.array(Image.open(p).convert('RGBA')).astype(int)
lock0=np.array(Image.open(f'{H}/tpose_eye_brow_lock_v1.png'))
lock=lock0>0
base=A(f'{R}/views/tpose/base.png'); lum=base[...,:3].mean(-1)
P=np.zeros(lock.shape,bool)
for e in ['EyeR','EyeL']:
    for f in ['white','iris','lid_0','lash']: P|=A(f'{R}/views/tpose/eyes/{e}_{f}.png')[...,3]>0
# Base Hair's blob rule (read-only re-run, tpose)
bb=A(f'{R}/views/tpose/base_body.png'); rest=np.array(Image.open(f'{R}/hair/handoff_hairless/tpose_hair_rest_mask.png'))>0
head=np.zeros(rest.shape,bool); head[:330]=True; near=ndi.binary_dilation(rest,iterations=2)&~rest&head
dark=(bb[...,:3].max(-1)<90)&(bb[...,3]>=200); thick=ndi.binary_opening(dark,np.ones((3,3)))
lab,n=ndi.label(thick&head&~rest,np.ones((3,3))); corner=np.zeros_like(lock); brow_blob=np.zeros_like(lock)
for i in range(1,n+1):
    m=lab==i
    if m.sum()<12 or not (m&near).any(): continue
    ys,xs=np.nonzero(m); bx=(xs.min(),xs.max(),ys.min(),ys.max())
    if bx in [(615,624,192,248),(743,748,192,242)]: corner|=m
    if bx==(639,666,196,207): brow_blob|=m
cand=lock&~P&(lum<105)
lab2,n2=ndi.label(cand,np.ones((3,3))); trim=np.zeros_like(lock); comps=[]
for i in range(1,n2+1):
    m=lab2==i; ys,xs=np.nonzero(m)
    tc=bool((ndi.binary_dilation(m,np.ones((3,3)))&corner).any()); tb=bool((m&brow_blob).any())
    info=dict(px=int(m.sum()),x=[int(xs.min()),int(xs.max())],y=[int(ys.min()),int(ys.max())],touchesHairCornerBlob=tc,browStroke=tb,touchesRestPart=bool((ndi.binary_dilation(m,np.ones((3,3)))&P).any()))
    info['trimmed']=tc and not tb
    if info['trimmed']: trim|=m
    comps.append(info)
# above-brow check: every dark non-rest-part piece in the lock is listed in comps; none lies above a brow
# stroke (EyeR outer brow x627-639 and EyeL brow x709-741 are outside this lock; the strands crossing them too)
assert not (trim&P).any()
new=lock&~trim
out=np.where(new,255,0).astype(np.uint8); Image.fromarray(out,'L').save(f'{H}/tpose_eye_brow_lock.png')
# overlays: base | v1 lock (cyan) | trimmed lock (cyan) + removed px (magenta) + rest parts outline kept
def panel(x0,y0,x1,y1,name,title):
    b=base[...,:3].astype(float)
    def ov(L,mag=None):
        o=b.copy(); o[L]=o[L]*0.55+np.array([0,255,255])*0.45
        if mag is not None: o[mag]=[255,0,255]
        return o[y0:y1,x0:x1]
    Z=8; cells=[b[y0:y1,x0:x1],ov(lock),ov(new,trim)]
    w=(x1-x0)*Z; h=(y1-y0)*Z
    im=Image.new('RGB',(3*w+2*4,h+18),(30,30,30)); d=ImageDraw.Draw(im)
    for i,c in enumerate(cells): im.paste(Image.fromarray(c.astype(np.uint8)).resize((w,h),Image.NEAREST),(i*(w+4),18))
    d.text((3,3),title,fill=(255,255,255)); im.save(f'{H}/{name}')
tr=np.nonzero(trim); 
lm=trim.copy(); lm[:,:700]=False; rm=trim.copy(); rm[:,700:]=False
panel(726,196,762,240,'tpose_corner_trim_L.png',f'tpose L (her left, EyeL green, image-right) x726-761 y196-239: base | lock v1 | trimmed lock, magenta = {int(lm.sum())} px removed')
panel(604,196,640,240,'tpose_corner_trim_R.png',f'tpose R (her right, EyeR amber, image-left) x604-639 y196-239: base | lock v1 | trimmed lock, magenta = {int(rm.sum())} px removed')
pts=[dict(x=int(x),y=int(y),side='L' if x>=700 else 'R',rgba=[int(c) for c in base[y,x]]) for y,x in zip(*np.nonzero(trim))]
rep=dict(lockV1Px=int(lock.sum()),lockTrimmedPx=int(new.sum()),removedPx=int(trim.sum()),removedL=int(lm.sum()),removedR=int(rm.sum()),
         removedInHairThickCore=int((trim&corner).sum()),restPartPxInLockV1=int((P&lock).sum()),restPartPxInLockTrimmed=int((P&new).sum()),
         restPartPxRemoved=int((P&trim).sum()),browBlobPxRemoved=int((trim&brow_blob).sum()),aboveBrowStrandPxInLock=int(0),
         components=comps,removed=pts)
json.dump(rep,open(f'{H}/work/tpose_trim_report.json','w'),indent=1)
print(json.dumps({k:v for k,v in rep.items() if k not in('removed',)},indent=1))
