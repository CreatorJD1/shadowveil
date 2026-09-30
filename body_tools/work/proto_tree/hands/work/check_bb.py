import numpy as np
from PIL import Image
from render import *
for v in ['apose','tpose','left','right','back']:
    b=np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'))
    bb=Image.open(f'{ROOT}/views/{v}/base_body.png').convert('RGBA'); B=np.array(bb)
    mask=np.array(Image.open(f'{ROOT}/hands/{v}_hand_erase_mask.png'))>0
    ch=np.abs(B.astype(int)-b.astype(int)).max(2)>0
    out,_,_=render(v,bb,skip_hidden=False); d=np.abs(np.array(out).astype(int)-b.astype(int)).max(2)
    print(v,'base_body differs from base at',ch.sum(),'px; inside mask',(ch&mask).sum(),'outside mask',(ch&~mask).sum(),
          '| mask px where base_body alpha>0:',(mask&(B[...,3]>0)).sum(),'| rest(base_body+parts) diff px:',(d>0).sum(),'max',d.max())
