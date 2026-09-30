import json,numpy as np
from PIL import Image
from scipy import ndimage as nd
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op);b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));k=np.ones(n+1,bool);k[list(b)]=False;k[0]=False;return k[lab]
def masks(A):
    op=A>=128;e=enclosed(op);t=nd.binary_closing(op,structure=disk(3),border_value=0)&~op&~e;s=nd.binary_erosion(op,structure=disk(4),border_value=0)&(A<255);return e,t,s
class Run:
    def __init__(s,D):
        s.D=D;m=json.load(open(D+'/meta.json'));s.C={c['name']:c for c in m['cases']}
    def parts(s,cn,S): return sorted([k for k in s.C[cn]['parts'] if k.startswith(S+'_')],key=lambda k:s.C[cn]['parts'][k]['layer'])
    def layer(s,cn,p): return np.array(Image.open(f'{s.D}/{cn}_layers/{p}.png').convert('RGBA'))
    def comp(s,cn,S):
        out=None
        for p in s.parts(cn,S):
            im=Image.open(f'{s.D}/{cn}_layers/{p}.png').convert('RGBA');out=im if out is None else Image.alpha_composite(out,im)
        return np.array(out)
    def defects(s,cn,S):
        R0=s.comp('rest',S)[...,3];A=s.comp(cn,S)[...,3];re,rt,rs=masks(R0);e,t,se=masks(A)
        return e&~nd.binary_dilation(re,structure=disk(3)),t&~nd.binary_dilation(rt,structure=disk(3)),se&~nd.binary_dilation(rs,structure=disk(2))
