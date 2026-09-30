# runs Base Hair's lineart_check.py (read-only copy of its logic, unchanged) with the warp resampler swapped:
#   MODE=bilinear (Hair's mirror, control) | nearest | ss2 (our default posed path: 2x supersample = mean of 4 bilinear taps at +-0.25 px)
import os,sys,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/tools');import render as RD
from scipy import ndimage as ndi
MODE=os.environ.get('MODE','bilinear');I=RD.I
def warp(img,Mx,box=None):
    H,W=img.shape[:2];x0,y0,x1,y1=box or (0,0,W,H);a,b,c,d,e,f=Mx
    if np.allclose(Mx,I): return img[y0:y1,x0:x1].copy()
    det=a*d-b*c;ia,ib,ic,id_=d/det,-b/det,-c/det,a/det
    offs=[(0,0)] if MODE!='ss2' else [(-0.25,-0.25),(0.25,-0.25),(-0.25,0.25),(0.25,0.25)];acc=0
    for dx,dy in offs:
        oy,ox=np.mgrid[y0:y1,x0:x1].astype(float);ox+=0.5+dx;oy+=0.5+dy;X=ox-e;Y=oy-f;sx=ia*X+ic*Y-0.5;sy=ib*X+id_*Y-0.5
        acc=acc+np.stack([ndi.map_coordinates(img[...,k],[sy,sx],order=0 if MODE=='nearest' else 1,mode='constant',cval=0) for k in range(4)],-1)
    return acc/len(offs)
RD.warp=warp
src=open('/workspace/shadowveil/hair/qa/lineart/work/lineart_check.py').read()
sys.argv=['lineart_check.py','--tag',MODE,'--hairroot','/workspace/shadowveil/views','--out',sys.argv[1]]
exec(compile(src,'lineart_check.py','exec'))
