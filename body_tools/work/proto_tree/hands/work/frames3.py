"""Finger frames v3 (apose / back / profiles): each finger's whole curled shape is drawn ONCE, as a single silhouette with
one outline (her line weight, flat skin + her line colour, no interior lines), inside the first segment's frame. The middle
and tip frames are empty but keep their childPivot chain, so the joints stay where the drawing puts them.
Toward the viewer (apose): folded pieces lie in front of the palm; pieces seen end-on / folded back tuck under the earlier ones.
Away from the viewer (back, profiles): folded pieces go behind the palm and the first segment."""
import json,os,sys,shutil,re,numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/hands/work')
from defs import D
from lw import width as inkw
ROOT='/workspace/shadowveil'; V=sys.argv[1]; SS=4; W,H=1365,1739
SRC=f'{ROOT}/hands/work/backup_apose_v2' if V=='apose' else f'{ROOT}/hands/work/backup_v2/{V}'   # rest cut + rotation-only tuning
V2=f'{ROOT}/hands/work/frames/{V}_v2'; OUT=f'{ROOT}/hands/work/frames/{V}_v3'
AWAY=V!='apose'
FLEX=(85,100,65) if not AWAY else (70,110,65)
LEAN=(12,8,6)
shutil.rmtree(OUT,ignore_errors=True); shutil.copytree(V2,OUT)
for f in os.listdir(OUT):                      # current palms (wrist fix) etc. from the live delivery
    if f.endswith('_palm.png'): shutil.copy(f'{ROOT}/views/{V}/hands/{f}',f'{OUT}/{f}')
