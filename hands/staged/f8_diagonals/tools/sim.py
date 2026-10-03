# F8 scratch sim: curl the staged near hands (rotation-only chain, angle = curl*maxCurlDeg about each pivot, premultiplied bilinear)
# and measure holes (enclosed transparent areas, A<128) in a box round the hand; live reference = the pulled renderer's apose
# render (f8/live_apose, layers) with the same metric.  sim.py <staged root> <out.json>
import json,sys,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
ROOT,OUTJ=sys.argv[1],sys.argv[2]
POSES={'rest':{},'Fist':dict(Thumb=1,Index=1,Middle=1,Ring=1,Pinky=1),'Point':dict(Thumb=1,Index=0,Middle=1,Ring=1,Pinky=1),'Peace':dict(Thumb=1,Index=0,Middle=0,Ring=1,Pinky=1)}
NEAR={'45':'L','135':'L','225':'R','315':'R'}
def rgba(f): return np.array(Image.open(f).convert('RGBA')).astype(float)/255.
def over(c,a):
    al=a[...,3:4];oa=al+c[...,3:4]*(1-al);return np.concatenate([np.where(oa>0,(a[...,:3]*al+c[...,:3]*c[...,3:4]*(1-al))/np.maximum(oa,1e-9),0),oa],-1)
def R(px,py,deg):
    t=np.radians(deg);c,s=np.cos(t),np.sin(t);return np.array([[c,-s,px-c*px+s*py],[s,c,py-s*px-c*py],[0,0,1]])
def warp(im,M,box):
    x0,y0,x1,y1=box;Y,X=np.mgrid[y0:y1,x0:x1].astype(float)+.5;Mi=np.linalg.inv(M);sx=Mi[0,0]*X+Mi[0,1]*Y+Mi[0,2]-.5;sy=Mi[1,0]*X+Mi[1,1]*Y+Mi[1,2]-.5
    pm=im.copy();pm[...,:3]*=pm[...,3:4];o=np.stack([nd.map_coordinates(pm[...,k],[sy,sx],order=1,mode='constant') for k in range(4)],-1)
    return np.concatenate([np.where(o[...,3:4]>0,o[...,:3]/np.maximum(o[...,3:4],1e-9),0),o[...,3:4]],-1)
def holes(c):
    op=c[...,3]>=0.5;lab,n=nd.label(~op);brd=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))
    sz=[int((lab==k).sum()) for k in range(1,n+1) if k not in brd]
    t=nd.binary_closing(op,structure=np.ones((5,5)),border_value=0)&~op&~np.isin(lab,[k for k in range(1,n+1) if k not in brd])
    return dict(n=len(sz),max=max(sz) if sz else 0,total=sum(sz),tears=int(t.sum()),opaque=int(op.sum()))
def comp_ours(ang,S,pose):
    rig=json.load(open(f'{ROOT}/{ang}/rig.json'));P={p['id']:p for p in rig['parts'] if p['id'].startswith(S+'_')}
    ims={k:rgba(f'{ROOT}/{ang}/'+p['file']) for k,p in P.items()};al=sum(i[...,3] for i in ims.values())>0;ys,xs=np.nonzero(al)
    box=(max(0,xs.min()-90),max(0,ys.min()-90),min(1365,xs.max()+90),min(1739,ys.max()+90))
    Ms={}
    def M(k):
        if k in Ms: return Ms[k]
        p=P[k];par=p.get('parent');Mp=M(par) if par else np.eye(3)
        f=k.split('_')[1][:-1] if k.split('_')[1][-1].isdigit() else None;cv=POSES[pose].get(f,0) if f else 0
        Ms[k]=Mp@R(p['pivotX'],p['pivotY'],cv*p.get('maxCurlDeg',0));return Ms[k]
    c=np.zeros((box[3]-box[1],box[2]-box[0],4))
    for k in sorted(P,key=lambda k:P[k]['layer']): c=over(c,warp(ims[k],M(k),box))
    return c
def comp_live(S,pose):
    d=f'live_apose/{"rest" if pose=="rest" else "pose_"+pose}_layers';rig=json.load(open('/workspace/shadowveil/views/apose/hands/rig.json'))
    ps=sorted([p for p in rig['parts'] if p.get('file') and p['id'].startswith(S+'_')],key=lambda p:p['layer']);c=None
    for p in ps:
        f=f'{d}/{p["id"]}.png'
        if not os.path.exists(f): continue
        a=rgba(f);c=a if c is None else over(c,a)
    ys,xs=np.nonzero(c[...,3]>0);return c[max(0,ys.min()-90):ys.max()+90,max(0,xs.min()-90):xs.max()+90]
res={}
for S in 'LR':
    for pose in POSES: res[f'live_apose_{S}_{pose}']=holes(comp_live(S,pose))
for ang,S in NEAR.items():
    for pose in POSES:
        c=comp_ours(ang,S,pose);res[f'{ang}_{S}_{pose}']=holes(c)
        Image.fromarray(np.round(c*255).astype(np.uint8)).save(f'{os.path.dirname(OUTJ) or "."}/sim_{ang}_{S}_{pose}.png')
for k,v in res.items(): print(k,v)
json.dump(res,open(OUTJ,'w'),indent=1)
