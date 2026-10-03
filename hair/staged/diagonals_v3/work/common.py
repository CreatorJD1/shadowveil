import numpy as np,glob,json,os
from PIL import Image
R='/workspace/shadowveil'; W,H=1365,1739; FR={'045':33,'315':191}
A=lambda p:np.array(Image.open(p).convert('RGBA')).astype(int)
def fit(ang):
    f=json.load(open(f'{R}/eyes/staged/diagonals/{ang}/rig.json'))['viewFit']; return f['scale'],f['dx'],f['dy']
def frame_to_view(fm,ang):
    s,dx,dy=fit(ang); yy,xx=np.mgrid[0:H,0:W]; fx=np.floor((xx+0.5-dx)/s).astype(int); fy=np.floor((yy+0.5-dy)/s).astype(int)
    ok=(fx>=0)&(fx<fm.shape[1])&(fy>=0)&(fy<fm.shape[0]); out=np.zeros((H,W)+fm.shape[2:],fm.dtype); out[ok]=fm[fy[ok],fx[ok]]; return out
def opening(ang):
    fm=None
    for p in ('white','iris','lash'):
        for f in glob.glob(f'{R}/eyes/staged/diagonals/{ang}/Eye?_{p}.png'):
            a=A(f)[...,3]>0; fm=a if fm is None else fm|a
    return frame_to_view(fm,ang)
def src_view(ang): return frame_to_view(A(f'{R}/reference/apose_turn/frames/f{FR[ang]:03d}.png'),ang)
