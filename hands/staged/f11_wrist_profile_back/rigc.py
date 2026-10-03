# F11 real-rig metrics: rigc.py <view> <run...>  (control = <view>/ctrl)
import json,sys,numpy as np
from PIL import Image
V=sys.argv[1];runs=sys.argv[2:];sys.argv=['x',V,'','/tmp/none.json'];src=open('../idle_bend/f11/wrist_sim_v.py').read();pre=src.split("res={'order'")[0].replace(";HS={S:hand(S) for S in SIDES}","")
exec(pre)
L=lambda f:np.array(Image.open(f).convert('RGBA'))
CASES=['wrist_Lp1','wrist_Lm1','wrist_Rp1','wrist_Rm1','anger+0.14','jump-0.2','jump+0.2969','run-0.12','run+0.12']
res={}
def met(run):
    r0=L(f'{V}/{run}/rest.png');o={}
    for S in SIDES:
        m0,_=metrics(r0,S);o[f'{S} rest']=m0
        for c in CASES:
            if c.startswith('wrist_') and c[6]!=S: continue
            m,_=metrics(L(f'{V}/{run}/{c}.png'),S);o[f'{S} {c}']={k:m[k]-m0[k] for k in ('holes','tears','partial','breaks')}|{'breaks_abs':m['breaks'],'holes_abs':m['holes'],'dw':None if m['width'] is None or m0['width'] is None else round(m['width']-m0['width'],3)}
    return o
C=met('ctrl');res['ctrl']=C
for run in runs:
    R=met(run);px={c:int((L(f'{V}/ctrl/{c}.png')!=L(f'{V}/{run}/{c}.png')).any(-1).sum()) for c in ['rest','pose_Fist','pose_Point','pose_Peace']+CASES}
    worse=[(k,{m:(C[k][m],R[k][m]) for m in ('holes','tears','breaks') if R[k][m]>C[k][m]}) for k in R if 'rest' not in k]
    worse=[w for w in worse if w[1]];mx=max(abs(R[k]['dw'] or 0) for k in R if 'rest' not in k)
    abs_=[(k,R[k]['holes_abs'],R[k]['breaks_abs']) for k in R if 'rest' not in k and (R[k]['holes_abs'] or R[k]['breaks_abs'])]
    res[run]=dict(metrics=R,px_vs_ctrl=px,worse_than_ctrl=worse,max_abs_dw=mx,abs_holes_breaks=abs_)
    print(V,run,'px',{k:px[k] for k in ['rest','pose_Fist','pose_Point','pose_Peace']},'worse',worse,'max|dw|',mx,'abs holes/breaks',abs_)
ca=[(k,C[k]['holes_abs'],C[k]['breaks_abs']) for k in C if 'rest' not in k and (C[k]['holes_abs'] or C[k]['breaks_abs'])];print(V,'ctrl abs holes/breaks',ca)
json.dump(res,open(f'rigc_{V}.json','w'),indent=1)
