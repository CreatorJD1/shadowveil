import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from defs import D
from handmask import side
for v in ['apose','tpose','left','right','back']:
    bb=np.array(Image.open(f'/workspace/shadowveil/views/{v}/base_body.png').convert('RGBA')).astype(float)
    base=np.array(Image.open(f'/workspace/shadowveil/views/{v}/base.png').convert('RGBA')).astype(float)
    mask=np.array(Image.open(f'/workspace/shadowveil/hands/{v}_hand_erase_mask.png'))>0
    yy,xx=np.mgrid[0:mask.shape[0],0:mask.shape[1]]; P=np.stack([xx,yy],-1).astype(float)
    for s,H in D[v].items():
        x0,y0,x1,y1=H['box']; hs=np.zeros(mask.shape,bool)
        sd=side(P[y0-10:y1+10,x0-10:x1+10],H['wrist']); ref=side(np.array(H['inside'],float),H['wrist'])
        # distal side, and at least 3px away from wrist line (normalised)
        (ax,ay),(bx,by)=H['wrist']; L=np.hypot(bx-ax,by-ay)
        hs[y0-10:y1+10,x0-10:x1+10]=(np.sign(sd)==np.sign(ref))&(np.abs(sd)/L>3)
        ring=ndi.binary_dilation(mask,iterations=5)&~mask&hs
        if v in('left','right'):
            far=ndi.binary_dilation(mask,iterations=12)&~ndi.binary_dilation(mask,iterations=8)&hs
            sk=np.median(bb[far&(bb[...,3]==255)][:,:3],0)
            lum=lambda c:c@np.array([.299,.587,.114])
            dl=np.abs(lum(bb[...,:3])-lum(sk))
            bad=ring&(dl>8)
        else:
            bad=ring&(bb[...,3]>0)
        # distance of bad px to mask
        dt=ndi.distance_transform_edt(~mask)
        print(v,s,'ring px',ring.sum(),'suspicious px',bad.sum(),'by dist',[int((bad&(np.round(dt)==d)).sum()) for d in range(1,6)],
              'base==base_body there:',int((bad&(np.abs(bb-base).max(2)==0)).sum()))
        np.save(f'bad_{v}_{s}.npy',bad)
