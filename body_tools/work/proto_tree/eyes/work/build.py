import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
from seg2 import classes
SRC={v:f'/workspace/shadowveil/views/{v}/base.png' for v in ['apose','tpose','left','right']}
OUTER={('apose','EyeR'):-1,('apose','EyeL'):1,('tpose','EyeR'):-1,('tpose','EyeL'):1,('left','EyeL'):1,('right','EyeR'):-1}
EYES={
 'apose':{'EyeR':dict(bb=(620,212,674,244),ic='amber',seeds=[(632,230),(645,232)]),
          'EyeL':dict(bb=(694,210,750,244),ic='green',seeds=[(730,230),(715,232)])},
 'tpose':{'EyeR':dict(bb=(620,204,676,238),ic='amber',seeds=[(637,222),(650,226)]),
          'EyeL':dict(bb=(692,204,748,238),ic='green',seeds=[(731,222),(715,226)])},
 'left':{'EyeL':dict(bb=(596,196,642,230),ic='green',seeds=[(625,212),(614,218)])},
 'right':{'EyeR':dict(bb=(726,196,772,232),ic='amber',seeds=[(745,215),(756,221)],extra=(753,211,759,224))},
}
def hull_mask(pts,shape):
    pts=np.array(pts,float)
    h=ConvexHull(pts)
    yy,xx=np.mgrid[0:shape[0],0:shape[1]]
    P=np.stack([xx.ravel(),yy.ravel()],1)
    inside=np.all(P@h.equations[:,:2].T+h.equations[:,2]<=1e-6,axis=1)
    return inside.reshape(shape)|_pts(pts,shape)
def _pts(pts,shape):
    m=np.zeros(shape,bool); p=pts.astype(int); m[p[:,1],p[:,0]]=True; return m
def seg_eye(a,cfg):
    x0,y0,x1,y1=cfg['bb']; sub=a[y0:y1,x0:x1,:3]
    sc,ir,lum=classes(sub,cfg['ic'])
    cand=sc|ir
    lab,_=ndi.label(ndi.binary_closing(cand,iterations=1)&(cand|(lum>=40)),structure=np.ones((3,3)))
    core=np.zeros_like(cand)
    for sx,sy in cfg['seeds']:
        l=lab[sy-y0,sx-x0]; assert l>0,(sx,sy); core|=lab==l
    core&=cand
    if 'extra' in cfg:
        ex0,ey0,ex1,ey1=cfg['extra']
        border=np.concatenate([sub[0],sub[-1],sub[:,0],sub[:,-1]]); bl=border.mean(1)
        skin=np.median(border[(bl>90)&(bl<200)],0)
        notskin=np.sqrt(((sub-skin)**2).sum(2))>=40
        ex=np.zeros_like(core); ex[ey0-y0:ey1-y0+1,ex0-x0:ex1-x0+1]=True; ex&=notskin
        core|=ex
    ys,xs=np.nonzero(core)
    mask=hull_mask(np.stack([xs,ys],1),core.shape)
    # iris footprint: hull of iris-class pixels connected to iris seed inside mask
    ilab,_=ndi.label(ir&mask,structure=np.ones((3,3)))
    isx,isy=cfg['seeds'][1]; l=ilab[isy-y0,isx-x0]; assert l>0
    irc=ilab==l
    # include other iris blobs close to the main one (split by pupil)
    d=ndi.distance_transform_edt(~irc)
    for k in range(1,ilab.max()+1):
        if k!=l and (d[ilab==k].min()<=4) and (ilab==k).sum()>=2: irc|=ilab==k
    ys,xs=np.nonzero(irc)
    foot=hull_mask(np.stack([xs,ys],1),core.shape)&mask
    if 'extra' in cfg:
        pts=np.argwhere(foot|(ex&mask)); foot=hull_mask(pts[:,::-1],core.shape)&mask
    # sclera anti-alias fringe (light, unsaturated) touching the hull is part of the opening too
    ring1=ndi.binary_dilation(mask,iterations=1)&~mask
    h_,sat_,val_=__import__('seg2').hsvarr(sub)
    fringe=ring1&(sat_<0.35)&(lum>=100)
    mask=mask|fringe
    # any drawn iris pixel touching the footprint but outside the hull joins the opening,
    # so the white always covers the whole drawn iris/pupil (no ghosting when the iris moves)
    add=ndi.binary_propagation(foot,mask=(foot|(ir&ndi.binary_dilation(foot,iterations=2))),structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&~mask
    mask|=add; foot|=add
    # dim iris-hued pixels of the drawn iris top (under the lash shadow) also belong to the iris
    border=np.concatenate([sub[0],sub[-1],sub[:,0],sub[:,-1]]); bl=border.mean(1)
    skinref=np.median(border[(bl>90)&(bl<200)],0)
    notskin=np.sqrt(((sub-skinref)**2).sum(2))>=35
    hh,ss,vv=__import__('seg2').hsvarr(sub)
    if cfg['ic']=='green': hue=(sub[...,1]>sub[...,0]+6)&(lum>30)
    else: hue=(hh>=18)&(hh<=55)&(ss>0.45)&(vv>0.18)
    near3=ndi.binary_dilation(foot,iterations=3)
    fy_=np.nonzero(foot)[0]; ycen=(fy_.min()+fy_.max())/2
    upper=np.zeros_like(foot); upper[:int(ycen)]=True
    add2=ndi.binary_propagation(foot,mask=foot|(hue&notskin&near3&upper),structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&~foot
    mask|=add2; foot|=add2
    # no holes: every row of the iris is one solid span (catchlight / pupil included)
    for yy_ in np.nonzero(foot.any(1))[0]:
        xx_=np.nonzero(foot[yy_])[0]; foot[yy_,xx_.min():xx_.max()+1]=True
    foot&=mask
    # dark iris rim / pupil pixels touching the footprint inside the opening move with the iris
    dk=(lum<85)&mask
    foot=ndi.binary_propagation(foot,mask=foot|(dk&ndi.binary_dilation(foot,iterations=2)),structure=np.ones((3,3)))
    return dict(sub=sub,sc=sc,ir=ir,lum=lum,core=core,mask=mask,foot=foot,off=(x0,y0))
def show(r,name):
    m=r['mask'];f=r['foot'];sub=r['sub'];x0,y0=r['off']
    out=[]
    for y in range(m.shape[0]):
        out.append('%3d '%(y+y0)+''.join(('F' if f[y,x] else ('M' if m[y,x] else ('#' if r['lum'][y,x]<85 else '.'))) for x in range(m.shape[1])))
    print(name,'x0',x0); print('\n'.join(out))
if __name__=='__main__':
    for v,eyes in EYES.items():
        a=np.array(Image.open(SRC[v]).convert('RGBA')).astype(int)
        for e,cfg in eyes.items(): show(seg_eye(a,cfg),v+' '+e)
