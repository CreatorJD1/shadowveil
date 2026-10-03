from common import *
V,C=VC(); L=render_cell(V,C,cfg,1,0)['L']
for k in ORDER:
    P=L[k]; a=P[...,3]; m=a>250; rgb=np.round(P[m][:,:3]*255/a[m,None]).astype(int)
    u,c=np.unique(rgb,axis=0,return_counts=True); o=np.argsort(-c)[:8]
    print(k,P.shape,int(m.sum()),[(tuple(u[i]),int(c[i])) for i in o])
