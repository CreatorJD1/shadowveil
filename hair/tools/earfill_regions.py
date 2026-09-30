import json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
from earfill_lib import *
EARBOX={'apose':[(570,195,628,280),(735,195,795,280)],'tpose':[(575,190,632,280),(730,190,790,280)],
        'left':[(675,185,730,262)],'right':[(640,190,690,262)],'back':[(585,195,632,272),(735,195,782,272)]}
def disk(r): y,x=np.mgrid[-r:r+1,-r:r+1]; return x*x+y*y<=r*r
def ear_interior(v,r=4):
    """pixels inside the closed ear/head silhouette of Body's rest stack (holes where Body erased hair), per ear box"""
    mid=unpremul(mid_stack(v)); H,W=mid.shape[:2]; a=mid[...,3]
    out=np.zeros((H,W),bool)
    for (x0,y0,x1,y1) in EARBOX[v]:
        pad=r+2; sub=a[y0-pad:y1+pad,x0-pad:x1+pad]>0
        cl=ndi.binary_fill_holes(ndi.binary_closing(np.pad(sub,r+1),disk(r)))[r+1:-r-1,r+1:-r-1]
        box=np.zeros_like(cl); box[pad:-pad,pad:-pad]=True
        out[y0-pad:y1+pad,x0-pad:x1+pad]|=cl&box&(sub==0)|(cl&box&(a[y0-pad:y1+pad,x0-pad:x1+pad]<255))
    return out
