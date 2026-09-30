# QA-style hand defect counts (same definitions as rig/previews/idle/harness/qa.py: holes, tears (3px closing), seam alpha<255 inside 4px erosion)
# restricted to the hand region (union of posed hand layers dilated 12 px); new = not within 3/2 px of the same defect at rest.  qa_hand.py <dir> <side> cases...
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
D,S=sys.argv[1],sys.argv[2];cases=sys.argv[3:]
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op);b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));k=np.ones(n+1,bool);k[list(b)]=False;k[0]=False;return k[lab]
def masks(A):
    op=A>=128;e=enclosed(op);t=nd.binary_closing(op,structure=disk(3),border_value=0)&~op&~e;s=nd.binary_erosion(op,structure=disk(4),border_value=0)&(A<255);return e,t,s
m=json.load(open(D+'/meta.json'));C={c['name']:c for c in m['cases']}
def region(cn):
    U=None
    for p in C[cn]['parts']:
        if p.startswith(S+'_'):
            a=np.array(Image.open(f'{D}/{cn}_layers/{p}.png'))[...,3]>0;U=a if U is None else U|a
    ys,xs=np.nonzero(U);box=(max(0,ys.min()-30),ys.max()+30,max(0,xs.min()-30),xs.max()+30);return nd.binary_dilation(U,structure=disk(12)),box
RA=np.array(Image.open(f'{D}/rest.png'))[...,3]
res={}
for cn in cases:
    reg,(y0,y1,x0,x1)=region(cn);regR,_=region('rest')
    bb=(slice(min(y0,0+y0),y1),slice(x0,x1))
    A=np.array(Image.open(f'{D}/{cn}.png'))[...,3][bb];R0=RA[bb];rg=reg[bb]
    e,t,s=masks(A);re,rt,rs=masks(R0)
    ne=e&~nd.binary_dilation(re,structure=disk(3))&rg;nt=t&~nd.binary_dilation(rt,structure=disk(3))&rg;ns=s&~nd.binary_dilation(rs,structure=disk(2))&rg
    res[cn]=dict(newHoles=int(ne.sum()),newTears=int(nt.sum()),newSeamAlpha=int(ns.sum()))
    ys,xs=np.nonzero(ne|nt|ns);res[cn]['where']=[[int(x+x0),int(y+y0)] for y,x in list(zip(ys,xs))[:6]]
    print(cn,res[cn])
json.dump(res,open(f'{D}/qa_hand_{S}.json','w'),indent=1)
