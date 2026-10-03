import json,sys
import numpy as np
from PIL import Image
R='/workspace/shadowveil/'
out={}
for v in ['apose','tpose','left','right','back']:
    B=np.array(Image.open(R+f'views/{v}/base.png').convert('RGBA')).astype(int)
    d=json.load(open(f'render_rest_{v}.json'))[v]
    o={'rigRestCheck':d['restCheck'].split('\n')[0],'console':d['console'],'handAngles':d['handAngles']}
    for tag in ['rest','rest_after_turn']+[f'turned_{a}' for a in (45,90,135,-45)]:
        fn=f'{tag}_{v}.png' if not tag.startswith('turned') else f'turned_{v}_{tag.split("_")[1]}.png'
        A=np.array(Image.open(fn).convert('RGBA')).astype(int)
        if A.shape!=B.shape: o[tag]=f'size {A.shape} vs {B.shape}'; continue
        m=(np.abs(A-B).max(-1)>0)&~((A[...,3]==0)&(B[...,3]==0))
        o[tag]=int(m.sum())
        if tag=='rest' and m.any():
            dimg=B.copy(); dimg[...,:3]//=3; dimg[m]=[255,0,0,255]; Image.fromarray(dimg.astype('uint8')).save(f'restdiff_{v}.png')
    out[v]=o
json.dump(out,open('summary.json','w'),indent=1); print(json.dumps(out,indent=1))
