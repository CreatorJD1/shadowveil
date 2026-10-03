# lean per-hand curl sweep: part PNGs cropped to the hand box once (float32), sim.py's warp/holes metric, rig curl magnitudes overridden in memory
import json,sys,os,numpy as np
from PIL import Image
sys.argv=['x',os.environ.get('ROOT','/workspace/scratch/f8/try4'),'/tmp/none.json'];src=open('sim.py').read().split('res={}')[0];exec(src)
def load(ang,S):
    rig=json.load(open(f'{ROOT}/{ang}/rig.json'));P={p['id']:p for p in rig['parts'] if p['id'].startswith(S+'_')}
    raw={k:np.array(Image.open(f'{ROOT}/{ang}/'+p['file']).convert('RGBA')) for k,p in P.items()}
    al=sum((i[...,3]>0).astype(np.uint8) for i in raw.values())>0;ys,xs=np.nonzero(al)
    box=(max(0,xs.min()-90),max(0,ys.min()-90),min(1365,xs.max()+90),min(1739,ys.max()+90))
    ims={k:(v[box[1]:box[3],box[0]:box[2]].astype(np.float32)/255.) for k,v in raw.items()};del raw
    return P,ims,box
def comp(P,ims,box,pose,cf,ct):
    Ms={}
    def M(k):
        if k in Ms: return Ms[k]
        p=P[k];par=p.get('parent');Mp=M(par) if par else np.eye(3)
        f=k.split('_')[1];fn=f[:-1] if f[-1].isdigit() else None;cv=POSES[pose].get(fn,0) if fn else 0
        mag=0 if fn is None else (ct if fn=='Thumb' else cf)[int(f[-1])-1]*np.sign(p.get('maxCurlDeg',0) or 1)
        # pivots are in view coords; images are cropped -> shift pivot into crop coords
        Ms[k]=Mp@R(p['pivotX']-box[0],p['pivotY']-box[1],cv*mag);return Ms[k]
    h,w=ims[next(iter(ims))].shape[:2];c=np.zeros((h,w,4))
    for k in sorted(P,key=lambda k:P[k]['layer']): c=over(c,warp(ims[k],M(k),(0,0,w,h)))
    return c
F=[tuple(map(float,x.split(','))) for x in os.environ.get('FS','90,95,15;120,40,15;100,80,10').split(';')];T=[tuple(map(float,x.split(','))) for x in os.environ.get('TS','5,60,25').split(';')]
for ang in os.environ['ANGS'].split(','):
    S=NEAR[ang];P,ims,box=load(ang,S);best=None
    r0=holes(comp(P,ims,box,'rest',F[0],T[0]));print(ang,S,'rest',r0,flush=True)
    for cf in F:
        for ct in T:
            r={pose:holes(comp(P,ims,box,pose,cf,ct)) for pose in ['Fist','Point','Peace']};mx=max(v['max'] for v in r.values());tot=sum(v['total'] for v in r.values())
            print(ang,S,cf,ct,{k:(v['n'],v['max']) for k,v in r.items()},'max',mx,'total',tot,flush=True)
            if best is None or (mx,tot)<best[0]: best=((mx,tot),cf,ct)
    print('BEST',ang,best,flush=True);del ims
