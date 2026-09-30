import numpy as np
from PIL import Image
from render import *
res={}
for v in ['apose','tpose','left','right','back']:
    base=Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA')
    mask=np.array(Image.open(f'{ROOT}/hands/{v}_hand_erase_mask.png'))>0
    b=np.array(base); be=b.copy(); be[mask]=0
    for sh in (True,False):
        out,rig,_=render(v,Image.fromarray(be,'RGBA'),skip_hidden=sh)
        o=np.array(out); diff=np.abs(o.astype(int)-b.astype(int)).max(2)
        print(v,'skip_hidden' if sh else 'draw_hidden','rest diff pixels:',(diff>0).sum(),'max',diff.max())
    # parts outside mask? blue?
    _,imgs=load_rig(v); U=np.zeros(mask.shape,bool); blue=0
    for k,im in imgs.items():
        A=np.array(im); al=A[...,3]>0; U|=al
        B=A[...,2].astype(int); mx=np.maximum(A[...,0],A[...,1]).astype(int)
        blue+=((B>mx+45)&(B>90)&al).sum()
    print('   part px outside mask:',(U&~mask).sum(),' mask px not covered:',(mask&~U).sum(),' blueish px:',blue)
    # unerased base + parts
    out,_,_=render(v,base); o=np.array(out); d=np.abs(o.astype(int)-b.astype(int)).max(2)
    print('   (unerased base + parts) diff px:',(d>0).sum(),'max',d.max())
