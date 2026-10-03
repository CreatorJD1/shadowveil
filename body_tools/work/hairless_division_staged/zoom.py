import json,sys,numpy as np
from PIL import Image
sys.argv=[sys.argv[0],'bilinear']+sys.argv[1:]
exec(open('jointtest.py').read().split("res={}; tiles=[]")[0])
def posed(jn,th):
    ch=J[jn]; c=pc[ch]['pivot']; sub=subtree(ch)
    H,W=h.shape[:2]; yy,xx=np.mgrid[0:H,0:W]
    out=np.zeros((H,W,4))
    for k in order:
        im=img[k]
        if k in sub:
            t=np.radians(-th); dx,dy=xx-c[0],yy-c[1]
            sx=np.round(c[0]+np.cos(t)*dx-np.sin(t)*dy).astype(int); sy=np.round(c[1]+np.sin(t)*dx+np.cos(t)*dy).astype(int)
            ok=(sx>=0)&(sx<W)&(sy>=0)&(sy<H); o=np.zeros_like(im); o[ok]=im[sy[ok],sx[ok]]; im=o
        out=over(out,im)
    return out
