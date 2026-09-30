"""PROPOSAL ONLY (not live): no side view of the anger face exists, so this is the FRONT anger mouth squashed horizontally
(scaleX = profile mouth width / source width, scaleY = front scale x profile/front face size) and fitted to the profile rest
mouth, clipped to her silhouette. Written to mouth/work/anger/proposal/<view>/anger.png only."""
import json,sys; import numpy as np
sys.path.insert(0,'/workspace/shadowveil/mouth/work'); from lipmask import load, lip_mask
from build_anger import build, SRC_W
G={'left':(609,285),'right':(774,272)}
CE={'apose':90.7,'left':88.4,'right':89.2}   # chin-to-eye-line, from mouth/work/turn_ref/ours_rest.json
rep={}
for v in ['left','right']:
    b=load(v); M,D,_=lip_mask(b,*G[v],profile=True); yd,xd=np.nonzero(D)
    rig=json.load(open(f'/workspace/shadowveil/views/{v}/mouth/rig.json'))
    x0,x1=xd.min(),xd.max()+1; sx=(x1-x0)/SRC_W; sy=0.5*CE[v]/CE['apose']
    r,k=build(v,out_dir=f'proposal/{v}',live=False,fit=dict(sx=sx,sy=sy,cx=(x0+x1)/2,seam=rig['anchor']['y']+0.5,D=D))
    r['PROPOSAL']='horizontally compressed FRONT anger mouth; not a real side view; not registered; live profile falls back to M'
    rep[v]=r; print(v,json.dumps(r['transform']),r['uncoveredRestLipPx'])
json.dump(rep,open('proposal/proposal_report.json','w'),indent=1)
