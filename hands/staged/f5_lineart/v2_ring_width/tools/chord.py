import sys,json,numpy as np; sys.path.insert(0,'/workspace/shadowveil/hands/qa/scale_audit/tools')
from f5_meas import geo
R='/workspace/shadowveil/'; d=sys.argv[1]
rig=json.load(open(R+'views/back/hands/rig.json')); P={p['id']:p for p in rig['parts']}
for pid in ('L_Ring1','R_Ring1'):
    piv=(P[pid]['pivotX'],P[pid]['pivotY']); g,_=geo(f'{d}/{pid}_f1.png',piv); l,_=geo(R+f'views/back/hands/{pid}_f1.png',piv)
    print(pid,'medchord',round(g['median_chord_w']-l['median_chord_w'],2),'reach',round(g['reach']-l['reach'],2),'maxw',round(g['width']-l['width'],2))
