import sys,numpy as np
from qalib import *
D,view=sys.argv[1],sys.argv[2];r=Run(D)
for S in 'LR':
    ps=r.parts('rest',S);pal=S+'_palm';above=[p for p in ps if p!=pal]
    cover=np.zeros((1739,1365),bool)
    for p in above: cover|=r.layer('rest',p)[...,3]==255
    PA=r.layer('rest',pal)[...,3]
    for cn in ['curl_0.20','curl_0.30','curl_0.50','curl_0.70','curl_1.00']:
        e,t,s=r.defects(cn,S);d=e|t|s
        fix=d&cover&(PA<255); vis=d&~cover
        ys,xs=np.nonzero(vis)
        print(view,S,cn,'defects',int(d.sum()),'palm-fixable',int(fix.sum()),'already palm-opaque under',int((d&cover&(PA==255)).sum()),'visible-at-rest(no-touch)',int(vis.sum()),'e.g.',list(zip(xs[:5].tolist(),ys[:5].tolist())))
