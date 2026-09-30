# Measure our apose shapes (read-only) with the same geometry as measure.py; opening classified by our own palette colours.
import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
from measure import lumf
V='/workspace/shadowveil/views/apose'
rig=json.load(open(f'{V}/mouth/rig.json')); C=rig['colors']; ax,ay=rig['anchor']['x'],rig['anchor']['y']
hexc=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],float)
base=Image.open(f'{V}/base.png').convert('RGBA')
out={}
for n in ['rest','M','smile','OH_half','AA_half','EE_half','OH','AA','EE']:
    im=base.copy(); im.alpha_composite(Image.open(f'{V}/mouth/{n}.png').convert('RGBA'))
    a=np.array(im)[ay-40:ay+40,ax-50:ax+50,:3].astype(float); l=lumf(a); skin_l=float(np.median(l[:12]))
    near=lambda h,t=40: np.linalg.norm(a-hexc(h),axis=-1)<t
    blue=a[...,2]>a[...,0]+30
    dark=(l<skin_l-28)&~blue
    keys=['skin','upper','lower','line','hl','inner','teeth','tongue']
    P=np.stack([hexc(C[k]) for k in keys]); cls=np.argmin(np.linalg.norm(a[...,None,:]-P[None,None],axis=-1),-1)
    cav=near(C['inner'],12); teeth=near(C['teeth'],12); tongue=near(C['tongue'],12)   # our flat palette, tight tolerance
    if n=='rest': cav[:]=False; teeth[:]=False; tongue[:]=False                        # her drawn rest is closed (gloss is not teeth)
    lab,k=ndi.label(ndi.binary_closing(dark|teeth|tongue,iterations=1))
    yy,xx=np.mgrid[:80,:100]; cnt=ndi.sum(np.hypot(yy-40,xx-50)<16,lab,range(1,k+1)); m=ndi.binary_fill_holes(lab==int(np.argmax(cnt))+1)
    ys,xs=np.nonzero(m); W=xs.max()-xs.min()+1; Hm=ys.max()-ys.min()+1
    inner=ndi.binary_erosion(m,iterations=1); op=ndi.binary_closing(cav|teeth|tongue,iterations=1)&inner
    lo,ho=ndi.label(op)
    if ho:
        seed=ndi.sum((cav|teeth)&op,lo,range(1,ho+1)); op=np.isin(lo,[i+1 for i in range(ho) if seed[i]>=1])
    spans=[]
    c0,c1=xs.min(),xs.max()
    for c in range(int(c0+0.3*(c1-c0)),int(c0+0.7*(c1-c0))+1):
        r=np.nonzero(op[:,c])[0]; spans.append((r.max()-r.min()+1) if len(r) else 0)
    oys,oxs=np.nonzero(op); OW=(oxs.max()-oxs.min()+1) if len(oxs) else 0
    coly=lambda c:(np.nonzero(m[:,c])[0].min()+np.nonzero(m[:,c])[0].max())/2
    ycor=(coly(c0)+coly(c1))/2; cxm=(c0+c1)//2
    r=np.nonzero(op[:,cxm-1:cxm+2].any(1))[0]
    if len(r): yc=(r.min()+r.max())/2
    else:
        lc=l[:,cxm].copy(); lc[~m[:,cxm]]=999; yc=float(np.argmin(lc))
    out[n]=dict(W=int(W),Hmouth=int(Hm),openH=int(max(spans)),openW=int(OW),teeth=int((teeth&inner).sum()),tongue=int((tongue&inner).sum()),cornerLift=float(yc-ycor))
    if n=='rest': Image.fromarray(np.concatenate([a.astype(np.uint8)],1)).resize((400,320),Image.NEAREST).save('tmp/ours_rest.png')
    ov=a.copy(); ov[m^ndi.binary_erosion(m)]=(0,255,0); ov[op&~ndi.binary_erosion(op)]=(255,0,255)
    out[n]['_tile']=np.concatenate([a,ov],1).astype(np.uint8)
W0=out['rest']['W']
for n,v in out.items():
    print(n,{k:v[k] for k in v if k!='_tile'},'W/W0 %.2f open/W0 %.2f Hm/W0 %.2f lift/W0 %.3f'%(v['W']/W0,v['openH']/W0,v['Hmouth']/W0,v['cornerLift']/W0))
np.save('tmp/ours_tiles.npy',np.stack([out[n]['_tile'] for n in out]))
json.dump({n:{k:v[k] for k in v if k!='_tile'} for n,v in out.items()},open('tmp/ours.json','w'),indent=1)