src=json.load(open(f'{SRC}/rig.json')); by={p['id']:p for p in src['parts']}
rig=json.load(open(f'{V2}/rig.json')); nb={p['id']:p for p in rig['parts']}
def A(pid): return np.array(Image.open(f"{SRC}/{by[pid]['file']}").convert('RGBA'))
def calib_lw(path,S,Lc): return float(np.clip(inkw(path,S,Lc)*0.88/0.68,0.7,2.2))
for side in 'LR':
    Hd=src['hands'][side]
    if not Hd.get('visible') or not by.get(side+'_palm',{}).get('file'): continue
    S=np.array(Hd['skinRGB'],float); Lc=np.array(Hd['lineRGB'],float)
    PALM=np.array(Image.open(f"{ROOT}/views/{V}/hands/{side}_palm.png").convert('RGBA'))[...,3]>=160
    x0,y0,x1,y1=Hd['box']; bx=(x0-40,y0-40,x1+40,y1+40)
    Y,X=np.mgrid[bx[1]*SS:bx[3]*SS,bx[0]*SS:bx[2]*SS]; Px=(X+0.5)/SS-0.5; Py=(Y+0.5)/SS-0.5
    palm_s=ndi.map_coordinates(PALM.astype(float),[Py,Px],order=0)>0.5
    for F in ['Index','Middle','Ring','Pinky']:
        ids=[f'{side}_{F}{k}' for k in (1,2,3)]
        P=[np.array([by[i]['pivotX'],by[i]['pivotY']],float) for i in ids]
        tip=np.array(D[V][side]['fingers'][F.lower()][-1],float); ends=[P[1],P[2],tip]
        imgs=[A(i) for i in ids]; hw=[float(ndi.distance_transform_edt(a[...,3]>0).max()) for a in imgs]
        lw=np.mean([calib_lw(f"{SRC}/{by[i]['file']}",S,Lc) for i in ids])
        for c,fi in ((0.5,1),(1.0,2)):
            cum=0; B=P[0].copy(); U=np.zeros(Px.shape,bool); cps=[]; basecap=None
            for k in range(3):
                cum+=FLEX[k]*c
                d=ends[k]-P[k]; L=np.linalg.norm(d); d/=L; s_=np.cos(np.deg2rad(cum)); E=B+d*L*s_
                rb=hw[k]; re=hw[k+1] if k<2 else hw[k]*0.85
                if k and abs(prev_s)<0.35: rb=max(rb,prev_rb)     # sits on an end-on knuckle: cover it fully (no double arc)
                v_=E-B; L2=max(v_@v_,1e-9); t=np.clip(((Px-B[0])*v_[0]+(Py-B[1])*v_[1])/L2,0,1)
                m=np.hypot(Px-(B[0]+t*v_[0]),Py-(B[1]+t*v_[1]))<=rb+(re-rb)*t
                # her own silhouette (taper), compressed along the segment, where it is long enough to matter
                if abs(s_)>0.08:
                    n=np.array([-d[1],d[0]]); a=(Px-B[0])*d[0]+(Py-B[1])*d[1]; b=(Px-B[0])*n[0]+(Py-B[1])*n[1]
                    sx=P[k][0]+(a/s_)*d[0]+b*n[0]; sy=P[k][1]+(a/s_)*d[1]+b*n[1]
                    mf=ndi.map_coordinates(imgs[k][...,3].astype(float),[sy,sx],order=1)>=128
                    m|=mf&((a*np.sign(s_))>=-rb*0.2)
                if k and (s_<0.3):
                    hide=U|(palm_s if AWAY else np.zeros_like(U))
                    m&=~ndi.binary_dilation(hide,iterations=2*SS//2)
                if k==0: basecap=(B.copy(),rb,d.copy())
                U|=m; prev_s=s_; prev_rb=rb
                # childPivot in this segment's own (rest) coords: its frame is drawn from rest pivot P[k]
                cps.append(P[k]+d*L*s_); B=E
            # one outline around the whole finger; no line where it runs inside the palm near its base (seam with palm)
            dt=ndi.distance_transform_edt(np.pad(U,4))[4:-4,4:-4]/SS; line=U&(dt<=lw)
            B0,r0,d0=basecap; aa=(Px-B0[0])*d0[0]+(Py-B0[1])*d0[1]
            line&=~(ndi.binary_erosion(palm_s,iterations=SS)&(np.hypot(Px-B0[0],Py-B0[1])<r0+lw+0.5)&(aa<0.2*r0))
            col=np.zeros(U.shape+(4,)); col[...,:3]=S; col[...,3]=U*255.; col[line,:3]=Lc
            pm=col.copy(); pm[...,:3]*=pm[...,3:]/255; h_,w_=bx[3]-bx[1],bx[2]-bx[0]
            ds=pm.reshape(h_,SS,w_,SS,4).mean((1,3)); al=ds[...,3:]
            fr=np.zeros((H,W,4),np.uint8); fr[bx[1]:bx[3],bx[0]:bx[2],:3]=np.clip(np.round(np.where(al>0,ds[...,:3]/np.maximum(al,1e-6)*255,0)),0,255); fr[bx[1]:bx[3],bx[0]:bx[2],3]=np.clip(np.round(al[...,0]),0,255)
            Image.fromarray(fr).save(f'{OUT}/{ids[0]}_f{fi}.png')
            empty=np.zeros((H,W,4),np.uint8)
            for k in (1,2): Image.fromarray(empty).save(f'{OUT}/{ids[k]}_f{fi}.png')
            for k in (0,1):
                nb[ids[k]]['frames'][fi]['childPivot']=[round(float(cps[k][0]),2),round(float(cps[k][1]),2)]
        for k,i in enumerate(ids):
            nb[i]['maxCurlDeg']=int(np.sign(by[i]['maxCurlDeg']))*LEAN[k]
rig['framesNote']=V+' frames v3: each finger\'s curled shape is drawn once as one silhouette with one outline (her line weight and colours, flat skin, no interior lines) in the first segment\'s frame; the middle/tip frames are empty and only carry the childPivot chain. '+('Fingers curl toward the viewer (in front of the palm).' if not AWAY else 'Fingers curl away from the viewer: folded pieces are hidden behind the palm and first segment.')+' maxCurlDeg is a small lean; maxCurlDegRotationOnly keeps the rotation-only tuning.'
json.dump(rig,open(f'{OUT}/rig.json','w'),indent=1); print('v3 written',V)
