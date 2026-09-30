# Ear-fill analysis: python mirror of rig/index.html (v1.3) with every non-hair part at rest (cut body parts,
# hands f0, eyes white+iris(source-atop)+lid_0+lash, mouth rest), hair parts chained + swayY, bilinear for rotated.
import json, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
R='/workspace/shadowveil'; VIEWS=['apose','tpose','left','right','back']
def rgba(p): return np.array(Image.open(p).convert('RGBA')).astype(np.float64)
def premul(a): a=a.copy(); a[...,:3]*=a[...,3:]/255; return a
def over(d,s): return s+d*(1-s[...,3:]/255)
def unpremul(p):
    a=p[...,3:]; rgb=np.where(a>0,p[...,:3]*255/np.maximum(a,1e-9),0); return np.clip(np.round(np.concatenate([rgb,a],-1)),0,255).astype(np.uint8)
def J(p):
    try: return json.load(open(p))
    except Exception: return None
def mid_stack(v):
    """premultiplied composite of all layer 200..599 parts at rest (body, hands, eyes, mouth), full canvas"""
    cp=f'/tmp/earfill_mid_{v}.npy'
    if os.path.exists(cp): return np.load(cp)
    b=f'{R}/views/{v}/'
    items=[]
    bj=J(b+'body/rig.json'); body=bj['parts']
    if isinstance(bj,dict) and bj.get('skin') and os.path.exists(b+'body/'+bj['skin']):   # v1.4+ skin: per-layer groups of the skin image (rest = exact copy)
        import sys as _s; _s.path.insert(0,R+'/rig/skin_tools'); import skinlib
        sj,SV,ST,SL=skinlib.load(b+'body/'+bj['skin']); H_,W_=np.array(Image.open(b+'base.png')).shape[:2]
        lm,cnt=skinlib.coverage(SV,ST,SL,W_,H_); sa=rgba(b+sj.get('image','base_body.png'))
        for lay in sorted(set(SL.tolist())):
            g=sa.copy(); g[lm!=lay]=0; items.append((int(lay),1,len(items),('arr',g)))
    else:
      for i,p in enumerate(body):
        if p.get('file') and os.path.exists(b+'body/'+p['file']): items.append((p['layer'],1,len(items),b+'body/'+p['file']))
    hands=J(b+'hands/rig.json')
    if hands:
        for p in hands['parts']:
            if p.get('file'): items.append((p['layer'],2,len(items),b+'hands/'+p['file']))
    eyes=J(b+'eyes/rig.json')
    if eyes:
        Z={p['id']:p['layer'] for p in eyes['parts']}
        for E in eyes['eyes']:
            items.append((Z[E+'_white'],3,len(items),('eye',E)))
            items.append((Z[E+'_lid_0'],3,len(items),b+f'eyes/{E}_lid_0.png'))
            items.append((Z[E+'_lash'],3,len(items),b+f'eyes/{E}_lash.png'))
    mo=J(b+'mouth/rig.json')
    if mo: items.append((next(p['layer'] for p in mo['parts'] if p['id']=='mouth_rest'),4,len(items),b+'mouth/rest.png'))
    base=rgba(b+'base.png'); can=np.zeros_like(base)
    for z,st,sq,f in sorted(items,key=lambda t:t[:3]):
        if isinstance(f,tuple) and f[0]=='arr': im=f[1]
        elif isinstance(f,tuple):
            E=f[1]; w=rgba(b+f'eyes/{E}_white.png'); ir=rgba(b+f'eyes/{E}_iris.png')
            ai=ir[...,3:]/255; rgb=ir[...,:3]*ai+w[...,:3]*(1-ai); im=np.concatenate([rgb,w[...,3:]],-1)
        else: im=rgba(f)
        can=over(can,premul(im))
    np.save(cp,can); return can
def mul(a,b): return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
def rotAt(px,py,deg):
    if not abs(deg)>=0.01: return [1,0,0,1,0,0]
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t); return [c,s,-s,c,px-c*px+s*py,py-s*px-c*py]
I=[1,0,0,1,0,0]
def hair_rig(v,hd=None):
    j=json.load(open(f'{hd or R+"/views/"+v+"/hair"}/rig.json')); return j['parts'],j.get('swayYMaxPx',0)
def matrices(parts,ymax,sx,sy):
    """sx,sy: float (shared slider) or dict id->drive"""
    by={p['id']:p for p in parts}; M={}
    g=lambda s,i:(s.get(i,0) if isinstance(s,dict) else s)
    def m(i):
        if i in M: return M[i]
        p=by[i]; q=p.get('parent'); base=m(q) if q and q in by else I
        M[i]=mul(base,rotAt(p.get('pivotX',0),p.get('pivotY',0),(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)*max(-1,min(1,g(sx,i)))))
        return M[i]
    out={}
    for p in parts:
        dy=int(np.floor(max(-1,min(1,g(sy,p['id'])))*min(1,max(0,p.get('swayY') or 0))*ymax+0.5))
        out[p['id']]=mul([1,0,0,1,0,dy],m(p['id']))
    return out
def isAxis(M): return abs(M[1])<1e-9 and abs(M[2])<1e-9 and abs(M[0]-1)<1e-9 and abs(M[3]-1)<1e-9
def warp(img,M,box):
    x0,y0,x1,y1=box
    if isAxis(M):
        dx,dy=int(np.floor(M[4]+0.5)),int(np.floor(M[5]+0.5)); H,W=img.shape[:2]
        out=np.zeros((y1-y0,x1-x0,4))
        sy0,sy1=y0-dy,y1-dy; sx0,sx1=x0-dx,x1-dx
        cy0,cy1=max(0,sy0),min(H,sy1); cx0,cx1=max(0,sx0),min(W,sx1)
        if cy1>cy0 and cx1>cx0: out[cy0-sy0:cy1-sy0,cx0-sx0:cx1-sx0]=img[cy0:cy1,cx0:cx1]
        return out
    a,b,c,d,e,f=M; det=a*d-b*c
    oy,ox=np.mgrid[y0:y1,x0:x1].astype(float); X=ox+.5-e; Y=oy+.5-f
    sx=(d*X-c*Y)/det-.5; sy=(-b*X+a*Y)/det-.5
    return np.stack([ndi.map_coordinates(img[...,k],[sy,sx],order=1,mode='constant',cval=0) for k in range(4)],-1)
class View:
    def __init__(s,v,box,hd=None):
        s.v=v; s.box=box; s.hd=hd or f'{R}/views/{v}/hair'; s.parts,s.ymax=hair_rig(v,s.hd)
        x0,y0,x1,y1=box
        s.mid=mid_stack(v)[y0:y1,x0:x1]
        s.img={p['id']:premul(rgba(f"{s.hd}/{p['file']}")) for p in s.parts}
        s.order=[p for _,p in sorted(enumerate(s.parts),key=lambda t:(t[1]['layer'],t[0]))]
    def render(s,sx=0,sy=0,hair_back=None):
        Ms=matrices(s.parts,s.ymax,sx,sy); can=np.zeros(s.mid.shape)
        for p in s.order:
            if p['layer']<200:
                im=s.img[p['id']] if not (p['id']=='hair_back' and hair_back is not None) else hair_back
                can=over(can,warp(im,Ms[p['id']],s.box))
        can=over(can,s.mid)
        for p in s.order:
            if p['layer']>=200: can=over(can,warp(s.img[p['id']],Ms[p['id']],s.box))
        return can
