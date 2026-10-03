# fast crop-based +-25 joint test from pieces/ + parts.json
# Usage: python3 jointtest.py [bilinear|nearest] [apose|tpose]
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
V=sys.argv[2] if len(sys.argv)>2 else 'apose'
OUT=f'/workspace/shadowveil/body_tools/work/hairless_division_staged/{V}'
pj=json.load(open(f'{OUT}/parts.json')); order=pj['layerOrder_backToFront']; pc={p['id']:p for p in pj['pieces']}
img={k:np.array(Image.open(f'{OUT}/pieces/{k}.png')).astype(float) for k in order}
h=np.array(Image.open(f'{OUT}/hairless_{V}.png')).astype(float)
# her T-pose art has faint interior seams (alpha 239-253, ~2.7k px, identical at rest): count holes only below that floor
_op=h[...,3]==255; _enc=ndimage.binary_fill_holes(_op)&~_op&(h[...,3]>0)
FLOOR=int(h[...,3][_enc].min()) if (_enc.sum()>100) else 255
HAND=np.array(Image.open(f'{OUT}/hand_mask.png'))>0
kids={}
for p in pj['pieces']: kids.setdefault(p['parent'],[]).append(p['id'])
def subtree(k): s=[k]; [s.extend(subtree(c)) for c in kids.get(k,[])]; return s
J={'shoulder_L':'upper_arm_L','shoulder_R':'upper_arm_R','elbow_L':'forearm_L','elbow_R':'forearm_R','hip_L':'thigh_L','hip_R':'thigh_R','knee_L':'shin_L','knee_R':'shin_R'}
def over(dst,src):
    sa=src[...,3:]/255.; da=dst[...,3:]/255.; oa=sa+da*(1-sa)
    rgb=np.where(oa>0,(src[...,:3]*sa+dst[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0); return np.concatenate([rgb,oa*255],-1)
MODE=sys.argv[1] if len(sys.argv)>1 else 'bilinear'
res={}; tiles=[]
for jn,ch in [(j_,c_) for j_,c_ in J.items() if j_ in pj['joints'] and c_ in pc]:   # profile views: one side only; shoulder flap sits on the torso
    c=pc[ch]['pivot']; fl=pj['joints'][jn]; r=fl['joint_radius_px']+15
    R=int(r+30); x0,y0=int(c[0])-R,int(c[1])-R; x1,y1=int(c[0])+R,int(c[1])+R
    yy,xx=np.mgrid[y0:y1,x0:x1]
    crop={k:img[k][y0:y1,x0:x1] for k in order}
    HANDC=HAND[max(y0,0):y1,max(x0,0):x1] if (x0>=0 and y0>=0) else np.zeros((y1-y0,x1-x0),bool)
    sub=subtree(ch); par=pc[ch]['parent']
    def rot(full,th):
        t=np.radians(-th); dx,dy=xx-c[0],yy-c[1]
        fx=c[0]+np.cos(t)*dx-np.sin(t)*dy; fy=c[1]+np.sin(t)*dx+np.cos(t)*dy
        H,W=full.shape[:2]
        if MODE=='nearest':
            sx=np.round(fx).astype(int); sy=np.round(fy).astype(int); ok=(sx>=0)&(sx<W)&(sy>=0)&(sy<H)
            o=np.zeros((y1-y0,x1-x0,4)); o[ok]=full[sy[ok],sx[ok]]; return o
        pm=full.copy(); pm[...,:3]*=pm[...,3:]/255.          # premultiplied bilinear (what a canvas renderer does)
        x0f=np.floor(fx).astype(int); y0f=np.floor(fy).astype(int); ax=fx-x0f; ay=fy-y0f
        def g(yi,xi):
            ok=(xi>=0)&(xi<W)&(yi>=0)&(yi<H); o=np.zeros((y1-y0,x1-x0,4)); o[ok]=pm[yi[ok],xi[ok]]; return o
        o=g(y0f,x0f)*((1-ax)*(1-ay))[...,None]+g(y0f,x0f+1)*(ax*(1-ay))[...,None]+g(y0f+1,x0f)*((1-ax)*ay)[...,None]+g(y0f+1,x0f+1)*(ax*ay)[...,None]
        a=o[...,3:]; o[...,:3]=np.where(a>0,o[...,:3]*255./np.maximum(a,1e-9),0)
        return np.where(np.abs(o[...,3:]-255)<0.01,np.concatenate([o[...,:3],np.full_like(a,255)],-1),o)
    band=np.hypot(xx-c[0],yy-c[1])<=r
    res[jn]={}
    for th in (-25,0,25):
        im2=dict(crop)
        for k in sub: im2[k]=rot(img[k],th)
        cp=np.zeros((y1-y0,x1-x0,4))
        for k in order: cp=over(cp,im2[k])
        pair=(im2[par][...,3]>=254.5)|np.any([im2[k][...,3]>=254.5 for k in sub],0)
        op=(cp[...,3]>=254.5)|HANDC   # the hand mask is Base Hands' layer (drawn there, static with the forearm)
        enclosed=ndimage.binary_fill_holes(pair)&~op&band            # transparent/partial px fully enclosed
        crack=ndimage.binary_fill_holes(ndimage.binary_closing(pair,iterations=1))&~op&band   # + 1px-wide cracks/notches
        notch=ndimage.binary_fill_holes(ndimage.binary_closing(pair,iterations=2))&~op&band   # + up to 4 px wide outline notches
        res[jn][f'{th:+d}']={'enclosed':int(enclosed.sum()),'crack1':int(crack.sum()),'notch2':int(notch.sum()),'enclosed_alpha0':int((enclosed&(cp[...,3]<1)).sum()),'crack1_alpha0':int((crack&(cp[...,3]<1)).sum()),'crack1_alpha_lt128':int((crack&(cp[...,3]<128)).sum()),'notch2_alpha0':int((notch&(cp[...,3]<1)).sum()),'notch2_alpha_lt128':int((notch&(cp[...,3]<128)).sum()),'notch_a0_xy':[[int(a+x0),int(b+y0)] for b,a in zip(*np.nonzero(notch&(cp[...,3]<128)))]}
        if FLOOR<255:
            res[jn][f'{th:+d}'][f'enclosed_alpha_lt{FLOOR}']=int((enclosed&(cp[...,3]<FLOOR-0.5)).sum()); res[jn][f'{th:+d}'][f'crack1_alpha_lt{FLOOR}']=int((crack&(cp[...,3]<FLOOR-0.5)).sum())
            res[jn][f'{th:+d}'][f'notch2_alpha_lt{FLOOR}']=int((notch&(cp[...,3]<FLOOR-0.5)).sum())
        if th and enclosed.any(): res[jn][f'{th:+d}']['enclosed_xy']=[[int(a+x0),int(b+y0),int(round(cp[b,a,3]))] for b,a in zip(*np.nonzero(enclosed))]
        if th: res[jn][f'{th:+d}']['crack_xy']=[[int(a+x0),int(b+y0)] for b,a in zip(*np.nonzero(crack))]
        if th:
            a=cp[...,3:]/255; v=cp[...,:3]*a+np.array([150,230,150])*(1-a); v[notch]=[255,200,0]; v[crack]=[255,120,0]; v[enclosed]=[255,0,0]
            tiles.append((f'{jn} {th:+d}: hole {int(enclosed.sum())} crack {int(crack.sum())} notch {int(notch.sum())}',v.astype(np.uint8)))
json.dump({'mode':MODE,**({'art_interior_alpha_floor':FLOOR,'floor_note':f'her {V} base art has {int(_enc.sum())} interior px at alpha {FLOOR}-254 (faint seams, same at rest); *_lt{FLOOR} = holes below that'} if FLOOR<255 else {}),'metrics':'enclosed = alpha<255 px fully enclosed by the two joint pieces; crack1/notch2 = same after closing 1/2 px (outline cracks/notches); *_alpha0 / *_lt128 = see-through subset','joints':res},open(f'{OUT}/joint_test_25_{MODE}.json','w'),indent=1)
tw=330; cols=4; sh=Image.new('RGB',(cols*tw,((len(tiles)+cols-1)//cols)*(tw+20)),(255,255,255)); d=ImageDraw.Draw(sh)
for i,(lbl,t) in enumerate(tiles):
    im=Image.fromarray(t).resize((tw-10,tw-10),Image.NEAREST); X=(i%cols)*tw; Y=(i//cols)*(tw+20); sh.paste(im,(X+5,Y+18)); d.text((X+5,Y+3),lbl,fill=(0,0,0))
sh.save(f'{OUT}/sheet_joint_test_25_{MODE}.png')
for jn in res: print(jn,{k:v for k,v in res[jn].items()})
