# Knuckle angles + speck attribution from hb_render outputs (read-only).  analyze.py <renderdir> <view> [side]
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage as nd
D,view=sys.argv[1],sys.argv[2]; SIDE=sys.argv[3] if len(sys.argv)>3 else 'L'
meta=json.load(open(f'{D}/meta.json')); C={c['name']:c for c in meta['cases']}
rig=json.load(open(f'/workspace/shadowveil/views/{view}/hands/rig.json')); by={p['id']:p for p in rig['parts']}
def A(case,pid):
    return np.array(Image.open(f'{D}/{case}_layers/{pid}.png'))
def pca(a,ref=None):
    ys,xs=np.nonzero(a[...,3]>=128)
    if len(xs)<15: return None
    P=np.stack([xs,ys],1).astype(float);c=P.mean(0);_,_,vt=np.linalg.svd(P-c,full_matrices=False);d=vt[0]
    if ref is not None and np.dot(d,ref)<0: d=-d
    return d
ang=lambda d:np.degrees(np.arctan2(d[1],d[0]))
wrap=lambda x:(x+180)%360-180
rot=lambda M:np.degrees(np.arctan2(M[1],M[0]))
out={}
cases=[n for n in C if n.startswith('curl_')]
for F in ['Index','Middle']:
    s1,s2=f'{SIDE}_{F}1',f'{SIDE}_{F}2'
    r1=pca(A('rest',s1)); r2=pca(A('rest',s2),r1)
    for cn in cases:
        c=C[cn]; P=c['parts']
        d1=pca(A(cn,s1),r1); d2=pca(A(cn,s2),r1)
        rotK1=wrap(rot(P[s1]['M'])-rot(P[f'{SIDE}_palm']['M'])); rotK2=wrap(rot(P[s2]['M'])-rot(P[s1]['M']))
        w90=lambda x:(x+90)%180-90
        pix1=None if d1 is None else rotK1+w90(wrap(ang(d1)-ang(r1))-rotK1); pix2=None if (d2 is None or d1 is None) else rotK2+w90(wrap((ang(d2)-ang(r2))-(ang(d1)-ang(r1)))-rotK2)
        out[f'{F} {cn}']=dict(frame=P[s1]['frame'],rotPalmSeg1=round(rotK1,1),rotSeg1Seg2=round(rotK2,1),pixPalmSeg1=None if pix1 is None else round(pix1,1),pixSeg1Seg2=None if pix2 is None else round(pix2,1),tipWorld=round(wrap(rot(P[f'{SIDE}_{F}3']['M'])-rot(P[f'{SIDE}_palm']['M'])),1))
for k,vv in out.items(): print(view,SIDE,k,vv)
json.dump(out,open(f'{D}/angles_{SIDE}.json','w'),indent=1)
# specks: tiny alpha components of each drawn hand layer that are visible (layer is top at >=50% of their px) in the final render
print('--- specks (tiny <=15px components of a layer, visible on top in the composite)')
sp={}
for cn in ['rest']+cases:
    fin=np.array(Image.open(f'{D}/{cn}.png')).astype(int); rows=[]
    parts=sorted([p for p in rig['parts'] if p.get('file') and p['id'].startswith(SIDE)],key=lambda p:C[cn]['parts'][p['id']]['layer'])
    L={p['id']:A(cn,p['id']).astype(int) for p in parts}
    for i,p in enumerate(parts):
        a=L[p['id']]; m=a[...,3]>=100; lab,n=nd.label(m,structure=np.ones((3,3)))
        if n<2: continue
        sz=nd.sum(m,lab,range(1,n+1))
        above=np.zeros(m.shape,bool)
        for q in parts[i+1:]: above|=L[q['id']][...,3]>=200
        below=np.zeros(m.shape,bool)
        for q in parts[:i]: below|=L[q['id']][...,3]>=200
        for k in np.nonzero(sz<=15)[0]:
            cm=lab==k+1; vis=cm&~above
            if vis.sum()==0: continue
            ys,xs=np.nonzero(vis); lum=a[...,:3][vis].mean()
            rows.append(dict(part=p['id'],px=int(cm.sum()),visible=int(vis.sum()),overOther=int((vis&below).sum()),onBg=int((vis&~below).sum()),xy=[int(xs.mean()),int(ys.mean())],lum=int(lum)))
    sp[cn]=rows; print(cn,len(rows),'visible specks', rows[:12])
json.dump(sp,open(f'{D}/specks_{SIDE}.json','w'),indent=1)
