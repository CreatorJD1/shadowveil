"""Trim Eyes' diagonal lash px that her source turn frame draws as hair (Base Hair's key rule: frame alpha>0 & B-max(R,G)>60,
the rule behind hair/staged/diagonals_v3/<ang>/src_hair_key_view.png). Keyed -> alpha 0 (RGB of existing transparent px), chroma -> #0000FF.
Lid frames: trimmed only where they carry px in the same set (checked: none). Backups in eyes/staged/diagonals/backups_lash_hair_trim/."""
import json, numpy as np
from PIL import Image
R='/workspace/shadowveil'; D=f'{R}/eyes/staged/diagonals'; FR={'045':'f033','315':'f191'}
res={}
for ang in ('045','315'):
    fr=np.array(Image.open(f'{R}/reference/apose_turn/frames/{FR[ang]}.png').convert('RGBA')).astype(int)
    key=(fr[...,3]>0)&(fr[...,2]-np.maximum(fr[...,0],fr[...,1])>60)
    for e in ('EyeR','EyeL'):
        for n in ['lash']+[f'lid_{k}' for k in range(8)]:
            pk=f'{D}/{ang}/{e}_{n}.png'; pc=f'{D}/{ang}/{e}_{n}_chroma.png'
            K=Image.open(pk); mode=K.mode; k=np.array(K.convert('RGBA')); c=np.array(Image.open(pc).convert('RGBA'))
            T=(k[...,3]>0)&key if n=='lash' else np.zeros(key.shape,bool)
            if n!='lash' and ((k[...,3]>0)&key).any(): pass  # lid px over key are lid-skin edge px, not lash; reported, not trimmed
            if not T.any(): continue
            bg=k[k[...,3]==0][0].copy(); ys,xs=np.nonzero(T)
            k[T]=bg; k[T,3]=0; c[T]=(0,0,255,255)
            Image.fromarray(k,'RGBA').convert(mode).save(pk); Image.fromarray(c,'RGBA').convert(Image.open(pc).mode).save(pc)
            res[f'{ang}/{e}_{n}']={'trimmed_frame_px':int(T.sum()),'bbox_frame_xyxy':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],'xy':[[int(x),int(y)] for x,y in zip(xs,ys)]}
json.dump(res,open('trim_lash.json','w'),indent=1); print({k:v['trimmed_frame_px'] for k,v in res.items()})
