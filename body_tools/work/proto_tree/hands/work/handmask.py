import numpy as np
from scipy import ndimage as ndi
from skimage.draw import polygon as skpoly
def side(P,w):
    (ax,ay),(bx,by)=w
    return (P[...,0]-ax)*(by-ay)-(P[...,1]-ay)*(bx-ax)
def hand_mask(a,H):
    """a: full RGBA float array. returns full-canvas bool mask of the hand (distal of wrist line)."""
    Hh,W=a.shape[:2]; x0,y0,x1,y1=H['box']
    yy,xx=np.mgrid[y0:y1,x0:x1]; P=np.stack([xx,yy],-1).astype(float)
    s=side(P,H['wrist']); ref=side(np.array(H['inside'],float),H['wrist'])
    hs=np.sign(s)==np.sign(ref)
    sub=a[y0:y1,x0:x1]; alpha=sub[...,3]
    if H.get('mode','alpha')=='alpha':
        m=(alpha>0)&hs
    else:
        rgb=sub[...,:3]; L=rgb@np.array([.299,.587,.114])
        dark=L<H.get('darkL',95)
        if 'loose' in H:
            reg=np.zeros(alpha.shape,bool); pp=np.array(H['loose'],float)
            rr,cc=skpoly(pp[:,1]-y0,pp[:,0]-x0,alpha.shape); reg[rr,cc]=True
        else: reg=np.ones(alpha.shape,bool)
        free=(~dark)&hs&reg
        for b in H.get('barriers',[]):
            from skimage.draw import line
            for i in range(len(b)-1):
                r,c=line(int(b[i][1]-y0),int(b[i][0]-x0),int(b[i+1][1]-y0),int(b[i+1][0]-x0))
                free[r,c]=False
        lab,_=ndi.label(free)
        # exterior = free components touching the loose-polygon border
        border=reg&~ndi.binary_erosion(reg)
        ext_ids=set(np.unique(lab[border&free]))-{0}
        ins_ids=set(lab[int(y-y0),int(x-x0)] for (x,y) in H['seeds'])-{0}
        assert not (ext_ids&ins_ids), ('leak',v if False else '', ext_ids&ins_ids)
        ext=np.isin(lab,list(ext_ids))
        m=reg&hs&~ext
        from skimage.morphology import disk
        m=ndi.binary_closing(np.pad(m,4),structure=disk(2))[4:-4,4:-4]&hs&reg
        m=ndi.binary_fill_holes(m)
        halo=L<H.get('haloL',150)
        m=m|(ndi.binary_dilation(m,iterations=1)&halo&hs&reg)
        m=ndi.binary_dilation(m,iterations=H.get('grow',2))&hs&reg   # take the soft line halo too
    lab,_=ndi.label(m); 
    ids=set(lab[int(y-y0),int(x-x0)] for (x,y) in H['seeds'])-{0}
    m=np.isin(lab,list(ids))
    full=np.zeros((Hh,W),bool); full[y0:y1,x0:x1]=m
    return full
