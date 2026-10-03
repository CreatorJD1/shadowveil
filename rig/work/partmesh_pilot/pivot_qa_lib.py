import json,numpy as np
from PIL import Image
from scipy import ndimage as nd
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op);b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));k=np.ones(n+1,bool);k[list(b)]=False;k[0]=False;return k[lab]
def masks(A):
    op=A>=128;e=enclosed(op);t=nd.binary_closing(op,structure=disk(3),border_value=0)&~op&~e;s=nd.binary_erosion(op,structure=disk(4),border_value=0)&(A<255);return e,t,s
_M={}
def comp_dir(D,cn,S):
    if D not in _M: _M[D]={c['name']:c for c in json.load(open(D+'/meta.json'))['cases']}
    C=_M[D];ps=sorted([k for k in C[cn]['parts'] if k.startswith(S+'_')],key=lambda k:C[cn]['parts'][k]['layer']);out=None
    for p in ps:
        im=Image.open(f'{D}/{cn}_layers/{p}.png').convert('RGBA');out=im if out is None else Image.alpha_composite(out,im)
    return np.array(out)
