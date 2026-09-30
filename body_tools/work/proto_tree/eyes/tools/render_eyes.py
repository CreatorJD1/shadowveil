#!/usr/bin/env python3
"""Shadowveil eye renderer (mirrors the runtime contract: drawImage only).
Per eye, on an offscreen layer: draw <E>_white (source-over), then <E>_iris translated by the
integer gaze offset with source-atop (white alpha is the only mask). The eye layer is drawn over
base.png, then the nearest lid frame, then the lash. No shapes, no tinting, no morphing.
Usage: render_eyes.py <view> [EyeLOpen=1 EyeROpen=1 EyeBallX=0 EyeBallY=0] [-o out.png] [--base base.png]
"""
import json, sys, os
import numpy as np
from PIL import Image
VIEWS='/workspace/shadowveil/views'
DEFAULT_BASE={}  # base is always views/<view>/base.png unless --base is given
_cache={}
def load(p):
    if p not in _cache: _cache[p]=np.array(Image.open(p).convert('RGBA')).astype(np.float64)/255.0
    return _cache[p]
def shift(img,dx,dy):
    out=np.zeros_like(img); H,W=img.shape[:2]
    ys=slice(max(0,dy),min(H,H+dy)); yd=slice(max(0,-dy),min(H,H-dy))
    xs=slice(max(0,dx),min(W,W+dx)); xd=slice(max(0,-dx),min(W,W-dx))
    out[ys,xs]=img[yd,xd]; return out
def over(dst,src):   # canvas source-over (premultiplied math, straight in/out)
    sa=src[...,3:4]; da=dst[...,3:4]; oa=sa+da*(1-sa)
    oc=np.where(oa>0,(src[...,:3]*sa+dst[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0)
    return np.concatenate([oc,oa],-1)
def atop(dst,src):   # canvas source-atop
    sa=src[...,3:4]; da=dst[...,3:4]
    oc=np.where(da>0,(src[...,:3]*sa*da+dst[...,:3]*da*(1-sa))/np.maximum(da,1e-9),0)
    return np.concatenate([oc,da],-1)
def offsets(rig,X,Y):
    L=rig['irisLimitsPx']; X=min(1,max(-1,X)); Y=min(1,max(-1,Y))
    dx=X*(L['dxAtXplus1'] if X>0 else -L['dxAtXminus1']); dy=Y*(L['dyAtYplus1'] if Y>0 else -L['dyAtYminus1'])
    import math
    jsround=lambda z: int(math.floor(z+0.5))   # JS Math.round, as in rig/index.html
    return jsround(dx),jsround(dy)
def render(view,params=None,base=None):
    p=dict(EyeLOpen=1.0,EyeROpen=1.0,EyeBallX=0.0,EyeBallY=0.0); p.update(params or {})
    d=f'{VIEWS}/{view}/eyes'; rig=json.load(open(f'{d}/rig.json'))
    if base is None:
        b=f'{VIEWS}/{view}/base.png'; base=b
    full=load(base)
    dx,dy=offsets(rig,p['EyeBallX'],p['EyeBallY'])
    parts={q['id']:q for q in rig['parts']}
    # speed-up only: all eye parts are transparent outside rig['workRegion'], so compute there
    x0,y0,x1,y1=rig['workRegion']; R=(slice(y0,y1),slice(x0,x1))
    canvas=full[R].copy()
    ld=lambda f: load(f)[R]
    touched=np.zeros(canvas.shape[:2],bool)
    for e in rig['eyes']:
        layer=np.zeros_like(canvas)
        layer=over(layer,ld(f"{d}/{parts[e+'_white']['file']}"))
        layer=atop(layer,shift(ld(f"{d}/{parts[e+'_iris']['file']}"),dx,dy))
        canvas=over(canvas,layer); touched|=layer[...,3]>0
        op=min(1,max(0,p[e+'Open'])); n_=int(rig.get('lidFrames',5)); k=int(np.floor((1-op)*(n_-1)+0.5))   # JS Math.round, n = lidFrames (default 5)
        for f in (parts[f'{e}_lid_{k}']['file'],parts[e+'_lash']['file']):
            src=ld(f"{d}/{f}"); canvas=over(canvas,src); touched|=src[...,3]>0
    out=(full*255+0.5).astype(np.uint8)
    # pixels no part touched are left exactly as in the base (incl. RGB of alpha-0 pixels)
    sub=out[R]; sub[touched]=(canvas[touched]*255+0.5).astype(np.uint8); out[R]=sub
    return out
if __name__=='__main__':
    args=sys.argv[1:]; view=args.pop(0); out=None; base=None; params={}
    while args:
        a=args.pop(0)
        if a=='-o': out=args.pop(0)
        elif a=='--base': base=args.pop(0)
        else: k,v=a.split('='); params[k]=float(v)
    img=render(view,params,base)
    Image.fromarray(img,'RGBA').save(out or f'render_{view}.png'); print('wrote',out or f'render_{view}.png')
