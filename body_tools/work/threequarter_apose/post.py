"""Post-process a Kontext candidate into her style. Writes base PNG (RGBA, 1365x1739)."""
import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize
ROOT='/workspace/shadowveil'
W,H=1365,1739
ANG={  # ring per body_tools/work/apose_turn/diagonals/diagonals.json
 '045':dict(nb='apose',  nb2='left',  foot=1682,cx=684.5),
 '135':dict(nb='back',   nb2='left',  foot=1681,cx=684.5),
 '225':dict(nb='back',   nb2='right', foot=1681,cx=676.0),
 '315':dict(nb='apose',  nb2='right', foot=1682,cx=676.0)}
LINE={'apose':(12,11,29),'left':(12,10,28),'right':(11,11,28),'back':(12,12,31)}
SKIN={'apose':(186,129,86),'left':(185,122,78),'right':(183,120,76),'back':(183,122,77)}
def exact_mode(view, lo, hi, part=None):
    """most common EXACT rgb of her art within an rgb box (so every tone used exists in her file)."""
    a=np.array(Image.open(part or f'{ROOT}/views/{view}/base.png').convert('RGBA'))
    m=a[...,3]>200; c=a[m][:,:3].astype(int)
    k=np.all((c>=lo)&(c<=hi),1); u,n=np.unique(c[k],axis=0,return_counts=True)
    return tuple(int(v) for v in u[n.argmax()])
def palette(view):
    P={'line':LINE[view],'skin':SKIN[view],
       'hair':exact_mode(view,(20,20,20),(40,40,40),f'{ROOT}/views/{view}/hair/bun.png'),
       'cloth':exact_mode(view,(48,46,48),(62,60,64)),
       'lip':exact_mode(view,(85,45,20),(110,70,45))}
    return P
def load_fig(gen):
    im=np.array(Image.open(gen).convert('RGB')).astype(int); h,w,_=im.shape
    bg=np.median(np.r_[im[:8].reshape(-1,3),im[-8:].reshape(-1,3),im[:,-8:].reshape(-1,3)],0)
    d=np.abs(im-bg).sum(-1)
    # magenta-ish: r,b high g low relative
    mag=(im[...,0]-im[...,1]>110)&(im[...,2]-im[...,1]>110)
    fg=(d>120)&~mag
    lab,n=nd.label(fg); sz=nd.sum(fg,lab,range(1,n+1))
    # right figure = largest component whose centroid is right of the middle
    cs=nd.center_of_mass(fg,lab,range(1,n+1))
    cand=[(sz[i],i+1) for i in range(n) if cs[i][1]>w*0.52]
    big=[i for i in range(n) if sz[i]>0.25*sz.max()]
    if len(big)==1: cand=[(sz[big[0]],big[0]+1)]
    keep=lab==max(cand)[1]
    # attach nearby small comps (loose wisps, fingers) within 6 px
    near=nd.binary_dilation(keep,iterations=6)
    kx=np.nonzero(keep)[1]; and_ok=lambda x: kx.min()-20<=x<=kx.max()+20
    for i in range(n):
        if sz[i]>=15 and and_ok(cs[i][1]) and (near&(lab==i+1)).any(): keep|=lab==i+1
    return im,keep,bg
def fit(im,keep,foot_t,cx_t,_s=None,_top=None):
    ys,xs=np.nonzero(keep); top,foot=ys.min(),ys.max()
    s=(foot_t-40)/(foot-top) if _s is None else _s
    top=top if _top is None else _top
    hb=keep[int(top+0.45*(foot-top)):int(top+0.50*(foot-top))]; cx=np.median(np.nonzero(hb)[1])
    # affine: X = s*(x-cx)+cx_t ; Y = s*(y-top)+40
    A=np.array([[s,0],[0,s]]); 
    def warp(arr,order):
        out=np.zeros((H,W)+arr.shape[2:],float)
        yy,xx=np.mgrid[0:H,0:W]; sy=(yy-40)/s+top; sx=(xx-cx_t)/s+cx
        if arr.ndim==3:
            for c in range(3): out[...,c]=nd.map_coordinates(arr[...,c].astype(float),[sy,sx],order=order,mode='constant',cval=0)
        else: out=nd.map_coordinates(arr.astype(float),[sy,sx],order=order,mode='constant',cval=0)
        return out
    rgb=warp(im,3); m=warp(keep.astype(float),1)>0.5
    m=nd.binary_opening(m,iterations=1)
    lab,n=nd.label(m); 
    if n>1:
        sz=nd.sum(m,lab,range(1,n+1)); m=nd.binary_dilation(lab==(sz.argmax()+1),iterations=0)|np.isin(lab,1+np.nonzero(sz>=40)[0])
    my=np.nonzero(m)[0]
    if _s is None and (my.min()!=40 or my.max()!=foot_t):
        s2=s*(foot_t-40)/(my.max()-my.min()); t2=top+(my.min()-40)/s
        for k in range(6):
            r=fit(im,keep,foot_t,cx_t,s2,t2); yy_=np.nonzero(r[1])[0]
            if yy_.min()==40 and yy_.max()==foot_t: return r
            s2*= (foot_t-40)/(yy_.max()-yy_.min()); t2+= (yy_.min()-40)/s2
        return r
    return np.clip(rgb,0,255),m,dict(scale=float(s),src_top=float(top),src_foot=int(foot),src_cx=float(cx),cx_t=cx_t)
def flatten(rgb,m,P,head_y1):
    """classify -> flat tones. dark strokes -> skeleton 1px line; dark masses -> hair (head) or cloth (body)."""
    L=rgb.mean(-1); r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    dark=m&(L<95)
    yy=np.mgrid[0:H,0:W][0]
    # masses: dark areas thicker than a stroke (opening with r=3)
    mass=nd.binary_opening(dark,structure=np.ones((7,7)))
    mass=nd.binary_dilation(mass,iterations=1)&dark
    stroke=dark&~mass
    lipz=m&(r-b>35)&(L<130)&(L>=60)&(yy<head_y1)&~mass
    out=np.zeros((H,W,4),np.uint8)
    def put(mask,c): out[mask,:3]=c; out[mask,3]=255
    put(m,P['skin'])
    hairm=mass&(yy<head_y1); clothm=mass&(yy>=head_y1)
    put(hairm,P['hair']); put(clothm,P['cloth'])
    put(lipz,P['lip'])
    # 1 px lines: silhouette boundary + skeleton of strokes + boundaries of masses
    sk=skeletonize(nd.binary_closing(stroke,iterations=1))&m
    edge=m&~nd.binary_erosion(m)
    medge=(hairm|clothm)&~nd.binary_erosion(hairm|clothm)
    put(sk|edge|medge,P['line'])
    return out,dict(dark=int(dark.sum()),hair=int(hairm.sum()),cloth=int(clothm.sum()),lip=int(lipz.sum()),stroke_skel=int(sk.sum()))
if __name__=='__main__':
    ang,gen,outp=sys.argv[1:4]
    cfg=ANG[ang]; P=palette(cfg['nb'])
    im,keep,bg=load_fig(gen)
    rgb,m,fitinfo=fit(im,keep,cfg['foot'],cfg['cx'])
    out,stats=flatten(rgb,m,P,head_y1=330)
    Image.fromarray(out).save(outp)
    Image.fromarray(rgb.astype(np.uint8)).save(outp.replace('.png','_upscaled_raw.png'))
    json.dump(dict(angle=ang,gen=gen,palette=P,fit=fitinfo,stats=stats,bg=list(map(float,bg))),open(outp.replace('.png','_post.json'),'w'),indent=1)
    print(ang,fitinfo,stats,P)
