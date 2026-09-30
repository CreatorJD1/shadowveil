import json,numpy as np,sys
from PIL import Image
from handgeo import handgeo
from shape import shape_metrics
R='/workspace/shadowveil/views'; out={}
for v in ['apose','left','right','back']:
    r=json.load(open(f'{R}/{v}/hands/rig.json')); a0=np.array(Image.open(f'{R}/{v}/base.png').convert('RGBA'))[...,3]>0; ys=np.nonzero(a0.any(1))[0]; Hh=int(ys.max()-ys.min()+1)
    P={p['id']:p for p in r['parts']}
    for s in 'LR':
        if not P.get(s+'_palm',{}).get('file'): continue
        acc=None
        for p in r['parts']:
            if p['id'].startswith(s+'_') and p.get('file'):
                a=np.array(Image.open(f"{R}/{v}/hands/{p['file']}").convert('RGBA'))[...,3]>127; acc=a if acc is None else acc|a
        w=np.array([P[s+'_palm']['pivotX'],P[s+'_palm']['pivotY']],float); mcp=np.array([P[s+'_Middle1']['pivotX'],P[s+'_Middle1']['pivotY']],float)
        g=handgeo(acc,w,mcp-w); sm=shape_metrics(acc,w,mcp-w)
        rec=dict(H=Hh,L=g['L'],W=g['W'],tips=g['tips'],palm_len=g['palm_len'],palm_w=g['palm_w'],finger_len=g['finger_len'],thumb_side=sm['thumb_side'],rig_palm_len=float(np.linalg.norm(mcp-w)))
        for k in ('L','palm_len','palm_w','finger_len','rig_palm_len'):
            rec[k+'_n']=rec[k]/Hh if rec[k] else None
        out[f'{v}_{s}']=rec; print(v,s,{k:(round(x,4) if isinstance(x,float) else x) for k,x in rec.items()})
json.dump(out,open('ours3.json','w'))
