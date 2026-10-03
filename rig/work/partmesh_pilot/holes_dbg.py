import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.dont_write_bytecode=True
from pivot_qa_lib import comp_dir
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op);b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));k=np.ones(n+1,bool);k[list(b)]=False;k[0]=False;return k[lab]
def masks(A):
    op=A>=128;e=enclosed(op);t=nd.binary_closing(op,structure=disk(3),border_value=0)&~op&~e;return e,t
for cn in sys.argv[1:]:
    r={}
    for t in ['base','pm']:
        A=comp_dir(f'r_{t}_data',cn,'R')[...,3];e,tt=masks(A);r[t]=(e,tt)
    for k,name in [(0,'holes'),(1,'tears')]:
        a,b=r['base'][k],r['pm'][k]
        for lab,tag in [(b&~a,'new in pm'),(a&~b,'gone in pm')]:
            L,n=nd.label(lab);
            for i in range(1,n+1):
                ys,xs=np.nonzero(L==i);print(cn,name,tag,len(xs),'at',int(xs.mean()),int(ys.mean()))
