import numpy as np
from PIL import Image
from scipy import ndimage as ndi
def hsvarr(sub):
    s=sub/255.0; r,g,b=s[...,0],s[...,1],s[...,2]
    mx=s.max(2); mn=s.min(2); c=mx-mn
    h=np.zeros_like(mx)
    m=c>1e-6
    rr=m&(mx==r); gg=m&(mx==g)&~rr; bb=m&~rr&~gg
    h[rr]=(60*((g-b)[rr]/c[rr]))%360; h[gg]=60*((b-r)[gg]/c[gg])+120; h[bb]=60*((r-g)[bb]/c[bb])+240
    sat=np.where(mx>0,c/np.maximum(mx,1e-6),0)
    return h,sat,mx
def classes(sub,iris):
    h,sat,val=hsvarr(sub); lum=sub.mean(2)
    sclera=(sat<0.28)&(lum>105)
    if iris=='green': ir=(sub[...,1]>sub[...,0]+8)&(sub[...,1]>=sub[...,2])&(lum>45)
    else: ir=(h>=29)&(h<=52)&(sat>0.45)&(val>0.45)
    return sclera,ir,lum
