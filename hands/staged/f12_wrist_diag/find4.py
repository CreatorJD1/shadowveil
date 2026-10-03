import sys,json,numpy as np
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/diag_body/tools')
from common import *
from scipy import ndimage as nd
DC=json.load(open(f'{ROOT}/hands/work/turn_check/diag_check.json'))
out={}
for ang in ['045','315']:
    F=frame(ang);fg,_=fg_mask(F);T=team_masks(ang);yy,xx=np.mgrid[0:1168,0:768]
    for S in 'LR':
        d=DC[f"{ANG[ang]['hands']}_{S}"];wx,wy=d['wrist'];th=np.deg2rad(d['axis_deg']);u=np.array([np.cos(th),np.sin(th)]);H=T['hand_'+S]
        sd=(xx+.5-wx)*u[0]+(yy+.5-wy)*u[1]
        if sd[H].mean()<0: sd=-sd
        m=fg&~H&(sd>=0)&nd.binary_dilation(H,iterations=3)
        ys,xs=np.nonzero(m);pts=[dict(x=int(x),y=int(y),rgb=F[y,x].tolist(),sd=round(float(sd[y,x]),2),dist_to_hand=None,key=bool(F[y,x,2]-max(F[y,x,0],F[y,x,1])>25)) for y,x in zip(ys,xs)]
        dt=nd.distance_transform_edt(~H)
        for p in pts: p['dist_to_hand']=round(float(dt[p['y'],p['x']]),2)
        out[f'{ang}_{S}']=pts;print(ang,S,len(pts),pts)
json.dump(out,open('find4.json','w'),indent=1)
