# blue-spill metric: fraction of mask pixels (kept by seg) that are still blue-tinted (b-max(r,g)>25), whole body and hair zone (top 22% H)
import sys,json,numpy as np
from PIL import Image
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/apose_turn'); from seg import mask_of
FR='/workspace/shadowveil/reference/apose_turn/frames/f%03d.png'
out={}
for c in (33,87,131,191):
    for f in range(c-4,c+5):
        a=np.array(Image.open(FR%f).convert('RGB')).astype(int); m=mask_of(FR%f)
        ys,xs=np.nonzero(m); t,b=ys.min(),ys.max()
        tint=(a[...,2]-np.maximum(a[...,0],a[...,1]))>25
        # enclosed key holes filled by seg (true blue inside filled mask)
        key=(a[...,2]-np.maximum(a[...,0],a[...,1]))>120
        hz=np.zeros_like(m); hz[t:int(t+.22*(b-t))]=True
        out[f]={'spill_px':int((m&tint&~key).sum()),'hair_spill_px':int((m&tint&~key&hz).sum()),'enclosed_key_px':int((m&key).sum()),'enclosed_key_hair_px':int((m&key&hz).sum())}
json.dump(out,open('/workspace/shadowveil/body_tools/work/apose_turn/diagonals/_spill.json','w'),indent=1)
for f,d in out.items(): print(f,d)
