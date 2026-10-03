#!/usr/bin/env python3
"""Side-glance white tone (STAGED). Reads live views/<view>/eyes/ (read-only), writes
eyes/staged/white_tone/<view>/<E>_white.png (+_chroma). Only white pixels under the rest iris
(hidden at rest -> rest unchanged) that some gaze offset exposes are re-filled.
Fill = flat tone per row and per side (inner/outer half of the iris footprint), each tone an actual
pixel colour of her drawn eye white in that row on that side (medoid of her sclera pixels; outline/AA
ring and the 1 px next to the iris rim excluded). Tone-down only: a pixel whose tone would not be darker keeps its old fill. Rows whose tone is within TOL lum of the band
start reuse the band tone (a few flat bands, no gradients). Profiles keep the anchored front-edge column."""
import json,os,sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT='/workspace/shadowveil'; OUT=f'{ROOT}/eyes/staged/white_tone'
TOL=14; KEY=(0,0,255)
VIEWS={'apose':['EyeR','EyeL'],'tpose':['EyeR','EyeL'],'left':['EyeL'],'right':['EyeR']}
def L(p): return np.array(Image.open(p).convert('RGBA')).astype(int)
log={}
for v,es in VIEWS.items():
    d=f'{ROOT}/views/{v}/eyes'; rig=json.load(open(f'{d}/rig.json')); lim=rig['irisLimitsPx']
    base=L(f'{ROOT}/views/{v}/base.png')
    os.makedirs(f'{OUT}/{v}',exist_ok=True)
    for e in es:
        w=L(f'{d}/{e}_white.png'); ir=L(f'{d}/{e}_iris.png')
        wm=w[...,3]>0; im=ir[...,3]>0
        # pixels exposed by some integer gaze offset (white minus shifted iris)
        cov_all=np.ones_like(im)
        exposed=np.zeros_like(im)
        for dx in range(lim['dxAtXminus1'],lim['dxAtXplus1']+1):
            for dy in range(lim['dyAtYminus1'],lim['dyAtYplus1']+1):
                s=np.zeros_like(im); H,W=im.shape
                s[max(0,dy):H+min(0,dy),max(0,dx):W+min(0,dx)]=im[max(0,-dy):H-max(0,dy),max(0,-dx):W-max(0,dx)]
                exposed|=im&~s
        # profile anchored front-edge column (white == her drawing there) stays
        anchored=np.zeros_like(im)
        if v in('left','right'):
            same=(w[...,:3]==base[...,:3]).all(-1)
            for y in np.nonzero(im.any(1))[0]:
                xs=np.nonzero(im[y])[0]
                for xf in (xs.min(),xs.max()):
                    if same[y,xf]: anchored[y,xf]=True
        tgt=exposed&~anchored
        rgb=base[...,:3]; lum=rgb.mean(-1)
        src=ndi.binary_erosion(wm,iterations=1)&~ndi.binary_dilation(im,iterations=1)&(lum>=120)&~im
        # her sclera only: drop saturated / skin-like (lid AA) pixels
        mx=rgb.max(-1); mn=rgb.min(-1); src&=(mx-mn)<=40
        rows=np.nonzero(tgt.any(1))[0]
        ys_i=np.nonzero(im.any(1))[0]
        def side_tone(y,side):
            for dy in [0,1,-1,2,-2,3,-3,4,-4]:
                yy=y+dy
                if not im[yy].any(): continue
                xs=np.nonzero(im[yy])[0]; a,b=xs.min(),xs.max()
                sx=np.nonzero(src[yy])[0]; sx=sx[sx<a] if side=='in0' else sx[sx>b]
                if len(sx)>=2:
                    P=rgb[yy,sx]; med=np.median(P,0); k=np.argmin(((P-med)**2).sum(1)); return tuple(int(c) for c in P[k]),yy
            return None,None
        new=w.copy(); tones={}
        for side in ('in0','in1'):
            band=None
            for y in range(ys_i.min(),ys_i.max()+1):
                t,yy=side_tone(y,side)
                if t is None: continue
                if band is not None and abs(np.mean(t)-np.mean(band))<TOL: t=band
                else: band=t
                tones[(y,side)]=t
        changed=0; used=set(); kept_brighter=[0]
        for y in rows:
            xs=np.nonzero(im[y])[0]; mid=(xs.min()+xs.max())/2
            for x in np.nonzero(tgt[y])[0]:
                side='in0' if x<=mid else 'in1'
                t=tones.get((y,side)) or tones.get((y,'in1' if side=='in0' else 'in0'))
                if t is None: continue
                if sum(t)>=new[y,x,:3].sum(): kept_brighter[0]+=1; continue   # tone-down only: never brighten
                used.add(t)
                if tuple(new[y,x,:3])!=t: new[y,x,:3]=t; changed+=1
        assert (new[...,3]==w[...,3]).all() and ((new[...,:3]!=w[...,:3]).any(-1)<=im).all()
        out=new.astype(np.uint8); Image.fromarray(out,'RGBA').save(f'{OUT}/{v}/{e}_white.png')
        ch=np.zeros(out.shape[:2]+(3,),np.uint8); ch[:]=KEY; ch[wm]=out[wm][:,:3]
        Image.fromarray(ch,'RGB').save(f'{OUT}/{v}/{e}_white_chroma.png')
        log[f'{v}/{e}']=dict(exposedPx=int(exposed.sum()),anchoredKept=int((exposed&anchored).sum()),changedPx=changed,keptNotDarker=kept_brighter[0],
                             irisPx=int(im.sum()),tonesUsed=['#%02X%02X%02X'%t for t in sorted(used,key=lambda t:-sum(t))])
        print(v,e,log[f'{v}/{e}'])
json.dump(log,open(f'{OUT}/white_tone_log.json','w'),indent=1)
