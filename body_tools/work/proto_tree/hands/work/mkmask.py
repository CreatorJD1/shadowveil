import numpy as np, sys
from PIL import Image, ImageDraw
from defs import D
from handmask import hand_mask
from seg import SRC
for v in D:
    a=np.array(Image.open(SRC[v]).convert('RGBA')).astype(np.float32)
    M=np.zeros(a.shape[:2],bool)
    for s,H in D[v].items():
        m=hand_mask(a,H); M|=m
        x0,y0,x1,y1=H['box']; sc=5
        base=a[...,:3]*a[...,3:]/255+255*(1-a[...,3:]/255)
        c=base.copy(); c[m]=c[m]*0.5+np.array([0,255,0])*0.5
        im=Image.fromarray(c[y0:y1,x0:x1].astype(np.uint8)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.NEAREST)
        d=ImageDraw.Draw(im); w=H['wrist']; d.line([((p[0]-x0)*sc,(p[1]-y0)*sc) for p in w],fill=(255,0,0))
        im.save(f'mk_{v}_{s}.png'); print(v,s,m.sum())
    np.save(f'mask_{v}.npy',M)
