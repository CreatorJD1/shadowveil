import json,numpy as np
from render import *
cfg=json.load(open('quality_cfg.json'))
def disp(parts,ymax,sid,tipid,far):
    M=matrices(parts,ymax,1,0)[tipid]; x,y=far; return np.hypot(M[0]*x+M[2]*y+M[4]-x,M[1]*x+M[3]*y+M[5]-y)
for v in ['apose','tpose','left','right','back']:
    parts,ymax=load_rig(v); old,_=load_rig(v,f'{R}/hair/backup_pre_quality/{v}')
    ob={p['id']:p for p in old}
    for p in parts:
        if not p['id'].endswith('_tip'): continue
        sid=p['id'][:-4]; a=np.array(Image.open(f"{R}/views/{v}/hair/{p['file']}"))[...,3]>0
        o=ob[sid]; ys,xs=np.where(a); j=np.argmax(np.hypot(xs-o['pivotX'],ys-o['pivotY'])); far=(xs[j],ys[j])
        dold=disp(old,ymax,sid,sid,far); dnew=disp(parts,ymax,sid,p['id'],far)
        k=cfg['views'][v]['strands'][sid]['k']; target=1.1*dold*k
        n=len([q for q in parts if q['id']==sid or q['id'].startswith(sid+'_')])
        D=[q['maxSwayDeg'] for q in parts if q['id']==sid or q['id'].startswith(sid+'_')]
        f=target/dnew; nd=[round(d*f,1) for d in D]
        cfg['views'][v]['strands'][sid]['deg']=nd
        print(v,sid,'old %.1f new %.1f target %.1f'%(dold,dnew,target),'deg',D,'->',nd)
json.dump(cfg,open('quality_cfg.json','w'),indent=1)
