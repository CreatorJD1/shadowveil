import sys; sys.path.insert(0,'/workspace/shadowveil/body_tools')
import numpy as np, joint_zoom as jz, pose_render as pr
from scipy import ndimage
jz.BG=(0,0,0,0)
disk=(np.hypot(*np.mgrid[-3:4,-3:4])<=3)
def resid(A):
    m=A>127; return ndimage.binary_closing(np.pad(m,4),disk)[4:-4,4:-4]&~m
for v in ['apose','tpose','left','right','back']:
    rig,_=jz.parts(v)
    for sd,wx,wy in jz.wrists(v):
        out=[]
        for lab,j,a in jz.WR:
            pose={} if j is None else {f'{j}{sd}':a}
            Wm=pr.world(rig,pose); cx,cy,_=Wm[f'forearm_{sd}']@[wx,wy,1]
            box=(int(cx-40),int(cy-40),int(cx+40),int(cy+40))
            A=np.array(jz.render_crop(v,pose,box,out=80,hands=True))[...,3]
            B=np.array(jz.render_crop(v,pose,box,out=80,hands=False))[...,3]
            # erased area showing: body-only alpha missing where hands also don't cover
            out.append((f'{lab}{a:+d}' if j else 'rest', int(resid(A).sum()), int(((A<128)&ndimage.binary_erosion(A>=128,iterations=0)).sum())))
        print(v,sd,[(o[0],o[1]) for o in out],flush=True)
