#!/usr/bin/env python3
"""Ear fill on hair_back.png (layer 100, under Body). Fill set per view = pixels that some sway pose exposes down to
hair_back (python mirror of rig/index.html, shared slider grid + independent per-chain drives; /tmp/earfill_expose_<v>.npy
from earfill_scan with hair_back removed), inside the ear boxes, enclosed by Body's drawn ear/skin (>=6 of 8 rays reach
Body before true background), where hair_back is empty or holds the earlier median-hair fill (backup_pre_quality diff).
Only pixels fully covered at rest (validator rule: swaying part alpha 255 inside the erase mask, Body alpha 255 outside).
Colour: one flat colour per ear = per-channel median of Body's opaque skin pixels within 3 px of that ear's fill."""
import json, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/hair/tools')
from earfill_classify import *
from earfill_scan import B
WRITE='--write' in sys.argv; rep={}
for v in VIEWS:
    x0,y0,x1,y1=B[v]; H,W=1739,1365
    sh,ind=np.load(f'/tmp/earfill_expose_{v}.npy'); ex=np.zeros((H,W),bool); ex[y0:y1,x0:x1]=ind|sh
    hbp=f'{R}/views/{v}/hair/hair_back.png'; hb=np.array(Image.open(hbp).convert('RGBA'))
    ob=np.array(Image.open(f'{R}/hair/backup_pre_quality/{v}/hair_back.png').convert('RGBA'))
    oldfill=(hb[...,3]>0)&(ob[...,3]==0)
    boxes=in_boxes(v,(H,W)); cand=(ex|oldfill)&boxes
    cnt=rays(v,cand); enc=cand&(cnt>=6)
    # rest cover rule (as validate_hair.py hair_back_under_soft_px)
    hd=f'{R}/views/{v}/hair'; rig=json.load(open(f'{hd}/rig.json'))['parts']
    em=np.array(Image.open(f'{R}/hair/{v}_hair_erase_mask.png').convert('L'))>127
    base=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA'))
    swa=np.max([np.array(Image.open(f"{hd}/{e['file']}").convert('RGBA'))[...,3] for e in rig if e['swayWeight']>0],0)
    above=np.where(em,swa,np.where(em,0,base[...,3]))
    F=enc&((hb[...,3]==0)|oldfill)
    unsafe=F&(above<255); F&=~unsafe
    mid=unpremul(mid_stack(v)); out=hb.copy(); r={'filled_px':0,'ears':[],'unsafe_skipped':int(unsafe.sum()),
        'exposed_in_ear_boxes':int((ex&boxes).sum()),'enclosed_candidates':int(enc.sum())}
    for (bx0,by0,bx1,by1) in EARBOX[v]:
        m=np.zeros((H,W),bool); m[by0:by1,bx0:bx1]=True; Fe=F&m
        if not Fe.any(): r['ears'].append({'box':[bx0,by0,bx1,by1],'px':0}); continue
        ring=ndi.binary_dilation(Fe,iterations=3)&~Fe&(mid[...,3]==255)
        px=mid[ring][:,:3].astype(int); lum=px@np.array([.3,.59,.11])
        sk=px[(lum>90)&(px[:,0]>px[:,2]+30)]
        col=[int(x) for x in np.median(sk,0).round()]
        out[Fe]=col+[255]
        r['ears'].append({'box':[bx0,by0,bx1,by1],'px':int(Fe.sum()),'new_px':int((Fe&(hb[...,3]==0)).sum()),
            'replaced_old_hair_fill_px':int((Fe&oldfill).sum()),'colour':'#%02X%02X%02X'%tuple(col),'skin_samples':int(len(sk))})
    r['filled_px']=int(F.sum()); rep[v]=r
    np.save(f'/tmp/earfill_F_{v}.npy',F)
    print(v,json.dumps(r),flush=True)
    if WRITE: Image.fromarray(out,'RGBA').save(hbp)
json.dump(rep,open('/tmp/earfill_apply.json','w'),indent=1)
