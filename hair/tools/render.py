# Faithful python mirror of rig/index.html hair drawing: chain(parts) -> M(id)=M(parent)*rotAt(pivot,angle),
# then T(0,dy)*M with dy=round(HairSwayY*swayY*swayYMaxPx) (not inherited). Canvas rotate(+deg)=clockwise (y down).
# Stack: hair parts layer<200, base_body.png (220), hair parts layer>=200 (eyes/mouth/hands at rest are pixel-equal to base
# so for hair QA the head crop uses base_body + face parts at rest drawn via optional 'face' overlay).
import json, numpy as np
from PIL import Image
from scipy import ndimage as ndi
R='/workspace/shadowveil'
def mul(a,b): return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
def rotAt(px,py,deg):
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t); return [c,s,-s,c,px-c*px+s*py,py-s*px-c*py]
I=[1,0,0,1,0,0]
def T(dx,dy): return [1,0,0,1,dx,dy]
def load_rig(v,hd=None):
    hd=hd or f'{R}/views/{v}/hair'; j=json.load(open(f'{hd}/rig.json'))
    return (j if isinstance(j,list) else j['parts']),(0 if isinstance(j,list) else j.get('swayYMaxPx',0))
def matrices(parts,ymax,sx,sy):
    by={p['id']:p for p in parts}; M={}
    def m(i):
        if i in M: return M[i]
        p=by[i]; q=p.get('parent'); base=m(q) if q and q in by else I
        M[i]=mul(base,rotAt(p.get('pivotX',0),p.get('pivotY',0),(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)*sx)); return M[i]
    out={}
    for p in parts:
        dy=int(np.floor(sy*min(1,max(0,p.get('swayY') or 0))*ymax+0.5))  # JS Math.round
        out[p['id']]=mul(T(0,dy),m(p['id']))
    return out
def warp(img,Mx,box=None):
    """draw full-canvas RGBA img (float, premultiplied) with affine Mx, bilinear; returns premult float array (box region)."""
    H,W=img.shape[:2]; x0,y0,x1,y1=box or (0,0,W,H)
    a,b,c,d,e,f=Mx
    if np.allclose(Mx,I): return img[y0:y1,x0:x1].copy()
    det=a*d-b*c; ia,ib,ic,id_=d/det,-b/det,-c/det,a/det
    oy,ox=np.mgrid[y0:y1,x0:x1].astype(float); ox+=0.5; oy+=0.5
    X=ox-e; Y=oy-f; sx=ia*X+ic*Y-0.5; sy=ib*X+id_*Y-0.5
    out=np.stack([ndi.map_coordinates(img[...,k],[sy,sx],order=1,mode='constant',cval=0) for k in range(4)],-1)
    return out
def premul(p): p=p.astype(float); p[...,:3]*=p[...,3:]/255; return p
def over(dst,src): return src+dst*(1-src[...,3:]/255)
def unpremul(p):
    a=p[...,3:]; rgb=np.where(a>0,p[...,:3]*255/np.maximum(a,1e-9),0); return np.clip(np.round(np.concatenate([rgb,a],-1)),0,255).astype(np.uint8)
_cache={}
def rgba(path):
    if path not in _cache: _cache[path]=premul(np.array(Image.open(path).convert('RGBA')))
    return _cache[path]
def render(v,sx=0,sy=0,box=None,hd=None,body=None,face=False,bg=None):
    parts,ymax=load_rig(v,hd); hd=hd or f'{R}/views/{v}/hair'
    Ms=matrices(parts,ymax,sx,sy)
    bb=rgba(body or f'{R}/views/{v}/base_body.png'); H,W=bb.shape[:2]; box=box or (0,0,W,H)
    x0,y0,x1,y1=box; can=np.zeros((y1-y0,x1-x0,4))
    if bg is not None: can[...]=list(bg)+[255]
    order=sorted(enumerate(parts),key=lambda t:(t[1]['layer'],t[0]))
    for _,p in order:
        if p['layer']<200: can=over(can,warp(rgba(f"{hd}/{p['file']}"),Ms[p['id']],box))
    can=over(can,bb[y0:y1,x0:x1])
    if face:  # eyes/mouth/hands at rest (layers 300-599) are exact base pixels: draw base where base_body differs & not hair
        fl=face_layer(v,hd)
        can=over(can,fl[y0:y1,x0:x1])
    for _,p in order:
        if p['layer']>=200: can=over(can,warp(rgba(f"{hd}/{p['file']}"),Ms[p['id']],box))
    return unpremul(can)
def face_layer(v,hd=None):
    key=('face',v)
    if key in _cache: return _cache[key]
    import glob
    fl=np.zeros_like(rgba(f'{R}/views/{v}/base.png'))
    for f in sorted(glob.glob(f'{R}/views/{v}/eyes/Eye*_white.png'))+sorted(glob.glob(f'{R}/views/{v}/eyes/Eye*_lid_0.png'))+sorted(glob.glob(f'{R}/views/{v}/eyes/Eye*_lash.png'))+glob.glob(f'{R}/views/{v}/mouth/rest.png'):
        fl=over(fl,rgba(f))
    _cache[key]=fl; return fl
