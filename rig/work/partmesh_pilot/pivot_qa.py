# Hand-only composite (hand layers over transparent, in layer order) -> QA defects (holes / tears(3px closing) / partial alpha inside 4px erosion)
# that are new vs rest; counted within R px of each finger seg1 pivot (Index..Pinky) and in the whole hand.  pivot_qa.py <dir> <view> <out.json>
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
D,view,OUT=sys.argv[1],sys.argv[2],sys.argv[3];RAD=12
rig=json.load(open(sys.argv[4] if len(sys.argv)>4 else f'/workspace/shadowveil/views/{view}/hands/rig.json'));by={p['id']:p for p in rig['parts']}
meta=json.load(open(D+'/meta.json'));C={c['name']:c for c in meta['cases']}
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op);b=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));k=np.ones(n+1,bool);k[list(b)]=False;k[0]=False;return k[lab]
def masks(A):
    op=A>=128;e=enclosed(op);t=nd.binary_closing(op,structure=disk(3),border_value=0)&~op&~e;s=nd.binary_erosion(op,structure=disk(4),border_value=0)&(A<255);return e,t,s
def comp(cn,S):
    ps=sorted([k for k in C[cn]['parts'] if k.startswith(S+'_')],key=lambda k:C[cn]['parts'][k]['layer'])
    out=None
    for p in ps:
        im=Image.open(f'{D}/{cn}_layers/{p}.png').convert('RGBA')
        out=im if out is None else Image.alpha_composite(out,im)
    return np.array(out)
res={}
for S in 'LR':
    if not (by.get(S+'_palm') or {}).get('file'): continue
    piv=[(by[f'{S}_{f}1']['pivotX'],by[f'{S}_{f}1']['pivotY']) for f in ['Index','Middle','Ring','Pinky']]
    R0=comp('rest',S)[...,3];ys,xs=np.nonzero(R0);y0,y1,x0,x1=ys.min()-40,ys.max()+40,xs.min()-40,xs.max()+40
    R0=R0[y0:y1,x0:x1];re,rt,rs=masks(R0)
    yy,xx=np.mgrid[y0:y1,x0:x1];PV=np.zeros(R0.shape,bool)
    for px,py in piv: PV|=(xx-px)**2+(yy-py)**2<=RAD*RAD
    for cn in [c for c in C if c!='rest']:
        A=comp(cn,S)[y0:y1,x0:x1,3];e,t,s=masks(A)
        ne=e&~nd.binary_dilation(re,structure=disk(3));nt=t&~nd.binary_dilation(rt,structure=disk(3));ns=s&~nd.binary_dilation(rs,structure=disk(2))
        r=dict(pivot_holes=int((ne&PV).sum()),pivot_tears=int((nt&PV).sum()),pivot_partial=int((ns&PV).sum()),hand_holes=int(ne.sum()),hand_tears=int(nt.sum()),hand_partial=int(ns.sum()))
        KN=np.zeros(R0.shape,bool)
        for f in ['Index','Middle']:
            px,py=by[f'{S}_{f}1']['pivotX'],by[f'{S}_{f}1']['pivotY'];KN|=((xx-px)**2+(yy-py)**2<=81)&(yy<=py+1)
        r['knuckle']=int(((nt|ns|ne)&KN).sum())
        yy2,xx2=np.nonzero((ne|nt|ns)&PV);r['pivot_px']=[[int(x+x0),int(y+y0)] for y,x in zip(yy2,xx2)]
        res[f'{S} {cn}']=r;print(view,S,cn,{k:v for k,v in r.items() if k!='pivot_px'})
json.dump(res,open(OUT,'w'))
