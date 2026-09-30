import numpy as np, colorsys
from PIL import Image
from scipy import ndimage as ndi
def hsv(sub):
    s=sub/255.0; mx=s.max(2); mn=s.min(2)
    sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0); return sat,mx
def segment(a,bb,dark_thr=85,close=1):
    x0,y0,x1,y1=bb; sub=a[y0:y1,x0:x1,:3].astype(int)
    lum=sub.mean(2); sat,val=hsv(sub)
    dark=lum<dark_thr
    dk=ndi.binary_closing(dark,iterations=close) if close else dark
    dk=dk|dark
    filled=ndi.binary_fill_holes(dk)
    inner=filled&~dk
    # keep biggest inner component(s) (eye opening)
    lab,n=ndi.label(inner)
    sizes=ndi.sum(inner,lab,range(1,n+1))
    keep=np.zeros_like(inner)
    for i,s in enumerate(sizes):
        if s>=0.25*sizes.max(): keep|=lab==i+1
    opening=ndi.binary_fill_holes(keep|(filled&ndi.binary_dilation(keep,iterations=3)&~dk)) # rough
    return sub,lum,sat,dark,filled,keep
