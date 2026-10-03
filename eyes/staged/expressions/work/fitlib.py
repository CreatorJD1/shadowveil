"""Shared helpers for the staged front (apose) expression parts. Read-only on rig/ and views/."""
import json, numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT='/workspace/shadowveil'
BASE=f'{ROOT}/views/apose/base.png'
EYES=f'{ROOT}/views/apose/eyes'
W8=np.array([0.299,0.587,0.114])

def load_rgb(p): return np.array(Image.open(p).convert('RGB')).astype(np.int32)
def lum(rgb): return (rgb*W8).sum(-1)
def alpha(f): return np.array(Image.open(f'{EYES}/{f}'))[...,3]>0

_base=None
def base():
    global _base
    if _base is None: _base=np.array(Image.open(BASE).convert('RGBA'))
    return _base

def medoid(cols):
    """actual colour from the set closest to the per-channel median (so it is an exact base tone)"""
    cols=np.asarray(cols).reshape(-1,3)
    med=np.median(cols,0)
    i=np.argmin(((cols-med)**2).sum(1)); return tuple(int(v) for v in cols[i])

def corners(open_mask):
    ys,xs=np.nonzero(open_mask)
    xl,xr=xs.min(),xs.max()
    pl=(xl+0.5, ys[xs==xl].mean()+0.5); pr=(xr+0.5, ys[xs==xr].mean()+0.5)
    return np.array(pl),np.array(pr)

class Frame:
    """eye frame: outer corner O -> inner corner I. u along O->I (0..1), v perpendicular (down positive for a level eye) in units of |OI|"""
    def __init__(s,O,I):
        s.O=np.asarray(O,float); s.I=np.asarray(I,float); s.d=s.I-s.O; s.L=np.hypot(*s.d)
        s.ex=s.d/s.L; s.ey=np.array([-s.ex[1],s.ex[0]])
        if s.ey[1]<0: s.ey=-s.ey
    def to_uv(s,p):
        p=np.asarray(p,float)-s.O; return np.stack([p@s.ex/s.L, p@s.ey/s.L],-1)
    def from_uv(s,uv):
        uv=np.asarray(uv,float); return s.O+uv[...,:1]*s.ex*s.L+uv[...,1:2]*s.ey*s.L

def ink_profile(Lc, x0, y0, thr=90, Lskin=None, Link=None, pick=None):
    """largest ink component of a crop -> per column (x, centre y, eff. vertical width, top, bottom) in full-image coords"""
    ink=Lc<thr
    lab,n=ndi.label(ink,np.ones((3,3)))
    if n==0: return None
    sz=ndi.sum(ink,lab,range(1,n+1))
    k=(pick if pick else int(np.argmax(sz))+1)
    comp=lab==k
    if Lskin is None: Lskin=np.median(Lc[~ndi.binary_dilation(ink,iterations=2)])
    if Link is None: Link=np.percentile(Lc[comp],5)
    cov=np.clip((Lskin-Lc)/(Lskin-Link),0,1)
    out=[]
    for x in range(comp.shape[1]):
        r=np.nonzero(comp[:,x])[0]
        if len(r)==0: continue
        a,b=r.min(),r.max()
        a2=max(0,a-1); b2=min(comp.shape[0]-1,b+1)
        w=cov[a2:b2+1,x]; rows=np.arange(a2,b2+1)
        out.append((x+x0+0.5, (w*(rows+0.5)).sum()/max(w.sum(),1e-6)+y0, w.sum(), a+y0, b+y0))
    return np.array(out), comp

def stroke_mask(shape, pts, widths, ss=4):
    """binary stroke: pixel on if >=50% of ss x ss subsamples lie within width/2 of the dense polyline"""
    pts=np.asarray(pts,float); widths=np.asarray(widths,float)
    # densify
    seg=np.hypot(*np.diff(pts,axis=0).T); t=np.concatenate([[0],np.cumsum(seg)])
    tt=np.linspace(0,t[-1],max(2,int(t[-1]*10)))
    P=np.stack([np.interp(tt,t,pts[:,0]),np.interp(tt,t,pts[:,1])],1); Wd=np.interp(tt,t,widths)
    x0=int(np.floor(P[:,0].min()-Wd.max()))-1; x1=int(np.ceil(P[:,0].max()+Wd.max()))+2
    y0=int(np.floor(P[:,1].min()-Wd.max()))-1; y1=int(np.ceil(P[:,1].max()+Wd.max()))+2
    H,Wc=shape; m=np.zeros(shape,bool)
    off=(np.arange(ss)+0.5)/ss
    for y in range(max(0,y0),min(H,y1)):
        for x in range(max(0,x0),min(Wc,x1)):
            sx=(x+off)[None,:].repeat(ss,0).ravel(); sy=(y+off)[:,None].repeat(ss,1).ravel()
            dx=sx[:,None]-P[None,:,0]; dy=sy[:,None]-P[None,:,1]
            d=np.hypot(dx,dy); inside=(d<=Wd[None,:]/2).any(1)
            if inside.mean()>=0.5: m[y,x]=True
    return m

def vert_width(mask, x):
    r=np.nonzero(mask[:,x])[0]; return len(r)
