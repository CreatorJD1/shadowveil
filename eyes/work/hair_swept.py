"""Swept (union over sway) alpha of every hair part in a view, following rig/index.html:
angle = swayWeight*maxSwayDeg*s about own pivot, in parent's transformed space; dy = round(sY*swayY*swayYMaxPx).
Parent and own sway are sampled independently (conservative)."""
import json, numpy as np, os
from PIL import Image
from scipy import ndimage as ndi
ROOT='/workspace/shadowveil/views'
_c={}
def swept(view, ids=None, n=31, dilate=True):
    key=(view,tuple(ids) if ids else None,n,dilate)
    if key in _c: return _c[key]
    p=f'{ROOT}/{view}/hair/rig.json'
    if not os.path.exists(p): return None
    rig=json.load(open(p)); parts=rig['parts'] if isinstance(rig,dict) else rig
    ymax=float(rig.get('swayYMaxPx',0)) if isinstance(rig,dict) else 0.0
    by={q['id']:q for q in parts}
    def chain(q):
        c=[]
        while q is not None:
            c.append(q); q=by.get(q.get('parent'))
        return c  # own first, then ancestors
    H=W=None; out=None
    for q in parts:
        if not q.get('file') or (ids and q['id'] not in ids): continue
        a=np.array(Image.open(f'{ROOT}/{view}/hair/{q["file"]}').convert('RGBA'))[...,3]>0
        if H is None: H,W=a.shape; out=np.zeros((H,W),bool)
        ys,xs=np.nonzero(a)
        if len(xs)==0: continue
        pts=np.stack([xs+0.5,ys+0.5],1)
        ch=chain(q); amp=[(c_.get('swayWeight') or 0)*(c_.get('maxSwayDeg') or 0) for c_ in ch]
        grids=[np.linspace(-A,A,n) if A>0 else [0.0] for A in amp]
        dys=range(-int(round(abs(q.get('swayY') or 0)*ymax)),int(round(abs(q.get('swayY') or 0)*ymax))+1)
        import itertools
        for angs in itertools.product(*grids):
            P=pts.copy()
            for c_,ang in zip(ch,angs):     # own rotation first, then each ancestor about its pivot
                if ang==0: continue
                t=np.deg2rad(ang); cx,cy=c_['pivotX'],c_['pivotY']
                x=P[:,0]-cx; y=P[:,1]-cy
                P=np.stack([cx+x*np.cos(t)-y*np.sin(t), cy+x*np.sin(t)+y*np.cos(t)],1)
            for dy in dys:
                xi=np.floor(P[:,0]).astype(int); yi=np.floor(P[:,1]+dy).astype(int)
                ok=(xi>=0)&(xi<W)&(yi>=0)&(yi<H); out[yi[ok],xi[ok]]=True
    if out is not None and dilate: out=ndi.binary_dilation(out,iterations=1)
    _c[key]=out; return out
if __name__=='__main__':
    import sys
    m=swept(sys.argv[1], sys.argv[2:] or None); print(m.sum())
