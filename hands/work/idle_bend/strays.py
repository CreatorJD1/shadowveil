# floating specks: connected components (alpha>=40, 8-conn) of the hand-only composite smaller than 25 px, with owning layer
import sys,numpy as np
from scipy import ndimage as nd
from qalib import *
def strays(D,cn,S):
    r=Run(D);A=r.comp(cn,S)[...,3];lab,n=nd.label(A>=40,structure=np.ones((3,3)));sz=nd.sum(A>=40,lab,range(1,n+1));out=[]
    for k in np.nonzero(sz<25)[0]:
        ys,xs=np.nonzero(lab==k+1);own=[p for p in r.parts(cn,S) if (r.layer(cn,p)[ys,xs,3]>=40).any()]
        out.append((int(sz[k]),int(xs.mean()),int(ys.mean()),own))
    return out
if __name__=='__main__':
    for D in sys.argv[2:]:
        for S in 'LR':
            for cn in ['curl_0.20','curl_0.30','curl_0.50','curl_0.70','curl_1.00']:
                s=strays(D,cn,S)
                if s: print(D.split('renders/')[-1],sys.argv[1],S,cn,s)
