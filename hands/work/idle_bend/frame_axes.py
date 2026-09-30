# Drawn axis of each finger frame (PCA of alpha>=128 pixels) and pivot->childPivot direction, vs f0. Read-only.
import json,sys,numpy as np
from PIL import Image
R='/workspace/shadowveil/views'
def axis(fn,ref=None):
    a=np.array(Image.open(fn))[...,3]; ys,xs=np.nonzero(a>=128)
    if len(xs)<20: return None,0
    P=np.stack([xs,ys],1).astype(float); c=P.mean(0); u,s,vt=np.linalg.svd(P-c,full_matrices=False); d=vt[0]
    if ref is not None and np.dot(d,ref)<0: d=-d
    return (np.degrees(np.arctan2(d[1],d[0])),len(xs)),c
out={}
for view in sys.argv[1:]:
    j=json.load(open(f'{R}/{view}/hands/rig.json')); by={p['id']:p for p in j['parts']}
    for p in j['parts']:
        if not p.get('frames') or not p.get('file'): continue
        fid=p['id']; kid=next((q for q in j['parts'] if q.get('parent')==fid),None)
        piv=np.array([p['pivotX'],p['pivotY']]); row={}
        c0=np.array([kid['pivotX'],kid['pivotY']]) if kid and kid.get('pivotX') is not None else None
        ref=(c0-piv) if c0 is not None else None
        for k,e in enumerate(p['frames']):
            e=e if isinstance(e,dict) else {'file':e}
            (ax,cen)=axis(f'{R}/{view}/hands/{e["file"]}',ref)
            cp=np.array(e['childPivot']) if 'childPivot' in e else c0
            cpd=None if cp is None else (float(np.degrees(np.arctan2(*(cp-piv)[::-1]))),float(np.hypot(*(cp-piv))))
            row[f'f{k}']={'pcaDeg':None if ax is None else round(ax[0],1),'px':0 if ax is None else ax[1],'pivToChild':None if cpd is None else [round(cpd[0],1),round(cpd[1],1)]}
        out[f'{view}:{fid}']=row
        print(view,fid,'maxCurl',p['maxCurlDeg'],json.dumps(row))
json.dump(out,open('/workspace/shadowveil/hands/work/idle_bend/frame_axes.json','w'),indent=1)
