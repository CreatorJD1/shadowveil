"""Palm wrist edge: make it opaque and extend the palm 3 px past the wrist line onto the forearm with base.png's own pixels
(only where base.png is opaque there, so the rest composite is unchanged)."""
import json,numpy as np,sys
from PIL import Image
from defs import D
ROOT='/workspace/shadowveil'; EXT=3.0
for V in ['apose','tpose','left','right','back']:
    base=np.array(Image.open(f'{ROOT}/views/{V}/base.png').convert('RGBA'))
    rig=json.load(open(f'{ROOT}/views/{V}/hands/rig.json'))
    for side,dd in D[V].items():
        p=next(q for q in rig['parts'] if q['id']==side+'_palm')
        if not p.get('file'): continue
        fp=f"{ROOT}/views/{V}/hands/{p['file']}"; a=np.array(Image.open(fp).convert('RGBA'))
        (x0,y0),(x1,y1)=dd['wrist']; A=np.array([x0,y0],float); Bv=np.array([x1,y1],float); t=Bv-A; Lw=np.linalg.norm(t); t/=Lw; n=np.array([-t[1],t[0]])
        ins=np.array(dd['inside'],float)
        if (ins-A)@n>0: n=-n            # n points toward the forearm
        Y,X=np.mgrid[0:a.shape[0],0:a.shape[1]]
        s=(X-A[0])*n[0]+(Y-A[1])*n[1]; u=(X-A[0])*t[0]+(Y-A[1])*t[1]
        band=(s>-2.5)&(s<=EXT)&(u>=0.5)&(u<=Lw-0.5)   # stay between the arm contours (no thigh or background)
        # only extend where the palm already reaches the wrist line nearby (not into open space / the thigh beside the hand)
        tgt=band&(base[...,3]==255)&(a[...,3]<255)
        near=np.zeros_like(tgt)
        from scipy import ndimage as ndi
        near=ndi.binary_dilation(a[...,3]>0,iterations=int(EXT)+1)
        tgt&=near
        a[tgt]=base[tgt]; Image.fromarray(a).save(fp)
        print(V,side,'wrist px set opaque/extended:',int(tgt.sum()))
