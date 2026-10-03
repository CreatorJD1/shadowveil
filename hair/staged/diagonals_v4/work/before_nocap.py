# sway gate with the caps stripped (in memory) = the uncapped v4 baseline, same masks as caps.py
import json
from sway_gate import *
res={}
for ang in ('045','315'):
    for scale in ('view','frame'):
        d,rig,parts,im=load(ang,scale)
        for p in parts: p.pop('degAtPlus1',None); p.pop('degAtMinus1',None)
        op,mt=masks(ang,scale); worst,per=sweep(parts,im,rig.get('swayYMaxPx',3),{'eye_opening':np.nonzero(op)}|{k:np.nonzero(v) for k,v in mt.items()})
        res[f'{ang}_{scale}']=dict(worst={k:dict(px=v[0],state=v[1]) for k,v in worst.items()},per_part_dir={f'{k}|{p}|{s}':n for (k,p,s),n in per.items() if n})
        print(ang,scale,json.dumps(res[f'{ang}_{scale}']),flush=True)
json.dump(res,open(f'{O}/sway_gate_before.json','w'),indent=1)
