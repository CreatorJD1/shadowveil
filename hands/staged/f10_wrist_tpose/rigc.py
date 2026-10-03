import json,sys,numpy as np
from PIL import Image
runs=sys.argv[1:];sys.argv=['x','','/tmp/none.json'];src=open('../idle_bend/f10/wrist_sim_t.py').read();pre=src.split("res={'order'")[0].replace(";HS={S:hand(S) for S in 'LR'}","")
exec(pre)
L=lambda f:np.array(Image.open(f).convert('RGBA'))
CASES=['wrist_Lp1','wrist_Lm1','wrist_Rp1','wrist_Rm1','anger+0.14','jump-0.2','jump+0.2969','run-0.12','run+0.12']
res={}
for run in ['ul']+runs:
    r0=L(f'{run}/rest.png');tot={'holes':0,'tears':0,'partial':0,'breaks':0};worst=[]
    for S in 'LR':
        m0,_=metrics(r0,S)
        for c in CASES:
            if c.startswith('wrist_') and c[6]!=S: continue
            m,_=metrics(L(f'{run}/{c}.png'),S)
            for k in tot: tot[k]+=m[k]-m0[k]
            if m['breaks']>m0['breaks'] or m['holes']>m0['holes']: worst.append((S,c,m['holes']-m0['holes'],m['breaks']-m0['breaks']))
    px={c:int((L(f'ul/{c}.png')!=L(f'{run}/{c}.png')).any(-1).sum()) for c in ['rest','pose_Fist','pose_Point','pose_Peace']}
    res[run]=dict(tot=tot,new_holes_or_breaks=worst,px_vs_live_under=px);print(run,tot,worst,px)
json.dump(res,open('rigc_'+'_'.join(runs)+'.json','w'),indent=1)
